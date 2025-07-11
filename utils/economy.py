import os
import json
from config import (
    ECONOMY_FOLDER,
    DEFAULT_CURRENCY_GIVE,
    DEFAULT_CURRENCY_TAKE,
    CURRENCY_NAME,
    GAME_WIN
)

# Ensure the economy folder exists
if not os.path.exists(ECONOMY_FOLDER):
    os.makedirs(ECONOMY_FOLDER)

def sanitize_filename(username):
    """Ensure the filename is safe by removing special characters."""
    return "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in username)

def get_user_file(username):
    """Return the full path of the user's economy file."""
    safe = sanitize_filename(username)
    return os.path.join(ECONOMY_FOLDER, f"{safe}.json")

def load_economy(username):
    """Load or initialize a user's economy data."""
    path = get_user_file(username)
    if os.path.exists(path):
        with open(path, 'r') as f:
            data = json.load(f)
        # Back‑fill missing keys (including new XP/level)
        for key, default in {
            "bet_lock": 0,
            "wordle_streak": 0,
            "connect4_streak": 0,
            "rolls": [],
            "currency": DEFAULT_CURRENCY_GIVE,
            "xp": 0,
            "level": 1
        }.items():
            if key not in data:
                data[key] = default
        save_economy(username, data)
        return data

    # New user: create with defaults
    data = {
        "username": username,
        "currency": DEFAULT_CURRENCY_GIVE,
        "bet_lock": 0,
        "wordle_streak": 0,
        "connect4_streak": 0,
        "rolls": [],
        "xp": 0,
        "level": 1
    }
    save_economy(username, data)
    return data

def save_economy(username, data):
    """Persist a user's economy data."""
    with open(get_user_file(username), 'w') as f:
        json.dump(data, f, indent=4)

def add_currency(username, amount=DEFAULT_CURRENCY_GIVE):
    data = load_economy(username)
    data["currency"] += amount
    save_economy(username, data)
    return data["currency"]

def remove_currency(username, amount=DEFAULT_CURRENCY_TAKE):
    data = load_economy(username)
    data["currency"] = max(0, data["currency"] - amount)
    save_economy(username, data)
    return data["currency"]

def get_balance(username):
    return load_economy(username)["currency"]

# —————— New XP / Level Functions ——————

def add_xp(username, amount):
    """
    Award XP to a user, handle level‑ups, and pay out level reward.
    Returns (leveled_up: bool, new_level: int).
    """
    data = load_economy(username)
    data["xp"] += amount
    leveled_up = False

    # While enough XP to level
    while data["xp"] >= 100 * data["level"]:
        data["xp"] -= 100 * data["level"]
        data["level"] += 1
        # Reward = new level in currency
        data["currency"] += data["level"]
        leveled_up = True

    save_economy(username, data)
    return leveled_up, data["level"]

def get_xp_level(username):
    """Retrieve current XP and level."""
    data = load_economy(username)
    return data["xp"], data["level"]

# —————— Game‑specific Helpers ——————

def get_wordle_streak(username):
    return load_economy(username)["wordle_streak"]

def set_wordle_streak(username, streak):
    data = load_economy(username)
    data["wordle_streak"] = streak
    save_economy(username, data)
    return streak

def get_connect4_streak(username):
    return load_economy(username)["connect4_streak"]

def set_connect4_streak(username, streak):
    data = load_economy(username)
    data["connect4_streak"] = streak
    save_economy(username, data)
    return streak

# —————— Role‑shop Helpers ——————

def add_role(username, role_name):
    data = load_economy(username)
    if role_name not in data["rolls"]:
        data["rolls"].append(role_name)
        save_economy(username, data)
        return True
    return False

def remove_role(username, role_name):
    data = load_economy(username)
    if role_name in data["rolls"]:
        data["rolls"].remove(role_name)
        save_economy(username, data)
        return True
    return False

def has_role(username, role_name):
    return role_name in load_economy(username)["rolls"]

def handle_roll_reaction(username, role_name):
    return remove_role(username, role_name) if has_role(username, role_name) else add_role(username, role_name)
