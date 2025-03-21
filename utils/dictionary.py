import os
import json
from config import BOT_NAME, COMMAND_PREFIX, HELP_COMMAND_CHANNEL_CATEGORY

# Path to the commands JSON file
COMMANDS_JSON_PATH = os.path.join("data", "commands.json")

def replace_placeholders(text, config_vars):
    """Helper function to replace placeholders in text using provided config variables."""
    if isinstance(text, str):
        for var_name, var_value in config_vars.items():
            placeholder = f"{{{var_name}}}"
            text = text.replace(placeholder, str(var_value))
    return text

def load_commands_data():
    """Load the commands JSON file and replace any placeholders using config.py values."""
    try:
        with open(COMMANDS_JSON_PATH, "r") as f:
            data = json.load(f)
        
        # Prepare the config variables for replacement
        config_vars = {
            "BOT_NAME": BOT_NAME,
            "COMMAND_PREFIX": COMMAND_PREFIX,
            "HELP_COMMAND_CHANNEL_CATEGORY": HELP_COMMAND_CHANNEL_CATEGORY
        }

        # Perform the placeholder replacement
        for cmd in data:
            for key in ["Description", "LLM_Context"]:
                if key in cmd and isinstance(cmd[key], str):
                    cmd[key] = replace_placeholders(cmd[key], config_vars)

        return data
    except Exception as e:
        print(f"Error loading commands JSON: {e}")
        return None

def get_command_info(command_name):
    """Retrieve information about a specific command from commands.json."""
    commands_data = load_commands_data()
    if not commands_data:
        return None

    # Find the command with the given name (case-insensitive)
    command = next(
        (cmd for cmd in commands_data if cmd.get("Command_Name", "").lower() == command_name.lower()), 
        None
    )

    return command
