# cogs/bet.py

import discord
from discord.ext import commands
from utils.economy import load_economy, save_economy, add_currency, remove_currency
from utils.embed import create_embed
from config import BETTING_CHANNEL  # Channel ID for betting messages
import random

class BetCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def manage_bet_lock(self, username, lock_status):
        """Update the bet_lock status in the user's economy file."""
        data = load_economy(username)
        data['bet_lock'] = lock_status
        save_economy(username, data)

    async def can_place_bet(self, username):
        """Check if the user can place a bet (bet_lock is not 1)."""
        data = load_economy(username)
        return data.get('bet_lock', 0) == 0  # 0 means they can bet

    async def initiate_bet(self, ctx, amount, user_bet_against):
        """Initiate the bet between two users."""
        # Ensure both users can bet
        if not await self.can_place_bet(ctx.author.name):
            await ctx.send(f"{ctx.author.mention}, you are locked from placing bets. Resolve your previous bet first.")
            return
        
        if not await self.can_place_bet(user_bet_against.name):
            await ctx.send(f"{user_bet_against.mention} is locked from placing bets. They need to resolve their previous bet first.")
            return

        # Ensure the amount is valid
        if amount <= 0:
            await ctx.send("You must bet a positive amount!")
            return

        # Lock both users from placing new bets until this one is resolved
        await self.manage_bet_lock(ctx.author.name, 1)
        await self.manage_bet_lock(user_bet_against.name, 1)

        # Send the bet invitation to the betting channel
        bet_message = f"{ctx.author.mention} has challenged {user_bet_against.mention} to a bet of {amount} currency!\n" \
                      f"Do you accept or decline, {user_bet_against.mention}? React with ✅ to accept, ❌ to decline."

        bet_embed = create_embed(
            title="Bet Challenge",
            description=bet_message,
            color=discord.Color.green()
        )

        bet_channel = self.bot.get_channel(BETTING_CHANNEL)
        bet_message = await bet_channel.send(embed=bet_embed)
        await bet_message.add_reaction("✅")
        await bet_message.add_reaction("❌")

        # Wait for the reaction from the bet recipient
        def check_reaction(reaction, user):
            return user == user_bet_against and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == bet_message.id

        try:
            reaction, _ = await self.bot.wait_for('reaction_add', timeout=60.0, check=check_reaction)
            if str(reaction.emoji) == "✅":
                await ctx.send(f"{user_bet_against.mention} has accepted the bet! The challenge is on!")
                # You can handle the result later once both agree on the winner.
            else:
                await ctx.send(f"{user_bet_against.mention} has declined the bet.")
                # Unlock both users as the bet was declined
                await self.manage_bet_lock(ctx.author.name, 0)
                await self.manage_bet_lock(user_bet_against.name, 0)
                return
        except TimeoutError:
            await ctx.send(f"{user_bet_against.mention} did not respond in time. The bet is canceled.")
            # Unlock both users if they don't respond
            await self.manage_bet_lock(ctx.author.name, 0)
            await self.manage_bet_lock(user_bet_against.name, 0)

    async def resolve_bet(self, ctx, winner, loser, amount):
        """Resolve the bet and transfer the currency to the winner."""
        # Add currency to the winner and remove it from the loser
        add_currency(winner, amount)
        remove_currency(loser, amount)

        # Unlock both users after the bet is resolved
        await self.manage_bet_lock(winner, 0)
        await self.manage_bet_lock(loser, 0)

        # Notify both users of the outcome
        await ctx.send(f"{winner.mention} wins the bet! {amount} currency has been transferred to them!")
        await ctx.send(f"{loser.mention}, better luck next time!")

    @commands.command()
    async def bet(self, ctx, amount: int, user_bet_against: discord.User):
        """Place a bet against another user."""
        if ctx.author == user_bet_against:
            await ctx.send("You can't bet against yourself!")
            return
        
        await self.initiate_bet(ctx, amount, user_bet_against)

    @commands.command()
    async def choose_winner(self, ctx, winner: discord.User, loser: discord.User, amount: int):
        """Choose the winner of the bet. Only both users can choose."""
        # Ensure the bet is resolved by both participants
        if ctx.author != winner and ctx.author != loser:
            await ctx.send("Only the participants of the bet can resolve it.")
            return
        
        if winner != loser:
            await self.resolve_bet(ctx, winner, loser, amount)
        else:
            await ctx.send("Both users must select a different winner!")

async def setup(bot):
    await bot.add_cog(BetCog(bot))
