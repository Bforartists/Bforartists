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

# <pep8 compliant>

import bpy
import math

from bpy.types import (
    PoseBone,
    ShapeKey,
)

# may be overwritten by user!
from . import USE_VERBOSE


# -----------------------------------------------------------------------------
# Utilities

def coords_to_loc_3d(context, coords_2d_seq, depth_location):
    from bpy_extras.view3d_utils import region_2d_to_location_3d
    region = context.region
    rv3d = context.region_data

    return tuple((
        region_2d_to_location_3d(region, rv3d, mval, depth_location)
        for mval in coords_2d_seq
    ))


def calc_view_vector(context):
    rv3d = context.region_data
    viewinv = rv3d.view_matrix.inverted()
    return -viewinv.col[2].xyz.normalized()


def pose_bone_calc_transform_orientation(pose_bone):
    ob_pose = pose_bone.id_data
    return (ob_pose.matrix_world @ pose_bone.matrix).inverted().to_3x3()


def pose_bone_rotation_attr_from_mode(pose_bone):
    return {
        # XYZ or any re-ordering maps to euler
        'AXIS_ANGLE': 'rotation_axis_angle',
        'QUATERNION': 'rotation_quaternion',
    }.get(pose_bone.rotation_mode, 'rotation_euler')


def pose_bone_autokey(pose_bone, attr_key, attr_lock):
    ob_pose = pose_bone.id_data
    value = getattr(pose_bone, attr_key)
    locks = getattr(pose_bone, attr_lock)
    data_path = pose_bone.path_from_id() + "." + attr_key
    for i in range(len(value)):
        # needed because quaternion has only 3 locks
        try:
            is_lock = locks[i]
        except IndexError:
            is_lock = False

        ob_pose.keyframe_insert(data_path, i)


def pose_bone_set_attr_with_locks(pose_bone, attr_key, attr_lock, value):
    ob_pose = pose_bone.id_data
    locks = getattr(pose_bone, attr_lock)
    if not any(locks):
        setattr(pose_bone, attr_key, value)
    else:
        # keep wrapped
        value_wrap = getattr(pose_bone, attr_key)
        # update from 'value' for unlocked axis
        value_new = value_wrap.copy()
        for i in range(len(value)):
            # needed because quaternion has only 3 locks
            try:
                is_lock = locks[i]
            except IndexError:
                is_lock = False

            if not is_lock:
                value_new[i] = value[i]
        # Set all at once instead of per-axis to avoid multiple RNA updates.
        value_wrap[:] = value_new


# -----------------------------------------------------------------------------
# Interactivity class
#
# Note, this could use asyncio, we may want to investigate that!
# for now generators work fine.

def widget_iter_template(context, mpr, ob, fmap, fmap_target):
    # generic initialize
    if USE_VERBOSE:
        print("(iter-init)")

    # invoke()
    # ...
    if USE_VERBOSE:
        print("(iter-invoke)")

    context.area.header_text_set("No operation found for: {}".format(fmap.name))

    event = yield
    tweak = set()

    # modal(), first step
    # Keep this loop fast! runs on mouse-movement.
    while True:
        event, tweak_next = yield
        if event in {True, False}:
            break
        if event.type == 'INBETWEEN_MOUSEMOVE':
            continue
        tweak = tweak_next

        if USE_VERBOSE:
            print("(iter-modal)", event, tweak)

    # exit()
    if USE_VERBOSE:
        print("(iter-exit)", event)

    context.area.header_text_set(None)


def widget_iter_pose_translate(context, mpr, ob, fmap, fmap_target):
    from mathutils import (
        Vector,
    )
    # generic initialize
    if USE_VERBOSE:
        print("(iter-init)")

    context.area.header_text_set("Translating face-map: {}".format(fmap.name))

    # invoke()
    # ...
    if USE_VERBOSE:
        print("(iter-invoke)")
    event = yield
    tweak = set()

    # modal(), first step
    mval_init = Vector((event.mouse_region_x, event.mouse_region_y))
    mval = mval_init.copy()

    # impl vars
    pose_bone = fmap_target
    del fmap_target

    tweak_attr = "location"
    tweak_attr_lock = "lock_location"

    # Could use face-map center too
    # Don't update these while interacting
    bone_matrix_init = pose_bone.matrix.copy()
    depth_location = bone_matrix_init.to_translation()

    world_to_local_3x3 = pose_bone_calc_transform_orientation(pose_bone)

    loc_init = pose_bone.location.copy()

    # Keep this loop fast! runs on mouse-movement.
    while True:
        event, tweak_next = yield
        if event in {True, False}:
            break
        if event.type == 'INBETWEEN_MOUSEMOVE':
            continue
        tweak = tweak_next

        if USE_VERBOSE:
            print("(iter-modal)", event, tweak)

        mval = Vector((event.mouse_region_x, event.mouse_region_y))

        co_init, co = coords_to_loc_3d(context, (mval_init, mval), depth_location)
        loc_delta = world_to_local_3x3 @ (co - co_init)

        input_scale = 1.0
        is_precise = 'PRECISE' in tweak
        if is_precise:
            input_scale /= 10.0

        loc_delta *= input_scale
        # relative snap
        if 'SNAP' in tweak:
            loc_delta[:] = [round(v, 2 if is_precise else 1) for v in loc_delta]

        final_value = loc_init + loc_delta
        pose_bone_set_attr_with_locks(pose_bone, tweak_attr, tweak_attr_lock, final_value)

    # exit()
    if USE_VERBOSE:
        print("(iter-exit)", event)
    if event is True:  # cancel
        pose_bone.location = loc_init
    else:
        pose_bone_autokey(pose_bone, tweak_attr, tweak_attr_lock)

    context.area.header_text_set(None)


