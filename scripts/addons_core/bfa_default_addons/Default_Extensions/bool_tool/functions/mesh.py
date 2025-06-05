import bpy, bmesh, mathutils, math
from bpy_extras import view3d_utils


#### ------------------------------ FUNCTIONS ------------------------------ ####

def create_cutter_shape(self, context):
    """Creates flat mesh from the vertices provided in `self.verts` (which is created by `carver_overlay`)"""

    # ALIGNMENT: View
    coords = self.mouse_path[0][0], self.mouse_path[0][1]
    region = context.region
    rv3d = context.region_data
    depth_location = view3d_utils.region_2d_to_vector_3d(region, rv3d, coords)
    self.view_vector = depth_location
    plane_direction = depth_location.normalized()

    # depth
    if self.depth == 'CURSOR':
        plane_point = context.scene.cursor.location
    elif self.depth == 'VIEW':
        plane_point = mathutils.Vector((0.0, 0.0, 0.0))


    # Create Mesh & Object
    faces = {}
    mesh = bpy.data.meshes.new(name='cutter')
    bm = bmesh.new()
    bm.from_mesh(mesh)

    obj = bpy.data.objects.new('cutter', mesh)
    obj.booleans.carver = True
    self.cutter = obj
    context.collection.objects.link(obj)

    # Create Faces from `self.verts`
    create_face(context, plane_direction, plane_point,
                bm, "original", faces, self.verts)

    # ARRAY
    if len(self.duplicates) > 0:
        for i, duplicate in self.duplicates.items():
            create_face(context, plane_direction, plane_point,
                        bm, str(i), faces, duplicate)

    bm.verts.index_update()
    for i, face in faces.items():
        bm.faces.new(face)

    # remove_doubles
    bmesh.ops.remove_doubles(bm, verts=[v for v in bm.verts], dist=0.0001)

    bm.to_mesh(mesh)


def extrude(self, mesh):
    """Extrudes cutter face (created by carve operation) along view vector to create a non-manifold mesh"""

    bm = bmesh.new()
    bm.from_mesh(mesh)
    faces = [f for f in bm.faces]

    # move_the_mesh_towards_view
    box_bounding = combined_bounding_box(self.selected_objects)
    for face in faces:
        for vert in face.verts:
            # vert.co += -self.view_vector * box_bounding
            vert.co += -self.view_vector * box_bounding

    # extrude_the_face
    ret = bmesh.ops.extrude_face_region(bm, geom=faces)
    verts_extruded = [v for v in ret['geom'] if isinstance(v, bmesh.types.BMVert)]
    for v in verts_extruded:
        if self.depth == 'CURSOR':
            v.co += self.view_vector * box_bounding
        elif self.depth == 'VIEW':
            v.co += self.view_vector * box_bounding * 2

    # correct_normals
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    bm.to_mesh(mesh)
    mesh.update()
    bm.free()


def combined_bounding_box(objects):
    """Calculate the combined bounding box of multiple objects."""
    
    min_corner = mathutils.Vector((float('inf'), float('inf'), float('inf')))
    max_corner = mathutils.Vector((-float('inf'), -float('inf'), -float('inf')))

    for obj in objects:
        # Transform the bounding box corners to world space
        bbox_corners = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]

        for corner in bbox_corners:
            min_corner.x = min(min_corner.x, corner.x)
            min_corner.y = min(min_corner.y, corner.y)
            min_corner.z = min(min_corner.z, corner.z)
            max_corner.x = max(max_corner.x, corner.x)
            max_corner.y = max(max_corner.y, corner.y)
            max_corner.z = max(max_corner.z, corner.z)

    # Calculate the diagonal of the combined bounding box
    bounding_box_diag = (max_corner - min_corner).length
    return bounding_box_diag


def create_face(context, direction, depth, bm, name, faces, verts, polyline=False):
    """Creates bmesh face with given list of vertices and appends it to given 'faces' dict"""

    def intersect_line_plane(context, vert, direction, depth):
        """Finds the intersection of a line going through each vertex and the infinite plane"""

        region = context.region
        rv3d = context.region_data

        vec = view3d_utils.region_2d_to_vector_3d(region, rv3d, vert)
        p0 = view3d_utils.region_2d_to_location_3d(region, rv3d, vert, vec)
        p1 = p0 + direction
        loc = mathutils.geometry.intersect_line_plane(p0, p1, depth, direction)

        return loc

    face_verts = []
    for i, vert in enumerate(verts):
        loc = intersect_line_plane(context, vert, direction, depth)
        vertex = bm.verts.new(loc)
        face_verts.append(vertex)

    faces[name] = face_verts


def shade_smooth_by_angle(obj, angle=30):
    """Replication of "Auto Smooth" functionality: Marks faces as smooth, sharp edges (by angle) as sharp"""

    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    # shade_smooth
    for f in bm.faces:
        f.smooth = True

    # select_sharp_edges
    for edge in bm.edges:
        if len(edge.link_faces) == 2:
            face1, face2 = edge.link_faces
            edge_angle = math.degrees(face1.normal.angle(face2.normal))
            if edge_angle >= angle:
                edge.select = True

    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    # mark_sharp_edges
    for edge in mesh.edges:
        if edge.select:
            edge.use_edge_sharp = True
    mesh.update()
