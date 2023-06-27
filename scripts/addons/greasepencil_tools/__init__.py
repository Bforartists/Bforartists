# SPDX-FileCopyrightText: 2020-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
"name": "Grease Pencil Tools",
"description": "Extra tools for Grease Pencil",
"author": "Samuel Bernou, Antonio Vazquez, Daniel Martinez Lara, Matias Mendiola",
"version": (1, 8, 0),
"blender": (3, 0, 0),
"location": "Sidebar > Grease Pencil > Grease Pencil Tools",
"warning": "",
"doc_url": "{BLENDER_MANUAL_URL}/addons/object/greasepencil_tools.html",
"tracker_url": "https://github.com/Pullusb/greasepencil-addon/issues",
"category": "Object",
"support": "COMMUNITY",
}

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
