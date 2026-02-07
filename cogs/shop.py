import os
import discord
from discord.ext import commands

from utils.embed import create_embed
from utils.economy import get_balance, remove_currency
from utils.shop import (
    ensure_shop_schema,
    grant_frame,
    grant_color,
    equip_frame,
    equip_color,
    owns_frame,
    owns_color,
    get_owned_frames,
    get_owned_colors,
    get_equipped,
    normalize_hex_color,
)

# Folder that holds frame PNG files
PROFILE_FRAMES_DIR = os.path.join("data", "profile_frames")

# ============================================================
# HARD-CODED SHOP CATALOG
# ============================================================
# HOW TO ADD MORE FRAMES:
# 1. Drop a PNG in data/profile_frames/<frame_id>.png
# 2. Add a new entry to SHOP_FRAMES using the SAME <frame_id>
#
# Example:
# "gold": {"name": "Gold Frame", "price": 750},
#
SHOP_FRAMES = {
    "red": {
        "name": "Red Frame",
        "price": 100,
    },
}

# HOW TO ADD MORE COLORS:
# 1. Pick a hex color (#RRGGBB)
# 2. Add it here as the key
#
# Example:
# "#ff9900": {"name": "Orange", "price": 300},
#
SHOP_COLORS = {
    "#3D5361": {
        "name": "Blue",
        "price": 100,
    },
}

# ============================================================

def _frame_exists(frame_id: str) -> bool:
    """Check that the PNG file actually exists on disk."""
    return os.path.exists(os.path.join(PROFILE_FRAMES_DIR, f"{frame_id}.png"))


class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ----------------------------
    # !shop
    # ----------------------------
    @commands.command(name="shop")
    async def shop(self, ctx):
        """Show available shop items."""
        ensure_shop_schema(ctx.author)

        frame_lines = []
        for frame_id, meta in SHOP_FRAMES.items():
            missing = "" if _frame_exists(frame_id) else " ⚠️ (file missing)"
            frame_lines.append(
                f"• `{frame_id}` — **{meta['name']}** — `{meta['price']}` gold{missing}"
            )

        color_lines = []
        for hexv, meta in SHOP_COLORS.items():
            color_lines.append(
                f"• `{hexv}` — **{meta['name']}** — `{meta['price']}` gold"
            )

        description = (
            "**🖼 Frames**\n"
            + ("\n".join(frame_lines) if frame_lines else "_None_")
            + "\n\n"
            "**🎨 Colors**\n"
            + ("\n".join(color_lines) if color_lines else "_None_")
            + "\n\n"
            "**Buy:** `!buy frame <id>` or `!buy color <#hex>`\n"
            "**Equip:** `!equip frame <id|none>` or `!equip color <#hex|none>`"
        )

        embed = await create_embed("Shop", description, color=discord.Color.gold())
        await ctx.send(embed=embed)

        try:
            await ctx.message.delete()
        except (discord.NotFound, discord.Forbidden):
            pass

    # ----------------------------
    # !buy
    # ----------------------------
    @commands.command(name="buy")
    async def buy(self, ctx, category: str, *, item: str):
        """Buy a shop item."""
        ensure_shop_schema(ctx.author)

        category = category.lower().strip()
        item = item.strip()

        if category not in {"frame", "color"}:
            await ctx.send("Usage: `!buy frame <id>` or `!buy color <#hex>`")
            return

        # -------- FRAME PURCHASE --------
        if category == "frame":
            frame_id = item.lower()

            if frame_id not in SHOP_FRAMES:
                await ctx.send("That frame is not sold in the shop.")
                return

            if not _frame_exists(frame_id):
                await ctx.send("Frame PNG file is missing on the server.")
                return

            if owns_frame(ctx.author, frame_id):
                await ctx.send("You already own this frame.")
                return

            price = SHOP_FRAMES[frame_id]["price"]
            bal = get_balance(ctx.author)

            if bal < price:
                await ctx.send(f"You need `{price}` gold, but only have `{bal}`.")
                return

            remove_currency(ctx.author, price)
            grant_frame(ctx.author, frame_id)

            embed = await create_embed(
                "Purchase Complete",
                f"{ctx.author.mention} bought **{SHOP_FRAMES[frame_id]['name']}** for `{price}` gold.",
                color=discord.Color.green(),
            )
            await ctx.send(embed=embed)
            return

        # -------- COLOR PURCHASE --------
        color_hex = normalize_hex_color(item)
        if not color_hex or color_hex not in SHOP_COLORS:
            await ctx.send("That color is not sold in the shop.")
            return

        if owns_color(ctx.author, color_hex):
            await ctx.send("You already own this color.")
            return

        price = SHOP_COLORS[color_hex]["price"]
        bal = get_balance(ctx.author)

        if bal < price:
            await ctx.send(f"You need `{price}` gold, but only have `{bal}`.")
            return

        remove_currency(ctx.author, price)
        grant_color(ctx.author, color_hex)

        embed = await create_embed(
            "Purchase Complete",
            f"{ctx.author.mention} bought **{SHOP_COLORS[color_hex]['name']}** for `{price}` gold.",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    # ----------------------------
    # !equip
    # ----------------------------
    @commands.command(name="equip")
    async def equip(self, ctx, category: str, *, item: str):
        """Equip an owned cosmetic."""
        ensure_shop_schema(ctx.author)

        category = category.lower().strip()
        item = item.strip()

        if category not in {"frame", "color"}:
            await ctx.send("Usage: `!equip frame <id|none>` or `!equip color <#hex|none>`")
            return

        if category == "frame":
            if item.lower() == "none":
                equip_frame(ctx.author, None)
                await ctx.send("Frame unequipped.")
                return

            if not owns_frame(ctx.author, item.lower()):
                await ctx.send("You don’t own that frame.")
                return

            equip_frame(ctx.author, item.lower())
            await ctx.send(f"Equipped frame `{item.lower()}`.")
            return

        # color
        if item.lower() == "none":
            equip_color(ctx.author, None)
            await ctx.send("Accent color reset to default.")
            return

        color_hex = normalize_hex_color(item)
        if not color_hex or not owns_color(ctx.author, color_hex):
            await ctx.send("You don’t own that color.")
            return

        equip_color(ctx.author, color_hex)
        await ctx.send(f"Equipped color `{color_hex}`.")

    # ----------------------------
    # !inventory (optional helper)
    # ----------------------------
    @commands.command(name="inventory")
    async def inventory(self, ctx, member: discord.Member | None = None):
        """Show a user's owned cosmetics (public)."""
        member = member or ctx.author
        ensure_shop_schema(member)

        frames = get_owned_frames(member)
        colors = get_owned_colors(member)
        frame_eq, color_eq = get_equipped(member)

        desc = (
            f"{member.mention}\n\n"
            f"**Equipped Frame:** `{frame_eq or 'none'}`\n"
            f"**Equipped Color:** `{color_eq or 'default'}`\n\n"
            f"**Owned Frames:** {', '.join(f'`{f}`' for f in frames) if frames else '_none_'}\n"
            f"**Owned Colors:** {', '.join(f'`{c}`' for c in colors) if colors else '_none_'}\n"
        )

        embed = await create_embed("Inventory", desc, color=discord.Color.blurple())
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Shop(bot))
