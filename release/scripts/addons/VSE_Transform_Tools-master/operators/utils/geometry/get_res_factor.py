import bpy


def get_res_factor():
    """
    Get the scene resolution percentage as a factor

    Returns
        :fac: The resolution factor (float)
    """
    fac = 1.0

    prs = bpy.context.space_data.proxy_render_size
    res_perc = bpy.context.scene.render.resolution_percentage

    if prs == 'SCENE':
        fac = res_perc / 100

    return fac
