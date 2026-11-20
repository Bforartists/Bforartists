"""Pure-Python test for the manual override sanctuary in p12_lipsync_engine.

Verifies the central guarantee of v11.0.0: any keyframe flagged as a manual
override survives a rebake, and only auto-baked keys are deleted/rewritten.

Uses lightweight stub action / fcurve / keyframe_point classes so the engine
can run without bpy.
"""

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

from core import p12_rhubarb_adapter as rh  # noqa: E402
from core.p12_lipsync_engine import (  # noqa: E402
    BakeRequest,
    bake_lipsync,
    clear_auto_keys,
    is_manual_override,
    mark_manual_override,
)


# ---------------------------------------------------------------------------
# Stub bpy data shapes — minimal duck-typed surface used by the engine.
# ---------------------------------------------------------------------------

class StubKeyframePoint:
    def __init__(self, frame: int, value: float):
        self.co = (frame, value)


class StubKeyframePoints:
    def __init__(self):
        self._points: list[StubKeyframePoint] = []

    def __iter__(self):
        return iter(self._points)

    def __len__(self):
        return len(self._points)

    def __getitem__(self, i):
        return self._points[i]

    def insert(self, frame, value, options=None):  # noqa: ARG002
        for p in self._points:
            if int(round(p.co[0])) == frame:
                p.co = (frame, value)
                return p
        self._points.append(StubKeyframePoint(frame, value))
        self._points.sort(key=lambda p: p.co[0])
        return self._points[-1]

    def remove(self, point):
        self._points.remove(point)


class StubFCurve:
    def __init__(self, data_path: str, array_index: int):
        self.data_path = data_path
        self.array_index = array_index
        self.keyframe_points = StubKeyframePoints()


class StubFCurves:
    def __init__(self):
        self._curves: list[StubFCurve] = []

    def __iter__(self):
        return iter(self._curves)

    def find(self, data_path, index=0):
        for c in self._curves:
            if c.data_path == data_path and c.array_index == index:
                return c
        return None

    def new(self, data_path, index=0):
        fc = StubFCurve(data_path, index)
        self._curves.append(fc)
        return fc


class StubAction:
    def __init__(self):
        self.fcurves = StubFCurves()
        self._props: dict = {}

    def get(self, key, default=None):
        return self._props.get(key, default)

    def __setitem__(self, key, value):
        self._props[key] = value

    def __getitem__(self, key):
        return self._props[key]


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

class TestManualOverrideSanctuary(unittest.TestCase):

    def _make_request(self, action) -> BakeRequest:
        return BakeRequest(
            armature=object(),
            action=action,
            cues=[
                rh.PhonemeCue(time_seconds=0.0, viseme_name="rest"),
                rh.PhonemeCue(time_seconds=0.5, viseme_name="open"),
                rh.PhonemeCue(time_seconds=1.0, viseme_name="rest"),
            ],
            library_id="BASIC_JAW",
            user_pose_overrides=[],
            rig_wiring={"jaw": "jaw_master"},
            fps=24.0,
            frame_offset=1,
            anticipation_frames=0,
        )

    def test_bake_writes_auto_keys(self):
        action = StubAction()
        report = bake_lipsync(self._make_request(action))
        self.assertGreater(report.keys_written, 0)
        self.assertEqual(report.keys_skipped_manual, 0)
        # Three frames keyed = ~9 fcurve writes (loc, rot, scale * 3 axes).
        self.assertGreater(len(list(action.fcurves)), 0)

    def test_clear_auto_keys_removes_only_auto(self):
        action = StubAction()
        bake_lipsync(self._make_request(action))
        # Mark the keyframe at frame 13 (~0.5s @ 24fps) on rotation axis 0 as manual.
        rot_path = 'pose.bones["jaw_master"].rotation_euler'
        # Find the index of the 0.5s key on the rotation_euler[0] curve.
        target_frame = 1 + int(round(0.5 * 24.0))
        for fc in action.fcurves:
            if fc.data_path == rot_path and fc.array_index == 0:
                for i, p in enumerate(fc.keyframe_points):
                    if int(round(p.co[0])) == target_frame:
                        mark_manual_override(action, rot_path, 0, i)

        deleted = clear_auto_keys(action, ["jaw_master"])
        self.assertGreater(deleted, 0)

        # Verify the manual key survived.
        survivors = []
        for fc in action.fcurves:
            if fc.data_path == rot_path and fc.array_index == 0:
                survivors = [int(round(p.co[0])) for p in fc.keyframe_points]
        self.assertIn(target_frame, survivors, "manual override key was deleted")

    def test_rebake_preserves_manual(self):
        action = StubAction()
        bake_lipsync(self._make_request(action))
        rot_path = 'pose.bones["jaw_master"].rotation_euler'
        target_frame = 1 + int(round(0.5 * 24.0))
        for fc in action.fcurves:
            if fc.data_path == rot_path and fc.array_index == 0:
                for i, p in enumerate(fc.keyframe_points):
                    if int(round(p.co[0])) == target_frame:
                        # Hand-tweak to a distinct value AND mark manual.
                        p.co = (p.co[0], 999.0)
                        mark_manual_override(action, rot_path, 0, i)

        # Rebake = clear + bake.
        clear_auto_keys(action, ["jaw_master"])
        bake_lipsync(self._make_request(action))

        # Find the manual key — it must still exist with value 999.0.
        for fc in action.fcurves:
            if fc.data_path == rot_path and fc.array_index == 0:
                for p in fc.keyframe_points:
                    if int(round(p.co[0])) == target_frame:
                        self.assertEqual(p.co[1], 999.0,
                            "manual override value was overwritten by rebake")
                        return
        self.fail("manual override key vanished after rebake")

    def test_is_manual_override_default_false(self):
        action = StubAction()
        self.assertFalse(is_manual_override(
            action,
            'pose.bones["jaw_master"].location',
            0,
            0,
        ))


if __name__ == "__main__":
    unittest.main()
