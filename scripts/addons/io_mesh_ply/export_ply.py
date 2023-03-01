# SPDX-License-Identifier: GPL-2.0-or-later

"""
This script exports Stanford PLY files from Blender. It supports normals,
colors, and texture coordinates per face or per vertex.
"""

import bpy


def _write_binary(fw, ply_verts: list, ply_faces: list) -> None:
    from struct import pack

    # Vertex data
    # ---------------------------

    for v, normal, uv, color in ply_verts:
        fw(pack("<3f", *v.co))
        if normal is not None:
            fw(pack("<3f", *normal))
        if uv is not None:
            fw(pack("<2f", *uv))
        if color is not None:
            fw(pack("<4B", *color))

    # Face data
    # ---------------------------

    for pf in ply_faces:
        length = len(pf)
        fw(pack(f"<B{length}I", length, *pf))


def _write_ascii(fw, ply_verts: list, ply_faces: list) -> None:

    # Vertex data
    # ---------------------------

    for v, normal, uv, color in ply_verts:
        fw(b"%.6f %.6f %.6f" % v.co[:])
        if normal is not None:
            fw(b" %.6f %.6f %.6f" % normal[:])
        if uv is not None:
            fw(b" %.6f %.6f" % uv)
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


def save_mesh(filepath, bm, use_ascii, use_normals, use_uv, use_color):
    uv_lay = bm.loops.layers.uv.active
    col_lay = bm.loops.layers.color.active

    use_uv = use_uv and uv_lay is not None
    use_color = use_color and col_lay is not None
    normal = uv = color = None

    ply_faces = []
    ply_verts = []
    ply_vert_map = {}
    ply_vert_id = 0

    for f in bm.faces:
        pf = []
        ply_faces.append(pf)

        for loop in f.loops:
            v = map_id = loop.vert

            if use_uv:
                uv = loop[uv_lay].uv[:]
                map_id = v, uv

            # Identify vertex by pointer unless exporting UVs,
            # in which case id by UV coordinate (will split edges by seams).
            if (_id := ply_vert_map.get(map_id)) is not None:
                pf.append(_id)
                continue

            if use_normals:
                normal = v.normal
            if use_color:
                color = tuple(int(x * 255.0) for x in loop[col_lay])

            ply_verts.append((v, normal, uv, color))
            ply_vert_map[map_id] = ply_vert_id
            pf.append(ply_vert_id)
            ply_vert_id += 1

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
        if use_uv:
            fw(
                b"property float s\n"
                b"property float t\n"
            )
        if use_color:
            fw(
                b"property uchar red\n"
                b"property uchar green\n"
                b"property uchar blue\n"
                b"property uchar alpha\n"
            )

        fw(b"element face %d\n" % len(ply_faces))
        fw(b"property list uchar uint vertex_indices\n")
        fw(b"end_header\n")

        # Geometry
        # ---------------------------

        if use_ascii:
            _write_ascii(fw, ply_verts, ply_faces)
        else:
            _write_binary(fw, ply_verts, ply_faces)


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

    # Workaround for hardcoded unsigned char limit in other DCCs PLY importers
    if (ngons := [f for f in bm.faces if len(f.verts) > 255]):
        bmesh.ops.triangulate(bm, faces=ngons)

    if global_matrix is not None:
        bm.transform(global_matrix)

    if use_normals:
        bm.normal_update()

    save_mesh(
        filepath,
        bm,
        use_ascii,
        use_normals,
        use_uv_coords,
        use_colors,
    )

    bm.free()

    t_delta = time.time() - t
    print(f"Export completed {filepath!r} in {t_delta:.3f}")
