# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

import bpy
import blf
import mathutils

from spa_sequencer.sync.core import (
    get_sync_master_strip,
    get_sync_settings,
    remap_frame_value,
)

from spa_sequencer.gpu_utils import Vec4f, OverlayDrawer
from spa_sequencer.utils import register_classes, unregister_classes


# - Overlay UI global settings

# Height of a shot strip item
STRIP_HEIGHT = 20
# Vertical offset for active shot
ACTIVE_SHOT_Y_OFFSET = STRIP_HEIGHT * 0.5
# Height of the timeline area
TIMELINE_HEIGHT = STRIP_HEIGHT + 8
# Width of strip handles
HANDLE_WIDTH: int = 1
HANDLE_WIDTH_ACTIVE: int = 4
# Minimum height of the region to display the overlay
MIN_REGION_HEIGHT = TIMELINE_HEIGHT * 4

# Colors
STRIP_COLOR_BASE: Vec4f = (0.1, 0.1, 0.1, 0.5)
STRIP_COLOR_ACTIVE: Vec4f = (0.1, 0.1, 0.1, 0.8)
HANDLE_COLOR_BASE: Vec4f = (0.3, 0.3, 0.3, 0.7)
HANDLE_COLOR_LEFT_ACTIVE: Vec4f = (0.3, 0.95, 0.4, 0.6)
HANDLE_COLOR_RIGHT_ACTIVE: Vec4f = (0.95, 0.3, 0.4, 0.6)
TEXT_COLOR_BASE: Vec4f = (0.8, 0.8, 0.8, 0.7)
TEXT_COLOR_ACTIVE: Vec4f = (0.8, 0.8, 0.8, 0.9)


def ui_scaled(val):
    """Return value multiplied by UI scale factor."""
    return val * bpy.context.preferences.system.ui_scale


def ui_baseline_y_pos(context):
    return ui_scaled(45 if context.scene.timeline_markers else 14)


def shot_baseline_y_pos(context):
    return ui_baseline_y_pos(context) + ui_scaled(TIMELINE_HEIGHT - STRIP_HEIGHT) * 0.5


def draw_shot_strip(
    region: bpy.types.Region,
    drawer: OverlayDrawer,
    strip: bpy.types.SceneSequence,
    active: bool = False,
):
    """
    Draw a shot `strip` in the given `region`.

    :param region: The draw region.
    :param drawer: A PolyDrawer instance.
    :param strip: The shot strip to draw.
    :param active: Whether this shot strip is the active one.
    """
    strip_height = ui_scaled(STRIP_HEIGHT)
    base_y_pos = shot_baseline_y_pos(bpy.context)

    frame_in = remap_frame_value(strip.frame_final_start, strip)
    frame_out = remap_frame_value(strip.frame_final_end, strip)
    frame_in = region.view2d.view_to_region(frame_in, 0, clip=False)[0]
    frame_out = region.view2d.view_to_region(frame_out, 0, clip=False)[0]
    duration = frame_out - frame_in
    y = base_y_pos + (ui_scaled(ACTIVE_SHOT_Y_OFFSET) if active else 0)

    strip_col = STRIP_COLOR_ACTIVE if active else STRIP_COLOR_BASE
    handle_l_col = HANDLE_COLOR_LEFT_ACTIVE if active else HANDLE_COLOR_BASE
    handle_r_col = HANDLE_COLOR_RIGHT_ACTIVE if active else HANDLE_COLOR_BASE
    handle_width = ui_scaled(HANDLE_WIDTH_ACTIVE) if active else ui_scaled(HANDLE_WIDTH)

    # Strip
    drawer.draw_rect(frame_in, y, duration, strip_height, strip_col)
    # Left handle
    drawer.draw_rect(frame_in, y, handle_width, strip_height, handle_l_col)
    # Right handle
    drawer.draw_rect(
        frame_out - handle_width, y, handle_width, strip_height, handle_r_col
    )

    # Shot name
    font_id = 0
    blf.color(font_id, *(TEXT_COLOR_ACTIVE if active else TEXT_COLOR_BASE))
    blf.size(font_id, int(11 * bpy.context.preferences.system.ui_scale) / 72)

    # Compute text dimensions for horizontal centering
    dims = blf.dimensions(0, strip.name)
    padding = handle_width + 2
    blf.position(font_id, frame_in + padding, y + (strip_height - dims[1]) * 0.5, 0)
    blf.enable(0, blf.CLIPPING)
    blf.clipping(font_id, frame_in, y, frame_out - padding, y + strip_height)
    blf.draw(font_id, strip.name)
    blf.disable(0, blf.CLIPPING)


