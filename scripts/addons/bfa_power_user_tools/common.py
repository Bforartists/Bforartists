from typing import Callable

import bpy

def column_count(region: bpy.types.Region):
    # Currently this just checks the width,
    # we could have different layouts as preferences too.
    system = bpy.context.preferences.system
    view2d = region.view2d
    view2d_scale = (
            view2d.region_to_view(1.0, 0.0)[0] -
            view2d.region_to_view(0.0, 0.0)[0]
    )
    width_scale = region.width * view2d_scale / system.ui_scale

    # how many rows. 4 is text buttons.

    if width_scale > 160.0:
        column_count = 4
    elif width_scale > 140.0:
        column_count = 3
    elif width_scale > 90:
        column_count = 2
    else:
        column_count = 1

    return column_count
