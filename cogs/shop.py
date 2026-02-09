import os
import io
import discord
from discord.ext import commands
from PIL import Image, ImageDraw  # Pillow installed

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
    DEFAULT_PROFILE_FRAMES_DIR,
    frame_path,
    frame_exists,
    format_frame_line,
    format_price,
)

# Folder that holds frame PNG files
PROFILE_FRAMES_DIR = DEFAULT_PROFILE_FRAMES_DIR

# ============================================================
# SHOP CATALOGS
# ============================================================

SHOP_FRAMES = {
    "purple": {"price": 100},
    "red": {"price": 100},
    "yellow": {"price": 100},
}

# User-facing name -> internal hex
SHOP_COLORS = {
    "red":    {"hex": "#832e2c", "price": 100},
    "orange": {"hex": "#a95e3f", "price": 100},
    "yellow": {"hex": "#bfa066", "price": 100},
    "green":  {"hex": "#5b6d61", "price": 100},
    "blue":   {"hex": "#3d5361", "price": 100},
    "purple": {"hex": "#6b5b7b", "price": 100},
}

# Reverse lookup: hex -> name (useful for inventory display)
HEX_TO_COLOR_NAME = {v["hex"]: k for k, v in SHOP_COLORS.items()}

# ============================================================
# SWATCH HELPERS
# ============================================================

def _hex_to_rgb(color_hex: str) -> tuple[int, int, int]:
    s = color_hex.lstrip("#")
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)


def _make_color_swatch(color_hex: str, size: int = 256) -> tuple[discord.File, str]:
    r, g, b = _hex_to_rgb(color_hex)
    img = Image.new("RGBA", (size, size), (r, g, b, 255))

    # subtle border so light colors show on dark discord bg
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, size - 1, size - 1], outline=(0, 0, 0, 90), width=4)

    bio = io.BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)

    filename = "color_swatch.png"
    return discord.File(fp=bio, filename=filename), filename


