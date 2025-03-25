import discord
from discord.ext import commands
import asyncio
import re
from utils.embed import create_embed
from utils.economy import add_currency, remove_currency, load_economy, save_economy
from config import GAME_WIN, GAME_LOSE, BATTLESHIP_CHANNEL

# --- Constants & Helper Functions ---

EMPTY_CELL = "⬜"       # Open ocean
SHIP_CELL = "🟩"        # Placed ship cell during placement
HIT_CELL = "🟥"         # Ship hit
MISS_CELL = "🟦"        # Miss (blue square)

# Arrow emojis used as cursor; also indicate orientation.
CURSOR_EMOJIS = {
    "left": ":rewind:",
    "up": ":arrow_double_up:",
    "right": ":fast_forward:",
    "down": ":arrow_double_down:"
}

# Valid orientations in order.
ORIENTATIONS = ["right", "down", "left", "up"]

# Grid labels for a 10x10 board.
ROWS = list("ABCDEFGHIJ")
COLUMNS = [str(i) for i in range(1, 11)]

def coords_to_label(row, col):
    return f"{ROWS[row]}{col+1}"

# --- Battleship Game State Class ---

class BattleshipGame:
    def __init__(self, player1: discord.Member, player2: discord.Member):
        self.player1 = player1
        self.player2 = player2
        # Each player's board for ship placements and damage.
        self.board1 = [[EMPTY_CELL for _ in range(10)] for _ in range(10)]
        self.board2 = [[EMPTY_CELL for _ in range(10)] for _ in range(10)]
        # Record of shots fired by each player (for shot history).
        self.shots1 = [[EMPTY_CELL for _ in range(10)] for _ in range(10)]
        self.shots2 = [[EMPTY_CELL for _ in range(10)] for _ in range(10)]
        # Ships placed: dictionary mapping ship size to list of coordinates.
        self.ships1 = {}
        self.ships2 = {}
        # Each player must place one ship for each of these sizes.
        self.ship_sizes = [2, 3, 4, 5]
        # Ready flags for each player's placement phase.
        self.placement_ready = {self.player1: False, self.player2: False}
        self.phase = "placement"  # or "firing"
        self.current_turn = None  # For firing phase

    def can_place_ship(self, board, start_row, start_col, ship_size, orientation):
        """Return list of coordinates if ship placement is valid; else None."""
        coords = []
        for i in range(ship_size):
            if orientation == "left":
                r, c = start_row, start_col - i
            elif orientation == "right":
                r, c = start_row, start_col + i
            elif orientation == "up":
                r, c = start_row - i, start_col
            elif orientation == "down":
                r, c = start_row + i, start_col
            else:
                return None
            if not (0 <= r < 10 and 0 <= c < 10):
                return None
            if board[r][c] != EMPTY_CELL:
                return None
            coords.append((r, c))
        return coords

    def place_ship(self, player: discord.Member, ship_size: int, coords: list):
        """Place a ship on the player's board and record it."""
        if player == self.player1:
            board = self.board1
            self.ships1[ship_size] = coords
        else:
            board = self.board2
            self.ships2[ship_size] = coords
        for r, c in coords:
            board[r][c] = SHIP_CELL

    def remove_ship(self, player: discord.Member, ship_size: int):
        """Remove a placed ship of the given size from the player's board."""
        if player == self.player1:
            if ship_size in self.ships1:
                coords = self.ships1.pop(ship_size)
                board = self.board1
            else:
                return False
        else:
            if ship_size in self.ships2:
                coords = self.ships2.pop(ship_size)
                board = self.board2
            else:
                return False
        for r, c in coords:
            board[r][c] = EMPTY_CELL
        return True

    def remove_all_ships(self, player: discord.Member):
        """Remove all ships for the given player."""
        removed_any = False
        for size in self.ship_sizes:
            if player == self.player1 and size in self.ships1:
                self.remove_ship(player, size)
                removed_any = True
            elif player == self.player2 and size in self.ships2:
                self.remove_ship(player, size)
                removed_any = True
        return removed_any

    def board_to_string(self, board):
        """Return a string representation of a board with labels."""
        s = "   " + " ".join(COLUMNS) + "\n"
        for i, row in enumerate(board):
            s += ROWS[i] + "  " + " ".join(row) + "\n"
        return s

    def placement_board_to_string(self, board, cursor_data=None):
        """
        Return a string representation of the board for ship placement.
        If cursor_data is provided as ((row, col), emoji), that cell is overlaid with the emoji.
        """
        display = []
        for r in range(10):
            row_disp = []
            for c in range(10):
                if cursor_data and (r, c) == cursor_data[0]:
                    row_disp.append(cursor_data[1])
                else:
                    row_disp.append(board[r][c])
            display.append(row_disp)
        s = "   " + " ".join(COLUMNS) + "\n"
        for i, row in enumerate(display):
            s += ROWS[i] + "  " + " ".join(row) + "\n"
        return s

    def fire(self, player: discord.Member, target: str):
        """
        Fire at a target cell on the opponent's board.
        Mark hit/miss on both the opponent's board and the player's shot board.
        Returns 'hit', 'miss', or an error message.
        """
        m = re.match(r"^([A-Ja-j])([1-9]|10)$", target)
        if not m:
            return "Invalid target. Use format like A1."
        row_letter = m.group(1).upper()
        col = int(m.group(2)) - 1
        row = ROWS.index(row_letter)
        if player == self.player1:
            opp_board = self.board2
            shot_board = self.shots1
            ships = self.ships2
        else:
            opp_board = self.board1
            shot_board = self.shots2
            ships = self.ships1
        if opp_board[row][col] in [HIT_CELL, MISS_CELL]:
            return "You already fired at that cell."
        hit = False
        for coords in ships.values():
            if (row, col) in coords:
                hit = True
                opp_board[row][col] = HIT_CELL
                shot_board[row][col] = HIT_CELL
                break
        if not hit:
            opp_board[row][col] = MISS_CELL
            shot_board[row][col] = MISS_CELL
        return "hit" if hit else "miss"

