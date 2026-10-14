import bpy
from .. import __package__ as base_package

from ..functions.canvas import (
    is_canvas,
)

from .common import (
    get_modifier_from_list_index,
    boolean_extras_menu,
)


#### ------------------------------ PANELS ------------------------------ ####

# Boolean Operators Panel
class VIEW3D_PT_boolean(bpy.types.Panel):
    bl_label = "Boolean"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Edit"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        prefs = context.preferences.addons[base_package].preferences
        return prefs.show_in_sidebar

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_DEFAULT'
        col = layout.column(align=True)

        col.label(text="Auto Boolean")
        row = col.row(align=False)
        row.operator("object.boolean_auto_difference", text="Difference", icon='SELECT_SUBTRACT')
        row.operator("object.boolean_auto_difference", text="", icon='UV_SYNC_SELECT').flip=True
        row = col.row(align=False)
        row.operator("object.boolean_auto_union", text="Union", icon='SELECT_EXTEND')
        row.operator("object.boolean_auto_union", text="", icon='UV_SYNC_SELECT').flip=True
        row = col.row(align=False)
        row.operator("object.boolean_auto_intersect", text="Intersect", icon='SELECT_INTERSECT')
        row.operator("object.boolean_auto_intersect", text="", icon='UV_SYNC_SELECT').flip=True
        row = col.row(align=False)
        row.operator("object.boolean_auto_slice", text="Slice", icon='SELECT_DIFFERENCE')
        row.operator("object.boolean_auto_slice", text="", icon='UV_SYNC_SELECT').flip=True

        col.separator()
        col.label(text="Brush Boolean")
        row = col.row(align=False)
        row.operator("object.boolean_brush_difference", text="Difference", icon='SELECT_SUBTRACT')
        row.operator("object.boolean_brush_difference", text="", icon='UV_SYNC_SELECT').flip=True
        row = col.row(align=False)
        row.operator("object.boolean_brush_union", text="Union", icon='SELECT_EXTEND')
        row.operator("object.boolean_brush_union", text="", icon='UV_SYNC_SELECT').flip=True
        row = col.row(align=False)
        row.operator("object.boolean_brush_intersect", text="Intersect", icon='SELECT_INTERSECT')
        row.operator("object.boolean_brush_intersect", text="", icon='UV_SYNC_SELECT').flip=True
        row = col.row(align=False)
        row.operator("object.boolean_brush_slice", text="Slice", icon='SELECT_DIFFERENCE')
        row.operator("object.boolean_brush_slice", text="", icon='UV_SYNC_SELECT').flip=True


# Cutters Panel
class VIEW3D_PT_boolean_cutters(bpy.types.Panel):
    bl_label = "Cutters"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Edit"
    bl_context = "objectmode"
    bl_parent_id = "VIEW3D_PT_boolean"

    @classmethod
    def poll(cls, context):
        prefs = context.preferences.addons[base_package].preferences
        if prefs.show_in_sidebar:
            if context.active_object:
                if is_canvas(context.active_object):
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

    def draw(self, context):
        layout = self.layout
        canvas = context.active_object

        # Cutters List
        row = layout.row()
        col = row.column()
        col.template_list(
            "VIEW3D_UL_boolean_cutters",
            "",
            canvas, "modifiers",
            canvas.booleans, "modifiers_list_index",
            rows=5,
        )

        # Filter & Operators
        col = row.column(align=True)
        cutters_list_index = canvas.booleans.modifiers_list_index
        mod = get_modifier_from_list_index(canvas, cutters_list_index)
        sub = col.column(align=True)

        # Apply Cutter
        op_apply = sub.operator("object.boolean_apply_cutter", text="", icon='CHECKMARK')
        op_apply.method = 'SPECIFIED'
        op_apply.specified_cutter = mod.object.name if mod else ""
        op_apply.specified_canvas = canvas.name

        # Remove Cutter
        op_remove = sub.operator("object.boolean_remove_cutter", text="", icon='X')
        op_remove.method = 'SPECIFIED'
        op_remove.specified_cutter = mod.object.name if mod else ""
        op_remove.specified_canvas = canvas.name
        op_remove.specified_modifier = mod.name if mod else ""

        if cutters_list_index < 0 or not mod:
            sub.enabled = False

        col.separator()
        col.menu("VIEW3D_MT_boolean_specials", icon='DOWNARROW_HLT', text="")


# Helpers Panel
class VIEW3D_PT_boolean_helpers(bpy.types.Panel):
    bl_label = "Helpers"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Edit"
    bl_context = "objectmode"
    bl_parent_id = "VIEW3D_PT_boolean"

    @classmethod
    def poll(cls, context):
        prefs = context.preferences.addons[base_package].preferences
        if not prefs.show_in_sidebar:
            return False
        if not context.active_object:
            return False
        if context.active_object.booleans.cutter:
            return True

        return False

    def draw(self, context):
        boolean_extras_menu(self, context, cutter_only=True)



#### ------------------------------ MENUS ------------------------------ ####

# Specials
class VIEW3D_MT_boolean_specials(bpy.types.Menu):
    bl_label = "Boolean Operators"
    bl_idname = "VIEW3D_MT_boolean_specials"

    def draw(self, context):
        boolean_extras_menu(self, context)



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = (
    VIEW3D_PT_boolean,
    VIEW3D_PT_boolean_cutters,
    VIEW3D_PT_boolean_helpers,
    VIEW3D_MT_boolean_specials,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
