import os
import json
import discord
from discord.ext import commands
from config import ECONOMY_FOLDER, CURRENCY_SYMBOL
from utils.embed import create_embed

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="leaderboard",
        help="Show top 10 users by level and XP, including currency"
    )
    async def leaderboard(self, ctx):
        users = []

        # Economy files are now ID-keyed: <user_id>.json
        for filename in os.listdir(ECONOMY_FOLDER):
            if not filename.endswith(".json"):
                continue

            user_id_str = filename[:-5]  # strip ".json"
            if not user_id_str.isdigit():
                continue

            path = os.path.join(ECONOMY_FOLDER, filename)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                continue

            users.append((
                int(user_id_str),                # user_id
                data.get("level", 1),
                data.get("xp", 0),
                data.get("currency", 0)
            ))

        # Sort by level first, then XP (descending)
        users.sort(key=lambda x: (x[1], x[2]), reverse=True)
        top10 = users[:10]

        leaderboard_text = ""

        for i, (user_id, lvl, xp, bal) in enumerate(top10, start=1):
            member = ctx.guild.get_member(user_id)

            if member:
                mention = member.mention
                display = member.display_name
            else:
                mention = f"`{user_id}`"
                display = "Unknown Member"

            leaderboard_text += (
                f"**{i}.** {mention} ({display}) — "
                f"Level {lvl} ({xp} XP) — {CURRENCY_SYMBOL}{bal}\n"
            )

        if not leaderboard_text:
            leaderboard_text = "No leaderboard data available yet."

        embed = await create_embed(
            title="Leaderboard: Top Levels & Currency",
            description=leaderboard_text,
            color=discord.Color.purple()
        )

        await ctx.send(embed=embed)

        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

async def setup(bot):
    await bot.add_cog(Leaderboard(bot))
