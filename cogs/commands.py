import os
import json
import discord
from discord.ext import commands
from utils.embed import create_embed
from utils.llm_api import query_llm
from config import COMMAND_PREFIX, HELP_COMMAND_CHANNEL_CATEGORY

# Path to the commands JSON file (adjust folder name/path as needed)
COMMANDS_JSON_PATH = os.path.join("data", "commands.json")

def load_commands_data():
    """Load the commands JSON file and return its data."""
    try:
        with open(COMMANDS_JSON_PATH, "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading commands JSON: {e}")
        return None

class CommandHelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Map user_id to private channel object
        self.active_private_channels = {}

    @commands.command(name="commands", help="Displays a list of all available commands with descriptions and usage examples.")
    async def show_commands(self, ctx):
        commands_data = load_commands_data()
        if not commands_data:
            await ctx.send("Error: Could not load commands information.")
            return

        fields = []
        for cmd in commands_data:
            command_name = cmd.get("Command_Name", "N/A")
            description = cmd.get("Description", "No description provided.")
            example = cmd.get("Example", "No example provided.")
            field_value = f"**Description:** {description}\n**Example:** `{example}`"
            fields.append({"name": f"!{command_name}", "value": field_value, "inline": False})

        embed = create_embed(
            title="Available Commands",
            description="Below is a list of all commands along with their descriptions and example usage:",
            fields=fields,
            color=0x00FF00
        )
        await ctx.send(embed=embed)

    @commands.command(name="command_help", help="Provides detailed help for a specific command using LLM context.")
    async def command_help(self, ctx, command_name: str):
        commands_data = load_commands_data()
        if not commands_data:
            await ctx.send("Error: Could not load commands information.")
            return

        # Find the command info by name (case-insensitive)
        command_info = next(
            (cmd for cmd in commands_data if cmd.get("Command_Name", "").lower() == command_name.lower()),
            None
        )
        if not command_info:
            await ctx.send(f"Command '{command_name}' not found.")
            return

        llm_context = command_info.get("LLM_Context", "")
        if not llm_context:
            await ctx.send(f"No LLM context available for command '{command_name}'.")
            return

        # Check if the user already has an active private channel
        if ctx.author.id in self.active_private_channels:
            private_channel = self.active_private_channels[ctx.author.id]
            await ctx.send(f"You already have a private channel: {private_channel.mention}")
            return

        # Locate the category for private channels using the new config value.
        category = discord.utils.get(ctx.guild.categories, id=HELP_COMMAND_CHANNEL_CATEGORY)
        if not category:
            await ctx.send("Error: Private channel category not found.")
            return

        # Set permission overwrites so only the user and the bot can see the channel
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        channel_name = f"{ctx.author.name}-help"
        try:
            private_channel = await ctx.guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites
            )
            self.active_private_channels[ctx.author.id] = private_channel
        except Exception as e:
            await ctx.send(f"Failed to create private channel: {e}")
            return

        # Use the LLM context as the initial prompt to your LLM server.
        response = await query_llm(ctx, llm_context)
        await private_channel.send(f"LLM Response for command **{command_name}**:\n{response}")
        await ctx.send(f"Private channel created: {private_channel.mention}")

    @commands.command(name="bye", help="Closes your private help channel.")
    async def bye(self, ctx):
        # Ensure this command is run in a private channel that you created.
        if ctx.author.id not in self.active_private_channels:
            await ctx.send("You don't have an active private channel.")
            return

        private_channel = self.active_private_channels[ctx.author.id]
        if ctx.channel.id != private_channel.id:
            await ctx.send("This command must be used in your private help channel.")
            return

        try:
            await ctx.channel.delete(reason="User requested channel closure.")
            del self.active_private_channels[ctx.author.id]
        except Exception as e:
            await ctx.send(f"Failed to delete channel: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore messages from bots.
        if message.author.bot:
            return

        # Check if this message is in one of our active private channels.
        if message.channel.id not in [ch.id for ch in self.active_private_channels.values()]:
            return

        # If the message starts with the command prefix, let the command handler process it.
        if message.content.startswith(COMMAND_PREFIX):
            return

        # Forward the user's message to the LLM automatically.
        try:
            async with message.channel.typing():
                # Using the message content as prompt.
                response = await query_llm(message, message.content)
            await message.channel.send(response)
        except Exception as e:
            await message.channel.send(f"Error processing your message: {e}")

async def setup(bot):
    await bot.add_cog(CommandHelpCog(bot))
