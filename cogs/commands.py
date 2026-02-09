import discord
from discord.ext import commands
from utils.dictionary import get_member_commands, get_moderator_commands
from config import COMMAND_PREFIX, MODERATOR_ROLE_ID

# Discord embed field/value limits (practical guardrails)
_EMBED_DESC_LIMIT = 4096
_FIELD_VALUE_LIMIT = 1024

def format_command(cmd, include_examples: bool = True) -> str:
    """
    Format a command entry as:
      **!command**: description
      _Example_: ...
    """
    name = cmd.get("Command_Name", "unknown")
    desc = cmd.get("Description", "").strip()

    lines = [f"**{COMMAND_PREFIX}{name}**: {desc}" if desc else f"**{COMMAND_PREFIX}{name}**"]

    if include_examples:
        ex = (cmd.get("Example") or "").strip()
        if ex:
            # keep it readable; Example strings already contain pipes/backticks
            lines.append(f"_Example_: {ex}")

    return "\n".join(lines)

def categorize(cmds, categories):
    groups = {cat: [] for cat in categories}
    for cmd in cmds:
        for cat in cmd.get("Category", []):
            if cat in groups:
                groups[cat].append(cmd)
    return groups

def _dedupe_by_name(cmds):
    """Prevent duplicate entries if your command list contains duplicates."""
    seen = set()
    out = []
    for c in cmds:
        name = c.get("Command_Name")
        if not name or name in seen:
            continue
        seen.add(name)
        out.append(c)
    return out

def _chunk_lines_to_field_values(lines, limit=_FIELD_VALUE_LIMIT):
    """
    Takes a list of pre-formatted command blocks (each block may be multi-line),
    and splits into multiple field values if needed to avoid the 1024 char limit.
    """
    chunks = []
    current = ""
    for block in lines:
        candidate = (current + "\n\n" + block) if current else block
        if len(candidate) <= limit:
            current = candidate
        else:
            if current:
                chunks.append(current)
            # If a single block is too large, hard-split it (rare)
            if len(block) > limit:
                chunks.append(block[:limit - 1] + "…")
                current = ""
            else:
                current = block
    if current:
        chunks.append(current)
    return chunks

class CommandHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _delete_invocation(self, ctx) -> None:
        """Delete the user's command message (best-effort)."""
        try:
            await ctx.message.delete()
        except (discord.NotFound, discord.Forbidden):
            pass

    @commands.command(name="commands")
    async def commands_list(self, ctx):
        """Show general member commands (Category: general)."""
        cmds = _dedupe_by_name(get_member_commands())
        general_cmds = [
            c for c in cmds
            if "general" in c.get("Category", []) and "moderator" not in c.get("Category", [])
        ]

        blocks = [format_command(c, include_examples=True) for c in general_cmds]

        # Description embeds get cramped quickly; keep in description but guard size.
        description = "\n\n".join(blocks) if blocks else "_No commands found._"
        if len(description) > _EMBED_DESC_LIMIT:
            # If it exceeds, fall back to fields for safety
            embed = discord.Embed(
                title="📋 General Commands",
                description="General member commands.",
                color=discord.Color.blue()
            )
            for i, chunk in enumerate(_chunk_lines_to_field_values(blocks)):
                embed.add_field(
                    name="Commands" if i == 0 else "Commands (cont.)",
                    value=chunk,
                    inline=False
                )
        else:
            if any(r.id == MODERATOR_ROLE_ID for r in ctx.author.roles):
                # keep this as a small note, not mixed into the command list
                note = f"\n\n_Mod commands available via `{COMMAND_PREFIX}modcommands`_"
                if len(description) + len(note) <= _EMBED_DESC_LIMIT:
                    description += note

            embed = discord.Embed(
                title="📋 General Commands",
                description=description,
                color=discord.Color.blue()
            )

        await ctx.send(embed=embed)
        await self._delete_invocation(ctx)

    @commands.command(name="economycommands")
    async def economy_commands(self, ctx):
        """Show member economy commands (excluding moderator-only)."""
        cmds = _dedupe_by_name(get_member_commands())
        econ_cmds = [
            c for c in cmds
            if "economy" in c.get("Category", []) and "moderator" not in c.get("Category", [])
        ]

        blocks = [format_command(c, include_examples=True) for c in econ_cmds]
        desc = "\n\n".join(blocks) if blocks else "_No commands found._"

        if len(desc) <= _EMBED_DESC_LIMIT:
            embed = discord.Embed(
                title="💰 Economy Commands",
                description=desc,
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="💰 Economy Commands",
                description="Member economy commands.",
                color=discord.Color.green()
            )
            for i, chunk in enumerate(_chunk_lines_to_field_values(blocks)):
                embed.add_field(
                    name="Commands" if i == 0 else "Commands (cont.)",
                    value=chunk,
                    inline=False
                )

        await ctx.send(embed=embed)
        await self._delete_invocation(ctx)

    @commands.command(name="gamecommands")
    async def game_commands(self, ctx):
        """Show member game and leaderboard commands grouped by game."""
        cmds = _dedupe_by_name(get_member_commands())
        cmds = [c for c in cmds if "moderator" not in c.get("Category", [])]

        categories = ["leaderboards", "wordle", "connect4", "battleship", "dice"]
        grouped = categorize(cmds, categories)

        embed = discord.Embed(
            title="🎮 Game Commands",
            description="All commands related to games and leaderboards.",
            color=discord.Color.red()
        )

        subtitles = {
            "leaderboards": "📊 Leaderboards",
            "wordle": "🟩 Wordle",
            "connect4": "🔴 Connect 4",
            "battleship": "🚢 Battleship",
            "dice": "🎲 Dice Commands"
        }

        any_fields = False
        for key in categories:
            if grouped[key]:
                any_fields = True
                blocks = [format_command(cmd, include_examples=True) for cmd in grouped[key]]
                for i, chunk in enumerate(_chunk_lines_to_field_values(blocks)):
                    embed.add_field(
                        name=subtitles.get(key, key.title()) if i == 0 else f"{subtitles.get(key, key.title())} (cont.)",
                        value=chunk,
                        inline=False
                    )

        if not any_fields:
            embed.description = "_No commands found._"

        await ctx.send(embed=embed)
        await self._delete_invocation(ctx)

    @commands.command(name="modcommands")
    @commands.has_role(MODERATOR_ROLE_ID)
    async def mod_commands(self, ctx):
        """Show all moderator commands grouped by category."""
        cmds = _dedupe_by_name(get_moderator_commands())

        categories = ["general", "economy", "settings"]
        grouped = categorize(cmds, categories)

        embed = discord.Embed(
            title="🛠️ Moderator Commands",
            description="Moderator-only tools and utilities.",
            color=discord.Color.gold()
        )

        subtitles = {
            "general": "📋 General",
            "economy": "💰 Economy Tools",
            "settings": "⚙️ Bot Settings"
        }

        any_fields = False
        for key in categories:
            if grouped[key]:
                any_fields = True
                blocks = [format_command(cmd, include_examples=True) for cmd in grouped[key]]
                for i, chunk in enumerate(_chunk_lines_to_field_values(blocks)):
                    embed.add_field(
                        name=subtitles.get(key, key.title()) if i == 0 else f"{subtitles.get(key, key.title())} (cont.)",
                        value=chunk,
                        inline=False
                    )

        if not any_fields:
            embed.description = "_No commands found._"

        await ctx.send(embed=embed)
        await self._delete_invocation(ctx)

async def setup(bot):
    await bot.add_cog(CommandHelp(bot))
