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

bl_info = {
    "name": "Camera Overscan",
    "author": "John Roper, Barnstorm VFX, Luca Scheller",
    "version": (1, 2, 1),
    "blender": (2, 76, 0),
    "location": "Render Settings > Camera Overscan",
    "description": "Render Overscan",
    "warning": "",
    "wiki_url": "https://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Render/Camera_Overscan",
    "tracker_url": "",
    "category": "Render"}

import bpy
from bpy.types import (
        Operator,
        PropertyGroup,
        )
from bpy.props import (
        BoolProperty,
        IntProperty,
        FloatProperty,
        StringProperty,
        PointerProperty,
        )


class CODuplicateCamera(Operator):
    bl_idname = "scene.co_duplicate_camera"
    bl_label = "Bake to New Camera"
    bl_description = ("Make a new overscan camera with all the settings builtin\n"
                      "Needs an active Camera type in the Scene")

    @classmethod
    def poll(cls, context):
        active_cam = getattr(context.scene, "camera", None)
        return active_cam is not None

    def execute(self, context):
        active_cam = getattr(context.scene, "camera", None)
        try:
            if active_cam and active_cam.type == 'CAMERA':
                cam_obj = active_cam.copy()
                cam_obj.data = active_cam.data.copy()
                cam_obj.name = "Camera_Overscan"
                context.collection.objects.link(cam_obj)
        except:
            self.report({'WARNING'}, "Setting up a new Overscan Camera has failed")
            return {'CANCELLED'}

        return {'FINISHED'}


def RO_Update(self, context):
    scene = context.scene
    overscan = scene.camera_overscan
    render_settings = scene.render
    active_camera = getattr(scene, "camera", None)
    active_cam = getattr(active_camera, "data", None)

    # Check if there is a camera type in the scene (Object as camera doesn't work)
    if not active_cam or active_camera.type not in {'CAMERA'}:
        return None

    if overscan.RO_Activate:
        if overscan.RO_Safe_SensorSize == -1:
            # Safe Property Values
            overscan.RO_Safe_Res_X = render_settings.resolution_x
            overscan.RO_Safe_Res_Y = render_settings.resolution_y
            overscan.RO_Safe_SensorSize = active_cam.sensor_width
            overscan.RO_Safe_SensorFit = active_cam.sensor_fit

        if overscan.RO_Custom_Res_X == 0 or overscan.RO_Custom_Res_Y == 0:
            # avoid infinite recursion on props update
            if overscan.RO_Custom_Res_X != render_settings.resolution_x:
                overscan.RO_Custom_Res_X = render_settings.resolution_x
            if overscan.RO_Custom_Res_Y != render_settings.resolution_y:
                overscan.RO_Custom_Res_Y = render_settings.resolution_y

        # Reset Property Values
        active_cam.sensor_width = scene.camera_overscan.RO_Safe_SensorSize

        # Calc Sensor Size
        active_cam.sensor_fit = 'HORIZONTAL'
        sensor_size_factor = overscan.RO_Custom_Res_X / overscan.RO_Safe_Res_X
        Old_SensorSize = active_cam.sensor_width
        New_SensorSize = Old_SensorSize * sensor_size_factor

        # Set New Property Values
        active_cam.sensor_width = New_SensorSize
        render_settings.resolution_x = overscan.RO_Custom_Res_X
        render_settings.resolution_y = overscan.RO_Custom_Res_Y

    else:
        if overscan.RO_Safe_SensorSize != -1:
            # Set Property Values
            render_settings.resolution_x = overscan.RO_Safe_Res_X
            render_settings.resolution_y = overscan.RO_Safe_Res_Y
            active_cam.sensor_width = overscan.RO_Safe_SensorSize
            active_cam.sensor_fit = overscan.RO_Safe_SensorFit
            overscan.RO_Safe_SensorSize = -1


def RO_Menu(self, context):
    scene = context.scene
    overscan = scene.camera_overscan
    layout = self.layout
    row = layout.row()
    active_cam = getattr(scene, "camera", None)

    if active_cam and active_cam.type == 'CAMERA':
        row.prop(overscan, 'RO_Activate', text="Use Overscan")
        row_enable = row.row(align=True)
        if not overscan.RO_Activate:
            row_enable.enabled = False
        row_enable.prop(overscan, 'RO_Custom_Res_X', text="X")
        row_enable.prop(overscan, 'RO_Custom_Res_Y', text="Y")
        row = layout.row()
        if not overscan.RO_Activate:
            row.enabled = False
        row.operator("scene.co_duplicate_camera", icon="RENDER_STILL")
    else:
        row.label(text="No active Camera type in the Scene", icon='INFO')


class camera_overscan_props(PropertyGroup):
    RO_Activate: BoolProperty(
                        default=False,
                        description="Enable/Disable Camera Overscan\n"
                                    "Affects the active Scene Camera only\n"
                                    "(Objects as cameras are not supported)",
                        update=RO_Update
                        )
    RO_Custom_Res_X: IntProperty(
                        default=0,
                        min=0,
                        max=65536,
                        update=RO_Update
                        )
    RO_Custom_Res_Y: IntProperty(
                        default=0,
                        min=0,
                        max=65536,
                        update=RO_Update
                        )
    RO_Safe_Res_X: FloatProperty()
    RO_Safe_Res_Y: FloatProperty()

    # the hard limit is sys.max which is too much, used 65536 instead
    RO_Safe_SensorSize: FloatProperty(
                        default=-1,
                        min=-1,
                        max=65536
                        )
    RO_Safe_SensorFit: StringProperty()


def register():
    bpy.utils.register_module(__name__)
    bpy.types.RENDER_PT_dimensions.append(RO_Menu)
    bpy.types.Scene.camera_overscan = PointerProperty(
                                        type=camera_overscan_props
                                        )


def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.RENDER_PT_dimensions.remove(RO_Menu)
    del bpy.types.Scene.camera_overscan


if __name__ == "__main__":
    register()
