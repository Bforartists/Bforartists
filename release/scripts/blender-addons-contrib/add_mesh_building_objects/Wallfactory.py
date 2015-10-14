# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you may redistribute it, and/or
# modify it, under the terms of the GNU General Public License
# as published by the Free Software Foundation - either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, write to:
#
#	the Free Software Foundation Inc.
#	51 Franklin Street, Fifth Floor
#	Boston, MA 02110-1301, USA
#
# or go online at: http://www.gnu.org/licenses/ to view license options.
#
# ***** END GPL LICENCE BLOCK *****

#
# This module contains the UI definition, display, and processing (create mesh)
# functions.
#
# The routines to generate the vertices for the wall are found in the "Blocks" module.
#


import bpy
import mathutils
from bpy.props import *
from add_mesh_building_objects.Blocks import *
#from add_mesh_walls.preset_utils import *


#
class add_mesh_wallb(bpy.types.Operator):
    """Add a wall mesh"""
    bl_idname = "mesh.wall_add"
    bl_label = "Add A Masonry Wall"
    bl_options = {'REGISTER', 'UNDO'} # removes object, does not reset to "last" modification.
    bl_description = "adds a block wall"

    # UI items - API for properties - User accessable variables... 
# not all options are via UI, and some operations just don't work yet.

    # only create object when True
    # False allows modifying several parameters without creating object
    ConstructTog = BoolProperty(name="Construct",
                                description="Generate the object",
                                default = True)

# need to modify so radial makes a tower (normal); want "flat" setting to make disk (alternate)
    # make the wall circular - if not sloped it's a flat disc
    RadialTog = BoolProperty(name="Radial",
                             description="Make masonry radial",
                             default = False)

    # curve the wall - if radial creates dome.
    SlopeTog = BoolProperty(name="Curved",
                            description="Make masonry sloped, or curved",
                            default = False)

