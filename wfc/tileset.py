from __future__ import annotations

import itertools
import json
import os

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Dict, List, Optional, Set

    from .types import AttributionDict, Direction, Edge, EdgeDict, TilesJson

from .constants import DEFAULT_ATTRIBUTION, DIRECTIONS
from .tile import Tile


class TileSet:
    """Represents a set of `Tile`s to be used when generating `TileMap`s."""

    def __init__(
        self,
        name: str,
        tile_width: int,
        tiles: Set[Tile],
        tile_height: Optional[int] = None,
        attribution: Optional[AttributionDict] = None,
    ):
        """Constructs a new `TileSet` object.

        :param name: The name of this tileset
        :ptype name: `str`
        :param tile_width: How wide each tile is, in pixels
        :ptype tile_width: `int`
        :param tiles: All `Tile`s that should be in this tileset
        :ptype tiles: `Set[Tile]`
        :param tile_height: How wide each tile is, in pixels. If omitted, `tile_width` is used.
        :ptype tile_height: `Optional[int]`
        :param attribution: Credits for this tileset
        :ptype attribution: `Optional[AttributionDict]`
        """
        self.name = name
        self.tile_width = tile_width
        self.tiles = tiles

        self.tile_height = int(tile_height) if tile_height is not None else tile_width
        self.attribution: Dict[str, str] = attribution or DEFAULT_ATTRIBUTION

    @staticmethod
    def load_from_json(pack_name: str) -> Optional[TileSet]:
        """Parses a JSON file located at `tiles/pack_name/pack.json`,
        and creates a `TileSet` from it.

        :param pack_name: The name of the folder this tileset's assets are located in
        :ptype pack_name: `str`
        :return: A `TileSet` object, or `None` if the file cannot be parsed
        :rtype: `Optional[TileSet]`
        """

        path = os.path.join(os.getcwd(), "tiles", pack_name)
        with open(os.path.join(path, "pack.json")) as f:
            pack_json = json.load(f)

        if not pack_json:
            return None

        name = pack_json["pack_name"]
        tile_width = pack_json["tile_width"]
        tiles = _build_tiles(pack_json["tiles"], path)
        _build_rules(tiles)
        tile_height = pack_json.get("tile_height", tile_width)
        attribution = pack_json.get("attribution")

        return TileSet(name, tile_width, tiles, tile_height, attribution)


def _parse_edges(edges: List[Edge]) -> EdgeDict:
    """Returns a dictionary of edges.

    :param edges: A list of edges in NESW order
    :ptype edges: `List[Edge]`
    :return: Dictionary of edges
    :rtype: `EdgeDict`
    """
    return dict(zip(DIRECTIONS.keys(), edges))


def _are_compatible(tile_a: Tile, tile_b: Tile, direction: Direction) -> bool:
    """Checks if two tiles are compatible in the given direction.

    :param tile_a: The first tile
    :ptype tile_a: `Tile`
    :param tile_b: The second tile
    :ptype tile_b: `Tile`
    :param direction: The direction in which to compare these two tiles
    :return: Whether or not these two tiles are compatible in the given direction
    :rtype: `bool`
    """

    direction_names = tuple(DIRECTIONS.keys())
    direction_a = direction
    direction_b = direction_names[
        (direction_names.index(direction) + 2) % len(direction_names)
    ]

    edge_a = tile_a.edges[direction_a]
    edge_b = tile_b.edges[direction_b][::-1]
    return edge_a == edge_b


def _build_tiles(tiles_json: TilesJson, base_path: str) -> Set[Tile]:
    """Build `Tile` objects for every tile defined in a JSON file.

    :param tiles_json: The `tiles` definition from a `pack.json` file
    :ptype tiles_json: `TilesJson`
    """
    tiles = set()

    for idx, tile in enumerate(tiles_json):
        tile_id = idx
        img_path = os.path.join(base_path, tile["filename"])
        tiles.add(Tile(tile_id, **_parse_edges(tile["edges"]), img=img_path))

    return tiles


def _build_rules(tiles: Set[Tile]) -> None:
    """Builds adjacency rules from a given set of `Tile`s.

    :param tiles: The tiles to build rules for
    :ptype tiles: `Set[Tile]`
    """

    for _tile, tile, direction in itertools.product(tiles, tiles, DIRECTIONS.keys()):
        if _are_compatible(_tile, tile, direction):
            _tile.add_compatible_tile(tile, direction)
