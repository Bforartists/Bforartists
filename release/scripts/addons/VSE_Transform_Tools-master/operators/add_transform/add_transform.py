import bpy

from ..utils.geometry import get_transform_box
from ..utils.geometry import get_strip_box
from ..utils.selection import get_input_tree

class AddTransform(bpy.types.Operator):
    """
    ![Demo](https://i.imgur.com/v4racQW.gif)

    A transform modifier must be added to a strip before the strip can
    be grabbed, scaled, rotated, or cropped by this addon.
    Any strips with "Image Offset" enabled will transfer this offset to
    the transform strip
    """
    bl_idname = "vse_transform_tools.add_transform"
    bl_label = "Add Transform"
    bl_description = "Add transform modifier to selected strips"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.scene.sequence_editor:
            return True
        return False

    def execute(self, context):
        bpy.ops.vse_transform_tools.check_update()

        scene = context.scene

        selected_strips = []
        for strip in context.selected_sequences:
            if not strip.type == 'SOUND':
                selected_strips.append(strip)

        for strip in selected_strips:
            strip.use_float = True

            bpy.ops.sequencer.select_all(action='DESELECT')
            scene.sequence_editor.active_strip = strip
            bpy.ops.sequencer.effect_strip_add(type="TRANSFORM")

            transform_strip = context.scene.sequence_editor.active_strip
            transform_strip.name = "[TR]-%s" % strip.name

            transform_strip.blend_type = 'ALPHA_OVER'
            transform_strip.blend_alpha = strip.blend_alpha

            tree = get_input_tree(transform_strip)[1::]
            for child in tree:
                child.mute = True

            if not strip.use_crop:
                strip.use_crop = True
                strip.crop.min_x = 0
                strip.crop.max_x = 0
                strip.crop.min_y = 0
                strip.crop.max_y = 0

            if strip.use_translation:
                if strip.type == 'TRANSFORM':
                    left, right, bottom, top = get_transform_box(strip)
                else:
                    left, right, bottom, top = get_strip_box(strip)

                width = right - left
                height = top - bottom

                res_x = context.scene.render.resolution_x
                res_y = context.scene.render.resolution_y

                ratio_x = width / res_x
                ratio_y = height / res_y

                transform_strip.scale_start_x = ratio_x
                transform_strip.scale_start_y = ratio_y

                offset_x = strip.transform.offset_x
                offset_y = strip.transform.offset_y

                flip_x = 1
                if strip.use_flip_x:
                    flip_x = -1

                flip_y = 1
                if strip.use_flip_y:
                    flip_y = -1

                pos_x = offset_x + (width / 2) - (res_x / 2)
                pos_x *= flip_x

                pos_y = offset_y + (height / 2) - (res_y / 2)
                pos_y *= flip_y

                if transform_strip.translation_unit == 'PERCENT':
                    pos_x = (pos_x / res_x) * 100
                    pos_y = (pos_y / res_y) * 100

                transform_strip.translate_start_x = pos_x
                transform_strip.translate_start_y = pos_y

                strip.use_translation = False

        return {'FINISHED'}
