import bpy
from bpy.types import Operator
from math import radians
from rna_prop_ui import rna_idprop_ui_prop_get
from .create_widgets import (create_root_widget,
                             create_widget,
                             create_camera_widget,
                             create_aim_widget,
                             )


def build_dolly_rig(context):
    """Operator to build the dolly rig"""
    # Set the bone layers
    boneLayer = (False, True, False, False, False, False, False, False,
                 False, False, False, False, False, False, False, False,
                 False, False, False, False, False, False, False, False,
                 False, False, False, False, False, False, False, False)

    # Add the new armature object:
    bpy.ops.object.armature_add()
    rig = context.active_object

    # it will try to name the rig "Dolly_rig" but if that name exists it will
    # add 000 to the name
    if "Dolly_rig" not in context.scene.objects:
        rig.name = "Dolly_rig"
    else:
        rig.name = "Dolly_rig.000"
    rig["rig_id"] = "Dolly_rig"

    bpy.ops.object.mode_set(mode='EDIT')

    # Remove default bone:
    bones = rig.data.edit_bones
    bones.remove(bones[0])

    # Add new bones:
    root = bones.new("Root")
    root.tail = (0.0, 3.0, 0.0)

    bpy.ops.object.mode_set(mode='EDIT')
    ctrlAimChild = bones.new("aim_MCH")
    ctrlAimChild.head = (0.0, 5.0, 3.0)
    ctrlAimChild.tail = (0.0, 7.0, 3.0)
    ctrlAimChild.layers = boneLayer

    ctrlAim = bones.new("Aim")
    ctrlAim.head = (0.0, 5.0, 3.0)
    ctrlAim.tail = (0.0, 7.0, 3.0)

    ctrl = bones.new("Camera")
    ctrl.head = (0.0, 0.0, 3.0)
    ctrl.tail = (0.0, 2.0, 3.0)

    # Setup hierarchy:
    ctrl.parent = root
    ctrlAim.parent = root
    ctrlAimChild.parent = ctrlAim

    # jump into pose mode and change bones to euler
    bpy.ops.object.mode_set(mode='POSE')
    for x in bpy.context.object.pose.bones:
        x.rotation_mode = 'XYZ'

    # jump into pose mode and add the custom bone shapes
    bpy.ops.object.mode_set(mode='POSE')
    bpy.context.object.pose.bones["Root"].custom_shape = bpy.data.objects[
        "WDGT_Camera_root"]  # add the widget as custom shape
    # set the wireframe checkbox to true
    bpy.context.object.data.bones["Root"].show_wire = True
    bpy.context.object.pose.bones[
        "Aim"].custom_shape = bpy.data.objects["WDGT_Aim"]
    bpy.context.object.data.bones["Aim"].show_wire = True
    bpy.context.object.pose.bones["Aim"].custom_shape_transform = bpy.data.objects[
        rig.name].pose.bones["aim_MCH"]  # sets the "At" field to the child
    bpy.context.object.pose.bones[
        "Camera"].custom_shape = bpy.data.objects["WDGT_Camera"]
    bpy.context.object.data.bones["Camera"].show_wire = True

    # jump into object mode
    bpy.ops.object.mode_set(mode='OBJECT')

    # Add constraints to bones:
    con = rig.pose.bones['aim_MCH'].constraints.new('COPY_ROTATION')
    con.target = rig
    con.subtarget = "Camera"

    con = rig.pose.bones['Camera'].constraints.new('TRACK_TO')
    con.target = rig
    con.subtarget = "Aim"
    con.use_target_z = True

    # Add custom Bone property to Camera bone
    ob = bpy.context.object.pose.bones['Camera']
    prop = rna_idprop_ui_prop_get(ob, "lock", create=True)
    ob["lock"] = 1.0
    prop["soft_min"] = prop["min"] = 0.0
    prop["soft_max"] = prop["max"] = 1.0

    # Add Driver to Lock/Unlock Camera from Aim Target
    rig = bpy.context.view_layer.objects.active
    pose_bone = bpy.data.objects[rig.name].pose.bones['Camera']

    constraint = pose_bone.constraints["Track To"]
    inf_driver = constraint.driver_add('influence')
    inf_driver.driver.type = 'SCRIPTED'
    var = inf_driver.driver.variables.new()
    var.name = 'var'
    var.type = 'SINGLE_PROP'

    # Target the Custom bone property
    var.targets[0].id = bpy.data.objects[rig.name]
    var.targets[0].data_path = 'pose.bones["Camera"]["lock"]'
    inf_driver.driver.expression = 'var'

    # Add custom property for the lens / add the driver after the camera is created
    ob = bpy.context.object.pose.bones['Camera']
    prop = rna_idprop_ui_prop_get(ob, "focal_length", create=True)
    ob["focal_length"] = 50.0
    prop["soft_min"] = prop["min"] = 1.0
    prop["default"] = 50.0
    prop["soft_max"] = prop["max"] = 5000.0

    # Add custom property for the focus distance / add the driver after the camera is created
    ob = bpy.context.object.pose.bones['Camera']
    prop = rna_idprop_ui_prop_get(ob, "focus_distance", create=True)
    ob["focus_distance"] = 10.00
    prop["soft_min"] = prop["min"] = 0.0
    prop["soft_max"] = prop["max"] = 1000.0

    # Add custom property for the f-stop / add the driver after the camera is created
    ob = bpy.context.object.pose.bones['Camera']
    prop = rna_idprop_ui_prop_get(ob, "f-stop", create=True)
    ob["f-stop"] = 2.8
    prop["soft_min"] = prop["min"] = 0.1
    prop["soft_max"] = prop["max"] = 128.00

    # Add the camera object:
    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.camera_add()
    cam = bpy.context.active_object

    # Name the Camera Object
    if 'Dolly_camera' not in context.scene.objects:
        cam.name = "Dolly_camera"
    else:
        cam.name = "Dolly_camera.000"

    # this will name the camera data
    cam.data.name = cam.name

    cam_data_name = bpy.context.object.data.name
    bpy.data.cameras[cam_data_name].display_size = 1.0
    cam.rotation_euler = [radians(90), 0, 0]  # rotate the camera 90 degrees in x

    cam.location = (0.0, -2.0, 0.0)  # move the camera to the correct postion
    cam.parent = rig
    cam.parent_type = "BONE"
    cam.parent_bone = "Camera"

    # Add Driver to link the camera lens to the custom property on the armature
    pose_bone = bpy.data.objects[rig.name].pose.bones['Camera']
    lens_driver = cam.data.driver_add("lens")
    lens_driver.driver.type = 'SCRIPTED'
    var = lens_driver.driver.variables.new()
    var.name = 'var'
    var.type = 'SINGLE_PROP'

    # Target the Custom bone property
    var.targets[0].id = bpy.data.objects[rig.name]
    var.targets[0].data_path = 'pose.bones["Camera"]["focal_length"]'
    lens_driver.driver.expression = 'var'

    # Add Driver to link the camera focus distance to the custom property on the armature
    pose_bone = bpy.data.objects[rig.name].pose.bones['Camera']
    lens_driver = cam.data.driver_add("dof.focus_distance")
    lens_driver.driver.type = 'SCRIPTED'
    var = lens_driver.driver.variables.new()
    var.name = 'var'
    var.type = 'SINGLE_PROP'

    # Target the Custom bone property
    var.targets[0].id = bpy.data.objects[rig.name]
    var.targets[0].data_path = 'pose.bones["Camera"]["focus_distance"]'
    lens_driver.driver.expression = 'var'

    # Add Driver to link the camera f-stop to the custom property on the armature
    pose_bone = bpy.data.objects[rig.name].pose.bones['Camera']
    lens_driver = cam.data.driver_add("dof.aperture_fstop")
    lens_driver.driver.type = 'SCRIPTED'
    var = lens_driver.driver.variables.new()
    var.name = 'var'
    var.type = 'SINGLE_PROP'

    # Target the Custom bone property
    var.targets[0].id = bpy.data.objects[rig.name]
    var.targets[0].data_path = 'pose.bones["Camera"]["f-stop"]'
    lens_driver.driver.expression = 'var'

    # lock the location/rotation/scale of the camera
    cam.lock_location = [True, True, True]
    cam.lock_rotation = [True, True, True]
    cam.lock_scale = [True, True, True]

    # Set new camera as active camera
    bpy.context.scene.camera = cam

    # make sure the camera is selectable by default (this can be locked in the UI)
    bpy.context.object.hide_select = False

    # make the rig the active object before finishing
    bpy.context.view_layer.objects.active = rig
    bpy.data.objects[cam.name].select_set(False)
    bpy.data.objects[rig.name].select_set(True)

    return rig


