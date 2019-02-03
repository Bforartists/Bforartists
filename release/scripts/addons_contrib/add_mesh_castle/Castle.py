################################################################################
# ***** BEGIN GPL LICENSE BLOCK *****
#
# This is free software under the terms of the GNU General Public License
# you may redistribute it, and/or modify it.
#
# This code is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License (http://www.gnu.org/licenses/) for more details.
#
# ***** END GPL LICENSE BLOCK *****
'''
Generate an object: (OBJ_N) "Castle", complex mesh collection.
 Derived from many sources, inspired by many in the "community",
 - see documentation for details on use and credits.
'''
# mod list, in order of complexity and necessity...
#  some want, some needed, some a feature not a bug just need controls.
#
# @todo: fix dome radius -  not complete when wall width or depth < 15
#        globe (z/2) is fun but not intended design.
# @todo: check width minimum as is done for height, maybe depth too.
# @todo: fix grout for bottom of first row (adjust wall base).
#
# @todo: eleminate result of "None" if possible from  circ() and other subroutines.
# @todo: review defaults and limits for all UI entries.
#
#
# Abstract/experimental use only:
# @todo: Curve (wallSlope) inverts walls: reverse slope and adjust sizing to fit floor.
# @todo: Tunnel, paired sloped walls, need to create separate objects and adjust sizing.
# @todo: Turret/tower - uses rotated wall, need to change curvature/slope orientation/sizing
#  allow openings and placement (corners, center wall, etc.).
#
#
# wish list:
# @todo: do not allow opening overlap.
# @todo: implement "Oculus" for dome (top center opening). See "Radial" floor with door.
# @todo: make "true" roof: top of castle walls or turret, multiple levels, style options - peaked, flat.
# @todo: integrate portal with doorway.
# @todo: add stair_builder; keep (wall) steps.
# @todo: integrate balcony with shelf.
# @todo: add block shapes: triangle, hexagon, octagon, round (disc/ball), "Rocks" (Brikbot author), etc...
#        - possible window/door/opening shapes?
#
################################################################################

import bpy
from bpy.props import IntProperty, FloatProperty, FloatVectorProperty, BoolProperty, EnumProperty
from random import random

import math
from math import fmod, sqrt, sin, cos, atan

################################################################################

################################################################################

#####
# constants
#####

OBJ_N = "Castle"  # Primary object name (base/floor/foundation)
OBJ_CF = "CFloor"  # Multi-level "floor"
OBJ_CR = "CRoof"  # roofing
OBJ_WF = "CWallF"  # front, left, back, right wall objects
OBJ_WL = "CWallL"
OBJ_WB = "CWallB"
OBJ_WR = "CWallR"

# not sure if this is more efficient or not, just seems no need to import value.
cPie = 3.14159265359
cPieHlf = cPie / 2  # used to rotate walls 90 degrees (1.570796...)

BLOCK_MIN = 0.1  # Min block sizing; also used for openings.

WALL_MAX = 100
HALF_WALL = WALL_MAX / 2  # edging, openings, etc., limited to half wall limit.

WALL_MIN = BLOCK_MIN * 3  # min wall block size*3 for each dimension.
WALL_DEF = 20  # Default wall/dome size

LVL_MAX = 10  # castle levels (vertical wall repeat).

# riser BLOCK_XDEF should be 0.75 and tread BLOCK_DDEF 1.0 for stair steps.
BLOCK_XDEF = 0.75  # stanadard block width, including steps and shelf.
BLOCK_DDEF = 1.0  # standard block depth.
BLOCK_MAX = WALL_MAX  # Max block sizing.
BLOCK_VMAX = BLOCK_MAX / 2  # block variations, no negative values.

# gap 0 makes solid wall but affects other options, like openings, not in a good way.
# Negative gap creates "phantom blocks" (extraneous verts) inside the faces.
GAP_MIN = 0.01  # min space between blocks.
GAP_MAX = BLOCK_MAX / 2  # maybe later... -BLOCK_MIN # max space between blocks.

ROW_H_WEIGHT = 0.5  # Use 0.5, else create parameter:
#  0=no effect, 1=1:1 relationship, negative values allowed.

BASE_TMIN = BLOCK_MIN  # floor min thickness
BASE_TMAX = BLOCK_MAX / 2  # floor max thickness, limit to half (current) block height.

# Default Door settings
DEF_DOORW = 2.5
DEF_DOORH = 3.5
DEF_DOORX = 2.5

#####
# working variables, per option per level.
#####

# wall/block Settings
settings = {'w': 1.2, 'wv': 0.3, 'h': .6, 'hv': 0.1, 'd': 0.3, 'dv': 0.1,
            'g': 0.1, 'sdv': 0.1,
            'eoff': 0.3,
            'Steps': False, 'StepsL': False, 'StepsB': False, 'StepsO': False,
            'Shelf': False, 'ShelfO': False,
            'Radial': False, 'Slope': False}
# 'w':width 'wv':width Variation
# 'h':height 'hv':height Variation
# 'd':depth 'dv':depth Variation
# 'g':grout
# 'sdv':subdivision(distance or angle)
# 'eoff':edge offset
# passed as params since modified per object; no sense to change UI values.
# 'Steps' create steps, 'StepsL'step left, 'StepsB' fill with blocks, 'StepsO' outside of wall.
# 'Shelf' add shelf/balcony, 'ShelfO'outside of wall.
# 'Radial' create "disc"; makes dome when combined with "Slope" (globe when height/2).
# 'Slope' curve wall - forced for Dome

# dims = area of wall (centered/splitX from 3D cursor); modified for radial/dome.
dims = {'s': -10, 'e': 10, 't': 15}
# dims = {'s':0, 'e':cPie*3/2, 't':12.3} # radial
# 's' start, 'e' end, 't' top

# Apertures in wall, includes all openings for door, window, slot.
#openingSpecs = []
# openingSpecs indexes, based on order of creation.
OP_DOOR = 0
OP_PORT = 1
OP_CREN = 2
OP_SLOT = 3

openingSpecs = [{'a': False, 'w': 0.5, 'h': 0.5, 'x': 0.8, 'z': 0, 'n': 0, 'bvl': 0.0,
                 'v': 0, 'vl': 0, 't': 0, 'tl': 0}]
# 'a': active (apply to object),
# 'w': opening width, 'h': opening height,
# 'x': horizontal position, 'z': vertical position,
# 'n': repeat opening with a spacing of x,
# 'bvl': bevel the inside of the opening,
# 'v': height of the top arch, 'vl':height of the bottom arch,
# 't': thickness of the top arch, 'tl': thickness of the bottom arch


################################################################################

############################
#
# Psuedo macros:
#
# random values (in specific range).
# random value +-0.5
def rndc(): return (random() - 0.5)

# random value +-1


def rndd(): return rndc() * 2

# line/circle intercepts
# COff = distance perpendicular to the line to the center
# cRad=radius
# return the distance paralell to the line to the center of the circle at the intercept.
# @todo: eleminate result of "None" if possible from  circ() and other subroutines.


def circ(COff=0, cRad=1):
    absCOff = abs(COff)
    if absCOff > cRad:
        return None
    elif absCOff == cRad:
        return 0
    else:
        return sqrt(cRad**2 - absCOff**2)

# bevel blocks.
# pointsToAffect are: left=(4,6), right=(0,2)


def bevelBlockOffsets(offsets, bevel, pointsToAffect):
    for num in pointsToAffect:
        offsets[num] = offsets[num][:]
        offsets[num][0] += bevel

############################
#
# Simple material management.
# Return new, existing, or modified material reference.
#
# @todo: create additional materials based on diffuse options.
#


def uMatRGBSet(matName, RGBs, matMod=False, dShader='LAMBERT', dNtz=1.0):

    if matName not in bpy.data.materials:
        mtl = bpy.data.materials.new(matName)
        matMod = True
    else:
        mtl = bpy.data.materials[matName]

    if matMod:  # Set material values
        mtl.diffuse_color = RGBs
        mtl.diffuse_shader = dShader
        mtl.diffuse_intensity = dNtz

    return mtl

################################################################################

################################################################################
#
#  UI functions and object creation.
#


