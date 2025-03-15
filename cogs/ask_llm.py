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
            # Call the query_llm function from llm_api.py to get the response
            response = await query_llm(question)
            await ctx.send(response)  # Send the LLM's response back to the Discord channel
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

# Setup function to add the cog to the bot
def setup(bot):
    bot.add_cog(AskLLMCog(bot))
