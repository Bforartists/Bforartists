# Stairbuilder - Stringer generation
#
# Generates stringer mesh for stair generation.
#   Stair Type (typ):
#       - id1 = Freestanding staircase
#       - id2 = Housed-open staircase
#       - id3 = Box staircase
#       - id4 = Circular staircase
#   Stringer Type (typ_s):
#       - sId1 = Classic
#       - sId2 = I-Beam
#       - sId3 = C-Beam
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

from math import atan, cos, radians, tan
from mathutils import Matrix, Vector
from mathutils.geometry import (intersect_line_plane,
                                intersect_line_line)

class Stringer:
    def  __init__(self,G,typ,typ_s,rise,run,w,h,nT,hT,wT,tT,tO,tw,tf,tp,g,
                  nS=1,dis=False,notMulti=True,deg=4):
        self.G = G #General
        self.typ = typ # Stair type
        self.typ_s = typ_s # Stringer type
        self.rise = rise #Stair rise
        self.run = run #Stair run. Degrees if self.typ == "id4"
        if notMulti:
            self.w = w / 100 #stringer width
        else:
            self.w = (wT * (w / 100)) / nS
        self.h = h #stringer height
        self.nT = nT #number of treads
        self.hT = hT #tread height
        self.wT = wT #tread width
        self.tT = tT #tread toe
        self.tO = tO #Tread overhang. Inner radius if self.typ == "id4"
        self.tw = self.w * (tw / 100) #stringer web thickness
        self.tf = tf #stringer flange thickness
        self.tp = 1 - (tp / 100) #stringer flange taper
        self.g = g #does stringer intersect the ground?
        self.nS = nS #number of stringers
        self.dis = dis #Use distributed stringers
        self.deg = deg #number of sections per "slice". Only applys if self.typ == "id4"
        # Default stringer object (classic / sId1):
        self.faces1=[[0,1,3,2],[1,5,3],[3,5,4],[6,7,9,8],[7,11,9],[9,11,10],
                     [0,2,8,6],[0,1,7,6],[1,5,11,7],[2,3,9,8],[3,4,10,9],[4,5,11,10]]
        # Box stair type stringer:
        self.faces2=[[0,1,7,6],[1,3,9,7],[3,4,10,9],[4,10,11,5],[5,11,8,2],
                     [2,8,6,0],[0,1,2],[1,2,5,3],[3,4,5],[6,7,8],[7,8,11,9],[9,10,11]]
        # I-beam stringer (id2 / sId2 / Taper < 100%):
        self.faces3a=[[0,1,17,16],[1,2,18,17],[2,3,19,18],[3,4,20,19],[4,5,21,20],[5,6,22,21],
                      [6,7,23,22],[7,8,24,23],[8,9,25,24],[9,10,26,25],[10,11,27,26],
                      [11,12,28,27],[12,13,29,28],[13,14,30,29],[14,15,31,30],[15,0,16,31],
                      [0,1,2,15],[2,11,14,15],[11,12,13,14],[2,3,10,11],[3,4,5,6],[3,6,7,10],
                      [7,8,9,10],[16,17,18,31],[18,27,30,31],[27,28,29,30],[18,19,26,27],
                      [19,20,21,22],[19,22,23,26],[23,24,25,26]]
        # I-beam stringer (id2 / sId2 / Taper = 100%):
        self.faces3b=[[0,1,9,8],[1,2,10,9],[2,3,11,10],[3,4,12,11],[4,5,13,12],[5,6,14,13],
                      [6,7,15,14],[7,0,8,15],[0,1,6,7],[1,2,5,6],[2,3,4,5],[8,9,14,15],
                      [9,10,13,14],[10,11,12,13]]
        # I-beam stringer (id3 / sId2 / Taper < 100%):
        self.faces3c=[[0,1,2,7],[2,3,6,7],[3,4,5,6],[1,2,23,16],[2,3,22,23],
                      [3,4,21,22],[16,17,18,23],[18,19,22,23],[19,20,21,22],
                      [17,8,15,18],[18,15,14,19],[19,14,13,20],[8,9,10,15],
                      [10,11,14,15],[11,12,13,14],[9,10,53,52],[10,11,54,53],
                      [11,12,55,54],[52,53,61,60],[53,54,62,61],[54,55,63,62],
                      [60,61,34,33],[61,62,35,34],[62,63,36,35],[32,33,34,39],
                      [34,35,38,39],[35,36,37,38],[41,32,39,42],[42,39,38,43],
                      [43,38,37,44],[40,41,42,47],[42,43,46,47],[43,44,45,46],
                      [25,26,47,40],[26,27,46,47],[27,28,45,46],[24,25,26,31],
                      [26,27,30,31],[27,28,29,30],[24,31,57,56],[31,30,58,57],
                      [30,29,59,58],[48,49,57,56],[49,50,58,57],[50,51,59,58],
                      [0,7,49,48],[7,6,50,49],[6,5,51,50],[0,1,16,48],[16,40,56,48],
                      [24,25,40,56],[16,17,41,40],[8,9,52,17],[17,52,60,41],
                      [32,33,60,41],[12,13,20,55],[20,44,63,55],[37,44,63,36],
                      [20,21,45,44],[28,29,51,21],[21,51,59,45],[28,45,59,29],
                      [4,5,51,21]]
        # C-beam stringer (id3 / sId3 / Taper < 100%):
        self.faces4c=[[0,1,2,7],[2,3,6,7],[3,4,5,6],[1,2,23,16],[2,3,22,23],[3,4,21,22],
                      [16,17,18,23],[18,19,22,23],[19,20,21,22],[17,8,15,18],[18,15,14,19],
                      [19,14,13,20],[8,9,10,15],[10,11,14,15],[11,12,13,14],[0,24,25,7],
                      [7,25,26,6],[6,26,27,5],[9,31,30,10],[10,30,29,11],[11,29,28,12],
                      [24,25,30,31],[25,26,29,30],[26,27,28,29],[0,1,16,24],[16,24,31,17],
                      [8,9,31,17],[4,5,27,21],[20,21,27,28],[12,13,20,28]]
        self.Create()


    def Create(self):
        if self.typ == "id1":
            if self.typ_s == "sId1":
                if self.dis or self.nS == 1:
                    offset = (self.wT / (self.nS + 1)) - (self.w / 2)
                else:
                    offset = 0
                for i in range(self.nS):
                    for j in range(self.nT):
                        coords = []
                        coords.append(Vector([0, offset, -self.rise]))
                        coords.append(Vector([self.run, offset, -self.rise]))
                        coords.append(Vector([0, offset, -self.hT]))
                        coords.append(Vector([self.run, offset, -self.hT]))
                        coords.append(Vector([self.run, offset, 0]))
                        coords.append(Vector([self.run * 2, offset, 0]))
                        for k in range(6):
                            coords.append(coords[k]+Vector([0, self.w, 0]))
                        for k in coords:
                            k += j*Vector([self.run, 0, self.rise])
                        self.G.Make_mesh(coords,self.faces1,'stringer')
                    if self.dis or self.nS == 1:
                        offset += self.wT / (self.nS + 1)
                    else:
                        offset += (self.wT - self.w) / (self.nS - 1)
            elif self.typ_s == "sId2":
                self.I_beam()
        elif self.typ == "id2":
            if self.typ_s == "sId1":
                coords = []
                coords.append(Vector([-self.tT, -self.w, -self.rise]))
                coords.append(Vector([self.hT / self.G.slope, -self.w, -self.rise]))
                coords.append(Vector([-self.tT, -self.w, 0]))
                coords.append(Vector([self.nT * self.run, -self.w,
                                      ((self.nT - 1) * self.rise) - self.hT]))
                coords.append(Vector([self.nT * self.run, -self.w, self.nT * self.rise]))
                coords.append(Vector([(self.nT * self.run) - self.tT, -self.w,
                                      self.nT * self.rise]))
                for i in range(6):
                    coords.append(coords[i] + Vector([0, self.w, 0]))
                self.G.Make_mesh(coords, self.faces2, 'stringer')
                for i in coords:
                    i += Vector([0, self.w + self.wT, 0])
                self.G.Make_mesh(coords, self.faces2, 'stringer')
            elif self.typ_s == "sId2":
                self.housed_I_beam()
            elif self.typ_s == "sId3":
                self.housed_C_beam()
        elif self.typ == "id3":
            h = (self.rise - self.hT) - self.rise #height of top section
            for i in range(self.nT):
                coords = []
                coords.append(Vector([i * self.run,0,-self.rise]))
                coords.append(Vector([(i + 1) * self.run,0,-self.rise]))
                coords.append(Vector([i * self.run,0,h + (i * self.rise)]))
                coords.append(Vector([(i + 1) * self.run,0,h + (i * self.rise)]))
                for j in range(4):
                    coords.append(coords[j] + Vector([0,self.wT,0]))
                self.G.Make_mesh(coords, self.G.faces, 'stringer')
        elif self.typ == "id4":
            offset = (self.wT / (self.nS + 1)) - (self.w / 2)
            for s in range(self.nS):
                base = self.tO + (offset * (s + 1))
                start = [Vector([0, -base, -self.hT]),
                         Vector([0, -base, -self.hT - self.rise]),
                         Vector([0, -base - self.w, -self.hT]),
                         Vector([0, -base - self.w, -self.hT - self.rise])]
                self.d = radians(self.run) / self.nT
                for i in range(self.nT):
                    coords = []
                    # Base faces.  Should be able to append more sections:
                    tId4_faces = [[0, 1, 3, 2]]
                    t_inner = Matrix.Rotation(self.d * i, 3, 'Z')
                    coords.append((t_inner * start[0]) + Vector([0, 0, self.rise * i]))
                    coords.append((t_inner * start[1]) + Vector([0, 0, self.rise * i]))
                    t_outer = Matrix.Rotation(self.d * i, 3, 'Z')
                    coords.append((t_outer * start[2]) + Vector([0, 0, self.rise * i]))
                    coords.append((t_outer * start[3]) + Vector([0, 0, self.rise * i]))
                    k = 0
                    for j in range(self.deg):
                        k = (j * 4) + 4
                        tId4_faces.append([k, k - 4, k - 3, k + 1])
                        tId4_faces.append([k - 2, k - 1, k + 3, k + 2])
                        tId4_faces.append([k + 1, k - 3, k - 1, k + 3])
                        tId4_faces.append([k, k - 4, k - 2, k + 2])
                        rot = Matrix.Rotation(((self.d * (j + 1)) / self.deg) + (self.d * i), 3, 'Z')
                        for v in start:
                            coords.append((rot * v) + Vector([0, 0, self.rise * i]))
                    for j in range(self.deg):
                        k = ((j + self.deg) * 4) + 4
                        tId4_faces.append([k, k - 4, k - 3, k + 1])
                        tId4_faces.append([k - 2, k - 1, k + 3, k + 2])
                        tId4_faces.append([k + 1, k - 3, k - 1, k + 3])
                        tId4_faces.append([k, k - 4, k - 2, k + 2])
                        rot = Matrix.Rotation(((self.d * ((j + self.deg) + 1)) / self.deg) + (self.d * i), 3, 'Z')
                        for v in range(4):
                            if v in [1, 3]:
                                incline = (self.rise * i) + (self.rise / self.deg) * (j + 1)
                                coords.append((rot * start[v]) + Vector([0, 0, incline]))
                            else:
                                coords.append((rot * start[v]) + Vector([0, 0, self.rise * i]))
                    self.G.Make_mesh(coords, tId4_faces, 'treads')

        return {'FINISHED'}


    def I_beam(self):
        mid = self.w / 2
        web = self.tw / 2
        # Bottom of the stringer:
        baseZ = -self.rise - self.hT - self.h
        # Top of the strigner:
        topZ = -self.rise - self.hT
        # Vertical taper amount:
        taper = self.tf * self.tp

        if self.dis or self.nS == 1:
            offset = (self.wT / (self.nS + 1)) - mid
        else:
            offset = 0

        # taper < 100%:
        if self.tp > 0:
            for i in range(self.nS):
                coords = []
                coords.append(Vector([0, offset,                baseZ]))
                coords.append(Vector([0, offset,                baseZ + taper]))
                coords.append(Vector([0, offset + (mid - web),  baseZ + self.tf]))
                coords.append(Vector([0, offset + (mid - web),  topZ - self.tf]))
                coords.append(Vector([0, offset,                topZ - taper]))
                coords.append(Vector([0, offset,                topZ]))
                coords.append(Vector([0, offset + (mid - web),  topZ]))
                coords.append(Vector([0, offset + (mid + web),  topZ]))
                coords.append(Vector([0, offset + self.w,       topZ]))
                coords.append(Vector([0, offset + self.w,       topZ - taper]))
                coords.append(Vector([0, offset + (mid + web),  topZ - self.tf]))
                coords.append(Vector([0, offset + (mid + web),  baseZ + self.tf]))
                coords.append(Vector([0, offset + self.w,       baseZ + taper]))
                coords.append(Vector([0, offset + self.w,       baseZ]))
                coords.append(Vector([0, offset + (mid + web),  baseZ]))
                coords.append(Vector([0, offset + (mid - web),  baseZ]))
                for j in range(16):
                    coords.append(coords[j]+Vector([self.run * self.nT, 0, self.rise * self.nT]))
                # If the bottom meets the ground:
                #   Bottom be flat with the xy plane, but shifted down.
                #   Either project onto the plane along a vector (hard) or use the built in
                #       interest found in mathutils.geometry (easy).  Using intersect:
                if self.g:
                    for j in range(16):
                        coords[j] = intersect_line_plane(coords[j], coords[j + 16],
                                                         Vector([0, 0, topZ]),
                                                         Vector([0, 0, 1]))
                self.G.Make_mesh(coords, self.faces3a, 'stringer')

                if self.dis or self.nS == 1:
                    offset += self.wT / (self.nS + 1)
                else:
                    offset += (self.wT - self.w) / (self.nS - 1)
        # taper = 100%:
        else:
            for i in range(self.nS):
                coords = []
                coords.append(Vector([0, offset,                baseZ]))
                coords.append(Vector([0, offset + (mid - web),  baseZ + self.tf]))
                coords.append(Vector([0, offset + (mid - web),  topZ - self.tf]))
                coords.append(Vector([0, offset,                topZ]))
                coords.append(Vector([0, offset + self.w,       topZ]))
                coords.append(Vector([0, offset + (mid + web),  topZ - self.tf]))
                coords.append(Vector([0, offset + (mid + web),  baseZ + self.tf]))
                coords.append(Vector([0, offset + self.w,       baseZ]))
                for j in range(8):
                    coords.append(coords[j]+Vector([self.run * self.nT, 0, self.rise * self.nT]))
                self.G.Make_mesh(coords, self.faces3b, 'stringer')
                offset += self.wT / (self.nS + 1)
                
        return {'FINISHED'}


    def housed_I_beam(self):
        webOrth = Vector([self.rise, 0, -self.run]).normalized()
        webHeight = Vector([self.run + self.tT, 0, -self.hT]).project(webOrth).length
        vDelta_1 = self.tf * tan(self.G.angle)
        vDelta_2 = (self.rise * (self.nT - 1)) - (webHeight + self.tf)
        flange_y = (self.w - self.tw) / 2
        front = -self.tT - self.tf
        outer = -self.tO - self.tw - flange_y

        coords = []
        if self.tp > 0:
            # Upper-Outer flange:
            coords.append(Vector([front, outer, -self.rise]))
            coords.append(Vector([-self.tT, outer, -self.rise]))
            coords.append(Vector([-self.tT, outer, 0]))
            coords.append(Vector([(self.run * (self.nT - 1)) - self.tT, outer,
                                  self.rise * (self.nT - 1)]))
            coords.append(Vector([self.run * self.nT, outer,
                                  self.rise * (self.nT - 1)]))
            coords.append(Vector([self.run * self.nT, outer,
                                  (self.rise * (self.nT - 1)) + self.tf]))
            coords.append(Vector([(self.run * (self.nT - 1)) - self.tT, outer,
                                  (self.rise * (self.nT - 1)) + self.tf]))
            coords.append(Vector([front, outer, self.tf - vDelta_1]))
            # Lower-Outer flange:
            coords.append(coords[0] + Vector([self.tf + webHeight, 0, 0]))
            coords.append(coords[1] + Vector([self.tf + webHeight, 0, 0]))
            coords.append(intersect_line_line(coords[9],
                                              coords[9] - Vector([0, 0, 1]),
                                              Vector([self.run, 0, -self.hT - self.tf]),
                                              Vector([self.run * 2, 0, self.rise - self.hT - self.tf]))[0])
            coords.append(Vector([(self.run * self.nT) - ((webHeight - self.hT) / tan(self.G.angle)),
                                  outer, vDelta_2]))
            coords.append(coords[4] - Vector([0, 0, self.tf + webHeight]))
            coords.append(coords[5] - Vector([0, 0, self.tf + webHeight]))
            coords.append(coords[11] + Vector([0, 0, self.tf]))
            coords.append(intersect_line_line(coords[8],
                                              coords[8] - Vector([0, 0, 1]),
                                              Vector([self.run, 0, -self.hT]),
                                              Vector([self.run * 2, 0, self.rise - self.hT]))[0])
            # Outer web:
            coords.append(coords[1] + Vector([0, flange_y, 0]))
            coords.append(coords[8] + Vector([0, flange_y, 0]))
            coords.append(coords[15] + Vector([0, flange_y, 0]))
            coords.append(coords[14] + Vector([0, flange_y, 0]))
            coords.append(coords[13] + Vector([0, flange_y, 0]))
            coords.append(coords[4] + Vector([0, flange_y, 0]))
            coords.append(coords[3] + Vector([0, flange_y, 0]))
            coords.append(coords[2] + Vector([0, flange_y, 0]))
            # Upper-Inner flange and lower-inner flange:
            for i in range(16):
                coords.append(coords[i] + Vector([0, self.w, 0]))
            # Inner web:
            for i in range(8):
                coords.append(coords[i + 16] + Vector([0, self.tw, 0]))
            # Mid nodes to so faces will be quads:
            for i in [0,7,6,5,9,10,11,12]:
                coords.append(coords[i] + Vector([0, flange_y, 0]))
            for i in range(8):
                coords.append(coords[i + 48] + Vector([0, self.tw, 0]))

            self.G.Make_mesh(coords, self.faces3c, 'stringer')

            for i in coords:
                i += Vector([0, self.wT + self.tw, 0])

            self.G.Make_mesh(coords, self.faces3c, 'stringer')

        # @TODO Taper = 100%
        
        return {'FINISHED'}


    def C_Beam(self):
        mid = self.w / 2
        web = self.tw / 2
        # Bottom of the stringer:
        baseZ = -self.rise - self.hT - self.h
        # Top of the strigner:
        topZ = -self.rise - self.hT
        # Vertical taper amount:
        taper = self.tf * self.tp

        if self.dis or self.nS == 1:
            offset = (self.wT / (self.nS + 1)) - mid
        else:
            offset = 0

        # taper < 100%:
        if self.tp > 0:
            for i in range(self.nS):
                coords = []
                coords.append(Vector([0, offset,                baseZ]))
                coords.append(Vector([0, offset,                baseZ + taper]))
                coords.append(Vector([0, offset + (mid - web),  baseZ + self.tf]))
                coords.append(Vector([0, offset + (mid - web),  topZ - self.tf]))
                coords.append(Vector([0, offset,                topZ - taper]))
                coords.append(Vector([0, offset,                topZ]))
                coords.append(Vector([0, offset + (mid - web),  topZ]))
                coords.append(Vector([0, offset + (mid + web),  topZ]))
                coords.append(Vector([0, offset + self.w,       topZ]))
                coords.append(Vector([0, offset + self.w,       topZ - taper]))
                coords.append(Vector([0, offset + (mid + web),  topZ - self.tf]))
                coords.append(Vector([0, offset + (mid + web),  baseZ + self.tf]))
                coords.append(Vector([0, offset + self.w,       baseZ + taper]))
                coords.append(Vector([0, offset + self.w,       baseZ]))
                coords.append(Vector([0, offset + (mid + web),  baseZ]))
                coords.append(Vector([0, offset + (mid - web),  baseZ]))
                for j in range(16):
                    coords.append(coords[j]+Vector([self.run * self.nT, 0, self.rise * self.nT]))
                # If the bottom meets the ground:
                #   Bottom be flat with the xy plane, but shifted down.
                #   Either project onto the plane along a vector (hard) or use the built in
                #       interest found in mathutils.geometry (easy).  Using intersect:
                if self.g:
                    for j in range(16):
                        coords[j] = intersect_line_plane(coords[j], coords[j + 16],
                                                         Vector([0, 0, topZ]),
                                                         Vector([0, 0, 1]))
                self.G.Make_mesh(coords, self.faces3a, 'stringer')

                if self.dis or self.nS == 1:
                    offset += self.wT / (self.nS + 1)
                else:
                    offset += (self.wT - self.w) / (self.nS - 1)
        # taper = 100%:
        else:
            for i in range(self.nS):
                coords = []
                coords.append(Vector([0, offset,                baseZ]))
                coords.append(Vector([0, offset + (mid - web),  baseZ + self.tf]))
                coords.append(Vector([0, offset + (mid - web),  topZ - self.tf]))
                coords.append(Vector([0, offset,                topZ]))
                coords.append(Vector([0, offset + self.w,       topZ]))
                coords.append(Vector([0, offset + (mid + web),  topZ - self.tf]))
                coords.append(Vector([0, offset + (mid + web),  baseZ + self.tf]))
                coords.append(Vector([0, offset + self.w,       baseZ]))
                for j in range(8):
                    coords.append(coords[j]+Vector([self.run * self.nT, 0, self.rise * self.nT]))
                self.G.Make_mesh(coords, self.faces3b, 'stringer')
                offset += self.wT / (self.nS + 1)
                
        return {'FINISHED'}


    def housed_C_beam(self):
        webOrth = Vector([self.rise, 0, -self.run]).normalized()
        webHeight = Vector([self.run + self.tT, 0, -self.hT]).project(webOrth).length
        vDelta_1 = self.tf * tan(self.G.angle)
        vDelta_2 = (self.rise * (self.nT - 1)) - (webHeight + self.tf)
        flange_y = (self.w - self.tw) / 2
        front = -self.tT - self.tf
        outer = -self.tO - self.tw - flange_y

        coords = []
        if self.tp > 0:
            # Upper-Outer flange:
            coords.append(Vector([front, outer, -self.rise]))
            coords.append(Vector([-self.tT, outer, -self.rise]))
            coords.append(Vector([-self.tT, outer, 0]))
            coords.append(Vector([(self.run * (self.nT - 1)) - self.tT, outer,
                                  self.rise * (self.nT - 1)]))
            coords.append(Vector([self.run * self.nT, outer,
                                  self.rise * (self.nT - 1)]))
            coords.append(Vector([self.run * self.nT, outer,
                                  (self.rise * (self.nT - 1)) + self.tf]))
            coords.append(Vector([(self.run * (self.nT - 1)) - self.tT, outer,
                                  (self.rise * (self.nT - 1)) + self.tf]))
            coords.append(Vector([front, outer, self.tf - vDelta_1]))
            # Lower-Outer flange:
            coords.append(coords[0] + Vector([self.tf + webHeight, 0, 0]))
            coords.append(coords[1] + Vector([self.tf + webHeight, 0, 0]))
            coords.append(intersect_line_line(coords[9],
                                              coords[9] - Vector([0, 0, 1]),
                                              Vector([self.run, 0, -self.hT - self.tf]),
                                              Vector([self.run * 2, 0, self.rise - self.hT - self.tf]))[0])
            coords.append(Vector([(self.run * self.nT) - ((webHeight - self.hT) / tan(self.G.angle)),
                                  outer, vDelta_2]))
            coords.append(coords[4] - Vector([0, 0, self.tf + webHeight]))
            coords.append(coords[5] - Vector([0, 0, self.tf + webHeight]))
            coords.append(coords[11] + Vector([0, 0, self.tf]))
            coords.append(intersect_line_line(coords[8],
                                              coords[8] - Vector([0, 0, 1]),
                                              Vector([self.run, 0, -self.hT]),
                                              Vector([self.run * 2, 0, self.rise - self.hT]))[0])
            # Outer web:
            coords.append(coords[1] + Vector([0, flange_y, 0]))
            coords.append(coords[8] + Vector([0, flange_y, 0]))
            coords.append(coords[15] + Vector([0, flange_y, 0]))
            coords.append(coords[14] + Vector([0, flange_y, 0]))
            coords.append(coords[13] + Vector([0, flange_y, 0]))
            coords.append(coords[4] + Vector([0, flange_y, 0]))
            coords.append(coords[3] + Vector([0, flange_y, 0]))
            coords.append(coords[2] + Vector([0, flange_y, 0]))
            # Outer corner nodes:
            for i in [0, 7, 6, 5, 12, 11, 10, 9]:
                coords.append(coords[i] + Vector([0, flange_y + self.tw, 0]))

            self.G.Make_mesh(coords, self.faces4c, 'stringer')

            for i in range(16):
                coords[i] += Vector([0, -outer * 2, 0])
            for i in range(8):
                coords[i + 16] += Vector([0, (-outer - flange_y) * 2, 0])
            for i in coords:
                i += Vector([0, (self.tO * 2) + self.wT, 0])

            self.G.Make_mesh(coords, self.faces4c, 'stringer')
        
        return {'FINISHED'}
