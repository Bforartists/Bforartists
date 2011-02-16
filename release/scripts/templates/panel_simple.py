import bpy


class OBJECT_PT_hello(bpy.types.Panel):
    bl_label = "Hello World Panel"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    def draw(self, context):
        layout = self.layout

        obj = context.object

        row = layout.row()
        row.label(text="Hello world!", icon='WORLD_DATA')

        row = layout.row()
        row.label(text="Active object is: " + obj.name)
        row = layout.row()
        row.prop(obj, "name")


def register():
    bpy.utils.register_class(OBJECT_PT_hello)


def unregister():
    bpy.utils.unregister_class(OBJECT_PT_hello)


if __name__ == "__main__":
    register()
