import bpy

def set_pos_y(strip, pos):
    """
    Set the Y position of a transform strip, accounting for whether or
    not the translation unit is set to PERCENT

    Args
        :strip: The transform strip (bpy.types.Sequence)
        :pos:   The X position the strip should be moved to, in pixels
                (int)
    """
    res_y = bpy.context.scene.render.resolution_y

    if strip.translation_unit == 'PERCENT':
        pos = pos * 100 / res_y

    return pos
