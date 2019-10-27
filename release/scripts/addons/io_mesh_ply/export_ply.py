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


def save_mesh(filepath, mesh, use_normals=True, use_uv_coords=True, use_colors=True):
    import os
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

        smooth = not use_normals or f.use_smooth
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

            if smooth:
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

    with open(filepath, "w", encoding="utf-8", newline="\n") as file:
        fw = file.write

        # Header
        # ---------------------------

        fw("ply\n")
        fw("format ascii 1.0\n")
        fw(
            f"comment Created by Blender {bpy.app.version_string} - "
            f"www.blender.org, source file: {os.path.basename(bpy.data.filepath)!r}\n"
        )

        fw(f"element vertex {len(ply_verts)}\n")
        fw(
            "property float x\n"
            "property float y\n"
            "property float z\n"
        )
        if use_normals:
            fw(
                "property float nx\n"
                "property float ny\n"
                "property float nz\n"
            )
        if use_uv_coords:
            fw(
                "property float s\n"
                "property float t\n"
            )
        if use_colors:
            fw(
                "property uchar red\n"
                "property uchar green\n"
                "property uchar blue\n"
                "property uchar alpha\n"
            )

        fw(f"element face {len(mesh.polygons)}\n")
        fw("property list uchar uint vertex_indices\n")

        fw("end_header\n")

        # Vertex data
        # ---------------------------

        for i, v in enumerate(ply_verts):
            fw("%.6f %.6f %.6f" % mesh_verts[v[0]].co[:])
            if use_normals:
                fw(" %.6f %.6f %.6f" % v[1])
            if use_uv_coords:
                fw(" %.6f %.6f" % v[2])
            if use_colors:
                fw(" %u %u %u %u" % v[3])
            fw("\n")

        # Face data
        # ---------------------------

        for pf in ply_faces:
            fw(f"{len(pf)}")
            for v in pf:
                fw(f" {v}")
            fw("\n")

        print(f"Writing {filepath!r} done")

    return {'FINISHED'}


def save(
    operator,
    context,
    filepath="",
    use_selection=False,
    use_mesh_modifiers=True,
    use_normals=True,
    use_uv_coords=True,
    use_colors=True,
    global_matrix=None
):
    import bpy
    import bmesh

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

    ret = save_mesh(
        filepath,
        mesh,
        use_normals=use_normals,
        use_uv_coords=use_uv_coords,
        use_colors=use_colors,
    )

    bpy.data.meshes.remove(mesh)

    return ret
