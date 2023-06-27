# SPDX-FileCopyrightText: 2016-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Hotkey: 'W'",
    "description": "Sculpt Brush Menu",
    "author": "pitiwazou, meta-androcto",
    "version": (0, 1, 0),
    "blender": (2, 80, 0),
    "location": "W key",
    "warning": "",
    "doc_url": "",
    "category": "Sculpt Pie"
}

import os
import bpy
from bpy.types import (
    Menu,
    Operator,
)


# Sculpt Draw
class PIE_OT_SculptSculptDraw(Operator):
    bl_idname = "sculpt.sculptraw"
    bl_label = "Sculpt SculptDraw"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.tool_settings.sculpt.brush = bpy.data.brushes['SculptDraw']
        return {'FINISHED'}


# Pie Sculp Pie Menus - W
class PIE_MT_SculptPie(Menu):
    bl_idname = "PIE_MT_sculpt"
    bl_label = "Pie Sculpt"

    def draw(self, context):
        global brush_icons
        layout = self.layout
        pie = layout.menu_pie()
        pie.scale_y = 1.2
        # 4 - LEFT
        pie.operator("paint.brush_select",
                     text="    Crease", icon_value=brush_icons["crease"]).sculpt_tool = 'CREASE'
        # 6 - RIGHT
        pie.operator("paint.brush_select",
                     text="    Blob", icon_value=brush_icons["blob"]).sculpt_tool = 'BLOB'
        # 2 - BOTTOM
        pie.menu(PIE_MT_Sculpttwo.bl_idname, text="More Brushes")
        # 8 - TOP
        pie.operator("sculpt.sculptraw",
                     text="    Draw", icon_value=brush_icons["draw"])
        # 7 - TOP - LEFT
        pie.operator("paint.brush_select",
                     text="    Clay", icon_value=brush_icons["clay"]).sculpt_tool = 'CLAY'
        # 9 - TOP - RIGHT
        pie.operator("paint.brush_select",
                     text="    Clay Strips", icon_value=brush_icons["clay_strips"]).sculpt_tool = 'CLAY_STRIPS'
        # 1 - BOTTOM - LEFT
        pie.operator("paint.brush_select",
                     text="    Inflate/Deflate", icon_value=brush_icons["inflate"]).sculpt_tool = 'INFLATE'
        # 3 - BOTTOM - RIGHT
        pie.menu(PIE_MT_Sculptthree.bl_idname,
                 text="    Grab Brushes", icon_value=brush_icons["grab"])


# Pie Sculpt 2
class PIE_MT_Sculpttwo(Menu):
    bl_idname = "PIE_MT_sculpttwo"
    bl_label = "Pie Sculpt 2"

    def draw(self, context):
        global brush_icons
        layout = self.layout
        layout.scale_y = 1.5

        layout.operator("paint.brush_select", text='    Smooth',
                        icon_value=brush_icons["smooth"]).sculpt_tool = 'SMOOTH'
        layout.operator("paint.brush_select", text='    Flatten',
                        icon_value=brush_icons["flatten"]).sculpt_tool = 'FLATTEN'
        layout.operator("paint.brush_select", text='    Scrape/Peaks',
                        icon_value=brush_icons["scrape"]).sculpt_tool = 'SCRAPE'
        layout.operator("paint.brush_select", text='    Fill/Deepen',
                        icon_value=brush_icons["fill"]).sculpt_tool = 'FILL'
        layout.operator("paint.brush_select", text='    Pinch/Magnify',
                        icon_value=brush_icons["pinch"]).sculpt_tool = 'PINCH'
        layout.operator("paint.brush_select", text='    Layer',
                        icon_value=brush_icons["layer"]).sculpt_tool = 'LAYER'
        layout.operator("paint.brush_select", text='    Mask',
                        icon_value=brush_icons["mask"]).sculpt_tool = 'MASK'


# Pie Sculpt Three
class PIE_MT_Sculptthree(Menu):
    bl_idname = "PIE_MT_sculptthree"
    bl_label = "Pie Sculpt 3"

    def draw(self, context):
        global brush_icons
        layout = self.layout
        layout.scale_y = 1.5

        layout.operator("paint.brush_select",
                        text='    Grab', icon_value=brush_icons["grab"]).sculpt_tool = 'GRAB'
        layout.operator("paint.brush_select",
                        text='    Nudge', icon_value=brush_icons["nudge"]).sculpt_tool = 'NUDGE'
        layout.operator("paint.brush_select",
                        text='    Thumb', icon_value=brush_icons["thumb"]).sculpt_tool = 'THUMB'
        layout.operator("paint.brush_select",
                        text='    Snakehook', icon_value=brush_icons["snake_hook"]).sculpt_tool = 'SNAKE_HOOK'
        layout.operator("paint.brush_select",
                        text='    Rotate', icon_value=brush_icons["rotate"]).sculpt_tool = 'ROTATE'


brush_icons = {}


def create_icons():
    global brush_icons
    icons_directory = bpy.utils.system_resource('DATAFILES', path="icons")
    brushes = (
        "crease", "blob", "smooth", "draw", "clay", "clay_strips", "inflate", "grab",
        "nudge", "thumb", "snake_hook", "rotate", "flatten", "scrape", "fill", "pinch",
        "layer", "mask",
    )
    for brush in brushes:
        filename = os.path.join(icons_directory, f"brush.sculpt.{brush}.dat")
        icon_value = bpy.app.icons.new_triangles_from_file(filename)
        brush_icons[brush] = icon_value


def release_icons():
    global brush_icons
    for value in brush_icons.values():
        bpy.app.icons.release(value)


classes = (
    PIE_MT_SculptPie,
    PIE_MT_Sculpttwo,
    PIE_MT_Sculptthree,
    PIE_OT_SculptSculptDraw,
)

addon_keymaps = []


def register():
    create_icons()

    for cls in classes:
        bpy.utils.register_class(cls)

    wm = bpy.context.window_manager
    if wm.keyconfigs.addon:
        # Sculpt Pie Menu
        km = wm.keyconfigs.addon.keymaps.new(name='Sculpt')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'W', 'PRESS')
        kmi.properties.name = "PIE_MT_sculpt"
        addon_keymaps.append((km, kmi))


def unregister():
    release_icons()

    for cls in classes:
        bpy.utils.unregister_class(cls)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        for km, kmi in addon_keymaps:
            km.keymap_items.remove(kmi)
    addon_keymaps.clear()


if __name__ == "__main__":
    register()
