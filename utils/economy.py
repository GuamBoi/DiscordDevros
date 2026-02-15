import os
import json
import time
import threading
from json import JSONDecodeError
from typing import Union, Optional
import discord
from config import (
    ECONOMY_FOLDER,
    DEFAULT_CURRENCY_GIVE,
    DEFAULT_CURRENCY_TAKE,
    LEVEL_UP_REWARD_MULTIPLIER
)

EconomyIdentity = Union[str, discord.abc.User]  # str = user_id, or a Member/User

# One lock per user_id to prevent concurrent writes in-process
_USER_LOCKS: dict[str, threading.Lock] = {}


def user_key(member: discord.abc.User) -> str:
    return str(member.id)


def _key_of(identity: EconomyIdentity) -> str:
    return identity if isinstance(identity, str) else user_key(identity)


def _member_of(identity: EconomyIdentity) -> Optional[discord.abc.User]:
    return identity if not isinstance(identity, str) else None


def _lock_for(user_id: str) -> threading.Lock:
    lock = _USER_LOCKS.get(user_id)
    if lock is None:
        lock = threading.Lock()
        _USER_LOCKS[user_id] = lock
    return lock


def get_user_file(identity: EconomyIdentity) -> str:
    key = _key_of(identity)
    return os.path.join(ECONOMY_FOLDER, f"{key}.json")


def _default_economy_schema(user_id: str) -> dict:
    return {
        "user_id": user_id,
        "username": None,
        "display_name": None,
        "currency": DEFAULT_CURRENCY_GIVE,
        "bet_lock": 0,
        "wordle_streak": 0,
        "connect4_streak": 0,
        "battleship_streak": 0,
        "xp": 0,
        "level": 1,
    }


def _coerce_schema(data: dict, user_id: str) -> tuple[dict, bool]:
    """
    Backfill missing keys and coerce basic types.
    Returns (data, changed_flag).
    """
    changed = False
    base = _default_economy_schema(user_id)

    if not isinstance(data, dict):
        data = {}
        changed = True

    for k, v in base.items():
        if k not in data:
            data[k] = v
            changed = True

    if data.get("user_id") != user_id:
        data["user_id"] = user_id
        changed = True

    def _coerce_int(field: str, default: int, min_value: Optional[int] = None):
        nonlocal changed
        try:
            val = int(data.get(field, default) or 0)
        except Exception:
            val = default
        if min_value is not None and val < min_value:
            val = min_value
        if data.get(field) != val:
            data[field] = val
            changed = True

    _coerce_int("currency", base["currency"], 0)
    _coerce_int("bet_lock", 0, 0)
    _coerce_int("wordle_streak", 0, 0)
    _coerce_int("connect4_streak", 0, 0)
    _coerce_int("battleship_streak", 0, 0)
    _coerce_int("xp", 0, 0)
    _coerce_int("level", 1, 1)

    for field in ("username", "display_name"):
        if data.get(field) is not None and not isinstance(data[field], str):
            data[field] = str(data[field])
            changed = True

    return data, changed


def load_economy(identity: EconomyIdentity) -> dict:
    os.makedirs(ECONOMY_FOLDER, exist_ok=True)

    user_id = _key_of(identity)
    member = _member_of(identity)
    path = get_user_file(user_id)

    with _lock_for(user_id):
        data = None
        changed = False

        if os.path.exists(path):
            try:
                if os.path.getsize(path) == 0:
                    raise JSONDecodeError("Empty economy file", "", 0)
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (JSONDecodeError, ValueError):
                try:
                    corrupt_path = f"{path}.corrupt.{int(time.time())}"
                    os.replace(path, corrupt_path)
                except Exception:
                    pass
                data = _default_economy_schema(user_id)
                changed = True
        else:
            data = _default_economy_schema(user_id)
            changed = True

        data, coerced_changed = _coerce_schema(data, user_id)
        changed = changed or coerced_changed

        if member is not None:
            new_username = getattr(member, "name", None)
            new_display = getattr(member, "display_name", None)
            if data.get("username") != new_username:
                data["username"] = new_username
                changed = True
            if data.get("display_name") != new_display:
                data["display_name"] = new_display
                changed = True

        if changed:
            save_economy(user_id, data)

        return data


def save_economy(identity: EconomyIdentity, data: dict) -> None:
    os.makedirs(ECONOMY_FOLDER, exist_ok=True)

    user_id = _key_of(identity)
    path = get_user_file(user_id)
    tmp_path = f"{path}.tmp"

    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())

    os.replace(tmp_path, path)


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
    data = load_economy(identity)
    return int(data.get("currency", 0) or 0)


def add_xp(identity: EconomyIdentity, amount: int):
    data = load_economy(identity)
    data["xp"] = int(data.get("xp", 0) or 0) + int(amount)
    data["level"] = max(1, int(data.get("level", 1) or 1))

    leveled_up = False
    while data["xp"] >= 100 * data["level"]:
        data["xp"] -= 100 * data["level"]
        data["level"] += 1

        reward = int(LEVEL_UP_REWARD_MULTIPLIER * data["level"])
        data["currency"] = int(data.get("currency", 0) or 0) + reward
        leveled_up = True

    save_economy(data["user_id"], data)
    return leveled_up, data["level"]