def draw_sequence_overlay_cb(drawer: OverlayDrawer):
    """
    Draw master sequence strips using the current scene in the dopesheet.

    :param drawer: PolyDrawer instance.
    """
    context = bpy.context
    sync_settings = get_sync_settings()
    sequence_settings = context.window_manager.sequence_settings

    # Early return if sync or overlay options are disabled.
    if not sync_settings.enabled or not sequence_settings.overlay_dopesheet:
        return

    # Only draw overlay if current scene matches master strip's scene.
    master_strip = get_sync_master_strip(use_cache=True)[0]
    if not master_strip or master_strip.scene != context.scene:
        return

    if context.region.height < MIN_REGION_HEIGHT:
        return

    # Draw 1 frame duration at current time.
    # This helps getting a better sense of the frame's extent.
    frame = context.scene.frame_current
    f0 = context.region.view2d.view_to_region(frame, 0, clip=False)[0]
    f1 = context.region.view2d.view_to_region(frame + 1, 0, clip=False)[0]
    drawer.draw_rect(
        f0,
        ui_baseline_y_pos(bpy.context),
        f1 - f0,
        ui_scaled(TIMELINE_HEIGHT),
        (0.1, 0.5, 0.8, 0.6),
    )

    # List strips using the currently active scene in the master sequence timeline
    scene_strips = [
        s
        for s in sync_settings.master_scene.sequence_editor.sequences
        if isinstance(s, bpy.types.SceneSequence)
        and s.scene == context.scene
        and s != master_strip
    ]

    # Draw those strips
    for strip in scene_strips:
        draw_shot_strip(context.region, drawer, strip)

    # Draw master strip on top
    draw_shot_strip(context.region, drawer, master_strip, active=True)


class GIZMO_GT_Rectangle(bpy.types.Gizmo):
    """Unit rectangular area, with origin at bottom left corner."""

    def draw(self, context):
        self.draw_custom_shape(self.custom_shape)

    def setup(self):
        bl, br, tr, tl = (0, 0), (0, 1), (1, 1), (1, 0)
        self.custom_shape = self.new_custom_shape("TRIS", (bl, br, tr, bl, tr, tl))


class GIZMO_GT_MouseArea(GIZMO_GT_Rectangle):
    """Unit rectangle area reacting to mouse events."""

    cursor: bpy.props.StringProperty(
        name="CURSOR",
        description="Mouse cursor for this area",
        default="",
    )

    def test_select(self, context, v):
        # Compute rectangle area in world coordinates
        tl = self.matrix_world @ mathutils.Vector((0, 1, 0, 1))
        br = self.matrix_world @ mathutils.Vector((1, 0, 0, 1))
        # Rectangle/point intersection test
        res = (tl[0] <= v[0] <= br[0]) and (br[1] <= v[1] <= tl[1])
        if self.cursor:
            if res:
                context.window.cursor_set(self.cursor)
            else:
                context.window.cursor_set("DEFAULT")
        return 0 if res else -1


