import os
import discord
from discord.ext import commands
from config import COMMAND_PREFIX, DISCORD_BOT_TOKEN

# Create intents object and enable the message content and reaction intents
intents = discord.Intents.default()
intents.message_content = True  # Enable the message content intent
intents.reactions = True  # Enable reaction intents
intents.members = True  # Enable member intents (for adding/removing roles)

# Create bot instance with the correct intents
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

# Load all cogs (commands) dynamically
async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and filename != "__init__.py":
            await bot.load_extension(f"cogs.{filename[:-3]}")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await load_cogs()
    print("Cogs Loaded Successfully!")

# Run the bot
bot.run(DISCORD_BOT_TOKEN)
