import discord
from discord.ext import commands, tasks
from utils.llm_api import query_llm
from utils.dictionary import get_command_info  # Import the function to load command data
from config import HELP_COMMAND_CHANNEL_CATEGORY
import asyncio

class CommandHelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_private_channels = {}
        self.inactivity_timeout_task.start()  # Start the inactivity timeout check task

    @tasks.loop(minutes=1)
    async def inactivity_timeout_task(self):
        """Check for inactivity in private channels and delete if inactive for 1 hour."""
        current_time = discord.utils.utcnow()
        for user_id, private_channel in list(self.active_private_channels.items()):
            # Get the last message timestamp for the channel
            last_message_time = private_channel.last_message.created_at if private_channel.last_message else current_time
            time_difference = (current_time - last_message_time).total_seconds()

            # If no message for 1 hour, delete the channel
            if time_difference > 3600:
                try:
                    await private_channel.delete(reason="No activity for 1 hour.")
                    del self.active_private_channels[user_id]
                except discord.NotFound:
                    pass  # Channel might have already been deleted manually

    @commands.command(name="command_help", help="Provides detailed help for a specific command using LLM context.")
    async def command_help(self, ctx, command_name: str):
        # Get command information using dictionary.py's get_command_info method
        command_info = get_command_info(command_name)
        
        if not command_info:
            await ctx.send(f"Command '{command_name}' not found.")
            return

        # Retrieve LLM_Context from the command's data
        llm_context = command_info.get("LLM_Context", "")
        if not llm_context:
            await ctx.send(f"No LLM context available for command '{command_name}'.")
            return

        # Check if the user already has a private channel
        if ctx.author.id in self.active_private_channels:
            private_channel = self.active_private_channels[ctx.author.id]
            await ctx.send(f"You already have a private channel: {private_channel.mention}")
            return

        # Create a private channel for the user
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

        # Send message asking user for help context
        await private_channel.send(f"Hey {ctx.author.mention}, how can I help you with the **{command_name}** command?")

        # Wait for the user's response and send to the LLM for a response
        def check(m):
            return m.author == ctx.author and m.channel == private_channel

        # Send the response to the LLM once user message is received
        user_message = await self.bot.wait_for("message", check=check)

        # Get the user's message and combine it with LLM_Context for the query
        user_query = user_message.content
        full_llm_input = f"{llm_context}\nUser's question: {user_query}"

        # Query the LLM with the combined context
        response = await query_llm(ctx, full_llm_input)

        # Send the response from the LLM in the private channel
        await private_channel.send(f"LLM Response for **{command_name}**:\n{response}")

        # Add a listener for future messages in the private channel
        async def on_message_in_private_channel(message):
            if message.author == ctx.author and message.channel == private_channel:
                # Process the new message and send it to the LLM
                new_user_query = message.content
                full_llm_input = f"{llm_context}\nUser's question: {new_user_query}"

                # Query the LLM with the updated context
                response = await query_llm(ctx, full_llm_input)

                # Send the new response from the LLM in the private channel
                await private_channel.send(f"LLM Response for **{command_name}**:\n{response}")

        # Register the message listener
        self.bot.add_listener(on_message_in_private_channel)

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

# Function to setup the cog
async def setup(bot):
    await bot.add_cog(CommandHelpCog(bot))
