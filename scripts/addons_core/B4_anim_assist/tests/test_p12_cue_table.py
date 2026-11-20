"""Tests for p12_cue_table - find_active_cue, blend factor, viseme value lookup."""

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

from core.p12_cue_table import (  # noqa: E402
    Cue,
    ease_smoothstep,
    find_active_cue,
    viseme_value_at_time,
)


class TestFindActiveCue(unittest.TestCase):

    def test_empty(self):
        prev, nxt, t = find_active_cue([], 1.0)
        self.assertIsNone(prev)
        self.assertIsNone(nxt)
        self.assertEqual(t, 0.0)

    def test_before_first_clamps_left(self):
        cues = [Cue(1.0, "A"), Cue(2.0, "E")]
        prev, nxt, t = find_active_cue(cues, 0.5)
        self.assertEqual(prev.viseme_name, "A")
        self.assertEqual(nxt.viseme_name, "A")
        self.assertEqual(t, 0.0)

    def test_after_last_clamps_right(self):
        cues = [Cue(1.0, "A"), Cue(2.0, "E")]
        prev, nxt, t = find_active_cue(cues, 5.0)
        self.assertEqual(prev.viseme_name, "E")
        self.assertEqual(nxt.viseme_name, "E")
        self.assertEqual(t, 0.0)

    def test_midpoint_blend(self):
        cues = [Cue(1.0, "A"), Cue(2.0, "E")]
        prev, nxt, t = find_active_cue(cues, 1.5)
        self.assertEqual(prev.viseme_name, "A")
        self.assertEqual(nxt.viseme_name, "E")
        self.assertAlmostEqual(t, 0.5)

    def test_quarter_blend(self):
        cues = [Cue(0.0, "A"), Cue(4.0, "E")]
        _, _, t = find_active_cue(cues, 1.0)
        self.assertAlmostEqual(t, 0.25)


class TestEaseSmoothstep(unittest.TestCase):

    def test_endpoints(self):
        self.assertEqual(ease_smoothstep(0.0), 0.0)
        self.assertEqual(ease_smoothstep(1.0), 1.0)

    def test_midpoint(self):
        self.assertAlmostEqual(ease_smoothstep(0.5), 0.5)

    def test_clamps(self):
        self.assertEqual(ease_smoothstep(-0.5), 0.0)
        self.assertEqual(ease_smoothstep(2.0), 1.0)


class TestVisemeValueAtTime(unittest.TestCase):

    def test_full_match(self):
        cues = [Cue(0.0, "A"), Cue(1.0, "A"), Cue(2.0, "E")]
        # at t=0.5 between A and A, value of A should be 1.0
        self.assertAlmostEqual(viseme_value_at_time(cues, 0.5, "A"), 1.0)

    def test_crossfade(self):
        cues = [Cue(0.0, "A"), Cue(1.0, "E")]
        # At t=0.5 the smoothstep is 0.5, A drops to 0.5, E rises to 0.5
        self.assertAlmostEqual(viseme_value_at_time(cues, 0.5, "A"), 0.5)
        self.assertAlmostEqual(viseme_value_at_time(cues, 0.5, "E"), 0.5)

    def test_unrelated_viseme_zero(self):
        cues = [Cue(0.0, "A"), Cue(1.0, "E")]
        self.assertEqual(viseme_value_at_time(cues, 0.5, "O"), 0.0)


if __name__ == "__main__":
    unittest.main()
