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

def seperator(self, context):
    self.layout.separator()


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
    bpy.types.VIEW3D_MT_gpencil_animation.append(seperator)
    bpy.types.VIEW3D_MT_gpencil_animation.append(ops.BFA_OT_insertframe_left.menu_func)
    bpy.types.VIEW3D_MT_gpencil_animation.append(ops.BFA_OT_removeframe_left.menu_func)
    bpy.types.VIEW3D_MT_gpencil_animation.append(seperator)
    bpy.types.VIEW3D_MT_gpencil_animation.append(ops.BFA_OT_insertframe_right.menu_func)
    bpy.types.VIEW3D_MT_gpencil_animation.append(ops.BFA_OT_removeframe_right.menu_func)

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
    bpy.types.TIME_MT_editor_menus.append(BFA_MT_timeline_key.menu_func) # Creates menu before adding in operators
    bpy.types.BFA_MT_timeline_key.append(seperator)
    bpy.types.BFA_MT_timeline_key.append(ops.BFA_OT_insertframe_left.menu_func)
    bpy.types.BFA_MT_timeline_key.append(ops.BFA_OT_removeframe_left.menu_func)
    bpy.types.BFA_MT_timeline_key.append(seperator)
    bpy.types.BFA_MT_timeline_key.append(ops.BFA_OT_insertframe_right.menu_func)
    bpy.types.BFA_MT_timeline_key.append(ops.BFA_OT_removeframe_right.menu_func)


def unregister():
    ## 3D View Editor
    bpy.types.VIEW3D_MT_object.remove(seperator)
    bpy.types.VIEW3D_MT_object_animation.remove(ops.BFA_OT_insertframe_left.menu_func)
    bpy.types.VIEW3D_MT_object_animation.remove(ops.BFA_OT_insertframe_left.menu_func)
    bpy.types.VIEW3D_MT_object_animation.remove(seperator)
    bpy.types.VIEW3D_MT_object_animation.remove(ops.BFA_OT_insertframe_right.menu_func)
    bpy.types.VIEW3D_MT_object_animation.remove(ops.BFA_OT_removeframe_right.menu_func)

    ## 3D View Editor - Grease Pencil
    bpy.types.VIEW3D_MT_gpencil_animation.remove(seperator)
    bpy.types.VIEW3D_MT_gpencil_animation.remove(ops.BFA_OT_insertframe_left.menu_func)
    bpy.types.VIEW3D_MT_gpencil_animation.remove(ops.BFA_OT_removeframe_left.menu_func)
    bpy.types.VIEW3D_MT_gpencil_animation.remove(seperator)
    bpy.types.VIEW3D_MT_gpencil_animation.remove(ops.BFA_OT_insertframe_right.menu_func)
    bpy.types.VIEW3D_MT_gpencil_animation.remove(ops.BFA_OT_removeframe_right.menu_func)

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
    bpy.types.BFA_MT_timeline_key.remove(seperator)
    bpy.types.BFA_MT_timeline_key.remove(ops.BFA_OT_insertframe_left.menu_func)
    bpy.types.BFA_MT_timeline_key.remove(ops.BFA_OT_removeframe_left.menu_func)
    bpy.types.BFA_MT_timeline_key.remove(seperator)
    bpy.types.BFA_MT_timeline_key.remove(ops.BFA_OT_insertframe_right.menu_func)
    bpy.types.BFA_MT_timeline_key.remove(ops.BFA_OT_removeframe_right.menu_func)
    bpy.types.TIME_MT_editor_menus.remove(BFA_MT_timeline_key.menu_func) # Removes menu after removing operators

    for cls in menu_classes:
        bpy.utils.unregister_class(cls)
