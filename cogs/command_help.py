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

    @commands.command(name="command_help", aliases=["commands"])  # Keep "commands", remove "h"
    async def command_help(self, ctx, *, command_name=None):
        """
        This command provides help for a specific command (via DM) or lists all available commands
        if no command name is given.
        """
        if command_name:
            # If a command name is provided, give detailed help for that command
            command_info = commands_list.get(command_name.lower())

            if command_info:
                # Prepare command info and send it to the LLM for further processing
                user_question = f"How can I use the command '{command_name}'?"
                # Call the function that queries the LLM with command info and user question
                response = await query_llm_with_command_info(command_info, user_question, ctx)
                # Send the response to the user via DM
                await ctx.author.send(response)
            else:
                await ctx.send(f"Command '{command_name}' not found. Use `{COMMAND_PREFIX}command_help` for a list of commands.")
        else:
            # If no command name is provided, list all available commands in a blue embed
            help_message = ""
            for command in commands_list:
                command_info = commands_list[command]
                description = command_info.get("Description", "No description available.")
                example = command_info.get("Example", "No example available.")
                
                help_message += f"**{COMMAND_PREFIX}{command}**\n"
                help_message += f"**Description**: {description}\n"
                help_message += f"**Example**: {example}\n\n"

            # Create the embed with all commands
            embed = await create_embed(
                title="Command List",
                description=help_message,
                color=discord.Color.blue()  # Embed color set to blue
            )

            # Send the embed to the user
            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        # Check if the message is sent via DM (Direct Message)
        if isinstance(message.channel, discord.DMChannel):
            # Skip the bot's own messages to avoid loops
            if message.author == self.bot.user:
                return

            # Get the user's message content
            user_message = message.content

            # Query the LLM for a response using the user's message.
            # Pass message.channel as ctx since it supports the typing() method.
            response = await query_llm(ctx=message.channel, prompt=user_message)
            
            # Use the embed utility to format the response
            embed = await create_embed(
                title="Response from the Bot",
                description=response,
                color=discord.Color.blue(),  # Customize the color if desired
            )

            # Send the embed back to the user via DM
            await message.channel.send(embed=embed)

# The setup function must be asynchronous!
async def setup(bot):
    await bot.add_cog(CommandHelp(bot))
