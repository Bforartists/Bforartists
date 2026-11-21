"""Pure-Python tests for p7_proxy_math helpers.

Run with:
    python tests/test_p7_proxy_math.py -v
"""

from __future__ import annotations

import sys
import types
import unittest

# Stub bpy for outside-Blender testing.
_bpy_stub = types.ModuleType("bpy")
_bpy_stub.types = types.ModuleType("bpy.types")
_bpy_stub.props = types.ModuleType("bpy.props")
_bpy_stub.data = types.ModuleType("bpy.data")
_bpy_stub.app = types.ModuleType("bpy.app")
_bpy_stub.app.handlers = types.ModuleType("bpy.app.handlers")
_bpy_stub.app.handlers.load_post = []
_bpy_stub.app.handlers.undo_post = []
_bpy_stub.app.handlers.redo_post = []
_bpy_stub.types.PropertyGroup = type("PropertyGroup", (), {})
_bpy_stub.types.Operator = type("Operator", (), {})
_bpy_stub.types.Context = type("Context", (), {})
_bpy_stub.types.Scene = type("Scene", (), {})
for _prop in (
    "BoolProperty", "EnumProperty", "FloatProperty",
    "IntProperty", "StringProperty", "PointerProperty",
    "CollectionProperty", "FloatVectorProperty",
):
    setattr(_bpy_stub.props, _prop, lambda **kw: None)
    setattr(_bpy_stub, _prop, lambda **kw: None)

sys.modules.setdefault("bpy", _bpy_stub)
sys.modules.setdefault("bpy.types", _bpy_stub.types)
sys.modules.setdefault("bpy.props", _bpy_stub.props)
sys.modules.setdefault("bpy.app", _bpy_stub.app)
sys.modules.setdefault("bpy.app.handlers", _bpy_stub.app.handlers)

import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.p7_proxy_math import (
    resolve_bake_range,
    reduce_keys,
    KeySample,
    channels_for_mode,
    proxy_object_name,
    locator_object_name,
    mirror_name,
    PROXY_CONFIGS,
)


class TestResolveBakeRange(unittest.TestCase):

    def test_scene_range(self):
        self.assertEqual(
            resolve_bake_range("SCENE", 1, 250, None, None, 10, 100),
            (1, 250),
        )

    def test_action_range(self):
        self.assertEqual(
            resolve_bake_range("ACTION", 1, 250, 10.5, 80.3, 0, 0),
            (10, 81),
        )

    def test_custom_range(self):
        self.assertEqual(
            resolve_bake_range("CUSTOM", 1, 250, None, None, 50, 100),
            (50, 100),
        )

    def test_custom_range_swapped(self):
        self.assertEqual(
            resolve_bake_range("CUSTOM", 1, 250, None, None, 100, 50),
            (50, 100),
        )

    def test_selection_range(self):
        self.assertEqual(
            resolve_bake_range("SELECTION", 1, 250, None, None, 0, 0, [5.0, 20.0, 15.0]),
            (5, 20),
        )

    def test_selection_fallback_to_scene(self):
        self.assertEqual(
            resolve_bake_range("SELECTION", 1, 250, None, None, 0, 0, None),
            (1, 250),
        )

    def test_preview_range(self):
        self.assertEqual(
            resolve_bake_range(
                "PREVIEW", 1, 250, None, None, 0, 0,
                preview_start=10, preview_end=50,
            ),
            (10, 50),
        )

    def test_preview_fallback_to_scene(self):
        self.assertEqual(
            resolve_bake_range("PREVIEW", 1, 250, None, None, 0, 0),
            (1, 250),
        )