#need to review defaults and limits for all of these UI objects.

    # wall area/size
    WallStart = FloatProperty(name="Start",
                              description="Left side, or start angle",
                              default=-10.0, min=-100, max=100.0)
    WallEnd = FloatProperty(name="End",
                            description="Right side, or end angle",
                            default=10.0, min=0.0, max=100.0)
    WallBottom = FloatProperty(name="Bottom",
                               description="Lower height or radius",
                               default=0.0, min=-100, max=100)
    WallTop = FloatProperty(name="Top",
                            description="Upper height or radius",
                            default=15.0, min=0.0, max=100.0)
    EdgeOffset = FloatProperty(name="Edging",
                               description="Block staggering on wall sides",
                               default=0.6, min=0.0, max=100.0)

    # block sizing
    Width = FloatProperty(name="Width",
                          description="Average width of each block",
                          default=1.5, min=0.01, max=100.0)
    WidthVariance = FloatProperty(name="Variance",
                                  description="Random variance of block width",
                                  default=0.5, min=0.0, max=100.0)
    WidthMinimum = FloatProperty(name="Minimum",
                                 description="Absolute minimum block width",
                                 default=0.5, min=0.01, max=100.0)
    Height = FloatProperty(name="Height",
                           description="Average Height of each block",
                           default=0.7, min=0.01, max=100.0)
    HeightVariance = FloatProperty(name="Variance",
                                   description="Random variance of block Height",
                                   default=0.3, min=0.0, max=100.0)
    HeightMinimum = FloatProperty(name="Minimum",
                                  description="Absolute minimum block Height",
                                  default=0.25, min=0.01, max=100.0)
    Depth = FloatProperty(name="Depth",
                          description="Average Depth of each block",
                          default=2.0, min=0.01, max=100.0)
    DepthVariance = FloatProperty(name="Variance",
                                  description="Random variance of block Depth",
                                  default=0.1, min=0.0, max=100.0)
    DepthMinimum = FloatProperty(name="Minimum",
                                 description="Absolute minimum block Depth",
                                 default=1.0, min=0.01, max=100.0)
    MergeBlock = BoolProperty(name="Merge Blocks",
                              description="Make big blocks (merge closely adjoining blocks)",
                              default = False)

    # edging for blocks
    Grout = FloatProperty(name="Thickness",
                          description="Distance between blocks",
                          default=0.1, min=-10.0, max=10.0)
    GroutVariance = FloatProperty(name="Variance",
                                  description="Random variance of block Grout",
                                  default=0.03, min=0.0, max=100.0)
    GroutDepth = FloatProperty(name="Depth",
                          description="Grout Depth from the face of the blocks",
                          default=0.1, min=0.0001, max=10.0)
    GroutDepthVariance = FloatProperty(name="Variance",
                                  description="Random variance of block Grout Depth",
                                  default=0.03, min=0.0, max=100.0)
    GroutEdge = BoolProperty(name="Edging",
                             description="Grout perimiter",
                             default = False)

    #properties for openings
    Opening1Tog = BoolProperty(name="Opening(s)",description="Make windows or doors", default = True)
    Opening1Width = FloatProperty(name="Width",
                                  description="The Width of opening 1",
                                  default=2.5, min=0.01, max=100.0)
    Opening1Height = FloatProperty(name="Height",
                                   description="The Height of opening 1",
                                   default=3.5, min=0.01, max=100.0)
    Opening1X = FloatProperty(name="Indent",
                              description="The x position or spacing of opening 1",
                              default=5.0, min=-100, max=100.0)
    Opening1Z = FloatProperty(name="Bottom",
                              description="The z position of opening 1",
                              default=5.0, min=-100, max=100.0)
    Opening1Repeat = BoolProperty(name="Repeat",
                                  description="make multiple openings, with spacing X1",
                                  default=False)
    Opening1TopArchTog = BoolProperty(name="Top Arch",
                                      description="Add an arch to the top of opening 1",
                                      default=True)
    Opening1TopArch = FloatProperty(name="Curve",
                                    description="Height of the arch on the top of the opening",
                                    default=2.5, min=0.001, max=100.0)
    Opening1TopArchThickness = FloatProperty(name="Thickness",
                                             description="Thickness of the arch on the top of the opening",
                                             default=0.75, min=0.001, max=100.0)
    Opening1BtmArchTog = BoolProperty(name="Bottom Arch",
                                      description="Add an arch to the bottom of opening 1",
                                      default=False)
    Opening1BtmArch = FloatProperty(name="Curve",
                                    description="Height of the arch on the bottom of the opening",
                                    default=1.0, min=0.01, max=100.0)
    Opening1BtmArchThickness = FloatProperty(name="Thickness",
                                             description="Thickness of the arch on the bottom of the opening",
                                             default=0.5, min=0.01, max=100.0)
    Opening1Bevel = FloatProperty(name="Bevel",
                                             description="Angle block face",
                                             default=0.25, min=-10.0, max=10.0)


    # openings on top of wall.
    CrenelTog = BoolProperty(name="Crenels",
                             description="Make openings along top of wall",
                             default = False)
    CrenelXP = FloatProperty(name="Width %",
                             description="Gap width in wall based % of wall width",
                             default=0.25, min=0.10, max=1.0)
    CrenelZP = FloatProperty(name="Height %",
                             description="Crenel Height as % of wall height",
                             default=0.10, min=0.10, max=1.0)


    # narrow openings in wall.
#need to prevent overlap with arch openings - though inversion is an interesting effect.
    SlotTog = BoolProperty(name="Slots",
                           description="Make narrow openings in wall",
                           default = False)
    SlotRpt = BoolProperty(name="Repeat",
                           description="Repeat slots along wall",
                           default = False)
    SlotWdg = BoolProperty(name="Wedged (n/a)",
                           description="Bevel edges of slots",
                           default = False)
    SlotX = FloatProperty(name="Indent",
                          description="The x position or spacing of slots",
                          default=0.0, min=-100, max=100.0)
    SlotGap = FloatProperty(name="Opening",
                            description="The opening size of slots",
                            default=0.5, min=0.10, max=100.0)
    SlotV = BoolProperty(name="Vertical",
                         description="Vertical slots",
                         default = True)
    SlotVH = FloatProperty(name="Height",
                           description="Height of vertical slot",
                           default=3.5, min=0.10, max=100.0)
    SlotVBtm = FloatProperty(name="Bottom",
                             description="Z position for slot",
                             default=5.00, min=-100.0, max=100.0)
    SlotH = BoolProperty(name="Horizontal",
                         description="Horizontal slots",
                         default = False)
    SlotHW = FloatProperty(name="Width",
                           description="Width of horizontal slot",
                           default=2.5, min=0.10, max=100.0)
