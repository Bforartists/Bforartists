# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import Operator
from bpy_extras import object_utils
from mathutils import Vector
from math import pi

from .create_widgets import (create_root_widget,
                             create_camera_widget, create_camera_offset_widget,
                             create_aim_widget, create_circle_widget,
                             create_corner_widget)


def create_prop_driver(rig, cam, prop_from, prop_to):
    """Create driver to a property on the rig"""
    driver = cam.data.driver_add(prop_to)
    driver.driver.type = 'SCRIPTED'
    var = driver.driver.variables.new()
    var.name = 'var'
    var.type = 'SINGLE_PROP'

    # Target the custom bone property
    var.targets[0].id = rig
    var.targets[0].data_path = 'pose.bones["Camera"]["%s"]' % prop_from
    driver.driver.expression = 'var'


def create_dolly_bones(rig):
    """Create bones for the dolly camera rig"""
    bones = rig.data.edit_bones

    # Add new bones
    root = bones.new("Root")
    root.tail = (0.0, 1.0, 0.0)
    root.show_wire = True
    rig.data.collections.new(name="Controls")
    rig.data.collections['Controls'].assign(root)

    ctrl_aim_child = bones.new("MCH-Aim_shape_rotation")
    ctrl_aim_child.head = (0.0, 10.0, 1.7)
    ctrl_aim_child.tail = (0.0, 11.0, 1.7)
    # Create bone collection and assign bone
    rig.data.collections.new(name="MCH")
    rig.data.collections['MCH'].assign(ctrl_aim_child)
    rig.data.collections['MCH'].is_visible = False

    ctrl_aim = bones.new("Aim")
    ctrl_aim.head = (0.0, 10.0, 1.7)
    ctrl_aim.tail = (0.0, 11.0, 1.7)
    ctrl_aim.show_wire = True
    rig.data.collections['Controls'].assign(ctrl_aim)

    ctrl = bones.new("Camera")
    ctrl.head = (0.0, 0.0, 1.7)
    ctrl.tail = (0.0, 1.0, 1.7)
    ctrl.show_wire = True
    rig.data.collections['Controls'].assign(ctrl)

    ctrl_offset = bones.new("Camera_Offset")
    ctrl_offset.head = (0.0, 0.0, 1.7)
    ctrl_offset.tail = (0.0, 1.0, 1.7)
    ctrl_offset.show_wire = True
    rig.data.collections['Controls'].assign(ctrl_offset)


    # Setup hierarchy
    ctrl.parent = root
    ctrl_offset.parent = ctrl
    ctrl_aim.parent = root
    ctrl_aim_child.parent = ctrl_aim

    # Jump into object mode
    bpy.ops.object.mode_set(mode='OBJECT')
    pose_bones = rig.pose.bones
    # Lock the relevant scale channels of the Camera_offset bone
    pose_bones["Camera_Offset"].lock_scale = (True,) * 3


