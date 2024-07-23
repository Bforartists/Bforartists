import bpy
from .. import __package__ as base_package

from ..functions.poll import (
    basic_poll,
)
from ..functions.set import (
    object_visibility_set,
    delete_empty_collection,
)
from ..functions.list import (
    list_canvases,
    list_selected_cutters,
    list_canvas_cutters,
    list_canvas_slices,
    list_cutter_users,
    list_unused_cutters,
)


#### ------------------------------ OPERATORS ------------------------------ ####

# Toggle Boolean Cutter
class OBJECT_OT_boolean_toggle_cutter(bpy.types.Operator):
    bl_idname = "object.boolean_toggle_cutter"
    bl_label = "Toggle Boolean Cutter"
    bl_description = "Toggle this boolean cutter. If cutter is the active object it will be toggled for every canvas that uses it"
    bl_options = {'UNDO'}

    method: bpy.props.EnumProperty(
        name = "Method",
        items = (('ALL', "All", "Remove cutter from all canvases that use it"),
                 ('SPECIFIED', "Specified", "Remove cutter from specified canvas")),
        default = 'ALL',
    )

    specified_cutter: bpy.props.StringProperty(
    )
    specified_canvas: bpy.props.StringProperty(
    )

    @classmethod
    def poll(cls, context):
        return basic_poll(context)

    def execute(self, context):
        if self.method == 'SPECIFIED':
            canvases = [bpy.data.objects[self.specified_canvas]]
            cutters = [bpy.data.objects[self.specified_cutter]]
            slices = list_canvas_slices(canvases)
        elif self.method == 'ALL':
            canvases = list_canvases()
            cutters = list_selected_cutters(context)

        if cutters:
            for canvas in canvases:
                # toggle_slices_visibility (for_all_method)
                if canvas.booleans.slice == True:
                    if any(modifier.object in cutters for modifier in canvas.modifiers):
                        canvas.hide_viewport = not canvas.hide_viewport
                        canvas.hide_render = not canvas.hide_render

                # Toggle Modifiers
                for modifier in canvas.modifiers:
                    if "boolean_" in modifier.name:
                        if modifier.object in cutters:
                            modifier.show_viewport = not modifier.show_viewport
                            modifier.show_render = not modifier.show_render


            if self.method == 'SPECIFIED':
                # toggle_slices_visibility (for_specified_method)
                for slice in slices:
                    for mod in slice.modifiers:
                        if mod.type == 'BOOLEAN' and mod.object in cutters:
                            slice.hide_viewport = not slice.hide_viewport
                            slice.hide_render = not slice.hide_render
                            mod.show_viewport = not mod.show_viewport
                            mod.show_render = not mod.show_render

                # hide_cutter_if_not_used_by_any_visible_modifiers
                other_canvases = list_canvases()
                for obj in other_canvases:
                    if obj not in canvases:
                        if any(modifier.object in cutters and modifier.show_viewport for modifier in obj.modifiers):
                            cutters[:] = [cutter for cutter in cutters if cutter not in [modifier.object for modifier in obj.modifiers]]

                for cutter in cutters:
                    cutter.hide_viewport = not cutter.hide_viewport

        else:
            self.report({'INFO'}, "Boolean cutters are not selected")

        return {'FINISHED'}


# Remove Boolean Cutter
class OBJECT_OT_boolean_remove_cutter(bpy.types.Operator):
    bl_idname = "object.boolean_remove_cutter"
    bl_label = "Remove Boolean Cutter"
    bl_description = "Remove this boolean cutter. If cutter is the active object it will be removed from every canvas that uses it"
    bl_options = {'UNDO'}

    method: bpy.props.EnumProperty(
        name = "Method",
        items = (('ALL', "All", "Remove cutter from all canvases that use it"),
                 ('SPECIFIED', "Specified", "Remove cutter from specified canvas")),
        default = 'ALL',
    )

    specified_cutter: bpy.props.StringProperty(
    )
    specified_canvas: bpy.props.StringProperty(
    )

    @classmethod
    def poll(cls, context):
        return basic_poll(context)

    def execute(self, context):
        prefs = bpy.context.preferences.addons[base_package].preferences
        leftovers = []

        if self.method == 'SPECIFIED':
            canvases = [bpy.data.objects[self.specified_canvas]]
            cutters = [bpy.data.objects[self.specified_cutter]]
            slices = list_canvas_slices(canvases)
        elif self.method == 'ALL':
            canvases = list_canvases()
            cutters = list_selected_cutters(context)

        if cutters:
            # Remove Modifiers
            for canvas in canvases:
                for modifier in canvas.modifiers:
                    if "boolean_" in modifier.name:
                        if modifier.object in cutters:
                            canvas.modifiers.remove(modifier)

                # remove_canvas_property_if_needed
                other_cutters, __ = list_canvas_cutters([canvas])
                if len(other_cutters) == 0:
                    canvas.booleans.canvas = False

                # Remove Slices (for_all_method)
                if canvas.booleans.slice == True:
                    bpy.data.objects.remove(canvas)


            if self.method == 'SPECIFIED':
                # Remove Slices (for_specified_method)
                for slice in slices:
                    for mod in slice.modifiers:
                        if mod.type == 'BOOLEAN' and mod.object in cutters:
                            bpy.data.objects.remove(slice)

                cutters, leftovers = list_unused_cutters(cutters, canvases, do_leftovers=True)


            # Restore Orphaned Cutters
            for cutter in cutters:
                # restore_visibility
                cutter.display_type = 'TEXTURED'
                object_visibility_set(cutter, value=True)
                cutter.hide_render = False
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
            if prefs.parent and leftovers != None:
                for cutter in leftovers:
                    if cutter.parent in canvases:
                        other_canvases = list_cutter_users([cutter])
                        cutter.parent = other_canvases[0]

        else:
            self.report({'INFO'}, "Boolean cutters are not selected")

        return {'FINISHED'}


