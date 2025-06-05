# SPDX-FileCopyrightText: 2017-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Alexander Milovsky, Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"

from math import sin, cos, pi

import bpy
import bmesh
from bpy.props import (
    FloatProperty,
    FloatVectorProperty,
    BoolProperty,
    EnumProperty
)
from mathutils import Vector

from .. import common
from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry
from ..utils import compatibility as compat


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


def _get_uv_layer(ops_obj, bm, assign_uvmap):
    # get UV layer
    if not bm.loops.layers.uv:
        if assign_uvmap:
            bm.loops.layers.uv.new()
        else:
            ops_obj.report({'WARNING'},
                           "Object must have more than one UV map")
            return None
    uv_layer = bm.loops.layers.uv.verify()

    return uv_layer


def _apply_box_map(bm, uv_layer, size, offset, rotation,
                   tex_aspect, force_axis, force_axis_tex_aspect_correction,
                   force_axis_rotation):
    scale = 1.0 / size

    sx = 1.0 * scale
    sy = 1.0 * scale
    sz = 1.0 * scale
    ofx = offset[0]
    ofy = offset[1]
    ofz = offset[2]
    rx = rotation[0] * pi / 180.0
    ry = rotation[1] * pi / 180.0
    rz = rotation[2] * pi / 180.0

    farx = force_axis_rotation[0] * pi / 180.0
    fary = force_axis_rotation[1] * pi / 180.0
    farz = force_axis_rotation[2] * pi / 180.0

    sel_faces = [f for f in bm.faces if f.select]

    # update UV coordinate
    for f in sel_faces:
        n = f.normal
        for l in f.loops:
            co = l.vert.co
            x = co.x * sx
            y = co.y * sy
            z = co.z * sz
            aspect = tex_aspect

            transformed = False
            if force_axis == 'X':
                # Use Y-plane
                if abs(n[1]) < abs(n[0]) and abs(n[1]) >= abs(n[2]):
                    aspect *= force_axis_tex_aspect_correction
                    if n[1] >= 0.0:
                        u = -(x - ofx) * cos(fary) + (z - ofz) * sin(fary)
                        v = (x * aspect - ofx) * sin(fary) + \
                            (z * aspect - ofz) * cos(fary)
                    else:
                        u = (x - ofx) * cos(fary) + (z - ofz) * sin(fary)
                        v = -(x * aspect - ofx) * sin(fary) + \
                            (z * aspect - ofz) * cos(fary)
                    transformed = True
                # Use Z-plane
                elif abs(n[2]) < abs(n[0]) and abs(n[2]) >= abs(n[1]):
                    aspect *= force_axis_tex_aspect_correction
                    if n[2] >= 0.0:
                        u = (x - ofx) * cos(farz) + (y - ofy) * sin(farz)
                        v = -(x * aspect - ofx) * sin(farz) + \
                            (y * aspect - ofy) * cos(farz)
                    else:
                        u = -(x - ofx) * cos(farz) - (y + ofy) * sin(farz)
                        v = -(x * aspect + ofx) * sin(farz) + \
                            (y * aspect - ofy) * cos(farz)
                    transformed = True
            elif force_axis == 'Y':
                # Use X-plane
                if abs(n[0]) < abs(n[1]) and abs(n[0]) >= abs(n[2]):
                    aspect *= force_axis_tex_aspect_correction
                    if n[0] >= 0.0:
                        u = (y - ofy) * cos(farx) + (z - ofz) * sin(farx)
                        v = -(y * aspect - ofy) * sin(farx) + \
                            (z * aspect - ofz) * cos(farx)
                    else:
                        u = -(y - ofy) * cos(farx) + (z - ofz) * sin(farx)
                        v = (y * aspect - ofy) * sin(farx) + \
                            (z * aspect - ofz) * cos(farx)
                    transformed = True
                # Use Z-plane
                elif abs(n[2]) >= abs(n[0]) and abs(n[2]) < abs(n[1]):
                    aspect *= force_axis_tex_aspect_correction
                    if n[2] >= 0.0:
                        u = (x - ofx) * cos(farz) + (y - ofy) * sin(farz)
                        v = -(x * aspect - ofx) * sin(farz) + \
                            (y * aspect - ofy) * cos(farz)
                    else:
                        u = -(x - ofx) * cos(farz) - (y + ofy) * sin(farz)
                        v = -(x * aspect + ofx) * sin(farz) + \
                            (y * aspect - ofy) * cos(farz)
                    transformed = True
            elif force_axis == 'Z':
                # Use X-plane
                if abs(n[0]) >= abs(n[1]) and abs(n[0]) < abs(n[2]):
                    aspect *= force_axis_tex_aspect_correction
                    if n[0] >= 0.0:
                        u = (y - ofy) * cos(farx) + (z - ofz) * sin(farx)
                        v = -(y * aspect - ofy) * sin(farx) + \
                            (z * aspect - ofz) * cos(farx)
                    else:
                        u = -(y - ofy) * cos(farx) + (z - ofz) * sin(farx)
                        v = (y * aspect - ofy) * sin(farx) + \
                            (z * aspect - ofz) * cos(farx)
                    transformed = True
                # Use Y-plane
                elif abs(n[1]) >= abs(n[0]) and abs(n[1]) < abs(n[2]):
                    aspect *= force_axis_tex_aspect_correction
                    if n[1] >= 0.0:
                        u = -(x - ofx) * cos(fary) + (z - ofz) * sin(fary)
                        v = (x * aspect - ofx) * sin(fary) + \
                            (z * aspect - ofz) * cos(fary)
                    else:
                        u = (x - ofx) * cos(fary) + (z - ofz) * sin(fary)
                        v = -(x * aspect - ofx) * sin(fary) + \
                            (z * aspect - ofz) * cos(fary)
                    transformed = True

            if not transformed:
                # X-plane
                if abs(n[0]) >= abs(n[1]) and abs(n[0]) >= abs(n[2]):
                    if n[0] >= 0.0:
                        u = (y - ofy) * cos(rx) + (z - ofz) * sin(rx)
                        v = -(y * aspect - ofy) * sin(rx) + \
                            (z * aspect - ofz) * cos(rx)
                    else:
                        u = -(y - ofy) * cos(rx) + (z - ofz) * sin(rx)
                        v = (y * aspect - ofy) * sin(rx) + \
                            (z * aspect - ofz) * cos(rx)
                # Y-plane
                elif abs(n[1]) >= abs(n[0]) and abs(n[1]) >= abs(n[2]):
                    if n[1] >= 0.0:
                        u = -(x - ofx) * cos(ry) + (z - ofz) * sin(ry)
                        v = (x * aspect - ofx) * sin(ry) + \
                            (z * aspect - ofz) * cos(ry)
                    else:
                        u = (x - ofx) * cos(ry) + (z - ofz) * sin(ry)
                        v = -(x * aspect - ofx) * sin(ry) + \
                            (z * aspect - ofz) * cos(ry)
                # Z-plane
                elif abs(n[2]) >= abs(n[0]) and abs(n[2]) >= abs(n[1]):
                    if n[2] >= 0.0:
                        u = (x - ofx) * cos(rz) + (y - ofy) * sin(rz)
                        v = -(x * aspect - ofx) * sin(rz) + \
                            (y * aspect - ofy) * cos(rz)
                    else:
                        u = -(x - ofx) * cos(rz) - (y + ofy) * sin(rz)
                        v = -(x * aspect + ofx) * sin(rz) + \
                            (y * aspect - ofy) * cos(rz)

            l[uv_layer].uv = Vector((u, v))


