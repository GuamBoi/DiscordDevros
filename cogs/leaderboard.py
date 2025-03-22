import os
import discord
from discord.ext import commands
from config import ECONOMY_FOLDER, CURRENCY_NAME, CURRENCY_SYMBOL
from utils.economy import load_economy
from utils.embed import create_embed

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='balance', help='Check your current balance')
    async def balance(self, ctx):
        """Display the user's current currency balance."""
        username = ctx.author.name  # Using username as key in economy files
        balance_value = load_economy(username)["currency"]
        
        embed = await create_embed(
            title=f"{CURRENCY_NAME} Balance",
            description=f"You currently have {CURRENCY_SYMBOL}{balance_value}.",
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
                economy_data.append((username, data['currency']))
        
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
            title=f"Top 10 {CURRENCY_NAME} Leaderboard",
            description=leaderboard_text,
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)
        await ctx.message.delete()

# Ensure setup() is async and awaits add_cog()
async def setup(bot):
    await bot.add_cog(Leaderboard(bot))
