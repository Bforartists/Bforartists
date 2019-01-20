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

from mathutils import Vector
import bmesh

from .. import common


def _is_valid_context(context):
    # 'IMAGE_EDITOR' and 'VIEW_3D' space is allowed to execute.
    # If 'View_3D' space is not allowed, you can't find option in Tool-Shelf
    # after the execution
    for space in context.area.spaces:
        if (space.type == 'IMAGE_EDITOR') or (space.type == 'VIEW_3D'):
            break
    else:
        return False

    return True


class AlignUVCursorLegacyImpl:
    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    def execute(self, ops_obj, context):
        area, _, space = common.get_space_legacy('IMAGE_EDITOR', 'WINDOW',
                                                 'IMAGE_EDITOR')
        bd_size = common.get_uvimg_editor_board_size(area)

        if ops_obj.base == 'UV':
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

        elif ops_obj.base == 'UV_SEL':
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

        elif ops_obj.base == 'TEXTURE':
            min_ = Vector((0.0, 0.0))
            max_ = Vector((1.0, 1.0))
            center = Vector((0.5, 0.5))
        else:
            ops_obj.report({'ERROR'}, "Unknown Operation")
            return {'CANCELLED'}

        if ops_obj.position == 'CENTER':
            cx = center.x * bd_size[0]
            cy = center.y * bd_size[1]
        elif ops_obj.position == 'LEFT_TOP':
            cx = min_.x * bd_size[0]
            cy = max_.y * bd_size[1]
        elif ops_obj.position == 'LEFT_MIDDLE':
            cx = min_.x * bd_size[0]
            cy = center.y * bd_size[1]
        elif ops_obj.position == 'LEFT_BOTTOM':
            cx = min_.x * bd_size[0]
            cy = min_.y * bd_size[1]
        elif ops_obj.position == 'MIDDLE_TOP':
            cx = center.x * bd_size[0]
            cy = max_.y * bd_size[1]
        elif ops_obj.position == 'MIDDLE_BOTTOM':
            cx = center.x * bd_size[0]
            cy = min_.y * bd_size[1]
        elif ops_obj.position == 'RIGHT_TOP':
            cx = max_.x * bd_size[0]
            cy = max_.y * bd_size[1]
        elif ops_obj.position == 'RIGHT_MIDDLE':
            cx = max_.x * bd_size[0]
            cy = center.y * bd_size[1]
        elif ops_obj.position == 'RIGHT_BOTTOM':
            cx = max_.x * bd_size[0]
            cy = min_.y * bd_size[1]
        else:
            ops_obj.report({'ERROR'}, "Unknown Operation")
            return {'CANCELLED'}

        space.cursor_location = Vector((cx, cy))

        return {'FINISHED'}


class AlignUVCursorImpl:
    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    def execute(self, ops_obj, context):
        _, _, space = common.get_space_legacy('IMAGE_EDITOR', 'WINDOW',
                                              'IMAGE_EDITOR')

        if ops_obj.base == 'UV':
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

        elif ops_obj.base == 'UV_SEL':
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

        elif ops_obj.base == 'TEXTURE':
            min_ = Vector((0.0, 0.0))
            max_ = Vector((1.0, 1.0))
            center = Vector((0.5, 0.5))
        else:
            ops_obj.report({'ERROR'}, "Unknown Operation")
            return {'CANCELLED'}

        if ops_obj.position == 'CENTER':
            cx = center.x
            cy = center.y
        elif ops_obj.position == 'LEFT_TOP':
            cx = min_.x
            cy = max_.y
        elif ops_obj.position == 'LEFT_MIDDLE':
            cx = min_.x
            cy = center.y
        elif ops_obj.position == 'LEFT_BOTTOM':
            cx = min_.x
            cy = min_.y
        elif ops_obj.position == 'MIDDLE_TOP':
            cx = center.x
            cy = max_.y
        elif ops_obj.position == 'MIDDLE_BOTTOM':
            cx = center.x
            cy = min_.y
        elif ops_obj.position == 'RIGHT_TOP':
            cx = max_.x
            cy = max_.y
        elif ops_obj.position == 'RIGHT_MIDDLE':
            cx = max_.x
            cy = center.y
        elif ops_obj.position == 'RIGHT_BOTTOM':
            cx = max_.x
            cy = min_.y
        else:
            ops_obj.report({'ERROR'}, "Unknown Operation")
            return {'CANCELLED'}

        space.cursor_location = Vector((cx, cy))

        return {'FINISHED'}
