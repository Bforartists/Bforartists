#====================== BEGIN GPL LICENSE BLOCK ======================
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
#======================= END GPL LICENSE BLOCK ========================

bl_info = {
    "name": "Sapling",
    "author": "Andrew Hale (TrumanBlending)",
    "version": (0, 2, 6),
    "blender": (2, 73, 0),
    "location": "View3D > Add > Curve",
    "description": ("Adds a parametric tree. The method is presented by "
    "Jason Weber & Joseph Penn in their paper 'Creation and Rendering of "
    "Realistic Trees'."),
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/Curve/Sapling_Tree",
    "category": "Add Curve",
}


if "bpy" in locals():
    import importlib
    importlib.reload(utils)
else:
    from add_curve_sapling import utils

import bpy
import time
import os

#from utils import *
from mathutils import *
from math import pi, sin, degrees, radians, atan2, copysign
from random import random, uniform, seed, choice, getstate, setstate
from bpy.props import *

from add_curve_sapling.utils import *

#global splitError
useSet = False

shapeList = [('0', 'Conical (0)', 'Shape = 0'),
            ('1', 'Spherical (1)', 'Shape = 1'),
            ('2', 'Hemispherical (2)', 'Shape = 2'),
            ('3', 'Cylindrical (3)', 'Shape = 3'),
            ('4', 'Tapered Cylindrical (4)', 'Shape = 4'),
            ('5', 'Flame (5)', 'Shape = 5'),
            ('6', 'Inverse Conical (6)', 'Shape = 6'),
            ('7', 'Tend Flame (7)', 'Shape = 7')]

handleList = [('0', 'Auto', 'Auto'),
                ('1', 'Vector', 'Vector')]

settings = [('0', 'Geometry', 'Geometry'),
            ('1', 'Branch Splitting', 'Branch Splitting'),
            ('2', 'Branch Growth', 'Branch Growth'),
            ('3', 'Pruning', 'Pruning'),
            ('4', 'Leaves', 'Leaves'),
            ('5', 'Armature', 'Armature')]


def getPresetpath():
    """Support user defined scripts directory
       Find the first ocurrence of add_curve_sapling/presets in possible script paths
       and return it as preset path"""
    presetpath = ""
    for p in bpy.utils.script_paths():
        presetpath = os.path.join(p, 'addons', 'add_curve_sapling', 'presets')
        if os.path.exists(presetpath):
            break
    return presetpath


class ExportData(bpy.types.Operator):
    """This operator handles writing presets to file"""
    bl_idname = 'sapling.exportdata'
    bl_label = 'Export Preset'

    data = StringProperty()

    def execute(self, context):
        # Unpack some data from the input
        data, filename = eval(self.data)
        try:
            # Check whether the file exists by trying to open it.
            f = open(os.path.join(getPresetpath(), filename + '.py'), 'r')
            f.close()
            # If it exists then report an error
            self.report({'ERROR_INVALID_INPUT'}, 'Preset Already Exists')
            return {'CANCELLED'}
        except IOError:
            if data:
                # If it doesn't exist, create the file with the required data
                f = open(os.path.join(getPresetpath(), filename + '.py'), 'w')
                f.write(data)
                f.close()
                return {'FINISHED'}
            else:
                return {'CANCELLED'}


class ImportData(bpy.types.Operator):
    """This operator handles importing existing presets"""
    bl_idname = 'sapling.importdata'
    bl_label = 'Import Preset'

    filename = StringProperty()

    def execute(self, context):
        # Make sure the operator knows about the global variables
        global settings, useSet
        # Read the preset data into the global settings
        f = open(os.path.join(getPresetpath(), self.filename), 'r')
        settings = f.readline()
        f.close()
        #print(settings)
        settings = eval(settings)
        # Set the flag to use the settings
        useSet = True
        return {'FINISHED'}