def create_crane_bones(rig):
    """Create bones for the crane camera rig"""
    bones = rig.data.edit_bones

    # Add new bones
    root = bones.new("Root")
    root.tail = (0.0, 1.0, 0.0)
    root.show_wire = True
    rig.data.collections.new(name="Controls")
    rig.data.collections['Controls'].assign(root)

    ctrl_aim_child = bones.new("MCH-Aim_shape_rotation")
    ctrl_aim_child.head = (0.0, 10.0, 1.7)
    ctrl_aim_child.tail = (0.0, 11.0, 1.7)
    rig.data.collections.new(name="MCH")
    rig.data.collections['MCH'].assign(ctrl_aim_child)
    rig.data.collections['MCH'].is_visible = False

    ctrl_aim = bones.new("Aim")
    ctrl_aim.head = (0.0, 10.0, 1.7)
    ctrl_aim.tail = (0.0, 11.0, 1.7)
    ctrl_aim.show_wire = True
    rig.data.collections['Controls'].assign(ctrl_aim)

    ctrl = bones.new("Camera")
    ctrl.head = (0.0, 1.0, 1.7)
    ctrl.tail = (0.0, 2.0, 1.7)
    rig.data.collections['Controls'].assign(ctrl)

    ctrl_offset = bones.new("Camera_Offset")
    ctrl_offset.head = (0.0, 1.0, 1.7)
    ctrl_offset.tail = (0.0, 2.0, 1.7)
    rig.data.collections['Controls'].assign(ctrl_offset)

    arm = bones.new("Crane_Arm")
    arm.head = (0.0, 0.0, 1.7)
    arm.tail = (0.0, 1.0, 1.7)
    rig.data.collections['Controls'].assign(arm)

    height = bones.new("Crane_Height")
    height.head = (0.0, 0.0, 0.0)
    height.tail = (0.0, 0.0, 1.7)
    rig.data.collections['Controls'].assign(height)

    # Setup hierarchy
    ctrl.parent = arm
    ctrl_offset.parent = ctrl
    ctrl.use_inherit_rotation = False
    ctrl.inherit_scale = "NONE"
    ctrl.show_wire = True

    arm.parent = height
    arm.inherit_scale = "NONE"

    height.parent = root
    ctrl_aim.parent = root
    ctrl_aim_child.parent = ctrl_aim

    # Jump into object mode
    bpy.ops.object.mode_set(mode='OBJECT')
    pose_bones = rig.pose.bones

    # Lock the relevant loc, rot and scale
    pose_bones["Crane_Arm"].lock_rotation = (False, True, False)
    pose_bones["Crane_Arm"].lock_scale = (True, False, True)
    pose_bones["Crane_Height"].lock_location = (True,) * 3
    pose_bones["Crane_Height"].lock_rotation = (True,) * 3
    pose_bones["Crane_Height"].lock_scale = (True, False, True)
    pose_bones["Camera_Offset"].lock_scale = (True,) * 3


def setup_3d_rig(rig, cam):
    """Finish setting up Dolly and Crane rigs"""
    # Jump into object mode and change bones to euler
    bpy.ops.object.mode_set(mode='OBJECT')
    pose_bones = rig.pose.bones
    for bone in pose_bones:
        bone.rotation_mode = 'XYZ'

    # Lens property
    pb = pose_bones['Camera']
    pb["lens"] = 50.0
    ui_data = pb.id_properties_ui("lens")
    ui_data.update(min=1.0, max=1000000.0, soft_max = 5000.0, default=50.0)

    # Build the widgets
    root_widget = create_root_widget("Camera_Root")
    camera_widget = create_camera_widget("Camera")
    camera_offset_widget = create_camera_offset_widget("Camera_Offset")
    aim_widget = create_aim_widget("Aim")

    # Add the custom bone shapes
    pose_bones["Root"].custom_shape = root_widget
    pose_bones["Aim"].custom_shape = aim_widget
    pose_bones["Camera"].custom_shape = camera_widget
    pose_bones["Camera_Offset"].custom_shape = camera_offset_widget

    # Set the "Override Transform" field to the mechanism position
    pose_bones["Aim"].custom_shape_transform = pose_bones["MCH-Aim_shape_rotation"]

    # Add constraints to bones
    con = pose_bones['MCH-Aim_shape_rotation'].constraints.new('COPY_ROTATION')
    con.target = rig
    con.subtarget = "Camera"

    con = pose_bones['Camera'].constraints.new('TRACK_TO')
    con.track_axis = 'TRACK_Y'
    con.up_axis = 'UP_Z'
    con.target = rig
    con.subtarget = "Aim"
    con.use_target_z = True

    cam.data.display_size = 1.0
    cam.rotation_euler[0] = pi / 2.0  # Rotate the camera 90 degrees in x

    create_prop_driver(rig, cam, "lens", "lens")


