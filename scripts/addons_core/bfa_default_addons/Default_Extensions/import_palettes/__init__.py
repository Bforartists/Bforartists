# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

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
    import importlib

    importlib.reload(import_ase)
    importlib.reload(import_krita)
else:
    from . import import_ase
    from . import import_krita
    from . import import_jascpal

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

class ImportJASCPAL(bpy.types.Operator, ImportHelper):
    """Load a JASC Palette File"""
    bl_idname = "import_jascpal.read"
    bl_label = "Import Palette"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".pal"
    filter_glob: StringProperty(
        default="*.pal",
        options={'HIDDEN'},
    )

    def execute(self, context):
        return import_jascpal.load(context, self.properties.filepath)

    def draw(self, context):
        pass

def menu_func_import(self, context):
    self.layout.operator(importKPL.bl_idname, text="KPL Palette (.kpl)")
    self.layout.operator(ImportASE.bl_idname, text="ASE Palette (.ase)")
    self.layout.operator(ImportJASCPAL.bl_idname, text="JASC/Gale Palette (.pal)")


classes = (
    ImportASE,
    importKPL,
    ImportJASCPAL,
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
