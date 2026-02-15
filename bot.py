import os
import discord
from discord.ext import commands
from config import COMMAND_PREFIX, DISCORD_BOT_TOKEN

# Create intents object and enable the message content and reaction intents
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True

class DevrosBot(commands.Bot):
    async def setup_hook(self):
        # Load all cogs (commands) ONCE at startup (setup_hook is one-time per process)
        for filename in os.listdir("./cogs"):
            if not filename.endswith(".py") or filename == "__init__.py":
                continue

            module_name = f"cogs.{filename[:-3]}"

            # Prevent accidental double-loads (e.g., if called again)
            if module_name in self.extensions:
                continue

            try:
                print(f"→ Loading extension: {module_name}")
                await self.load_extension(module_name)
                print(f"✅ Successfully loaded {module_name}")
            except Exception as e:
                print(f"❌ Failed to load {module_name}: {e.__class__.__name__}: {e}")

        print("All cogs loaded (or attempted).")

# Create bot instance with the correct intents
bot = DevrosBot(command_prefix=COMMAND_PREFIX, intents=intents)

@bot.event
async def on_ready():
    # on_ready can fire multiple times; keep it for logging/presence only
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

    activity = discord.Activity(
        type=discord.ActivityType.listening,
        name=f"{COMMAND_PREFIX}commands for a list of commands"
    )
    await bot.change_presence(activity=activity)

# Start the bot
bot.run(DISCORD_BOT_TOKEN)
