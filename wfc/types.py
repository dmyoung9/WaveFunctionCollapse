from __future__ import annotations

from typing import Dict, List, Literal, Optional, TypedDict

TileId = int
Edge = str

Direction = Literal["north", "east", "south", "west"]
EdgeDict = Dict[Direction, Edge]

Attribution = Literal["author", "source"]
AttributionDict = Dict[Attribution, str]


class TileJson(TypedDict):
    filename: str
    edges: List[Edge]


class TilesJson(TypedDict):
    tiles: List[TileJson]


class JsonDict(TypedDict):
    pack_name: str
    tile_width: int
    tile_height: Optional[int]
    attribution: Optional[AttributionDict]
    tiles: TilesJson
