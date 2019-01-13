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
from bpy.props import StringProperty, EnumProperty, BoolProperty

from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry
from ..impl import preserve_uv_aspect_impl as impl


__all__ = [
    'Properties',
    'MUV_OT_PreserveUVAspect',
]


@PropertyClassRegistry()
class _Properties:
    idname = "preserve_uv_aspect"

    @classmethod
    def init_props(cls, scene):
        def get_loaded_texture_name(_, __):
            items = [(key, key, "") for key in bpy.data.images.keys()]
            items.append(("None", "None", ""))
            return items

        scene.muv_preserve_uv_aspect_enabled = BoolProperty(
            name="Preserve UV Aspect Enabled",
            description="Preserve UV Aspect is enabled",
            default=False
        )
        scene.muv_preserve_uv_aspect_tex_image = EnumProperty(
            name="Image",
            description="Texture Image",
            items=get_loaded_texture_name
        )
        scene.muv_preserve_uv_aspect_origin = EnumProperty(
            name="Origin",
            description="Aspect Origin",
            items=[
                ('CENTER', 'Center', 'Center'),
                ('LEFT_TOP', 'Left Top', 'Left Bottom'),
                ('LEFT_CENTER', 'Left Center', 'Left Center'),
                ('LEFT_BOTTOM', 'Left Bottom', 'Left Bottom'),
                ('CENTER_TOP', 'Center Top', 'Center Top'),
                ('CENTER_BOTTOM', 'Center Bottom', 'Center Bottom'),
                ('RIGHT_TOP', 'Right Top', 'Right Top'),
                ('RIGHT_CENTER', 'Right Center', 'Right Center'),
                ('RIGHT_BOTTOM', 'Right Bottom', 'Right Bottom')

            ],
            default="CENTER"
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_preserve_uv_aspect_enabled
        del scene.muv_preserve_uv_aspect_tex_image
        del scene.muv_preserve_uv_aspect_origin


@BlClassRegistry()
class MUV_OT_PreserveUVAspect(bpy.types.Operator):
    """
    Operation class: Preserve UV Aspect
    """

    bl_idname = "uv.muv_preserve_uv_aspect_operator"
    bl_label = "Preserve UV Aspect"
    bl_description = "Choose Image"
    bl_options = {'REGISTER', 'UNDO'}

    dest_img_name: StringProperty(options={'HIDDEN'})
    origin: EnumProperty(
        name="Origin",
        description="Aspect Origin",
        items=[
            ('CENTER', 'Center', 'Center'),
            ('LEFT_TOP', 'Left Top', 'Left Bottom'),
            ('LEFT_CENTER', 'Left Center', 'Left Center'),
            ('LEFT_BOTTOM', 'Left Bottom', 'Left Bottom'),
            ('CENTER_TOP', 'Center Top', 'Center Top'),
            ('CENTER_BOTTOM', 'Center Bottom', 'Center Bottom'),
            ('RIGHT_TOP', 'Right Top', 'Right Top'),
            ('RIGHT_CENTER', 'Right Center', 'Right Center'),
            ('RIGHT_BOTTOM', 'Right Bottom', 'Right Bottom')

        ],
        default="CENTER"
    )

    def __init__(self):
        self.__impl = impl.PreserveUVAspectImpl()

    @classmethod
    def poll(cls, context):
        return impl.PreserveUVAspectImpl.poll(context)

    def execute(self, context):
        return self.__impl.execute(self, context)
