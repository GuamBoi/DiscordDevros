# utils/embed.py

import discord
from config import BOT_NAME, BOT_VERSION  # Import the bot name and version from config

async def create_embed(title: str, description: str, color: discord.Color = discord.Color.blue(), footer_text: str = None, image_url: str = None) -> discord.Embed:
    """
    Creates a visually appealing and customizable embed for the bot.
    
    Args:
        title (str): The title of the embed.
        description (str): The description/content of the embed.
        color (discord.Color, optional): The color of the embed. Defaults to blue.
        footer_text (str, optional): The footer text. Defaults to BOT_NAME and BOT_VERSION if not provided.
        image_url (str, optional): A URL to an image to include in the embed. Defaults to None.
    
    Returns:
        discord.Embed: The created embed.
    """
    embed = discord.Embed(title=title, description=description, color=color)
    
    # If no footer text is provided, use the bot name and version from config
    if not footer_text:
        footer_text = f"{BOT_NAME} v{BOT_VERSION}"
    
    # Set the footer with the option to include custom text
    embed.set_footer(text=footer_text)
    
    # Optionally add an image to the embed
    if image_url:
        embed.set_image(url=image_url)
    
    return embed
