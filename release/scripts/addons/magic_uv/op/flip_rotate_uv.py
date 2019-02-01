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

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.0"
__date__ = "26 Jan 2019"

import bpy
import bmesh
from bpy.props import (
    BoolProperty,
    IntProperty,
)

from .. import common
from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry
from ..utils import compatibility as compat


def _is_valid_context(context):
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


def _get_uv_layer(ops_obj, bm):
    # get UV layer
    if not bm.loops.layers.uv:
        ops_obj.report({'WARNING'}, "Object must have more than one UV map")
        return None
    uv_layer = bm.loops.layers.uv.verify()

    return uv_layer


def _get_src_face_info(ops_obj, bm, uv_layers, only_select=False):
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


def _paste_uv(ops_obj, bm, src_info, dest_info, uv_layers, strategy, flip,
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


@PropertyClassRegistry()
class _Properties:
    idname = "flip_rotate_uv"

    @classmethod
    def init_props(cls, scene):
        scene.muv_flip_rotate_uv_enabled = BoolProperty(
            name="Flip/Rotate UV Enabled",
            description="Flip/Rotate UV is enabled",
            default=False
        )
        scene.muv_flip_rotate_uv_seams = BoolProperty(
            name="Seams",
            description="Seams",
            default=True
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_flip_rotate_uv_enabled
        del scene.muv_flip_rotate_uv_seams


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_FlipRotate(bpy.types.Operator):
    """
    Operation class: Flip and Rotate UV coordinate
    """

    bl_idname = "uv.muv_ot_flip_rotate_uv"
    bl_label = "Flip/Rotate UV"
    bl_description = "Flip/Rotate UV coordinate"
    bl_options = {'REGISTER', 'UNDO'}

    flip = BoolProperty(
        name="Flip UV",
        description="Flip UV...",
        default=False
    )
    rotate = IntProperty(
        default=0,
        name="Rotate UV",
        min=0,
        max=30
    )
    seams = BoolProperty(
        name="Seams",
        description="Seams",
        default=True
    )

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    def execute(self, context):
        self.report({'INFO'}, "Flip/Rotate UV")
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        if common.check_version(2, 73, 0) >= 0:
            bm.faces.ensure_lookup_table()

        # get UV layer
        uv_layer = _get_uv_layer(self, bm)
        if not uv_layer:
            return {'CANCELLED'}

        # get selected face
        src_info = _get_src_face_info(self, bm, [uv_layer], True)
        if not src_info:
            return {'CANCELLED'}

        face_count = len(src_info[list(src_info.keys())[0]])
        self.report({'INFO'}, "{} face(s) are selected".format(face_count))

        # paste
        ret = _paste_uv(self, bm, src_info, src_info, [uv_layer], 'N_N',
                        self.flip, self.rotate, self.seams)
        if ret:
            return {'CANCELLED'}

        bmesh.update_edit_mesh(obj.data)

        if compat.check_version(2, 80, 0) < 0:
            if self.seams is True:
                obj.data.show_edge_seams = True

        return {'FINISHED'}
