import os
import bpy
import bpy.utils.previews
from bpy.app.handlers import persistent

from . import internals
from . import preferences
from . import qcd_move_widget
from . import qcd_operators
from . import ui

addon_qcd_keymaps = []
addon_qcd_view_hotkey_keymaps = []
addon_qcd_view_edit_mode_hotkey_keymaps = []


qcd_classes = (
    qcd_move_widget.QCDMoveWidget,
    qcd_operators.MoveToQCDSlot,
    qcd_operators.ViewQCDSlot,
    qcd_operators.ViewMoveQCDSlot,
    qcd_operators.RenumerateQCDSlots,
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
    km = wm.keyconfigs.addon.keymaps.new(name='Object Mode')
    kmi = km.keymap_items.new('view3d.qcd_move_widget', 'V', 'PRESS')
    addon_qcd_keymaps.append((km, kmi))

    bpy.app.handlers.save_pre.append(save_internal_data)
    bpy.app.handlers.load_post.append(load_internal_data)

    prefs = bpy.context.preferences.addons[__package__].preferences

    if prefs.enable_qcd_view_hotkeys:
        register_qcd_view_hotkeys()

    if prefs.enable_qcd_view_edit_mode_hotkeys:
        register_qcd_view_edit_mode_hotkeys()

    bpy.types.VIEW3D_HT_header.append(ui.view3d_header_qcd_slots)
    bpy.types.TOPBAR_HT_upper_bar.append(ui.view_layer_update)


def register_qcd_view_hotkeys():
    wm = bpy.context.window_manager
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


def register_qcd_view_edit_mode_hotkeys():
    wm = bpy.context.window_manager
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
