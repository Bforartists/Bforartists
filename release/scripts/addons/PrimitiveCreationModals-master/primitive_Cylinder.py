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

    
def cylindermesh(radius_out = 1.0, radius_in = 0.0, use_inner = True, sector_from = 0.0, sector_to = 2*pi, scale = (1, 1, 2), seg = (32, 1, 1), centered = (True, True, True)):
    #init Vars
    height = scale.z
    size_x = scale.x
    size_y = scale.y
    seg_perimeter = seg[0]
    seg_radius = seg[1] + 1
    seg_height = seg[2] + 1
    
    
    verts = []
    edges = []
    faces = []

    top_rings = []
    bottom_rings = []
    loops = []
    inner_loops = []
    midpoints = []

    #Make sure the outer radius is larger.
    if radius_out < radius_in:
        radius_in, radius_out = radius_out, radius_in

    if sector_from > sector_to:
        sector_to, sector_from = sector_from, sector_to

    if radius_out - radius_in < 0.0001:
        use_inner = False

    #Make sure there is at least 3 Verts, otherwise it's not a Circle
    if seg_perimeter < 3:
        seg_perimeter = 3

    stepAngle = (sector_to - sector_from) / seg_perimeter
    stepRadius = (radius_out - radius_in) / seg_radius
    stepHeight = height / seg_height

    middlePoint = radius_in <= 0.0001
    closed = (sector_to - sector_from) >= 2*pi
    seg_number = seg_perimeter
    if not closed:
        seg_number = seg_perimeter +1
    rad_number = seg_radius
    if middlePoint:
        rad_number = seg_radius -1

    #Side Verts
    for z in range(seg_height +1):
        loop = []
        for s in range(seg_number):
            loop.append(len(verts))
            quat = Quaternion((0,0,1), (s * stepAngle) + sector_from)
            verts.append(quat * Vector((radius_out, 0.0, z * stepHeight)))
        loops.append(loop)

    #Side Faces
    for i in range(len(loops) -1):
        faces.extend(bridgeVertLoops(loops[i], loops[i +1], closed))

    
    if use_inner:
        #fill the caps (without the center)
        for z in range(2):
            if z == 0:
                bottom_rings.append(loops[0])
            else:
                top_rings.append(loops[-1])

            for r in range(rad_number):
                ring = []
                for s in range(seg_number):
                    ring.append(len(verts))
                    quat = Quaternion((0,0,1), (s * stepAngle) + sector_from)
                    verts.append(quat * Vector((radius_out - ((r+1) * stepRadius), 0.0, z * height)))
                if z == 0:
                    bottom_rings.append(ring)
                else:
                    top_rings.append(ring)



        for i in range(len(top_rings) -1):
            faces.extend(bridgeVertLoops(top_rings[i], top_rings[i +1], closed))
        for i in range(len(bottom_rings) -1):
            faces.extend(bridgeVertLoops(bottom_rings[-(i+1)], bottom_rings[-(i+2)], closed))

        
        #fill the center
        if middlePoint:
            #fill with middle point
            if closed:
                for z in range(2):
                    midpoints.append(len(verts))
                    verts.append(Vector((0.0, 0.0, z * height)))
            else:
                for z in range(seg_height +1):
                    midpoints.append(len(verts))
                    verts.append(Vector((0.0, 0.0, z * stepHeight)))

            #close the cup
            for s in range(seg_number -1):
                faces.append((bottom_rings[-1][s], midpoints[0], bottom_rings[-1][s+1]))
                faces.append((top_rings[-1][s], top_rings[-1][s+1], midpoints[-1]))
            if closed:
                faces.append((bottom_rings[-1][-1], midpoints[0], bottom_rings[-1][0]))
                faces.append((top_rings[-1][-1], top_rings[-1][0], midpoints[-1]))

        else:
            #fill with inner loops
            inner_loops.append(bottom_rings[-1])
            for z in range(seg_height-1):
                loop = []
                for s in range(seg_number):
                    loop.append(len(verts))
                    quat = Quaternion((0,0,1), (s * stepAngle) + sector_from)
                    verts.append(quat * Vector((radius_in, 0.0, (z+1) * stepHeight)))
                inner_loops.append(loop)
            inner_loops.append(top_rings[-1])
            for i in range(len(inner_loops) -1):
                faces.extend(bridgeVertLoops(inner_loops[-(i+1)], inner_loops[-(i+2)], closed))

        #fill the walls
        if not closed:
            wall_lines_01 = []
            wall_lines_02 = []
            if middlePoint:
                rad_number += 1
            #first wall
            quat = Quaternion((0,0,1), sector_from)
            line = []
            for loop in loops:
                line.append(loop[0])
            wall_lines_01.append(line)
            for r in range(rad_number-1):
                line = []
                line.append(bottom_rings[r+1][0])
                for h in range(seg_height -1):
                    line.append(len(verts))
                    verts.append(quat * Vector((radius_out - ((r+1) *stepRadius), 0.0, (h+1) * stepHeight)))
                line.append(top_rings[r+1][0])
                wall_lines_01.append(line)

            if middlePoint:
                wall_lines_01.append(midpoints)
            else:
                line = []
                for loop in inner_loops:
                    line.append(loop[0])
                wall_lines_01.append(line)

            #second wal
            quat = Quaternion((0,0,1), sector_to)
            line = []
            for loop in loops:
                line.append(loop[-1])
            wall_lines_02.append(line)
            for r in range(rad_number-1):
                line = []
                line.append(bottom_rings[r+1][-1])
                for h in range(seg_height -1):
                    line.append(len(verts))
                    verts.append(quat * Vector((radius_out - ((r+1) *stepRadius), 0.0, (h+1) * stepHeight)))
                line.append(top_rings[r+1][-1])
                wall_lines_02.append(line)

            if middlePoint:
                wall_lines_02.append(midpoints)
            else:
                line = []
                for loop in inner_loops:
                    line.append(loop[-1])
                wall_lines_02.append(line)

            #filling the walls
            for i in range(len(wall_lines_01) -1):
                faces.extend(bridgeVertLoops(wall_lines_01[i], wall_lines_01[i +1], False))
            for i in range(len(wall_lines_02) -1):
                faces.extend(bridgeVertLoops(wall_lines_02[-(i+1)], wall_lines_02[-(i+2)], False))

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
        
    #Inverts mesh faces if the mesh is inverted
    if size_x * size_y * height < 0:
        Faceinv = []
        for f in faces:
            temp = tuple(reversed(f))
            Faceinv.append(temp)
        faces = Faceinv

    return verts, edges, faces

def UpdateCylinder(cont, scale, seg, center):
    #updates the Cylinder. use this in object mode so you're not using an operator that is a performance hog
    verts, edges, faces = cylindermesh(scale = scale, seg = seg, centered = center)

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
    bl_idname = "mesh.add_primcylinder"
    bl_label = "Add PrimCylinder"
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
        verts, edges, faces = cylindermesh(scale = self.scale, seg = self.seg, centered = self.center)
                
        # Create new mesh
        mesh = bpy.data.meshes.new("Cylinder")

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
