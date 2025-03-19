import discord
from discord.ext import commands
from utils.embed import create_embed
from utils.dictionary import get_command_info
from utils.llm_api import query_llm
from utils.prompts import load_prompts  # New import from prompts.py
from config import BOT_NAME, BOT_VERSION
import asyncio

class CommandHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Load prompt templates once during initialization
        self.prompts = load_prompts()

    @commands.command()
    async def command_help(self, ctx, command_name: str = None):
        """Provide help in a private channel and wait for user responses."""
        if command_name is None:
            await ctx.send("Please specify the command you need help with. Usage: `!command_help <command>`")
            return

        user = ctx.author
        # Create a private channel for the user
        private_channel = await ctx.guild.create_text_channel(f"{user.name}-help")

        # Retrieve command information for LLM context
        command_info = get_command_info(command_name)
        if not command_info:
            await private_channel.send("Sorry, I couldn't find information on that command.")
            return

        llm_context = command_info.get("LLM_Context", "No specific context available.")
        example = command_info.get("Example", "No example available.")
        # Get the prompt name from command info; default to "help_default" if not provided.
        prompt_name = command_info.get("Prompt_Name", "help_default")

        # Retrieve the prompt template from the loaded prompts data.
        prompt_data = self.prompts.get(prompt_name)
        if prompt_data is None:
            # Fall back to help_default if the specified prompt name is not found.
            prompt_data = self.prompts.get("help_default", {
                "LLM_Message": "Context: {LLM_Context}\nExample: {Example}\nUser Question: {USER_QUESTION}"
            })

        llm_message_template = prompt_data.get("LLM_Message")

        # Prepare the embed with the command help message.
        embed = discord.Embed(
            title="Command Help",
            description=f"Hey {user.mention}, how can I help you with the `{command_name}` command?\n\n{llm_context}",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Please use `!bye` at the end of our conversation to delete this channel.")
        
        # Send the embed in the private channel.
        await private_channel.send(embed=embed)

        # Wait for the user's response.
        def check(m):
            return m.author == user and m.channel == private_channel

        try:
            user_response = await self.bot.wait_for("message", check=check)

            # Build the final prompt by replacing the placeholders in the template.
            final_prompt = llm_message_template.format(
                LLM_Context=llm_context,
                Example=example,
                USER_QUESTION=user_response.content
            )
            
            # Query the LLM using your llm_api.py logic and show the typing indicator in the private channel.
            llm_response = await query_llm(ctx, final_prompt, private_channel=private_channel)
            
            # Create an embed for the LLM response.
            embed = await create_embed(
                title=f"{command_name} Help",
                description=llm_response,
                footer_text=f"{BOT_NAME} v{BOT_VERSION}"
            )
            await private_channel.send(embed=embed)

            # Wait a minute before closing the channel.
            await asyncio.sleep(60)
            await private_channel.delete()

        except asyncio.TimeoutError:
            await private_channel.send("No response received. Closing this help session.")
            await private_channel.delete()

    @commands.command()
    async def explain(self, ctx, command_name: str = None):
        """Explain a command with its description and example."""
        if command_name is None:
            await ctx.send("Please specify the command you need help with. Usage: `!explain <command>`")
            return

        # Retrieve command information.
        command_info = get_command_info(command_name)
        if not command_info:
            await ctx.send("Sorry, I couldn't find information on that command.")
            return

        description = command_info.get("Description", "No description available.")
        example = command_info.get("Example", "No example available.")

        embed = await create_embed(
            title=f"Command: {command_name}",
            description=f"**Description:**\n{description}\n\n**Example:**\n{example}",
            footer_text=f"{BOT_NAME} v{BOT_VERSION}"
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CommandHelp(bot))