def _apply_planer_map(bm, uv_layer, size, offset, rotation, tex_aspect):
    scale = 1.0 / size

    sx = 1.0 * scale
    sy = 1.0 * scale
    ofx = offset[0]
    ofy = offset[1]
    rz = rotation * pi / 180.0
    aspect = tex_aspect

    sel_faces = [f for f in bm.faces if f.select]

    # calculate average of normal
    n_ave = Vector((0.0, 0.0, 0.0))
    for f in sel_faces:
        n_ave = n_ave + f.normal
    q = n_ave.rotation_difference(Vector((0.0, 0.0, 1.0)))

    # update UV coordinate
    for f in sel_faces:
        for l in f.loops:
            co = compat.matmul(q, l.vert.co)
            x = co.x * sx
            y = co.y * sy

            u = x * cos(rz) - y * sin(rz) + ofx
            v = -x * aspect * sin(rz) - y * aspect * cos(rz) + ofy

            l[uv_layer].uv = Vector((u, v))


@PropertyClassRegistry()
class _Properties:
    idname = "uvw"

    @classmethod
    def init_props(cls, scene):
        scene.muv_uvw_enabled = BoolProperty(
            name="UVW Enabled",
            description="UVW is enabled",
            default=False
        )
        scene.muv_uvw_assign_uvmap = BoolProperty(
            name="Assign UVMap",
            description="Assign UVMap when no UVmaps are available",
            default=True
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_uvw_enabled
        del scene.muv_uvw_assign_uvmap


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_UVW_BoxMap(bpy.types.Operator):
    bl_idname = "uv.muv_uvw_box_map"
    bl_label = "Box Map"
    bl_options = {'REGISTER', 'UNDO'}

    size = FloatProperty(
        name="Size",
        default=1.0,
        precision=4
    )
    rotation = FloatVectorProperty(
        name="Rotation",
        size=3,
        default=(0.0, 0.0, 0.0),
        subtype='XYZ'
    )
    offset = FloatVectorProperty(
        name="Offset",
        size=3,
        default=(0.0, 0.0, 0.0),
        subtype='XYZ'
    )
    tex_aspect = FloatProperty(
        name="Texture Aspect",
        default=1.0,
        precision=4
    )
    assign_uvmap = BoolProperty(
        name="Assign UVMap",
        description="Assign UVMap when no UVmaps are available",
        default=True
    )
    force_axis = EnumProperty(
        name="Force Axis",
        description="Axis to force the mapping",
        items=[
            ('NONE', "None", "None"),
            ('X', "X", "Axis X"),
            ('Y', "Y", "Axis Y"),
            ('Z', "Z", "Axis Z")
        ],
        default='NONE'
    )
    force_axis_tex_aspect_correction = FloatProperty(
        name="Texture Aspect Correction (Force Axis)",
        description="Texture Aspect correction for the faces mapped forcibly",
        default=3.14,
        precision=4
    )
    force_axis_rotation = FloatVectorProperty(
        name="Rotation (Force Axis)",
        description="Rotation for the faces mapped forcibly",
        size=3,
        default=(0.0, 0.0, 0.0),
        subtype='XYZ'
    )

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    def draw(self, _):
        layout = self.layout

        col = layout.column()
        row = col.row()
        row.label(text="Size:")
        row.prop(self, "size", text="")

        layout.label(text="Rotation:")
        layout.row().prop(self, "rotation", text="")

        layout.label(text="Offset:")
        layout.row().prop(self, "offset", text="")

        col = layout.column()
        row = col.row()
        row.label(text="Texture Aspect:")
        row.prop(self, "tex_aspect", text="")

        layout.prop(self, "assign_uvmap")

        layout.separator(factor=2.0)

        layout.prop(self, "force_axis")
        if self.force_axis != 'NONE':
            col = layout.column()
            row = col.row()
            row.label(text="Texture Aspect Correction (Force Axis)")
            row.prop(self, "force_axis_tex_aspect_correction", text="")

            layout.label(text="Rotation (Force Axis)")
            layout.row().prop(self, "force_axis_rotation", text="")

    def execute(self, context):
        objs = common.get_uv_editable_objects(context)

        for obj in objs:
            bm = bmesh.from_edit_mesh(obj.data)
            if common.check_version(2, 73, 0) >= 0:
                bm.faces.ensure_lookup_table()

            # get UV layer
            uv_layer = _get_uv_layer(self, bm, self.assign_uvmap)
            if not uv_layer:
                return {'CANCELLED'}

            _apply_box_map(bm, uv_layer, self.size, self.offset, self.rotation,
                           self.tex_aspect, self.force_axis,
                           self.force_axis_tex_aspect_correction,
                           self.force_axis_rotation)
            bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_UVW_BestPlanerMap(bpy.types.Operator):
    bl_idname = "uv.muv_uvw_best_planer_map"
    bl_label = "Best Planer Map"
    bl_options = {'REGISTER', 'UNDO'}

    size = FloatProperty(
        name="Size",
        default=1.0,
        precision=4
    )
    rotation = FloatProperty(
        name="Rotation",
        default=0.0
    )
    offset = FloatVectorProperty(
        name="Offset",
        size=2,
        default=(0.0, 0.0)
    )
    tex_aspect = FloatProperty(
        name="Texture Aspect",
        default=1.0,
        precision=4
    )
    assign_uvmap = BoolProperty(
        name="Assign UVMap",
        description="Assign UVMap when no UVmaps are available",
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

        for obj in objs:
            bm = bmesh.from_edit_mesh(obj.data)
            if common.check_version(2, 73, 0) >= 0:
                bm.faces.ensure_lookup_table()

            # get UV layer
            uv_layer = _get_uv_layer(self, bm, self.assign_uvmap)
            if not uv_layer:
                return {'CANCELLED'}

            _apply_planer_map(bm, uv_layer, self.size, self.offset,
                              self.rotation, self.tex_aspect)

            bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}
