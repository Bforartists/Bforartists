import bgl
import math
from mathutils import Vector


def draw_px_point(self, context):
    """
    Draws the handle seen when rotating or scaling
    """
    vx = Vector([1, 0])
    try:
        math.degrees(self.vec_act.angle_signed(vx))
        math.degrees(self.vec_act.angle_signed(vx))
    except ValueError:
        return

    bgl.glEnable(bgl.GL_BLEND)
    bgl.glColor4f(1.0, 0.5, 0.0, 1.0)

    bgl.glLineStipple(4, 0x5555)
    bgl.glEnable(bgl.GL_LINE_STIPPLE)

    bgl.glPushMatrix()
    bgl.glTranslatef(self.center_area.x, self.center_area.y, 0)
    bgl.glBegin(bgl.GL_LINES)
    bgl.glVertex2f(0, 0)
    bgl.glVertex2f(self.vec_act.x, self.vec_act.y)
    bgl.glEnd()
    bgl.glPopMatrix()

    bgl.glDisable(bgl.GL_LINE_STIPPLE)

    bgl.glLineWidth(3)


    bgl.glPushMatrix()
    bgl.glTranslatef(self.center_area.x + self.vec_act.x, self.center_area.y + self.vec_act.y, 0)

    if self.bl_idname == 'VSE_TRANSFORM_TOOLS_OT_scale':
        bgl.glRotatef(math.degrees(self.vec_act.angle_signed(vx)), 0, 0, 1)
    if self.bl_idname == 'VSE_TRANSFORM_TOOLS_OT_rotate':
        bgl.glRotatef(math.degrees(self.vec_act.angle_signed(vx)) + 90, 0, 0, 1)

    bgl.glBegin(bgl.GL_LINES)
    bgl.glVertex2f(5, 0)
    bgl.glVertex2f(15, 0)
    bgl.glVertex2f(15, 0)
    bgl.glVertex2f(10, -7)
    bgl.glVertex2f(15, 0)
    bgl.glVertex2f(10, 7)

    bgl.glVertex2f(-5, 0)
    bgl.glVertex2f(-15, 0)
    bgl.glVertex2f(-15, 0)
    bgl.glVertex2f(-10, -7)
    bgl.glVertex2f(-15, 0)
    bgl.glVertex2f(-10, 7)
    bgl.glEnd()
    bgl.glPopMatrix()

    bgl.glLineWidth(1)

    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
