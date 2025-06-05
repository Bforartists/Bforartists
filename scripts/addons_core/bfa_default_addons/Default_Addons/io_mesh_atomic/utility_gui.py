# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import Operator, Panel
from bpy.props import (StringProperty,
                       EnumProperty,
                       FloatProperty,
                       BoolProperty)

from io_mesh_atomic.utility_panel import choose_objects
from io_mesh_atomic.utility_panel import custom_datafile
from io_mesh_atomic.utility_panel import custom_datafile_change_atom_props
from io_mesh_atomic.utility_panel import separate_atoms
from io_mesh_atomic.utility_panel import distance


# -----------------------------------------------------------------------------
#                                                                           GUI

# The panel.
class PANEL_PT_prepare(Panel):
    bl_label       = "Atomic Blender Utilities"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_options     = {'DEFAULT_CLOSED'}
    bl_category = "Create"
    bl_idname = "ATOMIC_PT_utilities"


    # This thing here just guarantees that the panel is NOT opened when the
    # check box in the addon preferences is not activated! See __init__.py
    @classmethod
    def poll(cls, context):
        pref = context.preferences
        return pref.addons[__package__].preferences.bool_utility

    def draw(self, context):
        layout = self.layout
        scn    = context.scene.atom_blend

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Custom data file")
        col.prop(scn, "datafile")
        col.operator("atom_blend.datafile_apply")

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Measure distances")
        col.operator("atom_blend.button_distance")
        col.prop(scn, "distance")

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Change atom size")
        col.label(text="1. Type of radii")
        col.prop(scn, "radius_type")
        col2 = col.column()
        col2.active = (scn.radius_type == '3')
        col2.prop(scn, "radius_type_ionic")
        col = box.column(align=True)
        col.label(text="2. Radii in pm")
        col.prop(scn, "radius_pm_name")
        col.prop(scn, "radius_pm")
        col = box.column(align=True)
        col.label(text="3. Radii by scale")
        col.prop(scn, "radius_all")
        row = col.row()
        row.operator("atom_blend.radius_all_smaller")
        row.operator("atom_blend.radius_all_bigger")

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Change stick size")
        col.prop(scn, "sticks_all")
        row = col.row()
        row.operator("atom_blend.sticks_all_smaller")
        row.operator("atom_blend.sticks_all_bigger")

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Change atom shape")
        col2 = col.column()
        col2.active = (scn.replace_objs_special == '0')
        col2.prop(scn, "replace_objs")
        col2.prop(scn, "replace_objs_material")
        col.prop(scn, "replace_objs_special")
        col.operator("atom_blend.replace_atom")
        col.label(text="Default values")
        col.operator("atom_blend.default_atoms")

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Separate atoms")
        col3 = col.column()
        col3.active = (bpy.context.mode == 'EDIT_MESH')
        col3.operator("atom_blend.separate_atom")


