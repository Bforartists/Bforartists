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

# Grease Pencil Select Menu - shared across draw, sculpt, vertex paint, and weight paint modes
class BFA_MT_gp_select(bpy.types.Menu):
    bl_idname = "BFA_MT_gp_select"
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.gp_select_layer_under_mouse", icon='GREASEPENCIL')
        layout.operator("view3d.gp_select_layer_under_mouse_isolate", icon='LOCKED')

    def menu_func(self, context):
        wm = context.window_manager
        if wm.BFA_UI_addon_props.BFA_PROP_toggle_gplayerselect:
            self.layout.menu(BFA_MT_gp_select.bl_idname)





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
    BFA_MT_gp_select,
]

# Store keymap items for cleanup
ui_keymap_items = []


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



    ## Grease Pencil Edit & Vertex Paint - add operator to existing Select menu
    bpy.types.VIEW3D_MT_select_edit_grease_pencil.append(ops.BFA_OT_gp_select_layer_under_mouse.menu_func)
    bpy.types.VIEW3D_MT_select_edit_grease_pencil.append(ops.BFA_OT_gp_select_layer_under_mouse_isolate.menu_func)

    ## Register Grease Pencil keymap for the operator to work under mouse
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name="Grease Pencil", space_type='EMPTY')
        kmi = km.keymap_items.new(
            ops.BFA_OT_gp_select_layer_under_mouse.bl_idname,
            type='NONE',
            value='PRESS',
            any=True,
        )
        # Store for unregister
        ui_keymap_items.append((km, kmi))

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

    ## Grease Pencil Edit & Vertex Paint Select menu
    bpy.types.VIEW3D_MT_select_edit_grease_pencil.remove(ops.BFA_OT_gp_select_layer_under_mouse.menu_func)

    ## Remove keymap items
    for km, kmi in ui_keymap_items:
        km.keymap_items.remove(kmi)
    ui_keymap_items.clear()


    for cls in menu_classes:
        bpy.utils.unregister_class(cls)
