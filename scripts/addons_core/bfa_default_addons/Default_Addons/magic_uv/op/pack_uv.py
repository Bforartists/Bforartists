# SPDX-FileCopyrightText: 2017-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"

from math import fabs

import bpy
from bpy.props import (
    FloatProperty,
    FloatVectorProperty,
    BoolProperty,
)
import bmesh
import mathutils
from mathutils import Vector

from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry
from ..utils.graph import graph_is_isomorphic
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


def _sort_island_faces(kd, uvs, isl1, isl2):
    """
    Sort faces in island
    """

    sorted_faces = []
    for f in isl1['sorted']:
        _, idx, _ = kd.find(
            Vector((f['ave_uv'].x, f['ave_uv'].y, 0.0)))
        sorted_faces.append(isl2['faces'][uvs[idx]['face_idx']])
    return sorted_faces


def _group_island(island_info, allowable_center_deviation,
                  allowable_size_deviation):
    """
    Group island
    """

    num_group = 0
    while True:
        # search islands which is not parsed yet
        isl_1 = None
        for isl_1 in island_info:
            if isl_1['group'] == -1:
                break
        else:
            break   # all faces are parsed
        if isl_1 is None:
            break
        isl_1['group'] = num_group
        isl_1['sorted'] = isl_1['faces']

        # search same island
        for isl_2 in island_info:
            if isl_2['group'] == -1:
                dcx = isl_2['center'].x - isl_1['center'].x
                dcy = isl_2['center'].y - isl_1['center'].y
                dsx = isl_2['size'].x - isl_1['size'].x
                dsy = isl_2['size'].y - isl_1['size'].y
                center_x_matched = (
                    fabs(dcx) < allowable_center_deviation[0]
                )
                center_y_matched = (
                    fabs(dcy) < allowable_center_deviation[1]
                )
                size_x_matched = (
                    fabs(dsx) < allowable_size_deviation[0]
                )
                size_y_matched = (
                    fabs(dsy) < allowable_size_deviation[1]
                )
                center_matched = center_x_matched and center_y_matched
                size_matched = size_x_matched and size_y_matched
                num_uv_matched = (isl_2['num_uv'] == isl_1['num_uv'])
                # are islands have same?
                if center_matched and size_matched and num_uv_matched:
                    isl_2['group'] = num_group
                    kd = mathutils.kdtree.KDTree(len(isl_2['faces']))
                    uvs = [
                        {
                            'uv': Vector(
                                (f['ave_uv'].x, f['ave_uv'].y, 0.0)
                            ),
                            'face_idx': fidx
                        } for fidx, f in enumerate(isl_2['faces'])
                    ]
                    for i, uv in enumerate(uvs):
                        kd.insert(uv['uv'], i)
                    kd.balance()
                    # sort faces for copy/paste UV
                    isl_2['sorted'] = _sort_island_faces(kd, uvs, isl_1, isl_2)
        num_group = num_group + 1

    return num_group