class add_castle(bpy.types.Operator):
    bl_idname = "mesh.add_castle"
    bl_label = OBJ_N
    bl_description = OBJ_N
    bl_options = {'REGISTER', 'UNDO'}

    # only create object when True
    # False allows modifying several parameters without creating object
    ConstructTog: BoolProperty(name="Construct", description="Generate the object", default=True)

    # Base area - set dimensions - Width (front/back) and Depth (sides),
    # floor origin/offset, thickness, and, material/color.
    cBaseW: FloatProperty(name="Width", min=WALL_MIN, max=WALL_MAX, default=WALL_DEF, description="Base Width (X)")
    cBaseD: FloatProperty(name="Depth", min=WALL_MIN, max=WALL_MAX, default=WALL_DEF, description="Base Depth (Y)")
    cBaseO: FloatProperty(name='Base', min=0, max=WALL_MAX, default=0, description="vert offset from 3D cursor.")
    cBaseT: FloatProperty(min=BASE_TMIN, max=BASE_TMAX, default=BASE_TMIN, description="Base thickness")

    cBaseRGB: FloatVectorProperty(min=0, max=1, default=(0.1, 0.1, 0.1), subtype='COLOR', size=3)

    CBaseB: BoolProperty(name="BloX", default=False, description="Block flooring")
    CBaseR: BoolProperty(default=False, description="Round flooring")

    CLvls: IntProperty(name="Levels", min=1, max=LVL_MAX, default=1)

    # current wall level parameter value display.
    CLvl: IntProperty(name="Level", min=1, max=LVL_MAX, default=1)

    #    curLvl=CLvl

    # block sizing
    blockX: FloatProperty(name="Width", min=BLOCK_MIN, max=BLOCK_MAX, default=BLOCK_XDEF)
    blockZ: FloatProperty(name="Height", min=BLOCK_MIN, max=BLOCK_MAX, default=BLOCK_XDEF)
    blockD: FloatProperty(name="Depth", min=BLOCK_MIN, max=BLOCK_MAX, default=BLOCK_DDEF)
    # allow 0 for test cases...
    #    blockD=FloatProperty(name="Depth",min=0,max=BLOCK_MAX,default=BLOCK_DDEF)

    blockVar: BoolProperty(name="Vary", default=True, description="Randomize block sizing")

    blockWVar: FloatProperty(name="Width", min=0, max=BLOCK_VMAX, default=BLOCK_MIN, description="Random Width")
    blockHVar: FloatProperty(name="Height", min=0, max=BLOCK_VMAX, default=BLOCK_MIN, description="Random Height")
    blockDVar: FloatProperty(name="Depth", min=0, max=BLOCK_VMAX, default=BLOCK_MIN, description="Random Depth")

    blockMerge: BoolProperty(name="Merge", default=True, description="Merge closely adjoining blocks")

    # @todo: fix edgeing for mis-matched row sizing (or just call it a feature).
    EdgeOffset: FloatProperty(name="Edging", min=0, max=HALF_WALL, default=0.25, description="stagger wall ends")

    # block spacing
    Grout: FloatProperty(name="Gap", min=GAP_MIN, max=GAP_MAX, default=0.05, description="Block separation")

    wallRGB: FloatVectorProperty(min=0, max=1, default=(0.5, 0.5, 0.5), subtype='COLOR', size=3)


    # track height with each level...?
    wallH: FloatProperty(name="Height", min=WALL_MIN, max=WALL_MAX, default=WALL_DEF)

    # floor per level - LVL_MAX
    # Base, always true (primary object/parent)
    #    CFloor1=BoolProperty(default=True)
    CFloor2: BoolProperty(default=False)
    CFloor3: BoolProperty(default=False)
    CFloor4: BoolProperty(default=False)
    CFloor5: BoolProperty(default=False)
    CFloor6: BoolProperty(default=False)
    CFloor7: BoolProperty(default=False)
    CFloor8: BoolProperty(default=False)
    CFloor9: BoolProperty(default=False)
    CFloor10: BoolProperty(default=False)

    # Which walls to generate, per level - LVL_MAX
    wallF1: BoolProperty(default=False, description="Front")
    wallF2: BoolProperty(default=False)
    wallF3: BoolProperty(default=False)
    wallF4: BoolProperty(default=False)
    wallF5: BoolProperty(default=False)
    wallF6: BoolProperty(default=False)
    wallF7: BoolProperty(default=False)
    wallF8: BoolProperty(default=False)
    wallF9: BoolProperty(default=False)
    wallF10: BoolProperty(default=False)

    wallL1: BoolProperty(default=False, description="Left")
    wallL2: BoolProperty(default=False)
    wallL3: BoolProperty(default=False)
    wallL4: BoolProperty(default=False)
    wallL5: BoolProperty(default=False)
    wallL6: BoolProperty(default=False)
    wallL7: BoolProperty(default=False)
    wallL8: BoolProperty(default=False)
    wallL9: BoolProperty(default=False)
    wallL10: BoolProperty(default=False)

    wallB1: BoolProperty(default=False, description="Back")
    wallB2: BoolProperty(default=False)
    wallB3: BoolProperty(default=False)
    wallB4: BoolProperty(default=False)
    wallB5: BoolProperty(default=False)
    wallB6: BoolProperty(default=False)
    wallB7: BoolProperty(default=False)
    wallB8: BoolProperty(default=False)
    wallB9: BoolProperty(default=False)
    wallB10: BoolProperty(default=False)

    wallR1: BoolProperty(default=False, description="Right")
    wallR2: BoolProperty(default=False)
    wallR3: BoolProperty(default=False)
    wallR4: BoolProperty(default=False)
    wallR5: BoolProperty(default=False)
    wallR6: BoolProperty(default=False)
    wallR7: BoolProperty(default=False)
    wallR8: BoolProperty(default=False)
    wallR9: BoolProperty(default=False)
    wallR10: BoolProperty(default=False)

    # round walls per level - LVL_MAX
    wallFO1: BoolProperty(default=False, description="Front")
    wallFO2: BoolProperty(default=False)
    wallFO3: BoolProperty(default=False)
    wallFO4: BoolProperty(default=False)
    wallFO5: BoolProperty(default=False)
    wallFO6: BoolProperty(default=False)
    wallFO7: BoolProperty(default=False)
    wallFO8: BoolProperty(default=False)
    wallFO9: BoolProperty(default=False)
    wallFO10: BoolProperty(default=False)

    wallLO1: BoolProperty(default=False, description="Left")
    wallLO2: BoolProperty(default=False)
    wallLO3: BoolProperty(default=False)
    wallLO4: BoolProperty(default=False)
    wallLO5: BoolProperty(default=False)
    wallLO6: BoolProperty(default=False)
    wallLO7: BoolProperty(default=False)
    wallLO8: BoolProperty(default=False)
    wallLO9: BoolProperty(default=False)
    wallLO10: BoolProperty(default=False)

    wallBO1: BoolProperty(default=False, description="Back")
    wallBO2: BoolProperty(default=False)
    wallBO3: BoolProperty(default=False)
    wallBO4: BoolProperty(default=False)
    wallBO5: BoolProperty(default=False)
    wallBO6: BoolProperty(default=False)
    wallBO7: BoolProperty(default=False)
    wallBO8: BoolProperty(default=False)
    wallBO9: BoolProperty(default=False)
    wallBO10: BoolProperty(default=False)

    wallRO1: BoolProperty(default=False, description="Right")
    wallRO2: BoolProperty(default=False)
    wallRO3: BoolProperty(default=False)
    wallRO4: BoolProperty(default=False)
    wallRO5: BoolProperty(default=False)
    wallRO6: BoolProperty(default=False)
    wallRO7: BoolProperty(default=False)
    wallRO8: BoolProperty(default=False)
    wallRO9: BoolProperty(default=False)
    wallRO10: BoolProperty(default=False)

    #    CRoof=BoolProperty(name="Roof",default=False)

    # Select wall modifier option to view/edit
    wallOpView: EnumProperty(items=(
        ("1", "Door", ""),
        ("2", "Window", ""),
        ("3", "Slot", ""),  # "classical arrow/rifle ports
        ("4", "Crenel", ""),  # gaps along top of wall
        ("5", "Steps", ""),
        ("6", "Shelf", ""),
    ),
        name="", description="View/Edit wall modifiers", default="1")
    # could add material selection for step and shelf...

    # Radiating from one point - round (disc), with slope makes dome.
    cDome: BoolProperty(name='Dome', default=False)
    cDomeRGB: FloatVectorProperty(min=0, max=1, default=(0.3, 0.1, 0), subtype='COLOR', size=3)

    cDomeH: FloatProperty(name='Height', min=WALL_MIN, max=WALL_MAX, default=WALL_DEF / 2)
    cDomeZ: FloatProperty(name='Base', min=BASE_TMIN, max=WALL_MAX, default=WALL_DEF, description="offset from floor")
    cDomeO: FloatProperty(name='Oculus', min=0, max=HALF_WALL, default=0, description="Dome opening.")

    # holes/openings in wall - doors, windows or slots; affects block row size.
    wallDoorW: FloatProperty(name="Width", min=BLOCK_MIN, max=HALF_WALL, default=DEF_DOORW)
    wallDoorH: FloatProperty(name="Height", min=BLOCK_MIN, max=HALF_WALL, default=DEF_DOORH)
    wallDoorX: FloatProperty(name="Indent", min=0, max=WALL_MAX, default=DEF_DOORX, description="horizontal offset from cursor")
    doorBvl: FloatProperty(name="Bevel", min=-10, max=10, default=0.25, description="Angle block face")
    doorRpt: BoolProperty(default=False, description="make multiple openings")
    doorArch: BoolProperty(name="Arch", default=True)
    doorArchC: FloatProperty(name="Curve", min=0.01, max=HALF_WALL, default=2.5, description="Arch curve height")
    doorArchT: FloatProperty(name="Thickness", min=0.001, max=HALF_WALL, default=0.75)

    wallDF1: BoolProperty(default=False, description="Front")
    wallDF2: BoolProperty(default=False)
    wallDF3: BoolProperty(default=False)
    wallDF4: BoolProperty(default=False)
    wallDF5: BoolProperty(default=False)
    wallDF6: BoolProperty(default=False)
    wallDF7: BoolProperty(default=False)
    wallDF8: BoolProperty(default=False)
    wallDF9: BoolProperty(default=False)
    wallDF10: BoolProperty(default=False)

    wallDL1: BoolProperty(default=False, description="Left")
    wallDL2: BoolProperty(default=False)
    wallDL3: BoolProperty(default=False)
    wallDL4: BoolProperty(default=False)
    wallDL5: BoolProperty(default=False)
    wallDL6: BoolProperty(default=False)
    wallDL7: BoolProperty(default=False)
    wallDL8: BoolProperty(default=False)
    wallDL9: BoolProperty(default=False)
    wallDL10: BoolProperty(default=False)

    wallDB1: BoolProperty(default=False, description="Back")
    wallDB2: BoolProperty(default=False)
    wallDB3: BoolProperty(default=False)
    wallDB4: BoolProperty(default=False)
    wallDB5: BoolProperty(default=False)
    wallDB6: BoolProperty(default=False)
    wallDB7: BoolProperty(default=False)
    wallDB8: BoolProperty(default=False)
    wallDB9: BoolProperty(default=False)
    wallDB10: BoolProperty(default=False)

    wallDR1: BoolProperty(default=False, description="Right")
    wallDR2: BoolProperty(default=False)
    wallDR3: BoolProperty(default=False)
    wallDR4: BoolProperty(default=False)
    wallDR5: BoolProperty(default=False)
    wallDR6: BoolProperty(default=False)
    wallDR7: BoolProperty(default=False)
    wallDR8: BoolProperty(default=False)
    wallDR9: BoolProperty(default=False)
    wallDR10: BoolProperty(default=False)

    # Slots, embrasure - classical slit for arrow/rifle ports.
    # need to prevent overlap with arch openings - though inversion is an interesting effect.
    SlotVW: FloatProperty(name="Width", min=BLOCK_MIN, max=HALF_WALL, default=0.5)
    SlotVH: FloatProperty(name="Height", min=BLOCK_MIN, max=HALF_WALL, default=3.5)
    SlotVL: FloatProperty(name="Indent", min=-WALL_MAX, max=WALL_MAX, default=0, description="The x position or spacing")
    SlotVZ: FloatProperty(name="Bottom", min=-WALL_MAX, max=WALL_MAX, default=4.00)
    slotVArchT: BoolProperty(name="Top", default=True)
    slotVArchB: BoolProperty(name="Bottom", default=True)
    SlotVRpt: BoolProperty(name="Repeat", default=False)

    wallEF1: BoolProperty(default=False, description="Front")
    wallEF2: BoolProperty(default=False)
    wallEF3: BoolProperty(default=False)
    wallEF4: BoolProperty(default=False)
    wallEF5: BoolProperty(default=False)
    wallEF6: BoolProperty(default=False)
    wallEF7: BoolProperty(default=False)
    wallEF8: BoolProperty(default=False)
    wallEF9: BoolProperty(default=False)
    wallEF10: BoolProperty(default=False)

    wallEL1: BoolProperty(default=False, description="Left")
    wallEL2: BoolProperty(default=False)
    wallEL3: BoolProperty(default=False)
    wallEL4: BoolProperty(default=False)
    wallEL5: BoolProperty(default=False)
    wallEL6: BoolProperty(default=False)
    wallEL7: BoolProperty(default=False)
    wallEL8: BoolProperty(default=False)
    wallEL9: BoolProperty(default=False)
    wallEL10: BoolProperty(default=False)

    wallEB1: BoolProperty(default=False, description="Back")
    wallEB2: BoolProperty(default=False)
    wallEB3: BoolProperty(default=False)
    wallEB4: BoolProperty(default=False)
    wallEB5: BoolProperty(default=False)
    wallEB6: BoolProperty(default=False)
    wallEB7: BoolProperty(default=False)
    wallEB8: BoolProperty(default=False)
    wallEB9: BoolProperty(default=False)
    wallEB10: BoolProperty(default=False)

    wallER1: BoolProperty(default=False, description="Right")
    wallER2: BoolProperty(default=False)
    wallER3: BoolProperty(default=False)
    wallER4: BoolProperty(default=False)
    wallER5: BoolProperty(default=False)
    wallER6: BoolProperty(default=False)
    wallER7: BoolProperty(default=False)
    wallER8: BoolProperty(default=False)
    wallER9: BoolProperty(default=False)
    wallER10: BoolProperty(default=False)

    # window opening in wall.
    wallPort: BoolProperty(default=False, description="Window opening")
    wallPortW: FloatProperty(name="Width", min=BLOCK_MIN, max=HALF_WALL, default=2, description="Window (hole) width")
    wallPortH: FloatProperty(name="Height", min=BLOCK_MIN, max=HALF_WALL, default=3, description="Window (hole) height")
    wallPortX: FloatProperty(name="Indent", min=-WALL_MAX, max=WALL_MAX, default=-2.5, description="The x position or spacing")
    wallPortZ: FloatProperty(name="Bottom", min=-WALL_MAX, max=WALL_MAX, default=5)
    wallPortBvl: FloatProperty(name="Bevel", min=-10, max=10, default=0.25, description="Angle block face")
    wallPortArchT: BoolProperty(name="Top", default=False)
    wallPortArchB: BoolProperty(name="Bottom", default=False)
    wallPortRpt: BoolProperty(name="Repeat", default=False)

    wallPF1: BoolProperty(default=False, description="Front")
    wallPF2: BoolProperty(default=False)
    wallPF3: BoolProperty(default=False)
    wallPF4: BoolProperty(default=False)
    wallPF5: BoolProperty(default=False)
    wallPF6: BoolProperty(default=False)
    wallPF7: BoolProperty(default=False)
    wallPF8: BoolProperty(default=False)
    wallPF9: BoolProperty(default=False)
    wallPF10: BoolProperty(default=False)

    wallPL1: BoolProperty(default=False, description="Left")
    wallPL2: BoolProperty(default=False)
    wallPL3: BoolProperty(default=False)
    wallPL4: BoolProperty(default=False)
    wallPL5: BoolProperty(default=False)
    wallPL6: BoolProperty(default=False)
    wallPL7: BoolProperty(default=False)
    wallPL8: BoolProperty(default=False)
    wallPL9: BoolProperty(default=False)
    wallPL10: BoolProperty(default=False)

    wallPB1: BoolProperty(default=False, description="Back")
    wallPB2: BoolProperty(default=False)
    wallPB3: BoolProperty(default=False)
    wallPB4: BoolProperty(default=False)
    wallPB5: BoolProperty(default=False)
    wallPB6: BoolProperty(default=False)
    wallPB7: BoolProperty(default=False)
    wallPB8: BoolProperty(default=False)
    wallPB9: BoolProperty(default=False)
    wallPB10: BoolProperty(default=False)

    wallPR1: BoolProperty(default=False, description="Right")
    wallPR2: BoolProperty(default=False)
    wallPR3: BoolProperty(default=False)
    wallPR4: BoolProperty(default=False)
    wallPR5: BoolProperty(default=False)
    wallPR6: BoolProperty(default=False)
    wallPR7: BoolProperty(default=False)
    wallPR8: BoolProperty(default=False)
    wallPR9: BoolProperty(default=False)
    wallPR10: BoolProperty(default=False)

    # Crenel = "gaps" on top of wall.
    # review and determine min for % - should allow less...
    CrenelXP: FloatProperty(name="Width %", min=0.10, max=1.0, default=0.15)
    CrenelZP: FloatProperty(name="Height %", min=0.10, max=1.0, default=0.10)

    wallCF1: BoolProperty(default=False, description="Front")
    wallCF2: BoolProperty(default=False)
    wallCF3: BoolProperty(default=False)
    wallCF4: BoolProperty(default=False)
    wallCF5: BoolProperty(default=False)
    wallCF6: BoolProperty(default=False)
    wallCF7: BoolProperty(default=False)
    wallCF8: BoolProperty(default=False)
    wallCF9: BoolProperty(default=False)
    wallCF10: BoolProperty(default=False)

    wallCL1: BoolProperty(default=False, description="Left")
    wallCL2: BoolProperty(default=False)
    wallCL3: BoolProperty(default=False)
    wallCL4: BoolProperty(default=False)
    wallCL5: BoolProperty(default=False)
    wallCL6: BoolProperty(default=False)
    wallCL7: BoolProperty(default=False)
    wallCL8: BoolProperty(default=False)
    wallCL9: BoolProperty(default=False)
    wallCL10: BoolProperty(default=False)

    wallCB1: BoolProperty(default=False, description="Back")
    wallCB2: BoolProperty(default=False)
    wallCB3: BoolProperty(default=False)
    wallCB4: BoolProperty(default=False)
    wallCB5: BoolProperty(default=False)
    wallCB6: BoolProperty(default=False)
    wallCB7: BoolProperty(default=False)
    wallCB8: BoolProperty(default=False)
    wallCB9: BoolProperty(default=False)
    wallCB10: BoolProperty(default=False)

    wallCR1: BoolProperty(default=False, description="Right")
    wallCR2: BoolProperty(default=False)
    wallCR3: BoolProperty(default=False)
    wallCR4: BoolProperty(default=False)
    wallCR5: BoolProperty(default=False)
    wallCR6: BoolProperty(default=False)
    wallCR7: BoolProperty(default=False)
    wallCR8: BoolProperty(default=False)
    wallCR9: BoolProperty(default=False)
    wallCR10: BoolProperty(default=False)

    # shelf location and size.
    # see "balcony" options for improved capabilities.
    # should limit x and z to wall boundaries
    ShelfX: FloatProperty(name="XOff", min=-WALL_MAX, max=WALL_MAX, default=-(WALL_DEF / 2), description="x origin")
    ShelfZ: FloatProperty(name="Base", min=-WALL_MAX, max=WALL_MAX, default=WALL_DEF, description="z origin")
    ShelfW: FloatProperty(name="Width", min=BLOCK_MIN, max=WALL_MAX, default=WALL_DEF, description="The Width of shelf area")
    # height seems to be double, check usage
    ShelfH: FloatProperty(name="Height", min=BLOCK_MIN, max=HALF_WALL, default=0.5, description="The Height of Shelf area")
    ShelfD: FloatProperty(name="Depth", min=BLOCK_MIN, max=WALL_MAX, default=BLOCK_DDEF, description="Depth of shelf")
    ShelfOut: BoolProperty(name="Out", default=True, description="Position outside of wall")

    wallBF1: BoolProperty(default=False, description="Front")
    wallBF2: BoolProperty(default=False)
    wallBF3: BoolProperty(default=False)
    wallBF4: BoolProperty(default=False)
    wallBF5: BoolProperty(default=False)
    wallBF6: BoolProperty(default=False)
    wallBF7: BoolProperty(default=False)
    wallBF8: BoolProperty(default=False)
    wallBF9: BoolProperty(default=False)
    wallBF10: BoolProperty(default=False)

    wallBL1: BoolProperty(default=False, description="Left")
    wallBL2: BoolProperty(default=False)
    wallBL3: BoolProperty(default=False)
    wallBL4: BoolProperty(default=False)
    wallBL5: BoolProperty(default=False)
    wallBL6: BoolProperty(default=False)
    wallBL7: BoolProperty(default=False)
    wallBL8: BoolProperty(default=False)
    wallBL9: BoolProperty(default=False)
    wallBL10: BoolProperty(default=False)

    wallBB1: BoolProperty(default=False, description="Back")
    wallBB2: BoolProperty(default=False)
    wallBB3: BoolProperty(default=False)
    wallBB4: BoolProperty(default=False)
    wallBB5: BoolProperty(default=False)
    wallBB6: BoolProperty(default=False)
    wallBB7: BoolProperty(default=False)
    wallBB8: BoolProperty(default=False)
    wallBB9: BoolProperty(default=False)
    wallBB10: BoolProperty(default=False)

    wallBR1: BoolProperty(default=False, description="Right")
    wallBR2: BoolProperty(default=False)
    wallBR3: BoolProperty(default=False)
    wallBR4: BoolProperty(default=False)
    wallBR5: BoolProperty(default=False)
    wallBR6: BoolProperty(default=False)
    wallBR7: BoolProperty(default=False)
    wallBR8: BoolProperty(default=False)
    wallBR9: BoolProperty(default=False)
    wallBR10: BoolProperty(default=False)

    # steps
    StepX: FloatProperty(name="XOff", min=-WALL_MAX, max=WALL_MAX, default=-(WALL_DEF / 2), description="x origin")
    StepZ: FloatProperty(name="Base", min=-WALL_MAX, max=WALL_MAX, default=0, description="z origin")
    StepW: FloatProperty(name="Width", min=BLOCK_MIN, max=WALL_MAX, default=WALL_DEF, description="Width of step area")
    StepH: FloatProperty(name="Height", min=BLOCK_MIN, max=WALL_MAX, default=WALL_DEF, description="Height of step area")
    StepD: FloatProperty(name="Depth", min=BLOCK_MIN, max=HALF_WALL, default=BLOCK_XDEF, description="Step offset (distance) from wall")
    StepV: FloatProperty(name="Riser", min=BLOCK_MIN, max=HALF_WALL, default=BLOCK_XDEF, description="Step height")
    StepT: FloatProperty(name="Tread", min=BLOCK_MIN, max=HALF_WALL, default=BLOCK_DDEF, description="Step footing/tread")
    StepL: BoolProperty(name="Slant", default=False, description="Step direction.")
    StepF: BoolProperty(name="Fill", default=False, description="Fill with supporting blocks")
    StepOut: BoolProperty(name="Out", default=False, description="Position outside of wall")

    wallSF1: BoolProperty(default=False, description="Front")
    wallSF2: BoolProperty(default=False)
    wallSF3: BoolProperty(default=False)
    wallSF4: BoolProperty(default=False)
    wallSF5: BoolProperty(default=False)
    wallSF6: BoolProperty(default=False)
    wallSF7: BoolProperty(default=False)
    wallSF8: BoolProperty(default=False)
    wallSF9: BoolProperty(default=False)
    wallSF10: BoolProperty(default=False)

    wallSL1: BoolProperty(default=False, description="Left")
    wallSL2: BoolProperty(default=False)
    wallSL3: BoolProperty(default=False)
    wallSL4: BoolProperty(default=False)
    wallSL5: BoolProperty(default=False)
    wallSL6: BoolProperty(default=False)
    wallSL7: BoolProperty(default=False)
    wallSL8: BoolProperty(default=False)
    wallSL9: BoolProperty(default=False)
    wallSL10: BoolProperty(default=False)

    wallSB1: BoolProperty(default=False, description="Back")
    wallSB2: BoolProperty(default=False)
    wallSB3: BoolProperty(default=False)
    wallSB4: BoolProperty(default=False)
    wallSB5: BoolProperty(default=False)
    wallSB6: BoolProperty(default=False)
    wallSB7: BoolProperty(default=False)
    wallSB8: BoolProperty(default=False)
    wallSB9: BoolProperty(default=False)
    wallSB10: BoolProperty(default=False)

    wallSR1: BoolProperty(default=False, description="Right")
    wallSR2: BoolProperty(default=False)
    wallSR3: BoolProperty(default=False)
    wallSR4: BoolProperty(default=False)
    wallSR5: BoolProperty(default=False)
    wallSR6: BoolProperty(default=False)
    wallSR7: BoolProperty(default=False)
    wallSR8: BoolProperty(default=False)
    wallSR9: BoolProperty(default=False)
    wallSR10: BoolProperty(default=False)

    # Experimental options
    # allow per wall and level?
    cXTest: BoolProperty(default=False)
    # wall shape modifiers
    # make the wall circular - if not curved it's a flat disc
    # Radiating from one point - round/disc; instead of square
    #    wallDisc=BoolProperty(default=False,description="Make wall disc")
    # Warp/slope/curve wall - abstract use only (except for dome use)
    wallSlope: BoolProperty(default=False, description="Curve wall")  # top to bottom mid
    CTunnel: BoolProperty(default=False, description="Tunnel wall")  # bottom to top mid
    # rotate tunnel?...
    CTower: BoolProperty(name='Tower', default=False)

    ##
    ####
    ############################################################################
    # Show the UI - present properties to user.
    # Display the toolbox options
    ############################################################################
    ####
    ##
    def draw(self, context):

        layout = self.layout

        box = layout.box()
        box.prop(self, 'ConstructTog')
        # Castle area.
        box = layout.box()
        row = box.row()
        row.prop(self, 'cBaseRGB', text='Base')
        row = box.row()
        row.prop(self, 'cBaseW')
        row.prop(self, 'cBaseD')
        # this is 0 until more complex settings allowed... like repeat or
        # per-level (like wall) selection.
        #        box.prop(self,'cBaseO') # vert offset from 3D cursor

        box.prop(self, 'cBaseT', text="Thickness")  # height/thickness of floor.
        row = box.row()
        row.prop(self, 'CBaseB')  # Blocks or slab
        if self.properties.CBaseB:
            row.prop(self, 'CBaseR', text='', icon="MESH_CIRCLE")  # Round
        box.prop(self, 'CLvls', text="Levels")  # number of floors.

        # block sizing
        box = layout.box()
        row = box.row()
        row.label(text='Blocks:')
        box.prop(self, 'blockX')
        box.prop(self, 'blockZ')
        box.prop(self, 'blockD')
        box.prop(self, 'Grout')
        box.prop(self, 'EdgeOffset')

        # "fixed" sizing unless variance enabled.
        row = box.row()
        row.prop(self, 'blockVar')  # randomize block sizing
        if self.properties.blockVar:
            row.prop(self, 'blockMerge')
            box.prop(self, 'blockHVar')
            box.prop(self, 'blockWVar')
            box.prop(self, 'blockDVar')

        box = layout.box()
        box.prop(self, 'CLvl', text="Level")  # current "Level" (UI parameter values).

        # Walls
        row = box.row()
        row.prop(self, 'wallRGB', text='Walls')
        row = box.row()  # which walls to generate - show current level value.
        row.prop(self, 'wallF' + str(self.properties.CLvl), text='', icon="TRIA_DOWN_BAR")
        row.prop(self, 'wallL' + str(self.properties.CLvl), text='', icon="TRIA_LEFT_BAR")
        row.prop(self, 'wallB' + str(self.properties.CLvl), text='', icon="TRIA_UP_BAR")
        row.prop(self, 'wallR' + str(self.properties.CLvl), text='', icon="TRIA_RIGHT_BAR")
        row = box.row()  # round wall option
        row.prop(self, 'wallFO' + str(self.properties.CLvl), text='', icon="MESH_CIRCLE")
        row.prop(self, 'wallLO' + str(self.properties.CLvl), text='', icon="MESH_CIRCLE")
        row.prop(self, 'wallBO' + str(self.properties.CLvl), text='', icon="MESH_CIRCLE")
        row.prop(self, 'wallRO' + str(self.properties.CLvl), text='', icon="MESH_CIRCLE")
        box.prop(self, 'wallH')
        if self.properties.CLvl > 1:  # Base is first level (always true)
            box.prop(self, 'CFloor' + str(self.properties.CLvl), text="Floor")  # floor for level.

        box.prop(self, 'wallOpView')  # View/edit wall modifiers

        # Door
        if self.properties.wallOpView == "1":
            #            box.prop(self,'doorRpt',text='Dupe')
            row = box.row()  # which walls have a Door
            row.prop(self, 'wallDF' + str(self.properties.CLvl), text='', icon="TRIA_DOWN_BAR")
            row.prop(self, 'wallDL' + str(self.properties.CLvl), text='', icon="TRIA_LEFT_BAR")
            row.prop(self, 'wallDB' + str(self.properties.CLvl), text='', icon="TRIA_UP_BAR")
            row.prop(self, 'wallDR' + str(self.properties.CLvl), text='', icon="TRIA_RIGHT_BAR")
            box.prop(self, 'wallDoorW')
            box.prop(self, 'wallDoorH')
            box.prop(self, 'wallDoorX')
            box.prop(self, 'doorBvl')

            box.prop(self, 'doorArch')
            if self.doorArch:
                box.prop(self, 'doorArchC')
                box.prop(self, 'doorArchT')

        # Window
        if self.properties.wallOpView == "2":
            #            box.prop(self,'wallPortRpt',text='Dupe')
            row = box.row()  # which walls have portal/window
            row.prop(self, 'wallPF' + str(self.properties.CLvl), text='', icon="TRIA_DOWN_BAR")
            row.prop(self, 'wallPL' + str(self.properties.CLvl), text='', icon="TRIA_LEFT_BAR")
            row.prop(self, 'wallPB' + str(self.properties.CLvl), text='', icon="TRIA_UP_BAR")
            row.prop(self, 'wallPR' + str(self.properties.CLvl), text='', icon="TRIA_RIGHT_BAR")
            row = box.row()
            row.prop(self, 'wallPortW')
            row.prop(self, 'wallPortH')
            box.prop(self, 'wallPortX')
            box.prop(self, 'wallPortZ')
            box.prop(self, 'wallPortBvl')
            box.label(text='Arch')
            row = box.row()
            row.prop(self, 'wallPortArchT')
            row.prop(self, 'wallPortArchB')

        # Slots
        if self.properties.wallOpView == "3":
            box.prop(self, 'SlotVRpt', text='Dupe')
            row = box.row()  # which walls have embrasures/slits
            row.prop(self, 'wallEF' + str(self.properties.CLvl), text='', icon="TRIA_DOWN_BAR")
            row.prop(self, 'wallEL' + str(self.properties.CLvl), text='', icon="TRIA_LEFT_BAR")
            row.prop(self, 'wallEB' + str(self.properties.CLvl), text='', icon="TRIA_UP_BAR")
            row.prop(self, 'wallER' + str(self.properties.CLvl), text='', icon="TRIA_RIGHT_BAR")
            box.prop(self, 'SlotVW')
            box.prop(self, 'SlotVH')
            box.prop(self, 'SlotVL')
            box.prop(self, 'SlotVZ')
            box.label(text='Arch')
            row = box.row()
            row.prop(self, 'slotVArchT')
            row.prop(self, 'slotVArchB')

        # Crenellation: gaps in top of wall, base of dome.
        if self.properties.wallOpView == "4":
            row = box.row()  # which walls have Crenellation
            row.prop(self, 'wallCF' + str(self.properties.CLvl), text='', icon="TRIA_DOWN_BAR")
            row.prop(self, 'wallCL' + str(self.properties.CLvl), text='', icon="TRIA_LEFT_BAR")
            row.prop(self, 'wallCB' + str(self.properties.CLvl), text='', icon="TRIA_UP_BAR")
            row.prop(self, 'wallCR' + str(self.properties.CLvl), text='', icon="TRIA_RIGHT_BAR")
            box.prop(self, 'CrenelXP')
            box.prop(self, 'CrenelZP')

        # Steps
        if self.properties.wallOpView == "5":
            row = box.row()
            row.prop(self, 'StepL')
            row.prop(self, 'StepF')
            row.prop(self, 'StepOut')
            row = box.row()  # which walls have steps
            row.prop(self, 'wallSF' + str(self.properties.CLvl), text='', icon="TRIA_DOWN_BAR")
            row.prop(self, 'wallSL' + str(self.properties.CLvl), text='', icon="TRIA_LEFT_BAR")
            row.prop(self, 'wallSB' + str(self.properties.CLvl), text='', icon="TRIA_UP_BAR")
            row.prop(self, 'wallSR' + str(self.properties.CLvl), text='', icon="TRIA_RIGHT_BAR")
            box.prop(self, 'StepX')
            box.prop(self, 'StepZ')
            box.prop(self, 'StepW')
            box.prop(self, 'StepH')
            box.prop(self, 'StepD')
            box.prop(self, 'StepV')
            box.prop(self, 'StepT')

        # Shelf/Balcony
        if self.properties.wallOpView == "6":
            box.prop(self, 'ShelfOut')
            row = box.row()  # which walls have a shelf
            row.prop(self, 'wallBF' + str(self.properties.CLvl), text='', icon="TRIA_DOWN_BAR")
            row.prop(self, 'wallBL' + str(self.properties.CLvl), text='', icon="TRIA_LEFT_BAR")
            row.prop(self, 'wallBB' + str(self.properties.CLvl), text='', icon="TRIA_UP_BAR")
            row.prop(self, 'wallBR' + str(self.properties.CLvl), text='', icon="TRIA_RIGHT_BAR")
            box.prop(self, 'ShelfX')
            box.prop(self, 'ShelfZ')
            box.prop(self, 'ShelfW')
            box.prop(self, 'ShelfH')
            box.prop(self, 'ShelfD')

        # Dome
        box = layout.box()
        row = box.row()
        row.prop(self, 'cDome')
        if self.properties.cDome:
            row.prop(self, 'cDomeRGB', text='')
            box.prop(self, 'cDomeH')
            box.prop(self, 'cDomeZ')
        # Oculus - opening in top of dome
        #            box.prop(self,'cDomeO')

        # abstract/experimental
        # Use "icon="MESH_CONE" for roof
        box = layout.box()
        row = box.row()
        row.prop(self, 'cXTest', text='Experimental')
        if self.properties.cXTest:
            box.prop(self, 'wallSlope', text='Curve')
            box.prop(self, 'CTunnel', text='Tunnel', icon="CURVE_DATA")
            box.prop(self, 'CTower', text='Tower', icon="CURVE_DATA")

    ##
    ####
    ############################################################################
    # Respond to UI - process the properties set by user.
        # Check and process UI settings to generate castle.
    ############################################################################
    ####
    ##

    def execute(self, context):

        global openingSpecs
        global dims
        # Limit UI settings relative to other parameters,
        #  set globals and effeciency variables.

        # current level cannot exceed level setting...
        if self.properties.CLvl > self.properties.CLvls:
            self.properties.CLvl = self.properties.CLvls

        castleScene = bpy.context.scene
        blockWidth = self.properties.blockX
        blockHeight = self.properties.blockZ
        blockDepth = self.properties.blockD

        # wall "area" must be at least 3 blocks.
        minWallW = blockWidth * 3  # min wall width/depth
        minWallH = blockHeight * 3  # min wall height

        if self.properties.cBaseW < minWallW:
            self.properties.cBaseW = minWallW
        CastleX = self.properties.cBaseW
        midWallW = CastleX / 2

        if self.properties.wallH < minWallH:
            self.properties.wallH = minWallH
        planeHL = self.properties.wallH
        planeHL2 = planeHL * 2
        # proportional crenel height, shared with roof positioning.
        crenelH = planeHL * self.properties.CrenelZP

        if self.properties.cBaseD < minWallW:
            self.properties.cBaseD = minWallW
        CastleD = self.properties.cBaseD
        midWallD = (CastleD + blockDepth) / 2
        #        midWallD=CastleD/2
        #        midWallD=(CastleD-blockDepth)/2

        # gap cannot reduce block below minimum.
        if self.properties.Grout > blockHeight / 2 - BLOCK_MIN:
            self.properties.Grout = blockHeight / 2 - BLOCK_MIN

        # Variance limit for minimum block height.
        # not quite right, but usuable.
        blockHMin = self.properties.Grout + BLOCK_MIN

        # floor "thickness" cannot exceed block height
        if self.properties.cBaseT > blockHeight:
            self.properties.cBaseT = blockHeight

        ############
        #
        if self.properties.cDome:
            # base can't be lower than floor
            # consider limiting base to roof or wall height by levels?
            domeLimit = self.properties.cBaseO + self.properties.cBaseT
            if self.properties.cDomeZ < domeLimit:
                self.properties.cDomeZ = domeLimit

            # base can't be higher than double wall height (per level)
            domeLimit = planeHL2 * self.properties.CLvls
            if self.properties.cDomeZ > domeLimit:
                self.properties.cDomeZ = domeLimit

            # height limit to twice smallest wall width/depth.
            if CastleD < CastleX:  # use least dimension for dome.
                domeLimit = CastleD * 2
            else:
                domeLimit = CastleX * 2

            if self.properties.cDomeH > domeLimit:
                self.properties.cDomeH = domeLimit
            domeMaxO = self.properties.cDomeH / 2

            # Dome Oculus (opening) can't be more than half dome height
            if self.properties.cDomeO > domeMaxO:
                self.properties.cDomeO = domeMaxO

        #
        ############
        #####
        #
        # After validating all the properties see if need to create...
        # @todo: fix so last object preserved... (i.e. changing levels).
        # No build if construct off
        if not self.properties.ConstructTog:
            # No build if construct off or just changing levels
            #        if not self.properties.ConstructTog or self.properties.curLvl!=self.properties.CLvl:
            #            self.properties.curLvl=self.properties.CLvl
            return {'FINISHED'}

        #
        #####
        ############
        #
        # rowprocessing() front/back wall, modified by sides and Dome.
        # this centers the wall, maybe add flag to center or offset from cursor...
        # if centerwall:
        dims['s'] = -midWallW
        dims['e'] = midWallW
        # else:
        #        dims['s'] = 0
        #        dims['e'] = CastleX

        dims['t'] = planeHL

        # block sizing
        settings['h'] = blockHeight
        settings['w'] = blockWidth
        settings['d'] = blockDepth

        if self.properties.blockVar:
            settings['hv'] = self.properties.blockHVar
            settings['wv'] = self.properties.blockWVar
            settings['dv'] = self.properties.blockDVar
        else:
            settings['hv'] = 0
            settings['wv'] = 0
            settings['dv'] = 0

        settings['sdv'] = blockWidth  # divisions in area.

        settings['g'] = self.properties.Grout

        settings['eoff'] = self.properties.EdgeOffset

        # when openings overlap they create inverse stonework - interesting but not the desired effect
        # if opening width == indent*2 the edge blocks fail (row of blocks cross opening) - bug.
        openingSpecs = []
        archTop = [0, 0]
        archBot = [0, 0]

        #
        ############
        #
        # Openings always set info; flag per wall, per level to enable.
        #
        ############
        #
        ############
        # Door
            # set locals
        # @todo: fix this....
        openZ = self.properties.cBaseT + 1  # track with floor - else 0

        if self.properties.doorArch:
            archTop[0] = self.properties.doorArchC
            archTop[1] = self.properties.doorArchT

        # set opening values
        openingSpecs += [{'a': False,
                          'w': self.properties.wallDoorW, 'h': self.properties.wallDoorH,
                          'x': self.properties.wallDoorX, 'z': openZ,
                          'n': self.properties.doorRpt, 'bvl': self.properties.doorBvl,
                          'v': archTop[0], 'vl':archBot[0], 't':archTop[1], 'tl':archBot[1]}]

        ############
        # Window
        archTop[0] = 0
        archTop[1] = 0
        archBot[0] = 0
        archBot[1] = 0

        if self.properties.wallPortArchT:
            archTop[0] = self.properties.wallPortW / 2
            archTop[1] = self.properties.wallPortW / 4

        if self.properties.wallPortArchB:
            archBot[0] = self.properties.wallPortW / 2
            archBot[1] = self.properties.wallPortW / 4

        # set opening values
        openingSpecs += [{'a': False,
                          'w': self.properties.wallPortW, 'h': self.properties.wallPortH,
                          'x': self.properties.wallPortX, 'z': self.properties.wallPortZ,
                          'n': self.properties.wallPortRpt, 'bvl': self.properties.wallPortBvl,
                          'v': archTop[0], 'vl':archBot[0], 't':archTop[1], 'tl':archBot[1]}]

        ############
        # crenellation, top wall gaps...
        # if crenel opening overlaps with arch opening it fills with blocks...
        archTop[0] = 0
        archTop[1] = 0
        # add bottom arch option?
        archBot[0] = 0
        archBot[1] = 0

        crenelW = CastleX * self.properties.CrenelXP  # Width % opening.
        crenelz = planeHL - (crenelH / 2)  # set bottom of opening

        crenelSpace = crenelW * 2  # assume standard spacing
        crenelRpt = True
        # set indent 0 (center) if opening is 50% or more of wall width, no repeat.
        if crenelSpace >= CastleX:
            crenelSpace = 0
            crenelRpt = False

        # set opening values
        openingSpecs += [{'a': False,
                          'w': crenelW, 'h': crenelH,
                          'x': crenelSpace, 'z': crenelz,
                          'n': crenelRpt, 'bvl': 0,
                          'v': archTop[0], 'vl':archBot[0], 't':archTop[1], 'tl':archBot[1]}]

        ############
        # Slots
        archTop[0] = 0
        archTop[1] = 0
        archBot[0] = 0
        archBot[1] = 0

        if self.properties.slotVArchT:
            archTop[0] = self.properties.SlotVW
            archTop[1] = self.properties.SlotVW / 2
        if self.properties.slotVArchB:
            archBot[0] = self.properties.SlotVW
            archBot[1] = self.properties.SlotVW / 2

        # set opening values
        openingSpecs += [{'a': False,
                          'w': self.properties.SlotVW, 'h': self.properties.SlotVH,
                          'x': self.properties.SlotVL, 'z': self.properties.SlotVZ,
                          'n': self.properties.SlotVRpt, 'bvl': 0,
                          'v': archTop[0], 'vl':archBot[0], 't':archTop[1], 'tl':archBot[1]}]

        ##
        ####
        ########################################################################
        # Process the user settings to generate castle.
        ########################################################################
        ####
        ##
        # Deselect all objects.
        bpy.ops.object.select_all(action='DESELECT')

        ############
        # Base/floor/foundation, main object for Castle, parent to all other elements.
        wallExtOpts = [False, False]  # no steps or shelf
        # @todo: offset door by floor height/thickness
        # @todo: replicate for "multi-floor" option-shared with roof.
        #  - will need openings (in plane) for stairs and such...
        settings['Slope'] = False  # no curve
        settings['eoff'] = 0  # no edgeing
        # need separate flag for floor/roof...
        settings['Radial'] = False

        baseMtl = uMatRGBSet('cBase_mat', self.cBaseRGB, matMod=True)

        baseDisc = False  # only when blocks and round...
        if self.properties.CBaseB:  # floor blocks
            baseDisc = self.properties.CBaseR  # rounded

        # set block "area": height, width, depth, and spacing for floor
        # - when rotated or disc shape, height is depth, depth is thickness.
        blockArea = [self.properties.cBaseD, self.properties.cBaseW, self.properties.cBaseT, self.properties.blockZ, settings['hv'], self.properties.Grout]

        # Block floor uses wall to generate... initialize location values.
        wallLoc = [castleScene.cursor_location.x, castleScene.cursor_location.y, castleScene.cursor_location.z]

        baseRotate = False  # rotate for blocks...
        if self.properties.CBaseB:  # make floor with blocks.
            saveBD = settings['d']  # put back when done with floor...
            saveBDV = settings['dv']
            settings['d'] = self.properties.cBaseT
            settings['dv'] = 0

            if baseDisc:  # make base disc shaped
                settings['Radial'] = True
                if self.properties.cBaseD < self.properties.cBaseW:  # narrowest extent
                    blockArea[0] = self.properties.cBaseD / 2
                else:
                    blockArea[0] = self.properties.cBaseW / 2

                wallLoc[1] += self.properties.cBaseW / 2  # adjust location for radius

            else:  # rotate if not disc.
                baseRotate = True

            castleObj = makeWallObj(self, castleScene, wallLoc, OBJ_N, blockArea, [], wallExtOpts, baseMtl)

            if baseRotate:
                castleObj.select_set(True)  # must select to rotate
                # rotate 90 backward
                bpy.ops.transform.rotate(value=-cPieHlf, constraint_axis=[True, False, False])
                bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
                castleObj.select_set(False)  # deselect after rotate else joined with others...

            settings['d'] = saveBD  # restore block values
            settings['dv'] = saveBDV

        else:  # make solid plane
            # set plane dimensions and location
            baseZ = self.properties.cBaseO
            baseT = baseZ + self.properties.cBaseT
            baseW = self.properties.cBaseW
            baseXO = -baseW / 2  # center
            baseXE = baseW / 2

            baseBounds = [baseXO, baseXE, baseZ, baseT, 0, self.properties.cBaseD]
            castleObj = makePlaneObj(OBJ_N, baseBounds, baseMtl, baseW)
            castleScene.objects.link(castleObj)  # must do for generation/rotation


        ####################
        # Make Floor and Walls
        wallMtl = uMatRGBSet('cWall_mat', self.wallRGB, matMod=True)

        # Block floor uses wall to generate... reset location values.
        wallLoc[1] = castleScene.cursor_location.y

        wallLvl = 0  # make per level as selected...
        while wallLvl < self.properties.CLvls:  # make castle levels
            if wallLvl == 0:
                floorLvl = False  # First floor is Castle base (parent).
                wallFLvl = self.properties.wallF1
                wallLLvl = self.properties.wallL1
                wallBLvl = self.properties.wallB1
                wallRLvl = self.properties.wallR1
                wallFOLvl = self.properties.wallFO1
                wallLOLvl = self.properties.wallLO1
                wallBOLvl = self.properties.wallBO1
                wallROLvl = self.properties.wallRO1
                wallDLvlF = self.properties.wallDF1
                wallDLvlL = self.properties.wallDL1
                wallDLvlB = self.properties.wallDB1
                wallDLvlR = self.properties.wallDR1
                wallPLvlF = self.properties.wallPF1
                wallPLvlL = self.properties.wallPL1
                wallPLvlB = self.properties.wallPB1
                wallPLvlR = self.properties.wallPR1
                wallELvlF = self.properties.wallEF1
                wallELvlL = self.properties.wallEL1
                wallELvlB = self.properties.wallEB1
                wallELvlR = self.properties.wallER1
                wallCLvlF = self.properties.wallCF1
                wallCLvlL = self.properties.wallCL1
                wallCLvlB = self.properties.wallCB1
                wallCLvlR = self.properties.wallCR1
                wallSLvlF = self.properties.wallSF1
                wallSLvlL = self.properties.wallSL1
                wallSLvlB = self.properties.wallSB1
                wallSLvlR = self.properties.wallSR1
                wallBLvlF = self.properties.wallBF1
                wallBLvlL = self.properties.wallBL1
                wallBLvlB = self.properties.wallBB1
                wallBLvlR = self.properties.wallBR1

            if wallLvl == 1:
                floorLvl = self.properties.CFloor2
                wallFLvl = self.properties.wallF2
                wallLLvl = self.properties.wallL2
                wallBLvl = self.properties.wallB2
                wallRLvl = self.properties.wallR2
                wallFOLvl = self.properties.wallFO2
                wallLOLvl = self.properties.wallLO2
                wallBOLvl = self.properties.wallBO2
                wallROLvl = self.properties.wallRO2
                wallDLvlF = self.properties.wallDF2
                wallDLvlL = self.properties.wallDL2
                wallDLvlB = self.properties.wallDB2
                wallDLvlR = self.properties.wallDR2
                wallPLvlF = self.properties.wallPF2
                wallPLvlL = self.properties.wallPL2
                wallPLvlB = self.properties.wallPB2
                wallPLvlR = self.properties.wallPR2
                wallELvlF = self.properties.wallEF2
                wallELvlL = self.properties.wallEL2
                wallELvlB = self.properties.wallEB2
                wallELvlR = self.properties.wallER2
                wallCLvlF = self.properties.wallCF2
                wallCLvlL = self.properties.wallCL2
                wallCLvlB = self.properties.wallCB2
                wallCLvlR = self.properties.wallCR2
                wallSLvlF = self.properties.wallSF2
                wallSLvlL = self.properties.wallSL2
                wallSLvlB = self.properties.wallSB2
                wallSLvlR = self.properties.wallSR2
                wallBLvlF = self.properties.wallBF2
                wallBLvlL = self.properties.wallBL2
                wallBLvlB = self.properties.wallBB2
                wallBLvlR = self.properties.wallBR2

            if wallLvl == 2:
                floorLvl = self.properties.CFloor3
                wallFLvl = self.properties.wallF3
                wallLLvl = self.properties.wallL3
                wallBLvl = self.properties.wallB3
                wallRLvl = self.properties.wallR3
                wallFOLvl = self.properties.wallFO3
                wallLOLvl = self.properties.wallLO3
                wallBOLvl = self.properties.wallBO3
                wallROLvl = self.properties.wallRO3
                wallDLvlF = self.properties.wallDF3
                wallDLvlL = self.properties.wallDL3
                wallDLvlB = self.properties.wallDB3
                wallDLvlR = self.properties.wallDR3
                wallPLvlF = self.properties.wallPF3
                wallPLvlL = self.properties.wallPL3
                wallPLvlB = self.properties.wallPB3
                wallPLvlR = self.properties.wallPR3
                wallELvlF = self.properties.wallEF3
                wallELvlL = self.properties.wallEL3
                wallELvlB = self.properties.wallEB3
                wallELvlR = self.properties.wallER3
                wallCLvlF = self.properties.wallCF3
                wallCLvlL = self.properties.wallCL3
                wallCLvlB = self.properties.wallCB3
                wallCLvlR = self.properties.wallCR3
                wallSLvlF = self.properties.wallSF3
                wallSLvlL = self.properties.wallSL3
                wallSLvlB = self.properties.wallSB3
                wallSLvlR = self.properties.wallSR3
                wallBLvlF = self.properties.wallBF3
                wallBLvlL = self.properties.wallBL3
                wallBLvlB = self.properties.wallBB3
                wallBLvlR = self.properties.wallBR3

            if wallLvl == 3:
                floorLvl = self.properties.CFloor4
                wallFLvl = self.properties.wallF4
                wallLLvl = self.properties.wallL4
                wallBLvl = self.properties.wallB4
                wallRLvl = self.properties.wallR4
                wallFOLvl = self.properties.wallFO4
                wallLOLvl = self.properties.wallLO4
                wallBOLvl = self.properties.wallBO4
                wallROLvl = self.properties.wallRO4
                wallDLvlF = self.properties.wallDF4
                wallDLvlL = self.properties.wallDL4
                wallDLvlB = self.properties.wallDB4
                wallDLvlR = self.properties.wallDR4
                wallPLvlF = self.properties.wallPF4
                wallPLvlL = self.properties.wallPL4
                wallPLvlB = self.properties.wallPB4
                wallPLvlR = self.properties.wallPR4
                wallELvlF = self.properties.wallEF4
                wallELvlL = self.properties.wallEL4
                wallELvlB = self.properties.wallEB4
                wallELvlR = self.properties.wallER4
                wallCLvlF = self.properties.wallCF4
                wallCLvlL = self.properties.wallCL4
                wallCLvlB = self.properties.wallCB4
                wallCLvlR = self.properties.wallCR4
                wallSLvlF = self.properties.wallSF4
                wallSLvlL = self.properties.wallSL4
                wallSLvlB = self.properties.wallSB4
                wallSLvlR = self.properties.wallSR4
                wallBLvlF = self.properties.wallBF4
                wallBLvlL = self.properties.wallBL4
                wallBLvlB = self.properties.wallBB4
                wallBLvlR = self.properties.wallBR4

            if wallLvl == 4:
                floorLvl = self.properties.CFloor5
                wallFLvl = self.properties.wallF5
                wallLLvl = self.properties.wallL5
                wallBLvl = self.properties.wallB5
                wallRLvl = self.properties.wallR5
                wallFOLvl = self.properties.wallFO5
                wallLOLvl = self.properties.wallLO5
                wallBOLvl = self.properties.wallBO5
                wallROLvl = self.properties.wallRO5
                wallDLvlF = self.properties.wallDF5
                wallDLvlL = self.properties.wallDL5
                wallDLvlB = self.properties.wallDB5
                wallDLvlR = self.properties.wallDR5
                wallPLvlF = self.properties.wallPF5
                wallPLvlL = self.properties.wallPL5
                wallPLvlB = self.properties.wallPB5
                wallPLvlR = self.properties.wallPR5
                wallELvlF = self.properties.wallEF5
                wallELvlL = self.properties.wallEL5
                wallELvlB = self.properties.wallEB5
                wallELvlR = self.properties.wallER5
                wallCLvlF = self.properties.wallCF5
                wallCLvlL = self.properties.wallCL5
                wallCLvlB = self.properties.wallCB5
                wallCLvlR = self.properties.wallCR5
                wallSLvlF = self.properties.wallSF5
                wallSLvlL = self.properties.wallSL5
                wallSLvlB = self.properties.wallSB5
                wallSLvlR = self.properties.wallSR5
                wallBLvlF = self.properties.wallBF5
                wallBLvlL = self.properties.wallBL5
                wallBLvlB = self.properties.wallBB5
                wallBLvlR = self.properties.wallBR5

            if wallLvl == 5:
                floorLvl = self.properties.CFloor6
                wallFLvl = self.properties.wallF6
                wallLLvl = self.properties.wallL6
                wallBLvl = self.properties.wallB6
                wallRLvl = self.properties.wallR6
                wallFOLvl = self.properties.wallFO6
                wallLOLvl = self.properties.wallLO6
                wallBOLvl = self.properties.wallBO6
                wallROLvl = self.properties.wallRO6
                wallDLvlF = self.properties.wallDF6
                wallDLvlL = self.properties.wallDL6
                wallDLvlB = self.properties.wallDB6
                wallDLvlR = self.properties.wallDR6
                wallPLvlF = self.properties.wallPF6
                wallPLvlL = self.properties.wallPL6
                wallPLvlB = self.properties.wallPB6
                wallPLvlR = self.properties.wallPR6
                wallELvlF = self.properties.wallEF6
                wallELvlL = self.properties.wallEL6
                wallELvlB = self.properties.wallEB6
                wallELvlR = self.properties.wallER6
                wallCLvlF = self.properties.wallCF6
                wallCLvlL = self.properties.wallCL6
                wallCLvlB = self.properties.wallCB6
                wallCLvlR = self.properties.wallCR6
                wallSLvlF = self.properties.wallSF6
                wallSLvlL = self.properties.wallSL6
                wallSLvlB = self.properties.wallSB6
                wallSLvlR = self.properties.wallSR6
                wallBLvlF = self.properties.wallBF6
                wallBLvlL = self.properties.wallBL6
                wallBLvlB = self.properties.wallBB6
                wallBLvlR = self.properties.wallBR6

            if wallLvl == 6:
                floorLvl = self.properties.CFloor7
                wallFLvl = self.properties.wallF7
                wallLLvl = self.properties.wallL7
                wallBLvl = self.properties.wallB7
                wallRLvl = self.properties.wallR7
                wallFOLvl = self.properties.wallFO7
                wallLOLvl = self.properties.wallLO7
                wallBOLvl = self.properties.wallBO7
                wallROLvl = self.properties.wallRO7
                wallDLvlF = self.properties.wallDF7
                wallDLvlL = self.properties.wallDL7
                wallDLvlB = self.properties.wallDB7
                wallDLvlR = self.properties.wallDR7
                wallPLvlF = self.properties.wallPF7
                wallPLvlL = self.properties.wallPL7
                wallPLvlB = self.properties.wallPB7
                wallPLvlR = self.properties.wallPR7
                wallELvlF = self.properties.wallEF7
                wallELvlL = self.properties.wallEL7
                wallELvlB = self.properties.wallEB7
                wallELvlR = self.properties.wallER7
                wallCLvlF = self.properties.wallCF7
                wallCLvlL = self.properties.wallCL7
                wallCLvlB = self.properties.wallCB7
                wallCLvlR = self.properties.wallCR7
                wallSLvlF = self.properties.wallSF7
                wallSLvlL = self.properties.wallSL7
                wallSLvlB = self.properties.wallSB7
                wallSLvlR = self.properties.wallSR7
                wallBLvlF = self.properties.wallBF7
                wallBLvlL = self.properties.wallBL7
                wallBLvlB = self.properties.wallBB7
                wallBLvlR = self.properties.wallBR7

            if wallLvl == 7:
                floorLvl = self.properties.CFloor38
                wallFLvl = self.properties.wallF8
                wallLLvl = self.properties.wallL8
                wallBLvl = self.properties.wallB8
                wallRLvl = self.properties.wallR8
                wallFOLvl = self.properties.wallFO8
                wallLOLvl = self.properties.wallLO8
                wallBOLvl = self.properties.wallBO8
                wallROLvl = self.properties.wallRO8
                wallDLvlF = self.properties.wallDF8
                wallDLvlL = self.properties.wallDL8
                wallDLvlB = self.properties.wallDB8
                wallDLvlR = self.properties.wallDR8
                wallPLvlF = self.properties.wallPF8
                wallPLvlL = self.properties.wallPL8
                wallPLvlB = self.properties.wallPB8
                wallPLvlR = self.properties.wallPR8
                wallELvlF = self.properties.wallEF8
                wallELvlL = self.properties.wallEL8
                wallELvlB = self.properties.wallEB8
                wallELvlR = self.properties.wallER8
                wallCLvlF = self.properties.wallCF8
                wallCLvlL = self.properties.wallCL8
                wallCLvlB = self.properties.wallCB8
                wallCLvlR = self.properties.wallCR8
                wallSLvlF = self.properties.wallSF8
                wallSLvlL = self.properties.wallSL8
                wallSLvlB = self.properties.wallSB8
                wallSLvlR = self.properties.wallSR8
                wallBLvlF = self.properties.wallBF8
                wallBLvlL = self.properties.wallBL8
                wallBLvlB = self.properties.wallBB8
                wallBLvlR = self.properties.wallBR8

            if wallLvl == 8:
                floorLvl = self.properties.CFloor9
                wallFLvl = self.properties.wallF9
                wallLLvl = self.properties.wallL9
                wallBLvl = self.properties.wallB9
                wallRLvl = self.properties.wallR9
                wallFOLvl = self.properties.wallFO9
                wallLOLvl = self.properties.wallLO9
                wallBOLvl = self.properties.wallBO9
                wallROLvl = self.properties.wallRO9
                wallDLvlF = self.properties.wallDF9
                wallDLvlL = self.properties.wallDL9
                wallDLvlB = self.properties.wallDB9
                wallDLvlR = self.properties.wallDR9
                wallPLvlF = self.properties.wallPF9
                wallPLvlL = self.properties.wallPL9
                wallPLvlB = self.properties.wallPB9
                wallPLvlR = self.properties.wallPR9
                wallELvlF = self.properties.wallEF9
                wallELvlL = self.properties.wallEL9
                wallELvlB = self.properties.wallEB9
                wallELvlR = self.properties.wallER9
                wallCLvlF = self.properties.wallCF9
                wallCLvlL = self.properties.wallCL9
                wallCLvlB = self.properties.wallCB9
                wallCLvlR = self.properties.wallCR9
                wallSLvlF = self.properties.wallSF9
                wallSLvlL = self.properties.wallSL9
                wallSLvlB = self.properties.wallSB9
                wallSLvlR = self.properties.wallSR9
                wallBLvlF = self.properties.wallBF9
                wallBLvlL = self.properties.wallBL9
                wallBLvlB = self.properties.wallBB9
                wallBLvlR = self.properties.wallBR9

            if wallLvl == 9:
                floorLvl = self.properties.CFloor10
                wallFLvl = self.properties.wallF10
                wallLLvl = self.properties.wallL10
                wallBLvl = self.properties.wallB10
                wallRLvl = self.properties.wallR10
                wallFOLvl = self.properties.wallFO10
                wallLOLvl = self.properties.wallLO10
                wallBOLvl = self.properties.wallBO10
                wallROLvl = self.properties.wallRO10
                wallDLvlF = self.properties.wallDF10
                wallDLvlL = self.properties.wallDL10
                wallDLvlB = self.properties.wallDB10
                wallDLvlR = self.properties.wallDR10
                wallPLvlF = self.properties.wallPF10
                wallPLvlL = self.properties.wallPL10
                wallPLvlB = self.properties.wallPB10
                wallPLvlR = self.properties.wallPR10
                wallELvlF = self.properties.wallEF10
                wallELvlL = self.properties.wallEL10
                wallELvlB = self.properties.wallEB10
                wallELvlR = self.properties.wallER10
                wallCLvlF = self.properties.wallCF10
                wallCLvlL = self.properties.wallCL10
                wallCLvlB = self.properties.wallCB10
                wallCLvlR = self.properties.wallCR10
                wallSLvlF = self.properties.wallSF10
                wallSLvlL = self.properties.wallSL10
                wallSLvlB = self.properties.wallSB10
                wallSLvlR = self.properties.wallSR10
                wallBLvlF = self.properties.wallBF10
                wallBLvlL = self.properties.wallBL10
                wallBLvlB = self.properties.wallBB10
                wallBLvlR = self.properties.wallBR10

            levelBase = planeHL * wallLvl

            floorDisc = False  # affects floor and wall positioning.
            if self.properties.CBaseB:  # if blocks for floor can make disc.
                floorDisc = self.properties.CBaseR

            ############
            # make floor for each level
            if floorLvl:
                objName = OBJ_CF + str(wallLvl)

                # set plane dimensions and location
                floorBase = levelBase
                floorTop = floorBase + self.properties.cBaseT
                floorPW = self.properties.cBaseW
                floorD = self.properties.cBaseD
                floorXO = -floorPW / 2  # center
                floorXE = floorPW / 2
                floorBounds = [floorXO, floorXE, floorBase, floorTop, 0, floorD]

                floorObj = makePlaneObj(objName, floorBounds, baseMtl, floorPW)

                # adjust floor location for 3D cursor since parented to Base...
                yMod = castleScene.cursor_location.y
                if floorDisc:  # make a disc shaped floor
                    yMod += self.properties.cBaseD / 2
                floorObj.location.x -= castleScene.cursor_location.x
                floorObj.location.y -= yMod
                floorObj.location.z -= castleScene.cursor_location.z

                castleScene.objects.link(floorObj)  # must do for generation/rotation

                floorObj.parent = castleObj  # Connect to parent

            ############
            # make walls for each level
            wallSides = [wallFLvl, wallLLvl, wallBLvl, wallRLvl]
            # Wall modifiers, per level, per wall (FBLR not FLBR order to match wall build sequence).
            wallMods = [[wallDLvlF, wallPLvlF, wallELvlF, wallCLvlF, wallSLvlF, wallBLvlF, wallFOLvl],
                        [wallDLvlB, wallPLvlB, wallELvlB, wallCLvlB, wallSLvlB, wallBLvlB, wallBOLvl],
                        [wallDLvlL, wallPLvlL, wallELvlL, wallCLvlL, wallSLvlL, wallBLvlL, wallLOLvl],
                        [wallDLvlR, wallPLvlR, wallELvlR, wallCLvlR, wallSLvlR, wallBLvlR, wallROLvl]
                        ]

            wallLoc[2] = levelBase  # each segment base...
            makeWalls(self, castleScene, castleObj, wallSides, wallMods, wallLoc, wallMtl, wallLvl, floorDisc)
            wallLvl += 1

        ####################
        # Make "Tower"
        if self.properties.cXTest and self.properties.CTower:
            # no steps or shelf for tower...
            wallExtOpts[0] = False
            wallExtOpts[1] = False

            settings['Slope'] = True  # force curvature

            dims['s'] = 0.0  # radial origin
            dims['e'] = CastleX / 2  # effective tower height; affects radius.

            # set block "area": height, width, depth, and spacing.
            blockArea = [dims['e'], CastleX, blockDepth, self.properties.blockZ, settings['hv'], self.properties.Grout]

            # Make "tower" wall.
            wallLoc[0] = 0
            wallLoc[1] = 0
            wallLoc[2] = castleScene.cursor_location.z

            # generate tower...
            cTower1Obj = makeWallObj(self, castleScene, wallLoc, "CTower1", blockArea, [], wallExtOpts, wallMtl)

            cTower1Obj.select_set(True)  # must select to rotate
            # rotate 90 forward (face plant)...
            #            bpy.ops.transform.rotate(value=cPieHlf,constraint_axis=[True,False,False])
            # rotate 90 ccw along side
            bpy.ops.transform.rotate(value=-cPieHlf, constraint_axis=[False, True, False])
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
            cTower1Obj.select_set(False)  # deselect after rotate else joined with others...

            cTower1Obj.parent = castleObj  # Connect to parent

        ####################
        # Make "Dome"
        settings['Radial'] = self.properties.cDome
        if self.properties.cDome:
            # no steps or shelf for dome...
            wallExtOpts[0] = False
            wallExtOpts[1] = False

            settings['Slope'] = True  # force curvature
            settings['sdv'] = 0.12

            wallLoc[0] = castleScene.cursor_location.x
            wallLoc[1] = midWallD
            wallLoc[2] = self.properties.cDomeZ

            domeMtl = uMatRGBSet('cDome_mat', self.cDomeRGB, matMod=True)

            # set block "area": height, width, depth, and spacing.
            blockArea = [self.properties.cDomeH, CastleX, blockDepth, self.properties.blockZ, settings['hv'], self.properties.Grout]

            # eliminate to allow user control for start/completion by width setting.
            dims['s'] = 0.0  # complete radial

            if midWallD < midWallW:  # use shortest dimension for dome.
                dims['e'] = midWallD
            else:
                dims['e'] = midWallW

            # generate dome...
            cDomeObj = makeWallObj(self, castleScene, wallLoc, "cDome", blockArea, [], wallExtOpts, domeMtl)

            yMod = 0  # shift "location" as needed...
            if floorDisc:  # make a disc shaped floor
                yMod -= (CastleD + blockDepth) / 2
            cDomeObj.location.y += yMod

            cDomeObj.parent = castleObj  # Connect to parent

        castleObj.select_set(True)
        context.view_layer.objects.active = castleObj

        return {'FINISHED'}

