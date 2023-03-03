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


def compatible(tile_a, tile_b, direction):
    direction_a = direction[1]
    direction_b = DIRECTION_NAMES[(direction[0] + 2) % len(DIRECTION_NAMES)]

    edge_a = tile_a.edges[direction_a]
    edge_b = tile_b.edges[direction_b][::-1]
    return edge_a == edge_b


class TileMap:
    def __init__(self, width: int, height: int, tileset: TileSet):
        self.width = width
        self.height = height
        self.tileset_name = tileset.name
        self.tile_width = tileset.tile_width
        self.tile_height = tileset.tile_height
        self.tiles = tileset.tiles
        self.tk_images = {}
        self.cells = self.init_cells(self.width, self.height, self.tiles)
        self.rules = TileMap.build_rules(self.tiles)
        self.contradictions = 0
        self.stack = []
        self.history = {}

    def init_cells(self, width: int, height: int, tiles: Set[Tile]) -> List[List[Cell]]:
        cells = []
        for y in range(height):
            row = [Cell(x, y, tiles) for x in range(width)]
            cells.append(row)

        self.stack = []
        return cells

    @staticmethod
    def build_rules(tiles: Set[Tile]):
        rules = {tile.id: {k: set() for k in DIRECTION_NAMES} for tile in tiles}

        for _tile in tiles:
            for tile in tiles:
                if _tile.id == 0 and tile.id == 8:
                    print()
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

            neighbors.add(self.cells[cell.y][(cell.x + dx) % self.width])
            neighbors.add(self.cells[(cell.y + dy) % self.height][cell.x])

        return neighbors

    def _get_uncollapsed_neighbors(self, cell: Cell) -> Set[Cell]:
        return {
            neighbor for neighbor in self._get_neighbors(cell) if not neighbor.collapsed
        }

    def _get_collapsed_neighbors(self, cell: Cell) -> Set[Cell]:
        return {
            neighbor for neighbor in self._get_neighbors(cell) if neighbor.collapsed
        }

    def _observe_random_cell(self, cells: Union[Set[Cell], None] = None) -> Cell:
        if cells is None:
            cells = self._get_cells_with_minimum_entropy()

        if not cells:
            return None

        cell = random().choice(tuple(cells))
        try:
            options = cell.options.copy()
            cell.collapse()
            self._propagate(cell)
        except NoSolutionException as nse:
            self.contradictions += 1
            print(
                f"_observe_random_cell: {nse}, stack: {len(self.stack)}, contradictions: {self.contradictions}"
            )
            # print(f"cell: {cell}, options: {options}")
            # print(f"uncollapsed cells: {len(self._get_cells_with_minimum_entropy())}")
            # print(f"cells with minimum entropy: {len(cells)}")

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
                            & set(self.rules[tile.id][direction])
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
                self.history.pop(backtrack_cell, self.tiles) & backtrack_cell.options
            )

            neighbors = self._get_neighbors(backtrack_cell)
            for neighbor in neighbors:
                neighbor.options = self.tiles
                if neighbor in self.stack:
                    self.stack.remove(neighbor)

            self._propagate(backtrack_cell)

            if self.contradictions > len(self.stack):
                break

            return False

        self.contradictions = 0
        self.stack = []
        self.cells = self.init_cells(self.width, self.height, self.tiles)

        return True

    def print_map(self):
        print("\033[2J\033[H", end="")
        print("\033[1;0H", end="")
        print("-" * self.width)
        for y, row in enumerate(self.cells):
            for x, column in enumerate(row):
                print(f"\033[{y+2};{x+1}H", end="")
                cell = self.cells[y][x]
                if cell.collapsed:
                    print(cell.get_tile().id, end="")
                    continue
                print("?", end="")
        print(f"\033[{self.height+2};0H", end="")
        print("-" * self.width)

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

    def show_map_window(self):
        self.contradictions = 0

        def reset(event):
            self.cells = self.init_cells(self.width, self.height, self.tiles)
            self.contradictions = 0
            self.stack = []
            update()

        window = tk.Tk()
        window.minsize(
            (self.width * self.tile_width + self.tile_width) * 2,
            (self.height * self.tile_height + self.tile_height) * 2,
        )
        window.maxsize(
            (self.width * self.tile_width + self.tile_width) * 2,
            (self.height * self.tile_height + self.tile_height) * 2,
        )
        canvas = tk.Canvas(window)
        canvas.bind("<Button-1>", reset)
        canvas.pack(fill="both", expand=True)

        def update():
            finished = False
            if cells := self._get_cells_with_minimum_entropy(self.cells):
                finished = self._collapse(cells)
            else:
                finished = True

            draw(cells)
            if not finished:
                window.after(FRAME_DELAY, update)
            else:
                self.draw_map()
                print(f"Finished with {self.contradictions} contradictions.")

        def draw_cell(cell: Cell):
            # canvas.create_rectangle(
            #     (cell.x * self.tile_width + (self.tile_width // 2)) * 2,
            #     (cell.y * self.tile_height + (self.tile_height // 2)) * 2,
            #     (cell.x * self.tile_width + (self.tile_width * 1.5)) * 2,
            #     (cell.y * self.tile_height + (self.tile_height * 1.5)) * 2,
            #     tag=f"{cell.x},{cell.y}_blank",
            # )
            canvas.delete(f"{cell.x},{cell.y}_overlay")

            if cell.entropy > 1:
                # print(f"Erasing cell at ({cell.x}, {cell.y})...")
                canvas.delete(f"{cell.x},{cell.y}")
                # canvas.delete(f"{cell.x},{cell.y}_contradiction")
            elif cell.entropy == 1:
                # canvas.delete(f"{cell.x},{cell.y}_blank")
                # canvas.delete(f"{cell.x},{cell.y}_contradiction")
                # print(f"Drawing cell at ({cell.x}, {cell.y})...")
                tile = cell.get_tile()
                if (tk_img := self.tk_images.get(tile.id)) is None:
                    tk_img = tk.PhotoImage(file=tile.img).zoom(2)
                    self.tk_images[tile.id] = tk_img

                canvas.create_image(
                    (cell.x * self.tile_width + (self.tile_width // 2)) * 2,
                    (cell.y * self.tile_height + (self.tile_height // 2)) * 2,
                    anchor=tk.NW,
                    image=tk_img,
                    tag=f"{cell.x},{cell.y}",
                )
            canvas.create_rectangle(
                (cell.x * self.tile_width + (self.tile_width // 2)) * 2,
                (cell.y * self.tile_height + (self.tile_height // 2)) * 2,
                (cell.x * self.tile_width + (self.tile_width * 1.5)) * 2,
                (cell.y * self.tile_height + (self.tile_height * 1.5)) * 2,
                tag=f"{cell.x},{cell.y}_overlay",
            )
            # if cell.entropy == 0:
            #     canvas.create_rectangle(
            #         (cell.x * self.tile_width + (self.tile_width // 2)) * 2,
            #         (cell.y * self.tile_height + (self.tile_height // 2)) * 2,
            #         (cell.x * self.tile_width + (self.tile_width * 1.5)) * 2,
            #         (cell.y * self.tile_height + (self.tile_height * 1.5)) * 2,
            #         tag=f"{cell.x},{cell.y}_contradiction",
            #         outline="red"
            #     )

        def draw(cells):
            for cell in cells or [cell for row in self.cells for cell in row]:
                draw_cell(cell)

        draw([cell for row in self.cells for cell in row])
        window.after(FRAME_DELAY, update)
        window.mainloop()
