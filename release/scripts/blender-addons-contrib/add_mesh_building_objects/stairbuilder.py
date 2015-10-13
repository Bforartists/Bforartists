# Stairs and railing creator script for blender 2.49
# Author: Nick van Adium
# Date: 2010 08 09
# 
# Creates a straight-run staircase with railings and stringer
# All components are optional and can be turned on and off by setting e.g. makeTreads=True or makeTreads=False
# No GUI for the script, all parameters must be defined below
# Current values assume 1 blender unit = 1 metre
# 
# Stringer will rest on lower landing and hang from upper landing
# Railings start on the lowest step and end on the upper landing
# 
# NOTE: You must have numpy installed for this script to work!
#       numpy is used to easily perform the necessary algebra
#       numpy can be found at http://www.scipy.org/Download
# 
# Note: I'm not sure how to use recalcNormals so not all normals points ouwards.
#       Perhaps someone else can contribute this.
#
#-----------------------------------------------------------
#
# Converted to Blender 2.5:
#   - Still uses NumPy.
#   - Classes are basically copy-paste from the original code
#   - New Make_mesh copied from BrikBot's rock generator
#   - Implemented standard add mesh GUI.
#   @todo:
#   - global vs. local needs cleaned up.
#   - Join separate stringer objects and then clean up the mesh.
#   - Put all objects into a group.
#   - Generate left/right posts/railings/retainers separatly with
#       option to disable just the left/right.
#   - Add wall railing type as an option for left/right
#   - Add different rail styles (profiles).  Select with enum.
#   - Should have a non-NumPy code path for cross-compatability.
#       - Could be another file with equivalent classes/functions?
#           Then we would just import from there instead of from
#           NumPy without having to change the actual code.  It
#           would instead be a "try-except" block that trys to use
#           NumPy.
#   - Would like to add additional staircase types.
#       - Spiral staircase
#       - "L" staircase
#       - "T" staircase
#
# Last Modified By: Paul "brikbot" Marshall
# Last Modification: January 29, 2011
#
# ##### BEGIN GPL LICENSE BLOCK #####
#
#  Stairbuilder is for quick stair generation.
#  Copyright (C) 2011  Paul Marshall
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####

#-----------------------------------------------------------
# BEGIN NEW B2.5/Py3.2 CODE
import bpy
from add_mesh_building_objects.general import General
from add_mesh_building_objects.post import Posts
from add_mesh_building_objects.rail import Rails
from add_mesh_building_objects.retainer import Retainers
from add_mesh_building_objects.stringer import Stringer
from add_mesh_building_objects.tread import Treads
from bpy.props import (BoolProperty,
                       EnumProperty,
                       IntProperty,
                       FloatProperty)
from mathutils import Vector

global G
global typ
global typ_s
global typ_t
global rise
global run               
            
