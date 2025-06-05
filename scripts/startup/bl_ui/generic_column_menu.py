import bpy

# BFA
def fetch_op_data(class_name):
    type_class = getattr(bpy.types, class_name)
    type_props = type_class.bl_rna.properties["type"]

    OPERATOR_DATA = {
        enum_it.identifier: (enum_it.name, enum_it.icon)
            for enum_it in type_props.enum_items_static
        }

    TRANSLATION_CONTEXT = type_props.translation_context

    return (OPERATOR_DATA, TRANSLATION_CONTEXT)


class GenericColumnMenu:
    bl_label = ""
    bl_options = {'SEARCH_ON_KEY_PRESS'}

    search_header = ""

    @classmethod
    def draw_operator_column(cls, layout, header, types, icon='NONE'):
        text_ctxt = cls.TRANSLATION_CONTEXT
        col = layout.column()
        if layout.operator_context == 'INVOKE_REGION_WIN':
            col.label(text=cls.search_header)
        else:
            col.label(text=header, icon=icon)
            col.separator()

        for op_type in types:
            label, op_icon = cls.OPERATOR_DATA[op_type]
            col.operator(cls.op_id, text=label, icon=op_icon, text_ctxt=text_ctxt).type = op_type


class InvokeMenuOperator:
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space and space.type == cls.space_type and space.context == cls.space_context

    def invoke(self, context, event):
        return bpy.ops.wm.call_menu(name=self.menu_id)

# A classes iterable is needed even if empty due to how Blender/Bforartists registers modules under startup/bl_ui
classes = []
