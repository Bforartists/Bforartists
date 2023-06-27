# SPDX-FileCopyrightText: 2017-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Keith (Wahooney) Boshoff, Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"

import bpy
from bpy.props import (
    EnumProperty,
    FloatProperty,
    BoolProperty,
)
import bmesh
from mathutils import Vector, Euler

from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry
from ..utils import compatibility as compat
from .. import common


def _is_valid_context(context):
    # only 'VIEW_3D' space is allowed to execute
    if not common.is_valid_space(context, ['VIEW_3D']):
        return False

    objs = common.get_uv_editable_objects(context)
    if not objs:
        return False

    # only edit mode is allowed to execute
    if context.object.mode != 'EDIT':
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


def _mirror_uvs(uv_layer, src, dst, axis, error, transformed):
    """
    Copy UV coordinates from one UV face to another
    """
    for sl in src.loops:
        suv = sl[uv_layer].uv.copy()
        svco = transformed[sl.vert].copy()
        for dl in dst.loops:
            dvco = transformed[dl.vert].copy()
            if axis == 'X':
                dvco.x = -dvco.x
            elif axis == 'Y':
                dvco.y = -dvco.y
            elif axis == 'Z':
                dvco.z = -dvco.z

            if _is_vector_similar(svco, dvco, error):
                dl[uv_layer].uv = suv.copy()


def _get_face_center(face, transformed):
    """
    Get center coordinate of the face
    """
    center = Vector((0.0, 0.0, 0.0))
    for v in face.verts:
        tv = transformed[v]
        center = center + tv

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
        scene.muv_mirror_uv_origin = EnumProperty(
            items=(
                ('WORLD', "World", "World"),
                ("GLOBAL", "Global", "Global"),
                ('LOCAL', "Local", "Local"),
            ),
            name="Origin",
            description="Origin of the mirror operation",
            default='LOCAL'
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_mirror_uv_enabled
        del scene.muv_mirror_uv_axis
        del scene.muv_mirror_uv_origin


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_MirrorUV(bpy.types.Operator):
    """
    Operation class: Mirror UV
    """

    bl_idname = "uv.muv_mirror_uv"
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
    origin = EnumProperty(
        items=(
            ('WORLD', "World", "World"),
            ("GLOBAL", "Global", "Global"),
            ('LOCAL', "Local", "Local"),
        ),
        name="Origin",
        description="Origin of the mirror operation",
        default='LOCAL'
    )

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    def _get_world_vertices(self, obj, bm):
        # Get world orientation matrix.
        world_orientation_mat = obj.matrix_world

        # Move to local to world.
        transformed = {}
        for v in bm.verts:
            transformed[v] = compat.matmul(world_orientation_mat, v.co)

        return transformed

    def _get_global_vertices(self, obj, bm):
        # Get world rotation matrix.
        eular = Euler(obj.rotation_euler)
        rotation_mat = eular.to_matrix()

        # Get center location of all vertices.
        center_location = Vector((0.0, 0.0, 0.0))
        for v in bm.verts:
            center_location += v.co
        center_location /= len(bm.verts)

        # Move to local to global.
        transformed = {}
        for v in bm.verts:
            transformed[v] = compat.matmul(rotation_mat, v.co)
            transformed[v] -= center_location

        return transformed

    def _get_local_vertices(self, _, bm):
        transformed = {}

        # Get center location of all vertices.
        center_location = Vector((0.0, 0.0, 0.0))
        for v in bm.verts:
            center_location += v.co
        center_location /= len(bm.verts)

        for v in bm.verts:
            transformed[v] = v.co.copy()
            transformed[v] -= center_location

        return transformed

    def execute(self, context):
        objs = common.get_uv_editable_objects(context)

        for obj in objs:
            bm = bmesh.from_edit_mesh(obj.data)

            error = self.error
            axis = self.axis

            if common.check_version(2, 73, 0) >= 0:
                bm.faces.ensure_lookup_table()
            if not bm.loops.layers.uv:
                self.report({'WARNING'},
                            "Object {} must have more than one UV map"
                            .format(obj.name))
                return {'CANCELLED'}
            uv_layer = bm.loops.layers.uv.verify()

            if self.origin == 'WORLD':
                transformed_verts = self._get_world_vertices(obj, bm)
            elif self.origin == 'GLOBAL':
                transformed_verts = self._get_global_vertices(obj, bm)
            elif self.origin == 'LOCAL':
                transformed_verts = self._get_local_vertices(obj, bm)

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
                    dst = _get_face_center(f_dst, transformed_verts)
                    src = _get_face_center(f_src, transformed_verts)

                    # invert source axis
                    if axis == 'X':
                        if ((dst.x > 0 and src.x > 0) or
                                (dst.x < 0 and src.x < 0)):
                            continue
                        src.x = -src.x
                    elif axis == 'Y':
                        if ((dst.y > 0 and src.y > 0) or
                                (dst.y < 0 and src.y < 0)):
                            continue
                        src.y = -src.y
                    elif axis == 'Z':
                        if ((dst.z > 0 and src.z > 0) or
                                (dst.z < 0 and src.z < 0)):
                            continue
                        src.z = -src.z

                    # do mirror UV
                    if _is_vector_similar(dst, src, error):
                        _mirror_uvs(uv_layer, f_src, f_dst,
                                    self.axis, self.error, transformed_verts)

            bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}
