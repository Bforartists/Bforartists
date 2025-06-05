# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Passepartout on Specials menu

The passepartout value of local cameras is now available on the Specials
menu for easy access.
Under Specials menu W, when in Camera view.
"""

import bpy


def button_camera_passepartout(self, context):
    view3d = context.space_data.region_3d
    cam = context.scene.camera

    if view3d.view_perspective == "CAMERA":
        if cam is None or not hasattr(cam, "data") or cam.type != "CAMERA":
            return

        layout = self.layout
        if cam.data.show_passepartout:
            layout.prop(cam.data, "passepartout_alpha", text="Passepartout")
        else:
            layout.prop(cam.data, "show_passepartout")


def register():
    bpy.types.VIEW3D_MT_object_context_menu.append(button_camera_passepartout)


def unregister():
    bpy.types.VIEW3D_MT_object_context_menu.remove(button_camera_passepartout)
