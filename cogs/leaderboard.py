import os
import discord
from discord.ext import commands
from config import ECONOMY_FOLDER, CURRENCY_NAME, CURRENCY_SYMBOL
from utils.economy import load_economy
from utils.embed import create_embed

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='balance', help='Check your current balance and streaks')
    async def balance(self, ctx):
        """Display the user's current currency balance, Wordle streak, and Connect4 streak."""
        username = ctx.author.name  # Using username as key in economy files
        econ_data = load_economy(username)
        balance_value = econ_data.get("currency", "No Balance Found")
        wordle_streak = econ_data.get("wordle_streak", "No Wordle Streak Found")
        connect4_streak = econ_data.get("connect4_streak", "No Connect 4 Streak Found")
        
        description = (
            f"{ctx.author.mention}, you currently have {CURRENCY_SYMBOL}{balance_value}.\n\n"
            f"**Wordle Streak:** `{wordle_streak}`\n"
            f"**Connect4 Streak:** `{connect4_streak}`"
        )
        
        embed = await create_embed(
            title=f"{CURRENCY_NAME} Balance",
            description=description,
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        await ctx.message.delete()

    @commands.command(name='leaderboard', help='Show the top 10 users with the highest currency')
    async def leaderboard(self, ctx):
        """Display a leaderboard of the top 10 users with the highest currency balance."""
        economy_data = []
        
        # Iterate through all JSON files in the economy folder
        for file in os.listdir(ECONOMY_FOLDER):
            if file.endswith(".json"):
                username = file.replace(".json", "")
                data = load_economy(username)
                economy_data.append((username, data.get('currency', 0)))
        
        # Sort the data by currency in descending order and take the top 10
        economy_data.sort(key=lambda x: x[1], reverse=True)
        top_10 = economy_data[:10]

        leaderboard_text = ""
        for i, (username, currency) in enumerate(top_10, start=1):
            # Try to get a member from the guild to tag them; otherwise just show the username.
            member = discord.utils.get(ctx.guild.members, name=username)
            user_tag = member.mention if member else username
            leaderboard_text += f"{i}. {user_tag} - {CURRENCY_SYMBOL}{currency}\n"

        embed = await create_embed(
            title=f"Top 10 {CURRENCY_NAME} Wallets",
            description=leaderboard_text,
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(Leaderboard(bot))
