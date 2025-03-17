import discord
from discord.ext import commands
import config
from utils.llm_api import query_llm  # Use your current LLM query function

# Helper function to generate a random 5-letter word using the LLM API
async def generate_word():
    prompt = "Generate a random 5-letter word for a Wordle game. Your final answer MUST only include 1 word with 5 alphabetic letters inorder for the game to work correctly!"
    word = await query_llm(prompt)
    word = word.strip().lower()
    # Validate that the result is exactly 5 letters; fallback if not
    if len(word) != 5:
        # Fallback to a default word or you can choose to reprompt
        return "apple"
    return word

# Helper function to generate a custom win or lose message using the LLM API
async def generate_result_message(username: str, win: bool, attempts: list, correct_word: str):
    if win:
        prompt = (
            f"{username} just played Wordle and guessed the word '{correct_word}' correctly in {len(attempts)} attempts! Write a congratulatory message that includes their name, the word '{correct_word}', and how many guesses thy used with a fun and creative tone. Example Message: Congragulations {username}! You correctly guessed the word '{correct_word}' in {len(attempts)} attempt(s)!"
        )
    else:
        prompt = (
            f"{username} just played Wordle and failed to guess the word '{correct_word}' after 6 attempts. Write a consoling message that includes their name and the word '{correct_word}', encouraging them to try again. Example Message: Nice try, {username}, but the correct word was '{correct_word}'! Start a new game to try again!"
        )

    message = await query_llm(prompt)
    return message

class WordleGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}  # Stores game state for each user

    @commands.command(name="wordle")
    async def wordle(self, ctx):
        """Starts a new Wordle game using an AI-generated word."""
        user = ctx.author
        if user.id in self.active_games:
            await ctx.send("You already have an active game! Finish it first.")
            return

        # Generate the secret word using the LLM
        word = await generate_word()
        if not word or len(word) != 5:
            await ctx.send("Error generating a valid 5-letter word. Please try again.")
            return

        # Save the game state for this user
        self.active_games[user.id] = {
            "word": word,
            "attempts": [],
            "won": False
        }

        embed = discord.Embed(
            title="Wordle Game",
            description="Guess the 5-letter word!",
            color=discord.Color.blue()
        )
        embed.add_field(name="Attempts Left", value="6", inline=False)
        embed.set_footer(text="Use !guess <word> to make a guess.")

        # Always send the game embed to the channel specified in config.WORDLE_CHANNEL
        channel = self.bot.get_channel(config.WORDLE_CHANNEL)
        if channel:
            await channel.send(embed=embed)
        else:
            await ctx.send("Wordle game channel not found. Please check the config file.")

    @commands.command(name="guess")
    async def guess(self, ctx, word: str):
        """Allows the user to make a guess in an active Wordle game."""
        user = ctx.author
        if user.id not in self.active_games:
            await ctx.send("You don't have an active Wordle game! Start one with !wordle.")
            return

        game = self.active_games[user.id]
        if game["won"]:
            await ctx.send("You've already won! Start a new game with !wordle.")
            return

        # Validate that the guess is exactly 5 alphabetic letters
        if len(word) != 5 or not word.isalpha():
            await ctx.send("Your guess must be exactly 5 alphabetic letters!")
            return

        word = word.lower()
        game["attempts"].append(word)
        attempts_left = 6 - len(game["attempts"])

        # If the guess is correct, generate a custom win message using the LLM
        if word == game["word"]:
            game["won"] = True
            custom_message = await generate_result_message(True, game["attempts"], game["word"])
            await ctx.send(custom_message)
            # Here you can add logic to award coins, etc.
            del self.active_games[user.id]
            return

        # If no attempts remain, generate a custom lose message using the LLM
        if attempts_left <= 0:
            custom_message = await generate_result_message(False, game["attempts"], game["word"])
            await ctx.send(custom_message)
            del self.active_games[user.id]
            return

        await ctx.send(f"Incorrect guess. Attempts left: {attempts_left}")

async def setup(bot):
    await bot.add_cog(WordleGame(bot))
