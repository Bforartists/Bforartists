# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Import Palettes",
    "author": "Antonio Vazquez, Kevin C. Burke (@blastframe)",
    "version": (1, 0, 1),
    "blender": (2, 81, 6),
    "location": "File > Import",
    "description": "Import Palettes",
    "warning": "",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/import_export/palettes.html",
    "category": "Import-Export",
}

import sys
import os

# ----------------------------------------------
# Add to Python path (once only)
# ----------------------------------------------
path = sys.path
flag = False
for item in path:
    if "io_import_palette" in item:
        flag = True
if flag is False:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'io_import_palette'))

# ----------------------------------------------
# Import modules
# ----------------------------------------------
if "bpy" in locals():
    import imp

    imp.reload(import_ase)
    imp.reload(import_krita)
else:
    import import_ase
    import import_krita

import bpy
from bpy.props import (
    StringProperty,
)
from bpy_extras.io_utils import (
    ImportHelper,
    path_reference_mode,
)


class ImportASE(bpy.types.Operator, ImportHelper):
    """Load a Palette File"""
    bl_idname = "import_ase.read"
    bl_label = "Import ASE"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".ase"
    filter_glob: StringProperty(
        default="*.ase",
        options={'HIDDEN'},
    )

    def execute(self, context):
        return import_ase.load(context, self.properties.filepath)

    def draw(self, context):
        pass


class importKPL(bpy.types.Operator, ImportHelper):
    """Load a File"""
    bl_idname = "import_krita.read"
    bl_label = "Import Palette"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".kpl"
    filter_glob: StringProperty(
        default="*.kpl;*gpl",
        options={'HIDDEN'},
    )

    def execute(self, context):
        return import_krita.load(context, self.properties.filepath)

    def draw(self, context):
        pass


def menu_func_import(self, context):
    self.layout.operator(importKPL.bl_idname, text="KPL Palette (.kpl)")
    self.layout.operator(ImportASE.bl_idname, text="ASE Palette (.ase)")


classes = (
    ImportASE,
    importKPL,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
