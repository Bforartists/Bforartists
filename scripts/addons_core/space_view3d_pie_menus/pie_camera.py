# SPDX-FileCopyrightText: 2016-2024 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Menu, Operator
from .op_pie_wrappers import WM_OT_call_menu_pie_drag_only

# Some magic numbers that are either hard-coded into Blender,
# or are the indirect product of Blender's viewport implementation.
VIEWPORT_SENSOR_WIDTH = 72
VIEWPORT_CAMERA_ZOOM = 29.0746


class PIE_MT_camera(Menu):
    bl_idname = "PIE_MT_camera"
    bl_label = "Camera"

    def draw(self, context):
        pie = self.layout.menu_pie()
        scene = context.scene
        space = context.area.spaces.active
        camera = get_current_camera(context)

        # 4 - LEFT
        if context.space_data.region_3d.view_perspective == 'CAMERA':
            pie.operator("view3d.view_center_camera", icon='PIVOT_BOUNDBOX')
        else:
            pie.operator(
                "view3d.camera_fit_view",
                text="Active Camera to View",
                icon='CON_CAMERASOLVER',
            )
        # 6 - RIGHT
        text = "View Active Camera"
        if context.space_data.region_3d.view_perspective == 'CAMERA':
            text = "Return to Viewport"
        pie.operator(
            'view3d.view_camera_with_poll', text=text, icon='VIEW_CAMERA_UNSELECTED'
        )
        # 2 - BOTTOM
        box = pie.box().column(align=True)
        row = box.row()
        if space.type == 'VIEW_3D' and space.use_local_camera:
            row.prop(space, 'camera', text="Local Cam")
        else:
            row.prop(scene, 'camera', text="Scene Cam")
        if camera:
            box.prop(camera.data, 'lens')
            box.prop(camera.data, 'sensor_width')
            row = box.row(align=True)
            row.prop(camera.data, 'show_passepartout', text="")
            row.prop(camera.data, 'passepartout_alpha')
            row = box.row(align=True)
            row.prop(camera.data, 'show_composition_thirds')
            row.prop(camera.data, 'show_composition_center')
            row.prop(camera.data, 'show_composition_center_diagonal', text="Diagonal")

        # 8 - TOP
        if context.space_data.region_3d.view_perspective == 'CAMERA':
            icon = 'LOCKED' if context.space_data.lock_camera else 'UNLOCKED'
            pie.prop(context.space_data, 'lock_camera', icon=icon)
        else:
            pie.operator("view3d.camera_from_view", icon='ADD')

        # 7 - TOP - LEFT
        word = "Lock"
        icon = 'UNLOCKED'
        if camera and all(camera.lock_rotation) and all(camera.lock_location):
            word = "Unlock"
            icon = 'LOCKED'
        pie.operator(
            'view3d.lock_active_camera_transforms',
            icon=icon,
            text=f"{word} Camera Transforms",
        )
        # 9 - TOP - RIGHT
        pie.operator('view3d.set_active_camera', icon='VIEW_CAMERA')
        # 1 - BOTTOM - LEFT
        # 3 - BOTTOM - RIGHT


class VIEW3D_OT_lock_active_camera_transforms(Operator):
    """Toggle whether the current camera can be transformed"""

    bl_idname = "view3d.lock_active_camera_transforms"
    bl_label = "Lock Camera Transforms"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not get_current_camera(context):
            cls.poll_message_set("No active camera in this viewport.")
            return False
        return True

    def execute(self, context):
        camera = get_current_camera(context)

        lock = False
        if not (all(camera.lock_rotation) and all(camera.lock_location)):
            lock = True

        camera.lock_rotation = [lock, lock, lock]
        camera.lock_rotation_w = lock
        camera.lock_location = [lock, lock, lock]

        word = "Locked" if lock else "Unlocked"
        self.report({'INFO'}, f"{word} {camera.name}.")

        return {'FINISHED'}


