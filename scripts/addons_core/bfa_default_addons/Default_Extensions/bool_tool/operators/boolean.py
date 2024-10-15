import bpy
from .. import __package__ as base_package

from ..functions.poll import (
    basic_poll,
    is_linked,
)
from ..functions.object import (
    convert_to_mesh,
    add_boolean_modifier,
    set_cutter_properties,
    change_parent,
    create_slice,
    delete_cutter,
)
from ..functions.list import (
    list_candidate_objects,
    list_cutter_users,
    list_pre_boolean_modifiers,
)


class ModifierProperties():
    material_mode: bpy.props.EnumProperty(
        name = "Materials",
        description = "Method for setting materials on the new faces",
        items = (('INDEX', "Index Based", "Set the material on new faces based on the order of the material slot lists. If a material doesn’t exist on the\n"
                  "modifier object, the face will use the same material slot or the first if the object doesn’t have enough slots."),
                 ('TRANSFER', "Transfer", "Transfer materials from non-empty slots to the result mesh, adding new materials as necessary.\n"
                  "For empty slots, fall back to using the same material index as the operand mesh.")),
        default = 'INDEX',
    )
    use_self: bpy.props.BoolProperty(
        name = "Self Intersection",
        description = "Allow self-intersection in operands",
        default = False,
    )
    use_hole_tolerant: bpy.props.BoolProperty(
        name = "Hole Tolerant",
        description = "Better results when there are holes (slower)",
        default = False,
    )
    double_threshold: bpy.props.FloatProperty(
        name = "Overlap Threshold",
        description = "Threshold for checking overlapping geometry",
        subtype = 'DISTANCE',
        min = 0, max = 1, precision = 12, step = 0.0001,
        default = 0.000001,
    )

    def draw(self, context):
        prefs = bpy.context.preferences.addons[base_package].preferences

        layout = self.layout
        layout.use_property_split = True

        if prefs.solver == 'EXACT':
            layout.prop(self, "material_mode")
            layout.prop(self, "use_self")
            layout.prop(self, "use_hole_tolerant")
        elif prefs.solver == 'FAST':
            layout.prop(self, "double_threshold")



#### ------------------------------ /brush_boolean/ ------------------------------ ####

class BrushBoolean(ModifierProperties):
    def execute(self, context):
        prefs = bpy.context.preferences.addons[base_package].preferences

        canvas = context.active_object
        cutters = list_candidate_objects(self, context, canvas)

        # abort_when_no_candidate_objects
        if len(cutters) == 0:
            return {'CANCELLED'}

        # abort_when_linked
        if is_linked(context, canvas):
            self.report({'ERROR'}, "Booleans can not be performed on linked objects")
            return {'CANCELLED'}

        # abort_when_creating_cutter/canvas_loop
        canvas_canvases = list_cutter_users([canvas])
        if any(cutter in canvas_canvases for cutter in cutters):
            self.report({'ERROR'}, "Object can not cut its own cutter")
            cutters = [c for c in cutters if c not in canvas_canvases]


        for cutter in cutters:
            set_cutter_properties(context, canvas, cutter, self.mode, parent=prefs.parent, collection=prefs.use_collection)
            add_boolean_modifier(self, canvas, cutter, "DIFFERENCE" if self.mode == "SLICE" else self.mode, prefs.solver, pin=prefs.pin)

        if self.mode == "SLICE":
            # Create Slices
            slices = []
            for i in range(len(cutters)):
                create_slice(context, canvas, slices, modifier=True)

            # add_modifiers_on_slices
            for cutter, slice in zip(cutters, slices):
                add_boolean_modifier(self, slice, cutter, "INTERSECT", prefs.solver)

        context.view_layer.objects.active = canvas
        canvas.booleans.canvas = True

        return {'FINISHED'}

    def invoke(self, context, event):
        if len(context.selected_objects) < 2:
            self.report({'ERROR'}, "Boolean operator needs at least two objects selected")
            return {'CANCELLED'}

        return self.execute(context)


class OBJECT_OT_boolean_brush_union(bpy.types.Operator, BrushBoolean):
    bl_idname = "object.boolean_brush_union"
    bl_label = "Boolean Union (Brush)"
    bl_description = "Merge selected objects into active one"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(context)

    mode = "UNION"


