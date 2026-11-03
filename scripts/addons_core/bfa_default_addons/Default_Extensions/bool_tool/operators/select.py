import bpy

from ..functions.canvas import (
    is_canvas,
    list_selected_canvases,
    list_canvas_cutters,
)
from ..functions.cutter import (
    list_selected_cutters,
    list_cutter_users,
)
from ..functions.poll import (
    basic_poll,
)


#### ------------------------------ OPERATORS ------------------------------ ####

# Select Cutter Canvas
class OBJECT_OT_select_cutter_canvas(bpy.types.Operator):
    bl_idname = "object.select_cutter_canvas"
    bl_label = "Select Boolean Canvas"
    bl_description = "Select all canvases that use selected objects as Boolean cutters"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(cls, context, check_active=True) and context.active_object.booleans.cutter

    def execute(self, context):
        cutters = list_selected_cutters(context)
        canvases = list_cutter_users(cutters).keys()

        for obj in context.scene.objects:
            obj.select_set(False)

        # Select canvases.
        for canvas in canvases:
            if not canvas.booleans.slice:
                canvas.select_set(True)

        return {'FINISHED'}


# Select All Cutters
class OBJECT_OT_boolean_select_all(bpy.types.Operator):
    bl_idname = "object.boolean_select_all"
    bl_label = "Select Boolean Cutters"
    bl_description = "Select all Boolean cutters affecting selected canvases"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(cls, context, check_active=True) and is_canvas(context.active_object)

    def execute(self, context):
        canvases = list_selected_canvases(context)
        cutters, __ = list_canvas_cutters(canvases)

        for obj in context.scene.objects:
            obj.select_set(False)

        # Select cutters.
        for cutter in cutters:
            cutter.select_set(True)

        return {'FINISHED'}


# Select Modifier Object
class OBJECT_OT_boolean_select_cutter(bpy.types.Operator):
    bl_idname = "object.boolean_select_cutter"
    bl_label = "Select Boolean Cutter"
    bl_options = {'UNDO'}

    cutter: bpy.props.StringProperty()
    extend: bpy.props.BoolProperty()

    def invoke(self, context, event):
        self.extend = event.shift
        return self.execute(context)

    def execute(self, context):
        cutter = bpy.data.objects.get(self.cutter)

        if not self.extend:
            for obj in context.scene.objects:
                obj.select_set(False)

        if cutter:
            cutter.select_set(True)

        return {'FINISHED'}



#### ------------------------------ REGISTRATION ------------------------------ ####

addon_keymaps = []

classes = (
    OBJECT_OT_select_cutter_canvas,
    OBJECT_OT_boolean_select_all,
    OBJECT_OT_boolean_select_cutter,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
