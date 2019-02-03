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
__version__ = "6.0"
__date__ = "26 Jan 2019"

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
)
import bmesh

from .. import common
from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry
from ..utils import compatibility as compat


def _is_valid_context(context):
    obj = context.object

    # only edit mode is allowed to execute
    if obj is None:
        return False
    if obj.type != 'MESH':
        return False
    if context.object.mode != 'EDIT':
        return False

    # only 'VIEW_3D' space is allowed to execute
    for space in context.area.spaces:
        if space.type == 'VIEW_3D':
            break
    else:
        return False

    return True


@PropertyClassRegistry()
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
@compat.make_annotations
class MUV_OT_UnwrapConstraint(bpy.types.Operator):
    """
    Operation class: Unwrap with constrain UV coordinate
    """

    bl_idname = "uv.muv_ot_unwrap_constraint"
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

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    def execute(self, context):
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        if common.check_version(2, 73, 0) >= 0:
            bm.faces.ensure_lookup_table()

        # bpy.ops.uv.unwrap() makes one UV map at least
        if not bm.loops.layers.uv:
            self.report({'WARNING'}, "Object must have more than one UV map")
            return {'CANCELLED'}
        uv_layer = bm.loops.layers.uv.verify()

        # get original UV coordinate
        faces = [f for f in bm.faces if f.select]
        uv_list = []
        for f in faces:
            uvs = [l[uv_layer].uv.copy() for l in f.loops]
            uv_list.append(uvs)

        # unwrap
        bpy.ops.uv.unwrap(
            method=self.method,
            fill_holes=self.fill_holes,
            correct_aspect=self.correct_aspect,
            use_subsurf_data=self.use_subsurf_data,
            margin=self.margin)

        # when U/V-Constraint is checked, revert original coordinate
        for f, uvs in zip(faces, uv_list):
            for l, uv in zip(f.loops, uvs):
                if self.u_const:
                    l[uv_layer].uv.x = uv.x
                if self.v_const:
                    l[uv_layer].uv.y = uv.y

        # update mesh
        bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}
