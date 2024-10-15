# SPDX-FileCopyrightText: 2016-2024 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from .hotkeys import register_hotkey


def register():
    context = bpy.context
    kc_active = context.window_manager.keyconfigs.active

    prefs = kc_active.preferences
    if prefs and hasattr(prefs, 'spacebar_action'):
        # This is a rough way to check if user is on the default "Blender"
        # keymap preset, so they actually have preferences.
        # In this case, we don't need to give them the built-in pie menus,
        # they can configure it themselves thorugh said preferences.
        return

    print("Extra Pies: Register built-in pies for use with non-standard Keymap.")

    # Mode Pie with "Tab for Pie Menu" disabled because it would conflict with Search on Industry Compatible.
    # So, it's on Ctrl+Tab.
    register_hotkey(
        'view3d.object_mode_pie_or_toggle',
        hotkey_kwargs={'type': 'TAB', 'value': 'PRESS', 'ctrl': True},
        key_cat='Object Non-modal',
    )

    # Shading Pie with "Extra Shading Pie Menu Items" enabled but "Pie Menu on Drag" disabled.
    register_hotkey(
        'wm.call_menu_pie',
        op_kwargs={'name': 'VIEW3D_MT_shading_ex_pie'},
        hotkey_kwargs={'type': 'Z', 'value': 'PRESS'},
        key_cat='3D View',
    )

    # View Pie with "Pie Menu on Drag" replicated.
    register_hotkey(
        'wm.call_menu_pie',
        op_kwargs={
            'name': 'VIEW3D_MT_view_pie',
        },
        hotkey_kwargs={'type': 'ACCENT_GRAVE', 'value': 'CLICK_DRAG'},
        key_cat='3D View',
    )
    register_hotkey(
        'view3d.navigate',
        hotkey_kwargs={'type': 'ACCENT_GRAVE', 'value': 'CLICK'},
        key_cat='3D View',
    )

    # Region Toggle Pie with "Pie Menu on Drag"-type functionality,
    # so that if tapped, it toggles the sidebar, but if held and dragged,
    # summons this pie menu.
    # Note that in 4.2, this is actually only a built-in pie with Developer Extras,
    # for some reason.
    register_hotkey(
        'wm.call_menu_pie_drag_only',
        op_kwargs={
            'name': 'WM_MT_region_toggle_pie',
            'fallback_operator': 'wm.context_toggle',
            'op_kwargs': '{"data_path":"space_data.show_region_ui"}',
        },
        hotkey_kwargs={'type': 'N', 'value': 'PRESS'},
        key_cat='3D View Generic',
    )
