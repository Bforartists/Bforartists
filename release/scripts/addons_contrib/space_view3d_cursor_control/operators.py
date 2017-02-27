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
  TODO:

      IDEAS:

      LATER:

      ISSUES:
          Bugs:
          Mites:

      QUESTIONS:


"""



import bpy
import bgl
import math
from mathutils import Vector, Matrix
from mathutils import geometry
from .misc_utils import *
from .constants_utils import *
from .cursor_utils import *
from .ui_utils import *
from .geometry_utils import *


class VIEW3D_OT_cursor_to_origin(bpy.types.Operator):
    """Move to world origin"""
    bl_idname = "view3d.cursor_to_origin"
    bl_label = "Move to world origin"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        cc = context.scene.cursor_control
        cc.hideLinexChoice()
        cc.setCursor([0,0,0])
        return {'FINISHED'}



class VIEW3D_OT_cursor_to_active_object_center(bpy.types.Operator):
    """Move to active object origin"""
    bl_idname = "view3d.cursor_to_active_object_center"
    bl_label = "Move to active object origin"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        cc = context.scene.cursor_control
        cc.hideLinexChoice()
        cc.setCursor(context.active_object.location)
        return {'FINISHED'}



#class VIEW3D_OT_cursor_to_nearest_object(bpy.types.Operator):
    #"""Move to center of nearest object"""
    #bl_idname = "view3d.cursor_to_nearest_object"
    #bl_label = "Move to center of nearest object"
    #bl_options = {'REGISTER'}

    #def modal(self, context, event):
        #return {'FINISHED'}

    #def execute(self, context):
        #cc.setCursor(context.active_object.location)
        #return {'FINISHED'}



#class VIEW3D_OT_cursor_to_selection_midpoint(bpy.types.Operator):
    #"""Move to active objects median"""
    #bl_idname = "view3d.cursor_to_selection_midpoint"
    #bl_label = "Move to active objects median"
    #bl_options = {'REGISTER'}

    #def modal(self, context, event):
        #return {'FINISHED'}

    #def execute(self, context):
        #location = Vector((0,0,0))
        #n = 0
        #for obj in context.selected_objects:
            #location = location + obj.location
            #n += 1
        #if (n==0):
            #return {'CANCELLED'}
        #location = location / n
        #cc.setCursor(location)
        #return {'FINISHED'}



class VIEW3D_OT_cursor_to_sl(bpy.types.Operator):
    """Move to saved location"""
    bl_idname = "view3d.cursor_to_sl"
    bl_label = "Move to saved location"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        cc = context.scene.cursor_control
        if hasattr(context.scene, "cursor_memory"):
            cm = context.scene.cursor_memory
            cc.hideLinexChoice()
            cc.setCursor(cm.savedLocation)
        return {'FINISHED'}



class VIEW3D_OT_cursor_to_sl_mirror(bpy.types.Operator):
    """Mirror cursor around SL or selection"""
    bl_idname = "view3d.cursor_to_sl_mirror"
    bl_label = "Mirror cursor around SL or selection"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def mirror(self, cc, p):
        v = p - Vector(CursorAccess.getCursor())
        cc.setCursor(p + v)

    def execute(self, context):
        BlenderFake.forceUpdate()
        obj = context.active_object
        cc = context.scene.cursor_control
        cc.hideLinexChoice()
        
        if obj==None or obj.data.total_vert_sel==0:
            if hasattr(context.scene, "cursor_memory"):
                cm = context.scene.cursor_memory
                self.mirror(cc, Vector(cm.savedLocation))
            return {'FINISHED'}

        mat = obj.matrix_world

        if obj.data.total_vert_sel==1:
            sf = [f for f in obj.data.vertices if f.select == 1]
            self.mirror(cc, mat*Vector(sf[0].co))
            return {'FINISHED'}

        mati = mat.copy()
        mati.invert()
        c = mati*Vector(CursorAccess.getCursor())

        if obj.data.total_vert_sel==2:
            sf = [f for f in obj.data.vertices if f.select == 1]
            p = G3.closestP2L(c, Vector(sf[0].co), Vector(sf[1].co))
            self.mirror(cc, mat*p)
            return {'FINISHED'}
            
        if obj.data.total_vert_sel==3:
            sf = [f for f in obj.data.vertices if f.select == 1]
            v0 = Vector(sf[0].co)
            v1 = Vector(sf[1].co)
            v2 = Vector(sf[2].co)
            normal = (v1-v0).cross(v2-v0)
            normal.normalize();            
            p = G3.closestP2S(c, v0, normal)
            self.mirror(cc, mat*p)
            return {'FINISHED'}
              
        if obj.data.total_face_sel==1:
            sf = [f for f in obj.data.faces if f.select == 1]
            v0 = Vector(obj.data.vertices[sf[0].vertices[0]].co)
            v1 = Vector(obj.data.vertices[sf[0].vertices[1]].co)
            v2 = Vector(obj.data.vertices[sf[0].vertices[2]].co)
            normal = (v1-v0).cross(v2-v0)
            normal.normalize();            
            p = G3.closestP2S(c, v0, normal)
            self.mirror(cc, mat*p)
            return {'FINISHED'}

        return {'CANCELLED'}


class VIEW3D_OT_cursor_to_vertex(bpy.types.Operator):
    """Move to closest vertex"""
    bl_idname = "view3d.cursor_to_vertex"
    bl_label = "Move to closest vertex"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        BlenderFake.forceUpdate()
        cc = context.scene.cursor_control
        cc.hideLinexChoice()
        obj = context.active_object
        mat = obj.matrix_world
        mati = mat.copy()
        mati.invert()
        vs = obj.data.vertices
        c = mati*Vector(CursorAccess.getCursor())
        v = None
        d = -1
        for vv in vs:
            if not vv.select:
                continue
            w = Vector(vv.co)
            dd = G3.distanceP2P(c, w)
            if d<0 or dd<d:
                v = w
                d = dd
        if v==None:
            return
        cc.setCursor(mat*v)
        return {'FINISHED'}


class VIEW3D_OT_cursor_to_line(bpy.types.Operator):
    """Move to closest point on line"""
    bl_idname = "view3d.cursor_to_line"
    bl_label = "Move to closest point on line"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        BlenderFake.forceUpdate()
        cc = context.scene.cursor_control
        cc.hideLinexChoice()
        obj = bpy.context.active_object
        mat = obj.matrix_world
        if obj.data.total_vert_sel==2:
            sf = [f for f in obj.data.vertices if f.select == 1]
            p = CursorAccess.getCursor()
            v0 = mat*sf[0].co
            v1 = mat*sf[1].co
            q = G3.closestP2L(p, v0, v1)
            cc.setCursor(q)
            return {'FINISHED'}
        if obj.data.total_edge_sel<2:
            return {'CANCELLED'}
        mati = mat.copy()
        mati.invert()
        c = mati*Vector(CursorAccess.getCursor())
        q = None
        d = -1
        for ee in obj.data.edges:
            if not ee.select:
                continue
            e1 = Vector(obj.data.vertices[ee.vertices[0]].co)
            e2 = Vector(obj.data.vertices[ee.vertices[1]].co)
            qq = G3.closestP2L(c, e1, e2)
            dd = G3.distanceP2P(c, qq)
            if d<0 or dd<d:
                q = qq
                d = dd
        if q==None:
            return {'CANCELLED'}
        cc.setCursor(mat*q)
        return {'FINISHED'}


class VIEW3D_OT_cursor_to_edge(bpy.types.Operator):
    """Move to closest point on edge"""
    bl_idname = "view3d.cursor_to_edge"
    bl_label = "Move to closest point on edge"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        BlenderFake.forceUpdate()
        cc = context.scene.cursor_control
        cc.hideLinexChoice()
        obj = bpy.context.active_object
        mat = obj.matrix_world
        if obj.data.total_vert_sel==2:
            sf = [f for f in obj.data.vertices if f.select == 1]
            p = CursorAccess.getCursor()
            v0 = mat*sf[0].co
            v1 = mat*sf[1].co
            q = G3.closestP2E(p, v0, v1)
            cc.setCursor(q)
            return {'FINISHED'}
        if obj.data.total_edge_sel<2:
            return {'CANCELLED'}
        mati = mat.copy()
        mati.invert()
        c = mati*Vector(CursorAccess.getCursor())
        q = None
        d = -1
        for ee in obj.data.edges:
            if not ee.select:
                continue
            e1 = Vector(obj.data.vertices[ee.vertices[0]].co)
            e2 = Vector(obj.data.vertices[ee.vertices[1]].co)
            qq = G3.closestP2E(c, e1, e2)
            dd = G3.distanceP2P(c, qq)
            if d<0 or dd<d:
                q = qq
                d = dd
        if q==None:
            return {'CANCELLED'}
        cc.setCursor(mat*q)
        return {'FINISHED'}


class VIEW3D_OT_cursor_to_plane(bpy.types.Operator):
    """Move to closest point on a plane"""
    bl_idname = "view3d.cursor_to_plane"
    bl_label = "Move to closest point on a plane"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        BlenderFake.forceUpdate()
        cc = context.scene.cursor_control
        cc.hideLinexChoice()
        obj = bpy.context.active_object
        mesh = obj.data.vertices
        mat = obj.matrix_world
        if obj.data.total_vert_sel==3:
            sf = [f for f in obj.data.vertices if f.select == 1]
            v0 = Vector(sf[0].co)
            v1 = Vector(sf[1].co)
            v2 = Vector(sf[2].co)
            normal = (v1-v0).cross(v2-v0)
            normal.normalize();
            p = CursorAccess.getCursor()
            n = mat*normal-obj.location
            v = mat*v0
            k = - (p-v).dot(n) / n.dot(n)
            q = p+n*k
            cc.setCursor(q)
            return {'FINISHED'}

        mati = mat.copy()
        mati.invert()
        c = mati*Vector(CursorAccess.getCursor())
        q = None
        d = -1
        for ff in obj.data.polygons:
            if not ff.select:
                continue
            qq = G3.closestP2S(c, Vector(obj.data.vertices[ff.vertices[0]].co), ff.normal)
            dd = G3.distanceP2P(c, qq)
            if d<0 or dd<d:
                q = qq
                d = dd
        if q==None:
            return {'CANCELLED'}
        cc.setCursor(mat*q)
        return {'FINISHED'}


class VIEW3D_OT_cursor_to_face(bpy.types.Operator):
    """Move to closest point on a face"""
    bl_idname = "view3d.cursor_to_face"
    bl_label = "Move to closest point on a face"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        BlenderFake.forceUpdate()
        cc = context.scene.cursor_control
        cc.hideLinexChoice()
        obj = bpy.context.active_object
        mesh = obj.data.vertices
        mat = obj.matrix_world
        mati = mat.copy()
        mati.invert()
        c = mati*Vector(CursorAccess.getCursor())
        if obj.data.total_vert_sel==3:
            sf = [f for f in obj.data.vertices if f.select == 1]
            v0 = Vector(sf[0].co)
            v1 = Vector(sf[1].co)
            v2 = Vector(sf[2].co)
            fv = [v0, v1, v2]
            normal = (v1-v0).cross(v2-v0)
            normal.normalize();
            q = G3.closestP2F(c, fv, normal)
            cc.setCursor(mat*q)
            return {'FINISHED'}

        #visual = True

        qqq = []
        q = None
        d = -1
        for ff in obj.data.polygons:
            if not ff.select:
                continue
            fv=[]
            for vi in ff.vertices:
                fv.append(Vector(obj.data.vertices[vi].co))
            qq = G3.closestP2F(c, fv, ff.normal)
            #if visual:
                #qqq.append(qq)
            dd = G3.distanceP2P(c, qq)
            if d<0 or dd<d:
                q = qq
                d = dd
        if q==None:
            return {'CANCELLED'}

        #if visual:
            #ci = MeshEditor.addVertex(c)
            #for qq in qqq:
                #qqi = MeshEditor.addVertex(qq)
                #MeshEditor.addEdge(ci, qqi)

        cc.setCursor(mat*q)
        return {'FINISHED'}


class VIEW3D_OT_cursor_to_vertex_median(bpy.types.Operator):
    """Move to median of vertices"""
    bl_idname = "view3d.cursor_to_vertex_median"
    bl_label = "Move to median of vertices"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        BlenderFake.forceUpdate()
        cc = context.scene.cursor_control
        cc.hideLinexChoice()
        obj = context.active_object
        mat = obj.matrix_world
        vs = obj.data.vertices
        selv = [v for v in vs if v.select == 1]
        location = Vector((0,0,0))
        for v in selv:
            location = location + v.co
        n = len(selv)
        if (n==0):
            return {'CANCELLED'}
        location = location / n
        cc.setCursor(mat*location)
        return {'FINISHED'}


class VIEW3D_OT_cursor_to_linex(bpy.types.Operator):
    """Alternate between closest encounter points of two lines"""
    bl_idname = "view3d.cursor_to_linex"
    bl_label = "Alternate between to closest encounter points of two lines"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        BlenderFake.forceUpdate()
        obj = bpy.context.active_object
        mat = obj.matrix_world

        se = [e for e in obj.data.edges if (e.select == 1)]
        e1v1 = obj.data.vertices[se[0].vertices[0]].co
        e1v2 = obj.data.vertices[se[0].vertices[1]].co
        e2v1 = obj.data.vertices[se[1].vertices[0]].co
        e2v2 = obj.data.vertices[se[1].vertices[1]].co

        qq = geometry.intersect_line_line (e1v1, e1v2, e2v1, e2v2)

        q = None
        if len(qq)==0:
            #print ("lx 0")
            return {'CANCELLED'}

        if len(qq)==1:
            #print ("lx 1")
            q = qq[0]
        
        if len(qq)==2:
            cc = context.scene.cursor_control
            cc.cycleLinexCoice(2)
            q = qq[cc.linexChoice]

        #q = geometry.intersect_line_line (e1v1, e1v2, e2v1, e2v2)[qc] * mat
        #i2 = geometry.intersect_line_line (e2v1, e2v2, e1v1, e1v2)[0] * mat
        cc.setCursor(mat*q)
        return {'FINISHED'}


class VIEW3D_OT_cursor_to_cylinderaxis(bpy.types.Operator):
    """Move to closest point on cylinder axis"""
    bl_idname = "view3d.cursor_to_cylinderaxis"
    bl_label = "Move to closest point on cylinder axis"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        BlenderFake.forceUpdate()
        cc = context.scene.cursor_control
        cc.hideLinexChoice()
        obj = bpy.context.active_object
        mesh = obj.data.vertices
        mat = obj.matrix_world
        mati = mat.copy()
        mati.invert()
        c = mati*Vector(CursorAccess.getCursor())

        sf = [f for f in obj.data.vertices if f.select == 1]
        v0 = Vector(sf[0].co)
        v1 = Vector(sf[1].co)
        v2 = Vector(sf[2].co)
        fv = [v0, v1, v2]
        q = G3.closestP2CylinderAxis(c, fv)
        if(q==None):
            return {'CANCELLED'}
        cc.setCursor(mat*q)
        return {'FINISHED'}     


class VIEW3D_OT_cursor_to_spherecenter(bpy.types.Operator):
    """Move to center of cylinder or sphere"""
    bl_idname = "view3d.cursor_to_spherecenter"
    bl_label = "Move to center of cylinder or sphere"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        BlenderFake.forceUpdate()
        cc = context.scene.cursor_control
        cc.hideLinexChoice()
        obj = bpy.context.active_object
        mesh = obj.data.vertices
        mat = obj.matrix_world
        mati = mat.copy()
        mati.invert()
        c = mati*Vector(CursorAccess.getCursor())

        if obj.data.total_vert_sel==3:
            sf = [f for f in obj.data.vertices if f.select == 1]
            v0 = Vector(sf[0].co)
            v1 = Vector(sf[1].co)
            v2 = Vector(sf[2].co)
            fv = [v0, v1, v2]
            q = G3.closestP2CylinderAxis(c, fv)
            #q = G3.centerOfSphere(fv)
            if(q==None):
                return {'CANCELLED'}
            cc.setCursor(mat*q)
            return {'FINISHED'}
        if obj.data.total_vert_sel==4:
            sf = [f for f in obj.data.vertices if f.select == 1]
            v0 = Vector(sf[0].co)
            v1 = Vector(sf[1].co)
            v2 = Vector(sf[2].co)
            v3 = Vector(sf[3].co)
            fv = [v0, v1, v2, v3]
            q = G3.centerOfSphere(fv)
            if(q==None):
                return {'CANCELLED'}
            cc.setCursor(mat*q)
            return {'FINISHED'}
        return {'CANCELLED'}



class VIEW3D_OT_cursor_to_perimeter(bpy.types.Operator):
    """Move to perimeter of cylinder or sphere"""
    bl_idname = "view3d.cursor_to_perimeter"
    bl_label = "Move to perimeter of cylinder or sphere"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        BlenderFake.forceUpdate()
        cc = context.scene.cursor_control
        cc.hideLinexChoice()
        obj = bpy.context.active_object
        mesh = obj.data.vertices
        mat = obj.matrix_world
        mati = mat.copy()
        mati.invert()
        c = mati*Vector(CursorAccess.getCursor())

        if obj.data.total_vert_sel==3:
            sf = [f for f in obj.data.vertices if f.select == 1]
            v0 = Vector(sf[0].co)
            v1 = Vector(sf[1].co)
            v2 = Vector(sf[2].co)
            fv = [v0, v1, v2]
            q = G3.closestP2Cylinder(c, fv)
            if(q==None):
                return {'CANCELLED'}
            #q = G3.centerOfSphere(fv)
            cc.setCursor(mat*q)
            return {'FINISHED'}
        if obj.data.total_vert_sel==4:
            sf = [f for f in obj.data.vertices if f.select == 1]
            v0 = Vector(sf[0].co)
            v1 = Vector(sf[1].co)
            v2 = Vector(sf[2].co)
            v3 = Vector(sf[3].co)
            fv = [v0, v1, v2, v3]
            q = G3.closestP2Sphere(c, fv)
            if(q==None):
                return {'CANCELLED'}
            cc.setCursor(mat*q)
            return {'FINISHED'}
        return {'CANCELLED'}



#class VIEW3D_OT_cursor_offset_from_radius(bpy.types.Operator):
    #"""Calculate offset from radius"""
    #bl_idname = "view3d.cursor_offset_from_radius"
    #bl_label = "Calculate offset from radius"
    #bl_options = {'REGISTER'}

    #def modal(self, context, event):
        #return {'FINISHED'}

    #def execute(self, context):
        #BlenderFake.forceUpdate()
        #cc = context.scene.cursor_control
        #cc.hideLinexChoice()
        #obj = bpy.context.active_object
        #mesh = obj.data.vertices
        #mat = obj.matrix_world
        #mati = mat.copy()
        #mati.invert()
        #c = mati*Vector(CursorAccess.getCursor())

        #if obj.data.total_vert_sel==3:
            #sf = [f for f in obj.data.vertices if f.select == 1]
            #v0 = Vector(sf[0].co)
            #v1 = Vector(sf[1].co)
            #v2 = Vector(sf[2].co)
            #fv = [v0, v1, v2]
            #q = G3.centerOfSphere(fv)
            #d = (v0-q).length
            #cc.stepLengthValue = d
            #return {'FINISHED'}
        #if obj.data.total_vert_sel==4:
            #sf = [f for f in obj.data.vertices if f.select == 1]
            #v0 = Vector(sf[0].co)
            #v1 = Vector(sf[1].co)
            #v2 = Vector(sf[2].co)
            #v3 = Vector(sf[3].co)
            #fv = [v0, v1, v2, v3]
            #q = G3.centerOfSphere(fv)
            #d = (v0-q).length
            #cc.stepLengthValue = d
            #return {'FINISHED'}
        #return {'CANCELLED'}



class VIEW3D_OT_cursor_stepval_phinv(bpy.types.Operator):
    """Set step value to 1/Phi"""
    bl_idname = "view3d.cursor_stepval_phinv"
    bl_label = "Set step value to 1/Phi"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        cc = context.scene.cursor_control
        cc.stepLengthValue = PHI_INV
        BlenderFake.forceRedraw()
        return {'FINISHED'}



class VIEW3D_OT_cursor_stepval_phi(bpy.types.Operator):
    """Set step value to Phi"""
    bl_idname = "view3d.cursor_stepval_phi"
    bl_label = "Set step value to Phi"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        cc = context.scene.cursor_control
        cc.stepLengthValue = PHI
        BlenderFake.forceRedraw()
        return {'FINISHED'}



class VIEW3D_OT_cursor_stepval_phi2(bpy.types.Operator):
    """Set step value to Phi²"""
    bl_idname = "view3d.cursor_stepval_phi2"
    bl_label = "Set step value to Phi²"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        cc = context.scene.cursor_control
        cc.stepLengthValue = PHI_SQR
        BlenderFake.forceRedraw()
        return {'FINISHED'}



class VIEW3D_OT_cursor_stepval_vvdist(bpy.types.Operator):
    """Set step value to distance vertex-vertex"""
    bl_idname = "view3d.cursor_stepval_vvdist"
    bl_label = "Set step value to distance vertex-vertex"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        BlenderFake.forceUpdate()
        cc = context.scene.cursor_control
        cc.hideLinexChoice()
        obj = bpy.context.active_object
        mesh = obj.data.vertices
        mat = obj.matrix_world
        mati = mat.copy()
        mati.invert()
        c = mati*Vector(CursorAccess.getCursor())

        sf = [f for f in obj.data.vertices if f.select == 1]
        v0 = Vector(sf[0].co)
        v1 = Vector(sf[1].co)
        q = (v0-v1).length
        cc.stepLengthValue = q

        BlenderFake.forceRedraw()
        return {'FINISHED'}




class VIEW3D_OT_ccdelta_invert(bpy.types.Operator):
    """Invert delta vector"""
    bl_idname = "view3d.ccdelta_invert"
    bl_label = "Invert delta vector"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        cc = context.scene.cursor_control
        cc.invertDeltaVector()
        return {'FINISHED'}



class VIEW3D_OT_ccdelta_normalize(bpy.types.Operator):
    """Normalize delta vector"""
    bl_idname = "view3d.ccdelta_normalize"
    bl_label = "Normalize delta vector"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        cc = context.scene.cursor_control
        cc.normalizeDeltaVector()
        return {'FINISHED'}



class VIEW3D_OT_ccdelta_add(bpy.types.Operator):
    """Add delta vector to 3D cursor"""
    bl_idname = "view3d.ccdelta_add"
    bl_label = "Add delta vector to 3D cursor"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        cc = context.scene.cursor_control
        cc.addDeltaVectorToCursor()
        return {'FINISHED'}



class VIEW3D_OT_ccdelta_sub(bpy.types.Operator):
    """Subtract delta vector to 3D cursor"""
    bl_idname = "view3d.ccdelta_sub"
    bl_label = "Subtract delta vector to 3D cursor"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        cc = context.scene.cursor_control
        cc.subDeltaVectorToCursor()
        return {'FINISHED'}



class VIEW3D_OT_ccdelta_vvdist(bpy.types.Operator):
    """Set delta vector from selection"""
    bl_idname = "view3d.ccdelta_vvdist"
    bl_label = "Set delta vector from selection"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        BlenderFake.forceUpdate()
        cc = context.scene.cursor_control
        obj = bpy.context.active_object
        if obj.data.total_vert_sel==0:
            if hasattr(context.scene, "cursor_memory"):
                cm = context.scene.cursor_memory
                
                mesh = obj.data.vertices
                mat = obj.matrix_world
                mati = mat.copy()
                mati.invert()
                c = mati*Vector(CursorAccess.getCursor())
                
                v0 = Vector(cm.savedLocation)
                v1 = Vector(c)
                cc.deltaVector = v0-v1
                
                
        if obj.data.total_vert_sel==1:
            mesh = obj.data.vertices
            mat = obj.matrix_world
            mati = mat.copy()
            mati.invert()
            c = mati*Vector(CursorAccess.getCursor())

            sf = [f for f in obj.data.vertices if f.select == 1]
            v0 = Vector(sf[0].co)
            v1 = Vector(c)
            cc.deltaVector = v0-v1

        if obj.data.total_vert_sel==2:
            #mesh = obj.data.vertices
            #mat = obj.matrix_world
            #mati = mat.copy()
            #mati.invert()
            #c = mati*Vector(CursorAccess.getCursor())

            sf = [f for f in obj.data.vertices if f.select == 1]
            v0 = Vector(sf[0].co)
            v1 = Vector(sf[1].co)
            cc.deltaVector = v1-v0

        return {'FINISHED'}