class ADD_CAMERA_RIGS_OT_build_dolly_rig(Operator):
    bl_idname = "add_camera_rigs.build_dolly_rig"
    bl_label = "Build Dolly Camera Rig"
    bl_description = "Build a Camera Dolly Rig"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # build the Widgets
        if not "WDGT_Camera_root" in bpy.context.scene.objects:
            create_root_widget(self, "Camera_root")
        if not "WDGT_Camera" in bpy.context.scene.objects:
            create_camera_widget(self, "Camera")
        if not "WDGT_Aim" in bpy.context.scene.objects:
            create_aim_widget(self, "Aim")

        # call the function to build the rig
        build_dolly_rig(context)

        return {'FINISHED'}


def build_crane_rig(context):
    # Define some useful variables:
    boneLayer = (False, True, False, False, False, False, False, False,
                 False, False, False, False, False, False, False, False,
                 False, False, False, False, False, False, False, False,
                 False, False, False, False, False, False, False, False)

    # Add the new armature object:
    bpy.ops.object.armature_add()
    rig = context.active_object

    # it will try to name the rig "Crane_rig" but if that name exists it will
    # add .000 to the name
    if "Crane_rig" not in context.scene.objects:
        rig.name = "Crane_rig"
    else:
        rig.name = "Crane_rig.000"
    rig["rig_id"] = "Crane_rig"

    bpy.ops.object.mode_set(mode='EDIT')

    # Remove default bone:
    bones = rig.data.edit_bones
    bones.remove(bones[0])

    # Add new bones:
    root = bones.new("Root")
    root.tail = (0.0, 3.0, 0.0)

    ctrlAimChild = bones.new("aim_MCH")
    ctrlAimChild.head = (0.0, 10.0, 1.0)
    ctrlAimChild.tail = (0.0, 12.0, 1.0)
    ctrlAimChild.layers = boneLayer

    ctrlAim = bones.new("Aim")
    ctrlAim.head = (0.0, 10.0, 1.0)
    ctrlAim.tail = (0.0, 12.0, 1.0)

    ctrl = bones.new("Camera")
    ctrl.head = (0.0, 1.0, 1.0)
    ctrl.tail = (0.0, 3.0, 1.0)

    arm = bones.new("Crane_arm")
    arm.head = (0.0, 0.0, 1.0)
    arm.tail = (0.0, 1.0, 1.0)

    height = bones.new("Crane_height")
    height.head = (0.0, 0.0, 0.0)
    height.tail = (0.0, 0.0, 1.0)

    # Setup hierarchy:
    ctrl.parent = arm
    ctrl.use_inherit_rotation = False
    ctrl.use_inherit_scale = False

    arm.parent = height
    arm.use_inherit_scale = False

    height.parent = root
    ctrlAim.parent = root
    ctrlAimChild.parent = ctrlAim

    # change display to BBone: it just looks nicer
    bpy.context.object.data.display_type = 'BBONE'
    # change display to wire for object
    bpy.context.object.display_type = 'WIRE'

    # jump into pose mode and change bones to euler
    bpy.ops.object.mode_set(mode='POSE')
    for x in bpy.context.object.pose.bones:
        x.rotation_mode = 'XYZ'

    # lock the relevant loc, rot and scale
    bpy.context.object.pose.bones[
        "Crane_arm"].lock_rotation = [False, True, False]
    bpy.context.object.pose.bones["Crane_arm"].lock_scale = [True, False, True]
    bpy.context.object.pose.bones["Crane_height"].lock_location = [True, True, True]
    bpy.context.object.pose.bones["Crane_height"].lock_rotation = [True, True, True]
    bpy.context.object.pose.bones["Crane_height"].lock_scale = [True, False, True]

    # add the custom bone shapes
    bpy.context.object.pose.bones["Root"].custom_shape = bpy.data.objects[
        "WDGT_Camera_root"]  # add the widget as custom shape
    # set the wireframe checkbox to true
    bpy.context.object.data.bones["Root"].show_wire = True
    bpy.context.object.pose.bones[
        "Aim"].custom_shape = bpy.data.objects["WDGT_Aim"]
    bpy.context.object.data.bones["Aim"].show_wire = True
    bpy.context.object.pose.bones["Aim"].custom_shape_transform = bpy.data.objects[
        rig.name].pose.bones["aim_MCH"]  # sets the "At" field to the child
    bpy.context.object.pose.bones[
        "Camera"].custom_shape = bpy.data.objects["WDGT_Camera"]
    bpy.context.object.data.bones["Camera"].show_wire = True

    # jump into object mode
    bpy.ops.object.mode_set(mode='OBJECT')

    # Add constraints to bones:
    con = rig.pose.bones['aim_MCH'].constraints.new('COPY_ROTATION')
    con.target = rig
    con.subtarget = "Camera"

    con = rig.pose.bones['Camera'].constraints.new('TRACK_TO')
    con.target = rig
    con.subtarget = "Aim"
    con.use_target_z = True

    # Add custom Bone property to Camera bone
    ob = bpy.context.object.pose.bones['Camera']
    prop = rna_idprop_ui_prop_get(ob, "lock", create=True)
    ob["lock"] = 1.0
    prop["soft_min"] = prop["min"] = 0.0
    prop["soft_max"] = prop["max"] = 1.0

    # Add Driver to Lock/Unlock Camera from Aim Target
    rig = bpy.context.view_layer.objects.active
    pose_bone = bpy.data.objects[rig.name].pose.bones['Camera']

    constraint = pose_bone.constraints["Track To"]
    inf_driver = constraint.driver_add('influence')
    inf_driver.driver.type = 'SCRIPTED'
    var = inf_driver.driver.variables.new()
    var.name = 'var'
    var.type = 'SINGLE_PROP'

    # Target the Custom bone property
    var.targets[0].id = bpy.data.objects[rig.name]
    var.targets[0].data_path = 'pose.bones["Camera"]["lock"]'
    inf_driver.driver.expression = 'var'

    # Add custom property for the lens / add the driver after the camera is created
    ob = bpy.context.object.pose.bones['Camera']
    prop = rna_idprop_ui_prop_get(ob, "focal_length", create=True)
    ob["focal_length"] = 50.0
    prop["soft_min"] = prop["min"] = 1.0
    prop["default"] = 50.0
    prop["soft_max"] = prop["max"] = 5000.0

    # Add custom property for the focus distance / add the driver after the camera is created
    ob = bpy.context.object.pose.bones['Camera']
    prop = rna_idprop_ui_prop_get(ob, "focus_distance", create=True)
    ob["focus_distance"] = 10.00
    prop["soft_min"] = prop["min"] = 0.0
    prop["soft_max"] = prop["max"] = 1000.0

    # Add custom property for the focus distance / add the driver after the camera is created
    ob = bpy.context.object.pose.bones['Camera']
    prop = rna_idprop_ui_prop_get(ob, "focus_distance", create=True)
    ob["focus_distance"] = 10.00
    prop["soft_min"] = prop["min"] = 0.0
    prop["soft_max"] = prop["max"] = 1000.0

    # Add custom property for the f-stop / add the driver after the camera is created
    ob = bpy.context.object.pose.bones['Camera']
    prop = rna_idprop_ui_prop_get(ob, "f-stop", create=True)
    ob["f-stop"] = 2.8
    prop["soft_min"] = prop["min"] = 0.1
    prop["soft_max"] = prop["max"] = 128.00

    # Add the camera object:
    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.camera_add()
    cam = bpy.context.active_object

    # this will name the Camera Object
    if 'Crane_camera' not in context.scene.objects:
        cam.name = "Crane_camera"
    else:
        cam.name = "Crane_camera.000"

    # this will name the camera Data Object
    if "Crane_camera" not in bpy.context.scene.objects.data.camera:
        cam.data.name = "Crane_camera"
    else:
        cam.data.name = "Crane_camera.000"

    cam_data_name = bpy.context.object.data.name
    bpy.data.cameras[cam_data_name].display_size = 1.0
    cam.rotation_euler = [radians(90), 0, 0]  # rotate the camera 90 degrees in x
    cam.location = (0.0, -2.0, 0.0)  # move the camera to the correct postion
    cam.parent = rig
    cam.parent_type = "BONE"
    cam.parent_bone = "Camera"

    # Add Driver to link the camera lens to the custom property on the armature
    pose_bone = bpy.data.objects[rig.name].pose.bones['Camera']
    lens_driver = cam.data.driver_add("lens")
    lens_driver.driver.type = 'SCRIPTED'
    var = lens_driver.driver.variables.new()
    var.name = 'var'
    var.type = 'SINGLE_PROP'

    # Target the Custom bone property
    var.targets[0].id = bpy.data.objects[rig.name]
    var.targets[0].data_path = 'pose.bones["Camera"]["focal_length"]'
    lens_driver.driver.expression = 'var'

    # Add Driver to link the camera focus distance to the custom property on the armature
    pose_bone = bpy.data.objects[rig.name].pose.bones['Camera']
    lens_driver = cam.data.driver_add("dof.focus_distance")
    lens_driver.driver.type = 'SCRIPTED'
    var = lens_driver.driver.variables.new()
    var.name = 'var'
    var.type = 'SINGLE_PROP'

    # Target the Custom bone property
    var.targets[0].id = bpy.data.objects[rig.name]
    var.targets[0].data_path = 'pose.bones["Camera"]["focus_distance"]'
    lens_driver.driver.expression = 'var'

    # Add Driver to link the camera f-stop to the custom property on the armature
    pose_bone = bpy.data.objects[rig.name].pose.bones['Camera']
    lens_driver = cam.data.driver_add("dof.aperture_fstop")
    lens_driver.driver.type = 'SCRIPTED'
    var = lens_driver.driver.variables.new()
    var.name = 'var'
    var.type = 'SINGLE_PROP'

    # Target the Custom bone property
    var.targets[0].id = bpy.data.objects[rig.name]
    var.targets[0].data_path = 'pose.bones["Camera"]["f-stop"]'
    lens_driver.driver.expression = 'var'

    #  the location/rotation/scale of the camera
    cam.lock_location = [True, True, True]
    cam.lock_rotation = [True, True, True]
    cam.lock_scale = [True, True, True]

    # Set new camera as active camera
    bpy.context.scene.camera = cam

    # make sure the camera is selectable by default (this can be locked in the UI)
    bpy.context.object.hide_select = False

    # make the rig the active object before finishing
    bpy.context.view_layer.objects.active = rig
    bpy.data.objects[cam.name].select_set(False)
    bpy.data.objects[rig.name].select_set(True)

    return rig


