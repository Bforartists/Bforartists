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

# <pep8 compliant>

import bpy
import os
from bpy.types import Operator
from bpy.props import BoolProperty



def ObjectDistributeOscurart(self, X, Y, Z):
    if len(bpy.selection_osc[:]) > 1:
        # VARIABLES
        dif = bpy.selection_osc[-1].location - bpy.selection_osc[0].location
        chunkglobal = dif / (len(bpy.selection_osc[:]) - 1)
        chunkx = 0
        chunky = 0
        chunkz = 0
        deltafst = bpy.selection_osc[0].location

        # ORDENA
        for OBJECT in bpy.selection_osc[:]:
            if X:
                OBJECT.location.x = deltafst[0] + chunkx
            if Y:
                OBJECT.location[1] = deltafst[1] + chunky
            if Z:
                OBJECT.location.z = deltafst[2] + chunkz
            chunkx += chunkglobal[0]
            chunky += chunkglobal[1]
            chunkz += chunkglobal[2]
    else:
        self.report({'INFO'}, "Needs at least two selected objects")


class DistributeOsc(Operator):
    """Distribute evenly the selected objects in x y z"""
    bl_idname = "object.distribute_osc"
    bl_label = "Distribute Objects"
    Boolx : BoolProperty(name="X")
    Booly : BoolProperty(name="Y")
    Boolz : BoolProperty(name="Z")

    def execute(self, context):
        ObjectDistributeOscurart(self, self.Boolx, self.Booly, self.Boolz)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.Boolx = True
        self.Booly = True
        self.Boolz = True
        return context.window_manager.invoke_props_dialog(self)