def widget_iter_pose_rotate(context, mpr, ob, fmap, fmap_target):
    from mathutils import (
        Vector,
        Quaternion,
    )
    # generic initialize
    if USE_VERBOSE:
        print("(iter-init)")

    tweak_attr = pose_bone_rotation_attr_from_mode(fmap_target)
    context.area.header_text_set("Rotating ({}) face-map: {}".format(tweak_attr, fmap.name))
    tweak_attr_lock = "lock_rotation"

    # invoke()
    # ...
    if USE_VERBOSE:
        print("(iter-invoke)")
    event = yield
    tweak = set()

    # modal(), first step
    mval_init = Vector((event.mouse_region_x, event.mouse_region_y))
    mval = mval_init.copy()

    # impl vars
    pose_bone = fmap_target
    del fmap_target

    # Could use face-map center too
    # Don't update these while interacting
    bone_matrix_init = pose_bone.matrix.copy()
    depth_location = bone_matrix_init.to_translation()
    rot_center = bone_matrix_init.to_translation()

    world_to_local_3x3 = pose_bone_calc_transform_orientation(pose_bone)

    # for rotation
    local_view_vector = (calc_view_vector(context) @ world_to_local_3x3).normalized()

    rot_init = getattr(pose_bone, tweak_attr).copy()

    # Keep this loop fast! runs on mouse-movement.
    while True:
        event, tweak_next = yield
        if event in {True, False}:
            break
        if event.type == 'INBETWEEN_MOUSEMOVE':
            continue
        tweak = tweak_next

        if USE_VERBOSE:
            print("(iter-modal)", event, tweak)

        mval = Vector((event.mouse_region_x, event.mouse_region_y))

        # calculate rotation matrix from input
        co_init, co = coords_to_loc_3d(context, (mval_init, mval), depth_location)
        # co_delta = world_to_local_3x3 @ (co - co_init)

        input_scale = 1.0
        is_precise = 'PRECISE' in tweak
        if is_precise:
            input_scale /= 10.0

        if False:
            # Dial logic, not obvious enough unless we show graphical line to center...
            # but this is typically too close to the center of the face-map.
            rot_delta = (co_init - rot_center).rotation_difference(co - rot_center).to_matrix()
        else:
            # Steering wheel logic, left to rotate left, right to rotate right :)
            # use X-axis only

            # Calculate imaginary point as if mouse was moved 100px to the right
            # then transform to local orientation and use to see where the cursor is

            rotate_angle = ((mval.x - mval_init.x) / 100.0)
            rotate_angle *= input_scale

            if 'SNAP' in tweak:
                v = math.radians(1.0 if is_precise else 15.0)
                rotate_angle = round(rotate_angle / v) * v
                del v

            rot_delta = Quaternion(local_view_vector, rotate_angle).to_matrix()

            # rot_delta = (co_init - rot_center).rotation_difference(co - rot_center).to_matrix()

        rot_matrix = rot_init.to_matrix()
        rot_matrix = rot_matrix @ rot_delta

        if tweak_attr == "rotation_quaternion":
            final_value = rot_matrix.to_quaternion()
        elif tweak_attr == "rotation_euler":
            final_value = rot_matrix.to_euler(pose_bone.rotation_mode, rot_init)
        else:
            assert(tweak_attr == "rotation_axis_angle")
            final_value = rot_matrix.to_quaternion().to_axis_angle()
            final_value = (*final_value[0], final_value[1])  # flatten

        pose_bone_set_attr_with_locks(pose_bone, tweak_attr, tweak_attr_lock, final_value)

    # exit()
    if USE_VERBOSE:
        print("(iter-exit)", event)
    if event is True:  # cancel
        setattr(pose_bone, tweak_attr, rot_init)
    else:
        pose_bone_autokey(pose_bone, tweak_attr, tweak_attr_lock)

    context.area.header_text_set(None)


