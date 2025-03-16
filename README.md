
# DiscordDevros

A Discord bot structured with a modular command system using cogs.

## Bot File Structure
```
DiscordDevros/
│── bot.py                  # Main bot file (loads commands dynamically)
│── config.py               # Loads API keys and settings from .env
│── .env                    # Stores bot token, prefix, and API info
│── utils/
│   ├── llm_api.py          # Handles communication with the LLM API
│── cogs/                   # Folder for command files
│   ├── __init__.py         # Makes cogs a package
│   ├── get_word.py         # Command for getting a random word
│── requirements.txt        # Dependencies
│── README.md               # Documentation
```

## Features
- Uses cogs for modular command handling
- Loads bot token and prefix from a `.env` file for security
- Easy expansion by adding new command files in the `cogs/` folder

## Installation

### 1. Clone the Repository
```sh
git clone git@github.com:GuamBoi/DiscordDevros.git
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

### 4. Setup Environment Variables
Create a `.env` file in the root directory and add your bot token and command prefix:
```bash
nano .env
```

```
DISCORD_BOT_TOKEN=YOUR_DISCORD_BOT_TOKEN
OPENWEBUI_API_URL=http://YOUR_PI_IP_ADDRESS:PORT/api/chat/completions
OPENWEBUI_API_KEY=YOUR_OPEN_WEBUI_API_KEY
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
