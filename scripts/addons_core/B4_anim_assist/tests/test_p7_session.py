"""Pure-Python tests for the P7Session state machine and serialization.

These tests exercise the session lifecycle (begin → active → baking →
committed; begin → active → rollback) using only the Python-side
registry, without requiring Blender or bpy.  Functions that import bpy
(rollback_session, purge_session_artifacts, save/load_session_to_scene)
are NOT tested here — they require a live Blender context and should be
verified manually or via Blender's built-in test runner.

Run with:
    python -m pytest tests/test_p7_session.py -v
    # or without pytest:
    python tests/test_p7_session.py
"""

from __future__ import annotations

import json
import sys
import types
import unittest

# ---------------------------------------------------------------------------
# Stub out bpy so the module loads outside Blender.
# ---------------------------------------------------------------------------

_bpy_stub = types.ModuleType("bpy")
_bpy_stub.types = types.ModuleType("bpy.types")
_bpy_stub.props = types.ModuleType("bpy.props")
_bpy_stub.data = types.ModuleType("bpy.data")
_bpy_stub.app = types.ModuleType("bpy.app")
_bpy_stub.app.handlers = types.ModuleType("bpy.app.handlers")
_bpy_stub.app.handlers.load_post = []
_bpy_stub.app.handlers.undo_post = []
_bpy_stub.app.handlers.redo_post = []

# Minimal type stubs so PropertyGroup and Operator can be subclassed.
_bpy_stub.types.PropertyGroup = type("PropertyGroup", (), {})
_bpy_stub.types.Operator = type("Operator", (), {})
_bpy_stub.types.Context = type("Context", (), {})
_bpy_stub.types.Scene = type("Scene", (), {})

# Property constructors (no-ops outside Blender).
for _prop in (
    "BoolProperty", "EnumProperty", "FloatProperty",
    "IntProperty", "StringProperty", "PointerProperty",
    "CollectionProperty",
):
    setattr(_bpy_stub.props, _prop, lambda **kw: None)
    setattr(_bpy_stub, _prop, lambda **kw: None)  # some imports via bpy.<Prop>

sys.modules.setdefault("bpy", _bpy_stub)
sys.modules.setdefault("bpy.types", _bpy_stub.types)
sys.modules.setdefault("bpy.props", _bpy_stub.props)
sys.modules.setdefault("bpy.app", _bpy_stub.app)
sys.modules.setdefault("bpy.app.handlers", _bpy_stub.app.handlers)

# Now we can import the module under test.
# Adjust path if needed — run from the addon root directory.
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.p7_session import (
    P7Session,
    ConstraintRecord,
    begin_session,
    set_stage,
    commit_session,
    get_session,
    get_all_sessions,
    clear_all_sessions,
    TAG_TEMP,
    TAG_SESSION_ID,
    TAG_ARTIFACT_ROLE,
    CONSTRAINT_PREFIX,
    SCENE_SESSION_KEY,
    tag_artifact,
    make_constraint_name,
)


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

class TestP7SessionDataclass(unittest.TestCase):
    """P7Session construction, property access, and serialization."""

    def test_default_construction(self):
        s = P7Session()
        self.assertEqual(s.stage, "ACTIVE")
        self.assertEqual(len(s.session_id), 36)  # UUID format
        self.assertEqual(len(s.short_id), 8)
        self.assertFalse(s.created_objects)
        self.assertFalse(s.created_constraints)
        self.assertFalse(s.created_collections)

    def test_register_object_deduplicates(self):
        s = P7Session()
        s.register_object("Cube", "helper")
        s.register_object("Cube", "helper")
        self.assertEqual(len(s.created_objects), 1)

    def test_register_constraint(self):
        s = P7Session()
        s.register_constraint("Armature", "Spine", "AA_P7_abc12345_IK")
        self.assertEqual(len(s.created_constraints), 1)
        rec = s.created_constraints[0]
        self.assertEqual(rec.object_name, "Armature")
        self.assertEqual(rec.bone_name, "Spine")
        self.assertEqual(rec.constraint_name, "AA_P7_abc12345_IK")

    def test_register_collection_deduplicates(self):
        s = P7Session()
        s.register_collection("AA_P7_Temp_abc12345")
        s.register_collection("AA_P7_Temp_abc12345")
        self.assertEqual(len(s.created_collections), 1)

    def test_register_custom_prop_deduplicates(self):
        s = P7Session()
        s.register_custom_prop("Cube", "my_key")
        s.register_custom_prop("Cube", "my_key")
        self.assertEqual(len(s.created_custom_props), 1)


