import bgl
from mathutils import Vector

from .draw_line import draw_line


def draw_snap(self, loc, orientation):
    """
    Draws the purple snap lines
    """
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glLineWidth(2)
    bgl.glPushMatrix()

    r = 1.0
    g = 0.0
    b = 1.0
    a = 0.5
    bgl.glColor4f(r, g, b, a)

    if orientation == "VERTICAL":
        bgl.glTranslatef(loc, 0, 0)

        start = Vector([0, -10000])
        end = Vector([0, 10000])
        draw_line(start, end)

    elif orientation == "HORIZONTAL":
        bgl.glTranslatef(0, loc, 0)

        start = Vector([-10000, 0])
        end = Vector([10000, 0])
        draw_line(start, end)

    bgl.glPopMatrix()

    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
