import bpy
from bpy.types import Operator


def set_scene_camera():
    '''Makes the camera the active and sets it to the scene camera'''
    ob = bpy.context.active_object
    # find the children on the rig (the camera name)
    active_cam = ob.children[0].name
    # cam = bpy.data.cameras[bpy.data.objects[active_cam]]
    scene_cam = bpy.context.scene.camera

    if active_cam != scene_cam.name:
        bpy.context.scene.camera = bpy.data.objects[active_cam]
    else:
        return None


class ADD_CAMERA_RIGS_OT_set_scene_camera(Operator):
    bl_idname = "add_camera_rigs.set_scene_camera"
    bl_label = "Make Camera Active"
    bl_description = "Makes the camera parented to this rig the active scene camera"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        set_scene_camera()

        return {'FINISHED'}


def markerBind():
    '''Defines the function to add a marker to timeling and bind camera'''
    rig = bpy.context.active_object  # rig object
    active_cam = rig.children[0]  # camera object

    # switch area to DOPESHEET to add marker
    bpy.context.area.type = 'DOPESHEET_EDITOR'
    # add marker
    bpy.ops.marker.add()  # it will automatiically have the name of the camera
    # select rig camera
    bpy.context.view_layer.objects.active = active_cam
    # bind marker to selected camera
    bpy.ops.marker.camera_bind()
    # make the rig the active object before finishing
    bpy.context.view_layer.objects.active = rig
    bpy.data.objects[active_cam.name].select_set(False)
    bpy.data.objects[rig.name].select_set(True)
    # switch back to 3d view
    bpy.context.area.type = 'VIEW_3D'


class ADD_CAMERA_RIGS_OT_add_marker_bind(Operator):
    bl_idname = "add_camera_rigs.add_marker_bind"
    bl_label = "Add Marker and Bind Camera"
    bl_description = "Add marker to current frame then bind rig camera to it (for camera switching)"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        markerBind()

        return {'FINISHED'}


def add_DOF_object():
    """Define the function to add an Empty as DOF object """
    smode = bpy.context.mode
    rig = bpy.context.active_object
    bone = rig.data.bones['aim_MCH']
    active_cam = rig.children[0].name
    cam = bpy.data.cameras[bpy.data.objects[active_cam].data.name]

    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    # Add Empty
    bpy.ops.object.empty_add()
    obj = bpy.context.active_object

    obj.name = "Empty_DOF"
    # parent to aim_MCH
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "aim_MCH"
    # clear loc and rot
    bpy.ops.object.location_clear()
    bpy.ops.object.rotation_clear()
    # move to bone head
    obj.location = bone.head

    # make this new empty the dof_object
    cam.dof.focus_object = obj

    # make the rig the active object before finishing
    bpy.context.view_layer.objects.active = rig
    bpy.data.objects[obj.name].select_set(False)
    bpy.data.objects[rig.name].select_set(True)

    bpy.ops.object.mode_set(mode=smode, toggle=False)


class ADD_CAMERA_RIGS_OT_add_dof_object(Operator):
    bl_idname = "add_camera_rigs.add_dof_object"
    bl_label = "Add DOF Object"
    bl_description = "Create Empty and add as DOF Object"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        add_DOF_object()

        return {'FINISHED'}


classes = (
    ADD_CAMERA_RIGS_OT_set_scene_camera,
    ADD_CAMERA_RIGS_OT_add_marker_bind,
    ADD_CAMERA_RIGS_OT_add_dof_object,
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)
