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

PROFILE_FRAMES_DIR = os.path.join("data", "profile_frames")

# --------- Hard-coded shop catalog ---------
# Frame IDs must match filenames in data/profile_frames/<frame_id>.png
SHOP_FRAMES = {
    "classic": {"name": "Classic Frame", "price": 250},
    "gold": {"name": "Gold Frame", "price": 750},
    "neon": {"name": "Neon Frame", "price": 1000},
}

# Colors sold as hex. Users will equip with the hex value.
SHOP_COLORS = {
    "#5865f2": {"name": "Blurple", "price": 300},
    "#ff9900": {"name": "Orange", "price": 300},
    "#2ecc71": {"name": "Green", "price": 300},
    "#e74c3c": {"name": "Red", "price": 300},
    "#9b59b6": {"name": "Purple", "price": 300},
}

def _frame_exists(frame_id: str) -> bool:
    return os.path.exists(os.path.join(PROFILE_FRAMES_DIR, f"{frame_id}.png"))

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="shop")
    async def shop(self, ctx):
        """Show shop items."""
        ensure_shop_schema(ctx.author)

        frames_lines = []
        for frame_id, meta in SHOP_FRAMES.items():
            missing = "" if _frame_exists(frame_id) else " (missing file!)"
            frames_lines.append(f"• `{frame_id}` — **{meta['name']}** — `{meta['price']}` gold{missing}")

        colors_lines = []
        for hexv, meta in SHOP_COLORS.items():
            colors_lines.append(f"• `{hexv}` — **{meta['name']}** — `{meta['price']}` gold")

        description = (
            "**Frames**\n" + ("\n".join(frames_lines) if frames_lines else "_None_") +
            "\n\n**Colors**\n" + ("\n".join(colors_lines) if colors_lines else "_None_") +
            "\n\n**Buy:** `!buy frame <id>` or `!buy color <#hex>`\n"
            "**Equip:** `!equip frame <id|none>` or `!equip color <#hex|none>`"
        )

        embed = await create_embed("Shop", description, color=discord.Color.gold())
        await ctx.send(embed=embed)

        try:
            await ctx.message.delete()
        except (discord.NotFound, discord.Forbidden):
            pass

    @commands.command(name="buy")
    async def buy(self, ctx, category: str, *, item: str):
        """Buy an item: !buy frame <id> OR !buy color <#hex>"""
        ensure_shop_schema(ctx.author)

        category = (category or "").lower().strip()
        item = (item or "").strip()

        if category not in {"frame", "color"}:
            await ctx.send("Usage: `!buy frame <id>` or `!buy color <#hex>`")
            return

        if category == "frame":
            frame_id = item.lower()
            if frame_id not in SHOP_FRAMES:
                await ctx.send("That frame does not exist in the shop.")
                return
            if not _frame_exists(frame_id):
                await ctx.send("That frame is configured in the shop but the PNG file is missing on disk.")
                return
            if owns_frame(ctx.author, frame_id):
                await ctx.send("You already own that frame.")
                return

            price = int(SHOP_FRAMES[frame_id]["price"])
            bal = get_balance(ctx.author)
            if bal < price:
                await ctx.send(f"Not enough gold. You have `{bal}`, need `{price}`.")
                return

            remove_currency(ctx.author, price)
            grant_frame(ctx.author, frame_id)

            embed = await create_embed(
                "Purchase Complete",
                f"{ctx.author.mention} bought frame `{frame_id}` for `{price}` gold.",
                color=discord.Color.green(),
            )
            await ctx.send(embed=embed)
            return

        # category == "color"
        color_hex = normalize_hex_color(item)
        if not color_hex or color_hex not in SHOP_COLORS:
            await ctx.send("That color does not exist in the shop. Use a shop-listed hex like `#ff9900`.")
            return
        if owns_color(ctx.author, color_hex):
            await ctx.send("You already own that color.")
            return

        price = int(SHOP_COLORS[color_hex]["price"])
        bal = get_balance(ctx.author)
        if bal < price:
            await ctx.send(f"Not enough gold. You have `{bal}`, need `{price}`.")
            return

        remove_currency(ctx.author, price)
        grant_color(ctx.author, color_hex)

        embed = await create_embed(
            "Purchase Complete",
            f"{ctx.author.mention} bought color `{color_hex}` for `{price}` gold.",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="equip")
    async def equip(self, ctx, category: str, *, item: str):
        """Equip an owned item: !equip frame <id|none> OR !equip color <#hex|none>"""
        ensure_shop_schema(ctx.author)

        category = (category or "").lower().strip()
        item = (item or "").strip()

        if category not in {"frame", "color"}:
            await ctx.send("Usage: `!equip frame <id|none>` or `!equip color <#hex|none>`")
            return

        if category == "frame":
            if item.lower() == "none":
                equip_frame(ctx.author, None)
                await ctx.send("Frame unequipped.")
                return

            frame_id = item.lower()
            if not owns_frame(ctx.author, frame_id):
                await ctx.send("You don’t own that frame.")
                return

            equip_frame(ctx.author, frame_id)
            await ctx.send(f"Equipped frame `{frame_id}`.")
            return

        # category == "color"
        if item.lower() == "none":
            equip_color(ctx.author, None)
            await ctx.send("Accent color reset to default.")
            return

        color_hex = normalize_hex_color(item)
        if not color_hex:
            await ctx.send("Invalid hex. Example: `!equip color #ff9900`")
            return
        if not owns_color(ctx.author, color_hex):
            await ctx.send("You don’t own that color.")
            return

        equip_color(ctx.author, color_hex)
        await ctx.send(f"Equipped color `{color_hex}`.")

    # Optional convenience command (you said maybe)
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
