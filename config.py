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
COMMAND_PREFIX = "!"              # Change value if you want different prefix.
MODEL_NAME = "devros-mini"        # Set your model name here.
ECONOMY_FOLDER = "data/eco"       # Folder where economy files are saved

# Bot Info
BOT_NAME = "Devros"               # The name of your bot
BOT_VERSION = "2.1 Beta"          # The version of your bot

# Role Info
MODERATOR_ROLE_ID = 1035393475631394896      # Role ID for server mods

# XP Values
ENABLE_XP_SYSTEM = True           # Set to False to disable XP System
SHOW_LEVEL_UP_MESSAGES = True     # Set to False to disable level up messages
XP_NOTIFICATION_CHANNEL_ID = None  # Replace with your actual channel ID, or set to None to use current channel
XP_PER_MESSAGE =  1               # XP gained from regular messages
XP_PER_REACTION = 1               # XP gained from reacting to messages
XP_PER_COMMAND = 5                # XP gained from using Devros commands
LEVEL_UP_REWARD_MULTIPLIER = 100     # Default value Level Up reward (Value * LVL Earned)

# Server Economy Settings
## Currency Values
CURRENCY_NAME = "Devros Dolhairs"  # Name of your server's currency
CURRENCY_SYMBOL = "Đ"
DEFAULT_CURRENCY_GIVE = 100       # Default value adding currency (Also the amount players start with when their wallet is first generated)
DEFAULT_CURRENCY_TAKE = 100       # Default value removing currency
GAME_WIN = 50                     # Game won currency value
GAME_LOSE = 25                    # Game lost currency value

# Channel Specifications (Defined directly in config.py, not from .env)
## Game Channels
INVITE_CHANNEL = 1036762745527357450         # Set Game Invite Channel ID
WORDLE_CHANNEL = 1209772800492179526         # Set Wordle Game Channel
CONNECT4_CHANNEL = 1213909567965102111       # Set the Connect 4 Channel
BATTLESHIP_CHANNEL = 1354106419435278336     # Set the Battleship Channel

## Channels
WELCOME_CHANNEL = 1036760459161911366        # Set Welcome Channel ID
GOODBYE_CHANNEL = 1206374744719626361        # Set Goodbye Channel ID
HELP_COMMAND_CHANNEL_CATEGORY = 1036929287346999326
ROLLS_CHANNEL = 1036732354426843146          # Set Roll Selection Channel ID
BETTING_CHANNEL = 1351377151676518483        # Set Betting Channel ID
