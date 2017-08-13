# gpl authors: nfloyd, Francesco Siddi

import bpy
from bpy.props import (
        IntProperty,
        StringProperty,
        )
from bpy.types import Operator
from .core import (
        stored_view_factory,
        DataStore,
        )
from .ui import init_draw


class VIEW3D_stored_views_save(Operator):
    bl_idname = "stored_views.save"
    bl_label = "Save Current"
    bl_description = "Save the view 3d current state"

    index = IntProperty()

    def execute(self, context):
        mode = context.scene.stored_views.mode
        sv = stored_view_factory(mode, self.index)
        sv.save()
        context.scene.stored_views.view_modified = False
        init_draw(context)

        return {'FINISHED'}


class VIEW3D_stored_views_set(Operator):
    bl_idname = "stored_views.set"
    bl_label = "Set"
    bl_description = "Update the view 3D according to this view"

    index = IntProperty()

    def execute(self, context):
        mode = context.scene.stored_views.mode
        sv = stored_view_factory(mode, self.index)
        sv.set()
        context.scene.stored_views.view_modified = False
        init_draw(context)

        return {'FINISHED'}


class VIEW3D_stored_views_delete(Operator):
    bl_idname = "stored_views.delete"
    bl_label = "Delete"
    bl_description = "Delete this view"

    index = IntProperty()

    def execute(self, context):
        data = DataStore()
        data.delete(self.index)

        return {'FINISHED'}


class VIEW3D_New_Camera_to_View(Operator):
    bl_idname = "stored_views.newcamera"
    bl_label = "New Camera To View"
    bl_description = "Add a new Active Camera and align it to this view"

    def execute(self, context):
        try:
            # check for operator's poll (there is no active object, for instance)
            if bpy.ops.object.mode_set.poll():
                bpy.ops.object.mode_set(mode='OBJECT')

            bpy.ops.object.camera_add(view_align=True)
            cam = bpy.context.active_object
            bpy.ops.view3d.object_as_camera()
            bpy.ops.view3d.camera_to_view()

            # this will name the Camera Object
            if 'View_Camera' not in context.scene.objects:
                cam.name = "View_Camera"
            else:
                cam.name = "View_Camera.000"

            return {'FINISHED'}
        except:
            self.report({'WARNING'},
                        "Operation Cancelled. New Camera to View failed to add a new camera")
            return {'CANCELLED'}


# Camera marker & switcher by Fsiddi
class SetSceneCamera(Operator):
    bl_idname = "cameraselector.set_scene_camera"
    bl_label = "Set Scene Camera"
    bl_description = "Set chosen camera as the scene's active camera"

    chosen_camera = StringProperty()
    select_chosen = False

    def execute(self, context):
        chosen_camera = bpy.data.objects.get(self.chosen_camera, None)
        scene = context.scene
        if not chosen_camera:
            self.report({'ERROR'}, "Camera %s not found.")
            return {'CANCELLED'}

        if self.select_chosen:
            if context.mode == 'OBJECT':
                for o in context.selected_objects:
                    o.select = False
                chosen_camera.select = True
                scene.objects.active = chosen_camera
            for c in [o for o in scene.objects if o.type == 'CAMERA']:
                c.hide = (c != chosen_camera)
        scene.camera = chosen_camera
        bpy.context.scene.objects.active = chosen_camera
        bpy.ops.object.select_all(action='TOGGLE')
        chosen_camera.select = True
        return {'FINISHED'}

    def invoke(self, context, event):
        if event.ctrl:
            self.select_chosen = True

        return self.execute(context)


class AddCameraMarker(Operator):
    bl_idname = "cameraselector.add_camera_marker"
    bl_label = "Add Camera Marker"
    bl_description = "Add a timeline marker bound to chosen camera"

    chosen_camera = StringProperty()

    def execute(self, context):
        chosen_camera = bpy.data.objects.get(self.chosen_camera, None)
        scene = context.scene
        if not chosen_camera:
            self.report({'WARNING'}, "Camera %s not found. Operation Cancelled")
            return {'CANCELLED'}

        current_frame = scene.frame_current
        marker = None
        for m in reversed(sorted(filter(lambda m: m.frame <= current_frame,
                                        scene.timeline_markers),
                                 key=lambda m: m.frame)):
            marker = m
            break
        if marker and (marker.camera == chosen_camera):
            # Cancel if the last marker at or immediately before
            # current frame is already bound to the camera.
            return {'CANCELLED'}

        marker_name = "F_%02d_%s" % (current_frame, self.chosen_camera)
        if marker and (marker.frame == current_frame):
            # Reuse existing marker at current frame to avoid
            # overlapping bound markers.
            marker.name = marker_name
        else:
            marker = scene.timeline_markers.new(marker_name)
        marker.frame = scene.frame_current
        marker.camera = chosen_camera
        marker.select = True

        for other_marker in [m for m in scene.timeline_markers if m != marker]:
            other_marker.select = False

        return {'FINISHED'}
