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

__author__ = "Alexander Milovsky, Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "5.2"
__date__ = "17 Nov 2018"

import bpy
import bmesh
from bpy.props import (
    FloatProperty,
    FloatVectorProperty,
    BoolProperty
)

from .. import common
from ..impl import uvw_impl as impl
from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry


__all__ = [
    'Properties',
    'MUV_OT_UVW_BoxMap',
    'MUV_OT_UVW_BestPlanerMap',
]


@PropertyClassRegistry()
class Properties:
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
class MUV_OT_UVW_BoxMap(bpy.types.Operator):
    bl_idname = "uv.muv_uvw_operator_box_map"
    bl_label = "Box Map"
    bl_options = {'REGISTER', 'UNDO'}

    size: FloatProperty(
        name="Size",
        default=1.0,
        precision=4
    )
    rotation: FloatVectorProperty(
        name="XYZ Rotation",
        size=3,
        default=(0.0, 0.0, 0.0)
    )
    offset: FloatVectorProperty(
        name="XYZ Offset",
        size=3,
        default=(0.0, 0.0, 0.0)
    )
    tex_aspect: FloatProperty(
        name="Texture Aspect",
        default=1.0,
        precision=4
    )
    assign_uvmap: BoolProperty(
        name="Assign UVMap",
        description="Assign UVMap when no UVmaps are available",
        default=True
    )

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return impl.is_valid_context(context)

    def execute(self, context):
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        if common.check_version(2, 73, 0) >= 0:
            bm.faces.ensure_lookup_table()

        # get UV layer
        uv_layer = impl.get_uv_layer(self, bm, self.assign_uvmap)
        if not uv_layer:
            return {'CANCELLED'}

        impl.apply_box_map(bm, uv_layer, self.size, self.offset,
                           self.rotation, self.tex_aspect)
        bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}


@BlClassRegistry()
class MUV_OT_UVW_BestPlanerMap(bpy.types.Operator):
    bl_idname = "uv.muv_uvw_operator_best_planer_map"
    bl_label = "Best Planer Map"
    bl_options = {'REGISTER', 'UNDO'}

    size: FloatProperty(
        name="Size",
        default=1.0,
        precision=4
    )
    rotation: FloatProperty(
        name="XY Rotation",
        default=0.0
    )
    offset: FloatVectorProperty(
        name="XY Offset",
        size=2,
        default=(0.0, 0.0)
    )
    tex_aspect: FloatProperty(
        name="Texture Aspect",
        default=1.0,
        precision=4
    )
    assign_uvmap: BoolProperty(
        name="Assign UVMap",
        description="Assign UVMap when no UVmaps are available",
        default=True
    )

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return impl.is_valid_context(context)

    def execute(self, context):
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        if common.check_version(2, 73, 0) >= 0:
            bm.faces.ensure_lookup_table()

        # get UV layer
        uv_layer = impl.get_uv_layer(self, bm, self.assign_uvmap)
        if not uv_layer:
            return {'CANCELLED'}

        impl.apply_planer_map(bm, uv_layer, self.size, self.offset,
                              self.rotation, self.tex_aspect)

        bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}
