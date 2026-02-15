# utils/xp.py
import time
from utils.economy import load_economy, add_xp, EconomyIdentity


def get_xp_multiplier(identity: EconomyIdentity) -> float:
    """
    Returns active XP multiplier based on xp_bonus.
    """
    data = load_economy(identity)
    bonus = data.get("xp_bonus", {}) or {}

    mult = float(bonus.get("multiplier", 1.0) or 1.0)
    expires = int(bonus.get("expires_at", 0) or 0)

    if mult > 1.0 and int(time.time()) < expires:
        return mult

    return 1.0


def award_xp(identity: EconomyIdentity, base_amount: int):
    """
    Applies XP multiplier, awards XP, returns (leveled_up, new_level, awarded_amount).
    """
    mult = get_xp_multiplier(identity)
    awarded = int(round(base_amount * mult))

    leveled, level = add_xp(identity, awarded)
    return leveled, level, awarded