#this should offset from VBtm... maybe make a % like crenels?
    SlotHBtm = FloatProperty(name="Bottom",
                             description="Z position for horizontal slot",
                             default=5.50, min=-100.0, max=100.0)


    #properties for shelf (extend blocks in area)
    ShelfTog = BoolProperty(name="Shelf",description="Add blocks in area by depth to make shelf/platform", default = False)
    ShelfX = FloatProperty(name="Left",
                              description="The x position of Shelf",
                              default=-5.00, min=-100, max=100.0)
    ShelfZ = FloatProperty(name="Bottom",
                              description="The z position of Shelf",
                              default=10.0, min=-100, max=100.0)
    ShelfH = FloatProperty(name="Height",
                                   description="The Height of Shelf area",
                                   default=1.0, min=0.01, max=100.0)
    ShelfW = FloatProperty(name="Width",
                                  description="The Width of shelf area",
                                  default=5.0, min=0.01, max=100.0)
    ShelfD = FloatProperty(name="Depth",
                          description="Depth of each block for shelf (from cursor + 1/2 wall depth)",
                          default=2.0, min=0.01, max=100.0)
    ShelfBack = BoolProperty(name="Backside",description="Shelf on backside of wall", default = False)


    #properties for steps (extend blocks in area, progressive width)
    StepTog = BoolProperty(name="Steps",description="Add blocks in area by depth with progressive width to make steps", default = False)
    StepX = FloatProperty(name="Left",
                              description="The x position of steps",
                              default=-9.00, min=-100, max=100.0)
    StepZ = FloatProperty(name="Bottom",
                              description="The z position of steps",
                              default=0.0, min=-100, max=100.0)
    StepH = FloatProperty(name="Height",
                                   description="The Height of step area",
                                   default=10.0, min=0.01, max=100.0)
    StepW = FloatProperty(name="Width",
                                  description="The Width of step area",
                                  default=8.0, min=0.01, max=100.0)
    StepD = FloatProperty(name="Depth",
                          description="Depth of each block for steps (from cursor + 1/2 wall depth)",
                          default=1.0, min=0.01, max=100.0)
    StepV = FloatProperty(name="Riser",
                                  description="Height of each step",
                                  default=0.70, min=0.01, max=100.0)
    StepT = FloatProperty(name="Tread",
                          description="Width of each step",
                          default=1.0, min=0.01, max=100.0)
    StepLeft = BoolProperty(name="High Left",description="Height left; else Height right", default = False)
    StepOnly = BoolProperty(name="No Blocks",description="Steps only, no supporting blocks", default = False)
    StepBack = BoolProperty(name="Backside",description="Steps on backside of wall", default = False)

##
##
#####
# Show the UI - expose the properties.
#####
##
##
    # Display the toolbox options

    def draw(self, context):

        layout = self.layout

        box = layout.box()
        box.prop(self, 'ConstructTog')

# Wall area (size/position)
        box = layout.box()
        box.label(text='Wall Size (area)')
        box.prop(self, 'WallStart')
        box.prop(self, 'WallEnd')
        box.prop(self, 'WallBottom')
        box.prop(self, 'WallTop')
        box.prop(self, 'EdgeOffset')

# Wall block sizing
        box = layout.box()
        box.label(text='Block Sizing')
        box.prop(self, 'MergeBlock')
#add checkbox for "fixed" sizing (ignore variance) a.k.a. bricks.
        box.prop(self, 'Width')
        box.prop(self, 'WidthVariance')
        box.prop(self, 'WidthMinimum')
        box.prop(self, 'Height')
        box.prop(self, 'HeightVariance')
        box.prop(self, 'HeightMinimum')
        box.prop(self, 'Depth')
        box.prop(self, 'DepthVariance')
        box.prop(self, 'DepthMinimum')

# grout settings
        box = layout.box()
        bl_label = "Grout"
        box.label(text='Grout')
        box.prop(self, 'Grout')
        box.prop(self, 'GroutVariance')
        box.prop(self, 'GroutDepth')
        box.prop(self, 'GroutDepthVariance')
#		box.prop(self, 'GroutEdge')

