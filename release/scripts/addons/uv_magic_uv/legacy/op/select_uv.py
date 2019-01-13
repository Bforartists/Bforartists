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
from bpy.props import BoolProperty

from ...utils.bl_class_registry import BlClassRegistry
from ...utils.property_class_registry import PropertyClassRegistry
from ...impl import select_uv_impl as impl


@PropertyClassRegistry(legacy=True)
class _Properties:
    idname = "select_uv"

    @classmethod
    def init_props(cls, scene):
        scene.muv_select_uv_enabled = BoolProperty(
            name="Select UV Enabled",
            description="Select UV is enabled",
            default=False
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_select_uv_enabled


@BlClassRegistry(legacy=True)
class MUV_OT_SelectUV_SelectOverlapped(bpy.types.Operator):
    """
    Operation class: Select faces which have overlapped UVs
    """

    bl_idname = "uv.muv_select_uv_operator_select_overlapped"
    bl_label = "Overlapped"
    bl_description = "Select faces which have overlapped UVs"
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        self.__impl = impl.SelectOverlappedImpl()

    @classmethod
    def poll(cls, context):
        return impl.SelectOverlappedImpl.poll(context)

    def execute(self, context):
        return self.__impl.execute(self, context)


@BlClassRegistry(legacy=True)
class MUV_OT_SelectUV_SelectFlipped(bpy.types.Operator):
    """
    Operation class: Select faces which have flipped UVs
    """

    bl_idname = "uv.muv_select_uv_operator_select_flipped"
    bl_label = "Flipped"
    bl_description = "Select faces which have flipped UVs"
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        self.__impl = impl.SelectFlippedImpl()

    @classmethod
    def poll(cls, context):
        return impl.SelectFlippedImpl.poll(context)

    def execute(self, context):
        return self.__impl.execute(self, context)
