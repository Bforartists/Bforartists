import bpy
import math
from mathutils import Vector

from .draw_pixelate_controls import draw_pixelate_controls

from ..utils.selection import get_input_tree
from ..utils import process_input


class Pixelate(bpy.types.Operator):
    """
    ![Demo](https://i.imgur.com/u8nUPj6.gif)

    Pixelate a clip by adding 2 transform effects: 1 shrinking,
    1 expanding.
    """
    bl_idname = "vse_transform_tools.pixelate"
    bl_label = "Pixelate"
    bl_description = "Pixelate a strip"
    bl_options = {'REGISTER', 'UNDO'}

    first_mouse = Vector((0, 0))
    pos = Vector((0, 0))
    pixel_factor = 0.0
    handle_pixelation = None
    fac = 0

    key_val = ''

    tab = []

    @classmethod
    def poll(cls, context):
        scene = context.scene
        if (scene.sequence_editor and
           scene.sequence_editor.active_strip and
           scene.sequence_editor.active_strip.select):
            return True
        return False

    def modal(self, context, event):
        scene = context.scene
        res_x = scene.render.resolution_x
        res_y = scene.render.resolution_y

        context.area.tag_redraw()
        w = context.region.width

        mouse_x = event.mouse_region_x
        mouse_x += (self.pixel_factor * w) / 5
        mouse_y = event.mouse_region_y

        self.pos = Vector([mouse_x, mouse_y])
        self.pos -= self.first_mouse

        if self.pos.x < 0:
            self.pos.x = 0.0
        if self.pos.x > w / 5:
            self.pos.x = w / 5
        self.fac = self.pos.x / (w / 5)

        process_input(self, event.type, event.value)
        if self.key_val != '':
            try:
                self.fac = abs(float(self.key_val))
                if self.fac > 1:
                    self.fac = abs(float('0.' + self.key_val.replace('.', '')))
                self.pos.x = self.fac * (w / 5)
            except ValueError:
                pass

        precision = 2
        if event.ctrl:
            precision = 1

        self.fac = round(self.fac, precision)

        if (event.type == 'LEFTMOUSE' or
            event.type == 'RET' or
                event.type == 'NUMPAD_ENTER'):

            if self.fac > 0:
                selected_strips = []
                for strip in context.selected_sequences:
                    if not strip.type == 'SOUND':
                        selected_strips.append(strip)

                for strip in selected_strips:
                    channel = strip.channel

                    bpy.ops.sequencer.select_all(action='DESELECT')
                    scene.sequence_editor.active_strip = strip
                    bpy.ops.sequencer.effect_strip_add(type="TRANSFORM")

                    shrinker = context.scene.sequence_editor.active_strip
                    shrinker.name = "SHRINKER-%s" % strip.name
                    shrinker.interpolation = "NONE"

                    bpy.ops.sequencer.effect_strip_add(type="TRANSFORM")
                    expander = context.scene.sequence_editor.active_strip
                    expander.name = "EXPANDER-%s" % strip.name
                    expander.blend_alpha = strip.blend_alpha
                    expander.interpolation = "NONE"
                    expander.use_float = True

                    tree = get_input_tree(expander)[1::]
                    for child in tree:
                        child.mute = True
                        child.select = True

                    bpy.ops.sequencer.meta_make()
                    meta = context.scene.sequence_editor.active_strip
                    meta.name = "PIX-%s" % strip.name
                    meta.channel = channel
                    meta.blend_type = "ALPHA_OVER"

                    pixel_fac = self.fac * 100

                    shrink_fac = (100 / pixel_fac) / 100

                    shrink_factor_x = (100 / (res_x / math.ceil(res_x * shrink_fac))) / 100
                    shrink_factor_y = (100 / (res_y / math.ceil(res_y * shrink_fac))) / 100

                    shrinker.scale_start_x = shrink_factor_x
                    shrinker.scale_start_y = shrink_factor_y

                    expand_factor_x = 1 / shrink_factor_x
                    expand_factor_y = 1 / shrink_factor_y

                    expander.scale_start_x = expand_factor_x
                    expander.scale_start_y = expand_factor_y

                    shrunk_x = round(res_x * shrink_factor_x)
                    if shrunk_x % 2 == 1:
                        expander.translate_start_x = ((-1 / (shrunk_x - 1)) / 2) * 100

                    shrunk_y = round(res_y * shrink_factor_y)
                    if shrunk_y % 2 == 1:
                        expander.translate_start_y = ((-1 / (shrunk_y - 1)) / 2) * 100

                bpy.types.SpaceSequenceEditor.draw_handler_remove(
                    self.handle_pixelation, 'PREVIEW')

                return {'FINISHED'}

        if event.type == 'ESC' or event.type == 'RIGHTMOUSE':
            bpy.types.SpaceSequenceEditor.draw_handler_remove(
                self.handle_alpha, 'PREVIEW')
            return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        scene = context.scene

        mouse_x = event.mouse_region_x
        mouse_y = event.mouse_region_y
        self.first_mouse = Vector([mouse_x, mouse_y])

        self.pixel_factor = 0.0
        self.key_val != ''

        args = (self, context)
        self.handle_pixelation = bpy.types.SpaceSequenceEditor.draw_handler_add(
            draw_pixelate_controls, args, 'PREVIEW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}
