import bpy
import bmesh
from bpy.types import Operator
from bpy_extras.object_utils import AddObjectHelper, object_data_add
from bpy.props import (
    FloatVectorProperty,
    IntVectorProperty,
    BoolVectorProperty,
    PointerProperty
)
from mathutils import (
    Quaternion,
    Vector
)
from math import pi

from .gen_func import bridgeVertLoops

    
def circlemesh(radius_out = 1.0, radius_in = 0.0, use_inner = True, sector_from = 0.0, sector_to = 2*pi, scale = (1, 1, 2), seg = (32, 1, 1), centered = (True, True, True)):#height = 2.0, use_inner = True, seg_perimeter = 32, seg_radius = 1, seg_height = 1, sector_from = 0.0, sector_to = 2*pi, centered = True, size_x = 1, size_y = 1):
    
    #init vars
    height = scale.z
    size_x = scale.x
    size_y = scale.y
    seg_perimeter = seg[0]
    seg_radius = seg[1] + 1
    seg_height = seg[2] + 1
    
    verts = []
    edges = []
    faces = []

    loops = []

    #Make sure the outer radius is larger.
    if radius_out < radius_in:
        radius_in, radius_out = radius_out, radius_in

    if sector_from > sector_to:
        sector_to, sector_from = sector_from, sector_to

    if (radius_out - radius_in) < 0.0001:
        use_inner = False

    #Make sure there is at least 3 Verts, otherwise it's not a Circle
    if seg_perimeter < 3:
        seg_perimeter = 3

    stepAngle = (sector_to - sector_from) / seg_perimeter
    stepRadius = (radius_out - radius_in) / seg_radius

    loop_number = seg_radius
    if radius_in > 0.0001:
        loop_number = seg_radius +1

    seg_number = seg_perimeter
    closed = True
    if sector_to - sector_from < (2 * pi):
        seg_number = seg_perimeter +1
        closed = False

    if use_inner:
        for r in range(loop_number):
            loop = []
            for s in range(seg_number):
                loop.append(len(verts))
                quat = Quaternion((0,0,1), (s * stepAngle) + sector_from)
                verts.append(quat * Vector((radius_out - (r * stepRadius), 0.0, 0.0)))
            loops.append(loop)

        #fill the loops
        for i in range(len(loops) -1):
            faces.extend(bridgeVertLoops(loops[i], loops[i +1], closed))

        #Center Point
        if loop_number == seg_radius:
            verts.append(Vector((0.0, 0.0, 0.0)))
            for s in range(seg_number -1):
                faces.append((loops[-1][s], loops[-1][s+1], len(verts) -1))
            if seg_number == seg_perimeter:
                faces.append((loops[-1][-1], loops[-1][0], len(verts) -1))

    else:
        for s in range(seg_number):
            quat = Quaternion((0,0,1), (s * stepAngle) + sector_from)
            verts.append(quat * Vector((radius_out, 0.0, 0.0)))

        for v in range(len(verts) -1):
            edges.append((v, v+1))
        if closed:
            edges.append((len(verts) -1, 0))

    #X,Y,Z, Center 
    if not centered[0] or not centered[1] or not centered[2]:
        half_x = 0
        half_y = 0
        half_z = 0
        
        if not centered[0]:
            half_x = radius_out
        if not centered[1]:
            half_y = radius_out
        if not centered[2]:
            half_z = height / 2
        
        for vertex in verts:
            vertex -= Vector((half_x, half_y, half_z))
    
    #Scale mesh 
    for vertex in verts:
        half_x = size_x
        half_y = size_y
        half_z = 0
        vertex.x *= (size_x / 2) * -1
        vertex.y *= (size_y / 2) * -1
        vertex.z *= (height / 2) * -1

    #Inverts mesh faces if the mesh is inverted
    if size_x * size_y * height < 0:
        Faceinv = []
        for f in faces:
            temp = tuple(reversed(f))
            Faceinv.append(temp)
        faces = Faceinv

    return verts, edges, faces

def UpdateCircle(cont, scale, seg, center):
    #updates the Circle. use this in object mode so you're not using an operator that is a performance hog
    verts, edges, faces = circlemesh(scale = scale, seg = seg, centered = center)
    
    tmpMesh = bpy.data.meshes.new("TemporaryMesh")
    tmpMesh.from_pydata(verts, edges, faces)
    tmpMesh.update()

    bm = bmesh.new()
    bm.from_mesh(tmpMesh)
    bm.to_mesh(cont.object.data)
    bm.free()
    
    bpy.data.meshes.remove(tmpMesh)
    bpy.context.active_object.data.update()

class OBJECT_OT_add_object(Operator, AddObjectHelper):
    """Create a new Mesh Object"""
    bl_idname = "mesh.add_primcircle"
    bl_label = "Add PrimCircle"
    bl_options = {'REGISTER', 'UNDO'}

    scale = FloatVectorProperty(
            name="scale",
            default=(1.0, 1.0, 1.0),
            subtype='TRANSLATION',
            description="scaling",
            )
    seg = IntVectorProperty(
            name="Segments",
            default=(32.0, 1.0, 1.0),
            subtype='TRANSLATION',
            description="Segments",
            )
            
    center = BoolVectorProperty(
                name="Centered",
                default=(True, True, True),
                description="Is it Centered"
                )

    def execute(self, context):

        #Create mesh Data
        verts, edges, faces = circlemesh(scale = self.scale, seg = self.seg, centered = self.center)
                
        # Create new mesh
        mesh = bpy.data.meshes.new("Circle")

        # Make a mesh from a list of verts/edges/faces.
        mesh.from_pydata(verts, edges, faces)

        # Update mesh geometry after adding stuff.
        mesh.update()
        
        object_data_add(context, mesh, operator=self)
        
        return {'FINISHED'}


# Registration
def register():
    bpy.utils.register_class(OBJECT_OT_add_object)



def unregister():
    bpy.utils.unregister_class(OBJECT_OT_add_object)



if __name__ == "__main__":
    register()