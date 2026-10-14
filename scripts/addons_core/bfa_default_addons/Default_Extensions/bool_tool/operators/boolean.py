import bpy
from collections import defaultdict
from .. import __package__ as base_package

from ..functions.canvas import (
    filter_canvases,
    create_slice,
)
from ..functions.cutter import (
    filter_cutters,
    make_cutter,
)
from ..functions.modifier import (
    add_boolean_modifier,
    apply_modifiers,
    get_modifiers_to_apply,
)
from ..functions.object import (
    change_parent,
    delete_object,
)
from ..functions.poll import (
    basic_poll,
    convert_to_mesh_confirmation,
    destructive_op_confirmation,
)


#### ------------------------------ PROPERTIES ------------------------------ ####

class BooleanBase():
    # Add-on properties.
    flip: bpy.props.BoolProperty(
        name = "Flip Canvas & Cutters",
        options = {'SKIP_SAVE'},
        default = False,
    )

    # Boolean modifier properties.
    material_mode: bpy.props.EnumProperty(
        name = "Materials",
        description = "Method for setting materials on the new faces",
        items = (('INDEX', "Index Based",
                  ("Set the material on new faces based on the order of the material slot lists. If a material doesn't exist on the\n"
                   "modifier object, the face will use the same material slot or the first if the object doesn't have enough slots.")),
                 ('TRANSFER', "Transfer",
                  ("Transfer materials from non-empty slots to the result mesh, adding new materials as necessary.\n"
                   "For empty slots, fall back to using the same material index as the operand mesh."))),
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

    # Built-in Methods.
    @classmethod
    def poll(cls, context):
        return basic_poll(cls, context)


    def draw(self, context):
        prefs = context.preferences.addons[base_package].preferences

        layout = self.layout
        layout.use_property_split = True

        col = layout.column()
        col.prop(self, "flip")
        if self._unflippable:
            col.enabled = False

        layout.separator()
        if prefs.solver == 'EXACT':
            layout.prop(self, "material_mode")
            layout.prop(self, "use_self")
            layout.prop(self, "use_hole_tolerant")
        elif prefs.solver == 'FLOAT':
            layout.prop(self, "double_threshold")


    # Custom Methods.
    def _filter_objects(self, context) -> tuple[list, list]:
        """Returns lists of cutters & canvases."""

        canvases = [context.active_object]
        cutters = [obj for obj in context.selected_objects if obj != context.active_object]

        # Flip.
        if self.flip:
            canvases, cutters = cutters, canvases

        # Filter Canvases.
        canvases = filter_canvases(self, context, canvases)
        if len(canvases) == 0:
            self.report({'WARNING'}, "No valid canvases selected")
            return None, None

        # Filter Cutters.
        cutters = filter_cutters(self, context, cutters, canvases)
        if len(cutters) == 0:
            self.report({'WARNING'}, "No valid cutters selected")
            return None, None

        return canvases, cutters



#### ------------------------------ /brush_boolean/ ------------------------------ ####

class BrushBoolean(BooleanBase):

    def invoke(self, context, event):
        # Abort if there are less than 2 objects selected.
        if len(context.selected_objects) < 2:
            self.report({'WARNING'}, "Boolean operator needs at least two selected objects")
            return {'CANCELLED'}

        if not self.flip:
            cutters = [obj for obj in context.selected_objects if obj != context.active_object]
        else:
            cutters = [context.active_object]

        self._unflippable = False
        return convert_to_mesh_confirmation(self, context, event, cutters, "Brush Boolean")


    def execute(self, context):
        prefs = context.preferences.addons[base_package].preferences

        # Create lists of cutters & canvases.
        canvases, cutters = self._filter_objects(context)
        if canvases is None or cutters is None:
            return {'CANCELLED'}

        # Create slices.
        if self.mode == "SLICE":
            for cutter in cutters:
                """
                NOTE: Slices need to be created in a separate loop to avoid
                inheriting Boolean modifiers that the operator adds.
                """
                for canvas in canvases:
                    slice = create_slice(context, canvas, modifier=True)
                    add_boolean_modifier(self, context, slice, cutter, "INTERSECT", prefs.solver, pin=prefs.pin)

        for cutter in cutters:
            make_cutter(context, cutter, self.mode,
                        display=prefs.display,
                        collection=prefs.use_collection)

            mode = "DIFFERENCE" if self.mode == "SLICE" else self.mode
            for canvas in canvases:
                add_boolean_modifier(self, context, canvas, cutter, mode, prefs.solver, pin=prefs.pin)

            if prefs.parent:
                change_parent(context, cutter, canvases[0], inverse=True)

        # Set Boolean property to canvases.
        for canvas in canvases:
            canvas.booleans.canvas = True

        return {'FINISHED'}


class OBJECT_OT_boolean_brush_union(bpy.types.Operator, BrushBoolean):
    bl_idname = "object.boolean_brush_union"
    bl_label = "Boolean Union (Brush)"
    bl_options = {'REGISTER', 'UNDO'}

    mode = "UNION"

    @classmethod
    def description(cls, context, properties):
        if not properties.flip:
            return "Merge selected objects into the active one"
        else:
            return "Merge the active object into selected ones"


class OBJECT_OT_boolean_brush_intersect(bpy.types.Operator, BrushBoolean):
    bl_idname = "object.boolean_brush_intersect"
    bl_label = "Boolean Intersection (Brush)"
    bl_options = {'REGISTER', 'UNDO'}

    mode = "INTERSECT"

    @classmethod
    def description(cls, context, properties):
        if not properties.flip:
            return "Only keep parts of the active object that are interesecting selected objects"
        else:
            return "Only keep parts of selected objects that are interesecting the active one"


class OBJECT_OT_boolean_brush_difference(bpy.types.Operator, BrushBoolean):
    bl_idname = "object.boolean_brush_difference"
    bl_label = "Boolean Difference (Brush)"
    bl_options = {'REGISTER', 'UNDO'}

    mode = "DIFFERENCE"

    @classmethod
    def description(cls, context, properties):
        if not properties.flip:
            return "Subtract selected objects from the active one"
        else:
            return "Subtract the active object from selected ones"


class OBJECT_OT_boolean_brush_slice(bpy.types.Operator, BrushBoolean):
    bl_idname = "object.boolean_brush_slice"
    bl_label = "Boolean Slice (Brush)"
    bl_description = "Slice active object along the selected ones. Will create slices as separate objects"
    bl_options = {'REGISTER', 'UNDO'}

    mode = "SLICE"

    @classmethod
    def description(cls, context, properties):
        if not properties.flip:
            return "Slice the active object by selected ones. Will create slices as separate objects"
        else:
            return "Slice selected objects by the active one. Will create slices as separate objects"



#### ------------------------------ /auto_boolean/ ------------------------------ ####

class AutoBoolean(BooleanBase):

    def invoke(self, context, event):
        # Abort if there are less than 2 selected objects.
        if len(context.selected_objects) < 2:
            self.report({'WARNING'}, "Boolean operator needs at least two selected objects")
            return {'CANCELLED'}

        if not self.flip:
            canvases = [context.active_object]
        else:
            canvases = [obj for obj in context.selected_objects if obj != context.active_object]

        for canvas in canvases:
            if canvas.type != 'MESH':
                canvases.remove(canvas)

        self._unflippable = False
        return destructive_op_confirmation(self, context, event, canvases, "Auto Boolean")


    def execute(self, context):
        prefs = context.preferences.addons[base_package].preferences
        new_modifiers = defaultdict(list)

        # Create lists of cutters & canvases.
        canvases, cutters = self._filter_objects(context)
        if canvases is None or cutters is None:
            return {'CANCELLED'}

        # Create slices.
        if self.mode == "SLICE":
            for cutter in cutters:
                """
                NOTE: Slices need to be created in a separate loop to avoid
                inheriting Boolean modifiers that the operator adds.
                """
                for canvas in canvases:
                    slice = create_slice(context, canvas)
                    modifier = add_boolean_modifier(self, context, slice, cutter, "INTERSECT",
                                                    prefs.solver, pin=prefs.pin)
                    new_modifiers[slice].append(modifier)
                    slice.select_set(True)

        for cutter in cutters:
            # Add Boolean modifier on canvases.
            mode = "DIFFERENCE" if self.mode == "SLICE" else self.mode
            for canvas in canvases:
                modifier = add_boolean_modifier(self, context, canvas, cutter, mode, prefs.solver, pin=prefs.pin)
                new_modifiers[canvas].append(modifier)

            # Transfer cutters children to a canvas.
            for child in cutter.children:
                change_parent(context, child, canvases[0])

            # Select all faces of the cutter so that newly created faces in canvas
            # are also selected after applying the modifier.
            for face in cutter.data.polygons:
                face.select = True

        # Apply modifiers on canvases & slices.
        for obj, modifiers in new_modifiers.items():
            modifiers = get_modifiers_to_apply(context, obj, modifiers)
            apply_modifiers(context, obj, modifiers)

        # Delete cutters.
        for cutter in cutters:
            delete_object(cutter)

        return {'FINISHED'}


class OBJECT_OT_boolean_auto_union(bpy.types.Operator, AutoBoolean):
    bl_idname = "object.boolean_auto_union"
    bl_label = "Boolean Union (Auto)"
    bl_options = {'REGISTER', 'UNDO'}

    mode = "UNION"

    @classmethod
    def description(cls, context, properties):
        if not properties.flip:
            return "Merge selected objects into the active one"
        else:
            return "Merge the active object into selected ones"


class OBJECT_OT_boolean_auto_difference(bpy.types.Operator, AutoBoolean):
    bl_idname = "object.boolean_auto_difference"
    bl_label = "Boolean Difference (Auto)"
    bl_options = {'REGISTER', 'UNDO'}

    mode = "DIFFERENCE"

    @classmethod
    def description(cls, context, properties):
        if not properties.flip:
            return "Subtract selected objects from the active one"
        else:
            return "Subtract the active object from selected ones"


class OBJECT_OT_boolean_auto_intersect(bpy.types.Operator, AutoBoolean):
    bl_idname = "object.boolean_auto_intersect"
    bl_label = "Boolean Intersect (Auto)"
    bl_options = {'REGISTER', 'UNDO'}

    mode = "INTERSECT"

    @classmethod
    def description(cls, context, properties):
        if not properties.flip:
            return "Only keep parts of the active object that are interesecting selected objects"
        else:
            return "Only keep parts of selected objects that are interesecting the active one"


class OBJECT_OT_boolean_auto_slice(bpy.types.Operator, AutoBoolean):
    bl_idname = "object.boolean_auto_slice"
    bl_label = "Boolean Slice (Auto)"
    bl_description = "Slice active object along the selected ones. Will create slices as separate objects"
    bl_options = {'REGISTER', 'UNDO'}

    mode = "SLICE"

    @classmethod
    def description(cls, context, properties):
        if not properties.flip:
            return "Slice the active object by selected ones. Will create slices as separate objects"
        else:
            return "Slice selected objects by the active one. Will create slices as separate objects"



#### ------------------------------ REGISTRATION ------------------------------ ####

addon_keymaps = []

classes = (
    OBJECT_OT_boolean_brush_union,
    OBJECT_OT_boolean_brush_difference,
    OBJECT_OT_boolean_brush_intersect,
    OBJECT_OT_boolean_brush_slice,

    OBJECT_OT_boolean_auto_union,
    OBJECT_OT_boolean_auto_difference,
    OBJECT_OT_boolean_auto_intersect,
    OBJECT_OT_boolean_auto_slice,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # KEYMAP
    addon = bpy.context.window_manager.keyconfigs.addon
    km = addon.keymaps.new(name="Object Mode")

    # Brush Operators
    kmi = km.keymap_items.new("object.boolean_brush_union", 'NUMPAD_PLUS', 'PRESS', ctrl=True)
    kmi.active = True
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new("object.boolean_brush_difference", 'NUMPAD_MINUS', 'PRESS', ctrl=True)
    kmi.active = True
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new("object.boolean_brush_intersect", 'NUMPAD_ASTERIX', 'PRESS', ctrl=True)
    kmi.active = True
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new("object.boolean_brush_slice", 'NUMPAD_SLASH', 'PRESS', ctrl=True)
    kmi.active = True
    addon_keymaps.append((km, kmi))

    # Auto Operators
    kmi = km.keymap_items.new("object.boolean_auto_union", 'NUMPAD_PLUS', 'PRESS', ctrl=True, shift=True)
    kmi.active = True
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new("object.boolean_auto_difference", 'NUMPAD_MINUS', 'PRESS', ctrl=True, shift=True)
    kmi.active = True
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new("object.boolean_auto_intersect", 'NUMPAD_ASTERIX', 'PRESS', ctrl=True, shift=True)
    kmi.active = True
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new("object.boolean_auto_slice", 'NUMPAD_SLASH', 'PRESS', ctrl=True, shift=True)
    kmi.active = True
    addon_keymaps.append((km, kmi))


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # KEYMAP
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
