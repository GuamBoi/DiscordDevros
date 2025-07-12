import discord
from discord.ext import commands
from config import CURRENCY_NAME, CURRENCY_SYMBOL
from utils.economy import load_economy
from utils.embed import create_embed

class Balance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='balance', help='Check your currency, level, and XP')
    async def balance(self, ctx):
        data = load_economy(ctx.author.name)
        lvl    = data.get("level", 1)
        xp     = data.get("xp", 0)
        needed = 100 * lvl
        bal    = data.get("currency", 0)

        description = (
            f"{ctx.author.mention}, you have **{CURRENCY_SYMBOL}{bal}**.\n\n"
            f"**Level:** {lvl}\n"
            f"**XP:** {xp} / {needed}\n\n"
            f"**Wordle Streak:** `{data.get('wordle_streak', 0)}`  "
            f"**Connect4 Streak:** `{data.get('connect4_streak', 0)}`"
        )

        embed = await create_embed(
            title=f"{CURRENCY_NAME} & XP Status",
            description=description,
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(Balance(bot))
