import bpy


class BFA_OT_set_brush(bpy.types.Operator):
    bl_label = "Set Brush"
    bl_idname = "bfa.set_brush"
    bl_options = {"UNDO"}

    tool_settings_attribute_name: bpy.props.StringProperty()
    brush_name: bpy.props.StringProperty()
    dynamic_description: bpy.props.StringProperty()

    def execute(self, context):
        paint_settings = getattr(
            context.tool_settings, self.tool_settings_attribute_name
        )
        paint_settings.brush = bpy.data.brushes[self.brush_name]
        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):
        return properties.dynamic_description


def register():
    bpy.utils.register_class(BFA_OT_set_brush)


def unregister():
    bpy.utils.unregister_class(BFA_OT_set_brush)
