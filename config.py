import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Fetch bot settings
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!")

# Fetch OpenWebUI API settings
OPENWEBUI_API_URL = os.getenv("OPENWEBUI_API_URL")
OPENWEBUI_API_KEY = os.getenv("OPENWEBUI_API_KEY")
