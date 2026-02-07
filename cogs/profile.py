# cogs/profile.py
import discord
from discord.ext import commands
from config import CURRENCY_NAME, CURRENCY_SYMBOL
from utils.economy import load_economy, user_key
from utils.embed import create_embed
from utils.shop import (
    ensure_shop_schema,
    get_equipped,
    get_owned_frames,
    get_owned_colors,
)
from utils.profile_card import render_profile_thumbnail

def _discord_color_from_hex(value: str | None) -> discord.Color:
    if not value:
        return discord.Color.blue()
    s = value.strip()
    if s.startswith("#"):
        s = s[1:]
    try:
        return discord.Color(int(s, 16))
    except Exception:
        return discord.Color.blue()

class Balance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="profile",
        aliases=["balance", "bal"],
        help="Show your (or another user’s) profile: currency, level, XP, streaks."
    )
    async def profile(self, ctx, member: discord.Member | None = None):
        member = member or ctx.author

        key = user_key(member)
        data = load_economy(key)

        # Ensure inventory exists for anyone viewed
        ensure_shop_schema(member)

        # Use equipped values only to render visuals (do NOT display them in text)
        frame_id, accent_hex = get_equipped(member)

        owned_frames = get_owned_frames(member)
        owned_colors = get_owned_colors(member)

        lvl = int(data.get("level", 1) or 1)
        xp = int(data.get("xp", 0) or 0)
        needed = 100 * lvl
        bal = int(data.get("currency", 0) or 0)

        frames_text = ", ".join(f"`{f}`" for f in owned_frames) if owned_frames else "`none`"
        colors_text = ", ".join(f"`{c}`" for c in owned_colors) if owned_colors else "`none`"

        description = (
            f"{member.mention}\n\n"
            f"**🪙 Wallet\n"
            f"**{CURRENCY_NAME}:** {CURRENCY_SYMBOL}{bal}\n"
            f"**Level:** {lvl}\n"
            f"**XP:** {xp} / {needed}\n\n"
            f"**🔥 Streaks\n"
            f"**Wordle Streak:** `{int(data.get('wordle_streak', 0) or 0)}`\n"
            f"**Connect4 Streak:** `{int(data.get('connect4_streak', 0) or 0)}`\n"
            f"**Battleship Win Streak:** `{int(data.get('battleship_streak', 0) or 0)}`\n\n"
            f"**🛍️ Owned Items\n"
            f"**Frames:** {frames_text}\n"
            f"**Colors:** {colors_text}\n"
        )

        embed = await create_embed(
            title=f"{member.display_name}'s Profile",
            description=description,
            color=_discord_color_from_hex(accent_hex),
        )

        # Render framed thumbnail (top-left)
        thumb_bytes = await render_profile_thumbnail(
            member,
            frame_id=frame_id,
            accent_hex=accent_hex,
            size=256,
        )
        thumb_file = discord.File(fp=thumb_bytes, filename="thumb.png")
        embed.set_thumbnail(url="attachment://thumb.png")

        await ctx.send(embed=embed, file=thumb_file)

        try:
            await ctx.message.delete()
        except (discord.NotFound, discord.Forbidden):
            pass

async def setup(bot):
    await bot.add_cog(Balance(bot))
