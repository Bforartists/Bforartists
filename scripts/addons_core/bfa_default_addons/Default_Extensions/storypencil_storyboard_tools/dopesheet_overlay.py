# SPDX-FileCopyrightText: 2022-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import typing

import bpy
import gpu
from gpu_extras.batch import batch_for_shader

from .utils import (redraw_all_areas_by_type)
from .synchro import (is_secondary_window, window_id, get_main_strip)

Int3 = typing.Tuple[int, int, int]

Float2 = typing.Tuple[float, float]
Float3 = typing.Tuple[float, float, float]
Float4 = typing.Tuple[float, float, float, float]


class LineDrawer:
    def __init__(self):
        self._format = gpu.types.GPUVertFormat()
        self._pos_id = self._format.attr_add(
            id="pos", comp_type="F32", len=2, fetch_mode="FLOAT"
        )
        self._color_id = self._format.attr_add(
            id="color", comp_type="F32", len=4, fetch_mode="FLOAT"
        )

        self.shader = gpu.shader.from_builtin('UNIFORM_COLOR')

    def draw(
            self,
            coords: typing.List[Float2],
            indices: typing.List[Int3],
            color: Float4,
    ):
        if not coords:
            return

        gpu.state.blend_set('ALPHA')

        self.shader.uniform_float("color", color)

        batch = batch_for_shader(self.shader, 'TRIS', {"pos": coords}, indices=indices)
        batch.program_set(self.shader)
        batch.draw()

        gpu.state.blend_set('NONE')


def get_scene_strip_in_out(strip):
    """ Return the in and out keyframe of the given strip in the scene time reference"""
    shot_in = strip.scene.frame_start + strip.frame_offset_start
    shot_out = shot_in + strip.frame_final_duration - 1
    return (shot_in, shot_out)


def draw_callback_px(line_drawer: LineDrawer):
    context = bpy.context
    region = context.region
    main_scene = context.scene.storypencil_main_scene
    if main_scene is None:
        return

    use_win = main_scene.storypencil_use_new_window
    wm = context.window_manager

    if (
            (use_win and not wm.storypencil_settings.active)
            or not wm.storypencil_settings.show_main_strip_range
            or (use_win and not is_secondary_window(wm, window_id(context.window)))
            or (not use_win and context.scene == main_scene)
    ):
        return

    # get main strip driving the sync
    strip = get_main_strip(wm)

    if not strip or strip.scene != context.scene:
        return

    xwin1, ywin1 = region.view2d.region_to_view(0, 0)
    one_pixel_further_x = region.view2d.region_to_view(1, 1)[0]
    pixel_size_x = one_pixel_further_x - xwin1
    rect_width = 1

    shot_in, shot_out = get_scene_strip_in_out(strip)
    key_coords_in = [
        (
            shot_in - rect_width * pixel_size_x,
            ywin1,
        ),
        (
            shot_in + rect_width * pixel_size_x,
            ywin1,
        ),
        (
            shot_in + rect_width * pixel_size_x,
            ywin1 + context.region.height,
        ),
        (
            shot_in - rect_width * pixel_size_x,
            ywin1 + context.region.height,
        ),
    ]

    key_coords_out = [
        (
            shot_out - rect_width * pixel_size_x,
            ywin1,
        ),
        (
            shot_out + rect_width * pixel_size_x,
            ywin1,
        ),
        (
            shot_out + rect_width * pixel_size_x,
            ywin1 + context.region.height,
        ),
        (
            shot_out - rect_width * pixel_size_x,
            ywin1 + context.region.height,
        ),
    ]

    indices = [(0, 1, 2), (2, 0, 3)]
    # Draw the IN frame in green
    # hack: in certain cases, opengl draw state is invalid for the first drawn item
    #       resulting in a non-colored line
    #       => draw it a first time with a null alpha, so that the second one is drawn correctly
    line_drawer.draw(key_coords_in, indices, (0, 0, 0, 0))
    line_drawer.draw(key_coords_in, indices, (0.3, 0.99, 0.4, 0.5))
    # Draw the OUT frame un red
    line_drawer.draw(key_coords_out, indices, (0.99, 0.3, 0.4, 0.5))


def tag_redraw_all_dopesheets():
    redraw_all_areas_by_type(bpy.context, 'DOPESHEET')


# This is a list so it can be changed instead of set
# if it is only changed, it does not have to be declared as a global everywhere
cb_handle = []


def callback_enable():
    if cb_handle:
        return

    # Doing GPU stuff in the background crashes Blender, so let's not.
    if bpy.app.background:
        return

    line_drawer = LineDrawer()
    # POST_VIEW allow to work in time coordinate (1 unit = 1 frame)
    cb_handle[:] = (
        bpy.types.SpaceDopeSheetEditor.draw_handler_add(
            draw_callback_px, (line_drawer,), 'WINDOW', 'POST_VIEW'
        ),
    )

    tag_redraw_all_dopesheets()


def callback_disable():
    if not cb_handle:
        return

    try:
        bpy.types.SpaceDopeSheetEditor.draw_handler_remove(cb_handle[0], 'WINDOW')
    except ValueError:
        # Thrown when already removed.
        pass
    cb_handle.clear()

    tag_redraw_all_dopesheets()


def register():
    callback_enable()


def unregister():
    callback_disable()
