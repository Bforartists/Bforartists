#!/usr/bin/env python
"""Unit tests for pair detection and mirror math (pure Python).

Tests that do NOT require Blender (pair detection, mirror math,
pair cache).
"""

import sys
import os
import unittest

# Ensure the parent package is importable.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ============================================================================
# PAIR DETECTION TESTS
# ============================================================================


class TestDetectSide(unittest.TestCase):
    """Tests for detect_side()."""

    def test_dot_L(self):
        from core.p9_pair_detect import detect_side
        self.assertEqual(detect_side("Hand.L"), "L")

    def test_dot_R(self):
        from core.p9_pair_detect import detect_side
        self.assertEqual(detect_side("Hand.R"), "R")

    def test_under_L(self):
        from core.p9_pair_detect import detect_side
        self.assertEqual(detect_side("Hand_L"), "L")

    def test_under_R(self):
        from core.p9_pair_detect import detect_side
        self.assertEqual(detect_side("Hand_R"), "R")

    def test_word_Left(self):
        from core.p9_pair_detect import detect_side
        self.assertEqual(detect_side("LeftHand"), "L")

    def test_word_Right(self):
        from core.p9_pair_detect import detect_side
        self.assertEqual(detect_side("RightHand"), "R")

    def test_center(self):
        from core.p9_pair_detect import detect_side
        self.assertEqual(detect_side("Spine"), "C")

    def test_dot_l_lowercase(self):
        from core.p9_pair_detect import detect_side
        self.assertEqual(detect_side("hand.l"), "L")

    def test_dot_r_lowercase(self):
        from core.p9_pair_detect import detect_side
        self.assertEqual(detect_side("hand.r"), "R")


class TestFindOpposite(unittest.TestCase):
    """Tests for find_opposite()."""

    def test_dot_L_to_R(self):
        from core.p9_pair_detect import find_opposite
        self.assertEqual(find_opposite("Hand.L"), "Hand.R")

    def test_dot_R_to_L(self):
        from core.p9_pair_detect import find_opposite
        self.assertEqual(find_opposite("Hand.R"), "Hand.L")

    def test_under_L_to_R(self):
        from core.p9_pair_detect import find_opposite
        self.assertEqual(find_opposite("Hand_L"), "Hand_R")

    def test_under_R_to_L(self):
        from core.p9_pair_detect import find_opposite
        self.assertEqual(find_opposite("Hand_R"), "Hand_L")

    def test_word_Left_to_Right(self):
        from core.p9_pair_detect import find_opposite
        self.assertEqual(find_opposite("LeftHand"), "RightHand")

    def test_word_Right_to_Left(self):
        from core.p9_pair_detect import find_opposite
        self.assertEqual(find_opposite("RightHand"), "LeftHand")

    def test_no_match(self):
        from core.p9_pair_detect import find_opposite
        self.assertIsNone(find_opposite("Spine"))

    def test_dot_L_with_prefix(self):
        from core.p9_pair_detect import find_opposite
        result = find_opposite("Finger_01.L")
        self.assertEqual(result, "Finger_01.R")

    def test_dot_l_lowercase(self):
        from core.p9_pair_detect import find_opposite
        self.assertEqual(find_opposite("hand.l"), "hand.r")

    def test_under_l_lowercase(self):
        from core.p9_pair_detect import find_opposite
        self.assertEqual(find_opposite("hand_l"), "hand_r")

    def test_override_takes_priority(self):
        from core.p9_pair_detect import find_opposite
        overrides = {"Custom_A": "Custom_B", "Custom_B": "Custom_A"}
        self.assertEqual(
            find_opposite("Custom_A", overrides=overrides), "Custom_B"
        )

    def test_exception_takes_priority(self):
        from core.p9_pair_detect import find_opposite
        exceptions = {"Weird_Bone": "Other_Bone"}
        self.assertEqual(
            find_opposite("Weird_Bone", exceptions=exceptions), "Other_Bone"
        )

    def test_word_left_lowercase(self):
        from core.p9_pair_detect import find_opposite
        self.assertEqual(find_opposite("leftHand"), "rightHand")


