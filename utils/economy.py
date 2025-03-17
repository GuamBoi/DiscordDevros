import os
import json
from config import ECONOMY_FOLDER, DEFAULT_CURRENCY_GIVE, DEFAULT_CURRENCY_TAKE, CURRENCY_NAME

# Ensure the economy folder exists
if not os.path.exists(ECONOMY_FOLDER):
    os.makedirs(ECONOMY_FOLDER)

def get_user_file(user_id):
    return os.path.join(ECONOMY_FOLDER, f"{user_id}.json")

def load_economy(user_id):
    """Load a user's economy data, or create a new file if none exists."""
    user_file = get_user_file(user_id)
    if os.path.exists(user_file):
        with open(user_file, 'r') as f:
            return json.load(f)
    else:
        # Create a new economy file with default values
        data = {"currency": DEFAULT_CURRENCY_GIVE}
        save_economy(user_id, data)
        return data

def save_economy(user_id, data):
    """Save a user's economy data."""
    user_file = get_user_file(user_id)
    with open(user_file, 'w') as f:
        json.dump(data, f, indent=4)

def add_currency(user_id, amount=DEFAULT_CURRENCY_GIVE):
    """Add currency to a user's economy."""
    data = load_economy(user_id)
    data["currency"] += amount
    save_economy(user_id, data)
    return data["currency"]

def remove_currency(user_id, amount=DEFAULT_CURRENCY_TAKE):
    """Remove currency from a user's economy."""
    data = load_economy(user_id)
    data["currency"] = max(0, data["currency"] - amount)  # Prevent negative values
    save_economy(user_id, data)
    return data["currency"]

def get_balance(user_id):
    """Retrieve the current balance for a user."""
    return load_economy(user_id)["currency"]

def get_currency_name():
    """Retrieve the configured currency name."""
    return CURRENCY_NAME
