import discord
from discord.ext import commands
import json
import os
from utils.embed import create_embed
import config

class ServerCustomization(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rolls_file = os.path.join("data", "rolls.json")
        self.rolls_data = self.load_rolls()

    # ----------------------------
    # File helpers
    # ----------------------------
    def ensure_data_folder(self):
        if not os.path.exists("data"):
            os.makedirs("data")

    def load_rolls(self):
        self.ensure_data_folder()
        if os.path.exists(self.rolls_file):
            with open(self.rolls_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"color": {}, "channels": {}, "notifications": {}}

    def save_rolls(self):
        self.ensure_data_folder()
        with open(self.rolls_file, "w", encoding="utf-8") as f:
            json.dump(self.rolls_data, f, indent=4, ensure_ascii=False)

    # ----------------------------
    # Idempotent panels
    # ----------------------------
    async def _fetch_existing_message(self, channel: discord.TextChannel, id_key: str):
        msg_id = self.rolls_data.get(id_key)
        if not msg_id:
            return None
        try:
            return await channel.fetch_message(int(msg_id))
        except Exception:
            return None

    async def _ensure_panel(self, channel: discord.TextChannel, role_type: str, id_key: str):
        """
        Ensure a single reaction-role panel exists.
        - If stored message exists: edit embed (no duplicates)
        - If missing/deleted: create new message, save ID, add reactions
        """
        existing = await self._fetch_existing_message(channel, id_key)
        embed = await self.create_role_embed(role_type)

        if existing:
            try:
                await existing.edit(embed=embed)
            except Exception:
                pass
            return existing

        msg = await channel.send(embed=embed)
        self.rolls_data[id_key] = msg.id
        self.save_rolls()
        await self.add_reactions(msg, role_type)
        return msg

    @commands.command(name="server_customization")
    async def server_customization(self, ctx):
        # Best-effort delete the command message
        try:
            await ctx.message.delete()
        except (discord.NotFound, discord.Forbidden):
            pass

        rolls_channel = self.bot.get_channel(config.ROLLS_CHANNEL)
        if rolls_channel is None:
            await ctx.send("Invalid channel ID in the config file.", delete_after=30)
            return

        # Reload file in case it changed
        self.rolls_data = self.load_rolls()

        await self._ensure_panel(rolls_channel, "color", "color_roles_message_id")
        await self._ensure_panel(rolls_channel, "channels", "channels_roles_message_id")
        await self._ensure_panel(rolls_channel, "notifications", "notifications_roles_message_id")

        await ctx.send("Server customization panels are set.", delete_after=30)

    @commands.command(name="update_rolls")
    async def update_rolls(self, ctx):
        try:
            await ctx.message.delete()
        except (discord.NotFound, discord.Forbidden):
            pass

        self.rolls_data = self.load_rolls()
        await ctx.send("Rolls data updated from file.", delete_after=30)

    async def create_role_embed(self, role_type: str):
        role_data = self.rolls_data.get(role_type, {})
        if not role_data:
            return await create_embed(
                "No Roles",
                f"No roles found for '{role_type}'.",
                color=discord.Color.red()
            )

        message = role_data.get("message", "No message")
        description = role_data.get("description", "No description")
        note = role_data.get("note")
        options = role_data.get("options", {})

        options_text = "\n".join([f"{emoji} {role['name']}" for emoji, role in options.items()])
        body = f"{description}\n\n{options_text}"
        if note:
            body += f"\n\n_{note}_"

        return await create_embed(message, body, color=discord.Color.blue())

    async def add_reactions(self, message: discord.Message, role_type: str):
        options = self.rolls_data.get(role_type, {}).get("options", {})
        for emoji in options.keys():
            try:
                await message.add_reaction(emoji)
            except Exception:
                pass

    # ----------------------------
    # IMPORTANT FIX: raw reactions
    # ----------------------------
    def _panel_message_ids(self) -> set[int]:
        ids = set()
        for k in ("color_roles_message_id", "channels_roles_message_id", "notifications_roles_message_id"):
            v = self.rolls_data.get(k)
            if isinstance(v, int):
                ids.add(v)
            elif isinstance(v, str) and v.isdigit():
                ids.add(int(v))
        return ids

    def get_role_type_from_emoji(self, emoji: str) -> str | None:
        if emoji in self.rolls_data.get("color", {}).get("options", {}):
            return "color"
        if emoji in self.rolls_data.get("channels", {}).get("options", {}):
            return "channels"
        if emoji in self.rolls_data.get("notifications", {}).get("options", {}):
            return "notifications"
        return None

    async def _apply_role_change(self, payload: discord.RawReactionActionEvent, action: str):
        if payload.guild_id is None:
            return

        # Reload latest mapping
        self.rolls_data = self.load_rolls()

        if payload.message_id not in self._panel_message_ids():
            return

        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return

        # Get the member
        member = guild.get_member(payload.user_id)
        if member is None:
            try:
                member = await guild.fetch_member(payload.user_id)
            except Exception:
                return

        if member.bot:
            return

        emoji = str(payload.emoji)  # works for unicode emojis and custom emoji names
        role_type = self.get_role_type_from_emoji(emoji)
        if not role_type:
            return

        role_info = self.rolls_data.get(role_type, {}).get("options", {}).get(emoji)
        if not role_info:
            return

        role = guild.get_role(int(role_info["role_id"]))
        if role is None:
            return

        try:
            if action == "add":
                await member.add_roles(role, reason="Reaction role")
                if role_type != "color":
                    welcome_channel = self.bot.get_channel(config.WELCOME_CHANNEL)
                    if welcome_channel:
                        embed = await create_embed(
                            "Role Assigned",
                            f"Welcome {member.mention}, you have been given the {role.name} role!",
                            color=discord.Color.blue()
                        )
                        await welcome_channel.send(embed=embed)
            else:
                await member.remove_roles(role, reason="Reaction role removed")
                if role_type != "color":
                    goodbye_channel = self.bot.get_channel(config.GOODBYE_CHANNEL)
                    if goodbye_channel:
                        embed = await create_embed(
                            "Role Removed",
                            f"{member.mention} has been removed from the {role.name} role.",
                            color=discord.Color.blue()
                        )
                        await goodbye_channel.send(embed=embed)
        except discord.Forbidden:
            # Most common: bot role is below target role OR missing Manage Roles
            pass
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == getattr(self.bot.user, "id", None):
            return
        await self._apply_role_change(payload, "add")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == getattr(self.bot.user, "id", None):
            return
        await self._apply_role_change(payload, "remove")

async def setup(bot):
    await bot.add_cog(ServerCustomization(bot))
