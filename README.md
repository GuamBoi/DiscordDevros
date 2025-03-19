# DiscordDevros

DiscordDevros is a Discord bot interconnected with an Open WebUI server to generate unique and more natural language responses. The code is structured in a modular format to allow for easy customization based on the needs of your server. The `cogs` folder contains the code for all commands available on the server. Each script is either an individual command, or a group of commands that function together to create a game or other feature. 

## Bot File Structure
```
DiscordDevros/         # Main Directory
│
├── cogs/                 # Folder for command files
│   ├── __init__.py          # Makes the cogs folder a package
│   ├── ask.py               # Ask your Pi LLM a question (Ai)
│   ├── bet.py               # Handles bets between 2 server members
│   ├── command_help.py      # Starts a chat to help users with commands (Ai)
│   ├── dice.py              # Allows users to roll diffrent DND dice
│   ├── invite.py            # Sends a game invite to the game being played
│   ├── leaderboard.py       # Allows Users to check the economy leaderboard
│   └── wordle.py            # Commands for starting / guessing in wordle (Ai)
│
├── data/                 # Folder for storing 
│   └── commands.json        # File for storing command descriptions
│
│
│
├── utils/                # Folder for utility script files
│   ├── __init__.py          # Makes the utils folder a package
│   ├── dictionary.py        # Loads and formats command information
│   ├── economy.py           # Handls the economy logic
│   ├── embed.py             # Handles the embed format for bot messages
│   └── llm_api.py           # Handles connection with Open WebUI's API
│
├── .env                     # Stores bot token, prefix, and API info
├── .gitignore               # Ignores sensitive files when cloned
├── README.md                # Code documentation (This File)
├── bot.py                   # Main bot file (loads commands dynamically)
├── config.py                # Cofiguration file for bot settings
└── requirements.txt         # Dependencies that need to be installed
```

## Features
- Uses cogs for modular command handling (add or remove scripts from the `cogs/` folder to customize the bot)
- Loads bot token and prefix from a `.env` file for security. (Sensitive info in this file is loaded into the `config.py` file)
- The `utils/` folder contains utility scripts. 
	- The `llm_api.py` file is used to easily integrate the Open WebUI API into any script with the `(Ai)` tag in the folder structure above.

## Installation

### 1. Clone the Repository
```sh
git clone https://github.com/GuamBoi/DiscordDevros.git
cd DiscordDevros
```

### 2. Set Up a Virtual Environment
Create a virtual environment to isolate the bot's dependencies:
```sh
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
Once the virtual environment is activated, install the required Python dependencies:
```sh
pip install -r requirements.txt
```

### 4. Setup Environment Variables and `config.py` file Variables
1. Create a `.env` file in the root directory and add your bot token and command prefix:
    ```bash
    nano .env
    ```

    ```
    DISCORD_BOT_TOKEN=YOUR_DISCORD_BOTTOKEN
    OPENWEBUI_API_URL=http://YOUR_PI_IP:PORT/api/chat/completions      # Change `YOUR_PI_IP` with the IP address of the raspberry Pi running your Open WebUI Server, and `PORT` with the port its running on.
    OPENWEBUI_API_KEY=YOUR_OPEN_WEBUI_API_KEY
    ```

2. Edit the `config.py` file to configure the bot to your server and liking:
    ```bash
    nano config.py
    ```

    ```python
    import os
    from dotenv import load_dotenv

    # Load environment variables from .env file.
    load_dotenv()

    # Sensitive settings (Change these in the .env file only)
    DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")     # Pulled from your .env file
    OPENWEBUI_API_KEY = os.getenv("OPENWEBUI_API_KEY")     # Pulled from your .env file
    OPENWEBUI_API_URL = os.getenv("OPENWEBUI_API_URL")     # Pulled from your .env file

    # Non-sensitive settings (Additional bot settings that are okay to share)
    COMMAND_PREFIX = "!"           # Change this value if you want a different prefix.
    MODEL_NAME = "YOUR_MODEL_NAME"     # Set your model name here.

    # Channel Specifications (Defined directly in config.py, not from .env)
    WORDLE_CHANNEL = YOUR_WORDLE_CHANNEL_ID                # Set your Wordle Game Channel
    ```

### 5. Run the Bot
After setting up the environment, run the bot:
```sh
python bot.py
```

### 5. Run the Bot
After setting up the environment, run the bot:
```sh
python bot.py
```

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
    async def hello(self, ctx, *, prompt: str = "Say Hello to the server and introduce yourself"):
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

## Removing the Bot
```bash
sudo chown -R $USER:$USER ~/DiscordDevros
rm -rf ~/DiscordDevros
```
