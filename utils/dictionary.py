import os
import json
from config import BOT_NAME

# Path to the commands JSON file
COMMANDS_JSON_PATH = os.path.join("data", "commands.json")

def load_commands_data():
    """Load the commands JSON file and replace any placeholders using config.py values."""
    try:
        with open(COMMANDS_JSON_PATH, "r") as f:
            data = json.load(f)
        
        # Convert config variables to a dictionary
        from config import COMMAND_PREFIX, HELP_COMMAND_CHANNEL_CATEGORY
        config_vars = {k: v for k, v in vars().items() if not k.startswith("__") and not callable(v)}

        # Perform the placeholder replacement
        for cmd in data:
            for key in ["Description", "LLM_Context"]:
                if key in cmd and isinstance(cmd[key], str):
                    for var_name, var_value in config_vars.items():
                        placeholder = f"{{{var_name}}}"
                        cmd[key] = cmd[key].replace(placeholder, str(var_value))

        return data
    except Exception as e:
        print(f"Error loading commands JSON: {e}")
        return None

def get_command_info(command_name):
    """Retrieve information about a specific command from commands.json."""
    commands_data = load_commands_data()
    if not commands_data:
        return None

    return next(
        (cmd for cmd in commands_data if cmd.get("Command_Name", "").lower() == command_name.lower()),
        None
    )
