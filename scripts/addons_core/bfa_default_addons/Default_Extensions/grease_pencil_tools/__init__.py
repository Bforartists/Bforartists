# SPDX-FileCopyrightText: 2020-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Infos
# "location": "Sidebar > Grease Pencil > Grease Pencil Tools",
# "tracker_url": "https://github.com/Pullusb/greasepencil_tools/issues",

import bpy
from .  import (prefs,
                box_deform,
                line_reshape,
                rotate_canvas,
                layer_navigator,
                timeline_scrub,
                draw_tools,
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
