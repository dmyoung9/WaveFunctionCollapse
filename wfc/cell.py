from __future__ import annotations

from typing import TYPE_CHECKING

from wfc.exception import NoSolutionException

if TYPE_CHECKING:
    from typing import Set, Union
    from .tile import Tile

from .util import random


class Cell:
    def __init__(self, x: int, y: int, options: Set[Tile]):
        """
        A single cell in a `TileMap`. Each cell is initialized with a set of
        all possible `Tile`s that could inhabit it.
        """
        self.x = x
        self.y = y
        self.options = set(options)

    @property
    def entropy(self) -> int:
        """
        Returns the entropy (an integer value) of this cell.
        """
        return len(self.options)

    @property
    def collapsed(self) -> bool:
        """
        Whether or not this cell is collapsed (has only a single valid `Tile`).
        """
        return self.entropy == 1

    def collapse(self, options: Union[Set[Tile], None] = None) -> None:
        """
        Collapses the cell down to one of the valid options.
        """
        if not self.options:
            raise NoSolutionException(self)

        self.options = {random().choice(tuple(options or self.options))}

    def get_tile(self) -> Union[Cell, None]:
        return tuple(self.options)[0] if self.collapsed else None

    def __repr__(self) -> str:
        return f"({self.x}, {self.y}) -> {self.entropy}"
