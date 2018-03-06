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

    
def spheremesh(radius = 1, seg = (32, 16, 1), size = Vector((1,1,1)), centered = (True, True, True)): 

    #init Vars
    segments = seg[0]
    rings = seg[1]
    
    #Make sure the segments stay high enough to make something at least resembling a sphere.
    if segments < 3:
        segments = 3
    if rings < 3:
        rings = 3
        

    verts = []
    edges = []
    faces = []

    loops = []

    #Create top and bottom verts
    verts.append(Vector((0.0, 0.0, radius)))
    verts.append(Vector((0.0, 0.0, -radius)))

    #Calculate angles
    UAngle = (2*pi)/segments
    VAngle = pi/rings

    #Create rings
    for v in range(rings -1):
        loop = []
        quatV = Quaternion((0,-1,0), VAngle * (v +1))
        baseVect = quatV * Vector((0.0, 0.0, -radius))
        for u in range(segments):
            loop.append(len(verts))
            quatU = Quaternion((0, 0, 1), UAngle * u)
            verts.append(quatU * baseVect)
        loops.append(loop)

    #Create faces
    for i in range(rings -2):
        faces.extend(bridgeVertLoops(loops[i], loops[i+1], True))

    #Fill top fan
    ring = loops[-1]
    for i in range(segments):
        if (i == segments -1):
            faces.append((ring[i], ring[0], 0))
        else:
            faces.append((ring[i], ring[i+1], 0))

    #Fill bottom fan
    ring = loops[0]
    for i in range(segments):
        if (i == segments -1):
            faces.append((ring[0], ring[i], 1))
        else:
            faces.append((ring[i+1], ring[i], 1))
            
    #X,Y,Z, Center 
    if not centered[0] or not centered[1] or not centered[2]:
        half_x = 0
        half_y = 0
        half_z = 0
        
        if not centered[0]:
            half_x = radius
        if not centered[1]:
            half_y = radius
        if not centered[2]:
            half_z = radius
        
        for vertex in verts:
            vertex -= Vector((half_x, half_y, half_z))
    
    #Scale mesh 
    for vertex in verts:
        half_x = size.x
        half_y = size.y
        half_z = size.z
        vertex.x *= (size.x / 2) * -1
        vertex.y *= (size.y / 2) * -1
        vertex.z *= (size.z / 2) * -1
        
    #Inverts mesh faces if the mesh is inverted
    if size.x * size.y * (size.z * -1) < 0:
        Faceinv = []
        for f in faces:
            temp = tuple(reversed(f))
            Faceinv.append(temp)
        faces = Faceinv
    
    
    return verts, edges, faces

def UpdateSphere(cont, scale, seg, center):
    #updates the Circle. use this in object mode so you're not using an operator that is a performance hog
    verts, edges, faces = spheremesh(seg=seg, size=scale, centered=center)
    
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
    bl_idname = "mesh.add_primsphere"
    bl_label = "Add PrimSphere"
    bl_options = {'REGISTER', 'UNDO'}

    scale = FloatVectorProperty(
            name="scale",
            default=(1.0, 1.0, 1.0),
            subtype='TRANSLATION',
            description="scaling",
            )
    seg = IntVectorProperty(
            name="Segments",
            default=(32.0, 16.0, 1.0),
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
        verts, edges, faces = spheremesh(seg=self.seg, size=self.scale, centered=self.center)
        
        # Create new mesh
        mesh = bpy.data.meshes.new("Sphere")

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
