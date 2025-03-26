import discord
from discord.ext import commands
from utils.economy import add_currency, get_balance
from utils.embed import create_embed
from config import DEFAULT_CURRENCY_GIVE, BETTING_CHANNEL, CURRENCY_NAME, CURRENCY_SYMBOL

class EconomyAward(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="award")
    @commands.has_role("Moderator")
    async def award(self, ctx, amount: int, member: discord.Member, *, reason: str = None):
        """
        Award currency to a server member.
        Usage: award <amount> @User <optional reason>
        """
        # Check that the awarded amount does not exceed the allowed limit.
        if amount > DEFAULT_CURRENCY_GIVE:
            await ctx.send(f"You cannot award more than {DEFAULT_CURRENCY_GIVE} {CURRENCY_NAME} ({CURRENCY_SYMBOL}).")
            return

        # Award the currency using the economy utility.
        new_balance = add_currency(member.name, amount)
        
        # Build the embed message.
        title = "Currency Awarded!"
        description = (
            f"{ctx.author.mention} awarded **{amount} {CURRENCY_SYMBOL} {CURRENCY_NAME}** to {member.mention}.\n"
            f"New balance for {member.mention}: **{new_balance} {CURRENCY_SYMBOL}**."
        )
        if reason:
            description += f"\n**Reason:** {reason}"
        
        # Create the embed.
        embed_result = create_embed(title, description)
        # If the result is awaitable, await it.
        if hasattr(embed_result, '__await__'):
            embed = await embed_result
        else:
            embed = embed_result
        
        # Get the designated channel.
        channel = self.bot.get_channel(BETTING_CHANNEL)
        if channel:
            await channel.send(embed=embed)
        else:
            # Fallback: send in the current channel if BETTING_CHANNEL isn't found.
            await ctx.send(embed=embed)
        
        # Confirm the action to the moderator.
        await ctx.send(f"{member.mention} has been awarded **{amount} {CURRENCY_SYMBOL} {CURRENCY_NAME}**.")

def setup(bot):
    bot.add_cog(EconomyAward(bot))
