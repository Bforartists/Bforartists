# SPDX-FileCopyrightText: 2016-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Camera Overscan",
    "author": "John Roper, Barnstorm VFX, Luca Scheller, dskjal",
    "version": (1, 4, 2),
    "blender": (3, 1, 0),
    "location": "Render Settings > Camera Overscan",
    "description": "Render Overscan",
    "warning": "",
    "doc_url": "https://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Render/Camera_Overscan",
    "tracker_url": "",
    "category": "Render"}

import bpy
from bpy.types import (
    Panel,
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


class RENDER_OT_co_duplicate_camera(Operator):
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


# Foldable panel
class RenderOutputButtonsPanel:
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "output"

    @classmethod
    def poll(cls, context):
        return (context.engine in cls.COMPAT_ENGINES)


# UI panel
class RENDER_PT_overscan(RenderOutputButtonsPanel, Panel):
    bl_label = "Overscan"
    bl_parent_id = "RENDER_PT_format"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'CYCLES', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}

    def draw_header(self, context):
        overscan = context.scene.camera_overscan
        self.layout.prop(overscan, "activate", text="")

    def draw(self, context):
        scene = context.scene
        overscan = scene.camera_overscan
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation

        active_cam = getattr(scene, "camera", None)

        if active_cam and active_cam.type == 'CAMERA':
            col = layout.column(align=True)
            col.prop(overscan, 'original_res_x', text="Original X")
            col.prop(overscan, 'original_res_y', text="Y")
            col.enabled = False

            col = layout.column(align=True)
            col.prop(overscan, 'custom_res_x', text="New X")
            col.prop(overscan, 'custom_res_y', text="Y")
            col.prop(overscan, 'custom_res_scale', text="%")
            col.enabled = overscan.activate

            col = layout.column(align=True)
            col.prop(overscan, 'custom_res_offset_x', text="dX")
            col.prop(overscan, 'custom_res_offset_y', text="dY")
            col.prop(overscan, 'custom_res_retain_aspect_ratio', text="Retain Aspect Ratio")
            col.enabled = overscan.activate

            col = layout.column()
            col.separator()
            col.operator("scene.co_duplicate_camera", icon="RENDER_STILL")
        else:
            layout.label(text="No active camera in the scene", icon='INFO')


def update(self, context):
    scene = context.scene
    overscan = scene.camera_overscan
    render_settings = scene.render
    active_camera = getattr(scene, "camera", None)
    active_cam = getattr(active_camera, "data", None)

    # Check if there is a camera type in the scene (Object as camera doesn't work)
    if not active_cam or active_camera.type not in {'CAMERA'}:
        return None

    if overscan.activate:
        if overscan.original_sensor_size == -1:
            # Save property values
            overscan.original_res_x = render_settings.resolution_x
            overscan.original_res_y = render_settings.resolution_y
            overscan.original_sensor_size = active_cam.sensor_width
            overscan.original_sensor_fit = active_cam.sensor_fit

        if overscan.custom_res_x == 0 or overscan.custom_res_y == 0:
            # Avoid infinite recursion on props update
            if overscan.custom_res_x != render_settings.resolution_x:
                overscan.custom_res_x = render_settings.resolution_x
            if overscan.custom_res_y != render_settings.resolution_y:
                overscan.custom_res_y = render_settings.resolution_y

        # Reset property values
        active_cam.sensor_width = scene.camera_overscan.original_sensor_size

        # Calc sensor size
        active_cam.sensor_fit = 'HORIZONTAL'
        dx = overscan.custom_res_offset_x
        dy = overscan.custom_res_offset_y
        scale = overscan.custom_res_scale * 0.01
        x = int(overscan.custom_res_x * scale + dx)
        y = int(overscan.custom_res_y * scale + dy)
        sensor_size_factor = float(x / overscan.original_res_x)

        # Set new property values
        active_cam.sensor_width = active_cam.sensor_width * sensor_size_factor
        render_settings.resolution_x = x
        render_settings.resolution_y = y

    else:
        if overscan.original_sensor_size != -1:
            # Restore property values
            render_settings.resolution_x = int(overscan.original_res_x)
            render_settings.resolution_y = int(overscan.original_res_y)
            active_cam.sensor_width = overscan.original_sensor_size
            active_cam.sensor_fit = overscan.original_sensor_fit
            overscan.original_sensor_size = -1


def get_overscan_object(context):
    scene = context.scene
    overscan = scene.camera_overscan
    active_camera = getattr(scene, "camera", None)
    active_cam = getattr(active_camera, "data", None)
    if not active_cam or active_camera.type not in {'CAMERA'} or not overscan.activate:
        return None
    return overscan


def update_x_offset(self, context):
    overscan = get_overscan_object(context)
    if overscan is None:
        return

    if overscan.custom_res_retain_aspect_ratio:
        overscan.activate = False  # Recursion guard
        overscan.custom_res_offset_y = int(overscan.custom_res_offset_x * overscan.original_res_y / overscan.original_res_x)

    overscan.activate = True
    update(self, context)


def update_y_offset(self, context):
    overscan = get_overscan_object(context)
    if overscan is None:
        return None

    if overscan.custom_res_retain_aspect_ratio:
        overscan.activate = False  # Recursion guard
        overscan.custom_res_offset_x = int(overscan.custom_res_offset_y * overscan.original_res_x / overscan.original_res_y)

    overscan.activate = True
    update(self, context)


class CameraOverscanProps(PropertyGroup):
    activate: BoolProperty(
        name="Enable Camera Overscan",
        description="Affects the active Scene Camera only\n"
        "(Objects as cameras are not supported)",
        default=False,
        update=update
    )
    custom_res_x: IntProperty(
        name="Target Resolution X",
        default=0,
        min=0,
        max=65536,
        update=update,
    )
    custom_res_y: IntProperty(
        name="Target Resolution Y",
        default=0,
        min=0,
        max=65536,
        update=update,
    )
    custom_res_scale: FloatProperty(
        name="Resolution Percentage",
        default=100,
        min=0,
        max=1000,
        step=100,
        update=update,
    )
    custom_res_offset_x: IntProperty(
        name="Resolution Offset X",
        default=0,
        min=-65536,
        max=65536,
        update=update_x_offset,
    )
    custom_res_offset_y: IntProperty(
        name="Resolution Offset Y",
        default=0,
        min=-65536,
        max=65536,
        update=update_y_offset,
    )
    custom_res_retain_aspect_ratio: BoolProperty(
        name="Retain Aspect Ratio",
        description="Keep the aspect ratio of the original resolution. Affects dX, dY",
        default=False,
    )

    original_res_x: IntProperty(name="Original Resolution X")
    original_res_y: IntProperty(name="Original Resolution Y")

    # The hard limit is sys.max which is too much, used 65536 instead
    original_sensor_size: FloatProperty(
        default=-1,
        min=-1,
        max=65536
    )
    original_sensor_fit: StringProperty()


def register():
    bpy.utils.register_class(RENDER_OT_co_duplicate_camera)
    bpy.utils.register_class(CameraOverscanProps)
    bpy.utils.register_class(RENDER_PT_overscan)
    bpy.types.Scene.camera_overscan = PointerProperty(
        type=CameraOverscanProps
    )


def unregister():
    bpy.utils.unregister_class(RENDER_PT_overscan)
    bpy.utils.unregister_class(RENDER_OT_co_duplicate_camera)
    bpy.utils.unregister_class(CameraOverscanProps)
    del bpy.types.Scene.camera_overscan


if __name__ == "__main__":
    register()