class stairs(bpy.types.Operator):
    """Add stair objects"""
    bl_idname = "mesh.stairs"
    bl_label = "Add Stairs"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Add stairs"

    # Stair types for enum:
    id1 = ("id1", "Freestanding", "Generate a freestanding staircase.")
    id2 = ("id2", "Housed-Open", "Generate a housed-open staircase.")
    id3 = ("id3", "Box", "Generate a box staircase.")
    id4 = ("id4", "Circular", "Generate a circular or spiral staircase.")

    # Tread types for enum:
    tId1 = ("tId1", "Classic", "Generate wooden style treads")
    tId2 = ("tId2", "Basic Steel", "Generate common steel style treads")
    tId3 = ("tId3", "Bar 1", "Generate bar/slat steel treads")
    tId4 = ("tId4", "Bar 2", "Generate bar-grating steel treads")
    tId5 = ("tId5", "Bar 3", "Generate bar-support steel treads")

    # Stringer types for enum:
    sId1 = ("sId1", "Classic", "Generate a classic style stringer")
    sId2 = ("sId2", "I-Beam", "Generate a steel I-beam stringer")
    sId3 = ("sId3", "C-Beam", "Generate a C-channel style stringer")
    
    typ = EnumProperty(name = "Type",
                       description = "Type of staircase to generate",
                       items = [id1, id2, id3, id4])

    rise = FloatProperty(name = "Rise",
                         description = "Single tread rise",
                         min = 0.0, max = 1024.0,
                         default = 0.20)
    run = FloatProperty(name = "Run",
                        description = "Single tread run",
                        min = 0.0, max = 1024.0,
                        default = 0.30)

    #for circular
    rad1 = FloatProperty(name = "Inner Radius",
                         description = "Inner radius for circular staircase",
                         min = 0.0, max = 1024.0,
                         soft_max = 10.0,
                         default = 0.25)
    rad2 = FloatProperty(name = "Outer Radius",
                         description = "Outer radius for circular staircase",
                         min = 0.0, max = 1024.0,
                         soft_min = 0.015625, soft_max = 32.0,
                         default = 1.0)
    deg = FloatProperty(name = "Degrees",
                        description = "Number of degrees the stairway rotates",
                        min = 0.0, max = 92160.0, step = 5.0,
                        default = 450.0)
    center = BoolProperty(name = "Center Pillar",
                          description = "Generate a central pillar",
                          default = False)

    #for treads
    make_treads = BoolProperty(name = "Make Treads",
                              description = "Enable tread generation",
                              default = True)
    tread_w = FloatProperty(name = "Tread Width",
                            description = "Width of each generated tread",
                            min = 0.0001, max = 1024.0,
                            default = 1.2)
    tread_h = FloatProperty(name = "Tread Height",
                            description = "Height of each generated tread",
                            min = 0.0001, max = 1024.0,
                            default = 0.04)
    tread_t = FloatProperty(name = "Tread Toe",
                            description = "Toe (aka \"nosing\") of each generated tread",
                            min = 0.0, max = 10.0,
                            default = 0.03)
    tread_o = FloatProperty(name = "Tread Overhang",
                            description = "How much tread \"overhangs\" the sides",
                            min = 0.0, max = 1024.0,
                            default = 0.025)
    tread_n = IntProperty(name = "Number of Treads",
                          description = "How many treads to generate",
                          min = 1, max = 1024,
                          default = 10)
    typ_t = EnumProperty(name = "Tread Type",
                         description = "Type/style of treads to generate",
                         items = [tId1, tId2, tId3, tId4, tId5])
    tread_tk = FloatProperty(name = "Thickness",
                             description = "Thickness of the treads",
                             min = 0.0001, max = 10.0,
                             default = 0.02)
    tread_sec = IntProperty(name = "Sections",
                            description = "Number of sections to use for tread",
                            min = 1, max = 1024,
                            default = 5)
    tread_sp = IntProperty(name = "Spacing",
                           description = "Total spacing between tread sections as a percentage of total tread width",
                           min = 0, max = 80,
                           default = 5)
    tread_sn = IntProperty(name = "Crosses",
                           description = "Number of cross section supports",
                           min = 2, max = 1024,
                           default = 4)
    #special circular tread properties:
    tread_slc = IntProperty(name = "Slices",
                            description = "Number of slices each tread is composed of",
                            min = 1, max = 1024,
                            soft_max = 16,
                            default = 4)

    #for posts
    make_posts = BoolProperty(name = "Make Posts",
                              description = "Enable post generation",
                              default = True)
    post_d = FloatProperty(name = "Post Depth",
                           description = "Depth of generated posts",
                           min = 0.0001, max = 10.0,
                           default = 0.04)
    post_w = FloatProperty(name = "Post Width",
                           description = "Width of generated posts",
                           min = 0.0001, max = 10.0,
                           default = 0.04)
    post_n = IntProperty(name = "Number of Posts",
                         description = "Number of posts to generated",
                         min = 1, max = 1024,
                         default = 5)

    #for railings
    make_railings = BoolProperty(name = "Make Railings",
                                 description = "Generate railings",
                                 default = True)
    rail_w = FloatProperty(name = "Railings Width",
                           description = "Width of railings to generate",
                           min = 0.0001, max = 10.0,
                           default = 0.12)
    rail_t = FloatProperty(name = "Railings Thickness",
                           description = "Thickness of railings to generate",
                           min = 0.0001, max = 10.0,
                           default = 0.03)
    rail_h = FloatProperty(name = "Railings Height",
                           description = "Height of railings to generate",
                           min = 0.0001, max = 10.0,
                           default = 0.90)

    #for retainers
    make_retainers = BoolProperty(name = "Make Retainers",
                                  description = "Generate retainers",
                                  default = True)
    ret_w = FloatProperty(name = "Retainer Width",
                          description = "Width of generated retainers",
                          min = 0.0001, max = 10.0,
                          default = 0.01)
    ret_h = FloatProperty(name = "Retainer Height",
                          description = "Height of generated retainers",
                          min = 0.0001, max = 10.0,
                          default = 0.01)
    ret_n = IntProperty(name = "Number of Retainers",
                        description = "Number of retainers to generated",
                        min = 1, max = 1024,
                        default = 3)

    #for stringer
    make_stringer = BoolProperty(name = "Make Stringer",
                                 description = "Generate stair stringer",
                                 default = True)
    typ_s = EnumProperty(name = "Stringer Type",
                         description = "Type/style of stringer to generate",
                         items = [sId1, sId2, sId3])
    string_n = IntProperty(name = "Number of Stringers",
                           description = "Number of stringers to generate",
                           min = 1, max = 10,
                           default = 1)
    string_dis = BoolProperty(name = "Distributed",
                              description = "Use distributed stringers",
                              default = False)
    string_w = FloatProperty(name = "Stringer width",
                             description = "Width of stringer as a percentage of tread width",
                             min = 0.0001, max = 100.0,
                             default = 15.0)
    string_h = FloatProperty(name = "Stringer Height",
                             description = "Height of the stringer",
                             min = 0.0001, max = 100.0,
                             default = 0.3)
    string_tw = FloatProperty(name = "Web Thickness",
                              description = "Thickness of the beam's web as a percentage of width",
                              min = 0.0001, max = 100.0,
                              default = 25.0)
    string_tf = FloatProperty(name = "Flange Thickness",
                              description = "Thickness of the flange",
                              min = 0.0001, max = 100.0,
                              default = 0.05)
    string_tp = FloatProperty(name = "Flange Taper",
                              description = "Flange thickness taper as a percentage",
                              min = 0.0, max = 100.0,
                              default = 0.0)
    string_g = BoolProperty(name = "Floating",
                            description = "Cut bottom of strigner to be a \"floating\" section",
                            default = False)

    use_original = BoolProperty(name = "Use legacy method",
                                description = "Use the Blender 2.49 legacy method for stair generation",
                                default = True)
    rEnable = BoolProperty(name = "Right Details",
                           description = "Generate right side details (posts/rails/retainers)",
                           default = True)
    lEnable = BoolProperty(name = "Left Details",
                           description = "Generate left side details (posts/rails/retainers)",
                           default = True)

    # Draw the GUI:
    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.prop(self, 'typ')
        box = layout.box()
        box.prop(self, 'rise')
        if self.typ != "id4":
            box.prop(self, 'run')
        else:
            box.prop(self, 'deg')
            box.prop(self, 'rad1')
            box.prop(self, 'rad2')
            box.prop(self, 'center')
        if self.typ == "id1":
            box.prop(self, 'use_original')
            if not self.use_original:
                box.prop(self, 'rEnable')
                box.prop(self, 'lEnable')
        else:
            self.use_original = False
            box.prop(self, 'rEnable')
            box.prop(self, 'lEnable')
            
        # Treads
        box = layout.box()
        box.prop(self, 'make_treads')
        if self.make_treads:
            if not self.use_original and self.typ != "id4":
                box.prop(self, 'typ_t')
            else:
                self.typ_t = "tId1"
            if self.typ != "id4":
                box.prop(self, 'tread_w')
            box.prop(self, 'tread_h')
            box.prop(self, 'tread_t')
            if self.typ not in ["id2", "id4"]:
                box.prop(self, 'tread_o')
            else:
                self.tread_o = 0.0
            box.prop(self, 'tread_n')
            if self.typ_t != "tId1":
                box.prop(self, 'tread_tk')
                box.prop(self, 'tread_sec')
                if self.tread_sec > 1 and self.typ_t not in ["tId3", "tId4"]:
                    box.prop(self, 'tread_sp')
                if self.typ_t in ["tId3", "tId4", "tId5"]:
                    box.prop(self, 'tread_sn')
            elif self.typ == "id4":
                box.prop(self, "tread_slc")
                    
        # Posts
        box = layout.box()
        box.prop(self, 'make_posts')
        if self.make_posts:
            box.prop(self, 'post_d')
            box.prop(self, 'post_w')
            box.prop(self, 'post_n')
            
        # Railings
        box = layout.box()
        box.prop(self, 'make_railings')
        if self.make_railings:
            box.prop(self, 'rail_w')
            box.prop(self, 'rail_t')
            box.prop(self, 'rail_h')
            
        # Retainers
        box = layout.box()
        box.prop(self, 'make_retainers')
        if self.make_retainers:
            box.prop(self, 'ret_w')
            box.prop(self, 'ret_h')
            box.prop(self, 'ret_n')
            
        # Stringers
        box = layout.box()
        if self.typ != "id2":
            box.prop(self, 'make_stringer')
        else:
            self.make_stringer = True
        if self.make_stringer:
            if not self.use_original:
                box.prop(self, 'typ_s')
            else:
                self.typ_s = "sId1"
            box.prop(self, 'string_w')
            if self.typ == "id1":
                if self.typ_s == "sId1" and not self.use_original:
                    box.prop(self, 'string_n')
                    box.prop(self, 'string_dis')
                elif self.typ_s in ["sId2", "sId3"]:
                    box.prop(self, 'string_n')
                    box.prop(self, 'string_dis')
                    box.prop(self, 'string_h')
                    box.prop(self, 'string_tw')
                    box.prop(self, 'string_tf')
                    box.prop(self, 'string_tp')
                    box.prop(self, 'string_g')
            elif self.typ == "id2":
                if self.typ_s in ["sId2", "sId3"]:
                    box.prop(self, 'string_tw')
                    box.prop(self, 'string_tf')

        # Tread support:
