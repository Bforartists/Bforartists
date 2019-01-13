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
from mathutils import Vector
from bpy.props import EnumProperty, BoolProperty, FloatVectorProperty

from ... import common
from ...utils.bl_class_registry import BlClassRegistry
from ...utils.property_class_registry import PropertyClassRegistry
from ...impl import align_uv_cursor_impl as impl


@PropertyClassRegistry(legacy=True)
class _Properties:
    idname = "align_uv_cursor"

    @classmethod
    def init_props(cls, scene):
        def auvc_get_cursor_loc(self):
            area, _, space = common.get_space_legacy('IMAGE_EDITOR', 'WINDOW',
                                                     'IMAGE_EDITOR')
            bd_size = common.get_uvimg_editor_board_size(area)
            loc = space.cursor_location
            if bd_size[0] < 0.000001:
                cx = 0.0
            else:
                cx = loc[0] / bd_size[0]
            if bd_size[1] < 0.000001:
                cy = 0.0
            else:
                cy = loc[1] / bd_size[1]
            self['muv_align_uv_cursor_cursor_loc'] = Vector((cx, cy))
            return self.get('muv_align_uv_cursor_cursor_loc', (0.0, 0.0))

        def auvc_set_cursor_loc(self, value):
            self['muv_align_uv_cursor_cursor_loc'] = value
            area, _, space = common.get_space_legacy('IMAGE_EDITOR', 'WINDOW',
                                                     'IMAGE_EDITOR')
            bd_size = common.get_uvimg_editor_board_size(area)
            cx = bd_size[0] * value[0]
            cy = bd_size[1] * value[1]
            space.cursor_location = Vector((cx, cy))

        scene.muv_align_uv_cursor_enabled = BoolProperty(
            name="Align UV Cursor Enabled",
            description="Align UV Cursor is enabled",
            default=False
        )

        scene.muv_align_uv_cursor_cursor_loc = FloatVectorProperty(
            name="UV Cursor Location",
            size=2,
            precision=4,
            soft_min=-1.0,
            soft_max=1.0,
            step=1,
            default=(0.000, 0.000),
            get=auvc_get_cursor_loc,
            set=auvc_set_cursor_loc
        )
        scene.muv_align_uv_cursor_align_method = EnumProperty(
            name="Align Method",
            description="Align Method",
            default='TEXTURE',
            items=[
                ('TEXTURE', "Texture", "Align to texture"),
                ('UV', "UV", "Align to UV"),
                ('UV_SEL', "UV (Selected)", "Align to Selected UV")
            ]
        )

        scene.muv_uv_cursor_location_enabled = BoolProperty(
            name="UV Cursor Location Enabled",
            description="UV Cursor Location is enabled",
            default=False
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_align_uv_cursor_enabled
        del scene.muv_align_uv_cursor_cursor_loc
        del scene.muv_align_uv_cursor_align_method

        del scene.muv_uv_cursor_location_enabled


@BlClassRegistry(legacy=True)
class MUV_OT_AlignUVCursor(bpy.types.Operator):

    bl_idname = "uv.muv_align_uv_cursor_operator"
    bl_label = "Align UV Cursor"
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

    def __init__(self):
        self.__impl = impl.AlignUVCursorLegacyImpl()

    @classmethod
    def poll(cls, context):
        return impl.AlignUVCursorLegacyImpl.poll(context)

    def execute(self, context):
        return self.__impl.execute(self, context)
