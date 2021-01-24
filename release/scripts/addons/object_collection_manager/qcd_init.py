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

if "bpy" in locals():
    import importlib

    importlib.reload(internals)
    importlib.reload(qcd_move_widget)
    importlib.reload(qcd_operators)
    importlib.reload(ui)
    importlib.reload(preferences)

else:
    from . import internals
    from . import qcd_move_widget
    from . import qcd_operators
    from . import ui
    from . import preferences

import os
import bpy
import bpy.utils.previews
from bpy.app.handlers import persistent


addon_qcd_keymaps = []
addon_qcd_view_hotkey_keymaps = []
addon_qcd_view_edit_mode_hotkey_keymaps = []


qcd_classes = (
    qcd_move_widget.QCDMoveWidget,
    qcd_operators.EnableAllQCDSlotsMeta,
    qcd_operators.EnableAllQCDSlots,
    qcd_operators.EnableAllQCDSlotsIsolated,
    qcd_operators.IsolateSelectedObjectsCollections,
    qcd_operators.DisableSelectedObjectsCollections,
    qcd_operators.DisableAllNonQCDSlots,
    qcd_operators.DisableAllCollections,
    qcd_operators.SelectAllQCDObjects,
    qcd_operators.DiscardQCDHistory,
    qcd_operators.MoveToQCDSlot,
    qcd_operators.ViewQCDSlot,
    qcd_operators.ViewMoveQCDSlot,
    qcd_operators.RenumerateQCDSlots,
    ui.EnableAllQCDSlotsMenu,
    )


@persistent
def save_internal_data(dummy):
    cm = bpy.context.scene.collection_manager

    cm.qcd_slots_blend_data = internals.qcd_slots.get_data_for_blend()


@persistent
def load_internal_data(dummy):
    cm = bpy.context.scene.collection_manager
    data = cm.qcd_slots_blend_data

    if not data:
        return

    internals.qcd_slots.load_blend_data(data)


@persistent
def load_pre_handler(dummy):
    internals.qcd_collection_state.clear()
    for key in list(internals.qcd_history.keys()):
        del internals.qcd_history[key]


def register_qcd():
    for cls in qcd_classes:
        bpy.utils.register_class(cls)

    pcoll = bpy.utils.previews.new()
    icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    pcoll.load("active_icon_base", os.path.join(icons_dir, "minus.png"), 'IMAGE', True)
    pcoll.load("active_icon_text", os.path.join(icons_dir, "minus.png"), 'IMAGE', True)
    pcoll.load("active_icon_text_sel", os.path.join(icons_dir, "minus.png"), 'IMAGE', True)
    ui.preview_collections["icons"] = pcoll

    wm = bpy.context.window_manager
    if wm.keyconfigs.addon: # not present when started with --background
        km = wm.keyconfigs.addon.keymaps.new(name='Object Mode')
        kmi = km.keymap_items.new('view3d.qcd_move_widget', 'V', 'PRESS')
        addon_qcd_keymaps.append((km, kmi))

    bpy.app.handlers.save_pre.append(save_internal_data)
    bpy.app.handlers.load_post.append(load_internal_data)
    bpy.app.handlers.load_pre.append(load_pre_handler)

    prefs = bpy.context.preferences.addons[__package__].preferences

    if prefs.enable_qcd_view_hotkeys:
        register_qcd_view_hotkeys()

    if prefs.enable_qcd_view_edit_mode_hotkeys:
        register_qcd_view_edit_mode_hotkeys()

    bpy.types.VIEW3D_HT_header.append(ui.view3d_header_qcd_slots)
    bpy.types.TOPBAR_HT_upper_bar.append(ui.view_layer_update)


