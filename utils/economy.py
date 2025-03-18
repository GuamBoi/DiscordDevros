import os
import json
from config import ECONOMY_FOLDER, DEFAULT_CURRENCY_GIVE, DEFAULT_CURRENCY_TAKE, CURRENCY_NAME

# Ensure the economy folder exists
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
            return json.load(f)
    else:
        # Create a new economy file with default values
        data = {
            "username": username,
            "currency": DEFAULT_CURRENCY_GIVE
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
    data["currency"] = max(0, data["currency"] - amount)  # Prevent negative values
    save_economy(username, data)
    return data["currency"]

def get_balance(username):
    """Retrieve the current balance for a user."""
    return load_economy(username)["currency"]

def get_currency_name():
    """Retrieve the configured currency name."""
    return CURRENCY_NAME
