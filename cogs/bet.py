import discord
from discord.ext import commands
from utils.economy import load_economy, save_economy, add_currency, remove_currency
from utils.embed import create_embed
from config import BETTING_CHANNEL

class BetCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_bets = {}
        self.agreement_phase = {}

    async def manage_bet_lock(self, username, lock_status):
        data = load_economy(username)
        data['bet_lock'] = lock_status
        save_economy(username, data)

    async def can_place_bet(self, username):
        data = load_economy(username)
        return data.get('bet_lock', 0) == 0

    async def initiate_bet(self, ctx, amount, user_bet_against):
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

        bet_message = (
            f"{ctx.author.mention} has challenged {user_bet_against.mention} to a bet of {amount} currency!\n"
            f"Do you accept or decline, {user_bet_against.mention}? React with ✅ to accept, ❌ to decline."
        )
        bet_embed = await create_embed(
            title="Bet Challenge",
            description=bet_message,
            color=discord.Color.green()
        )
        bet_channel = self.bot.get_channel(BETTING_CHANNEL)
        bet_msg = await bet_channel.send(embed=bet_embed)
        await bet_msg.add_reaction("✅")
        await bet_msg.add_reaction("❌")

        self.active_bets[bet_msg.id] = {
            "stage": "challenge",
            "challenger": ctx.author,
            "opponent": user_bet_against,
            "amount": amount,
            "ctx": ctx,
            "channel": bet_channel
        }

    async def resolve_bet(self, ctx, winner, loser, amount):
        add_currency(winner.name, amount)
        remove_currency(loser.name, amount)
        await self.manage_bet_lock(winner.name, 0)
        await self.manage_bet_lock(loser.name, 0)
        resolution_embed = await create_embed(
            title="Bet Resolved",
            description=(
                f"{winner.mention} wins the bet! {amount} currency has been transferred to them!\n"
                f"{loser.mention}, better luck next time!"
            ),
            color=discord.Color.purple()
        )
        await ctx.send(embed=resolution_embed)

    @commands.command()
    async def bet(self, ctx, amount: int, user_bet_against: discord.User):
        if ctx.author == user_bet_against:
            await ctx.send("You can't bet against yourself!")
            return
        await self.initiate_bet(ctx, amount, user_bet_against)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return

        message_id = reaction.message.id

        if message_id in self.active_bets:
            bet_data = self.active_bets[message_id]
            if bet_data["stage"] == "challenge":
                ctx = bet_data["ctx"]
                challenger = bet_data["challenger"]
                opponent = bet_data["opponent"]
                amount = bet_data["amount"]
                channel = bet_data["channel"]

                if user != opponent:
                    return

                if str(reaction.emoji) == "✅":
                    challenger_emoji = chr(127462 + (ord(challenger.name[0].upper()) - ord('A')))
                    opponent_emoji = chr(127462 + (ord(opponent.name[0].upper()) - ord('A')))
                    agreement_message = (
                        f"{challenger.mention} and {opponent.mention}, please vote on the winner of the bet.\n"
                        f"React with {challenger_emoji} for **{challenger.name}** or {opponent_emoji} for **{opponent.name}**."
                    )
                    agreement_embed = await create_embed(
                        title="Bet Resolution",
                        description=agreement_message,
                        color=discord.Color.blue()
                    )
                    agreement_msg = await channel.send(embed=agreement_embed)
                    await agreement_msg.add_reaction(challenger_emoji)
                    await agreement_msg.add_reaction(opponent_emoji)
                    self.agreement_phase[agreement_msg.id] = {
                        "challenger": challenger,
                        "opponent": opponent,
                        "amount": amount,
                        "ctx": ctx,
                        "challenger_emoji": challenger_emoji,
                        "opponent_emoji": opponent_emoji
                    }
                    del self.active_bets[message_id]

                elif str(reaction.emoji) == "❌":
                    decline_embed = await create_embed(
                        title="Bet Declined",
                        description=(
                            f"{opponent.mention} declined the bet against {challenger.mention}. No currency was exchanged."
                        ),
                        color=discord.Color.red()
                    )
                    await channel.send(embed=decline_embed)
                    await self.manage_bet_lock(challenger.name, 0)
                    await self.manage_bet_lock(opponent.name, 0)
                    del self.active_bets[message_id]

async def setup(bot):
    await bot.add_cog(BetCog(bot))