@PropertyClassRegistry()
class _Properties:
    idname = "pack_uv"

    @classmethod
    def init_props(cls, scene):
        scene.muv_pack_uv_enabled = BoolProperty(
            name="Pack UV Enabled",
            description="Pack UV is enabled",
            default=False
        )
        scene.muv_pack_uv_allowable_center_deviation = FloatVectorProperty(
            name="Allowable Center Deviation",
            description="Allowable center deviation to judge same UV island",
            min=0.000001,
            max=10.0,
            default=(0.001, 0.001),
            size=2,
            subtype='XYZ'
        )
        scene.muv_pack_uv_allowable_size_deviation = FloatVectorProperty(
            name="Allowable Size Deviation",
            description="Allowable sizes deviation to judge same UV island",
            min=0.000001,
            max=10.0,
            default=(0.001, 0.001),
            size=2,
            subtype='XYZ'
        )
        scene.muv_pack_uv_accurate_island_copy = BoolProperty(
            name="Accurate Island Copy",
            description="Copy islands topologically",
            default=True
        )
        scene.muv_pack_uv_stride = FloatVectorProperty(
            name="Stride",
            description="Stride UV coordinates",
            min=-100.0,
            max=100.0,
            default=(0.0, 0.0),
            size=2,
            subtype='XYZ'
        )
        scene.muv_pack_uv_apply_pack_uv = BoolProperty(
            name="Apply Pack UV",
            description="Apply Pack UV operation intrinsic to Blender itself",
            default=True
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_pack_uv_enabled
        del scene.muv_pack_uv_allowable_center_deviation
        del scene.muv_pack_uv_allowable_size_deviation
        del scene.muv_pack_uv_accurate_island_copy
        del scene.muv_pack_uv_stride
        del scene.muv_pack_uv_apply_pack_uv


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_PackUV(bpy.types.Operator):
    """
    Operation class: Pack UV with same UV islands are integrated
    Island matching algorithm
     - Same center of UV island
     - Same size of UV island
     - Same number of UV
    """

    bl_idname = "uv.muv_pack_uv"
    bl_label = "Pack UV"
    bl_description = "Pack UV (Same UV Islands are integrated)"
    bl_options = {'REGISTER', 'UNDO'}

    rotate = BoolProperty(
        name="Rotate",
        description="Rotate option used by default pack UV function",
        default=False)
    margin = FloatProperty(
        name="Margin",
        description="Margin used by default pack UV function",
        min=0,
        max=1,
        default=0.001
    )
    allowable_center_deviation = FloatVectorProperty(
        name="Allowable Center Deviation",
        description="Allowable center deviation to judge same UV island",
        min=0.000001,
        max=10.0,
        default=(0.001, 0.001),
        size=2,
        subtype='XYZ'
    )
    allowable_size_deviation = FloatVectorProperty(
        name="Allowable Size Deviation",
        description="Allowable sizse deviation to judge same UV island",
        min=0.000001,
        max=10.0,
        default=(0.001, 0.001),
        size=2,
        subtype='XYZ'
    )
    accurate_island_copy = BoolProperty(
        name="Accurate Island Copy",
        description="Copy islands topologically",
        default=True
    )
    stride = FloatVectorProperty(
        name="Stride",
        description="Stride UV coordinates",
        min=-100.0,
        max=100.0,
        default=(0.0, 0.0),
        size=2,
        subtype='XYZ'
    )
    apply_pack_uv = BoolProperty(
        name="Apply Pack UV",
        description="Apply Pack UV operation intrinsic to Blender itself",
        default=True
    )

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    def execute(self, context):
        objs = common.get_uv_editable_objects(context)

        island_info = []
        selected_faces = []
        island_to_bm = {}
        island_to_uv_layer = {}
        bm_to_loop_lists = {}
        for obj in objs:
            bm = bmesh.from_edit_mesh(obj.data)
            if common.check_version(2, 73, 0) >= 0:
                bm.faces.ensure_lookup_table()
            if not bm.loops.layers.uv:
                self.report({'WARNING'},
                            "Object {} must have more than one UV map"
                            .format(obj.name))
                return {'CANCELLED'}
            uv_layer = bm.loops.layers.uv.verify()

            selected_faces.extend([f for f in bm.faces if f.select])
            isl = common.get_island_info(obj)
            for i, info in enumerate(isl):
                id_ = i + len(island_info)
                island_to_bm[id_] = bm
                island_to_uv_layer[id_] = uv_layer
                info["id"] = id_
            island_info.extend(isl)
            bm_to_loop_lists[bm] = [l for f in bm.faces for l in f.loops]

        num_group = _group_island(island_info,
                                  self.allowable_center_deviation,
                                  self.allowable_size_deviation)
        bpy.ops.mesh.select_all(action='DESELECT')

        # pack UV
        for gidx in range(num_group):
            group = list(filter(
                lambda i, idx=gidx: i['group'] == idx, island_info))
            for f in group[0]['faces']:
                f['face'].select = True
        for obj in objs:
            bmesh.update_edit_mesh(obj.data)
        bpy.ops.uv.select_all(action='SELECT')
        if self.apply_pack_uv:
            bpy.ops.uv.pack_islands(rotate=self.rotate, margin=self.margin)

        # copy/paste UV among same islands
        for gidx in range(num_group):
            group = list(filter(
                lambda i, idx=gidx: i['group'] == idx, island_info))
            if len(group) <= 1:
                continue
            src_bm = island_to_bm[group[0]["id"]]
            src_uv_layer = island_to_uv_layer[group[0]["id"]]
            src_loop_lists = bm_to_loop_lists[src_bm]

            src_loops = []
            for f in group[0]["faces"]:
                for l in f["face"].loops:
                    src_loops.append(l)

            src_uv_graph = common.create_uv_graph(src_loops, src_uv_layer)

            for stride_idx, g in enumerate(group[1:]):
                dst_bm = island_to_bm[g["id"]]
                dst_uv_layer = island_to_uv_layer[g["id"]]
                dst_loop_lists = bm_to_loop_lists[dst_bm]

                dst_loops = []
                for f in g["faces"]:
                    for l in f["face"].loops:
                        dst_loops.append(l)

                dst_uv_graph = common.create_uv_graph(dst_loops, dst_uv_layer)

                uv_stride = Vector(((stride_idx + 1) * self.stride.x,
                                    (stride_idx + 1) * self.stride.y))
                if self.accurate_island_copy:
                    # Check if the graph is isomorphic.
                    # If the graph is isomorphic, matching pair is returned.
                    result, pairs = graph_is_isomorphic(
                        src_uv_graph, dst_uv_graph)
                    if not result:
                        self.report(
                            {'WARNING'},
                            "Island does not match. "
                            "Disable 'Accurate Island Copy' and try again")
                        return {'CANCELLED'}

                    # Paste UV island.
                    for n1, n2 in pairs.items():
                        uv1 = n1.value["uv_vert"][src_uv_layer].uv
                        l2 = n2.value["loops"]
                        for l in l2:
                            l[dst_uv_layer].uv = uv1 + uv_stride
                else:
                    for (src_face, dest_face) in zip(
                            group[0]['sorted'], g['sorted']):
                        for (src_loop, dest_loop) in zip(
                                src_face['face'].loops,
                                dest_face['face'].loops):
                            src_lidx = src_loop.index
                            dst_lidx = dest_loop.index
                            dst_loop_lists[dst_lidx][dst_uv_layer].uv = \
                                src_loop_lists[src_lidx][src_uv_layer].uv + \
                                uv_stride

        # restore face/UV selection
        bpy.ops.uv.select_all(action='DESELECT')
        bpy.ops.mesh.select_all(action='DESELECT')
        for f in selected_faces:
            f.select = True
        bpy.ops.uv.select_all(action='SELECT')

        for obj in objs:
            bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}
