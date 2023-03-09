from __future__ import annotations
import itertools
import time

from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk

from typing import TYPE_CHECKING

from wfc.util import time_execution

if TYPE_CHECKING:
    from .cell import Cell
    from .tilemap import TileMap

from .constants import FRAME_DELAY, WINDOW_DIMENSIONS

CANVAS_DIMENSIONS = (640, 480)
PANEL_WIDTH = 250


def show_map_window(tilemap: TileMap):
    # sourcery skip: instance-method-first-arg-name
    window = WfcWindow(tilemap)
    window.mainloop()


class WfcWindow(tk.Tk):
    def __init__(self, tilemap: TileMap, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tilemap = tilemap

        self.tile_width = tilemap.tile_width
        self.tile_height = tilemap.tile_height
        self.max_entropy = len(tilemap.tileset.tiles)
        self.map_width = 24
        self.map_height = 16

        self.scale_factor = 1
        self.cell_size = min(self.tile_width, self.tile_height) * self.scale_factor
        self.current_generation = set()

        self.title("Wave Function Collapse")
        self.minsize(*WINDOW_DIMENSIONS)
        self.resizable(True, True)

        self.canvas_frame = tk.Frame(
            self, bg="gray", width=CANVAS_DIMENSIONS[0], height=CANVAS_DIMENSIONS[1]
        )
        self.canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(
            self.canvas_frame,
            width=CANVAS_DIMENSIONS[0],
            height=CANVAS_DIMENSIONS[1],
        )
        self.canvas_width = CANVAS_DIMENSIONS[0]
        self.canvas_height = CANVAS_DIMENSIONS[1]

        self.panel = tk.Frame(
            self, bg="gray", width=PANEL_WIDTH, height=CANVAS_DIMENSIONS[1]
        )
        self.panel.pack(side=tk.LEFT, fill=tk.Y)
        self.update_idletasks()
        self.panel.pack_propagate(0)
        self.start_time = 0

        self.canvas.config(
            width=self.winfo_width()
            - PANEL_WIDTH,  # scrollregion=self.canvas.bbox("all")
        )
        self.canvas.bind("<Configure>", self.on_canvas_resize)

        self.reset_button = tk.Button(self.panel, text="Generate", command=self.reset)
        self.reset_button.pack(side=tk.BOTTOM, pady=10)

        self.scale_label = tk.Label(self.panel, text="Scale Factor:")
        self.scale_label.pack(pady=(10, 5))
        self.scale_var = tk.StringVar(value="1")
        self.scale_spinner = ttk.Spinbox(
            self.panel,
            from_=1,
            to=4,
            textvariable=self.scale_var,
            width=5,
        )
        self.scale_spinner.pack()

        self.width_label = tk.Label(self.panel, text="Width:")
        self.width_label.pack(pady=(10, 5))
        self.width_var = tk.StringVar(value="24")
        self.width_spinner = ttk.Spinbox(
            self.panel,
            from_=2,
            to=24,
            textvariable=self.width_var,
            width=5,
        )
        self.width_spinner.pack()

        self.height_label = tk.Label(self.panel, text="Height:")
        self.height_label.pack(pady=(10, 5))
        self.height_var = tk.StringVar(value="16")
        self.height_spinner = ttk.Spinbox(
            self.panel,
            from_=2,
            to=24,
            textvariable=self.height_var,
            width=5,
        )
        self.height_spinner.pack()

        # self.hscrollbar = tk.Scrollbar(
        #     self.canvas_frame, orient="horizontal", command=self.canvas.xview
        # )
        # self.hscrollbar.pack(side="bottom", fill="x")
        # self.vscrollbar = tk.Scrollbar(
        #     self.canvas_frame, orient="vertical", command=self.canvas.yview
        # )
        # self.vscrollbar.pack(side="right", fill="y")
        # self.canvas.configure(
        #     xscrollcommand=self.hscrollbar.set, yscrollcommand=self.vscrollbar.set
        # )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.bind("<Configure>", self.on_canvas_resize)

        self.tk_images = {}

    def on_canvas_resize(self, event):
        if (
            self.canvas_width != self.canvas.winfo_width()
            or self.canvas_height != self.canvas.winfo_height()
        ):
            self.canvas_width = self.canvas.winfo_width()
            self.canvas_height = self.canvas.winfo_height()

            self.canvas.config(width=event.width - PANEL_WIDTH)

    def change_scale_factor(self):
        scale = int(self.scale_var.get())
        self.scale_factor = scale
        self.cell_size = min(self.tile_width, self.tile_height) * self.scale_factor

    def change_dimensions(self):
        width = int(self.width_var.get())
        height = int(self.height_var.get())
        self.map_width = width
        self.map_height = height

    def invalidate(self):
        self.canvas.delete("all")
        self.current_generation = set()
        self.tk_images = {}

    # @time_execution
    def update(self):
        self.current_generation = next(self.tilemap.get_tilemap_generator(), set())

        if self.current_generation:
            self.draw()
        elif self.start_time != 0:
            self.draw()
            print(time.time() - self.start_time)
            self.start_time = 0

    def reset(self, _=None):
        self.change_scale_factor()
        self.change_dimensions()
        self.start_time = time.time()
        self.tilemap.initialize(self.map_width, self.map_height)
        self.invalidate()
        self.after(FRAME_DELAY, self.update)

    def draw_cell(self, cell: Cell, minimum: bool, first: bool = False):
        x1 = cell.x * self.cell_size
        y1 = cell.y * self.cell_size
        x2 = x1 + self.cell_size
        y2 = y1 + self.cell_size

        offset = 2 * self.scale_factor

        self.canvas.delete(f"{cell.x},{cell.y}")
        self.canvas.delete(f"{cell.x},{cell.y}_invalid")
        self.canvas.delete(f"{cell.x},{cell.y}_minimum")

        if not first and minimum:
            self.canvas.delete(f"{cell.x},{cell.y}_blank")
            self.canvas.create_rectangle(
                x1 + offset,
                y1 + offset,
                x2 - (offset + 1),
                y2 - (offset + 1),
                outline="yellow",
                width=self.scale_factor,
                tag=f"{cell.x},{cell.y}_minimum",
            )

        if cell.collapsed is None:
            self.canvas.delete(f"{cell.x},{cell.y}_blank")
            self.canvas.create_rectangle(
                x1 + offset,
                y1 + offset,
                x2 - (offset + 1),
                y2 - (offset + 1),
                outline="red",
                width=self.scale_factor,
                tag=f"{cell.x},{cell.y}_invalid",
            )
        elif cell.collapsed:
            self.canvas.delete(f"{cell.x},{cell.y}_blank")
            tile = cell.get_tile()
            tk_img = self._get_photo_image(tile)

            img_x1 = x1 + (self.cell_size - tk_img.width()) / 2
            img_y1 = y1 + (self.cell_size - tk_img.height()) / 2

            self.canvas.create_image(
                img_x1,
                img_y1,
                anchor=tk.NW,
                image=tk_img,
                tag=f"{cell.x},{cell.y}",
            )

    def _get_photo_image(self, tile, alpha=0):
        if (tk_img := self.tk_images.get(tile.id)) is None:
            img = Image.open(tile.img)
            width, height = img.size
            scale_factor = min(self.cell_size / width, self.cell_size / height)
            resized_img = img.resize(
                (int(width * scale_factor), int(height * scale_factor))
            )
            tk_img = ImageTk.PhotoImage(resized_img)
            self.tk_images[tile.id] = tk_img
        elif tk_img.width() != self.cell_size or tk_img.height() != self.cell_size:
            del self.tk_images[tile.id]
            return self._get_photo_image(tile)

        return tk_img

    # @time_execution
    def draw(self):
        minimum_entropy = (
            min(min_cells)
            if (
                min_cells := [
                    cell.entropy for cell in self.current_generation if cell.entropy > 1
                ]
            )
            else 1
        )

        first = False
        if len(self.current_generation) == self.map_width * self.map_height:
            first = True
            for x, y in itertools.product(
                range(self.map_width), range(self.map_height)
            ):
                x1 = x * self.cell_size
                y1 = y * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                offset = 2 * self.scale_factor

                self.canvas.create_rectangle(
                    x1 + offset,
                    y1 + offset,
                    x2 - (offset + 1),
                    y2 - (offset + 1),
                    width=self.scale_factor,
                    tag=f"{x},{y}_blank",
                )
        
        for cell in self.current_generation:
            self.draw_cell(cell, cell.entropy == minimum_entropy, first)
        self.after(FRAME_DELAY, self.update)