# Wall shape modifiers
        box = layout.box()
        box.label(text='Wall Shape')
        box.prop(self, 'RadialTog')
        box.prop(self, 'SlopeTog')

# Openings (doors, windows; arched)
        box = layout.box()
        box.prop(self, 'Opening1Tog')
        if self.properties.Opening1Tog:
            box.prop(self, 'Opening1Width')
            box.prop(self, 'Opening1Height')
            box.prop(self, 'Opening1X')
            box.prop(self, 'Opening1Z')
            box.prop(self, 'Opening1Bevel')
            box.prop(self, 'Opening1Repeat')
            box.prop(self, 'Opening1TopArchTog')
            box.prop(self, 'Opening1TopArch')
            box.prop(self, 'Opening1TopArchThickness')
            box.prop(self, 'Opening1BtmArchTog')
            box.prop(self, 'Opening1BtmArch')
            box.prop(self, 'Opening1BtmArchThickness')

# Slots (narrow openings)
        box = layout.box()
        box.prop(self, 'SlotTog')
        if self.properties.SlotTog:
#		box.prop(self, 'SlotWdg')
            box.prop(self, 'SlotX')
            box.prop(self, 'SlotGap')
            box.prop(self, 'SlotRpt')
            box.prop(self, 'SlotV')
            box.prop(self, 'SlotVH')
            box.prop(self, 'SlotVBtm')
            box.prop(self, 'SlotH')
            box.prop(self, 'SlotHW')
            box.prop(self, 'SlotHBtm')

# Crenels, gaps in top of wall
        box = layout.box()
        box.prop(self, 'CrenelTog')
        if self.properties.CrenelTog:
            box.prop(self, 'CrenelXP')
            box.prop(self, 'CrenelZP')

# Shelfing (protrusions)
        box = layout.box()
        box.prop(self, 'ShelfTog')
        if self.properties.ShelfTog:
            box.prop(self, 'ShelfX')
            box.prop(self, 'ShelfZ')
            box.prop(self, 'ShelfH')
            box.prop(self, 'ShelfW')
            box.prop(self, 'ShelfD')
            box.prop(self, 'ShelfBack')

# Steps
        box = layout.box()
        box.prop(self, 'StepTog')
        if self.properties.StepTog:
            box.prop(self, 'StepX')
            box.prop(self, 'StepZ')
            box.prop(self, 'StepH')
            box.prop(self, 'StepW')
            box.prop(self, 'StepD')
            box.prop(self, 'StepV')
            box.prop(self, 'StepT')
            box.prop(self, 'StepLeft')
            box.prop(self, 'StepOnly')
            box.prop(self, 'StepBack')

##
#####
# Respond to UI - get the properties set by user.
#####
##
    # Check and process UI settings to generate masonry

    def execute(self, context):

        global radialized
        global slope
        global openingSpecs
        global bigBlock
        global shelfExt
        global stepMod
        global stepLeft
        global shelfBack
        global stepOnly
        global stepBack

        # Create the wall when enabled (skip regen iterations when off)
        if not self.properties.ConstructTog: return {'FINISHED'}

        #enter the settings for the wall dimensions (area)
# start can't be zero - min/max don't matter [if max less than end] but zero don't workie.
# start can't exceed end.
        if not self.properties.WallStart or self.properties.WallStart >= self.properties.WallEnd:
            self.properties.WallStart = NOTZERO # Reset UI if input out of bounds...

        dims['s'] = self.properties.WallStart
        dims['e'] = self.properties.WallEnd
        dims['b'] = self.properties.WallBottom
        dims['t'] = self.properties.WallTop

        settings['eoff'] = self.properties.EdgeOffset

        #retrieve the settings for the wall block properties
        settings['w'] = self.properties.Width
        settings['wv'] = self.properties.WidthVariance
        settings['wm'] = self.properties.WidthMinimum
        if not radialized: settings['sdv'] = settings['w'] 
        else: settings['sdv'] = 0.12

        settings['h'] = self.properties.Height
        settings['hv'] = self.properties.HeightVariance
        settings['hm'] = self.properties.HeightMinimum

        settings['d'] = self.properties.Depth
        settings['dv'] = self.properties.DepthVariance
        settings['dm'] = self.properties.DepthMinimum

        if self.properties.MergeBlock:
            bigBlock = 1
        else: bigBlock = 0

        settings['g'] = self.properties.Grout
        settings['gv'] = self.properties.GroutVariance
        settings['gd'] = self.properties.GroutDepth
        settings['gdv'] = self.properties.GroutDepthVariance

        if self.properties.GroutEdge: settings['ge'] = 1
        else: settings['ge'] = 0

        # set wall shape modifiers
        if self.properties.RadialTog:
            radialized = 1
