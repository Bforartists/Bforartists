# SPDX-FileCopyrightText: 2016-2024 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from pathlib import Path

import bpy
from bpy.types import Menu
from bl_ui.properties_paint_common import BrushAssetShelf

from .op_pie_wrappers import WM_OT_call_menu_pie_drag_only


class PIE_MT_sculpt_brush_select(Menu):
    bl_idname = "PIE_MT_sculpt_brush_select"
    bl_label = "Sculpt Brush Select"

    def draw(self, context):
        global brush_icons
        layout = self.layout
        pie = layout.menu_pie()
        pie.scale_y = 1.2

        # 4 - LEFT
        pie.operator(
            'wm.call_menu_pie',
            text="    Transform Brushes...",
            icon_value=brush_icons['snake_hook'],
        ).name = PIE_MT_sculpt_brush_select_transform.bl_idname
        # 6 - RIGHT
        pie.operator(
            'wm.call_menu_pie',
            text="    Volume Brushes...",
            icon_value=brush_icons['blob'],
        ).name = PIE_MT_sculpt_brush_select_volume.bl_idname
        # 2 - BOTTOM
        if blender_uses_brush_assets():
            sculpt_settings = context.tool_settings.sculpt
            brush = sculpt_settings.brush
            col = pie.column()
            brush_row = col.row()
            brush_row.scale_y = 0.75
            brush_row.scale_x = 0.15
            BrushAssetShelf.draw_popup_selector(
                brush_row, context, brush, show_name=False
            )
            name_row = col.row().box()
            if brush:
                name_row.label(text=brush.name)
        else:
            pie.separator()

        # 8 - TOP
        draw_brush_operator(pie, 'Mask', 'mask')
        # 7 - TOP - LEFT
        draw_brush_operator(pie, 'Grab', 'grab')
        # 9 - TOP - RIGHT
        draw_brush_operator(pie, 'Draw', 'draw')
        # 1 - BOTTOM - LEFT
        pie.operator(
            'wm.call_menu_pie',
            text="    Contrast Brushes...",
            icon_value=brush_icons['flatten'],
        ).name = PIE_MT_sculpt_brush_select_contrast.bl_idname
        # 3 - BOTTOM - RIGHT
        pie.operator(
            'wm.call_menu_pie',
            text="    Special Brushes...",
            icon_value=brush_icons['draw_face_sets'],
        ).name = PIE_MT_sculpt_brush_select_special.bl_idname


class PIE_MT_sculpt_brush_select_contrast(Menu):
    bl_idname = "PIE_MT_sculpt_brush_select_contrast"
    bl_label = "Contrast Brushes"

    def draw(self, context):
        pie = self.layout.menu_pie()

        # 4 - LEFT
        draw_brush_operator(pie, 'Flatten/Contrast', 'flatten')
        # 6 - RIGHT
        draw_brush_operator(pie, 'Scrape/Fill', 'scrape')
        # 2 - BOTTOM
        draw_brush_operator(pie, 'Fill/Deepen', 'fill')
        # 8 - TOP
        draw_brush_operator(pie, 'Scrape Multiplane', 'multiplane_scrape')
        # 7 - TOP - LEFT
        pie.separator()
        # 9 - TOP - RIGHT
        pie.separator()
        # 1 - BOTTOM - LEFT
        draw_brush_operator(pie, 'Smooth', 'smooth')
        # 3 - BOTTOM - RIGHT


class PIE_MT_sculpt_brush_select_transform(Menu):
    bl_idname = "PIE_MT_sculpt_brush_select_transform"
    bl_label = "Transform Brushes"

    def draw(self, context):
        pie = self.layout.menu_pie()

        # 4 - LEFT
        draw_brush_operator(pie, 'Elastic Grab', 'elastic_deform')
        # 6 - RIGHT
        draw_brush_operator(pie, 'Nudge', 'nudge')
        # 2 - BOTTOM
        draw_brush_operator(pie, 'Relax Slide', 'topology')
        # 8 - TOP
        draw_brush_operator(pie, 'Snake Hook', 'snake_hook')
        # 7 - TOP - LEFT
        draw_brush_operator(pie, 'Twist', 'rotate')
        # 9 - TOP - RIGHT
        draw_brush_operator(pie, 'Pose', 'pose')
        # 1 - BOTTOM - LEFT
        draw_brush_operator(pie, 'Pinch/Magnify', 'pinch')
        # 3 - BOTTOM - RIGHT
        draw_brush_operator(pie, 'Thumb', 'thumb')


