# -*- coding: utf-8 -*-
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

"""
    geometry_utils.py

    3d geometry calculations
    
    

"""


from mathutils import Vector, Matrix
from mathutils import geometry


# 3D Geometry
class G3:

    @classmethod
    def distanceP2P(cls, p1, p2):
        return (p1-p2).length

    @classmethod
    def closestP2L(cls, p, l1, l2):
        vA = p - l1
        vL = l2- l1
        vL.normalize()
        return vL * (vL.dot(vA)) + l1

    @classmethod
    def closestP2E(cls, p, e1, e2):
        q = G3.closestP2L(p, e1, e2)
        de = G3.distanceP2P(e1, e2)
        d1 = G3.distanceP2P(q, e1)
        d2 = G3.distanceP2P(q, e2)
        if d1>de and d1>d2:
            q = e2
        if d2>de and d2>d1:
            q = e1
        return q

    @classmethod
    def heightP2S(cls, p, sO, sN):
        return (p-sO).dot(sN) / sN.dot(sN)

    @classmethod
    def closestP2S(cls, p, sO, sN):
        k = - G3.heightP2S(p, sO, sN)
        q = p+sN*k
        return q

    @classmethod
    def closestP2F(cls, p, fv, sN):
        q = G3.closestP2S(p, fv[0], sN)
        #pi = MeshEditor.addVertex(p)
        #qi = MeshEditor.addVertex(q)
        #MeshEditor.addEdge(pi, qi)
        #print ([d0,d1,d2])
        
        if len(fv)==3:
            h = G3.closestP2L(fv[0], fv[1], fv[2])
            d = (fv[0]-h).dot(q-h)
            if d<=0:
                return G3.closestP2E(q, fv[1], fv[2])
            h = G3.closestP2L(fv[1], fv[2], fv[0])
            d = (fv[1]-h).dot(q-h)
            if d<=0:
                return G3.closestP2E(q, fv[2], fv[0])
            h = G3.closestP2L(fv[2], fv[0], fv[1])
            d = (fv[2]-h).dot(q-h)
            if d<=0:
                return G3.closestP2E(q, fv[0], fv[1])
            return q
        if len(fv)==4:
            h = G3.closestP2L(fv[0], fv[1], fv[2])
            d = (fv[0]-h).dot(q-h)
            if d<=0:
                return G3.closestP2E(q, fv[1], fv[2])
            h = G3.closestP2L(fv[1], fv[2], fv[3])
            d = (fv[1]-h).dot(q-h)
            if d<=0:
                return G3.closestP2E(q, fv[2], fv[3])
            h = G3.closestP2L(fv[2], fv[3], fv[0])
            d = (fv[2]-h).dot(q-h)
            if d<=0:
                return G3.closestP2E(q, fv[3], fv[0])
            h = G3.closestP2L(fv[3], fv[0], fv[1])
            d = (fv[3]-h).dot(q-h)
            if d<=0:
                return G3.closestP2E(q, fv[0], fv[1])
            return q

    @classmethod
    def medianTriangle(cls, vv):
        m0 = (vv[1]+vv[2])/2
        m1 = (vv[0]+vv[2])/2
        m2 = (vv[0]+vv[1])/2
        return [m0, m1, m2]

    @classmethod
    def orthoCenter(cls, fv):
        try:
            h0 = G3.closestP2L(fv[0], fv[1], fv[2])
            h1 = G3.closestP2L(fv[1], fv[0], fv[2])
            #h2 = G3.closestP2L(fm[2], fm[0], fm[1])
            return geometry.intersect_line_line (fv[0], h0, fv[1], h1)[0]
        except(RuntimeError, TypeError):
            return None

    # Poor mans approach of finding center of circle
    @classmethod
    def circumCenter(cls, fv):
        fm = G3.medianTriangle(fv)
        return G3.orthoCenter(fm)

    @classmethod
    def ThreePnormal(cls, fv):
        n = (fv[1]-fv[0]).cross(fv[2]-fv[0])
        n.normalize()
        return n

    @classmethod
    def closestP2CylinderAxis(cls, p, fv):
        n = G3.ThreePnormal(fv)
        c = G3.circumCenter(fv)
        if(c==None):
            return None
        return G3.closestP2L(p, c, c+n)

    # Poor mans approach of finding center of sphere
    @classmethod
    def centerOfSphere(cls, fv):
        try:
            if len(fv)==3:
                return G3.circumCenter(fv) # Equator
            if len(fv)==4:
                fv3 = [fv[0],fv[1],fv[2]]
                c1 = G3.circumCenter(fv)
                n1 = G3.ThreePnormal(fv)
                fv3 = [fv[1],fv[2],fv[3]]
                c2 = G3.circumCenter(fv3)
                n2 = G3.ThreePnormal(fv3)
                d1 = c1+n1
                d2 = c2+n2
                return geometry.intersect_line_line (c1, d1, c2, d2)[0]
        except(RuntimeError, TypeError):
            return None

    @classmethod
    def closestP2Sphere(cls, p, fv):
        #print ("G3.closestP2Sphere")
        try:
            c = G3.centerOfSphere(fv)
            if c==None:
                return None
            pc = p-c
            if pc.length == 0:
                pc = pc + Vector((1,0,0))
            else:
                pc.normalize()
            return c + (pc * G3.distanceP2P(c, fv[0]))
        except(RuntimeError, TypeError):
            return None

    @classmethod
    def closestP2Cylinder(cls, p, fv):
        #print ("G3.closestP2Sphere")
        c = G3.closestP2CylinderAxis(p, fv)
        if c==None:
            return None
        r = (fv[0] - G3.centerOfSphere(fv)).length
        pc = p-c
        if pc.length == 0:
            pc = pc + Vector((1,0,0))
        else:
            pc.normalize()
        return c + (pc * r)

    #@classmethod
    #def closestP2Sphere4(cls, p, fv4):
        ##print ("G3.closestP2Sphere")
        #fv = [fv4[0],fv4[1],fv4[2]]
        #c1 = G3.circumCenter(fv)
        #n1 = G3.ThreePnormal(fv)
        #fv = [fv4[1],fv4[2],fv4[3]]
        #c2 = G3.circumCenter(fv)
        #n2 = G3.ThreePnormal(fv)
        #d1 = c1+n1
        #d2 = c2+n2
        #c = geometry.intersect_line_line (c1, d1, c2, d2)[0]
        #pc = p-c
        #if pc.length == 0:
            #pc = pc + Vector((1,0,0))
        #else:
            #pc.normalize()
        #return c + (pc * G3.distanceP2P(c, fv[0]))



