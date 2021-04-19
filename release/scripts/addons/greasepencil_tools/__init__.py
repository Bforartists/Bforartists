# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


bl_info = {
"name": "Grease Pencil Tools",
"description": "Extra tools for Grease Pencil",
"author": "Samuel Bernou, Antonio Vazquez, Daniel Martinez Lara, Matias Mendiola",
"version": (1, 4, 3),
"blender": (2, 91, 0),
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
                import_brush_pack,
                ui_panels,
                )

def register():
    prefs.register()
    timeline_scrub.register()
    box_deform.register()
    line_reshape.register()
    rotate_canvas.register()
    import_brush_pack.register()
    ui_panels.register()

    ## update tab name with update in pref file (passing addon_prefs)
    prefs.update_panel(prefs.get_addon_prefs(), bpy.context)

def unregister():
    ui_panels.unregister()
    import_brush_pack.unregister()
    rotate_canvas.unregister()
    box_deform.unregister()
    line_reshape.unregister()
    timeline_scrub.unregister()
    prefs.unregister()

if __name__ == "__main__":
    register()
