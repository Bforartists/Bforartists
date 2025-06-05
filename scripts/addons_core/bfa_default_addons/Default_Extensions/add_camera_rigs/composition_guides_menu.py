# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import Panel

from .operators import get_rig_and_cam

class ADD_CAMERA_RIGS_PT_composition_guides(Panel):
    bl_label = "Composition Guides"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'

    def draw(self, context):
        layout = self.layout

        rig, cam = get_rig_and_cam(context.active_object)
        cam = cam.data

        layout.prop(cam, "show_safe_areas")
        layout.row().separator()
        layout.prop(cam, "show_composition_center")
        layout.prop(cam, "show_composition_center_diagonal")
        layout.prop(cam, "show_composition_golden")
        layout.prop(cam, "show_composition_golden_tria_a")
        layout.prop(cam, "show_composition_golden_tria_b")
        layout.prop(cam, "show_composition_harmony_tri_a")
        layout.prop(cam, "show_composition_harmony_tri_b")
        layout.prop(cam, "show_composition_thirds")


def register():
    bpy.utils.register_class(ADD_CAMERA_RIGS_PT_composition_guides)


def unregister():
    bpy.utils.unregister_class(ADD_CAMERA_RIGS_PT_composition_guides)


if __name__ == "__main__":
    register()
