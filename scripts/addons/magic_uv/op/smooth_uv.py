# SPDX-FileCopyrightText: 2018-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "imdjs, Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"

import bpy
from bpy.props import BoolProperty, FloatProperty
import bmesh

from .. import common
from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry
from ..utils import compatibility as compat


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


@PropertyClassRegistry()
class _Properties:
    idname = "smooth_uv"

    @classmethod
    def init_props(cls, scene):
        scene.muv_smooth_uv_enabled = BoolProperty(
            name="Smooth UV Enabled",
            description="Smooth UV is enabled",
            default=False
        )
        scene.muv_smooth_uv_transmission = BoolProperty(
            name="Transmission",
            description="Smooth linked UVs",
            default=False
        )
        scene.muv_smooth_uv_mesh_infl = FloatProperty(
            name="Mesh Influence",
            description="Influence rate of mesh vertex",
            min=0.0,
            max=1.0,
            default=0.0
        )
        scene.muv_smooth_uv_select = BoolProperty(
            name="Select",
            description="Select UVs which are smoothed",
            default=False
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_smooth_uv_enabled
        del scene.muv_smooth_uv_transmission
        del scene.muv_smooth_uv_mesh_infl
        del scene.muv_smooth_uv_select


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_SmoothUV(bpy.types.Operator):

    bl_idname = "uv.muv_smooth_uv"
    bl_label = "Smooth"
    bl_description = "Smooth UV coordinates"
    bl_options = {'REGISTER', 'UNDO'}

    transmission = BoolProperty(
        name="Transmission",
        description="Smooth linked UVs",
        default=False
    )
    mesh_infl = FloatProperty(
        name="Mesh Influence",
        description="Influence rate of mesh vertex",
        min=0.0,
        max=1.0,
        default=0.0
    )
    select = BoolProperty(
        name="Select",
        description="Select UVs which are smoothed",
        default=False
    )

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    def __smooth_wo_transmission(self, loop_seqs, uv_layer):
        # calculate path length
        loops = []
        for hseq in loop_seqs:
            loops.extend([hseq[0][0], hseq[0][1]])
        full_vlen = 0
        accm_vlens = [0.0]
        full_uvlen = 0
        accm_uvlens = [0.0]
        orig_uvs = [loop_seqs[0][0][0][uv_layer].uv.copy()]
        for l1, l2 in zip(loops[:-1], loops[1:]):
            diff_v = l2.vert.co - l1.vert.co
            full_vlen = full_vlen + diff_v.length
            accm_vlens.append(full_vlen)
            diff_uv = l2[uv_layer].uv - l1[uv_layer].uv
            full_uvlen = full_uvlen + diff_uv.length
            accm_uvlens.append(full_uvlen)
            orig_uvs.append(l2[uv_layer].uv.copy())

        for hidx, hseq in enumerate(loop_seqs):
            pair = hseq[0]
            for pidx, l in enumerate(pair):
                if self.select:
                    l[uv_layer].select = True

                # ignore start/end loop
                if (hidx == 0 and pidx == 0) or\
                   ((hidx == len(loop_seqs) - 1) and (pidx == len(pair) - 1)):
                    continue

                # calculate target path length
                # target = no influenced * (1 - infl) + influenced * infl
                tgt_noinfl = full_uvlen * (hidx + pidx) / (len(loop_seqs))
                tgt_infl = full_uvlen * accm_vlens[hidx * 2 + pidx] / full_vlen
                target_length = tgt_noinfl * (1 - self.mesh_infl) + \
                    tgt_infl * self.mesh_infl

                # get target UV
                for i in range(len(accm_uvlens[:-1])):
                    # get line segment which UV will be placed
                    if accm_uvlens[i] <= target_length < accm_uvlens[i + 1]:
                        tgt_seg_len = target_length - accm_uvlens[i]
                        seg_len = accm_uvlens[i + 1] - accm_uvlens[i]
                        uv1 = orig_uvs[i]
                        uv2 = orig_uvs[i + 1]
                        target_uv = uv1 + (uv2 - uv1) * tgt_seg_len / seg_len
                        break
                else:
                    self.report({'ERROR'}, "Failed to get target UV")
                    return {'CANCELLED'}

                # update UV
                l[uv_layer].uv = target_uv

    def __smooth_w_transmission(self, loop_seqs, uv_layer):
        # calculate path length
        loops = []
        for vidx in range(len(loop_seqs[0])):
            ls = []
            for hseq in loop_seqs:
                ls.extend(hseq[vidx])
            loops.append(ls)

        orig_uvs = []
        accm_vlens = []
        full_vlens = []
        accm_uvlens = []
        full_uvlens = []
        for ls in loops:
            full_v = 0.0
            accm_v = [0.0]
            full_uv = 0.0
            accm_uv = [0.0]
            uvs = [ls[0][uv_layer].uv.copy()]
            for l1, l2 in zip(ls[:-1], ls[1:]):
                diff_v = l2.vert.co - l1.vert.co
                full_v = full_v + diff_v.length
                accm_v.append(full_v)
                diff_uv = l2[uv_layer].uv - l1[uv_layer].uv
                full_uv = full_uv + diff_uv.length
                accm_uv.append(full_uv)
                uvs.append(l2[uv_layer].uv.copy())
            accm_vlens.append(accm_v)
            full_vlens.append(full_v)
            accm_uvlens.append(accm_uv)
            full_uvlens.append(full_uv)
            orig_uvs.append(uvs)

        for hidx, hseq in enumerate(loop_seqs):
            for vidx, (pair, uvs, accm_v, full_v, accm_uv, full_uv)\
                    in enumerate(zip(hseq, orig_uvs, accm_vlens, full_vlens,
                                     accm_uvlens, full_uvlens)):
                for pidx, l in enumerate(pair):
                    if self.select:
                        l[uv_layer].select = True

                    # ignore start/end loop
                    if hidx == 0 and pidx == 0:
                        continue
                    if hidx == len(loop_seqs) - 1 and pidx == len(pair) - 1:
                        continue

                    # calculate target path length
                    # target = no influenced * (1 - infl) + influenced * infl
                    tgt_noinfl = full_uv * (hidx + pidx) / (len(loop_seqs))
                    tgt_infl = full_uv * accm_v[hidx * 2 + pidx] / full_v
                    target_length = tgt_noinfl * (1 - self.mesh_infl) + \
                        tgt_infl * self.mesh_infl

                    # get target UV
                    for i in range(len(accm_uv[:-1])):
                        # get line segment to be placed
                        if accm_uv[i] <= target_length < accm_uv[i + 1]:
                            tgt_seg_len = target_length - accm_uv[i]
                            seg_len = accm_uv[i + 1] - accm_uv[i]
                            uv1 = uvs[i]
                            uv2 = uvs[i + 1]
                            target_uv = uv1 +\
                                (uv2 - uv1) * tgt_seg_len / seg_len
                            break
                    else:
                        self.report({'ERROR'}, "Failed to get target UV")
                        return {'CANCELLED'}

                    # update UV
                    l[uv_layer].uv = target_uv

    def __smooth(self, loop_seqs, uv_layer):
        if self.transmission:
            self.__smooth_w_transmission(loop_seqs, uv_layer)
        else:
            self.__smooth_wo_transmission(loop_seqs, uv_layer)

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

            # smooth
            self.__smooth(loop_seqs, uv_layer)

            bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}
