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

# <pep8-80 compliant>

"""
This script exports Stanford PLY files from Blender. It supports normals,
colors, and texture coordinates per face or per vertex.
"""


def _write_binary(fw, ply_verts, ply_faces, mesh_verts):
    from struct import pack

    # Vertex data
    # ---------------------------

    for index, normal, uv_coords, color in ply_verts:
        fw(pack("<3f", *mesh_verts[index].co))
        if normal is not None:
            fw(pack("<3f", *normal))
        if uv_coords is not None:
            fw(pack("<2f", *uv_coords))
        if color is not None:
            fw(pack("<4B", *color))

    # Face data
    # ---------------------------

    for pf in ply_faces:
        length = len(pf)
        fw(pack("<B%dI" % length, length, *pf))


def _write_ascii(fw, ply_verts, ply_faces, mesh_verts):

    # Vertex data
    # ---------------------------

    for index, normal, uv_coords, color in ply_verts:
        fw(b"%.6f %.6f %.6f" % mesh_verts[index].co[:])
        if normal is not None:
            fw(b" %.6f %.6f %.6f" % normal)
        if uv_coords is not None:
            fw(b" %.6f %.6f" % uv_coords)
        if color is not None:
            fw(b" %u %u %u %u" % color)
        fw(b"\n")

    # Face data
    # ---------------------------

    for pf in ply_faces:
        fw(b"%d" % len(pf))
        for index in pf:
            fw(b" %d" % index)
        fw(b"\n")


def save_mesh(filepath, mesh, use_ascii, use_normals, use_uv_coords, use_colors):
    import bpy

    def rvec3d(v):
        return round(v[0], 6), round(v[1], 6), round(v[2], 6)

    def rvec2d(v):
        return round(v[0], 6), round(v[1], 6)

    if use_uv_coords and mesh.uv_layers:
        active_uv_layer = mesh.uv_layers.active.data
    else:
        use_uv_coords = False

    if use_colors and mesh.vertex_colors:
        active_col_layer = mesh.vertex_colors.active.data
    else:
        use_colors = False

    # in case
    color = uvcoord = uvcoord_key = normal = normal_key = None

    mesh_verts = mesh.vertices
    # vdict = {} # (index, normal, uv) -> new index
    vdict = [{} for i in range(len(mesh_verts))]
    ply_verts = []
    ply_faces = [[] for f in range(len(mesh.polygons))]
    vert_count = 0

    for i, f in enumerate(mesh.polygons):

        if use_normals:
            smooth = f.use_smooth
            if not smooth:
                normal = f.normal[:]
                normal_key = rvec3d(normal)

        if use_uv_coords:
            uv = [
                active_uv_layer[l].uv[:]
                for l in range(f.loop_start, f.loop_start + f.loop_total)
            ]
        if use_colors:
            col = [
                active_col_layer[l].color[:]
                for l in range(f.loop_start, f.loop_start + f.loop_total)
            ]

        pf = ply_faces[i]
        for j, vidx in enumerate(f.vertices):
            v = mesh_verts[vidx]

            if use_normals and smooth:
                normal = v.normal[:]
                normal_key = rvec3d(normal)

            if use_uv_coords:
                uvcoord = uv[j][0], uv[j][1]
                uvcoord_key = rvec2d(uvcoord)

            if use_colors:
                color = col[j]
                color = (
                    int(color[0] * 255.0),
                    int(color[1] * 255.0),
                    int(color[2] * 255.0),
                    int(color[3] * 255.0),
                )
            key = normal_key, uvcoord_key, color

            vdict_local = vdict[vidx]
            pf_vidx = vdict_local.get(key)  # Will be None initially

            if pf_vidx is None:  # Same as vdict_local.has_key(key)
                pf_vidx = vdict_local[key] = vert_count
                ply_verts.append((vidx, normal, uvcoord, color))
                vert_count += 1

            pf.append(pf_vidx)

    with open(filepath, "wb") as file:
        fw = file.write
        file_format = b"ascii" if use_ascii else b"binary_little_endian"

        # Header
        # ---------------------------

        fw(b"ply\n")
        fw(b"format %s 1.0\n" % file_format)
        fw(b"comment Created by Blender %s - www.blender.org\n" % bpy.app.version_string.encode("utf-8"))

        fw(b"element vertex %d\n" % len(ply_verts))
        fw(
            b"property float x\n"
            b"property float y\n"
            b"property float z\n"
        )
        if use_normals:
            fw(
                b"property float nx\n"
                b"property float ny\n"
                b"property float nz\n"
            )
        if use_uv_coords:
            fw(
                b"property float s\n"
                b"property float t\n"
            )
        if use_colors:
            fw(
                b"property uchar red\n"
                b"property uchar green\n"
                b"property uchar blue\n"
                b"property uchar alpha\n"
            )

        fw(b"element face %d\n" % len(mesh.polygons))
        fw(b"property list uchar uint vertex_indices\n")
        fw(b"end_header\n")

        # Geometry
        # ---------------------------

        if use_ascii:
            _write_ascii(fw, ply_verts, ply_faces, mesh_verts)
        else:
            _write_binary(fw, ply_verts, ply_faces, mesh_verts)


def save(
    context,
    filepath="",
    use_ascii=False,
    use_selection=False,
    use_mesh_modifiers=True,
    use_normals=True,
    use_uv_coords=True,
    use_colors=True,
    global_matrix=None,
):
    import time
    import bpy
    import bmesh

    t = time.time()

    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')

    if use_selection:
        obs = context.selected_objects
    else:
        obs = context.scene.objects

    depsgraph = context.evaluated_depsgraph_get()
    bm = bmesh.new()

    for ob in obs:
        if use_mesh_modifiers:
            ob_eval = ob.evaluated_get(depsgraph)
        else:
            ob_eval = ob

        try:
            me = ob_eval.to_mesh()
        except RuntimeError:
            continue

        me.transform(ob.matrix_world)
        bm.from_mesh(me)
        ob_eval.to_mesh_clear()

    mesh = bpy.data.meshes.new("TMP PLY EXPORT")
    bm.to_mesh(mesh)
    bm.free()

    if global_matrix is not None:
        mesh.transform(global_matrix)

    if use_normals:
        mesh.calc_normals()

    save_mesh(
        filepath,
        mesh,
        use_ascii,
        use_normals,
        use_uv_coords,
        use_colors,
    )

    bpy.data.meshes.remove(mesh)

    t_delta = time.time() - t
    print(f"Export completed {filepath!r} in {t_delta:.3f}")