class ADD_CAMERA_RIGS_OT_build_crane_rig(Operator):
    bl_idname = "add_camera_rigs.build_crane_rig"
    bl_label = "Build Crane Camera Rig"
    bl_description = "Build a Camera Crane Rig"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # build the Widgets
        if not "WDGT_Camera_root" in bpy.context.scene.objects:
            create_root_widget(self, "Camera_root")
        if not "WDGT_Camera" in bpy.context.scene.objects:
            create_camera_widget(self, "Camera")
        if not "WDGT_Aim" in bpy.context.scene.objects:
            create_aim_widget(self, "Aim")

        # call the function to build the rig
        build_crane_rig(context)

        return {'FINISHED'}


# dolly and crane entries in the Add Object > Camera Menu
def add_dolly_crane_buttons(self, context):
    if context.mode == 'OBJECT':
        self.layout.operator(
            ADD_CAMERA_RIGS_OT_build_dolly_rig.bl_idname,
            text="Dolly Camera Rig",
            icon='CAMERA_DATA'
        )
        self.layout.operator(
            ADD_CAMERA_RIGS_OT_build_crane_rig.bl_idname,
            text="Crane Camera Rig",
            icon='CAMERA_DATA'
        )


classes = (
    ADD_CAMERA_RIGS_OT_build_dolly_rig,
    ADD_CAMERA_RIGS_OT_build_crane_rig,
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