class TestFindAllPairs(unittest.TestCase):
    """Tests for find_all_pairs()."""

    def test_basic_pairs(self):
        from core.p9_pair_detect import find_all_pairs
        names = ["Hand.L", "Hand.R", "Spine", "Foot.L", "Foot.R"]
        pairs = find_all_pairs(names)
        self.assertEqual(pairs["Hand.L"], "Hand.R")
        self.assertEqual(pairs["Hand.R"], "Hand.L")
        self.assertEqual(pairs["Foot.L"], "Foot.R")
        self.assertNotIn("Spine", pairs)

    def test_mixed_conventions(self):
        from core.p9_pair_detect import find_all_pairs
        names = ["Arm.L", "Arm.R", "Leg_L", "Leg_R"]
        pairs = find_all_pairs(names)
        self.assertEqual(pairs["Arm.L"], "Arm.R")
        self.assertEqual(pairs["Leg_L"], "Leg_R")

    def test_empty(self):
        from core.p9_pair_detect import find_all_pairs
        self.assertEqual(find_all_pairs([]), {})


class TestFindUnpaired(unittest.TestCase):
    """Tests for find_unpaired()."""

    def test_unpaired(self):
        from core.p9_pair_detect import find_all_pairs, find_unpaired
        names = ["Hand.L", "Hand.R", "Spine", "Hips"]
        pairs = find_all_pairs(names)
        unpaired = find_unpaired(names, pairs)
        self.assertIn("Spine", unpaired)
        self.assertIn("Hips", unpaired)
        self.assertNotIn("Hand.L", unpaired)


class TestDetectActiveSide(unittest.TestCase):
    """Tests for detect_active_side()."""

    def test_majority_left(self):
        from core.p9_pair_detect import detect_active_side
        names = ["Hand.L", "Foot.L", "Arm.L", "Spine"]
        self.assertEqual(detect_active_side(names), "L")

    def test_majority_right(self):
        from core.p9_pair_detect import detect_active_side
        names = ["Hand.R", "Foot.R", "Arm.R"]
        self.assertEqual(detect_active_side(names), "R")


class TestCompileCustomPattern(unittest.TestCase):
    """Tests for compile_custom_pattern()."""

    def test_custom_pattern(self):
        from core.p9_pair_detect import compile_custom_pattern
        pat = compile_custom_pattern("test", r"_left$", r"_right$")
        self.assertIsNotNone(pat)
        self.assertEqual(pat.name, "test")


# ============================================================================
# MIRROR MATH TESTS
# ============================================================================


class TestMirrorLocation(unittest.TestCase):
    """Tests for mirror_location()."""

    def test_x_axis(self):
        from core.p9_mirror_math import mirror_location
        result = mirror_location((1.0, 2.0, 3.0), "X")
        self.assertAlmostEqual(result[0], -1.0)
        self.assertAlmostEqual(result[1], 2.0)
        self.assertAlmostEqual(result[2], 3.0)

    def test_y_axis(self):
        from core.p9_mirror_math import mirror_location
        result = mirror_location((1.0, 2.0, 3.0), "Y")
        self.assertAlmostEqual(result[0], 1.0)
        self.assertAlmostEqual(result[1], -2.0)

    def test_z_axis(self):
        from core.p9_mirror_math import mirror_location
        result = mirror_location((1.0, 2.0, 3.0), "Z")
        self.assertAlmostEqual(result[2], -3.0)

    def test_zero(self):
        from core.p9_mirror_math import mirror_location
        result = mirror_location((0.0, 0.0, 0.0), "X")
        self.assertEqual(result, (0.0, 0.0, 0.0))


class TestMirrorRotation(unittest.TestCase):
    """Tests for mirror_rotation_euler()."""

    def test_x_axis(self):
        from core.p9_mirror_math import mirror_rotation_euler
        result = mirror_rotation_euler((0.5, 1.0, -0.3), "X")
        self.assertAlmostEqual(result[0], 0.5)
        self.assertAlmostEqual(result[1], -1.0)
        self.assertAlmostEqual(result[2], 0.3)

    def test_y_axis(self):
        from core.p9_mirror_math import mirror_rotation_euler
        result = mirror_rotation_euler((0.5, 1.0, -0.3), "Y")
        self.assertAlmostEqual(result[0], -0.5)
        self.assertAlmostEqual(result[1], 1.0)
        self.assertAlmostEqual(result[2], 0.3)


