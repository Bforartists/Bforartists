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



import bpy
import bmesh
from mathutils.geometry import area_tri
from math import sqrt
from math import pow


def setImageRes(object):
    global pixels
    mat = object.material_slots[object.active_material_index].material
    if  mat.node_tree.nodes.active.type in ["TEX_IMAGE"]:
        pixels = [mat.node_tree.nodes.active.image.size[0] ,mat.node_tree.nodes.active.image.size[1] ]
        return(True)

    else:
        print("Please select image node first")
        return(False)


def makeTessellate(actObj):
    global bm_tess
    ob = actObj
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm_tess = bpy.data.meshes.new("Tris")
    bm.to_mesh(bm_tess)


def calcArea():
    global totalArea
    totalArea = 0
    for poly in bm_tess.polygons:
        uno = bm_tess.uv_layers.active.data[poly.loop_indices[0]].uv
        dos = bm_tess.uv_layers.active.data[poly.loop_indices[1]].uv
        tres = bm_tess.uv_layers.active.data[poly.loop_indices[2]].uv
        area = area_tri(uno, dos, tres)
        totalArea += area

    bpy.data.meshes.remove(
        bm_tess,
        do_unlink=True,
        do_id_user=True,
        do_ui_user=True)


def calcMeshArea(ob):
    global GlobLog
    polyArea = 0
    for poly in ob.data.polygons:
        polyArea += poly.area
    ta = "UvGain: %s%s || " % (round(totalArea * 100),"%")    
    ma = "MeshArea: %s || " % (polyArea)
    pg = "PixelsGain: %s || " % (round(totalArea * (pixels[0] * pixels[1])))
    pl = "PixelsLost: %s || " % ((pixels[0]*pixels[1]) - round(totalArea * (pixels[0] * pixels[1])))
    tx = "Texel: %s pix/meter" % (round(sqrt(totalArea * pixels[0] * pixels[1] / polyArea)))    
    GlobLog = ta+ma+pg+pl+tx            

     


class uvStats(bpy.types.Operator):
    """Print Uv Stats"""
    bl_idname = "mesh.print_uv_stats"
    bl_label = "Print Uv Stats"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):              
        if round(
                bpy.context.object.scale.x,
                2) == 1 and round(
                    bpy.context.object.scale.y,
                    2) == 1 and round(
                        bpy.context.object.scale.x,
                        2) == 1:
            if setImageRes(bpy.context.object):
                makeTessellate(bpy.context.object)
                calcArea()
                calcMeshArea(bpy.context.object)   
        else:
            print("Warning: Non Uniform Scale Object")
            
            copyOb = bpy.context.object.copy()
            copyMe = bpy.context.object.data.copy()
            bpy.context.scene.collection.objects.link(copyOb)
            copyOb.data = copyMe
            bpy.ops.object.select_all(action="DESELECT")
            copyOb.select_set(1)
            bpy.ops.object.transform_apply()    
            
            if setImageRes(copyOb):
                makeTessellate(copyOb)
                calcArea()
                calcMeshArea(copyOb)
                
            bpy.data.objects.remove(copyOb)
            bpy.data.meshes.remove(copyMe)    
            
        self.report({'INFO'}, GlobLog)             
        return {'FINISHED'}       