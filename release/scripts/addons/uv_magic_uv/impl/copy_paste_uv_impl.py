# <pep8-80 compliant>

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

__author__ = "imdjs, Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "5.2"
__date__ = "17 Nov 2018"


import bmesh

from .. import common


__all__ = [
    'is_valid_context',
    'get_copy_uv_layers',
    'get_paste_uv_layers',
    'get_src_face_info',
    'get_dest_face_info',
    'get_select_history_src_face_info',
    'get_select_history_dest_face_info',
    'paste_uv',
]


def is_valid_context(context):
    obj = context.object

    # only edit mode is allowed to execute
    if obj is None:
        return False
    if obj.type != 'MESH':
        return False
    if context.object.mode != 'EDIT':
        return False

    # only 'VIEW_3D' space is allowed to execute
    for space in context.area.spaces:
        if space.type == 'VIEW_3D':
            break
    else:
        return False

    return True


def get_copy_uv_layers(ops_obj, bm, uv_map):
    uv_layers = []
    if uv_map == "__default":
        if not bm.loops.layers.uv:
            ops_obj.report(
                {'WARNING'}, "Object must have more than one UV map")
            return None
        uv_layers.append(bm.loops.layers.uv.verify())
        ops_obj.report({'INFO'}, "Copy UV coordinate")
    elif uv_map == "__all":
        for uv in bm.loops.layers.uv.keys():
            uv_layers.append(bm.loops.layers.uv[uv])
        ops_obj.report({'INFO'}, "Copy UV coordinate (UV map: ALL)")
    else:
        uv_layers.append(bm.loops.layers.uv[uv_map])
        ops_obj.report(
            {'INFO'}, "Copy UV coordinate (UV map:{})".format(uv_map))

    return uv_layers


def get_paste_uv_layers(ops_obj, obj, bm, src_info, uv_map):
    uv_layers = []
    if uv_map == "__default":
        if not bm.loops.layers.uv:
            ops_obj.report(
                {'WARNING'}, "Object must have more than one UV map")
            return None
        uv_layers.append(bm.loops.layers.uv.verify())
        ops_obj.report({'INFO'}, "Paste UV coordinate")
    elif uv_map == "__new":
        new_uv_map = common.create_new_uv_map(obj)
        if not new_uv_map:
            ops_obj.report({'WARNING'},
                           "Reached to the maximum number of UV map")
            return None
        uv_layers.append(bm.loops.layers.uv[new_uv_map.name])
        ops_obj.report(
            {'INFO'}, "Paste UV coordinate (UV map:{})".format(new_uv_map))
    elif uv_map == "__all":
        for src_layer in src_info.keys():
            if src_layer not in bm.loops.layers.uv.keys():
                new_uv_map = common.create_new_uv_map(obj, src_layer)
                if not new_uv_map:
                    ops_obj.report({'WARNING'},
                                   "Reached to the maximum number of UV map")
                    return None
            uv_layers.append(bm.loops.layers.uv[src_layer])
        ops_obj.report({'INFO'}, "Paste UV coordinate (UV map: ALL)")
    else:
        uv_layers.append(bm.loops.layers.uv[uv_map])
        ops_obj.report(
            {'INFO'}, "Paste UV coordinate (UV map:{})".format(uv_map))

    return uv_layers


def get_src_face_info(ops_obj, bm, uv_layers, only_select=False):
    src_info = {}
    for layer in uv_layers:
        face_info = []
        for face in bm.faces:
            if not only_select or face.select:
                info = {
                    "index": face.index,
                    "uvs": [l[layer].uv.copy() for l in face.loops],
                    "pin_uvs": [l[layer].pin_uv for l in face.loops],
                    "seams": [l.edge.seam for l in face.loops],
                }
                face_info.append(info)
        if not face_info:
            ops_obj.report({'WARNING'}, "No faces are selected")
            return None
        src_info[layer.name] = face_info

    return src_info


