from config import CURRENCY_NAME, CURRENCY_SYMBOL
from utils.economy import load_economy, user_key
from utils.embed import create_embed
from utils.shop import ensure_shop_schema, get_equipped_frame, get_equipped_accent_color
from utils.profile_card import render_profile_card

def _discord_color_from_hex(value: str | None) -> discord.Color:
    if not value:
        return discord.Color.blue()
    s = value.strip()
    if s.startswith("#"):
        s = s[1:]
    try:
        return discord.Color(int(s, 16))
    except Exception:
        return discord.Color.blue()

class Balance(commands.Cog):
def __init__(self, bot):
@@ -16,9 +29,16 @@ def __init__(self, bot):
async def profile(self, ctx, member: discord.Member | None = None):
member = member or ctx.author

        key = user_key(member)  # ID-keyed
        # Economy (ID-keyed)
        key = user_key(member)
data = load_economy(key)

        # Ensure shop schema exists (adds inventory if missing)
        ensure_shop_schema(key)

        frame_id = get_equipped_frame(key)
        accent_hex = get_equipped_accent_color(key)

lvl = int(data.get("level", 1) or 1)
xp = int(data.get("xp", 0) or 0)
needed = 100 * lvl
@@ -31,19 +51,23 @@ async def profile(self, ctx, member: discord.Member | None = None):
f"**XP:** {xp} / {needed}\n\n"
f"**Wordle Streak:** `{int(data.get('wordle_streak', 0) or 0)}`\n"
f"**Connect4 Streak:** `{int(data.get('connect4_streak', 0) or 0)}`\n"
            f"**Battleship Win Streak:** `{int(data.get('battleship_streak', 0) or 0)}`\n"
            f"**Battleship Win Streak:** `{int(data.get('battleship_streak', 0) or 0)}`\n\n"
            f"**Equipped Frame:** `{frame_id or 'none'}`\n"
            f"**Accent Color:** `{accent_hex or 'default'}`\n"
)

embed = await create_embed(
title=f"{member.display_name}'s Profile",
description=description,
            color=discord.Color.blue()
            color=_discord_color_from_hex(accent_hex),
)

        if member.display_avatar:
            embed.set_thumbnail(url=member.display_avatar.url)
        # Generate card image and attach it
        png_bytes = await render_profile_card(member, frame_id=frame_id, accent_hex=accent_hex)
        file = discord.File(fp=png_bytes, filename="profile.png")
        embed.set_image(url="attachment://profile.png")

        await ctx.send(embed=embed)
        await ctx.send(embed=embed, file=file)

try:
await ctx.message.delete()
