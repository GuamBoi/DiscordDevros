import discord
import asyncio
import os
import json
from discord.ext import commands

from utils.economy import add_currency, remove_currency, load_economy, save_economy
from utils.embed import create_embed
from config import GAME_WIN, GAME_LOSE, CURRENCY_NAME, CONNECT4_CHANNEL, ECONOMY_FOLDER

# Emoji definitions (using Unicode number emojis for columns 1-7)
number_emojis = ["\u0031\u20E3", "\u0032\u20E3", "\u0033\u20E3", "\u0034\u20E3", "\u0035\u20E3", "\u0036\u20E3", "\u0037\u20E3"]

# Board and token definitions (using your custom Discord emoji IDs)
ConnectBoard = "<:ConnectBoard:1213906784821977118>"
ConnectRed = "<:ConnectRed:1213906783437848616>"
ConnectYellow = "<:ConnectYellow:1213906785941987399>"

# Player class to track players
class Connect4Player:
    def __init__(self, member, token_emoji):
        self.member = member
        self.token_emoji = token_emoji

# The game logic encapsulated in a class
class Connect4Game:
    def __init__(self, player1, player2):
        # Initialize the board with empty slots (using ConnectBoard emoji)
        self.board = [[ConnectBoard for _ in range(7)] for _ in range(6)]
        self.column_heights = [0] * 7  # Tracks the number of chips in each column
        # Reverse the order: opponent goes first, then challenger.
        self.players = [player2, player1]
        self.turn = 0  # Starts with the opponent (index 0)
        self.active = True
        self.winner = None

    async def make_move(self, column, ctx):
        if not self.active:
            return "Game is already over."
        if not 0 <= column < 7:
            return "Invalid column. Please choose a column between 1 and 7."
        row = self.column_heights[column]
        if row >= 6:
            return "Column is full. Please choose another column."
        # Place the player's token on the board
        self.board[row][column] = self.players[self.turn].token_emoji
        self.column_heights[column] += 1
        if self.check_winner(row, column):
            self.active = False
            self.winner = self.players[self.turn]
        else:
            self.turn = 1 - self.turn  # Switch turns
        return None

    def check_winner(self, row, col):
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        token = self.board[row][col]
        for dr, dc in directions:
            count = 1
            # Check in the forward direction
            for i in range(1, 4):
                r, c = row + i * dr, col + i * dc
                if 0 <= r < 6 and 0 <= c < 7 and self.board[r][c] == token:
                    count += 1
                else:
                    break
            # Check in the backward direction
            for i in range(1, 4):
                r, c = row - i * dr, col - i * dc
                if 0 <= r < 6 and 0 <= c < 7 and self.board[r][c] == token:
                    count += 1
                else:
                    break
            if count >= 4:
                return True
        return False

# Cog to hold the Connect4 commands
class Connect4(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def create_game_board_embed(self, game):
        """Creates an embed displaying the current game board."""
        board_str = ""
        # Loop from top (row 5) to bottom (row 0)
        for row in range(5, -1, -1):
            board_str += "".join(game.board[row]) + "\n"
        
        # Add a single blank line between the game board and the numbers
        board_str += "\n"
        
        # Add number emojis as column headers (separated by spaces)
        board_str += " ".join(number_emojis)
        
        # Choose embed color based on whose token is active
        color = discord.Color.red() if game.players[game.turn].token_emoji == ConnectRed else discord.Color.gold()
        embed = await create_embed("Connect 4", board_str, color=color)
        return embed

    @commands.command()
    async def connect4(self, ctx, opponent: discord.Member):
        """Starts a game of Connect4 with the mentioned opponent."""
        # Delete the command message to keep channels clean
        await ctx.message.delete()

        if opponent == ctx.author:
            await ctx.send("You cannot play against yourself!")
            return

        # Get the channel defined in the config
        channel = self.bot.get_channel(CONNECT4_CHANNEL)
        if channel is None:
            await ctx.send("Connect4 channel not found.")
            return

        # Initialize players with their respective tokens
        # Challenger is ctx.author and opponent is the mentioned user.
        player1 = Connect4Player(ctx.author, ConnectRed)
        player2 = Connect4Player(opponent, ConnectYellow)
        game = Connect4Game(player1, player2)

        board_embed = await self.create_game_board_embed(game)
        game_message = await channel.send(f"{game.players[game.turn].member.mention}, it's your turn!", embed=board_embed)

        # Add number reactions (for columns 1-7)
        for emoji in number_emojis:
            await game_message.add_reaction(emoji)

        # Reaction check function
        def check(reaction, user):
            return (
                user == game.players[game.turn].member and
                reaction.message.id == game_message.id and
                str(reaction.emoji) in number_emojis
            )

        # Main game loop (no timeout so users can play at their own pace)
        while game.active:
            reaction, user = await self.bot.wait_for('reaction_add', check=check)
            column = number_emojis.index(str(reaction.emoji))
            error = await game.make_move(column, ctx)
            if error:
                await channel.send(error)
            else:
                new_embed = await self.create_game_board_embed(game)
                # Ping the current player for their turn
                await game_message.edit(content=f"{game.players[game.turn].member.mention}, it's your turn!", embed=new_embed)
            # Remove the reaction so players can reuse it in future moves
            try:
                await game_message.remove_reaction(reaction.emoji, user)
            except Exception:
                pass

        # Game has ended – update the economy and streak values
        if game.winner:
            winner = game.winner
            loser = game.players[1 - game.players.index(winner)]
            add_currency(winner.member.name, GAME_WIN)
            remove_currency(loser.member.name, GAME_LOSE)
            # Update Connect4 streak for winner and reset for loser
            winner_data = load_economy(winner.member.name)
            winner_data["connect4_streak"] = winner_data.get("connect4_streak", 0) + 1
            save_economy(winner.member.name, winner_data)
            loser_data = load_economy(loser.member.name)
            loser_data["connect4_streak"] = 0
            save_economy(loser.member.name, loser_data)

            result_embed = await create_embed(
                "Game Over",
                f"{winner.member.mention} wins!\nYou have been awarded {GAME_WIN} {CURRENCY_NAME}.\n"
                f"{loser.member.mention} loses {GAME_LOSE} {CURRENCY_NAME}.\n"
                f"{winner.member.mention} now has a Connect4 win streak of {winner_data['connect4_streak']}.",
                color=discord.Color.green()
            )
            await channel.send(embed=result_embed)
        else:
            await channel.send("It's a draw!")

    @commands.command()
    async def connect4_leaderboard(self, ctx):
        """Displays the top 10 members with the highest Connect4 win streaks."""
        # Delete the command message to keep channels clean
        await ctx.message.delete()

        leaderboard = []
        # Iterate over all economy files
        for filename in os.listdir(ECONOMY_FOLDER):
            if filename.endswith(".json"):
                filepath = os.path.join(ECONOMY_FOLDER, filename)
                with open(filepath, 'r') as f:
                    data = json.load(f)
                streak = data.get("connect4_streak", 0)
                username = data.get("username", "Unknown")
                leaderboard.append((username, streak))
        # Sort by streak descending
        leaderboard.sort(key=lambda x: x[1], reverse=True)
        top10 = leaderboard[:10]

        description = ""
        for idx, (username, streak) in enumerate(top10, start=1):
            # Try to get the guild member to mention them; fallback to username if not found
            member = ctx.guild.get_member_named(username)
            mention = member.mention if member else username
            description += f"**{idx}.** {mention} - `{streak}`\n"

        embed = await create_embed("Connect4 Leaderboard", description, color=discord.Color.gold())
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Connect4(bot))