def create_2d_bones(context, rig, cam):
    """Create bones for the 2D camera rig"""
    scene = context.scene
    bones = rig.data.edit_bones

    # Add new bones
    bones = rig.data.edit_bones
    root = bones.new("Root")
    root.tail = Vector((0.0, 0.0, 1.0))
    root.show_wire = True
    rig.data.collections.new(name="Controls")
    rig.data.collections['Controls'].assign(root)

    ctrl = bones.new('Camera')
    ctrl.tail = Vector((0.0, 0.0, 1.0))
    ctrl.show_wire = True
    rig.data.collections['Controls'].assign(ctrl)

    left_corner = bones.new("Left_Corner")
    left_corner.head = (-3, 10, -2)
    left_corner.tail = left_corner.head + Vector((0.0, 0.0, 1.0))
    left_corner.show_wire = True
    rig.data.collections['Controls'].assign(left_corner)

    right_corner = bones.new("Right_Corner")
    right_corner.head = (3, 10, -2)
    right_corner.tail = right_corner.head + Vector((0.0, 0.0, 1.0))
    right_corner.show_wire = True
    rig.data.collections['Controls'].assign(right_corner)

    corner_distance_x = (left_corner.head - right_corner.head).length
    corner_distance_y = -left_corner.head.z
    corner_distance_z = left_corner.head.y
    rig.data.collections['Controls'].assign(root)

    center = bones.new("MCH-Center")
    center.head = ((right_corner.head + left_corner.head) / 2.0)
    center.tail = center.head + Vector((0.0, 0.0, 1.0))
    center.show_wire = True
    rig.data.collections.new(name="MCH")
    rig.data.collections['MCH'].assign(center)
    rig.data.collections['MCH'].is_visible = False
    center.show_wire = True

    # Setup hierarchy
    ctrl.parent = root
    left_corner.parent = root
    right_corner.parent = root
    center.parent = root

    # Jump into object mode and change bones to euler
    bpy.ops.object.mode_set(mode='OBJECT')
    pose_bones = rig.pose.bones
    for bone in pose_bones:
        bone.rotation_mode = 'XYZ'

    # Bone drivers
    center_drivers = pose_bones["MCH-Center"].driver_add("location")

    # Center X driver
    driver = center_drivers[0].driver
    driver.type = 'AVERAGE'

    for corner in ('left', 'right'):
        var = driver.variables.new()
        var.name = corner
        var.type = 'TRANSFORMS'
        var.targets[0].id = rig
        var.targets[0].bone_target = corner.capitalize() + '_Corner'
        var.targets[0].transform_type = 'LOC_X'
        var.targets[0].transform_space = 'TRANSFORM_SPACE'

    # Center Y driver
    driver = center_drivers[1].driver
    driver.type = 'SCRIPTED'

    driver.expression = '({distance_x} - (left_x-right_x))*(res_y/res_x)/2 + (left_y + right_y)/2'.format(
        distance_x=corner_distance_x)

    for direction in ('x', 'y'):
        for corner in ('left', 'right'):
            var = driver.variables.new()
            var.name = '%s_%s' % (corner, direction)
            var.type = 'TRANSFORMS'
            var.targets[0].id = rig
            var.targets[0].bone_target = corner.capitalize() + '_Corner'
            var.targets[0].transform_type = 'LOC_' + direction.upper()
            var.targets[0].transform_space = 'TRANSFORM_SPACE'

        var = driver.variables.new()
        var.name = 'res_' + direction
        var.type = 'SINGLE_PROP'
        var.targets[0].id_type = 'SCENE'
        var.targets[0].id = scene
        var.targets[0].data_path = 'render.resolution_' + direction

    # Center Z driver
    driver = center_drivers[2].driver
    driver.type = 'AVERAGE'

    for corner in ('left', 'right'):
        var = driver.variables.new()
        var.name = corner
        var.type = 'TRANSFORMS'
        var.targets[0].id = rig
        var.targets[0].bone_target = corner.capitalize() + '_Corner'
        var.targets[0].transform_type = 'LOC_Z'
        var.targets[0].transform_space = 'TRANSFORM_SPACE'

    # Bone constraints
    con = pose_bones["Camera"].constraints.new('DAMPED_TRACK')
    con.target = rig
    con.subtarget = "MCH-Center"
    con.track_axis = 'TRACK_NEGATIVE_Z'

    # Build the widgets
    left_widget = create_corner_widget("Left_Corner", reverse=True)
    right_widget = create_corner_widget("Right_Corner")
    parent_widget = create_circle_widget("Root", radius=0.5)
    camera_widget = create_circle_widget("Camera_2D", radius=0.3)

    # Add the custom bone shapes
    pose_bones["Left_Corner"].custom_shape = left_widget
    pose_bones["Right_Corner"].custom_shape = right_widget
    pose_bones["Root"].custom_shape = parent_widget
    pose_bones["Camera"].custom_shape = camera_widget

    # Lock the relevant loc, rot and scale
    pose_bones["Left_Corner"].lock_rotation = (True,) * 3
    pose_bones["Right_Corner"].lock_rotation = (True,) * 3
    pose_bones["Camera"].lock_rotation = (True,) * 3
    pose_bones["Camera"].lock_scale = (True,) * 3

    # Camera settings

    cam.data.sensor_fit = "HORIZONTAL"  # Avoids distortion in portrait format

    # Property to switch between rotation and switch mode
    pose_bones["Camera"]['rotation_shift'] = 0.0
    ui_data = pose_bones["Camera"].id_properties_ui('rotation_shift')
    ui_data.update(min=0.0, max=1.0, description="rotation_shift")

    # Rotation / shift switch driver
    driver = con.driver_add('influence').driver
    driver.expression = '1 - rotation_shift'

    var = driver.variables.new()
    var.name = 'rotation_shift'
    var.type = 'SINGLE_PROP'
    var.targets[0].id = rig
    var.targets[0].data_path = 'pose.bones["Camera"]["rotation_shift"]'

    # Focal length driver
    driver = cam.data.driver_add('lens').driver
    driver.expression = 'abs({distance_z} - (left_z + right_z)/2 + cam_z) * 36 / frame_width'.format(
        distance_z=corner_distance_z)

    var = driver.variables.new()
    var.name = 'frame_width'
    var.type = 'LOC_DIFF'
    var.targets[0].id = rig
    var.targets[0].bone_target = "Left_Corner"
    var.targets[0].transform_space = 'WORLD_SPACE'
    var.targets[1].id = rig
    var.targets[1].bone_target = "Right_Corner"
    var.targets[1].transform_space = 'WORLD_SPACE'

    for corner in ('left', 'right'):
        var = driver.variables.new()
        var.name = corner + '_z'
        var.type = 'TRANSFORMS'
        var.targets[0].id = rig
        var.targets[0].bone_target = corner.capitalize() + '_Corner'
        var.targets[0].transform_type = 'LOC_Z'
        var.targets[0].transform_space = 'TRANSFORM_SPACE'

    var = driver.variables.new()
    var.name = 'cam_z'
    var.type = 'TRANSFORMS'
    var.targets[0].id = rig
    var.targets[0].bone_target = "Camera"
    var.targets[0].transform_type = 'LOC_Z'
    var.targets[0].transform_space = 'TRANSFORM_SPACE'

    # Orthographic scale driver
    driver = cam.data.driver_add('ortho_scale').driver
    driver.expression = 'abs({distance_x} - (left_x - right_x))'.format(distance_x=corner_distance_x)

    for corner in ('left', 'right'):
        var = driver.variables.new()
        var.name = corner + '_x'
        var.type = 'TRANSFORMS'
        var.targets[0].id = rig
        var.targets[0].bone_target = corner.capitalize() + '_Corner'
        var.targets[0].transform_type = 'LOC_X'
        var.targets[0].transform_space = 'TRANSFORM_SPACE'

    # Shift driver X
    driver = cam.data.driver_add('shift_x').driver

    driver.expression = 'rotation_shift * (((left_x + right_x)/2 - cam_x) * lens / abs({distance_z} - (left_z + right_z)/2 + cam_z) / 36)'.format(
        distance_z=corner_distance_z)

    var = driver.variables.new()
    var.name = 'rotation_shift'
    var.type = 'SINGLE_PROP'
    var.targets[0].id = rig
    var.targets[0].data_path = 'pose.bones["Camera"]["rotation_shift"]'

    for direction in ('x', 'z'):
        for corner in ('left', 'right'):
            var = driver.variables.new()
            var.name = '%s_%s' % (corner, direction)
            var.type = 'TRANSFORMS'
            var.targets[0].id = rig
            var.targets[0].bone_target = corner.capitalize() + '_Corner'
            var.targets[0].transform_type = 'LOC_' + direction.upper()
            var.targets[0].transform_space = 'TRANSFORM_SPACE'

        var = driver.variables.new()
        var.name = 'cam_' + direction
        var.type = 'TRANSFORMS'
        var.targets[0].id = rig
        var.targets[0].bone_target = "Camera"
        var.targets[0].transform_type = 'LOC_' + direction.upper()
        var.targets[0].transform_space = 'TRANSFORM_SPACE'

    var = driver.variables.new()
    var.name = 'lens'
    var.type = 'SINGLE_PROP'
    var.targets[0].id_type = 'CAMERA'
    var.targets[0].id = cam.data
    var.targets[0].data_path = 'lens'

    # Shift driver Y
    driver = cam.data.driver_add('shift_y').driver

    driver.expression = 'rotation_shift * -(({distance_y} - (left_y + right_y)/2 + cam_y) * lens / abs({distance_z} - (left_z + right_z)/2 + cam_z) / 36 - (res_y/res_x)/2)'.format(
        distance_y=corner_distance_y, distance_z=corner_distance_z)

    var = driver.variables.new()
    var.name = 'rotation_shift'
    var.type = 'SINGLE_PROP'
    var.targets[0].id = rig
    var.targets[0].data_path = 'pose.bones["Camera"]["rotation_shift"]'

    for direction in ('y', 'z'):
        for corner in ('left', 'right'):
            var = driver.variables.new()
            var.name = '%s_%s' % (corner, direction)
            var.type = 'TRANSFORMS'
            var.targets[0].id = rig
            var.targets[0].bone_target = corner.capitalize() + '_Corner'
            var.targets[0].transform_type = 'LOC_' + direction.upper()
            var.targets[0].transform_space = 'TRANSFORM_SPACE'

        var = driver.variables.new()
        var.name = 'cam_' + direction
        var.type = 'TRANSFORMS'
        var.targets[0].id = rig
        var.targets[0].bone_target = "Camera"
        var.targets[0].transform_type = 'LOC_' + direction.upper()
        var.targets[0].transform_space = 'TRANSFORM_SPACE'

    for direction in ('x', 'y'):
        var = driver.variables.new()
        var.name = 'res_' + direction
        var.type = 'SINGLE_PROP'
        var.targets[0].id_type = 'SCENE'
        var.targets[0].id = scene
        var.targets[0].data_path = 'render.resolution_' + direction

    var = driver.variables.new()
    var.name = 'lens'
    var.type = 'SINGLE_PROP'
    var.targets[0].id_type = 'CAMERA'
    var.targets[0].id = cam.data
    var.targets[0].data_path = 'lens'


