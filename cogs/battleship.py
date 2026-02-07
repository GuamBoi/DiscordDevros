import discord
from discord.ext import commands
import asyncio
import re

from utils.embed import create_embed
from utils.economy import add_currency, remove_currency, load_economy, save_economy, user_key
from config import GAME_WIN, GAME_LOSE, BATTLESHIP_CHANNEL, CURRENCY_SYMBOL


def _user_key(member: discord.Member) -> str:
    return user_key(member)


def increment_battleship_streak(member: discord.Member) -> int:
    """+1 the member's battleship win streak; returns new streak."""
    key = _user_key(member)
    data = load_economy(key)
    data["battleship_streak"] = data.get("battleship_streak", 0) + 1
    save_economy(key, data)
    return data["battleship_streak"]


def reset_battleship_streak(member: discord.Member) -> None:
    """Reset the member's battleship win streak to 0."""
    key = _user_key(member)
    data = load_economy(key)
    data["battleship_streak"] = 0
    save_economy(key, data)


# --- Constants & Helper Functions ---

EMPTY_CELL = ":white_large_square:"       # Open ocean
SHIP_CELL = ":green_square:"              # Placed ship cell during placement
HIT_CELL = ":red_square:"                 # Ship hit
MISS_CELL = ":blue_square:"               # Miss – also used for header alignment

# Arrow emojis used as cursor; also indicate orientation.
CURSOR_EMOJIS = {
    "left": "⏪",
    "up": "⏫",
    "right": "⏩",
    "down": "⏬"
}

# Valid orientations in order.
ORIENTATIONS = ["right", "down", "left", "up"]

# Grid labels for a 10x10 board.
ROWS = list("ABCDEFGHIJ")
COLUMNS = [str(i) for i in range(1, 11)]

# Emoji mappings for letters and numbers.
LETTER_EMOJIS = {
    "A": "🇦", "B": "🇧", "C": "🇨", "D": "🇩", "E": "🇪",
    "F": "🇫", "G": "🇬", "H": "🇭", "I": "🇮", "J": "🇯"
}

# Fix: correct 1-10 mapping (your pasted code had an 8 twice)
NUMBER_EMOJIS = {
    "1": "1️⃣", "2": "2️⃣", "3": "3️⃣", "4": "4️⃣", "5": "5️⃣",
    "6": "6️⃣", "7": "7️⃣", "8": "8️⃣", "9": "9️⃣", "10": "🔟"
}

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
        # Ships placed: dictionary mapping ship size to list(s) of coordinates.
        self.ships1 = {}
        self.ships2 = {}
        # Each player must place ships according to these requirements.
        self.ship_requirements = {2: 1, 3: 2, 4: 1, 5: 1}
        # Ready flags for each player's placement phase.
        self.placement_ready = {self.player1: False, self.player2: False}
        self.phase = "placement"  # or "firing"
        self.current_turn = None  # For firing phase
        self.prompt_message = None  # Persistent turn prompt message in BATTLESHIP_CHANNEL
        # Track sunk ships so they are announced only once.
        self.sunk_ships = {self.player1: [], self.player2: []}

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
            self.ships1.setdefault(ship_size, []).append(coords)
        else:
            board = self.board2
            self.ships2.setdefault(ship_size, []).append(coords)
        for r, c in coords:
            board[r][c] = SHIP_CELL

    def remove_ship(self, player: discord.Member, ship_size: int):
        """Remove one placed ship of the given size from the player's board."""
        if player == self.player1 and ship_size in self.ships1 and self.ships1[ship_size]:
            coords = self.ships1[ship_size].pop()
            board = self.board1
        elif player == self.player2 and ship_size in self.ships2 and self.ships2[ship_size]:
            coords = self.ships2[ship_size].pop()
            board = self.board2
        else:
            return False
        for r, c in coords:
            board[r][c] = EMPTY_CELL
        return True

    def remove_all_ships(self, player: discord.Member):
        """Remove all ships for the given player."""
        removed_any = False
        for size in self.ship_requirements:
            while self.remove_ship(player, size):
                removed_any = True
        return removed_any

    def board_to_string(self, board):
        """Return a string representation of a board with emoji labels."""
        header = "🟦 " + " ".join(NUMBER_EMOJIS[c] for c in COLUMNS) + "\n"
        s = header
        for i, row in enumerate(board):
            s += LETTER_EMOJIS[ROWS[i]] + "  " + " ".join(row) + "\n"
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
        header = "🟦 " + " ".join(NUMBER_EMOJIS[c] for c in COLUMNS) + "\n"
        s = header
        for i, row in enumerate(display):
            s += LETTER_EMOJIS[ROWS[i]] + "  " + " ".join(row) + "\n"
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
        for ship_coords_list in ships.values():
            for coords in ship_coords_list:
                if (row, col) in coords:
                    hit = True
                    opp_board[row][col] = HIT_CELL
                    shot_board[row][col] = HIT_CELL
                    break
            if hit:
                break

        if not hit:
            opp_board[row][col] = MISS_CELL
            shot_board[row][col] = MISS_CELL

        return "hit" if hit else "miss"


