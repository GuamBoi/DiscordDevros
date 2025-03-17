# cogs/leaderboard.py

import discord
from discord.ext import commands
from utils.economy import get_balance, load_economy, add_currency, remove_currency
from utils.embed import create_embed

# Create the leaderboard cog
class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='currency', help='Check your current balance')
    async def balance(self, ctx):
        """Command to check user's currency balance."""
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
        """Command to show the leaderboard of the top 10 users with the highest balance."""
        economy_data = []
        
        # Load all users' economy data
        for file in os.listdir(ECONOMY_FOLDER):
            if file.endswith(".json"):
                user_id = file.replace(".json", "")
                data = load_economy(user_id)
                economy_data.append((user_id, data['currency']))
        
        # Sort by currency amount in descending order and get the top 10
        economy_data.sort(key=lambda x: x[1], reverse=True)
        top_10 = economy_data[:10]

        # Prepare the leaderboard embed
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

# Setup function to add the cog to the bot
def setup(bot):
    bot.add_cog(Leaderboard(bot))
