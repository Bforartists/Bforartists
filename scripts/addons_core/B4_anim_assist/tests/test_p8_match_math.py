#!/usr/bin/env python
"""Unit tests for IK/FK matching math pure-Python helpers.

Tests that do NOT require Blender (AxisMask, ChannelFilter, mirror_name,
switch history, switch detect dataclasses).
"""

import sys
import os
import unittest

# Ensure the parent package is importable.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# AxisMask / ChannelFilter (pure dataclasses, no bpy needed)
# ---------------------------------------------------------------------------

class TestAxisMask(unittest.TestCase):

    def test_default_all_true(self):
        from core.p8_match_math import AxisMask
        m = AxisMask()
        self.assertTrue(m.x)
        self.assertTrue(m.y)
        self.assertTrue(m.z)
        self.assertTrue(m.any())

    def test_none(self):
        from core.p8_match_math import MATCH_NONE
        self.assertFalse(MATCH_NONE.x)
        self.assertFalse(MATCH_NONE.y)
        self.assertFalse(MATCH_NONE.z)
        self.assertFalse(MATCH_NONE.any())

    def test_partial(self):
        from core.p8_match_math import AxisMask
        m = AxisMask(True, False, True)
        self.assertTrue(m.any())
        self.assertEqual(m.as_tuple(), (True, False, True))

    def test_frozen(self):
        from core.p8_match_math import AxisMask
        m = AxisMask()
        with self.assertRaises(AttributeError):
            m.x = False


class TestChannelFilter(unittest.TestCase):

    def test_all(self):
        from core.p8_match_math import ChannelFilter
        cf = ChannelFilter.all()
        self.assertTrue(cf.location.any())
        self.assertTrue(cf.rotation.any())
        self.assertTrue(cf.scale.any())

    def test_loc_only(self):
        from core.p8_match_math import ChannelFilter
        cf = ChannelFilter.loc_only()
        self.assertTrue(cf.location.any())
        self.assertFalse(cf.rotation.any())
        self.assertFalse(cf.scale.any())

    def test_rot_only(self):
        from core.p8_match_math import ChannelFilter
        cf = ChannelFilter.rot_only()
        self.assertFalse(cf.location.any())
        self.assertTrue(cf.rotation.any())
        self.assertFalse(cf.scale.any())

    def test_scale_only(self):
        from core.p8_match_math import ChannelFilter
        cf = ChannelFilter.scale_only()
        self.assertFalse(cf.location.any())
        self.assertFalse(cf.rotation.any())
        self.assertTrue(cf.scale.any())

    def test_loc_rot(self):
        from core.p8_match_math import ChannelFilter
        cf = ChannelFilter.loc_rot()
        self.assertTrue(cf.location.any())
        self.assertTrue(cf.rotation.any())
        self.assertFalse(cf.scale.any())


# ---------------------------------------------------------------------------
# Mirror naming
# ---------------------------------------------------------------------------

class TestMirrorName(unittest.TestCase):

    def test_dot_L_to_R(self):
        from core.p8_match_math import mirror_name
        self.assertEqual(mirror_name("hand_ik.L"), "hand_ik.R")

    def test_dot_R_to_L(self):
        from core.p8_match_math import mirror_name
        self.assertEqual(mirror_name("foot_ik.R"), "foot_ik.L")

    def test_underscore_L(self):
        from core.p8_match_math import mirror_name
        self.assertEqual(mirror_name("hand_ik_L"), "hand_ik_R")

    def test_underscore_R(self):
        from core.p8_match_math import mirror_name
        self.assertEqual(mirror_name("hand_ik_R"), "hand_ik_L")

    def test_word_Left(self):
        from core.p8_match_math import mirror_name
        self.assertEqual(mirror_name("Left_hand"), "Right_hand")

    def test_word_Right(self):
        from core.p8_match_math import mirror_name
        self.assertEqual(mirror_name("Right_hand"), "Left_hand")

    def test_no_match(self):
        from core.p8_match_math import mirror_name
        self.assertEqual(mirror_name("spine_01"), "spine_01")


# ---------------------------------------------------------------------------
# MatchResult
# ---------------------------------------------------------------------------

class TestMatchResult(unittest.TestCase):

    def test_default(self):
        from core.p8_match_math import MatchResult
        r = MatchResult()
        self.assertIsNone(r.location)
        self.assertIsNone(r.rotation_euler)
        self.assertIsNone(r.scale)
        self.assertEqual(r.channels_written, [])


# ---------------------------------------------------------------------------
# Switch history (pure Python, no bpy)
# ---------------------------------------------------------------------------

