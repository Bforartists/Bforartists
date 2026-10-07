# SPDX-FileCopyrightText: 2019 Wayne Dixon
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
import mathutils
from bpy.types import Operator


def get_lens_driver_without_breathing(rig, cam):
    """Backwards compatible access to camera lens driver."""
    driver = None
    if rig.animation_data is not None:
        driver = next((
            fcurve.driver
            for fcurve in rig.animation_data.drivers
            if 'lens_without_breathing' in fcurve.data_path
        ), None)

    if driver is None:  # lens breathing not supported
        driver = next((
            fcurve.driver
            for fcurve in cam.data.animation_data.drivers
            if 'lens' in fcurve.data_path
        ), None)

    return driver


def get_lens_without_breathing(rig, cam):
    """Backwards compatible access to camera lens value."""
    lens_value = None
    if rig.animation_data is not None:
        fcurve = next((
            fcurve
            for fcurve in rig.animation_data.drivers
            if 'lens_without_breathing' in fcurve.data_path
        ), None)
        if fcurve is not None:
            lens_value = rig.pose.bones["Camera"]["lens_without_breathing"]
    
    if lens_value is None:  # lens breathing not supported
        lens_value = cam.data.lens

    return lens_value


def get_lens_expr(dolly_distance=None):
    return (
        '((distance * (lens + lens_offset) / %s ) / root_scale)' % dolly_distance
        if dolly_distance is not None
        else 'lens'
    )


def get_rig_and_cam(obj):
    if (obj.type == 'ARMATURE'
            and "rig_id" in obj
            and obj["rig_id"].lower() in {"dolly_rig",
                                          "crane_rig", "2d_rig"}):
        cam = None
        for child in obj.children:
            if child.type == 'CAMERA':
                cam = child
                break
        if cam is not None:
            return obj, cam
    elif (obj.type == 'CAMERA'
          and obj.parent is not None
          and "rig_id" in obj.parent
          and obj.parent["rig_id"].lower() in {"dolly_rig",
                                               "crane_rig", "2d_rig"}):
        return obj.parent, obj
    return None, None


def calculate_aim_distance(obj):
    '''This will return the distance of the camera and the aim bone at the time it is called.'''
    camera_bone = obj.pose.bones['Camera'].matrix
    aim_bone = obj.pose.bones['Aim'].matrix
    length = (camera_bone - aim_bone).to_translation().length
    return length


def poll_base(cls, context):
    if context.active_object is None:
        if hasattr(cls, "poll_message_set"):
            cls.poll_message_set("No object is selected.")
        return False
    if None in get_rig_and_cam(context.active_object):
        if hasattr(cls, "poll_message_set"):
            cls.poll_message_set("Active object is not in a camera rig.")
        return False
    return True


def poll_perspective(cls, context):
    if not poll_base(cls, context):
        return False

    rig, cam = get_rig_and_cam(context.active_object)
    if cam.data.type == 'ORTHO':
        cls.poll_message_set(
            "This operator is not supported for orthographic cameras.")
        return False
    if rig["rig_id"].lower() == '2d_rig':
        cls.poll_message_set(
            "This operator is not supported for 2D camera rigs.")
        return False
    return True


class ADD_CAMERA_RIGS_OT_set_scene_camera(Operator):
    bl_idname = "add_camera_rigs.set_scene_camera"
    bl_label = "Make Camera Active"
    bl_description = "Makes the camera parented to this rig the active scene camera"

    @classmethod
    def poll(cls, context):
        if not poll_base(cls, context):
            return False

        _rig, cam = get_rig_and_cam(context.active_object)
        if cam is context.scene.camera:
            cls.poll_message_set(
                "Selected camera is already the scene camera.")
            return False
        return True

    def execute(self, context):
        rig, cam = get_rig_and_cam(context.active_object)

        context.scene.camera = cam
        return {'FINISHED'}


class ADD_CAMERA_RIGS_OT_add_marker_bind(Operator):
    bl_idname = "add_camera_rigs.add_marker_bind"
    bl_label = "Add Marker and Bind Camera"
    bl_description = "Add marker to current frame then bind rig camera to it (for camera switching)"

    @classmethod
    def poll(cls, context):
        return poll_base(cls, context)

    def execute(self, context):
        rig, cam = get_rig_and_cam(context.active_object)

        marker = context.scene.timeline_markers.new(
            "cam_" + str(context.scene.frame_current),
            frame=context.scene.frame_current
        )
        marker.camera = cam

        return {'FINISHED'}


class ADD_CAMERA_RIGS_OT_set_dof_bone(Operator):
    bl_idname = "add_camera_rigs.set_dof_bone"
    bl_label = "Set DOF to Aim"
    bl_description = "Set the Aim bone as a DOF target"

    @classmethod
    def poll(cls, context):
        return poll_base(cls, context)

    def execute(self, context):
        rig, cam = get_rig_and_cam(context.active_object)

        if hasattr(rig.pose.bones["Camera"], '["lens_without_breathing"]'):
            # use acr prop variables to trigger DOF update
            rig.acr_focus_object = rig.name
            rig.acr_focus_subtarget = (
                'DOF' if rig["rig_id"].lower() == '2d_rig'
                else 'Aim')
        else:  # old rig, set focus directly
            cam.data.dof.focus_object = rig
            cam.data.dof.focus_subtarget = (
                'DOF' if rig["rig_id"].lower() == '2d_rig'
                else 'Aim')


        return {'FINISHED'}