################################################################################


####################
#
    # Walls
#
# when variations or openings are selected different block rows are
# generated for each wall; edges/ends don't match.
#
####################
def makeWalls(sRef, objScene, objParent, objSides, objMods, objLoc, objMat, objLvl, floorDisc):

    wallExtOpts = [False, False]  # no steps or shelf

    WobjH = sRef.properties.wallH
    WobjW = sRef.properties.cBaseW
    WobjY = sRef.properties.cBaseD
    WobjD = sRef.properties.blockD

    segWidth = sRef.properties.blockX

    # center wall...
    midWallD = (WobjY + WobjD) / 2
    midWallW = (WobjW + WobjD) / 2

    settings['eoff'] = sRef.properties.EdgeOffset
    settings['sdv'] = sRef.properties.blockX

    settings['Slope'] = False
    if sRef.properties.cXTest:
        if sRef.properties.CTunnel:
            settings['Slope'] = True  # force curve
        else:
            settings['Slope'] = sRef.properties.wallSlope  # user select curve walls...

    # passed as params since modified by wall and dome...
    settings['StepsB'] = sRef.properties.StepF  # fill under with blocks
    settings['StepsL'] = sRef.properties.StepL  # up to left
    settings['StepsO'] = sRef.properties.StepOut  # outside of wall

    # set block "area": height, width, depth, and spacing for front and back walls.
    blockArea = [WobjH, WobjW, WobjD, sRef.properties.blockZ, settings['hv'], sRef.properties.Grout]
    dims['s'] = -midWallW
    dims['e'] = midWallW

    yMod = 0  # shift front/back "location" as needed...
    if floorDisc:  # make a disc shaped floor
        yMod = WobjY

    ####################
    if objSides[0]:  # Make "front" wall
        objName = OBJ_WF + str(objLvl)

        wallRound = objMods[0][6]  # round (disc) wall...

        # adjust sizing for round wall else ensure full height.
        if wallRound:
            settings['Radial'] = True
            blockArea[0] = WobjH / 2  # half height for radius
        else:
            settings['Radial'] = False  # disable disc
            blockArea[0] = WobjH  # ensure full height

        wallSteps = False
        wallShelf = False
        wallHoles = []

        openingSpecs[OP_DOOR]['a'] = objMods[0][0]  # door
        openingSpecs[OP_PORT]['a'] = objMods[0][1]  # window
        openingSpecs[OP_SLOT]['a'] = objMods[0][2]  # slot
        openingSpecs[OP_CREN]['a'] = objMods[0][3]  # crenel
        wallExtOpts[0] = objMods[0][4]  # steps
        wallExtOpts[1] = objMods[0][5]  # shelf

        wallHoles = openList(sRef)

        objLoc[0] = 0
        if sRef.properties.cXTest and sRef.properties.CTunnel:
            objLoc[1] = WobjY / 2
        else:
            objLoc[1] = 0

        objLoc[1] -= yMod / 2  # offset for disc

        # generate wall...
        cFrontObj = makeWallObj(sRef, objScene, objLoc, objName, blockArea, wallHoles, wallExtOpts, objMat)
        cFrontObj.parent = objParent  # Connect to parent

        if wallRound:  # rotate 90 forward if round/disc
            cFrontObj.select_set(True)  # must select to rotate
            bpy.ops.transform.rotate(value=cPieHlf, constraint_axis=[True, False, False])
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
            cFrontObj.location.z += WobjH / 2  # adjust vertical after rotate for radius
            cFrontObj.select_set(False)  # deselect after rotate else joined with others...

    ####################
    if objSides[2]:  # Make "back" wall
        objName = OBJ_WB + str(objLvl)

        wallRound = objMods[1][6]  # round (disc) wall...

        # adjust sizing for round wall else ensure full height.
        if wallRound:
            settings['Radial'] = True
            blockArea[0] = WobjH / 2  # half height for radius
        else:
            settings['Radial'] = False  # disable disc
            blockArea[0] = WobjH  # ensure full height

        wallSteps = False
        wallShelf = False
        wallHoles = []

        openingSpecs[OP_DOOR]['a'] = objMods[1][0]  # door
        openingSpecs[OP_PORT]['a'] = objMods[1][1]  # window
        openingSpecs[OP_SLOT]['a'] = objMods[1][2]  # slot
        openingSpecs[OP_CREN]['a'] = objMods[1][3]  # crenel
        wallExtOpts[0] = objMods[1][4]  # steps
        wallExtOpts[1] = objMods[1][5]  # shelf

        wallHoles = openList(sRef)

        objLoc[0] = 0
        if sRef.properties.cXTest and sRef.properties.CTunnel:
            objLoc[1] = WobjY / 2
        else:
            objLoc[1] = WobjY

        objLoc[1] -= yMod / 2  # offset for floor disc

        # generate wall...
        cBackObj = makeWallObj(sRef, objScene, objLoc, objName, blockArea, wallHoles, wallExtOpts, objMat)
        cBackObj.parent = objParent  # Connect to parent

        cBackObj.select_set(True)  # must select to rotate

        # rotate to "reverse" face of wall, else just a mirror of front.
        bpy.ops.transform.rotate(value=cPie, constraint_axis=[False, False, True])
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

        if wallRound:  # rotate 90 forward
            bpy.ops.transform.rotate(value=cPieHlf, constraint_axis=[True, False, False])
            cBackObj.location.z += WobjH / 2  # adjust vertical after rotate for radius

        cBackObj.select_set(False)  # de-select after rotate else joined with others...

    ####################
    # set block "area": height, width, depth, and spacing for side walls...
    blockArea = [WobjH, WobjY - segWidth * 2, WobjD, sRef.properties.blockZ, settings['hv'], sRef.properties.Grout]
    #    blockArea=[WobjH,WobjY-segWidth,WobjD,sRef.properties.blockZ,settings['hv'],sRef.properties.Grout]
    #    blockArea=[WobjH,WobjY,WobjD,sRef.properties.blockZ,settings['hv'],sRef.properties.Grout]
    # rowprocessing() side walls
    dims['s'] = -midWallD
    dims['e'] = midWallD
    ####################

    ####################
    if objSides[1]:  # Make "Left" wall
        objName = OBJ_WL + str(objLvl)

        wallRound = objMods[2][6]  # round (disc) wall...

        # adjust sizing for round wall else ensure full height.
        if wallRound:
            settings['Radial'] = True
            blockArea[0] = WobjH / 2  # half height for radius
        else:
            settings['Radial'] = False  # disable disc
            blockArea[0] = WobjH  # ensure full height

        wallSteps = False
        wallShelf = False
        wallHoles = []

        openingSpecs[OP_DOOR]['a'] = objMods[2][0]  # door
        openingSpecs[OP_PORT]['a'] = objMods[2][1]  # window
        openingSpecs[OP_SLOT]['a'] = objMods[2][2]  # slot
        # radius/round sizing wrong when crenel selected...
        openingSpecs[OP_CREN]['a'] = objMods[2][3]  # crenel
        wallExtOpts[0] = objMods[2][4]  # steps
        wallExtOpts[1] = objMods[2][5]  # shelf

        wallHoles = openList(sRef)

        if sRef.properties.cXTest and sRef.properties.CTunnel:
            objLoc[0] = 0
        else:
            objLoc[0] = -midWallW

        if floorDisc:  # make a disc shaped floor
            objLoc[1] = 0
        else:
            objLoc[1] = midWallD - (WobjD / 2)
        #        objLoc[1]=midWallD

        # generate wall...
        cSideLObj = makeWallObj(sRef, objScene, objLoc, objName, blockArea, wallHoles, wallExtOpts, objMat)
        cSideLObj.parent = objParent  # Connect to parent

        cSideLObj.select_set(True)  # must select to rotate
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

        if wallRound:  # rotate 90 forward
            bpy.ops.transform.rotate(value=cPieHlf, constraint_axis=[True, False, False])
            cSideLObj.location.z += WobjH / 2  # adjust vertical after rotate for radius

        if sRef.properties.cXTest and sRef.properties.CTunnel:
            # rotate 90 horizontal, ccw...
            bpy.ops.transform.rotate(value=cPieHlf, constraint_axis=[False, False, True])
        else:
            # rotate 90 horizontal, cw...
            bpy.ops.transform.rotate(value=-cPieHlf, constraint_axis=[False, False, True])
        # rotate 90 forward (face plant)...
        #            bpy.ops.transform.rotate(value=cPieHlf,constraint_axis=[True,False,False])
        # rotate 90 cw along side
        #            bpy.ops.transform.rotate(value=cPieHlf,constraint_axis=[False,True,False])

        cSideLObj.select_set(False)  # deselect after rotate else joined with others...


    ####################
    if objSides[3]:  # Make "Right" wall
        objName = OBJ_WR + str(objLvl)

        wallRound = objMods[3][6]  # round (disc) wall...

        # adjust sizing for round wall else ensure full height.
        if wallRound:
            settings['Radial'] = True
            blockArea[0] = WobjH / 2  # half height for radius
        else:
            settings['Radial'] = False  # disable disc
            blockArea[0] = WobjH  # ensure full height

        wallSteps = False
        wallShelf = False
        wallHoles = []

        openingSpecs[OP_DOOR]['a'] = objMods[3][0]  # door
        openingSpecs[OP_PORT]['a'] = objMods[3][1]  # window
        openingSpecs[OP_SLOT]['a'] = objMods[3][2]  # slot
        openingSpecs[OP_CREN]['a'] = objMods[3][3]  # crenel
        wallExtOpts[0] = objMods[3][4]  # steps
        wallExtOpts[1] = objMods[3][5]  # shelf

        wallHoles = openList(sRef)

        if sRef.properties.cXTest and sRef.properties.CTunnel:
            objLoc[0] = 0
        else:
            objLoc[0] = midWallW

        if floorDisc:  # make a disc shaped floor
            objLoc[1] = 0
        else:
            objLoc[1] = midWallD - (WobjD / 2)

        cSideRObj = makeWallObj(sRef, objScene, objLoc, objName, blockArea, wallHoles, wallExtOpts, objMat)
        cSideRObj.parent = objParent  # Connect to parent
        #        objScene.objects.active=cSideRObj

        cSideRObj.select_set(True)  # must select to rotate
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

        if wallRound:  # rotate 90 forward
            bpy.ops.transform.rotate(value=cPieHlf, constraint_axis=[True, False, False])
            cSideRObj.location.z += WobjH / 2  # adjust vertical after rotate for radius

        if sRef.properties.cXTest and sRef.properties.CTunnel:
            # rotate 90 horizontal, cw...
            bpy.ops.transform.rotate(value=-cPieHlf, constraint_axis=[False, False, True])
        # rotate 90 horizontal, ccw...
        else:
            bpy.ops.transform.rotate(value=cPieHlf, constraint_axis=[False, False, True])
        # rotate 90 forward (face plant)...
        #        bpy.ops.transform.rotate(value=cPieHlf,constraint_axis=[True,False,False])
        # rotate 90 cw along side
        #        bpy.ops.transform.rotate(value=cPieHlf,constraint_axis=[False,True,False])

        cSideRObj.select_set(False)  # deselect after rotate...

        return  # all done, is automatic, just a matter of detail/protocol.


