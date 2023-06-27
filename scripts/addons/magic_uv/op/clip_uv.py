# SPDX-FileCopyrightText: 2020-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Dusan Stevanovic, Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"


import math

import bpy
import bmesh
from mathutils import Vector
from bpy.props import BoolProperty, FloatVectorProperty

from .. import common
from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry
from ..utils import compatibility as compat


def _is_valid_context(context):
    # 'IMAGE_EDITOR' and 'VIEW_3D' space is allowed to execute.
    # If 'View_3D' space is not allowed, you can't find option in Tool-Shelf
    # after the execution
    if not common.is_valid_space(context, ['IMAGE_EDITOR', 'VIEW_3D']):
        return False

    objs = common.get_uv_editable_objects(context)
    if not objs:
        return False

    # only edit mode is allowed to execute
    if context.object.mode != 'EDIT':
        return False

    return True


def round_clip_uv_range(v):
    sign = 1 if v >= 0.0 else -1
    return int((math.fabs(v) + 0.25) / 0.5) * 0.5 * sign


def get_clip_uv_range_max(self):
    return self.get('muv_clip_uv_range_max', (0.5, 0.5))


def set_clip_uv_range_max(self, value):
    u = round_clip_uv_range(value[0])
    u = 0.5 if u <= 0.5 else u
    v = round_clip_uv_range(value[1])
    v = 0.5 if v <= 0.5 else v
    self['muv_clip_uv_range_max'] = (u, v)


def get_clip_uv_range_min(self):
    return self.get('muv_clip_uv_range_min', (-0.5, -0.5))


def set_clip_uv_range_min(self, value):
    u = round_clip_uv_range(value[0])
    u = -0.5 if u >= -0.5 else u
    v = round_clip_uv_range(value[1])
    v = -0.5 if v >= -0.5 else v
    self['muv_clip_uv_range_min'] = (u, v)


@PropertyClassRegistry()
class _Properties:
    idname = "clip_uv"

    @classmethod
    def init_props(cls, scene):
        scene.muv_clip_uv_enabled = BoolProperty(
            name="Clip UV Enabled",
            description="Clip UV is enabled",
            default=False
        )

        scene.muv_clip_uv_range_max = FloatVectorProperty(
            name="Range Max",
            description="Max UV coordinates of the range to be clipped",
            size=2,
            default=(0.5, 0.5),
            min=0.5,
            step=50,
            get=get_clip_uv_range_max,
            set=set_clip_uv_range_max,
        )

        scene.muv_clip_uv_range_min = FloatVectorProperty(
            name="Range Min",
            description="Min UV coordinates of the range to be clipped",
            size=2,
            default=(-0.5, -0.5),
            max=-0.5,
            step=50,
            get=get_clip_uv_range_min,
            set=set_clip_uv_range_min,
        )

        # TODO: add option to preserve UV island

    @classmethod
    def del_props(cls, scene):
        del scene.muv_clip_uv_range_max
        del scene.muv_clip_uv_range_min


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_ClipUV(bpy.types.Operator):

    bl_idname = "uv.muv_clip_uv"
    bl_label = "Clip UV"
    bl_description = "Clip selected UV in the specified range"
    bl_options = {'REGISTER', 'UNDO'}

    clip_uv_range_max = FloatVectorProperty(
        name="Range Max",
        description="Max UV coordinates of the range to be clipped",
        size=2,
        default=(0.5, 0.5),
        min=0.5,
        step=50,
    )

    clip_uv_range_min = FloatVectorProperty(
        name="Range Min",
        description="Min UV coordinates of the range to be clipped",
        size=2,
        default=(-0.5, -0.5),
        max=-0.5,
        step=50,
    )

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    def execute(self, context):
        objs = common.get_uv_editable_objects(context)

        for obj in objs:
            bm = common.create_bmesh(obj)

            if not bm.loops.layers.uv:
                self.report({'WARNING'},
                            "Object {} must have more than one UV map"
                            .format(obj.name))
                return {'CANCELLED'}

            uv_layer = bm.loops.layers.uv.verify()

            for face in bm.faces:
                if not face.select:
                    continue

                selected_loops = [
                    l for l in face.loops
                    if l[uv_layer].select or
                    context.scene.tool_settings.use_uv_select_sync
                ]
                if not selected_loops:
                    continue

                # average of UV coordinates on the face
                max_uv = Vector((-10000000.0, -10000000.0))
                min_uv = Vector((10000000.0, 10000000.0))
                for l in selected_loops:
                    uv = l[uv_layer].uv
                    max_uv.x = max(max_uv.x, uv.x)
                    max_uv.y = max(max_uv.y, uv.y)
                    min_uv.x = min(min_uv.x, uv.x)
                    min_uv.y = min(min_uv.y, uv.y)

                # clip
                move_uv = Vector((0.0, 0.0))
                clip_size = Vector(self.clip_uv_range_max) - \
                    Vector(self.clip_uv_range_min)
                if max_uv.x > self.clip_uv_range_max[0]:
                    target_x = math.fmod(max_uv.x - self.clip_uv_range_min[0],
                                         clip_size.x)
                    if target_x < 0.0:
                        target_x += clip_size.x
                    target_x += self.clip_uv_range_min[0]
                    move_uv.x = target_x - max_uv.x
                if min_uv.x < self.clip_uv_range_min[0]:
                    target_x = math.fmod(min_uv.x - self.clip_uv_range_min[0],
                                         clip_size.x)
                    if target_x < 0.0:
                        target_x += clip_size.x
                    target_x += self.clip_uv_range_min[0]
                    move_uv.x = target_x - min_uv.x
                if max_uv.y > self.clip_uv_range_max[1]:
                    target_y = math.fmod(max_uv.y - self.clip_uv_range_min[1],
                                         clip_size.y)
                    if target_y < 0.0:
                        target_y += clip_size.y
                    target_y += self.clip_uv_range_min[1]
                    move_uv.y = target_y - max_uv.y
                if min_uv.y < self.clip_uv_range_min[1]:
                    target_y = math.fmod(min_uv.y - self.clip_uv_range_min[1],
                                         clip_size.y)
                    if target_y < 0.0:
                        target_y += clip_size.y
                    target_y += self.clip_uv_range_min[1]
                    move_uv.y = target_y - min_uv.y

                # update UV
                for l in selected_loops:
                    l[uv_layer].uv = l[uv_layer].uv + move_uv

            bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}