def widget_iter_pose_scale(context, mpr, ob, fmap, fmap_target):
    from mathutils import (
        Vector,
    )
    # generic initialize
    if USE_VERBOSE:
        print("(iter-init)")

    context.area.header_text_set("Scale face-map: {}".format(fmap.name))

    # invoke()
    # ...
    if USE_VERBOSE:
        print("(iter-invoke)")
    event = yield
    tweak = set()

    # modal(), first step
    mval_init = Vector((event.mouse_region_x, event.mouse_region_y))
    mval = mval_init.copy()

    # impl vars
    pose_bone = fmap_target
    del fmap_target
    tweak_attr = "scale"
    tweak_attr_lock = "lock_scale"

    scale_init = pose_bone.scale.copy()

    # Keep this loop fast! runs on mouse-movement.
    while True:
        event, tweak_next = yield
        if event in {True, False}:
            break
        if event.type == 'INBETWEEN_MOUSEMOVE':
            continue
        tweak = tweak_next

        if USE_VERBOSE:
            print("(iter-modal)", event, tweak)

        mval = Vector((event.mouse_region_x, event.mouse_region_y))

        input_scale = 1.0
        is_precise = 'PRECISE' in tweak
        if is_precise:
            input_scale /= 10.0

        scale_factor = ((mval.y - mval_init.y) / 200.0) * input_scale
        if 'SNAP' in tweak:
            # relative
            scale_factor = round(scale_factor, 2 if is_precise else 1)
        final_value = scale_init * (1.0 + scale_factor)
        pose_bone_set_attr_with_locks(pose_bone, tweak_attr, tweak_attr_lock, final_value)

    # exit()
    if USE_VERBOSE:
        print("(iter-exit)", event)
    if event is True:  # cancel
        pose_bone.scale = scale_init
    else:
        pose_bone_autokey(pose_bone, tweak_attr, tweak_attr_lock)

    context.area.header_text_set(None)


def widget_iter_shapekey(context, mpr, ob, fmap, fmap_target):
    from mathutils import (
        Vector,
    )
    # generic initialize
    if USE_VERBOSE:
        print("(iter-init)")

    context.area.header_text_set("ShapeKey face-map: {}".format(fmap.name))

    # invoke()
    # ...
    if USE_VERBOSE:
        print("(iter-invoke)")
    event = yield
    tweak = set()

    # modal(), first step
    mval_init = Vector((event.mouse_region_x, event.mouse_region_y))
    mval = mval_init.copy()

    # impl vars
    shape = fmap_target
    del fmap_target

    value_init = shape.value

    # Keep this loop fast! runs on mouse-movement.
    while True:
        event, tweak_next = yield
        if event in {True, False}:
            break
        if event.type == 'INBETWEEN_MOUSEMOVE':
            continue
        tweak = tweak_next

        if USE_VERBOSE:
            print("(iter-modal)", event, tweak)

        mval = Vector((event.mouse_region_x, event.mouse_region_y))

        input_scale = 1.0
        is_precise = 'PRECISE' in tweak
        if is_precise:
            input_scale /= 10.0

        final_value = value_init + ((mval.y - mval_init.y) / 200.0) * input_scale
        if 'SNAP' in tweak:
            final_value = round(final_value, 2 if is_precise else 1)

        shape.value = final_value

    # exit()
    if USE_VERBOSE:
        print("(iter-exit)", event)
    if event is True:  # cancel
        shape.value = scale_init
    else:
        shape.id_data.keyframe_insert(shape.path_from_id() + ".value")

    context.area.header_text_set(None)


# -------------------------
# Non Interactive Functions

def widget_clear_location(context, mpr, ob, fmap, fmap_target):

    if isinstance(fmap_target, ShapeKey):
        shape = fmap_target
        del fmap_target
        # gets clamped
        shape.value = 0.0
    elif isinstance(fmap_target, PoseBone):
        pose_bone = fmap_target
        del fmap_target

        tweak_attr = "location"
        tweak_attr_lock = "lock_location"

        pose_bone_set_attr_with_locks(pose_bone, tweak_attr, tweak_attr_lock, (0.0, 0.0, 0.0))
        pose_bone_autokey(pose_bone, tweak_attr, tweak_attr_lock)


def widget_clear_rotation(context, mpr, ob, fmap, fmap_target):

    if isinstance(fmap_target, PoseBone):
        pose_bone = fmap_target
        del fmap_target
        tweak_attr = pose_bone_rotation_attr_from_mode(pose_bone)
        tweak_attr_lock = "lock_rotation"

        value = getattr(pose_bone, tweak_attr).copy()
        if tweak_attr == 'rotation_axis_angle':
            # keep the axis
            value[3] = 0.0
        elif tweak_attr == 'rotation_quaternion':
            value.identity()
        elif tweak_attr == 'rotation_euler':
            value.zero()

        pose_bone_set_attr_with_locks(pose_bone, tweak_attr, tweak_attr_lock, value)
        pose_bone_autokey(pose_bone, tweak_attr, tweak_attr_lock)


def widget_clear_scale(context, mpr, ob, fmap, fmap_target):

    if isinstance(fmap_target, PoseBone):
        pose_bone = fmap_target
        del fmap_target

        tweak_attr = "scale"
        tweak_attr_lock = "lock_scale"

        pose_bone_set_attr_with_locks(pose_bone, tweak_attr, tweak_attr_lock, (1.0, 1.0, 1.0))
        pose_bone_autokey(pose_bone, tweak_attr, tweak_attr_lock)
