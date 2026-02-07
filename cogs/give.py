import discord
from discord.ext import commands
from utils.economy import add_currency, remove_currency, get_balance, user_key
from utils.embed import create_embed
from config import DEFAULT_CURRENCY_GIVE, BETTING_CHANNEL, CURRENCY_NAME, CURRENCY_SYMBOL


class EconomyGive(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="give")
    async def give(self, ctx, amount: int, member: discord.Member, *, reason: str = None):
        """
        Give currency from your own balance to another server member.
        Usage: give <amount> @User <optional reason>
        """
        # Ensure the amount is positive
        if amount <= 0:
            await ctx.send("You cannot give a non-positive amount.")
            return

        sender_key = user_key(ctx.author)
        receiver_key = user_key(member)

        # Get the balance of the user issuing the command (ID-keyed)
        user_balance = get_balance(sender_key)

        # Ensure the user has enough currency
        if user_balance < amount:
            await ctx.send(f"You do not have enough {CURRENCY_NAME} to give that amount.")
            return

        # Remove currency from the giver's balance
        new_balance_sender = remove_currency(sender_key, amount)

        # Add currency to the receiver's balance
        new_balance_receiver = add_currency(receiver_key, amount)

        # Build the embed message for the transaction
        title = "Currency Given!"
        description = (
            f"{ctx.author.mention} gave **{CURRENCY_SYMBOL}{amount} {CURRENCY_NAME}** to {member.mention}.\n"
            f"New balance for {ctx.author.mention}: **{CURRENCY_SYMBOL}{new_balance_sender}**.\n"
            f"New balance for {member.mention}: **{CURRENCY_SYMBOL}{new_balance_receiver}**."
        )

        if reason:
            description += f"\n**Reason:** {reason}"

        # Create the embed
        embed_result = create_embed(title, description)
        embed = await embed_result if hasattr(embed_result, "__await__") else embed_result

        # Send the result to the betting channel or fallback to the current channel
        channel = self.bot.get_channel(BETTING_CHANNEL)
        if channel:
            await channel.send(embed=embed)
        else:
            await ctx.send(embed=embed)

        # Confirm the transaction to the user
        await ctx.send(f"You gave **{CURRENCY_SYMBOL}{amount} {CURRENCY_NAME}** to {member.mention}.")


async def setup(bot):
    await bot.add_cog(EconomyGive(bot))
