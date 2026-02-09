from __future__ import annotations
import os
from typing import Optional, List, Tuple
from utils.economy import load_economy, save_economy, EconomyIdentity

# Default folder that holds frame PNG files
DEFAULT_PROFILE_FRAMES_DIR = os.path.join("data", "profile_frames")

# ============================================================
# Schema / inventory
# ============================================================

def ensure_shop_schema(identity: EconomyIdentity) -> dict:
    """
    Adds/repairs shop inventory fields inside the user's economy JSON.
    Safe to call any time.
    """
    data = load_economy(identity)

    inv = data.setdefault("inventory", {})

    # Equipped cosmetics
    profile = inv.setdefault("profile", {})
    profile.setdefault("frame", None)         # equipped frame_id (str) or None
    profile.setdefault("accent_color", None)  # equipped color hex "#RRGGBB" or None

    # Owned cosmetics
    owned = inv.setdefault("owned", {})
    owned.setdefault("frames", [])            # list[str]
    owned.setdefault("colors", [])            # list[str] (hex "#RRGGBB")

    # NOTE: This assumes your economy schema stores a stable user_id in the JSON.
    # If your economy layer uses member.id everywhere, make sure data["user_id"] is that id (string).
    save_economy(data["user_id"], data)
    return data

# ---------- Read helpers ----------

def get_equipped(identity: EconomyIdentity) -> Tuple[Optional[str], Optional[str]]:
    data = ensure_shop_schema(identity)
    prof = data["inventory"]["profile"]
    return prof.get("frame"), prof.get("accent_color")

def get_owned_frames(identity: EconomyIdentity) -> List[str]:
    data = ensure_shop_schema(identity)
    return list(data["inventory"]["owned"]["frames"])

def get_owned_colors(identity: EconomyIdentity) -> List[str]:
    data = ensure_shop_schema(identity)
    return list(data["inventory"]["owned"]["colors"])

def owns_frame(identity: EconomyIdentity, frame_id: str) -> bool:
    return frame_id in get_owned_frames(identity)

def owns_color(identity: EconomyIdentity, color_hex: str) -> bool:
    return color_hex in get_owned_colors(identity)

# ---------- Write helpers ----------

def grant_frame(identity: EconomyIdentity, frame_id: str) -> bool:
    """
    Adds a frame to owned frames. Returns True if newly added, False if already owned.
    """
    data = ensure_shop_schema(identity)
    frames = data["inventory"]["owned"]["frames"]
    if frame_id in frames:
        return False
    frames.append(frame_id)
    save_economy(data["user_id"], data)
    return True

def grant_color(identity: EconomyIdentity, color_hex: str) -> bool:
    """
    Adds a color to owned colors. Returns True if newly added, False if already owned.
    """
    data = ensure_shop_schema(identity)
    colors = data["inventory"]["owned"]["colors"]
    if color_hex in colors:
        return False
    colors.append(color_hex)
    save_economy(data["user_id"], data)
    return True

def equip_frame(identity: EconomyIdentity, frame_id: Optional[str]) -> None:
    data = ensure_shop_schema(identity)
    data["inventory"]["profile"]["frame"] = frame_id
    save_economy(data["user_id"], data)

def equip_color(identity: EconomyIdentity, color_hex: Optional[str]) -> None:
    data = ensure_shop_schema(identity)
    data["inventory"]["profile"]["accent_color"] = color_hex
    save_economy(data["user_id"], data)

# ---------- Validation helpers ----------

def normalize_hex_color(value: str) -> Optional[str]:
    """
    Accepts 'RRGGBB' or '#RRGGBB' and returns normalized '#rrggbb' or None if invalid.
    """
    if not value:
        return None
    s = value.strip()
    if s.startswith("#"):
        s = s[1:]
    if len(s) != 6:
        return None
    try:
        int(s, 16)
    except ValueError:
        return None
    return f"#{s.lower()}"

# ============================================================
# Shop presentation helpers (kept here so cogs stay clean)
# ============================================================

def frame_path(frame_id: str, frames_dir: str = DEFAULT_PROFILE_FRAMES_DIR) -> str:
    return os.path.join(frames_dir, f"{frame_id}.png")

def frame_exists(frame_id: str, frames_dir: str = DEFAULT_PROFILE_FRAMES_DIR) -> bool:
    return os.path.exists(frame_path(frame_id, frames_dir=frames_dir))

def format_price(price: int, currency: str = "gold") -> str:
    # price in italics as requested
    return f"*— {price} {currency}*"

def format_frame_line(frame_id: str, price: int, missing: bool = False) -> str:
    # Bold id, no name, italic price
    warn = " ⚠️ *(file missing)*" if missing else ""
    return f"• **{frame_id}** {format_price(price)}{warn}"

def format_color_line(color_hex: str, price: int) -> str:
    # Bold hex, no name, italic price
    return f"• **{color_hex}** {format_price(price)}"