def build_camera_rig(context, mode):
    """Create stuff common to all camera rigs."""
    # Add the camera object
    cam_name = "%s_Camera" % mode.capitalize()
    cam_data = bpy.data.cameras.new(cam_name)
    cam = object_utils.object_data_add(context, cam_data, name=cam_name)
    context.scene.camera = cam

    # Add the rig object
    rig_name = mode.capitalize() + "_Rig"
    rig_data = bpy.data.armatures.new(rig_name)
    rig = object_utils.object_data_add(context, rig_data, name=rig_name)
    rig["rig_id"] = "%s" % rig_name
    rig.location = context.scene.cursor.location

    bpy.ops.object.mode_set(mode='EDIT')

    # Add new bones and setup specific rigs
    if mode == "DOLLY":
        create_dolly_bones(rig)
        setup_3d_rig(rig, cam)
    elif mode == "CRANE":
        create_crane_bones(rig)
        setup_3d_rig(rig, cam)
    elif mode == "2D":
        create_2d_bones(context, rig, cam)

    # Parent the camera to the rig
    cam.location = (0.0, -1.0, 0.0)  # Move the camera to the correct position
    cam.parent = rig
    cam.parent_type = "BONE"
    if mode == "2D":
        cam.parent_bone = "Camera"
    else:
        cam.parent_bone = "Camera_Offset"

    # Change display to BBone: it just looks nicer
    rig.data.display_type = 'BBONE'
    # Change display to wire for object
    rig.display_type = 'WIRE'

    # Lock camera transforms
    cam.lock_location = (True,) * 3
    cam.lock_rotation = (True,) * 3
    cam.lock_scale = (True,) * 3

    # Add custom properties to the armature’s Camera bone,
    # so that all properties may be animated in a single action

    pose_bones = rig.pose.bones

    # DOF Focus Distance property
    pb = pose_bones['Camera']
    pb["focus_distance"] = 10.0
    ui_data = pb.id_properties_ui('focus_distance')
    ui_data.update(min=0.0, default=10.0)

    # DOF F-Stop property
    pb = pose_bones['Camera']
    pb["aperture_fstop"] = 2.8
    ui_data = pb.id_properties_ui('aperture_fstop')
    ui_data.update(min=0.0, soft_min=0.1, soft_max=128.0, default=2.8)

    # Add drivers to link the camera properties to the custom props
    # on the armature
    create_prop_driver(rig, cam, "focus_distance", "dof.focus_distance")
    create_prop_driver(rig, cam, "aperture_fstop", "dof.aperture_fstop")

    # Make the rig the active object
    view_layer = context.view_layer
    for obj in view_layer.objects:
        obj.select_set(False)
    rig.select_set(True)
    view_layer.objects.active = rig


