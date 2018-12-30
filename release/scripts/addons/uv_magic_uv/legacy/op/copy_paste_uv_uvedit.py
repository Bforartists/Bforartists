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

from ...utils.bl_class_registry import BlClassRegistry
from ...utils.property_class_registry import PropertyClassRegistry
from ...impl import copy_paste_uv_uvedit_impl as impl


__all__ = [
    'Properties',
    'MUV_OT_CopyPasteUVUVEdit_CopyUV',
    'MUV_OT_CopyPasteUVUVEdit_PasteUV',
]


@PropertyClassRegistry(legacy=True)
class Properties:
    idname = "copy_paste_uv_uvedit"

    @classmethod
    def init_props(cls, scene):
        class Props():
            src_uvs = None

        scene.muv_props.copy_paste_uv_uvedit = Props()

    @classmethod
    def del_props(cls, scene):
        del scene.muv_props.copy_paste_uv_uvedit


@BlClassRegistry(legacy=True)
class MUV_OT_CopyPasteUVUVEdit_CopyUV(bpy.types.Operator):
    """
    Operation class: Copy UV coordinate on UV/Image Editor
    """

    bl_idname = "uv.muv_copy_paste_uv_uvedit_operator_copy_uv"
    bl_label = "Copy UV (UV/Image Editor)"
    bl_description = "Copy UV coordinate (only selected in UV/Image Editor)"
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        self.__impl = impl.CopyUVImpl()

    @classmethod
    def poll(cls, context):
        return impl.CopyUVImpl.poll(context)

    def execute(self, context):
        return self.__impl.execute(self, context)


@BlClassRegistry(legacy=True)
class MUV_OT_CopyPasteUVUVEdit_PasteUV(bpy.types.Operator):
    """
    Operation class: Paste UV coordinate on UV/Image Editor
    """

    bl_idname = "uv.muv_copy_paste_uv_uvedit_operator_paste_uv"
    bl_label = "Paste UV (UV/Image Editor)"
    bl_description = "Paste UV coordinate (only selected in UV/Image Editor)"
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        self.__impl = impl.PasteUVImpl()

    @classmethod
    def poll(cls, context):
        return impl.PasteUVImpl.poll(context)

    def execute(self, context):
        return self.__impl.execute(self, context)