class TestReduceKeys(unittest.TestCase):

    def test_linear_reduction(self):
        """Points on a straight line should reduce to just endpoints."""
        samples = [KeySample(i, float(i)) for i in range(10)]
        result = reduce_keys(samples, tolerance=0.01)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].frame, 0)
        self.assertEqual(result[-1].frame, 9)

    def test_preserves_deviated_points(self):
        """A point far off the line should be preserved."""
        samples = [
            KeySample(0, 0),
            KeySample(5, 10),   # Large deviation
            KeySample(10, 0),
        ]
        result = reduce_keys(samples, tolerance=0.1)
        self.assertEqual(len(result), 3)

    def test_short_list(self):
        samples = [KeySample(0, 0)]
        result = reduce_keys(samples, tolerance=1.0)
        self.assertEqual(len(result), 1)

    def test_two_points(self):
        samples = [KeySample(0, 0), KeySample(10, 5)]
        result = reduce_keys(samples, tolerance=1.0)
        self.assertEqual(len(result), 2)


class TestChannelsForMode(unittest.TestCase):

    def test_all(self):
        ch = channels_for_mode("ALL")
        self.assertIn("location", ch)
        self.assertIn("scale", ch)

    def test_loc(self):
        ch = channels_for_mode("LOC")
        self.assertIn("location", ch)
        self.assertNotIn("scale", ch)

    def test_unknown_defaults_to_all(self):
        ch = channels_for_mode("UNKNOWN")
        self.assertEqual(ch, channels_for_mode("ALL"))


class TestNaming(unittest.TestCase):

    def test_proxy_name(self):
        name = proxy_object_name("Armature", "ORIENTATION", "a3f8c12b")
        self.assertEqual(name, "AA_P7_Proxy_Armature_ORIENTATION_a3f8c12b")

    def test_locator_name(self):
        name = locator_object_name("Hand.L", "a3f8c12b")
        self.assertEqual(name, "AA_P7_Loc_Hand.L_a3f8c12b")


class TestMirrorName(unittest.TestCase):

    def test_dot_l_to_r(self):
        self.assertEqual(mirror_name("Hand.L"), "Hand.R")

    def test_dot_r_to_l(self):
        self.assertEqual(mirror_name("Foot.R"), "Foot.L")

    def test_underscore_l(self):
        self.assertEqual(mirror_name("ctrl_L"), "ctrl_R")

    def test_word_left_right(self):
        self.assertEqual(mirror_name("ArmLeft"), "ArmRight")

    def test_no_pattern(self):
        self.assertEqual(mirror_name("Spine"), "Spine")


class TestProxyConfigs(unittest.TestCase):

    def test_all_nine_types(self):
        expected = {
            "ORIENTATION", "TRANSLATION", "AIM", "POLE", "UP_VECTOR",
            "MULTI_TARGET", "PARENT_SPACE", "WORLD_SPACE", "CAMERA_SPACE",
        }
        self.assertEqual(set(PROXY_CONFIGS.keys()), expected)

    def test_translation_has_constraint(self):
        cfg = PROXY_CONFIGS["TRANSLATION"]
        self.assertEqual(cfg.constraint_type, "COPY_LOCATION")

    def test_pole_has_no_constraint(self):
        cfg = PROXY_CONFIGS["POLE"]
        self.assertIsNone(cfg.constraint_type)

    def test_camera_space_has_keyed_influence(self):
        cfg = PROXY_CONFIGS["CAMERA_SPACE"]
        self.assertTrue(cfg.keyed_influence)

    def test_orientation_constraint(self):
        cfg = PROXY_CONFIGS["ORIENTATION"]
        self.assertEqual(cfg.constraint_type, "COPY_ROTATION")

    def test_aim_constraint(self):
        cfg = PROXY_CONFIGS["AIM"]
        self.assertEqual(cfg.constraint_type, "TRACK_TO")

    def test_parent_space_constraint(self):
        cfg = PROXY_CONFIGS["PARENT_SPACE"]
        self.assertEqual(cfg.constraint_type, "CHILD_OF")

    def test_world_space_constraint(self):
        cfg = PROXY_CONFIGS["WORLD_SPACE"]
        self.assertEqual(cfg.constraint_type, "COPY_TRANSFORMS")

    def test_feature_numbers(self):
        for key, cfg in PROXY_CONFIGS.items():
            self.assertGreaterEqual(cfg.feature, 11)
            self.assertLessEqual(cfg.feature, 19)


if __name__ == "__main__":
    unittest.main()
