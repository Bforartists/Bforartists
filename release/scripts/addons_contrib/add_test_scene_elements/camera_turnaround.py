# gpl: author Antonio Vazquez (antonioya)

bl_info = {
    "name": "Turnaround camera around object",
    "author": "Antonio Vazquez (antonioya)",
    "version": (0, 2, 4),
    "blender": (2, 68, 0),
    "location": "View3D > Toolshelf > Turnaround camera",
    "description": "Add a camera rotation around selected object.",
    "category": "Camera"}


import bpy
import math

# Action class
class RunAction(bpy.types.Operator):
    bl_idname = "object.rotate_around"
    bl_label = "Turnaround"
    bl_description = "Create camera rotation around selected object"

# Execute
    def execute(self, context):

# Save old data
        scene = context.scene
        selectobject = context.active_object
        camera = bpy.data.objects[bpy.context.scene.camera.name]
        savedcursor = bpy.context.scene.cursor_location.copy()  # cursor position
        savedframe = scene.frame_current
        if scene.use_cursor is False:
            bpy.ops.view3d.snap_cursor_to_selected()

# Create empty and parent
        bpy.ops.object.empty_add(type='PLAIN_AXES')
        myempty = bpy.data.objects[bpy.context.active_object.name]

        myempty.location = selectobject.location
        savedstate = myempty.matrix_world
        myempty.parent = selectobject
        myempty.name = 'MCH_Rotation_target'
        myempty.matrix_world = savedstate

# Parent camera to empty

        savedstate = camera.matrix_world
        camera.parent = myempty
        camera.matrix_world = savedstate

# Now add revolutions
# (make empty active object)

        bpy.ops.object.select_all(False)
        myempty.select = True
        bpy.context.scene.objects.active = myempty
# save current configuration
        savedinterpolation = context.user_preferences.edit.keyframe_new_interpolation_type
# change interpolation mode
        context.user_preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
# create first frame
        myempty.rotation_euler = (0, 0, 0)
        myempty.empty_draw_size = 0.1
        bpy.context.scene.frame_set(scene.frame_start)
        myempty.keyframe_insert(data_path='rotation_euler', frame=scene.frame_start)
# Dolly zoom
        if scene.dolly_zoom != "0":
            bpy.data.cameras[camera.name].lens = scene.camera_from_lens
            bpy.data.cameras[camera.name].keyframe_insert('lens', frame=scene.frame_start)

# Calculate rotation XYZ
        if scene.inverse_x:
            ix = -1
        else:
            ix = 1

        if scene.inverse_y:
            iy = -1
        else:
            iy = 1

        if scene.inverse_z:
            iz = -1
        else:
            iz = 1

        xrot = (math.pi * 2) * scene.camera_revol_x * ix
        yrot = (math.pi * 2) * scene.camera_revol_y * iy
        zrot = (math.pi * 2) * scene.camera_revol_z * iz

# create middle frame
        if scene.back_forw is True:
            myempty.rotation_euler = (xrot, yrot, zrot)
            myempty.keyframe_insert(data_path='rotation_euler', frame=((scene.frame_end - scene.frame_start) / 2))
# reverse
            xrot *= -1
            yrot *= -1
            zrot = 0

# Dolly zoom
        if scene.dolly_zoom == "2":
            bpy.data.cameras[camera.name].lens = scene.camera_to_lens
            bpy.data.cameras[camera.name].keyframe_insert('lens', frame=((scene.frame_end - scene.frame_start) / 2))

# create last frame
        myempty.rotation_euler = (xrot, yrot, zrot)
        myempty.keyframe_insert(data_path='rotation_euler', frame=scene.frame_end)
# Dolly zoom
        if scene.dolly_zoom != "0":
            if scene.dolly_zoom == "1":
                bpy.data.cameras[camera.name].lens = scene.camera_to_lens  # final
            else:
                bpy.data.cameras[camera.name].lens = scene.camera_from_lens  # back to init

            bpy.data.cameras[camera.name].keyframe_insert('lens', frame=scene.frame_end)

# Track constraint
        if scene.track is True:
            bpy.context.scene.objects.active = camera
            bpy.ops.object.constraint_add(type='TRACK_TO')
            bpy.context.object.constraints[-1].track_axis = 'TRACK_NEGATIVE_Z'
            bpy.context.object.constraints[-1].up_axis = 'UP_Y'
            bpy.context.object.constraints[-1].target = bpy.data.objects[myempty.name]

# back previous configuration
        context.user_preferences.edit.keyframe_new_interpolation_type = savedinterpolation
        bpy.context.scene.cursor_location = savedcursor


# Back to old selection
        bpy.ops.object.select_all(False)
        selectobject.select = True
        bpy.context.scene.objects.active = selectobject
        bpy.context.scene.frame_set(savedframe)

        return {'FINISHED'}

