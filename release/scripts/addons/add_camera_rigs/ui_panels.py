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

from .operators import get_arm_and_cam, CameraRigMixin


class ADD_CAMERA_RIGS_PT_camera_rig_ui(Panel, CameraRigMixin):
    bl_label = "Camera Rig"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Item'

    def draw(self, context):
        active_object = context.active_object
        arm, cam = get_arm_and_cam(context.active_object)
        pose_bones = arm.pose.bones
        cam_data = cam.data

        layout = self.layout.box().column()
        layout.label(text="Clipping:")
        layout.prop(cam_data, "clip_start", text="Start")
        layout.prop(cam_data, "clip_end", text="End")
        layout.prop(cam_data, "type")
        layout.prop(cam_data.dof, "use_dof")
        if cam_data.dof.use_dof:
            if cam_data.dof.focus_object is None:
                layout.operator("add_camera_rigs.add_dof_object",
                                text="Add DOF Empty", icon="OUTLINER_OB_EMPTY")
            layout.prop(pose_bones["Camera"],
                        '["focus_distance"]', text="Focus Distance")
            layout.prop(pose_bones["Camera"],
                        '["aperture_fstop"]', text="F-Stop")

        layout.prop(active_object, 'show_in_front',
                    toggle=False, text='Show in Front')
        layout.prop(cam_data, "show_limits")
        layout.prop(cam_data, "show_passepartout")
        if cam_data.show_passepartout:
            layout.prop(cam_data, "passepartout_alpha")

        layout.row().separator()
        # Added the comp guides here
        layout.popover(
            panel="ADD_CAMERA_RIGS_PT_composition_guides",
            text="Composition Guides",)
        layout.row().separator()

        layout.prop(cam,
                    "hide_select", text="Make Camera Unselectable")

        layout.operator("add_camera_rigs.add_marker_bind",
                        text="Add Marker and Bind", icon="MARKER_HLT")
        if context.scene.camera is not cam:
            layout.operator("add_camera_rigs.set_scene_camera",
                            text="Make Camera Active", icon='CAMERA_DATA')

        # Camera lens
        layout.separator()
        layout.prop(pose_bones["Camera"], '["lens"]', text="Focal Length (mm)")

        # Track to Constraint
        layout.label(text="Tracking:")
        layout.prop(pose_bones["Camera"].constraints["Track To"],
                    'influence', text="Aim Lock", slider=True)

        if arm["rig_id"].lower() == "crane_rig":
            col = layout.box().column()

            # Crane arm stuff
            col.label(text="Crane Arm:")
            col.prop(pose_bones["Crane_height"],
                     'scale', index=1, text="Arm Height")
            col.prop(pose_bones["Crane_arm"],
                     'scale', index=1, text="Arm Length")


def register():
    bpy.utils.register_class(ADD_CAMERA_RIGS_PT_camera_rig_ui)


def unregister():
    bpy.utils.unregister_class(ADD_CAMERA_RIGS_PT_camera_rig_ui)