class TestSwitchHistory(unittest.TestCase):

    def setUp(self):
        from core.p8_switch_history import clear_history
        clear_history()

    def test_push_and_get(self):
        from core.p8_switch_history import push_event, get_history, SwitchEvent
        e = SwitchEvent(frame=10, obj_name="Cube", bone_name="", prop_path='["space"]',
                        old_value=0, new_value=1)
        push_event(e)
        h = get_history()
        self.assertEqual(len(h), 1)
        self.assertEqual(h[0].frame, 10)

    def test_last_event(self):
        from core.p8_switch_history import push_event, get_last_event, SwitchEvent
        e1 = SwitchEvent(frame=10, obj_name="A", bone_name="", prop_path="p", old_value=0, new_value=1)
        e2 = SwitchEvent(frame=20, obj_name="B", bone_name="", prop_path="p", old_value=1, new_value=2)
        push_event(e1)
        push_event(e2)
        self.assertEqual(get_last_event().frame, 20)

    def test_clear(self):
        from core.p8_switch_history import push_event, clear_history, get_history, SwitchEvent
        push_event(SwitchEvent(frame=1, obj_name="X", bone_name="", prop_path="p", old_value=0, new_value=1))
        clear_history()
        self.assertEqual(len(get_history()), 0)

    def test_find_next(self):
        from core.p8_switch_history import push_event, find_next_event, SwitchEvent
        push_event(SwitchEvent(frame=5, obj_name="A", bone_name="", prop_path="p", old_value=0, new_value=1))
        push_event(SwitchEvent(frame=15, obj_name="B", bone_name="", prop_path="p", old_value=0, new_value=1))
        push_event(SwitchEvent(frame=25, obj_name="C", bone_name="", prop_path="p", old_value=0, new_value=1))
        nxt = find_next_event(10)
        self.assertIsNotNone(nxt)
        self.assertEqual(nxt.frame, 15)

    def test_find_prev(self):
        from core.p8_switch_history import push_event, find_prev_event, SwitchEvent
        push_event(SwitchEvent(frame=5, obj_name="A", bone_name="", prop_path="p", old_value=0, new_value=1))
        push_event(SwitchEvent(frame=15, obj_name="B", bone_name="", prop_path="p", old_value=0, new_value=1))
        prv = find_prev_event(10)
        self.assertIsNotNone(prv)
        self.assertEqual(prv.frame, 5)

    def test_find_next_none(self):
        from core.p8_switch_history import find_next_event
        self.assertIsNone(find_next_event(100))

    def test_unique_frames(self):
        from core.p8_switch_history import push_event, get_unique_frames, SwitchEvent
        push_event(SwitchEvent(frame=10, obj_name="A", bone_name="", prop_path="p", old_value=0, new_value=1))
        push_event(SwitchEvent(frame=10, obj_name="B", bone_name="", prop_path="p", old_value=0, new_value=1))
        push_event(SwitchEvent(frame=20, obj_name="A", bone_name="", prop_path="p", old_value=0, new_value=1))
        self.assertEqual(get_unique_frames(), [10, 20])

    def test_display_label(self):
        from core.p8_switch_history import SwitchEvent
        e = SwitchEvent(frame=42, obj_name="Armature", bone_name="hand.L",
                        prop_path='["space"]', old_value=0, new_value=2)
        label = e.display_label()
        self.assertIn("42", label)
        self.assertIn("hand.L", label)


# ---------------------------------------------------------------------------
# Switch detect dataclasses (no bpy needed)
# ---------------------------------------------------------------------------

class TestSwitchPattern(unittest.TestCase):

    def test_display_label(self):
        from core.p8_switch_detect import SwitchPattern
        p = SwitchPattern(
            obj_name="Armature",
            bone_name="hand.L",
            prop_path='["space_switch"]',
            kind="ENUM",
        )
        label = p.display_label()
        self.assertIn("hand.L", label)
        self.assertIn("space_switch", label)

    def test_display_label_no_bone(self):
        from core.p8_switch_detect import SwitchPattern
        p = SwitchPattern(
            obj_name="Cube",
            bone_name="",
            prop_path='["follow"]',
            kind="BOOL",
        )
        label = p.display_label()
        self.assertIn("Cube", label)


class TestKeywordScore(unittest.TestCase):

    def test_space_keyword(self):
        from core.p8_switch_detect import _keyword_score
        self.assertGreater(_keyword_score("space_switch"), 0.5)

    def test_no_match(self):
        from core.p8_switch_detect import _keyword_score
        self.assertLess(_keyword_score("color_rgb"), 0.01)

    def test_parent_keyword(self):
        from core.p8_switch_detect import _keyword_score
        self.assertGreater(_keyword_score("parent_space"), 0.5)


if __name__ == "__main__":
    unittest.main()
