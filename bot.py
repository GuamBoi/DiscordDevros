import discord
from discord.ext import commands
import config
import os
from dotenv import load_dotenv

load_dotenv()

# Define bot with command prefix
bot = commands.Bot(command_prefix=config.PREFIX, intents=discord.Intents.all())

# Load cogs dynamically
def load_cogs():
    for filename in os.listdir("cogs"):
        if filename.endswith(".py") and filename != "__init__.py":
            bot.load_extension(f"cogs.{filename[:-3]}")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# Load cogs before running the bot
load_cogs()
bot.run(config.TOKEN)
