from __future__ import annotations

import itertools
import json
import os

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Dict, List, Set, Union

from .constants import DEFAULT_ATTRIBUTION, DIRECTION_NAMES
from .tile import Tile


class TileSet:
    def __init__(
        self,
        name: str,
        tile_width: int,
        tile_height: Union[int, None],
        attribution: Union[Dict[str, str], None] = None,
        tiles: Union[Set[Tile], None] = None,
        rules: Dict[int, Dict[str, Set[Tile]]] = None,
    ):
        self.name = name
        self.tile_width = tile_width
        
        self.tile_height = int(tile_height) if tile_height is not None else tile_width
        self.attribution: Dict[str, str] = attribution or DEFAULT_ATTRIBUTION
        self.tiles = tiles or set()
        self.rules = rules or {}

    @staticmethod
    def load_from_json(pack_name: str) -> Union[TileSet, None]:
        path = os.path.join(os.getcwd(), "tiles", pack_name)
        with open(os.path.join(path, "pack.json")) as f:
            pack_json = json.load(f)

        if not pack_json:
            return None

        name = pack_json["pack_name"]
        tile_width = pack_json["tile_width"]
        tile_height = pack_json.get("tile_height", tile_width)
        attribution = pack_json.get("attribution")
        tiles = _build_tiles(pack_json["tiles"], path)
        rules = _build_rules(tiles)

        return TileSet(name, tile_width, tile_height, attribution, tiles, rules)
    
def _parse_edges(edges: List[str]) -> Dict[str, str]:
    return dict(zip(DIRECTION_NAMES, edges))

def _are_compatible(tile_a, tile_b, direction):
    direction_a = direction[1]
    direction_b = DIRECTION_NAMES[(direction[0] + 2) % len(DIRECTION_NAMES)]

    edge_a = tile_a.edges[direction_a]
    edge_b = tile_b.edges[direction_b][::-1]
    return edge_a == edge_b

def _build_tiles(tiles_json, base_path: str) -> Set[Tile]:
    tiles = set()

    for idx, tile in enumerate(tiles_json):
        tile_id = idx
        img_path = os.path.join(base_path, tile["filename"])
        tiles.add(
            Tile(tile_id, **_parse_edges(tile["edges"]), img=img_path)
        )

    return tiles

def _build_rules(tiles: Set[Tile]):
    rules = {tile.id: {k: set() for k in DIRECTION_NAMES} for tile in tiles}

    for _tile, tile in itertools.product(tiles, tiles):
        for idx, d in enumerate(DIRECTION_NAMES):
            if _are_compatible(_tile, tile, (idx, d)):
                rules[_tile.id][d].add(tile)

    return rules
