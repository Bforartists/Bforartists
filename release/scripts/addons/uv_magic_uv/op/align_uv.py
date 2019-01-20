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
from bpy.props import EnumProperty, BoolProperty, FloatProperty

from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry
from ..impl import align_uv_impl as impl


@PropertyClassRegistry()
class _Properties:
    idname = "align_uv"

    @classmethod
    def init_props(cls, scene):
        scene.muv_align_uv_enabled = BoolProperty(
            name="Align UV Enabled",
            description="Align UV is enabled",
            default=False
        )
        scene.muv_align_uv_transmission = BoolProperty(
            name="Transmission",
            description="Align linked UVs",
            default=False
        )
        scene.muv_align_uv_select = BoolProperty(
            name="Select",
            description="Select UVs which are aligned",
            default=False
        )
        scene.muv_align_uv_vertical = BoolProperty(
            name="Vert-Infl (Vertical)",
            description="Align vertical direction influenced "
                        "by mesh vertex proportion",
            default=False
        )
        scene.muv_align_uv_horizontal = BoolProperty(
            name="Vert-Infl (Horizontal)",
            description="Align horizontal direction influenced "
                        "by mesh vertex proportion",
            default=False
        )
        scene.muv_align_uv_mesh_infl = FloatProperty(
            name="Mesh Influence",
            description="Influence rate of mesh vertex",
            min=0.0,
            max=1.0,
            default=0.0
        )
        scene.muv_align_uv_location = EnumProperty(
            name="Location",
            description="Align location",
            items=[
                ('LEFT_TOP', "Left/Top", "Align to Left or Top"),
                ('MIDDLE', "Middle", "Align to middle"),
                ('RIGHT_BOTTOM', "Right/Bottom", "Align to Right or Bottom")
            ],
            default='MIDDLE'
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_align_uv_enabled
        del scene.muv_align_uv_transmission
        del scene.muv_align_uv_select
        del scene.muv_align_uv_vertical
        del scene.muv_align_uv_horizontal
        del scene.muv_align_uv_mesh_infl
        del scene.muv_align_uv_location


@BlClassRegistry()
class MUV_OT_AlignUV_Circle(bpy.types.Operator):

    bl_idname = "uv.muv_align_uv_operator_circle"
    bl_label = "Align UV (Circle)"
    bl_description = "Align UV coordinates to Circle"
    bl_options = {'REGISTER', 'UNDO'}

    transmission: BoolProperty(
        name="Transmission",
        description="Align linked UVs",
        default=False
    )
    select: BoolProperty(
        name="Select",
        description="Select UVs which are aligned",
        default=False
    )

    def __init__(self):
        self.__impl = impl.CircleImpl()

    @classmethod
    def poll(cls, context):
        return impl.CircleImpl.poll(context)

    def execute(self, context):
        return self.__impl.execute(self, context)


@BlClassRegistry()
class MUV_OT_AlignUV_Straighten(bpy.types.Operator):

    bl_idname = "uv.muv_align_uv_operator_straighten"
    bl_label = "Align UV (Straighten)"
    bl_description = "Straighten UV coordinates"
    bl_options = {'REGISTER', 'UNDO'}

    transmission: BoolProperty(
        name="Transmission",
        description="Align linked UVs",
        default=False
    )
    select: BoolProperty(
        name="Select",
        description="Select UVs which are aligned",
        default=False
    )
    vertical: BoolProperty(
        name="Vert-Infl (Vertical)",
        description="Align vertical direction influenced "
                    "by mesh vertex proportion",
        default=False
    )
    horizontal: BoolProperty(
        name="Vert-Infl (Horizontal)",
        description="Align horizontal direction influenced "
                    "by mesh vertex proportion",
        default=False
    )
    mesh_infl: FloatProperty(
        name="Mesh Influence",
        description="Influence rate of mesh vertex",
        min=0.0,
        max=1.0,
        default=0.0
    )

    def __init__(self):
        self.__impl = impl.StraightenImpl()

    @classmethod
    def poll(cls, context):
        return impl.StraightenImpl.poll(context)

    def execute(self, context):
        return self.__impl.execute(self, context)


@BlClassRegistry()
class MUV_OT_AlignUV_Axis(bpy.types.Operator):

    bl_idname = "uv.muv_align_uv_operator_axis"
    bl_label = "Align UV (XY-Axis)"
    bl_description = "Align UV to XY-axis"
    bl_options = {'REGISTER', 'UNDO'}

    transmission: BoolProperty(
        name="Transmission",
        description="Align linked UVs",
        default=False
    )
    select: BoolProperty(
        name="Select",
        description="Select UVs which are aligned",
        default=False
    )
    vertical: BoolProperty(
        name="Vert-Infl (Vertical)",
        description="Align vertical direction influenced "
                    "by mesh vertex proportion",
        default=False
    )
    horizontal: BoolProperty(
        name="Vert-Infl (Horizontal)",
        description="Align horizontal direction influenced "
                    "by mesh vertex proportion",
        default=False
    )
    location: EnumProperty(
        name="Location",
        description="Align location",
        items=[
            ('LEFT_TOP', "Left/Top", "Align to Left or Top"),
            ('MIDDLE', "Middle", "Align to middle"),
            ('RIGHT_BOTTOM', "Right/Bottom", "Align to Right or Bottom")
        ],
        default='MIDDLE'
    )
    mesh_infl: FloatProperty(
        name="Mesh Influence",
        description="Influence rate of mesh vertex",
        min=0.0,
        max=1.0,
        default=0.0
    )

    def __init__(self):
        self.__impl = impl.AxisImpl()

    @classmethod
    def poll(cls, context):
        return impl.AxisImpl.poll(context)

    def execute(self, context):
        return self.__impl.execute(self, context)
