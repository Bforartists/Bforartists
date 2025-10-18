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

from . import ops
from . import properties

# Declaratives
context = bpy.context
wm = context.window_manager

# Interface Separator
def seperator(self, context):
    self.layout.separator()

# Timeline Editor Key Menu - NOT USED
class BFA_MT_timeline_key(bpy.types.Menu):
    bl_idname = "BFA_MT_timeline_key"
    bl_label = "Key"

    def draw(self, context):
        layout = self.layout
        layout.separator()

    def menu_func(self, context):
        wm = context.window_manager
        if wm.BFA_UI_addon_props.BFA_PROP_toggle_insertframes or wm.BFA_UI_addon_props.BFA_PROP_toggle_animationpanel:
            self.layout.menu(BFA_MT_timeline_key.bl_idname)


# Timeline Editor Header Operators
def BFA_HT_timeline_skipframes(self, context):
    if context.space_data.mode == 'TIMELINE':
        layout = self.layout
        wm = context.window_manager

        row = layout.row(align=True)
        row.enabled = True
        row.alert = False
        row.scale_x = 1.0
        row.scale_y = 1.0

        if wm.BFA_UI_addon_props.BFA_PROP_toggle_insertframes:
            row.operator("anim.removeframe_left", text="", icon="PANEL_CLOSE")
            row.operator("anim.insertframe_left", text="", icon="TRIA_LEFT")

        if wm.BFA_UI_addon_props.BFA_PROP_toggle_insertframes:
            row.operator("anim.insertframe_right", text="", icon="TRIA_RIGHT")
            row.operator("anim.removeframe_right", text="", icon="PANEL_CLOSE")


menu_classes = [
    BFA_MT_timeline_key,
]


def register():
    for cls in menu_classes:
        bpy.utils.register_class(cls)

    ## 3D View Editor
    bpy.types.VIEW3D_MT_object.append(seperator)
    bpy.types.VIEW3D_MT_object_animation.append(ops.BFA_OT_insertframe_left.menu_func)
    bpy.types.VIEW3D_MT_object_animation.append(ops.BFA_OT_removeframe_left.menu_func)
    bpy.types.VIEW3D_MT_object_animation.append(seperator)
    bpy.types.VIEW3D_MT_object_animation.append(ops.BFA_OT_insertframe_right.menu_func)
    bpy.types.VIEW3D_MT_object_animation.append(ops.BFA_OT_removeframe_right.menu_func)

    ## 3D View Editor - Grease Pencil
    bpy.types.VIEW3D_MT_edit_greasepencil_animation.append(seperator)
    bpy.types.VIEW3D_MT_edit_greasepencil_animation.append(ops.BFA_OT_insertframe_left.menu_func)
    bpy.types.VIEW3D_MT_edit_greasepencil_animation.append(ops.BFA_OT_removeframe_left.menu_func)
    bpy.types.VIEW3D_MT_edit_greasepencil_animation.append(seperator)
    bpy.types.VIEW3D_MT_edit_greasepencil_animation.append(ops.BFA_OT_insertframe_right.menu_func)
    bpy.types.VIEW3D_MT_edit_greasepencil_animation.append(ops.BFA_OT_removeframe_right.menu_func)

    ## Dopesheet Editor
    bpy.types.DOPESHEET_MT_key.append(seperator)
    bpy.types.DOPESHEET_MT_key.append(ops.BFA_OT_insertframe_left.menu_func)
    bpy.types.DOPESHEET_MT_key.append(ops.BFA_OT_removeframe_left.menu_func)
    bpy.types.DOPESHEET_MT_key.append(seperator)
    bpy.types.DOPESHEET_MT_key.append(ops.BFA_OT_insertframe_right.menu_func)
    bpy.types.DOPESHEET_MT_key.append(ops.BFA_OT_removeframe_right.menu_func)

    ## Graph Editor
    bpy.types.GRAPH_MT_key.append(seperator)
    bpy.types.GRAPH_MT_key.append(ops.BFA_OT_insertframe_left.menu_func)
    bpy.types.GRAPH_MT_key.append(ops.BFA_OT_removeframe_left.menu_func)
    bpy.types.GRAPH_MT_key.append(seperator)
    bpy.types.GRAPH_MT_key.append(ops.BFA_OT_insertframe_right.menu_func)
    bpy.types.GRAPH_MT_key.append(ops.BFA_OT_removeframe_right.menu_func)

    ## Timeline Editor
    bpy.types.DOPESHEET_HT_header.append(BFA_HT_timeline_skipframes)

def unregister():
    ## 3D View Editor
    bpy.types.VIEW3D_MT_object.remove(seperator)
    bpy.types.VIEW3D_MT_object_animation.remove(ops.BFA_OT_insertframe_left.menu_func)
    bpy.types.VIEW3D_MT_object_animation.remove(ops.BFA_OT_insertframe_left.menu_func)
    bpy.types.VIEW3D_MT_object_animation.remove(seperator)
    bpy.types.VIEW3D_MT_object_animation.remove(ops.BFA_OT_insertframe_right.menu_func)
    bpy.types.VIEW3D_MT_object_animation.remove(ops.BFA_OT_removeframe_right.menu_func)

    ## 3D View Editor - Grease Pencil
    bpy.types.VIEW3D_MT_edit_greasepencil_animation.remove(seperator)
    bpy.types.VIEW3D_MT_edit_greasepencil_animation.remove(ops.BFA_OT_insertframe_left.menu_func)
    bpy.types.VIEW3D_MT_edit_greasepencil_animation.remove(ops.BFA_OT_removeframe_left.menu_func)
    bpy.types.VIEW3D_MT_edit_greasepencil_animation.remove(seperator)
    bpy.types.VIEW3D_MT_edit_greasepencil_animation.remove(ops.BFA_OT_insertframe_right.menu_func)
    bpy.types.VIEW3D_MT_edit_greasepencil_animation.remove(ops.BFA_OT_removeframe_right.menu_func)

    ## Dopesheet Editor
    bpy.types.DOPESHEET_MT_key.remove(seperator)
    bpy.types.DOPESHEET_MT_key.remove(ops.BFA_OT_insertframe_left.menu_func)
    bpy.types.DOPESHEET_MT_key.remove(ops.BFA_OT_removeframe_left.menu_func)
    bpy.types.DOPESHEET_MT_key.remove(seperator)
    bpy.types.DOPESHEET_MT_key.remove(ops.BFA_OT_insertframe_right.menu_func)
    bpy.types.DOPESHEET_MT_key.remove(ops.BFA_OT_removeframe_right.menu_func)

    ## Graph Editor
    bpy.types.GRAPH_MT_key.remove(seperator)
    bpy.types.GRAPH_MT_key.remove(ops.BFA_OT_insertframe_left.menu_func)
    bpy.types.GRAPH_MT_key.remove(ops.BFA_OT_removeframe_left.menu_func)
    bpy.types.GRAPH_MT_key.remove(seperator)
    bpy.types.GRAPH_MT_key.remove(ops.BFA_OT_insertframe_right.menu_func)
    bpy.types.GRAPH_MT_key.remove(ops.BFA_OT_removeframe_right.menu_func)

    ## Timeline Editor
    bpy.types.DOPESHEET_HT_header.remove(BFA_HT_timeline_skipframes)


    for cls in menu_classes:
        bpy.utils.unregister_class(cls)
