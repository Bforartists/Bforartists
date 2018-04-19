import bpy
import bgl
import blf

from mathutils import Vector

from .draw_alpha_controls import draw_alpha_controls

from ..utils import process_input


class AdjustAlpha(bpy.types.Operator):
    """
    ![Demo](https://i.imgur.com/PNsjamH.gif)
    """
    bl_idname = "vse_transform_tools.adjust_alpha"
    bl_label = "Adjust Alpha"
    bl_description = "Adjust alpha (opacity) of strips in the Image Preview"
    bl_options = {'REGISTER', 'UNDO'}

    first_mouse = Vector((0, 0))
    pos = Vector((0, 0))
    alpha_init = 0
    fac = 0
    key_val = ''

    tab = []

    handle_alpha = None

    @classmethod
    def poll(cls, context):
        scene = context.scene
        if (scene.sequence_editor and
           scene.sequence_editor.active_strip and
           scene.sequence_editor.active_strip.select):
            return True
        return False

    def modal(self, context, event):
        context.area.tag_redraw()
        w = context.region.width

        mouse_x = event.mouse_region_x
        mouse_x += (self.alpha_init * w) / 5
        mouse_y = event.mouse_region_y

        self.pos = Vector((mouse_x, mouse_y))
        self.pos -= self.first_mouse

        if self.pos.x < 0:
            self.pos.x = 0
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

        precision = 3
        if event.ctrl:
            precision = 1

        self.fac = round(self.fac, precision)
        for strip in self.tab:
            strip.blend_alpha = self.fac

        if (event.type == 'LEFTMOUSE' or
           event.type == 'RET' or
           event.type == 'NUMPAD_ENTER'):
            bpy.types.SpaceSequenceEditor.draw_handler_remove(
                self.handle_alpha, 'PREVIEW')

            scene = context.scene
            if scene.tool_settings.use_keyframe_insert_auto:
                cf = context.scene.frame_current
                for strip in self.tab:
                    strip.keyframe_insert(data_path='blend_alpha', frame=cf)

            return {'FINISHED'}

        if event.type == 'ESC' or event.type == 'RIGHTMOUSE':
            for strip in self.tab:
                strip.blend_alpha = self.alpha_init

            bpy.types.SpaceSequenceEditor.draw_handler_remove(
                self.handle_alpha, 'PREVIEW')
            return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if event.alt:
            for strip in context.selected_sequences:
                strip.blend_alpha = 1.0
            return {'FINISHED'}

        else:
            mouse_x = event.mouse_region_x
            mouse_y = event.mouse_region_y
            self.first_mouse = Vector((mouse_x, mouse_y))

            opacities = []

            selected_strips = []
            for strip in context.selected_sequences:
                if not strip.type == 'SOUND':
                    selected_strips.append(strip)

            for strip in selected_strips:
                self.tab.append(strip)
                opacities.append(strip.blend_alpha)

            self.alpha_init = max(opacities)

            self.key_val != ''

            args = (self, context)
            self.handle_alpha = bpy.types.SpaceSequenceEditor.draw_handler_add(
                draw_alpha_controls, args, 'PREVIEW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}
