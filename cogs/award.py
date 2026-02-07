import discord
from discord.ext import commands
from utils.economy import add_currency, user_key
from utils.embed import create_embed
from config import DEFAULT_CURRENCY_GIVE, BETTING_CHANNEL, CURRENCY_NAME, CURRENCY_SYMBOL


class EconomyAward(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="award")
    @commands.has_role("Moderator")  # Only allows moderators to run this command
    async def award(self, ctx, amount: int, member: discord.Member, *, reason: str = None):
        """
        Award currency to a server member.
        Usage: award <amount> @User <optional reason>
        """
        # Delete the command message
        await ctx.message.delete()

        # Check that the awarded amount does not exceed the allowed limit.
        if amount > DEFAULT_CURRENCY_GIVE:
            embed = discord.Embed(
                title="Award Limit Exceeded",
                description=f"You cannot award more than {CURRENCY_SYMBOL}{DEFAULT_CURRENCY_GIVE} {CURRENCY_NAME}.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # ✅ Centralized identity (ID-keyed)
        key = user_key(member)
        new_balance = add_currency(key, amount)

        title = "Currency Awarded!"
        description = (
            f"{ctx.author.mention} awarded **{CURRENCY_SYMBOL}{amount} {CURRENCY_NAME}** to {member.mention}.\n"
            f"New balance for {member.mention}: **{CURRENCY_SYMBOL}{new_balance}**."
        )

        if reason:
            description += f"\n**Reason:** {reason}"

        embed_result = create_embed(title, description)
        embed = await embed_result if hasattr(embed_result, "__await__") else embed_result

        channel = self.bot.get_channel(BETTING_CHANNEL)
        if channel:
            await channel.send(embed=embed)
        else:
            await ctx.send(embed=embed)

    @award.error
    async def award_error(self, ctx, error):
        if isinstance(error, commands.MissingRole):
            embed = discord.Embed(
                title="Permission Denied",
                description="You need the **Moderator** role to use that command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            await ctx.message.delete()


async def setup(bot):
    await bot.add_cog(EconomyAward(bot))
