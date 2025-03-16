# cogs/game_invite.py

import discord
from discord.ext import commands
from utils.llm_api import query_llm  # Import the LLM query function
from utils.embed import create_embed  # Import the embed function
from config import INVITE_CHANNEL  # Import invite channel ID from config

class GameInviteCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Helper function to generate an AI-enhanced game invite message
    async def generate_ai_invite(self, game_name):
        prompt = (
            f"Write a short, engaging invitation message encouraging others to join a game of {game_name}. "
            "Make it fun, casual, and exciting."
        )
        try:
            response = await query_llm(prompt)
            return response
        except Exception as e:
            return f"Come join the fun in {game_name}! 🎮"

    @commands.command()
    async def invite(self, ctx):
        """Creates a game invite message with a static intro and an AI-generated follow-up."""
        if ctx.author.voice and ctx.author.voice.channel:
            voice_channel = ctx.author.voice.channel
            game = ctx.author.activity.name if ctx.author.activity else None

            if game:
                role = discord.utils.get(ctx.guild.roles, name=game)
                role_mention = role.mention if role else "@everyone"

                invite_channel = ctx.guild.get_channel(INVITE_CHANNEL)
                if invite_channel:
                    async with ctx.typing():
                        ai_invite_message = await self.generate_ai_invite(game)

                    # Static message followed by AI-generated text
                    invite_message = (
                        f"{ctx.author.mention} is playing **{game}** in {voice_channel.mention}!\n\n"
                        f"📢 {ai_invite_message}"
                    )

                    embed = create_embed(
                        title="🎮 Game Invitation",
                        description=invite_message,
                        color=discord.Color.green()
                    )
                    await invite_channel.send(embed=embed)
                else:
                    await ctx.send("Invite channel not found.")
            else:
                await ctx.send("You need to be playing a game to use this command.")
        else:
            await ctx.send("You need to be in a voice channel to use this command.")

        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(GameInviteCog(bot))
