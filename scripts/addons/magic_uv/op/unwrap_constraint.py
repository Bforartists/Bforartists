# SPDX-FileCopyrightText: 2017-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"

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
    # only 'VIEW_3D' space is allowed to execute
    if not common.is_valid_space(context, ['VIEW_3D']):
        return False

    objs = common.get_uv_editable_objects(context)
    if not objs:
        return False

    # only edit mode is allowed to execute
    if context.object.mode != 'EDIT':
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

    bl_idname = "uv.muv_unwrap_constraint"
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
        objs = common.get_uv_editable_objects(context)

        uv_list = {}    # { Object: uv_list }
        for obj in objs:
            bm = bmesh.from_edit_mesh(obj.data)
            if common.check_version(2, 73, 0) >= 0:
                bm.faces.ensure_lookup_table()

            # bpy.ops.uv.unwrap() makes one UV map at least
            if not bm.loops.layers.uv:
                self.report({'WARNING'},
                            "Object {} must have more than one UV map"
                            .format(obj.name))
                return {'CANCELLED'}
            uv_layer = bm.loops.layers.uv.verify()

            # get original UV coordinate
            faces = [f for f in bm.faces if f.select]
            uv_list[obj] = []
            for f in faces:
                uvs = [l[uv_layer].uv.copy() for l in f.loops]
                uv_list[obj].append(uvs)

        # unwrap
        bpy.ops.uv.unwrap(
            method=self.method,
            fill_holes=self.fill_holes,
            correct_aspect=self.correct_aspect,
            use_subsurf_data=self.use_subsurf_data,
            margin=self.margin)

        # when U/V-Constraint is checked, revert original coordinate
        for obj in objs:
            bm = bmesh.from_edit_mesh(obj.data)
            if common.check_version(2, 73, 0) >= 0:
                bm.faces.ensure_lookup_table()
            uv_layer = bm.loops.layers.uv.verify()
            faces = [f for f in bm.faces if f.select]

            for f, uvs in zip(faces, uv_list[obj]):
                for l, uv in zip(f.loops, uvs):
                    if self.u_const:
                        l[uv_layer].uv.x = uv.x
                    if self.v_const:
                        l[uv_layer].uv.y = uv.y

            # update mesh
            bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}
