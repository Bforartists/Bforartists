import bpy
from ..utils.selection import get_input_tree


class MetaToggle(bpy.types.Operator):
    """
    ![Demo](https://i.imgur.com/ya0nEgV.gif)

    Toggles the selected strip if it is a META. If the selected strip is
    not a meta, recursively checks inputs until a META strip is
    encountered and toggles it. If no META is found, this operator does
    nothing.
    """
    bl_idname = "vse_transform_tools.meta_toggle"
    bl_label = "Meta Toggle"
    bl_description = "Toggle the Meta to reveal sequences within"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        if (scene.sequence_editor):
            return True
        return False

    def invoke(self, context, event):
        scene = context.scene

        active = scene.sequence_editor.active_strip

        children = get_input_tree(active)
        for child in children:
            try:
                if child.type == "META":
                    bpy.ops.sequencer.select_all(action="DESELECT")
                    scene.sequence_editor.active_strip = child
                    child.select = True
                    return bpy.ops.sequencer.meta_toggle('INVOKE_DEFAULT')

            except AttributeError:
                pass

        return bpy.ops.sequencer.meta_toggle('INVOKE_DEFAULT')