#eliminate to allow user control for start/completion?
            dims['s'] = 0.0 # complete radial
            if dims['e'] > PI*2: dims['e'] = PI*2 # max end for circle
            if dims['b'] < settings['g']: dims['b'] = settings['g'] # min bottom for grout extension
        else: radialized = 0

        if self.properties.SlopeTog: slope = 1
        else: slope = 0


        shelfExt = 0
        shelfBack = 0

	# Add shelf if enabled
        if self.properties.ShelfTog:
            shelfExt = 1
            shelfSpecs['h'] = self.properties.ShelfH
            shelfSpecs['w'] = self.properties.ShelfW
            shelfSpecs['d'] = self.properties.ShelfD
            shelfSpecs['x'] = self.properties.ShelfX
            shelfSpecs['z'] = self.properties.ShelfZ

            if self.properties.ShelfBack:
                shelfBack = 1


        stepMod = 0
        stepLeft = 0
        stepOnly = 0
        stepBack = 0

	# Make steps if enabled
        if self.properties.StepTog:
            stepMod = 1
            stepSpecs['x'] = self.properties.StepX
            stepSpecs['z'] = self.properties.StepZ
            stepSpecs['h'] = self.properties.StepH
            stepSpecs['w'] = self.properties.StepW
            stepSpecs['d'] = self.properties.StepD
            stepSpecs['v'] = self.properties.StepV
            stepSpecs['t'] = self.properties.StepT

            if self.properties.StepLeft:
                stepLeft = 1

            if self.properties.StepOnly:
                stepOnly = 1

            if self.properties.StepBack:
                stepBack = 1


        #enter the settings for the openings
#when openings overlap they create inverse stonework - interesting but not the desired effect :)
#if opening width == indent*2 the edge blocks fail (row of blocks cross opening) - bug.
        openingSpecs = []
        openingIdx = 0 # track opening array references for multiple uses

        # general openings with arch options - can be windows or doors.
        if self.properties.Opening1Tog:
            # set defaults...
            openingSpecs += [{'w':0.5, 'h':0.5, 'x':0.8, 'z':2.7, 'rp':1, 'b':0.0, 'v':0, 'vl':0, 't':0, 'tl':0}]

            openingSpecs[openingIdx]['w'] = self.properties.Opening1Width
            openingSpecs[openingIdx]['h'] = self.properties.Opening1Height
            openingSpecs[openingIdx]['x'] = self.properties.Opening1X
            openingSpecs[openingIdx]['z'] = self.properties.Opening1Z
            openingSpecs[openingIdx]['rp'] = self.properties.Opening1Repeat

            if self.properties.Opening1TopArchTog:
                openingSpecs[openingIdx]['v'] = self.properties.Opening1TopArch
                openingSpecs[openingIdx]['t'] = self.properties.Opening1TopArchThickness

            if self.properties.Opening1BtmArchTog:
                openingSpecs[openingIdx]['vl'] = self.properties.Opening1BtmArch
                openingSpecs[openingIdx]['tl'] = self.properties.Opening1BtmArchThickness
            
            openingSpecs[openingIdx]['b'] = self.properties.Opening1Bevel

            openingIdx += 1 # count window/door/arch openings

        # Slots (narrow openings)
        if self.properties.SlotTog:

            if self.properties.SlotV: # vertical slots
                # set defaults...
                openingSpecs += [{'w':0.5, 'h':0.5, 'x':0.0, 'z':2.7, 'rp':0, 'b':0.0, 'v':0, 'vl':0, 't':0, 'tl':0}]

                openingSpecs[openingIdx]['w'] = self.properties.SlotGap
                openingSpecs[openingIdx]['h'] = self.properties.SlotVH
                openingSpecs[openingIdx]['x'] = self.properties.SlotX
                openingSpecs[openingIdx]['z'] = self.properties.SlotVBtm
                openingSpecs[openingIdx]['rp'] = self.properties.SlotRpt

                # make them pointy...
                openingSpecs[openingIdx]['v'] = self.properties.SlotGap
                openingSpecs[openingIdx]['t'] = self.properties.SlotGap/2
                openingSpecs[openingIdx]['vl'] = self.properties.SlotGap
                openingSpecs[openingIdx]['tl'] = self.properties.SlotGap/2

                openingIdx += 1 # count vertical slot openings