class TestMirrorScale(unittest.TestCase):
    """Tests for mirror_scale()."""

    def test_passthrough(self):
        from core.p9_mirror_math import mirror_scale
        sca = (1.5, 2.0, 0.5)
        result = mirror_scale(sca, "X")
        self.assertEqual(result, sca)


class TestMirrorTransform(unittest.TestCase):
    """Tests for mirror_transform()."""

    def test_default_x(self):
        from core.p9_mirror_math import mirror_transform
        loc = (1.0, 2.0, 3.0)
        rot = (0.0, 0.5, -0.5)
        sca = (1.0, 1.0, 1.0)
        m_loc, m_rot, m_sca = mirror_transform(loc, rot, sca)
        self.assertAlmostEqual(m_loc[0], -1.0)
        self.assertAlmostEqual(m_rot[1], -0.5)
        self.assertEqual(m_sca, sca)


class TestMirrorResult(unittest.TestCase):
    """Tests for MirrorResult dataclass."""

    def test_default(self):
        from core.p9_mirror_math import MirrorResult
        r = MirrorResult(bone_name="Hand.L", opposite_name="Hand.R")
        self.assertEqual(r.bone_name, "Hand.L")
        self.assertTrue(r.success)

    def test_failure(self):
        from core.p9_mirror_math import MirrorResult
        r = MirrorResult(bone_name="Hand.L", opposite_name="",
                         success=False, error="No opposite found")
        self.assertFalse(r.success)


# ============================================================================
# PAIR CACHE TESTS
# ============================================================================


class TestPairCache(unittest.TestCase):
    """Tests for the pair cache module."""

    def setUp(self):
        from core import p9_pair_cache as _cache
        _cache.clear_cache()
        self._cache = _cache

    def test_empty_cache(self):
        self.assertIsNone(self._cache.get_pair_map("TestArm"))

    def test_build_and_get(self):
        pair_map = self._cache.build_pair_map("TestArm", ["Hand.L", "Hand.R", "Spine"])
        self.assertEqual(pair_map["Hand.L"], "Hand.R")
        self.assertIsNone(pair_map.get("Spine"))

    def test_get_opposite_from_cache(self):
        self._cache.build_pair_map("TestArm", ["Hand.L", "Hand.R"])
        self.assertEqual(self._cache.get_opposite("TestArm", "Hand.L"), "Hand.R")

    def test_get_opposite_uncached(self):
        self.assertIsNone(self._cache.get_opposite("NoArm", "Hand.L"))

    def test_invalidate_specific(self):
        self._cache.build_pair_map("Arm1", ["A.L", "A.R"])
        self._cache.build_pair_map("Arm2", ["B.L", "B.R"])
        self._cache.invalidate("Arm1")
        self.assertIsNone(self._cache.get_pair_map("Arm1"))
        self.assertIsNotNone(self._cache.get_pair_map("Arm2"))

    def test_invalidate_all(self):
        self._cache.build_pair_map("Arm1", ["A.L", "A.R"])
        self._cache.invalidate()
        self.assertIsNone(self._cache.get_pair_map("Arm1"))

    def test_generation_bumps(self):
        gen0 = self._cache.get_generation()
        self._cache.invalidate()
        self.assertGreater(self._cache.get_generation(), gen0)

    def test_clear_resets_generation(self):
        self._cache.invalidate()
        self._cache.clear_cache()
        self.assertEqual(self._cache.get_generation(), 0)

    def test_get_unpaired(self):
        self._cache.build_pair_map("TestArm", ["Hand.L", "Hand.R", "Spine"])
        unpaired = self._cache.get_unpaired("TestArm")
        self.assertIn("Spine", unpaired)

    def test_get_stats(self):
        self._cache.build_pair_map("TestArm", ["Hand.L", "Hand.R", "Spine", "Hips"])
        stats = self._cache.get_stats("TestArm")
        self.assertEqual(stats["total"], 4)
        self.assertEqual(stats["paired"], 2)
        self.assertEqual(stats["unpaired"], 2)


if __name__ == "__main__":
    unittest.main()
