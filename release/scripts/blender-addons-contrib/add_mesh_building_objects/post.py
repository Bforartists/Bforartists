# Stairbuilder - Post generation
#
# Generates posts for stair generation.
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

from mathutils import Vector

class Posts:
    def __init__(self,G,rise,run,d,w,wT,nP,hR,tR, rEnable, lEnable):
        self.G = G #General
        self.rise = rise #Stair rise
        self.run = run #Stair run
        self.x1=Vector([0,0,hR-tR]) #rail start
        self.x2=G.stop+Vector([0,0,hR-tR]) #rail stop
        self.d=d #post depth
        self.w=w #post width
        self.wT=wT #tread width
        self.nP=nP #number of posts 
        self.sp=Vector([(self.x2[0]-self.x1[0])/float(nP+1),0,0]) #spacing between posts
        self.rEnable = rEnable
        self.lEnable = lEnable
        self.Create()

    def Intersect(self,i,d):
        """find intersection point, x, for rail and post"""
        x3=self.x1+i*self.sp+Vector([d,d,d])
        x4=x3+Vector([0,0,self.x2[-1]])
        a=self.x2-self.x1
        b=x4-x3
        c=x3-self.x1
        cr_ab=a.cross(b)
        mag_cr_ab=(cr_ab * cr_ab)
        return self.x1+a*((c.cross(b).dot(cr_ab))/mag_cr_ab)

    def Create(self):
        for i in range(0,self.nP+2,1):
            coords = []
            #intersections with rail
            coords.append(self.Intersect(i,0.0))
            coords.append(self.Intersect(i,self.d))
            #intersections with tread
            coords.append(Vector([self.x1[0]+i*self.sp[0],0,
                                  int(coords[0][0]/self.run)*self.rise]))
            coords.append(coords[2]+Vector([self.d,0,0]))
            #inner face
            for j in range(4):
                coords.append(coords[j]+Vector([0,self.w,0]))
            if self.rEnable:
                self.G.Make_mesh(coords, self.G.faces, 'posts')
            if self.lEnable:
                #make post on other side of steps as well
                for j in coords:
                    j += Vector([0,self.wT-self.w,0])
                self.G.Make_mesh(coords, self.G.faces, 'posts')