class TestP7SessionSerialization(unittest.TestCase):
    """Round-trip serialization to dict / JSON."""

    def _make_populated_session(self) -> P7Session:
        s = P7Session(scene_name="TestScene")
        s.register_object("Helper_Empty", "locator")
        s.register_constraint("Rig", "Hand.L", "AA_P7_abc_IK")
        s.register_collection("AA_P7_Temp_abc12345")
        s.register_custom_prop("Cube", "my_prop")
        s.stage = "BAKING"
        return s

    def test_to_dict_fields(self):
        s = self._make_populated_session()
        d = s.to_dict()
        self.assertEqual(d["scene_name"], "TestScene")
        self.assertEqual(d["stage"], "BAKING")
        self.assertIn("Helper_Empty", d["created_objects"])
        self.assertEqual(len(d["created_constraints"]), 1)
        self.assertEqual(d["created_constraints"][0]["bone_name"], "Hand.L")

    def test_round_trip(self):
        original = self._make_populated_session()
        d = original.to_dict()
        restored = P7Session.from_dict(d)
        self.assertEqual(restored.session_id, original.session_id)
        self.assertEqual(restored.scene_name, original.scene_name)
        self.assertEqual(restored.stage, original.stage)
        self.assertEqual(restored.created_objects, original.created_objects)
        self.assertEqual(len(restored.created_constraints), 1)
        self.assertEqual(
            restored.created_constraints[0].constraint_name,
            original.created_constraints[0].constraint_name,
        )

    def test_json_round_trip(self):
        original = self._make_populated_session()
        blob = json.dumps(original.to_dict())
        restored = P7Session.from_dict(json.loads(blob))
        self.assertEqual(restored.session_id, original.session_id)
        self.assertEqual(restored.stage, "BAKING")


class TestP7SessionLifecycle(unittest.TestCase):
    """Python-side session registry lifecycle."""

    def setUp(self):
        clear_all_sessions()

    def tearDown(self):
        clear_all_sessions()

    def test_begin_creates_session(self):
        s = begin_session("MyScene")
        self.assertIsNotNone(get_session(s.session_id))
        self.assertEqual(s.stage, "ACTIVE")
        self.assertEqual(s.scene_name, "MyScene")

    def test_set_stage_transitions(self):
        s = begin_session("S")
        set_stage(s.session_id, "BAKING")
        self.assertEqual(get_session(s.session_id).stage, "BAKING")

    def test_commit_removes_from_registry(self):
        s = begin_session("S")
        commit_session(s.session_id)
        self.assertIsNone(get_session(s.session_id))

    def test_commit_unknown_session_is_harmless(self):
        # Should not raise.
        commit_session("nonexistent-uuid")

    def test_get_all_sessions(self):
        s1 = begin_session("A")
        s2 = begin_session("B")
        all_s = get_all_sessions()
        self.assertIn(s1.session_id, all_s)
        self.assertIn(s2.session_id, all_s)

    def test_clear_all_sessions(self):
        begin_session("A")
        begin_session("B")
        clear_all_sessions()
        self.assertEqual(len(get_all_sessions()), 0)

    def test_set_stage_unknown_session_is_harmless(self):
        set_stage("nonexistent-uuid", "BAKING")


class TestConstraintRecord(unittest.TestCase):
    """ConstraintRecord serialization."""

    def test_round_trip(self):
        cr = ConstraintRecord("Rig", "Spine", "AA_P7_abc_CopyLoc")
        d = cr.as_dict()
        restored = ConstraintRecord.from_dict(d)
        self.assertEqual(restored.object_name, "Rig")
        self.assertEqual(restored.bone_name, "Spine")
        self.assertEqual(restored.constraint_name, "AA_P7_abc_CopyLoc")


class TestTaggingHelpers(unittest.TestCase):
    """Utility functions for tagging artifacts and naming constraints."""

    def test_make_constraint_name(self):
        name = make_constraint_name("a3f8c12b-xxxx-yyyy-zzzz", "IK")
        self.assertEqual(name, "AA_P7_a3f8c12b_IK")

    def test_make_constraint_name_short_suffix(self):
        name = make_constraint_name("12345678-abcd-efgh-ijkl", "CopyLoc")
        self.assertTrue(name.startswith(CONSTRAINT_PREFIX))
        self.assertIn("CopyLoc", name)

    def test_tag_artifact(self):
        # Simulate a Blender object with __setitem__.
        fake_obj = {}
        tag_artifact(fake_obj, "test-session-id-1234", "proxy_locator", "Armature")
        self.assertTrue(fake_obj[TAG_TEMP])
        self.assertEqual(fake_obj[TAG_SESSION_ID], "test-session-id-1234")
        self.assertEqual(fake_obj[TAG_ARTIFACT_ROLE], "proxy_locator")
        self.assertEqual(fake_obj["anim_assist_owner_obj"], "Armature")

    def test_tag_artifact_no_owner(self):
        fake_obj = {}
        tag_artifact(fake_obj, "test-session-id-1234", "bake_target")
        self.assertNotIn("anim_assist_owner_obj", fake_obj)


class TestConstants(unittest.TestCase):
    """Verify tag constants are consistent."""

    def test_scene_session_key_is_string(self):
        self.assertIsInstance(SCENE_SESSION_KEY, str)

    def test_constraint_prefix(self):
        self.assertEqual(CONSTRAINT_PREFIX, "AA_P7_")


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
