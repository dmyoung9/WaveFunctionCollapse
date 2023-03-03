from __future__ import annotations


from wfc.tilemap import TileMap
from wfc.tileset import TileSet


def main():
    # Define the states
    tileset = TileSet("sheet")
    tilemap = TileMap(24, 16, tileset)
    tilemap.show_map_window()

    # generate_tilemap(*MAP_DIMENSIONS, tileset)


if __name__ == "__main__":
    main()
