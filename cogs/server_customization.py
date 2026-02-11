import discord
from discord.ext import commands
import json
import os
from utils.embed import create_embed
import config
from utils.economy import load_economy  # keep if you plan to use it later; otherwise safe to remove

class ServerCustomization(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rolls_file = os.path.join("data", "rolls.json")
        self.rolls_data = self.load_rolls()

    def ensure_data_folder(self):
        if not os.path.exists("data"):
            os.makedirs("data")

    def load_rolls(self):
        self.ensure_data_folder()
        if os.path.exists(self.rolls_file):
            with open(self.rolls_file, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            return {"color": {}, "channels": {}, "notifications": {}}

    def save_rolls(self):
        self.ensure_data_folder()
        with open(self.rolls_file, "w", encoding="utf-8") as f:
            json.dump(self.rolls_data, f, indent=4, ensure_ascii=False)

    async def _fetch_existing_message(self, channel: discord.TextChannel, id_key: str):
        """Fetch an existing panel message by stored ID. Returns None if missing/deleted."""
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
        - If the stored message exists: edit its embed (no duplicates)
        - If missing/deleted: create a new message, save its ID, add reactions
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
        # Delete the command message to keep channels clean (best effort)
        try:
            await ctx.message.delete()
        except (discord.NotFound, discord.Forbidden):
            pass

        rolls_channel = self.bot.get_channel(config.ROLLS_CHANNEL)
        if rolls_channel is None:
            await ctx.send("Invalid channel ID in the config file.", delete_after=30)
            return

        # Reload rolls.json in case it was edited while bot was running
        self.rolls_data = self.load_rolls()

        # Ensure panels exist (edit existing instead of reposting)
        await self._ensure_panel(rolls_channel, "color", "color_roles_message_id")
        await self._ensure_panel(rolls_channel, "channels", "channels_roles_message_id")
        await self._ensure_panel(rolls_channel, "notifications", "notifications_roles_message_id")

        await ctx.send("Server customization panels are set.", delete_after=30)

    @commands.command(name="update_rolls")
    async def update_rolls(self, ctx):
        """Reload the latest rolls.json file manually."""
        try:
            await ctx.message.delete()
        except (discord.NotFound, discord.Forbidden):
            pass

        self.rolls_data = self.load_rolls()
        await ctx.send("Rolls data updated from file.", delete_after=30)

    async def create_role_embed(self, role_type):
        role_data = self.rolls_data.get(role_type, {})
        if not role_data:
            return await create_embed(
                "No Roles",
                f"No roles found for '{role_type}'.",
                color=discord.Color.red()
            )

        message = role_data.get("message", "No message")
        description = role_data.get("description", "No description")
        options = role_data.get("options", {})
        options_text = "\n".join([f"{emoji} {role['name']}" for emoji, role in options.items()])

        return await create_embed(
            message,
            f"{description}\n\n{options_text}",
            color=discord.Color.blue()
        )

    async def add_reactions(self, message, role_type):
        options = self.rolls_data.get(role_type, {}).get("options", {})
        for emoji in options.keys():
            try:
                await message.add_reaction(emoji)
            except Exception:
                pass

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user == self.bot.user:
            return

        self.rolls_data = self.load_rolls()
        message_id = reaction.message.id
        if message_id in (
            self.rolls_data.get("color_roles_message_id"),
            self.rolls_data.get("channels_roles_message_id"),
            self.rolls_data.get("notifications_roles_message_id")
        ):
            await self.handle_reaction(reaction, user, "add")

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        if user == self.bot.user:
            return

        self.rolls_data = self.load_rolls()
        message_id = reaction.message.id
        if message_id in (
            self.rolls_data.get("color_roles_message_id"),
            self.rolls_data.get("channels_roles_message_id"),
            self.rolls_data.get("notifications_roles_message_id")
        ):
            await self.handle_reaction(reaction, user, "remove")

    async def handle_reaction(self, reaction, user, action):
        emoji = reaction.emoji if isinstance(reaction.emoji, str) else reaction.emoji.name
        role_type = self.get_role_type_from_emoji(emoji)
        if not role_type:
            return

        role_data = self.rolls_data.get(role_type, {}).get("options", {})
        role_info = role_data.get(emoji)
        if not role_info:
            return

        role = discord.utils.get(user.guild.roles, id=role_info["role_id"])
        if not role:
            return

        if action == "add":
            await user.add_roles(role)
            if role_type != "color":
                welcome_channel = self.bot.get_channel(config.WELCOME_CHANNEL)
                if welcome_channel:
                    embed = await create_embed(
                        "Role Assigned",
                        f"Welcome {user.mention}, you have been given the {role.name} role!",
                        color=discord.Color.blue()
                    )
                    await welcome_channel.send(embed=embed)

        elif action == "remove":
            await user.remove_roles(role)
            if role_type != "color":
                goodbye_channel = self.bot.get_channel(config.GOODBYE_CHANNEL)
                if goodbye_channel:
                    embed = await create_embed(
                        "Role Removed",
                        f"{user.mention} has been removed from the {role.name} role. Goodbye!",
                        color=discord.Color.blue()
                    )
                    await goodbye_channel.send(embed=embed)

    def get_role_type_from_emoji(self, emoji):
        if emoji in self.rolls_data.get("color", {}).get("options", {}):
            return "color"
        elif emoji in self.rolls_data.get("channels", {}).get("options", {}):
            return "channels"
        elif emoji in self.rolls_data.get("notifications", {}).get("options", {}):
            return "notifications"
        return None

async def setup(bot):
    await bot.add_cog(ServerCustomization(bot))
