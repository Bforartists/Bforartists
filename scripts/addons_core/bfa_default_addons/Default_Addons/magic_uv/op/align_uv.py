# SPDX-FileCopyrightText: 2018-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "imdjs, Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"

import math
from math import atan2, tan, sin, cos

import bpy
from bpy.props import (
    EnumProperty,
    BoolProperty,
    FloatProperty,
    FloatVectorProperty,
)
import bmesh
from mathutils import Vector

from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry
from ..utils import compatibility as compat

from .. import common


def _is_valid_context(context):
    # 'IMAGE_EDITOR' and 'VIEW_3D' space is allowed to execute.
    # If 'View_3D' space is not allowed, you can't find option in Tool-Shelf
    # after the execution
    if not common.is_valid_space(context, ['IMAGE_EDITOR', 'VIEW_3D']):
        return False

    objs = common.get_uv_editable_objects(context)
    if not objs:
        return False

    # only edit mode is allowed to execute
    if context.object.mode != 'EDIT':
        return False

    return True


# get sum vertex length of loop sequences
def _get_loop_vert_len(loops):
    length = 0
    for l1, l2 in zip(loops[:-1], loops[1:]):
        diff = l2.vert.co - l1.vert.co
        length = length + abs(diff.length)

    return length


# get sum uv length of loop sequences
def _get_loop_uv_len(loops, uv_layer):
    length = 0
    for l1, l2 in zip(loops[:-1], loops[1:]):
        diff = l2[uv_layer].uv - l1[uv_layer].uv
        length = length + abs(diff.length)

    return length


# get center/radius of circle by 3 vertices
def _get_circle(v):
    alpha = atan2((v[0].y - v[1].y), (v[0].x - v[1].x)) + math.pi / 2
    beta = atan2((v[1].y - v[2].y), (v[1].x - v[2].x)) + math.pi / 2
    ex = (v[0].x + v[1].x) / 2.0
    ey = (v[0].y + v[1].y) / 2.0
    fx = (v[1].x + v[2].x) / 2.0
    fy = (v[1].y + v[2].y) / 2.0
    cx = (ey - fy - ex * tan(alpha) + fx * tan(beta)) / \
         (tan(beta) - tan(alpha))
    cy = ey - (ex - cx) * tan(alpha)
    center = Vector((cx, cy))

    r = v[0] - center
    radian = r.length

    return center, radian


# get position on circle with same arc length
def _calc_v_on_circle(v, center, radius):
    base = v[0]
    theta = atan2(base.y - center.y, base.x - center.x)
    new_v = []
    for i in range(len(v)):
        angle = theta + i * 2 * math.pi / len(v)
        new_v.append(Vector((center.x + radius * sin(angle),
                             center.y + radius * cos(angle))))

    return new_v


# get accumulate vertex lengths of loop sequences
def _get_loop_vert_accum_len(loops):
    accum_lengths = [0.0]
    length = 0
    for l1, l2 in zip(loops[:-1], loops[1:]):
        diff = l2.vert.co - l1.vert.co
        length = length + abs(diff.length)
        accum_lengths.extend([length])

    return accum_lengths


# get sum uv length of loop sequences
def _get_loop_uv_accum_len(loops, uv_layer):
    accum_lengths = [0.0]
    length = 0
    for l1, l2 in zip(loops[:-1], loops[1:]):
        diff = l2[uv_layer].uv - l1[uv_layer].uv
        length = length + abs(diff.length)
        accum_lengths.extend([length])

    return accum_lengths


# get horizontal differential of UV influenced by mesh vertex
def _get_hdiff_uv_vinfl(uv_layer, loop_seqs, vidx, hidx, pidx, infl):
    common.debug_print(
        "loop_seqs[hidx={0}][vidx={1}][pidx={2}]".format(hidx, vidx, pidx))

    base_uv = loop_seqs[0][vidx][0][uv_layer].uv.copy()

    # calculate original length
    hloops = []
    for s in loop_seqs:
        hloops.extend([s[vidx][0], s[vidx][1]])
    total_vlen = _get_loop_vert_len(hloops)
    accum_vlens = _get_loop_vert_accum_len(hloops)
    total_uvlen = _get_loop_uv_len(hloops, uv_layer)
    accum_uvlens = _get_loop_uv_accum_len(hloops, uv_layer)
    orig_uvs = [l[uv_layer].uv.copy() for l in hloops]

    # calculate target length
    tgt_noinfl = total_uvlen * (hidx + pidx) / len(loop_seqs)
    tgt_infl = total_uvlen * accum_vlens[hidx * 2 + pidx] / total_vlen
    target_length = tgt_noinfl * (1 - infl) + tgt_infl * infl
    common.debug_print(target_length)
    common.debug_print(accum_uvlens)

    # calculate target UV
    for i in range(len(accum_uvlens[:-1])):
        # get line segment which UV will be placed
        if accum_uvlens[i] <= target_length < accum_uvlens[i + 1]:
            tgt_seg_len = target_length - accum_uvlens[i]
            seg_len = accum_uvlens[i + 1] - accum_uvlens[i]
            uv1 = orig_uvs[i]
            uv2 = orig_uvs[i + 1]
            target_uv = (uv1 - base_uv) + (uv2 - uv1) * tgt_seg_len / seg_len
            break
        elif i == (len(accum_uvlens[:-1]) - 1):
            if abs(accum_uvlens[i + 1] - target_length) > 0.000001:
                raise Exception(
                    "Internal Error: horizontal_target_length={}"
                    " is not equal to {}"
                    .format(target_length, accum_uvlens[-1]))
            tgt_seg_len = target_length - accum_uvlens[i]
            seg_len = accum_uvlens[i + 1] - accum_uvlens[i]
            uv1 = orig_uvs[i]
            uv2 = orig_uvs[i + 1]
            target_uv = (uv1 - base_uv) + (uv2 - uv1) * tgt_seg_len / seg_len
            break
    else:
        raise Exception("Internal Error: horizontal_target_length={}"
                        " is not in range {} to {}"
                        .format(target_length, accum_uvlens[0],
                                accum_uvlens[-1]))

    return target_uv


# --------------------- LOOP STRUCTURE ----------------------
#
#  loops[hidx][vidx][pidx]
#     hidx: horizontal index
#     vidx: vertical index
#     pidx: pair index
#
#              <----- horizontal ----->
#
#              (hidx, vidx, pidx) = (0, 3, 0)
#              |      (hidx, vidx, pidx) = (1, 3, 0)
#              v      v
#          ^   o --- oo --- o
#          |   |     ||     |
# vertical |   o --- oo --- o  <- (hidx, vidx, pidx)
#          |   o --- oo --- o          = (1, 2, 1)
#          |   |     ||     |
#          v   o --- oo --- o
#              ^            ^
#              |            (hidx, vidx, pidx) = (1, 0, 1)
#              (hidx, vidx, pidx) = (0, 0, 0)
#
# -----------------------------------------------------------


