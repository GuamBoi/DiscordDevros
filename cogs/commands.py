import discord
from discord.ext import commands
from utils.dictionary import get_member_commands, get_moderator_commands
from config import COMMAND_PREFIX, MODERATOR_ROLE_ID


def format_command(cmd):
    return f"**{COMMAND_PREFIX}{cmd['Command_Name']}**: {cmd['Description']}"


def categorize(commands, categories):
    groups = {cat: [] for cat in categories}
    for cmd in commands:
        for cat in cmd.get("Category", []):
            if cat in groups:
                groups[cat].append(cmd)
    return groups


class CommandHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="commands")
    async def commands_list(self, ctx):
        """Show general member commands (Category: general)."""
        cmds = get_member_commands()
        general_cmds = [c for c in cmds if "general" in c.get("Category", []) and "moderator" not in c.get("Category", [])]
        desc = [format_command(c) for c in general_cmds]

        if any(r.id == MODERATOR_ROLE_ID for r in ctx.author.roles):
            desc.append(f"\n_Mod commands available via `{COMMAND_PREFIX}modcommands`_")

        embed = discord.Embed(
            title="📋 General Commands",
            description="\n".join(desc),
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command(name="economycommands")
    async def economy_commands(self, ctx):
        """Show member economy commands (excluding moderator-only)."""
        cmds = get_member_commands()
        econ_cmds = [c for c in cmds if "economy" in c.get("Category", []) and "moderator" not in c.get("Category", [])]
        desc = [format_command(c) for c in econ_cmds]

        embed = discord.Embed(
            title="💰 Economy Commands",
            description="\n".join(desc),
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    @commands.command(name="gamecommands")
    async def game_commands(self, ctx):
        """Show member game and leaderboard commands grouped by game."""
        cmds = get_member_commands()
        cmds = [c for c in cmds if "moderator" not in c.get("Category", [])]
        categories = ["leaderboards", "wordle", "connect4", "battleship", "dice"]
        grouped = categorize(cmds, categories)

        embed = discord.Embed(
            title="🎮 Game Commands",
            description="All commands related to games and leaderboards.",
            color=discord.Color.purple()
        )

        subtitles = {
            "leaderboards": "📊 Leaderboards",
            "wordle": "🟩 Wordle",
            "connect4": "🔴 Connect 4",
            "battleship": "🚢 Battleship",
            "dice": "🎲 Dice Commands"
        }

        for key in categories:
            if grouped[key]:
                value = "\n".join(format_command(cmd) for cmd in grouped[key])
                embed.add_field(name=subtitles.get(key, key.title()), value=value, inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="modcommands")
    @commands.has_role(MODERATOR_ROLE_ID)
    async def mod_commands(self, ctx):
        """Show all moderator commands grouped by category."""
        cmds = get_moderator_commands()
        categories = ["general", "economy", "settings"]
        grouped = categorize(cmds, categories)

        embed = discord.Embed(
            title="🛠️ Moderator Commands",
            description="Moderator-only tools and utilities.",
            color=discord.Color.red()
        )

        subtitles = {
            "general": "📋 General",
            "economy": "💰 Economy Tools",
            "settings": "⚙️ Bot Settings"
        }

        for key in categories:
            if grouped[key]:
                value = "\n".join(format_command(cmd) for cmd in grouped[key])
                embed.add_field(name=subtitles.get(key, key.title()), value=value, inline=False)

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(CommandHelp(bot))
