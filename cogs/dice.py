# cogs/dice.py

import random
from discord.ext import commands
from utils.llm_api import query_llm  # Import the query_llm function
from utils.embed import create_embed  # Import the create_embed function

class DiceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Helper function to generate the LLM message
    async def generate_roll_message(self, dice_type, roll_result):
        prompt = f"Generate a fun and creative response for a roll of a {dice_type} with the result {roll_result}. Make it interesting and engaging!"
        try:
            response = await query_llm(prompt)
            return response
        except Exception as e:
            return f"An error occurred while generating the response: {e}"

    # Generalized dice roll command
    async def roll_dice(self, ctx, dice_type, max_value, color):
        roll_result = random.randint(1, max_value)
        response = await self.generate_roll_message(dice_type, roll_result)
        embed = create_embed(
            title=f"{dice_type} Roll",
            description=f"🎲 {response}",
            color=color,
            footer_text=f"Rolled a {dice_type}"
        )
        await ctx.send(embed=embed)
        await ctx.message.delete()

    # Individual dice commands
    @commands.command()
    async def d4(self, ctx):
        await self.roll_dice(ctx, "D4", 4, discord.Color.blue())

    @commands.command()
    async def d6(self, ctx):
        await self.roll_dice(ctx, "D6", 6, discord.Color.blue())

    @commands.command()
    async def d8(self, ctx):
        await self.roll_dice(ctx, "D8", 8, discord.Color.blue())

    @commands.command()
    async def d10(self, ctx):
        await self.roll_dice(ctx, "D10", 10, discord.Color.blue())

    @commands.command()
    async def d12(self, ctx):
        await self.roll_dice(ctx, "D12", 12, discord.Color.blue())

    @commands.command()
    async def d20(self, ctx):
        await self.roll_dice(ctx, "D20", 20, discord.Color.blue())

async def setup(bot):
    await bot.add_cog(DiceCog(bot))
