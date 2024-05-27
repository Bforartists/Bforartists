# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

# km_snap_utilities_modal_keymap = "Snap Utilities Modal Map"

km_tool_snap_utilities_line = "3D View Tool: Edit Mesh, Make Line"


def km_mesh_snap_utilities_operators():
    return (
        "Mesh",
        {"space_type": 'EMPTY', "region_type": 'WINDOW'},
        {"items": [
            ("mesh.snap_utilities_line", {"type": 'K', "value": 'PRESS'},
             {"properties": [("wait_for_input", True)],
              "active":False}),
        ]},
    )


"""
def km_snap_utilities_modal_map():
    items = []
    modal_enum = []
    keymap = (
        km_snap_utilities_modal_keymap,
        {"space_type": 'EMPTY', "region_type": 'WINDOW', "modal": True, "modal_enum": modal_enum},
        {"items": items},
    )

    modal_enum.extend([
        ("ADD_CUT", "ADD_CUT", ""),
        ("CANCEL", "CANCEL", ""),
        ("CONFIRM", "CONFIRM", ""),
        ("IGNORE_SNAP_ON", "IGNORE_SNAP_ON", ""),
        ("IGNORE_SNAP_OFF", "IGNORE_SNAP_OFF", ""),
    ])

    items.extend([
        ("ADD_CUT", {"type": 'LEFTMOUSE', "value": 'ANY', "any": True}, None),
        ("CANCEL", {"type": 'ESC', "value": 'PRESS', "any": True}, None),
        ("CANCEL", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK', "any": True}, None),
        ("CANCEL", {"type": 'RIGHTMOUSE', "value": 'PRESS', "any": True}, None),
        ("CONFIRM", {"type": 'RET', "value": 'PRESS', "any": True}, None),
        ("CONFIRM", {"type": 'NUMPAD_ENTER', "value": 'PRESS', "any": True}, None),
        ("CONFIRM", {"type": 'SPACE', "value": 'PRESS', "any": True}, None),
        ("IGNORE_SNAP_ON", {"type": 'LEFT_SHIFT', "value": 'PRESS', "any": True}, None),
        ("IGNORE_SNAP_OFF", {"type": 'LEFT_SHIFT', "value": 'RELEASE', "any": True}, None),
        ("IGNORE_SNAP_ON", {"type": 'RIGHT_SHIFT', "value": 'PRESS', "any": True}, None),
        ("IGNORE_SNAP_OFF", {"type": 'RIGHT_SHIFT', "value": 'RELEASE', "any": True}, None),
    ])

    return keymap
"""


def km_3d_view_tool_snap_utilities_line(tool_mouse):
    return (
        km_tool_snap_utilities_line,
        {"space_type": 'VIEW_3D', "region_type": 'WINDOW'},
        {"items": [
            ("mesh.snap_utilities_line", {"type": tool_mouse, "value": 'PRESS'},
             {"properties": [("wait_for_input", False)]}),
        ]},
    )


def km_view3d_empty(km_name):
    return (
        km_name,
        {"space_type": 'VIEW_3D', "region_type": 'WINDOW'},
        {"items": []},
    )

# ------------------------------------------------------------------------------
# Full Configuration


def generate_empty_snap_utilities_tools_keymaps():
    return [
        # km_view3d_empty(km_snap_utilities_modal_keymap),

        km_view3d_empty(km_tool_snap_utilities_line),
    ]


def generate_snap_utilities_global_keymaps(tool_mouse='LEFTMOUSE'):
    return [
        km_mesh_snap_utilities_operators(),
    ]


def generate_snap_utilities_tools_keymaps(tool_mouse='LEFTMOUSE'):
    return [
        # Tool System.
        km_3d_view_tool_snap_utilities_line(tool_mouse),
    ]


def generate_snap_utilities_keymaps(tool_mouse='LEFTMOUSE'):
    return [
        km_mesh_snap_utilities_operators(),

        # Modal maps.
        # km_snap_utilities_modal_map(),

        # Tool System.
        km_3d_view_tool_snap_utilities_line(tool_mouse),
    ]
