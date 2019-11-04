from enum import Enum
import random
import numpy as np

COLORS = ['RED', 'BLUE', 'TURQUOISE', 'YELLOW', 'BLACK']

FIRST_MOVER_TILE = 5

# map of which colors go where in tile wall
TILE_WALL_MAP = [[1, 3, 0, 4, 2], [2, 1, 3, 0, 4], [4, 2, 1, 3, 0],
                 [0, 4, 2, 1, 3], [3, 0, 4, 2, 1]]

# map of point loss for each floor position
FLOOR_MAP = [-1, -1, -2, -2, -2, -3, -3]


class Tile(object):
    def __init__(self, number, color):
        self.number = number
        self.color = color

    def __str__(self):
        if self.color < len(COLORS):
            return COLORS[self.color]
        elif self.color == FIRST_MOVER_TILE:
            return '1st'
        else:
            return ''


class Factory(object):
    def __init__(self, tiles):
        self.tiles = tiles

    def fetch(self, color):
        """
        Retrieve the colored tiles from this factory

        Returns:
            (fetched_tiles, discard_tiles) - fetched tiles are the tiles that match
            the color; discard tiles are the tiles that need to go in the center
        """
        fetched_tiles = []
        discard_tiles = []
        if any(t.color == color for t in self.tiles):
            # only perform the operation if the move is valid
            for t in self.tiles.copy():
                # copy the tiles so we can remove as we iterate
                if t.color == color:
                    fetched_tiles.append(t)
                else:
                    discard_tiles.append(t)
                self.tiles.remove(t)
        else:
            print("Invalid move.")
        return fetched_tiles, discard_tiles


class PlayerBoard(object):
    """
    An individual player's board
    """
    def __init__(self):
        self.staging_rows = [[None] * (x + 1) for x in range(0, 5)]
        self.tile_wall = [None] * 25
        self.floor = []