class OBJECT_OT_boolean_brush_intersect(bpy.types.Operator, BrushBoolean):
    bl_idname = "object.boolean_brush_intersect"
    bl_label = "Boolean Intersection (Brush)"
    bl_description = "Only keep the parts of the active object that are interesecting selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(context)

    mode = "INTERSECT"


class OBJECT_OT_boolean_brush_difference(bpy.types.Operator, BrushBoolean):
    bl_idname = "object.boolean_brush_difference"
    bl_label = "Boolean Difference (Brush)"
    bl_description = "Subtract selected objects from active one"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(context)

    mode = "DIFFERENCE"


class OBJECT_OT_boolean_brush_slice(bpy.types.Operator, BrushBoolean):
    bl_idname = "object.boolean_brush_slice"
    bl_label = "Boolean Slice (Brush)"
    bl_description = "Slice active object along the selected ones. Will create slices as separate objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(context)

    mode = "SLICE"



#### ------------------------------ /auto_boolean/ ------------------------------ ####

class AutoBoolean(ModifierProperties):
    def execute(self, context):
        prefs = bpy.context.preferences.addons[base_package].preferences

        canvas = context.active_object
        cutters = list_candidate_objects(self, context, canvas)

        # abort_when_no_candidate_objects
        if len(cutters) == 0:
            return {'CANCELLED'}

        # abort_when_linked
        if is_linked(context, canvas):
            self.report({'ERROR'}, "Booleans can not be performed on linked objects")
            return {'CANCELLED'}


        # apply_modifiers
        if (prefs.apply_order == 'ALL') or (prefs.apply_order == 'BEFORE' and prefs.pin == False):
            convert_to_mesh(context, canvas)
        else:
            if canvas.data.shape_keys:
                self.report({'ERROR'}, "Modifiers can't be applied to object with shape keys")
                return {'CANCELLED'}


        if self.mode == "SLICE":
            # Create Slices
            slices = []
            for i in range(len(cutters)):
                create_slice(context, canvas, slices)

            for cutter, slice in zip(cutters, slices):
                # add_modifiers_to_slices
                add_boolean_modifier(self, slice, cutter, "INTERSECT", prefs.solver, apply=True)


        for cutter in cutters:
            # Add Modifier
            mode = "DIFFERENCE" if self.mode == "SLICE" else self.mode
            add_boolean_modifier(self, canvas, cutter, mode, prefs.solver, apply=True, pin=prefs.pin)

            # Transfer Children
            children = [obj for obj in cutter.children]
            for child in children:
                change_parent(child, canvas)

            # Delete Cutter
            delete_cutter(cutter)

            if self.mode == "SLICE":
                slice.select_set(True)
                context.view_layer.objects.active = slice


        # remove_modifiers_before_final_boolean
        if prefs.apply_order == 'BEFORE' and prefs.pin:
            modifiers = list_pre_boolean_modifiers(canvas)
            for mod in modifiers:
                bpy.ops.object.modifier_apply(modifier=mod.name)

        return {'FINISHED'}

    def invoke(self, context, event):
        if len(context.selected_objects) < 2:
            self.report({'ERROR'}, "Boolean operator needs at least two objects selected")
            return {'CANCELLED'}

        return self.execute(context)


class OBJECT_OT_boolean_auto_union(bpy.types.Operator, AutoBoolean):
    bl_idname = "object.boolean_auto_union"
    bl_label = "Boolean Union (Auto)"
    bl_description = "Merge selected objects into active one"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(context)

    mode = "UNION"


class OBJECT_OT_boolean_auto_difference(bpy.types.Operator, AutoBoolean):
    bl_idname = "object.boolean_auto_difference"
    bl_label = "Boolean Difference (Auto)"
    bl_description = "Subtract selected objects from active one"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(context)

    mode = "DIFFERENCE"


class OBJECT_OT_boolean_auto_intersect(bpy.types.Operator, AutoBoolean):
    bl_idname = "object.boolean_auto_intersect"
    bl_label = "Boolean Intersect (Auto)"
    bl_description = "Only keep the parts of the active object that are interesecting selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(context)

    mode = "INTERSECT"


class OBJECT_OT_boolean_auto_slice(bpy.types.Operator, AutoBoolean):
    bl_idname = "object.boolean_auto_slice"
    bl_label = "Boolean Slice (Auto)"
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
