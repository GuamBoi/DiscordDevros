# About DiscordDevros

DiscordDevros is a Discord bot interconnected with an Open WebUI server to generate unique and more natural language responses. The code is structured in a modular format to allow for easy customization based on the needs of your server. The `cogs` folder contains the code for all commands available on the server. Each script is either an individual command, or a group of commands that function together to create a game or other feature. 

> [!info] Open WebUI Information
> This README does not include information on setting up Open WebUI. For information on setting up Open WebUI on your preferred OS, see the guides on my website below:
> 1. [Linux Guide](https://www.panoplylens.com/technology/hosting-a-local-llm-linux-recommendation/)
> 2. [Windows Guide](https://www.panoplylens.com/technology/hosting-a-local-llm-windows-recommendation/)


## File Structure with explanations:
```
DiscordDevros/         # Main Directory
│
├── cogs/                   # Folder for command files
│ ├── __init__.py             # Makes the cogs folder a package
│ ├── ask.py                  # Ask your Pi LLM a question (Ai)
│ ├── award.py                # Allows server mods to award currency
│ ├── balance.py              # Allows members to check their currency, XP, level, and streaks
│ ├── battleship.py           # Battleship game logic
│ ├── bet.py                  # Handles bets between 2 server members
│ ├── commands.ps             # Shows a list of commands
│ ├── config_manager.py       # Allows server mods to edit the bots config file with discord commands
│ ├── connect4.py             # Connect 4 game logic
│ ├── dice.py                 # Allows users to roll diffrent DND dice
│ ├── give.py                 # Allows other members to give their currency to another member
│ ├── leaderboard.py          # Allows Users to check the economy leaderboard
│ ├── server_customization.py # Command Logic for  
│ ├── wordle.py               # Commands for starting / guessing in wordle (Ai)
│ └── xp.px
│
├── data/                   # Folder for storing 
│ ├── economy/              # Default economy player file filder (Generated)
│ ├── commands.json           # File for storing command descriptions
│ ├── prompts.json            # File for configuring Ai Message
│ ├── rolls.json              # File for configuring server rolls
│ └── wordle_words.txt        # File that lists backup wordle words
│
│── utils/                  # Folder for utility script function files
│ ├── __init__.py             # Makes the utils folder a package
│ ├── dictionary.py           # Loads and formats command information
│ ├── economy.py              # Handls the economy logic
│ ├── embed.py                # Handles the embed format for bot messages
│ └── llm_api.py              # Handles connection with Open WebUI's API
│
├── .env                      # Stores bot token, prefix, and API info
├── .gitignore                # Ignores sensitive files when cloned
├── README.md                 # Code documentation (This File)
├── bot.py                    # Main bot file (loads commands dynamically)
├── config.py                 # Cofiguration file for bot settings
└── requirements.txt          # Dependencies that need to be installed
```

# Setting up your Discord Bot:

## Installation

### 1. Clone the Repository
- The commands below will:
	1. Install git if you don't have it already
	2. Clone [this GitHub repository](https://github.com/GuamBoi/DiscordDevros/tree/main).
	3. Put you in the DiscordDevros directory to run the next commands in

```sh
sudo apt install git -y
git clone https://github.com/GuamBoi/DiscordDevros.git
cd DiscordDevros
```

### 2. Set Up a Virtual Environment

- Create a virtual environment to isolate the bot's dependencies.
	- The following commands will:
		1. Install [python3-venv](https://docs.python.org/3/library/venv.html)
		2. Create a virtual environment
		3. Activate the created virtual environment

```sh
sudo apt-get install python3-venv -y
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

- Once the virtual environment is activated, install the required Python dependencies by running:

```sh
pip install -r requirements.txt
```

### 4. Setup Environment Variables
- Edit the `.env` file in the root directory with your bot token and Open WebUI API info by running:

```bash
nano .env
```

> Replace the placeholders you see below:
```
DISCORD_BOT_TOKEN=YOUR_DISCORD_BOT_TOKEN
OPENWEBUI_API_URL=http://RASPBERRY_PI_IP:PORT/api/chat/completions
OPENWEBUI_API_KEY=YOUR_OPENWEBUI_API_KEY
```

### 5. Edit the `config.py` File Variables
 - Edit the `config.py` file to configure the bot to your server by running:

```bash
nano config.py
```

> Make sure Channel IDs match your server and change any other variable you would like below:
```python
# WARNING: This file contains my default (DEVROS') configuration values.
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
DEFAULT_CURRENCY_GIVE = 100       # Default value adding currency
DEFAULT_CURRENCY_TAKE = 100       # Default value adding currency

## Game Values
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
```

### 6. Update the `rolls.json` File to Match Your Server
```json
# WARNING: This file is only a template for yo to use to match your configuration values to your discord server.

{
    "color": {
        "message": "Server Color Selection",
        "description": "Color Key:",
        "note": "Pick 1 color at a time.",
        "options": {
            "YOUR_ROLL_EMOJI": {"name": "`YOUR_ROLL_NAME`", "role_id": YOUR_ROLL_ID},
            "YOUR_ROLL_EMOJI": {"name": "`YOUR_ROLL_NAME`", "role_id": YOUR_ROLL_ID},
        }
    },
    "game": {
        "message": "Game Selection",
        "description": "Server Game Options:",
        "note": "Select all the games you want to be a part of!",
        "options": {
            "YOUR_ROLL_EMOJI": {"name": "`YOUR_ROLL_NAME`", "role_id": YOUR_ROLL_ID},
            "YOUR_ROLL_EMOJI": {"name": "`YOUR_ROLL_NAME`", "role_id": YOUR_ROLL_ID},
        }
    },
    "free_game": {
        "message": "Free Game and Update Channels",
        "description": "Channel Options:",
        "note": "Game update channel selection.",
        "options": {
            "YOUR_ROLL_EMOJI": {"name": "`YOUR_ROLL_NAME`", "role_id": YOUR_ROLL_ID},
            "YOUR_ROLL_EMOJI": {"name": "`YOUR_ROLL_NAME`", "role_id": YOUR_ROLL_ID}
        }
    }
}
```

### 7. Test the Bot

After setting up the environment, test the bot and try some of the commands after running the following command:

```sh
python bot.py
```

After you test everything, to ensure your Discord bot continues running after you close your SSH session, you can utilize the `nohup` command. This command allows processes to persist even after your PuTTY session is closed. 
- Close your current PuTTY instance and run the following commands after you log back in:

### 8. Run the Bot Using `nohup`

Enter the Bot Directory and activate the virtual environment again

```bash
cd DiscordDevros
source venv/bin/activate
```

To run your bot so that it continues operating after you disconnect from the SSH session, use the `nohup` command:

```bash
nohup python bot.py > bot_output.log 2>&1 &
```

In this command:
- `nohup` prevents the process from being terminated after the SSH session ends.
- `python bot.py` executes your bot script.
- `> bot_output.log` redirects the standard output to a log file named `bot_output.log`.
- `2>&1` ensures that both standard output and standard error are captured in the log file.
- `&` runs the process in the background, allowing you to continue using the terminal.

**2. Verify the Bot is Running**

To confirm that your bot is running in the background, you can check the list of running processes:

```bash
ps aux | grep bot.py
```

This command will display information about the running `bot.py` process.

**Example PID Output:**

```
USER    PID   %CPU  %MEM   VSZ   RSS   TTY     STAT   START   TIME  COMMAND
guam   3132   5.2   4.4  198864 41772  pts/0    Sl    01:45   0:01  python bot.py
```

### Stopping the Bot 
- If you need to stop the bot, first identify its Process ID (PID) using the`ps aux | grep bot.py` command, then terminate it:
	
```bash
kill PID
```
	
- **Viewing Logs**: To monitor the bot's output, you can view the log file:
    
```bash
tail -f bot_output.log
```
   
This command will display the log content in real-time.

### Removing the Bot

```bash
sudo chown -R $USER:$USER ~/DiscordDevros
rm -rf ~/DiscordDevros
```

___
## Adding Commands

To add a new command, create a `.py` file in the `cogs/` folder and follow this structure:
#### Example Command

```python
from discord.ext import commands

class Example(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def hello(self, ctx):
        await ctx.send("Hello, world!")

async def setup(bot):
    await bot.add_cog(Example(bot))
```

#### Example command to ping the Open WebUI Server with a prompt

```python
from discord.ext import commands
from utils.llm_api import query_llm  # Import the query_llm function

class Example(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def hello(self, ctx, *, prompt: str = "Say Hello to the server and inttroduce yourself"):
        """Command to ask the LLM with a customizable prompt."""
        try:
            # Ask the LLM with the user-defined prompt or default if not provided
            response = await query_llm(prompt)
            await ctx.send(response)  # Send the LLM's response to Discord
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

async def setup(bot):
    await bot.add_cog(Example(bot))
```

#### Adding Commands to the `commands.json` file

```json
{
        "Command_Name": "template",
        "Category": ["Example 1", "Example 2"],
        "Description": "Example template",
        "Example": "{COMMAND_PREFIX}template",
        "LLM_Context": "This is a template command for {BOT_NAME}."
    },
```
