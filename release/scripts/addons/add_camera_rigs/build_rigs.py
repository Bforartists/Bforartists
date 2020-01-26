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
from bpy_extras import object_utils
from bpy.types import Operator
from math import radians, pi
from rna_prop_ui import rna_idprop_ui_prop_get
from .create_widgets import (create_root_widget,
                             create_widget,
                             create_camera_widget,
                             create_aim_widget,
                             )


def create_dolly_bones(rig, bone_layers):
    bones = rig.data.edit_bones

    # Add new bones
    root = bones.new("Root")
    root.tail = (0.0, 1.0, 0.0)
    root.show_wire = True

    ctrl_aim_child = bones.new("Aim_shape_rotation-MCH")
    ctrl_aim_child.head = (0.0, 10.0, 1.7)
    ctrl_aim_child.tail = (0.0, 11.0, 1.7)
    ctrl_aim_child.layers = bone_layers

    ctrl_aim = bones.new("Aim")
    ctrl_aim.head = (0.0, 10.0, 1.7)
    ctrl_aim.tail = (0.0, 11.0, 1.7)
    ctrl_aim.show_wire = True

    ctrl = bones.new("Camera")
    ctrl.head = (0.0, 0.0, 1.7)
    ctrl.tail = (0.0, 1.0, 1.7)
    ctrl.show_wire = True

    # Setup hierarchy
    ctrl.parent = root
    ctrl_aim.parent = root
    ctrl_aim_child.parent = ctrl_aim


def create_crane_bones(rig, bone_layers):
    bones = rig.data.edit_bones

    # Add new bones
    root = bones.new("Root")
    root.tail = (0.0, 1.0, 0.0)
    root.show_wire = True

    ctrl_aim_child = bones.new("Aim_shape_rotation-MCH")
    ctrl_aim_child.head = (0.0, 10.0, 1.7)
    ctrl_aim_child.tail = (0.0, 11.0, 1.7)
    ctrl_aim_child.layers = bone_layers

    ctrl_aim = bones.new("Aim")
    ctrl_aim.head = (0.0, 10.0, 1.7)
    ctrl_aim.tail = (0.0, 11.0, 1.7)
    ctrl_aim.show_wire = True

    ctrl = bones.new("Camera")
    ctrl.head = (0.0, 1.0, 1.7)
    ctrl.tail = (0.0, 2.0, 1.7)

    arm = bones.new("Crane_arm")
    arm.head = (0.0, 0.0, 1.7)
    arm.tail = (0.0, 1.0, 1.7)

    height = bones.new("Crane_height")
    height.head = (0.0, 0.0, 0.0)
    height.tail = (0.0, 0.0, 1.7)

    # Setup hierarchy
    ctrl.parent = arm
    ctrl.use_inherit_rotation = False
    ctrl.use_inherit_scale = False
    ctrl.show_wire = True

    arm.parent = height
    arm.use_inherit_scale = False

    height.parent = root
    ctrl_aim.parent = root
    ctrl_aim_child.parent = ctrl_aim

    # Jump into object mode
    bpy.ops.object.mode_set(mode='OBJECT')
    pose_bones = rig.pose.bones

    # Lock the relevant loc, rot and scale
    pose_bones["Crane_arm"].lock_rotation = (False, True, False)
    pose_bones["Crane_arm"].lock_scale = (True, False, True)
    pose_bones["Crane_height"].lock_location = (True, True, True)
    pose_bones["Crane_height"].lock_rotation = (True, True, True)
    pose_bones["Crane_height"].lock_scale = (True, False, True)


