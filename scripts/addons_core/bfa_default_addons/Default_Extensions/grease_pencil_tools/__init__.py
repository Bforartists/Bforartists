# SPDX-FileCopyrightText: 2020-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from .  import (prefs,
                box_deform,
                line_reshape,
                rotate_canvas,
                layer_navigator,
                timeline_scrub,
                draw_tools,
                import_brush_pack,
                ui_panels,
                )

modules = (
    prefs,
    box_deform,
    line_reshape,
    rotate_canvas,
    layer_navigator,
    timeline_scrub,
    draw_tools,
    import_brush_pack,
    ui_panels,
)

def register():
    if bpy.app.background:
        return

    for mod in modules:
        mod.register()

    ## Update tab name with update in pref file (passing addon_prefs)
    prefs.update_panel(prefs.get_addon_prefs(), bpy.context)

def unregister():
    if bpy.app.background:
        return

    for mod in modules:
        mod.unregister()

if __name__ == "__main__":
    register()