def get_dest_face_info(ops_obj, bm, uv_layers, src_info, strategy,
                       only_select=False):
    dest_info = {}
    for layer in uv_layers:
        face_info = []
        for face in bm.faces:
            if not only_select or face.select:
                info = {
                    "index": face.index,
                    "uvs": [l[layer].uv.copy() for l in face.loops],
                }
                face_info.append(info)
        if not face_info:
            ops_obj.report({'WARNING'}, "No faces are selected")
            return None
        key = list(src_info.keys())[0]
        src_face_count = len(src_info[key])
        dest_face_count = len(face_info)
        if strategy == 'N_N' and src_face_count != dest_face_count:
            ops_obj.report(
                {'WARNING'},
                "Number of selected faces is different from copied" +
                "(src:{}, dest:{})"
                .format(src_face_count, dest_face_count))
            return None
        dest_info[layer.name] = face_info

    return dest_info


def get_select_history_src_face_info(ops_obj, bm, uv_layers):
    src_info = {}
    for layer in uv_layers:
        face_info = []
        for hist in bm.select_history:
            if isinstance(hist, bmesh.types.BMFace) and hist.select:
                info = {
                    "index": hist.index,
                    "uvs": [l[layer].uv.copy() for l in hist.loops],
                    "pin_uvs": [l[layer].pin_uv for l in hist.loops],
                    "seams": [l.edge.seam for l in hist.loops],
                }
                face_info.append(info)
        if not face_info:
            ops_obj.report({'WARNING'}, "No faces are selected")
            return None
        src_info[layer.name] = face_info

    return src_info


def get_select_history_dest_face_info(ops_obj, bm, uv_layers, src_info,
                                      strategy):
    dest_info = {}
    for layer in uv_layers:
        face_info = []
        for hist in bm.select_history:
            if isinstance(hist, bmesh.types.BMFace) and hist.select:
                info = {
                    "index": hist.index,
                    "uvs": [l[layer].uv.copy() for l in hist.loops],
                }
                face_info.append(info)
        if not face_info:
            ops_obj.report({'WARNING'}, "No faces are selected")
            return None
        key = list(src_info.keys())[0]
        src_face_count = len(src_info[key])
        dest_face_count = len(face_info)
        if strategy == 'N_N' and src_face_count != dest_face_count:
            ops_obj.report(
                {'WARNING'},
                "Number of selected faces is different from copied" +
                "(src:{}, dest:{})"
                .format(src_face_count, dest_face_count))
            return None
        dest_info[layer.name] = face_info

    return dest_info


def paste_uv(ops_obj, bm, src_info, dest_info, uv_layers, strategy, flip,
             rotate, copy_seams):
    for slayer_name, dlayer in zip(src_info.keys(), uv_layers):
        src_faces = src_info[slayer_name]
        dest_faces = dest_info[dlayer.name]

        for idx, dinfo in enumerate(dest_faces):
            sinfo = None
            if strategy == 'N_N':
                sinfo = src_faces[idx]
            elif strategy == 'N_M':
                sinfo = src_faces[idx % len(src_faces)]

            suv = sinfo["uvs"]
            spuv = sinfo["pin_uvs"]
            ss = sinfo["seams"]
            if len(sinfo["uvs"]) != len(dinfo["uvs"]):
                ops_obj.report({'WARNING'}, "Some faces are different size")
                return -1

            suvs_fr = [uv for uv in suv]
            spuvs_fr = [pin_uv for pin_uv in spuv]
            ss_fr = [s for s in ss]

            # flip UVs
            if flip is True:
                suvs_fr.reverse()
                spuvs_fr.reverse()
                ss_fr.reverse()

            # rotate UVs
            for _ in range(rotate):
                uv = suvs_fr.pop()
                pin_uv = spuvs_fr.pop()
                s = ss_fr.pop()
                suvs_fr.insert(0, uv)
                spuvs_fr.insert(0, pin_uv)
                ss_fr.insert(0, s)

            # paste UVs
            for l, suv, spuv, ss in zip(bm.faces[dinfo["index"]].loops,
                                        suvs_fr, spuvs_fr, ss_fr):
                l[dlayer].uv = suv
                l[dlayer].pin_uv = spuv
                if copy_seams is True:
                    l.edge.seam = ss

    return 0