################################################################################

def makeWallObj(sRef, objScene, objLoc, objName, blockArea, openList, wallExtOpts, objMat):

    settings['Steps'] = wallExtOpts[0]
    settings['Shelf'] = wallExtOpts[1]

    meshVs, meshFs = wallBuild(sRef, wallPlan(sRef, blockArea, openList), openList)

    newMesh = bpy.data.meshes.new(objName)
    newMesh.from_pydata(meshVs, [], meshFs)
    # doesn't seem to matter...
    #    newMesh.update(calc_edges=True)
    newMesh.materials.append(objMat)

    newObj = bpy.data.objects.new(objName, newMesh)
    newObj.location.x = objLoc[0]
    newObj.location.y = objLoc[1]
    newObj.location.z = objLoc[2]

    objScene.objects.link(newObj)  # must do for generation/rotation

    return newObj


########################
# Generate simple "plane" for floor objects.
#
# objArea[leftX,rightX,zBase,zTop,0,yDepth]
# objDiv will subdivide plane based on sizing;
#  - see MakeABlock(objArea,objDiv) for details.
#
def makePlaneObj(objName, objArea, objMat, objDiv):
    objVs = []
    objFs = []

    objVs, objFs = MakeABlock(objArea, objDiv)

    objMesh = bpy.data.meshes.new(objName)
    objMesh.from_pydata(objVs, [], objFs)
    objMesh.update()
    #    objMesh.update(calc_edges=True) # doesn't seem to matter...
    objMesh.materials.append(objMat)

    newObj = bpy.data.objects.new(objName, objMesh)
    newObj.location = bpy.context.scene.cursor_location

    return newObj


