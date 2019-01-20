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

__author__ = "McBuff, Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "5.2"
__date__ = "17 Nov 2018"

import bpy
from bpy.props import (
    EnumProperty,
    FloatProperty,
    IntVectorProperty,
    BoolProperty,
)

from ...utils.bl_class_registry import BlClassRegistry
from ...utils.property_class_registry import PropertyClassRegistry
from ...impl import world_scale_uv_impl as impl


@PropertyClassRegistry(legacy=True)
class Properties:
    idname = "world_scale_uv"

    @classmethod
    def init_props(cls, scene):
        scene.muv_world_scale_uv_enabled = BoolProperty(
            name="World Scale UV Enabled",
            description="World Scale UV is enabled",
            default=False
        )
        scene.muv_world_scale_uv_src_mesh_area = FloatProperty(
            name="Mesh Area",
            description="Source Mesh Area",
            default=0.0,
            min=0.0
        )
        scene.muv_world_scale_uv_src_uv_area = FloatProperty(
            name="UV Area",
            description="Source UV Area",
            default=0.0,
            min=0.0
        )
        scene.muv_world_scale_uv_src_density = FloatProperty(
            name="Density",
            description="Source Texel Density",
            default=0.0,
            min=0.0
        )
        scene.muv_world_scale_uv_tgt_density = FloatProperty(
            name="Density",
            description="Target Texel Density",
            default=0.0,
            min=0.0
        )
        scene.muv_world_scale_uv_tgt_scaling_factor = FloatProperty(
            name="Scaling Factor",
            default=1.0,
            max=1000.0,
            min=0.00001
        )
        scene.muv_world_scale_uv_tgt_texture_size = IntVectorProperty(
            name="Texture Size",
            size=2,
            min=1,
            soft_max=10240,
            default=(1024, 1024),
        )
        scene.muv_world_scale_uv_mode = EnumProperty(
            name="Mode",
            description="Density calculation mode",
            items=[
                ('PROPORTIONAL_TO_MESH', "Proportional to Mesh",
                 "Apply density proportionaled by mesh size"),
                ('SCALING_DENSITY', "Scaling Density",
                 "Apply scaled density from source"),
                ('SAME_DENSITY', "Same Density",
                 "Apply same density of source"),
                ('MANUAL', "Manual", "Specify density and size by manual"),
            ],
            default='MANUAL'
        )
        scene.muv_world_scale_uv_origin = EnumProperty(
            name="Origin",
            description="Aspect Origin",
            items=[
                ('CENTER', "Center", "Center"),
                ('LEFT_TOP', "Left Top", "Left Bottom"),
                ('LEFT_CENTER', "Left Center", "Left Center"),
                ('LEFT_BOTTOM', "Left Bottom", "Left Bottom"),
                ('CENTER_TOP', "Center Top", "Center Top"),
                ('CENTER_BOTTOM', "Center Bottom", "Center Bottom"),
                ('RIGHT_TOP', "Right Top", "Right Top"),
                ('RIGHT_CENTER', "Right Center", "Right Center"),
                ('RIGHT_BOTTOM', "Right Bottom", "Right Bottom")

            ],
            default='CENTER'
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_world_scale_uv_enabled
        del scene.muv_world_scale_uv_src_mesh_area
        del scene.muv_world_scale_uv_src_uv_area
        del scene.muv_world_scale_uv_src_density
        del scene.muv_world_scale_uv_tgt_density
        del scene.muv_world_scale_uv_tgt_scaling_factor
        del scene.muv_world_scale_uv_mode
        del scene.muv_world_scale_uv_origin


@BlClassRegistry(legacy=True)
class MUV_OT_WorldScaleUV_Measure(bpy.types.Operator):
    """
    Operation class: Measure face size
    """

    bl_idname = "uv.muv_world_scale_uv_operator_measure"
    bl_label = "Measure World Scale UV"
    bl_description = "Measure face size for scale calculation"
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        self.__impl = impl.MeasureImpl()

    @classmethod
    def poll(cls, context):
        return impl.MeasureImpl.poll(context)

    def execute(self, context):
        return self.__impl.execute(self, context)


@BlClassRegistry(legacy=True)
class MUV_OT_WorldScaleUV_ApplyManual(bpy.types.Operator):
    """
    Operation class: Apply scaled UV (Manual)
    """

    bl_idname = "uv.muv_world_scale_uv_operator_apply_manual"
    bl_label = "Apply World Scale UV (Manual)"
    bl_description = "Apply scaled UV based on user specification"
    bl_options = {'REGISTER', 'UNDO'}

    tgt_density = FloatProperty(
        name="Density",
        description="Target Texel Density",
        default=1.0,
        min=0.0
    )
    tgt_texture_size = IntVectorProperty(
        name="Texture Size",
        size=2,
        min=1,
        soft_max=10240,
        default=(1024, 1024),
    )
    origin = EnumProperty(
        name="Origin",
        description="Aspect Origin",
        items=[
            ('CENTER', "Center", "Center"),
            ('LEFT_TOP', "Left Top", "Left Bottom"),
            ('LEFT_CENTER', "Left Center", "Left Center"),
            ('LEFT_BOTTOM', "Left Bottom", "Left Bottom"),
            ('CENTER_TOP', "Center Top", "Center Top"),
            ('CENTER_BOTTOM', "Center Bottom", "Center Bottom"),
            ('RIGHT_TOP', "Right Top", "Right Top"),
            ('RIGHT_CENTER', "Right Center", "Right Center"),
            ('RIGHT_BOTTOM', "Right Bottom", "Right Bottom")

        ],
        default='CENTER'
    )
    show_dialog = BoolProperty(
        name="Show Diaglog Menu",
        description="Show dialog menu if true",
        default=True,
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    def __init__(self):
        self.__impl = impl.ApplyManualImpl()

    @classmethod
    def poll(cls, context):
        return impl.ApplyManualImpl.poll(context)

    def draw(self, context):
        self.__impl.draw(self, context)

    def invoke(self, context, event):
        return self.__impl.invoke(self, context, event)

    def execute(self, context):
        return self.__impl.execute(self, context)


@BlClassRegistry(legacy=True)
class MUV_OT_WorldScaleUV_ApplyScalingDensity(bpy.types.Operator):
    """
    Operation class: Apply scaled UV (Scaling Density)
    """

    bl_idname = "uv.muv_world_scale_uv_operator_apply_scaling_density"
    bl_label = "Apply World Scale UV (Scaling Density)"
    bl_description = "Apply scaled UV with scaling density"
    bl_options = {'REGISTER', 'UNDO'}

    tgt_scaling_factor = FloatProperty(
        name="Scaling Factor",
        default=1.0,
        max=1000.0,
        min=0.00001
    )
    origin = EnumProperty(
        name="Origin",
        description="Aspect Origin",
        items=[
            ('CENTER', "Center", "Center"),
            ('LEFT_TOP', "Left Top", "Left Bottom"),
            ('LEFT_CENTER', "Left Center", "Left Center"),
            ('LEFT_BOTTOM', "Left Bottom", "Left Bottom"),
            ('CENTER_TOP', "Center Top", "Center Top"),
            ('CENTER_BOTTOM', "Center Bottom", "Center Bottom"),
            ('RIGHT_TOP', "Right Top", "Right Top"),
            ('RIGHT_CENTER', "Right Center", "Right Center"),
            ('RIGHT_BOTTOM', "Right Bottom", "Right Bottom")

        ],
        default='CENTER'
    )
    src_density = FloatProperty(
        name="Density",
        description="Source Texel Density",
        default=0.0,
        min=0.0,
        options={'HIDDEN'}
    )
    same_density = BoolProperty(
        name="Same Density",
        description="Apply same density",
        default=False,
        options={'HIDDEN'}
    )
    show_dialog = BoolProperty(
        name="Show Diaglog Menu",
        description="Show dialog menu if true",
        default=True,
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    def __init__(self):
        self.__impl = impl.ApplyScalingDensityImpl()

    @classmethod
    def poll(cls, context):
        return impl.ApplyScalingDensityImpl.poll(context)

    def draw(self, context):
        self.__impl.draw(self, context)

    def invoke(self, context, event):
        return self.__impl.invoke(self, context, event)

    def execute(self, context):
        return self.__impl.execute(self, context)


@BlClassRegistry(legacy=True)
class MUV_OT_WorldScaleUV_ApplyProportionalToMesh(bpy.types.Operator):
    """
    Operation class: Apply scaled UV (Proportional to mesh)
    """

    bl_idname = "uv.muv_world_scale_uv_operator_apply_proportional_to_mesh"
    bl_label = "Apply World Scale UV (Proportional to mesh)"
    bl_description = "Apply scaled UV proportionaled to mesh"
    bl_options = {'REGISTER', 'UNDO'}

    origin = EnumProperty(
        name="Origin",
        description="Aspect Origin",
        items=[
            ('CENTER', "Center", "Center"),
            ('LEFT_TOP', "Left Top", "Left Bottom"),
            ('LEFT_CENTER', "Left Center", "Left Center"),
            ('LEFT_BOTTOM', "Left Bottom", "Left Bottom"),
            ('CENTER_TOP', "Center Top", "Center Top"),
            ('CENTER_BOTTOM', "Center Bottom", "Center Bottom"),
            ('RIGHT_TOP', "Right Top", "Right Top"),
            ('RIGHT_CENTER', "Right Center", "Right Center"),
            ('RIGHT_BOTTOM', "Right Bottom", "Right Bottom")

        ],
        default='CENTER'
    )
    src_density = FloatProperty(
        name="Source Density",
        description="Source Texel Density",
        default=0.0,
        min=0.0,
        options={'HIDDEN'}
    )
    src_uv_area = FloatProperty(
        name="Source UV Area",
        description="Source UV Area",
        default=0.0,
        min=0.0,
        options={'HIDDEN'}
    )
    src_mesh_area = FloatProperty(
        name="Source Mesh Area",
        description="Source Mesh Area",
        default=0.0,
        min=0.0,
        options={'HIDDEN'}
    )
    show_dialog = BoolProperty(
        name="Show Diaglog Menu",
        description="Show dialog menu if true",
        default=True,
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    def __init__(self):
        self.__impl = impl.ApplyProportionalToMeshImpl()

    @classmethod
    def poll(cls, context):
        return impl.ApplyProportionalToMeshImpl.poll(context)

    def draw(self, context):
        self.__impl.draw(self, context)

    def invoke(self, context, event):
        return self.__impl.invoke(self, context, event)

    def execute(self, context):
        return self.__impl.execute(self, context)
