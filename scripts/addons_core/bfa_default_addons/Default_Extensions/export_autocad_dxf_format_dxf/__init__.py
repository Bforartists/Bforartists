# SPDX-FileCopyrightText: 2012-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

if "bpy" in locals():
    from importlib import reload
    reload(operator)
    del reload

import bpy
from . import operator

def menu_func(self, context):
    self.layout.operator(operator.DXFExporter.bl_idname, text="AutoCAD DXF (.dxf)")

classes = (
    operator.DXFExporter,
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.TOPBAR_MT_file_export.append(menu_func)


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func)

if __name__ == "__main__":
    register()
