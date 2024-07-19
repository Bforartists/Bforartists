import bpy
from .. import __package__ as base_package

from ..functions.poll import basic_poll
from ..functions.set import add_boolean_modifier, object_visibility_set, create_slice
from ..functions.list import list_candidate_objects


#### ------------------------------ /brush_boolean/ ------------------------------ ####

class BrushBoolean():
    def execute(self, context):
        prefs = bpy.context.preferences.addons[base_package].preferences

        canvas = bpy.context.active_object
        cutters = list_candidate_objects(context)

        if self.mode == "SLICE":
            # Create Slices
            slices = []
            for i in range(len(cutters)):
                create_slice(context, canvas, slices, modifier=True)

            for cutter, slice in zip(cutters, slices):
                # add_modifiers_on_slices
                add_boolean_modifier(slice, cutter, "INTERSECT", prefs.solver)

        for cutter in cutters:
            # hide_cutter
            cutter.hide_render = True
            cutter.display_type = 'WIRE' if prefs.wireframe else 'BOUNDS'
            object_visibility_set(cutter, value=False)
            if prefs.parent and cutter.parent == None:
                cutter.parent = canvas
                cutter.matrix_parent_inverse = canvas.matrix_world.inverted()

            # cutters_collection
            collection_name = "boolean_cutters"
            cutters_collection = bpy.data.collections.get(collection_name)
            if cutters_collection is None:
                cutters_collection = bpy.data.collections.new(collection_name)
                context.scene.collection.children.link(cutters_collection)
                cutters_collection.hide_viewport = True
                cutters_collection.hide_render = True
                cutters_collection.color_tag = 'COLOR_01'
                bpy.context.view_layer.layer_collection.children[collection_name].exclude = True

            if cutters_collection not in cutter.users_collection:
                cutters_collection.objects.link(cutter)

            # Add Modifier
            add_boolean_modifier(canvas, cutter, "DIFFERENCE" if self.mode == "SLICE" else self.mode, prefs.solver)

            # add_boolean_properties
            canvas.booleans.canvas = True
            cutter.booleans.cutter = self.mode.capitalize()

        bpy.context.view_layer.objects.active = canvas
        return {'FINISHED'}

    def invoke(self, context, event):
        if len(context.selected_objects) < 2:
            self.report({'ERROR'}, "Boolean operator needs at least two objects selected")
            return {'CANCELLED'}

        return self.execute(context)


class OBJECT_OT_boolean_brush_union(bpy.types.Operator, BrushBoolean):
    bl_idname = "object.boolean_brush_union"
    bl_label = "Boolean Cutter Union"
    bl_description = "Merge selected objects into active one"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(context)

    mode = "UNION"


class OBJECT_OT_boolean_brush_intersect(bpy.types.Operator, BrushBoolean):
    bl_idname = "object.boolean_brush_intersect"
    bl_label = "Boolean Cutter Intersection"
    bl_description = "Only keep the parts of the active object that are interesecting selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(context)

    mode = "INTERSECT"


class OBJECT_OT_boolean_brush_difference(bpy.types.Operator, BrushBoolean):
    bl_idname = "object.boolean_brush_difference"
    bl_label = "Boolean Cutter Difference"
    bl_description = "Subtract selected objects from active one"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(context)

    mode = "DIFFERENCE"


class OBJECT_OT_boolean_brush_slice(bpy.types.Operator, BrushBoolean):
    bl_idname = "object.boolean_brush_slice"
    bl_label = "Boolean Cutter Slice"
    bl_description = "Slice active object along the selected ones. Will create slices as separate objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(context)

    mode = "SLICE"



#### ------------------------------ /auto_boolean/ ------------------------------ ####