# get vertical differential of UV influenced by mesh vertex
def _get_vdiff_uv_vinfl(uv_layer, loop_seqs, vidx, hidx, pidx, infl):
    common.debug_print(
        "loop_seqs[hidx={0}][vidx={1}][pidx={2}]".format(hidx, vidx, pidx))

    base_uv = loop_seqs[hidx][0][pidx][uv_layer].uv.copy()

    # calculate original length
    vloops = []
    for s in loop_seqs[hidx]:
        vloops.append(s[pidx])
    total_vlen = _get_loop_vert_len(vloops)
    accum_vlens = _get_loop_vert_accum_len(vloops)
    total_uvlen = _get_loop_uv_len(vloops, uv_layer)
    accum_uvlens = _get_loop_uv_accum_len(vloops, uv_layer)
    orig_uvs = [l[uv_layer].uv.copy() for l in vloops]

    # calculate target length
    tgt_noinfl = total_uvlen * int((vidx + 1) / 2) * 2 / len(loop_seqs[hidx])
    tgt_infl = total_uvlen * accum_vlens[vidx] / total_vlen
    target_length = tgt_noinfl * (1 - infl) + tgt_infl * infl
    common.debug_print(target_length)
    common.debug_print(accum_uvlens)

    # calculate target UV
    for i in range(len(accum_uvlens[:-1])):
        # get line segment which UV will be placed
        if accum_uvlens[i] <= target_length < accum_uvlens[i + 1]:
            tgt_seg_len = target_length - accum_uvlens[i]
            seg_len = accum_uvlens[i + 1] - accum_uvlens[i]
            uv1 = orig_uvs[i]
            uv2 = orig_uvs[i + 1]
            target_uv = (uv1 - base_uv) + (uv2 - uv1) * tgt_seg_len / seg_len
            break
        elif i == (len(accum_uvlens[:-1]) - 1):
            if abs(accum_uvlens[i + 1] - target_length) > 0.000001:
                raise Exception("Internal Error: horizontal_target_length={}"
                                " is not equal to {}"
                                .format(target_length, accum_uvlens[-1]))
            tgt_seg_len = target_length - accum_uvlens[i]
            seg_len = accum_uvlens[i + 1] - accum_uvlens[i]
            uv1 = orig_uvs[i]
            uv2 = orig_uvs[i + 1]
            target_uv = (uv1 - base_uv) + (uv2 - uv1) * tgt_seg_len / seg_len
            break
    else:
        raise Exception("Internal Error: horizontal_target_length={}"
                        " is not in range {} to {}"
                        .format(target_length, accum_uvlens[0],
                                accum_uvlens[-1]))

    return target_uv


# get horizontal differential of UV no influenced
def _get_hdiff_uv(uv_layer, loop_seqs, hidx):
    base_uv = loop_seqs[0][0][0][uv_layer].uv.copy()
    h_uv = loop_seqs[-1][0][1][uv_layer].uv.copy() - base_uv

    return hidx * h_uv / len(loop_seqs)


# get vertical differential of UV no influenced
def _get_vdiff_uv(uv_layer, loop_seqs, vidx, hidx):
    base_uv = loop_seqs[0][0][0][uv_layer].uv.copy()
    v_uv = loop_seqs[0][-1][0][uv_layer].uv.copy() - base_uv

    hseq = loop_seqs[hidx]
    return int((vidx + 1) / 2) * v_uv / (len(hseq) / 2)


