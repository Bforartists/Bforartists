# --- LIPSYNC AUDIO UTILITIES (Phase 12) ---
"""Audio file utilities for the Phase 12 lipsync system.

Kept *bpy-free* so the same helpers can run inside unit tests without booting
Blender. The module supports:

* SHA-256 hashing of audio files for stale detection.
* Reading a `.wav` file's RMS envelope using only the stdlib ``wave`` module
  — no numpy/scipy. The amplitude backend uses this to drive the jaw bone.
* Detecting speech onsets from the RMS envelope using a simple threshold +
  hysteresis pass — used as the default phoneme-marker generator when
  Rhubarb is not available.

Only `.wav` is supported in v11.0.0. Other formats raise ``UnsupportedFormat``
which the caller surfaces as a user-facing message ("convert to .wav first").
v11.1+ may add ffmpeg-based decoding behind the same interface.
"""

from __future__ import annotations

import hashlib
import os
import wave
from dataclasses import dataclass

from .logging import get_logger

__all__ = [
    "UnsupportedFormat",
    "AudioRead",
    "sha256_of_file",
    "read_wav_envelope",
    "detect_speech_onsets",
    "is_supported_audio",
]

_log = get_logger(__name__)

# Read 64 KiB at a time — small enough to keep memory flat on long VO files,
# large enough that the hashing loop's per-iteration overhead disappears.
_HASH_CHUNK = 64 * 1024

# Speech-onset detection defaults — tuned for dialogue, not music.
_DEFAULT_FRAME_MS = 30  # one envelope sample per 30 ms ≈ 33 fps
_DEFAULT_RMS_GATE = 0.05  # below this, treat as silence
_DEFAULT_HOLD_MS = 80  # require N ms above gate before flagging onset


class UnsupportedFormat(Exception):
    """Raised when the lipsync system is asked to read a non-`.wav` file."""


@dataclass
class AudioRead:
    """Result of envelope analysis on an audio file."""
    sample_rate: int
    channels: int
    duration_seconds: float
    envelope_ms: int  # ms per envelope sample
    rms_envelope: list[float]  # 0.0–1.0 RMS per envelope_ms window


def is_supported_audio(path: str) -> bool:
    """Return True if the path looks like a `.wav` file we can read."""
    if not path:
        return False
    return path.lower().endswith(".wav")


def sha256_of_file(path: str) -> str:
    """Return the SHA-256 hex digest of the file at *path*.

    Returns the empty string for missing/unreadable files — callers compare
    against the previously stored hash, so an empty string just means
    "no record" rather than "definitely changed".
    """
    if not path or not os.path.isfile(path):
        return ""
    h = hashlib.sha256()
    try:
        with open(path, "rb") as src:
            while True:
                block = src.read(_HASH_CHUNK)
                if not block:
                    break
                h.update(block)
    except OSError:
        _log.warning("Could not hash audio file %s", path)
        return ""
    return h.hexdigest()


def read_wav_envelope(
    path: str,
    frame_ms: int = _DEFAULT_FRAME_MS,
) -> AudioRead:
    """Read a `.wav` file and return its RMS envelope.

    Implementation notes
    --------------------
    * Uses ``wave`` from the stdlib — handles 8/16/24/32-bit PCM. 24-bit is
      the awkward case; we unpack as bytes and reconstruct manually.
    * Returns mono RMS per *frame_ms* window. Stereo is downmixed to mono
      by averaging channels (cheap and sufficient for amplitude-driven jaw).
    * The output is normalised to 0.0–1.0 by dividing by the format's max
      magnitude.

    Raises
    ------
    UnsupportedFormat
        If the file extension is not `.wav` or the file cannot be opened.
    """
    if not is_supported_audio(path):
        raise UnsupportedFormat(
            f"Lipsync v11.0.0 supports .wav only — got {path!r}. "
            "Convert via your DAW or ffmpeg, then re-bind."
        )
    if not os.path.isfile(path):
        raise UnsupportedFormat(f"Audio file not found: {path}")

    try:
        with wave.open(path, "rb") as src:
            sample_rate = src.getframerate()
            channels = src.getnchannels()
            sample_width = src.getsampwidth()
            n_frames = src.getnframes()
            raw = src.readframes(n_frames)
    except (wave.Error, OSError) as exc:
        raise UnsupportedFormat(f"Could not read .wav file {path}: {exc}") from exc

    duration = n_frames / float(sample_rate) if sample_rate else 0.0
    samples_per_frame = max(1, int(sample_rate * frame_ms / 1000))
    envelope = _rms_envelope(raw, sample_width, channels, samples_per_frame)
    return AudioRead(
        sample_rate=sample_rate,
        channels=channels,
        duration_seconds=duration,
        envelope_ms=frame_ms,
        rms_envelope=envelope,
    )


