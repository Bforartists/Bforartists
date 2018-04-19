import bpy
import math
from mathutils import Vector

from ..utils.geometry import set_pos_x
from ..utils.geometry import set_pos_y
from ..utils.geometry import rotate_point
from ..utils.geometry import get_res_factor


def apply_strip_rotation(self, strip, rot, init_rot, init_t, event):
    """
    Update a strip's rotation & position

    Parameters
    ----------
    strip : bpy.types.Sequence
        The transform strip that is being rotated
    rot : float
        The change in rotation since init_rot
    init_t : list
        the [x, y] position of the strip
    event : bpy.types.Event
        Allows us to check if ctrl is pressed
    """
    flip_x = 1
    if strip.use_flip_x:
        flip_x = -1

    flip_y = 1
    if strip.use_flip_y:
        flip_y = -1

    strip_rot = init_rot + (flip_x * flip_y * rot)

    if event.ctrl:
        strip_rot = math.ceil(strip_rot / self.stepwise_increment)
        strip_rot *= self.stepwise_increment

    pivot_type = bpy.context.scene.seq_pivot_type

    if (pivot_type == '1' or
       pivot_type in ['0', '3'] and len(self.tab) == 1):
        strip.rotation_start = strip_rot

    elif pivot_type in ['0', '3'] and len(self.tab) > 1:
        pos_init = Vector([init_t[0], init_t[1]])

        pos_flip_x = flip_x * self.center_real.x
        pos_flip_y = flip_y * self.center_real.y
        pos_flip = Vector([pos_flip_x, pos_flip_y])

        pos_init -= pos_flip
        point_rot = flip_x * flip_y * math.radians(rot)

        np = rotate_point(pos_init, point_rot)
        if event.ctrl:
            p_rot_degs = math.radians(strip_rot - init_rot)
            point_rot = flip_x * flip_y * p_rot_degs
            np = rotate_point(pos_init, point_rot)

        pos_x = np.x + flip_x * self.center_real.x
        pos_x = set_pos_x(strip, pos_x)

        pos_y = np.y + flip_y * self.center_real.y
        pos_y = set_pos_y(strip, pos_y)

        if np.x == 0 and np.y == 0:
            strip.rotation_start = strip_rot

        else:
            strip.rotation_start = strip_rot
            strip.translate_start_x = pos_x
            strip.translate_start_y = pos_y

    elif pivot_type == '2':
        fac = get_res_factor()

        pos_x = flip_x * bpy.context.scene.seq_cursor2d_loc[0]
        pos_y = flip_y * bpy.context.scene.seq_cursor2d_loc[1]

        center_c2d = Vector([pos_x, pos_y])
        center_c2d /= fac

        pos_init = Vector([init_t[0], init_t[1]])
        pos_init -= center_c2d

        point_rot = flip_x * flip_y * math.radians(rot)

        np = rotate_point(pos_init, point_rot)
        if event.ctrl:
            p_rot_degs = math.radians(strip_rot - init_rot)
            point_rot = flip_x * flip_y * p_rot_degs
            np = rotate_point(pos_init, point_rot)

        strip.rotation_start = strip_rot

        pos_x = set_pos_x(strip, np.x + center_c2d.x)
        pos_y = set_pos_y(strip, np.y + center_c2d.y)

        strip.translate_start_x = pos_x
        strip.translate_start_y = pos_y