class OBJECT_OT_build_camera_rig(Operator):
    bl_idname = "object.build_camera_rig"
    bl_label = "Build Camera Rig"
    bl_description = "Build a Camera Rig"
    bl_options = {'REGISTER', 'UNDO'}

    mode: bpy.props.EnumProperty(items=(('DOLLY', 'Dolly', 'Dolly rig'),
                                        ('CRANE', 'Crane', 'Crane rig',),
                                        ('2D', '2D', '2D rig')),
                                 name="mode",
                                 description="Type of camera to create",
                                 default="DOLLY")

    def execute(self, context):
        # Build the rig
        build_camera_rig(context, self.mode)
        return {'FINISHED'}


def add_dolly_crane_buttons(self, context):
    """Dolly and crane entries in the Add Object > Camera Menu"""
    if context.mode == 'OBJECT':
        self.layout.operator(
            OBJECT_OT_build_camera_rig.bl_idname,
            text="Dolly Camera Rig",
            icon='VIEW_CAMERA'
        ).mode = "DOLLY"

        self.layout.operator(
            OBJECT_OT_build_camera_rig.bl_idname,
            text="Crane Camera Rig",
            icon='VIEW_CAMERA'
        ).mode = "CRANE"

        self.layout.operator(
            OBJECT_OT_build_camera_rig.bl_idname,
            text="2D Camera Rig",
            icon='PIVOT_BOUNDBOX'
        ).mode = "2D"


classes = (
    OBJECT_OT_build_camera_rig,
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.VIEW3D_MT_camera_add.append(add_dolly_crane_buttons)


def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)

    bpy.types.VIEW3D_MT_camera_add.remove(add_dolly_crane_buttons)


if __name__ == "__main__":
    register()
