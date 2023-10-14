# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

import bpy
import gpu

from gpu_extras.batch import batch_for_shader


Vec3 = tuple[int, int, int]
Vec2f = tuple[float, float]
Vec4f = tuple[float, float, float, float]


def ui_scaled(val):
    """Return value multiplied by UI scale factor."""
    return val * bpy.context.preferences.system.ui_scale


class OverlayDrawer:
    """Helper class to draw overlays using gpu API."""

    def __init__(self):
        self.format = gpu.types.GPUVertFormat()
        self.shader = gpu.shader.from_builtin("UNIFORM_COLOR")

        self.pos_id = self.format.attr_add(
            id="pos", comp_type="F32", len=2, fetch_mode="FLOAT"
        )
        self.color_id = self.format.attr_add(
            id="color", comp_type="F32", len=2, fetch_mode="FLOAT"
        )

    def draw(self, coords: list[Vec2f], indices: list[Vec3], color: Vec4f):
        gpu.state.blend_set("ALPHA")

        batch = batch_for_shader(self.shader, "TRIS", {"pos": coords}, indices=indices)
        batch.program_set(self.shader)
        self.shader.uniform_float("color", color)
        batch.draw()

        gpu.state.blend_set("NONE")

    def draw_points(self, coords: list[Vec2f], color: Vec4f):
        """Draw points at specified coords.

        :param coords: Points coordinates.
        :param color: Color of the points.
        """
        gpu.state.blend_set("ALPHA")
        batch = batch_for_shader(self.shader, "POINTS", {"pos": coords})
        batch.program_set(self.shader)
        self.shader.uniform_float("color", color)
        batch.draw()
        gpu.state.blend_set("NONE")

    def draw_lines(self, coords: list[Vec2f], color: Vec4f):
        """Draw lines at specified coords.

        :param coords: Lines points coordinates.
        :param color: Color of the lines.
        """
        gpu.state.blend_set("ALPHA")
        batch = batch_for_shader(self.shader, "LINES", {"pos": coords})
        batch.program_set(self.shader)
        self.shader.uniform_float("color", color)
        batch.draw()
        gpu.state.blend_set("NONE")

    def draw_rect(self, x: float, y: float, width: float, height: float, color: Vec4f):
        """Draw a filled rectangle, with [x,y] origin at bottom left corner.

        :param x: x coordinate.
        :param y: y coordinate.
        :param width: Width of the rectangle.
        :param height: Height of the rectangle.
        :param color: Color of the rectangle.
        """
        coords = [(x, y), (x + width, y), (x + width, y + height), (x, y + height)]
        # Triangles indices
        indices = [(0, 1, 2), (2, 0, 3)]
        self.draw(coords, indices, color)

    def draw_box(self, x: float, y: float, width: float, height: float, color: Vec4f):
        """Draw an outline box, with [x,y] origin at bottom left corner.

        :param x: x coordinate.
        :param y: y coordinate.
        :param width: Width of the box.
        :param height: Height of the box.
        :param color: Color of the outmone.
        """
        bl = (x, y)
        br = (x + width, y)
        tr = (x + width, y + height)
        tl = (x, y + height)
        coords = [bl, br, br, tr, tr, tl, tl, bl]
        self.draw_lines(coords, color)
