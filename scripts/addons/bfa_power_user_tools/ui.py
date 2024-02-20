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

class BFA_MT_timeline_key(bpy.types.Menu):
    bl_idname = "BFA_MT_timeline_key"
    bl_label = "Key"

    def draw(self, context):
        layout = self.layout
        layout.separator()
        '''
        wm = context.window_manager
        if wm.BFA_UI_addon_props.BFA_PROP_toggle_insertkeyframes:
            layout.operator(operators.BFA_OT_insertframe_left).menu_func
            layout.operator(operators.BFA_OT_insertframe_right).menu_func
        '''

    def menu_func(self, context):
        wm = context.window_manager
        if wm.BFA_UI_addon_props.BFA_PROP_toggle_insertkeyframes:
            self.layout.menu(BFA_MT_timeline_key.bl_idname)

