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

from .operators import get_rig_and_cam, CameraRigMixin


class ADD_CAMERA_RIGS_PT_camera_rig_ui(Panel, CameraRigMixin):
    bl_label = "Camera Rig"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Item'

    def draw(self, context):
        active_object = context.active_object
        rig, cam = get_rig_and_cam(context.active_object)
        pose_bones = rig.pose.bones
        cam_data = cam.data
        layout = self.layout

        # Camera lens
        if rig["rig_id"].lower() in ("dolly_rig", "crane_rig"):
            layout.prop(pose_bones["Camera"], '["lens"]',
                        text="Focal Length (mm)")

        col = layout.column(align=True)
        col.label(text="Clipping:")
        col.prop(cam_data, "clip_start", text="Start")
        col.prop(cam_data, "clip_end", text="End")

        layout.prop(cam_data, "type")

        # DoF
        col = layout.column(align=True)
        col.prop(cam_data.dof, "use_dof")
        if cam_data.dof.use_dof:
            if rig["rig_id"].lower() in ("crane_rig", "dolly_rig"):
                if cam_data.dof.focus_object is None:
                    col.operator("add_camera_rigs.add_dof_object",
                                 text="Add DOF Empty", icon="OUTLINER_OB_EMPTY")
            else:
                col.prop(cam_data.dof, "focus_object")
            row = col.row(align=True)
            row.active = cam_data.dof.focus_object is None
            row.prop(pose_bones["Camera"],
                     '["focus_distance"]', text="Focus Distance")
            col.prop(pose_bones["Camera"],
                     '["aperture_fstop"]', text="F-Stop")

        # Viewport display
        layout.prop(active_object, 'show_in_front',
                    toggle=False, text='Show in Front')
        layout.prop(cam_data, "show_limits")
        col = layout.column(align=True)
        col.prop(cam_data, "show_passepartout")
        if cam_data.show_passepartout:
            col.prop(cam_data, "passepartout_alpha")

        # Composition guides
        layout.popover(
            panel="ADD_CAMERA_RIGS_PT_composition_guides",
            text="Composition Guides",)

        # Props and operators
        col = layout.column(align=True)
        col.prop(cam,
                    "hide_select", text="Make Camera Unselectable")
        col.operator("add_camera_rigs.add_marker_bind",
                     text="Add Marker and Bind", icon="MARKER_HLT")
        col.operator("add_camera_rigs.set_scene_camera",
                     text="Make Camera Active", icon='CAMERA_DATA')

        if rig["rig_id"].lower() in ("dolly_rig", "crane_rig"):
            # Track to Constraint
            col = layout.column(align=True)
            col.label(text="Tracking:")
            col.prop(pose_bones["Camera"].constraints["Track To"],
                     'influence', text="Aim Lock", slider=True)

            # Crane arm stuff
            if rig["rig_id"].lower() == "crane_rig":
                col = layout.column(align=True)
                col.label(text="Crane Arm:")
                col.prop(pose_bones["Crane_height"],
                         'scale', index=1, text="Arm Height")
                col.prop(pose_bones["Crane_arm"],
                         'scale', index=1, text="Arm Length")

        # 2D rig stuff
        elif rig["rig_id"].lower() == "2d_rig":
            col = layout.column(align=True)
            col.label(text="2D Rig:")
            col.prop(pose_bones["Camera"], '["rotation_shift"]',
                     text="Rotation/Shift")
            if cam.data.sensor_width != 36:
                col.label(text="Please set Camera Sensor Width to 36", icon="ERROR")


def register():
    bpy.utils.register_class(ADD_CAMERA_RIGS_PT_camera_rig_ui)


def unregister():
    bpy.utils.unregister_class(ADD_CAMERA_RIGS_PT_camera_rig_ui)
