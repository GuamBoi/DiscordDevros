# DiscordDevros
An Open WebUI Server intergrated with a Discord bot for more natural responces

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

### 2. Install Dependencies
```sh
pip install -r requirements.txt
```

### 3. Setup Environment Variables
Create a `.env` file in the root directory and add your bot token and command prefix:
```
DISCORD_BOT_TOKEN=your_token_here
COMMAND_PREFIX=!
```

### 4. Run the Bot
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

## Bot File Structure
```
GuamsServerBot/
│── bot.py                  # Main bot file (entry point)
│── config.py               # Configuration file (loads environment variables)
│── .env                    # Stores bot token and command prefix (not committed to Git)
│── cogs/                   # Folder for command files
│   ├── __init__.py         # Makes cogs a package
│   ├── example.py          # Example command file
│── requirements.txt        # Dependencies
│── README.md               # Project documentation
```

## Notes
- Ensure your `.env` file is not shared or pushed to GitHub to keep your bot token secure.
- You can change the bot’s prefix in the `.env` file by modifying `COMMAND_PREFIX=your_prefix_here`.
