import os
from io import BytesIO
from typing import Optional, Tuple
import discord
from PIL import Image, ImageDraw

PROFILE_FRAMES_DIR = os.path.join("data", "profile_frames")

CARD_SIZE = (512, 512)         # default you chose
AVATAR_SIZE = (360, 360)       # square avatar area
AVATAR_POS = (76, 96)          # centered with space for header strip
HEADER_HEIGHT = 64

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
    # --- base canvas ---
    base = Image.new("RGBA", CARD_SIZE, (32, 34, 37, 255))
    draw = ImageDraw.Draw(base)

    accent = _parse_hex_color(accent_hex, fallback=(88, 101, 242))  # discord-ish fallback
    draw.rectangle([0, 0, CARD_SIZE[0], HEADER_HEIGHT], fill=(accent[0], accent[1], accent[2], 255))

    # subtle border
    draw.rectangle([0, 0, CARD_SIZE[0] - 1, CARD_SIZE[1] - 1], outline=(0, 0, 0, 120), width=2)

    # --- avatar ---
    try:
        avatar_asset = member.display_avatar.replace(size=512, static_format="png")
        avatar_bytes = await avatar_asset.read()
        avatar = Image.open(BytesIO(avatar_bytes)).convert("RGBA")
        avatar = avatar.resize(AVATAR_SIZE, Image.Resampling.LANCZOS)
        base.alpha_composite(avatar, dest=AVATAR_POS)
    except Exception:
        # If avatar fails, just leave blank; don't kill the command
        pass

    # --- frame overlay ---
    if frame_id:
        frame_path = os.path.join(PROFILE_FRAMES_DIR, f"{frame_id}.png")
        if os.path.exists(frame_path):
            try:
                frame = Image.open(frame_path).convert("RGBA")
                frame = frame.resize(CARD_SIZE, Image.Resampling.LANCZOS)
                base.alpha_composite(frame, dest=(0, 0))
            except Exception:
                pass

    # --- output ---
    out = BytesIO()
    base.save(out, format="PNG")
    out.seek(0)
    return out