# UI Class

class PanelUI(bpy.types.Panel):
    bl_label = "Turnaround Camera"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "Animation"
    bl_options = {'DEFAULT_CLOSED'}

# Draw UI

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        try:
            bpy.context.scene.camera.name
        except AttributeError:
            row = layout.row(align=False)
            row.label("No defined camera for scene", icon="ERROR")
            return

        if context.active_object is not None:
            if context.active_object.type != 'CAMERA':
                buf = context.active_object.name
                row = layout.row(align=False)
                row.operator("object.rotate_around", icon='OUTLINER_DATA_CAMERA')
                row.label(buf, icon='MESH_DATA')
                row = layout.row()
                row.prop(scene, "use_cursor")
                row = layout.row(align=False)
                row.prop(scene, "camera")
                row = layout.row()
                row.prop(scene, "frame_start")
                row.prop(scene, "frame_end")
                row = layout.row()
                row.prop(scene, "camera_revol_x")
                row.prop(scene, "camera_revol_y")
                row.prop(scene, "camera_revol_z")
                row = layout.row()
                row.prop(scene, "inverse_x")
                row.prop(scene, "inverse_y")
                row.prop(scene, "inverse_z")
                row = layout.row()
                row.prop(scene, "back_forw")
                row = layout.row()
                row.prop(scene, "dolly_zoom")
                if scene.dolly_zoom != "0":
                    row = layout.row()
                    row.prop(scene, "camera_from_lens")
                    row.prop(scene, "camera_to_lens")
                row = layout.row()
                row.prop(scene, "track")

            else:
                buf = "No valid object selected"
                layout.label(buf, icon='MESH_DATA')

# Registration

def register():
    bpy.utils.register_class(RunAction)
    bpy.utils.register_class(PanelUI)

# Define properties
    bpy.types.Scene.camera_revol_x = bpy.props.FloatProperty(name='X', min=0, max=25,
                                                             default=0, precision=2,
                                                             description='Number total of revolutions in X axis')
    bpy.types.Scene.camera_revol_y = bpy.props.FloatProperty(name='Y', min=0, max=25,
                                                             default=0, precision=2,
                                                             description='Number total of revolutions in Y axis')
    bpy.types.Scene.camera_revol_z = bpy.props.FloatProperty(name='Z', min=0, max=25,
                                                             default=1, precision=2,
                                                             description='Number total of revolutions in Z axis')

    bpy.types.Scene.inverse_x = bpy.props.BoolProperty(name="-X", description="Inverse rotation", default=False)
    bpy.types.Scene.inverse_y = bpy.props.BoolProperty(name="-Y", description="Inverse rotation", default=False)
    bpy.types.Scene.inverse_z = bpy.props.BoolProperty(name="-Z", description="Inverse rotation", default=False)
    bpy.types.Scene.use_cursor = bpy.props.BoolProperty(name="Use cursor position",
                                                        description="Use cursor position instead of object origin",
                                                        default=False)
    bpy.types.Scene.back_forw = bpy.props.BoolProperty(name="Back and forward",
                                                       description="Create back and forward animation",
                                                       default=False)

    bpy.types.Scene.dolly_zoom = bpy.props.EnumProperty(items=(('0', "None", ""),
                                                               ('1', "Dolly zoom", ""),
                                                               ('2', "Dolly zoom B/F", "")),
                                                        name="Lens Effects",
                                                        description="Create a camera lens movement")

    bpy.types.Scene.camera_from_lens = bpy.props.FloatProperty(name='From', min=1, max=500, default=35,
                                                               precision=3,
                                                               description='Start lens value')
    bpy.types.Scene.camera_to_lens = bpy.props.FloatProperty(name='To', min=1, max=500, default=35, precision=3,
                                                             description='End lens value')

    bpy.types.Scene.track = bpy.props.BoolProperty(name="Create track constraint",
                                                   description="Add a track constraint to the camera",
                                                   default=False)


def unregister():
    bpy.utils.unregister_class(RunAction)
    bpy.utils.unregister_class(PanelUI)

    del bpy.types.Scene.camera_revol_x
    del bpy.types.Scene.camera_revol_y
    del bpy.types.Scene.camera_revol_z
    del bpy.types.Scene.inverse_x
    del bpy.types.Scene.inverse_y
    del bpy.types.Scene.inverse_z
    del bpy.types.Scene.use_cursor
    del bpy.types.Scene.back_forw
    del bpy.types.Scene.dolly_zoom
    del bpy.types.Scene.camera_from_lens
    del bpy.types.Scene.camera_to_lens
    del bpy.types.Scene.track

if __name__ == "__main__":
    register()
