import bpy


def get_pos_y(strip):
    """
    Get the Y position of a transform strip. Note that a transform
    strip's position may be defined as a percentage or a number of
    pixes.

    Args
        :strip: A transform strip (bpy.types.Sequence)
    Returns
        :pos: A Y position in pixels (int)
    """
    res_y = bpy.context.scene.render.resolution_y

    if strip.translation_unit == 'PERCENT':
        pos = strip.translate_start_y * res_y / 100

    else:
        pos = strip.translate_start_y

    return pos
