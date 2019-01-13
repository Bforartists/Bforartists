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
__version__ = "5.2"
__date__ = "17 Nov 2018"

import bpy
from bpy.props import (
    FloatProperty,
    FloatVectorProperty,
    BoolProperty,
)

from ...utils.bl_class_registry import BlClassRegistry
from ...utils.property_class_registry import PropertyClassRegistry
from ...impl import pack_uv_impl as impl


__all__ = [
    'Properties',
    'MUV_OT_PackUV',
]


@PropertyClassRegistry(legacy=True)
class Properties:
    idname = "pack_uv"

    @classmethod
    def init_props(cls, scene):
        scene.muv_pack_uv_enabled = BoolProperty(
            name="Pack UV Enabled",
            description="Pack UV is enabled",
            default=False
        )
        scene.muv_pack_uv_allowable_center_deviation = FloatVectorProperty(
            name="Allowable Center Deviation",
            description="Allowable center deviation to judge same UV island",
            min=0.000001,
            max=0.1,
            default=(0.001, 0.001),
            size=2
        )
        scene.muv_pack_uv_allowable_size_deviation = FloatVectorProperty(
            name="Allowable Size Deviation",
            description="Allowable sizse deviation to judge same UV island",
            min=0.000001,
            max=0.1,
            default=(0.001, 0.001),
            size=2
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_pack_uv_enabled
        del scene.muv_pack_uv_allowable_center_deviation
        del scene.muv_pack_uv_allowable_size_deviation


@BlClassRegistry(legacy=True)
class MUV_OT_PackUV(bpy.types.Operator):
    """
    Operation class: Pack UV with same UV islands are integrated
    Island matching algorithm
     - Same center of UV island
     - Same size of UV island
     - Same number of UV
    """

    bl_idname = "uv.muv_pack_uv_operator"
    bl_label = "Pack UV"
    bl_description = "Pack UV (Same UV Islands are integrated)"
    bl_options = {'REGISTER', 'UNDO'}

    rotate = BoolProperty(
        name="Rotate",
        description="Rotate option used by default pack UV function",
        default=False)
    margin = FloatProperty(
        name="Margin",
        description="Margin used by default pack UV function",
        min=0,
        max=1,
        default=0.001)
    allowable_center_deviation = FloatVectorProperty(
        name="Allowable Center Deviation",
        description="Allowable center deviation to judge same UV island",
        min=0.000001,
        max=0.1,
        default=(0.001, 0.001),
        size=2
    )
    allowable_size_deviation = FloatVectorProperty(
        name="Allowable Size Deviation",
        description="Allowable sizse deviation to judge same UV island",
        min=0.000001,
        max=0.1,
        default=(0.001, 0.001),
        size=2
    )

    def __init__(self):
        self.__impl = impl.PackUVImpl()

    @classmethod
    def poll(cls, context):
        return impl.PackUVImpl.poll(context)

    def execute(self, context):
        return self.__impl.execute(self, context)
