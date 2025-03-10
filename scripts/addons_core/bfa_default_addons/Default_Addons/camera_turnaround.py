# SPDX-FileCopyrightText: 2017-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Turnaround Camera",
    "author": "Antonio Vazquez (antonioya)",
    "version": (0, 3, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > View Tab > Turnaround Camera",
    "description": "Add a camera rotation around selected object",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/animation/turnaround_camera.html",
    "category": "Animation",
}


import bpy
from math import pi
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    PointerProperty,
)
from bpy.types import (
    Operator,
    Panel,
    PropertyGroup,
)


# ------------------------------------------------------
# Action class
# ------------------------------------------------------
class CAMERATURN_OT_RunAction(Operator):
    bl_idname = "object.rotate_around"
    bl_label = "Turnaround"
    bl_description = "Create camera rotation around selected object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # ----------------------
        # Save old data
        # ----------------------
        scene = context.scene
        turn_camera = scene.turn_camera
        selectobject = context.active_object
        camera = scene.camera
        savedcursor = scene.cursor.location.copy()  # cursor position
        savedframe = scene.frame_current
        if turn_camera.use_cursor is False:
            bpy.ops.view3d.snap_cursor_to_selected()

        # -------------------------
        # Create empty and parent
        # -------------------------
        bpy.ops.object.empty_add(type='PLAIN_AXES')
        myempty = context.active_object

        myempty.location = selectobject.location
        savedstate = myempty.matrix_world
        myempty.parent = selectobject
        myempty.name = "MCH_Rotation_target"
        myempty.matrix_world = savedstate

        # -------------------------
        # Parent camera to empty
        # -------------------------
        savedstate = camera.matrix_world
        camera.parent = myempty
        camera.matrix_world = savedstate

        # -------------------------
        # Now add revolutions
        # (make empty active object)
        # -------------------------
        bpy.ops.object.select_all(False)
        myempty.select_set(True)
        context.view_layer.objects.active = myempty
        # save current configuration
        savedinterpolation = context.preferences.edit.keyframe_new_interpolation_type
        # change interpolation mode
        context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
        # create first frame
        myempty.rotation_euler = (0, 0, 0)
        myempty.empty_display_size = 0.1
        scene.frame_set(scene.frame_start)
        myempty.keyframe_insert(data_path="rotation_euler", frame=scene.frame_start)

        # Clear the Camera Animations if the option is checked
        if turn_camera.reset_cam_anim:
            try:
                if bpy.data.cameras[camera.name].animation_data:
                    bpy.data.cameras[camera.name].animation_data_clear()
            except Exception as e:
                print("\n[Camera Turnaround]\nWarning: {}\n".format(e))

        # Dolly zoom
        if turn_camera.dolly_zoom != "0":
            bpy.data.cameras[camera.name].lens = turn_camera.camera_from_lens
            bpy.data.cameras[camera.name].keyframe_insert("lens", frame=scene.frame_start)

        # Calculate rotation XYZ
        ix = -1 if turn_camera.inverse_x else 1
        iy = -1 if turn_camera.inverse_y else 1
        iz = -1 if turn_camera.inverse_z else 1

        xrot = (pi * 2) * turn_camera.camera_revol_x * ix
        yrot = (pi * 2) * turn_camera.camera_revol_y * iy
        zrot = (pi * 2) * turn_camera.camera_revol_z * iz

        # create middle frame
        if turn_camera.back_forw is True:
            myempty.rotation_euler = (xrot, yrot, zrot)
            myempty.keyframe_insert(
                data_path="rotation_euler",
                frame=((scene.frame_end - scene.frame_start) / 2)
            )
            # reverse
            xrot *= -1
            yrot *= -1
            zrot = 0

        # Dolly zoom
        if turn_camera.dolly_zoom == "2":
            bpy.data.cameras[camera.name].lens = turn_camera.camera_to_lens
            bpy.data.cameras[camera.name].keyframe_insert(
                "lens",
                frame=((scene.frame_end - scene.frame_start) / 2)
            )

        # create last frame
        myempty.rotation_euler = (xrot, yrot, zrot)
        myempty.keyframe_insert(data_path="rotation_euler", frame=scene.frame_end)
        # Dolly zoom
        if turn_camera.dolly_zoom != "0":
            if turn_camera.dolly_zoom == "1":
                bpy.data.cameras[camera.name].lens = turn_camera.camera_to_lens  # final
            else:
                bpy.data.cameras[camera.name].lens = turn_camera.camera_from_lens  # back to init

            bpy.data.cameras[camera.name].keyframe_insert(
                "lens", frame=scene.frame_end
            )

        # Track constraint
        if turn_camera.track is True:
            bpy.context.view_layer.objects.active = camera
            bpy.ops.object.constraint_add(type='TRACK_TO')
            bpy.context.object.constraints[-1].track_axis = 'TRACK_NEGATIVE_Z'
            bpy.context.object.constraints[-1].up_axis = 'UP_Y'
            bpy.context.object.constraints[-1].target = myempty

        # back previous configuration
        context.preferences.edit.keyframe_new_interpolation_type = savedinterpolation
        scene.cursor.location = savedcursor

        # -------------------------
        # Back to old selection
        # -------------------------
        bpy.ops.object.select_all(False)
        selectobject.select_set(True)
        bpy.context.view_layer.objects.active = selectobject
        scene.frame_set(savedframe)

        return {'FINISHED'}


