import bpy
import bgl
import math

from . properties import Sun


class NorthClass:

    def __init__(self):
        self.handler = None
        self.isActive = False

    def refresh_screen(self):
        bpy.context.scene.cursor_location.x += 0.0

    def activate(self, context):

        if context.area.type == 'PROPERTIES':
            self.handler = bpy.types.SpaceView3D.draw_handler_add(
                DrawNorth_callback,
                (self, context), 'WINDOW', 'POST_PIXEL')
            self.isActive = True
            self.refresh_screen()
            return True
        return False

    def deactivate(self):
        if self.handler is not None:
            bpy.types.SpaceView3D.draw_handler_remove(self.handler, 'WINDOW')
            self.handler = None
        self.isActive = False
        self.refresh_screen()
        if Sun.SP:
            Sun.SP.ShowNorth = False
        Sun.ShowNorth = False


North = NorthClass()


def DrawNorth_callback(self, context):

    if not Sun.SP.ShowNorth and North.isActive:
        North.deactivate()
        return

    # ------------------------------------------------------------------
    # Set up the compass needle using the current north offset angle
    # less 90 degrees.  This forces the unit circle to begin at the
    # 12 O'clock instead of 3 O'clock position.
    # ------------------------------------------------------------------
    color = (0.2, 0.6, 1.0, 0.7)
    radius = 100
    angle = -(Sun.NorthOffset - math.pi / 2)
    x = math.cos(angle) * radius
    y = math.sin(angle) * radius

    p1, p2 = (0, 0, 0), (x, y, 0)   # Start & end of needle

    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # Thanks to Buerbaum Martin for the following which draws openGL
    # lines.  ( From his script space_view3d_panel_measure.py )
    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # ------------------------------------------------------------------
    # Convert the Perspective Matrix of the current view/region.
    # ------------------------------------------------------------------
    view3d = bpy.context
    region = view3d.region_data
    perspMatrix = region.perspective_matrix
    tempMat = [perspMatrix[j][i] for i in range(4) for j in range(4)]
    perspBuff = bgl.Buffer(bgl.GL_FLOAT, 16, tempMat)

    # ---------------------------------------------------------
    # Store previous OpenGL settings.
    # ---------------------------------------------------------
    MatrixMode_prev = bgl.Buffer(bgl.GL_INT, [1])
    bgl.glGetIntegerv(bgl.GL_MATRIX_MODE, MatrixMode_prev)
    MatrixMode_prev = MatrixMode_prev[0]

    # Store projection matrix
    ProjMatrix_prev = bgl.Buffer(bgl.GL_DOUBLE, [16])
    bgl.glGetFloatv(bgl.GL_PROJECTION_MATRIX, ProjMatrix_prev)

    # Store Line width
    lineWidth_prev = bgl.Buffer(bgl.GL_FLOAT, [1])
    bgl.glGetFloatv(bgl.GL_LINE_WIDTH, lineWidth_prev)
    lineWidth_prev = lineWidth_prev[0]

    # Store GL_BLEND
    blend_prev = bgl.Buffer(bgl.GL_BYTE, [1])
    bgl.glGetFloatv(bgl.GL_BLEND, blend_prev)
    blend_prev = blend_prev[0]

    line_stipple_prev = bgl.Buffer(bgl.GL_BYTE, [1])
    bgl.glGetFloatv(bgl.GL_LINE_STIPPLE, line_stipple_prev)
    line_stipple_prev = line_stipple_prev[0]

    # Store glColor4f
    color_prev = bgl.Buffer(bgl.GL_FLOAT, [4])
    bgl.glGetFloatv(bgl.GL_COLOR, color_prev)

    # ---------------------------------------------------------
    # Prepare for 3D drawing
    # ---------------------------------------------------------
    bgl.glLoadIdentity()
    bgl.glMatrixMode(bgl.GL_PROJECTION)
    bgl.glLoadMatrixf(perspBuff)

    bgl.glEnable(bgl.GL_BLEND)
    bgl.glEnable(bgl.GL_LINE_STIPPLE)

    # ------------------
    # and draw the line
    # ------------------
    width = 2
    bgl.glLineWidth(width)
    bgl.glColor4f(color[0], color[1], color[2], color[3])
    bgl.glBegin(bgl.GL_LINE_STRIP)
    bgl.glVertex3f(p1[0], p1[1], p1[2])
    bgl.glVertex3f(p2[0], p2[1], p2[2])
    bgl.glEnd()

    # ---------------------------------------------------------
    # Restore previous OpenGL settings
    # ---------------------------------------------------------
    bgl.glLoadIdentity()
    bgl.glMatrixMode(MatrixMode_prev)
    bgl.glLoadMatrixf(ProjMatrix_prev)
    bgl.glLineWidth(lineWidth_prev)

    if not blend_prev:
        bgl.glDisable(bgl.GL_BLEND)
    if not line_stipple_prev:
        bgl.glDisable(bgl.GL_LINE_STIPPLE)

    bgl.glColor4f(color_prev[0],
                  color_prev[1],
                  color_prev[2],
                  color_prev[3])
