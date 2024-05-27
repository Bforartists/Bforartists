# SPDX-FileCopyrightText: 2016-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later


bl_info = {
    "name": "tinyCAD Mesh tools",
    "author": "zeffii (aka Dealga McArdle)",
    "version": (1, 3, 2),
    "blender": (2, 80, 0),
    "location": "View3D > EditMode Context Menu",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/mesh/tinycad.html",
    "tracker_url": "https://github.com/zeffii/mesh_tiny_cad/issues",
    "category": "Mesh",
}


if "bpy" in locals():
    if 'VTX' in locals():

        print('tinyCAD: detected reload event.')
        import importlib

        try:
            modules = (CFG, VTX, V2X, XALL, BIX, CCEN, E2F)
            for m in modules:
                importlib.reload(m)
            print("tinyCAD: reloaded modules, all systems operational")

        except Exception as E:
            print('reload failed with error:')
            print(E)


import bpy

from .CFG import TinyCADProperties, VIEW3D_MT_edit_mesh_tinycad
from .CFG import register_icons, unregister_icons
from . import VTX, V2X, XALL, BIX, CCEN, E2F


def menu_func(self, context):
    self.layout.menu("VIEW3D_MT_edit_mesh_tinycad")
    self.layout.separator()

classes = [
    TinyCADProperties, VIEW3D_MT_edit_mesh_tinycad,
    VTX.TCAutoVTX,
    XALL.TCIntersectAllEdges,
    V2X.TCVert2Intersection,
    E2F.TCEdgeToFace,
    CCEN.TCCallBackCCEN, CCEN.TCCircleCenter,
    BIX.TCLineOnBisection
]

def register():
    register_icons()
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.tinycad_props = bpy.props.PointerProperty(
        name="TinyCAD props", type=TinyCADProperties)
    bpy.types.VIEW3D_MT_edit_mesh_context_menu.prepend(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_edit_mesh_context_menu.remove(menu_func)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.tinycad_props
    unregister_icons()
