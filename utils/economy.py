import os
import json
from config import ECONOMY_FOLDER, DEFAULT_CURRENCY_GIVE, DEFAULT_CURRENCY_TAKE, CURRENCY_NAME, GAME_WIN

# Ensure the economy folder exists inside the 'data' folder
if not os.path.exists(ECONOMY_FOLDER):
    os.makedirs(ECONOMY_FOLDER)

def sanitize_filename(username):
    """Ensure the filename is safe by removing special characters."""
    return "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in username)

def get_user_file(username):
    """Return the full path of the user's economy file based on their username."""
    safe_username = sanitize_filename(username)
    return os.path.join(ECONOMY_FOLDER, f"{safe_username}.json")

def load_economy(username):
    """Load a user's economy data, or create a new file if none exists."""
    user_file = get_user_file(username)

    if os.path.exists(user_file):
        with open(user_file, 'r') as f:
            data = json.load(f)
        
        # Check and set missing keys
        if "bet_lock" not in data:
            data["bet_lock"] = 0
        if "wordle_streak" not in data:
            data["wordle_streak"] = 0
        if "rolls" not in data:
            data["rolls"] = []
        if "currency" not in data:
            data["currency"] = DEFAULT_CURRENCY_GIVE

        save_economy(username, data)
        return data
    else:
        # Create a new economy file with default values
        data = {
            "username": username,
            "currency": DEFAULT_CURRENCY_GIVE,
            "bet_lock": 0,
            "wordle_streak": 0,
            "rolls": []
        }
        save_economy(username, data)
        return data

def save_economy(username, data):
    """Save a user's economy data."""
    user_file = get_user_file(username)
    with open(user_file, 'w') as f:
        json.dump(data, f, indent=4)

def add_currency(username, amount=DEFAULT_CURRENCY_GIVE):
    """Add currency to a user's economy."""
    data = load_economy(username)
    data["currency"] += amount
    save_economy(username, data)
    return data["currency"]

def remove_currency(username, amount=DEFAULT_CURRENCY_TAKE):
    """Remove currency from a user's economy."""
    data = load_economy(username)
    data["currency"] = max(0, data["currency"] - amount)
    save_economy(username, data)
    return data["currency"]

def get_balance(username):
    """Retrieve the current balance for a user."""
    return load_economy(username)["currency"]

def get_currency_name():
    """Retrieve the configured currency name."""
    return CURRENCY_NAME

def get_wordle_streak(username):
    """Retrieve the current Wordle streak for a user."""
    return load_economy(username)["wordle_streak"]

def set_wordle_streak(username, streak):
    """Set the Wordle streak for a user."""
    data = load_economy(username)
    data["wordle_streak"] = streak
    save_economy(username, data)
    return streak

def add_role(username, role_name):
    """Add a role to the user's rolls list."""
    data = load_economy(username)
    if role_name not in data["rolls"]:
        data["rolls"].append(role_name)
        save_economy(username, data)
        return True
    return False

def remove_role(username, role_name):
    """Remove a role from the user's rolls list."""
    data = load_economy(username)
    if role_name in data["rolls"]:
        data["rolls"].remove(role_name)
        save_economy(username, data)
        return True
    return False

def has_role(username, role_name):
    """Check if a user already has the specified role."""
    data = load_economy(username)
    return role_name in data["rolls"]

def handle_roll_reaction(username, role_name):
    """Handle reactions for role management."""
    if has_role(username, role_name):
        return remove_role(username, role_name)
    else:
        return add_role(username, role_name)
