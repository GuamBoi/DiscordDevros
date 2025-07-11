import os
import json
import discord
from discord.ext import commands
from config import ECONOMY_FOLDER, CURRENCY_NAME, CURRENCY_SYMBOL
from utils.embed import create_embed

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='leaderboard', help='Show the top 10 users with the highest currency')
    async def leaderboard(self, ctx):
        """Display a leaderboard of the top 10 users with the highest currency balance."""
        economy_data = []
        for file in os.listdir(ECONOMY_FOLDER):
            if file.endswith('.json'):
                username = file.replace('.json', '')
                data = json.load(open(os.path.join(ECONOMY_FOLDER, file), 'r'))
                economy_data.append((username, data.get('currency', 0)))

        economy_data.sort(key=lambda x: x[1], reverse=True)
        top_10 = economy_data[:10]

        leaderboard_text = ''
        for i, (username, currency) in enumerate(top_10, start=1):
            member = discord.utils.get(ctx.guild.members, name=username)
            mention = member.mention if member else username
            leaderboard_text += f"{i}. {mention} - {CURRENCY_SYMBOL}{currency}\n"

        embed = await create_embed(
            title=f"Top 10 {CURRENCY_NAME} Wallets",
            description=leaderboard_text,
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)
        await ctx.message.delete()

    @commands.command(name='xpleaderboard', help='Show top 10 users by level and XP')
    async def xpleaderboard(self, ctx):
        """Display a leaderboard of the top 10 users ranked by level and XP."""
        users = []
        for file in os.listdir(ECONOMY_FOLDER):
            if file.endswith('.json'):
                path = os.path.join(ECONOMY_FOLDER, file)
                data = json.load(open(path, 'r'))
                users.append((data.get('username', file.replace('.json', '')),
                              data.get('level', 1),
                              data.get('xp', 0)))

        # Sort by level first, then XP
        users.sort(key=lambda x: (x[1], x[2]), reverse=True)
        top10 = users[:10]

        leaderboard_text = ''
        for i, (username, lvl, xp) in enumerate(top10, start=1):
            member = discord.utils.get(ctx.guild.members, name=username)
            mention = member.mention if member else username
            leaderboard_text += f"{i}. {mention} — Level {lvl} ({xp} XP)\n"

        embed = discord.Embed(
            title="XP Leaderboard",
            description=leaderboard_text,
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed)
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(Leaderboard(bot))