def build_camera_rig(context, mode):
    bone_layers = tuple(i == 1 for i in range(32))
    view_layer = bpy.context.view_layer

    rig_name = mode.capitalize() + "_Rig"
    rig_data = bpy.data.armatures.new(rig_name)
    rig = object_utils.object_data_add(context, rig_data, name=rig_name)
    rig["rig_id"] = "%s" % rig_name
    view_layer.objects.active = rig
    rig.location = context.scene.cursor.location

    bpy.ops.object.mode_set(mode='EDIT')

    # Add new bones
    if mode == "DOLLY":
        create_dolly_bones(rig, bone_layers)
    elif mode == "CRANE":
        create_crane_bones(rig, bone_layers)

    # Jump into object mode and change bones to euler
    bpy.ops.object.mode_set(mode='OBJECT')
    pose_bones = rig.pose.bones
    for b in pose_bones:
        b.rotation_mode = 'XYZ'

    # Add custom properties to the armature’s Camera bone,
    # so that all properties may be animated in a single action
    # Add driver after the camera is created

    # Lens property
    pb = pose_bones['Camera']
    pb["lens"] = 50.0
    prop = rna_idprop_ui_prop_get(pb, "lens", create=True)
    prop["default"] = 50.0
    prop["min"] = 1.0
    prop["max"] = 1000000.0
    prop["soft_max"] = 5000.0

    # DOF Focus Distance property
    pb = pose_bones['Camera']
    pb["focus_distance"] = 10.0
    prop = rna_idprop_ui_prop_get(pb, "focus_distance", create=True)
    prop["default"] = 10.0
    prop["min"] = 0.0

    # DOF F-Stop property
    pb = pose_bones['Camera']
    pb["aperture_fstop"] = 2.8
    prop = rna_idprop_ui_prop_get(pb, "aperture_fstop", create=True)
    prop["default"] = 2.8
    prop["min"] = 0.0
    prop["soft_min"] = 0.1
    prop["soft_max"] = 128.0

    # Build the widgets
    root_widget = create_root_widget("Camera_Root")
    camera_widget = create_camera_widget("Camera")
    aim_widget = create_aim_widget("Aim")

    # Add the custom bone shapes
    pose_bones["Root"].custom_shape = root_widget
    pose_bones["Aim"].custom_shape = aim_widget
    pose_bones["Camera"].custom_shape = camera_widget

    # Set the "At" field to the child
    pose_bones["Aim"].custom_shape_transform = pose_bones["Aim_shape_rotation-MCH"]

    # Add constraints to bones
    con = pose_bones['Aim_shape_rotation-MCH'].constraints.new('COPY_ROTATION')
    con.target = rig
    con.subtarget = "Camera"

    con = pose_bones['Camera'].constraints.new('TRACK_TO')
    con.target = rig
    con.subtarget = "Aim"
    con.use_target_z = True

    # Change display to BBone: it just looks nicer
    bpy.context.object.data.display_type = 'BBONE'
    # Change display to wire for object
    bpy.context.object.display_type = 'WIRE'

    # Add the camera object
    cam_name = "%s_Camera" % mode.capitalize()
    cam_data = bpy.data.cameras.new(cam_name)
    cam = object_utils.object_data_add(context, cam_data, name=cam_name)
    view_layer.objects.active = cam
    context.scene.camera = cam

    cam.data.display_size = 1.0
    cam.rotation_euler[0] = pi / 2.0  # Rotate the camera 90 degrees in x

    cam.location = (0.0, -1.0, 0.0)  # Move the camera to the correct position
    cam.parent = rig
    cam.parent_type = "BONE"
    cam.parent_bone = "Camera"

    # Lock camera transforms
    cam.lock_location = (True,) * 3
    cam.lock_rotation = (True,) * 3
    cam.lock_scale = (True,) * 3

    # Add drivers to link the camera properties to the custom props
    # on the armature
    for prop_from, prop_to in (("lens", "lens"),
                               ("focus_distance", "dof.focus_distance"),
                               ("aperture_fstop", "dof.aperture_fstop")):
        driver = cam.data.driver_add(prop_to)
        driver.driver.type = 'SCRIPTED'
        var = driver.driver.variables.new()
        var.name = 'var'
        var.type = 'SINGLE_PROP'

        # Target the custom bone property
        var.targets[0].id = rig
        var.targets[0].data_path = 'pose.bones["Camera"]["%s"]' % prop_from
        driver.driver.expression = 'var'

    # Make the rig the active object
    for ob in view_layer.objects:
        ob.select_set(False)
    rig.select_set(True)
    view_layer.objects.active = rig

    return rig


class OBJECT_OT_build_camera_rig(Operator):
    bl_idname = "object.build_camera_rig"
    bl_label = "Build Camera Rig"
    bl_description = "Build a Camera Rig"
    bl_options = {'REGISTER', 'UNDO'}

    mode: bpy.props.EnumProperty(items=
                                 (('DOLLY',) * 3,
                                  ('CRANE',) * 3,),
                                 name="mode",
                                 description="", default="DOLLY")

    def execute(self, context):
        # Build the rig
        build_camera_rig(context, self.mode)
        return {'FINISHED'}


def add_dolly_crane_buttons(self, context):
    """Dolly and crane entries in the Add Object > Camera Menu"""
    if context.mode == 'OBJECT':
        op = self.layout.operator(
            OBJECT_OT_build_camera_rig.bl_idname,
            text="Dolly Camera Rig",
            icon='CAMERA_DATA'
        )
        op.mode = "DOLLY"
        op = self.layout.operator(
            OBJECT_OT_build_camera_rig.bl_idname,
            text="Crane Camera Rig",
            icon='CAMERA_DATA'
        )
        op.mode = "CRANE"


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
