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

__author__ = "Nutti <nutti.metro@gmail.com>, Mifth, MaxRobinot"
__status__ = "production"
__version__ = "5.2"
__date__ = "17 Nov 2018"

import bpy
import bmesh
from bpy.props import BoolProperty

from .. import common
from ..impl import transfer_uv_impl as impl
from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry


__all__ = [
    'Properties',
    'MUV_OT_TransferUV_CopyUV',
    'MUV_OT_TransferUV_PasteUV',
]


@PropertyClassRegistry()
class Properties:
    idname = "transfer_uv"

    @classmethod
    def init_props(cls, scene):
        class Props():
            topology_copied = None

        scene.muv_props.transfer_uv = Props()

        scene.muv_transfer_uv_enabled = BoolProperty(
            name="Transfer UV Enabled",
            description="Transfer UV is enabled",
            default=False
        )
        scene.muv_transfer_uv_invert_normals = BoolProperty(
            name="Invert Normals",
            description="Invert Normals",
            default=False
        )
        scene.muv_transfer_uv_copy_seams = BoolProperty(
            name="Copy Seams",
            description="Copy Seams",
            default=True
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_transfer_uv_enabled
        del scene.muv_transfer_uv_invert_normals
        del scene.muv_transfer_uv_copy_seams


@BlClassRegistry()
class MUV_OT_TransferUV_CopyUV(bpy.types.Operator):
    """
        Operation class: Transfer UV copy
        Topological based copy
    """

    bl_idname = "uv.muv_transfer_uv_operator_copy_uv"
    bl_label = "Transfer UV Copy UV"
    bl_description = "Transfer UV Copy UV (Topological based copy)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return impl.is_valid_context(context)

    def execute(self, context):
        props = context.scene.muv_props.transfer_uv
        active_obj = context.active_object
        bm = bmesh.from_edit_mesh(active_obj.data)
        bm.faces.ensure_lookup_table()

        uv_layer = impl.get_uv_layer(self, bm)
        if uv_layer is None:
            return {'CANCELLED'}

        faces = impl.get_selected_src_faces(self, bm, uv_layer)
        if faces is None:
            return {'CANCELLED'}
        props.topology_copied = faces

        bmesh.update_edit_mesh(active_obj.data)

        return {'FINISHED'}


@BlClassRegistry()
class MUV_OT_TransferUV_PasteUV(bpy.types.Operator):
    """
        Operation class: Transfer UV paste
        Topological based paste
    """

    bl_idname = "uv.muv_transfer_uv_operator_paste_uv"
    bl_label = "Transfer UV Paste UV"
    bl_description = "Transfer UV Paste UV (Topological based paste)"
    bl_options = {'REGISTER', 'UNDO'}

    invert_normals: BoolProperty(
        name="Invert Normals",
        description="Invert Normals",
        default=False
    )
    copy_seams: BoolProperty(
        name="Copy Seams",
        description="Copy Seams",
        default=True
    )

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        sc = context.scene
        props = sc.muv_props.transfer_uv
        if not props.topology_copied:
            return False
        return impl.is_valid_context(context)

    def execute(self, context):
        props = context.scene.muv_props.transfer_uv
        active_obj = context.active_object
        bm = bmesh.from_edit_mesh(active_obj.data)
        bm.faces.ensure_lookup_table()

        # get UV layer
        uv_layer = impl.get_uv_layer(self, bm)
        if uv_layer is None:
            return {'CANCELLED'}

        ret = impl.paste_uv(self, bm, uv_layer, props.topology_copied,
                            self.invert_normals, self.copy_seams)
        if ret:
            return {'CANCELLED'}

        bmesh.update_edit_mesh(active_obj.data)

        return {'FINISHED'}
