import bgl

from ..utils.geometry import get_preview_offset
from ..utils.geometry import get_strip_corners


def draw_select(self, context):
    """
    Draw a box around each selected strip in the preview window
    """
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glLineWidth(4)

    theme = context.user_preferences.themes['Default']
    active_color = theme.view_3d.object_active
    select_color = theme.view_3d.object_selected
    opacity = 0.9 - (self.seconds / self.fadeout_duration)

    active_strip = context.scene.sequence_editor.active_strip

    offset_x, offset_y, fac, preview_zoom = get_preview_offset()

    for strip in context.selected_sequences:
        if strip == active_strip:
            bgl.glColor4f(
                active_color[0], active_color[1], active_color[2],
                opacity)
        else:
            bgl.glColor4f(
                select_color[0], select_color[1], select_color[2],
                opacity)

        bgl.glBegin(bgl.GL_LINE_LOOP)
        corners = get_strip_corners(strip)
        for corner in corners:
            corner_x = int(corner[0] * preview_zoom * fac) + offset_x
            corner_y = int(corner[1] * preview_zoom * fac) + offset_y
            bgl.glVertex2i(corner_x, corner_y)
        bgl.glEnd()

    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
