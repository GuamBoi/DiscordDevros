import discord
from discord.ext import commands
from config import CURRENCY_NAME, CURRENCY_SYMBOL
from utils.economy import load_economy
from utils.embed import create_embed

class Balance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name='profile',
        aliases=['balance', 'bal'],
        help='Show your (or another user’s) profile: currency, level, XP, streaks.'
    )
    async def profile(self, ctx, member: discord.Member | None = None):
        member = member or ctx.author

        # Use a stable identifier (recommended). If your economy files currently key off name,
        # you can temporarily use str(member.id) going forward while still supporting legacy.
        user_key = str(member.id)

        data = load_economy(user_key)

        lvl    = data.get("level", 1)
        xp     = data.get("xp", 0)
        needed = 100 * lvl
        bal    = data.get("currency", 0)

        description = (
            f"{member.mention}\n\n"
            f"**{CURRENCY_NAME}:** {CURRENCY_SYMBOL}{bal}\n"
            f"**Level:** {lvl}\n"
            f"**XP:** {xp} / {needed}\n\n"
            f"**Wordle Streak:** `{data.get('wordle_streak', 0)}`\n"
            f"**Connect4 Streak:** `{data.get('connect4_streak', 0)}`\n"
            f"**Battleship Win Streak:** `{data.get('battleship_streak', 0)}`\n"
        )

        embed = await create_embed(
            title=f"{member.display_name}'s Profile",
            description=description,
            color=discord.Color.blue()
        )

        # Optional: add avatar thumbnail for more “profile” feel
        if member.display_avatar:
            embed.set_thumbnail(url=member.display_avatar.url)

        await ctx.send(embed=embed)

        # Safely attempt to delete the invoking message
        try:
            await ctx.message.delete()
        except (discord.NotFound, discord.Forbidden):
            pass

async def setup(bot):
    await bot.add_cog(Balance(bot))
