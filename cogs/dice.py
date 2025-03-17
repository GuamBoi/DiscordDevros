# cogs/dice.py

import discord
import random
from discord.ext import commands
from utils.llm_api import query_llm  # Import the query_llm function
from utils.embed import create_embed  # Import the create_embed function

class DiceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Helper function to generate an AI reaction to the roll result
    async def generate_roll_reaction(self, dice_type, roll_result, max_value):
        prompt = (
            f"You are an enthusiastic tabletop RPG companion. A user rolled a {dice_type} and got {roll_result} "
            f"out of a possible {max_value}. React with a short, fun message to their roll. "
            f"If the result is high, make it exciting. If it's low, make it lighthearted but funny. "
            f"Examples:\n"
            f"- 'Oof, tough luck! Maybe next time!'\n"
            f"- 'Critical success! You're on fire!'\n"
            f"- 'A solid roll! Let’s see what happens next!'\n"
            f"Limit your response to a single short sentence."
        )
        try:
            response = await query_llm(prompt)
            return response
        except Exception:
            return "Interesting roll! Let's see where this leads."

    # Generalized dice roll command with typing indicator
    async def roll_dice(self, ctx, dice_type, max_value, color):
        async with ctx.typing():  # Show typing indicator while processing
            roll_result = random.randint(1, max_value)
            reaction = await self.generate_roll_reaction(dice_type, roll_result, max_value)

        # Static message + AI-generated reaction
        roll_message = f"{ctx.author.mention} rolled a **{dice_type}** and got **{roll_result}**!\n🎲 {reaction}"

        embed = create_embed(
            title=f"{dice_type} Roll",
            description=roll_message,
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
    async def roll(self, ctx):
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
