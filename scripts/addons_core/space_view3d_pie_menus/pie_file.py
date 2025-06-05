# SPDX-FileCopyrightText: 2016-2024 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later


import bpy
from bpy.types import Menu, Operator
from bpy.props import BoolProperty
from .op_pie_wrappers import WM_OT_call_menu_pie_drag_only


class PIE_MT_file(Menu):
    bl_idname = "PIE_MT_file"
    bl_label = "File"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator("wm.open_mainfile", text="Open", icon='FILEBROWSER')
        # 6 - RIGHT
        pie.operator("wm.save_as_mainfile", text="Save As", icon='FILE_TICK')
        # 2 - BOTTOM
        pie.menu("TOPBAR_MT_file_export", text="Export...", icon='EXPORT')
        # 8 - TOP
        pie.menu("TOPBAR_MT_file_import", text="Import...", icon='IMPORT')
        # 7 - TOP - LEFT
        pie.operator('wm.call_menu_pie', text="Library...", icon='LINK_BLEND').name = (
            "PIE_MT_library"
        )
        # 9 - TOP - RIGHT
        pie.operator(
            "wm.save_mainfile", text="Save Incremental", icon='FILE_TICK'
        ).incremental = True
        # 1 - BOTTOM - LEFT
        pie.menu("TOPBAR_MT_file_open_recent", icon='FILE_FOLDER')
        # 3 - BOTTOM - RIGHT
        pie.menu("TOPBAR_MT_file_recover", icon='RECOVER_LAST')


class PIE_MT_library(Menu):
    bl_idname = "PIE_MT_library"
    bl_label = "Library"

    def draw(self, context):
        pie = self.layout.menu_pie()

        # 4 - LEFT
        pie.operator("wm.link", text="Link", icon='LINK_BLEND')
        # 6 - RIGHT
        pie.operator("wm.append", text="Append", icon='APPEND_BLEND')
        # 2 - BOTTOM
        pie.operator(
            "object.make_local", text="Make All Local", icon='FILE_BLEND'
        ).type = 'ALL'
        # 8 - TOP
        pie.prop(bpy.data, 'use_autopack', text="Auto-pack")
        # 7 - TOP - LEFT
        pie.operator(
            "file.pack_res_and_lib", text="Pack All Local", icon='PACKAGE'
        ).pack = True
        # 9 - TOP - RIGHT
        pie.operator(
            "file.pack_res_and_lib", text="Unpack All Local", icon='UGLYPACKAGE'
        ).pack = False
        # 1 - BOTTOM - LEFT
        pie.operator(
            "file.make_paths_relative", icon='FILE', text="Make Paths Relative"
        )
        # 3 - BOTTOM - RIGHT
        pie.operator(
            "file.make_paths_absolute",
            icon='LIBRARY_DATA_BROKEN',
            text="Make Paths Absolute",
        )


class WM_OT_pack_res_and_lib(Operator):
    """Pack/Unpack all local resources and libraries.\nNote: Packing indirectly linked data is not possible in Blender"""

    bl_idname = "file.pack_res_and_lib"
    bl_label = "Pack Resources and Libraries"
    bl_options = {'REGISTER', 'UNDO'}

    pack: BoolProperty()

    def execute(self, context):
        if self.pack:
            bpy.ops.file.pack_libraries()
            bpy.ops.file.pack_all()
        else:
            bpy.ops.file.unpack_libraries()
            bpy.ops.file.unpack_all()

        return {'FINISHED'}


registry = [
    PIE_MT_file,
    PIE_MT_library,
    WM_OT_pack_res_and_lib,
]


def draw_revert(self, context):
    self.layout.operator('wm.revert_mainfile', icon='LOOP_BACK')
    self.layout.separator()


def register():
    WM_OT_call_menu_pie_drag_only.register_drag_hotkey(
        keymap_name="Window",
        pie_name=PIE_MT_file.bl_idname,
        hotkey_kwargs={'type': "S", 'value': "PRESS", 'ctrl': True},
        default_fallback_op='wm.save_mainfile',
        on_drag=True,
    )

    bpy.types.TOPBAR_MT_file_recover.prepend(draw_revert)


def unregister():
    bpy.types.TOPBAR_MT_file_recover.remove(draw_revert)
