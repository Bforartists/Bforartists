import bpy


def get_strip_box(strip):
    """
    Gets the box of a non-transform strip

    Args
        :strip: A strip from the vse (bpy.types.Sequence)
    Returns
        :box: A list comprising the strip's left, right, bottom, top
              (list of int)
    """
    scene = bpy.context.scene

    res_x = scene.render.resolution_x
    res_y = scene.render.resolution_y

    if not strip.use_translation and not strip.use_crop:
        left = 0
        right = res_x
        bottom = 0
        top = res_y

    elif strip.use_crop and not strip.use_translation:
        left = 0
        right = res_x
        bottom = 0
        top = res_y

    elif not hasattr(strip, 'elements'):
        len_crop_x = res_x
        len_crop_y = res_y
        if strip.use_crop:
            len_crop_x -= (strip.crop.min_x + strip.crop.max_x)
            len_crop_y -= (strip.crop.min_y + strip.crop.max_y)

            if len_crop_x < 0:
                len_crop_x = 0
            if len_crop_y < 0:
                len_crop_y = 0

        left = 0
        right = res_x
        bottom = 0
        top = res_y

        if strip.use_translation:
            left = strip.transform.offset_x
            right = left + len_crop_x
            bottom = strip.transform.offset_y
            top = strip.transform.offset_y + len_crop_y

    elif strip.use_translation and not strip.use_crop:
        left = strip.transform.offset_x
        right = left + strip.elements[0].orig_width
        bottom = strip.transform.offset_y
        top = bottom + strip.elements[0].orig_height

    else:
        total_crop_x = strip.crop.min_x + strip.crop.max_x
        total_crop_y = strip.crop.min_y + strip.crop.max_y

        len_crop_x = strip.elements[0].orig_width - total_crop_x
        len_crop_y = strip.elements[0].orig_height - total_crop_y

        left = strip.transform.offset_x
        right = left + len_crop_x
        bottom = strip.transform.offset_y
        top = bottom + len_crop_y

    box = [left, right, bottom, top]

    return box
