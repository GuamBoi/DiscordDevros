from typing import Optional
from utils.economy import load_economy, save_economy, EconomyIdentity

def ensure_shop_schema(identity: EconomyIdentity) -> dict:
    """
    Adds/repairs shop inventory fields inside the user's economy JSON.
    Safe to call any time.
    """
    data = load_economy(identity)

    inv = data.setdefault("inventory", {})
    profile = inv.setdefault("profile", {})
    profile.setdefault("frame", None)         # equipped frame_id (str) or None
    profile.setdefault("accent_color", None)  # equipped color (hex like "#3498db") or None

    owned = inv.setdefault("owned", {})
    owned.setdefault("frames", [])            # list[str]
    owned.setdefault("colors", [])            # list[str]

    save_economy(data["user_id"], data)
    return data

def get_equipped_frame(identity: EconomyIdentity) -> Optional[str]:
    data = ensure_shop_schema(identity)
    return data["inventory"]["profile"].get("frame")

def get_equipped_accent_color(identity: EconomyIdentity) -> Optional[str]:
    data = ensure_shop_schema(identity)
    return data["inventory"]["profile"].get("accent_color")
