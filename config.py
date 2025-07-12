# WARNING: This file contains default configuration values.
#          Sensitive values should only be stored in .env!

import os
from dotenv import load_dotenv

# Load environment variables from .env file.
load_dotenv()

# Sensitive settings (Change these in the .env file only)
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")     # Pulled from .env file
OPENWEBUI_API_KEY = os.getenv("OPENWEBUI_API_KEY")     # Pulled from .env file
OPENWEBUI_API_URL = os.getenv("OPENWEBUI_API_URL")     # Pulled from .env file

# Non-sensitive settings (Additional bot settings that are okay to share)
BOT_NAME = "YOUR_BOTS_NAME"          # The name of your bot
BOT_VERSION = "YOUR_VERSION_NUMBER"  # The version of your bot
COMMAND_PREFIX = "YOUR_PREFIX"       # Change value if you want different prefix.
MODEL_NAME = "YOUR_LLM_MODEL_NAME"   # Set your model name here.

## XP Values
XP_PER_MESSAGE =  NUMBER_HERE                # XP gained from regular messages
XP_PER_REACTION = NUMBER_HERE                # XP gained from reacting to messages
XP_PER_COMMAND = NUMBER_HERE                 # XP gained from using Devros commands
LEVEL_UP_REWARD_MULTIPLIER = NUMBER_HERE     # Default value Level Up reward (Value * LVL Earned)

## Server Economy Settings
### Currency Values
ECONOMY_FOLDER = "data/economy_data"         # Folder where economy files are saved
CURRENCY_NAME = "CURRENCY_NAME"              # Name of your server's currency
CURRENCY_SYMBOL = "CURRENCY_SYMBOL"          # Symbol of your server's currency
DEFAULT_CURRENCY_GIVE = NUMBER_HERE          # Default value adding currency
DEFAULT_CURRENCY_TAKE = NUMBER_HERE          # Default value adding currency
GAME_WIN = NUMBER_HERE                       # Game win currency value
GAME_LOSE = NUMBER_HERE                      # Game lost currency value

### Stock Values (COMING SOON!!)

## Channel Specifications (Defined directly in config.py, not from .env)
WORDLE_CHANNEL = WORDLE_CHANNEL_ID                             # Set your Wordle Game Channel
INVITE_CHANNEL = INVITE_CHANNEL_ID                             # Set your Game Invite Channel ID
WELCOME_CHANNEL = WELCOME_CHANNEL_ID                           # Set your Welcome Channel ID
GOODBYE_CHANNEL = GOODBYE_CHANNEL_ID                           # Set your Goodbye Channel ID
BETTING_CHANNEL = BETTING_CHANNEL_ID                           # Set your Betting Channel ID
HELP_COMMAND_CHANNEL_CATEGORY = HELP_COMMAND_CATEGORY_ID       # Set your Help Commands Channel ID
ROLLS_CHANNEL = BETTING_CHANNEL_ID                             # Set Roll Selection Channel ID