# need to handle overlap of H and V slots...

            if self.properties.SlotH: # Horizontal slots
                # set defaults...
                openingSpecs += [{'w':0.5, 'h':0.5, 'x':0.0, 'z':2.7, 'rp':0, 'b':0.0, 'v':0, 'vl':0, 't':0, 'tl':0}]

                openingSpecs[openingIdx]['w'] = self.properties.SlotHW
                openingSpecs[openingIdx]['h'] = self.properties.SlotGap
                openingSpecs[openingIdx]['x'] = self.properties.SlotX
                openingSpecs[openingIdx]['z'] = self.properties.SlotHBtm
#horizontal repeat isn't same spacing as vertical...
                openingSpecs[openingIdx]['rp'] = self.properties.SlotRpt

                # make them pointy...
# want arc to go sideways... maybe wedge will be sufficient and can skip horiz arcs.
#				openingSpecs[openingIdx]['v'] = self.properties.SlotGap
#				openingSpecs[openingIdx]['t'] = self.properties.SlotGap/2
#				openingSpecs[openingIdx]['vl'] = self.properties.SlotGap
#				openingSpecs[openingIdx]['tl'] = self.properties.SlotGap/2

                openingIdx += 1 # count horizontal slot openings


        # Crenellations (top row openings)
        if self.properties.CrenelTog:

# add bottom arch option?
# perhaps a repeat toggle...
# if crenel opening overlaps with arch opening it fills with blocks...

            # set defaults...
            openingSpecs += [{'w':0.5, 'h':0.5, 'x':0.0, 'z':2.7, 'rp':1, 'b':0.0, 'v':0, 'vl':0, 't':0, 'tl':0}]

            wallW = self.properties.WallEnd - self.properties.WallStart
            crenelW = wallW*self.properties.CrenelXP # Width % opening.

            wallH = self.properties.WallTop - self.properties.WallBottom
            crenelH = wallH*self.properties.CrenelZP # % proportional height.

            openingSpecs[openingIdx]['w'] = crenelW
            openingSpecs[openingIdx]['h'] = crenelH

            # calculate the spacing between openings.
            # this isn't the absolute start (left), it's opening center offset relative to cursor (space between openings)...
            openingSpecs[openingIdx]['x'] = crenelW*2-1 # assume standard spacing

            if not radialized: # normal wall?
                # set indent 0 (center) if opening is 50% or more of wall width, no repeat.
                if crenelW*2 >= wallW:
                    openingSpecs[openingIdx]['x'] = 0
                    openingSpecs[openingIdx]['rp'] = 0

            openingSpecs[openingIdx]['z'] = self.properties.WallTop - (crenelH/2) # set bottom of opening (center of hole)

            openingIdx += 1 # count crenel openings

        #
        # Process the user settings to generate a wall
        #
        # generate the list of vertices for the wall...
        verts_array, faces_array = createWall(radialized, slope, openingSpecs, bigBlock,
                shelfExt, shelfBack, stepMod, stepLeft, stepOnly, stepBack)

        # Create new mesh
        mesh = bpy.data.meshes.new("Wall")

        # Make a mesh from a list of verts/edges/faces.
        mesh.from_pydata(verts_array, [], faces_array)

        scene = context.scene

        # Deselect all objects.
        bpy.ops.object.select_all(action='DESELECT')

        mesh.update()

        ob_new = bpy.data.objects.new("Wall", mesh)
        scene.objects.link(ob_new)
# leave this out to prevent 'Tab key" going into edit mode :):):)
# Use rmb click to select and still modify.
        scene.objects.active = ob_new
        ob_new.select = True

        ob_new.location = tuple(context.scene.cursor_location)
        ob_new.rotation_quaternion = [1.0,0.0,0.0,0.0]

        return {'FINISHED'}
