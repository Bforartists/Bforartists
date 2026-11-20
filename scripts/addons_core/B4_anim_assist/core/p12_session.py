# --- LIPSYNC SESSION CACHE (Phase 12) ---
"""Module-level cache for analyzed audio in the current Blender session.

Mirrors ``core/p7_session.py`` and the other phase session caches: stores
expensive-to-compute artifacts (here, decoded WAV envelopes and bake reports)
keyed by file sha256 so repeated bakes against the same audio don't re-decode.

Cleared on:
* addon ``unregister`` via ``clear_all_sessions``.
* file load (the addon's ``app_handlers`` invalidate caches across the board).

Kept bpy-free; the operator is responsible for invalidating entries when an
audio file's hash changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import p12_audio_utils as au
from . import p12_rhubarb_adapter as rh
from .logging import get_logger

__all__ = [
    "EnvelopeCacheEntry",
    "BakeRecord",
    "get_envelope",
    "get_analyze",
    "record_bake",
    "get_last_bake",
    "clear_all_sessions",
]

_log = get_logger(__name__)


@dataclass
class EnvelopeCacheEntry:
    """Cached audio envelope keyed by file hash."""
    audio_sha256: str
    read: au.AudioRead


@dataclass
class BakeRecord:
    """Last bake outcome for a given (layer_name, audio_sha256) pair."""
    keys_written: int = 0
    keys_skipped: int = 0
    bones_touched: int = 0
    cue_count: int = 0
    backend: str = "AMPLITUDE"
    fallback_used: bool = False
    fallback_reason: str = ""
    range_start: int = 0
    range_end: int = 0


# Module-level singletons. Keyed by sha256 because that's the same key used
# to detect audio drift on the layer link.
_envelope_cache: dict[str, EnvelopeCacheEntry] = {}
_analyze_cache: dict[tuple[str, str], rh.AnalyzeResult] = field(default_factory=dict)  # type: ignore[assignment]
# Re-init the dict properly — the field() above is a typing trick to keep the
# annotation visible without dataclass instantiation here.
_analyze_cache = {}
_bake_records: dict[str, BakeRecord] = {}


def get_envelope(audio_path: str, audio_sha256: str) -> au.AudioRead | None:
    """Return a cached envelope for *audio_sha256*, decoding on cache miss.

    Returns None when the audio cannot be decoded (unsupported format etc.) —
    the caller surfaces a user-facing error.
    """
    if not audio_sha256:
        return None
    cached = _envelope_cache.get(audio_sha256)
    if cached is not None:
        return cached.read
    try:
        read = au.read_wav_envelope(audio_path)
    except au.UnsupportedFormat as exc:
        _log.warning("Envelope decode failed for %s: %s", audio_path, exc)
        return None
    _envelope_cache[audio_sha256] = EnvelopeCacheEntry(
        audio_sha256=audio_sha256,
        read=read,
    )
    return read


def get_analyze(
    audio_path: str,
    audio_sha256: str,
    backend: str,
    rhubarb_path: str = "",
) -> rh.AnalyzeResult:
    """Return a cached AnalyzeResult, running the backend on cache miss."""
    cache_key = (audio_sha256, backend)
    cached = _analyze_cache.get(cache_key)
    if cached is not None:
        return cached
    result = rh.analyze(audio_path, backend=backend, rhubarb_path=rhubarb_path)
    if audio_sha256:
        _analyze_cache[cache_key] = result
    return result


def record_bake(layer_name: str, record: BakeRecord) -> None:
    """Remember the outcome of the last bake for *layer_name*."""
    if not layer_name:
        return
    _bake_records[layer_name] = record


def get_last_bake(layer_name: str) -> BakeRecord | None:
    """Return the cached BakeRecord for *layer_name*, if any."""
    return _bake_records.get(layer_name)


def clear_all_sessions() -> None:
    """Wipe all caches. Called from the addon unregister cleanup loop."""
    _envelope_cache.clear()
    _analyze_cache.clear()
    _bake_records.clear()
