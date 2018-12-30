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
__version__ = "5.2"
__date__ = "17 Nov 2018"

import bpy
from bpy.props import (
    EnumProperty,
    FloatProperty,
    BoolProperty,
)

from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry
from ..impl import mirror_uv_impl as impl


__all__ = [
    'Properties',
    'MUV_OT_MirrorUV',
]


@PropertyClassRegistry()
class Properties:
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
class MUV_OT_MirrorUV(bpy.types.Operator):
    """
    Operation class: Mirror UV
    """

    bl_idname = "uv.muv_mirror_uv_operator"
    bl_label = "Mirror UV"
    bl_options = {'REGISTER', 'UNDO'}

    axis: EnumProperty(
        items=(
            ('X', "X", "Mirror Along X axis"),
            ('Y', "Y", "Mirror Along Y axis"),
            ('Z', "Z", "Mirror Along Z axis")
        ),
        name="Axis",
        description="Mirror Axis",
        default='X'
    )
    error: FloatProperty(
        name="Error",
        description="Error threshold",
        default=0.001,
        min=0.0,
        max=100.0,
        soft_min=0.0,
        soft_max=1.0
    )

    def __init__(self):
        self.__impl = impl.MirrorUVImpl()

    @classmethod
    def poll(cls, context):
        return impl.MirrorUVImpl.poll(context)

    def execute(self, context):
        return self.__impl.execute(self, context)
