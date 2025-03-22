import discord
from discord.ext import commands
import json
import os
from utils.embed import create_embed
import config
from economy import handle_roll_reaction, load_economy, add_role, remove_role, get_balance  # Import economy functions

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
            with open(self.rolls_file, 'r') as f:
                return json.load(f)
        else:
            return {"color_roles": [], "channels_roles": [], "update_channels": []}

    def save_rolls(self):
        self.ensure_data_folder()
        with open(self.rolls_file, 'w') as f:
            json.dump(self.rolls_data, f, indent=4)

    @commands.command(name='server_customization')
    async def server_customization(self, ctx):
        # Fetch the channel from the config using ROLLS_CHANNEL
        rolls_channel = self.bot.get_channel(config.ROLLS_CHANNEL)

        if rolls_channel is None:
            await ctx.send("Invalid channel ID in the config file.")
            return

        # Prepare the embeds using the role options from rolls.json
        color_embed = await self.create_role_embed("color")
        channels_embed = await self.create_role_embed("channels")
        notifications_embed = await self.create_role_embed("notifications")

        # Send each embed only once
        await rolls_channel.send(embed=color_embed)
        await rolls_channel.send(embed=channels_embed)
        await rolls_channel.send(embed=notifications_embed)

        # Add reactions based on the emojis in the rolls.json file
        await self.add_reactions(color_embed, "color")
        await self.add_reactions(channels_embed, "channels")
        await self.add_reactions(notifications_embed, "notifications")

    async def create_role_embed(self, role_type):
        # Get the role data from rolls.json
        role_data = self.rolls_data.get(role_type, {})

        # Check if role_data exists for the requested role_type
        if not role_data:
            return await create_embed("No Roles", f"No roles found for '{role_type}'.", color=discord.Color.red())

        message = role_data.get("message", "No message")
        description = role_data.get("description", "No description")
        options = role_data.get("options", {})

        # Build the options string
        options_text = "\n".join([f"{emoji} {role['name']}" for emoji, role in options.items()])

        # Create the embed
        return await create_embed(
            message,
            f"{description}\n\n{options_text}",
            color=discord.Color.blue()
        )

    async def add_reactions(self, message, role_type):
        # Add reactions to the message based on the role options in rolls.json
        options = self.rolls_data.get(role_type, {}).get("options", {})
        for emoji in options.keys():
            await message.add_reaction(emoji)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        # Ignore the bot's own reactions
        if user == self.bot.user:
            return

        role_type = self.get_role_type_from_emoji(reaction.emoji)
        if not role_type:
            return

        # Get role info from rolls.json
        role_data = self.rolls_data.get(role_type, {}).get("options", {})
        role_info = role_data.get(reaction.emoji)

        if role_info:
            role = discord.utils.get(user.guild.roles, id=role_info["role_id"])
            if role:
                # Add role to user
                await user.add_roles(role)
                # Update economy (add role to user's rolls)
                if handle_roll_reaction(user.name, role.name):
                    # Send a welcome message if it's not a color role
                    if role_type != "color":
                        welcome_channel = self.bot.get_channel(config.WELCOME_CHANNEL)
                        if welcome_channel:
                            await welcome_channel.send(f"Welcome {user.mention}, you have been given the {role.name} role!")
                    # Ensure color roles are also applied
                    if role_type == "color":
                        await user.edit(color=role.color)

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        # Ignore the bot's own reactions
        if user == self.bot.user:
            return

        role_type = self.get_role_type_from_emoji(reaction.emoji)
        if not role_type:
            return

        # Get role info from rolls.json
        role_data = self.rolls_data.get(role_type, {}).get("options", {})
        role_info = role_data.get(reaction.emoji)

        if role_info:
            role = discord.utils.get(user.guild.roles, id=role_info["role_id"])
            if role:
                # Remove role from user
                await user.remove_roles(role)
                # Update economy (remove role from user's rolls)
                if remove_role(user.name, role.name):
                    # Send a goodbye message if it's not a color role
                    if role_type != "color":
                        goodbye_channel = self.bot.get_channel(config.GOODBYE_CHANNEL)
                        if goodbye_channel:
                            await goodbye_channel.send(f"{user.mention} has been removed from the {role.name} role. Goodbye!")

    def get_role_type_from_emoji(self, emoji):
        # Determine the role type based on the emoji reacted to
        if emoji in self.rolls_data.get("color", {}).get("options", {}):
            return "color"
        elif emoji in self.rolls_data.get("channels", {}).get("options", {}):
            return "channels"
        elif emoji in self.rolls_data.get("notifications", {}).get("options", {}):
            return "notifications"
        return None

async def setup(bot):
    await bot.add_cog(ServerCustomization(bot))
