# SPDX-FileCopyrightText: 2018-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "imdjs, Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"

import math
from math import atan2, sin, cos

import bpy
import bmesh
from mathutils import Vector
from bpy.props import BoolProperty

from .. import common
from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry
from ..utils.graph import graph_is_isomorphic
from ..utils import compatibility as compat


def _is_valid_context(context):
    # 'IMAGE_EDITOR' and 'VIEW_3D' space is allowed to execute.
    # If 'View_3D' space is not allowed, you can't find option in Tool-Shelf
    # after the execution
    if not common.is_valid_space(context, ['IMAGE_EDITOR', 'VIEW_3D']):
        return False

    # Multiple objects editing mode is not supported in this feature.
    objs = common.get_uv_editable_objects(context)
    if len(objs) != 1:
        return False

    # only edit mode is allowed to execute
    if context.object.mode != 'EDIT':
        return False

    return True


@PropertyClassRegistry()
class _Properties:
    idname = "copy_paste_uv_uvedit"

    @classmethod
    def init_props(cls, scene):
        class CopyPastUVProps():
            src_uvs = None

        class CopyPasteUVIslandProps():
            # [
            #   {
            #     "bmesh": BMesh,
            #     "uv_layer": UV Layer,
            #     "island": UV Island,
            #   }
            # ]
            src_data = []
            src_objects = []

        scene.muv_props.copy_paste_uv_uvedit = CopyPastUVProps()
        scene.muv_props.copy_paste_uv_island = CopyPasteUVIslandProps()

        scene.muv_copy_paste_uv_uvedit_unique_target = BoolProperty(
            name="Unique Target",
            description="Paste to the target uniquely",
            default=False
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_props.copy_paste_uv_uvedit
        del scene.muv_props.copy_paste_uv_island


@BlClassRegistry()
class MUV_OT_CopyPasteUVUVEdit_CopyUV(bpy.types.Operator):
    """
    Operation class: Copy UV coordinate on UV/Image Editor
    """

    bl_idname = "uv.muv_copy_paste_uv_uvedit_copy_uv"
    bl_label = "Copy UV (UV/Image Editor)"
    bl_description = "Copy UV coordinate (only selected in UV/Image Editor)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    def execute(self, context):
        props = context.scene.muv_props.copy_paste_uv_uvedit

        objs = common.get_uv_editable_objects(context)
        # poll() method ensures that only one object is selected.
        obj = objs[0]
        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.verify()
        if common.check_version(2, 73, 0) >= 0:
            bm.faces.ensure_lookup_table()

        props.src_uvs = []
        for face in bm.faces:
            if not face.select:
                continue
            skip = False
            for l in face.loops:
                if not l[uv_layer].select:
                    skip = True
                    break
            if skip:
                continue
            props.src_uvs.append([l[uv_layer].uv.copy() for l in face.loops])

        return {'FINISHED'}


@BlClassRegistry()
class MUV_OT_CopyPasteUVUVEdit_PasteUV(bpy.types.Operator):
    """
    Operation class: Paste UV coordinate on UV/Image Editor
    """

    bl_idname = "uv.muv_copy_paste_uv_uvedit_paste_uv"
    bl_label = "Paste UV (UV/Image Editor)"
    bl_description = "Paste UV coordinate (only selected in UV/Image Editor)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        sc = context.scene
        props = sc.muv_props.copy_paste_uv_uvedit
        if not props.src_uvs:
            return False
        return _is_valid_context(context)

    def execute(self, context):
        props = context.scene.muv_props.copy_paste_uv_uvedit

        objs = common.get_uv_editable_objects(context)
        # poll() method ensures that only one object is selected.
        obj = objs[0]
        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.verify()
        if common.check_version(2, 73, 0) >= 0:
            bm.faces.ensure_lookup_table()

        dest_uvs = []
        dest_face_indices = []
        for face in bm.faces:
            if not face.select:
                continue
            skip = False
            for l in face.loops:
                if not l[uv_layer].select:
                    skip = True
                    break
            if skip:
                continue
            dest_face_indices.append(face.index)
            uvs = [l[uv_layer].uv.copy() for l in face.loops]
            dest_uvs.append(uvs)

        for suvs, duvs in zip(props.src_uvs, dest_uvs):
            src_diff = suvs[1] - suvs[0]
            dest_diff = duvs[1] - duvs[0]

            src_base = suvs[0]
            dest_base = duvs[0]

            src_rad = atan2(src_diff.y, src_diff.x)
            dest_rad = atan2(dest_diff.y, dest_diff.x)
            if src_rad < dest_rad:
                radian = dest_rad - src_rad
            elif src_rad > dest_rad:
                radian = math.pi * 2 - (src_rad - dest_rad)
            else:       # src_rad == dest_rad
                radian = 0.0

            ratio = dest_diff.length / src_diff.length
            break

        for suvs, fidx in zip(props.src_uvs, dest_face_indices):
            for l, suv in zip(bm.faces[fidx].loops, suvs):
                base = suv - src_base
                radian_ref = atan2(base.y, base.x)
                radian_fin = (radian + radian_ref)
                length = base.length
                turn = Vector((length * cos(radian_fin),
                               length * sin(radian_fin)))
                target_uv = Vector((turn.x * ratio, turn.y * ratio)) + \
                    dest_base
                l[uv_layer].uv = target_uv

        bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}


