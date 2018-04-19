import bpy

from .get_res_factor import get_res_factor

def get_preview_offset():
    """
    Get the number of pixels (x and y) that the preview is offset in the
    preview window as well as other related information.

    Returns
        :offset_x:     The horizontal offset of the preview window
        :offset_y:     The vertical offset of the preview window
        :fac:          The resolution factor for the scene
        :preview_zoom: The zoom level of the preview window
    """
    context = bpy.context
    fac = get_res_factor()

    width = context.region.width
    height = context.region.height

    rv1 = context.region.view2d.region_to_view(0, 0)
    rv2 = context.region.view2d.region_to_view(width, height)

    res_x = context.scene.render.resolution_x
    res_y = context.scene.render.resolution_y

    preview_zoom = (width / (rv2[0] - rv1[0]))

    offset_x = -int((rv1[0] + ((res_x * fac) / 2)) * preview_zoom)
    offset_y = -int((rv1[1] + ((res_y * fac) / 2)) * preview_zoom)

    return offset_x, offset_y, fac, preview_zoom
