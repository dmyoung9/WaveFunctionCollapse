from __future__ import annotations

from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from typing import Optional, Set

    from .tile import Tile
    from .types import Direction

from .constants import DIRECTIONS
from .util import random


class Cell:
    """Represents a single cell in a `TileMap`."""

    def __init__(self, x: int, y: int, options: Set[Tile]):
        """Constructs a `Cell` object. Each cell is initialized with a set of
        all possible `Tile`s that could inhabit it.

        :param x: The x-coordinate of this Cell in the tilemap
        :ptype x: `int`
        :param y: The y-coordinate of this Cell in the tilemap
        :ptype y: `int`
        :param options: Tiles which could potentially inhabit this cell
        :ptype options: `Set[Tile]`
        """
        self.x = x
        self.y = y
        self.options = set(options)
        self.neighbors = dict.fromkeys(DIRECTIONS.keys())

    @property
    def entropy(self) -> int:
        """
        Returns the entropy (how many options are still valid) of this cell.

        :return: This cell's entropy
        :rtype: `int`
        """
        return len(self.options)

    @property
    def collapsed(self) -> Optional[bool]:
        """
        Whether or not this cell is collapsed (has only a single valid `Tile`).

        :return: `True` if this cell is collapsed, `False` if it isn't,
                 or `None` if the cell is invalid.
        :rtype: `Optional[bool]`
        """
        return None if self.entropy == 0 else self.entropy == 1

    def collapse(self, options: Optional[Set[Tile]] = None) -> None:
        """
        Collapses the cell down to one of the valid options.

        :param options: Optional set of `Tile`s to override this cells valid options with
        :ptype options: `Optional[Set[Tile]]`
        """

        self.options = {random().choice(tuple(options or self.options))}

    def get_neighbor(self, direction: Direction) -> Optional[Cell]:
        """Returns this cell's neighbor in `direction`.

        :return: A neighboring `Cell`
        :rtype: `Optional[Cell]`
        """
        return self.neighbors.get(direction, None)

    def get_neighbors(self) -> Dict[Direction, Cell]:
        """Return all the neighbors of this cell.

        :return: Dictionary of neighbors
        :rtype: `Dict[Direction, Cell]`
        """
        return self.neighbors

    def get_tile(self) -> Optional[Tile]:
        """Get the `Tile` object that this Cell has been collapsed to.

        :return: The only valid `Tile` if this cell is collapsed, otherwise `None`
        :rtype: `Optional[Tile]`
        """
        return tuple(self.options)[0] if self.collapsed else None

    def __repr__(self) -> str:
        return f"({self.x}, {self.y}) -> {self.entropy}"
