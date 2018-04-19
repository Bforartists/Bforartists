import bpy


def get_pos_x(strip):
    """
    Get the X position of a transform strip.

    Note that a transform strip's position may be defined as a
    percentage or a number of pixes.


    :param strip: A transform strip (bpy.types.Sequence)
    Returns
        :pos: An X position in pixels (int)
    """
    res_x = bpy.context.scene.render.resolution_x

    if strip.translation_unit == 'PERCENT':
        pos = strip.translate_start_x * res_x / 100

    else:
        pos = strip.translate_start_x

    return pos
