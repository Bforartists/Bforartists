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

bl_info = {
    "name": "HiRISE DTM from PDS IMG",
    "author": "Tim Spriggs (tims@uahirise.org)",
    "version": (0, 1, 4),
    "blender": (2, 63, 0),
    "location": "File > Import > HiRISE DTM from PDS IMG (.IMG)",
    "description": "Import a HiRISE DTM formatted as a PDS IMG file",
    "warning": "May consume a lot of memory",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/Import-Export/HiRISE_DTM_from_PDS_IMG",
    "category": "Import-Export",
}


# Revision History:
# 0.1.1 - make default import 12x12 bin (fast) to not consume too much memory
#         by default (TJS - 2010-12-07)
# 0.1.2 - included into svn under the tree:
#         trunk/py/scripts/addons/io_convert_image_to_mesh_img
#         may be moved out to contrib once the blender downloader works well
#         (TJS - 2010-12-14)
# 0.1.3 - upstream blender updates
#         performance enhancements by Chris Van Horne
#         (TJS - 2012-03-14)
# 0.1.4 - use bmesh from_pydata in blender 2.6.3
#         fixed/optimized bin2 method
#         (TJS - 2012-04-30)


if "bpy" in locals():
    import importlib
    importlib.reload(import_img)
else:
    from . import import_img


import bpy
from bpy.props import *
from bpy_extras.io_utils import ImportHelper


class ImportHiRISEIMGDTM(bpy.types.Operator, ImportHelper):
    """Import a HiRISE DTM formatted as a PDS IMG file"""
    bl_idname = "import_shape.img"
    bl_label  = "Import HiRISE DTM from PDS IMG"
    bl_options = {'UNDO'}

    filename_ext = ".IMG"
    filter_glob = StringProperty(default="*.IMG", options={'HIDDEN'})

    scale = FloatProperty(name="Scale",
                          description="Scale the IMG by this value",
                          min=0.0001,
                          max=10.0,
                          soft_min=0.001,
                          soft_max=100.0,
                          default=0.01)

    bin_mode = EnumProperty(items=(
                                   ('NONE', "None", "Don't bin the image"),
                                   ('BIN2', "2x2", "use 2x2 binning to import the mesh"),
                                   ('BIN6', "6x6", "use 6x6 binning to import the mesh"),
                                   ('BIN6-FAST', "6x6 Fast", "use one sample per 6x6 region"),
                                   ('BIN12', "12x12", "use 12x12 binning to import the mesh"),
                                   ('BIN12-FAST', "12x12 Fast", "use one sample per 12x12 region"),
                                  ),
                            name="Binning",
                            description="Import Binning",
                            default='BIN12-FAST'
                            )

    ## TODO: add support for cropping on import when the checkbox is checked
    # do_crop = BoolProperty(name="Crop Image", description="Crop the image during import", ... )
    ## we only want these visible when the above is "true"
    # crop_x = IntProperty(name="X", description="Offset from left side of image")
    # crop_y = IntProperty(name="Y", description="Offset from top of image")
    # crop_w = IntProperty(name="Width", description="width of cropped operation")
    # crop_h = IntProperty(name="Height", description="height of cropped region")
    ## This is also a bit ugly and maybe an anti-pattern. The problem is that
    ## importing a HiRISE DTM at full resolution will likely kill any mortal user with
    ## less than 16 GB RAM and getting at specific features in a DTM at full res
    ## may prove beneficial. Someday most mortals will have 16GB RAM.
    ## -TJS 2010-11-23

    def execute(self, context):
      filepath = self.filepath
      filepath = bpy.path.ensure_ext(filepath, self.filename_ext)

      return import_img.load(self, context,
                             filepath=self.filepath,
                             scale=self.scale,
                             bin_mode=self.bin_mode,
                             cropVars=False,
                             )

## How to register the script inside of Blender

def menu_import(self, context):
    self.layout.operator(ImportHiRISEIMGDTM.bl_idname, text="HiRISE DTM from PDS IMG (*.IMG)")

def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_import.append(menu_import)

def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_import.remove(menu_import)

if __name__ == "__main__":
    register()
