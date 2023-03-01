from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Dict


class Tile:
    def __init__(self, id: int, north: str, east: str, south: str, west: str):
        """
        A specific `Tile` that can be added to a `TileMap`. Each tile is
        identified by a unique integer ID.

        Where each string is a representation of that side of the tile.
        """
        self.id = id
        self.edges = self._init_edges(north, east, south, west)

    def _init_edges(
        self, north: str, east: str, south: str, west: str
    ) -> Dict[str, str]:
        if not (len(north) == len(east) == len(south) == len(west)):
            raise ValueError(f"Edges must be of the same length for Tile {id}!")

        return {"north": north, "east": east, "south": south, "west": west}

    def __eq__(self, other):
        return all(
            (self.id == other.id, self.edges == other.edges)
        )

    def __hash__(self):
        return hash(f"{self.id}_{self.edges}")

    def __repr__(self):
        return f"Tile(id: {self.id}, edges: {self.edges}, rules: {self.rules})"

    def __str__(self):
        return str(self.id)
