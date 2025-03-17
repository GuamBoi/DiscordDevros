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
            # Pass ctx to query_llm to show the typing indicator
            response = await query_llm(ctx, question)

            # Use display_name for a readable title, and mention in the message body
            embed = create_embed(
                title=f"Responce:",
                description=response,
                footer_text="<@{ctx.author.id}> This message was generated by AI"
            )

            await ctx.send(f"{ctx.author.mention}", embed=embed)  # Ensure user is mentioned
        except Exception as e:
            error_embed = create_embed(
                title="❌ Error",
                description=f"An error occurred: {e}",
                color=discord.Color.red(),
                footer_text="Message generated by AI"
            )
            await ctx.send(embed=error_embed)

# The setup function must be asynchronous!
async def setup(bot):
    await bot.add_cog(AskLLMCog(bot))
