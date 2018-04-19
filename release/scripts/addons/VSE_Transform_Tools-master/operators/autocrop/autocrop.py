import bpy
import math

from ..utils.selection import get_visible_strips
from ..utils.selection import get_transforms
from ..utils.selection import get_nontransforms

from ..utils.geometry import get_group_box
from ..utils.geometry import reposition_strip
from ..utils.geometry import reposition_transform_strip


class Autocrop(bpy.types.Operator):
    """
    ![Demo](https://i.imgur.com/IarxF14.gif)

    Sets the scene resolution to fit all visible content in
    the preview window without changing strip sizes.
    """
    bl_idname = "vse_transform_tools.autocrop"
    bl_label = "Autocrop"
    bl_description = "Collapse canvas to fit visible content"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        if scene.sequence_editor:
            return True
        return False

    def execute(self, context):
        scene = context.scene

        strips = get_visible_strips()

        if len(strips) == 0:
            return {'FINISHED'}

        group_box = get_group_box(strips)

        all_strips = scene.sequence_editor.sequences_all
        inputs = []
        for strip in all_strips:
            if hasattr(strip, "input_1"):
                inputs.append(strip.input_1)
            if hasattr(strip, "input_2"):
                inputs.append(strip.input_2)

        parents = []
        for strip in all_strips:
            if not strip in inputs and not strip.type == "SOUND":
                parents.append(strip)

        min_left, max_right, min_bottom, max_top = group_box

        total_width = max_right - min_left
        total_height = max_top - min_bottom

        nontransforms = get_nontransforms(parents)
        for strip in nontransforms:
            reposition_strip(strip, group_box)

        transforms = get_transforms(parents)
        for strip in transforms:
            reposition_transform_strip(strip, group_box)

        scene.render.resolution_x = total_width
        scene.render.resolution_y = total_height

        return {'FINISHED'}
