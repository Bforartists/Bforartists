import bpy


class CallMenu(bpy.types.Operator):
    """
    ![Demo](https://i.imgur.com/9Cx6XKj.gif)

    You may also enable automatic keyframe insertion.

    ![Automatic Keyframe Insertion](https://i.imgur.com/kFtT1ja.jpg)
    """
    bl_idname = "vse_transform_tools.call_menu"
    bl_label = "Call Menu"
    bl_description = "Open keyframe insertion menu"

    @classmethod
    def poll(cls, context):
        if (context.scene.sequence_editor and
           context.space_data.type == 'SEQUENCE_EDITOR' and
           context.region.type == 'PREVIEW'):
            return True
        return False

    def execute(self, context):
        bpy.ops.wm.call_menu(name="VSE_MT_Insert_keyframe_Menu")
        return {'FINISHED'}