################################################################################
################
########################
##
#
# Blocks module/script inclusion
# - to be reduced significantly.
##
# Module notes:
#
# consider removing wedge crit for small "c" and "cl" values
# wrap around for openings on radial stonework?
# repeat for opening doesn't distribute evenly when radialized
#  - see wrap around note above.
# if opening width == indent*2 the edge blocks fail (row of blocks cross opening).
# if block width variance is 0, and edging is on, right edge blocks create a "vertical seam".
#
##
#######################
################
################################################################################
##


###################################
#
# create lists of blocks.
#
# blockArea defines the "space" (vertical, horizontal, depth) to fill,
#  and provides block height, variation, and gap/grout. May affect "door" opening.
#
# holeList identifies "openings" in area.
#
# Returns: list of rows.
#  rows = [[center height,row height,edge offset],[...]]
#
def wallPlan(sRef, blockArea, holeList):

    rows = []

    blockAreaZ = blockArea[0]
    blockAreaX = blockArea[1]
    blockAreaY = blockArea[2]
    blockHMax = blockArea[3]
    blockHVar = blockArea[4]
    blockGap = blockArea[5]
    # this is wrong! should be...?
    blockHMin = BLOCK_MIN + blockGap

    # no variation for slopes so walls match curvature
    if sRef.properties.cXTest:
        if sRef.properties.wallSlope or sRef.properties.CTunnel:
            blockHVar = 0

    rowHMin = blockHMin
    # alternate rowHMin=blockHMax-blockHVar+blockGap

    # splits are a row division, for openings
    splits = [0]  # split bottom row
    # add a split for each critical point on each opening
    for hole in holeList:
        splits += hole.crits()
    # and, a split for the top row
    splits.append(blockAreaZ)
    splits.sort()  # needed?

    # divs are the normal old row divisions, add them between the top and bottom split
    # what's with "[1:-1]" at end????
    divs = fill(splits[0], splits[-1], blockHMax, blockHMin, blockHVar)[1:-1]

    # remove the divisions that are too close to the splits, so we don't get tiny thin rows
    for i in range(len(divs) - 1, -1, -1):
        for j in range(len(splits)):
            if abs(divs[i] - splits[j]) < rowHMin:
                del(divs[i])
                break

    # now merge the divs and splits lists
    divs += splits
    divs.sort()

    # trim the rows to the bottom and top of the wall
    if divs[0] < 0:
        divs[:1] = []
    if divs[-1] > blockAreaZ:
        divs[-1:] = []

    # process each row
    divCount = len(divs) - 1  # number of divs to check
    divCheck = 0  # current div entry

    while divCheck < divCount:
        RowZ = (divs[divCheck] + divs[divCheck + 1]) / 2
        RowHeight = divs[divCheck + 1] - divs[divCheck] - blockGap
        rowEdge = settings['eoff'] * (fmod(divCheck, 2) - 0.5)

        if RowHeight < rowHMin:  # skip row if too shallow
            del(divs[divCheck + 1])  # delete next div entry
            divCount -= 1  # Adjust count for removed div entry.
            continue

        rows.append(rowOb(RowZ, RowHeight, rowEdge))

        divCheck += 1  # on to next div entry

    # set up opening object to handle the edges of the wall
    WallBoundaries = OpeningInv((dims['s'] + dims['e']) / 2, blockAreaZ / 2, blockAreaX, blockAreaZ)

    # Go over each row in the list, set up edge blocks and block sections
    for rownum in range(len(rows)):
        rowProcessing(rows[rownum], holeList, WallBoundaries)

    return rows


