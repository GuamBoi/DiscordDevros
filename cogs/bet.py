import discord
from discord.ext import commands
from utils.economy import load_economy, save_economy, add_currency, remove_currency, user_key
from utils.embed import create_embed
from config import BETTING_CHANNEL, CURRENCY_NAME, CURRENCY_SYMBOL

class BetCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_bets = {}      # Active bet challenges (by message ID)
        self.agreement_phase = {}  # Active agreement messages (by message ID)

    def _letter_emoji_for(self, user: discord.abc.User) -> str:
        raw = getattr(user, "display_name", None) or user.name
        for ch in raw.upper():
            if "A" <= ch <= "Z":
                return chr(0x1F1E6 + (ord(ch) - ord("A")))
        return "🅰️"

    async def manage_bet_lock(self, member: discord.abc.User, lock_status):
        key = user_key(member)
        data = load_economy(key)
        data["bet_lock"] = lock_status
        save_economy(key, data)

    async def can_place_bet(self, member: discord.abc.User):
        data = load_economy(user_key(member))
        return data.get("bet_lock", 0) == 0

    async def initiate_bet(self, ctx, amount, user_bet_against, bet_explanation=None):
        if not await self.can_place_bet(ctx.author):
            await ctx.send(f"{ctx.author.mention}, you are locked from placing bets. Resolve your previous bet first.")
            return
        if not await self.can_place_bet(user_bet_against):
            await ctx.send(f"{user_bet_against.mention} is locked from placing bets. They need to resolve their previous bet first.")
            return
        if amount <= 0:
            await ctx.send("You must bet a positive amount!")
            return

        remove_currency(user_key(ctx.author), amount)
        remove_currency(user_key(user_bet_against), amount)

        await self.manage_bet_lock(ctx.author, 1)
        await self.manage_bet_lock(user_bet_against, 1)

        bet_message = f"{ctx.author.mention} has challenged {user_bet_against.mention} to a bet of {CURRENCY_SYMBOL}{amount} {CURRENCY_NAME}!\n\n"
        if bet_explanation:
            bet_message += f"Bet Explanation: \n{bet_explanation}\n\n"
        bet_message += f"Do you accept or decline, {user_bet_against.mention}? React with ✅ to accept, ❌ to decline."

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
            "channel": bet_channel,
            "explanation": bet_explanation
        }

    async def resolve_bet(self, ctx, winner, loser, amount, bet_explanation=None):
        add_currency(user_key(winner), 2 * amount)
        await self.manage_bet_lock(winner, 0)
        await self.manage_bet_lock(loser, 0)

        resolution_description = (
            f"{winner.mention} wins the bet! {CURRENCY_SYMBOL}{2 * amount} {CURRENCY_NAME} has been transferred to them!\n"
            f"{loser.mention} lost {CURRENCY_SYMBOL}{amount} {CURRENCY_NAME}."
        )

        if bet_explanation:
            resolution_description += f"\n\nBet Explanation: \n{bet_explanation}"

        resolution_embed = await create_embed(
            title="Bet Resolved",
            description=resolution_description,
            color=discord.Color.green()
        )

        betting_channel = self.bot.get_channel(BETTING_CHANNEL)
        await betting_channel.send(embed=resolution_embed)

    @commands.command()
    async def bet(self, ctx, amount: int, user_bet_against: discord.User, *, bet_explanation: str = None):
        if ctx.author == user_bet_against:
            await ctx.send("You can't bet against yourself!")
            return

        try:
            await ctx.message.delete()
        except discord.Forbidden:
            await ctx.send("I don't have permission to delete messages.")

        await self.initiate_bet(ctx, amount, user_bet_against, bet_explanation)

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
                bet_explanation = bet_data.get("explanation")

                if user.id != opponent.id:
                    return

                if str(reaction.emoji) == "✅":
                    challenger_emoji = self._letter_emoji_for(challenger)
                    opponent_emoji = self._letter_emoji_for(opponent)

                    agreement_message = f"{challenger.mention} and {opponent.mention}, please vote on the winner of the bet.\n\n"
                    if bet_explanation:
                        agreement_message += f"Bet Explanation: \n{bet_explanation}\n\n"

                    agreement_message += (
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
                        "opponent_emoji": opponent_emoji,
                        "explanation": bet_explanation
                    }

                    await reaction.message.delete()
                    del self.active_bets[message_id]

                elif str(reaction.emoji) == "❌":
                    refund_description = (
                        f"{opponent.mention} declined the bet against {challenger.mention}. No {CURRENCY_NAME} was exchanged.\n"
                        f"Both players have been refunded their bet of {CURRENCY_SYMBOL}{amount} {CURRENCY_NAME}."
                    )

                    if bet_explanation:
                        refund_description += f"\n\nBet Explanation: \n{bet_explanation}"

                    refund_embed = await create_embed(
                        title="Bet Declined",
                        description=refund_description,
                        color=discord.Color.red()
                    )

                    await channel.send(embed=refund_embed)
                    add_currency(user_key(challenger), amount)
                    add_currency(user_key(opponent), amount)
                    await self.manage_bet_lock(challenger, 0)
                    await self.manage_bet_lock(opponent, 0)

                    await reaction.message.delete()
                    del self.active_bets[message_id]

        elif message_id in self.agreement_phase:
            agreement_data = self.agreement_phase[message_id]
            challenger = agreement_data["challenger"]
            opponent = agreement_data["opponent"]
            ctx = agreement_data["ctx"]
            amount = agreement_data["amount"]
            challenger_emoji = agreement_data["challenger_emoji"]
            opponent_emoji = agreement_data["opponent_emoji"]
            bet_explanation = agreement_data.get("explanation")

            if str(reaction.emoji) not in [challenger_emoji, opponent_emoji]:
                return

            message = reaction.message
            for react in message.reactions:
                if str(react.emoji) in [challenger_emoji, opponent_emoji]:
                    users_reacted = [u async for u in react.users() if not u.bot]
                    if challenger in users_reacted and opponent in users_reacted:
                        winner = challenger if str(react.emoji) == challenger_emoji else opponent
                        loser = opponent if winner == challenger else challenger

                        await self.resolve_bet(ctx, winner, loser, amount, bet_explanation)
                        del self.agreement_phase[message_id]
                        return

async def setup(bot):
    await bot.add_cog(BetCog(bot))
