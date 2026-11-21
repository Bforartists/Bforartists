"""Exercise the production speaker-strip helper without a Blender runtime.

The AST seam keeps bpy registration out of these collection API regressions.
Run: python anim_assist/tests/test_p12_setup_speaker.py -v
"""

from __future__ import annotations

import ast
import logging
from pathlib import Path
import runpy
from types import SimpleNamespace
import unittest


_ADDON = Path(__file__).resolve().parents[1]
_SOURCE = _ADDON / "operators" / "p12_setup_ops.py"
_TREE = ast.parse(_SOURCE.read_text(encoding="utf-8"), filename=str(_SOURCE))
_FUNCTION = next(node for node in _TREE.body
                 if isinstance(node, ast.FunctionDef) and node.name == "_ensure_speaker_strip")
_NAMESPACE = {
    "constants": SimpleNamespace(**runpy.run_path(str(_ADDON / "constants.py"))),
    "_log": logging.getLogger("test_p12_setup_speaker"),
}
exec(compile(ast.fix_missing_locations(ast.Module(body=[ast.ImportFrom(module="__future__", names=[
    ast.alias(name="annotations")], level=0), _FUNCTION], type_ignores=[])),
    str(_SOURCE), "exec"), _NAMESPACE)
_ensure_speaker_strip = _NAMESPACE["_ensure_speaker_strip"]


class SoundStrips(list):
    """An empty RNA collection is false, but still exposes new_sound."""

    def __init__(self, error=None, result_name="created-sound"):
        super().__init__()
        self.calls = []
        self.error = error
        self.result_name = result_name

    def new_sound(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return SimpleNamespace(name=self.result_name)


class Scene:
    def __init__(self, editor, created_editor=None):
        self.sequence_editor = editor
        self.created_editor = created_editor
        self.create_calls = 0

    def sequence_editor_create(self):
        self.create_calls += 1
        self.sequence_editor = self.created_editor


def occupied(channel, start=10, end=20):
    return SimpleNamespace(channel=channel, frame_final_start=start, frame_final_end=end)


class TestSpeakerStrip(unittest.TestCase):
    def assert_sound(self, scene, strips, channel=1):
        self.assertEqual(_ensure_speaker_strip(scene, "dialogue.wav", 17), "created-sound")
        self.assertEqual(strips.calls, [{
            "name": "AA_P12_face_lipsync_17", "filepath": "dialogue.wav",
            "channel": channel, "frame_start": 17,
        }])

    def test_modern_empty_collection_creates_sound(self):
        strips = SoundStrips()
        self.assert_sound(Scene(SimpleNamespace(strips_all=[], strips=strips)), strips)

    def test_legacy_empty_collection_creates_sound(self):
        strips = SoundStrips()
        self.assert_sound(Scene(SimpleNamespace(sequences_all=[], sequences=strips)), strips)

    def test_modern_collections_win_even_when_empty(self):
        modern, legacy = SoundStrips(), SoundStrips()
        editor = SimpleNamespace(strips_all=[], strips=modern,
                                 sequences_all=[occupied(1)], sequences=legacy)
        self.assert_sound(Scene(editor), modern)
        self.assertEqual(legacy.calls, [])

    def test_channel_overlap_includes_both_endpoints(self):
        for all_name, collection_name in (("strips_all", "strips"),
                                           ("sequences_all", "sequences")):
            with self.subTest(api=all_name):
                strips = SoundStrips()
                editor = SimpleNamespace(**{
                    all_name: [occupied(1, 1, 17), occupied(2, 17, 24),
                               occupied(3, 1, 16), occupied(4, 18, 24)],
                    collection_name: strips,
                })
                self.assert_sound(Scene(editor), strips, channel=3)

    def test_full_channel_range_keeps_existing_channel_one_fallback(self):
        strips = SoundStrips()
        editor = SimpleNamespace(strips_all=[occupied(c) for c in range(1, 33)], strips=strips)
        self.assert_sound(Scene(editor), strips)

    def test_missing_editor_is_created(self):
        strips = SoundStrips()
        scene = Scene(None, SimpleNamespace(strips_all=[], strips=strips))
        self.assert_sound(scene, strips)
        self.assertEqual(scene.create_calls, 1)

    def test_unavailable_editor_returns_empty_name(self):
        scene = Scene(None)
        self.assertEqual(_ensure_speaker_strip(scene, "dialogue.wav", 17), "")
        self.assertEqual(scene.create_calls, 1)

    def test_bare_editor_sound_method_remains_supported(self):
        strips = SoundStrips()
        editor = SimpleNamespace(sequences_all=[], new_sound=strips.new_sound)
        self.assert_sound(Scene(editor), strips)

    def test_file_add_errors_remain_graceful(self):
        for error in (RuntimeError("unreadable audio"), AttributeError("missing sound API")):
            with self.subTest(error=type(error).__name__):
                strips = SoundStrips(error=error)
                scene = Scene(SimpleNamespace(strips_all=[], strips=strips))
                with self.assertLogs("test_p12_setup_speaker", level="WARNING"):
                    self.assertEqual(_ensure_speaker_strip(scene, "dialogue.wav", 17), "")
                self.assertEqual(len(strips.calls), 1)


if __name__ == "__main__":
    unittest.main()
