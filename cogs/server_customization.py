import discord
from discord.ext import commands
import json
import os
from utils.embed import create_embed
import config
from utils.economy import handle_roll_reaction, load_economy, add_role, remove_role, get_balance

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
            # Provide default structure if file doesn't exist
            return {"color": {}, "channels": {}, "notifications": {}}

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
        color_message = await rolls_channel.send(embed=color_embed)
        channels_message = await rolls_channel.send(embed=channels_embed)
        notifications_message = await rolls_channel.send(embed=notifications_embed)

        # Save the message IDs to rolls.json so the bot can track them
        self.rolls_data["color_roles_message_id"] = color_message.id
        self.rolls_data["channels_roles_message_id"] = channels_message.id
        self.rolls_data["notifications_roles_message_id"] = notifications_message.id
        self.save_rolls()

        # Add reactions based on the emojis in the rolls.json file
        await self.add_reactions(color_message, "color")
        await self.add_reactions(channels_message, "channels")
        await self.add_reactions(notifications_message, "notifications")
        await ctx.send("Server customization complete!")

    async def create_role_embed(self, role_type):
        # Get the role data from rolls.json for the specified role type
        role_data = self.rolls_data.get(role_type, {})
        if not role_data:
            return await create_embed("No Roles", f"No roles found for '{role_type}'.", color=discord.Color.red())

        message = role_data.get("message", "No message")
        description = role_data.get("description", "No description")
        options = role_data.get("options", {})

        # Build the options string from the available emojis and role names
        options_text = "\n".join([f"{emoji} {role['name']}" for emoji, role in options.items()])
        return await create_embed(
            message,
            f"{description}\n\n{options_text}",
            color=discord.Color.blue()
        )

    async def add_reactions(self, message, role_type):
        # Add reactions to the message based on the options from rolls.json
        options = self.rolls_data.get(role_type, {}).get("options", {})
        for emoji in options.keys():
            await message.add_reaction(emoji)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user == self.bot.user:
            return
        # Reload rolls_data to ensure it reflects any manual updates
        self.rolls_data = self.load_rolls()
        message_id = reaction.message.id
        if message_id == self.rolls_data.get("color_roles_message_id") or \
           message_id == self.rolls_data.get("channels_roles_message_id") or \
           message_id == self.rolls_data.get("notifications_roles_message_id"):
            await self.handle_reaction(reaction, user, "add")

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        if user == self.bot.user:
            return
        # Reload rolls_data to ensure it reflects any manual updates
        self.rolls_data = self.load_rolls()
        message_id = reaction.message.id
        if message_id == self.rolls_data.get("color_roles_message_id") or \
           message_id == self.rolls_data.get("channels_roles_message_id") or \
           message_id == self.rolls_data.get("notifications_roles_message_id"):
            await self.handle_reaction(reaction, user, "remove")

    async def handle_reaction(self, reaction, user, action):
        # Convert reaction emoji to a string for matching
        emoji = reaction.emoji if isinstance(reaction.emoji, str) else reaction.emoji.name
        print(f"Handling reaction {emoji} for user {user} with action {action}")
        role_type = self.get_role_type_from_emoji(emoji)
        if not role_type:
            print("No matching role type found for emoji:", emoji)
            return

        role_data = self.rolls_data.get(role_type, {}).get("options", {})
        role_info = role_data.get(emoji)
        if role_info:
            role = discord.utils.get(user.guild.roles, id=role_info["role_id"])
            if role:
                if action == "add":
                    await user.add_roles(role)
                    if handle_roll_reaction(user.name, role.name):
                        if role_type != "color":
                            welcome_channel = self.bot.get_channel(config.WELCOME_CHANNEL)
                            if welcome_channel:
                                embed = await create_embed(
                                    "Role Assigned",
                                    f"Welcome {user.mention}, you have been given the {role.name} role!",
                                    color=discord.Color.green()
                                )
                                await welcome_channel.send(embed=embed)
                elif action == "remove":
                    await user.remove_roles(role)
                    if remove_role(user.name, role.name):
                        if role_type != "color":
                            goodbye_channel = self.bot.get_channel(config.GOODBYE_CHANNEL)
                            if goodbye_channel:
                                embed = await create_embed(
                                    "Role Removed",
                                    f"{user.mention} has been removed from the {role.name} role. Goodbye!",
                                    color=discord.Color.red()
                                )
                                await goodbye_channel.send(embed=embed)
            else:
                print("Role not found for ID:", role_info["role_id"])
        else:
            print("No role info found for emoji:", emoji)

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