@PropertyClassRegistry()
class _Properties:
    idname = "align_uv"

    @classmethod
    def init_props(cls, scene):
        scene.muv_align_uv_enabled = BoolProperty(
            name="Align UV Enabled",
            description="Align UV is enabled",
            default=False
        )
        scene.muv_align_uv_transmission = BoolProperty(
            name="Transmission",
            description="Align linked UVs",
            default=False
        )
        scene.muv_align_uv_select = BoolProperty(
            name="Select",
            description="Select UVs which are aligned",
            default=False
        )
        scene.muv_align_uv_vertical = BoolProperty(
            name="Vert-Infl (Vertical)",
            description="Align vertical direction influenced "
                        "by mesh vertex proportion",
            default=False
        )
        scene.muv_align_uv_horizontal = BoolProperty(
            name="Vert-Infl (Horizontal)",
            description="Align horizontal direction influenced "
                        "by mesh vertex proportion",
            default=False
        )
        scene.muv_align_uv_mesh_infl = FloatProperty(
            name="Mesh Influence",
            description="Influence rate of mesh vertex",
            min=0.0,
            max=1.0,
            default=0.0
        )
        scene.muv_align_uv_location = EnumProperty(
            name="Location",
            description="Align location",
            items=[
                ('LEFT_TOP', "Left/Top", "Align to Left or Top"),
                ('MIDDLE', "Middle", "Align to middle"),
                ('RIGHT_BOTTOM', "Right/Bottom", "Align to Right or Bottom")
            ],
            default='MIDDLE'
        )

        scene.muv_align_uv_snap_method = EnumProperty(
            name="Snap Method",
            description="Snap method",
            items=[
                ('POINT', "Point", "Snap to point"),
                ('EDGE', "Edge", "Snap to edge"),
            ],
            default='POINT'
        )
        scene.muv_align_uv_snap_point_group = EnumProperty(
            name="Snap Group (Point)",
            description="Group that snap (point) operation applies for",
            items=[
                ('VERT', "Vertex", "Vertex"),
                ('FACE', "Face", "Face"),
                ('UV_ISLAND', "UV Island", "UV Island"),
            ],
            default='FACE'
        )
        scene.muv_align_uv_snap_point_target = FloatVectorProperty(
            name="Snap Target (Point)",
            description="Target point where UV vertices snap to",
            size=2,
            precision=4,
            soft_min=-1.0,
            soft_max=1.0,
            step=1,
            default=(0.000, 0.000),
        )
        scene.muv_align_uv_snap_edge_group = EnumProperty(
            name="Snap Group (Edge)",
            description="Group that snap (edge) operation applies for",
            items=[
                ('EDGE', "Edge", "Edge"),
                ('FACE', "Face", "Face"),
                ('UV_ISLAND', "UV Island", "UV Island"),
            ],
            default='FACE'
        )
        scene.muv_align_uv_snap_edge_target_1 = FloatVectorProperty(
            name="Snap Target (Edge)",
            description="Target edge where UV vertices snap to",
            size=2,
            precision=4,
            soft_min=-1.0,
            soft_max=1.0,
            step=1,
            default=(0.000, 0.000),
        )
        scene.muv_align_uv_snap_edge_target_2 = FloatVectorProperty(
            name="Snap Target (Edge)",
            description="Target edge where UV vertices snap to",
            size=2,
            precision=4,
            soft_min=-1.0,
            soft_max=1.0,
            step=1,
            default=(0.000, 0.000),
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_align_uv_enabled
        del scene.muv_align_uv_transmission
        del scene.muv_align_uv_select
        del scene.muv_align_uv_vertical
        del scene.muv_align_uv_horizontal
        del scene.muv_align_uv_mesh_infl
        del scene.muv_align_uv_location
        del scene.muv_align_uv_snap_method
        del scene.muv_align_uv_snap_point_group
        del scene.muv_align_uv_snap_point_target
        del scene.muv_align_uv_snap_edge_group
        del scene.muv_align_uv_snap_edge_target_1
        del scene.muv_align_uv_snap_edge_target_2


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_AlignUV_Circle(bpy.types.Operator):

    bl_idname = "uv.muv_align_uv_circle"
    bl_label = "Align UV (Circle)"
    bl_description = "Align UV coordinates to Circle"
    bl_options = {'REGISTER', 'UNDO'}

    transmission = BoolProperty(
        name="Transmission",
        description="Align linked UVs",
        default=False
    )
    select = BoolProperty(
        name="Select",
        description="Select UVs which are aligned",
        default=False
    )

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    def execute(self, context):
        objs = common.get_uv_editable_objects(context)

        for obj in objs:
            bm = bmesh.from_edit_mesh(obj.data)
            if common.check_version(2, 73, 0) >= 0:
                bm.faces.ensure_lookup_table()
            uv_layer = bm.loops.layers.uv.verify()

            # loop_seqs[horizontal][vertical][loop]
            loop_seqs, error = common.get_loop_sequences(bm, uv_layer, True)
            if not loop_seqs:
                self.report({'WARNING'},
                            "Object {}: {}".format(obj.name, error))
                return {'CANCELLED'}

            # get circle and new UVs
            uvs = [hseq[0][0][uv_layer].uv.copy() for hseq in loop_seqs]
            c, r = _get_circle(uvs[0:3])
            new_uvs = _calc_v_on_circle(uvs, c, r)

            # check if center is identical
            center_is_identical = False
            center = loop_seqs[0][-1][0].vert
            if (len(loop_seqs[0][-1]) == 1) and \
                    loop_seqs[0][-1][0].vert == center:
                center_is_identical = True

            # check if topology is correct
            if center_is_identical:
                for hseq in loop_seqs[1:]:
                    if len(hseq[-1]) != 1:
                        self.report({'WARNING'},
                                    "Object {}: Last face must be triangle"
                                    .format(obj.name))
                        return {'CANCELLED'}
                    if hseq[-1][0].vert != center:
                        self.report({'WARNING'},
                                    "Object {}: Center must be identical"
                                    .format(obj.name))
                        return {'CANCELLED'}
            else:
                for hseq in loop_seqs[1:]:
                    if len(hseq[-1]) == 1:
                        self.report({'WARNING'},
                                    "Object {}: Last face must not be triangle"
                                    .format(obj.name))
                        return {'CANCELLED'}
                    if hseq[-1][0].vert == center:
                        self.report({'WARNING'},
                                    "Object {}: Center must not be identical"
                                    .format(obj.name))
                        return {'CANCELLED'}

            # align to circle
            if self.transmission:
                for hidx, hseq in enumerate(loop_seqs):
                    for vidx, pair in enumerate(hseq):
                        all_ = int((len(hseq) + 1) / 2)
                        if center_is_identical:
                            r = (all_ - int((vidx + 1) / 2)) / all_
                        else:
                            r = (1 + all_ - int((vidx + 1) / 2)) / all_
                        pair[0][uv_layer].uv = c + (new_uvs[hidx] - c) * r
                        if self.select:
                            pair[0][uv_layer].select = True

                        if len(pair) < 2:
                            continue
                        # for quad polygon
                        next_hidx = (hidx + 1) % len(loop_seqs)
                        pair[1][uv_layer].uv = \
                            c + ((new_uvs[next_hidx]) - c) * r
                        if self.select:
                            pair[1][uv_layer].select = True
            else:
                for hidx, hseq in enumerate(loop_seqs):
                    pair = hseq[0]
                    pair[0][uv_layer].uv = new_uvs[hidx]
                    pair[1][uv_layer].uv = new_uvs[(hidx + 1) % len(loop_seqs)]
                    if self.select:
                        pair[0][uv_layer].select = True
                        pair[1][uv_layer].select = True

            bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_AlignUV_Straighten(bpy.types.Operator):

    bl_idname = "uv.muv_align_uv_straighten"
    bl_label = "Align UV (Straighten)"
    bl_description = "Straighten UV coordinates"
    bl_options = {'REGISTER', 'UNDO'}

    transmission = BoolProperty(
        name="Transmission",
        description="Align linked UVs",
        default=False
    )
    select = BoolProperty(
        name="Select",
        description="Select UVs which are aligned",
        default=False
    )
    vertical = BoolProperty(
        name="Vert-Infl (Vertical)",
        description="Align vertical direction influenced "
                    "by mesh vertex proportion",
        default=False
    )
    horizontal = BoolProperty(
        name="Vert-Infl (Horizontal)",
        description="Align horizontal direction influenced "
                    "by mesh vertex proportion",
        default=False
    )
    mesh_infl = FloatProperty(
        name="Mesh Influence",
        description="Influence rate of mesh vertex",
        min=0.0,
        max=1.0,
        default=0.0
    )

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    # selected and paralleled UV loop sequence will be aligned
    def __align_w_transmission(self, loop_seqs, uv_layer):
        base_uv = loop_seqs[0][0][0][uv_layer].uv.copy()

        # calculate diff UVs
        diff_uvs = []
        # hseq[vertical][loop]
        for hidx, hseq in enumerate(loop_seqs):
            # pair[loop]
            diffs = []
            for vidx in range(0, len(hseq), 2):
                if self.horizontal:
                    hdiff_uvs = [
                        _get_hdiff_uv_vinfl(uv_layer, loop_seqs, vidx, hidx, 0,
                                            self.mesh_infl),
                        _get_hdiff_uv_vinfl(uv_layer, loop_seqs, vidx, hidx, 1,
                                            self.mesh_infl),
                        _get_hdiff_uv_vinfl(uv_layer, loop_seqs, vidx + 1,
                                            hidx, 0, self.mesh_infl),
                        _get_hdiff_uv_vinfl(uv_layer, loop_seqs, vidx + 1,
                                            hidx, 1, self.mesh_infl),
                    ]
                else:
                    hdiff_uvs = [
                        _get_hdiff_uv(uv_layer, loop_seqs, hidx),
                        _get_hdiff_uv(uv_layer, loop_seqs, hidx + 1),
                        _get_hdiff_uv(uv_layer, loop_seqs, hidx),
                        _get_hdiff_uv(uv_layer, loop_seqs, hidx + 1)
                    ]
                if self.vertical:
                    vdiff_uvs = [
                        _get_vdiff_uv_vinfl(uv_layer, loop_seqs, vidx, hidx, 0,
                                            self.mesh_infl),
                        _get_vdiff_uv_vinfl(uv_layer, loop_seqs, vidx, hidx, 1,
                                            self.mesh_infl),
                        _get_vdiff_uv_vinfl(uv_layer, loop_seqs, vidx + 1,
                                            hidx, 0, self.mesh_infl),
                        _get_vdiff_uv_vinfl(uv_layer, loop_seqs, vidx + 1,
                                            hidx, 1, self.mesh_infl),
                    ]
                else:
                    vdiff_uvs = [
                        _get_vdiff_uv(uv_layer, loop_seqs, vidx, hidx),
                        _get_vdiff_uv(uv_layer, loop_seqs, vidx, hidx),
                        _get_vdiff_uv(uv_layer, loop_seqs, vidx + 1, hidx),
                        _get_vdiff_uv(uv_layer, loop_seqs, vidx + 1, hidx)
                    ]
                diffs.append([hdiff_uvs, vdiff_uvs])
            diff_uvs.append(diffs)

        # update UV
        for hseq, diffs in zip(loop_seqs, diff_uvs):
            for vidx in range(0, len(hseq), 2):
                loops = [
                    hseq[vidx][0], hseq[vidx][1],
                    hseq[vidx + 1][0], hseq[vidx + 1][1]
                ]
                for l, hdiff, vdiff in zip(loops, diffs[int(vidx / 2)][0],
                                           diffs[int(vidx / 2)][1]):
                    l[uv_layer].uv = base_uv + hdiff + vdiff
                    if self.select:
                        l[uv_layer].select = True

    # only selected UV loop sequence will be aligned
    def __align_wo_transmission(self, loop_seqs, uv_layer):
        base_uv = loop_seqs[0][0][0][uv_layer].uv.copy()

        h_uv = loop_seqs[-1][0][1][uv_layer].uv.copy() - base_uv
        for hidx, hseq in enumerate(loop_seqs):
            # only selected loop pair is targeted
            pair = hseq[0]
            hdiff_uv_0 = hidx * h_uv / len(loop_seqs)
            hdiff_uv_1 = (hidx + 1) * h_uv / len(loop_seqs)
            pair[0][uv_layer].uv = base_uv + hdiff_uv_0
            pair[1][uv_layer].uv = base_uv + hdiff_uv_1
            if self.select:
                pair[0][uv_layer].select = True
                pair[1][uv_layer].select = True

    def __align(self, loop_seqs, uv_layer):
        if self.transmission:
            self.__align_w_transmission(loop_seqs, uv_layer)
        else:
            self.__align_wo_transmission(loop_seqs, uv_layer)

    def execute(self, context):
        objs = common.get_uv_editable_objects(context)

        for obj in objs:
            bm = bmesh.from_edit_mesh(obj.data)
            if common.check_version(2, 73, 0) >= 0:
                bm.faces.ensure_lookup_table()
            uv_layer = bm.loops.layers.uv.verify()

            # loop_seqs[horizontal][vertical][loop]
            loop_seqs, error = common.get_loop_sequences(bm, uv_layer)
            if not loop_seqs:
                self.report({'WARNING'},
                            "Object {}: {}".format(obj.name, error))
                return {'CANCELLED'}

            # align
            self.__align(loop_seqs, uv_layer)

            bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_AlignUV_Axis(bpy.types.Operator):

    bl_idname = "uv.muv_align_uv_axis"
    bl_label = "Align UV (XY-Axis)"
    bl_description = "Align UV to XY-axis"
    bl_options = {'REGISTER', 'UNDO'}

    transmission = BoolProperty(
        name="Transmission",
        description="Align linked UVs",
        default=False
    )
    select = BoolProperty(
        name="Select",
        description="Select UVs which are aligned",
        default=False
    )
    vertical = BoolProperty(
        name="Vert-Infl (Vertical)",
        description="Align vertical direction influenced "
                    "by mesh vertex proportion",
        default=False
    )
    horizontal = BoolProperty(
        name="Vert-Infl (Horizontal)",
        description="Align horizontal direction influenced "
                    "by mesh vertex proportion",
        default=False
    )
    location = EnumProperty(
        name="Location",
        description="Align location",
        items=[
            ('LEFT_TOP', "Left/Top", "Align to Left or Top"),
            ('MIDDLE', "Middle", "Align to middle"),
            ('RIGHT_BOTTOM', "Right/Bottom", "Align to Right or Bottom")
        ],
        default='MIDDLE'
    )
    mesh_infl = FloatProperty(
        name="Mesh Influence",
        description="Influence rate of mesh vertex",
        min=0.0,
        max=1.0,
        default=0.0
    )

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    # get min/max of UV
    def __get_uv_max_min(self, loop_seqs, uv_layer):
        uv_max = Vector((-1000000.0, -1000000.0))
        uv_min = Vector((1000000.0, 1000000.0))
        for hseq in loop_seqs:
            for l in hseq[0]:
                uv = l[uv_layer].uv
                uv_max.x = max(uv.x, uv_max.x)
                uv_max.y = max(uv.y, uv_max.y)
                uv_min.x = min(uv.x, uv_min.x)
                uv_min.y = min(uv.y, uv_min.y)

        return uv_max, uv_min

    # get UV differentiation when UVs are aligned to X-axis
    def __get_x_axis_align_diff_uvs(self, loop_seqs, uv_layer, uv_min,
                                    width, height):
        diff_uvs = []
        for hidx, hseq in enumerate(loop_seqs):
            pair = hseq[0]
            luv0 = pair[0][uv_layer]
            luv1 = pair[1][uv_layer]
            target_uv0 = Vector((0.0, 0.0))
            target_uv1 = Vector((0.0, 0.0))
            if self.location == 'RIGHT_BOTTOM':
                target_uv0.y = target_uv1.y = uv_min.y
            elif self.location == 'MIDDLE':
                target_uv0.y = target_uv1.y = uv_min.y + height * 0.5
            elif self.location == 'LEFT_TOP':
                target_uv0.y = target_uv1.y = uv_min.y + height
            if luv0.uv.x < luv1.uv.x:
                target_uv0.x = uv_min.x + hidx * width / len(loop_seqs)
                target_uv1.x = uv_min.x + (hidx + 1) * width / len(loop_seqs)
            else:
                target_uv0.x = uv_min.x + (hidx + 1) * width / len(loop_seqs)
                target_uv1.x = uv_min.x + hidx * width / len(loop_seqs)
            diff_uvs.append([target_uv0 - luv0.uv, target_uv1 - luv1.uv])

        return diff_uvs

    # get UV differentiation when UVs are aligned to Y-axis
    def __get_y_axis_align_diff_uvs(self, loop_seqs, uv_layer, uv_min,
                                    width, height):
        diff_uvs = []
        for hidx, hseq in enumerate(loop_seqs):
            pair = hseq[0]
            luv0 = pair[0][uv_layer]
            luv1 = pair[1][uv_layer]
            target_uv0 = Vector((0.0, 0.0))
            target_uv1 = Vector((0.0, 0.0))
            if self.location == 'RIGHT_BOTTOM':
                target_uv0.x = target_uv1.x = uv_min.x + width
            elif self.location == 'MIDDLE':
                target_uv0.x = target_uv1.x = uv_min.x + width * 0.5
            elif self.location == 'LEFT_TOP':
                target_uv0.x = target_uv1.x = uv_min.x
            if luv0.uv.y < luv1.uv.y:
                target_uv0.y = uv_min.y + hidx * height / len(loop_seqs)
                target_uv1.y = uv_min.y + (hidx + 1) * height / len(loop_seqs)
            else:
                target_uv0.y = uv_min.y + (hidx + 1) * height / len(loop_seqs)
                target_uv1.y = uv_min.y + hidx * height / len(loop_seqs)
            diff_uvs.append([target_uv0 - luv0.uv, target_uv1 - luv1.uv])

        return diff_uvs

    # only selected UV loop sequence will be aligned along to X-axis
    def __align_to_x_axis_wo_transmission(self, loop_seqs, uv_layer,
                                          uv_min, width, height):
        # reverse if the UV coordinate is not sorted by position
        need_revese = loop_seqs[0][0][0][uv_layer].uv.x > \
            loop_seqs[-1][0][0][uv_layer].uv.x
        if need_revese:
            loop_seqs.reverse()
            for hidx, hseq in enumerate(loop_seqs):
                for vidx, pair in enumerate(hseq):
                    tmp = loop_seqs[hidx][vidx][0]
                    loop_seqs[hidx][vidx][0] = loop_seqs[hidx][vidx][1]
                    loop_seqs[hidx][vidx][1] = tmp

        # get UV differential
        diff_uvs = self.__get_x_axis_align_diff_uvs(loop_seqs,
                                                    uv_layer, uv_min,
                                                    width, height)

        # update UV
        for hseq, duv in zip(loop_seqs, diff_uvs):
            pair = hseq[0]
            luv0 = pair[0][uv_layer]
            luv1 = pair[1][uv_layer]
            luv0.uv = luv0.uv + duv[0]
            luv1.uv = luv1.uv + duv[1]

    # only selected UV loop sequence will be aligned along to Y-axis
    def __align_to_y_axis_wo_transmission(self, loop_seqs, uv_layer,
                                          uv_min, width, height):
        # reverse if the UV coordinate is not sorted by position
        need_revese = loop_seqs[0][0][0][uv_layer].uv.y > \
            loop_seqs[-1][0][0][uv_layer].uv.y
        if need_revese:
            loop_seqs.reverse()
            for hidx, hseq in enumerate(loop_seqs):
                for vidx, pair in enumerate(hseq):
                    tmp = loop_seqs[hidx][vidx][0]
                    loop_seqs[hidx][vidx][0] = loop_seqs[hidx][vidx][1]
                    loop_seqs[hidx][vidx][1] = tmp

        # get UV differential
        diff_uvs = self.__get_y_axis_align_diff_uvs(loop_seqs,
                                                    uv_layer, uv_min,
                                                    width, height)

        # update UV
        for hseq, duv in zip(loop_seqs, diff_uvs):
            pair = hseq[0]
            luv0 = pair[0][uv_layer]
            luv1 = pair[1][uv_layer]
            luv0.uv = luv0.uv + duv[0]
            luv1.uv = luv1.uv + duv[1]

    # selected and paralleled UV loop sequence will be aligned along to X-axis
    def __align_to_x_axis_w_transmission(self, loop_seqs, uv_layer,
                                         uv_min, width, height):
        # reverse if the UV coordinate is not sorted by position
        need_revese = loop_seqs[0][0][0][uv_layer].uv.x > \
            loop_seqs[-1][0][0][uv_layer].uv.x
        if need_revese:
            loop_seqs.reverse()
            for hidx, hseq in enumerate(loop_seqs):
                for vidx in range(len(hseq)):
                    tmp = loop_seqs[hidx][vidx][0]
                    loop_seqs[hidx][vidx][0] = loop_seqs[hidx][vidx][1]
                    loop_seqs[hidx][vidx][1] = tmp

        # get offset UVs when the UVs are aligned to X-axis
        align_diff_uvs = self.__get_x_axis_align_diff_uvs(loop_seqs,
                                                          uv_layer, uv_min,
                                                          width, height)
        base_uv = loop_seqs[0][0][0][uv_layer].uv.copy()
        offset_uvs = []
        for hseq, aduv in zip(loop_seqs, align_diff_uvs):
            luv0 = hseq[0][0][uv_layer]
            luv1 = hseq[0][1][uv_layer]
            offset_uvs.append([luv0.uv + aduv[0] - base_uv,
                               luv1.uv + aduv[1] - base_uv])

        # get UV differential
        diff_uvs = []
        # hseq[vertical][loop]
        for hidx, hseq in enumerate(loop_seqs):
            # pair[loop]
            diffs = []
            for vidx in range(0, len(hseq), 2):
                if self.horizontal:
                    hdiff_uvs = [
                        _get_hdiff_uv_vinfl(uv_layer, loop_seqs, vidx, hidx, 0,
                                            self.mesh_infl),
                        _get_hdiff_uv_vinfl(uv_layer, loop_seqs, vidx, hidx, 1,
                                            self.mesh_infl),
                        _get_hdiff_uv_vinfl(uv_layer, loop_seqs, vidx + 1,
                                            hidx, 0, self.mesh_infl),
                        _get_hdiff_uv_vinfl(uv_layer, loop_seqs, vidx + 1,
                                            hidx, 1, self.mesh_infl),
                    ]
                    hdiff_uvs[0].y = hdiff_uvs[0].y + offset_uvs[hidx][0].y
                    hdiff_uvs[1].y = hdiff_uvs[1].y + offset_uvs[hidx][1].y
                    hdiff_uvs[2].y = hdiff_uvs[2].y + offset_uvs[hidx][0].y
                    hdiff_uvs[3].y = hdiff_uvs[3].y + offset_uvs[hidx][1].y
                else:
                    hdiff_uvs = [
                        offset_uvs[hidx][0],
                        offset_uvs[hidx][1],
                        offset_uvs[hidx][0],
                        offset_uvs[hidx][1],
                    ]
                if self.vertical:
                    vdiff_uvs = [
                        _get_vdiff_uv_vinfl(uv_layer, loop_seqs, vidx, hidx, 0,
                                            self.mesh_infl),
                        _get_vdiff_uv_vinfl(uv_layer, loop_seqs, vidx, hidx, 1,
                                            self.mesh_infl),
                        _get_vdiff_uv_vinfl(uv_layer, loop_seqs, vidx + 1,
                                            hidx, 0, self.mesh_infl),
                        _get_vdiff_uv_vinfl(uv_layer, loop_seqs, vidx + 1,
                                            hidx, 1, self.mesh_infl),
                    ]
                else:
                    vdiff_uvs = [
                        _get_vdiff_uv(uv_layer, loop_seqs, vidx, hidx),
                        _get_vdiff_uv(uv_layer, loop_seqs, vidx, hidx),
                        _get_vdiff_uv(uv_layer, loop_seqs, vidx + 1, hidx),
                        _get_vdiff_uv(uv_layer, loop_seqs, vidx + 1, hidx)
                    ]
                diffs.append([hdiff_uvs, vdiff_uvs])
            diff_uvs.append(diffs)

        # update UV
        for hseq, diffs in zip(loop_seqs, diff_uvs):
            for vidx in range(0, len(hseq), 2):
                loops = [
                    hseq[vidx][0], hseq[vidx][1],
                    hseq[vidx + 1][0], hseq[vidx + 1][1]
                ]
                for l, hdiff, vdiff in zip(loops, diffs[int(vidx / 2)][0],
                                           diffs[int(vidx / 2)][1]):
                    l[uv_layer].uv = base_uv + hdiff + vdiff
                    if self.select:
                        l[uv_layer].select = True

    # selected and paralleled UV loop sequence will be aligned along to Y-axis
    def __align_to_y_axis_w_transmission(self, loop_seqs, uv_layer,
                                         uv_min, width, height):
        # reverse if the UV coordinate is not sorted by position
        need_revese = loop_seqs[0][0][0][uv_layer].uv.y > \
            loop_seqs[-1][0][-1][uv_layer].uv.y
        if need_revese:
            loop_seqs.reverse()
            for hidx, hseq in enumerate(loop_seqs):
                for vidx in range(len(hseq)):
                    tmp = loop_seqs[hidx][vidx][0]
                    loop_seqs[hidx][vidx][0] = loop_seqs[hidx][vidx][1]
                    loop_seqs[hidx][vidx][1] = tmp

        # get offset UVs when the UVs are aligned to Y-axis
        align_diff_uvs = self.__get_y_axis_align_diff_uvs(loop_seqs,
                                                          uv_layer, uv_min,
                                                          width, height)
        base_uv = loop_seqs[0][0][0][uv_layer].uv.copy()
        offset_uvs = []
        for hseq, aduv in zip(loop_seqs, align_diff_uvs):
            luv0 = hseq[0][0][uv_layer]
            luv1 = hseq[0][1][uv_layer]
            offset_uvs.append([luv0.uv + aduv[0] - base_uv,
                               luv1.uv + aduv[1] - base_uv])

        # get UV differential
        diff_uvs = []
        # hseq[vertical][loop]
        for hidx, hseq in enumerate(loop_seqs):
            # pair[loop]
            diffs = []
            for vidx in range(0, len(hseq), 2):
                if self.horizontal:
                    hdiff_uvs = [
                        _get_hdiff_uv_vinfl(uv_layer, loop_seqs, vidx, hidx, 0,
                                            self.mesh_infl),
                        _get_hdiff_uv_vinfl(uv_layer, loop_seqs, vidx, hidx, 1,
                                            self.mesh_infl),
                        _get_hdiff_uv_vinfl(uv_layer, loop_seqs, vidx + 1,
                                            hidx, 0, self.mesh_infl),
                        _get_hdiff_uv_vinfl(uv_layer, loop_seqs, vidx + 1,
                                            hidx, 1, self.mesh_infl),
                    ]
                    hdiff_uvs[0].x = hdiff_uvs[0].x + offset_uvs[hidx][0].x
                    hdiff_uvs[1].x = hdiff_uvs[1].x + offset_uvs[hidx][1].x
                    hdiff_uvs[2].x = hdiff_uvs[2].x + offset_uvs[hidx][0].x
                    hdiff_uvs[3].x = hdiff_uvs[3].x + offset_uvs[hidx][1].x
                else:
                    hdiff_uvs = [
                        offset_uvs[hidx][0],
                        offset_uvs[hidx][1],
                        offset_uvs[hidx][0],
                        offset_uvs[hidx][1],
                    ]
                if self.vertical:
                    vdiff_uvs = [
                        _get_vdiff_uv_vinfl(uv_layer, loop_seqs, vidx, hidx, 0,
                                            self.mesh_infl),
                        _get_vdiff_uv_vinfl(uv_layer, loop_seqs, vidx, hidx, 1,
                                            self.mesh_infl),
                        _get_vdiff_uv_vinfl(uv_layer, loop_seqs, vidx + 1,
                                            hidx, 0, self.mesh_infl),
                        _get_vdiff_uv_vinfl(uv_layer, loop_seqs, vidx + 1,
                                            hidx, 1, self.mesh_infl),
                    ]
                else:
                    vdiff_uvs = [
                        _get_vdiff_uv(uv_layer, loop_seqs, vidx, hidx),
                        _get_vdiff_uv(uv_layer, loop_seqs, vidx, hidx),
                        _get_vdiff_uv(uv_layer, loop_seqs, vidx + 1, hidx),
                        _get_vdiff_uv(uv_layer, loop_seqs, vidx + 1, hidx)
                    ]
                diffs.append([hdiff_uvs, vdiff_uvs])
            diff_uvs.append(diffs)

        # update UV
        for hseq, diffs in zip(loop_seqs, diff_uvs):
            for vidx in range(0, len(hseq), 2):
                loops = [
                    hseq[vidx][0], hseq[vidx][1],
                    hseq[vidx + 1][0], hseq[vidx + 1][1]
                ]
                for l, hdiff, vdiff in zip(loops, diffs[int(vidx / 2)][0],
                                           diffs[int(vidx / 2)][1]):
                    l[uv_layer].uv = base_uv + hdiff + vdiff
                    if self.select:
                        l[uv_layer].select = True

    def __align(self, loop_seqs, uv_layer, uv_min, width, height):
        # align along to x-axis
        if width > height:
            if self.transmission:
                self.__align_to_x_axis_w_transmission(loop_seqs,
                                                      uv_layer, uv_min,
                                                      width, height)
            else:
                self.__align_to_x_axis_wo_transmission(loop_seqs,
                                                       uv_layer, uv_min,
                                                       width, height)
        # align along to y-axis
        else:
            if self.transmission:
                self.__align_to_y_axis_w_transmission(loop_seqs,
                                                      uv_layer, uv_min,
                                                      width, height)
            else:
                self.__align_to_y_axis_wo_transmission(loop_seqs,
                                                       uv_layer, uv_min,
                                                       width, height)

    def execute(self, context):
        objs = common.get_uv_editable_objects(context)

        for obj in objs:
            bm = bmesh.from_edit_mesh(obj.data)
            if common.check_version(2, 73, 0) >= 0:
                bm.faces.ensure_lookup_table()
            uv_layer = bm.loops.layers.uv.verify()

            # loop_seqs[horizontal][vertical][loop]
            loop_seqs, error = common.get_loop_sequences(bm, uv_layer)
            if not loop_seqs:
                self.report({'WARNING'},
                            "Object {}: {}".format(obj.name, error))
                return {'CANCELLED'}

            # get height and width
            uv_max, uv_min = self.__get_uv_max_min(loop_seqs, uv_layer)
            width = uv_max.x - uv_min.x
            height = uv_max.y - uv_min.y

            self.__align(loop_seqs, uv_layer, uv_min, width, height)

            bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_AlignUV_SnapToPoint(bpy.types.Operator):

    bl_idname = "uv.muv_align_uv_snap_to_point"
    bl_label = "Align UV (Snap to Point)"
    bl_description = "Align UV to the target point"
    bl_options = {'REGISTER', 'UNDO'}

    group = EnumProperty(
        name="Snap Group",
        description="Group that snap operation applies for",
        items=[
            ('VERT', "Vertex", "Vertex"),
            ('FACE', "Face", "Face"),
            ('UV_ISLAND', "UV Island", "UV Island"),
        ],
        default='FACE'
    )
    target = FloatVectorProperty(
        name="Snap Target",
        description="Target where UV vertices snap to",
        size=2,
        precision=4,
        soft_min=-1.0,
        soft_max=1.0,
        step=1,
        default=(0.000, 0.000),
    )

    def _get_snap_target_loops(self, context, bm, uv_layer):
        target_loops = []

        selected_faces = [f for f in bm.faces if f.select]

        # Process snap operation.
        for face in selected_faces:
            for l in face.loops:
                if context.tool_settings.use_uv_select_sync or \
                        l[uv_layer].select:
                    target_loops.append(l)

        return target_loops

    def _get_snap_target_faces(self, context, bm, uv_layer):
        target_faces = []

        selected_faces = [f for f in bm.faces if f.select]

        for face in selected_faces:
            for l in face.loops:
                if not context.tool_settings.use_uv_select_sync and \
                        not l[uv_layer].select:
                    break
            else:
                target_faces.append(face)

        return target_faces

    def _get_snap_target_islands(self, context, bm, uv_layer):
        target_islands = []

        islands = common.get_island_info_from_bmesh(bm, only_selected=True)

        for isl in islands:
            some_verts_not_selected = False
            for face in isl["faces"]:
                for l in face["face"].loops:
                    if not context.tool_settings.use_uv_select_sync and \
                            not l[uv_layer].select:
                        some_verts_not_selected = True
                        break
            if not some_verts_not_selected:
                target_islands.append(isl)

        return target_islands

    def execute(self, context):
        objs = common.get_uv_editable_objects(context)

        group_to_reason = {
            'VERT': "Vertex",
            'FACE': "Face",
            'UV_ISLAND': "UV Island",
        }
        no_selection_reason = group_to_reason[self.group]

        for obj in objs:
            bm = bmesh.from_edit_mesh(obj.data)
            if common.check_version(2, 73, 0) >= 0:
                bm.faces.ensure_lookup_table()
            uv_layer = bm.loops.layers.uv.verify()

            if self.group == 'VERT':
                target_loops = \
                    self._get_snap_target_loops(context, bm, uv_layer)

                # Process snap operation.
                for l in target_loops:
                    l[uv_layer].uv = self.target
                    no_selection_reason = None

            elif self.group == 'FACE':
                target_faces = \
                    self._get_snap_target_faces(context, bm, uv_layer)

                for face in target_faces:
                    ave_uv = Vector((0.0, 0.0))
                    for l in face.loops:
                        ave_uv += l[uv_layer].uv
                    ave_uv /= len(face.loops)
                    diff = Vector(self.target) - ave_uv

                    # Process snap operation.
                    for l in face.loops:
                        l[uv_layer].uv += diff
                        no_selection_reason = None

            elif self.group == 'UV_ISLAND':
                target_islands = \
                    self._get_snap_target_islands(context, bm, uv_layer)

                for isl in target_islands:
                    ave_uv = Vector((0.0, 0.0))
                    count = 0
                    for face in isl["faces"]:
                        for l in face["face"].loops:
                            ave_uv += l[uv_layer].uv
                            count += 1
                    if count != 0:
                        ave_uv /= count
                    diff = Vector(self.target) - ave_uv

                    # Process snap operation.
                    for face in isl["faces"]:
                        for l in face["face"].loops:
                            l[uv_layer].uv += diff
                            no_selection_reason = None

            bmesh.update_edit_mesh(obj.data)

        if no_selection_reason:
            self.report(
                {'WARNING'},
                "Must select more than 1 {}.".format(no_selection_reason)
            )
            return {'CANCELLED'}

        return {'FINISHED'}


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_AlignUV_Snap_SetPointTargetToCursor(bpy.types.Operator):

    bl_idname = "uv.muv_align_uv_snap_set_point_target_to_cursor"
    bl_label = "Set Point Target to Cursor"
    bl_description = """Set point target to the cursor for
                        'Align UV (Snap to Point)'"""
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        sc = context.scene

        _, _, space = common.get_space('IMAGE_EDITOR', 'WINDOW',
                                       'IMAGE_EDITOR')
        cursor_loc = space.cursor_location

        sc.muv_align_uv_snap_point_target = cursor_loc

        return {'FINISHED'}


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_AlignUV_Snap_SetPointTargetToVertexGroup(bpy.types.Operator):

    bl_idname = "uv.muv_align_uv_snap_set_point_target_to_vertex_group"
    bl_label = "Set Point Target to Vertex Group"
    bl_description = """Set point target to the average of vertices for
                        'Align UV (Snap to Point)'"""
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        sc = context.scene
        objs = common.get_uv_editable_objects(context)

        ave_uv = Vector((0.0, 0.0))
        count = 0
        for obj in objs:
            bm = bmesh.from_edit_mesh(obj.data)
            if common.check_version(2, 73, 0) >= 0:
                bm.faces.ensure_lookup_table()
            uv_layer = bm.loops.layers.uv.verify()

            selected_faces = [f for f in bm.faces if f.select]
            for face in selected_faces:
                for l in face.loops:
                    if context.tool_settings.use_uv_select_sync or \
                            l[uv_layer].select:
                        ave_uv += l[uv_layer].uv
                        count += 1
        if count != 0:
            ave_uv /= count

        sc.muv_align_uv_snap_point_target = ave_uv

        return {'FINISHED'}


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_AlignUV_SnapToEdge(bpy.types.Operator):

    bl_idname = "uv.muv_align_uv_snap_to_edge"
    bl_label = "Align UV (Snap to Edge)"
    bl_description = "Align UV to the target edge"
    bl_options = {'REGISTER', 'UNDO'}

    group = EnumProperty(
        name="Snap Group",
        description="Group that snap operation applies for",
        items=[
            ('EDGE', "Edge", "Edge"),
            ('FACE', "Face", "Face"),
            ('UV_ISLAND', "UV Island", "UV Island"),
        ],
        default='FACE'
    )
    target_1 = FloatVectorProperty(
        name="Snap Target 1",
        description="Vertex 1 of the target edge",
        size=2,
        precision=4,
        soft_min=-1.0,
        soft_max=1.0,
        step=1,
        default=(0.000, 0.000),
    )
    target_2 = FloatVectorProperty(
        name="Snap Target 2",
        description="Vertex 2 of the target edge",
        size=2,
        precision=4,
        soft_min=-1.0,
        soft_max=1.0,
        step=1,
        default=(0.000, 0.000),
    )

    def _calc_snap_move_amount(self, loops, uv_layer):
        ave = (loops[0][uv_layer].uv + loops[1][uv_layer].uv) / 2
        target = (Vector(self.target_1) + Vector(self.target_2)) / 2

        return target - ave

    def _get_snap_target_loop_pairs(self, bm, uv_layer):
        target_loop_pairs = []

        selected_edges = [e for e in bm.edges if e.select]

        cand_loops = []
        for edge in selected_edges:
            for l in edge.link_loops:
                if l[uv_layer].select:
                    cand_loops.append(l)

        for l in cand_loops:
            if l[uv_layer].select and l.link_loop_next[uv_layer].select:
                d = {l, l.link_loop_next}
                if d not in target_loop_pairs:
                    assert l.face == l.link_loop_next.face
                    target_loop_pairs.append(d)

        return target_loop_pairs

    def _find_target_island_from_face(self, islands, face):
        for isl in islands:
            for f in isl["faces"]:
                if f["face"] == face:
                    return isl

        return None

    def execute(self, context):
        objs = common.get_uv_editable_objects(context)

        no_selection = True
        for obj in objs:
            bm = bmesh.from_edit_mesh(obj.data)
            if common.check_version(2, 73, 0) >= 0:
                bm.faces.ensure_lookup_table()
            uv_layer = bm.loops.layers.uv.verify()

            if self.group == 'EDGE':
                target_loop_pairs = \
                    self._get_snap_target_loop_pairs(bm, uv_layer)

                for pair in target_loop_pairs:
                    p = list(pair)
                    diff = self._calc_snap_move_amount(p, uv_layer)

                    # Process snap operation.
                    p[0][uv_layer].uv += diff
                    p[1][uv_layer].uv += diff

                    no_selection = False

            elif self.group == 'FACE':
                target_loop_pairs = \
                    self._get_snap_target_loop_pairs(bm, uv_layer)

                face_processed = []
                for pair in target_loop_pairs:
                    p = list(pair)
                    diff = self._calc_snap_move_amount(p, uv_layer)

                    # Process snap operation.
                    face = p[0].face
                    if face in face_processed:
                        self.report(
                            {'WARNING'},
                            "Must select only one edge per face. (Object: {})"
                            .format(obj.name)
                        )
                        return {'CANCELLED'}
                    face_processed.append(face)
                    for l in face.loops:
                        l[uv_layer].uv += diff
                        no_selection = False

            elif self.group == 'UV_ISLAND':
                target_loop_pairs = \
                    self._get_snap_target_loop_pairs(bm, uv_layer)

                islands = common.get_island_info_from_bmesh(
                    bm, only_selected=False)

                isl_processed = []
                for pair in target_loop_pairs:
                    p = list(pair)
                    diff = self._calc_snap_move_amount(p, uv_layer)

                    # Find island to process.
                    face = p[0].face
                    target_isl = \
                        self._find_target_island_from_face(islands, face)
                    if target_isl is None:
                        self.report(
                            {'WARNING'},
                            "Failed to find island. (Object: {})"
                            .format(obj.name)
                        )
                        return {'CANCELLED'}
                    if target_isl in isl_processed:
                        self.report(
                            {'WARNING'},
                            """Must select only one edge per island.
                               (Object: {})"""
                            .format(obj.name)
                        )
                        return {'CANCELLED'}
                    isl_processed.append(target_isl)

                    # Process snap operation.
                    for f in target_isl["faces"]:
                        for l in f["face"].loops:
                            l[uv_layer].uv += diff
                            no_selection = False

            bmesh.update_edit_mesh(obj.data)

        if no_selection:
            self.report({'WARNING'}, "Must select more than 1 Edge.")
            return {'CANCELLED'}

        return {'FINISHED'}


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_AlignUV_Snap_SetEdgeTargetToEdgeCenter(bpy.types.Operator):

    bl_idname = "uv.muv_align_uv_snap_set_edge_target_to_edge_center"
    bl_label = "Set Edge Target to Edge Center"
    bl_description = """Set edge target to the center of edge for
                        'Align UV (Snap to Edge)'"""
    bl_options = {'REGISTER', 'UNDO'}

    def _get_target_loop_pairs(self, bm, uv_layer):
        target_loop_pairs = []

        selected_edges = [e for e in bm.edges if e.select]

        cand_loops = []
        for edge in selected_edges:
            for l in edge.link_loops:
                if l[uv_layer].select:
                    cand_loops.append(l)

        for l in cand_loops:
            if l[uv_layer].select and l.link_loop_next[uv_layer].select:
                d = {l, l.link_loop_next}
                if d not in target_loop_pairs:
                    assert l.face == l.link_loop_next.face
                    target_loop_pairs.append(d)

        return target_loop_pairs

    def execute(self, context):
        sc = context.scene
        objs = common.get_uv_editable_objects(context)

        ave_uv_1 = Vector((0.0, 0.0))
        ave_uv_2 = Vector((0.0, 0.0))
        count = 0
        for obj in objs:
            bm = bmesh.from_edit_mesh(obj.data)
            if common.check_version(2, 73, 0) >= 0:
                bm.faces.ensure_lookup_table()
            uv_layer = bm.loops.layers.uv.verify()

            target_loop_pairs = self._get_target_loop_pairs(bm, uv_layer)
            for pair in target_loop_pairs:
                p = list(pair)
                uv_1 = p[0][uv_layer].uv
                uv_2 = p[1][uv_layer].uv
                ave_uv_1 += uv_1
                ave_uv_2 += uv_2
                count += 1

        if count != 0:
            ave_uv_1 /= count
            ave_uv_2 /= count

        sc.muv_align_uv_snap_edge_target_1 = ave_uv_1
        sc.muv_align_uv_snap_edge_target_2 = ave_uv_2

        return {'FINISHED'}
