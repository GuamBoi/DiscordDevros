import discord
from discord.ext import commands
from utils.llm_api import query_llm

class AskLLMCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ask(self, ctx, *, question: str):
        """Command to ask the LLM a question."""
        try:
            response = await query_llm(question)
            await ctx.send(response)
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

# FIX: Make the setup function asynchronous
async def setup(bot):
    await bot.add_cog(AskLLMCog(bot))
