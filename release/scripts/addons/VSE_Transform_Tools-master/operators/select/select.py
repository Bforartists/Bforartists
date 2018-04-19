import bpy
import bgl
import math
from mathutils import Vector
from mathutils.geometry import intersect_point_quad_2d

from ..utils.geometry import get_strip_corners
from ..utils.geometry import get_preview_offset
from ..utils.geometry import mouse_to_res

from ..utils.selection import get_visible_strips

from .draw_select import draw_select


class Select(bpy.types.Operator):
    """
    ![Demo](https://i.imgur.com/EVzmMAm.gif)
    """
    bl_idname = "vse_transform_tools.select"
    bl_label = "Select"
    bl_description = "Select visible sequences from the Image Preview"

    timer = None
    seconds = 0
    fadeout_duration = 0.20
    handle_select = None

    @classmethod
    def poll(self, context):
        if context.scene.sequence_editor:
            return True
        return False

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type == 'TIMER':
            self.seconds += 0.01

        if self.seconds > self.fadeout_duration:
            context.window_manager.event_timer_remove(self.timer)

            bpy.types.SpaceSequenceEditor.draw_handler_remove(
                self.handle_select, 'PREVIEW')

            return {'FINISHED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        bpy.ops.vse_transform_tools.initialize_pivot()

        scene = context.scene

        mouse_x = event.mouse_region_x
        mouse_y = event.mouse_region_y

        mouse_vec = Vector([mouse_x, mouse_y])
        vector = mouse_to_res(mouse_vec)

        current_frame = scene.frame_current
        current_strips = []

        sequence_editor = scene.sequence_editor
        selection_list = []

        strips = get_visible_strips()

        if 'MOUSE' in event.type:
            for strip in reversed(strips):

                corners = get_strip_corners(strip)

                bottom_left = Vector(corners[0])
                top_left = Vector(corners[1])
                top_right = Vector(corners[2])
                bottom_right = Vector(corners[3])

                intersects = intersect_point_quad_2d(
                    vector, bottom_left, top_left, top_right,
                    bottom_right)

                if intersects and not event.type == 'A':
                    selection_list.append(strip)
                    if not event.shift:
                        bpy.ops.sequencer.select_all(action='DESELECT')
                        strip.select = True
                        scene.sequence_editor.active_strip = strip
                        break
                    else:
                        if not strip.select:
                            strip.select = True
                            scene.sequence_editor.active_strip = strip
                            break
                        else:
                            strip.select = True
                            break
                if not selection_list and not event.shift and not event.type == 'A':
                    bpy.ops.sequencer.select_all(action='DESELECT')

                if strip.blend_type in ['CROSS', 'REPLACE']:
                    return {'FINISHED'}

        elif event.type == 'A':
            all_selected = True
            for strip in strips:
                if not strip.select:
                    all_selected = False

            bpy.ops.sequencer.select_all(action='DESELECT')

            if not all_selected:
                for strip in strips:
                    strip.select = True

        args = (self, context)
        self.handle_select = bpy.types.SpaceSequenceEditor.draw_handler_add(
            draw_select, args, 'PREVIEW', 'POST_PIXEL')

        self.timer = context.window_manager.event_timer_add(0.01, context.window)

        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}
