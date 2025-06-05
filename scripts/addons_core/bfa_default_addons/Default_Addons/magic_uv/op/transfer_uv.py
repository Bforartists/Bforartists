# SPDX-FileCopyrightText: 2017-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Nutti <nutti.metro@gmail.com>, Mifth, MaxRobinot"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"

from collections import OrderedDict

import bpy
import bmesh
from bpy.props import BoolProperty

from .. import common
from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry
from ..utils import compatibility as compat


def _is_valid_context(context):
    # only 'VIEW_3D' space is allowed to execute
    if not common.is_valid_space(context, ['VIEW_3D']):
        return False

    # Multiple objects editing mode is not supported in this feature.
    objs = common.get_uv_editable_objects(context)
    if len(objs) != 1:
        return False

    # only edit mode is allowed to execute
    if context.object.mode != 'EDIT':
        return False

    return True


def _get_uv_layer(ops_obj, bm):
    # get UV layer
    if not bm.loops.layers.uv:
        ops_obj.report({'WARNING'}, "Object must have more than one UV map")
        return None
    uv_layer = bm.loops.layers.uv.verify()

    return uv_layer


def _main_parse(ops_obj, uv_layer, sel_faces, active_face, active_face_nor):
    all_sorted_faces = OrderedDict()  # This is the main stuff

    used_verts = set()
    used_edges = set()

    faces_to_parse = []

    # get shared edge of two faces
    cross_edges = []
    for edge in active_face.edges:
        if edge in sel_faces[0].edges and edge in sel_faces[1].edges:
            cross_edges.append(edge)

    # parse two selected faces
    if cross_edges and len(cross_edges) == 1:
        shared_edge = cross_edges[0]
        vert1 = None
        vert2 = None

        dot_n = active_face_nor.normalized()
        edge_vec_1 = (shared_edge.verts[1].co - shared_edge.verts[0].co)
        edge_vec_len = edge_vec_1.length
        edge_vec_1 = edge_vec_1.normalized()

        af_center = active_face.calc_center_median()
        af_vec = shared_edge.verts[0].co + (edge_vec_1 * (edge_vec_len * 0.5))
        af_vec = (af_vec - af_center).normalized()

        if af_vec.cross(edge_vec_1).dot(dot_n) > 0:
            vert1 = shared_edge.verts[0]
            vert2 = shared_edge.verts[1]
        else:
            vert1 = shared_edge.verts[1]
            vert2 = shared_edge.verts[0]

        # get active face stuff and uvs
        face_stuff = _get_other_verts_edges(
            active_face, vert1, vert2, shared_edge, uv_layer)
        all_sorted_faces[active_face] = face_stuff
        used_verts.update(active_face.verts)
        used_edges.update(active_face.edges)

        # get first selected face stuff and uvs as they share shared_edge
        second_face = sel_faces[0]
        if second_face is active_face:
            second_face = sel_faces[1]
        face_stuff = _get_other_verts_edges(
            second_face, vert1, vert2, shared_edge, uv_layer)
        all_sorted_faces[second_face] = face_stuff
        used_verts.update(second_face.verts)
        used_edges.update(second_face.edges)

        # first Grow
        faces_to_parse.append(active_face)
        faces_to_parse.append(second_face)

    else:
        ops_obj.report({'WARNING'}, "Two faces should share one edge")
        return None

    # parse all faces
    while True:
        new_parsed_faces = []
        if not faces_to_parse:
            break
        for face in faces_to_parse:
            face_stuff = all_sorted_faces.get(face)
            new_faces = _parse_faces(face, face_stuff, used_verts, used_edges,
                                     all_sorted_faces, uv_layer)
            if new_faces is None:
                ops_obj.report({'WARNING'}, "More than 2 faces share edge")
                return None

            new_parsed_faces += new_faces
        faces_to_parse = new_parsed_faces

    return all_sorted_faces


