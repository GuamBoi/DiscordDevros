import os
import discord
from discord.ext import commands
from config import ECONOMY_FOLDER, CURRENCY_NAME
from utils.economy import get_balance, load_economy
from utils.embed import create_embed

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='balance', help='Check your current balance')
    async def balance(self, ctx):
        """Display the user's current currency balance."""
        user_id = str(ctx.author.id)
        balance = get_balance(user_id)
        
        embed = create_embed(
            title=f"{ctx.author.name}'s Currency Balance",
            description=f"You currently have {balance} {CURRENCY_NAME}.",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)

    @commands.command(name='leaderboard', help='Show the top 10 users with the highest currency')
    async def leaderboard(self, ctx):
        """Display a leaderboard of the top 10 users with the highest currency balance."""
        economy_data = []
        
        # Iterate through all JSON files in the economy folder
        for file in os.listdir(ECONOMY_FOLDER):
            if file.endswith(".json"):
                user_id = file.replace(".json", "")
                data = load_economy(user_id)
                economy_data.append((user_id, data['currency']))
        
        # Sort the data by currency in descending order and take the top 10
        economy_data.sort(key=lambda x: x[1], reverse=True)
        top_10 = economy_data[:10]

        # Create the leaderboard text
        leaderboard_text = ""
        for i, (user_id, currency) in enumerate(top_10, start=1):
            user = self.bot.get_user(int(user_id))
            leaderboard_text += f"{i}. {user.name if user else 'Unknown User'} - {currency} {CURRENCY_NAME}\n"

        embed = create_embed(
            title="Top 10 Currency Leaderboard",
            description=leaderboard_text,
            color=discord.Color.gold()
        )

        await ctx.send(embed=embed)

# Ensure setup() is async and awaits add_cog()
async def setup(bot):
    await bot.add_cog(Leaderboard(bot))
