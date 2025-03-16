
# DiscordDevros

A Discord bot structured with a modular command system using cogs.

## Bot File Structure
```
DiscordDevros/
├── cogs/                   # Folder for command files
│   ├── __init__.py         # Makes cogs a package
│   ├── ask.py              # Ask your Pi LLM a question (Ai)
│   └── wordle.py           # Commands for starting / guessing in wordle (Ai)
│
├── utils/
│   └── llm_api.py          # Handles connection with Open WebUI's API
│
├── .env                    # Stores bot token, prefix, and API info
├── .gitignore
├── README.md               # Documentation
├── bot.py                  # Main bot file (loads commands dynamically)
├── config.py               # Loads API keys and settings from .env
└── requirements.txt        # Dependencies
```

## Features
- Uses cogs for modular command handling
- Loads bot token and prefix from a `.env` file for security
- Easy expansion by adding new command files in the `cogs/` folder

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

## Adding Commands
To add a new command, create a `.py` file in the `cogs/` folder and follow this structure:

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

## Removing the Bot
```bash
sudo chown -R $USER:$USER ~/DiscordDevros
rm -rf ~/DiscordDevros
```

## Notes
- Ensure your `.env` file is not shared or pushed to GitHub to keep your bot token secure.
- You can change the bot’s prefix in the `.env` file by modifying `COMMAND_PREFIX=your_prefix_here`.
