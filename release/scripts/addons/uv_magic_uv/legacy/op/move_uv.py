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

__author__ = "kgeogeo, mem, Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "5.2"
__date__ = "17 Nov 2018"

import bpy
from bpy.props import BoolProperty

from ...impl import move_uv_impl as impl
from ...utils.bl_class_registry import BlClassRegistry
from ...utils.property_class_registry import PropertyClassRegistry


__all__ = [
    'Properties',
    'MUV_OT_MoveUV',
]


@PropertyClassRegistry(legacy=True)
class Properties:
    idname = "move_uv"

    @classmethod
    def init_props(cls, scene):
        scene.muv_move_uv_enabled = BoolProperty(
            name="Move UV Enabled",
            description="Move UV is enabled",
            default=False
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_move_uv_enabled


@BlClassRegistry(legacy=True)
class MUV_OT_MoveUV(bpy.types.Operator):
    """
    Operator class: Move UV
    """

    bl_idname = "uv.muv_move_uv_operator"
    bl_label = "Move UV"
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        self.__impl = impl.MoveUVImpl()

    @classmethod
    def poll(cls, context):
        return impl.MoveUVImpl.poll(context)

    @classmethod
    def is_running(cls, _):
        return impl.MoveUVImpl.is_running(_)

    def modal(self, context, event):
        return self.__impl.modal(self, context, event)

    def execute(self, context):
        return self.__impl.execute(self, context)
