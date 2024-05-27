# SPDX-FileCopyrightText: 2011 Ryan Inch
#
# SPDX-License-Identifier: GPL-2.0-or-later

if "bpy" in locals():
    import importlib

    importlib.reload(internals)
    importlib.reload(operator_utils)
    importlib.reload(operators)
    importlib.reload(ui)
    importlib.reload(preferences)

else:
    from . import internals
    from . import operator_utils
    from . import operators
    from . import ui
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
addon_disable_objects_hotkey_keymaps = []

classes = (
    internals.CMListCollection,
    internals.CMSendReport,
    internals.CMUISeparatorButton,
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
    operators.SelectAllCumulativeObjectsOperator,
    operators.CMSendObjectsToCollectionOperator,
    operators.CMPhantomModeOperator,
    operators.CMApplyPhantomModeOperator,
    operators.CMDisableObjectsOperator,
    operators.CMDisableUnSelectedObjectsOperator,
    operators.CMRestoreDisabledObjectsOperator,
    operators.CMUndoWrapper,
    operators.CMRedoWrapper,
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


@persistent
def global_load_pre_handler(dummy):
    internals.move_triggered = False
    internals.move_selection.clear()
    internals.move_active = None


def menu_addition(self, context):
    layout = self.layout

    layout.operator('view3d.collection_manager')

    if bpy.context.preferences.addons[__package__].preferences.enable_qcd:
        layout.operator('view3d.qcd_move_widget')

    layout.separator()

def disable_objects_menu_addition(self, context):
    preferences = bpy.context.preferences.addons[__package__].preferences
    if preferences.enable_disable_objects_override:
        layout = self.layout
        layout.separator()
        layout.operator('view3d.disable_selected_objects')
        layout.operator('view3d.disable_unselected_objects')
        layout.operator('view3d.restore_disabled_objects')


def register_disable_objects_hotkeys():
    if addon_disable_objects_hotkey_keymaps:
        # guard to handle default value updates (mouse hover + backspace)
        return

    wm = bpy.context.window_manager
    if wm.keyconfigs.addon: # not present when started with --background
        km = wm.keyconfigs.addon.keymaps.new(name='Object Mode')
        kmi = km.keymap_items.new('view3d.disable_selected_objects', 'H', 'PRESS')
        addon_disable_objects_hotkey_keymaps.append((km, kmi))

        km = wm.keyconfigs.addon.keymaps.new(name='Object Mode')
        kmi = km.keymap_items.new('view3d.disable_unselected_objects', 'H', 'PRESS', shift=True)
        addon_disable_objects_hotkey_keymaps.append((km, kmi))

        km = wm.keyconfigs.addon.keymaps.new(name='Object Mode')
        kmi = km.keymap_items.new('view3d.restore_disabled_objects', 'H', 'PRESS', alt=True)
        addon_disable_objects_hotkey_keymaps.append((km, kmi))

def unregister_disable_objects_hotkeys():
    # remove keymaps when disable objects hotkeys are deactivated
    for km, kmi in addon_disable_objects_hotkey_keymaps:
        km.keymap_items.remove(kmi)
    addon_disable_objects_hotkey_keymaps.clear()


def register_cm():
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

    # Add Disable Object Operators to the Object->Show/Hide menu
    bpy.types.VIEW3D_MT_object_showhide.append(disable_objects_menu_addition)

    bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_post_handler)
    bpy.app.handlers.undo_post.append(undo_redo_post_handler)
    bpy.app.handlers.redo_post.append(undo_redo_post_handler)
    bpy.app.handlers.load_pre.append(global_load_pre_handler)

    preferences = bpy.context.preferences.addons[__package__].preferences
    if preferences.enable_disable_objects_override:
        register_disable_objects_hotkeys()

def unregister_cm():
    preferences = bpy.context.preferences.addons[__package__].preferences
    if preferences.enable_disable_objects_override:
        unregister_disable_objects_hotkeys()

    for cls in classes:
        bpy.utils.unregister_class(cls)

    # Remove Collection Manager & QCD Move Widget from the Object->Collections menu
    bpy.types.VIEW3D_MT_object_collection.remove(menu_addition)

    # Remove Disable Object Operators to the Object->Show/Hide menu
    bpy.types.VIEW3D_MT_object_showhide.remove(disable_objects_menu_addition)

    bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update_post_handler)
    bpy.app.handlers.undo_post.remove(undo_redo_post_handler)
    bpy.app.handlers.redo_post.remove(undo_redo_post_handler)
    bpy.app.handlers.load_pre.remove(global_load_pre_handler)

    del bpy.types.Scene.collection_manager

    # remove keymaps when add-on is deactivated
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
