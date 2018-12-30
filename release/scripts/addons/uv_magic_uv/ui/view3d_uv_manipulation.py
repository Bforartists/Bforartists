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

from ..op import (
    flip_rotate_uv,
    mirror_uv,
    move_uv,
)
from ..utils.bl_class_registry import BlClassRegistry

__all__ = [
    'MUV_PT_View3D_UVManipulation',
]


@BlClassRegistry()
class MUV_PT_View3D_UVManipulation(bpy.types.Panel):
    """
    Panel class: UV Manipulation on Property Panel on View3D
    """

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "UV Manipulation"
    bl_category = "Magic UV"
    bl_context = 'mesh_edit'
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, _):
        layout = self.layout
        layout.label(text="", icon='IMAGE')

    def draw(self, context):
        sc = context.scene
        layout = self.layout

        box = layout.box()
        box.prop(sc, "muv_flip_rotate_uv_enabled", text="Flip/Rotate UV")
        if sc.muv_flip_rotate_uv_enabled:
            row = box.row()
            ops = row.operator(flip_rotate_uv.MUV_OT_FlipRotate.bl_idname,
                               text="Flip/Rotate")
            ops.seams = sc.muv_flip_rotate_uv_seams
            row.prop(sc, "muv_flip_rotate_uv_seams", text="Seams")

        box = layout.box()
        box.prop(sc, "muv_mirror_uv_enabled", text="Mirror UV")
        if sc.muv_mirror_uv_enabled:
            row = box.row()
            ops = row.operator(mirror_uv.MUV_OT_MirrorUV.bl_idname,
                               text="Mirror")
            ops.axis = sc.muv_mirror_uv_axis
            row.prop(sc, "muv_mirror_uv_axis", text="")

        box = layout.box()
        box.prop(sc, "muv_move_uv_enabled", text="Move UV")
        if sc.muv_move_uv_enabled:
            col = box.column()
            if not move_uv.MUV_OT_MoveUV.is_running(context):
                col.operator(move_uv.MUV_OT_MoveUV.bl_idname, icon='PLAY',
                             text="Start")
            else:
                col.operator(move_uv.MUV_OT_MoveUV.bl_idname, icon='PAUSE',
                             text="Stop")