def _parse_faces(check_face, face_stuff, used_verts, used_edges,
                 all_sorted_faces, uv_layer):
    """recurse faces around the new_grow only"""

    new_shared_faces = []
    for sorted_edge in face_stuff[1]:
        shared_faces = sorted_edge.link_faces
        if shared_faces:
            if len(shared_faces) > 2:
                bpy.ops.mesh.select_all(action='DESELECT')
                for face_sel in shared_faces:
                    face_sel.select = True
                shared_faces = []
                return None

            clear_shared_faces = _get_new_shared_faces(
                check_face, sorted_edge, shared_faces, all_sorted_faces.keys())
            if clear_shared_faces:
                shared_face = clear_shared_faces[0]
                # get vertices of the edge
                vert1 = sorted_edge.verts[0]
                vert2 = sorted_edge.verts[1]

                common.debug_print(face_stuff[0], vert1, vert2)
                if face_stuff[0].index(vert1) > face_stuff[0].index(vert2):
                    vert1 = sorted_edge.verts[1]
                    vert2 = sorted_edge.verts[0]

                common.debug_print(shared_face.verts, vert1, vert2)
                new_face_stuff = _get_other_verts_edges(
                    shared_face, vert1, vert2, sorted_edge, uv_layer)
                all_sorted_faces[shared_face] = new_face_stuff
                used_verts.update(shared_face.verts)
                used_edges.update(shared_face.edges)

                if common.is_debug_mode():
                    shared_face.select = True  # test which faces are parsed

                new_shared_faces.append(shared_face)

    return new_shared_faces


def _get_new_shared_faces(orig_face, shared_edge, check_faces, used_faces):
    shared_faces = []

    for face in check_faces:
        is_shared_edge = shared_edge in face.edges
        not_used = face not in used_faces
        not_orig = face is not orig_face
        not_hide = face.hide is False
        if is_shared_edge and not_used and not_orig and not_hide:
            shared_faces.append(face)

    return shared_faces


def _get_other_verts_edges(face, vert1, vert2, first_edge, uv_layer):
    face_edges = [first_edge]
    face_verts = [vert1, vert2]
    face_loops = []

    other_edges = [edge for edge in face.edges if edge not in face_edges]

    for _ in range(len(other_edges)):
        found_edge = None
        # get sorted verts and edges
        for edge in other_edges:
            if face_verts[-1] in edge.verts:
                other_vert = edge.other_vert(face_verts[-1])

                if other_vert not in face_verts:
                    face_verts.append(other_vert)

                found_edge = edge
                if found_edge not in face_edges:
                    face_edges.append(edge)
                break

        other_edges.remove(found_edge)

    # get sorted uvs
    for vert in face_verts:
        for loop in face.loops:
            if loop.vert is vert:
                face_loops.append(loop[uv_layer])
                break

    return [face_verts, face_edges, face_loops]


def _get_selected_src_faces(ops_obj, bm, uv_layer):
    topology_copied = []

    # get selected faces
    active_face = bm.faces.active
    sel_faces = [face for face in bm.faces if face.select]
    if len(sel_faces) != 2:
        ops_obj.report({'WARNING'}, "Two faces must be selected")
        return None
    if not active_face or active_face not in sel_faces:
        ops_obj.report({'WARNING'}, "Two faces must be active")
        return None

    # parse all faces according to selection
    active_face_nor = active_face.normal.copy()
    all_sorted_faces = _main_parse(ops_obj, uv_layer, sel_faces, active_face,
                                   active_face_nor)

    if all_sorted_faces:
        for face_data in all_sorted_faces.values():
            edges = face_data[1]
            uv_loops = face_data[2]
            uvs = [l.uv.copy() for l in uv_loops]
            pin_uvs = [l.pin_uv for l in uv_loops]
            seams = [e.seam for e in edges]
            topology_copied.append([uvs, pin_uvs, seams])
    else:
        return None

    return topology_copied


def _paste_uv(ops_obj, bm, uv_layer, src_faces, invert_normals, copy_seams):
    # get selection history
    all_sel_faces = [e for e in bm.select_history
                     if isinstance(e, bmesh.types.BMFace) and e.select]
    if len(all_sel_faces) % 2 != 0:
        ops_obj.report({'WARNING'}, "Two faces must be selected")
        return -1

    # parse selection history
    for i, _ in enumerate(all_sel_faces):
        if (i == 0) or (i % 2 == 0):
            continue
        sel_faces = [all_sel_faces[i - 1], all_sel_faces[i]]
        active_face = all_sel_faces[i]

        # parse all faces according to selection history
        active_face_nor = active_face.normal.copy()
        if invert_normals:
            active_face_nor.negate()
        all_sorted_faces = _main_parse(ops_obj, uv_layer, sel_faces,
                                       active_face, active_face_nor)

        if all_sorted_faces:
            # check amount of copied/pasted faces
            if len(all_sorted_faces) != len(src_faces):
                ops_obj.report({'WARNING'},
                               "Mesh has different amount of faces")
                return -1

            for j, face_data in enumerate(all_sorted_faces.values()):
                copied_data = src_faces[j]

                # check amount of copied/pasted verts
                if len(copied_data[0]) != len(face_data[2]):
                    bpy.ops.mesh.select_all(action='DESELECT')
                    # select problematic face
                    list(all_sorted_faces.keys())[j].select = True
                    ops_obj.report({'WARNING'},
                                   "Face have different amount of vertices")
                    return 0

                for k, (edge, uvloop) in enumerate(zip(face_data[1],
                                                       face_data[2])):
                    uvloop.uv = copied_data[0][k]
                    uvloop.pin_uv = copied_data[1][k]
                    if copy_seams:
                        edge.seam = copied_data[2][k]
        else:
            return -1

    return 0


