from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .cell import Cell


class NoSolutionException(Exception):
    def __init__(self, cell: Cell):
        super().__init__(f"Cell at ({cell.x}, {cell.y}) has no options left!")