class PIE_MT_sculpt_brush_select_volume(Menu):
    bl_idname = "PIE_MT_sculpt_brush_select_volume"
    bl_label = "Volume Brushes"

    def draw(self, context):
        pie = self.layout.menu_pie()
        # 4 - LEFT
        draw_brush_operator(pie, 'Blob', 'blob')
        # 6 - RIGHT
        draw_brush_operator(pie, 'Clay', 'clay')
        # 2 - BOTTOM
        draw_brush_operator(pie, 'Inflate/Deflate', 'inflate')
        # 8 - TOP
        draw_brush_operator(pie, 'Draw Sharp', 'draw_sharp')
        # 7 - TOP - LEFT
        draw_brush_operator(pie, 'Clay Strips', 'clay_strips')
        # 9 - TOP - RIGHT
        draw_brush_operator(pie, 'Crease Polish', 'crease')
        # 1 - BOTTOM - LEFT
        draw_brush_operator(pie, 'Clay Thumb', 'clay_thumb')
        # 3 - BOTTOM - RIGHT
        draw_brush_operator(pie, 'Layer', 'layer')


class PIE_MT_sculpt_brush_select_special(Menu):
    bl_idname = "PIE_MT_sculpt_brush_select_special"
    bl_label = "Special Brushes"

    def draw(self, context):
        pie = self.layout.menu_pie()
        # 4 - LEFT
        draw_brush_operator(pie, 'Grab Cloth', 'cloth')
        # 6 - RIGHT
        draw_brush_operator(pie, 'Erase Multires Displacement', 'displacement_eraser')
        # 2 - BOTTOM
        draw_brush_operator(pie, 'Density', 'simplify')
        # 8 - TOP
        draw_brush_operator(pie, 'Paint Soft', 'paint')
        # 7 - TOP - LEFT
        draw_brush_operator(pie, 'Smear', 'smear')
        # 9 - TOP - RIGHT
        draw_brush_operator(pie, 'Face Set Paint', 'draw_face_sets')
        # 1 - BOTTOM - LEFT
        draw_brush_operator(pie, 'Boundary', 'boundary')
        # 3 - BOTTOM - RIGHT
        draw_brush_operator(pie, 'Smear Multires Displacement', 'displacement_smear')


def blender_uses_brush_assets():
    return 'asset_activate' in dir(bpy.ops.brush)


def draw_brush_operator(layout, brush_name: str, brush_icon: str = ""):
    """Draw a brush select operator in the provided UI element with the pre-4.3 icons.
    brush_name must match the name of the Brush Asset.
    brush_icon must match the name of a file in this add-on's icons folder.
    """
    if blender_uses_brush_assets():
        # 4.3
        op = layout.operator(
            'brush.asset_activate',
            text="     " + brush_name,
            icon_value=brush_icons.get(brush_icon, 0),
        )
        op.asset_library_type = 'ESSENTIALS'
        op.relative_asset_identifier = os.path.join(
            "brushes", "essentials_brushes-mesh_sculpt.blend", "Brush", brush_name
        )
    else:
        # Pre-4.3
        if brush_icon:
            op = layout.operator(
                "paint.brush_select",
                text="     " + brush_name,
                icon_value=brush_icons[brush_icon],
            )
            op.sculpt_tool = brush_icon.upper()
        else:
            layout.separator()


brush_icons = {}


def create_icons():
    global brush_icons
    icons_directory = Path(__file__).parent / "icons"

    for icon_path in icons_directory.iterdir():
        icon_value = bpy.app.icons.new_triangles_from_file(icon_path.as_posix())
        brush_name = icon_path.stem.split(".")[-1]
        brush_icons[brush_name] = icon_value


def release_icons():
    global brush_icons
    for value in brush_icons.values():
        bpy.app.icons.release(value)


registry = (
    PIE_MT_sculpt_brush_select,
    PIE_MT_sculpt_brush_select_contrast,
    PIE_MT_sculpt_brush_select_transform,
    PIE_MT_sculpt_brush_select_volume,
    PIE_MT_sculpt_brush_select_special,
)


def register():
    create_icons()

    WM_OT_call_menu_pie_drag_only.register_drag_hotkey(
        keymap_name='Sculpt',
        pie_name=PIE_MT_sculpt_brush_select.bl_idname,
        hotkey_kwargs={'type': "W", 'value': "PRESS"},
        on_drag=False,
    )


def unregister():
    release_icons()
