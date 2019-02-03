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

__author__ = "Keith (Wahooney) Boshoff, Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.0"
__date__ = "26 Jan 2019"

import bpy
from bpy.props import (
    EnumProperty,
    FloatProperty,
    BoolProperty,
)
import bmesh
from mathutils import Vector

from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry
from ..utils import compatibility as compat
from .. import common


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


def _is_vector_similar(v1, v2, error):
    """
    Check if two vectors are similar, within an error threshold
    """
    within_err_x = abs(v2.x - v1.x) < error
    within_err_y = abs(v2.y - v1.y) < error
    within_err_z = abs(v2.z - v1.z) < error

    return within_err_x and within_err_y and within_err_z


def _mirror_uvs(uv_layer, src, dst, axis, error):
    """
    Copy UV coordinates from one UV face to another
    """
    for sl in src.loops:
        suv = sl[uv_layer].uv.copy()
        svco = sl.vert.co.copy()
        for dl in dst.loops:
            dvco = dl.vert.co.copy()
            if axis == 'X':
                dvco.x = -dvco.x
            elif axis == 'Y':
                dvco.y = -dvco.y
            elif axis == 'Z':
                dvco.z = -dvco.z

            if _is_vector_similar(svco, dvco, error):
                dl[uv_layer].uv = suv.copy()


def _get_face_center(face):
    """
    Get center coordinate of the face
    """
    center = Vector((0.0, 0.0, 0.0))
    for v in face.verts:
        center = center + v.co

    return center / len(face.verts)


@PropertyClassRegistry()
class _Properties:
    idname = "mirror_uv"

    @classmethod
    def init_props(cls, scene):
        scene.muv_mirror_uv_enabled = BoolProperty(
            name="Mirror UV Enabled",
            description="Mirror UV is enabled",
            default=False
        )
        scene.muv_mirror_uv_axis = EnumProperty(
            items=[
                ('X', "X", "Mirror Along X axis"),
                ('Y', "Y", "Mirror Along Y axis"),
                ('Z', "Z", "Mirror Along Z axis")
            ],
            name="Axis",
            description="Mirror Axis",
            default='X'
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_mirror_uv_enabled
        del scene.muv_mirror_uv_axis


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_MirrorUV(bpy.types.Operator):
    """
    Operation class: Mirror UV
    """

    bl_idname = "uv.muv_ot_mirror_uv"
    bl_label = "Mirror UV"
    bl_options = {'REGISTER', 'UNDO'}

    axis = EnumProperty(
        items=(
            ('X', "X", "Mirror Along X axis"),
            ('Y', "Y", "Mirror Along Y axis"),
            ('Z', "Z", "Mirror Along Z axis")
        ),
        name="Axis",
        description="Mirror Axis",
        default='X'
    )
    error = FloatProperty(
        name="Error",
        description="Error threshold",
        default=0.001,
        min=0.0,
        max=100.0,
        soft_min=0.0,
        soft_max=1.0
    )

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    def execute(self, context):
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)

        error = self.error
        axis = self.axis

        if common.check_version(2, 73, 0) >= 0:
            bm.faces.ensure_lookup_table()
        if not bm.loops.layers.uv:
            self.report({'WARNING'},
                        "Object must have more than one UV map")
            return {'CANCELLED'}
        uv_layer = bm.loops.layers.uv.verify()

        faces = [f for f in bm.faces if f.select]
        for f_dst in faces:
            count = len(f_dst.verts)
            for f_src in bm.faces:
                # check if this is a candidate to do mirror UV
                if f_src.index == f_dst.index:
                    continue
                if count != len(f_src.verts):
                    continue

                # test if the vertices x values are the same sign
                dst = _get_face_center(f_dst)
                src = _get_face_center(f_src)
                if (dst.x > 0 and src.x > 0) or (dst.x < 0 and src.x < 0):
                    continue

                # invert source axis
                if axis == 'X':
                    src.x = -src.x
                elif axis == 'Y':
                    src.y = -src.z
                elif axis == 'Z':
                    src.z = -src.z

                # do mirror UV
                if _is_vector_similar(dst, src, error):
                    _mirror_uvs(uv_layer, f_src, f_dst, self.axis, self.error)

        bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}
