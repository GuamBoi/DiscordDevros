import discord
from discord.ext import commands
import os
import json
import random
from config import GAME_WIN, GAME_LOSE, ECONOMY_FOLDER
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

class Wordle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="wordle")
    async def wordle(self, ctx):
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
        embed = await create_embed("Wordle Game", f"A new Wordle game has started! You have {MAX_ATTEMPTS} attempts to guess the word.")
        message = await ctx.send(embed=embed)
        active_games[username] = {"answer": word, "attempts": 0, "guesses": [], "message": message}

    @commands.command(name="guess")
    async def guess(self, ctx, guess_word: str):
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

async def setup(bot):
    await bot.add_cog(Wordle(bot))
