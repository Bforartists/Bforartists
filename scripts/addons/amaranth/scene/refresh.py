# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Refresh Scene

Refresh the current scene, useful when working with libraries or drivers.
Could also add an option to refresh the VSE maybe? Usage: Hit F5 or find
it on the Specials menu W.
"""

import bpy


KEYMAPS = list()


class AMTH_SCENE_OT_refresh(bpy.types.Operator):
    """Refresh the current scene"""
    bl_idname = "scene.refresh"
    bl_label = "Refresh!"

    def execute(self, context):
        get_addon = "amaranth" in context.preferences.addons.keys()
        if not get_addon:
            return {"CANCELLED"}

        preferences = context.preferences.addons["amaranth"].preferences
        scene = context.scene

        if preferences.use_scene_refresh:
            # Changing the frame is usually the best way to go
            scene.frame_current = scene.frame_current
            self.report({"INFO"}, "Scene Refreshed!")

        return {"FINISHED"}


def button_refresh(self, context):
    get_addon = "amaranth" in context.preferences.addons.keys()
    if not get_addon:
        return

    if context.preferences.addons["amaranth"].preferences.use_scene_refresh:
        self.layout.separator()
        self.layout.operator(AMTH_SCENE_OT_refresh.bl_idname,
                             text="Refresh!",
                             icon="FILE_REFRESH")


def register():
    bpy.utils.register_class(AMTH_SCENE_OT_refresh)
    bpy.types.VIEW3D_MT_object_context_menu.append(button_refresh)

    kc = bpy.context.window_manager.keyconfigs.addon
    if kc is not None:
        km = kc.keymaps.new(name="Window")
        kmi = km.keymap_items.new("scene.refresh", "F5", "PRESS",
                                  alt=True)
        KEYMAPS.append((km, kmi))


def unregister():
    bpy.utils.unregister_class(AMTH_SCENE_OT_refresh)
    bpy.types.VIEW3D_MT_object_context_menu.remove(button_refresh)
    for km, kmi in KEYMAPS:
        km.keymap_items.remove(kmi)
    KEYMAPS.clear()
