# Stairbuilder - Tread generation
#
# Generates treads for stair generation.
#   Stair Type (typ):
#       - id1 = Freestanding staircase
#       - id2 = Housed-open staircase
#       - id3 = Box staircase
#       - id4 = Circular staircase
#   Tread Type (typ_t):
#       - tId1 = Classic
#       - tId2 = Basic Steel
#       - tId3 = Bar 1
#       - tId4 = Bar 2
#       - tId5 = Bar 3
# 
# Paul "BrikBot" Marshall
# Created: September 19, 2011
# Last Modified: January 26, 2012
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

import mathutils
from copy import copy
from math import radians, sqrt
from mathutils import Matrix, Vector

class Treads:
    def __init__(self,G,typ,typ_t,run,w,h,d,r,toe,o,n,tk,sec,sp,sn,deg=4):
        self.G = G #General
        self.typ = typ #Stair type
        self.typ_t = typ_t #Tread type
        self.run = run #Stair run.  Degrees if self.typ == "id4"
        self.w=w #tread width.  Is outer radius if self.typ == "id4"
        self.h=h #tread height
        self.d=d #tread run.  Ignore for now if self.typ == "id4"
        self.r=r #tread rise
        self.t=toe #tread nosing
        self.o=o #tread side overhang.  Is inner radius if self.typ == "id4"
        self.n=n #number of treads
        self.tk=tk #thickness of tread metal
        self.sec=sec #metal sections for tread
        if sec != 1 and typ_t not in ["tId4", "tId5"]:
            self.sp=((d+toe)*(sp/100))/(sec-1) #spacing between sections (% of depth)
        elif typ_t in ["tId4", "tId5"]:
            self.sp=sp/100 #keep % value
        else:
            self.sp=0
        self.sn=sn #number of cross sections
        self.deg = deg #number of section per "slice".  Only applys if self.typ == "id4"
        self.tId2_faces = [[0,1,2,3],[0,3,4,5],[4,5,6,7],[6,7,8,9],[8,9,10,11],
                           [12,13,14,15],[12,15,16,17],[16,17,18,19],
                           [18,19,20,21],[20,21,22,23],[0,1,13,12],[1,2,14,13],
                           [2,3,15,14],[3,4,16,15],[4,7,19,16],[7,8,20,19],
                           [8,11,23,20],[11,10,22,23],[10,9,21,22],[9,6,18,21],
                           [6,5,17,18],[5,0,12,17]]
        self.out_faces = [[0,2,3,1],[0,2,10,8],[9,11,3,1],[9,11,10,8],
                          [2,6,7,3],[2,6,14,10],[11,15,7,3],[11,15,14,10],
                          [0,4,5,1],[0,4,12,8],[9,13,5,1],[9,13,12,8],
                          [4,6,7,5],[4,6,14,12],[13,15,14,12],[13,15,7,5]]
        self.Create()

    def Create(self):
        # Setup the coordinates:
        coords = []
        coords2 = []
        coords3 = []
        cross = 0
        cW = 0
        depth = 0
        offset = 0
        height = 0
        if self.typ in ["id1", "id2", "id3"]:
            if self.typ_t == "tId1":
                coords.append(Vector([-self.t,-self.o,0]))
                coords.append(Vector([self.d,-self.o,0]))
                coords.append(Vector([-self.t,self.w + self.o,0]))
                coords.append(Vector([self.d,self.w + self.o,0]))
                for i in range(4):
                    coords.append(coords[i]+Vector([0,0,-self.h]))

            elif self.typ_t == "tId2":
                depth = (self.d + self.t - (self.sec - 1) * self.sp) / self.sec
                inset = depth / 4
                tDepth = depth - self.t
                coords.append(Vector([-self.t, -self.o, -self.h]))                          #0
                coords.append(Vector([inset - self.t, -self.o, -self.h]))           #1
                coords.append(Vector([inset - self.t, -self.o, -self.h + self.tk])) #2
                coords.append(Vector([self.tk - self.t, -self.o, -self.h + self.tk]))       #3
                coords.append(Vector([self.tk - self.t, -self.o, -self.tk]))                #4
                coords.append(Vector([-self.t, -self.o, 0]))                                #5
                coords.append(Vector([tDepth, -self.o, 0]))                                 #6
                coords.append(Vector([tDepth - self.tk, -self.o, -self.tk]))                #7
                coords.append(Vector([tDepth - self.tk, -self.o, self.tk - self.h]))        #8
                coords.append(Vector([tDepth, -self.o, -self.h]))                           #9
                coords.append(Vector([tDepth - inset, -self.o, -self.h]))           #10
                coords.append(Vector([tDepth - inset, -self.o, -self.h + self.tk])) #11
                for i in range(12):
                    coords.append(coords[i] + Vector([0, self.w + (2 * self.o), 0]))
            
            elif self.typ_t in ["tId3", "tId4", "tId5"]:
                # Frame:
                coords.append(Vector([-self.t,-self.o,-self.h]))
                coords.append(Vector([self.d,-self.o,-self.h]))
                coords.append(Vector([-self.t,-self.o,0]))
                coords.append(Vector([self.d,-self.o,0]))
                for i in range(4):
                    if (i % 2) == 0:
                        coords.append(coords[i] + Vector([self.tk,self.tk,0]))
                    else:
                        coords.append(coords[i] + Vector([-self.tk,self.tk,0]))
                for i in range(4):
                    coords.append(coords[i] + Vector([0,self.w + self.o,0]))
                for i in range(4):
                    coords.append(coords[i + 4] + Vector([0,self.w + self.o - (2 * self.tk),0]))

                # Tread sections:
                if self.typ_t == "tId3":
                    offset = (self.tk * sqrt(2)) / 2
                    topset = self.h - offset
                    self.sp = ((self.d + self.t - (2 * self.tk)) - (offset * (self.sec) + topset)) / (self.sec + 1)
                    baseX = -self.t + self.sp + self.tk
                    coords2.append(Vector([baseX, self.tk - self.o, offset - self.h]))
                    coords2.append(Vector([baseX + offset, self.tk - self.o, -self.h]))
                    for i in range(2):
                        coords2.append(coords2[i] + Vector([topset, 0, topset]))
                    for i in range(4):
                        coords2.append(coords2[i] + Vector([0, (self.w + self.o) - (2 * self.tk), 0]))
                elif self.typ_t in ["tId4", "tId5"]:
                    offset = ((self.run + self.t) * self.sp) / (self.sec + 1)
                    topset = (((self.run + self.t) * (1 - self.sp)) - (2 * self.tk)) / self.sec
                    baseX = -self.t + self.tk + offset
                    baseY = self.w + self.o - 2 * self.tk
                    coords2.append(Vector([baseX, -self.o + self.tk, -self.h / 2]))
                    coords2.append(Vector([baseX + topset, -self.o + self.tk, -self.h / 2]))
                    coords2.append(Vector([baseX, -self.o + self.tk, 0]))
                    coords2.append(Vector([baseX + topset, -self.o + self.tk, 0]))
                    for i in range(4):
                        coords2.append(coords2[i] + Vector([0, baseY, 0]))

                # Tread cross-sections:
                if self.typ_t in ["tId3", "tId4"]:
                    cW = self.tk
                    cross = (self.w + (2 * self.o) - (self.sn + 2) * self.tk) / (self.sn + 1)
                else: # tId5
                    spacing = self.sp ** (1 / 4)
                    cross = ((2*self.o + self.w) * spacing) / (self.sn + 1)
                    cW = (-2*self.tk + (2*self.o + self.w) * (1 - spacing)) / self.sn
                    self.sp = topset
                    height = -self.h / 2
                baseY = -self.o + self.tk + cross
                coords3.append(Vector([-self.t + self.tk, baseY, -self.h]))
                coords3.append(Vector([self.d - self.tk, baseY, -self.h]))
                coords3.append(Vector([-self.t + self.tk, baseY, height]))
                coords3.append(Vector([self.d - self.tk, baseY, height]))
                for i in range(4):
                    coords3.append(coords3[i] + Vector([0, cW, 0]))

            # Make the treads:
            for i in range(self.n):
                if self.typ_t == "tId1":
                    self.G.Make_mesh(coords,self.G.faces,'treads')
                elif self.typ_t == "tId2":
                    temp = []
                    for j in coords:
                        temp.append(copy(j))
                    for j in range(self.sec):
                        self.G.Make_mesh(temp, self.tId2_faces, 'treads')
                        for k in temp:
                            k += Vector([depth + self.sp, 0, 0])
                elif self.typ_t in ["tId3", "tId4", "tId5"]:
                    self.G.Make_mesh(coords,self.out_faces,'treads')
                    temp = []
                    for j in coords2:
                        temp.append(copy(j))
                    for j in range(self.sec):
                        self.G.Make_mesh(temp,self.G.faces,'bars')
                        for k in temp:
                            k += Vector([offset + self.sp, 0, 0])
                    for j in coords2:
                        j += Vector([self.d, 0, self.r])
                    temp = []
                    for j in coords3:
                        temp.append(copy(j))
                    for j in range(self.sn):
                        self.G.Make_mesh(temp,self.G.faces,'crosses')
                        for k in temp:
                            k += Vector([0, cW + cross, 0])
                    for j in coords3:
                        j += Vector([self.d, 0, self.r])
                for j in coords:
                    j += Vector([self.d,0,self.r])
        # Circular staircase:
        elif self.typ in ["id4"]:
            start = [Vector([0, -self.o, 0]), Vector([0, -self.o, -self.h]),
                     Vector([0, -self.w, 0]), Vector([0, -self.w, -self.h])]
            self.d = radians(self.run) / self.n
            for i in range(self.n):
                coords = []
                # Base faces.  Should be able to append more sections:
                tId4_faces = [[0, 1, 3, 2]]
                t_inner = Matrix.Rotation((-self.t / self.o) + (self.d * i), 3, 'Z')
                coords.append((t_inner * start[0]) + Vector([0, 0, self.r * i]))
                coords.append((t_inner * start[1]) + Vector([0, 0, self.r * i]))
                t_outer = Matrix.Rotation((-self.t / self.w) + (self.d * i), 3, 'Z')
                coords.append((t_outer * start[2]) + Vector([0, 0, self.r * i]))
                coords.append((t_outer * start[3]) + Vector([0, 0, self.r * i]))
                k = 0
                for j in range(self.deg + 1):
                    k = (j * 4) + 4
                    tId4_faces.append([k, k - 4, k - 3, k + 1])
                    tId4_faces.append([k - 2, k - 1, k + 3, k + 2])
                    tId4_faces.append([k + 1, k - 3, k - 1, k + 3])
                    tId4_faces.append([k, k - 4, k - 2, k + 2])
                    rot = Matrix.Rotation(((self.d * j) / self.deg) + (self.d * i), 3, 'Z')
                    for v in start:
                        coords.append((rot * v) + Vector([0, 0, self.r * i]))
                tId4_faces.append([k, k + 1, k + 3, k + 2])
                self.G.Make_mesh(coords, tId4_faces, 'treads')
        return
