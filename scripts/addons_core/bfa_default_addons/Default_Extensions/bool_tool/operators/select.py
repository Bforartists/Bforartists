import bpy
from .. import __package__ as base_package

from ..functions.poll import (
    basic_poll,
    active_modifier_poll,
    is_canvas,
)
from ..functions.list import (
    list_selected_cutters,
    list_selected_canvases,
    list_canvas_cutters,
    list_cutter_users,
)


#### ------------------------------ OPERATORS ------------------------------ ####

# Select Cutter Canvas
class OBJECT_OT_select_cutter_canvas(bpy.types.Operator):
    bl_idname = "object.select_cutter_canvas"
    bl_label = "Select Boolean Canvas"
    bl_description = "Select all the objects that use selected objects as boolean cutters"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(context) and context.active_object.booleans.cutter

    def execute(self, context):
        cutters = list_selected_cutters(context)
        canvases = list_cutter_users(cutters)

        # Select Canvases
        bpy.ops.object.select_all(action='DESELECT')
        for canvas in canvases:
            canvas.select_set(True)

        return {'FINISHED'}


# Select All Cutters
class OBJECT_OT_boolean_select_all(bpy.types.Operator):
    bl_idname = "object.boolean_select_all"
    bl_label = "Select Boolean Cutters"
    bl_description = "Select all boolean cutters affecting active object"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(context) and is_canvas(context.active_object)

    def execute(self, context):
        canvases = list_selected_canvases(context)
        cutters, __ = list_canvas_cutters(canvases)

        # select_cutters
        bpy.ops.object.select_all(action='DESELECT')
        for cutter in cutters:
            cutter.select_set(True)

        return {'FINISHED'}


# Select Modifier Object
class OBJECT_OT_boolean_select_cutter(bpy.types.Operator):
    bl_idname = "object.boolean_select_cutter"
    bl_label = "Select Boolean Cutter"
    bl_description = "Select object that is used as boolean cutter by this modifier"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        prefs = bpy.context.preferences.addons[base_package].preferences
        return (basic_poll(context) and active_modifier_poll(context) and
                context.area.type == 'PROPERTIES' and context.space_data.context == 'MODIFIER' and
                prefs.double_click)

    def execute(self, context):
        modifier = context.object.modifiers.active
        if modifier and modifier.type == "BOOLEAN":
            cutter = modifier.object

            bpy.ops.object.select_all(action='DESELECT')
            cutter.select_set(True)
            context.view_layer.objects.active = cutter

        return {'FINISHED'}



#### ------------------------------ REGISTRATION ------------------------------ ####

addon_keymaps = []

classes = [
    OBJECT_OT_select_cutter_canvas,
    OBJECT_OT_boolean_select_all,
    OBJECT_OT_boolean_select_cutter,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # KEYMAP
    addon = bpy.context.window_manager.keyconfigs.addon
    km = addon.keymaps.new(name="Property Editor", space_type='PROPERTIES')
    kmi = km.keymap_items.new("object.boolean_select_cutter", type='LEFTMOUSE', value='DOUBLE_CLICK')
    kmi.active = True
    addon_keymaps.append(km)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    # KEYMAP
    for km in addon_keymaps:
        for kmi in km.keymap_items:
            km.keymap_items.remove(kmi)
    addon_keymaps.clear()
