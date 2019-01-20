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

import bpy
from bpy.props import BoolProperty, FloatProperty

from ...utils.bl_class_registry import BlClassRegistry
from ...utils.property_class_registry import PropertyClassRegistry
from ...impl import smooth_uv_impl as impl


@PropertyClassRegistry(legacy=True)
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


@BlClassRegistry(legacy=True)
class MUV_OT_SmoothUV(bpy.types.Operator):

    bl_idname = "uv.muv_smooth_uv_operator"
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

    def __init__(self):
        self.__impl = impl.SmoothUVImpl()

    @classmethod
    def poll(cls, context):
        return impl.SmoothUVImpl.poll(context)

    def execute(self, context):
        return self.__impl.execute(self, context)
