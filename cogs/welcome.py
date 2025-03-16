import discord
import aiohttp
from discord.ext import commands
from config import OPENWEBUI_API_URL, OPENWEBUI_API_KEY, MODEL_NAME

class WelcomeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Function to query Open Web UI and generate a custom welcome message
    async def generate_welcome_message(self, username):
        """Generate a custom welcome message for the new user."""
        if not OPENWEBUI_API_URL or not OPENWEBUI_API_KEY:
            return "Error: OpenWebUI API settings are missing."

        headers = {
            'Authorization': f'Bearer {OPENWEBUI_API_KEY}',
            'Content-Type': 'application/json'
        }

        prompt = f"Welcome {username} to the discord server! Please provide a personalized welcome message for them to be included AFTER their name in the discord server."

        data = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(OPENWEBUI_API_URL, json=data, headers=headers) as response:
                    if response.status == 200:
                        json_data = await response.json()
                        return json_data.get("generated_text", "Welcome to the server!")
                    else:
                        return f"API Error: {response.status}"
        except Exception as e:
            return f"Request Failed: {e}"

    # Event listener for when a member joins the server
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Generate and send a custom welcome message when a member joins."""
        username = member.name  # Get the username of the new member
        welcome_message = await self.generate_welcome_message(username)

        # Tag the new member directly in the message using @username
        welcome_message_with_tag = f"{member.mention}, {welcome_message}"

        # Send the message to the default channel (or specify your own channel)
        channel = member.guild.system_channel  # You can change this to a specific channel
        if channel:
            await channel.send(welcome_message_with_tag)

# Setup function to add the cog to the bot
def setup(bot):
    bot.add_cog(WelcomeCog(bot))
