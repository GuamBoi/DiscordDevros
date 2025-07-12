import os
import discord
from discord.ext import commands
from config import ECONOMY_FOLDER, CURRENCY_NAME, CURRENCY_SYMBOL
from utils.economy import load_economy
from utils.embed import create_embed

class Balance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='balance', help='Check your currency, level, and XP')
    async def balance(self, ctx):
        data = load_economy(ctx.author.name)
        lvl   = data["level"]
        xp    = data["xp"]
        needed = 100 * lvl
        bal   = data["currency"]
        desc = (
            f"{ctx.author.mention}, you have **{CURRENCY_SYMBOL}{bal}**.\n\n"
            f"**Level:** {lvl}\n"
            f"**XP:** {xp} / {needed}\n\n"
            f"**Wordle Streak:** `{data['wordle_streak']}`  "
            f"**Connect4 Streak:** `{data['connect4_streak']}`"
        )
        embed = await create_embed(
            title=f"{CURRENCY_NAME} & XP Status",
            description=desc,
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(Balance(bot))