class PresetMenu(bpy.types.Menu):
    """Create the preset menu by finding all preset files """ \
    """in the preset directory"""
    bl_idname = "sapling.presetmenu"
    bl_label = "Presets"

    def draw(self, context):
        # Get all the sapling presets
        presets = [a for a in os.listdir(getPresetpath()) if a[-3:] == '.py']
        layout = self.layout
        # Append all to the menu
        for p in presets:
            layout.operator("sapling.importdata", text=p[:-3]).filename = p


class AddTree(bpy.types.Operator):
    bl_idname = "curve.tree_add"
    bl_label = "Sapling: Add Tree"
    bl_options = {'REGISTER', 'UNDO'}


    def update_tree(self, context):
        self.do_update = True

    def no_update_tree(self, context):
        self.do_update = False

    do_update = BoolProperty(name='Do Update',
        default=True, options={'HIDDEN'})

    chooseSet = EnumProperty(name='Settings',
        description='Choose the settings to modify',
        items=settings,
        default='0', update=no_update_tree)
    bevel = BoolProperty(name='Bevel',
        description='Whether the curve is beveled',
        default=False, update=update_tree)
    prune = BoolProperty(name='Prune',
        description='Whether the tree is pruned',
        default=False, update=update_tree)
    showLeaves = BoolProperty(name='Show Leaves',
        description='Whether the leaves are shown',
        default=False, update=update_tree)
    useArm = BoolProperty(name='Use Armature',
        description='Whether the armature is generated',
        default=False, update=update_tree)
    seed = IntProperty(name='Random Seed',
        description='The seed of the random number generator',
        default=0, update=update_tree)
    handleType = IntProperty(name='Handle Type',
        description='The type of curve handles',
        min=0,
        max=1,
        default=0, update=update_tree)
    levels = IntProperty(name='Levels',
        description='Number of recursive branches (Levels, note that last level is also used for generating leaves)',
        min=1,
        max=6,
        default=3, update=update_tree)
    length = FloatVectorProperty(name='Length',
        description='The relative lengths of each branch level (nLength)',
        min=1e-6,
        default=[1, 0.3, 0.6, 0.45],
        size=4, update=update_tree)
    lengthV = FloatVectorProperty(name='Length Variation',
        description='The relative length variations of each level (nLengthV)',
        min=0.0,
        default=[0, 0, 0, 0],
        size=4, update=update_tree)
    branches = IntVectorProperty(name='Branches',
        description='The number of branches grown at each level (nBranches)',
        min=0,
        default=[50, 30, 10, 10],
        size=4, update=update_tree)
    curveRes = IntVectorProperty(name='Curve Resolution',
        description='The number of segments on each branch (nCurveRes)',
        min=1,
        default=[3, 5, 3, 1],
        size=4, update=update_tree)
    curve = FloatVectorProperty(name='Curvature',
        description='The angle of the end of the branch (nCurve)',
        default=[0, -40, -40, 0],
        size=4, update=update_tree)
    curveV = FloatVectorProperty(name='Curvature Variation',
        description='Variation of the curvature (nCurveV)',
        default=[20, 50, 75, 0],
        size=4, update=update_tree)
    curveBack = FloatVectorProperty(name='Back Curvature',
        description='Curvature for the second half of a branch (nCurveBack)',
        default=[0, 0, 0, 0],
        size=4, update=update_tree)
    baseSplits = IntProperty(name='Base Splits',
        description='Number of trunk splits at its base (nBaseSplits)',
        min=0,
        default=0, update=update_tree)
    segSplits = FloatVectorProperty(name='Segment Splits',
        description='Number of splits per segment (nSegSplits)',
        min=0,
        default=[0, 0, 0, 0],
        size=4, update=update_tree)
    splitAngle = FloatVectorProperty(name='Split Angle',
        description='Angle of branch splitting (nSplitAngle)',
        default=[0, 0, 0, 0],
        size=4, update=update_tree)
    splitAngleV = FloatVectorProperty(name='Split Angle Variation',
        description='Variation in the split angle (nSplitAngleV)',
        default=[0, 0, 0, 0],
        size=4, update=update_tree)
    scale = FloatProperty(name='Scale',
        description='The tree scale (Scale)',
        min=0.001,
        default=13.0, update=update_tree)
    scaleV = FloatProperty(name='Scale Variation',
        description='The variation in the tree scale (ScaleV)',
        default=3.0, update=update_tree)
    attractUp = FloatProperty(name='Vertical Attraction',
        description='Branch upward attraction',
        default=0.0, update=update_tree)
    shape = EnumProperty(name='Shape',
        description='The overall shape of the tree (Shape) - WARNING: at least three "Levels" of branching are needed',
        items=shapeList,
        default='7', update=update_tree)
    baseSize = FloatProperty(name='Base Size',
        description='Fraction of tree height with no branches (BaseSize)',
        min=0.001,
        max=1.0,
        default=0.4, update=update_tree)
    ratio = FloatProperty(name='Ratio',
        description='Base radius size (Ratio)',
        min=0.0,
        default=0.015, update=update_tree)
    taper = FloatVectorProperty(name='Taper',
        description='The fraction of tapering on each branch (nTaper)',
        min=0.0,
        max=1.0,
        default=[1, 1, 1, 1],
        size=4, update=update_tree)
    ratioPower = FloatProperty(name='Branch Radius Ratio',
        description=('Power which defines the radius of a branch compared to '
        'the radius of the branch it grew from (RatioPower)'),
        min=0.0,
        default=1.2, update=update_tree)
    downAngle = FloatVectorProperty(name='Down Angle',
        description=('The angle between a new branch and the one it grew '
        'from (nDownAngle)'),
        default=[90, 60, 45, 45],
        size=4, update=update_tree)
    downAngleV = FloatVectorProperty(name='Down Angle Variation',
        description='Variation in the down angle (nDownAngleV)',
        default=[0, -50, 10, 10],
        size=4, update=update_tree)
    rotate = FloatVectorProperty(name='Rotate Angle',
        description=('The angle of a new branch around the one it grew from '
        '(nRotate)'),
        default=[140, 140, 140, 77],
        size=4, update=update_tree)
    rotateV = FloatVectorProperty(name='Rotate Angle Variation',
        description='Variation in the rotate angle (nRotateV)',
        default=[0, 0, 0, 0],
        size=4, update=update_tree)
    scale0 = FloatProperty(name='Radius Scale',
        description='The scale of the trunk radius (0Scale)',
        min=0.0,
        default=1.0, update=update_tree)
    scaleV0 = FloatProperty(name='Radius Scale Variation',
        description='Variation in the radius scale (0ScaleV)',
        default=0.2, update=update_tree)
    pruneWidth = FloatProperty(name='Prune Width',
        description='The width of the envelope (PruneWidth)',
        min=0.0,
        default=0.4, update=update_tree)
    pruneWidthPeak = FloatProperty(name='Prune Width Peak',
        description=('Fraction of envelope height where the maximum width '
        'occurs (PruneWidthPeak)'),
        min=0.0,
        default=0.6, update=update_tree)
    prunePowerHigh = FloatProperty(name='Prune Power High',
        description=('Power which determines the shape of the upper portion '
        'of the envelope (PrunePowerHigh)'),
        default=0.5, update=update_tree)
    prunePowerLow = FloatProperty(name='Prune Power Low',
        description=('Power which determines the shape of the lower portion '
        'of the envelope (PrunePowerLow)'),
        default=0.001, update=update_tree)
    pruneRatio = FloatProperty(name='Prune Ratio',
        description='Proportion of pruned length (PruneRatio)',
        min=0.0,
        max=1.0,
        default=1.0, update=update_tree)
    leaves = FloatProperty(name='Leaves',
        description='Maximum number of leaves per branch (Leaves)',
        min=0,
        max=50,
        default=25, update=update_tree)
    leafScale = FloatProperty(name='Leaf Scale',
        description='The scaling applied to the whole leaf (LeafScale)',
        min=0.0,
        default=0.17, update=update_tree)
    leafScaleX = FloatProperty(name='Leaf Scale X',
        description=('The scaling applied to the x direction of the leaf '
        '(LeafScaleX)'),
        min=0.0,
        default=1.0, update=update_tree)
    leafShape = leafDist = EnumProperty(name='Leaf Shape',
        description='The shape of the leaves, rectangular are UV mapped',
        items=(('hex', 'Hexagonal', '0'), ('rect', 'Rectangular', '1')),
        default='hex', update=update_tree)
    bend = FloatProperty(name='Leaf Bend',
        description='The proportion of bending applied to the leaf (Bend)',
        min=0.0,
        max=1.0,
        default=0.0, update=update_tree)
    leafDist = EnumProperty(name='Leaf Distribution',
        description='The way leaves are distributed on branches',
        items=shapeList,
        default='4', update=update_tree)
    bevelRes = IntProperty(name='Bevel Resolution',
        description='The bevel resolution of the curves',
        min=0,
        default=0, update=update_tree)
    resU = IntProperty(name='Curve Resolution',
        description='The resolution along the curves',
        min=1,
        default=4, update=update_tree)
    handleType = EnumProperty(name='Handle Type',
        description='The type of handles used in the spline',
        items=handleList,
        default='1', update=update_tree)
    frameRate = FloatProperty(name='Frame Rate',
        description=('The number of frames per second which can be used to '
        'adjust the speed of animation'),
        min=0.001,
        default=1, update=update_tree)
    windSpeed = FloatProperty(name='Wind Speed',
        description='The wind speed to apply to the armature (WindSpeed)',
        default=2.0, update=update_tree)
    windGust = FloatProperty(name='Wind Gust',
        description='The greatest increase over Wind Speed (WindGust)',
        default=0.0, update=update_tree)
    armAnim = BoolProperty(name='Armature Animation',
        description='Whether animation is added to the armature',
        default=False, update=update_tree)

    presetName = StringProperty(name='Preset Name',
        description='The name of the preset to be saved',
        default='',
        subtype='FILE_NAME', update=no_update_tree)
    limitImport = BoolProperty(name='Limit Import',
        description='Limited imported tree to 2 levels & no leaves for speed',
        default=True, update=no_update_tree)

    startCurv = FloatProperty(name='Trunk Starting Angle',
        description=('The angle between vertical and the starting direction '
        'of the trunk'),
        min=0.0,
        max=360,
        default=0.0, update=update_tree)

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def check(self, context):
        # TODO, should check exact vars which require redraw
        return True

    def draw(self, context):

        layout = self.layout

        # Branch specs
        #layout.label('Tree Definition')

        layout.prop(self, 'chooseSet')

        if self.chooseSet == '0':
            box = layout.box()
            box.label("Geometry:")
            box.prop(self, 'bevel')

            row = box.row()
            row.prop(self, 'bevelRes')
            row.prop(self, 'resU')

            box.prop(self, 'handleType')
            sub = box.row()
            sub.active = self.levels >= 3
            sub.prop(self, 'shape')
            box.prop(self, 'seed')
            box.prop(self, 'ratio')

            row = box.row()
            row.prop(self, 'scale')
            row.prop(self, 'scaleV')

            row = box.row()
            row.prop(self, 'scale0')
            row.prop(self, 'scaleV0')

            # Here we create a dict of all the properties.
            # Unfortunately as_keyword doesn't work with vector properties,
            # so we need something custom. This is it
            data = []
            for a, b in (self.as_keywords(ignore=("chooseSet", "presetName", "limitImport", "do_update"))).items():
                # If the property is a vector property then add the slice to the list
                try:
                    len(b)
                    data.append((a, b[:]))
                # Otherwise, it is fine so just add it
                except:
                    data.append((a, b))
            # Create the dict from the list
            data = dict(data)

            row = box.row()
            row.prop(self, 'presetName')
            # Send the data dict and the file name to the exporter
            row.operator('sapling.exportdata').data = repr([repr(data),
                                                       self.presetName])
            row = box.row()
            row.menu('sapling.presetmenu', text='Load Preset')
            row.prop(self, 'limitImport')

        elif self.chooseSet == '1':
            box = layout.box()
            box.label("Branch Splitting:")
            box.prop(self, 'levels')
            box.prop(self, 'baseSplits')
            box.prop(self, 'baseSize')

            split = box.split()

            col = split.column()
            col.prop(self, 'branches')
            col.prop(self, 'splitAngle')
            col.prop(self, 'downAngle')
            col.prop(self, 'rotate')

            col = split.column()
            col.prop(self, 'segSplits')
            col.prop(self, 'splitAngleV')
            col.prop(self, 'downAngleV')
            col.prop(self, 'rotateV')

            box.prop(self, 'ratioPower')

        elif self.chooseSet == '2':
            box = layout.box()
            box.label("Branch Growth:")
            box.prop(self, 'startCurv')
            box.prop(self, 'attractUp')

            split = box.split()

            col = split.column()
            col.prop(self, 'length')
            col.prop(self, 'curve')
            col.prop(self, 'curveBack')

            col = split.column()
            col.prop(self, 'lengthV')
            col.prop(self, 'curveV')
            col.prop(self, 'taper')

            box.column().prop(self, 'curveRes')

        elif self.chooseSet == '3':
            box = layout.box()
            box.label("Pruning:")
            box.prop(self, 'prune')
            box.prop(self, 'pruneRatio')
            box.prop(self, 'pruneWidth')
            box.prop(self, 'pruneWidthPeak')

            row = box.row()
            row.prop(self, 'prunePowerHigh')
            row.prop(self, 'prunePowerLow')

        elif self.chooseSet == '4':
            box = layout.box()
            box.label("Leaves:")
            box.prop(self, 'showLeaves')
            box.prop(self, 'leafShape')
            box.prop(self, 'leaves')
            box.prop(self, 'leafDist')

            row = box.row()
            row.prop(self, 'leafScale')
            row.prop(self, 'leafScaleX')

            box.prop(self, 'bend')

        elif self.chooseSet == '5':
            box = layout.box()
            box.label("Armature and Animation:")

            row = box.row()
            row.prop(self, 'useArm')
            row.prop(self, 'armAnim')

            row = box.row()
            row.prop(self, 'windSpeed')
            row.prop(self, 'windGust')

            box.prop(self, 'frameRate')

    def execute(self, context):
        # Ensure the use of the global variables
        global settings, useSet
        start_time = time.time()
        #bpy.ops.ImportData.filename = "quaking_aspen"
        # If we need to set the properties from a preset then do it here
        if useSet:
            for a, b in settings.items():
                setattr(self, a, b)
            if self.limitImport:
                setattr(self, 'levels', 2)
                setattr(self, 'showLeaves', False)
            useSet = False
        if not self.do_update:
            return {'PASS_THROUGH'}
        addTree(self)
        print("Tree creation in %0.1fs" %(time.time()-start_time))
        return {'FINISHED'}

    def invoke(self, context, event):
#        global settings, useSet
#        useSet = True
        bpy.ops.sapling.importdata(filename = "quaking_aspen.py")
        return self.execute(context)


def menu_func(self, context):
    self.layout.operator(AddTree.bl_idname, text="Add Tree", icon='PLUGIN')


def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_curve_add.append(menu_func)


def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_curve_add.remove(menu_func)

if __name__ == "__main__":
    register()
