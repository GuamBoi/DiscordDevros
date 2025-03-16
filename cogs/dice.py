# cogs/dice.py

import discord
import random
from discord.ext import commands
from utils.llm_api import query_llm  # Import the query_llm function
from utils.embed import create_embed  # Import the create_embed function

class DiceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Helper function to generate a concise LLM message
    async def generate_roll_message(self, dice_type, roll_result):
        prompt = (
            f"Generate a short and witty response for rolling a {dice_type} "
            f"with a result of {roll_result}. Format it exactly like this: "
            f"'You rolled a {dice_type} and got a {roll_result}! [Witty remark]' "
            f"Keep it short and no longer than 1 sentence."
        )
        try:
            response = await query_llm(prompt)
            if not response.startswith(f"You rolled a {dice_type} and got a {roll_result}"):
                response = f"You rolled a {dice_type} and got a {roll_result}! Nice roll!"
            return response
        except Exception as e:
            return f"You rolled a {dice_type} and got a {roll_result}! (Error generating witty remark: {e})"

    # Generalized dice roll command with typing indicator
    async def roll_dice(self, ctx, dice_type, max_value, color):
        async with ctx.typing():  # Show typing indicator while processing
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
        await self.roll_dice(ctx, "D6", 6, discord.Color.green())

    @commands.command()
    async def d8(self, ctx):
        await self.roll_dice(ctx, "D8", 8, discord.Color.orange())

    @commands.command()
    async def d10(self, ctx):
        await self.roll_dice(ctx, "D10", 10, discord.Color.purple())

    @commands.command()
    async def d12(self, ctx):
        await self.roll_dice(ctx, "D12", 12, discord.Color.red())

    @commands.command()
    async def d20(self, ctx):
        await self.roll_dice(ctx, "D20", 20, discord.Color.gold())

async def setup(bot):
    await bot.add_cog(DiceCog(bot))
