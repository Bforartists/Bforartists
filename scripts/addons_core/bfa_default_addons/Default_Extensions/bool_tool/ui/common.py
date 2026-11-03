import bpy
from contextlib import contextmanager

from ..functions.canvas import (
    is_canvas,
)
from ..functions.modifier import (
    enumerate_boolean_modifiers,
    is_boolean_modifier,
)


#### ------------------------------ FUNCTIONS ------------------------------ ####

def get_modifier_from_list_index(obj, index: int):
    """
    Returns the modifier of an object based on Cutters list index.
    Filters out non-Boolean modifiers to leave a list that matches Cutters one in length.
    """

    # Create a list of only Boolean modifiers.
    boolean_modifiers = []
    for mod in obj.modifiers:
        if is_boolean_modifier(mod):
            boolean_modifiers.append(mod)

    if 0 <= index < len(boolean_modifiers):
        return boolean_modifiers[index]

    return None


@contextmanager
def preserve_list_index(prop_owner, index_prop: str):
    """Preserves index of active item in UI list."""

    index = getattr(prop_owner, index_prop, 0)
    stored_index = index

    try:
        yield

    finally:
        new_index = stored_index - 1

        if new_index < 0:
            new_index = 0

        setattr(prop_owner, index_prop, new_index)



#### ------------------------------ /ui/ ------------------------------ ####

def boolean_operators_menu(self, context):
    layout = self.layout
    layout.operator_context = 'INVOKE_DEFAULT'
    col = layout.column(align=True)

    col.label(text="Auto Boolean")
    col.operator("object.boolean_auto_difference", text="Difference", icon='SELECT_SUBTRACT')
    col.operator("object.boolean_auto_union", text="Union", icon='SELECT_EXTEND')
    col.operator("object.boolean_auto_intersect", text="Intersect", icon='SELECT_INTERSECT')
    col.operator("object.boolean_auto_slice", text="Slice", icon='SELECT_DIFFERENCE')

    col.separator()
    col.label(text="Brush Boolean")
    col.operator("object.boolean_brush_difference", text="Difference", icon='SELECT_SUBTRACT')
    col.operator("object.boolean_brush_union", text="Union", icon='SELECT_EXTEND')
    col.operator("object.boolean_brush_intersect", text="Intersect", icon='SELECT_INTERSECT')
    col.operator("object.boolean_brush_slice", text="Slice", icon='SELECT_DIFFERENCE')


def boolean_extras_menu(self, context, cutter_only=False):
    layout = self.layout
    layout.operator_context = 'INVOKE_DEFAULT'
    col = layout.column(align=True)
    obj = context.active_object

    if not obj:
        return

    # Canvas operators
    if is_canvas(obj) and not cutter_only:
        col.separator()
        col.operator("object.boolean_toggle_all", text="Toggle All Cuters")
        col.operator("object.boolean_apply_all", text="Apply All Cutters")
        col.operator("object.boolean_remove_all", text="Remove All Cutters")

    # Cutter operators
    if obj.booleans.cutter:
        if not cutter_only:
            col.separator()
        col.operator("object.boolean_toggle_cutter", text="Toggle Cutter").method='ALL'
        col.operator("object.boolean_apply_cutter", text="Apply Cutter").method='ALL'
        col.operator("object.boolean_remove_cutter", text="Remove Cutter").method='ALL'
