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
#  Homepage(Wiki)    : http://development.root-1.de/Atomic_Blender.php
#
#  Start of project              : 2011-12-01 by Clemens Barth
#  First publication in Blender  : 2011-12-18
#  Last modified                 : 2014-08-19
#
#  Acknowledgements
#  ================
#
#  Blender: ideasman, meta_androcto, truman, kilon, CoDEmanX, dairin0d, PKHG,
#           Valter, ...
#  Other: Frank Palmino
#

bl_info = {
    "name": "Atomic Blender - XYZ",
    "description": "Import/export of atoms described in .xyz files",
    "author": "Clemens Barth",
    "version": (1, 0),
    "blender": (2, 71, 0),
    "location": "File -> Import -> XYZ (.xyz)",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
        "Scripts/Import-Export/XYZ",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "Import-Export"}


import bpy
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.props import (StringProperty,
                       BoolProperty,
                       EnumProperty,
                       IntProperty,
                       FloatProperty)

from . import import_xyz
from . import export_xyz

# -----------------------------------------------------------------------------
#                                                                           GUI


# This is the class for the file dialog.
class ImportXYZ(Operator, ImportHelper):
    bl_idname = "import_mesh.xyz"
    bl_label  = "Import XYZ (*.xyz)"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".xyz"
    filter_glob  = StringProperty(default="*.xyz", options={'HIDDEN'},)

    use_camera = BoolProperty(
        name="Camera", default=False,
        description="Do you need a camera?")
    use_lamp = BoolProperty(
        name="Lamp", default=False,
        description = "Do you need a lamp?")
    ball = EnumProperty(
        name="Type of ball",
        description="Choose ball",
        items=(('0', "NURBS", "NURBS balls"),
               ('1', "Mesh" , "Mesh balls"),
               ('2', "Meta" , "Metaballs")),
               default='0',)
    mesh_azimuth = IntProperty(
        name = "Azimuth", default=32, min=1,
        description = "Number of sectors (azimuth)")
    mesh_zenith = IntProperty(
        name = "Zenith", default=32, min=1,
        description = "Number of sectors (zenith)")
    scale_ballradius = FloatProperty(
        name = "Balls", default=1.0, min=0.0001,
        description = "Scale factor for all atom radii")
    scale_distances = FloatProperty (
        name = "Distances", default=1.0, min=0.0001,
        description = "Scale factor for all distances")
    atomradius = EnumProperty(
        name="Type of radius",
        description="Choose type of atom radius",
        items=(('0', "Pre-defined", "Use pre-defined radius"),
               ('1', "Atomic", "Use atomic radius"),
               ('2', "van der Waals", "Use van der Waals radius")),
               default='0',)
    use_center = BoolProperty(
        name = "Object to origin (first frames)", default=False,
        description = "Put the object into the global origin, the first frame only")
    use_center_all = BoolProperty(
        name = "Object to origin (all frames)", default=True,
        description = "Put the object into the global origin, all frames")
    datafile = StringProperty(
        name = "", description="Path to your custom data file",
        maxlen = 256, default = "", subtype='FILE_PATH')
    use_frames = BoolProperty(
        name = "Load all frames?", default=False,
        description = "Do you want to load all frames?")
    skip_frames = IntProperty(
        name="", default=0, min=0,
        description="Number of frames you want to skip.")
    images_per_key = IntProperty(
        name="", default=1, min=1,
        description="Choose the number of images between 2 keys.")

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, "use_camera")
        row.prop(self, "use_lamp")
        row = layout.row()
        col = row.column()
        col.prop(self, "ball")
        row = layout.row()
        row.active = (self.ball == "1")
        col = row.column(align=True)
        col.prop(self, "mesh_azimuth")
        col.prop(self, "mesh_zenith")
        row = layout.row()
        col = row.column()
        col.label(text="Scaling factors")
        col = row.column(align=True)
        col.prop(self, "scale_ballradius")
        col.prop(self, "scale_distances")
        row = layout.row()
        row.prop(self, "use_center")
        row = layout.row()
        row.prop(self, "use_center_all")
        row = layout.row()
        row.prop(self, "atomradius")

        row = layout.row()
        row.prop(self, "use_frames")
        row = layout.row()
        row.active = self.use_frames
        col = row.column()
        col.label(text="Skip frames")
        col = row.column()
        col.prop(self, "skip_frames")
        row = layout.row()
        row.active = self.use_frames
        col = row.column()
        col.label(text="Frames/key")
        col = row.column()
        col.prop(self, "images_per_key")

    def execute(self, context):

        del import_xyz.ALL_FRAMES[:]
        del import_xyz.ELEMENTS[:]
        del import_xyz.STRUCTURE[:]

        # This is to determine the path.
        filepath_xyz = bpy.path.abspath(self.filepath)

        # Execute main routine
        import_xyz.import_xyz(
                      self.ball,
                      self.mesh_azimuth,
                      self.mesh_zenith,
                      self.scale_ballradius,
                      self.atomradius,
                      self.scale_distances,
                      self.use_center,
                      self.use_center_all,
                      self.use_camera,
                      self.use_lamp,
                      filepath_xyz)

        # Load frames
        if len(import_xyz.ALL_FRAMES) > 1 and self.use_frames:

            import_xyz.build_frames(self.images_per_key,
                                    self.skip_frames)

        return {'FINISHED'}


# This is the class for the file dialog of the exporter.
class ExportXYZ(Operator, ExportHelper):
    bl_idname = "export_mesh.xyz"
    bl_label  = "Export XYZ (*.xyz)"
    filename_ext = ".xyz"

    filter_glob  = StringProperty(
        default="*.xyz", options={'HIDDEN'},)

    atom_xyz_export_type = EnumProperty(
        name="Type of Objects",
        description="Choose type of objects",
        items=(('0', "All", "Export all active objects"),
               ('1', "Elements", "Export only those active objects which have"
                                 " a proper element name")),
               default='1',)

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, "atom_xyz_export_type")

    def execute(self, context):
        export_xyz.export_xyz(self.atom_xyz_export_type,
                              bpy.path.abspath(self.filepath))

        return {'FINISHED'}


# The entry into the menu 'file -> import'
def menu_func(self, context):
    self.layout.operator(ImportXYZ.bl_idname, text="XYZ (.xyz)")

# The entry into the menu 'file -> export'
def menu_func_export(self, context):
    self.layout.operator(ExportXYZ.bl_idname, text="XYZ (.xyz)")

def register():
    bpy.utils.register_module(__name__)
    bpy.types.TOPBAR_MT_file_import.append(menu_func)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":

    register()
