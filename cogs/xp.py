import discord
from discord.ext import commands
from config import XP_PER_MESSAGE, XP_PER_REACTION, XP_PER_COMMAND
from utils.economy import add_xp

class XP(commands.Cog):
    """Cog to award XP and handle level‑up rewards."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore bot messages
        if message.author.bot:
            return

        # Award XP for a regular message
        leveled, new_level = add_xp(message.author.name, XP_PER_MESSAGE)
        if leveled:
            await message.channel.send(
                f"🎉 {message.author.mention} just hit level **{new_level}** and earned **{new_level} Devros$**!"
            )

        # Ensure other commands still process
        await self.bot.process_commands(message)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        # Ignore bot reactions
        if user.bot:
            return

        # Award XP for reacting
        leveled, new_level = add_xp(user.name, XP_PER_REACTION)
        if leveled:
            await reaction.message.channel.send(
                f"🎉 {user.mention} just hit level **{new_level}** and earned **{new_level} Devros$**!"
            )

    @commands.Cog.listener()
    async def on_command(self, ctx):
        # Ignore bot‑originated commands
        if ctx.author.bot:
            return

        # Award XP for any Devros command use
        leveled, new_level = add_xp(ctx.author.name, XP_PER_COMMAND)
        if leveled:
            await ctx.send(
                f"🎉 {ctx.author.mention} just hit level **{new_level}** and earned **{new_level} Devros$**!"
            )

async def setup(bot):
    await bot.add_cog(XP(bot))
