import discord
from discord.ext import commands
from utils.embed import create_embed
from utils.dictionary import get_command_info
from utils.llm_api import query_llm
from config import BOT_NAME, BOT_VERSION
import asyncio

class CommandHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def explain(self, ctx, command_name: str):
        """Provides help information about a specific command."""
        # Get the command information from the dictionary
        command_info = get_command_info(command_name)
        if not command_info:
            await ctx.send("Sorry, I couldn't find information on that command.")
            return

        description = command_info.get("Description", "No description available.")
        example = command_info.get("Example", "No example available.")  # Get the example (if available)
        
        embed = await create_embed(
            title=f"{command_name} Explained",
            description=f"{description}\n\nExample: {example}",
            footer_text=f"{BOT_NAME} v{BOT_VERSION}"
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def command_help_private(self, ctx, command_name: str):
        """Provide help in a private channel and wait for user responses."""
        user = ctx.author
        # Create a private channel for the user
        private_channel = await ctx.guild.create_text_channel(f"{user.name}-help")

        # Retrieve command information for LLM context
        command_info = get_command_info(command_name)
        if not command_info:
            await private_channel.send("Sorry, I couldn't find information on that command.")
            return

        llm_context = command_info.get("LLM_Context", "No specific context available.")
        example = command_info.get("Example", "No example available.")  # Get the example (if available)

        # Ask the user how you can help them with the command
        await private_channel.send(f"Hey {user.mention}, how can I help you with the `{command_name}` command?")
        await private_channel.send(f"Please use `!bye` at the end of our conversation to delete this channel.")

        # Wait for the user's response
        def check(m):
            return m.author == user and m.channel == private_channel

        try:
            user_response = await self.bot.wait_for("message", check=check, timeout=3600)
            
            # Combine LLM context, example, and the user's question to form the prompt
            prompt = f"{llm_context}\nExample: {example}\nUser's question: {user_response.content}"
            
            # Query the LLM using your llm_api.py logic
            llm_response = await query_llm(ctx, prompt)
            
            # Create an embed for the LLM response
            embed = await create_embed(
                title=f"{command_name} Help",
                description=llm_response,
                footer_text=f"{BOT_NAME} v{BOT_VERSION}"
            )
            await private_channel.send(embed=embed)

            # Wait a minute before closing the channel
            await asyncio.sleep(60)
            await private_channel.delete()

        except asyncio.TimeoutError:
            await private_channel.send("No response received. Closing this help session.")
            await private_channel.delete()

async def setup(bot):
    await bot.add_cog(CommandHelp(bot))
