import discord
from discord.ext import commands
import json
import os
import config

CONFIG_FILE = "config.json"

class ConfigManager(commands.Cog):
    """
    Cog allowing moderators to view and modify runtime configuration settings,
    with persistent saving/loading from a JSON file.
    """
    def __init__(self, bot):
        self.bot = bot
        self.editable = {
            'ENABLE_XP_SYSTEM': bool,
            'SHOW_LEVEL_UP_MESSAGES': bool,
            'XP_NOTIFICATION_CHANNEL_ID': int,
            'XP_PER_MESSAGE': int,
            'XP_PER_REACTION': int,
            'XP_PER_COMMAND': int,
            'LEVEL_UP_REWARD_MULTIPLIER': int,
            'DEFAULT_CURRENCY_GIVE': int,
            'DEFAULT_CURRENCY_TAKE': int,
            'GAME_WIN': int,
            'GAME_LOSE': int,
            'ENABLE_STOCK_SYSTEM': bool,
            'STOCK_NAME': str,
            'STOCK_TICKER': str,
            'BASE_DIVIDEND_VALUE': int,
            'DYNAMIC_DIVIDEND_YIELD': bool,
            'STOCK_NOTIFICATION_CHANNEL_ID': (int, type(None)),
            'COMMAND_PREFIX': str,
        }
        self.load_config()

    def cog_check(self, ctx):
        mod_role_id = config.MODERATOR_ROLE_ID
        return any(role.id == mod_role_id for role in ctx.author.roles)

    def load_config(self):
        """Load config values from JSON file and update config module."""
        if not os.path.isfile(CONFIG_FILE):
            return  # No config file yet, skip loading

        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[ConfigManager] Failed to load config.json: {e}")
            return

        # Override config.py attributes if present in JSON
        for key, val in data.items():
            if key in self.editable:
                setattr(config, key, val)

    def save_config(self):
        """Save current editable config values to JSON file."""
        data = {}
        for key in self.editable:
            val = getattr(config, key)
            # For types like None, json can handle it directly
            data[key] = val
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"[ConfigManager] Failed to save config.json: {e}")

    @commands.group(name='config', invoke_without_command=True)
    async def config(self, ctx):
        await ctx.send("Usage: `!config get <key>`, `!config set <key> <value>`, `!config list`")

    @config.command(name='get')
    async def config_get(self, ctx, key: str):
        key = key.upper()
        if key not in self.editable:
            return await ctx.send(f"❌ `{key}` is not an editable config key.")
        value = getattr(config, key)
        await ctx.send(f"🔍 `{key}` = `{value}`")

    @config.command(name='set')
    async def config_set(self, ctx, key: str, *, raw_value: str):
        key = key.upper()
        if key not in self.editable:
            return await ctx.send(f"❌ `{key}` is not an editable config key.")
        expected_type = self.editable[key]
        try:
            if expected_type is bool:
                val = raw_value.lower() in ('true', '1', 'yes', 'on')
            elif expected_type is int:
                val = int(raw_value)
            elif expected_type is str:
                val = raw_value
            elif isinstance(expected_type, tuple):
                if raw_value.lower() == 'none':
                    val = None
                else:
                    val = int(raw_value)
            else:
                return await ctx.send(f"Unsupported type for `{key}`.")
        except Exception as e:
            return await ctx.send(f"❌ Failed to cast value: {e}")
        setattr(config, key, val)
        self.save_config()
        await ctx.send(f"✅ `{key}` set to `{val}`")

    @config.command(name='list')
    async def config_list(self, ctx):
        lines = []
        for k in sorted(self.editable.keys()):
            val = getattr(config, k)
            lines.append(f"`{k}` = `{val}`")
        msg = "\n".join(lines)
        await ctx.send(f"**Editable Config Keys:**\n{msg}")

    @commands.command(name="setprefix")
    async def setprefix(self, ctx, new_prefix: str):
        setattr(config, "COMMAND_PREFIX", new_prefix)
        self.save_config()
        await ctx.send(f"✅ Command prefix updated to `{new_prefix}`")

async def setup(bot):
    await bot.add_cog(ConfigManager(bot))
