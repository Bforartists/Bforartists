import bpy

from ..functions.modifier import (
    is_boolean_modifier,
)


#### ------------------------------ /cutters_list/ ------------------------------ ####

class VIEW3D_UL_boolean_cutters(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        canvas = context.active_object
        mod = item

        # Pick Icon
        if mod.operation == 'DIFFERENCE':
            icon = 'SELECT_SUBTRACT'
        elif mod.operation == 'UNION':
            icon = 'SELECT_EXTEND'
        elif mod.operation == 'INTERSECT':
            icon = 'SELECT_INTERSECT'

        row = layout.row(align=True)
        row.prop(mod.object, "name", text="", icon=icon, emboss=False)

        # Select Cutter
        op_select = row.operator("object.boolean_select_cutter", text="", icon='RESTRICT_SELECT_OFF', emboss=False)
        op_select.cutter = mod.object.name

        # Toggle Cutter
        icon = 'HIDE_OFF' if mod.show_viewport else 'HIDE_ON'
        op_toggle = row.operator("object.boolean_toggle_cutter", text="", icon=icon, emboss=False)
        op_toggle.method = 'SPECIFIED'
        op_toggle.specified_cutter = mod.object.name
        op_toggle.specified_canvas = canvas.name
        op_toggle.specified_modifier = mod.name


    def filter_items(self, context, data, propname):
        flags = []
        indices = []

        modifiers = getattr(data, propname)
        for mod in modifiers:
            if is_boolean_modifier(mod):
                flags.append(self.bitflag_filter_item)
            else:
                flags.append(0)

        # Search Filter
        if self.filter_name:
            filter_name = self.filter_name.lower()
            for i, mod in enumerate(modifiers):
                if flags[i] != self.bitflag_filter_item:
                    continue
                if filter_name not in mod.object.name.lower():
                    flags[i] = 0

        # Invert
        if self.use_filter_invert:
            for i, mod in enumerate(modifiers):
                if not is_boolean_modifier(mod):
                    continue
                flags[i] ^= self.bitflag_filter_item

        # Sort by Name
        indices = list(range(len(modifiers)))
        if self.use_filter_sort_alpha:
            sorted_indices = sorted(range(len(modifiers)),
                                    key=lambda i: modifiers[i].object.name if modifiers[i].object else "")
            indices = [0] * len(modifiers)
            for rank, original_i in enumerate(sorted_indices):
                indices[original_i] = rank

        return flags, indices



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = (
    VIEW3D_UL_boolean_cutters,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
