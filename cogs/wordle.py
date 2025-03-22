import discord
from discord.ext import commands
import os
import json
import random
from config import GAME_WIN, GAME_LOSE, ECONOMY_FOLDER, WORDLE_CHANNEL
from utils import economy
from utils.embed import create_embed
from utils.llm_api import query_llm_with_prompt

MAX_ATTEMPTS = 6
WORDLE_WORDS_FILE = os.path.join('data', 'wordle_words.txt')

# Active games stored in-memory
active_games = {}

def ensure_wordle_file():
    if not os.path.exists(WORDLE_WORDS_FILE):
        with open(WORDLE_WORDS_FILE, 'w') as f:
            pass

def add_word_to_file(word):
    ensure_wordle_file()
    with open(WORDLE_WORDS_FILE, 'r') as f:
        words = {line.strip() for line in f}
    if word not in words:
        with open(WORDLE_WORDS_FILE, 'a') as f:
            f.write(f"{word}\n")
            print(f"Word '{word}' added to Wordle Words file.")

def get_random_word_from_file():
    ensure_wordle_file()
    with open(WORDLE_WORDS_FILE, 'r') as f:
        words = [line.strip() for line in f if len(line.strip()) == 5]
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
        description += f"Guess: `{guess}` - {feedback}\n"
    attempts_left = MAX_ATTEMPTS - game_state["attempts"]
    description += f"\nAttempts remaining: **{attempts_left}**"
    return description

class Wordle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="wordle")
    async def wordle(self, ctx):
        await ctx.message.delete()
        username = ctx.author.name

        # Try generating word with LLM
        word = (await query_llm_with_prompt("wordle_prompt", ctx)).strip().lower()
        print(f"Generated word: {word}")

        # Validate the word and add it to the wordle file if valid
        if word and len(word) == 5:
            add_word_to_file(word)
        else:
            word = get_random_word_from_file()
            if not word:
                await ctx.send(f"{ctx.author.mention} Failed to generate a valid word. Please try again later.")
                return
            print(f"Using fallback word: {word}")

        # Create game state
        channel = self.bot.get_channel(WORDLE_CHANNEL)
        embed = await create_embed("Wordle Game", f"A new Wordle game has started! You have {MAX_ATTEMPTS} attempts to guess the word.")
        message = await channel.send(embed=embed)
        active_games[username] = {"answer": word, "attempts": 0, "guesses": [], "message": message}

    @commands.command(name="guess")
    async def guess(self, ctx, guess_word: str):
        await ctx.message.delete()
        username = ctx.author.name
        guess_word = guess_word.lower().strip()

        if username not in active_games:
            await ctx.send(f"{ctx.author.mention}, you need to start a Wordle game first using !wordle.")
            return

        game = active_games[username]
        answer = game["answer"]

        if len(guess_word) != len(answer):
            await ctx.send(f"Your guess must be {len(answer)} letters long.")
            return

        game["attempts"] += 1
        game["guesses"].append(guess_word)

        description = build_game_description(game)

        if guess_word == answer:
            econ = economy.load_economy(username)
            econ["wordle_streak"] = econ.get("wordle_streak", 0) + 1
            economy.save_economy(username, econ)
            economy.add_currency(username, GAME_WIN)
            description += f"\n\nCongratulations {ctx.author.mention}! You won and earned **{GAME_WIN} {economy.get_currency_name()}**!"
            del active_games[username]
        elif game["attempts"] >= MAX_ATTEMPTS:
            econ = economy.load_economy(username)
            econ["wordle_streak"] = 0
            economy.save_economy(username, econ)
            economy.remove_currency(username, GAME_LOSE)
            description += f"\n\nGame Over! The correct word was **{answer}**. You lost **{GAME_LOSE} {economy.get_currency_name()}**."
            del active_games[username]

        embed = await create_embed("Wordle Game", description)
        await game["message"].edit(embed=embed)

    @commands.command(name="wordle_streaks")
    async def wordle_streaks(self, ctx):
        streaks = []
        for filename in os.listdir(ECONOMY_FOLDER):
            if filename.endswith(".json"):
                filepath = os.path.join(ECONOMY_FOLDER, filename)
                try:
                    with open(filepath, "r") as f:
                        data = json.load(f)
                    streak = data.get("wordle_streak", 0)
                    username = data.get("username", filename[:-5])
                    streaks.append((username, streak))
                except Exception as e:
                    print(f"Error reading {filename}: {e}")

        streaks.sort(key=lambda x: x[1], reverse=True)
        top10 = streaks[:10]

        description = "".join(f"{username} - `{streak}`\n" for username, streak in top10) or "No streak data available."
        embed = await create_embed("Wordle Streak Leaderboard", description, color=discord.Color.gold())
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Wordle(bot))
