# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2013-2022 Campbell Barton
# SPDX-FileCopyrightText: 2016-2026 Mikhail Rachinskiy

import array
import random
from collections.abc import Iterator, MutableSequence
from random import uniform
from typing import Any, NamedTuple

import bmesh
import bpy
import mathutils
from bmesh.types import BMesh, BMFace
from bpy.types import Modifier, Object, Operator
from mathutils import Vector

from . import var


class EnumProp(NamedTuple):
    op: Operator
    prop: str


def clean_float(value: float, precision: int = 0) -> str:
    # Avoid scientific notation and strip trailing zeros: 0.000 -> 0.0

    text = f"{value:.{precision}f}"
    index = text.rfind(".")

    if index != -1:
        index += 2
        head, tail = text[:index], text[index:]
        tail = tail.rstrip("0")
        text = head + tail

    return text


# Mesh
# -------------------------------------


def bmesh_copy_from_object(obj: Object, transform=True, triangulate=True, apply_modifiers=False) -> BMesh:
    """Returns a transformed, triangulated copy of the mesh"""

    if (apply_modifiers and obj.modifiers) or obj.type != "MESH":
        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj_eval = obj.evaluated_get(depsgraph)
        me = obj_eval.to_mesh()
        bm = bmesh.new()
        bm.from_mesh(me)
        obj_eval.to_mesh_clear()
    else:
        me = obj.data
        if obj.mode == "EDIT":
            bm_orig = bmesh.from_edit_mesh(me)
            bm = bm_orig.copy()
        else:
            bm = bmesh.new()
            bm.from_mesh(me)

    # TODO. remove all customdata layers.
    # would save ram

    if transform:
        mat = obj.matrix_world.copy()
        # Avoid floating-point error when object is far away from scene center
        mat.translation.zero()
        if not mat.is_identity:
            bm.transform(mat)
            # Update normals if matrix has no rotation.
            bm.normal_update()

    if triangulate:
        bmesh.ops.triangulate(bm, faces=bm.faces)

    return bm


def bmesh_from_object(obj: Object) -> BMesh:
    """Object/Edit Mode get mesh, use bmesh_to_object() to write back."""
    me = obj.data

    if obj.mode == "EDIT":
        bm = bmesh.from_edit_mesh(me)
    else:
        bm = bmesh.new()
        bm.from_mesh(me)

    return bm


def bmesh_to_object(obj: Object, bm: BMesh) -> None:
    """Object/Edit Mode update the object."""
    me = obj.data

    if obj.mode == "EDIT":
        bmesh.update_edit_mesh(me, loop_triangles=True)
    else:
        bm.to_mesh(me)
        me.update()


def bmesh_calc_area(bm: BMesh) -> float:
    """Calculate the surface area."""
    return sum(f.calc_area() for f in bm.faces)


def bmesh_check_self_intersect_object(obj: Object) -> MutableSequence[int]:
    """Check if any faces self intersect returns an array of edge index values."""

    if not obj.data.polygons:
        return array.array("i", ())

    bm = bmesh_copy_from_object(obj, transform=False, triangulate=False)
    tree = mathutils.bvhtree.BVHTree.FromBMesh(bm, epsilon=0.00001)
    overlap = tree.overlap(tree)
    faces_error = {i for i_pair in overlap for i in i_pair}

    return array.array("i", faces_error)


def _bmesh_face_points_random(f: BMFace, num_points=1, margin=0.05) -> Iterator[Vector]:
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


def bmesh_check_thick_object(obj: Object, thickness: float) -> MutableSequence[int]:
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
        for p in _bmesh_face_points_random(f, num_points=6):
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

    return array.array("i", faces_error)


def face_is_distorted(face: BMFace, angle: float) -> bool:
    face_no = face.normal
    get_angle = face_no.angle

    for loop in face.loops:
        loop_no = loop.calc_normal()

        if loop_no.dot(face_no) < 0.0:
            loop_no.negate()

        # For some reason Split Non-Planar Faces operator calculates 2x angle
        if (get_angle(loop_no, 1000.0) * 2.0) > angle:
            return True

    return False


# Asset
# -------------------------------------


def gn_setup(ng_name: str, ob: Object) -> Modifier:
    if (ng := bpy.data.node_groups.get(ng_name)) is None:
        with bpy.data.libraries.load(str(var.NODEGROUPS_FILE)) as (data_from, data_to):
            data_to.node_groups = [ng_name]
        ng = data_to.node_groups[0]

    md = ob.modifiers.new(ng_name, "NODES")
    md.node_group = ng
    md.show_group_selector = False
    if hasattr(md, "show_manage_panel"):
        # VER >= 5.0
        md.show_manage_panel = False

    return md


def md_input_set(md: Modifier, id: str, value: Any, enum_prop: EnumProp = ()) -> None:
    if hasattr(md, "properties"):  # VER >= 5.2
        getattr(md.properties.inputs, id).value = value
    else:
        if enum_prop:
            enum_items = [x[1] for x in enum_prop.op.__class__.__annotations__[enum_prop.prop].keywords["items"]]
            md[id] = enum_items.index(value)
        else:
            md[id] = value


def md_panel_set(md: Modifier, id: int, value: bool) -> None:
    if hasattr(md, "properties"):  # VER >= 5.2
        setattr(md.properties.panels, f"open_{id}", value)
    else:
        md.panels[id].is_open = value


def md_get_panels(md: Modifier) -> dict[str, int]:
    if hasattr(md, "properties"):  # VER >= 5.2
        return {
            p.name: p.identifier
            for p in md.node_group.interface.items_tree
            if p.item_type == "PANEL"
        }

    return {
        p.name: i
        for i, p in enumerate(
            p for p in md.node_group.interface.items_tree
            if p.item_type == "PANEL"
        )
    }
