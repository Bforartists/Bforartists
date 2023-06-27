# SPDX-FileCopyrightText: 2016-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Hotkey: 'Z'",
    "description": "Viewport Shading Menus",
    "author": "pitiwazou, meta-androcto",
    "version": (0, 1, 1),
    "blender": (2, 80, 0),
    "location": "3D View",
    "warning": "",
    "doc_url": "",
    "category": "Shading Pie"
}

import bpy
from bpy.types import Menu


# Pie Shading - Z
class PIE_MT_ShadingView(Menu):
    bl_idname = "PIE_MT_shadingview"
    bl_label = "Pie Shading"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()
        pie.prop(context.space_data.shading, "type", expand=True)

        if context.active_object:
            if context.mode == 'EDIT_MESH':
                pie.operator("MESH_OT_faces_shade_smooth")
                pie.operator("MESH_OT_faces_shade_flat")
            else:
                pie.operator("OBJECT_OT_shade_smooth")
                pie.operator("OBJECT_OT_shade_flat")


classes = (
    PIE_MT_ShadingView,
)

addon_keymaps = []


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    wm = bpy.context.window_manager
    if wm.keyconfigs.addon:
        # Shading
        km = wm.keyconfigs.addon.keymaps.new(name='3D View Generic', space_type='VIEW_3D')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'Z', 'PRESS')
        kmi.properties.name = "PIE_MT_shadingview"
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
