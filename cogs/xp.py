import discord
from discord.ext import commands
from config import XP_PER_MESSAGE, XP_PER_REACTION, XP_PER_COMMAND, LEVEL_UP_REWARD_MULTIPLIER
from utils.economy import add_xp
from utils.embed import create_embed

class XP(commands.Cog):
    """Cog to award XP and handle level-up rewards."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        leveled, new_level = add_xp(message.author.name, XP_PER_MESSAGE)
        if leveled:
            reward = new_level * LEVEL_UP_REWARD_MULTIPLIER
            embed = await create_embed(
                title="Level Up! 🎉",
                description=f"{message.author.mention}, you just hit level **{new_level}** and earned **{reward} Devros$**!",
                color=discord.Color.green()
            )
            await message.channel.send(embed=embed)

        # Removed await self.bot.process_commands(message) to prevent duplication

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return

        leveled, new_level = add_xp(user.name, XP_PER_REACTION)
        if leveled:
            reward = new_level * LEVEL_UP_REWARD_MULTIPLIER
            embed = await create_embed(
                title="Level Up! 🎉",
                description=f"{user.mention}, you just hit level **{new_level}** and earned **{reward} Devros$**!",
                color=discord.Color.green()
            )
            await reaction.message.channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_command(self, ctx):
        if ctx.author.bot:
            return

        leveled, new_level = add_xp(ctx.author.name, XP_PER_COMMAND)
        if leveled:
            reward = new_level * LEVEL_UP_REWARD_MULTIPLIER
            embed = await create_embed(
                title="Level Up! 🎉",
                description=f"{ctx.author.mention}, you just hit level **{new_level}** and earned **{reward} Devros$**!",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(XP(bot))
