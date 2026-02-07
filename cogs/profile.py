from typing import Optional, List, Tuple
from utils.economy import load_economy, save_economy, EconomyIdentity

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
    Accepts 'RRGGBB' or '#RRGGBB' and returns '#RRGGBB' or None if invalid.
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
