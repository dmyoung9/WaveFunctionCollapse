from __future__ import annotations

import os
import time

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Generator, Optional, Set

    from .tile import Tile
    from .tileset import TileSet

from PIL import Image

from .cell import Cell
from .constants import DIRECTIONS
from .util import random


def _build_cells(
    width: int, height: int, tiles: Set[Tile], seamless: bool = False
) -> Set[Cell]:
    """Builds a `width`x`height` two-dimensional array of `Cell` objects with maximum entropy.

    :param width: The width for the array of cells
    :ptype width: `int`
    :param height: The height for the array of cells
    :ptype height: `int`
    :param tiles: All possible `Tile`s that should be used
    :ptype tiles: `Set[Tile]`
    :param seamless: Whether to consider neighbors seamlessly along map borders
    :ptype seamless: `bool`
    :return: Set of `Cell`s in completely unobserved state
    :rtype: `Set[Cell]`
    """
    cells = []

    for y in range(height):
        row = [Cell(x, y, tiles) for x in range(width)]
        cells.append(row)

    cell_set = set()

    for cell in [cell for row in cells for cell in row]:
        for direction, offset in DIRECTIONS.items():
            dx, dy = offset

            if ((0 <= cell.x + dx < width) and (0 <= cell.y + dy < height)) or seamless:
                x = (cell.x + dx) % width if seamless else (cell.x + dx)
                y = (cell.y + dy) % height if seamless else (cell.y + dy)
                cell.neighbors[direction] = cells[y][x]

        cell_set.add(cell)

    return cell_set


