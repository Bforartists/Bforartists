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

__author__ = "McBuff, Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "5.2"
__date__ = "17 Nov 2018"

from math import sqrt

import bmesh
from mathutils import Vector

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


def _measure_wsuv_info(obj, tex_size=None):
    mesh_area = common.measure_mesh_area(obj)
    if common.check_version(2, 80, 0) >= 0:
        uv_area = common.measure_uv_area(obj, tex_size)
    else:
        uv_area = common.measure_uv_area_legacy(obj, tex_size)

    if not uv_area:
        return None, mesh_area, None

    if mesh_area == 0.0:
        density = 0.0
    else:
        density = sqrt(uv_area) / sqrt(mesh_area)

    return uv_area, mesh_area, density


def _apply(obj, origin, factor):
    bm = bmesh.from_edit_mesh(obj.data)
    if common.check_version(2, 73, 0) >= 0:
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

    sel_faces = [f for f in bm.faces if f.select]

    uv_layer = bm.loops.layers.uv.verify()

    # calculate origin
    if origin == 'CENTER':
        origin = Vector((0.0, 0.0))
        num = 0
        for f in sel_faces:
            for l in f.loops:
                uv = l[uv_layer].uv
                origin = origin + uv
                num = num + 1
        origin = origin / num
    elif origin == 'LEFT_TOP':
        origin = Vector((100000.0, -100000.0))
        for f in sel_faces:
            for l in f.loops:
                uv = l[uv_layer].uv
                origin.x = min(origin.x, uv.x)
                origin.y = max(origin.y, uv.y)
    elif origin == 'LEFT_CENTER':
        origin = Vector((100000.0, 0.0))
        num = 0
        for f in sel_faces:
            for l in f.loops:
                uv = l[uv_layer].uv
                origin.x = min(origin.x, uv.x)
                origin.y = origin.y + uv.y
                num = num + 1
        origin.y = origin.y / num
    elif origin == 'LEFT_BOTTOM':
        origin = Vector((100000.0, 100000.0))
        for f in sel_faces:
            for l in f.loops:
                uv = l[uv_layer].uv
                origin.x = min(origin.x, uv.x)
                origin.y = min(origin.y, uv.y)
    elif origin == 'CENTER_TOP':
        origin = Vector((0.0, -100000.0))
        num = 0
        for f in sel_faces:
            for l in f.loops:
                uv = l[uv_layer].uv
                origin.x = origin.x + uv.x
                origin.y = max(origin.y, uv.y)
                num = num + 1
        origin.x = origin.x / num
    elif origin == 'CENTER_BOTTOM':
        origin = Vector((0.0, 100000.0))
        num = 0
        for f in sel_faces:
            for l in f.loops:
                uv = l[uv_layer].uv
                origin.x = origin.x + uv.x
                origin.y = min(origin.y, uv.y)
                num = num + 1
        origin.x = origin.x / num
    elif origin == 'RIGHT_TOP':
        origin = Vector((-100000.0, -100000.0))
        for f in sel_faces:
            for l in f.loops:
                uv = l[uv_layer].uv
                origin.x = max(origin.x, uv.x)
                origin.y = max(origin.y, uv.y)
    elif origin == 'RIGHT_CENTER':
        origin = Vector((-100000.0, 0.0))
        num = 0
        for f in sel_faces:
            for l in f.loops:
                uv = l[uv_layer].uv
                origin.x = max(origin.x, uv.x)
                origin.y = origin.y + uv.y
                num = num + 1
        origin.y = origin.y / num
    elif origin == 'RIGHT_BOTTOM':
        origin = Vector((-100000.0, 100000.0))
        for f in sel_faces:
            for l in f.loops:
                uv = l[uv_layer].uv
                origin.x = max(origin.x, uv.x)
                origin.y = min(origin.y, uv.y)

    # update UV coordinate
    for f in sel_faces:
        for l in f.loops:
            uv = l[uv_layer].uv
            diff = uv - origin
            l[uv_layer].uv = origin + diff * factor

    bmesh.update_edit_mesh(obj.data)


class MeasureImpl:
    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    def execute(self, ops_obj, context):
        sc = context.scene
        obj = context.active_object

        uv_area, mesh_area, density = _measure_wsuv_info(obj)
        if not uv_area:
            ops_obj.report({'WARNING'},
                           "Object must have more than one UV map and texture")
            return {'CANCELLED'}

        sc.muv_world_scale_uv_src_uv_area = uv_area
        sc.muv_world_scale_uv_src_mesh_area = mesh_area
        sc.muv_world_scale_uv_src_density = density

        ops_obj.report({'INFO'},
                       "UV Area: {0}, Mesh Area: {1}, Texel Density: {2}"
                       .format(uv_area, mesh_area, density))

        return {'FINISHED'}


