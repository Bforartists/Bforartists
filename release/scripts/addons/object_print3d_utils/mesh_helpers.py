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

# Generic helper functions, to be used by any modules.


import bmesh


def bmesh_copy_from_object(obj, transform=True, triangulate=True, apply_modifiers=False):
    """Returns a transformed, triangulated copy of the mesh"""

    assert obj.type == 'MESH'

    if apply_modifiers and obj.modifiers:
        import bpy
        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj_eval = obj.evaluated_get(depsgraph)
        me = obj_eval.to_mesh()
        bm = bmesh.new()
        bm.from_mesh(me)
        obj_eval.to_mesh_clear()
    else:
        me = obj.data
        if obj.mode == 'EDIT':
            bm_orig = bmesh.from_edit_mesh(me)
            bm = bm_orig.copy()
        else:
            bm = bmesh.new()
            bm.from_mesh(me)

    # TODO. remove all customdata layers.
    # would save ram

    if transform:
        bm.transform(obj.matrix_world)

    if triangulate:
        bmesh.ops.triangulate(bm, faces=bm.faces)

    return bm


def bmesh_from_object(obj):
    """Object/Edit Mode get mesh, use bmesh_to_object() to write back."""
    me = obj.data

    if obj.mode == 'EDIT':
        bm = bmesh.from_edit_mesh(me)
    else:
        bm = bmesh.new()
        bm.from_mesh(me)

    return bm


def bmesh_to_object(obj, bm):
    """Object/Edit Mode update the object."""
    me = obj.data

    if obj.mode == 'EDIT':
        bmesh.update_edit_mesh(me, True)
    else:
        bm.to_mesh(me)
        me.update()


def bmesh_calc_area(bm):
    """Calculate the surface area."""
    return sum(f.calc_area() for f in bm.faces)


def bmesh_check_self_intersect_object(obj):
    """Check if any faces self intersect returns an array of edge index values."""
    import array
    import mathutils

    if not obj.data.polygons:
        return array.array('i', ())

    bm = bmesh_copy_from_object(obj, transform=False, triangulate=False)
    tree = mathutils.bvhtree.BVHTree.FromBMesh(bm, epsilon=0.00001)
    overlap = tree.overlap(tree)
    faces_error = {i for i_pair in overlap for i in i_pair}

    return array.array('i', faces_error)


def bmesh_face_points_random(f, num_points=1, margin=0.05):
    import random
    from random import uniform

    # for pradictable results
    random.seed(f.index)

    uniform_args = 0.0 + margin, 1.0 - margin
    vecs = [v.co for v in f.verts]

    for _ in range(num_points):
        u1 = uniform(*uniform_args)
        u2 = uniform(*uniform_args)
        u_tot = u1 + u2

        if u_tot > 1.0:
            u1 = 1.0 - u1
            u2 = 1.0 - u2

        side1 = vecs[1] - vecs[0]
        side2 = vecs[2] - vecs[0]

        yield vecs[0] + u1 * side1 + u2 * side2


def bmesh_check_thick_object(obj, thickness):
    import array
    import bpy

    # Triangulate
    bm = bmesh_copy_from_object(obj, transform=True, triangulate=False)

    # map original faces to their index.
    face_index_map_org = {f: i for i, f in enumerate(bm.faces)}
    ret = bmesh.ops.triangulate(bm, faces=bm.faces)
    face_map = ret["face_map"]
    del ret
    # old edge -> new mapping

    # Convert new/old map to index dict.

    # Create a real mesh (lame!)
    context = bpy.context
    layer = context.view_layer
    scene_collection = context.layer_collection.collection

    me_tmp = bpy.data.meshes.new(name="~temp~")
    bm.to_mesh(me_tmp)
    obj_tmp = bpy.data.objects.new(name=me_tmp.name, object_data=me_tmp)
    scene_collection.objects.link(obj_tmp)

    layer.update()
    ray_cast = obj_tmp.ray_cast

    EPS_BIAS = 0.0001

    faces_error = set()
    bm_faces_new = bm.faces[:]

    for f in bm_faces_new:
        no = f.normal
        no_sta = no * EPS_BIAS
        no_end = no * thickness
        for p in bmesh_face_points_random(f, num_points=6):
            # Cast the ray backwards
            p_a = p - no_sta
            p_b = p - no_end
            p_dir = p_b - p_a

            ok, _co, no, index = ray_cast(p_a, p_dir, distance=p_dir.length)

            if ok:
                # Add the face we hit
                for f_iter in (f, bm_faces_new[index]):
                    # if the face wasn't triangulated, just use existing
                    f_org = face_map.get(f_iter, f_iter)
                    f_org_index = face_index_map_org[f_org]
                    faces_error.add(f_org_index)

    bm.free()

    scene_collection.objects.unlink(obj_tmp)
    bpy.data.objects.remove(obj_tmp)
    bpy.data.meshes.remove(me_tmp)

    layer.update()

    return array.array('i', faces_error)


def face_is_distorted(ele, angle_distort):
    no = ele.normal
    angle_fn = no.angle

    for loop in ele.loops:
        loopno = loop.calc_normal()

        if loopno.dot(no) < 0.0:
            loopno.negate()

        if angle_fn(loopno, 1000.0) > angle_distort:
            return True

    return False
