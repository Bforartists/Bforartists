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
import bmesh
from bpy.props import (
    BoolProperty,
    IntProperty,
)

from .. import common
from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry
from ..impl import flip_rotate_impl as impl

__all__ = [
    'Properties',
    'MUV_OT_FlipRotate',
]


@PropertyClassRegistry()
class Properties:
    idname = "flip_rotate_uv"

    @classmethod
    def init_props(cls, scene):
        scene.muv_flip_rotate_uv_enabled = BoolProperty(
            name="Flip/Rotate UV Enabled",
            description="Flip/Rotate UV is enabled",
            default=False
        )
        scene.muv_flip_rotate_uv_seams = BoolProperty(
            name="Seams",
            description="Seams",
            default=True
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_flip_rotate_uv_enabled
        del scene.muv_flip_rotate_uv_seams


@BlClassRegistry()
class MUV_OT_FlipRotate(bpy.types.Operator):
    """
    Operation class: Flip and Rotate UV coordinate
    """

    bl_idname = "uv.muv_flip_rotate_uv_operator"
    bl_label = "Flip/Rotate UV"
    bl_description = "Flip/Rotate UV coordinate"
    bl_options = {'REGISTER', 'UNDO'}

    flip: BoolProperty(
        name="Flip UV",
        description="Flip UV...",
        default=False
    )
    rotate: IntProperty(
        default=0,
        name="Rotate UV",
        min=0,
        max=30
    )
    seams: BoolProperty(
        name="Seams",
        description="Seams",
        default=True
    )

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return impl.is_valid_context(context)

    def execute(self, context):
        self.report({'INFO'}, "Flip/Rotate UV")
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        if common.check_version(2, 73, 0) >= 0:
            bm.faces.ensure_lookup_table()

        # get UV layer
        uv_layer = impl.get_uv_layer(self, bm)
        if not uv_layer:
            return {'CANCELLED'}

        # get selected face
        src_info = impl.get_src_face_info(self, bm, [uv_layer], True)
        if not src_info:
            return {'CANCELLED'}

        face_count = len(src_info[list(src_info.keys())[0]])
        self.report({'INFO'}, "{} face(s) are selected".format(face_count))

        # paste
        ret = impl.paste_uv(self, bm, src_info, src_info, [uv_layer], 'N_N',
                            self.flip, self.rotate, self.seams)
        if ret:
            return {'CANCELLED'}

        bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}
