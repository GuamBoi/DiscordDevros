import discord
from discord.ext import commands
from utils.economy import add_currency, user_key
from utils.embed import create_embed
from config import MODERATOR_ROLE_ID, CURRENCY_NAME, CURRENCY_SYMBOL, COMMAND_PREFIX

class EconomyAward(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="award")
    @commands.has_role(MODERATOR_ROLE_ID)
    async def award(self, ctx, member: discord.Member, amount: int, *, reason: str = None):
        """
        Award currency to a server member.
        Usage: award @User <amount> <optional reason>
        """
        # Delete the command message (best-effort)
        try:
            await ctx.message.delete()
        except (discord.NotFound, discord.Forbidden):
            pass

        if amount <= 0:
            embed = await create_embed(
                title="❌ Invalid Amount",
                description="Award amount must be greater than 0.",
                color=discord.Color.red(),
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

        embed = await create_embed(title, description, color=discord.Color.green())
        await ctx.send(embed=embed)

    @award.error
    async def award_error(self, ctx, error):
        if isinstance(error, commands.MissingRole):
            embed = await create_embed(
                title="❌ Permission Denied",
                description="You need the **Moderator** role to use this command.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            try:
                await ctx.message.delete()
            except (discord.NotFound, discord.Forbidden):
                pass
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = await create_embed(
                title="❌ Missing Arguments",
                description=f"Usage: `{COMMAND_PREFIX}award @USER AMOUNT OPTIONAL_REASON`",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.BadArgument):
            embed = await create_embed(
                title="❌ Invalid Arguments",
                description="Make sure you mention a valid user and use a numeric amount.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(EconomyAward(bot))
