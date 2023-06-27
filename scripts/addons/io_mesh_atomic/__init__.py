# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

#  Author            : Clemens Barth (Blendphys@root-1.de)
#  Homepage(Wiki)    : https://docs.blender.org/manual/en/dev/addons/import_export/mesh_atomic.html
#
#  Start of project                  : 2011-08-31 by CB
#  First publication in Blender      : 2011-11-11 by CB
#  Fusion of the PDB, XYZ and Panel  : 2019-03-22 by CB
#  Last modified                     : 2023-05-19
#
#  Contributing authors
#  ====================
#
#  So far ... none ... .
#
#
#  Acknowledgements
#  ================
#
#  A big thank you to all those people who I met in particular in the IRC and
#  who helped me a lot.
#
#  Blender developers
#  ------------------
#  Campbell Barton      (ideasman)
#  Brendon Murphy       (meta_androcto)
#  Truman Melton (?)    (truman)
#  Kilon Alios          (kilon)
#  ??                   (CoDEmanX)
#  Dima Glib            (dairin0d)
#  Peter K.H. Gragert   (PKHG)
#  Valter Battioli (?)  (valter)
#  ?                    (atmind)
#  Ray Molenkamp        (bzztploink)
#
#  Other
#  -----
#  Frank Palmino (Femto-St institute, Belfort-Montbéliard, France)
#  ... for testing the addons and for feedback

bl_info = {
    "name": "Atomic Blender PDB/XYZ",
    "description": "Importing atoms listed in PDB or XYZ files as balls into Blender",
    "author": "Clemens Barth",
    "version": (1, 8, 1),
    "blender": (2, 80, 0),
    "location": "File -> Import -> PDB (.pdb) and File -> Import -> XYZ (.xyz)",
    "warning": "",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/import_export/mesh_atomic.html",
    "category": "Import-Export",
}

import bpy
from bpy.types import Operator, AddonPreferences
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.props import (
        StringProperty,
        BoolProperty,
        EnumProperty,
        IntProperty,
        FloatProperty,
        )

from . import (
        pdb_gui,
        xyz_gui,
        utility_gui,
        utility_panel
        )

# -----------------------------------------------------------------------------
#                                                                   Preferences

class AddonPreferences(AddonPreferences):
    # This must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    bool_pdb : BoolProperty(
               name="PDB import/export",
               default=True,
               description="Import/export PDB",
               )
    bool_xyz : BoolProperty(
               name="XYZ import/export",
               default=True,
               description="Import/export XYZ",
               )
    # This boolean is checked in the poll function in PANEL_PT_prepare
    # (see utility.py).
    bool_utility : BoolProperty(
                   name="Utility panel",
                   default=False,
                   description=("Panel with functionalities for modifying " \
                                "atomic structures"),
                   )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Choose the importer(s) and a 'utility' panel")
        layout.prop(self, "bool_pdb")
        layout.prop(self, "bool_xyz")
        layout.prop(self, "bool_utility")


# -----------------------------------------------------------------------------
#                                                                          Menu


# The entry into the menu 'file -> import'
def menu_func_import_pdb(self, context):
    lay = self.layout
    lay.operator(pdb_gui.IMPORT_OT_pdb.bl_idname,text="Protein Data Bank (.pdb)")

def menu_func_import_xyz(self, context):
    lay = self.layout
    lay.operator(xyz_gui.IMPORT_OT_xyz.bl_idname,text="XYZ (.xyz)")

# The entry into the menu 'file -> export'
def menu_func_export_pdb(self, context):
    lay = self.layout
    lay.operator(pdb_gui.EXPORT_OT_pdb.bl_idname,text="Protein Data Bank (.pdb)")

def menu_func_export_xyz(self, context):
    lay = self.layout
    lay.operator(xyz_gui.EXPORT_OT_xyz.bl_idname,text="XYZ (.xyz)")


# -----------------------------------------------------------------------------
#                                                                      Register

def register():
    from bpy.utils import register_class

    register_class(AddonPreferences)

    register_class(pdb_gui.IMPORT_OT_pdb)
    register_class(pdb_gui.EXPORT_OT_pdb)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_pdb)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export_pdb)

    register_class(xyz_gui.IMPORT_OT_xyz)
    register_class(xyz_gui.EXPORT_OT_xyz)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_xyz)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export_xyz)

    classes = (utility_gui.PANEL_PT_prepare,
                utility_gui.PanelProperties,
                utility_gui.DatafileApply,
                utility_gui.DefaultAtom,
                utility_gui.ReplaceAtom,
                utility_gui.SeparateAtom,
                utility_gui.DistanceButton,
                utility_gui.RadiusAllBiggerButton,
                utility_gui.RadiusAllSmallerButton,
                utility_gui.SticksAllBiggerButton,
                utility_gui.SticksAllSmallerButton)
    from bpy.utils import register_class
    utility_panel.read_elements()
    for cls in classes:
        register_class(cls)

    scene = bpy.types.Scene
    scene.atom_blend = bpy.props.PointerProperty(type=utility_gui.PanelProperties)


def unregister():
    from bpy.utils import unregister_class

    unregister_class(AddonPreferences)

    unregister_class(pdb_gui.IMPORT_OT_pdb)
    unregister_class(pdb_gui.EXPORT_OT_pdb)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_pdb)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export_pdb)

    unregister_class(xyz_gui.IMPORT_OT_xyz)
    unregister_class(xyz_gui.EXPORT_OT_xyz)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_xyz)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export_xyz)

    classes = (utility_gui.PANEL_PT_prepare,
                utility_gui.PanelProperties,
                utility_gui.DatafileApply,
                utility_gui.DefaultAtom,
                utility_gui.ReplaceAtom,
                utility_gui.SeparateAtom,
                utility_gui.DistanceButton,
                utility_gui.RadiusAllBiggerButton,
                utility_gui.RadiusAllSmallerButton,
                utility_gui.SticksAllBiggerButton,
                utility_gui.SticksAllSmallerButton)
    for cls in classes:
        unregister_class(cls)


# -----------------------------------------------------------------------------
#                                                                          Main

if __name__ == "__main__":

    register()
