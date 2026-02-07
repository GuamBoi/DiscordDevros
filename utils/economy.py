import os
import json
from typing import Optional

import discord
from config import (
    ECONOMY_FOLDER,
    DEFAULT_CURRENCY_GIVE,
    DEFAULT_CURRENCY_TAKE,
    CURRENCY_NAME,
    GAME_WIN,
    LEVEL_UP_REWARD_MULTIPLIER
)

def user_key(member: discord.abc.User) -> str:
    """Centralized economy identity. Uses Discord member/user ID."""
    return str(member.id)

# Ensure the economy folder exists
if not os.path.exists(ECONOMY_FOLDER):
    os.makedirs(ECONOMY_FOLDER)

def get_user_file(key: str) -> str:
    """Get full path for a user's economy JSON file (key is Discord ID string)."""
    return os.path.join(ECONOMY_FOLDER, f"{key}.json")

def _load_from_disk(key: str) -> Optional[dict]:
    path = get_user_file(key)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_economy(key: str, member: Optional[discord.abc.User] = None) -> dict:
    """
    Load a user's economy data.
    - If file exists: load it (no back-fill except optional label refresh).
    - If not: create with full default schema.
    If member is provided, refresh human-readable labels (username/display_name).
    """
    data = _load_from_disk(key)

    if data is None:
        # New user: create default data
        data = {
            "user_id": key,
            "username": None,
            "display_name": None,
            "currency": DEFAULT_CURRENCY_GIVE,
            "bet_lock": 0,
            "wordle_streak": 0,
            "connect4_streak": 0,
            "battleship_streak": 0,
            "rolls": [],
            "xp": 0,
            "level": 1
        }

    # Optional: refresh labels (safe metadata only)
    if member is not None:
        data["user_id"] = key
        data["username"] = getattr(member, "name", None)
        data["display_name"] = getattr(member, "display_name", None)

    save_economy(key, data)
    return data

def save_economy(key: str, data: dict) -> None:
    """Persist a user's economy data to disk."""
    with open(get_user_file(key), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def add_currency(key: str, amount=DEFAULT_CURRENCY_GIVE) -> int:
    data = load_economy(key)
    data["currency"] = int(data.get("currency", 0) or 0) + int(amount)
    save_economy(key, data)
    return data["currency"]

def remove_currency(key: str, amount=DEFAULT_CURRENCY_TAKE) -> int:
    data = load_economy(key)
    current = int(data.get("currency", 0) or 0)
    data["currency"] = max(0, current - int(amount))
    save_economy(key, data)
    return data["currency"]

def get_balance(key: str) -> int:
    return int(load_economy(key).get("currency", 0) or 0)

# —————— XP / Level Functions ——————

def add_xp(key: str, amount: int):
    """
    Award XP, handle level-ups, and reward currency on each new level.
    Returns (leveled_up: bool, new_level: int).
    """
    data = load_economy(key)
    data["xp"] = int(data.get("xp", 0) or 0) + int(amount)
    data["level"] = int(data.get("level", 1) or 1)

    leveled_up = False

    while data["xp"] >= 100 * data["level"]:
        data["xp"] -= 100 * data["level"]
        data["level"] += 1

        reward = int(LEVEL_UP_REWARD_MULTIPLIER * data["level"])
        data["currency"] = int(data.get("currency", 0) or 0) + reward
        leveled_up = True

    save_economy(key, data)
    return leveled_up, data["level"]

# —————— Game-specific Helpers ——————

def get_wordle_streak(key: str) -> int:
    return int(load_economy(key).get("wordle_streak", 0) or 0)

def set_wordle_streak(key: str, streak: int) -> int:
    data = load_economy(key)
    data["wordle_streak"] = int(streak)
    save_economy(key, data)
    return data["wordle_streak"]

def get_connect4_streak(key: str) -> int:
    return int(load_economy(key).get("connect4_streak", 0) or 0)

def set_connect4_streak(key: str, streak: int) -> int:
    data = load_economy(key)
    data["connect4_streak"] = int(streak)
    save_economy(key, data)
    return data["connect4_streak"]

# —————— Role-shop Helpers ——————

def add_role(key: str, role_name: str) -> bool:
    data = load_economy(key)
    data.setdefault("rolls", [])
    if role_name not in data["rolls"]:
        data["rolls"].append(role_name)
        save_economy(key, data)
        return True
    return False

def remove_role(key: str, role_name: str) -> bool:
    data = load_economy(key)
    data.setdefault("rolls", [])
    if role_name in data["rolls"]:
        data["rolls"].remove(role_name)
        save_economy(key, data)
        return True
    return False

def has_role(key: str, role_name: str) -> bool:
    return role_name in load_economy(key).get("rolls", [])

def handle_roll_reaction(key: str, role_name: str) -> bool:
    return remove_role(key, role_name) if has_role(key, role_name) else add_role(key, role_name)