################################################################################
#
# Build the wall, based on rows, "holeList", and parameters;
#     geometry for the blocks, arches, steps, platforms...
#
# Return: verts and faces for wall object.
#
def wallBuild(sRef, rows, holeList):

    wallVs = []
    wallFs = []

    AllBlocks = []

    # create local references for anything that's used more than once...
    rowCount = len(rows)

    wallTop = rows[rowCount - 1].z
    #    wallTop=sRef.properties.wallH
    wallTop2 = wallTop * 2

    wallDome = settings['Radial']
    wallSlope = settings['Slope']

    blockWidth = sRef.properties.blockX

    blockGap = sRef.properties.Grout
    halfGrout = blockGap / 2  # half grout for block size modifier
    blockHMin = BLOCK_MIN + blockGap

    blockDhalf = settings['d'] / 2  # offset by half block depth to match UI setting

    for rowidx in range(rowCount):  # add blocks for each row.
        rows[rowidx].FillBlocks()

    if sRef.properties.blockVar and sRef.properties.blockMerge:  # merge (vertical) blocks in close proximity...
        blockSpace = blockGap
        for rowidx in range(rowCount - 1):
            if wallDome:
                blockSpace = blockGap / (wallTop * sin(abs(rows[rowidx].z) * cPie / wallTop2))
            #            else: blockSpace=blockGap/(abs(rows[rowidx].z)) # make it flat

            idxThis = len(rows[rowidx].BlocksNorm[:]) - 1
            idxThat = len(rows[rowidx + 1].BlocksNorm[:]) - 1

            while True:
                # end loop when either array idx wraps
                if idxThis < 0 or idxThat < 0:
                    break

                blockThis = rows[rowidx].BlocksNorm[idxThis]
                blockThat = rows[rowidx + 1].BlocksNorm[idxThat]

                cx, cz, cw, ch, cd = blockThis[:5]
                ox, oz, ow, oh, od = blockThat[:5]

                if (abs(cw - ow) < blockSpace) and (abs(cx - ox) < blockSpace):
                    if cw > ow:
                        BlockW = ow
                    else:
                        BlockW = cw

                    AllBlocks.append([(cx + ox) / 2, (cz + oz + (oh - ch) / 2) / 2, BlockW, abs(cz - oz) + (ch + oh) / 2, (cd + od) / 2, None])

                    rows[rowidx].BlocksNorm.pop(idxThis)
                    rows[rowidx + 1].BlocksNorm.pop(idxThat)
                    idxThis -= 1
                    idxThat -= 1

                elif cx > ox:
                    idxThis -= 1
                else:
                    idxThat -= 1

    ####
    # Add blocks to create a "shelf/platform".
    # Does not account for openings (crosses gaps - which is a good thing)
    if settings['Shelf']:

        # Use wall block settings for shelf
        shelfBW = blockWidth
        shelfBWVar = settings['wv']
        shelfBH = sRef.properties.blockZ

        ShelfLft = sRef.properties.ShelfX
        ShelfBtm = sRef.properties.ShelfZ
        ShelfRt = ShelfLft + sRef.properties.ShelfW
        ShelfTop = ShelfBtm + sRef.properties.ShelfH
        ShelfThk = sRef.properties.ShelfD
        ShelfThk2 = ShelfThk * 2  # double-depth to position at cursor.

        if sRef.properties.ShelfOut:  # place blocks on outside of wall
            ShelfOffsets = [[0, -blockDhalf, 0], [0, -ShelfThk, 0], [0, -blockDhalf, 0], [0, -ShelfThk, 0], [0, -blockDhalf, 0], [0, -ShelfThk, 0], [0, -blockDhalf, 0], [0, -ShelfThk, 0]]
        else:
            ShelfOffsets = [[0, ShelfThk, 0], [0, blockDhalf, 0], [0, ShelfThk, 0], [0, blockDhalf, 0], [0, ShelfThk, 0], [0, blockDhalf, 0], [0, ShelfThk, 0], [0, blockDhalf, 0]]

        while ShelfBtm < ShelfTop:  # Add blocks for each "shelf row" in area
            divs = fill(ShelfLft, ShelfRt, shelfBW, shelfBW, shelfBWVar)

            for i in range(len(divs) - 1):  # add blocks for row divisions
                ThisBlockx = (divs[i] + divs[i + 1]) / 2
                ThisBlockw = divs[i + 1] - divs[i] - halfGrout
                AllBlocks.append([ThisBlockx, ShelfBtm, ThisBlockw, shelfBH, ShelfThk2, ShelfOffsets])

            ShelfBtm += shelfBH + halfGrout  # moving up to next row...

    # Set shelf material/color... on wish list.

    ####
    # Add blocks to create "steps".
    # Does not account for openings (crosses gaps - which is a good thing)
    if settings['Steps']:

        stepsFill = settings['StepsB']
        steps2Left = settings['StepsL']

        # step block "filler" by wall block settings.
        stepFW = blockWidth
        StepFWVar = settings['wv']

        StepXMod = sRef.properties.StepT  # step tread, also sets basic block size.
        StepZMod = sRef.properties.StepV

        StepLft = sRef.properties.StepX
        StepWide = sRef.properties.StepW
        StepRt = StepLft + StepWide
        StepBtm = sRef.properties.StepZ + StepZMod / 2  # Start offset for centered blocks
        StepTop = StepBtm + sRef.properties.StepH

        StepThk = sRef.properties.StepD
        StepThk2 = StepThk * 2  # use double-depth due to offsets to position at cursor.

        # Use "corners" to adjust steps so not centered on depth.
        # steps at cursor so no gaps between steps and wall face due to wall block depth.
        if settings['StepsO']:  # place blocks on outside of wall
            StepOffsets = [[0, -blockDhalf, 0], [0, -StepThk, 0], [0, -blockDhalf, 0], [0, -StepThk, 0], [0, -blockDhalf, 0], [0, -StepThk, 0], [0, -blockDhalf, 0], [0, -StepThk, 0]]
        else:
            StepOffsets = [[0, StepThk, 0], [0, blockDhalf, 0], [0, StepThk, 0], [0, blockDhalf, 0], [0, StepThk, 0], [0, blockDhalf, 0], [0, StepThk, 0], [0, blockDhalf, 0]]

        # Add steps for each "step row" in area (neg width is interesting but prevented)
        while StepBtm < StepTop and StepWide > 0:

            # Make blocks for each step row - based on rowOb:fillblocks
            if stepsFill:
                divs = fill(StepLft, StepRt, StepXMod, stepFW, StepFWVar)

                # loop through the row divisions, adding blocks for each one
                for i in range(len(divs) - 1):
                    ThisBlockx = (divs[i] + divs[i + 1]) / 2
                    ThisBlockw = divs[i + 1] - divs[i] - halfGrout

                    AllBlocks.append([ThisBlockx, StepBtm, ThisBlockw, StepZMod, StepThk2, StepOffsets])
            else:  # "cantilevered steps"
                if steps2Left:
                    stepStart = StepRt - StepXMod
                else:
                    stepStart = StepLft

                AllBlocks.append([stepStart, StepBtm, StepXMod, StepZMod, StepThk2, StepOffsets])

            StepBtm += StepZMod + halfGrout  # moving up to next row...
            StepWide -= StepXMod  # reduce step width

            # adjust side limit depending on direction of steps
            if steps2Left:
                StepRt -= StepXMod  # move from right
            else:
                StepLft += StepXMod  # move from left

    ####
    # Copy all the blocks out of the rows
    for row in rows:
        AllBlocks += row.BlocksEdge
        AllBlocks += row.BlocksNorm

    ####
    # make individual blocks for each block specified in the plan
    subDivision = settings['sdv']

    for block in AllBlocks:
        x, z, w, h, d, corners = block
        holeW2 = w / 2

        geom = MakeABlock([x - holeW2, x + holeW2, z - h / 2, z + h / 2, -d / 2, d / 2], subDivision, len(wallVs), corners)
        wallVs += geom[0]
        wallFs += geom[1]

    # make Arches for every opening specified in the plan.
    for hole in holeList:
        # lower arch stones
        if hole.vl > 0 and hole.rtl > blockHMin:
            archGeneration(hole, wallVs, wallFs, -1)

        # top arch stones
        if hole.v > 0 and hole.rt > blockHMin:
            archGeneration(hole, wallVs, wallFs, 1)

    if wallSlope:  # Curve wall, dome shape if "radialized".
        for i, vert in enumerate(wallVs):
            wallVs[i] = [vert[0], (wallTop + vert[1]) * cos(vert[2] * cPie / wallTop2), (wallTop + vert[1]) * sin(vert[2] * cPie / wallTop2)]

    if wallDome:  # Make wall circular, dome if sloped, else disc (flat round).
        for i, vert in enumerate(wallVs):
            wallVs[i] = [vert[2] * cos(vert[0]), vert[2] * sin(vert[0]), vert[1]]

    return wallVs, wallFs


################################################################################
#
# create a list of openings from the general specifications.
#
def openList(sRef):
    boundlist = []

    # initialize variables
    areaStart = dims['s']
    areaEnd = dims['e']

    SetWid = sRef.properties.blockX
    wallDisc = settings['Radial']

    for x in openingSpecs:
        if x['a']:  # apply opening to object
            # hope this is faster, at least for repeat.
            xOpenW = x['w']
            xOpenX = x['x']
            xOpenZ = x['z']

            if x['n']:  # repeat...
                if wallDisc:
                    r1 = xOpenZ
                else:
                    r1 = 1

                if xOpenX > (xOpenW + SetWid):
                    spacing = xOpenX / r1
                else:
                    spacing = (xOpenW + SetWid) / r1

                minspacing = (xOpenW + SetWid) / r1

                divs = fill(areaStart, areaEnd, spacing, minspacing, center=1)

                for posidx in range(len(divs) - 2):
                    boundlist.append(opening(divs[posidx + 1], xOpenZ, xOpenW, x['h'], x['v'], x['t'], x['vl'], x['tl'], x['bvl']))

            else:
                boundlist.append(opening(xOpenX, xOpenZ, xOpenW, x['h'], x['v'], x['t'], x['vl'], x['tl'], x['bvl']))
            # check for edge overlap?

    return boundlist


################################################################################
#
# fill a linear space with divisions
#
#    objXO: x origin
#    objXL: x limit
#    avedst: the average distance between points
#    mindst: the minimum distance between points
#    dev: the maximum random deviation from avedst
#    center: flag to center the elements in the range, 0 == disabled
#
# returns an ordered list of points, including the end points.
#
def fill(objXO, objXL, avedst, mindst=0.0, dev=0.0, center=0):

    curpos = objXO
    poslist = [curpos]  # set starting point

    # Set offset by average spacing, then add blocks (fall through);
    # if not at edge.
    if center:
        curpos += ((objXL - objXO - mindst * 2) % avedst) / 2 + mindst
        if curpos - poslist[-1] < mindst:
            curpos = poslist[-1] + mindst + random() * dev / 2

        # clip to right edge.
        if (objXL - curpos < mindst) or (objXL - curpos < mindst):
            poslist.append(objXL)
            return poslist
        else:
            poslist.append(curpos)

    # make block edges
    while True:
        curpos += avedst + rndd() * dev
        if curpos - poslist[-1] < mindst:
            curpos = poslist[-1] + mindst + random() * dev / 2

        if (objXL - curpos < mindst) or (objXL - curpos < mindst):
            poslist.append(objXL)  # close off edges at limit
            return poslist
        else:
            poslist.append(curpos)


#######################################################################
#
# MakeABlock: Generate block geometry
#  to be made into a square cornered block, subdivided along the length.
#
#  bounds: a list of boundary positions:
#      0:left, 1:right, 2:bottom, 3:top, 4:front, 5:back
#  segsize: the maximum size before subdivision occurs
#  vll: the number of vertexes already in the mesh. len(mesh.verts) should
#          give this number.
#  Offsets: list of coordinate delta values.
#      Offsets are lists, [x,y,z] in
#          [
#          0:left_bottom_back,
#          1:left_bottom_front,
#          2:left_top_back,
#          3:left_top_front,
#          4:right_bottom_back,
#          5:right_bottom_front,
#          6:right_top_back,
#          7:right_top_front,
#          ]
#  FaceExclude: list of faces to exclude from the faces list; see bounds above for indices
#
#  return lists of points and faces.
#
def MakeABlock(bounds, segsize, vll=0, Offsets=None, FaceExclude=[]):

    slices = fill(bounds[0], bounds[1], segsize, segsize, center=1)
    points = []
    faces = []

    if Offsets == None:
        points.append([slices[0], bounds[4], bounds[2]])
        points.append([slices[0], bounds[5], bounds[2]])
        points.append([slices[0], bounds[5], bounds[3]])
        points.append([slices[0], bounds[4], bounds[3]])

        for x in slices[1:-1]:
            points.append([x, bounds[4], bounds[2]])
            points.append([x, bounds[5], bounds[2]])
            points.append([x, bounds[5], bounds[3]])
            points.append([x, bounds[4], bounds[3]])

        points.append([slices[-1], bounds[4], bounds[2]])
        points.append([slices[-1], bounds[5], bounds[2]])
        points.append([slices[-1], bounds[5], bounds[3]])
        points.append([slices[-1], bounds[4], bounds[3]])

    else:
        points.append([slices[0] + Offsets[0][0], bounds[4] + Offsets[0][1], bounds[2] + Offsets[0][2]])
        points.append([slices[0] + Offsets[1][0], bounds[5] + Offsets[1][1], bounds[2] + Offsets[1][2]])
        points.append([slices[0] + Offsets[3][0], bounds[5] + Offsets[3][1], bounds[3] + Offsets[3][2]])
        points.append([slices[0] + Offsets[2][0], bounds[4] + Offsets[2][1], bounds[3] + Offsets[2][2]])

        for x in slices[1:-1]:
            xwt = (x - bounds[0]) / (bounds[1] - bounds[0])
            points.append([x + Offsets[0][0] * (1 - xwt) + Offsets[4][0] * xwt, bounds[4] + Offsets[0][1] * (1 - xwt) + Offsets[4][1] * xwt, bounds[2] + Offsets[0][2] * (1 - xwt) + Offsets[4][2] * xwt])
            points.append([x + Offsets[1][0] * (1 - xwt) + Offsets[5][0] * xwt, bounds[5] + Offsets[1][1] * (1 - xwt) + Offsets[5][1] * xwt, bounds[2] + Offsets[1][2] * (1 - xwt) + Offsets[5][2] * xwt])
            points.append([x + Offsets[3][0] * (1 - xwt) + Offsets[7][0] * xwt, bounds[5] + Offsets[3][1] * (1 - xwt) + Offsets[7][1] * xwt, bounds[3] + Offsets[3][2] * (1 - xwt) + Offsets[7][2] * xwt])
            points.append([x + Offsets[2][0] * (1 - xwt) + Offsets[6][0] * xwt, bounds[4] + Offsets[2][1] * (1 - xwt) + Offsets[6][1] * xwt, bounds[3] + Offsets[2][2] * (1 - xwt) + Offsets[6][2] * xwt])

        points.append([slices[-1] + Offsets[4][0], bounds[4] + Offsets[4][1], bounds[2] + Offsets[4][2]])
        points.append([slices[-1] + Offsets[5][0], bounds[5] + Offsets[5][1], bounds[2] + Offsets[5][2]])
        points.append([slices[-1] + Offsets[7][0], bounds[5] + Offsets[7][1], bounds[3] + Offsets[7][2]])
        points.append([slices[-1] + Offsets[6][0], bounds[4] + Offsets[6][1], bounds[3] + Offsets[6][2]])

    faces.append([vll, vll + 3, vll + 2, vll + 1])

    for x in range(len(slices) - 1):
        faces.append([vll, vll + 1, vll + 5, vll + 4])
        vll += 1
        faces.append([vll, vll + 1, vll + 5, vll + 4])
        vll += 1
        faces.append([vll, vll + 1, vll + 5, vll + 4])
        vll += 1
        faces.append([vll, vll - 3, vll + 1, vll + 4])
        vll += 1

    faces.append([vll, vll + 1, vll + 2, vll + 3])

    return points, faces


