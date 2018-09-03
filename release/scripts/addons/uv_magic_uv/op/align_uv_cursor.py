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
__version__ = "5.1"
__date__ = "24 Feb 2018"

import bpy
from mathutils import Vector
from bpy.props import EnumProperty
import bmesh

from .. import common


class MUV_AUVCAlignOps(bpy.types.Operator):

    bl_idname = "uv.muv_auvc_align"
    bl_label = "Align"
    bl_description = "Align cursor to the center of UV island"
    bl_options = {'REGISTER', 'UNDO'}

    position = EnumProperty(
        items=(
            ('CENTER', "Center", "Align to Center"),
            ('LEFT_TOP', "Left Top", "Align to Left Top"),
            ('LEFT_MIDDLE', "Left Middle", "Align to Left Middle"),
            ('LEFT_BOTTOM', "Left Bottom", "Align to Left Bottom"),
            ('MIDDLE_TOP', "Middle Top", "Align to Middle Top"),
            ('MIDDLE_BOTTOM', "Middle Bottom", "Align to Middle Bottom"),
            ('RIGHT_TOP', "Right Top", "Align to Right Top"),
            ('RIGHT_MIDDLE', "Right Middle", "Align to Right Middle"),
            ('RIGHT_BOTTOM', "Right Bottom", "Align to Right Bottom")
        ),
        name="Position",
        description="Align position",
        default='CENTER'
    )
    base = EnumProperty(
        items=(
            ('TEXTURE', "Texture", "Align based on Texture"),
            ('UV', "UV", "Align to UV"),
            ('UV_SEL', "UV (Selected)", "Align to Selected UV")
        ),
        name="Base",
        description="Align base",
        default='TEXTURE'
    )

    def execute(self, context):
        area, _, space = common.get_space('IMAGE_EDITOR', 'WINDOW',
                                          'IMAGE_EDITOR')
        bd_size = common.get_uvimg_editor_board_size(area)

        if self.base == 'UV':
            obj = context.active_object
            bm = bmesh.from_edit_mesh(obj.data)
            if not bm.loops.layers.uv:
                return None
            uv_layer = bm.loops.layers.uv.verify()

            max_ = Vector((-10000000.0, -10000000.0))
            min_ = Vector((10000000.0, 10000000.0))
            for f in bm.faces:
                if not f.select:
                    continue
                for l in f.loops:
                    uv = l[uv_layer].uv
                    max_.x = max(max_.x, uv.x)
                    max_.y = max(max_.y, uv.y)
                    min_.x = min(min_.x, uv.x)
                    min_.y = min(min_.y, uv.y)
            center = Vector(((max_.x + min_.x) / 2.0, (max_.y + min_.y) / 2.0))

        elif self.base == 'UV_SEL':
            obj = context.active_object
            bm = bmesh.from_edit_mesh(obj.data)
            if not bm.loops.layers.uv:
                return None
            uv_layer = bm.loops.layers.uv.verify()

            max_ = Vector((-10000000.0, -10000000.0))
            min_ = Vector((10000000.0, 10000000.0))
            for f in bm.faces:
                if not f.select:
                    continue
                for l in f.loops:
                    if not l[uv_layer].select:
                        continue
                    uv = l[uv_layer].uv
                    max_.x = max(max_.x, uv.x)
                    max_.y = max(max_.y, uv.y)
                    min_.x = min(min_.x, uv.x)
                    min_.y = min(min_.y, uv.y)
            center = Vector(((max_.x + min_.x) / 2.0, (max_.y + min_.y) / 2.0))

        elif self.base == 'TEXTURE':
            min_ = Vector((0.0, 0.0))
            max_ = Vector((1.0, 1.0))
            center = Vector((0.5, 0.5))
        else:
            self.report({'ERROR'}, "Unknown Operation")

        if self.position == 'CENTER':
            cx = center.x * bd_size[0]
            cy = center.y * bd_size[1]
        elif self.position == 'LEFT_TOP':
            cx = min_.x * bd_size[0]
            cy = max_.y * bd_size[1]
        elif self.position == 'LEFT_MIDDLE':
            cx = min_.x * bd_size[0]
            cy = center.y * bd_size[1]
        elif self.position == 'LEFT_BOTTOM':
            cx = min_.x * bd_size[0]
            cy = min_.y * bd_size[1]
        elif self.position == 'MIDDLE_TOP':
            cx = center.x * bd_size[0]
            cy = max_.y * bd_size[1]
        elif self.position == 'MIDDLE_BOTTOM':
            cx = center.x * bd_size[0]
            cy = min_.y * bd_size[1]
        elif self.position == 'RIGHT_TOP':
            cx = max_.x * bd_size[0]
            cy = max_.y * bd_size[1]
        elif self.position == 'RIGHT_MIDDLE':
            cx = max_.x * bd_size[0]
            cy = center.y * bd_size[1]
        elif self.position == 'RIGHT_BOTTOM':
            cx = max_.x * bd_size[0]
            cy = min_.y * bd_size[1]
        else:
            self.report({'ERROR'}, "Unknown Operation")

        space.cursor_location = Vector((cx, cy))

        return {'FINISHED'}
