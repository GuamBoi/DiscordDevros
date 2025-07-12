import os
import json
from config import COMMAND_PREFIX  # to clean placeholder spacing if needed

# Path to the commands JSON file
COMMANDS_JSON_PATH = os.path.join("data", "commands.json")

def replace_placeholders(text, config_vars):
    """Helper function to replace placeholders in text using provided config variables."""
    if isinstance(text, str):
        for var_name, var_value in config_vars.items():
            placeholder = f"{{{var_name}}}"
            text = text.replace(placeholder, f"{var_value}")
        # Normalize spaces
        text = ' '.join(text.split())
        # Fix spacing after prefix or mentions
        text = text.replace(f"{COMMAND_PREFIX} ", COMMAND_PREFIX)
        text = text.replace("@ ", "@")
    return text

def load_commands_data():
    """Load the commands JSON file and replace placeholders using config.py values."""
    try:
        with open(COMMANDS_JSON_PATH, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading commands JSON: {e}")
        return []

    # Build a dict of config vars excluding sensitive ones
    from config import __dict__ as cfg
    config_vars = {
        k: v for k, v in cfg.items()
        if k.isupper() and k not in {
            "DISCORD_BOT_TOKEN", "OPENWEBUI_API_KEY", "OPENWEBUI_API_URL"
        }
    }

    # Replace placeholders in each command entry
    for cmd in data:
        for key in ("Description", "LLM_Context", "Example"):
            if key in cmd and isinstance(cmd[key], str):
                cmd[key] = replace_placeholders(cmd[key], config_vars)

    return data

def get_member_commands():
    """Return list of commands with Category 'member'."""
    return [
        cmd for cmd in load_commands_data()
        if cmd.get("Category", "member").lower() == "member"
    ]

def get_moderator_commands():
    """Return list of commands with Category 'moderator'."""
    return [
        cmd for cmd in load_commands_data()
        if cmd.get("Category", "").lower() == "moderator"
    ]

def get_command_info(command_name):
    """Retrieve information about a specific command from commands.json."""
    commands_data = load_commands_data()
    return next(
        (cmd for cmd in commands_data
         if cmd.get("Command_Name", "").lower() == command_name.lower()),
        None
    )