class ADD_CAMERA_RIGS_OT_set_dolly_zoom(Operator):
    bl_idname = "add_camera_rigs.set_dolly_zoom"
    bl_label = "Set Dolly Zoom"
    bl_description = "Use the aim bone as a focal length (Dolly Zoom effect)"

    @classmethod
    def poll(cls, context):
        return poll_perspective(cls, context)

    def execute(self, context):
        rig, cam = get_rig_and_cam(context.active_object)

        value = calculate_aim_distance(rig)
        drv = get_lens_driver_without_breathing(rig, cam)
        drv.expression = get_lens_expr(dolly_distance=value)

        # set the bone color to default
        rig.pose.bones["Aim"].color.palette = 'THEME01'

        return {'FINISHED'}


class ADD_CAMERA_RIGS_OT_remove_dolly_zoom(Operator):
    bl_idname = "add_camera_rigs.remove_dolly_zoom"
    bl_label = "Remove Dolly Zoom"
    bl_description = "Disconnect the aim bone as a focal length (Dolly Zoom effect)"

    @classmethod
    def poll(cls, context):
        return poll_perspective(cls, context)

    def execute(self, context):
        rig, cam = get_rig_and_cam(context.active_object)

        drv = get_lens_driver_without_breathing(rig, cam)
        lens_value = get_lens_without_breathing(rig, cam)

        drv.expression = get_lens_expr()
        rig.pose.bones["Camera"]["lens"] = lens_value

        # reset the offset back to zero
        rig.pose.bones["Camera"]["lens_offset"] = 0.0

        # set the bone color to default
        rig.pose.bones["Aim"].color.palette = 'DEFAULT'

        return {'FINISHED'}


class ADD_CAMERA_RIGS_OT_shift_to_pivot(Operator):
    bl_idname = "add_camera_rigs.shift_to_pivot"
    bl_label = "Shift To Pivot"
    bl_description = "Offset the Camera and Aim such that the Aim bone is above the Root control"

    @classmethod
    def poll(cls, context):
        return poll_base(cls, context)

    def execute(self, context):
        rig, cam = get_rig_and_cam(context.active_object)

        # get the local matrix of the aim bone
        aim_loc = rig.pose.bones["Aim"].matrix_basis.to_translation()

        # create a transform matrix for the z loc of the aim bone
        mat_trans = mathutils.Matrix.Translation(
            [0, 0, aim_loc[2] + 1.7])  # Hardcoded height of rest position
        # repostion the aim bone so it's above the root (using the original z value)
        rig.pose.bones["Aim"].matrix = rig.pose.bones["Root"].matrix @ mat_trans

        # offset the camera matrix relative to the new aim position
        camera_offset_vector = (
            rig.pose.bones["Aim"].matrix_basis.to_translation()) - aim_loc
        camera_offset_matrix = mathutils.Matrix.Translation(
            camera_offset_vector)
        rig.pose.bones["Camera"].matrix = rig.pose.bones["Camera"].matrix @ camera_offset_matrix
        return {'FINISHED'}


class ADD_CAMERA_RIGS_OT_swap_lens(Operator):
    bl_idname = "add_camera_rigs.swap_lens"
    bl_label = "Swap Lens"
    bl_description = "Set the focal length to a specific value and shift the camera to match the same framing"
    bl_options = {'REGISTER', 'UNDO'}

    camera_lens: bpy.props.FloatProperty(
        name="Focal Length (mm)",
        default=50,
        min=1,
        max=1000,
        subtype='DISTANCE_CAMERA',
        description="The value of the new focal length",
    )

    @classmethod
    def poll(cls, context):
        return poll_perspective(cls, context)

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text="Focal Length:")
        row.prop(self, "camera_lens", text="")
        row = layout.row()

    def invoke(self, context, event):
        rig, _cam = get_rig_and_cam(context.active_object)
        self.camera_lens = rig.pose.bones["Camera"]["lens"]

        return context.window_manager.invoke_props_popup(self, event)

    def execute(self, context):
        rig, cam = get_rig_and_cam(context.active_object)

        # get the vector from aim to camera bone
        vector = (rig.pose.bones["Aim"].matrix.to_translation()
                  - rig.pose.bones["Camera"].matrix.to_translation())

        old_lens = rig.pose.bones["Camera"]["lens"]
        new_lens = self.camera_lens

        # set the new camera lens
        rig.pose.bones["Camera"]["lens"] = new_lens

        # set the new camera position, by offsetting it
        # towards the aim bone proportionally to the lens change
        loc = rig.pose.bones["Camera"].matrix.translation
        loc += vector * (1.0 - new_lens / old_lens)

        return {'FINISHED'}


classes = (
    ADD_CAMERA_RIGS_OT_set_scene_camera,
    ADD_CAMERA_RIGS_OT_add_marker_bind,
    ADD_CAMERA_RIGS_OT_set_dof_bone,
    ADD_CAMERA_RIGS_OT_set_dolly_zoom,
    ADD_CAMERA_RIGS_OT_remove_dolly_zoom,
    ADD_CAMERA_RIGS_OT_shift_to_pivot,
    ADD_CAMERA_RIGS_OT_swap_lens,
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)
