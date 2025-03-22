# cogs/bet.py

import discord
from discord.ext import commands
from utils.economy import load_economy, save_economy, add_currency, remove_currency
from utils.embed import create_embed
from config import BETTING_CHANNEL  # Channel ID for betting messages

class BetCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_bets = {}  # Track active bets using message IDs

    async def manage_bet_lock(self, username, lock_status):
        """Update the bet_lock status in the user's economy file."""
        data = load_economy(username)
        data['bet_lock'] = lock_status
        save_economy(username, data)

    async def can_place_bet(self, username):
        """Check if the user can place a bet (bet_lock is not 1)."""
        data = load_economy(username)
        return data.get('bet_lock', 0) == 0

    async def initiate_bet(self, ctx, amount, user_bet_against):
        """Initiate the bet between two users."""
        if not await self.can_place_bet(ctx.author.name):
            await ctx.send(f"{ctx.author.mention}, you are locked from placing bets. Resolve your previous bet first.")
            return

        if not await self.can_place_bet(user_bet_against.name):
            await ctx.send(f"{user_bet_against.mention} is locked from placing bets. They need to resolve their previous bet first.")
            return

        if amount <= 0:
            await ctx.send("You must bet a positive amount!")
            return

        await self.manage_bet_lock(ctx.author.name, 1)
        await self.manage_bet_lock(user_bet_against.name, 1)

        bet_message = f"{ctx.author.mention} has challenged {user_bet_against.mention} to a bet of {amount} currency!\n" \
                      f"Do you accept or decline, {user_bet_against.mention}? React with ✅ to accept, ❌ to decline."

        bet_embed = await create_embed(
            title="Bet Challenge",
            description=bet_message,
            color=discord.Color.green()
        )

        bet_channel = self.bot.get_channel(BETTING_CHANNEL)
        bet_message = await bet_channel.send(embed=bet_embed)
        await bet_message.add_reaction("✅")
        await bet_message.add_reaction("❌")

        # Store the bet details using message ID
        self.active_bets[bet_message.id] = {
            "challenger": ctx.author,
            "opponent": user_bet_against,
            "amount": amount,
            "ctx": ctx
        }

    async def resolve_bet(self, ctx, winner, loser, amount):
        add_currency(winner.name, amount)
        remove_currency(loser.name, amount)

        await self.manage_bet_lock(winner.name, 0)
        await self.manage_bet_lock(loser.name, 0)

        await ctx.send(f"{winner.mention} wins the bet! {amount} currency has been transferred to them!")
        await ctx.send(f"{loser.mention}, better luck next time!")

    @commands.command()
    async def bet(self, ctx, amount: int, user_bet_against: discord.User):
        """Place a bet against another user."""
        if ctx.author == user_bet_against:
            await ctx.send("You can't bet against yourself!")
            return
        await self.initiate_bet(ctx, amount, user_bet_against)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Handle bet acceptance or decline."""
        if user.bot:
            return

        message_id = reaction.message.id
        if message_id not in self.active_bets:
            return

        bet_data = self.active_bets[message_id]
        challenger = bet_data['challenger']
        opponent = bet_data['opponent']
        amount = bet_data['amount']
        ctx = bet_data['ctx']

        # Ensure only the challenged user can respond
        if user != opponent:
            return

        # Handle reactions
        if str(reaction.emoji) == "✅":
            await ctx.send(f"{opponent.mention} accepted the bet! Let the competition begin!")
            await self.resolve_bet(ctx, opponent, challenger, amount)
        elif str(reaction.emoji) == "❌":
            await ctx.send(f"{opponent.mention} declined the bet. No currency was exchanged.")
            await self.manage_bet_lock(challenger.name, 0)
            await self.manage_bet_lock(opponent.name, 0)

        # Clean up
        del self.active_bets[message_id]

async def setup(bot):
    await bot.add_cog(BetCog(bot))
