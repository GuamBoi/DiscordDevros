import os
from dotenv import load_dotenv

# Load environment variables from .env file.
load_dotenv()

# Sensitive settings (Change these in the .env file only)
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")        # Pulled from your .env file
OPENWEBUI_API_KEY = os.getenv("OPENWEBUI_API_KEY")        # Pulled from your .env file
OPENWEBUI_API_URL = os.getenv("OPENWEBUI_API_URL")        # Pulled from your .env file

# Non-sensitive settings (Additional bot settings that are okay to share)
COMMAND_PREFIX = "!"                                      # Change this value if you want a different prefix.
MODEL_NAME = "YOUR_MODEL_NAME"                            # Set your model name here.

# Channel Specifications
WORDLE_CHANNEL = YOUR_CHANNEL_ID                          # Change to your Wordle Channels ID
