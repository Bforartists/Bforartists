# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Save & Reload File

When working with linked libraries, very often you need to save and load
again to see the changes.
This does it in one go, without asking, so be careful :)
Usage: Hit Ctrl + Shift + W or find it at the bottom of the File menu.
"""

import bpy


KEYMAPS = list()

def check_for_unsaved_images(self):
    im_unsaved = []

    for im in bpy.data.images:
        if im.is_dirty:
            im_unsaved.append(im.name)

    if im_unsaved:
        report_text = 'There are unsaved changes in {0} image(s), check console for details.'\
                        .format(len(im_unsaved))
        self.report({"WARNING"}, report_text)

        print("\nAmaranth found unsaved images when trying to save and reload.")
        for im in im_unsaved:
            print('* Image: "' + im + '" has unsaved changes.')
        return True
    return

class AMTH_WM_OT_save_reload(bpy.types.Operator):
    """Save and Reload the current blend file"""
    bl_idname = "wm.save_reload"
    bl_label = "Save & Reload"

    def save_reload(self, context, path):
        if not path:
            bpy.ops.wm.save_as_mainfile("INVOKE_AREA")
            return

        if check_for_unsaved_images(self):
            return

        bpy.ops.wm.save_mainfile()
        self.report({"INFO"}, "Saved & Reloaded")
        bpy.ops.wm.open_mainfile("EXEC_DEFAULT", filepath=path)

    def execute(self, context):
        path = bpy.data.filepath
        self.save_reload(context, path)

        return {"FINISHED"}


def button_save_reload(self, context):
    get_addon = "amaranth" in context.preferences.addons.keys()
    if not get_addon:
        return

    if context.preferences.addons["amaranth"].preferences.use_file_save_reload:
        self.layout.separator()
        self.layout.operator(
            AMTH_WM_OT_save_reload.bl_idname,
            text="Save & Reload",
            icon="FILE_REFRESH")


def register():
    bpy.utils.register_class(AMTH_WM_OT_save_reload)
    bpy.types.TOPBAR_MT_file.append(button_save_reload)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc is not None:
        km = kc.keymaps.new(name="Window")
        kmi = km.keymap_items.new("wm.save_reload", "W", "PRESS",
                                  shift=True, ctrl=True)
        KEYMAPS.append((km, kmi))


def unregister():
    bpy.utils.unregister_class(AMTH_WM_OT_save_reload)
    bpy.types.TOPBAR_MT_file.remove(button_save_reload)
    for km, kmi in KEYMAPS:
        km.keymap_items.remove(kmi)
    KEYMAPS.clear()
