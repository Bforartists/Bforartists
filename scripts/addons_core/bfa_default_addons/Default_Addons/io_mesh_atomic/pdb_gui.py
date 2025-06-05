# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

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

from io_mesh_atomic.pdb_import import import_pdb
from io_mesh_atomic.pdb_export import export_pdb

# -----------------------------------------------------------------------------
#                                                                     Operators

# This is the class for the file dialog of the importer.
class IMPORT_OT_pdb(Operator, ImportHelper):
    bl_idname = "import_mesh.pdb"
    bl_label  = "Import Protein Data Bank(*.pdb)"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".pdb"
    filter_glob: StringProperty(default="*.pdb", options={'HIDDEN'},)

    use_center: BoolProperty(
        name = "Object to origin", default=True,
        description = "Put the object into the global origin")
    use_camera: BoolProperty(
        name="Camera", default=False,
        description="Do you need a camera?")
    use_light: BoolProperty(
        name="Lamp", default=False,
        description = "Do you need a lamp?")
    ball: EnumProperty(
        name="Type of ball",
        description="Choose ball",
        items=(('0', "NURBS", "NURBS balls"),
               ('1', "Mesh" , "Mesh balls"),
               ('2', "Meta" , "Metaballs")),
               default='0',)
    mesh_azimuth: IntProperty(
        name = "Azimuth", default=32, min=1,
        description = "Number of sectors (azimuth)")
    mesh_zenith: IntProperty(
        name = "Zenith", default=32, min=1,
        description = "Number of sectors (zenith)")
    scale_ballradius: FloatProperty(
        name = "Balls", default=1.0, min=0.0001,
        description = "Scale factor for all atom radii")
    scale_distances: FloatProperty (
        name = "Distances", default=1.0, min=0.0001,
        description = "Scale factor for all distances")
    atomradius: EnumProperty(
        name="Type",
        description="Choose type of atom radius",
        items=(('0', "Pre-defined", "Use pre-defined radius"),
               ('1', "Atomic", "Use atomic radius"),
               ('2', "van der Waals", "Use van der Waals radius")),
               default='0',)
    use_sticks: BoolProperty(
        name="Use sticks", default=True,
        description="Do you want to display the sticks?")
    use_sticks_type: EnumProperty(
        name="Type",
        description="Choose type of stick",
        items=(('0', "Dupliverts", "Use dupliverts structures"),
               ('1', "Skin", "Use skin and subdivision modifier"),
               ('2', "Normal", "Use simple cylinders")),
               default='0',)
    sticks_subdiv_view: IntProperty(
        name = "SubDivV", default=2, min=1,
        description="Number of subdivisions (view)")
    sticks_subdiv_render: IntProperty(
        name = "SubDivR", default=2, min=1,
        description="Number of subdivisions (render)")
    sticks_sectors: IntProperty(
        name = "Sector", default=20, min=1,
        description="Number of sectors of a stick")
    sticks_radius: FloatProperty(
        name = "Radius", default=0.2, min=0.0001,
        description ="Radius of a stick")
    sticks_unit_length: FloatProperty(
        name = "Unit", default=0.05, min=0.0001,
        description = "Length of the unit of a stick in Angstrom")
    use_sticks_color: BoolProperty(
        name="Color", default=True,
        description="The sticks appear in the color of the atoms")
    use_sticks_smooth: BoolProperty(
        name="Smooth", default=True,
        description="The sticks are round (sectors are not visible)")
    use_sticks_bonds: BoolProperty(
        name="Bonds", default=False,
        description="Show double and triple bonds")
    sticks_dist: FloatProperty(
        name="", default = 0.8, min=0.0, max=3.0,
        description="Distance between sticks (double or tripple bonds) measured in stick diameter")
    use_sticks_one_object: BoolProperty(
        name="One object", default=False,
        description="All sticks are one object")
    use_sticks_one_object_nr: IntProperty(
        name = "No.", default=200, min=10,
        description="Number of sticks to be grouped at once")
    datafile: StringProperty(
        name = "", description="Path to your custom data file",
        maxlen = 256, default = "", subtype='FILE_PATH')

    # This thing here just guarantees that the menu entry is not active when the
    # check box in the addon preferences is not activated! See __init__.py
    @classmethod
    def poll(cls, context):
        pref = context.preferences
        return pref.addons[__package__].preferences.bool_pdb

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, "use_camera")
        row.prop(self, "use_light")
        row = layout.row()
        row.prop(self, "use_center")
        # Balls
        box = layout.box()
        row = box.row()
        row.label(text="Balls / atoms")
        row = box.row()
        col = row.column()
        col.prop(self, "ball")
        row = box.row()
        row.active = (self.ball == "1")
        col = row.column(align=True)
        col.prop(self, "mesh_azimuth")
        col.prop(self, "mesh_zenith")
        row = box.row()
        col = row.column()
        col.label(text="Scaling factors")
        col = row.column(align=True)
        col.prop(self, "scale_ballradius")
        col.prop(self, "scale_distances")
        row = box.row()
        row.prop(self, "atomradius")
        # Sticks
        box = layout.box()
        row = box.row()
        row.label(text="Sticks / bonds")
        row = box.row()
        row.prop(self, "use_sticks")
        row = box.row()
        row.active = self.use_sticks
        row.prop(self, "use_sticks_type")
        row = box.row()
        row.active = self.use_sticks
        col = row.column()
        if self.use_sticks_type == '0' or self.use_sticks_type == '2':
            col.prop(self, "sticks_sectors")
        col.prop(self, "sticks_radius")
        if self.use_sticks_type == '1':
            row = box.row()
            row.active = self.use_sticks
            row.prop(self, "sticks_subdiv_view")
            row.prop(self, "sticks_subdiv_render")
            row = box.row()
            row.active = self.use_sticks
        if self.use_sticks_type == '0':
            col.prop(self, "sticks_unit_length")
        col = row.column(align=True)
        if self.use_sticks_type == '0':
            col.prop(self, "use_sticks_color")
        col.prop(self, "use_sticks_smooth")
        if self.use_sticks_type == '0' or self.use_sticks_type == '2':
            col.prop(self, "use_sticks_bonds")
        row = box.row()
        if self.use_sticks_type == '0':
            row.active = self.use_sticks and self.use_sticks_bonds
            row.label(text="Distance")
            row.prop(self, "sticks_dist")
        if self.use_sticks_type == '2':
            row.active = self.use_sticks
            col = row.column()
            col.prop(self, "use_sticks_one_object")
            col = row.column()
            col.active = self.use_sticks_one_object
            col.prop(self, "use_sticks_one_object_nr")
            row = box.row()
            row.active = self.use_sticks and self.use_sticks_bonds
            row.label(text="Distance")
            row.prop(self, "sticks_dist")

    def execute(self, context):
        # Switch to 'OBJECT' mode when in 'EDIT' mode.
        if bpy.context.mode == 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        # This is in order to solve this strange 'relative path' thing.
        filepath_pdb = bpy.path.abspath(self.filepath)

        # Execute main routine
        import_pdb(self.ball,
                   self.mesh_azimuth,
                   self.mesh_zenith,
                   self.scale_ballradius,
                   self.atomradius,
                   self.scale_distances,
                   self.use_sticks,
                   self.use_sticks_type,
                   self.sticks_subdiv_view,
                   self.sticks_subdiv_render,
                   self.use_sticks_color,
                   self.use_sticks_smooth,
                   self.use_sticks_bonds,
                   self.use_sticks_one_object,
                   self.use_sticks_one_object_nr,
                   self.sticks_unit_length,
                   self.sticks_dist,
                   self.sticks_sectors,
                   self.sticks_radius,
                   self.use_center,
                   self.use_camera,
                   self.use_light,
                   filepath_pdb)

        return {'FINISHED'}


# This is the class for the file dialog of the exporter.
class EXPORT_OT_pdb(Operator, ExportHelper):
    bl_idname = "export_mesh.pdb"
    bl_label  = "Export Protein Data Bank(*.pdb)"
    filename_ext = ".pdb"

    filter_glob: StringProperty(
        default="*.pdb", options={'HIDDEN'},)

    atom_pdb_export_type: EnumProperty(
        name="Type of Objects",
        description="Choose type of objects",
        items=(('0', "All", "Export all active objects"),
               ('1', "Elements", "Export only those active objects which have"
                                 " a proper element name")),
               default='1',)

    # This thing here just guarantees that the menu entry is not active when the
    # check box in the addon preferences is not activated! See __init__.py
    @classmethod
    def poll(cls, context):
        pref = context.preferences
        return pref.addons[__package__].preferences.bool_pdb

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, "atom_pdb_export_type")

    def execute(self, context):
        export_pdb(self.atom_pdb_export_type,
                   bpy.path.abspath(self.filepath))

        return {'FINISHED'}
