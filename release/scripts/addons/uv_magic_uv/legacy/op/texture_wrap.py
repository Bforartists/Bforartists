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
    BoolProperty,
)

from ...utils.bl_class_registry import BlClassRegistry
from ...utils.property_class_registry import PropertyClassRegistry
from ...impl import texture_wrap_impl as impl


@PropertyClassRegistry(legacy=True)
class _Properties:
    idname = "texture_wrap"

    @classmethod
    def init_props(cls, scene):
        class Props():
            ref_face_index = -1
            ref_obj = None

        scene.muv_props.texture_wrap = Props()

        scene.muv_texture_wrap_enabled = BoolProperty(
            name="Texture Wrap",
            description="Texture Wrap is enabled",
            default=False
        )
        scene.muv_texture_wrap_set_and_refer = BoolProperty(
            name="Set and Refer",
            description="Refer and set UV",
            default=True
        )
        scene.muv_texture_wrap_selseq = BoolProperty(
            name="Selection Sequence",
            description="Set UV sequentially",
            default=False
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_props.texture_wrap
        del scene.muv_texture_wrap_enabled
        del scene.muv_texture_wrap_set_and_refer
        del scene.muv_texture_wrap_selseq


@BlClassRegistry(legacy=True)
class MUV_OT_TextureWrap_Refer(bpy.types.Operator):
    """
    Operation class: Refer UV
    """

    bl_idname = "uv.muv_texture_wrap_operator_refer"
    bl_label = "Refer"
    bl_description = "Refer UV"
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        self.__impl = impl.ReferImpl()

    @classmethod
    def poll(cls, context):
        return impl.ReferImpl.poll(context)

    def execute(self, context):
        return self.__impl.execute(self, context)


@BlClassRegistry(legacy=True)
class MUV_OT_TextureWrap_Set(bpy.types.Operator):
    """
    Operation class: Set UV
    """

    bl_idname = "uv.muv_texture_wrap_operator_set"
    bl_label = "Set"
    bl_description = "Set UV"
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        self.__impl = impl.SetImpl()

    @classmethod
    def poll(cls, context):
        return impl.SetImpl.poll(context)

    def execute(self, context):
        return self.__impl.execute(self, context)
