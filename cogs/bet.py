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
        if not await self.can_place_bet(ctx.author.name) or not await self.can_place_bet(user_bet_against.name):
            await ctx.send("One or both users are locked from betting. Resolve previous bets first.")
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
            "ctx": ctx
        }

    async def resolve_bet(self, ctx, winner, loser, amount):
        add_currency(winner.name, amount)
        remove_currency(loser.name, amount)
        await self.manage_bet_lock(winner.name, 0)
        await self.manage_bet_lock(loser.name, 0)
        await ctx.send(f"{winner.mention} wins the bet! {amount} currency has been transferred to them!")

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
            stage = bet_data.get("stage")
            ctx = bet_data["ctx"]
            challenger = bet_data["challenger"]
            opponent = bet_data["opponent"]
            amount = bet_data["amount"]

            if stage == "challenge" and user == opponent:
                if str(reaction.emoji) == "✅":
                    await ctx.send(f"{opponent.mention} accepted the bet! Both users must now agree on the winner.")
                    
                    challenger_emoji = f":regional_indicator_{challenger.name[0].lower()}:"
                    opponent_emoji = f":regional_indicator_{opponent.name[0].lower()}:"

                    agreement_embed = await create_embed(
                        title="Bet Resolution",
                        description=(
                            f"{challenger.mention} and {opponent.mention}, react to decide the winner.\n"
                            f"React with {challenger_emoji} for {challenger.name} or {opponent_emoji} for {opponent.name}."
                        ),
                        color=discord.Color.blue()
                    )
                    agreement_msg = await ctx.send(embed=agreement_embed)
                    await agreement_msg.add_reaction(challenger_emoji)
                    await agreement_msg.add_reaction(opponent_emoji)
                    
                    self.agreement_phase[agreement_msg.id] = {
                        "challenger": challenger,
                        "opponent": opponent,
                        "amount": amount,
                        "ctx": ctx
                    }

                    del self.active_bets[message_id]

            elif message_id in self.agreement_phase:
                agreement_data = self.agreement_phase[message_id]
                emoji_used = str(reaction.emoji)
                
                if emoji_used in [f":regional_indicator_{agreement_data['challenger'].name[0].lower()}:",
                                  f":regional_indicator_{agreement_data['opponent'].name[0].lower()}:"]:
                    if len(set(reaction.message.reactions)) == 2:  # Both reacted
                        if reaction.message.reactions[0].emoji == reaction.message.reactions[1].emoji:
                            winner = agreement_data['challenger'] if emoji_used == f":regional_indicator_{agreement_data['challenger'].name[0].lower()}:" else agreement_data['opponent']
                            loser = agreement_data['opponent'] if winner == agreement_data['challenger'] else agreement_data['challenger']
                            await self.resolve_bet(ctx, winner, loser, agreement_data['amount'])
                            del self.agreement_phase[message_id]
                        else:
                            await ctx.send("Users disagreed on the result. Please try again to resolve the bet.")

async def setup(bot):
    await bot.add_cog(BetCog(bot))
