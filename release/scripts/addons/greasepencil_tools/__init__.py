# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
"name": "Grease Pencil Tools",
"description": "Extra tools for Grease Pencil",
"author": "Samuel Bernou, Antonio Vazquez, Daniel Martinez Lara, Matias Mendiola",
"version": (1, 6, 2),
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
                timeline_scrub,
                draw_tools,
                import_brush_pack,
                ui_panels,
                )

def register():
    if bpy.app.background:
        return
    prefs.register()
    timeline_scrub.register()
    box_deform.register()
    line_reshape.register()
    rotate_canvas.register()
    draw_tools.register()
    import_brush_pack.register()
    ui_panels.register()

    ## update tab name with update in pref file (passing addon_prefs)
    prefs.update_panel(prefs.get_addon_prefs(), bpy.context)

def unregister():
    if bpy.app.background:
        return
    ui_panels.unregister()
    import_brush_pack.unregister()
    draw_tools.unregister()
    rotate_canvas.unregister()
    box_deform.unregister()
    line_reshape.unregister()
    timeline_scrub.unregister()
    prefs.unregister()

if __name__ == "__main__":
    register()