# Return selected/all count.
#   If context.tool_settings.use_uv_select_sync is enabled:
#      Return selected/all face count.
#   If context.tool_settings.use_uv_select_sync is disabled:
#      Return selected/all loop count.
def get_counts(context, island, uv_layer):
    selected_count = 0
    all_count = 0
    if context.tool_settings.use_uv_select_sync:
        for f in island["faces"]:
            all_count += 1
            if f["face"].select:
                selected_count += 1
    else:
        for f in island["faces"]:
            for l in f["face"].loops:
                all_count += 1
                if l[uv_layer].select:
                    selected_count += 1

    return selected_count, all_count


@BlClassRegistry()
class MUV_OT_CopyPasteUVUVEdit_CopyUVIsland(bpy.types.Operator):
    """
    Operation class: Copy UV island on UV/Image Editor
    """

    bl_idname = "uv.muv_copy_paste_uv_uvedit_copy_uv_island"
    bl_label = "Copy UV Island (UV/Image Editor)"
    bl_description = "Copy UV island (only selected in UV/Image Editor)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    def execute(self, context):
        sc = context.scene
        props = sc.muv_props.copy_paste_uv_island

        props.src_data = []
        props.src_objects = []
        objs = common.get_uv_editable_objects(context)
        for obj in objs:
            bm = bmesh.from_edit_mesh(obj.data)
            uv_layer = bm.loops.layers.uv.verify()
            if common.check_version(2, 73, 0) >= 0:
                bm.verts.ensure_lookup_table()
                bm.edges.ensure_lookup_table()
                bm.faces.ensure_lookup_table()

            if context.tool_settings.use_uv_select_sync:
                islands = common.get_island_info_from_bmesh(
                    bm, only_selected=False)
            else:
                islands = common.get_island_info_from_bmesh(
                    bm, only_selected=True)
            for isl in islands:
                # Check if all UVs belonging to the island is selected.
                selected_count, all_count = get_counts(context, isl, uv_layer)
                if selected_count == 0:
                    continue
                if selected_count != all_count:
                    self.report(
                        {'WARNING'},
                        "All UVs belonging to the island must be selected")
                    return {'CANCELLED'}

                data = {
                    "bmesh": bm,
                    "uv_layer": uv_layer,
                    "island": isl
                }
                props.src_data.append(data)
            props.src_objects.append(obj)

        return {'FINISHED'}


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_CopyPasteUVUVEdit_PasteUVIsland(bpy.types.Operator):
    """
    Operation class: Paste UV island on UV/Image Editor
    """

    bl_idname = "uv.muv_copy_paste_uv_uvedit_paste_uv_island"
    bl_label = "Paste UV Island (UV/Image Editor)"
    bl_description = "Paste UV island (only selected in UV/Image Editor)"
    bl_options = {'REGISTER', 'UNDO'}

    unique_target = BoolProperty(
        name="Unique Target",
        description="Paste to the target uniquely",
        default=False
    )

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        sc = context.scene
        props = sc.muv_props.copy_paste_uv_island
        if not props.src_data:
            return False
        return _is_valid_context(context)

    def execute(self, context):
        sc = context.scene
        props = sc.muv_props.copy_paste_uv_island

        src_data = props.src_data
        src_objs = props.src_objects

        bms_and_uv_layers = {}
        for d in src_data:
            bms_and_uv_layers[d["bmesh"]] = d["uv_layer"]
        dst_data = []
        for bm, uv_layer in bms_and_uv_layers.items():
            if context.tool_settings.use_uv_select_sync:
                islands = common.get_island_info_from_bmesh(
                    bm, only_selected=False)
            else:
                islands = common.get_island_info_from_bmesh(
                    bm, only_selected=True)
            for isl in islands:
                # Check if all UVs belonging to the island is selected.
                selected_count, all_count = get_counts(context, isl, uv_layer)
                if selected_count == 0:
                    continue
                if selected_count != all_count:
                    self.report(
                        {'WARNING'},
                        "All UVs belonging to the island must be selected")
                    return {'CANCELLED'}

                dst_data.append(
                    {
                        "bm": bm,
                        "uv_layer": uv_layer,
                        "island": isl,
                    }
                )

        used = []
        for ddata in dst_data:
            dst_loops = []
            for f in ddata["island"]["faces"]:
                for l in f["face"].loops:
                    dst_loops.append(l)
            dst_uv_layer = ddata["uv_layer"]

            # Find a suitable island.
            for sdata in src_data:
                if self.unique_target and sdata in used:
                    continue

                src_loops = []
                for f in sdata["island"]["faces"]:
                    for l in f["face"].loops:
                        src_loops.append(l)
                src_uv_layer = sdata["uv_layer"]

                # Create UV graph.
                src_uv_graph = common.create_uv_graph(src_loops, src_uv_layer)
                dst_uv_graph = common.create_uv_graph(dst_loops, dst_uv_layer)

                # Check if the graph is isomorphic.
                # If the graph is isomorphic, matching pair is returned.
                result, pairs = graph_is_isomorphic(src_uv_graph, dst_uv_graph)
                if result:
                    # Paste UV island.
                    for n1, n2 in pairs.items():
                        uv1 = n1.value["uv_vert"][src_uv_layer].uv
                        l2 = n2.value["loops"]
                        for l in l2:
                            l[dst_uv_layer].uv = uv1
                    used.append(sdata)
                    break
            else:
                self.report({'WARNING'}, "Island does not match")
                return {'CANCELLED'}

        for obj in src_objs:
            bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}