class AutoBoolean:
    def execute(self, context):
        prefs = bpy.context.preferences.addons[base_package].preferences

        canvas = bpy.context.active_object
        cutters = list_candidate_objects(context)

        if self.mode == "SLICE":
            # Create Slices
            slices = []
            for i in range(len(cutters)):
                create_slice(context, canvas, slices)

            for cutter, slice in zip(cutters, slices):
                # add_modifiers_to_slices
                add_boolean_modifier(slice, cutter, "INTERSECT", prefs.solver, apply=True)

        for cutter in cutters:
            # Add Modifier
            mode = "DIFFERENCE" if self.mode == "SLICE" else self.mode
            add_boolean_modifier(canvas, cutter, mode, prefs.solver, apply=True)

            # Delete Cutter
            bpy.data.objects.remove(cutter)

            if self.mode == "SLICE":
                slice.select_set(True)
                context.view_layer.objects.active = slice

        return {'FINISHED'}

    def invoke(self, context, event):
        if len(context.selected_objects) < 2:
            self.report({'ERROR'}, "Boolean operator needs at least two objects selected")
            return {'CANCELLED'}

        return self.execute(context)


class OBJECT_OT_boolean_auto_union(bpy.types.Operator, AutoBoolean):
    bl_idname = "object.boolean_auto_union"
    bl_label = "Boolean Union"
    bl_description = "Merge selected objects into active one"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(context)

    mode = "UNION"


class OBJECT_OT_boolean_auto_difference(bpy.types.Operator, AutoBoolean):
    bl_idname = "object.boolean_auto_difference"
    bl_label = "Boolean Difference"
    bl_description = "Subtract selected objects from active one"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(context)

    mode = "DIFFERENCE"


class OBJECT_OT_boolean_auto_intersect(bpy.types.Operator, AutoBoolean):
    bl_idname = "object.boolean_auto_intersect"
    bl_label = "Boolean Intersect"
    bl_description = "Only keep the parts of the active object that are interesecting selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(context)

    mode = "INTERSECT"


class OBJECT_OT_boolean_auto_slice(bpy.types.Operator, AutoBoolean):
    bl_idname = "object.boolean_auto_slice"
    bl_label = "Boolean Slice"
    bl_description = "Slice active object along the selected ones. Will create slices as separate objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(context)

    mode = "SLICE"



#### ------------------------------ REGISTRATION ------------------------------ ####

addon_keymaps = []

classes = [
    OBJECT_OT_boolean_brush_union,
    OBJECT_OT_boolean_brush_difference,
    OBJECT_OT_boolean_brush_intersect,
    OBJECT_OT_boolean_brush_slice,

    OBJECT_OT_boolean_auto_union,
    OBJECT_OT_boolean_auto_difference,
    OBJECT_OT_boolean_auto_intersect,
    OBJECT_OT_boolean_auto_slice,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # KEYMAP
    addon = bpy.context.window_manager.keyconfigs.addon
    km = addon.keymaps.new(name="Object Mode")

    # brush_operators
    kmi = km.keymap_items.new(OBJECT_OT_boolean_brush_union.bl_idname, 'NUMPAD_PLUS', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new(OBJECT_OT_boolean_brush_difference.bl_idname, 'NUMPAD_MINUS', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new(OBJECT_OT_boolean_brush_intersect.bl_idname, 'NUMPAD_ASTERIX', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new(OBJECT_OT_boolean_brush_slice.bl_idname, 'NUMPAD_SLASH', 'PRESS', ctrl=True)

    # auto_operators
    kmi = km.keymap_items.new(OBJECT_OT_boolean_auto_union.bl_idname, 'NUMPAD_PLUS', 'PRESS', ctrl=True, shift=True)
    kmi = km.keymap_items.new(OBJECT_OT_boolean_auto_difference.bl_idname, 'NUMPAD_MINUS', 'PRESS', ctrl=True, shift=True)
    kmi = km.keymap_items.new(OBJECT_OT_boolean_auto_intersect.bl_idname, 'NUMPAD_ASTERIX', 'PRESS', ctrl=True, shift=True)
    kmi = km.keymap_items.new(OBJECT_OT_boolean_auto_slice.bl_idname, 'NUMPAD_SLASH', 'PRESS', ctrl=True, shift=True)
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
