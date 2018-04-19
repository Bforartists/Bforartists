import bpy
import math
from mathutils import Vector
from mathutils import Quaternion

from .draw import draw_axes


def func_constrain_axis_mmb(self, context, key, value, angle):
    if len(self.tab) > 1:
        angle = 0
    if key == 'MIDDLEMOUSE':
        if value == 'PRESS':
            if self.handle_axes == None:
                args = (self, context, angle)
                self.handle_axes = bpy.types.SpaceSequenceEditor.draw_handler_add(
                    draw_axes, args, 'PREVIEW', 'POST_PIXEL')
            self.choose_axis = True
            self.pos_clic = self.mouse_pos
        if value == 'RELEASE' :
            self.choose_axis = False
            if self.pos_clic == self.mouse_pos:
                self.axis_x = self.axis_y = True
                if self.handle_axes:
                    bpy.types.SpaceSequenceEditor.draw_handler_remove(
                        self.handle_axes, 'PREVIEW')
                    self.handle_axes = None
    if self.choose_axis:
        vec_axis_z = Vector((0, 0, 1))
        vec_axis_x = Vector((1, 0, 0))
        vec_axis_x.rotate(Quaternion(vec_axis_z, math.radians(angle)))
        vec_axis_x = vec_axis_x.to_2d()
        vec_axis_y = Vector((0, 1, 0))
        vec_axis_y.rotate(Quaternion(vec_axis_z, math.radians(angle)))
        vec_axis_y = vec_axis_y.to_2d()

        ang_x = math.degrees(vec_axis_x.angle(self.mouse_pos - self.center_area))
        ang_y = math.degrees(vec_axis_y.angle(self.mouse_pos - self.center_area))

        if ang_x > 90:
            ang_x = 180 - ang_x
        if ang_y > 90:
            ang_y = 180 - ang_y

        if ang_x < ang_y:
            self.axis_x = True
            self.axis_y = False
        else :
            self.axis_x = False
            self.axis_y = True
