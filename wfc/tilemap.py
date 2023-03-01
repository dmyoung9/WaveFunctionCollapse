from __future__ import annotations

import time

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterable, List, Set, Union
    from .tile import Tile

from .cell import Cell
from .constants import FRAME_DELAY, MAP_DIMENSIONS, DIRECTIONS, DIRECTION_NAMES
from .exception import NoSolutionException
from .util import random


def compatible(tile_a, tile_b, direction):
    direction_a = direction[1]
    direction_b = DIRECTION_NAMES[(direction[0] + 2) % len(DIRECTION_NAMES)]

    edge_a = tile_a.edges[direction_a]
    edge_b = tile_b.edges[direction_b][::-1]
    return edge_a == edge_b


class TileMap:
    def __init__(self, width: int, height: int, tiles: Iterable[Tile]):
        self.width = width
        self.height = height
        self.tiles = set(tiles)
        self.cells = self._init_cells(self.width, self.height, self.tiles)
        self.rules = self._build_rules(self.tiles)

    def _init_cells(
        self, width: int, height: int, tiles: Set[Tile]
    ) -> List[List[Cell]]:
        cells = []
        for y in range(height):
            row = [Cell(x, y, tiles) for x in range(width)]
            cells.append(row)
        return cells

    def _build_rules(self, tiles: Set[Tile]):
        rules = {tile.id: {k: set() for k in DIRECTION_NAMES} for tile in tiles}

        for _tile in tiles:
            for tile in tiles:
                for idx, d in enumerate(DIRECTION_NAMES):
                    if compatible(_tile, tile, (idx, d)):
                        rules[_tile.id][d].add(tile)

        return rules

    def _get_cells_with_minimum_entropy(
        self, cells: Union[List[Cell], None] = None
    ) -> Set[Cell]:
        all_cells = [cell for row in cells or self.cells for cell in row]
        uncollapsed_cells = [cell for cell in all_cells if not cell.collapsed]
        if not uncollapsed_cells:
            return []

        min_entropy = min(cell.entropy for cell in uncollapsed_cells)
        return {cell for cell in uncollapsed_cells if cell.entropy == min_entropy}

    def _get_neighbors(self, cell: Cell) -> List[Cell]:
        neighbors = set()

        for _, offset in DIRECTIONS.items():
            dx, dy = offset

            if 0 <= cell.x + dx < MAP_DIMENSIONS[0]:
                neighbors.add(self.cells[(cell.y)][cell.x + dx])
            if 0 <= cell.y + dy < MAP_DIMENSIONS[1]:
                neighbors.add(self.cells[(cell.y + dy)][cell.x])

        return neighbors

    def _get_uncollapsed_neighbors(self, cell: Cell) -> Set[Cell]:
        return {
            neighbor for neighbor in self._get_neighbors(cell) if not neighbor.collapsed
        }

    def _get_collapsed_neighbors(self, cell: Cell) -> Set[Cell]:
        return {
            neighbor for neighbor in self._get_neighbors(cell) if neighbor.collapsed
        }

    def _observe_random_cell(
        self, cells: Union[Set[Cell], None] = None, backtrack: bool = False
    ) -> Cell:
        cell = random().choice(tuple(cells or self._get_cells_with_minimum_entropy()))
        cell.collapse(self.tiles if backtrack else None)
        return cell

    def _propagate(self, collapsed_cell: Cell):
        faces = (
            ((0, -1), "south"),
            ((1, 0), "west"),
            ((0, 1), "north"),
            ((-1, 0), "east"),
        )

        uncollapsed_neighbors = self._get_uncollapsed_neighbors(collapsed_cell)
        for uncollapsed_neighbor in uncollapsed_neighbors:
            collapsed_neighbors = self._get_collapsed_neighbors(uncollapsed_neighbor)
            for collapsed_neighbor in collapsed_neighbors:
                tile = collapsed_neighbor.get_tile()
                for idx, direction in enumerate(DIRECTION_NAMES):
                    dx, dy = DIRECTIONS[direction]

                    if (collapsed_neighbor.x, collapsed_neighbor.y) == (
                        uncollapsed_neighbor.x + dx,
                        uncollapsed_neighbor.y + dy,
                    ):
                        direction = DIRECTION_NAMES[(idx + 2) % len(DIRECTION_NAMES)]
                        uncollapsed_neighbor.options = (
                            uncollapsed_neighbor.options
                            & set(self.rules[tile.id][direction])
                        )

            if not len(uncollapsed_neighbor.options):
                raise NoSolutionException(uncollapsed_neighbor)

    def print_map(self):
        print("\033[2J\033[H", end="")
        print("\033[1;0H", end="")
        print("-" * MAP_DIMENSIONS[0])
        for y, row in enumerate(self.cells):
            for x, column in enumerate(row):
                print(f"\033[{y+2};{x+1}H", end="")
                cell = self.cells[y][x]
                if cell.collapsed:
                    print(cell.get_tile().id, end="")
                    continue
                print("?", end="")
        print(f"\033[{MAP_DIMENSIONS[1]+2};0H", end="")
        print("-" * MAP_DIMENSIONS[0])


def generate_tilemap(width: int, height: int, tiles: Set[Tile]):
    # initialize a new tilemap and clear screen
    tilemap = TileMap(width, height, tiles)
    print("\033[2J", end="")

    while cells := tilemap._get_cells_with_minimum_entropy():
        # observe one of the least entropic cells
        collapsed_cell = tilemap._observe_random_cell(cells)
        try:
            tilemap._propagate(collapsed_cell)
        except NoSolutionException as nse:
            # failure state
            all_cells = [cell for row in tilemap.cells for cell in row]
            tilemap.print_map()
            print(nse)
            print(
                f"{len([i for i in all_cells if not i.collapsed])}/{len(all_cells)} cells not collapsed."
            )
            break
        else:
            tilemap.print_map()

        time.sleep(FRAME_DELAY)
