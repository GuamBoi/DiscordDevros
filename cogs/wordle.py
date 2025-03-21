import discord
from discord.ext import commands
import os
import json
from config import GAME_WIN, ECONOMY_FOLDER
from utils import economy
from utils.embed import create_embed
from llm_api import query_llm_with_prompt  # New helper function

MAX_ATTEMPTS = 6

# Active games stored in-memory (keyed by user ID)
# Each game state is a dict: {"answer": <word>, "attempts": <int>, "guesses": [list of guesses], "message": <embed message object>}
active_games = {}

def generate_feedback(answer: str, guess: str) -> str:
    """
    Generates feedback for the guess using emojis:
      - 🟩 for correct letter in the correct position
      - 🟨 for correct letter in the wrong position
      - ⬜ for a letter not in the answer
    """
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
    """
    Builds a description string to show all guesses and the current game status.
    """
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
        """
        Starts a new Wordle game.
        The word is generated by querying the LLM server using the 'wordle_prompt'
        from prompts.json. The game is presented in an embed that will be updated as the game progresses.
        """
        user_id = str(ctx.author.id)
        
        # Query the LLM server for a random 5-letter word using the prompt from prompts.json
        word = (await query_llm_with_prompt("wordle_prompt", ctx)).strip().lower()
        if not word or len(word) != 5:
            await ctx.send(f"{ctx.author.mention} Failed to generate a valid 5-letter word. Please try again later.")
            return

        # Create the initial embed for the game
        initial_description = f"A new Wordle game has started! You have {MAX_ATTEMPTS} attempts to guess the word."
        embed = await create_embed("Wordle Game", initial_description)
        message = await ctx.send(embed=embed)
        
        # Store the game state along with the embed message
        active_games[user_id] = {
            "answer": word,
            "attempts": 0,
            "guesses": [],
            "message": message
        }

    @commands.command(name="guess")
    async def guess(self, ctx, guess_word: str):
        """
        Processes a guess for the active Wordle game.
        The embed is updated after each guess.
        If the guess is correct, the player's Wordle streak is incremented and currency is awarded.
        If the maximum attempts are reached, the streak is reset.
        """
        user_id = str(ctx.author.id)
        guess_word = guess_word.lower().strip()

        if user_id not in active_games:
            await ctx.send(f"{ctx.author.mention}, you need to start a Wordle game first using !wordle.")
            return

        game = active_games[user_id]
        answer = game["answer"]

        # Validate the guess length
        if len(guess_word) != len(answer):
            await ctx.send(f"Your guess must be {len(answer)} letters long.")
            return

        # Update game state with the guess
        game["attempts"] += 1
        game["guesses"].append(guess_word)
        
        # Build updated description for the embed
        description = build_game_description(game)
        
        # Check win condition
        if guess_word == answer:
            econ = economy.load_economy(user_id)
            if "wordle_streak" not in econ:
                econ["wordle_streak"] = 0
            econ["wordle_streak"] += 1
            economy.save_economy(user_id, econ)
            economy.add_currency(user_id, GAME_WIN)
            description += (
                f"\n\nCongratulations {ctx.author.mention}! You guessed the word in {game['attempts']} attempts."
                f"\nYour current Wordle streak is **{econ['wordle_streak']}** and you've been awarded **{GAME_WIN} {economy.get_currency_name()}**!"
            )
            embed = await create_embed("Wordle Game - You Won!", description)
            await game["message"].edit(embed=embed)
            del active_games[user_id]
            return

        # Check loss condition (maximum attempts reached)
        if game["attempts"] >= MAX_ATTEMPTS:
            econ = economy.load_economy(user_id)
            econ["wordle_streak"] = 0  # Reset streak on loss
            economy.save_economy(user_id, econ)
            description += f"\n\nSorry {ctx.author.mention}, you've used all your attempts. The correct word was **{answer}**. Your Wordle streak has been reset."
            embed = await create_embed("Wordle Game - Game Over", description)
            await game["message"].edit(embed=embed)
            del active_games[user_id]
            return

        # Otherwise, update the embed with the current game state
        embed = await create_embed("Wordle Game", description)
        await game["message"].edit(embed=embed)

    @commands.command(name="wordle_streaks")
    async def wordle_streaks(self, ctx):
        """
        Displays the top 10 players with the highest Wordle streaks.
        The leaderboard is generated by reading each user's economy file from ECONOMY_FOLDER.
        """
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
                except Exception:
                    continue

        streaks.sort(key=lambda x: x[1], reverse=True)
        top10 = streaks[:10]

        description = ""
        if top10:
            for i, (username, streak) in enumerate(top10, start=1):
                description += f"**{i}. {username}** - {streak}\n"
        else:
            description = "No streak data available."
        
        embed = await create_embed("Wordle Streak Leaderboard", description)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Wordle(bot))