#
# For generating Keystone Geometry
def MakeAKeystone(xpos, width, zpos, ztop, zbtm, thick, bevel, vll=0, FaceExclude=[], xBevScl=1):
    __doc__ = """\
    MakeAKeystone returns lists of points and faces to be made into a square cornered keystone, with optional bevels.
    xpos: x position of the centerline
    width: x width of the keystone at the widest point (discounting bevels)
    zpos: z position of the widest point
    ztop: distance from zpos to the top
    zbtm: distance from zpos to the bottom
    thick: thickness
    bevel: the amount to raise the back vertex to account for arch beveling
    vll: the number of vertexes already in the mesh. len(mesh.verts) should give this number
    faceExclude: list of faces to exclude from the faces list.  0:left, 1:right, 2:bottom, 3:top, 4:back, 5:front
    xBevScl: how much to divide the end (+- x axis) bevel dimensions.  Set to current average radius to compensate for angular distortion on curved blocks
    """

    points = []
    faces = []
    faceinclude = [1 for x in range(6)]
    for x in FaceExclude:
        faceinclude[x] = 0
    Top = zpos + ztop
    Btm = zpos - zbtm
    Wid = width / 2.
    Thk = thick / 2.

    # The front top point
    points.append([xpos, Thk, Top])
    # The front left point
    points.append([xpos - Wid, Thk, zpos])
    # The front bottom point
    points.append([xpos, Thk, Btm])
    # The front right point
    points.append([xpos + Wid, Thk, zpos])

    MirrorPoints = []
    for i in points:
        MirrorPoints.append([i[0], -i[1], i[2]])
    points += MirrorPoints
    points[6][2] += bevel

    faces.append([3, 2, 1, 0])
    faces.append([4, 5, 6, 7])
    faces.append([4, 7, 3, 0])
    faces.append([5, 4, 0, 1])
    faces.append([6, 5, 1, 2])
    faces.append([7, 6, 2, 3])
    # Offset the vertex numbers by the number of verticies already in the list
    for i in range(len(faces)):
        for j in range(len(faces[i])):
            faces[i][j] += vll

    return points, faces


# class openings in the wall
class opening:
    __doc__ = """\
    This is the class for holding the data for the openings in the wall.
    It has methods for returning the edges of the opening for any given position value,
    as well as bevel settings and top and bottom positions.
    It stores the 'style' of the opening, and all other pertinent information.
    """
    # x = 0. # x position of the opening
    # z = 0. # x position of the opening
    # w = 0. # width of the opening
    # h = 0. # height of the opening
    r = 0  # top radius of the arch (derived from 'v')
    rl = 0  # lower radius of the arch (derived from 'vl')
    rt = 0  # top arch thickness
    rtl = 0  # lower arch thickness
    ts = 0  # Opening side thickness, if greater than average width, replaces it.
    c = 0  # top arch corner position (for low arches), distance from the top of the straight sides
    cl = 0  # lower arch corner position (for low arches), distance from the top of the straight sides
    # form = 0 # arch type (unused for now)
    # b = 0. # back face bevel distance, like an arrow slit
    v = 0.  # top arch height
    vl = 0.  # lower arch height
    # variable "s" is used for "side" in the "edge" function.
    # it is a signed int, multiplied by the width to get + or - of the center

    def btm(self):
        if self.vl <= self.w / 2:
            return self.z - self.h / 2 - self.vl - self.rtl
        else:
            return self.z - sqrt((self.rl + self.rtl)**2 - (self.rl - self.w / 2)**2) - self.h / 2

    def top(self):
        if self.v <= self.w / 2:
            return self.z + self.h / 2 + self.v + self.rt
        else:
            return sqrt((self.r + self.rt)**2 - (self.r - self.w / 2)**2) + self.z + self.h / 2

    # crits returns the critical split points, or discontinuities, used for making rows
    def crits(self):
        critlist = []
        if self.vl > 0:  # for lower arch
            # add the top point if it is pointed
            #if self.vl >= self.w/2.: critlist.append(self.btm())
            if self.vl < self.w / 2.:  # else: for low arches, with wedge blocks under them
                # critlist.append(self.btm())
                critlist.append(self.z - self.h / 2 - self.cl)

        if self.h > 0:  # if it has a height, append points at the top and bottom of the main square section
            critlist += [self.z - self.h / 2, self.z + self.h / 2]
        else:  # otherwise, append just one in the center
            critlist.append(self.z)

        if self.v > 0:  # for the upper arch
            if self.v < self.w / 2.:  # add the splits for the upper wedge blocks, if needed
                critlist.append(self.z + self.h / 2 + self.c)
                # critlist.append(self.top())
            # otherwise just add the top point, if it is pointed
            # else: critlist.append(self.top())

        return critlist

    #
    # get the side position of the opening.
    # ht is the z position; s is the side: 1 for right, -1 for left
    # if the height passed is above or below the opening, return None
    #
    def edgeS(edgeParms, ht, s):

        wallTopZ = dims['t']
        wallHalfH = edgeParms.h / 2
        wallHalfW = edgeParms.w / 2
        wallBase = edgeParms.z

        # set the row radius: 1 for standard wall (flat)
        if settings['Radial']:
            if settings['Slope']:
                r1 = abs(wallTopZ * sin(ht * cPie / (wallTopZ * 2)))
            else:
                r1 = abs(ht)
        else:
            r1 = 1

        # Go through all the options, and return the correct value
        if ht < edgeParms.btm():  # too low
            return None
        elif ht > edgeParms.top():  # too high
            return None

        # in this range, pass the lower arch info
        elif ht <= wallBase - wallHalfH - edgeParms.cl:
            if edgeParms.vl > wallHalfW:
                circVal = circ(ht - wallBase + wallHalfH, edgeParms.rl + edgeParms.rtl)
                if circVal == None:
                    return None
                else:
                    return edgeParms.x + s * (wallHalfW - edgeParms.rl + circVal) / r1
            else:
                circVal = circ(ht - wallBase + wallHalfH + edgeParms.vl - edgeParms.rl, edgeParms.rl + edgeParms.rtl)
                if circVal == None:
                    return None
                else:
                    return edgeParms.x + s * circVal / r1

        # in this range, pass the top arch info
        elif ht >= wallBase + wallHalfH + edgeParms.c:
            if edgeParms.v > wallHalfW:
                circVal = circ(ht - wallBase - wallHalfH, edgeParms.r + edgeParms.rt)
                if circVal == None:
                    return None
                else:
                    return edgeParms.x + s * (wallHalfW - edgeParms.r + circVal) / r1
            else:
                circVal = circ(ht - (wallBase + wallHalfH + edgeParms.v - edgeParms.r), edgeParms.r + edgeParms.rt)
                if circVal == None:
                    return None
                else:
                    return edgeParms.x + s * circVal / r1

        # in this range pass the lower corner edge info
        elif ht <= wallBase - wallHalfH:
            d = sqrt(edgeParms.rtl**2 - edgeParms.cl**2)
            if edgeParms.cl > edgeParms.rtl / sqrt(2.):
                return edgeParms.x + s * (wallHalfW + (wallBase - wallHalfH - ht) * d / edgeParms.cl) / r1
            else:
                return edgeParms.x + s * (wallHalfW + d) / r1

        # in this range pass the upper corner edge info
        elif ht >= wallBase + wallHalfH:
            d = sqrt(edgeParms.rt**2 - edgeParms.c**2)
            if edgeParms.c > edgeParms.rt / sqrt(2.):
                return edgeParms.x + s * (wallHalfW + (ht - wallBase - wallHalfH) * d / edgeParms.c) / r1
            else:
                return edgeParms.x + s * (wallHalfW + d) / r1

        # in this range, pass the middle info (straight sides)
        else:
            return edgeParms.x + s * wallHalfW / r1

    # get the top or bottom of the opening
    # ht is the x position; archSide: 1 for top, -1 for bottom
    #
    def edgeV(self, ht, archSide):
        wallTopZ = dims['t']
        dist = abs(self.x - ht)

        def radialAdjust(dist, sideVal):  # adjust distance and for radial geometry.
            if settings['Radial']:
                if settings['Slope']:
                    dist = dist * abs(wallTopZ * sin(sideVal * cPie / (wallTopZ * 2)))
                else:
                    dist = dist * sideVal
            return dist

        if archSide > 0:  # check top down
            # hack for radialized masonry, import approx Z instead of self.top()
            dist = radialAdjust(dist, self.top())

            # no arch on top, flat
            if not self.r:
                return self.z + self.h / 2

            # pointed arch on top
            elif self.v > self.w / 2:
                circVal = circ(dist - self.w / 2 + self.r, self.r + self.rt)
                if circVal == None:
                    return 0.0
                else:
                    return self.z + self.h / 2 + circVal

            # domed arch on top
            else:
                circVal = circ(dist, self.r + self.rt)
                if circVal == None:
                    return 0.0
                else:
                    return self.z + self.h / 2 + self.v - self.r + circVal

        else:  # check bottom up
            # hack for radialized masonry, import approx Z instead of self.top()
            dist = radialAdjust(dist, self.btm())

            # no arch on bottom
            if not self.rl:
                return self.z - self.h / 2

            # pointed arch on bottom
            elif self.vl > self.w / 2:
                circVal = circ(dist - self.w / 2 + self.rl, self.rl + self.rtl)
                if circVal == None:
                    return 0.0
                else:
                    return self.z - self.h / 2 - circVal

            # old conditional? if (dist-self.w/2+self.rl)<=(self.rl+self.rtl):
            # domed arch on bottom
            else:
                circVal = circ(dist, self.rl + self.rtl)  # dist-self.w/2+self.rl
                if circVal == None:
                    return 0.0
                else:
                    return self.z - self.h / 2 - self.vl + self.rl - circVal

    #
    def edgeBev(self, ht):
        wallTopZ = dims['t']
        if ht > (self.z + self.h / 2):
            return 0.0
        if ht < (self.z - self.h / 2):
            return 0.0
        if settings['Radial']:
            if settings['Slope']:
                r1 = abs(wallTopZ * sin(ht * cPie / (wallTopZ * 2)))
            else:
                r1 = abs(ht)
        else:
            r1 = 1
        bevel = self.b / r1
        return bevel

    #
    ##
    #

    def __init__(self, xpos, zpos, width, height, archHeight=0, archThk=0,
                 archHeightLower=0, archThkLower=0, bevel=0, edgeThk=0):
        self.x = float(xpos)
        self.z = float(zpos)
        self.w = float(width)
        self.h = float(height)
        self.rt = archThk
        self.rtl = archThkLower
        self.v = archHeight
        self.vl = archHeightLower

        # find the upper arch radius
        if archHeight >= width / 2:
            # just one arch, low long
            self.r = (self.v**2) / self.w + self.w / 4
        elif archHeight <= 0:
            # No arches
            self.r = 0
            self.v = 0
        else:
            # Two arches
            self.r = (self.w**2) / (8 * self.v) + self.v / 2.
            self.c = self.rt * cos(atan(self.w / (2 * (self.r - self.v))))

        # find the lower arch radius
        if archHeightLower >= width / 2:
            self.rl = (self.vl**2) / self.w + self.w / 4
        elif archHeightLower <= 0:
            self.rl = 0
            self.vl = 0
        else:
            self.rl = (self.w**2) / (8 * self.vl) + self.vl / 2.
            self.cl = self.rtl * cos(atan(self.w / (2 * (self.rl - self.vl))))

        # self.form = something?
        self.b = float(bevel)
        self.ts = edgeThk

#
#
# class for the whole wall boundaries; a sub-class of "opening"


class OpeningInv(opening):
    # this is supposed to switch the sides of the opening
    # so the wall will properly enclose the whole wall.

    def edgeS(self, ht, s):
        return opening.edgeS(self, ht, -s)

    def edgeV(self, ht, s):
        return opening.edgeV(self, ht, -s)

# class rows in the wall


class rowOb:
    __doc__ = """\
    This is the class for holding the data for individual rows of blocks.
    each row is required to have some edge blocks, and can also have
    intermediate sections of "normal" blocks.
    """

    #z = 0.
    #h = 0.
    radius = 1
    rowEdge = 0

    def FillBlocks(self):
        wallTopZ = dims['t']

        # Set the radius variable, in the case of radial geometry
        if settings['Radial']:
            if settings['Slope']:
                self.radius = wallTopZ * (sin(self.z * cPie / (wallTopZ * 2)))
            else:
                self.radius = self.z

        # initialize internal variables from global settings
        SetH = settings['h']
        # no HVar?
        SetWid = settings['w']
        SetWidVar = settings['wv']
        SetGrt = settings['g']
        SetDepth = settings['d']
        SetDepthVar = settings['dv']

        # height weight, make shorter rows have narrower blocks, and vice-versa
        rowHWt = ((self.h / SetH - 1) * ROW_H_WEIGHT + 1)

        # set variables for persistent values: loop optimization, readability, single ref for changes.
        avgDist = rowHWt * SetWid / self.radius
        minDist = SetWid / self.radius
        deviation = rowHWt * SetWidVar / self.radius
        grtOffset = SetGrt / (2 * self.radius)

        # init loop variables that may change...
        blockGap = SetGrt / self.radius
        ThisBlockHeight = self.h
        ThisBlockDepth = SetDepth + (rndd() * SetDepthVar)

        for segment in self.RowSegments:
            divs = fill(segment[0] + grtOffset, segment[1] - grtOffset, avgDist, minDist, deviation)

            # loop through the divisions, adding blocks for each one
            for i in range(len(divs) - 1):
                ThisBlockx = (divs[i] + divs[i + 1]) / 2
                ThisBlockw = divs[i + 1] - divs[i] - blockGap

                self.BlocksNorm.append([ThisBlockx, self.z, ThisBlockw, ThisBlockHeight, ThisBlockDepth, None])

                if SetDepthVar:  # vary depth
                    ThisBlockDepth = SetDepth + (rndd() * SetDepthVar)

    def __init__(self, centerheight, rowheight, rowEdge=0):
        self.z = float(centerheight)
        self.h = float(rowheight)
        self.rowEdge = float(rowEdge)

        # THIS INITILIZATION IS IMPORTANT!  OTHERWISE ALL OBJECTS WILL HAVE THE SAME LISTS!
        self.BlocksEdge = []
        self.RowSegments = []
        self.BlocksNorm = []

#


def arch(ra, rt, x, z, archStart, archEnd, bevel, bevAngle, vll):
    __doc__ = """\
    Makes a list of faces and vertexes for arches.
    ra: the radius of the arch, to the center of the bricks
    rt: the thickness of the arch
    x: x center location of the circular arc, as if the arch opening were centered on x = 0
    z: z center location of the arch
    anglebeg: start angle of the arch, in radians, from vertical?
    angleend: end angle of the arch, in radians, from vertical?
    bevel: how much to bevel the inside of the arch.
    vll: how long is the vertex list already?
    """
    avlist = []
    aflist = []

    # initialize internal variables for global settings
    SetH = settings['h']
    SetWid = settings['w']
    SetWidVar = settings['wv']
    SetGrt = settings['g']
    SetDepth = settings['d']
    SetDepthVar = settings['dv']
    wallTopZ = dims['t']

    wallDome = settings['Radial']

    ArchInner = ra - rt / 2
    ArchOuter = ra + rt / 2 - SetGrt

    DepthBack = -SetDepth / 2 - rndc() * SetDepthVar
    DepthFront = SetDepth / 2 + rndc() * SetDepthVar

    # there's something wrong here...
    if wallDome:
        subdivision = settings['sdv']
    else:
        subdivision = 0.12

    blockGap = SetGrt / (2 * ra)  # grout offset
    # set up the offsets, it will be the same for every block
    offsets = ([[0] * 2 + [bevel]] + [[0] * 3] * 3) * 2

    # make the divisions in the "length" of the arch
    divs = fill(archStart, archEnd, settings['w'] / ra, settings['w'] / ra, settings['wv'] / ra)

    for i in range(len(divs) - 1):
         # modify block offsets for bevel.
        if i == 0:
            ThisOffset = offsets[:]
            pointsToAffect = (0, 2, 3)

            for num in pointsToAffect:
                offsets[num] = ThisOffset[num][:]
                offsets[num][0] += bevAngle
        elif i == len(divs) - 2:
            ThisOffset = offsets[:]
            pointsToAffect = (4, 6, 7)

            for num in pointsToAffect:
                offsets[num] = ThisOffset[num][:]
                offsets[num][0] -= bevAngle
        else:
            ThisOffset = offsets

        geom = MakeABlock([divs[i] + blockGap, divs[i + 1] - blockGap, ArchInner, ArchOuter, DepthBack, DepthFront],
                          subdivision, len(avlist) + vll, ThisOffset, [])

        avlist += geom[0]
        aflist += geom[1]

        if SetDepthVar:  # vary depth
            DepthBack = -SetDepth / 2 - rndc() * SetDepthVar
            DepthFront = SetDepth / 2 + rndc() * SetDepthVar

    for i, vert in enumerate(avlist):
        v0 = vert[2] * sin(vert[0]) + x
        v1 = vert[1]
        v2 = vert[2] * cos(vert[0]) + z

        if wallDome:
            r1 = wallTopZ * (sin(v2 * cPie / (wallTopZ * 2)))
        #            if settings['Slope']: r1 = wallTopZ*(sin(v2*cPie/(wallTopZ*2)))
        #            else: r1 = v2 # disc
            v0 = v0 / r1

        avlist[i] = [v0, v1, v2]

    return (avlist, aflist)


#################################################################
#
# Make wedge blocks for openings.
#
#  examples:
#   wedgeBlocks(row, LeftWedgeEdge, LNerEdge, LEB, r1)
#   wedgeBlocks(row, RNerEdge, RightWedgeEdge, rSide, r1)
#
def wedgeBlocks(row, opening, leftPos, rightPos, edgeSide, r1):

    wedgeWRad = settings['w'] / r1

    wedgeEdges = fill(leftPos, rightPos, wedgeWRad, wedgeWRad, settings['wv'] / r1)

    blockDepth = settings['d']
    blockDepthV = settings['dv']
    blockGap = settings['g'] / r1

    for i in range(len(wedgeEdges) - 1):
        x = (wedgeEdges[i + 1] + wedgeEdges[i]) / 2
        w = wedgeEdges[i + 1] - wedgeEdges[i] - blockGap
        halfBW = w / 2

        ThisBlockDepth = blockDepth + rndd() * blockDepthV

        LVert = -((row.z - ((row.h / 2) * edgeSide)) - opening.edgeV(x - halfBW, edgeSide))
        #        LVert =  -( row.z - (row.h/2)*edgeSide - (opening.edgeV(x-halfBW,edgeSide)))
        RightVertOffset = -(row.z - (row.h / 2) * edgeSide - opening.edgeV(x + halfBW, edgeSide))

        # Wedges are on top = Voff, blank, Voff, blank
        # Wedges are on btm = blank, Voff, blank, Voff
        ThisBlockOffsets = [[0, 0, LVert]] * 2 + [[0] * 3] * 2 + [[0, 0, RightVertOffset]] * 2
        # Instert or append "blank" for top or bottom wedges.
        if edgeSide == 1:
            ThisBlockOffsets = ThisBlockOffsets + [[0] * 3] * 2
        else:
            ThisBlockOffsets = [[0] * 3] * 2 + ThisBlockOffsets

        row.BlocksEdge.append([x, row.z, w, row.h, ThisBlockDepth, ThisBlockOffsets])


