import discord
from discord.ext import commands
from utils.llm_api import query_llm

class GetWord(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def get_word(self, ctx):
        """Fetch a random five-letter word from the LLM API."""
        await ctx.send("Generating a word, please wait...")
        word = await query_llm("Give me a random five-letter word.")
        await ctx.send(f"Here's a random word: **{word}**")

async def setup(bot):
    await bot.add_cog(GetWord(bot))