# The properties of buttons etc. in the panel.
class PanelProperties(bpy.types.PropertyGroup):

    def Callback_radius_type(self, context):
        scn = bpy.context.scene.atom_blend
        choose_objects("ATOM_RADIUS_TYPE",
                       None,
                       None,
                       scn.radius_type,
                       scn.radius_type_ionic,
                       None)
    def Callback_radius_pm(self, context):
        scn = bpy.context.scene.atom_blend
        choose_objects("ATOM_RADIUS_PM",
                       None,
                       [scn.radius_pm_name,
                       scn.radius_pm],
                       None,
                       None,
                       None)

    datafile: StringProperty(
        name = "", description="Path to your custom data file",
        maxlen = 256, default = "", subtype='FILE_PATH')
    XYZ_file: StringProperty(
        name = "Path to file", default="",
        description = "Path of the XYZ file")
    number_atoms: StringProperty(name="",
        default="Number", description = "This output shows "
        "the number of atoms which have been loaded")
    distance: StringProperty(
        name="", default="Distance (A)",
        description="Distance of 2 objects in Angstrom")
    replace_objs: EnumProperty(
        name="Shape",
        description="Choose a different atom shape",
        items=(('0',"Unchanged", "Do not change the shape"),
               ('1a',"Sphere (Mesh)", "Replace with a sphere (Mesh)"),
               ('1b',"Sphere (NURBS)", "Replace with a sphere (NURBS)"),
               ('2',"Cube", "Replace with a cube"),
               ('3',"Plane", "Replace with a plane"),
               ('4a',"Circle (Mesh)", "Replace with a circle (Mesh)"),
               ('4b',"Circle (NURBS)", "Replace with a circle (NURBS)"),
               ('5a',"Icosphere 1", "Replace with a icosphere, subd=1"),
               ('5b',"Icosphere 2", "Replace with a icosphere, subd=2"),
               ('5c',"Icosphere 3", "Replace with a icosphere, subd=3"),
               ('5d',"Icosphere 4", "Replace with a icosphere, subd=4"),
               ('5e',"Icosphere 5", "Replace with a icosphere, subd=5"),
               ('6a',"Cylinder (Mesh)", "Replace with a cylinder (Mesh)"),
               ('6b',"Cylinder (NURBS)", "Replace with a cylinder (NURBS)"),
               ('7',"Cone", "Replace with a cone"),
               ('8a',"Torus (Mesh)", "Replace with a torus (Mesh)"),
               ('8b',"Torus (NURBS)", "Replace with a torus (NURBS)")),
               default='0',)
    replace_objs_material: EnumProperty(
        name="Material",
        description="Choose a different material",
        items=(('0',"Unchanged", "Leave the material unchanged"),
               ('1',"Normal", "Use normal material (no transparency and reflection)"),
               ('2',"Transparent", "Use transparent material"),
               ('3',"Reflecting", "Use reflecting material"),
               ('4',"Transparent + reflecting", "Use transparent and reflecting material")),
               default='0',)
    replace_objs_special: EnumProperty(
        name="Special",
        description="Choose a special atom shape",
        items=(('0',"None", "Use no special shape."),
               ('1',"F2+ center", "Replace with a F2+ center"),
               ('2',"F+ center", "Replace with a F+ center"),
               ('3',"F0 center", "Replace with a F0 center")),
               default='0',)
    radius_type: EnumProperty(
        name="Type",
        description="Which type of atom radii?",
        items=(('0',"predefined", "Use pre-defined radii"),
               ('1',"atomic", "Use atomic radii"),
               ('2',"van der Waals","Use van der Waals radii"),
               ('3',"ionic radii", "Use ionic radii")),
               default='0',update=Callback_radius_type)
    radius_type_ionic: EnumProperty(
        name="Charge",
        description="Charge state of the ions if existing",
        items=(('0',"-4", "Charge state -4"),
               ('1',"-3", "Charge state -3"),
               ('2',"-2", "Charge state -2"),
               ('3',"-1", "Charge state -1"),
               ('4'," 0", "Charge state  0: nothing is done"),
               ('5',"+1", "Charge state +1"),
               ('6',"+2", "Charge state +2"),
               ('7',"+3", "Charge state +3"),
               ('8',"+4", "Charge state +4"),
               ('9',"+5", "Charge state +5"),
               ('10',"+6", "Charge state +6"),
               ('11',"+7", "Charge state +7")),
               default='4',update=Callback_radius_type)
    radius_pm_name: StringProperty(
        name="", default="Atom name",
        description="Put in the name of the atom (e.g. Hydrogen)")
    radius_pm: FloatProperty(
        name="", default=100.0, min=0.0,
        description="Put in the radius of the atom (in pm)",
        update=Callback_radius_pm)
    radius_all: FloatProperty(
        name="Scale", default = 1.05, min=1.0, max=5.0,
        description="Put in the scale factor")
    sticks_all: FloatProperty(
        name="Scale", default = 1.05, min=1.0, max=5.0,
        description="Put in the scale factor")


# Button loading a custom data file
class DatafileApply(Operator):
    bl_idname = "atom_blend.datafile_apply"
    bl_label = "Apply"
    bl_description = "Use color and radii values stored in the custom file"

    def execute(self, context):
        scn = bpy.context.scene.atom_blend

        if scn.datafile == "":
            return {'FINISHED'}

        custom_datafile(scn.datafile)
        custom_datafile_change_atom_props()

        return {'FINISHED'}


