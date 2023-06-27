# SPDX-FileCopyrightText: 2010-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later


def create_and_link_mesh(name, faces, face_nors, points, global_matrix):
    """
    Create a blender mesh and object called name from a list of
    *points* and *faces* and link it in the current scene.
    """

    import array
    from itertools import chain
    import bpy

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(points, [], faces)

    if face_nors:
        # Note: we store 'temp' normals in loops, since validate() may alter final mesh,
        #       we can only set custom lnors *after* calling it.
        mesh.create_normals_split()
        lnors = tuple(chain(*chain(*zip(face_nors, face_nors, face_nors))))
        mesh.loops.foreach_set("normal", lnors)

    mesh.transform(global_matrix)

    # update mesh to allow proper display
    mesh.validate(clean_customdata=False)  # *Very* important to not remove lnors here!

    if face_nors:
        clnors = array.array('f', [0.0] * (len(mesh.loops) * 3))
        mesh.loops.foreach_get("normal", clnors)

        mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))

        mesh.normals_split_custom_set(tuple(zip(*(iter(clnors),) * 3)))
        mesh.use_auto_smooth = True
        mesh.free_normals_split()

    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)


def faces_from_mesh(ob, global_matrix, use_mesh_modifiers=False):
    """
    From an object, return a generator over a list of faces.

    Each faces is a list of his vertices. Each vertex is a tuple of
    his coordinate.

    use_mesh_modifiers
        Apply the preview modifier to the returned liste

    triangulate
        Split the quad into two triangles
    """

    import bpy

    # get the editmode data
    if ob.mode == "EDIT":
        ob.update_from_editmode()

    # get the modifiers
    if use_mesh_modifiers:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        mesh_owner = ob.evaluated_get(depsgraph)
    else:
        mesh_owner = ob

    # Object.to_mesh() is not guaranteed to return a mesh.
    try:
        mesh = mesh_owner.to_mesh()
    except RuntimeError:
        return

    if mesh is None:
        return

    mat = global_matrix @ ob.matrix_world
    mesh.transform(mat)
    if mat.is_negative:
        mesh.flip_normals()
    mesh.calc_loop_triangles()

    vertices = mesh.vertices

    for tri in mesh.loop_triangles:
        yield [vertices[index].co.copy() for index in tri.vertices]

    mesh_owner.to_mesh_clear()
