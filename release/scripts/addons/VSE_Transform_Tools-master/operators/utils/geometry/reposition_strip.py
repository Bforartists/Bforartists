import bpy


def reposition_strip(strip, group_box):
    """
    Reposition a (non-transform) strip.

    After adjusting scene resolution, strip sizes will be
    discombobulated. This function will reset a strip's size and
    position to how it was relative to the group box prior to the
    resolution change.

    Args
        :strip:     A strip (bpy.types.Sequence)
        :group_box: The group bounding box prior to the scene resolution
                    change. (list of int: ie [left, right, bottom, top])
    """
    scene = bpy.context.scene

    min_left, max_right, min_bottom, max_top = group_box

    total_width = max_right - min_left
    total_height = max_top - min_bottom

    res_x = scene.render.resolution_x
    res_y = scene.render.resolution_y

    available_width = res_x - total_width
    available_height = res_y - total_height

    print(strip.name)

    if strip.use_translation:
        strip.transform.offset_x -= min_left
        strip.transform.offset_y -= min_bottom

    if not hasattr(strip, 'elements') and strip.use_crop:
        if strip.crop.min_x < available_width:
            available_width -= strip.crop.min_x
            strip.crop.min_x = 0
        else:
            strip.crop.min_x -= available_width
            available_width = 0

        if strip.crop.min_y < available_height:
            available_height -= strip.crop.min_y
            strip.crop.min_y = 0
        else:
            strip.crop.min_y -= available_height
            available_height = 0

        strip.crop.max_x -= available_width
        strip.crop.max_y -= available_height
