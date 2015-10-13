import bpy
from bpy.props import IntProperty

from . core import stored_view_factory, DataStore
from . ui import init_draw


class VIEW3D_stored_views_save(bpy.types.Operator):
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


class VIEW3D_stored_views_set(bpy.types.Operator):
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


class VIEW3D_stored_views_delete(bpy.types.Operator):
    bl_idname = "stored_views.delete"
    bl_label = "Delete"
    bl_description = "Delete this view"

    index = bpy.props.IntProperty()

    def execute(self, context):
        data = DataStore()
        data.delete(self.index)

        return {'FINISHED'}
