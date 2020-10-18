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
    "version": (2, 15, 3),
    "blender": (2, 80, 0),
    "location": "View3D - Object Mode (Shortcut - M)",
    "warning": '',  # used for warning icon and text in addons panel
    "doc_url": "{BLENDER_MANUAL_URL}/addons/interface/collection_manager.html",
    "tracker_url": "https://blenderartists.org/t/release-addon-collection-manager-feedback/1186198/",
    "category": "Interface",
}


if "bpy" in locals():
    import importlib

    importlib.reload(internals)
    importlib.reload(operator_utils)
    importlib.reload(operators)
    importlib.reload(qcd_move_widget)
    importlib.reload(qcd_operators)
    importlib.reload(ui)
    importlib.reload(qcd_init)
    importlib.reload(preferences)

else:
    from . import internals
    from . import operator_utils
    from . import operators
    from . import qcd_move_widget
    from . import qcd_operators
    from . import ui
    from . import qcd_init
    from . import preferences

import bpy
from bpy.app.handlers import persistent
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
    cm_list_index: IntProperty()

    show_exclude: BoolProperty(default=True, name="[EC] Exclude from View Layer")
    show_selectable: BoolProperty(default=True, name="[SS] Disable Selection")
    show_hide_viewport: BoolProperty(default=True, name="[VV] Hide in Viewport")
    show_disable_viewport: BoolProperty(default=False, name="[DV] Disable in Viewports")
    show_render: BoolProperty(default=False, name="[RR] Disable in Renders")
    show_holdout: BoolProperty(default=False, name="[HH] Holdout")
    show_indirect_only: BoolProperty(default=False, name="[IO] Indirect Only")

    align_local_ops: BoolProperty(default=False, name="Align Local Options",
                                  description="Align local options in a column to the right")

    in_phantom_mode: BoolProperty(default=False)

    update_header: CollectionProperty(type=internals.CMListCollection)

    ui_separator: StringProperty(name="", default="")

    qcd_slots_blend_data: StringProperty()


addon_keymaps = []

classes = (
    internals.CMListCollection,
    internals.CMSendReport,
    operators.SetActiveCollection,
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
    operators.CMHoldoutOperator,
    operators.CMUnHoldoutAllOperator,
    operators.CMIndirectOnlyOperator,
    operators.CMUnIndirectOnlyAllOperator,
    operators.CMNewCollectionOperator,
    operators.CMRemoveCollectionOperator,
    operators.CMRemoveEmptyCollectionsOperator,
    operators.CMSelectCollectionObjectsOperator,
    operators.CMSetCollectionOperator,
    operators.CMPhantomModeOperator,
    operators.CMApplyPhantomModeOperator,
    preferences.CMPreferences,
    ui.CM_UL_items,
    ui.CollectionManager,
    ui.CMDisplayOptionsPanel,
    ui.SpecialsMenu,
    CollectionManagerProperties,
    )

@persistent
def depsgraph_update_post_handler(dummy):
    if internals.move_triggered:
        internals.move_triggered = False
        return

    internals.move_selection.clear()
    internals.move_active = None

@persistent
def undo_redo_post_handler(dummy):
    internals.move_selection.clear()
    internals.move_active = None


def menu_addition(self, context):
    layout = self.layout

    layout.operator('view3d.collection_manager')

    if bpy.context.preferences.addons[__package__].preferences.enable_qcd:
        layout.operator('view3d.qcd_move_widget')

    layout.separator()


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.collection_manager = PointerProperty(type=CollectionManagerProperties)

    # create the global menu hotkey
    wm = bpy.context.window_manager
    if wm.keyconfigs.addon: # not present when started with --background
        km = wm.keyconfigs.addon.keymaps.new(name='Object Mode')
        kmi = km.keymap_items.new('view3d.collection_manager', 'M', 'PRESS')
        addon_keymaps.append((km, kmi))

    # Add Collection Manager & QCD Move Widget to the Object->Collections menu
    bpy.types.VIEW3D_MT_object_collection.prepend(menu_addition)

    bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_post_handler)
    bpy.app.handlers.undo_post.append(undo_redo_post_handler)
    bpy.app.handlers.redo_post.append(undo_redo_post_handler)

    if bpy.context.preferences.addons[__package__].preferences.enable_qcd:
        qcd_init.register_qcd()

def unregister():
    if bpy.context.preferences.addons[__package__].preferences.enable_qcd:
        qcd_init.unregister_qcd()

    for cls in classes:
        bpy.utils.unregister_class(cls)

    # Remove Collection Manager & QCD Move Widget from the Object->Collections menu
    bpy.types.VIEW3D_MT_object_collection.remove(menu_addition)

    bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update_post_handler)
    bpy.app.handlers.undo_post.remove(undo_redo_post_handler)
    bpy.app.handlers.redo_post.remove(undo_redo_post_handler)

    del bpy.types.Scene.collection_manager

    # remove keymaps when add-on is deactivated
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


if __name__ == "__main__":
    register()
