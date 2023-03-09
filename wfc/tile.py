from __future__ import annotations

from typing import TYPE_CHECKING
from wfc.constants import DIRECTIONS

from wfc.types import Direction

if TYPE_CHECKING:
    from typing import Optional, Set

    from PIL.Image import Image

    from .types import Edge, EdgeDict, TileId


class Tile:
    """Represents a single Tile that could potentially be placed in a `TileMap`."""

    def __init__(
        self,
        id: TileId,
        north: Edge,
        east: Edge,
        south: Edge,
        west: Edge,
        img: Optional[Image] = None,
    ):
        """
        Constructs a `Tile` object. Each tile is identified by a unique integer ID.

        Where each string is a representation of that side of the tile.
        """
        self.id = id
        self.edges = self._init_edges(north, east, south, west)
        self.rules = {k: set() for k in DIRECTIONS.keys()}
        self.img = img

    def _init_edges(self, north: Edge, east: Edge, south: Edge, west: Edge) -> EdgeDict:
        """Returns a dictionary of this Tile's edges.

        :param north: The north edge of this Tile
        :ptype north: `str`
        :param east: The east edge of this Tile
        :ptype east: `str`
        :param south: The south edge of this Tile
        :ptype south: `str`
        :param west: The west edge of this Tile
        :ptype west: `str`
        :return: This tiles edges in a dictionary
        :rtype: `EdgeDict`
        """

        if not (len(north) == len(east) == len(south) == len(west)):
            raise ValueError(f"Edges must be of the same length for Tile {id}!")

        return {"north": north, "east": east, "south": south, "west": west}

    def add_compatible_tile(self, tile: Tile, direction: Direction):
        """Adds an adjacency rule to this tile's ruleset.

        :param tile: The tile to add to this tile's ruleset
        :ptype tile: `Tile`
        :param direction: The direction to add it to
        :ptype direction: `Direction`
        """
        self.rules[direction].add(tile)

    def get_compatible_tiles(self, direction: Direction) -> Set[Tile]:
        """Returns the set of valid tiles in `direction`.

        :param direction: The direction to return rules for
        :ptype direction: `Direction`
        """
        return self.rules[direction]

    def __eq__(self, other):
        return all((self.id == other.id, self.edges == other.edges))

    def __hash__(self):
        return hash(f"{self.id}_{self.edges}")

    def __repr__(self):
        return f"Tile(id: {self.id}, edges: {self.edges}, rules: {self.rules})"

    def __str__(self):
        return str(self.id)
