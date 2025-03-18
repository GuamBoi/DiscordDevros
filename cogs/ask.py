import discord
from discord.ext import commands
from utils.llm_api import query_llm
from utils.embed import create_embed

class AskLLMCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ask(self, ctx, *, question: str):
        """Command to ask the LLM a question."""
        try:
            # Pass ctx to query_llm to show the typing indicator and process the response.
            response = await query_llm(ctx, question)

            # Create an embed with the response (await the async create_embed function)
            embed = await create_embed(
                title="Response:",
                description=response,
                footer_text="Message generated by AI"
            )

            # Send the embed without pinging the original user.
            await ctx.send(embed=embed)
        except Exception as e:
            # Create an error embed (await the async create_embed function)
            error_embed = await create_embed(
                title="❌ Error",
                description=f"An error occurred: {e}",
                color=discord.Color.red(),
                footer_text="Message generated by AI"
            )
            await ctx.send(embed=error_embed)

# The setup function must be asynchronous!
async def setup(bot):
    await bot.add_cog(AskLLMCog(bot))
