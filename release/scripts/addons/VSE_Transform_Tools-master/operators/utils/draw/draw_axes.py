import bpy
import bgl

from ..geometry.get_group_box import get_group_box
from ..geometry.get_preview_offset import get_preview_offset

def draw_axes(self, context, angle):
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glLineWidth(2)

    bgl.glPushMatrix()

    transforms = []
    strips = bpy.context.selected_sequences
    for strip in strips:
        if strip.type == 'TRANSFORM':
            transforms.append(strip)

    group_box = get_group_box(transforms)
    min_left, max_right, min_bottom, max_top = group_box
    group_width = max_right - min_left
    group_height = max_top - min_bottom

    group_pos_x = min_left + (group_width / 2)
    group_pos_y = min_bottom + (group_height / 2)

    offset_x, offset_y, fac, preview_zoom = get_preview_offset()

    x = (group_pos_x * fac * preview_zoom) + offset_x
    y = (group_pos_y * fac * preview_zoom) + offset_y

    bgl.glTranslatef(x, y, 0)
    bgl.glRotatef(angle, 0, 0, 1)

    bgl.glBegin(bgl.GL_LINES)
    bgl.glColor4f(1.0, 0.0, 0.0, 0.2 * self.choose_axis + self.axis_x * 0.8)
    bgl.glVertex2f(-10000, 0)
    bgl.glVertex2f(10000, 0)
    bgl.glColor4f(0.0, 1.0, 0.0, 0.2 * self.choose_axis + self.axis_y * 0.8)
    bgl.glVertex2f(0, -10000)
    bgl.glVertex2f(0, 10000)
    bgl.glEnd()

    bgl.glPopMatrix()

    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