# --- UI Views ---

class ShipSizeView(discord.ui.View):
    """Allows a player to select a ship size via buttons."""
    def __init__(self):
        super().__init__(timeout=300)
        self.selected_size = None

    @discord.ui.button(label="2", style=discord.ButtonStyle.secondary)
    async def size2(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.selected_size = 2
        await interaction.response.send_message("Ship size 2 selected.", ephemeral=True)
        self.stop()

    @discord.ui.button(label="3", style=discord.ButtonStyle.secondary)
    async def size3(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.selected_size = 3
        await interaction.response.send_message("Ship size 3 selected.", ephemeral=True)
        self.stop()

    @discord.ui.button(label="4", style=discord.ButtonStyle.secondary)
    async def size4(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.selected_size = 4
        await interaction.response.send_message("Ship size 4 selected.", ephemeral=True)
        self.stop()

    @discord.ui.button(label="5", style=discord.ButtonStyle.secondary)
    async def size5(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.selected_size = 5
        await interaction.response.send_message("Ship size 5 selected.", ephemeral=True)
        self.stop()

class ShipPlacementGridView(discord.ui.View):
    """
    Interactive grid for ship placement.
    The cursor is shown as an arrow emoji reflecting the current orientation.
    """
    def __init__(self, game: BattleshipGame, player: discord.Member, ship_size: int):
        super().__init__(timeout=300)
        self.game = game
        self.player = player
        self.ship_size = ship_size
        self.cursor = (0, 0)
        self.orientation = "right"
        self.message = None

    async def update_message(self, interaction: discord.Interaction):
        board = self.game.board1 if self.player == self.game.player1 else self.game.board2
        cursor_data = (self.cursor, CURSOR_EMOJIS[self.orientation])
        board_str = self.game.placement_board_to_string(board, cursor_data=cursor_data)
        text = (f"Placing ship of size {self.ship_size}.\n"
                f"Current starting cell: {coords_to_label(*self.cursor)}\n"
                f"Orientation: {self.orientation} {CURSOR_EMOJIS[self.orientation]}\n"
                "Use arrow buttons to move, rotate to change orientation, or confirm to place the ship.\n"
                "Use the Remove button to reposition if needed.")
        embed = await create_embed("Battleship - Ship Placement", text + "\n\n" + board_str)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Up", style=discord.ButtonStyle.secondary)
    async def move_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        r, c = self.cursor
        if r > 0:
            self.cursor = (r - 1, c)
        await self.update_message(interaction)

    @discord.ui.button(label="Down", style=discord.ButtonStyle.secondary)
    async def move_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        r, c = self.cursor
        if r < 9:
            self.cursor = (r + 1, c)
        await self.update_message(interaction)

    @discord.ui.button(label="Left", style=discord.ButtonStyle.secondary)
    async def move_left(self, interaction: discord.Interaction, button: discord.ui.Button):
        r, c = self.cursor
        if c > 0:
            self.cursor = (r, c - 1)
        await self.update_message(interaction)

    @discord.ui.button(label="Right", style=discord.ButtonStyle.secondary)
    async def move_right(self, interaction: discord.Interaction, button: discord.ui.Button):
        r, c = self.cursor
        if c < 9:
            self.cursor = (r, c + 1)
        await self.update_message(interaction)

    @discord.ui.button(label="Rotate", style=discord.ButtonStyle.primary, emoji="🔄")
    async def rotate(self, interaction: discord.Interaction, button: discord.ui.Button):
        current_index = ORIENTATIONS.index(self.orientation)
        self.orientation = ORIENTATIONS[(current_index + 1) % len(ORIENTATIONS)]
        await self.update_message(interaction)

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        board = self.game.board1 if self.player == self.game.player1 else self.game.board2
        coords = self.game.can_place_ship(board, self.cursor[0], self.cursor[1], self.ship_size, self.orientation)
        if coords is None:
            await interaction.response.send_message("Invalid placement: Out of bounds or overlapping.", ephemeral=True)
            return
        self.game.place_ship(self.player, self.ship_size, coords)
        self.game.placement_ready[self.player] = True
        await interaction.response.send_message(f"Ship of size {self.ship_size} placed at {coords_to_label(*self.cursor)} facing {self.orientation}.", ephemeral=True)
        self.stop()

    @discord.ui.button(label="Remove", style=discord.ButtonStyle.danger, emoji="❌")
    async def remove(self, interaction: discord.Interaction, button: discord.ui.Button):
        removed = self.game.remove_ship(self.player, self.ship_size)
        if removed:
            self.game.placement_ready[self.player] = False
            await interaction.response.send_message(f"Ship of size {self.ship_size} removed. You may reposition it.", ephemeral=True)
        else:
            await interaction.response.send_message("No ship of that size to remove.", ephemeral=True)
        await self.update_message(interaction)

class StartGameView(discord.ui.View):
    """View with a Start button that locks in the player's board."""
    def __init__(self):
        super().__init__(timeout=300)
        self.started = False

    @discord.ui.button(label="Start", style=discord.ButtonStyle.success)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.started = True
        await interaction.response.send_message("Board locked. Waiting for other players to start...", ephemeral=True)
        self.stop()

# --- Battleship Cog ---

class Battleship(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Active games keyed by tuple(sorted(player1.id, player2.id))
        self.games = {}

    @commands.command(name="battleship")
    async def battleship(self, ctx, opponent: discord.Member):
        """Start a Battleship game with the tagged opponent."""
        await ctx.message.delete()
        if opponent == ctx.author:
            await ctx.send("You cannot play against yourself!")
            return

        game = BattleshipGame(ctx.author, opponent)
        key = tuple(sorted([ctx.author.id, opponent.id]))
        self.games[key] = game

        # For each ship size, let each player select and place their ship via DM.
        for size in game.ship_sizes:
            game.placement_ready[ctx.author] = False
            game.placement_ready[opponent] = False

            # Ship size selection:
            size_prompt = await create_embed("Battleship - Ship Size Selection", f"Select the ship size for your ship (should be {size}).")
            size_view1 = ShipSizeView()
            size_view2 = ShipSizeView()
            try:
                await ctx.author.send(embed=size_prompt, view=size_view1)
                await opponent.send(embed=size_prompt, view=size_view2)
            except Exception:
                await ctx.send("Could not send DM for ship size selection. Please ensure your DMs are open.")
                return
            await asyncio.sleep(5)
            size_p1 = size_view1.selected_size or size
            size_p2 = size_view2.selected_size or size
            size_p1 = size_p1 if size_p1 == size else size
            size_p2 = size_p2 if size_p2 == size else size

            # Interactive ship placement:
            placement_prompt = await create_embed("Battleship - Ship Placement", f"Place your ship of size {size}. Use the grid below.")
            placement_view1 = ShipPlacementGridView(game, ctx.author, size_p1)
            placement_view2 = ShipPlacementGridView(game, opponent, size_p2)
            try:
                await ctx.author.send(embed=placement_prompt, view=placement_view1)
                await opponent.send(embed=placement_prompt, view=placement_view2)
            except Exception:
                await ctx.send("Could not send DM for ship placement. Please ensure your DMs are open.")
                return
            while not (game.placement_ready[ctx.author] and game.placement_ready[opponent]):
                await asyncio.sleep(1)

        # After all ships are placed, send an embed to BATTLESHIP_CHANNEL indicating boards are locked.
        channel = self.bot.get_channel(BATTLESHIP_CHANNEL)
        board_summary_p1 = f"{ctx.author.mention}'s board is locked in."
        board_summary_p2 = f"{opponent.mention}'s board is locked in."
        summary_embed = await create_embed("Battleship - Boards Locked", board_summary_p1 + "\n" + board_summary_p2, color=discord.Color.purple())
        await channel.send(embed=summary_embed)

        # Now, send a Start button to each player to lock in their board and signal readiness.
        start_view1 = StartGameView()
        start_view2 = StartGameView()
        try:
            await ctx.author.send(embed=await create_embed("Battleship - Start", "Press Start when you are ready to begin firing."), view=start_view1)
            await opponent.send(embed=await create_embed("Battleship - Start", "Press Start when you are ready to begin firing."), view=start_view2)
        except Exception:
            await ctx.send("Could not send DM for starting the game. Please ensure your DMs are open.")
            return
        while not (start_view1.started and start_view2.started):
            await asyncio.sleep(1)

        # Transition to firing phase.
        game.phase = "firing"
        game.current_turn = ctx.author  # Let challenger start

        # Send each player their boards via DM:
        board_embed1 = await create_embed("Battleship - Your Board", game.board_to_string(game.board1))
        board_embed2 = await create_embed("Battleship - Your Board", game.board_to_string(game.board2))
        shot_embed1 = await create_embed("Battleship - Shots Taken", game.board_to_string(game.shots1))
        shot_embed2 = await create_embed("Battleship - Shots Taken", game.board_to_string(game.shots2))
        await ctx.author.send(embed=board_embed1)
        await ctx.author.send(embed=shot_embed1)
        await opponent.send(embed=board_embed2)
        await opponent.send(embed=shot_embed2)

        await ctx.send("Battleship game started! Use !fire <cell> (e.g. !fire A1) to take your turn.")

    @commands.command(name="fire")
    async def fire(self, ctx, target: str):
        """Fire at a cell (e.g. !fire A1). Command message is deleted."""
        await ctx.message.delete()
        for key, game in self.games.items():
            if ctx.author.id in key:
                if game.phase != "firing":
                    await ctx.send("The game is not in the firing phase.")
                    return
                if ctx.author != game.current_turn:
                    await ctx.send("It is not your turn.")
                    return
                result = game.fire(ctx.author, target)
                if result not in ["hit", "miss"]:
                    await ctx.send(result)
                    return
                # Update boards after the shot
                if ctx.author == game.player1:
                    board_embed = await create_embed("Battleship - Your Board", game.board_to_string(game.board1))
                    shot_embed = await create_embed("Battleship - Shots Taken", game.board_to_string(game.shots1))
                    opponent_embed = await create_embed("Battleship - Opponent Board", game.board_to_string(game.board2))
                    await game.player1.send(embed=board_embed)
                    await game.player1.send(embed=shot_embed)
                    await game.player2.send(embed=opponent_embed)
                else:
                    board_embed = await create_embed("Battleship - Your Board", game.board_to_string(game.board2))
                    shot_embed = await create_embed("Battleship - Shots Taken", game.board_to_string(game.shots2))
                    opponent_embed = await create_embed("Battleship - Opponent Board", game.board_to_string(game.board1))
                    await game.player2.send(embed=board_embed)
                    await game.player2.send(embed=shot_embed)
                    await game.player1.send(embed=opponent_embed)
                # Switch turn
                game.current_turn = game.player1 if ctx.author == game.player2 else game.player2
                # Check for win condition
                if self.check_win(game):
                    winner = ctx.author
                    loser = game.player1 if winner == game.player2 else game.player2
                    add_currency(winner.name, GAME_WIN)
                    remove_currency(loser.name, GAME_LOSE)
                    final_board1 = await create_embed("Battleship - Final Board", game.board_to_string(game.board1))
                    final_board2 = await create_embed("Battleship - Final Board", game.board_to_string(game.board2))
                    channel = self.bot.get_channel(BATTLESHIP_CHANNEL)
                    await channel.send(f"Final Boards for Battleship game between {game.player1.mention} and {game.player2.mention}:")
                    await channel.send(embed=final_board1)
                    await channel.send(embed=final_board2)
                    await ctx.send(f"{winner.mention} wins the Battleship game!")
                    del self.games[key]
                    return
                return
        await ctx.send("No active Battleship game found for you.")

    @commands.command(name="resetships")
    async def resetships(self, ctx):
        """
        Reset (remove) all your placed ships so you can reposition them.
        This command only works during the ship placement phase.
        """
        for key, game in self.games.items():
            if ctx.author.id in key and game.phase == "placement":
                removed = game.remove_all_ships(ctx.author)
                if removed:
                    game.placement_ready[ctx.author] = False
                    await ctx.send(f"{ctx.author.mention}, all your ships have been removed. Please re-place them.", delete_after=10)
                else:
                    await ctx.send(f"{ctx.author.mention}, you have no ships to remove.", delete_after=10)
                return
        await ctx.send("No active Battleship game found for you.", delete_after=10)

    def check_win(self, game: BattleshipGame):
        """Check if all ship cells of a player have been hit."""
        def all_ships_sunk(ships, board):
            for coords in ships.values():
                for r, c in coords:
                    if board[r][c] != HIT_CELL:
                        return False
            return True
        if all_ships_sunk(game.ships1, game.board2):
            return True
        if all_ships_sunk(game.ships2, game.board1):
            return True
        return False

async def setup(bot):
    await bot.add_cog(Battleship(bot))
