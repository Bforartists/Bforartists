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
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
)

from ...utils.bl_class_registry import BlClassRegistry
from ...utils.property_class_registry import PropertyClassRegistry
from ...impl import unwrap_constraint_impl as impl


@PropertyClassRegistry(legacy=True)
class _Properties:
    idname = "unwrap_constraint"

    @classmethod
    def init_props(cls, scene):
        scene.muv_unwrap_constraint_enabled = BoolProperty(
            name="Unwrap Constraint Enabled",
            description="Unwrap Constraint is enabled",
            default=False
        )
        scene.muv_unwrap_constraint_u_const = BoolProperty(
            name="U-Constraint",
            description="Keep UV U-axis coordinate",
            default=False
        )
        scene.muv_unwrap_constraint_v_const = BoolProperty(
            name="V-Constraint",
            description="Keep UV V-axis coordinate",
            default=False
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_unwrap_constraint_enabled
        del scene.muv_unwrap_constraint_u_const
        del scene.muv_unwrap_constraint_v_const


@BlClassRegistry(legacy=True)
class MUV_OT_UnwrapConstraint(bpy.types.Operator):
    """
    Operation class: Unwrap with constrain UV coordinate
    """

    bl_idname = "uv.muv_unwrap_constraint_operator"
    bl_label = "Unwrap Constraint"
    bl_description = "Unwrap while keeping uv coordinate"
    bl_options = {'REGISTER', 'UNDO'}

    # property for original unwrap
    method = EnumProperty(
        name="Method",
        description="Unwrapping method",
        items=[
            ('ANGLE_BASED', 'Angle Based', 'Angle Based'),
            ('CONFORMAL', 'Conformal', 'Conformal')
        ],
        default='ANGLE_BASED')
    fill_holes = BoolProperty(
        name="Fill Holes",
        description="Virtual fill holes in meshes before unwrapping",
        default=True)
    correct_aspect = BoolProperty(
        name="Correct Aspect",
        description="Map UVs taking image aspect ratio into account",
        default=True)
    use_subsurf_data = BoolProperty(
        name="Use Subsurf Modifier",
        description="""Map UVs taking vertex position after subsurf
                       into account""",
        default=False)
    margin = FloatProperty(
        name="Margin",
        description="Space between islands",
        max=1.0,
        min=0.0,
        default=0.001)

    # property for this operation
    u_const = BoolProperty(
        name="U-Constraint",
        description="Keep UV U-axis coordinate",
        default=False
    )
    v_const = BoolProperty(
        name="V-Constraint",
        description="Keep UV V-axis coordinate",
        default=False
    )

    def __init__(self):
        self.__impl = impl.UnwrapConstraintImpl()

    @classmethod
    def poll(cls, context):
        return impl.UnwrapConstraintImpl.poll(context)

    def execute(self, context):
        return self.__impl.execute(self, context)
