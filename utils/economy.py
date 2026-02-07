import os
import json
from config import (
    ECONOMY_FOLDER,
    DEFAULT_CURRENCY_GIVE,
    DEFAULT_CURRENCY_TAKE,
    CURRENCY_NAME,
    GAME_WIN,
    LEVEL_UP_REWARD_MULTIPLIER
)

def user_key(member):  # Centralized economy identity. Uses Discord member ID.
    return str(member.id)

# Ensure the economy folder exists
if not os.path.exists(ECONOMY_FOLDER):
    os.makedirs(ECONOMY_FOLDER)

def get_user_file(key: str):
    """Get full path for a user's economy JSON file (key is Discord ID string)."""
    return os.path.join(ECONOMY_FOLDER, f"{key}.json")

def load_economy(key: str):
    """
    Load a user's economy data.
    - If file exists: load it (no back-fill).
    - If not: create with full default schema.
    """
    path = get_user_file(key)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # New user: create default data
    data = {
        "username": key,  # keep field for compatibility; you can store display name elsewhere later
        "currency": DEFAULT_CURRENCY_GIVE,
        "bet_lock": 0,
        "wordle_streak": 0,
        "connect4_streak": 0,
        "rolls": [],
        "xp": 0,
        "level": 1
    }
    save_economy(key, data)
    return data

def save_economy(key: str, data: dict):
    """Persist a user's economy data to disk."""
    with open(get_user_file(key), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def add_currency(key: str, amount=DEFAULT_CURRENCY_GIVE):
    data = load_economy(key)
    data["currency"] += amount
    save_economy(key, data)
    return data["currency"]

def remove_currency(key: str, amount=DEFAULT_CURRENCY_TAKE):
    data = load_economy(key)
    data["currency"] = max(0, data["currency"] - amount)
    save_economy(key, data)
    return data["currency"]

def get_balance(key: str):
    return load_economy(key)["currency"]

# —————— XP / Level Functions ——————

def add_xp(key: str, amount):
    """
    Award XP, handle level-ups, and reward currency on each new level.
    Returns (leveled_up: bool, new_level: int).
    """
    data = load_economy(key)
    data["xp"] += amount
    leveled_up = False

    while data["xp"] >= 100 * data["level"]:
        data["xp"] -= 100 * data["level"]
        data["level"] += 1

        # Reward = multiplier × new level
        reward = int(LEVEL_UP_REWARD_MULTIPLIER * data["level"])
        data["currency"] += reward

        leveled_up = True

    save_economy(key, data)
    return leveled_up, data["level"]

# —————— Game-specific Helpers ——————

def get_wordle_streak(key: str):
    return load_economy(key).get("wordle_streak", 0)

def set_wordle_streak(key: str, streak):
    data = load_economy(key)
    data["wordle_streak"] = streak
    save_economy(key, data)
    return streak

def get_connect4_streak(key: str):
    return load_economy(key).get("connect4_streak", 0)

def set_connect4_streak(key: str, streak):
    data = load_economy(key)
    data["connect4_streak"] = streak
    save_economy(key, data)
    return streak

# —————— Role-shop Helpers ——————

def add_role(key: str, role_name):
    data = load_economy(key)
    if role_name not in data["rolls"]:
        data["rolls"].append(role_name)
        save_economy(key, data)
        return True
    return False

def remove_role(key: str, role_name):
    data = load_economy(key)
    if role_name in data["rolls"]:
        data["rolls"].remove(role_name)
        save_economy(key, data)
        return True
    return False

def has_role(key: str, role_name):
    return role_name in load_economy(key).get("rolls", [])

def handle_roll_reaction(key: str, role_name):
    return remove_role(key, role_name) if has_role(key, role_name) else add_role(key, role_name)
