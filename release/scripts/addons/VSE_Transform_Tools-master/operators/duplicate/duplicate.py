import bpy

from ..utils.selection import get_input_tree

from .get_vertical_translation import get_vertical_translation


class Duplicate(bpy.types.Operator):
    """
    ![Demo](https://i.imgur.com/IJh7v3z.gif)

    Duplicates all selected strips and any strips that are inputs
    of those strips.
    Calls the Grab operator immediately after duplicating.
    """
    bl_idname = "vse_transform_tools.duplicate"
    bl_label = "Duplicate"
    bl_description = "Duplicate selected and their inputs recursively"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        if (scene.sequence_editor and
           scene.sequence_editor.active_strip):
            return True
        return False

    def invoke(self, context, event):

        selected = context.selected_sequences

        duplicated = []

        for strip in selected:
            if strip not in duplicated:
                bpy.ops.sequencer.select_all(action="DESELECT")

                tree = get_input_tree(strip)
                for seq in tree:
                    seq.select = True

                duplicated.extend(tree)

                vertical_translation = get_vertical_translation(
                    context.selected_sequences)

                bpy.ops.sequencer.duplicate_move(
                        SEQUENCER_OT_duplicate={"mode": "TRANSLATION"},
                        TRANSFORM_OT_seq_slide={
                            "value": (0, vertical_translation)})

        return bpy.ops.vse_transform_tools.grab('INVOKE_DEFAULT')
