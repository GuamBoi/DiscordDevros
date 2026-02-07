import os
import json
from typing import Union, Optional

import discord
from config import (
    ECONOMY_FOLDER,
    DEFAULT_CURRENCY_GIVE,
    DEFAULT_CURRENCY_TAKE,
    LEVEL_UP_REWARD_MULTIPLIER
)

EconomyIdentity = Union[str, discord.abc.User]  # str = user_id, or a Member/User

def user_key(member: discord.abc.User) -> str:
    """Centralized economy identity. Uses Discord user ID."""
    return str(member.id)

if not os.path.exists(ECONOMY_FOLDER):
    os.makedirs(ECONOMY_FOLDER)

def _key_of(identity: EconomyIdentity) -> str:
    return identity if isinstance(identity, str) else user_key(identity)

def _member_of(identity: EconomyIdentity) -> Optional[discord.abc.User]:
    return identity if not isinstance(identity, str) else None

def get_user_file(identity: EconomyIdentity) -> str:
    key = _key_of(identity)
    return os.path.join(ECONOMY_FOLDER, f"{key}.json")

def load_economy(identity: EconomyIdentity) -> dict:
    """
    Load a user's economy data.
    If identity is a Member/User, refreshes username/display_name automatically.
    """
    key = _key_of(identity)
    member = _member_of(identity)

    path = get_user_file(key)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
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

    # Always ensure canonical ID
    data["user_id"] = key

    # Auto-refresh labels when we have a member object
    if member is not None:
        data["username"] = getattr(member, "name", None)
        data["display_name"] = getattr(member, "display_name", None)

    save_economy(key, data)
    return data

def save_economy(identity: EconomyIdentity, data: dict) -> None:
    key = _key_of(identity)
    with open(get_user_file(key), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def add_currency(identity: EconomyIdentity, amount=DEFAULT_CURRENCY_GIVE) -> int:
    data = load_economy(identity)
    data["currency"] = int(data.get("currency", 0) or 0) + int(amount)
    save_economy(data["user_id"], data)
    return data["currency"]

def remove_currency(identity: EconomyIdentity, amount=DEFAULT_CURRENCY_TAKE) -> int:
    data = load_economy(identity)
    current = int(data.get("currency", 0) or 0)
    data["currency"] = max(0, current - int(amount))
    save_economy(data["user_id"], data)
    return data["currency"]

def get_balance(identity: EconomyIdentity) -> int:
    return int(load_economy(identity).get("currency", 0) or 0)

def add_xp(identity: EconomyIdentity, amount: int):
    data = load_economy(identity)
    data["xp"] = int(data.get("xp", 0) or 0) + int(amount)
    data["level"] = int(data.get("level", 1) or 1)

    leveled_up = False
    while data["xp"] >= 100 * data["level"]:
        data["xp"] -= 100 * data["level"]
        data["level"] += 1

        reward = int(LEVEL_UP_REWARD_MULTIPLIER * data["level"])
        data["currency"] = int(data.get("currency", 0) or 0) + reward
        leveled_up = True

    save_economy(data["user_id"], data)
    return leveled_up, data["level"]
