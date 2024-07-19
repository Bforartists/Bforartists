import bpy, itertools
from .. import __package__ as base_package

from ..functions.poll import (
    basic_poll,
    is_canvas
)
from ..functions.set import (
    object_visibility_set,
    delete_empty_collection,
)
from ..functions.list import (
    list_canvases,
    list_canvas_slices,
    list_canvas_cutters,
    list_cutter_users,
    list_selected_canvases,
    list_unused_cutters,
)


#### ------------------------------ OPERATORS ------------------------------ ####

# Toggle All Cutters
class OBJECT_OT_boolean_toggle_all(bpy.types.Operator):
    bl_idname = "object.boolean_toggle_all"
    bl_label = "Toggle Boolean Cutters"
    bl_description = "Toggle all boolean cutters affecting selected canvases"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(context) and is_canvas(context.active_object)

    def execute(self, context):
        canvases = list_selected_canvases(context)
        cutters, modifiers = list_canvas_cutters(canvases)
        slices = list_canvas_slices(canvases)

        # Toggle Modifiers
        for mod in modifiers:
            mod.show_viewport = not mod.show_viewport
            mod.show_render = not mod.show_render

        # Hide Slices
        for slice in slices:
            slice.hide_viewport = not slice.hide_viewport
            for mod in slice.modifiers:
                if mod.type == 'BOOLEAN' and mod.object in cutters:
                    mod.show_viewport = not mod.show_viewport
                    mod.show_render = not mod.show_render


        # Hide Unused Cutters
        other_canvases = list_canvases()
        for obj in other_canvases:
            if obj not in canvases:
                if any(modifier.object in cutters and modifier.show_viewport for modifier in obj.modifiers):
                    cutters[:] = [cutter for cutter in cutters if cutter not in [modifier.object for modifier in obj.modifiers]]

        for cutter in cutters:
            cutter.hide_viewport = not cutter.hide_viewport

        return {'FINISHED'}


# Remove All Cutters
class OBJECT_OT_boolean_remove_all(bpy.types.Operator):
    bl_idname = "object.boolean_remove_all"
    bl_label = "Remove Boolean Cutters"
    bl_description = "Remove all boolean cutters from selected canvases"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(context) and is_canvas(context.active_object)

    def execute(self, context):
        prefs = bpy.context.preferences.addons[base_package].preferences

        canvases = list_selected_canvases(context)
        cutters, __ = list_canvas_cutters(canvases)
        slices = list_canvas_slices(canvases)

        # Remove Slices
        for slice in slices:
            bpy.data.objects.remove(slice)
            if slice in canvases:
                canvases.remove(slice)

        for canvas in canvases:
            # Remove Modifiers
            for modifier in canvas.modifiers:
                if modifier.type == 'BOOLEAN' and "boolean_" in modifier.name:
                    if modifier.object in cutters:
                        canvas.modifiers.remove(modifier)

            # remove_boolean_properties
            if canvas.booleans.canvas == True:
                canvas.booleans.canvas = False


        # Restore Orphaned Cutters
        unused_cutters, leftovers = list_unused_cutters(cutters, canvases, slices, do_leftovers=True)

        for cutter in unused_cutters:
            # restore_visibility
            cutter.display_type = 'TEXTURED'
            object_visibility_set(cutter, value=True)
            cutter.hide_render = False
            if cutter.booleans.cutter:
                cutter.booleans.cutter = ""

            # remove_parent_&_collection
            if prefs.parent and cutter.parent in canvases:
                cutter.parent = None

            cutters_collection = bpy.data.collections.get("boolean_cutters")
            if cutters_collection in cutter.users_collection:
                bpy.data.collections.get("boolean_cutters").objects.unlink(cutter)

        # purge_empty_collection
        delete_empty_collection()


        # Change Leftover Cutter Parent
        if prefs.parent:
            for cutter in leftovers:
                if cutter.parent in canvases:
                    other_canvases = list_cutter_users([cutter])
                    cutter.parent = other_canvases[0]

        return {'FINISHED'}


# Apply All Cutters
class OBJECT_OT_boolean_apply_all(bpy.types.Operator):
    bl_idname = "object.boolean_apply_all"
    bl_label = "Apply All Boolean Cutters"
    bl_description = "Apply all boolean cutters on selected canvases"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(context) and is_canvas(context.active_object)

    def execute(self, context):
        prefs = bpy.context.preferences.addons[base_package].preferences

        canvases = list_selected_canvases(context)
        cutters, __ = list_canvas_cutters(canvases)
        slices = list_canvas_slices(canvases)

        # Apply Modifiers
        for canvas in itertools.chain(canvases, slices):
            bpy.context.view_layer.objects.active = canvas
            for modifier in canvas.modifiers:
                if "boolean_" in modifier.name:
                    try:
                        bpy.ops.object.modifier_apply(modifier=modifier.name)
                    except:
                        context.active_object.data = context.active_object.data.copy()
                        bpy.ops.object.modifier_apply(modifier=modifier.name)

            # remove_boolean_properties
            canvas.booleans.canvas = False
            canvas.booleans.slice = False


        # Purge Orphaned Cutters
        unused_cutters, leftovers = list_unused_cutters(cutters, canvases, slices, do_leftovers=True)

        purged_cutters = []
        for cutter in unused_cutters:
            if cutter not in purged_cutters:
                orphaned_mesh = cutter.data
                bpy.data.objects.remove(cutter)
                bpy.data.meshes.remove(orphaned_mesh)
                purged_cutters.append(cutter)

        # purge_empty_collection
        delete_empty_collection()


        # Change Leftover Cutter Parent
        if prefs.parent:
            for cutter in leftovers:
                if cutter.parent in canvases:
                    other_canvases = list_cutter_users([cutter])
                    cutter.parent = other_canvases[0]

        return {'FINISHED'}



#### ------------------------------ REGISTRATION ------------------------------ ####

addon_keymaps = []

classes = [
    OBJECT_OT_boolean_toggle_all,
    OBJECT_OT_boolean_remove_all,
    OBJECT_OT_boolean_apply_all,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # KEYMAP
    addon = bpy.context.window_manager.keyconfigs.addon
    km = addon.keymaps.new(name="Object Mode")
    kmi = km.keymap_items.new("object.boolean_apply_all", 'NUMPAD_ENTER', 'PRESS', shift=True, ctrl=True)
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
