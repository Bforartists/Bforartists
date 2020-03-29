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

# Copyright 2011, Ryan Inch

bl_info = {
    "name": "Collection Manager",
    "description": "Manage collections and their objects",
    "author": "Ryan Inch",
    "version": (2,4,5),
    "blender": (2, 80, 0),
    "location": "View3D - Object Mode (Shortcut - M)",
    "warning": '',  # used for warning icon and text in addons panel
    "doc_url": "{BLENDER_MANUAL_URL}/addons/interface/collection_manager.html",
    "category": "Interface",
}


if "bpy" in locals():
    import importlib

    importlib.reload(internals)
    importlib.reload(operators)
    importlib.reload(qcd_move_widget)
    importlib.reload(qcd_operators)
    importlib.reload(ui)
    importlib.reload(qcd_init)
    importlib.reload(preferences)

else:
    from . import internals
    from . import operators
    from . import qcd_move_widget
    from . import qcd_operators
    from . import ui
    from . import qcd_init
    from . import preferences

import bpy
from bpy.types import PropertyGroup
from bpy.props import (
    CollectionProperty,
    EnumProperty,
    IntProperty,
    BoolProperty,
    StringProperty,
    PointerProperty,
    )


class CollectionManagerProperties(PropertyGroup):
    cm_list_collection: CollectionProperty(type=internals.CMListCollection)
    cm_list_index: IntProperty(update=ui.update_selection)

    show_exclude: BoolProperty(default=True, name="Exclude from View Layer")
    show_selectable: BoolProperty(default=True, name="Selectable")
    show_hide_viewport: BoolProperty(default=True, name="Hide in Viewport")
    show_disable_viewport: BoolProperty(default=False, name="Disable in Viewports")
    show_render: BoolProperty(default=False, name="Disable in Renders")

    in_phantom_mode: BoolProperty(default=False)

    update_header: CollectionProperty(type=internals.CMListCollection)

    qcd_slots_blend_data: StringProperty()


addon_keymaps = []

classes = (
    internals.CMListCollection,
    internals.CMSendReport,
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
    preferences.CMPreferences,
    ui.CM_UL_items,
    ui.CollectionManager,
    ui.CMRestrictionTogglesPanel,
    CollectionManagerProperties,
    )



def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.collection_manager = PointerProperty(type=CollectionManagerProperties)

    # create the global menu hotkey
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='Object Mode')
    kmi = km.keymap_items.new('view3d.collection_manager', 'M', 'PRESS')
    addon_keymaps.append((km, kmi))

    if bpy.context.preferences.addons[__package__].preferences.enable_qcd:
        qcd_init.register_qcd()

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.collection_manager

    # remove keymaps when add-on is deactivated
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    qcd_init.unregister_qcd()


if __name__ == "__main__":
    register()