############################################################
#
#
    # set end blocks
    # check for openings, record top and bottom of row for right and left of each
    # if both top and bottom intersect create blocks on each edge, appropriate to the size of the overlap
    # if only one side intersects, run fill to get edge positions, but this should never happen
    #
#
def rowProcessing(row, holeList, WallBoundaries):

    if settings['Radial']:  # radial stonework sets the row radius
        if settings['Slope']:
            r1 = abs(dims['t'] * sin(row.z * cPie / (dims['t'] * 2)))
        else:
            r1 = abs(row.z)
    else:
        r1 = 1

    # set block working values
    blockWidth = settings['w']
    blockWVar = settings['wv']
    blockDepth = settings['d']
    blockDVar = settings['dv']

    blockGap = settings['g'] / r1
    blockHMin = BLOCK_MIN + blockGap

    # set row working values
    rowH = row.h
    rowH2 = rowH / 2
    rowEdge = row.rowEdge / r1
    rowStart = dims['s'] + rowEdge
    # shouldn't rowEnd be minus rowEdge?
    rowEnd = dims['e'] + rowEdge
    rowTop = row.z + rowH2
    rowBtm = row.z - rowH2

    # left and right wall limits for top and bottom of row.
    edgetop = [[rowStart, WallBoundaries], [rowEnd, WallBoundaries]]
    edgebtm = [[rowStart, WallBoundaries], [rowEnd, WallBoundaries]]

    for hole in holeList:
        # check the top and bottom of the row, looking at the opening from the right
        holeEdge = [hole.edgeS(rowTop, -1), hole.edgeS(rowBtm, -1)]

        # If either one hit the opening, make split points for the side of the opening.
        if holeEdge[0] or holeEdge[1]:
            holeEdge += [hole.edgeS(rowTop, 1), hole.edgeS(rowBtm, 1)]

            # If one of them missed for some reason, set that value to
            # the middle of the opening.
            for i, pos in enumerate(holeEdge):
                if pos == None:
                    holeEdge[i] = hole.x

            # add the intersects to the list of edge points
            edgetop.append([holeEdge[0], hole])
            edgetop.append([holeEdge[2], hole])
            edgebtm.append([holeEdge[1], hole])
            edgebtm.append([holeEdge[3], hole])

    # make the walls in order, sort the intersects.
    #  remove edge points that are out of order;
    #  else the "oddity" where opening overlap creates blocks inversely.
    edgetop.sort()
    edgebtm.sort()

    # These two loops trim the edges to the limits of the wall.
    # This way openings extending outside the wall don't enlarge the wall.
    while True:
        try:
            if (edgetop[-1][0] > rowEnd) or (edgebtm[-1][0] > rowEnd):
                edgetop[-2:] = []
                edgebtm[-2:] = []
            else:
                break
        except IndexError:
            break
    # still trimming the edges...
    while True:
        try:
            if (edgetop[0][0] < rowStart) or (edgebtm[0][0] < rowStart):
                edgetop[:2] = []
                edgebtm[:2] = []
            else:
                break
        except IndexError:
            break

    # finally, make edge blocks and rows!

    # Process each section, a pair of points in edgetop,
    # and place the edge blocks and inbetween normal block zones into the row object.

    # maximum distance to span with one block
    MaxWid = (blockWidth + blockWVar) / r1

    for OpnSplitNo in range(int(len(edgetop) / 2)):
        lEdgeIndx = 2 * OpnSplitNo
        rEdgeIndx = lEdgeIndx + 1

        leftOpening = edgetop[lEdgeIndx][1]
        rightOpening = edgetop[rEdgeIndx][1]

        # find the difference between the edge top and bottom on both sides
        LTop = edgetop[lEdgeIndx][0]
        LBtm = edgebtm[lEdgeIndx][0]
        RTop = edgetop[rEdgeIndx][0]
        RBtm = edgebtm[rEdgeIndx][0]
        LDiff = LBtm - LTop
        RDiff = RTop - RBtm

        # set side edge limits from top and bottom
        if LDiff > 0:  # if furthest edge is top,
            LEB = 1
            LFarEdge = LTop  # The furthest edge
            LNerEdge = LBtm  # the nearer edge
        else:  # furthest edge is bottom
            LEB = -1
            LFarEdge = LBtm
            LNerEdge = LTop

        if RDiff > 0:  # if furthest edge is top,
            rSide = 1
            RFarEdge = RTop  # The furthest edge
            RNerEdge = RBtm  # the nearer edge
        else:  # furthest edge is bottom
            rSide = -1
            RFarEdge = RBtm  # The furthest edge
            RNerEdge = RTop  # the nearer edge

        blockXx = RNerEdge - LNerEdge  # The space between the closest edges of the openings in this section of the row
        blockXm = (RNerEdge + LNerEdge) / 2  # The mid point between the nearest edges

        # check the left and right sides for wedge blocks
        # find the edge of the correct side, offset for minimum block height.  The LEB decides top or bottom
        ZPositionCheck = row.z + (rowH2 - blockHMin) * LEB
        # edgeS may return "None"
        LeftWedgeEdge = leftOpening.edgeS(ZPositionCheck, 1)

        if (abs(LDiff) > blockWidth) or (not LeftWedgeEdge):
            # make wedge blocks
            if not LeftWedgeEdge:
                LeftWedgeEdge = leftOpening.x
            wedgeBlocks(row, leftOpening, LeftWedgeEdge, LNerEdge, LEB, r1)
            # set the near and far edge settings to vertical, so the other edge blocks don't interfere
            LFarEdge, LTop, LBtm = LNerEdge, LNerEdge, LNerEdge
            LDiff = 0

        # Now do the wedge blocks for the right, same drill... repeated code?
        # find the edge of the correct side, offset for minimum block height.
        ZPositionCheck = row.z + (rowH2 - blockHMin) * rSide
        # edgeS may return "None"
        RightWedgeEdge = rightOpening.edgeS(ZPositionCheck, -1)
        if (abs(RDiff) > blockWidth) or (not RightWedgeEdge):
            # make wedge blocks
            if not RightWedgeEdge:
                RightWedgeEdge = rightOpening.x
            wedgeBlocks(row, rightOpening, RNerEdge, RightWedgeEdge, rSide, r1)

            # set the near and far edge settings to vertical, so the other edge blocks don't interfere
            RFarEdge, RTop, RBtm = RNerEdge, RNerEdge, RNerEdge
            RDiff = 0

        # Single block - needed for arch "point" (keystone).
        if blockXx < MaxWid:
            x = (LNerEdge + RNerEdge) / 2.
            w = blockXx
            ThisBlockDepth = rndd() * blockDVar + blockDepth
            BtmOff = LBtm - LNerEdge
            TopOff = LTop - LNerEdge
            ThisBlockOffsets = [[BtmOff, 0, 0]] * 2 + [[TopOff, 0, 0]] * 2
            BtmOff = RBtm - RNerEdge
            TopOff = RTop - RNerEdge
            ThisBlockOffsets += [[BtmOff, 0, 0]] * 2 + [[TopOff, 0, 0]] * 2

            pointsToAffect = (0, 2)
            bevelBlockOffsets(ThisBlockOffsets, leftOpening.edgeBev(rowTop), pointsToAffect)

            pointsToAffect = (4, 6)
            bevelBlockOffsets(ThisBlockOffsets, -rightOpening.edgeBev(rowTop), pointsToAffect)

            row.BlocksEdge.append([x, row.z, w, rowH, ThisBlockDepth, ThisBlockOffsets])
            continue

        # must be two or more blocks

        # Left offsets
        BtmOff = LBtm - LNerEdge
        TopOff = LTop - LNerEdge
        leftOffsets = [[BtmOff, 0, 0]] * 2 + [[TopOff, 0, 0]] * 2 + [[0] * 3] * 4
        bevelL = leftOpening.edgeBev(rowTop)

        pointsToAffect = (0, 2)
        bevelBlockOffsets(leftOffsets, bevelL, pointsToAffect)

        # Right offsets
        BtmOff = RBtm - RNerEdge
        TopOff = RTop - RNerEdge
        rightOffsets = [[0] * 3] * 4 + [[BtmOff, 0, 0]] * 2 + [[TopOff, 0, 0]] * 2
        bevelR = rightOpening.edgeBev(rowTop)

        pointsToAffect = (4, 6)
        bevelBlockOffsets(rightOffsets, -bevelR, pointsToAffect)

        if blockXx < MaxWid * 2:  # only two blocks?
            # div is the x position of the dividing point between the two bricks
            div = blockXm + (rndd() * blockWVar) / r1

            # set the x position and width for the left block
            x = (div + LNerEdge) / 2 - blockGap / 4
            w = (div - LNerEdge) - blockGap / 2
            ThisBlockDepth = rndd() * blockDVar + blockDepth
            # For reference: EdgeBlocks = [[x,z,w,h,d,[corner offset matrix]],[etc.]]
            row.BlocksEdge.append([x, row.z, w, rowH, ThisBlockDepth, leftOffsets])

            # Initialize for the block on the right side
            x = (div + RNerEdge) / 2 + blockGap / 4
            w = (RNerEdge - div) - blockGap / 2
            ThisBlockDepth = rndd() * blockDVar + blockDepth
            row.BlocksEdge.append([x, row.z, w, rowH, ThisBlockDepth, rightOffsets])
            continue

        # more than two blocks in the row, and no wedge blocks

        # make Left edge block
        # set the x position and width for the block
        widOptions = [blockWidth, bevelL + blockWidth, leftOpening.ts]
        baseWidMax = max(widOptions)
        w = baseWidMax + row.rowEdge + (rndd() * blockWVar)
        widOptions[0] = blockWidth
        widOptions[2] = w
        w = max(widOptions) / r1 - blockGap
        x = w / 2 + LNerEdge + blockGap / 2
        BlockRowL = x + w / 2
        ThisBlockDepth = rndd() * blockDVar + blockDepth
        row.BlocksEdge.append([x, row.z, w, rowH, ThisBlockDepth, leftOffsets])

        # make Right edge block
        # set the x position and width for the block
        widOptions = [blockWidth, bevelR + blockWidth, rightOpening.ts]
        baseWidMax = max(widOptions)
        w = baseWidMax + row.rowEdge + (rndd() * blockWVar)
        widOptions[0] = blockWidth
        widOptions[2] = w
        w = max(widOptions) / r1 - blockGap
        x = RNerEdge - w / 2 - blockGap / 2
        BlockRowR = x - w / 2
        ThisBlockDepth = rndd() * blockDVar + blockDepth
        row.BlocksEdge.append([x, row.z, w, rowH, ThisBlockDepth, rightOffsets])

        row.RowSegments.append([BlockRowL, BlockRowR])


#####################################
#
# Makes arches for the top and bottom
# hole is the "wall opening" that the arch is for.
#
def archGeneration(hole, vlist, flist, sideSign):

    avlist = []
    aflist = []

    if sideSign == 1:  # top
        r = hole.r  # radius of the arch
        rt = hole.rt  # thickness of the arch (stone height)
        v = hole.v  # height of the arch
        c = hole.c
    else:  # bottom
        r = hole.rl  # radius of the arch
        rt = hole.rtl  # thickness of the arch (stone height)
        v = hole.vl  # height of the arch
        c = hole.cl

    ra = r + rt / 2  # average radius of the arch
    x = hole.x
    w = hole.w
    holeW2 = w / 2
    h = hole.h
    z = hole.z
    bev = hole.b

    blockGap = settings['g']
    blockHMin = BLOCK_MIN + blockGap

    blockDepth = settings['d']
    blockDVar = settings['dv']

    if v > holeW2:  # two arcs, to make a pointed arch
        # positioning
        zpos = z + (h / 2) * sideSign
        xoffset = r - holeW2
        # left side top, right side bottom
        # angles reference straight up, and are in radians
        bevRad = r + bev
        bevHt = sqrt(bevRad**2 - (bevRad - (holeW2 + bev))**2)
        midHalfAngle = atan(v / (r - holeW2))
        midHalfAngleBevel = atan(bevHt / (r - holeW2))
        bevelAngle = midHalfAngle - midHalfAngleBevel
        anglebeg = (cPieHlf) * (-sideSign)
        angleend = (cPieHlf) * (-sideSign) + midHalfAngle

        avlist, aflist = arch(ra, rt, (xoffset) * (sideSign), zpos, anglebeg, angleend, bev, bevelAngle, len(vlist))

        for i, vert in enumerate(avlist):
            avlist[i] = [vert[0] + hole.x, vert[1], vert[2]]
        vlist += avlist
        flist += aflist

        # right side top, left side bottom
        # angles reference straight up, and are in radians
        anglebeg = (cPieHlf) * (sideSign) - midHalfAngle
        angleend = (cPieHlf) * (sideSign)

        avlist, aflist = arch(ra, rt, (xoffset) * (-sideSign), zpos, anglebeg, angleend, bev, bevelAngle, len(vlist))

        for i, vert in enumerate(avlist):
            avlist[i] = [vert[0] + hole.x, vert[1], vert[2]]

        vlist += avlist
        flist += aflist

        # keystone
        Dpth = blockDepth + rndc() * blockDVar
        angleBevel = (cPieHlf) * (sideSign) - midHalfAngle
        Wdth = (rt - blockGap - bev) * 2 * sin(angleBevel) * sideSign  # note, sin may be negative
        MidZ = ((sideSign) * (bevHt + h / 2.0) + z) + (rt - blockGap - bev) * cos(angleBevel)  # note, cos may come out negative too
        nearCorner = sideSign * (MidZ - z) - v - h / 2

        if sideSign == 1:
            TopHt = hole.top() - MidZ - blockGap
            BtmHt = nearCorner
        else:
            BtmHt = - (hole.btm() - MidZ) - blockGap
            TopHt = nearCorner

        # set the amout to bevel the keystone
        keystoneBevel = (bevHt - v) * sideSign
        if Wdth >= blockHMin:
            avlist, aflist = MakeAKeystone(x, Wdth, MidZ, TopHt, BtmHt, Dpth, keystoneBevel, len(vlist))

            if settings['Radial']:
                for i, vert in enumerate(avlist):
                    if settings['Slope']:
                        r1 = dims['t'] * sin(vert[2] * cPie / (dims['t'] * 2))
                    else:
                        r1 = vert[2]
                    avlist[i] = [((vert[0] - hole.x) / r1) + hole.x, vert[1], vert[2]]

            vlist += avlist
            flist += aflist

    else:  # only one arc - curve not peak.
        # bottom (sideSign -1) arch has poorly sized blocks...

        zpos = z + (sideSign * (h / 2 + v - r))  # single arc positioning

        # angles reference straight up, and are in radians
        if sideSign == -1:
            angleOffset = cPie
        else:
            angleOffset = 0.0

        if v < holeW2:
            halfangle = atan(w / (2 * (r - v)))

            anglebeg = angleOffset - halfangle
            angleend = angleOffset + halfangle
        else:
            anglebeg = angleOffset - cPieHlf
            angleend = angleOffset + cPieHlf

        avlist, aflist = arch(ra, rt, 0, zpos, anglebeg, angleend, bev, 0.0, len(vlist))

        for i, vert in enumerate(avlist):
            avlist[i] = [vert[0] + x, vert[1], vert[2]]

        vlist += avlist
        flist += aflist

        # Make the Side Stones
        archBW = sqrt(rt**2 - c**2)
        archBWG = archBW - blockGap

        if c > blockHMin and c < archBW:
            subdivision = settings['sdv']
            if settings['Radial']:
                subdivision *= (zpos + (h / 2) * sideSign)

            # set the height of the block, it should be as high as the max corner position, minus grout
            height = c - blockGap * (0.5 + c / archBW)

            # the vertical offset for the short side of the block
            voff = sideSign * (blockHMin - height)
            xstart = holeW2
            zstart = z + sideSign * (h / 2 + blockGap / 2)
            woffset = archBWG * (blockHMin) / (c - blockGap / 2)
            #            woffset = archBWG*(BLOCK_MIN + blockGap/2)/(c - blockGap/2)
            depth = blockDepth + (rndd() * blockDVar)

            if sideSign == 1:
                offsets = [[0] * 3] * 6 + [[0] * 2 + [voff]] * 2
                topSide = zstart + height
                btmSide = zstart
            else:
                offsets = [[0] * 3] * 4 + [[0] * 2 + [voff]] * 2 + [[0] * 3] * 2
                topSide = zstart
                btmSide = zstart - height

            pointsToAffect = (4, 6)  # left
            bevelBlockOffsets(offsets, bev, pointsToAffect)

            avlist, aflist = MakeABlock([x - xstart - archBWG, x - xstart - woffset, btmSide, topSide, -depth / 2, depth / 2], subdivision, len(vlist), Offsets=offsets)

            # top didn't use radialized in prev version; just noting for clarity - may need to revise for "sideSign == 1"
            if settings['Radial']:
                for i, vert in enumerate(avlist):
                    avlist[i] = [((vert[0] - x) / vert[2]) + x, vert[1], vert[2]]

            vlist += avlist
            flist += aflist

            if sideSign == 1:
                offsets = [[0] * 3] * 2 + [[0] * 2 + [voff]] * 2 + [[0] * 3] * 4
                topSide = zstart + height
                btmSide = zstart
            else:
                offsets = [[0] * 2 + [voff]] * 2 + [[0] * 3] * 6
                topSide = zstart
                btmSide = zstart - height

            pointsToAffect = (0, 2)  # right
            bevelBlockOffsets(offsets, bev, pointsToAffect)

            avlist, aflist = MakeABlock([x + xstart + woffset, x + xstart + archBWG, btmSide, topSide, -depth / 2, depth / 2], subdivision, len(vlist), Offsets=offsets)

            # top didn't use radialized in prev version; just noting for clarity - may need to revise for "sideSign == 1"
            if settings['Radial']:
                for i, vert in enumerate(avlist):
                    avlist[i] = [((vert[0] - x) / vert[2]) + x, vert[1], vert[2]]

            vlist += avlist
            flist += aflist
