import bgl
from mathutils import Vector

def draw_line(start, end):
    """
    Draws a line using two Vector points
    """
    bgl.glBegin(bgl.GL_LINES)
    bgl.glVertex2f(start.x, start.y)
    bgl.glVertex2f(end.x, end.y)
    bgl.glEnd()