# ============================================================
# COG
# ============================================================

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ----------------------------
    # Helpers (clean chat)
    # ----------------------------
    async def _delete_invocation(self, ctx) -> None:
        """Delete the user's command message (best-effort)."""
        try:
            await ctx.message.delete()
        except (discord.NotFound, discord.Forbidden):
            pass

    async def _send_plain(self, ctx, content: str) -> None:
        """Send a plain bot message that auto-deletes after 30 seconds."""
        await ctx.send(content, delete_after=30)

    # ----------------------------
    # !shop
    # ----------------------------
    @commands.command(name="shop")
    async def shop(self, ctx):
        """Show available shop items (embeds stay permanently)."""
        ensure_shop_schema(ctx.author)

        frame_lines = []
        for frame_id, meta in SHOP_FRAMES.items():
            missing = not frame_exists(frame_id, frames_dir=PROFILE_FRAMES_DIR)
            frame_lines.append(format_frame_line(frame_id, meta["price"], missing=missing))

        color_lines = []
        for name, meta in SHOP_COLORS.items():
            color_lines.append(f"• **{name}** {format_price(meta['price'])}")

        description = (
            "**🖼 Frames**\n"
            + ("\n".join(frame_lines) if frame_lines else "_None_")
            + "\n\n"
            "**🎨 Colors**\n"
            + ("\n".join(color_lines) if color_lines else "_None_")
            + "\n\n"
            "**Preview:** `!preview frame <id>` or `!preview color <name>`\n"
            "**Buy:** `!buy frame <id>` or `!buy color <name>`\n"
            "**Equip:** `!equip frame <id|none>` or `!equip color <name|none>`"
        )

        embed = await create_embed("Shop", description, color=discord.Color.gold())
        await ctx.send(embed=embed)
        await self._delete_invocation(ctx)

    # ----------------------------
    # !preview
    # ----------------------------
    @commands.command(name="preview")
    async def preview(self, ctx, category: str, *, item: str):
        """
        Preview a frame (PNG) or a color (swatch).
        Usage:
          !preview frame <id>
          !preview color <name>
        """
        ensure_shop_schema(ctx.author)

        category = category.lower().strip()
        key = item.lower().strip()

        if category not in {"frame", "color"}:
            await self._send_plain(ctx, "Usage: `!preview frame <id>` or `!preview color <name>`")
            await self._delete_invocation(ctx)
            return

        # ---- Frame preview ----
        if category == "frame":
            frame_id = key

            if frame_id not in SHOP_FRAMES:
                await self._send_plain(ctx, "That frame is not sold in the shop.")
                await self._delete_invocation(ctx)
                return

            if not frame_exists(frame_id, frames_dir=PROFILE_FRAMES_DIR):
                await self._send_plain(ctx, "Frame PNG file is missing on the server.")
                await self._delete_invocation(ctx)
                return

            price = SHOP_FRAMES[frame_id]["price"]
            owned = owns_frame(ctx.author, frame_id)

            desc = (
                f"**{frame_id}** {format_price(price)}\n"
                f"Owned: **{'yes' if owned else 'no'}**\n\n"
                f"Buy: `!buy frame {frame_id}`\n"
                f"Equip: `!equip frame {frame_id}`"
            )

            embed = await create_embed("Frame Preview", desc, color=discord.Color.gold())

            file_name = f"{frame_id}.png"
            file = discord.File(frame_path(frame_id, frames_dir=PROFILE_FRAMES_DIR), filename=file_name)
            embed.set_image(url=f"attachment://{file_name}")

            await ctx.send(embed=embed, file=file)
            await self._delete_invocation(ctx)
            return

        # ---- Color preview ----
        color_name = key
        if color_name not in SHOP_COLORS:
            await self._send_plain(ctx, "That color is not sold in the shop.")
            await self._delete_invocation(ctx)
            return

        color_hex = SHOP_COLORS[color_name]["hex"]
        price = SHOP_COLORS[color_name]["price"]
        owned = owns_color(ctx.author, color_hex)

        desc = (
            f"**{color_name}** {format_price(price)}\n"
            f"Owned: **{'yes' if owned else 'no'}**\n\n"
            f"Buy: `!buy color {color_name}`\n"
            f"Equip: `!equip color {color_name}`"
        )

        r, g, b = _hex_to_rgb(color_hex)
        embed = await create_embed(
            "Color Preview",
            desc,
            color=discord.Color.from_rgb(r, g, b),
        )

        swatch_file, swatch_name = _make_color_swatch(color_hex, size=256)
        embed.set_thumbnail(url=f"attachment://{swatch_name}")

        await ctx.send(embed=embed, file=swatch_file)
        await self._delete_invocation(ctx)

    # ----------------------------
    # !buy
    # ----------------------------
    @commands.command(name="buy")
    async def buy(self, ctx, category: str, *, item: str):
        """
        Buy a shop item.
        Usage:
          !buy frame <id>
          !buy color <name>
        """
        ensure_shop_schema(ctx.author)

        category = category.lower().strip()
        key = item.lower().strip()

        if category not in {"frame", "color"}:
            await self._send_plain(ctx, "Usage: `!buy frame <id>` or `!buy color <name>`")
            await self._delete_invocation(ctx)
            return

        # -------- FRAME PURCHASE --------
        if category == "frame":
            frame_id = key

            if frame_id not in SHOP_FRAMES:
                await self._send_plain(ctx, "That frame is not sold in the shop.")
                await self._delete_invocation(ctx)
                return

            if not frame_exists(frame_id, frames_dir=PROFILE_FRAMES_DIR):
                await self._send_plain(ctx, "Frame PNG file is missing on the server.")
                await self._delete_invocation(ctx)
                return

            if owns_frame(ctx.author, frame_id):
                await self._send_plain(ctx, "You already own this frame.")
                await self._delete_invocation(ctx)
                return

            price = SHOP_FRAMES[frame_id]["price"]
            bal = get_balance(ctx.author)

            if bal < price:
                await self._send_plain(ctx, f"You need `{price}` gold, but only have `{bal}`.")
                await self._delete_invocation(ctx)
                return

            remove_currency(ctx.author, price)
            grant_frame(ctx.author, frame_id)

            embed = await create_embed(
                "Purchase Complete",
                f"{ctx.author.mention} bought **{frame_id}** {format_price(price)}.",
                color=discord.Color.green(),
            )
            await ctx.send(embed=embed)
            await self._delete_invocation(ctx)
            return

        # -------- COLOR PURCHASE --------
        color_name = key
        if color_name not in SHOP_COLORS:
            await self._send_plain(ctx, "That color is not sold in the shop.")
            await self._delete_invocation(ctx)
            return

        color_hex = SHOP_COLORS[color_name]["hex"]
        price = SHOP_COLORS[color_name]["price"]

        if owns_color(ctx.author, color_hex):
            await self._send_plain(ctx, "You already own this color.")
            await self._delete_invocation(ctx)
            return

        bal = get_balance(ctx.author)
        if bal < price:
            await self._send_plain(ctx, f"You need `{price}` gold, but only have `{bal}`.")
            await self._delete_invocation(ctx)
            return

        remove_currency(ctx.author, price)
        grant_color(ctx.author, color_hex)

        embed = await create_embed(
            "Purchase Complete",
            f"{ctx.author.mention} bought **{color_name}** {format_price(price)}.",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)
        await self._delete_invocation(ctx)

    # ----------------------------
    # !equip
    # ----------------------------
    @commands.command(name="equip")
    async def equip(self, ctx, category: str, *, item: str):
        """
        Equip an owned cosmetic.
        Usage:
          !equip frame <id|none>
          !equip color <name|none>
        """
        ensure_shop_schema(ctx.author)

        category = category.lower().strip()
        key = item.lower().strip()

        if category not in {"frame", "color"}:
            await self._send_plain(ctx, "Usage: `!equip frame <id|none>` or `!equip color <name|none>`")
            await self._delete_invocation(ctx)
            return

        # -------- FRAME EQUIP --------
        if category == "frame":
            if key == "none":
                equip_frame(ctx.author, None)
                await self._send_plain(ctx, "Frame unequipped.")
                await self._delete_invocation(ctx)
                return

            frame_id = key
            if not owns_frame(ctx.author, frame_id):
                await self._send_plain(ctx, "You don’t own that frame.")
                await self._delete_invocation(ctx)
                return

            equip_frame(ctx.author, frame_id)
            await self._send_plain(ctx, f"Equipped frame **{frame_id}**.")
            await self._delete_invocation(ctx)
            return

        # -------- COLOR EQUIP --------
        if key == "none":
            equip_color(ctx.author, None)
            await self._send_plain(ctx, "Accent color reset.")
            await self._delete_invocation(ctx)
            return

        color_name = key
        if color_name not in SHOP_COLORS:
            await self._send_plain(ctx, "That color is not sold in the shop.")
            await self._delete_invocation(ctx)
            return

        color_hex = SHOP_COLORS[color_name]["hex"]
        if not owns_color(ctx.author, color_hex):
            await self._send_plain(ctx, "You don’t own that color.")
            await self._delete_invocation(ctx)
            return

        equip_color(ctx.author, color_hex)
        await self._send_plain(ctx, f"Equipped color **{color_name}**.")
        await self._delete_invocation(ctx)

    # ----------------------------
    # !inventory
    # ----------------------------
    @commands.command(name="inventory")
    async def inventory(self, ctx, member: discord.Member | None = None):
        """Show a user's owned cosmetics (public)."""
        member = member or ctx.author
        ensure_shop_schema(member)

        frames = get_owned_frames(member)
        colors_hex = get_owned_colors(member)
        frame_eq, color_eq_hex = get_equipped(member)

        # Convert stored hex colors to names when possible (fallback to hex)
        colors_display = []
        for hx in colors_hex:
            colors_display.append(HEX_TO_COLOR_NAME.get(hx, hx))

        equipped_color_display = HEX_TO_COLOR_NAME.get(color_eq_hex, color_eq_hex) if color_eq_hex else "default"

        desc = (
            f"{member.mention}\n\n"
            f"**Equipped Frame:** **{frame_eq or 'none'}**\n"
            f"**Equipped Color:** **{equipped_color_display}**\n\n"
            f"**Owned Frames:** {', '.join(f'**{f}**' for f in frames) if frames else '_none_'}\n"
            f"**Owned Colors:** {', '.join(f'**{c}**' for c in colors_display) if colors_display else '_none_'}\n"
        )

        embed = await create_embed("Inventory", desc, color=discord.Color.blurple())
        await ctx.send(embed=embed)
        await self._delete_invocation(ctx)


async def setup(bot):
    await bot.add_cog(Shop(bot))