# Button for separating single atoms from a dupliverts structure
class DefaultAtom(Operator):
    bl_idname = "atom_blend.default_atoms"
    bl_label = "Default"
    bl_description = ("Use default shapes and colors for atoms")

    # Are we in the OBJECT mode?
    @classmethod
    def poll(self, context):
        if bpy.context.mode == 'OBJECT':
            return True
        else:
            return False

    def execute(self, context):
        scn = bpy.context.scene.atom_blend
        choose_objects("ATOM_DEFAULT_OBJ",
                       None,
                       None,
                       None,
                       None,
                       None)
        return {'FINISHED'}


# Button for separating single atoms from a dupliverts structure
class ReplaceAtom(Operator):
    bl_idname = "atom_blend.replace_atom"
    bl_label = "Replace"
    bl_description = ("Replace selected atoms with atoms of different shape")

    # Are we in the OBJECT mode?
    @classmethod
    def poll(self, context):
        if bpy.context.mode == 'OBJECT':
            return True
        else:
            return False

    def execute(self, context):
        scn = bpy.context.scene.atom_blend
        choose_objects("ATOM_REPLACE_OBJ",
                       None,
                       None,
                       None,
                       None,
                       None)
        return {'FINISHED'}


# Button for separating single atoms from a dupliverts structure
class SeparateAtom(Operator):
    bl_idname = "atom_blend.separate_atom"
    bl_label = "Separate"
    bl_description = ("Separate selected atoms in a dupliverts structure. "
                      "You have to be in the 'Edit Mode'")

    # Are we in the EDIT mode?
    @classmethod
    def poll(self, context):
        if bpy.context.mode == 'EDIT_MESH':
            return True
        else:
            return False

    def execute(self, context):
        scn = bpy.context.scene.atom_blend

        separate_atoms(scn)

        return {'FINISHED'}


# Button for measuring the distance of active objects
class DistanceButton(Operator):
    bl_idname = "atom_blend.button_distance"
    bl_label = "Measure ..."
    bl_description = "Measure the distance between two atoms (objects)"

    def execute(self, context):
        scn  = bpy.context.scene.atom_blend
        dist = distance()

        # Put the distance into the string of the output field.
        scn.distance = dist
        return {'FINISHED'}


# Button for increasing the radii of all selected atoms
class RadiusAllBiggerButton(Operator):
    bl_idname = "atom_blend.radius_all_bigger"
    bl_label = "Bigger ..."
    bl_description = "Increase the radii of selected atoms"

    def execute(self, context):
        scn = bpy.context.scene.atom_blend
        choose_objects("ATOM_RADIUS_ALL",
                       scn.radius_all,
                       None,
                       None,
                       None,
                       None)
        return {'FINISHED'}


# Button for decreasing the radii of all selected atoms
class RadiusAllSmallerButton(Operator):
    bl_idname = "atom_blend.radius_all_smaller"
    bl_label = "Smaller ..."
    bl_description = "Decrease the radii of selected atoms"

    def execute(self, context):
        scn = bpy.context.scene.atom_blend
        choose_objects("ATOM_RADIUS_ALL",
                       1.0/scn.radius_all,
                       None,
                       None,
                       None,
                       None)
        return {'FINISHED'}


# Button for increasing the radii of all selected sticks
class SticksAllBiggerButton(Operator):
    bl_idname = "atom_blend.sticks_all_bigger"
    bl_label = "Bigger ..."
    bl_description = "Increase the radii of selected sticks"

    def execute(self, context):
        scn = bpy.context.scene.atom_blend
        choose_objects("STICKS_RADIUS_ALL",
                       None,
                       None,
                       None,
                       None,
                       scn.sticks_all)
        return {'FINISHED'}


# Button for decreasing the radii of all selected sticks
class SticksAllSmallerButton(Operator):
    bl_idname = "atom_blend.sticks_all_smaller"
    bl_label = "Smaller ..."
    bl_description = "Decrease the radii of selected sticks"

    def execute(self, context):
        scn = bpy.context.scene.atom_blend
        choose_objects("STICKS_RADIUS_ALL",
                       None,
                       None,
                       None,
                       None,
                       1.0/scn.sticks_all)
        return {'FINISHED'}
