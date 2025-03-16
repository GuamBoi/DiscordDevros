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
            # Show the bot is typing
            async with ctx.typing():
                response = await query_llm(question)
            await ctx.send(response)
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

# The setup function must be asynchronous!
async def setup(bot):
    await bot.add_cog(AskLLMCog(bot))
