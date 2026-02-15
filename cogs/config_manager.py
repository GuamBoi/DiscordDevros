import discord
from discord.ext import commands
import json
import os
import config as bot_config

from utils.embed import create_embed  # async in your project

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "..", "config.json")
CONFIG_FILE = os.path.abspath(CONFIG_FILE)

TRUE_VALUES = {"true", "1", "yes", "on"}
FALSE_VALUES = {"false", "0", "no", "off"}

def _type_label(t):
    if t is bool:
        return "bool"
    if t is int:
        return "int"
    if t is str:
        return "str"
    return str(t)

def _normalize_key(s: str) -> str:
    return s.strip().upper()

def _parse_shop_key(key: str):
    """
    Accepts:
      SHOP_FRAME_PRICES.red
      SHOP_COLOR_PRICES.blue
    Returns: ("SHOP_FRAME_PRICES", "red") or (None, None)
    """
    k = key.strip()
    if "." not in k:
        return None, None
    left, right = k.split(".", 1)
    left = left.strip().upper()
    right = right.strip().lower()
    if left in ("SHOP_FRAME_PRICES", "SHOP_COLOR_PRICES") and right:
        return left, right
    return None, None

class ConfigManager(commands.Cog):
    """
    Moderators can view/modify selected runtime config settings,
    persisted in config.json and applied to config.py module attributes.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        # Editable module attributes
        self.editable = {
            "ENABLE_XP_SYSTEM": bool,
            "SHOW_LEVEL_UP_MESSAGES": bool,
            "XP_PER_MESSAGE": int,
            "XP_PER_REACTION": int,
            "XP_PER_COMMAND": int,
            "LEVEL_UP_REWARD_MULTIPLIER": int,

            "CURRENCY_NAME": str,
            "CURRENCY_SYMBOL": str,
            "DEFAULT_CURRENCY_GIVE": int,
            "DEFAULT_CURRENCY_TAKE": int,
            "GAME_WIN": int,
            "GAME_LOSE": int,
        }

        # Editable dicts (nested)
        self.shop_dicts = ("SHOP_FRAME_PRICES", "SHOP_COLOR_PRICES")

        self._ensure_config_defaults()
        self.load_config()

    def cog_check(self, ctx: commands.Context):
        if ctx.guild is None or not isinstance(ctx.author, discord.Member):
            return False
        mod_role_id = bot_config.MODERATOR_ROLE_ID
        return any(role.id == mod_role_id for role in ctx.author.roles)

    def _ensure_config_defaults(self):
        # Ensure flat keys exist (don’t crash)
        for key, t in self.editable.items():
            if not hasattr(bot_config, key):
                setattr(bot_config, key, False if t is bool else 0 if t is int else "")

        # Ensure shop dicts exist
        for dkey in self.shop_dicts:
            if not hasattr(bot_config, dkey) or not isinstance(getattr(bot_config, dkey), dict):
                setattr(bot_config, dkey, {})

    async def _make_embed(self, ctx: commands.Context, title: str, description: str, **kwargs) -> discord.Embed:
        """
        Your create_embed is async, so we MUST await it.
        If your create_embed signature differs, adjust here only.
        """
        try:
            return await create_embed(ctx, title=title, description=description, **kwargs)
        except TypeError:
            # fallback if your util signature is different
            return await create_embed(title=title, description=description, **kwargs)

    def _expected_type(self, key: str):
        left, color = _parse_shop_key(key)
        if left:
            return int
        return self.editable.get(_normalize_key(key))

    def _get_value(self, key: str):
        left, color = _parse_shop_key(key)
        if left:
            d = getattr(bot_config, left, {})
            return d.get(color)
        return getattr(bot_config, _normalize_key(key), None)

    def _set_value(self, key: str, value):
        left, color = _parse_shop_key(key)
        if left:
            d = getattr(bot_config, left, {})
            if not isinstance(d, dict):
                d = {}
            d[color] = value
            setattr(bot_config, left, d)
            return
        setattr(bot_config, _normalize_key(key), value)

    def load_config(self):
        if not os.path.isfile(CONFIG_FILE):
            return
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[ConfigManager] Failed to load {CONFIG_FILE}: {e}")
            return

        # Flat keys
        for key in self.editable.keys():
            if key in data:
                setattr(bot_config, key, data[key])

        # Shop dicts
        for dkey in self.shop_dicts:
            if dkey in data and isinstance(data[dkey], dict):
                normalized = {str(k).lower(): int(v) for k, v in data[dkey].items()}
                setattr(bot_config, dkey, normalized)

        self._ensure_config_defaults()

    def save_config(self):
        payload = {}

        for key in self.editable.keys():
            payload[key] = getattr(bot_config, key)

        for dkey in self.shop_dicts:
            d = getattr(bot_config, dkey, {})
            if not isinstance(d, dict):
                d = {}
            payload[dkey] = {str(k).lower(): int(v) for k, v in d.items()}

        try:
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=4)
        except Exception as e:
            print(f"[ConfigManager] Failed to save {CONFIG_FILE}: {e}")

    @commands.group(name="config", hidden=True, invoke_without_command=True)
    async def config_group(self, ctx: commands.Context):
        # Base invocation is an error (plain text)
        await ctx.send("❌ Use `!modcommands` for help. Valid: `!config get|set|list`.")

    @config_group.command(name="get")
    async def config_get(self, ctx: commands.Context, key: str):
        expected = self._expected_type(key)
        if expected is None:
            return await ctx.send(f"❌ `{key}` is not an editable config key.")

        value = self._get_value(key)
        desc = f"**Key:** `{key}`\n**Type:** `{_type_label(expected)}`\n**Current Value:** `{value}`"
        embed = await self._make_embed(ctx, title="Config Value", description=desc)
        await ctx.send(embed=embed)

    @config_group.command(name="set")
    async def config_set(self, ctx: commands.Context, key: str, *, raw_value: str):
        expected = self._expected_type(key)
        if expected is None:
            return await ctx.send(f"❌ `{key}` is not an editable config key.")

        raw = raw_value.strip()

        try:
            if expected is bool:
                low = raw.lower()
                if low in TRUE_VALUES:
                    val = True
                elif low in FALSE_VALUES:
                    val = False
                else:
                    return await ctx.send(
                        f"❌ Invalid boolean for `{key}`. Use: {', '.join(sorted(TRUE_VALUES | FALSE_VALUES))}"
                    )
            elif expected is int:
                val = int(raw)
            elif expected is str:
                val = raw
            else:
                return await ctx.send(f"❌ Unsupported type for `{key}`.")
        except Exception as e:
            return await ctx.send(f"❌ Failed to cast value for `{key}`: {e}")

        if expected is int and val < 0:
            return await ctx.send(f"❌ `{key}` cannot be negative.")

        self._set_value(key, val)
        self.save_config()

        desc = f"**Updated:** `{key}`\n**New Value:** `{val}`\n**Type:** `{_type_label(expected)}`"
        embed = await self._make_embed(ctx, title="Config Updated", description=desc)
        await ctx.send(embed=embed)

    @config_group.command(name="list")
    async def config_list(self, ctx: commands.Context):
        lines = []

        # Flat keys
        for k in sorted(self.editable.keys()):
            t = self.editable[k]
            v = getattr(bot_config, k)
            lines.append(f"`{k}`  •  `{_type_label(t)}`  •  `{v}`")

        # Shop keys expanded
        for dkey in self.shop_dicts:
            d = getattr(bot_config, dkey, {})
            if not isinstance(d, dict):
                d = {}
            for color in sorted(d.keys()):
                lines.append(f"`{dkey}.{color}`  •  `int`  •  `{d[color]}`")

        # Chunk to avoid embed field limits
        chunks = []
        current = ""
        for line in lines:
            if len(current) + len(line) + 1 > 900:
                chunks.append(current)
                current = ""
            current += line + "\n"
        if current:
            chunks.append(current)

        embed = await self._make_embed(
            ctx,
            title="Editable Config Keys",
            description=(
                "Keys moderators can change (name • type • current value).\n"
                "Shop keys use dot-notation: `SHOP_FRAME_PRICES.red`"
            ),
        )

        for i, chunk in enumerate(chunks, start=1):
            embed.add_field(
                name=f"Keys ({i}/{len(chunks)})",
                value=chunk,
                inline=False
            )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ConfigManager(bot))