# --- Persistent Turn Prompt Function ---

async def update_turn_prompt(game: BattleshipGame, bot: discord.Client):
    # Determine active player and their shot board
    if game.current_turn == game.player1:
        shot_board = game.shots1
        active = game.player1
    else:
        shot_board = game.shots2
        active = game.player2

    prompt_text = (
        f"{active.mention}, it's your turn! Use `!fire <cell>` to take your shot.\n\n"
        f"Your guessed board:\n{game.board_to_string(shot_board)}"
    )
    embed = await create_embed("Battleship - Turn Prompt", prompt_text)
    channel = bot.get_channel(BATTLESHIP_CHANNEL)
    if game.prompt_message is None:
        game.prompt_message = await channel.send(embed=embed)
    else:
        await game.prompt_message.edit(embed=embed)


# --- Persistent Ship Placement UI ---

class ShipSizeSelect(discord.ui.Select):
    def __init__(self, placed_ships, requirements):
        options = []
        for size in sorted(requirements.keys()):
            count = placed_ships[size]
            req = requirements[size]
            label = f"Ship Size {size} ({count}/{req} placed)"
            options.append(discord.SelectOption(label=label, value=str(size)))
        super().__init__(placeholder="Select a ship to place or remove", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        view: "PersistentShipPlacementView" = self.view
        size = int(self.values[0])

        if view.placed_ships[size] >= view.game.ship_requirements[size]:
            await interaction.response.send_message(
                f"All required ships of size {size} are already placed. Use the Remove button to reposition one.",
                ephemeral=True
            )
            return

        view.current_ship_size = size
        await interaction.response.defer(ephemeral=True)
        await view.update_message(interaction)


class FinishBattlefieldButton(discord.ui.Button):
    def __init__(self, parent_view: "PersistentShipPlacementView"):
        super().__init__(label="Finish Battlefield", style=discord.ButtonStyle.success)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        for size, req in self.parent_view.game.ship_requirements.items():
            if self.parent_view.placed_ships[size] < req:
                await interaction.response.send_message(
                    f"You must place {req} ship(s) of size {size}.",
                    ephemeral=True
                )
                return

        self.parent_view.game.placement_ready[self.parent_view.player] = True
        channel = self.parent_view.bot.get_channel(BATTLESHIP_CHANNEL)

        finish_embed = await create_embed(
            "Battleship - Ship Placement Complete",
            f"{interaction.user.mention} has finished placing their ships and is waiting on the other player.",
            color=discord.Color.blue()
        )
        await channel.send(embed=finish_embed)

        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "Finished placing ships. Waiting for the other player...",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "Finished placing ships. Waiting for the other player...",
                    ephemeral=True
                )
        except Exception:
            pass

        self.parent_view.stop()


