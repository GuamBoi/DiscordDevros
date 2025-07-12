import os
import discord
from discord.ext import commands
from config import COMMAND_PREFIX, DISCORD_BOT_TOKEN

# Create intents object and enable the message content and reaction intents
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True

# Create bot instance with the correct intents
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

# Load all cogs (commands) dynamically with debug output
async def load_cogs():
    for filename in os.listdir("./cogs"):
        # Skip non-.py files and __init__.py
        if not filename.endswith(".py") or filename == "__init__.py":
            continue

        module_name = f"cogs.{filename[:-3]}"
        try:
            print(f"→ Loading extension: {module_name}")
            await bot.load_extension(module_name)
            print(f"✅ Successfully loaded {module_name}")
        except Exception as e:
            print(f"❌ Failed to load {module_name}: {e.__class__.__name__}: {e}")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    await load_cogs()
    print("All cogs loaded (or attempted).")
    
    # Set custom bot status to suggest using the commands
    activity = discord.Activity(
        type=discord.ActivityType.listening,
        name=f"{COMMAND_PREFIX}commands for a list of commands"
    )
    await bot.change_presence(activity=activity)

# Start the bot
bot.run(DISCORD_BOT_TOKEN)
