# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

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
