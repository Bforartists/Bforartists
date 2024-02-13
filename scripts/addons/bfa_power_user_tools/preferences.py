# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import bpy

class BFA_UI_preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.scale_y = 1.5

        wm = context.window_manager

        row = layout.row()
        col = row.column(align=True)
        col.label(text="Animation:", icon="TIME")
        layout.prop(wm.BFA_UI_addon_props, "BFA_PROP_toggle_insertkeyframes")
