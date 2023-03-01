from __future__ import annotations

from wfc.constants import MAP_DIMENSIONS
from wfc.tile import Tile
from wfc import generate_tilemap


def main():
    # Define the states
    tiles = {
        Tile(0, north="0", east="0", south="0", west="0"),
        Tile(1, north="1", east="1", south="0", west="1"),
        Tile(2, north="1", east="1", south="1", west="0"),
        Tile(3, north="0", east="1", south="1", west="1"),
        Tile(4, north="1", east="0", south="1", west="1"),
    }

    generate_tilemap(*MAP_DIMENSIONS, tiles)


if __name__ == "__main__":
    main()
