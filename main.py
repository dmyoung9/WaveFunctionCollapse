from __future__ import annotations


from wfc.tilemap import TileMap
from wfc.tileset import TileSet
from wfc.window import show_map_window


def main():
    # Define the states
    tileset = TileSet.load_from_json("sheet")
    tilemap = TileMap(16, 16, tileset)
    show_map_window(tilemap)

    # generate_tilemap(*MAP_DIMENSIONS, tileset)


if __name__ == "__main__":
    main()
