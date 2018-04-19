import bpy
from mathutils import Vector

from ..utils.geometry import get_pos_x
from ..utils.geometry import get_pos_y
from ..utils.geometry import set_pos_x
from ..utils.geometry import set_pos_y
from ..utils.geometry import get_res_factor
from ..utils.geometry import get_group_box
from ..utils.geometry import get_preview_offset

from ..utils import func_constrain_axis_mmb
from ..utils import func_constrain_axis
from ..utils import process_input

from ..utils.selection import get_visible_strips
from ..utils.selection import ensure_transforms

from ..utils.draw import draw_px_point
from ..utils.draw import draw_snap

class Scale(bpy.types.Operator):
    """
    ![Demo](https://i.imgur.com/oAxSEYB.gif)
    """
    bl_idname = "vse_transform_tools.scale"
    bl_label = "Scale"
    bl_description = "Scale strips in Image Preview Window"
    bl_options = {'REGISTER', 'UNDO', 'GRAB_CURSOR', 'BLOCKING'}

    axis_x = True
    axis_y = True
    choose_axis = False

    first_mouse = Vector([0, 0])
    pos_clic = Vector([0, 0])
    mouse_pos = Vector([0, 0])

    vec_init = Vector([0, 0])
    vec_act = Vector([0, 0])
    vec_prev = Vector([0, 0])

    center_c2d = Vector([0, 0])

    center_area = Vector([0, 0])
    center_real = Vector([0, 0])

    key_val = ''

    handle_axes = None
    handle_line = None
    handle_snap = None

    group_width = 0
    group_height = 0

    slow_factor = 10
    scale_prev = 1.0

    horizontal_interests = []
    vertical_interests = []

    original_group_box = [Vector([0, 0]), Vector([0, 0]), Vector([0, 0]), Vector([0, 0])]

    last_snap_orientation = ""
    last_line_loc = None
    orientation_conflict_winner = 0

    @classmethod
    def poll(cls, context):
        scene = context.scene
        if (scene.sequence_editor and
           scene.sequence_editor.active_strip):
            return True
        return False

    def modal(self, context, event):
        scene = context.scene

        res_x = scene.render.resolution_x
        res_y = scene.render.resolution_y

        if self.tab:
            self.mouse_pos = Vector([event.mouse_region_x, event.mouse_region_y])
            self.vec_act = self.mouse_pos - self.center_area

            addition = (self.vec_act.length - self.vec_prev.length) / self.vec_init.length
            if event.shift:
                addition /= self.slow_factor

            self.scale_prev += addition

            diff = float(self.scale_prev)

            self.vec_prev = Vector(self.vec_act)

            func_constrain_axis_mmb(
                self, context, event.type, event.value,
                self.sign_rot * context.scene.sequence_editor.active_strip.rotation_start)

            func_constrain_axis(
                self, context, event.type, event.value,
                self.sign_rot * context.scene.sequence_editor.active_strip.rotation_start)

            process_input(self, event.type, event.value)
            if self.key_val != '':
                try:
                    diff = abs(float(self.key_val))
                except ValueError:
                    pass

            diff_x = 1
            if self.axis_x:
                diff_x = diff

            diff_y = 1
            if self.axis_y:
                diff_y = diff

            precision = 5
            snap_distance = int(max([res_x, res_y]) / 100)
            if event.ctrl:

                if context.scene.seq_pivot_type == '2':
                    origin_point = Vector([self.center_c2d.x + (res_x / 2), self.center_c2d.y + (res_y / 2)])
                else:
                    origin_x = self.center_real.x + (res_x / 2)
                    origin_y = self.center_real.y + (res_y / 2)
                    origin_point = Vector([origin_x, origin_y])

                orig_left = self.original_group_box[0]
                trans_diff_l = (((origin_point.x - orig_left) * diff_x) - (origin_point.x - orig_left))
                current_left = orig_left - trans_diff_l

                orig_right = self.original_group_box[1]
                trans_diff_r = (((origin_point.x - orig_right) * diff_x) - (origin_point.x - orig_right))
                current_right = orig_right - trans_diff_r

                orig_bottom = self.original_group_box[2]
                trans_diff_b = (((origin_point.y - orig_bottom) * diff_y) - (origin_point.y - orig_bottom))
                current_bottom = orig_bottom - trans_diff_b

                orig_top = self.original_group_box[3]
                trans_diff_t = (((origin_point.y - orig_top) * diff_y) - (origin_point.y - orig_top))
                current_top = orig_top - trans_diff_t

                orientations = []
                line_locs = []
                offset_x, offset_y, fac, preview_zoom = get_preview_offset()

                for line in self.horizontal_interests:

                    if (current_left < line + snap_distance and
                            current_left > line - snap_distance and
                            abs(origin_point.x - orig_left) > snap_distance):
                        scale_to_line = (origin_point.x - line) / (origin_point.x - orig_left)

                        if self.axis_y:
                            diff_y *= (scale_to_line / diff_x)
                        diff_x = scale_to_line

                        line_locs.append((line * fac * preview_zoom) + offset_x)
                        orientations.append("VERTICAL")

                        break

                    if (current_right > line - snap_distance and
                            current_right < line + snap_distance and
                            abs(origin_point.x - orig_right) > snap_distance):
                        scale_to_line = (origin_point.x - line) / (origin_point.x - orig_right)

                        if self.axis_y:
                            diff_y *= (scale_to_line / diff_x)
                        diff_x = scale_to_line

                        line_locs.append((line * fac * preview_zoom) + offset_x)
                        orientations.append("VERTICAL")

                for line in self.vertical_interests:
                    if (current_bottom < line + snap_distance and
                            current_bottom > line - snap_distance and
                            abs(origin_point.y - orig_bottom) > snap_distance):
                        scale_to_line = (origin_point.y - line) / (origin_point.y - orig_bottom)

                        if self.axis_x:
                            diff_x *= (scale_to_line / diff_y)
                        diff_y = scale_to_line

                        line_locs.append((line * fac * preview_zoom) + offset_y)
                        orientations.append("HORIZONTAL")

                        break

                    if (current_top > line - snap_distance and
                            current_top < line + snap_distance and
                            abs(origin_point.y - orig_top) > snap_distance):

                        scale_to_line = (origin_point.y - line) / (origin_point.y - orig_top)
                        if self.axis_x:
                            diff_x *= (scale_to_line / diff_y)
                        diff_y = scale_to_line

                        line_locs.append((line * fac * preview_zoom) + offset_y)
                        orientations.append("HORIZONTAL")

                orientation = ""
                line_loc = None
                if len(orientations) > 1 and self.last_snap_orientation != "" and self.orientation_conflict_winner == -1:
                    index = orientations.index(self.last_snap_orientation)
                    orientations.pop(index)
                    line_locs.pop(index)

                    self.orientation_conflict_winner = int(not index)

                    orientation = orientations[0]
                    line_loc = line_locs[0]

                elif len(orientations) > 1 and self.last_snap_orientation == "" and self.orientation_conflict_winner == -1:
                    self.orientation_conflict_winner = 0
                    orientation = orientations[0]
                    line_loc = line_locs[0]

                elif len(orientations) > 1:
                    orientation = orientations[self.orientation_conflict_winner]
                    line_loc = line_locs[self.orientation_conflict_winner]

                elif len(orientations) > 0:
                    self.orientation_conflict_winner = 0
                    orientation = orientations[0]
                    line_loc = line_locs[0]

                if orientation != "" and (self.handle_snap == None or "RNA_HANDLE_REMOVED" in str(self.handle_snap)):
                    args = (self, line_loc, orientation)
                    self.handle_snap = bpy.types.SpaceSequenceEditor.draw_handler_add(
                        draw_snap, args, 'PREVIEW', 'POST_PIXEL')
                    self.last_snap_orientation = orientation
                    self.last_line_loc = line_loc
                elif (orientation != self.last_snap_orientation or line_loc != self.last_line_loc) and self.handle_snap != None and not "RNA_HANDLE_REMOVED" in str(self.handle_snap):
                    bpy.types.SpaceSequenceEditor.draw_handler_remove(self.handle_snap, 'PREVIEW')
                    self.last_snap_orientation = orientation
                    self.last_line_loc = line_loc

            elif self.handle_snap != None and not "RNA_HANDLE_REMOVED" in str(self.handle_snap):
                bpy.types.SpaceSequenceEditor.draw_handler_remove(self.handle_snap, 'PREVIEW')

            info_x = round(diff_x, precision)
            info_y = round(diff_y, precision)
            if not self.axis_x:
                context.area.header_text_set("Scale: %.4f along local Y" % info_y)
            if not self.axis_y:
                context.area.header_text_set("Scale: %.4f along local X" % info_x)
            if self.axis_x and self.axis_y :
                context.area.header_text_set("Scale X:%.4f Y: %.4f" % (info_x, info_y))

            for strip, init_s, init_t in zip(self.tab, self.tab_init_s, self.tab_init_t):
                strip.scale_start_x =  init_s[0] * round(diff_x, precision)
                strip.scale_start_y =  init_s[1] * round(diff_y, precision)

                flip_x = 1
                if strip.use_flip_x:
                    flip_x = -1

                flip_y = 1
                if strip.use_flip_y:
                    flip_y = -1

                if context.scene.seq_pivot_type in ['0', '3']:
                    strip.translate_start_x = set_pos_x(strip, (init_t[0] - flip_x * self.center_real.x) * round(diff_x, precision) + flip_x * self.center_real.x)
                    strip.translate_start_y = set_pos_y(strip, (init_t[1] - flip_y * self.center_real.y) * round(diff_y, precision) + flip_y * self.center_real.y)

                if context.scene.seq_pivot_type == '2':
                    strip.translate_start_x = set_pos_x(strip, (init_t[0] - self.center_c2d.x) * round(diff_x, precision) + self.center_c2d.x)
                    strip.translate_start_y = set_pos_y(strip, (init_t[1] - self.center_c2d.y) * round(diff_y, precision) + self.center_c2d.y)

            if (event.type == 'LEFTMOUSE' or
               event.type == 'RET' or
               event.type == 'NUMPAD_ENTER' or
               not self.tab):

                bpy.types.SpaceSequenceEditor.draw_handler_remove(self.handle_line, 'PREVIEW')

                if self.handle_snap != None and not "RNA_HANDLE_REMOVED" in str(self.handle_snap):
                    bpy.types.SpaceSequenceEditor.draw_handler_remove(self.handle_snap, 'PREVIEW')

                scene = context.scene
                if scene.tool_settings.use_keyframe_insert_auto:
                    cf = context.scene.frame_current
                    pivot_type = context.scene.seq_pivot_type
                    if (pivot_type == '0' and len(self.tab) > 1) or pivot_type == '2':
                        for strip in self.tab:
                            strip.keyframe_insert(data_path='translate_start_x', frame=cf)
                            strip.keyframe_insert(data_path='translate_start_y', frame=cf)
                            strip.keyframe_insert(data_path='scale_start_x', frame=cf)
                            strip.keyframe_insert(data_path='scale_start_y', frame=cf)
                    elif pivot_type == '1' or pivot_type == '3' or (pivot_type == '0' and len(self.tab) == 1):
                        for strip in self.tab:
                            strip.keyframe_insert(data_path='scale_start_x', frame=cf)
                            strip.keyframe_insert(data_path='scale_start_y', frame=cf)

                if self.handle_axes:
                    bpy.types.SpaceSequenceEditor.draw_handler_remove(self.handle_axes, 'PREVIEW')
                context.area.header_text_set()
                return {'FINISHED'}

            if event.type == 'ESC' or event.type == 'RIGHTMOUSE':
                for strip, init_s, init_t in zip(self.tab, self.tab_init_s, self.tab_init_t):
                    strip.scale_start_x = init_s[0]
                    strip.scale_start_y = init_s[1]
                    strip.translate_start_x = set_pos_x(strip, init_t[0])
                    strip.translate_start_y = set_pos_y(strip, init_t[1])

                bpy.types.SpaceSequenceEditor.draw_handler_remove(self.handle_line, 'PREVIEW')

                if self.handle_snap != None and not "RNA_HANDLE_REMOVED" in str(self.handle_snap):
                    bpy.types.SpaceSequenceEditor.draw_handler_remove(self.handle_snap, 'PREVIEW')

                if self.handle_axes:
                    bpy.types.SpaceSequenceEditor.draw_handler_remove(self.handle_axes, 'PREVIEW')
                context.area.header_text_set()
                return {'FINISHED'}

        else:
            return {'FINISHED'}
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        scene = context.scene
        bpy.ops.vse_transform_tools.initialize_pivot()

        res_x = scene.render.resolution_x
        res_y = scene.render.resolution_y

        self.horizontal_interests = [0, res_x]
        self.vertical_interests = [0, res_y]

        if event.alt :
            selected = ensure_transforms()
            for strip in selected:
                strip.select = True
                reset_transform_scale(strip)

            return {'FINISHED'}

        else:
            self.tab_init_s = []
            self.tab_init_t = []

            self.tab = []

            self.center_real = Vector([0, 0])
            self.center_area = Vector([0, 0])

            self.key_val = ''
            self.old_key_val = '0'

            fac = get_res_factor()

            scaled_count = 0

            self.tab = ensure_transforms()
            visible_strips = get_visible_strips()

            for strip in visible_strips:
                if strip not in self.tab:
                    left, right, bottom, top = get_group_box([strip])

                    self.horizontal_interests.append(left)
                    self.horizontal_interests.append(right)

                    self.vertical_interests.append(bottom)
                    self.vertical_interests.append(top)

            for strip in self.tab:
                strip.select = True
                self.tab_init_s.append([strip.scale_start_x, strip.scale_start_y])
                self.tab_init_t.append([get_pos_x(strip), get_pos_y(strip)])

                flip_x = 1
                if strip.use_flip_x:
                    flip_x = -1

                flip_y = 1
                if strip.use_flip_y:
                    flip_y = -1

                self.sign_rot = flip_x * flip_y

                center_x = flip_x * get_pos_x(strip)
                center_y = flip_y * get_pos_y(strip)
                self.center_real += Vector([center_x, center_y])
                self.center_area += Vector([center_x, center_y])

            if len(self.tab) > 0:
                self.center_real /= len(self.tab)
                self.original_group_box = get_group_box(self.tab)
                if scene.seq_pivot_type == '2':
                    cursor_x = context.scene.seq_cursor2d_loc[0]
                    cursor_y = context.scene.seq_cursor2d_loc[1]
                    cursor_pos = context.region.view2d.view_to_region(cursor_x, cursor_y)
                    self.center_area = Vector(cursor_pos)

                    self.center_c2d = Vector((flip_x * context.scene.seq_cursor2d_loc[0], flip_y * context.scene.seq_cursor2d_loc[1])) / fac

                elif scene.seq_pivot_type == '3':
                    active_strip = scene.sequence_editor.active_strip

                    flip_x = 1
                    if active_strip.use_flip_x:
                        flip_x = -1

                    flip_y = 1
                    if active_strip.use_flip_y:
                        flip_y = -1

                    pos_x = flip_x * get_pos_x(active_strip)
                    pos_y = flip_y * get_pos_y(active_strip)

                    self.center_real = Vector([pos_x, pos_y])

                    pos = context.region.view2d.view_to_region(pos_x * fac, pos_y * fac)
                    self.center_area = Vector(pos)

                else:
                    self.center_area /= len(self.tab)

                    pos_x = self.center_area.x * fac
                    pos_y = self.center_area.y * fac
                    pos = context.region.view2d.view_to_region(pos_x, pos_y,clip=False)
                    self.center_area = Vector(pos)

                self.vec_init = Vector(
                    (event.mouse_region_x, event.mouse_region_y))
                self.vec_init -= self.center_area

                self.vec_prev = Vector(self.vec_init)

                args = (self, context)
                self.handle_line = bpy.types.SpaceSequenceEditor.draw_handler_add(
                    draw_px_point, args, 'PREVIEW', 'POST_PIXEL')

                context.window_manager.modal_handler_add(self)
                return {'RUNNING_MODAL'}
        return {'FINISHED'}


def reset_transform_scale(strip):
    """Reset a strip to it's factor"""
    strip_in = strip.input_1
    res_x = bpy.context.scene.render.resolution_x
    res_y = bpy.context.scene.render.resolution_y

    if hasattr(strip_in, 'elements'):
        len_crop_x = strip_in.elements[0].orig_width
        len_crop_y = strip_in.elements[0].orig_height

        if strip_in.use_crop:
            len_crop_x -= (strip_in.crop.min_x + strip_in.crop.max_x)
            len_crop_y -= (strip_in.crop.min_y + strip_in.crop.max_y)

        ratio_x = len_crop_x / res_x
        ratio_y = len_crop_y / res_y

        strip.scale_start_x = ratio_x
        strip.scale_start_y = ratio_y

    elif strip_in.type == "SCENE":
        strip_scene = bpy.data.scenes[strip_in.name]

        ratio_x = strip_scene.render.resolution_x / res_x
        ratio_y = strip_scene.render.resolution_y / res_y

        strip.scale_start_x = ratio_x
        strip.scale_start_y = ratio_y

    else:
        strip.scale_start_x = 1.0
        strip.scale_start_y = 1.0
