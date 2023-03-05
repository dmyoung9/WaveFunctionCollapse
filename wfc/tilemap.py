from __future__ import annotations

import os
import time

from typing import TYPE_CHECKING

import tkinter as tk
from PIL import Image

if TYPE_CHECKING:
    from typing import List, Set, Union
    from .tile import Tile
    from .tileset import TileSet

from .cell import Cell
from .constants import FRAME_DELAY, DIRECTIONS, DIRECTION_NAMES
from .exception import NoSolutionException
from .util import random


class TileMap:
    def __init__(self, width: int, height: int, tileset: TileSet):
        self.width = width
        self.height = height
        self.tileset_name = tileset.name
        self.tile_width = tileset.tile_width
        self.tile_height = tileset.tile_height
        self.tileset = tileset
        self.initialize()

    def initialize(self):
        self.contradictions = 0
        self.stack = []
        self.history = {}
        self.cells = TileMap.build_cells(self.width, self.height, self.tileset.tiles)

    @staticmethod
    def build_cells(width: int, height: int, tiles: Set[Tile]) -> List[List[Cell]]:
        cells = []
        for y in range(height):
            row = [Cell(x, y, tiles) for x in range(width)]
            cells.append(row)

        return cells

    def _get_all_cells(self) -> Set[Cell]:
        return {cell for row in self.cells for cell in row}

    def _get_minimum_entropy_cells(self) -> Set[Cell]:
        all_cells = self._get_all_cells()
        uncollapsed_cells = [cell for cell in all_cells if not cell.collapsed]
        if not uncollapsed_cells:
            return []

        min_entropy = min(cell.entropy for cell in uncollapsed_cells)
        return {cell for cell in uncollapsed_cells if cell.entropy == min_entropy}

    def _get_neighbors(self, cell: Cell) -> List[Cell]:
        neighbors = set()

        for _, offset in DIRECTIONS.items():
            dx, dy = offset

            neighbors.add(self.cells[cell.y][(cell.x + dx) % self.width])
            neighbors.add(self.cells[(cell.y + dy) % self.height][cell.x])

        return neighbors

    def _get_uncollapsed_neighbors(self, cell: Cell) -> Set[Cell]:
        return {
            neighbor
            for neighbor in self._get_neighbors(cell)
            if neighbor.collapsed == False
        }

    def _get_collapsed_neighbors(self, cell: Cell) -> Set[Cell]:
        return {
            neighbor
            for neighbor in self._get_neighbors(cell)
            if neighbor.collapsed == True
        }

    def _get_invalid_neighbors(self, cell: Cell) -> Set[Cell]:
        return {
            neighbor
            for neighbor in self._get_neighbors(cell)
            if neighbor.collapsed is None
        }

    def _observe_random_cell(self, cells: Union[Set[Cell], None] = None) -> Cell:
        if cells is None:
            cells = self._get_minimum_entropy_cells()

        if not cells:
            return None

        cell = random().choice(tuple(cells))
        try:
            options = cell.options.copy()
            cell.collapse()
            self._propagate(cell)
        except NoSolutionException as nse:
            self.contradictions += 1

            self._backtrack(cell)
        else:
            self.stack.append(cell)
            self.history[cell] = options

        return cell

    def _propagate(self, collapsed_cell: Cell):
        uncollapsed_neighbors = self._get_uncollapsed_neighbors(collapsed_cell)
        for uncollapsed_neighbor in uncollapsed_neighbors:
            collapsed_neighbors = self._get_collapsed_neighbors(uncollapsed_neighbor)
            for collapsed_neighbor in collapsed_neighbors:
                tile = collapsed_neighbor.get_tile()
                for idx, direction in enumerate(DIRECTION_NAMES):
                    dx, dy = DIRECTIONS[direction]

                    if (collapsed_neighbor.x, collapsed_neighbor.y) == (
                        (uncollapsed_neighbor.x + dx) % self.width,
                        (uncollapsed_neighbor.y + dy) % self.height,
                    ):
                        direction = DIRECTION_NAMES[(idx + 2) % len(DIRECTION_NAMES)]
                        options = uncollapsed_neighbor.options.copy()
                        uncollapsed_neighbor.options = (
                            uncollapsed_neighbor.options
                            & set(self.tileset.rules[tile.id][direction])
                        )

                        if uncollapsed_neighbor.entropy == 1:
                            self.stack.append(uncollapsed_neighbor)
                            self.history[uncollapsed_neighbor] = options

    def _collapse(self, cells: Union[Set[Cell], None] = None):
        return self._observe_random_cell(cells) is None

    def _backtrack(self, prev: Cell):
        while self.stack:
            backtrack_cell = self.stack.pop()
            if backtrack_cell == prev:
                break

            backtrack_cell.options = (
                self.history.pop(backtrack_cell, self.tileset.tiles) & backtrack_cell.options
            )

            neighbors = self._get_neighbors(backtrack_cell)
            for neighbor in neighbors:
                neighbor.options = self.tileset.tiles
                if neighbor in self.stack:
                    self.stack.remove(neighbor)

            self._propagate(backtrack_cell)

            if self.contradictions > len(self.stack):
                break

            return False

        self.initialize()

        return True

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
