import discord
from discord.ext import commands
from utils.dictionary import get_member_commands, get_moderator_commands, get_command_info
from utils.embed import create_embed
from config import COMMAND_PREFIX, MODERATOR_ROLE_ID

class CommandHelp(commands.Cog):
    @commands.command(name="commands")
    async def commands_list(self, ctx):
        """Show available member commands."""
        cmds = get_member_commands()
        desc = []
        for c in cmds:
            desc.append(f"**{COMMAND_PREFIX}{c['Command_Name']}**: {c['Description']}")
        # Show hint for mods
        if any(r.id==MODERATOR_ROLE_ID for r in ctx.author.roles):
            desc.append(f"\n_Mod commands available via `{COMMAND_PREFIX}modcommands`_ ")
        embed = await create_embed(
            title="Available Commands",
            description="\n".join(desc)
        )
        await ctx.send(embed=embed)

    @commands.command(name="modcommands")
    @commands.has_role(MODERATOR_ROLE_ID)
    async def mod_commands(self, ctx):
        """Show moderator-only commands."""
        cmds = get_moderator_commands()
        desc = [f"**{COMMAND_PREFIX}{c['Command_Name']}**: {c['Description']}" for c in cmds]
        embed = await create_embed(
            title="Moderator Commands",
            description="\n".join(desc)
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CommandHelp(bot))