# ------------------------------------------------------
# Define Properties
# ------------------------------------------------------
class CAMERATURN_Props(PropertyGroup):

    camera_revol_x: FloatProperty(
        name="X", min=0, max=25,
        default=0, precision=2,
        description="Number total of revolutions in X axis"
    )
    camera_revol_y: FloatProperty(
        name="Y", min=0, max=25,
        default=0, precision=2,
        description="Number total of revolutions in Y axis"
    )
    camera_revol_z: FloatProperty(
        name="Z", min=0, max=25,
        default=1, precision=2,
        description="Number total of revolutions in Z axis"
    )
    inverse_x: BoolProperty(
        name="-X",
        description="Inverse rotation",
        default=False
    )
    inverse_y: BoolProperty(
        name="-Y",
        description="Inverse rotation",
        default=False
    )
    inverse_z: BoolProperty(
        name="-Z",
        description="Inverse rotation",
        default=False
    )
    use_cursor: BoolProperty(
        name="Use cursor position",
        description="Use cursor position instead of object origin",
        default=False
    )
    back_forw: BoolProperty(
        name="Back and forward",
        description="Create back and forward animation",
        default=False
    )
    dolly_zoom: EnumProperty(
        items=(
            ('0', "None", ""),
            ('1', "Dolly zoom", ""),
            ('2', "Dolly zoom B/F", "")
        ),
        name="Lens Effects",
        description="Create a camera lens movement"
    )
    camera_from_lens: FloatProperty(
        name="From",
        min=1, max=500, default=35,
        precision=3,
        description="Start lens value"
    )
    camera_to_lens: FloatProperty(
        name="To",
        min=1, max=500,
        default=35, precision=3,
        description="End lens value"
    )
    track: BoolProperty(
        name="Create track constraint",
        description="Add a track constraint to the camera",
        default=False
    )
    reset_cam_anim: BoolProperty(
        name="Clear Camera",
        description="Clear previous camera animations if there are any\n"
        "(For instance, previous Dolly Zoom)",
        default=False
    )


# ------------------------------------------------------
# UI Class
# ------------------------------------------------------
class CAMERATURN_PT_ui(Panel):
    bl_idname = "CAMERA_TURN_PT_main"
    bl_label = "Turnaround Camera"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Animate"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        turn_camera = scene.turn_camera

        try:
            scene.camera.name
        except AttributeError:
            row = layout.row(align=False)
            row.label(text="No defined camera for scene", icon="INFO")
            return

        if context.active_object is not None:
            if context.active_object.type != 'CAMERA':
                buf = context.active_object.name
                row = layout.row(align=True)
                row.operator("object.rotate_around", icon='OUTLINER_DATA_CAMERA')
                box = row.box()
                box.scale_y = 0.5
                box.label(text=buf, icon='MESH_DATA')
                row = layout.row(align=False)
                row.prop(scene, "camera")

                layout.label(text="Rotation:")
                row = layout.row(align=True)
                row.prop(scene, "frame_start")
                row.prop(scene, "frame_end")

                col = layout.column(align=True)
                split = col.split(factor=0.85, align=True)
                split.prop(turn_camera, "camera_revol_x")
                split.prop(turn_camera, "inverse_x", toggle=True)
                split = col.split(factor=0.85, align=True)
                split.prop(turn_camera, "camera_revol_y")
                split.prop(turn_camera, "inverse_y", toggle=True)
                split = col.split(factor=0.85, align=True)
                split.prop(turn_camera, "camera_revol_z")
                split.prop(turn_camera, "inverse_z", toggle=True)

                col = layout.column(align=True)
                col.label(text="Options:")
                row = col.row(align=True)
                row.prop(turn_camera, "back_forw", toggle=True)
                row.prop(turn_camera, "reset_cam_anim", toggle=True)
                col.prop(turn_camera, "track", toggle=True)
                col.prop(turn_camera, "use_cursor", toggle=True)

                row = layout.row()
                row.prop(turn_camera, "dolly_zoom")
                if turn_camera.dolly_zoom != "0":
                    row = layout.row(align=True)
                    row.prop(turn_camera, "camera_from_lens")
                    row.prop(turn_camera, "camera_to_lens")

            else:
                buf = "No valid object selected"
                layout.label(text=buf, icon='MESH_DATA')


# ------------------------------------------------------
# Registration
# ------------------------------------------------------
classes = (
    CAMERATURN_OT_RunAction,
    CAMERATURN_PT_ui,
    CAMERATURN_Props
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.turn_camera = PointerProperty(type=CAMERATURN_Props)


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    del bpy.types.Scene.turn_camera


if __name__ == "__main__":
    register()
