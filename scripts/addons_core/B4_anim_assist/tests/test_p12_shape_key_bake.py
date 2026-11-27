"""Tests for v12 shape key bake path - writes to key_blocks fcurves; manual override sanctuary works."""

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

from core import p12_cue_table as ct  # noqa: E402
from core.p12_lipsync_engine import (  # noqa: E402
    bake_shape_keys,
    clear_auto_shape_key_keys,
    is_manual_override,
    mark_manual_override,
)


# Reuse the stub action shape from test_p12_manual_override.
class StubKP:
    def __init__(self, frame, value):
        self.co = (frame, value)


class StubKPs:
    def __init__(self):
        self._points = []

    def __iter__(self):
        return iter(self._points)

    def __len__(self):
        return len(self._points)

    def __getitem__(self, i):
        return self._points[i]

    def insert(self, frame, value, options=None):
        for p in self._points:
            if int(round(p.co[0])) == frame:
                p.co = (frame, value)
                return p
        self._points.append(StubKP(frame, value))
        self._points.sort(key=lambda p: p.co[0])
        return self._points[-1]

    def remove(self, point):
        self._points.remove(point)


class StubFC:
    def __init__(self, data_path, array_index):
        self.data_path = data_path
        self.array_index = array_index
        self.keyframe_points = StubKPs()


class StubFCurves:
    def __init__(self):
        self._curves = []

    def __iter__(self):
        return iter(self._curves)

    def find(self, data_path, index=0):
        for c in self._curves:
            if c.data_path == data_path and c.array_index == index:
                return c
        return None

    def new(self, data_path, index=0):
        fc = StubFC(data_path, index)
        self._curves.append(fc)
        return fc


class StubAction:
    def __init__(self):
        self.fcurves = StubFCurves()
        self._props = {}

    def get(self, k, default=None):
        return self._props.get(k, default)

    def __setitem__(self, k, v):
        self._props[k] = v

    def __getitem__(self, k):
        return self._props[k]


class TestShapeKeyBake(unittest.TestCase):

    def _cues(self):
        return [
            ct.Cue(0.0, "rest"),
            ct.Cue(0.5, "A"),
            ct.Cue(1.0, "E"),
            ct.Cue(1.5, "rest"),
        ]

    def _wiring(self):
        return {"A": "mouth_A", "E": "mouth_E"}

    def test_bake_writes_keys(self):
        action = StubAction()
        report = bake_shape_keys(
            action=action, cues=self._cues(), shape_key_wiring=self._wiring(),
            fps=24.0, frame_offset=1, anticipation_frames=0,
        )
        self.assertGreater(report.keys_written, 0)
        # Verify at least one fcurve exists for mouth_A
        paths = [fc.data_path for fc in action.fcurves]
        self.assertIn('key_blocks["mouth_A"].value', paths)
        self.assertIn('key_blocks["mouth_E"].value', paths)

    def test_bake_value_is_one_at_matching_cue(self):
        action = StubAction()
        bake_shape_keys(
            action=action, cues=self._cues(), shape_key_wiring=self._wiring(),
            fps=24.0, frame_offset=1, anticipation_frames=0,
        )
        # mouth_A cue at t=0.5s, fps=24, offset=1 -> frame 13
        target_frame = 1 + int(round(0.5 * 24.0))
        for fc in action.fcurves:
            if fc.data_path == 'key_blocks["mouth_A"].value':
                for p in fc.keyframe_points:
                    if int(round(p.co[0])) == target_frame:
                        self.assertEqual(p.co[1], 1.0)
                        return
        self.fail("mouth_A frame 13 key not found")

    def test_clear_auto_keys_removes_all(self):
        action = StubAction()
        bake_shape_keys(
            action=action, cues=self._cues(), shape_key_wiring=self._wiring(),
            fps=24.0, frame_offset=1, anticipation_frames=0,
        )
        deleted = clear_auto_shape_key_keys(action, ["mouth_A", "mouth_E"])
        self.assertGreater(deleted, 0)

    def test_manual_override_survives_clear(self):
        action = StubAction()
        bake_shape_keys(
            action=action, cues=self._cues(), shape_key_wiring=self._wiring(),
            fps=24.0, frame_offset=1, anticipation_frames=0,
        )
        # Mark frame 13 on mouth_A as manual
        target_frame = 1 + int(round(0.5 * 24.0))
        mark_manual_override(action, 'key_blocks["mouth_A"].value', 0, target_frame)

        clear_auto_shape_key_keys(action, ["mouth_A", "mouth_E"])

        # mouth_A frame 13 should still exist
        for fc in action.fcurves:
            if fc.data_path == 'key_blocks["mouth_A"].value':
                survivors = [int(round(p.co[0])) for p in fc.keyframe_points]
                self.assertIn(target_frame, survivors)
                return
        self.fail("mouth_A fcurve missing")

    def test_manual_override_survives_rebake(self):
        action = StubAction()
        bake_shape_keys(
            action=action, cues=self._cues(), shape_key_wiring=self._wiring(),
            fps=24.0, frame_offset=1, anticipation_frames=0,
        )
        target_frame = 1 + int(round(0.5 * 24.0))
        # Tweak the mouth_A key at frame 13 to a sentinel value, then lock it.
        for fc in action.fcurves:
            if fc.data_path == 'key_blocks["mouth_A"].value':
                for p in fc.keyframe_points:
                    if int(round(p.co[0])) == target_frame:
                        p.co = (p.co[0], 0.42)
        mark_manual_override(action, 'key_blocks["mouth_A"].value', 0, target_frame)

        # Rebake: clear + bake
        clear_auto_shape_key_keys(action, ["mouth_A", "mouth_E"])
        bake_shape_keys(
            action=action, cues=self._cues(), shape_key_wiring=self._wiring(),
            fps=24.0, frame_offset=1, anticipation_frames=0,
        )

        # mouth_A frame 13 should STILL be 0.42, not overwritten back to 1.0
        for fc in action.fcurves:
            if fc.data_path == 'key_blocks["mouth_A"].value':
                for p in fc.keyframe_points:
                    if int(round(p.co[0])) == target_frame:
                        self.assertEqual(p.co[1], 0.42, "manual override value lost on rebake")
                        return
        self.fail("manual override key vanished")


if __name__ == "__main__":
    unittest.main()
