"""Pure-Python tests for p12_audio_utils.

Run with:
    python tests/test_p12_audio_utils.py -v
"""

from __future__ import annotations

import os
import struct
import sys
import tempfile
import types
import unittest
import wave

# Stub bpy so the module imports without Blender.
_bpy_stub = types.ModuleType("bpy")
_bpy_stub.types = types.ModuleType("bpy.types")
_bpy_stub.props = types.ModuleType("bpy.props")
_bpy_stub.types.PropertyGroup = type("PropertyGroup", (), {})
sys.modules.setdefault("bpy", _bpy_stub)
sys.modules.setdefault("bpy.types", _bpy_stub.types)
sys.modules.setdefault("bpy.props", _bpy_stub.props)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.p12_audio_utils import (  # noqa: E402
    UnsupportedFormat,
    detect_speech_onsets,
    is_supported_audio,
    read_wav_envelope,
    sha256_of_file,
)


def _write_silence_wav(path: str, seconds: float = 0.5, rate: int = 16000) -> None:
    """Write a mono 16-bit silent WAV used as a baseline for envelope tests."""
    with wave.open(path, "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(rate)
        out.writeframes(b"\x00\x00" * int(seconds * rate))


def _write_burst_wav(path: str, rate: int = 16000) -> None:
    """Write a 1-second WAV: silence — loud burst — silence."""
    samples = []
    one_third = rate // 3
    samples.extend([0] * one_third)
    # Saturated tone-ish burst at full scale.
    samples.extend([20000 if (i // 50) % 2 == 0 else -20000 for i in range(one_third)])
    samples.extend([0] * one_third)
    payload = b"".join(struct.pack("<h", s) for s in samples)
    with wave.open(path, "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(rate)
        out.writeframes(payload)


class TestSupportedAudio(unittest.TestCase):

    def test_wav_supported(self):
        self.assertTrue(is_supported_audio("/tmp/foo.wav"))
        self.assertTrue(is_supported_audio("/tmp/Foo.WAV"))

    def test_other_formats_rejected(self):
        self.assertFalse(is_supported_audio("/tmp/foo.mp3"))
        self.assertFalse(is_supported_audio("/tmp/foo.ogg"))
        self.assertFalse(is_supported_audio(""))


class TestSha256(unittest.TestCase):

    def test_hash_changes_on_content_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "a.wav")
            _write_silence_wav(path)
            first = sha256_of_file(path)
            self.assertEqual(len(first), 64)

            _write_burst_wav(path)
            second = sha256_of_file(path)
            self.assertNotEqual(first, second)

    def test_missing_file_returns_empty(self):
        self.assertEqual(sha256_of_file("/nonexistent/path.wav"), "")


class TestEnvelope(unittest.TestCase):

    def test_unsupported_format_raises(self):
        with self.assertRaises(UnsupportedFormat):
            read_wav_envelope("/tmp/foo.mp3")

    def test_silent_envelope_is_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "silent.wav")
            _write_silence_wav(path, seconds=0.3)
            read = read_wav_envelope(path)
            self.assertGreater(len(read.rms_envelope), 0)
            self.assertTrue(all(v <= 0.001 for v in read.rms_envelope))

    def test_burst_envelope_has_speech_window(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "burst.wav")
            _write_burst_wav(path)
            read = read_wav_envelope(path)
            peak = max(read.rms_envelope)
            self.assertGreater(peak, 0.1)
            onsets = detect_speech_onsets(read)
            # One burst → at least one onset.
            self.assertGreaterEqual(len(onsets), 1)


if __name__ == "__main__":
    unittest.main()
