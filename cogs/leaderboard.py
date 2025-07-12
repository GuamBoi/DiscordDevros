import os
import json
import discord
from discord.ext import commands
from config import ECONOMY_FOLDER, CURRENCY_SYMBOL
from utils.embed import create_embed
from utils.economy import load_economy

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='leaderboard', help='Show top 10 users by level and XP, including currency')
    async def leaderboard(self, ctx):
        """Display a leaderboard of the top 10 users ranked by level and XP, also showing currency."""
        users = []
        for filename in os.listdir(ECONOMY_FOLDER):
            if filename.endswith('.json'):
                path = os.path.join(ECONOMY_FOLDER, filename)
                data = json.load(open(path, 'r'))
                users.append((
                    data.get('username', filename[:-5]),
                    data.get('level', 1),
                    data.get('xp', 0),
                    data.get('currency', 0)
                ))

        # Sort by level first, then XP
        users.sort(key=lambda x: (x[1], x[2]), reverse=True)
        top10 = users[:10]

        leaderboard_text = ''
        for i, (username, lvl, xp, bal) in enumerate(top10, start=1):
            member = discord.utils.get(ctx.guild.members, name=username)
            mention = member.mention if member else username
            leaderboard_text += (
                f"{i}. {mention} — Level {lvl} ({xp} XP) — "
                f"{CURRENCY_SYMBOL}{bal}\n"
            )

        embed = await create_embed(
            title="Leaderboard: Top Levels & Currency",
            description=leaderboard_text,
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed)
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(Leaderboard(bot))