class DOPESHEET_GGT_SequenceGizmos(bpy.types.GizmoGroup):
    bl_label = "Sequence Gizmos"
    bl_options = {"PERSISTENT", "SHOW_MODAL_ALL", "SCALE"}
    bl_space_type = "DOPESHEET_EDITOR"
    bl_region_type = "WINDOW"

    @classmethod
    def poll(cls, context: bpy.types.Context):
        master_strip = get_sync_master_strip(use_cache=True)[0]
        return (
            context.window_manager.sequence_settings.overlay_dopesheet
            and master_strip
            and master_strip.scene == context.scene
        )

    @staticmethod
    def set_gizmo_geom(gizmo: bpy.types.Gizmo, x, y, width, height):
        gizmo.matrix_basis[0][3] = x
        gizmo.matrix_basis[1][3] = y
        gizmo.matrix_basis[0][0] = width
        gizmo.matrix_basis[1][1] = height

    def draw_prepare(self, context: bpy.types.Context):
        # Safety check: gizmos must be initialized
        if not self.gizmos:
            return

        region = context.region
        if context.region.height < MIN_REGION_HEIGHT:
            for gz in self.gizmos:
                if not gz.hide:
                    gz.hide = True
            return

        for gz in self.gizmos:
            if gz.hide:
                gz.hide = False

        base_y = ui_baseline_y_pos(context)
        self.set_gizmo_geom(
            self.sequence_timeline,
            x=0,
            y=base_y,
            width=region.width,
            height=ui_scaled(TIMELINE_HEIGHT),
        )

        strip, _ = get_sync_master_strip(use_cache=True)

        # Toggle strip handles based on whether there is an active master strip
        for gizmo in (self.right_handle, self.left_handle, self.shot_handle):
            gizmo.hide = not strip
        # Early return if not active strip
        if not strip:
            return

        frame_in = remap_frame_value(strip.frame_final_start, strip)
        frame_out = remap_frame_value(strip.frame_final_end, strip)
        frame_in = region.view2d.view_to_region(frame_in, 0, clip=False)[0]
        frame_out = region.view2d.view_to_region(frame_out, 0, clip=False)[0]

        handle_width = ui_scaled(HANDLE_WIDTH_ACTIVE) * 2
        strip_height = ui_scaled(STRIP_HEIGHT)
        strip_y = shot_baseline_y_pos(context) + ui_scaled(ACTIVE_SHOT_Y_OFFSET)

        # Left handle
        self.set_gizmo_geom(
            self.left_handle,
            x=frame_in - handle_width * 0.5,
            y=strip_y,
            width=handle_width,
            height=strip_height,
        )

        # Right handle
        self.set_gizmo_geom(
            self.right_handle,
            x=frame_out - handle_width * 0.5,
            y=strip_y,
            width=handle_width,
            height=strip_height,
        )

        strip_handle_height = strip_height * 0.5
        # Shot handle
        self.set_gizmo_geom(
            self.shot_handle,
            x=frame_in,
            y=strip_y + strip_height - strip_handle_height * 0.5,
            width=frame_out - frame_in,
            height=strip_handle_height,
        )

    def add_gizmo(self, operator: str):
        gizmo = self.gizmos.new("GIZMO_GT_MouseArea")
        gizmo.cursor = "MOVE_X"
        gizmo.color = gizmo.color_highlight = 0.4, 0.4, 0.4
        gizmo.alpha = 0.0
        gizmo.alpha_highlight = 0.7
        gizmo.use_draw_modal = True
        gizmo.use_draw_scale = False

        props = gizmo.target_set_operator(operator)
        return gizmo, props

    def setup(self, context):
        # Active shot gizmos
        # - Left handle
        self.left_handle, props = self.add_gizmo("sequencer.shot_timing_adjust")
        props.strip_handle = "LEFT"
        # - Right handle
        self.right_handle, props = self.add_gizmo("sequencer.shot_timing_adjust")
        props.strip_handle = "RIGHT"
        # - Shot handle (slip content)
        self.shot_handle, props = self.add_gizmo("sequencer.shot_timing_adjust")
        self.shot_handle.alpha = 0.2
        self.shot_handle.alpha_highlight = 0.7
        props.mode = "SLIP"

        # Sequence timeline scrub gizmo
        self.sequence_timeline, props = self.add_gizmo("dopesheet.sequence_navigate")
        self.sequence_timeline.cursor = ""
        self.sequence_timeline.color = 0.17, 0.17, 0.17
        self.sequence_timeline.alpha = 0.8
        self.sequence_timeline.alpha_highlight = 0.8
        self.sequence_timeline.color_highlight = self.sequence_timeline.color


# Global handle object to store registered custom overlay draw callback
draw_cb_handle = []


def enable_sequence_overlay():
    # Discard overlay in background mode or if already registered
    if bpy.app.background or draw_cb_handle:
        return

    # Create a PolyDrawer instance for custom shape drawing
    drawer = OverlayDrawer()
    # Register the sequence overlay draw callback in dopesheet based editors
    draw_cb_handle[:] = [
        bpy.types.SpaceDopeSheetEditor.draw_handler_add(
            draw_sequence_overlay_cb, (drawer,), "WINDOW", "POST_PIXEL"
        )
    ]


def disable_sequence_overlay():
    # Discard if draw callback has not been registered
    if not draw_cb_handle:
        return
    # Remove sequence overlay draw callback
    bpy.types.SpaceDopeSheetEditor.draw_handler_remove(draw_cb_handle[0], "WINDOW")
    # Clear global handle object
    draw_cb_handle.clear()


classes = (
    GIZMO_GT_Rectangle,
    GIZMO_GT_MouseArea,
    DOPESHEET_GGT_SequenceGizmos,
)


def register():
    enable_sequence_overlay()
    register_classes(classes)


def unregister():
    disable_sequence_overlay()
    unregister_classes(classes)
