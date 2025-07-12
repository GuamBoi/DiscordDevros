import discord
from discord.ext import commands
from config import (
    ENABLE_XP_SYSTEM,
    SHOW_LEVEL_UP_MESSAGES,
    XP_NOTIFICATION_CHANNEL_ID,
    XP_PER_MESSAGE,
    XP_PER_REACTION,
    XP_PER_COMMAND,
    LEVEL_UP_REWARD_MULTIPLIER,
    CURRENCY_NAME, 
    CURRENCY_SYMBOL,
)
from utils.economy import add_xp
from utils.embed import create_embed

class XP(commands.Cog):
    """Cog to award XP and handle level-up rewards."""

    def __init__(self, bot):
        self.bot = bot

    async def send_level_up_message(self, member, level, channel):
        if not SHOW_LEVEL_UP_MESSAGES:
            return

        reward = level * LEVEL_UP_REWARD_MULTIPLIER
        embed = await create_embed(
            title="Level Up! 🎉",
            description=f"{member.mention}, you just hit level **{level}** and earned **{CURRENCY_SYMBOL}{reward}** {CURRENCY_NAME}",
            color=discord.Color.green()
        )

        try:
            # Use specified channel or fallback
            if XP_NOTIFICATION_CHANNEL_ID:
                notify_channel = self.bot.get_channel(XP_NOTIFICATION_CHANNEL_ID)
                if notify_channel:
                    await notify_channel.send(embed=embed)
                    return

            # Fallback: send to original channel if XP_NOTIFICATION_CHANNEL_ID is not set or invalid
            await channel.send(embed=embed)
        except Exception as e:
            print(f"[XP] Failed to send level-up message: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if not ENABLE_XP_SYSTEM or message.author.bot:
            return

        leveled, new_level = add_xp(message.author.name, XP_PER_MESSAGE)
        if leveled:
            await self.send_level_up_message(message.author, new_level, message.channel)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if not ENABLE_XP_SYSTEM or user.bot:
            return

        leveled, new_level = add_xp(user.name, XP_PER_REACTION)
        if leveled:
            await self.send_level_up_message(user, new_level, reaction.message.channel)

    @commands.Cog.listener()
    async def on_command(self, ctx):
        if not ENABLE_XP_SYSTEM or ctx.author.bot:
            return

        leveled, new_level = add_xp(ctx.author.name, XP_PER_COMMAND)
        if leveled:
            await self.send_level_up_message(ctx.author, new_level, ctx.channel)

async def setup(bot):
    await bot.add_cog(XP(bot))
