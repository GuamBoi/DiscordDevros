import discord
from discord.ext import commands
import os
import json
import random
from config import GAME_WIN, GAME_LOSE, ECONOMY_FOLDER, WORDLE_CHANNEL, CURRENCY_NAME
from utils import economy
from utils.embed import create_embed
from utils.economy import user_key

MAX_ATTEMPTS = 6
WORDLE_WORDS_FILE = os.path.join("data", "wordle_words.txt")

# Active games stored in-memory (keyed by user_key -> str(member.id))
active_games = {}

def ensure_wordle_file():
    if not os.path.exists(WORDLE_WORDS_FILE):
        with open(WORDLE_WORDS_FILE, "w", encoding="utf-8") as f:
            pass

def get_random_word_from_file():
    ensure_wordle_file()
    with open(WORDLE_WORDS_FILE, "r", encoding="utf-8") as f:
        words = [line.strip().lower() for line in f if len(line.strip()) == 5]
    return random.choice(words) if words else None

def generate_feedback(answer: str, guess: str) -> str:
    feedback = ""
    for i, char in enumerate(guess):
        if char == answer[i]:
            feedback += "🟩"
        elif char in answer:
            feedback += "🟨"
        else:
            feedback += "⬜"
    return feedback

def build_game_description(game_state) -> str:
    description = ""
    for guess in game_state["guesses"]:
        feedback = generate_feedback(game_state["answer"], guess)
        description += f"`{guess}` - {feedback}\n"
    attempts_left = MAX_ATTEMPTS - game_state["attempts"]
    description += f"\nAttempts remaining: **{attempts_left}**"
    return description

class Wordle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="wordle")
    async def wordle(self, ctx):
        await ctx.message.delete()
        key = user_key(ctx.author)  # ID-keyed economy identity

        # Get a random word from the file
        word = get_random_word_from_file()
        if not word:
            await ctx.send(
                f"{ctx.author.mention} No valid word available. Please add some 5-letter words to the file."
            )
            return

        channel = self.bot.get_channel(WORDLE_CHANNEL)
        embed = await create_embed(
            "Wordle Game",
            f"A new Wordle game has started! You have {MAX_ATTEMPTS} attempts to guess the word."
        )
        message = await channel.send(embed=embed)

        active_games[key] = {"answer": word, "attempts": 0, "guesses": [], "message": message}

    @commands.command(name="guess")
    async def guess(self, ctx, guess_word: str):
        await ctx.message.delete()
        key = user_key(ctx.author)  # ID-keyed
        guess_word = guess_word.lower().strip()

        if key not in active_games:
            await ctx.send(f"{ctx.author.mention}, you need to start a Wordle game first using !wordle.")
            return

        game = active_games[key]
        answer = game["answer"]

        if len(guess_word) != len(answer):
            await ctx.send(f"Your guess must be {len(answer)} letters long.")
            return

        game["attempts"] += 1
        game["guesses"].append(guess_word)

        description = build_game_description(game)

        if guess_word == answer:
            econ = economy.load_economy(key)
            econ["wordle_streak"] = econ.get("wordle_streak", 0) + 1
            economy.save_economy(key, econ)
            economy.add_currency(key, GAME_WIN)

            description += (
                f"\n\nCongratulations {ctx.author.mention}! "
                f"You won and earned **{GAME_WIN} {CURRENCY_NAME}**!"
            )
            del active_games[key]

        elif game["attempts"] >= MAX_ATTEMPTS:
            econ = economy.load_economy(key)
            econ["wordle_streak"] = 0
            economy.save_economy(key, econ)
            economy.remove_currency(key, GAME_LOSE)

            description += (
                f"\n\nGame Over {ctx.author.mention}! The correct word was **{answer}**. "
                f"You lost **{GAME_LOSE} {CURRENCY_NAME}**."
            )
            del active_games[key]

        embed = await create_embed("Wordle Game", description)
        await game["message"].edit(embed=embed)

    @commands.command(name="wordle_leaderboard")
    async def wordle_leaderboard(self, ctx):
        # Delete the command message to keep the channel clean
        await ctx.message.delete()

        streaks = []
        for filename in os.listdir(ECONOMY_FOLDER):
            if not filename.endswith(".json"):
                continue

            user_id_str = filename[:-5]  # strip ".json"
            if not user_id_str.isdigit():
                continue

            filepath = os.path.join(ECONOMY_FOLDER, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                print(f"Error reading {filename}: {e}")
                continue

            streak = int(data.get("wordle_streak", 0) or 0)
            streaks.append((int(user_id_str), streak))

        streaks.sort(key=lambda x: x[1], reverse=True)
        top10 = streaks[:10]

        if not top10:
            description = "No streak data available."
        else:
            lines = []
            for user_id, streak in top10:
                member = ctx.guild.get_member(user_id)
                if member:
                    lines.append(f"{member.mention} ({member.display_name}) - `{streak}`")
                else:
                    lines.append(f"`{user_id}` (Unknown Member) - `{streak}`")
            description = "\n".join(lines)

        embed = await create_embed("Wordle Leaderboard", description, color=discord.Color.gold())
        await ctx.send(embed=embed)
async def setup(bot):
    await bot.add_cog(Wordle(bot))
