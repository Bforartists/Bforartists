# Stairbuilder - Retainer generation
#
# Generates retainers for stair generation.
#   Stair Type (typ):
#       - id1 = Freestanding staircase
#       - id2 = Housed-open staircase
#       - id3 = Box staircase
#       - id4 = Circular staircase
# 
# Paul "BrikBot" Marshall
# Created: September 19, 2011
# Last Modified: January 29, 2011
# Homepage (blog): http://post.darkarsenic.com/
#                       //blog.darkarsenic.com/
#
# Coded in IDLE, tested in Blender 2.61.
# Search for "@todo" to quickly find sections that need work.
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

from math import tan
from mathutils import Vector

class Rails:
    def __init__(self,G,w,t,h,tT,wP,dP,wT, rEnable, lEnable):
        self.G = G #General
        self.w=w #rail width
        self.t=t #rail thickness
        self.h=h #rail height
        self.start=Vector([0,0,self.h-self.t]) #rail start
        self.stop=G.stop+Vector([0,0,self.h-self.t]) #rail stop
        self.tT=tT #tread toe
        self.wP=wP #post width
        self.dP=dP #post depth
        self.wT=wT #tread width
        self.rEnable = rEnable
        self.lEnable = lEnable
        self.Create()

    def Create(self):
        #determine offset to include railing toe
        offset=Vector([self.tT,0,self.tT*tan(self.G.angle)])
        coords = []
        coords.append(self.start-offset)
        coords.append(self.stop+offset+Vector([self.dP,0,
                                               self.dP*tan(self.G.angle)]))
        coords.append(self.start-offset+Vector([0,self.w,0]))
        coords.append(self.stop+offset+Vector([self.dP,self.w,
                                               self.dP*tan(self.G.angle)]))
        for j in range(4):
            coords.append(coords[j]+Vector([0,0,self.t]))
        #centre over posts
        for j in coords:
            j += Vector([0,0.5*(-self.w+self.wP),0])
        if self.rEnable:
            self.G.Make_mesh(coords, self.G.faces, 'rails')
        if self.lEnable:
            #make rail on other side
            for j in coords:
                j += Vector([0,self.wT-self.wP,0])
            self.G.Make_mesh(coords, self.G.faces, 'rails')
