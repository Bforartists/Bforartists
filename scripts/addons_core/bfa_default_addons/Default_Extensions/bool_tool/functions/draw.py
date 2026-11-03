import bpy
import gpu
import math
import mathutils
from bpy_extras import view3d_utils
from mathutils import Vector
from gpu_extras.batch import batch_for_shader


#### ------------------------------ FUNCTIONS ------------------------------ ####

def draw_shader(type, color, alpha, coords, size=1, indices=None):
    """Sets up and draws a batch for a given GPU shader type."""

    gpu.state.blend_set('ALPHA')

    if type == 'POINTS':
        gpu.state.program_point_size_set(False)
        gpu.state.point_size_set(size)
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        shader.uniform_float("color", (color[0], color[1], color[2], alpha))
        batch = batch_for_shader(shader, 'POINTS', {"pos": coords}, indices=indices)

    elif type in 'LINES':
        gpu.state.line_width_set(size)
        shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        shader.uniform_float("viewportSize", gpu.state.viewport_get()[2:])
        shader.uniform_float("lineWidth", size)
        shader.uniform_float("color", (color[0], color[1], color[2], alpha))
        batch = batch_for_shader(shader, 'LINES', {"pos": coords}, indices=indices)

    elif type in 'LINE_LOOP':
        shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        shader.uniform_float("viewportSize", gpu.state.viewport_get()[2:])
        shader.uniform_float("lineWidth", size)
        shader.uniform_float("color", (color[0], color[1], color[2], alpha))
        batch = batch_for_shader(shader, 'LINE_LOOP', {"pos": coords})

    if type == 'SOLID':
        gpu.state.depth_test_set('NONE')
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        shader.uniform_float("color", (color[0], color[1], color[2], alpha))
        batch = batch_for_shader(shader, 'TRIS', {"pos": coords}, indices=indices)

    batch.draw(shader)
    gpu.state.point_size_set(1.0)
    gpu.state.line_width_set(1.0)
    gpu.state.blend_set('NONE')


def draw_bmesh_faces(faces, world_matrix) -> tuple[list, list]:
    """
    Gets world-space vertex pairs and indices from `bmesh` faces.
    Returns the list of 3D vertices and the list of triangle indices to be used in GPU batch.
    Adapted from "Blockout" extension by niewinny (https://github.com/niewinny/blockout).
    """

    if not faces:
        return None, None

    vertices = []
    indices = []

    vert_index_map = {}
    vert_count = 0
    for face in faces:
        face_indices = []

        # Collect unique vertices only (avoid storing verts that are shared by multiple faces).
        # (NOTE: Iterating over face corners because unlike `face.verts` they're ordered).
        for loop in face.loops:
            vert = loop.vert

            if vert not in vert_index_map:
                co = world_matrix @ Vector(vert.co)
                vertices.append(co)
                vert_index_map[vert] = vert_count
                face_indices.append(vert_count)
                vert_count += 1
            else:
                face_indices.append(vert_index_map[vert])

        # Triangulate face and map local indices to global vertex indices.
        if len(face_indices) >= 3:
            try:
                face_verts_co = [vertices[idx] for idx in face_indices]
                tris = mathutils.geometry.tessellate_polygon([face_verts_co])
                for tri in tris:
                    indices.append((face_indices[tri[0]], face_indices[tri[1]], face_indices[tri[2]]))
            except:
                # Fallback to simple fan triangulation if tessellation fails.
                for i in range(1, len(face_indices) - 1):
                    indices.append((face_indices[0], face_indices[i], face_indices[i + 1]))

    return vertices, indices


def draw_circle_billboard(context, origin: Vector, radius: float, segments: int) -> list:
    """
    Draws a view-facing circle in the world-space around the given origin Vector.
    Returns the list of 3D vertices.
    """

    region = context.region
    rv3d = context.region_data
    origin_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, origin)
    radius = min(radius, 25)

    vertices = []
    for i in range(segments + 1):
        angle = i * (2 * math.pi / segments)

        # Add offset in screen-space.
        offset_x = radius * math.cos(angle)
        offset_y = radius * math.sin(angle)
        vert_2d = Vector((origin_2d.x + offset_x, origin_2d.y + offset_y))

        # Convert back to world-space.
        vert_3d = view3d_utils.region_2d_to_location_3d(region, rv3d, vert_2d, origin)
        vertices.append(vert_3d)

    return vertices
