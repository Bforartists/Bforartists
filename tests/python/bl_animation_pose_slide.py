# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy_extras import anim_utils

import unittest
import sys
import pathlib

"""
blender -b --factory-startup --python tests/python/bl_animation_pose_slide.py
"""


def _get_view3d_context():
    ctx = bpy.context.copy()

    for area in bpy.context.window.screen.areas:
        if area.type != 'VIEW_3D':
            continue

        ctx['area'] = area
        ctx['space'] = area.spaces.active
        break

    return ctx


_BONE_NAME = "bone"
_CUSTOM_PROP = "test"


class BreakdownerTestPoseBone(unittest.TestCase):
    armature_ob: bpy.types.Object
    pose_bone: bpy.types.PoseBone

    def setUp(self) -> None:
        bpy.ops.wm.read_homefile(use_factory_startup=True)
        armature = bpy.data.armatures.new("armature")
        self.armature_ob = bpy.data.objects.new("armature_ob", armature)
        bpy.context.scene.collection.objects.link(self.armature_ob)
        bpy.context.view_layer.objects.active = self.armature_ob
        bpy.ops.object.mode_set(mode='EDIT')
        armature.edit_bones.new(_BONE_NAME)
        bpy.ops.object.mode_set(mode='POSE')
        self.pose_bone = self.armature_ob.pose.bones[_BONE_NAME]
        self.pose_bone.rotation_mode = 'XYZ'
        self.pose_bone[_CUSTOM_PROP] = 1.0
        self.pose_bone.select = True

    def _keyframe_all(self):
        self.pose_bone.keyframe_insert("location")
        self.pose_bone.keyframe_insert("rotation_euler")
        self.pose_bone.keyframe_insert("scale")
        self.pose_bone.keyframe_insert("bbone_curveinx")
        self.pose_bone.keyframe_insert(f'["{_CUSTOM_PROP}"]')

    def test_break_down_no_keys(self):
        # The case of no keys will produce no interpolation.
        self.pose_bone.location = (1, 1, 1)
        with bpy.context.temp_override(**_get_view3d_context()):
            bpy.ops.pose.breakdown(factor=0.5)

        for i in range(3):
            self.assertAlmostEqual(self.pose_bone.location[i], 1, 3)

    def test_break_down_single_key(self):
        # Creating a breakdown with a single key will not change the current value
        # but adds a key if autokeying is enabled.
        bpy.context.scene.frame_set(0)
        self.pose_bone.location = (1, 1, 1)
        self.pose_bone.keyframe_insert("location")

        bpy.context.scene.frame_set(10)

        with bpy.context.temp_override(**_get_view3d_context()):
            bpy.ops.pose.breakdown(factor=0.5)

        action = self.armature_ob.animation_data.action
        slot = self.armature_ob.animation_data.action_slot
        channelbag = anim_utils.action_get_channelbag_for_slot(action, slot)
        self.assertEqual(len(channelbag.fcurves), 3)
        self.assertEqual(len(channelbag.fcurves[0].keyframe_points), 1)

        for i in range(3):
            self.assertAlmostEqual(self.pose_bone.location[i], 1, 3)

        bpy.context.scene.tool_settings.use_keyframe_insert_auto = True

        with bpy.context.temp_override(**_get_view3d_context()):
            bpy.ops.pose.breakdown(factor=0.5)

        for i in range(3):
            self.assertAlmostEqual(self.pose_bone.location[i], 1, 3)

        # The key count depends on the setting "Only insert available" in the user preferences.
        self.assertEqual(len(channelbag.fcurves), 10)
        self.assertEqual(len(channelbag.fcurves[0].keyframe_points), 2)

    def test_break_down_all_properties(self):
        # By default the pose slide operators act on location, rotation, scale, bbone properties and custom properties.
        bpy.context.scene.frame_set(0)
        self.pose_bone.location = (1, 1, 1)
        self.pose_bone.rotation_euler = (1, 1, 1)
        self.pose_bone.scale = (1, 1, 1)
        self.pose_bone.bbone_curveinx = 1
        self.pose_bone[_CUSTOM_PROP] = 1.0
        self._keyframe_all()

        bpy.context.scene.frame_set(10)
        self.pose_bone.location = (2, 2, 2)
        self.pose_bone.rotation_euler = (2, 2, 2)
        self.pose_bone.scale = (2, 2, 2)
        self.pose_bone.bbone_curveinx = 2
        self.pose_bone[_CUSTOM_PROP] = 2.0
        self._keyframe_all()

        action = self.armature_ob.animation_data.action
        slot = self.armature_ob.animation_data.action_slot
        channelbag = anim_utils.action_get_channelbag_for_slot(action, slot)
        self.assertEqual(len(channelbag.fcurves), 11)

        bpy.context.scene.tool_settings.use_keyframe_insert_auto = True

        bpy.context.scene.frame_set(1)
        with bpy.context.temp_override(**_get_view3d_context()):
            # The prev and next frames have to be specified in order for this to work correctly.
            bpy.ops.pose.breakdown(factor=0.5, prev_frame=0, next_frame=10)

        for i in range(3):
            self.assertAlmostEqual(self.pose_bone.location[i], 1.5, 3)
            self.assertAlmostEqual(self.pose_bone.rotation_euler[i], 1.5, 3)
            self.assertAlmostEqual(self.pose_bone.scale[i], 1.5, 3)

        self.assertAlmostEqual(self.pose_bone.bbone_curveinx, 1.5, 3)
        self.assertAlmostEqual(self.pose_bone[_CUSTOM_PROP], 1.5, 3)

    def test_break_down_location(self):
        # The pose slide operators can constrain to a single property type.
        # All other properties should not be modified.
        bpy.context.scene.frame_set(0)
        self.pose_bone.location = (1, 1, 1)
        self.pose_bone.rotation_euler = (1, 1, 1)
        self._keyframe_all()

        bpy.context.scene.frame_set(10)
        self.pose_bone.location = (2, 2, 2)
        self.pose_bone.rotation_euler = (2, 2, 2)
        self._keyframe_all()

        bpy.context.scene.tool_settings.use_keyframe_insert_auto = True

        bpy.context.scene.frame_set(1)
        with bpy.context.temp_override(**_get_view3d_context()):
            # The prev and next frames have to be specified in order for this to work correctly.
            bpy.ops.pose.breakdown(factor=0.5, prev_frame=0, next_frame=10, channels='LOC')

        for i in range(3):
            self.assertAlmostEqual(self.pose_bone.location[i], 1.5, 3)
            # Rotation should not be modified.
            self.assertAlmostEqual(self.pose_bone.rotation_euler[i], 1.0279, 3)

    def test_break_down_location_x(self):
        # The slider operators can constrain to a single axis.
        bpy.context.scene.frame_set(0)
        self.pose_bone.location = (1, 1, 1)
        self._keyframe_all()

        bpy.context.scene.frame_set(10)
        self.pose_bone.location = (2, 2, 2)
        self._keyframe_all()

        bpy.context.scene.frame_set(1)
        with bpy.context.temp_override(**_get_view3d_context()):
            # The prev and next frames have to be specified in order for this to work correctly.
            bpy.ops.pose.breakdown(factor=0.5, prev_frame=0, next_frame=10, channels='LOC', axis_lock="X")

        self.assertAlmostEqual(self.pose_bone.location[0], 1.5, 3)
        self.assertAlmostEqual(self.pose_bone.location[1], 1.0279, 3)
        self.assertAlmostEqual(self.pose_bone.location[2], 1.0279, 3)


def main():
    global args
    import argparse

    argv = [sys.argv[0]]
    if '--' in sys.argv:
        argv += sys.argv[sys.argv.index('--') + 1:]

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        dest="output_dir",
        type=pathlib.Path,
        default=pathlib.Path("."),
        help="Where to output temp saved blendfiles",
        required=False,
    )

    args, remaining = parser.parse_known_args(argv)

    unittest.main(argv=remaining)


if __name__ == "__main__":
    main()