@PropertyClassRegistry()
class _Properties:
    idname = "transfer_uv"

    @classmethod
    def init_props(cls, scene):
        class Props():
            topology_copied = None

        scene.muv_props.transfer_uv = Props()

        scene.muv_transfer_uv_enabled = BoolProperty(
            name="Transfer UV Enabled",
            description="Transfer UV is enabled",
            default=False
        )
        scene.muv_transfer_uv_invert_normals = BoolProperty(
            name="Invert Normals",
            description="Invert Normals",
            default=False
        )
        scene.muv_transfer_uv_copy_seams = BoolProperty(
            name="Copy Seams",
            description="Copy Seams",
            default=True
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_transfer_uv_enabled
        del scene.muv_transfer_uv_invert_normals
        del scene.muv_transfer_uv_copy_seams


@BlClassRegistry()
class MUV_OT_TransferUV_CopyUV(bpy.types.Operator):
    """
        Operation class: Transfer UV copy
        Topological based copy
    """

    bl_idname = "uv.muv_transfer_uv_copy_uv"
    bl_label = "Transfer UV Copy UV"
    bl_description = "Transfer UV Copy UV (Topological based copy)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    def execute(self, context):
        props = context.scene.muv_props.transfer_uv

        objs = common.get_uv_editable_objects(context)
        # poll() method ensures that only one object is selected.
        obj = objs[0]
        bm = bmesh.from_edit_mesh(obj.data)
        if compat.check_version(2, 73, 0) >= 0:
            bm.faces.ensure_lookup_table()

        uv_layer = _get_uv_layer(self, bm)
        if uv_layer is None:
            return {'CANCELLED'}

        faces = _get_selected_src_faces(self, bm, uv_layer)
        if faces is None:
            return {'CANCELLED'}
        props.topology_copied = faces

        bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_TransferUV_PasteUV(bpy.types.Operator):
    """
        Operation class: Transfer UV paste
        Topological based paste
    """

    bl_idname = "uv.muv_transfer_uv_paste_uv"
    bl_label = "Transfer UV Paste UV"
    bl_description = "Transfer UV Paste UV (Topological based paste)"
    bl_options = {'REGISTER', 'UNDO'}

    invert_normals = BoolProperty(
        name="Invert Normals",
        description="Invert Normals",
        default=False
    )
    copy_seams = BoolProperty(
        name="Copy Seams",
        description="Copy Seams",
        default=True
    )

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        sc = context.scene
        props = sc.muv_props.transfer_uv
        if not props.topology_copied:
            return False
        return _is_valid_context(context)

    def execute(self, context):
        props = context.scene.muv_props.transfer_uv

        objs = common.get_uv_editable_objects(context)
        # poll() method ensures that only one object is selected.
        obj = objs[0]
        bm = bmesh.from_edit_mesh(obj.data)
        if compat.check_version(2, 73, 0) >= 0:
            bm.faces.ensure_lookup_table()

        # get UV layer
        uv_layer = _get_uv_layer(self, bm)
        if uv_layer is None:
            return {'CANCELLED'}

        ret = _paste_uv(self, bm, uv_layer, props.topology_copied,
                        self.invert_normals, self.copy_seams)
        if ret:
            return {'CANCELLED'}

        bmesh.update_edit_mesh(obj.data)

        if compat.check_version(2, 80, 0) < 0:
            if self.copy_seams:
                obj.data.show_edge_seams = True

        return {'FINISHED'}