def register_qcd_view_hotkeys():
    wm = bpy.context.window_manager
    if wm.keyconfigs.addon: # not present when started with --background
        # create qcd hotkeys
        qcd_hotkeys = [
            ["ONE", False, "1"],
            ["TWO", False, "2"],
            ["THREE", False, "3"],
            ["FOUR", False, "4"],
            ["FIVE", False, "5"],
            ["SIX", False, "6"],
            ["SEVEN", False, "7"],
            ["EIGHT", False, "8"],
            ["NINE", False, "9"],
            ["ZERO", False, "10"],
            ["ONE", True, "11"],
            ["TWO", True, "12"],
            ["THREE", True, "13"],
            ["FOUR", True, "14"],
            ["FIVE", True, "15"],
            ["SIX", True, "16"],
            ["SEVEN", True, "17"],
            ["EIGHT", True, "18"],
            ["NINE", True, "19"],
            ["ZERO", True, "20"],
        ]

        for key in qcd_hotkeys:
            for mode in ['Object Mode', 'Pose', 'Weight Paint']:
                km = wm.keyconfigs.addon.keymaps.new(name=mode)
                kmi = km.keymap_items.new('view3d.view_qcd_slot', key[0], 'PRESS', alt=key[1])
                kmi.properties.slot = key[2]
                kmi.properties.toggle = False
                addon_qcd_view_hotkey_keymaps.append((km, kmi))

                km = wm.keyconfigs.addon.keymaps.new(name=mode)
                kmi = km.keymap_items.new('view3d.view_qcd_slot', key[0], 'PRESS',shift=True,  alt=key[1])
                kmi.properties.slot = key[2]
                kmi.properties.toggle = True
                addon_qcd_view_hotkey_keymaps.append((km, kmi))

                km = wm.keyconfigs.addon.keymaps.new(name=mode)
                kmi = km.keymap_items.new('view3d.enable_all_qcd_slots', 'PLUS', 'PRESS', shift=True)
                addon_qcd_view_hotkey_keymaps.append((km, kmi))

                km = wm.keyconfigs.addon.keymaps.new(name=mode)
                kmi = km.keymap_items.new('view3d.isolate_selected_objects_collections', 'EQUAL', 'PRESS')
                addon_qcd_view_hotkey_keymaps.append((km, kmi))

                km = wm.keyconfigs.addon.keymaps.new(name=mode)
                kmi = km.keymap_items.new('view3d.disable_selected_objects_collections', 'MINUS', 'PRESS')
                addon_qcd_view_hotkey_keymaps.append((km, kmi))

                km = wm.keyconfigs.addon.keymaps.new(name=mode)
                kmi = km.keymap_items.new('view3d.disable_all_non_qcd_slots', 'PLUS', 'PRESS', shift=True, alt=True)
                addon_qcd_view_hotkey_keymaps.append((km, kmi))

                km = wm.keyconfigs.addon.keymaps.new(name=mode)
                kmi = km.keymap_items.new('view3d.disable_all_collections', 'EQUAL', 'PRESS', alt=True, ctrl=True)
                addon_qcd_view_hotkey_keymaps.append((km, kmi))

                km = wm.keyconfigs.addon.keymaps.new(name=mode)
                kmi = km.keymap_items.new('view3d.select_all_qcd_objects', 'PLUS', 'PRESS', shift=True, ctrl=True)
                addon_qcd_view_hotkey_keymaps.append((km, kmi))


                km = wm.keyconfigs.addon.keymaps.new(name=mode)
                kmi = km.keymap_items.new('view3d.discard_qcd_history', 'EQUAL', 'PRESS', alt=True)
                addon_qcd_view_hotkey_keymaps.append((km, kmi))


