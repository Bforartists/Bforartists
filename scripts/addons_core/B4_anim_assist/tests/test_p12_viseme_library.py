"""Pure-Python tests for p12_viseme_library."""

from __future__ import annotations

import os
import sys
import types
import unittest

_bpy_stub = types.ModuleType("bpy")
_bpy_stub.types = types.ModuleType("bpy.types")
_bpy_stub.props = types.ModuleType("bpy.props")
_bpy_stub.types.PropertyGroup = type("PropertyGroup", (), {})
sys.modules.setdefault("bpy", _bpy_stub)
sys.modules.setdefault("bpy.types", _bpy_stub.types)
sys.modules.setdefault("bpy.props", _bpy_stub.props)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.p12_viseme_library import (  # noqa: E402
    BASIC_JAW,
    CARTOON_5,
    LIBRARIES,
    REALISTIC_12,
    get_library,
    library_role_set,
    merge_user_overrides,
    pose_from_json,
    pose_to_json,
)


class TestLibraries(unittest.TestCase):

    def test_all_libraries_have_rest(self):
        for lib_id, lib in LIBRARIES.items():
            self.assertIn("rest", lib, f"library {lib_id} missing rest pose")

    def test_basic_jaw_has_jaw_role(self):
        self.assertIn("jaw", BASIC_JAW["open"])

    def test_cartoon_5_has_classic_visemes(self):
        for v in ("A", "E", "I", "O", "U"):
            self.assertIn(v, CARTOON_5)

    def test_realistic_12_uses_phoneme_groups(self):
        for v in ("A_I", "M_B_P", "F_V", "L", "S_Z"):
            self.assertIn(v, REALISTIC_12)

    def test_get_library_unknown_returns_empty(self):
        self.assertEqual(get_library("NOT_A_REAL_LIBRARY"), {})

    def test_role_set_contains_jaw(self):
        roles = library_role_set("CARTOON_5")
        self.assertIn("jaw", roles)


class TestPoseSerialisation(unittest.TestCase):

    def test_round_trip(self):
        pose = {
            "jaw": ((0.0, 0.0, 0.0), (0.45, 0.0, 0.0), (1.0, 1.0, 1.0)),
        }
        payload = pose_to_json(pose)
        restored = pose_from_json(payload)
        self.assertEqual(restored, pose)

    def test_empty_string_safe(self):
        self.assertEqual(pose_from_json(""), {})

    def test_garbage_safe(self):
        self.assertEqual(pose_from_json("not json"), {})


class TestUserOverrides(unittest.TestCase):

    def test_override_replaces_builtin(self):
        custom_jaw_open = {"jaw": ((0.0, 0.0, 0.0), (0.99, 0.0, 0.0), (1.0, 1.0, 1.0))}
        merged = merge_user_overrides(
            "BASIC_JAW",
            [("open", pose_to_json(custom_jaw_open))],
        )
        self.assertEqual(merged["open"]["jaw"][1], (0.99, 0.0, 0.0))

    def test_unrelated_visemes_survive(self):
        custom_a = {"jaw": ((0.0, 0.0, 0.0), (0.99, 0.0, 0.0), (1.0, 1.0, 1.0))}
        merged = merge_user_overrides(
            "CARTOON_5",
            [("A", pose_to_json(custom_a))],
        )
        # E, I, O, U still come from the built-in.
        for v in ("E", "I", "O", "U"):
            self.assertIn(v, merged)


if __name__ == "__main__":
    unittest.main()
