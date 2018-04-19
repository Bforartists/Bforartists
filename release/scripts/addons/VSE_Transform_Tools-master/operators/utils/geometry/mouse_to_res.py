import bpy
from mathutils import Vector

from .get_res_factor import get_res_factor


def mouse_to_res(mouse_vec):
    """
    Convert mouse click position to pixel position.

    When a user clicks the preview window, the position is given as a
    unit of pixels from the bottom left of the entire preview window.

    This function converts that position to a unit of video resolution
    begining from the bottom left of the player part of the preview
    window

    Args
        :mouse_vec: The point at which the mouse click occured
                    (mathutils.Vector)
    Returns
        :mouse_res: The point at which the mouse click occured, in
                    resolution pixels (mathutils.Vector)
    """
    scene = bpy.context.scene

    res_x = scene.render.resolution_x
    res_y = scene.render.resolution_y

    mouse_x = mouse_vec.x
    mouse_y = mouse_vec.y

    fac = get_res_factor()

    pos = bpy.context.region.view2d.region_to_view(mouse_x, mouse_y)

    pos_x = (pos[0] + (res_x * fac / 2)) / fac
    pos_y = (pos[1] + (res_y * fac / 2)) / fac

    mouse_res = Vector((pos_x, pos_y))

    return mouse_res