class PersistentShipPlacementView(discord.ui.View):
    def __init__(self, game: BattleshipGame, player: discord.Member):
        super().__init__(timeout=300)
        self.game = game
        self.player = player
        self.bot = game.player1.guild if hasattr(game.player1, "guild") else None
        self.cursor = (0, 0)
        self.orientation = "right"
        self.placed_ships = {size: 0 for size in game.ship_requirements}
        self.current_ship_size = None
        self.add_item(ShipSizeSelect(self.placed_ships, game.ship_requirements))
        self.add_item(FinishBattlefieldButton(self))

    async def update_select_menu(self):
        for child in self.children:
            if isinstance(child, ShipSizeSelect):
                new_options = []
                for size, req in self.game.ship_requirements.items():
                    count = self.placed_ships[size]
                    label = f"Ship Size {size} ({count}/{req} placed)"
                    new_options.append(discord.SelectOption(label=label, value=str(size)))
                child.options = new_options

    async def update_message(self, interaction: discord.Interaction):
        board = self.game.board1 if self.player == self.game.player1 else self.game.board2
        cursor_data = (self.cursor, CURSOR_EMOJIS[self.orientation])
        board_str = self.game.placement_board_to_string(board, cursor_data=cursor_data)

        if self.current_ship_size:
            header = f"Placing ship of size {self.current_ship_size}.\n"
        else:
            header = "Select a ship size to place or remove from the dropdown below.\n"

        text = (
            header +
            f"Current starting cell: {coords_to_label(*self.cursor)}\n"
            "Use arrow buttons to move, rotate to change orientation, or press Place Ship to place your ship.\n"
            "Use the Remove button to reposition if needed.\n\n" +
            board_str
        )
        embed = await create_embed("Battleship - Ship Placement", text)

        try:
            if not interaction.response.is_done():
                await interaction.response.edit_message(embed=embed, view=self)
            else:
                await interaction.followup.edit_message(
                    message_id=interaction.message.id,
                    embed=embed,
                    view=self
                )
        except Exception as e:
            print(e)

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

    @discord.ui.button(label="Place Ship", style=discord.ButtonStyle.success, emoji="✅")
    async def place_ship(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_ship_size is None:
            await interaction.response.send_message("Please select a ship size first.", ephemeral=True)
            return

        if self.placed_ships[self.current_ship_size] >= self.game.ship_requirements[self.current_ship_size]:
            await interaction.response.send_message(
                f"All required ships of size {self.current_ship_size} are already placed.",
                ephemeral=True
            )
            return

        board = self.game.board1 if self.player == self.game.player1 else self.game.board2
        coords = self.game.can_place_ship(board, self.cursor[0], self.cursor[1], self.current_ship_size, self.orientation)
        if coords is None:
            await interaction.response.send_message("Invalid placement: Out of bounds or overlapping.", ephemeral=True)
            return

        self.game.place_ship(self.player, self.current_ship_size, coords)
        self.placed_ships[self.current_ship_size] += 1
        self.current_ship_size = None
        await self.update_select_menu()
        await self.update_message(interaction)

    @discord.ui.button(label="Remove", style=discord.ButtonStyle.danger, emoji="❌")
    async def remove(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_ship_size is None:
            await interaction.response.send_message("Select the ship size you want to remove.", ephemeral=True)
            return

        if self.placed_ships[self.current_ship_size] <= 0:
            await interaction.response.send_message(
                f"No ship of size {self.current_ship_size} is placed.",
                ephemeral=True
            )
            return

        removed = self.game.remove_ship(self.player, self.current_ship_size)
        if removed:
            self.placed_ships[self.current_ship_size] -= 1
            await interaction.response.send_message(
                f"One ship of size {self.current_ship_size} removed.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message("Failed to remove ship.", ephemeral=True)

        self.current_ship_size = None
        await self.update_select_menu()
        await self.update_message(interaction)


# --- Battleship Cog ---

class Battleship(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}  # Active games keyed by tuple(sorted(player1.id, player2.id))

    @commands.command(name="battleship")
    async def battleship(self, ctx, opponent: discord.Member):
        """Start a Battleship game with the tagged opponent."""
        await ctx.message.delete()

        if opponent == ctx.author:
            await ctx.send("You cannot play against yourself!")
            return

        game = BattleshipGame(ctx.author, opponent)
        game_key = tuple(sorted([ctx.author.id, opponent.id]))
        self.games[game_key] = game

        # Send one persistent ship placement DM to each player.
        try:
            placement_embed = await create_embed(
                "Battleship - Ship Placement",
                "Select a ship size to place or remove from the dropdown below."
            )
            view1 = PersistentShipPlacementView(game, ctx.author)
            view2 = PersistentShipPlacementView(game, opponent)
            await ctx.author.send(embed=placement_embed, view=view1)
            await opponent.send(embed=placement_embed, view=view2)
        except Exception:
            await ctx.send("Could not send DM for ship placement. Please ensure your DMs are open.")
            return

        # Wait until both players have finished placing all ships.
        while not (game.placement_ready[ctx.author] and game.placement_ready[opponent]):
            await asyncio.sleep(1)

        # Transition to firing phase in the battleship channel.
        game.phase = "firing"

        # CHANGE: tagged opponent goes first
        game.current_turn = opponent

        # Send each player their boards via DM.
        board_embed1 = await create_embed("Battleship - Your Board", game.board_to_string(game.board1))
        board_embed2 = await create_embed("Battleship - Your Board", game.board_to_string(game.board2))
        await ctx.author.send(embed=board_embed1)
        await opponent.send(embed=board_embed2)

        # Create the persistent turn prompt in BATTLESHIP_CHANNEL.
        await update_turn_prompt(game, self.bot)

    @commands.command(name="fire")
    async def fire(self, ctx, target: str):
        """Fire at a cell (e.g. !fire A1). Command message is deleted."""
        await ctx.message.delete()

        for game_key, game in list(self.games.items()):
            if ctx.author.id not in game_key:
                continue

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

            # If the shot was a hit, check if any ship was sunk.
            if result == "hit":
                opponent = game.player2 if ctx.author == game.player1 else game.player1
                opp_board = game.board2 if ctx.author == game.player1 else game.board1
                opponent_ships = game.ships2 if ctx.author == game.player1 else game.ships1
                sunk_list = game.sunk_ships[opponent]

                for size, ships in opponent_ships.items():
                    for ship in ships:
                        if ship not in sunk_list and all(opp_board[r][c] == HIT_CELL for r, c in ship):
                            sunk_list.append(ship)
                            embed = await create_embed(
                                "Battleship - Ship Sunk",
                                f"{ctx.author.mention} has sunk {opponent.mention}'s ship of size {size}!",
                                color=discord.Color.red()
                            )
                            channel = self.bot.get_channel(BATTLESHIP_CHANNEL)
                            await channel.send(embed=embed, delete_after=60)

            # Check for win condition.
            winner = self.check_win(game)
            if winner:
                loser = game.player1 if winner == game.player2 else game.player2

                add_currency(_user_key(winner), GAME_WIN)
                remove_currency(_user_key(loser), GAME_LOSE)

                increment_battleship_streak(winner)
                reset_battleship_streak(loser)

                channel = self.bot.get_channel(BATTLESHIP_CHANNEL)
                await channel.send(
                    f"Final Boards for Battleship game between {game.player1.mention} and {game.player2.mention}:"
                )

                final_board1 = await create_embed("Battleship - Final Board", game.board_to_string(game.board1))
                final_board2 = await create_embed("Battleship - Final Board", game.board_to_string(game.board2))
                await channel.send(embed=final_board1)
                await channel.send(embed=final_board2)

                description_text = (
                    f"{winner.mention} beat {loser.mention} in Battleship!\n\n"
                    f"**{winner.display_name}** won {CURRENCY_SYMBOL}{GAME_WIN}\n"
                    f"**{loser.display_name}** lost {CURRENCY_SYMBOL}{GAME_LOSE}\n\n"
                    "Thanks for playing!"
                )
                final_embed = await create_embed("Battleship - Game Over", description_text, color=discord.Color.blue())
                await channel.send(embed=final_embed)

                del self.games[game_key]
                return

            # If miss, switch turn; if hit, same player continues
            if result == "miss":
                game.current_turn = game.player1 if ctx.author == game.player2 else game.player2

            await update_turn_prompt(game, self.bot)
            return

        await ctx.send("No active Battleship game found for you.")

    @commands.command(name="resetships")
    async def resetships(self, ctx):
        """
        Reset (remove) all your placed ships so you can reposition them.
        This command only works during the ship placement phase.
        """
        for game_key, game in self.games.items():
            if ctx.author.id in game_key and game.phase == "placement":
                removed = game.remove_all_ships(ctx.author)
                if removed:
                    game.placement_ready[ctx.author] = False
                    await ctx.send(
                        f"{ctx.author.mention}, all your ships have been removed. Please re-place them.",
                        delete_after=10
                    )
                else:
                    await ctx.send(
                        f"{ctx.author.mention}, you have no ships to remove.",
                        delete_after=10
                    )
                return
        await ctx.send("No active Battleship game found for you.", delete_after=10)

    def check_win(self, game: BattleshipGame):
        """
        Check if a player has lost all their ships.
        Returns the winning player if so, otherwise None.
        """
        def all_ships_sunk(ships, board):
            for ship_coords_list in ships.values():
                for coords in ship_coords_list:
                    for r, c in coords:
                        if board[r][c] != HIT_CELL:
                            return False
            return True

        if all_ships_sunk(game.ships1, game.board1):
            return game.player2
        if all_ships_sunk(game.ships2, game.board2):
            return game.player1
        return None


async def setup(bot):
    await bot.add_cog(Battleship(bot))
