# SPDX-FileCopyrightText: 2016-2024 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Menu
from .hotkeys import register_hotkey


class PIE_MT_mesh_delete(Menu):
    bl_idname = "PIE_MT_mesh_delete"
    bl_label = "Mesh Delete"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        box = pie.split().column()
        box.operator(
            "mesh.dissolve_limited", text="Limited Dissolve", icon='STICKY_UVS_LOC'
        )
        box.operator("mesh.delete_edgeloop", text="Delete Edge Loops", icon='NONE')
        box.operator("mesh.edge_collapse", text="Edge Collapse", icon='UV_EDGESEL')
        # 6 - RIGHT
        box = pie.split().column()
        box.operator("mesh.remove_doubles", text="Merge By Distance", icon='NONE')
        box.operator("mesh.delete", text="Only Edge & Faces", icon='NONE').type = (
            'EDGE_FACE'
        )
        box.operator("mesh.delete", text="Only Faces", icon='UV_FACESEL').type = (
            'ONLY_FACE'
        )
        # 2 - BOTTOM
        pie.operator("mesh.dissolve_edges", text="Dissolve Edges", icon='SNAP_EDGE')
        # 8 - TOP
        pie.operator("mesh.delete", text="Delete Edges", icon='EDGESEL').type = 'EDGE'
        # 7 - TOP - LEFT
        pie.operator("mesh.delete", text="Delete Vertices", icon='VERTEXSEL').type = (
            'VERT'
        )
        # 9 - TOP - RIGHT
        pie.operator("mesh.delete", text="Delete Faces", icon='FACESEL').type = 'FACE'
        # 1 - BOTTOM - LEFT
        pie.operator(
            "mesh.dissolve_verts", text="Dissolve Vertices", icon='SNAP_VERTEX'
        )
        # 3 - BOTTOM - RIGHT
        pie.operator("mesh.dissolve_faces", text="Dissolve Faces", icon='SNAP_FACE')


registry = [
    PIE_MT_mesh_delete,
]


def register():
    register_hotkey(
        'wm.call_menu_pie',
        op_kwargs={'name': 'PIE_MT_mesh_delete'},
        hotkey_kwargs={'type': "X", 'value': "PRESS"},
        key_cat="Mesh",
    )
