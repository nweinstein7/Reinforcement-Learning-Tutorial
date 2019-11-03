from enum import Enum
import random
import numpy as np

COLORS = ['RED', 'BLUE', 'TURQUOISE', 'YELLOW', 'BLACK']

FIRST_MOVER_TILE = 5


class Tile(object):
    def __init__(self, number, color):
        self.number = number
        self.color = color


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
        for t in self.tiles:
            if t.color == color:
                fetched_tiles.append(t)
            else:
                discard_tiles.append(t)
            self.tiles.remove(t)
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
        for factory in self.factories:
            for _ in range(0, 4):
                factory.tiles.append(self.bag.pop())

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
        print("Running step with selection {}, color {}, placement {}".format(
            selection, COLORS[color], placement))

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
        return 0

    def get_obs(self):
        """
        Render game into observable state
        """
        obs = np.zeros(shape=(self.num_tiles + 1, self.num_factories + 2 +
                              (self.num_players * 31)))
        for i, f in enumerate(self.factories):
            for t in f.tiles:
                obs[t.number][i] = float(t.color)
        for bag_tile in self.bag:
            obs[bag_tile.number][self.num_factories] = float(bag_tile.color)
        for center_tile in self.center:
            obs[center_tile.number][self.num_factories + 1] = float(
                center_tile.color)
        return obs

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
            print("{}: {}".format(
                i + 1, ' '.join([COLORS[t.color] for t in factory.tiles])))
        print("CENTER")
        print("{}".format(' '.join(
            [COLORS[t.color] for t in self.center if t.color < len(COLORS)])))
