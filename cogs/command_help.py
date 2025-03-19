import discord
from discord.ext import commands
from utils.llm_api import query_llm, query_llm_with_command_info
from config import COMMAND_PREFIX
import json
import os

# Load the commands from the commands.json file
def load_commands():
    with open('data/commands.json', 'r') as f:
        return json.load(f)

commands = load_commands()

class CommandHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help", aliases=["h", "commands"])
    async def help_command(self, ctx, *, command_name=None):
        """
        This command is responsible for providing help with a specific command or
        listing available commands if no command name is given.
        """
        if command_name:
            # If a command name is provided, give detailed help for that command
            command_info = commands.get(command_name.lower())

            if command_info:
                # Prepare command info and send it to LLM for further processing
                description = command_info.get("Description", "No description available.")
                user_question = f"How can I use the command '{command_name}'?"
                # Call the function that queries the LLM with command info and user question
                response = await query_llm_with_command_info(command_name, user_question, ctx)
                # Send the response to the private channel or current channel
                await ctx.author.send(response)
            else:
                await ctx.send(f"Command '{command_name}' not found. Use `{COMMAND_PREFIX}help` for a list of commands.")
        else:
            # If no command name is provided, list all available commands
            help_message = "Here are the available commands:\n"
            for command_name in commands:
                help_message += f" - `{COMMAND_PREFIX}{command_name}`\n"
            help_message += f"Use `{COMMAND_PREFIX}help <command_name>` for more information on a specific command."
            await ctx.send(help_message)

# The setup function must be asynchronous!
async def setup(bot):
    await bot.add_cog(CommandHelp(bot))