def register_qcd_view_edit_mode_hotkeys():
    wm = bpy.context.window_manager
    if wm.keyconfigs.addon: # not present when started with --background
        # create qcd hotkeys
        qcd_hotkeys = [
            ["ONE", False, "1"],
            ["TWO", False, "2"],
            ["THREE", False, "3"],
            ["FOUR", False, "4"],
            ["FIVE", False, "5"],
            ["SIX", False, "6"],
            ["SEVEN", False, "7"],
            ["EIGHT", False, "8"],
            ["NINE", False, "9"],
            ["ZERO", False, "10"],
            ["ONE", True, "11"],
            ["TWO", True, "12"],
            ["THREE", True, "13"],
            ["FOUR", True, "14"],
            ["FIVE", True, "15"],
            ["SIX", True, "16"],
            ["SEVEN", True, "17"],
            ["EIGHT", True, "18"],
            ["NINE", True, "19"],
            ["ZERO", True, "20"],
        ]

        for mode in ["Mesh", "Curve", "Armature", "Metaball", "Lattice", "Grease Pencil Stroke Edit Mode"]:
            for key in qcd_hotkeys:
                km = wm.keyconfigs.addon.keymaps.new(name=mode)
                kmi = km.keymap_items.new('view3d.view_qcd_slot', key[0], 'PRESS', alt=key[1])
                kmi.properties.slot = key[2]
                kmi.properties.toggle = False
                addon_qcd_view_edit_mode_hotkey_keymaps.append((km, kmi))

                km = wm.keyconfigs.addon.keymaps.new(name=mode)
                kmi = km.keymap_items.new('view3d.view_qcd_slot', key[0], 'PRESS',shift=True,  alt=key[1])
                kmi.properties.slot = key[2]
                kmi.properties.toggle = True
                addon_qcd_view_edit_mode_hotkey_keymaps.append((km, kmi))

            km = wm.keyconfigs.addon.keymaps.new(name=mode)
            kmi = km.keymap_items.new('view3d.enable_all_qcd_slots', 'PLUS', 'PRESS', shift=True)
            addon_qcd_view_edit_mode_hotkey_keymaps.append((km, kmi))

            km = wm.keyconfigs.addon.keymaps.new(name=mode)
            kmi = km.keymap_items.new('view3d.isolate_selected_objects_collections', 'EQUAL', 'PRESS')
            addon_qcd_view_edit_mode_hotkey_keymaps.append((km, kmi))

            km = wm.keyconfigs.addon.keymaps.new(name=mode)
            kmi = km.keymap_items.new('view3d.disable_all_non_qcd_slots', 'PLUS', 'PRESS', shift=True, alt=True)
            addon_qcd_view_edit_mode_hotkey_keymaps.append((km, kmi))

            km = wm.keyconfigs.addon.keymaps.new(name=mode)
            kmi = km.keymap_items.new('view3d.disable_all_collections', 'EQUAL', 'PRESS', alt=True, ctrl=True)
            addon_qcd_view_edit_mode_hotkey_keymaps.append((km, kmi))

            km = wm.keyconfigs.addon.keymaps.new(name=mode)
            kmi = km.keymap_items.new('view3d.discard_qcd_history', 'EQUAL', 'PRESS', alt=True)
            addon_qcd_view_edit_mode_hotkey_keymaps.append((km, kmi))


        km = wm.keyconfigs.addon.keymaps.new(name="Mesh")
        kmi = km.keymap_items.new('wm.call_menu', 'ACCENT_GRAVE', 'PRESS')
        kmi.properties.name = "VIEW3D_MT_edit_mesh_select_mode"
        addon_qcd_view_edit_mode_hotkey_keymaps.append((km, kmi))



def unregister_qcd():
    bpy.types.VIEW3D_HT_header.remove(ui.view3d_header_qcd_slots)
    bpy.types.TOPBAR_HT_upper_bar.remove(ui.view_layer_update)

    for cls in qcd_classes:
        bpy.utils.unregister_class(cls)

    bpy.app.handlers.save_pre.remove(save_internal_data)
    bpy.app.handlers.load_post.remove(load_internal_data)
    bpy.app.handlers.load_pre.remove(load_pre_handler)

    for pcoll in ui.preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    ui.preview_collections.clear()
    ui.last_icon_theme_text = None
    ui.last_icon_theme_text_sel = None

    # remove keymaps when qcd is deactivated
    for km, kmi in addon_qcd_keymaps:
        km.keymap_items.remove(kmi)
    addon_qcd_keymaps.clear()


    unregister_qcd_view_hotkeys()

    unregister_qcd_view_edit_mode_hotkeys()


def unregister_qcd_view_hotkeys():
    # remove keymaps when qcd view hotkeys are deactivated
    for km, kmi in addon_qcd_view_hotkey_keymaps:
        km.keymap_items.remove(kmi)
    addon_qcd_view_hotkey_keymaps.clear()


def unregister_qcd_view_edit_mode_hotkeys():
    # remove keymaps when qcd view hotkeys are deactivated
    for km, kmi in addon_qcd_view_edit_mode_hotkey_keymaps:
        km.keymap_items.remove(kmi)
    addon_qcd_view_edit_mode_hotkey_keymaps.clear()