##        if self.make_stringer and typ_s in ["sId2", "sId3"]:

    def execute(self, context):
        global G
        global typ
        global typ_s
        global typ_t
        global rise
        global run
        typ = self.typ
        typ_s = self.typ_s
        typ_t = self.typ_t
        rise = self.rise
        run = self.run
        G=General(rise,run,self.tread_n)
        if self.make_treads:
            if typ != "id4":
                Treads(G,
                       typ,
                       typ_t,
                       run,
                       self.tread_w,
                       self.tread_h,
                       self.run,
                       self.rise,
                       self.tread_t,
                       self.tread_o,
                       self.tread_n,
                       self.tread_tk,
                       self.tread_sec,
                       self.tread_sp,
                       self.tread_sn)
            else:
                Treads(G,
                       typ,
                       typ_t,
                       self.deg,
                       self.rad2,
                       self.tread_h,
                       self.run,
                       self.rise,
                       self.tread_t,
                       self.rad1,
                       self.tread_n,
                       self.tread_tk,
                       self.tread_sec,
                       self.tread_sp,
                       self.tread_sn,
                       self.tread_slc)
        if self.make_posts and (self.rEnable or self.lEnable):
            Posts(G,
                  rise,
                  run,
                  self.post_d,
                  self.post_w,
                  self.tread_w,
                  self.post_n,
                  self.rail_h,
                  self.rail_t,
                  self.rEnable,
                  self.lEnable)
        if self.make_railings and (self.rEnable or self.lEnable):
            Rails(G,
                  self.rail_w,
                  self.rail_t,
                  self.rail_h,
                  self.tread_t,
                  self.post_w,
                  self.post_d,
                  self.tread_w,
                  self.rEnable,
                  self.lEnable)
        if self.make_retainers and (self.rEnable or self.lEnable):
            Retainers(G,
                      self.ret_w,
                      self.ret_h,
                      self.post_w,
                      self.tread_w,
                      self.rail_h,
                      self.ret_n,
                      self.rEnable,
                      self.lEnable)
        if self.make_stringer:
            if typ == "id1" and self.use_original:
                Stringer(G,
                         typ,
                         typ_s,
                         rise,
                         run,
                         self.string_w,
                         self.string_h,
                         self.tread_n,
                         self.tread_h,
                         self.tread_w,
                         self.tread_t,
                         self.tread_o,
                         self.string_tw,
                         self.string_tf,
                         self.string_tp,
                         not self.string_g)
            elif typ == "id3":
                Stringer(G,
                         typ,
                         typ_s,
                         rise,
                         run,
                         100,
                         self.string_h,
                         self.tread_n,
                         self.tread_h,
                         self.tread_w,
                         self.tread_t,
                         self.tread_o,
                         self.string_tw,
                         self.string_tf,
                         self.string_tp,
                         not self.string_g,
                         1, False, False)
            elif typ == "id4":
                Stringer(G,
                         typ,
                         typ_s,
                         rise,
                         self.deg,
                         self.string_w,
                         self.string_h,
                         self.tread_n,
                         self.tread_h,
                         self.rad2 - self.rad1,
                         self.tread_t,
                         self.rad1,
                         self.string_tw,
                         self.string_tf,
                         self.string_tp,
                         not self.string_g,
                         self.string_n,
                         self.string_dis,
                         self.use_original,
                         self.tread_slc)
            else:
                Stringer(G,
                         typ,
                         typ_s,
                         rise,
                         run,
                         self.string_w,
                         self.string_h,
                         self.tread_n,
                         self.tread_h,
                         self.tread_w,
                         self.tread_t,
                         self.tread_o,
                         self.string_tw,
                         self.string_tf,
                         self.string_tp,
                         not self.string_g,
                         self.string_n,
                         self.string_dis,
                         self.use_original)
        return {'FINISHED'}
