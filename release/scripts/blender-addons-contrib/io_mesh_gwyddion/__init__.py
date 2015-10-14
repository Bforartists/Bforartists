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

#
#
#  Authors           : Clemens Barth (Blendphys@root-1.de), ...
#
#  Homepage          : http://development.root-1.de/Atomic_Blender.php
#
#  Start of project              : 2012-11-12 by Clemens Barth
#  First publication in Blender  : 2012-11-19
#  Last modified                 : 2012-11-19
#
#  Acknowledgements
#  ================
#
#  Other: Frank Palmino
#

bl_info = {
    "name": "Atomic Blender - Gwyddion",
    "description": "Loading Gwyddion Atomic Force Microscopy images",
    "author": "Clemens Barth",
    "version": (0, 1),
    "blender": (2, 60, 0),
    "location": "File > Import > Gwyddion (.gwy)",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
        "Scripts/Import-Export/Gwyddion",
    "tracker_url": "https://developer.blender.org/T33236",
    "category": "Import-Export"}


import bpy
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper
from bpy.props import (BoolProperty,
                       StringProperty,
                       EnumProperty,
                       FloatProperty)

from . import import_gwyddion

# -----------------------------------------------------------------------------
#                                                                           GUI

# This is the class for the file dialog of the importer.
class ImportGwyddion(Operator, ImportHelper):
    bl_idname = "import_mesh.gwy"
    bl_label  = "Import Gwyddion (*.gwy)"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".gwy"
    filter_glob  = StringProperty(default="*.gwy", options={'HIDDEN'},)

    use_camera = BoolProperty(
        name="Camera", default=False,
        description="Do you need a camera?")
    use_lamp = BoolProperty(
        name="Lamp", default=False,
        description = "Do you need a lamp?")
    use_smooth = BoolProperty(
        name="Smooth image data", default=False,
        description = "Smooth the images")
    scale_size = FloatProperty (
        name = "Scale xy", default=0.5,
        description = "Scale the lateral size")
    scale_height = FloatProperty (
        name = "Scale h", default=3.0,
        description = "Scale the height")
    use_all_channels = BoolProperty(
        name="All channels", default=False,
        description = "Load all images")
    use_c1 = BoolProperty(
        name="1", default=True,
        description = "Channel 1")
    use_c2 = BoolProperty(
        name="2", default=False,
        description = "Channel 2")
    use_c3 = BoolProperty(
        name="3", default=False,
        description = "Channel 3")
    use_c4 = BoolProperty(
        name="4", default=False,
        description = "Channel 4")
    use_c5 = BoolProperty(
        name="5", default=False,
        description = "Channel 5")
    use_c6 = BoolProperty(
        name="6", default=False,
        description = "Channel 6")
    use_c7 = BoolProperty(
        name="7", default=False,
        description = "Channel 7")
    use_c8 = BoolProperty(
        name="8", default=False,
        description = "Channel 8")

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, "use_camera")
        row.prop(self, "use_lamp")
        row = layout.row()
        row.prop(self, "use_smooth")
        row = layout.row()
        row.prop(self, "scale_size")
        row.prop(self, "scale_height")
        row = layout.row()
        row.label(text="Channels")
        row.prop(self, "use_all_channels")
        row = layout.row()
        row.prop(self, "use_c1")
        row.prop(self, "use_c2")
        row.prop(self, "use_c3")
        row.prop(self, "use_c4")
        row = layout.row()
        row.prop(self, "use_c5")
        row.prop(self, "use_c6")
        row.prop(self, "use_c7")
        row.prop(self, "use_c8")

        if self.use_all_channels:
            self.use_c1, self.use_c2, self.use_c3, self.use_c4, \
            self.use_c5, self.use_c6, self.use_c7, self.use_c8  \
            = True, True, True, True, True, True, True, True

    def execute(self, context):
        # This is in order to solve this strange 'relative path' thing.
        filepath_par = bpy.path.abspath(self.filepath)

        channels = [self.use_c1, self.use_c2, self.use_c3, self.use_c4,
                    self.use_c5, self.use_c6, self.use_c7, self.use_c8]

        # Execute main routine
        #print("passed - 1")
        images, AFMdata = import_gwyddion.load_gwyddion_images(filepath_par,
                                                               channels)

        #print("passed - 3")
        import_gwyddion.create_mesh(images,
                                 AFMdata,
                                 self.use_smooth,
                                 self.scale_size,
                                 self.scale_height,
                                 self.use_camera,
                                 self.use_lamp)
        #print("passed - 4")

        return {'FINISHED'}


# The entry into the menu 'file -> import'
def menu_func_import(self, context):
    self.layout.operator(ImportGwyddion.bl_idname, text="Gwyddion (.gwy)")


def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":

    register()
