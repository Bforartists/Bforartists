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
"""
3D View Shading Shortcuts

Two new shortcuts have been added to the 3D View.
Shift+Z Rendered Preview (now in Blender 2.70)
Alt+Shift+Z Only Render
"""

import bpy


KEYMAPS = list()


class AMTH_VIEW3D_OT_show_only_render(bpy.types.Operator):
    bl_idname = "view3d.show_only_render"
    bl_label = "Show Only Render"

    def execute(self, context):
        space = bpy.context.space_data

        if space.show_only_render:
            space.show_only_render = False
        else:
            space.show_only_render = True
        return {"FINISHED"}


def register():
    bpy.utils.register_class(AMTH_VIEW3D_OT_show_only_render)
    kc = bpy.context.window_manager.keyconfigs.addon
    km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
    kmi = km.keymap_items.new("view3d.show_only_render", "Z", "PRESS",
                              shift=True, alt=True)
    KEYMAPS.append((km, kmi))


def unregister():
    bpy.utils.unregister_class(AMTH_VIEW3D_OT_show_only_render)
    for km, kmi in KEYMAPS:
        km.keymap_items.remove(kmi)
    KEYMAPS.clear()
