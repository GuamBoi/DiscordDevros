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
    """Sanitize username for filesystem use."""
    return "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in username)

def get_user_file(username):
    """Get full path for a user's economy JSON file."""
    safe = sanitize_filename(username)
    return os.path.join(ECONOMY_FOLDER, f"{safe}.json")

def load_economy(username):
    """
    Load a user's economy data.
    - If file exists: load it (no back-fill).
    - If not: create with full default schema.
    """
    path = get_user_file(username)
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)

    # New user: create default data
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
    """Persist a user's economy data to disk."""
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

# —————— XP / Level Functions ——————

def add_xp(username, amount):
    """
    Award XP, handle level-ups, and reward currency on each new level.
    Returns (leveled_up: bool, new_level: int).
    """
    data = load_economy(username)
    data["xp"] += amount
    leveled_up = False

    while data["xp"] >= 100 * data["level"]:
        data["xp"] -= 100 * data["level"]
        data["level"] += 1
        data["currency"] += data["level"]
        leveled_up = True

    save_economy(username, data)
    return leveled_up, data["level"]

def get_xp_level(username):
    """Return (xp, level)."""
    d = load_economy(username)
    return d.get("xp", 0), d.get("level", 1)

# —————— Game‑specific Helpers ——————

def get_wordle_streak(username):
    return load_economy(username).get("wordle_streak", 0)

def set_wordle_streak(username, streak):
    data = load_economy(username)
    data["wordle_streak"] = streak
    save_economy(username, data)
    return streak

def get_connect4_streak(username):
    return load_economy(username).get("connect4_streak", 0)

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
    return role_name in load_economy(username).get("rolls", [])

def handle_roll_reaction(username, role_name):
    return remove_role(username, role_name) if has_role(username, role_name) else add_role(username, role_name)
