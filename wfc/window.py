from __future__ import annotations

from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .cell import Cell
    from .tilemap import TileMap

from .constants import FRAME_DELAY, WINDOW_DIMENSIONS


class WfcWindow(tk.Tk):
    def __init__(self, tilemap: TileMap, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tilemap = tilemap

        self.tile_width = tilemap.tile_width
        self.tile_height = tilemap.tile_height

        self.scale_factor = 1
        self.cell_size = min(self.tile_width, self.tile_height) * self.scale_factor

        self.title("Wave Function Collapse")
        self.minsize(*WINDOW_DIMENSIONS)
        self.resizable(True, True)

        self.canvas_frame = tk.Frame(self, bg="gray", width=640, height=480)
        self.canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(
            self.canvas_frame,
            width=640,
            height=480,
        )
        self.canvas_width = 640
        self.canvas_height = 480
        # self.canvas.bind("<Button-1>", self.reset)

        self.panel = tk.Frame(self, bg="gray", width=250, height=480)
        self.panel.pack(side=tk.LEFT, fill=tk.Y)
        self.update_idletasks()
        self.panel.pack_propagate(0)

        self.canvas.config(
            width=self.winfo_width() - 250, scrollregion=self.canvas.bbox("all")
        )
        self.canvas.bind("<Configure>", self.on_canvas_resize)

        self.reset_button = tk.Button(self.panel, text="Generate", command=self.reset)
        self.reset_button.pack(side=tk.BOTTOM, pady=10)

        self.width_label = tk.Label(self.panel, text="Scale Factor:")
        self.width_label.pack(pady=(10, 5))
        self.width_var = tk.StringVar(value="1")
        self.width_spinner = ttk.Spinbox(
            self.panel,
            from_=1,
            to=4,
            textvariable=self.width_var,
            width=5,
            command=self.change_scale_factor,
        )
        self.width_spinner.pack()

        self.hscrollbar = tk.Scrollbar(
            self.canvas_frame, orient="horizontal", command=self.canvas.xview
        )
        self.hscrollbar.pack(side="bottom", fill="x")
        self.vscrollbar = tk.Scrollbar(
            self.canvas_frame, orient="vertical", command=self.canvas.yview
        )
        self.vscrollbar.pack(side="right", fill="y")
        self.canvas.configure(
            xscrollcommand=self.hscrollbar.set, yscrollcommand=self.vscrollbar.set
        )
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

            self.canvas.config(width=event.width - 250)
            self.canvas.configure(
                scrollregion=(
                    0,
                    0,
                    self.canvas_width + self.cell_size,
                    self.canvas_height + self.cell_size,
                )
            )

    def change_scale_factor(self):
        scale = int(self.width_var.get())
        self.scale_factor = scale
        self.cell_size = min(self.tile_width, self.tile_height) * self.scale_factor
        self.invalidate()

    def invalidate(self):
        self.canvas.delete("all")
        self.tk_images = {}

    def update(self):
        if not self.tk_images:
            self.draw(self.tilemap._get_all_cells())

        finished = False
        if cells := self.tilemap._get_minimum_entropy_cells():
            finished = self.tilemap._collapse(cells)
        else:
            finished = True

        self.draw(cells)
        if not finished:
            self.after(FRAME_DELAY, self.update)
        else:
            self.draw(self.tilemap._get_all_cells())
            self.tilemap.draw_map()
            print(f"Finished with {self.tilemap.contradictions} contradictions.")

    def reset(self, _=None):
        self.tilemap.initialize()
        self.invalidate()
        self.update()

    def draw_cell(self, cell: Cell):
        x1 = cell.x * self.cell_size
        y1 = cell.y * self.cell_size
        x2 = x1 + self.cell_size
        y2 = y1 + self.cell_size

        self.canvas.create_rectangle(
            x1,
            y1,
            x2,
            y2,
            outline="black",
            tag=f"{cell.x},{cell.y}_blank",
        )

        if cell.entropy > 1:
            self.canvas.delete(f"{cell.x},{cell.y}")
        elif cell.entropy == 1:
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

    def _get_photo_image(self, tile):
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

    def draw(self, cells):
        for cell in cells:
            self.draw_cell(cell)


def show_map_window(tilemap: TileMap):
    window = WfcWindow(tilemap)
    window.mainloop()
