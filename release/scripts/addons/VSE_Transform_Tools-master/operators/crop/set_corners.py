import math
from mathutils import Vector

from .get_perpendicular_point import get_perpendicular_point
from ..utils.geometry import get_strip_corners
from ..utils.geometry import get_preview_offset
from ..utils.geometry import rotate_point


def set_corners(self, context):
    """
    Set the crop corner handles based on how they are dragged by the
    user.
    """
    active_strip = context.scene.sequence_editor.active_strip
    angle = math.radians(active_strip.rotation_start)

    sin = math.sin(angle)
    cos = math.cos(angle)

    offset_x, offset_y, fac, preview_zoom = get_preview_offset()

    self.max_corners = get_strip_corners(active_strip)
    for corner in self.max_corners:
        corner.x = (corner.x * preview_zoom * fac) + offset_x
        corner.y = (corner.y * preview_zoom * fac) + offset_y

    origin = self.max_corners[2] - self.max_corners[0]

    bl = rotate_point(self.max_corners[0], -angle, origin)
    tl = rotate_point(self.max_corners[1], -angle, origin)
    tr = rotate_point(self.max_corners[2], -angle, origin)
    br = rotate_point(self.max_corners[3], -angle, origin)

    vec = self.current_mouse - self.mouse_pos

    crop_left = self.crop_left * preview_zoom * fac
    crop_bottom = self.crop_bottom * preview_zoom * fac
    crop_top = self.crop_top * preview_zoom * fac
    crop_right = self.crop_right * preview_zoom * fac

    cushion = 10
    if self.clicked_quad is not None:
        for i in range(len(self.max_corners)):
            # Bottom Left Clicked
            if self.clicked_quad == 0:
                pt_x = bl.x + (vec.x * cos) + (vec.y * sin) + crop_left
                pt_y = bl.y + (vec.y * cos) - (vec.x * sin) + crop_bottom
                pt = get_perpendicular_point(
                    Vector([pt_x, pt_y]), bl, tl, tr, br)

                self.corners[2].x = tr.x - crop_right
                self.corners[2].y = tr.y - crop_top

                if pt.x > self.corners[2].x - cushion:
                    pt.x = self.corners[2].x - cushion
                if pt.y > self.corners[2].y - cushion:
                    pt.y = self.corners[2].y - cushion

                self.corners[0] = pt

                self.corners[1].x = tl.x + (pt.x - bl.x)
                self.corners[1].y = tl.y - crop_top

                self.corners[3].x = br.x - crop_right
                self.corners[3].y = br.y + (pt.y - bl.y)

                break
            # Top Left Clicked
            elif self.clicked_quad == 1:
                pt_x = tl.x + (vec.x * cos) + (vec.y * sin) + crop_left
                pt_y = tl.y + (vec.y * cos) - (vec.x * sin) - crop_top
                pt = get_perpendicular_point(
                    Vector([pt_x, pt_y]), bl, tl, tr, br)

                self.corners[3].x = br.x - crop_right
                self.corners[3].y = br.y + crop_bottom

                if pt.x > self.corners[3].x - cushion:
                    pt.x = self.corners[3].x - cushion
                if pt.y < self.corners[3].y + cushion:
                    pt.y = self.corners[3].y + cushion

                self.corners[1] = pt

                self.corners[0].x = bl.x + (pt.x - tl.x)
                self.corners[0].y = bl.y + crop_bottom

                self.corners[2].x = tr.x - crop_right
                self.corners[2].y = tr.y - (tl.y - pt.y)

                break
            # Top Right Clicked
            elif self.clicked_quad == 2:
                pt_x = tr.x + (vec.x * cos) + (vec.y * sin) - crop_right
                pt_y = tr.y + (vec.y * cos) - (vec.x * sin) - crop_top
                pt = get_perpendicular_point(
                    Vector([pt_x, pt_y]), bl, tl, tr, br)

                self.corners[0].x = bl.x + crop_left
                self.corners[0].y = bl.y + crop_bottom

                if pt.x < self.corners[0].x + cushion:
                    pt.x = self.corners[0].x + cushion
                if pt.y < self.corners[0].y + cushion:
                    pt.y = self.corners[0].y + cushion

                self.corners[2] = pt

                self.corners[1].x = tl.x + crop_left
                self.corners[1].y = tl.y - (tr.y - pt.y)

                self.corners[3].x = br.x - (tr.x - pt.x)
                self.corners[3].y = br.y + crop_bottom
            # Bottom Right Clicked
            elif self.clicked_quad == 3:
                pt_x = br.x + (vec.x * cos) + (vec.y * sin) - crop_right
                pt_y = br.y + (vec.y * cos) - (vec.x * sin) + crop_bottom
                pt = get_perpendicular_point(
                    Vector([pt_x, pt_y]), bl, tl, tr, br)

                self.corners[1].x = tl.x + crop_left
                self.corners[1].y = tl.y - crop_top

                if pt.x < self.corners[1].x + cushion:
                    pt.x = self.corners[1].x + cushion
                if pt.y > self.corners[1].y - cushion:
                    pt.y = self.corners[1].y - cushion

                self.corners[3] = pt

                self.corners[0].x = bl.x + crop_left
                self.corners[0].y = bl.y + (pt.y - br.y)

                self.corners[2].x = tr.x - (tr.x - pt.x)
                self.corners[2].y = tr.y - crop_top

    else:
        self.corners[0].x = bl.x + crop_left
        self.corners[0].y = bl.y + crop_bottom

        self.corners[1].x = tl.x + crop_left
        self.corners[1].y = tl.y - crop_top

        self.corners[2].x = tr.x - crop_right
        self.corners[2].y = tr.y - crop_top

        self.corners[3].x = br.x - crop_right
        self.corners[3].y = br.y + crop_bottom

    self.corners[0] = rotate_point(self.corners[0], angle, origin)
    self.corners[1] = rotate_point(self.corners[1], angle, origin)
    self.corners[2] = rotate_point(self.corners[2], angle, origin)
    self.corners[3] = rotate_point(self.corners[3], angle, origin)
