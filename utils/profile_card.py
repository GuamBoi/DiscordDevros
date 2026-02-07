# utils/profile_card.py
import os
from io import BytesIO
from typing import Optional, Tuple

import discord
from PIL import Image, ImageDraw

PROFILE_FRAMES_DIR = os.path.join("data", "profile_frames")

CARD_SIZE = (512, 512)         # default you chose
AVATAR_SIZE = (360, 360)       # square avatar area on the full card
AVATAR_POS = (76, 96)          # where the avatar is placed on the full card
HEADER_HEIGHT = 64             # top accent strip height

def _parse_hex_color(value: Optional[str], fallback: Tuple[int, int, int] = (54, 57, 63)) -> Tuple[int, int, int]:
    """
    Accepts "#RRGGBB" or "RRGGBB". Returns RGB tuple.
    """
    if not value:
        return fallback
    s = value.strip()
    if s.startswith("#"):
        s = s[1:]
    if len(s) != 6:
        return fallback
    try:
        r = int(s[0:2], 16)
        g = int(s[2:4], 16)
        b = int(s[4:6], 16)
        return (r, g, b)
    except ValueError:
        return fallback

async def render_profile_card(
    member: discord.Member,
    frame_id: Optional[str] = None,
    accent_hex: Optional[str] = None,
) -> BytesIO:
    """
    Returns PNG bytes for a generated 512x512 profile card:
    - solid background
    - accent header strip
    - user's square avatar
    - optional PNG frame overlay from data/profile_frames/<frame_id>.png
    """
    # Base canvas
    base = Image.new("RGBA", CARD_SIZE, (32, 34, 37, 255))
    draw = ImageDraw.Draw(base)

    accent = _parse_hex_color(accent_hex, fallback=(88, 101, 242))
    draw.rectangle([0, 0, CARD_SIZE[0], HEADER_HEIGHT], fill=(accent[0], accent[1], accent[2], 255))

    # Subtle border
    draw.rectangle([0, 0, CARD_SIZE[0] - 1, CARD_SIZE[1] - 1], outline=(0, 0, 0, 120), width=2)

    # Avatar (square)
    try:
        avatar_asset = member.display_avatar.replace(size=512, static_format="png")
        avatar_bytes = await avatar_asset.read()
        avatar = Image.open(BytesIO(avatar_bytes)).convert("RGBA")
        avatar = avatar.resize(AVATAR_SIZE, Image.Resampling.LANCZOS)
        base.alpha_composite(avatar, dest=AVATAR_POS)
    except Exception:
        pass

    # Frame overlay (full 512x512)
    if frame_id:
        frame_path = os.path.join(PROFILE_FRAMES_DIR, f"{frame_id}.png")
        if os.path.exists(frame_path):
            try:
                frame = Image.open(frame_path).convert("RGBA")
                frame = frame.resize(CARD_SIZE, Image.Resampling.LANCZOS)
                base.alpha_composite(frame, dest=(0, 0))
            except Exception:
                pass

    out = BytesIO()
    base.save(out, format="PNG")
    out.seek(0)
    return out

async def render_profile_thumbnail(
    member: discord.Member,
    frame_id: Optional[str] = None,
    accent_hex: Optional[str] = None,
    size: int = 256,
) -> BytesIO:
    """
    Returns PNG bytes for a square thumbnail (default 256x256):
    - user's avatar
    - optional frame overlay (scaled from 512x512 frame PNG)
    - subtle accent border
    """
    base = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(base)

    # Subtle accent border
    accent = _parse_hex_color(accent_hex, fallback=(88, 101, 242))
    border_w = max(2, size // 64)
    draw.rectangle([0, 0, size - 1, size - 1], outline=(accent[0], accent[1], accent[2], 255), width=border_w)

    # Avatar (fills the thumbnail)
    try:
        avatar_asset = member.display_avatar.replace(size=512, static_format="png")
        avatar_bytes = await avatar_asset.read()
        avatar = Image.open(BytesIO(avatar_bytes)).convert("RGBA")
        avatar = avatar.resize((size, size), Image.Resampling.LANCZOS)
        base.alpha_composite(avatar, dest=(0, 0))
    except Exception:
        pass

    # Frame overlay scaled down
    if frame_id:
        frame_path = os.path.join(PROFILE_FRAMES_DIR, f"{frame_id}.png")
        if os.path.exists(frame_path):
            try:
                frame = Image.open(frame_path).convert("RGBA")
                frame = frame.resize((size, size), Image.Resampling.LANCZOS)
                base.alpha_composite(frame, dest=(0, 0))
            except Exception:
                pass

    out = BytesIO()
    base.save(out, format="PNG")
    out.seek(0)
    return out
