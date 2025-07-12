import discord
from discord.ext import commands
from config import (
    XP_PER_MESSAGE,
    XP_PER_REACTION,
    XP_PER_COMMAND,
    LEVEL_UP_REWARD_MULTIPLIER,
    LEVEL_UP_CHANNEL_ID
)
from utils.economy import add_xp
from utils.embed import create_embed

class XP(commands.Cog):
    """Cog to award XP and handle level-up rewards."""

    def __init__(self, bot):
        self.bot = bot

    def get_announcement_channel(self, fallback_channel):
        """Returns the appropriate level-up announcement channel."""
        if LEVEL_UP_CHANNEL_ID:
            channel = self.bot.get_channel(LEVEL_UP_CHANNEL_ID)
            return channel if channel else fallback_channel
        return fallback_channel

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
            channel = self.get_announcement_channel(message.channel)
            await channel.send(embed=embed)

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
            channel = self.get_announcement_channel(reaction.message.channel)
            await channel.send(embed=embed)

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
            channel = self.get_announcement_channel(ctx.channel)
            await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(XP(bot))
