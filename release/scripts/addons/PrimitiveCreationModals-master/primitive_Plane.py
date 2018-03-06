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
    Vector
)

from .gen_func import bridgeVertLoops

    
def planemesh(size = (1, 1, 1), seg = (1, 1, 1), centered = (True, True, True)):

    #init Vars
    x = size.x
    y = size.y
    z = size.z
    seg_x = seg[0] + 1
    seg_y = seg[1] + 1

    verts = []
    edges = []
    faces = []
    lines = []

    dist_x = x / seg_x
    dist_y = y / seg_y

    for i in range(seg_y +1):
        line = []
        for j in range(seg_x +1):
            line.append(len(verts))
            verts.append(Vector((j*dist_x, i*dist_y, 0.0)))
        lines.append(line)

    for i in range(len(lines) -1):
        faces.extend(bridgeVertLoops(lines[i], lines[i+1], False))

    #X,Y, Centered
    if centered[0] or centered[1]:
        half_x = 0
        half_y = 0
                
        if centered[0]:
            half_x = x /2
        if centered[1]:
            half_y = y /2
                
        for vertex in verts:
            vertex[0] -= half_x
            vertex[1] -= half_y

    #Inverts mesh faces if the mesh is inverted
    if x * y * z < 0:
        Faceinv = []
        for f in faces:
            temp = tuple(reversed(f))
            Faceinv.append(temp)
        faces = Faceinv

        
    return verts, edges, faces

def UpdatePlane(cont, scale, seg, center):
    #updates the Plane. use this in object mode so you're not using an operator that is a performance hog
    verts, edges, faces = planemesh(scale, seg, center)
    
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
    bl_idname = "mesh.add_primplane"
    bl_label = "Add PrimPlane"
    bl_options = {'REGISTER', 'UNDO'}

    scale = FloatVectorProperty(
            name="scale",
            default=(1.0, 1.0, 1.0),
            subtype='TRANSLATION',
            description="scaling",
            )
    seg = IntVectorProperty(
            name="Segments",
            default=(1.0, 1.0, 1.0),
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
        verts, edges, faces = planemesh(self.scale, self.seg, self.center)
                
        # Create new mesh
        mesh = bpy.data.meshes.new("Plane")

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
