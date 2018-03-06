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

    
def boxmesh(size = (1, 1, 1), seg = (1, 1, 1), centered = (True, True, True)):

    #init Vars
    size_x = size.x
    size_y = size.y
    size_z = size.z
    seg_x = seg[0] + 1
    seg_y = seg[1] + 1
    seg_z = seg[2] + 1
    
    verts = []
    edges = []
    faces = []

    bottom_lines = []
    top_lines = []
    loops = []

    dist_x = size_x / seg_x
    dist_y = size_y / seg_y
    dist_z = size_z / seg_z

    #Bottom Verts
    for y in range(seg_y +1):
        line = []
        for x in range(seg_x +1):
            line.append(len(verts))
            verts.append(Vector((x * dist_x, y * dist_y, 0.0)))
        bottom_lines.append(line)

    #Top Verts
    for y in range(seg_y +1):
        line = []
        for x in range(seg_x +1):
            line.append(len(verts))
            verts.append(Vector((x * dist_x, y * dist_y, size_z)))
        top_lines.append(line)

    #Bottom Edges
    loop = []
    for i in range(seg_x +1):
        loop.append(bottom_lines[0][i])
    for i in range(seg_y -1):
        loop.append(bottom_lines[i+1][-1])
    for i in range(seg_x +1):
        loop.append(bottom_lines[-1][-(i+1)])
    for i in range(seg_y -1):
        loop.append(bottom_lines[-(i+2)][0])
    loops.append(loop)

    #Side Segments
    for z in range(seg_z -1):
        loop = []
        for i in range(seg_x +1):
            loop.append(len(verts))
            verts.append(Vector((i * dist_x, 0.0, (z +1) * dist_z)))
        for i in range(seg_y -1):
            loop.append(len(verts))
            verts.append(Vector((size_x, (i +1) * dist_y, (z +1) * dist_z)))
        for i in range(seg_x +1):
            loop.append(len(verts))
            verts.append(Vector((size_x - (i * dist_x), size_y, (z +1) * dist_z)))
        for i in range(seg_y -1):
            loop.append(len(verts))
            verts.append(Vector((0.0, size_y - ((i +1) * dist_y), (z +1) * dist_z)))
        loops.append(loop)

    #Top Edges
    loop = []
    for i in range(seg_x +1):
        loop.append(top_lines[0][i])
    for i in range(seg_y -1):
        loop.append(top_lines[i+1][-1])
    for i in range(seg_x +1):
        loop.append(top_lines[-1][-(i+1)])
    for i in range(seg_y -1):
        loop.append(top_lines[-(i+2)][0])
    loops.append(loop)

    #Bottom Faces
    for i in range(seg_y):
        
        bottomFace = bridgeVertLoops(bottom_lines[i], bottom_lines[i +1], False)
        
        #invert bottom face so it's the correct direction.
        bottomFaceinv = []
        for f in bottomFace:
            temp = tuple(reversed(f))
            bottomFaceinv.append(temp)
        faces.extend(bottomFaceinv)


    #Top Faces
    for i in range(seg_y):
        faces.extend(bridgeVertLoops(top_lines[i], top_lines[i +1], False))

    #Side Faces
    for i in range(seg_z):
        faces.extend(bridgeVertLoops(loops[i], loops[i+1], True))

    #X,Y,Z, Center
    if centered[0] or centered[1] or centered[2]:
        half_x = 0
        half_y = 0
        half_z = 0
        
        if centered[0]:
            half_x = size_x /2
        if centered[1]:
            half_y = size_y /2
        if centered[2]:
            half_z = size_z /2
        
        for vertex in verts:
            vertex -= Vector((half_x, half_y, half_z))
    
    #Inverts mesh faces if the mesh is inverted
    if size_x * size_y * size_z < 0:

        Faceinv = []
        for f in faces:
            temp = tuple(reversed(f))
            Faceinv.append(temp)
        faces = Faceinv
        
    return verts, edges, faces

def UpdateBox(cont, scale, seg, center):
    
    #updates the box. use this in object mode so you're not using an operator that is a performance hog
    verts, edges, faces = boxmesh(scale, seg, center)
    
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
    bl_idname = "mesh.add_primbox"
    bl_label = "Add PrimBox"
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
                default=(True,True,True),
                description="Is it Centered"
                )

    def execute(self, context):

        #Create mesh Data
        verts, edges, faces = boxmesh(self.scale, self.seg, self.center)
                
        # Create new mesh
        mesh = bpy.data.meshes.new("Box")

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
