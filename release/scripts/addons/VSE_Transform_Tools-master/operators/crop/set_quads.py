import math
from mathutils import Vector
from ..utils.geometry import rotate_point


def set_quads(self, context):
    """
    Set the location of the crop handles
    """
    self.corner_quads = []

    active_strip = context.scene.sequence_editor.active_strip
    angle = math.radians(active_strip.rotation_start)
    rect_size = 7.5

    for corner in self.corners:
        origin = corner

        x1 = corner.x - rect_size
        x2 = corner.x + rect_size
        y1 = corner.y - rect_size
        y2 = corner.y + rect_size

        bl = rotate_point(Vector([x1, y1]), angle, origin)
        tl = rotate_point(Vector([x1, y2]), angle, origin)
        tr = rotate_point(Vector([x2, y2]), angle, origin)
        br = rotate_point(Vector([x2, y1]), angle, origin)

        self.corner_quads.append([bl, tl, tr, br])