def detect_speech_onsets(
    read: AudioRead,
    rms_gate: float = _DEFAULT_RMS_GATE,
    hold_ms: int = _DEFAULT_HOLD_MS,
) -> list[float]:
    """Return a list of onset timestamps (seconds) extracted from *read*.

    Onset = first sample where RMS crosses ``rms_gate`` and stays above
    for at least ``hold_ms``. Silence return resets the detector.

    This is the marker generator used by setup mode ``MARKER_ONLY`` and
    by the amplitude backend's coarse phoneme stand-in. It is *not* a
    phoneme classifier — it answers "did the character start saying
    something here?", not "what did they say?".
    """
    if not read.rms_envelope:
        return []
    hold_samples = max(1, int(hold_ms / max(1, read.envelope_ms)))

    onsets: list[float] = []
    above_count = 0
    in_speech = False
    for i, value in enumerate(read.rms_envelope):
        if value >= rms_gate:
            above_count += 1
            if not in_speech and above_count >= hold_samples:
                # Onset = first sample of the run, not the trigger sample.
                onset_index = max(0, i - hold_samples + 1)
                onsets.append(onset_index * read.envelope_ms / 1000.0)
                in_speech = True
        else:
            above_count = 0
            in_speech = False
    return onsets


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------

def _rms_envelope(
    raw: bytes,
    sample_width: int,
    channels: int,
    samples_per_frame: int,
) -> list[float]:
    """Compute mono RMS envelope from interleaved PCM bytes."""
    if not raw or samples_per_frame <= 0:
        return []

    if sample_width == 1:
        # Unsigned 8-bit PCM: 0..255, midpoint at 128.
        values = [b - 128 for b in raw]
        max_mag = 128.0
    elif sample_width == 2:
        values = _unpack_signed(raw, 2)
        max_mag = 32768.0
    elif sample_width == 3:
        values = _unpack_signed_24(raw)
        max_mag = 8388608.0
    elif sample_width == 4:
        values = _unpack_signed(raw, 4)
        max_mag = 2147483648.0
    else:
        _log.warning("Unsupported sample width %d — returning empty envelope", sample_width)
        return []

    if channels > 1:
        mono = [
            sum(values[i:i + channels]) / channels
            for i in range(0, len(values) - channels + 1, channels)
        ]
    else:
        mono = values

    envelope: list[float] = []
    for start in range(0, len(mono), samples_per_frame):
        window = mono[start:start + samples_per_frame]
        if not window:
            continue
        rms = (sum(s * s for s in window) / len(window)) ** 0.5
        envelope.append(min(1.0, rms / max_mag))
    return envelope


def _unpack_signed(raw: bytes, width: int) -> list[int]:
    """Unpack little-endian signed integers of *width* bytes."""
    out: list[int] = []
    for i in range(0, len(raw) - width + 1, width):
        out.append(int.from_bytes(raw[i:i + width], "little", signed=True))
    return out


def _unpack_signed_24(raw: bytes) -> list[int]:
    """24-bit signed PCM — wave returns 3 bytes per sample, no struct format."""
    out: list[int] = []
    for i in range(0, len(raw) - 2, 3):
        out.append(int.from_bytes(raw[i:i + 3], "little", signed=True))
    return out
