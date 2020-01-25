import bpy
from bpy.types import AddonPreferences
from bpy.props import StringProperty


class Add_Camera_Rigs_Preferences(AddonPreferences):
    bl_idname = 'add_camera_rigs'

    # widget prefix
    widget_prefix: StringProperty(
        name="Camera Widget prefix",
        description="Choose a prefix for the widget objects",
        default="WDGT_",
    )

    # collection name
    camera_widget_collection_name: StringProperty(
        name="Bone Widget collection name",
        description="Choose a name for the collection the widgets will appear",
        default="WDGTS_camera",
    )

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        col = row.column()
        col.prop(self, "widget_prefix", text="Widget Prefix")
        col.prop(self, "camera_widget_collection_name", text="Collection name")


classes = (
    Add_Camera_Rigs_Preferences,
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)
