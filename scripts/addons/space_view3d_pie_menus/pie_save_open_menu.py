# SPDX-FileCopyrightText: 2016-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Hotkey: 'Ctrl S'",
    "description": "Save/Open & File Menus",
    "blender": (2, 80, 0),
    "location": "All Editors",
    "warning": "",
    "doc_url": "",
    "category": "Save Open Pie"
}

import bpy
from bpy.types import (
    Menu,
    Operator,
)
import os


# Pie Save/Open
class PIE_MT_SaveOpen(Menu):
    bl_idname = "PIE_MT_saveopen"
    bl_label = "Pie Save/Open"

    @staticmethod
    def _save_as_mainfile_calc_incremental_name():
        import re
        dirname, base_name = os.path.split(bpy.data.filepath)
        base_name_no_ext, ext = os.path.splitext(base_name)
        match = re.match(r"(.*)_([\d]+)$", base_name_no_ext)
        if match:
            prefix, number = match.groups()
            number = int(number) + 1
        else:
            prefix, number = base_name_no_ext, 1
        prefix = os.path.join(dirname, prefix)
        while os.path.isfile(output := "%s_%03d%s" % (prefix, number, ext)):
            number += 1
        return output

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator("wm.read_homefile", text="New", icon='FILE_NEW')
        # 6 - RIGHT
        pie.menu("PIE_MT_link", text="Link Menu", icon='LINK_BLEND')
        # 2 - BOTTOM
        pie.menu("PIE_MT_fileio", text="Import/Export Menu", icon='IMPORT')
        # 8 - TOP
        pie.menu("PIE_MT_openio", text="Open Menu", icon='FILE_FOLDER')
        # 7 - TOP - LEFT
        pie.operator("wm.save_mainfile", text="Save", icon='FILE_TICK')
        # 9 - TOP - RIGHT
        pie.operator("wm.save_as_mainfile", text="Save As...", icon='NONE')
        # 1 - BOTTOM - LEFT
        if bpy.data.is_saved:
            default_operator_contest = layout.operator_context
            layout.operator_context = 'EXEC_DEFAULT'
            pie.operator(
                "wm.save_as_mainfile", text="Incremental Save", icon='NONE',
            ).filepath = self._save_as_mainfile_calc_incremental_name()
            layout.operator_context = default_operator_contest
        else:
            pie.box().label(text="Incremental Save (unsaved)")

        # 3 - BOTTOM - RIGHT
        pie.menu("PIE_MT_recover", text="Recovery Menu", icon='RECOVER_LAST')


class PIE_MT_link(Menu):
    bl_idname = "PIE_MT_link"
    bl_label = "Link"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        box = pie.split().column()
        box.operator("wm.link", text="Link", icon='LINK_BLEND')
        box.operator("wm.append", text="Append", icon='APPEND_BLEND')
        box.separator()
        box.operator("file.autopack_toggle", text="Automatically Pack Into .blend")
        box.operator("file.pack_all", text="Pack All Into .blend")
        box.operator("file.unpack_all", text="Unpack All Into Files")
        box.separator()
        box.operator("file.make_paths_relative", text="Make All Paths Relative")
        box.operator("file.make_paths_absolute", text="Make All Paths Absolute")


class PIE_MT_recover(Menu):
    bl_idname = "PIE_MT_recover"
    bl_label = "Recovery"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        box = pie.split().column()
        box.operator("wm.recover_auto_save", text="Recover Auto Save...", icon='NONE')
        box.operator("wm.recover_last_session", text="Recover Last Session", icon='RECOVER_LAST')
        box.operator("wm.revert_mainfile", text="Revert", icon='FILE_REFRESH')
        box.separator()
        box.operator("file.report_missing_files", text="Report Missing Files")
        box.operator("file.find_missing_files", text="Find Missing Files")


class PIE_MT_fileio(Menu):
    bl_idname = "PIE_MT_fileio"
    bl_label = "Import/Export"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        box = pie.split().column()
        box.menu("TOPBAR_MT_file_import", icon='IMPORT')
        box.separator()
        box.menu("TOPBAR_MT_file_export", icon='EXPORT')


class PIE_MT_openio(Menu):
    bl_idname = "PIE_MT_openio"
    bl_label = "Open/Open Recent"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        box = pie.split().column()
        box.operator("wm.open_mainfile", text="Open File", icon='FILE_FOLDER')
        box.separator()
        box.menu("TOPBAR_MT_file_open_recent", icon='FILE_FOLDER')


classes = (
    PIE_MT_SaveOpen,
    PIE_MT_fileio,
    PIE_MT_recover,
    PIE_MT_link,
    PIE_MT_openio,
)

addon_keymaps = []


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    wm = bpy.context.window_manager
    if wm.keyconfigs.addon:
        # Save/Open/...
        km = wm.keyconfigs.addon.keymaps.new(name='Window')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'S', 'PRESS', ctrl=True)
        kmi.properties.name = "PIE_MT_saveopen"
        addon_keymaps.append((km, kmi))


def unregister():
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