# Apply Boolean Cutter
class OBJECT_OT_boolean_apply_cutter(bpy.types.Operator):
    bl_idname = "object.boolean_apply_cutter"
    bl_label = "Apply Boolean Cutter"
    bl_description = "Apply this boolean cutter. If cutter is the active object it will be applied to every canvas that uses it"
    bl_options = {'UNDO'}

    method: bpy.props.EnumProperty(
        name = "Method",
        items = (('ALL', "All", "Remove cutter from all canvases that use it"),
                 ('SPECIFIED', "Specified", "Remove cutter from specified canvas")),
        default = 'ALL',
    )

    specified_cutter: bpy.props.StringProperty(
    )
    specified_canvas: bpy.props.StringProperty(
    )

    @classmethod
    def poll(cls, context):
        return basic_poll(context)

    def execute(self, context):
        prefs = bpy.context.preferences.addons[base_package].preferences
        leftovers = []

        if self.method == 'SPECIFIED':
            canvases = [bpy.data.objects[self.specified_canvas]]
            cutters = [bpy.data.objects[self.specified_cutter]]
            slices = list_canvas_slices(canvases)
        elif self.method == 'ALL':
            canvases = list_canvases()
            cutters = list_selected_cutters(context)

        if cutters:
            # Apply Modifiers
            for canvas in canvases:
                context.view_layer.objects.active = canvas
                for mod in canvas.modifiers:
                    if "boolean_" in mod.name:
                        if mod.object in cutters:
                            try:
                                bpy.ops.object.modifier_apply(modifier=mod.name)
                            except:
                                context.active_object.data = context.active_object.data.copy()
                                bpy.ops.object.modifier_apply(modifier=mod.name)

                # remove_canvas_property_if_needed
                other_cutters, __ = list_canvas_cutters([canvas])
                if len(other_cutters) == 0:
                    canvas.booleans.canvas = False
                canvas.booleans.slice = False


            if self.method == 'SPECIFIED':
                # Apply Modifier for Slices (for_specified_method)
                for slice in slices:
                    for mod in slice.modifiers:
                        if mod.type == 'BOOLEAN' and mod.object in cutters:
                            context.view_layer.objects.active = slice
                            bpy.ops.object.modifier_apply(modifier=mod.name)

                cutters, leftovers = list_unused_cutters(cutters, canvases, do_leftovers=True)


            # Purge Orphaned Cutters
            for cutter in cutters:
                orphaned_mesh = cutter.data
                bpy.data.objects.remove(cutter)
                bpy.data.meshes.remove(orphaned_mesh)

            # purge_empty_collection
            delete_empty_collection()


            # Change Leftover Cutter Parent
            if prefs.parent and leftovers != None:
                for cutter in leftovers:
                    if cutter.parent in canvases:
                        other_canvases = list_cutter_users([cutter])
                        cutter.parent = other_canvases[0]

        else:
            self.report({'INFO'}, "Boolean cutters are not selected")

        return {'FINISHED'}



#### ------------------------------ REGISTRATION ------------------------------ ####

addon_keymaps = []

classes = [
    OBJECT_OT_boolean_toggle_cutter,
    OBJECT_OT_boolean_remove_cutter,
    OBJECT_OT_boolean_apply_cutter,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # KEYMAP
    addon = bpy.context.window_manager.keyconfigs.addon
    km = addon.keymaps.new(name="Object Mode")
    kmi = km.keymap_items.new("object.boolean_apply_cutter", 'NUMPAD_ENTER', 'PRESS', ctrl=True)
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
