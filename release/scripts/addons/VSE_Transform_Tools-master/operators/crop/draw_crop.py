import bgl
import math
from .set_corners import set_corners
from .set_quads import set_quads


def draw_crop(self, context):
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glLineWidth(1)
    bgl.glColor4f(0.0, 1.0, 1.0, 1.0)

    active_strip = context.scene.sequence_editor.active_strip
    angle = math.radians(active_strip.rotation_start)

    theme = context.user_preferences.themes['Default']
    active_color = theme.view_3d.object_active

    set_corners(self, context)
    set_quads(self, context)

    # Edges
    bgl.glBegin(bgl.GL_LINE_LOOP)
    for corner in self.corners:
        bgl.glVertex2f(corner[0], corner[1])
    bgl.glEnd()

    sin = math.sin(angle)
    cos = math.cos(angle)

    # Points
    for i in range(len(self.corner_quads)):
        quad = self.corner_quads[i]

        bl = quad[0]
        tl = quad[1]
        tr = quad[2]
        br = quad[3]

        if self.clicked_quad == i:
            bgl.glColor4f(
                active_color[0], active_color[1], active_color[2], 1.0)
        else:
            bgl.glColor4f(0.0, 1.0, 1.0, 1.0)

        bgl.glBegin(bgl.GL_QUADS)
        bgl.glVertex2f(bl[0], bl[1])
        bgl.glVertex2f(tl[0], tl[1])
        bgl.glVertex2f(tr[0], tr[1])
        bgl.glVertex2f(br[0], br[1])
        bgl.glEnd()
