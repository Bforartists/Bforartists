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


""" Copyright 2011 GPL licence applies"""

bl_info = {
    "name": "Collection Manager",
    "description": "Manage collections and their objects",
    "author": "Ryan Inch",
    "version": (1,5,1),
    "blender": (2, 80, 0),
    "location": "View3D - Object Mode (Shortcut - M)",
    "warning": '',  # used for warning icon and text in addons panel
    "wiki_url": "",
    "category": "User Interface"}


if "bpy" in locals():
    import importlib
    
    importlib.reload(internals)
    importlib.reload(operators)
    importlib.reload(ui)

else:
    from . import internals
    from . import operators
    from . import ui

import bpy
from bpy.props import (
    CollectionProperty,
    IntProperty,
    BoolProperty,
    )

addon_keymaps = []

classes = (
    internals.CMListCollection,
    operators.ExpandAllOperator,
    operators.ExpandSublevelOperator,
    operators.CMExcludeOperator,
    operators.CMUnExcludeAllOperator,
    operators.CMRestrictSelectOperator,
    operators.CMUnRestrictSelectAllOperator,
    operators.CMHideOperator,
    operators.CMUnHideAllOperator,
    operators.CMDisableViewportOperator,
    operators.CMUnDisableViewportAllOperator,
    operators.CMDisableRenderOperator,
    operators.CMUnDisableRenderAllOperator,
    operators.CMNewCollectionOperator,
    operators.CMRemoveCollectionOperator,
    operators.CMSetCollectionOperator,
    operators.CMPhantomModeOperator,
    ui.CM_UL_items,
    ui.CollectionManager,
    ui.CMRestrictionTogglesPanel,
    )

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.CMListCollection = CollectionProperty(type=internals.CMListCollection)
    bpy.types.Scene.CMListIndex = IntProperty(update=ui.update_selection)
    
    bpy.types.Scene.show_exclude = BoolProperty(default=True, name="Exclude from View Layer")
    bpy.types.Scene.show_selectable = BoolProperty(default=True, name="Selectable")
    bpy.types.Scene.show_hideviewport = BoolProperty(default=True, name="Hide in Viewport")
    bpy.types.Scene.show_disableviewport = BoolProperty(default=False, name="Disable in Viewports")
    bpy.types.Scene.show_render = BoolProperty(default=False, name="Disable in Renders")
    
    bpy.types.Scene.CM_Phantom_Mode = BoolProperty(default=False)


    # create the global menu hotkey
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='Object Mode')
    kmi = km.keymap_items.new('view3d.collection_manager', 'M', 'PRESS')
    addon_keymaps.append((km, kmi))
 
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.CMListCollection
    del bpy.types.Scene.CMListIndex
    
    del bpy.types.Scene.show_exclude
    del bpy.types.Scene.show_selectable
    del bpy.types.Scene.show_hideviewport
    del bpy.types.Scene.show_disableviewport
    del bpy.types.Scene.show_render
    
    del bpy.types.Scene.CM_Phantom_Mode
    
    # remove keymaps when add-on is deactivated
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    
if __name__ == "__main__":
    register()