class AzulSimulator(object):
    """
    Simulate a game of Azul
    """
    def __init__(self, num_players=3, num_tiles=100):
        self.num_players = num_players
        self.num_tiles = num_tiles
        self.num_factories = self.num_players * 2 + 1
        self.bag = []
        self.factories = []
        self.center = []
        self.boards = []
        self.box = []

    def initialize_factories(self):
        """
        Initialize each factory from the bag
        """
        for factory in self.factories:
            for _ in range(0, 4):
                if len(self.bag) == 0:
                    # repopulate from box
                    self.bag = self.box.copy()
                    self.box = []
                factory.tiles.append(self.bag.pop())

    def reset_game(self):
        # create a bag of tiles
        self.bag = []
        tile_number = 0
        for c in range(0, len(COLORS)):
            for _ in range(0, 20):
                self.bag.append(Tile(tile_number, c))
                tile_number += 1
        # randomize the bag
        random.shuffle(self.bag)

        # initialize the factories with tiles
        self.factories = [Factory([]) for _ in range(0, self.num_factories)]
        self.initialize_factories()

        # initialize the center with the first mover tile
        self.center = [Tile(self.num_tiles, FIRST_MOVER_TILE)]

        # initialize player boards
        self.boards = [PlayerBoard() for _ in range(0, self.num_players)]
        print("GAME RESET")
        self.print_board()

    def act(self, selection, color, placement, player):
        """
        Perform a move for a given player
        selection - the location selected (1 of factories or center)
        color - the color tiles to select
        placement - where to place the tiles (staging row or floor)
        player - which player is making the move
        """
        tile_row = placement + 1
        if placement == 5:
            tile_row = "floor"
        factory_selection = selection + 1
        if selection == 5:
            factory_selection = "center"
        print("Running step with factory {}, color {}, tile row {}, player {}".
              format(factory_selection, COLORS[color], tile_row, player + 1))

        tiles = []
        if selection >= self.num_factories:
            # selected center
            if len([t for t in self.center if t.color == color]) > 0:
                for t in self.center:
                    if t.color == color or t.color == FIRST_MOVER_TILE:
                        tiles.append(t)
                        self.center.remove(t)
        else:
            f = self.factories[selection]
            tiles, discard_tiles = f.fetch(color)
            print("Fetched: {}".format([t.color for t in tiles]))
            print("Discarded: {}".format([t.color for t in discard_tiles]))

            self.center.extend(discard_tiles)
        board = self.boards[player]
        if placement < len(board.staging_rows):
            row = board.staging_rows[placement]
            if all(t == None or t.color == color for t in row):
                for i, cell in enumerate(row):
                    if cell == None:
                        tile = next((_t for _t in tiles if _t.color == color),
                                    None)
                        if tile:
                            print("Tile found: {}".format(COLORS[tile.color]))
                            row[i] = tile
                            tiles.remove(tile)
                        else:
                            print("No tiles found")
        board.floor.extend(tiles)
        self.print_board()
        reward = self.start_new_round()
        return reward

    def get_obs(self):
        """
        Render game into observable state
        """
        obs = np.zeros(shape=(self.num_tiles + 1, self.num_factories + 3 +
                              (self.num_players * 31)))
        for i, f in enumerate(self.factories):
            for t in f.tiles:
                obs[t.number][i] = float(t.color)
        for bag_tile in self.bag:
            obs[bag_tile.number][self.num_factories] = float(bag_tile.color)
        for center_tile in self.center:
            obs[center_tile.number][self.num_factories + 1] = float(
                center_tile.color)
        for box_tile in self.box:
            obs[box_tile.number][self.num_factories + 2] = float(
                box_tile.color)
        return obs

    def start_new_round(self):
        """
        Check if we need to start a new round, and if so:
            - tally up points
            - move used tiles to box
            - if bag runs out, move box tiles back to bag
        Return reward
        """
        if all(len(f.tiles) == 0
               for f in self.factories) and len(self.center) == 0:
            print("New round.")
            total_reward = 0  # for now, reward for all player success
            for board in self.boards:
                for i, sr in enumerate(board.staging_rows):
                    if all(t != None for t in sr):
                        # if the row is complete
                        for j, tile in enumerate(sr):
                            if j == 0:
                                # add the first tile to board
                                index = TILE_WALL_MAP[i].index(tile.color)
                                tile_wall_location = i * 5 + index
                                print("Tile wall location: {}".format(
                                    tile_wall_location))
                                board.tile_wall[tile_wall_location] = tile
                                #tally up score
                                horizontal_tally = 0
                                horizontal_start = tile_wall_location
                                while horizontal_start > i * 5 and board.tile_wall[
                                        horizontal_start - 1] != None:
                                    horizontal_start -= 1
                                print("Horizontal start: {}".format(
                                    horizontal_start))
                                for horizontal_tally_location in range(
                                        horizontal_start, (i + 1) * 5):
                                    print(
                                        "Horizontal tally location: {}".format(
                                            horizontal_tally_location))
                                    if board.tile_wall[
                                            horizontal_tally_location] != None:
                                        horizontal_tally += 1
                                        print("Tally: {}".format(
                                            horizontal_tally))
                                    else:
                                        break
                                total_reward += horizontal_tally
                            else:
                                # add remainder of tiles to box
                                self.box.append(tile)
                            # empty this row
                            sr[j] = None
                    else:
                        print("Incomplete row found.")
                # subtract points for floor and put 1st mover tile back
                for i in range(0, len(board.floor.copy())):
                    if i < len(FLOOR_MAP):
                        # floor values are negative
                        total_reward += FLOOR_MAP[i]
                    # remove tile from floor and add back to box, or center if 1st mover tile
                    t = board.floor.pop()
                    if t.color == FIRST_MOVER_TILE:
                        self.center.append(t)
                    else:
                        self.box.append(t)
            # repopulate all the factories
            self.initialize_factories()
            print("Reward: {}".format(total_reward))
            return total_reward
        else:
            print("Round not done yet.")
            return 0

    def game_over(self):
        for board in self.boards:
            for i in range(0, 5):
                filled_in = True
                for j in range(0, 5):
                    filled_in = (board.tile_wall[5 * i + j] != None
                                 and filled_in)
                if filled_in:
                    return True
        return False

    def print_board(self):
        print("FACTORIES")
        for i, factory in enumerate(self.factories):
            print("{}: {}".format(i + 1,
                                  ' '.join([str(t) for t in factory.tiles])))
        print("CENTER")
        print("{}".format(' '.join([str(t) for t in self.center])))

        print("BOARDS")
        for i, board in enumerate(self.boards):
            print("{}:".format(i + 1))
            for j, sr in enumerate(board.staging_rows):
                tile_wall_row = [
                    board.tile_wall[k] for k in range(j * 5, j * 5 + 5)
                ]
                print("\t{}:{}\t|\t{}".format(
                    j + 1, " ".join([str(t) for t in sr]),
                    " ".join([str(t) for t in tile_wall_row])))
            print("\tFloor:{}".format(" ".join([str(t) for t in board.floor])))