class VIEW3D_OT_camera_fit_view(Operator):
    """Align and fit selected or scene camera to view, including lens properties"""

    bl_idname = "view3d.camera_fit_view"
    bl_label = "Snap Camera to View"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not context.space_data or not hasattr(context.space_data, 'region_3d'):
            return False
        if context.space_data.region_3d.view_perspective == 'CAMERA':
            cls.poll_message_set("Already in a camera view.")
            return False
        camera = get_current_camera(context)
        if not camera and not (
            context.active_object and context.active_object.type == 'CAMERA'
        ):
            cls.poll_message_set("No active camera.")
            return False
        if camera and (any(camera.lock_location) or any(camera.lock_rotation)):
            cls.poll_message_set("Active camera's transforms are locked.")
            return False
        return True

    def invoke(self, context, _event):
        if not context.scene.camera and not (
            context.active_object and context.active_object.type == 'CAMERA'
        ):
            self.create_camera = True
        return self.execute(context)

    def execute(self, context):
        cam = get_current_camera(context)

        space = context.space_data
        if cam:
            if space.region_3d.view_perspective == 'ORTHO':
                cam.data.type = 'ORTHO'
            elif space.region_3d.view_perspective == 'PERSP':
                cam.data.type = 'PERSP'

            bpy.ops.view3d.camera_to_view()

            space.region_3d.view_camera_offset = [0, 0]
            space.region_3d.view_camera_zoom = VIEWPORT_CAMERA_ZOOM

            cam.data.sensor_width = VIEWPORT_SENSOR_WIDTH
            cam.data.lens = space.lens
            cam.data.clip_start = space.clip_start
            cam.data.clip_end = space.clip_end

        return {'FINISHED'}


class VIEW3D_OT_camera_from_view(Operator):
    """Create new camera from this view perspective"""

    bl_idname = "view3d.camera_from_view"
    bl_label = "New Camera from View"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.camera_add()
        space = context.area.spaces.active
        if space.type == 'VIEW_3D' and space.use_local_camera:
            space.camera = context.active_object
        else:
            context.scene.camera = context.active_object
        return bpy.ops.view3d.camera_fit_view()


class VIEW3D_OT_set_active_camera(Operator):
    """Set active camera as the scene camera"""

    bl_idname = "view3d.set_active_camera"
    bl_label = "Set Active Camera"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not context.active_object:
            cls.poll_message_set("No active object.")
            return False
        if context.active_object.type != 'CAMERA':
            cls.poll_message_set("Active object must be a camera.")
            return False
        if context.active_object == context.scene.camera:
            cls.poll_message_set("This is already the active camera.")
            return False
        return True

    def execute(self, context):
        context.scene.camera = context.active_object
        self.report({'INFO'}, f"Set active camera: {context.active_object.name}")
        return {'FINISHED'}


class VIEW3D_OT_view_camera_with_poll(Operator):
    """Toggle viewing the active camera"""

    bl_idname = "view3d.view_camera_with_poll"
    bl_label = "View Active Camera"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not get_current_camera(context):
            cls.poll_message_set("No active camera.")
            return False
        return True

    def execute(self, context):
        return bpy.ops.view3d.view_camera()


def get_current_camera(context):
    space = context.area.spaces.active
    if space.type == 'VIEW_3D' and space.use_local_camera:
        return space.camera
    return context.scene.camera


registry = [
    PIE_MT_camera,
    VIEW3D_OT_lock_active_camera_transforms,
    VIEW3D_OT_camera_fit_view,
    VIEW3D_OT_camera_from_view,
    VIEW3D_OT_set_active_camera,
    VIEW3D_OT_view_camera_with_poll,
]


def register():
    WM_OT_call_menu_pie_drag_only.register_drag_hotkey(
        keymap_name="3D View",
        pie_name=PIE_MT_camera.bl_idname,
        hotkey_kwargs={'type': "C", 'value': "PRESS", 'alt': True},
        on_drag=False,
    )
