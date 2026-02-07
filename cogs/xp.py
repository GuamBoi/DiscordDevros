# cogs/xp.py
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
from utils.economy import user_key
from utils.xp import award_xp
from utils.embed import create_embed


class XP(commands.Cog):
    """Cog to award XP and handle level-up rewards."""

    def __init__(self, bot):
        self.bot = bot

    async def send_level_up_message(self, member, level, channel):
        if not SHOW_LEVEL_UP_MESSAGES:
            return

        reward = int(LEVEL_UP_REWARD_MULTIPLIER * level)

        embed = await create_embed(
            title="Level Up!",
            description=(
                f"{member.mention}, you reached level **{level}** "
                f"and earned **{CURRENCY_SYMBOL}{reward}** {CURRENCY_NAME}"
            ),
            color=discord.Color.green(),
        )

        try:
            if XP_NOTIFICATION_CHANNEL_ID:
                notify_channel = self.bot.get_channel(XP_NOTIFICATION_CHANNEL_ID)
                if notify_channel:
                    await notify_channel.send(embed=embed)
                    return

            await channel.send(embed=embed)
        except Exception as e:
            print(f"[XP] Failed to send level-up message: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if not ENABLE_XP_SYSTEM or message.author.bot:
            return

        key = user_key(message.author)
        leveled, level, _ = award_xp(key, XP_PER_MESSAGE)

        if leveled:
            await self.send_level_up_message(message.author, level, message.channel)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if not ENABLE_XP_SYSTEM or user.bot:
            return

        key = user_key(user)
        leveled, level, _ = award_xp(key, XP_PER_REACTION)

        if leveled:
            await self.send_level_up_message(user, level, reaction.message.channel)

    @commands.Cog.listener()
    async def on_command(self, ctx):
        if not ENABLE_XP_SYSTEM or ctx.author.bot:
            return

        key = user_key(ctx.author)
        leveled, level, _ = award_xp(key, XP_PER_COMMAND)

        if leveled:
            await self.send_level_up_message(ctx.author, level, ctx.channel)


async def setup(bot):
    await bot.add_cog(XP(bot))