class TileMap:
    """Implements the 'Wave Function Collapse' algorithm in the context of
    generating 2d tilemaps.
    """

    def __init__(self, width: int, height: int, tileset: TileSet):
        """Constructs a new `TileMap` with the given properties.

        :param width: Number of tiles wide this tilemap should be
        :type width: int
        :param height: Number of tiles tall this tilemap should be
        :type height: int
        :param tileset: A `TileSet` instance to be used for this tilemap
        :type tileset: `TileSet`
        """

        self.width = width
        self.height = height
        self.tileset_name = tileset.name
        self.tile_width = tileset.tile_width
        self.tile_height = tileset.tile_height
        self.tileset = tileset

        self.cells = None
        self.generator = None
        self.initialize()

    def initialize(
        self,
        width: Optional[int] = None,
        height: Optional[int] = None,
        tiles: Optional[Set[Tile]] = None,
    ) -> None:
        """Initializes this `TileMap` to a fully unobserved state.

        :param width: Optional value to change the width of this tilemap
        :ptype width: `Optional[int]`
        :param width: Optional value to change the height of this tilemap
        :ptype width: `Optional[int]`
        :param tiles: Optional value to change the tileset used for this tilemap
        :ptype tiles: `Optional[Set[Tile]]`
        """
        self.cells = _build_cells(
            width or self.width, height or self.height, tiles or self.tileset.tiles
        )
        self.generator = self.generate()

    def _finished(self) -> bool:
        return (
            len({cell for cell in self.cells if cell.collapsed is True})
            == self.width * self.height
        )

    def _get_uncollapsed_cells(self) -> Set[Cell]:
        """Returns all cells that are uncollapsed.

        :return: Set of uncollapsed cells
        :rtype: `Set[Cell]`
        """
        return {cell for cell in self.cells if cell.collapsed is False}

    def _get_invalid_cells(self):
        """Returns all cells that are invalid.

        :return: Set of invalid cells
        :rtype: `Set[Cell]`
        """
        return {cell for cell in self.cells if cell.collapsed is None}

    def _get_minimum_entropy_cells(self, cells: Set[Cell]) -> Set[Cell]:
        """Returns all cells that have the least entropy (greater than 1).

        :return: Set of cells
        :rtype: `Set[Cell]`
        """
        if not (min_cells := [cell.entropy for cell in cells if cell.entropy > 1]):
            return set()

        minimum_entropy = min(min_cells)
        return {cell for cell in cells if cell.entropy == minimum_entropy}

    def _get_random_cell(self, cells: Set[Cell]) -> Optional[Cell]:
        """Returns a random cell with the lowest entropy from the tilemap.

        :param cells: Optional set of `Cell`s to override the pool of options
        :ptype cells: `Optional[Set[Cell]]`
        :return: A random `Cell` with lowest entropy from the pool of given cells,
        or `None` if all given cells are either invalid or already collapsed.
        :rtype: `Optional[Cell]`
        """

        return random().choice(tuple(cells)) if cells else None

    def get_tilemap_generator(self) -> Generator[Set[Cell]]:
        """Get the generator for this tilemap.

        :return: A generator which incrementally yields the state of this tilemap
        :rtype: `Generator[Set[Cell]]`
        """
        return self.generator or self.generate()

    def generate(self) -> Generator[Set[Cell]]:
        """Yields the set of modified `Cell`s in this tilemap after every generation.

        :return: Generator that yields set of modified cells
        :rtype: `Generator[Set[Cell]]`
        """
        yield self.cells

        while not self._finished():
            affected_cells = set()

            if invalid_cells := self._get_invalid_cells():
                invalid_cell = self._get_random_cell(invalid_cells)
                affected_cells.add(invalid_cell)
                backtracked_cells = self.backtrack(invalid_cell)
                yield affected_cells.union(backtracked_cells)

            if uncollapsed_cells := self._get_uncollapsed_cells():
                minimum_cells = self._get_minimum_entropy_cells(uncollapsed_cells)
                cell = self._get_random_cell(minimum_cells)
                cell.collapse()
                propagated_cells = self.propagate(cell)
                affected_cells.add(cell)
                minimum_cells = self._get_minimum_entropy_cells(self.cells)
                yield affected_cells.union(propagated_cells, minimum_cells)

            if invalid_cells and not uncollapsed_cells:
                break

        yield self.cells

    def propagate(self, changed_cell: Cell) -> Set[Cell]:
        """Reduces the options of neighboring cells to `changed_cell`. Returns any
        cells whose options were changed. Recursively propagates cells which are
        collapsed by another cell's propagation.

        :param changed_cell: The cell which was changed to trigger this propagation
        :ptype changed_cell: `Cell`
        :return: Cells whose options changed
        :rtype: `Set[Cell]`
        """
        affected_cells = set()

        for direction, neighbor in changed_cell.get_neighbors().items():
            if neighbor is None:
                continue

            options = neighbor.options.copy()
            if neighbor.collapsed is False and changed_cell.collapsed:
                tile = changed_cell.get_tile()
                neighbor.options = neighbor.options & tile.get_compatible_tiles(
                    direction
                )

            if neighbor.options != options:
                affected_cells.add(neighbor)
                if neighbor.collapsed:
                    propagated_cells = self.propagate(neighbor)
                    affected_cells = affected_cells.union(propagated_cells)

        return affected_cells

    def backtrack(self, start_cell: Cell):
        """Backtracks recursively from `start_cell`, resetting options until
        a valid state can be achieved.

        :param start_cell: The `Cell` from which to start backtracking
        :ptype start_cell: `Cell`
        :return: All cells reset during the backtracking process
        :rtype: `Set[Cell]`
        """
        # TODO: Implement this method.
        pass

    def draw_map(self):
        background = Image.new(
            "RGBA",
            (self.width * self.tile_width, self.height * self.tile_height),
            (255, 255, 255, 255),
        )

        for cell in [cell for row in self.cells for cell in row]:
            if not cell.collapsed:
                continue

            img = Image.open(cell.get_tile().img)
            background.paste(
                img,
                (cell.x * self.tile_width, cell.y * self.tile_height),
            )

        filename = f"{self.tileset_name}-{self.width}x{self.height}-{time.time()}.png"
        os.makedirs(os.path.join(os.getcwd(), "output"), exist_ok=True)
        background.save(os.path.join(os.getcwd(), "output", filename))
