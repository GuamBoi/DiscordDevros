import os
import discord
from discord.ext import commands
from config import COMMAND_PREFIX, DISCORD_BOT_TOKEN

intents = discord.Intents.default()
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
