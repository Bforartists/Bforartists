import bpy
from .draw import draw_axes


def func_constrain_axis(self, context, key, value, angle):
    if len(self.tab) > 1:
        angle = 0
    if key in ['X','Y']:
        if self.handle_axes == None:
            args = (self, context, angle)
            self.handle_axes = bpy.types.SpaceSequenceEditor.draw_handler_add(
                draw_axes, args, 'PREVIEW', 'POST_PIXEL')
        if key == 'X' and value == 'PRESS':
            if self.axis_x == True and self.axis_y == True:
                self.axis_y = False
            elif self.axis_x == True and self.axis_y == False:
                self.axis_y = True
            elif self.axis_x == False and self.axis_y == True:
                self.axis_y = False
                self.axis_x = True

        if key == 'Y' and value == 'PRESS':
            if self.axis_x == True and self.axis_y == True:
                self.axis_x = False
            elif self.axis_x == False and self.axis_y == True:
                self.axis_x = True
            elif self.axis_x == True and self.axis_y == False:
                self.axis_y = True
                self.axis_x = False

        if self.axis_x and self.axis_y:
            if self.handle_axes:
                bpy.types.SpaceSequenceEditor.draw_handler_remove(
                    self.handle_axes, 'PREVIEW')
                self.handle_axes = None
