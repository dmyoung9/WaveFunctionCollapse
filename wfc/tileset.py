import json
import os

from PIL import Image

from .constants import DIRECTION_NAMES
from .tile import Tile


class TileSet:
    def __init__(self, name: str):
        self.name = None
        self.tile_width = 0
        self.tile_height = 0
        self.tiles = set()

        self._load_from_json(name)

    def _load_from_json(self, name: str):
        path = os.path.join(os.getcwd(), "tiles", name)
        with open(os.path.join(path, "pack.json")) as f:
            pack_json = json.load(f)

        if pack_json:
            self.name = pack_json["pack_name"]
            self.tile_width = pack_json["tile_width"]
            self.tile_height = pack_json["tile_height"]

            for tile in pack_json["tiles"]:
                tile_img = os.path.join(path, tile["filename"])
                tile_id = int(tile["filename"].split(".")[0])
                tile_edges = dict(zip(DIRECTION_NAMES, tile["edges"]))
                self.tiles.add(Tile(tile_id, **tile_edges, img=tile_img))
