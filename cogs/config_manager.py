import discord
from discord.ext import commands
import config

class ConfigManager(commands.Cog):
    """
    Cog allowing moderators to view and modify runtime configuration settings.
    """
    def __init__(self, bot):
        self.bot = bot
        # Gather editable config keys and their types
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
        }

    def cog_check(self, ctx):
        # Only allow moderators to use these commands
        mod_role_id = config.MODERATOR_ROLE_ID
        return any(role.id == mod_role_id for role in ctx.author.roles)

    @commands.group(name='config', invoke_without_command=True)
    async def config(self, ctx):
        """View or edit bot configuration. Use subcommands `get`, `set`, `list`"""
        await ctx.send("Usage: `!config get <key>`, `!config set <key> <value>`, `!config list`")

    @config.command(name='get')
    async def config_get(self, ctx, key: str):
        """Get the current value of a config key"""
        key = key.upper()
        if key not in self.editable:
            return await ctx.send(f"❌ `{key}` is not an editable config key.")
        value = getattr(config, key)
        await ctx.send(f"🔍 `{key}` = `{value}`")

    @config.command(name='set')
    async def config_set(self, ctx, key: str, *, raw_value: str):
        """Set a new value for a config key"""
        key = key.upper()
        if key not in self.editable:
            return await ctx.send(f"❌ `{key}` is not an editable config key.")
        expected_type = self.editable[key]
        try:
            # Cast raw_value into expected_type
            if expected_type is bool:
                val = raw_value.lower() in ('true', '1', 'yes', 'on')
            elif expected_type is int:
                val = int(raw_value)
            elif expected_type is str:
                val = raw_value
            elif isinstance(expected_type, tuple):  # e.g. (int, NoneType)
                if raw_value.lower() == 'none':
                    val = None
                else:
                    val = int(raw_value)
            else:
                return await ctx.send(f"Unsupported type for `{key}`.")
        except Exception as e:
            return await ctx.send(f"❌ Failed to cast value: {e}")
        setattr(config, key, val)
        await ctx.send(f"✅ `{key}` set to `{val}`")

    @config.command(name='list')
    async def config_list(self, ctx):
        """List all editable config keys and their current values"""
        lines = []
        for k in sorted(self.editable.keys()):
            val = getattr(config, k)
            lines.append(f"`{k}` = `{val}`")
        msg = "\n".join(lines)
        await ctx.send(f"**Editable Config Keys:**\n{msg}")

async def setup(bot):
    await bot.add_cog(ConfigManager(bot))
