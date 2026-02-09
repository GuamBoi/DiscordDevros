# cogs/leaderboard.py
import os
import json
import discord
from discord.ext import commands
from config import ECONOMY_FOLDER, CURRENCY_SYMBOL
from utils.embed import create_embed

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _delete_invocation(self, ctx):
        try:
            await ctx.message.delete()
        except (discord.NotFound, discord.Forbidden):
            pass

    def _iter_economy_records(self):
        """
        Yields tuples: (user_id: int, data: dict)
        Economy files are assumed to be ID-keyed: <user_id>.json
        """
        for filename in os.listdir(ECONOMY_FOLDER):
            if not filename.endswith(".json"):
                continue

            user_id_str = filename[:-5]
            if not user_id_str.isdigit():
                continue

            path = os.path.join(ECONOMY_FOLDER, filename)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                continue

            yield int(user_id_str), data

    def _format_member(self, ctx, user_id: int):
        member = ctx.guild.get_member(user_id)
        if member:
            return member.mention, member.display_name
        return f"`{user_id}`", "Unknown Member"

    # --------------------------------------------------
    # GENERAL LEADERBOARD (Level / XP / Currency)
    # --------------------------------------------------
    @commands.command(
        name="leaderboard",
        help="Show top 10 users by level and XP, including currency"
    )
    async def leaderboard(self, ctx):
        users = []

        for user_id, data in self._iter_economy_records():
            users.append((
                user_id,
                int(data.get("level", 1) or 1),
                int(data.get("xp", 0) or 0),
                int(data.get("currency", 0) or 0),
            ))

        users.sort(key=lambda x: (x[1], x[2]), reverse=True)
        top10 = users[:10]

        lines = []
        for i, (user_id, lvl, xp, bal) in enumerate(top10, start=1):
            mention, display = self._format_member(ctx, user_id)
            lines.append(
                f"**{i}.** {mention} ({display}) — "
                f"Level {lvl} ({xp} XP) — {CURRENCY_SYMBOL}{bal}"
            )

        if not lines:
            lines = ["No leaderboard data available yet."]

        embed = await create_embed(
            title="🏆 Leaderboard: Top Levels & Currency",
            description="\n".join(lines),
            color=discord.Color.gold(),  # ✅ yellow
        )

        await ctx.send(embed=embed)
        await self._delete_invocation(ctx)

    # --------------------------------------------------
    # BATTLESHIP LEADERBOARD (Win Streak)
    # --------------------------------------------------
    @commands.command(
        name="battleship_leaderboard",
        help="Show top 10 users by Battleship win streak"
    )
    async def battleship_leaderboard(self, ctx):
        rows = []
        for user_id, data in self._iter_economy_records():
            streak = int(data.get("battleship_streak", 0) or 0)
            if streak > 0:
                rows.append((user_id, streak))

        rows.sort(key=lambda x: x[1], reverse=True)
        top10 = rows[:10]

        lines = []
        for i, (user_id, streak) in enumerate(top10, start=1):
            mention, display = self._format_member(ctx, user_id)
            lines.append(f"**{i}.** {mention} ({display}) — 🔥 `{streak}`")

        if not lines:
            lines = ["No Battleship streak data yet."]

        embed = await create_embed(
            title="🚢 Battleship Leaderboard",
            description="\n".join(lines),
            color=discord.Color.gold(),  # ✅ yellow
        )

        await ctx.send(embed=embed)
        await self._delete_invocation(ctx)

    # --------------------------------------------------
    # CONNECT4 LEADERBOARD (Win Streak)
    # --------------------------------------------------
    @commands.command(
        name="connect4_leaderboard",
        help="Show top 10 users by Connect4 win streak"
    )
    async def connect4_leaderboard(self, ctx):
        rows = []
        for user_id, data in self._iter_economy_records():
            streak = int(data.get("connect4_streak", 0) or 0)
            if streak > 0:
                rows.append((user_id, streak))

        rows.sort(key=lambda x: x[1], reverse=True)
        top10 = rows[:10]

        lines = []
        for i, (user_id, streak) in enumerate(top10, start=1):
            mention, display = self._format_member(ctx, user_id)
            lines.append(f"**{i}.** {mention} ({display}) — 🔥 `{streak}`")

        if not lines:
            lines = ["No Connect4 streak data yet."]

        embed = await create_embed(
            title="🔴 Connect4 Leaderboard",
            description="\n".join(lines),
            color=discord.Color.gold(),  # ✅ yellow
        )

        await ctx.send(embed=embed)
        await self._delete_invocation(ctx)

    # --------------------------------------------------
    # WORDLE LEADERBOARD (Win Streak)
    # --------------------------------------------------
    @commands.command(
        name="wordle_leaderboard",
        help="Show top 10 users by Wordle win streak"
    )
    async def wordle_leaderboard(self, ctx):
        rows = []
        for user_id, data in self._iter_economy_records():
            streak = int(data.get("wordle_streak", 0) or 0)
            if streak > 0:
                rows.append((user_id, streak))

        rows.sort(key=lambda x: x[1], reverse=True)
        top10 = rows[:10]

        lines = []
        for i, (user_id, streak) in enumerate(top10, start=1):
            mention, display = self._format_member(ctx, user_id)
            lines.append(f"**{i}.** {mention} ({display}) — 🔥 `{streak}`")

        if not lines:
            lines = ["No Wordle streak data yet."]

        embed = await create_embed(
            title="🟩 Wordle Leaderboard",
            description="\n".join(lines),
            color=discord.Color.gold(),  # ✅ yellow
        )

        await ctx.send(embed=embed)
        await self._delete_invocation(ctx)

async def setup(bot):
    await bot.add_cog(Leaderboard(bot))
