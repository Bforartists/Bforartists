import bpy
import math
from mathutils import Vector

from ..utils import process_input

from ..utils.geometry import get_res_factor
from ..utils.geometry import rotate_point
from ..utils.geometry import get_pos_x
from ..utils.geometry import get_pos_y
from ..utils.geometry import set_pos_x
from ..utils.geometry import set_pos_y

from ..utils.selection import ensure_transforms

from ..utils.draw import draw_px_point

from .apply_strip_rotation import apply_strip_rotation


class Rotate(bpy.types.Operator):
    """
    ![Demo](https://i.imgur.com/SyL2HeA.gif)
    """
    bl_idname = "vse_transform_tools.rotate"
    bl_label = "Rotate"
    bl_description = "Rotate strips in the Image Preview"
    bl_options = {'REGISTER', 'UNDO', 'GRAB_CURSOR', 'BLOCKING'}

    first_mouse = Vector([0, 0])
    tab_init = []
    tab_init_t = []
    tab = []

    center_area = Vector([0, 0])
    center_real = Vector([0, 0])

    rot_prev = 0
    vec_init = Vector([0, 0])
    vec_prev = Vector([0, 0])
    vec_act = Vector([0, 0])

    key_val = ''
    key_period = False
    key_period_val = 1

    stepwise_increment = 5
    slow_factor = 10

    @classmethod
    def poll(cls, context):
        scene = context.scene
        if (scene.sequence_editor and
                scene.sequence_editor.active_strip):
            return True
        return False

    def modal(self, context, event):
        context.area.tag_redraw()

        if self.tab:
            self.vec_act = Vector([event.mouse_region_x, event.mouse_region_y])
            self.vec_act -= self.center_area

            rot = math.degrees(-self.vec_prev.angle_signed(self.vec_act))

            if event.shift:
                rot /= self.slow_factor

            self.rot_prev += rot
            self.rot_prev %= 360

            self.vec_prev = Vector(self.vec_act)

            rot = float(self.rot_prev)

            if abs(self.init_rot - (rot - 360)) < abs(self.init_rot - rot):
                rot = rot - 360

            process_input(self, event.type, event.value)
            if self.key_val != '':
                try:
                    rot = -float(self.key_val)
                except ValueError:
                    pass

            for i in range(len(self.tab)):
                strip = self.tab[i]
                init_rot = self.tab_init[i]
                init_t = self.tab_init_t[i]

                apply_strip_rotation(
                    self, strip, rot, init_rot, init_t, event)

            if event.ctrl:
                rot = math.ceil(rot / self.stepwise_increment)
                rot *= self.stepwise_increment
                rot %= 360

            info_rot = (rot)
            context.area.header_text_set("Rotation %.4f " % info_rot)

        if (event.type == 'LEFTMOUSE' or
           event.type == 'RET' or
           event.type == 'NUMPAD_ENTER' or
           not self.tab):
            bpy.types.SpaceSequenceEditor.draw_handler_remove(
                self.handle_line, 'PREVIEW')

            scene = context.scene
            if scene.tool_settings.use_keyframe_insert_auto:
                cf = context.scene.frame_current
                pivot_type = context.scene.seq_pivot_type
                if (pivot_type == '0' and len(self.tab) > 1) or pivot_type == '2':
                    for strip in self.tab:
                        strip.keyframe_insert(data_path='translate_start_x', frame=cf)
                        strip.keyframe_insert(data_path='translate_start_y', frame=cf)
                        strip.keyframe_insert(data_path='rotation_start', frame=cf)
                elif pivot_type == '1' or pivot_type == '3' or (pivot_type == '0' and len(self.tab) == 1):
                    for strip in self.tab:
                        strip.keyframe_insert(data_path='rotation_start', frame=cf)

            context.area.header_text_set()
            return {'FINISHED'}

        if event.type == 'ESC' or event.type == 'RIGHTMOUSE':
            for i in range(len(self.tab)):
                strip = self.tab[i]
                init_rot = self.tab_init[i]
                init_t = self.tab_init_t[i]

                strip.rotation_start = init_rot
                strip.translate_start_x = set_pos_x(strip, init_t[0])
                strip.translate_start_y = set_pos_y(strip, init_t[1])

            bpy.types.SpaceSequenceEditor.draw_handler_remove(
                self.handle_line, 'PREVIEW')
            context.area.header_text_set()
            return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        scene = context.scene
        view2d = context.region.view2d

        bpy.ops.vse_transform_tools.initialize_pivot()

        if event.alt:
            selected = ensure_transforms()
            for strip in selected:
                strip.select = True
                strip.rotation_start = 0.0
            return {'FINISHED'}

        else:
            fac = get_res_factor()
            self.tab_init = []
            self.tab = []
            self.tab_init_t = []
            self.center_real = Vector([0, 0])
            self.center_area = Vector([0, 0])
            self.key_val = ''
            self.slow_additions = []
            rotated_count = 0


            self.tab = ensure_transforms()
            active_strip = scene.sequence_editor.active_strip

            for strip in self.tab:
                strip.select = True
                pos_x = get_pos_x(strip)
                pos_y = get_pos_y(strip)

                self.tab_init.append(strip.rotation_start)
                self.tab_init_t.append([pos_x, pos_y])

                flip_x = 1
                if strip.use_flip_x:
                    flip_x = -1

                flip_y = 1
                if strip.use_flip_y:
                    flip_y = -1

                self.center_real += Vector((
                    flip_x * pos_x, flip_y * pos_y))
                self.center_area += Vector((
                    flip_x * pos_x, flip_y * pos_y))

                rotated_count += 1

            if self.tab:
                self.center_real /= rotated_count
                if context.scene.seq_pivot_type == '2':
                    cur_loc = context.scene.seq_cursor2d_loc
                    pos = view2d.view_to_region(cur_loc[0], cur_loc[1])
                    self.center_area = Vector(pos)

                elif context.scene.seq_pivot_type == '3':
                    flip_x = 1
                    if strip.use_flip_x:
                        flip_x = -1

                    flip_y = 1
                    if strip.use_flip_y:
                        flip_y = -1

                    pos_x = get_pos_x(active_strip)
                    pos_y = get_pos_y(active_strip)

                    self.center_real = Vector((
                        flip_x * pos_x, flip_y * pos_y))

                    pos_x *= flip_x * fac
                    pos_y *= flip_y * fac

                    view_2d = context.region.view2d
                    pos = view_2d.view_to_region(pos_x, pos_y)
                    self.center_area = Vector(pos)

                else:
                    self.center_area /= rotated_count

                    pos_x = self.center_area.x * fac
                    pos_y = self.center_area.y * fac
                    pos = view2d.view_to_region(
                        pos_x, pos_y, clip=False)
                    self.center_area = Vector(pos)

                self.vec_init = Vector(
                    (event.mouse_region_x, event.mouse_region_y))

                self.vec_init -= self.center_area

                self.vec_prev = Vector(self.vec_init)

                self.init_rot = active_strip.rotation_start

            args = (self, context)
            self.handle_line = bpy.types.SpaceSequenceEditor.draw_handler_add(
                draw_px_point, args, 'PREVIEW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}