class ApplyManualImpl:
    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    def __apply_manual(self, ops_obj, context):
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        if common.check_version(2, 73, 0) >= 0:
            bm.verts.ensure_lookup_table()
            bm.edges.ensure_lookup_table()
            bm.faces.ensure_lookup_table()

        tex_size = ops_obj.tgt_texture_size
        uv_area, _, density = _measure_wsuv_info(obj, tex_size)
        if not uv_area:
            ops_obj.report({'WARNING'},
                           "Object must have more than one UV map")
            return {'CANCELLED'}

        tgt_density = ops_obj.tgt_density
        factor = tgt_density / density

        _apply(context.active_object, ops_obj.origin, factor)
        ops_obj.report({'INFO'}, "Scaling factor: {0}".format(factor))

        return {'FINISHED'}

    def draw(self, ops_obj, _):
        layout = ops_obj.layout

        layout.prop(ops_obj, "tgt_density")
        layout.prop(ops_obj, "tgt_texture_size")
        layout.prop(ops_obj, "origin")

        layout.separator()

    def invoke(self, ops_obj, context, _):
        if ops_obj.show_dialog:
            wm = context.window_manager
            return wm.invoke_props_dialog(ops_obj)

        return ops_obj.execute(context)

    def execute(self, ops_obj, context):
        return self.__apply_manual(ops_obj, context)


class ApplyScalingDensityImpl:
    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    def __apply_scaling_density(self, ops_obj, context):
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        if common.check_version(2, 73, 0) >= 0:
            bm.verts.ensure_lookup_table()
            bm.edges.ensure_lookup_table()
            bm.faces.ensure_lookup_table()

        uv_area, _, density = _measure_wsuv_info(obj)
        if not uv_area:
            ops_obj.report({'WARNING'},
                           "Object must have more than one UV map and texture")
            return {'CANCELLED'}

        tgt_density = ops_obj.src_density * ops_obj.tgt_scaling_factor
        factor = tgt_density / density

        _apply(context.active_object, ops_obj.origin, factor)
        ops_obj.report({'INFO'}, "Scaling factor: {0}".format(factor))

        return {'FINISHED'}

    def draw(self, ops_obj, _):
        layout = ops_obj.layout

        layout.label(text="Source:")
        col = layout.column()
        col.prop(ops_obj, "src_density")
        col.enabled = False

        layout.separator()

        if not ops_obj.same_density:
            layout.prop(ops_obj, "tgt_scaling_factor")
        layout.prop(ops_obj, "origin")

        layout.separator()

    def invoke(self, ops_obj, context, _):
        sc = context.scene

        if ops_obj.show_dialog:
            wm = context.window_manager

            if ops_obj.same_density:
                ops_obj.tgt_scaling_factor = 1.0
            else:
                ops_obj.tgt_scaling_factor = \
                    sc.muv_world_scale_uv_tgt_scaling_factor
                ops_obj.src_density = sc.muv_world_scale_uv_src_density

            return wm.invoke_props_dialog(ops_obj)

        return ops_obj.execute(context)

    def execute(self, ops_obj, context):
        if ops_obj.same_density:
            ops_obj.tgt_scaling_factor = 1.0

        return self.__apply_scaling_density(ops_obj, context)


class ApplyProportionalToMeshImpl:
    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    def __apply_proportional_to_mesh(self, ops_obj, context):
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        if common.check_version(2, 73, 0) >= 0:
            bm.verts.ensure_lookup_table()
            bm.edges.ensure_lookup_table()
            bm.faces.ensure_lookup_table()

        uv_area, mesh_area, density = _measure_wsuv_info(obj)
        if not uv_area:
            ops_obj.report({'WARNING'},
                           "Object must have more than one UV map and texture")
            return {'CANCELLED'}

        tgt_density = ops_obj.src_density * sqrt(mesh_area) / sqrt(
            ops_obj.src_mesh_area)

        factor = tgt_density / density

        _apply(context.active_object, ops_obj.origin, factor)
        ops_obj.report({'INFO'}, "Scaling factor: {0}".format(factor))

        return {'FINISHED'}

    def draw(self, ops_obj, _):
        layout = ops_obj.layout

        layout.label(text="Source:")
        col = layout.column(align=True)
        col.prop(ops_obj, "src_density")
        col.prop(ops_obj, "src_uv_area")
        col.prop(ops_obj, "src_mesh_area")
        col.enabled = False

        layout.separator()
        layout.prop(ops_obj, "origin")

        layout.separator()

    def invoke(self, ops_obj, context, _):
        if ops_obj.show_dialog:
            wm = context.window_manager
            sc = context.scene

            ops_obj.src_density = sc.muv_world_scale_uv_src_density
            ops_obj.src_mesh_area = sc.muv_world_scale_uv_src_mesh_area

            return wm.invoke_props_dialog(ops_obj)

        return ops_obj.execute(context)

    def execute(self, ops_obj, context):
        return self.__apply_proportional_to_mesh(ops_obj, context)
