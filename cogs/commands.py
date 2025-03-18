import os
import json
import discord
from discord.ext import commands
from utils.embed import create_embed
from utils.llm_api import query_llm
from config import COMMAND_PREFIX, HELP_COMMAND_CHANNEL_CATEGORY, BOT_NAME

# Path to the commands JSON file
COMMANDS_JSON_PATH = os.path.join("data", "commands.json")

def load_commands_data():
    """Load the commands JSON file and replace any placeholders using config.py values."""
    try:
        with open(COMMANDS_JSON_PATH, "r") as f:
            data = json.load(f)
        
        # Convert config variables to a dictionary
        config_vars = {k: v for k, v in vars(config).items() if not k.startswith("__") and not callable(v)}

        # Perform the placeholder replacement
        for cmd in data:
            for key in ["Description", "LLM_Context"]:
                if key in cmd and isinstance(cmd[key], str):
                    for var_name, var_value in config_vars.items():
                        placeholder = f"{{{var_name}}}"
                        cmd[key] = cmd[key].replace(placeholder, str(var_value))

        return data
    except Exception as e:
        print(f"Error loading commands JSON: {e}")
        return None

class CommandHelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
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

        if ctx.author.id in self.active_private_channels:
            private_channel = self.active_private_channels[ctx.author.id]
            await ctx.send(f"You already have a private channel: {private_channel.mention}")
            return

        category = discord.utils.get(ctx.guild.categories, id=HELP_COMMAND_CHANNEL_CATEGORY)
        if not category:
            await ctx.send("Error: Private channel category not found.")
            return

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

        response = await query_llm(ctx, llm_context)
        await private_channel.send(f"LLM Response for command **{command_name}**:\n{response}")
        await ctx.send(f"Private channel created: {private_channel.mention}")

    @commands.command(name="bye", help="Closes your private help channel.")
    async def bye(self, ctx):
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

async def setup(bot):
    await bot.add_cog(CommandHelpCog(bot))
