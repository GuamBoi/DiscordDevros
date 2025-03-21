import discord
from discord.ext import commands
from utils.llm_api import query_llm, query_llm_with_command_info
from utils.embed import create_embed  # Import the embed function
from config import COMMAND_PREFIX
import json
import os

# Load the commands from the commands.json file
def load_commands():
    with open('data/commands.json', 'r') as f:
        return {cmd['Command_Name'].lower(): cmd for cmd in json.load(f)}

commands_list = load_commands()  # Changed to dictionary

class CommandHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="command_help", aliases=["h", "commands"])
    async def command_help(self, ctx, *, command_name=None):
        """
        This command is responsible for providing help with a specific command or
        listing available commands if no command name is given.
        """
        if command_name:
            # If a command name is provided, give detailed help for that command
            command_info = commands_list.get(command_name.lower())

            if command_info:
                # Prepare command info and send it to LLM for further processing
                description = command_info.get("Description", "No description available.")
                user_question = f"How can I use the command '{command_name}'?"
                # Call the function that queries the LLM with command info and user question
                response = await query_llm_with_command_info(command_info, user_question, ctx)
                # Send the response to the private channel or current channel
                await ctx.author.send(response)
            else:
                await ctx.send(f"Command '{command_name}' not found. Use `{COMMAND_PREFIX}command_help` for a list of commands.")
        else:
            # If no command name is provided, list all available commands
            help_message = "Here are the available commands:\n"
            for command_name in commands_list:
                help_message += f" - `{COMMAND_PREFIX}{command_name}`\n"
            help_message += f"Use `{COMMAND_PREFIX}command_help <command_name>` for more information on a specific command."
            await ctx.send(help_message)

    @commands.Cog.listener()
    async def on_message(self, message):
        # Check if the message is sent via DM (Direct Message)
        if isinstance(message.channel, discord.DMChannel):
            # Skip the bot's own messages to avoid loops
            if message.author == self.bot.user:
                return

            # Get the message the user sent
            user_message = message.content

            # Query the LLM for a response using the user's message
            response = await query_llm(user_message)  # Using the generic query_llm for a more general response
            
            # Use the embed utility to format the response
            embed = await create_embed(
                title="Response from the Bot",
                description=response,
                color=discord.Color.blue(),  # You can change the color if you prefer
            )

            # Send the embed back to the user via DM
            await message.channel.send(embed=embed)

# The setup function must be asynchronous!
async def setup(bot):
    await bot.add_cog(CommandHelp(bot))
