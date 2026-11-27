# --- RHUBARB / AMPLITUDE LIPSYNC BACKEND ADAPTER (Phase 12) ---
"""Audio-analysis backend adapter for the lipsync system.

Two backends, one interface:

* ``analyze_amplitude`` — always available; uses ``p12_audio_utils`` to read
  the WAV envelope and emit a coarse phoneme schedule of "open / closed"
  cues at speech onsets and decays. Ships in v11.0.0.

* ``analyze_rhubarb`` — invokes the Rhubarb Lip Sync CLI as a subprocess
  and parses its JSON output into a phoneme schedule. Stubbed in v11.0.0:
  detection always fails gracefully, the system reports "Rhubarb not
  available, falling back to amplitude" and continues. Real implementation
  will land in v11.1 once per-platform CLI bundling is solved.

Output format
-------------
Both backends emit a list of ``PhonemeCue`` records — ``(time_seconds,
viseme_name)``. The bake operator translates these into keyframes by
looking up the viseme in the active library and writing the resulting
bone deltas onto the layer's Action.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass

from . import p12_audio_utils as au
from .logging import get_logger

__all__ = [
    "PhonemeCue",
    "BackendUnavailable",
    "AnalyzeResult",
    "is_rhubarb_available",
    "analyze",
    "analyze_amplitude",
    "analyze_rhubarb",
]

_log = get_logger(__name__)

# Mapping from Rhubarb's "mouth shape" letters (A–H, X) to the role names
# used by REALISTIC_12 in the viseme library. Kept here, not in the library
# module, because the mapping is backend-specific.
RHUBARB_TO_VISEME: dict[str, str] = {
    "A": "M_B_P",   # closed
    "B": "K_G",     # k/g/n
    "C": "E",       # eh / open vowel
    "D": "A_I",     # ah/aye — wide open
    "E": "O",       # rounded
    "F": "U",       # tight rounded
    "G": "F_V",     # lip on teeth
    "H": "L",
    "X": "rest",    # silence / rest
}

# Conservative onset/release pulse for amplitude mode. When RMS climbs above
# the gate, fire an "open" cue; when it drops below, fire a "rest" cue.
_AMP_OPEN_VISEME = "open"
_AMP_REST_VISEME = "rest"


@dataclass
class PhonemeCue:
    """One phoneme/viseme cue at a point in time."""
    time_seconds: float
    viseme_name: str


@dataclass
class AnalyzeResult:
    """Complete output of an audio analysis run."""
    backend: str
    cues: list[PhonemeCue]
    # Set when the requested backend was unavailable and we fell back. The
    # UI surfaces this so the user knows why output looks coarser than expected.
    fallback_used: bool = False
    fallback_reason: str = ""


class BackendUnavailable(Exception):
    """Raised internally when a backend cannot be invoked."""


# ---------------------------------------------------------------------------
# Backend dispatch
# ---------------------------------------------------------------------------

def is_rhubarb_available(rhubarb_path: str = "") -> bool:
    """Return True if a Rhubarb executable can be located.

    *rhubarb_path* takes precedence; otherwise PATH is checked for ``rhubarb``.
    """
    candidate = rhubarb_path.strip() if rhubarb_path else ""
    if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
        return True
    return shutil.which("rhubarb") is not None


def analyze(
    audio_path: str,
    backend: str = "AMPLITUDE",
    rhubarb_path: str = "",
) -> AnalyzeResult:
    """Public entry point — run the requested *backend*, fall back if needed.

    The caller is the bake operator; it never needs to know which backend
    was actually used unless it wants to surface that to the user.
    """
    if backend == "RHUBARB":
        if not is_rhubarb_available(rhubarb_path):
            _log.info("Rhubarb requested but not available — using amplitude")
            cues = analyze_amplitude(audio_path)
            return AnalyzeResult(
                backend="AMPLITUDE",
                cues=cues,
                fallback_used=True,
                fallback_reason="Rhubarb executable not found on PATH",
            )
        try:
            cues = analyze_rhubarb(audio_path, rhubarb_path=rhubarb_path)
            return AnalyzeResult(backend="RHUBARB", cues=cues)
        except BackendUnavailable as exc:
            _log.warning("Rhubarb invocation failed: %s — falling back", exc)
            cues = analyze_amplitude(audio_path)
            return AnalyzeResult(
                backend="AMPLITUDE",
                cues=cues,
                fallback_used=True,
                fallback_reason=str(exc),
            )

    # Amplitude path (default).
    cues = analyze_amplitude(audio_path)
    return AnalyzeResult(backend="AMPLITUDE", cues=cues)


# ---------------------------------------------------------------------------
# Amplitude backend — ships in v11.0.0
# ---------------------------------------------------------------------------

def analyze_amplitude(audio_path: str) -> list[PhonemeCue]:
    """Generate coarse open/rest cues from the WAV envelope.

    Strategy: walk the RMS envelope; emit ``open`` when crossing the gate
    upward, ``rest`` when crossing back down. The bake operator then
    interpolates the jaw between rest and open across these markers, which
    gives moving-mouth lipsync that is always *roughly* in time with the
    audio even with no phoneme detection.
    """
    try:
        read = au.read_wav_envelope(audio_path)
    except au.UnsupportedFormat as exc:
        _log.warning("Amplitude analysis unavailable: %s", exc)
        return []

    if not read.rms_envelope:
        return []

    cues: list[PhonemeCue] = [PhonemeCue(time_seconds=0.0, viseme_name=_AMP_REST_VISEME)]
    gate = 0.05
    in_speech = False
    for i, value in enumerate(read.rms_envelope):
        t = i * read.envelope_ms / 1000.0
        if value >= gate and not in_speech:
            cues.append(PhonemeCue(time_seconds=t, viseme_name=_AMP_OPEN_VISEME))
            in_speech = True
        elif value < gate and in_speech:
            cues.append(PhonemeCue(time_seconds=t, viseme_name=_AMP_REST_VISEME))
            in_speech = False
    if in_speech:
        # Close out at the end of the file so the mouth doesn't hang open.
        cues.append(
            PhonemeCue(
                time_seconds=read.duration_seconds,
                viseme_name=_AMP_REST_VISEME,
            )
        )
    return cues


# ---------------------------------------------------------------------------
# Rhubarb backend — stub in v11.0.0, real impl arrives in v11.1
# ---------------------------------------------------------------------------

def analyze_rhubarb(audio_path: str, rhubarb_path: str = "") -> list[PhonemeCue]:
    """Run the Rhubarb CLI and parse its JSON output.

    v11.0.0 status: the CLI invocation logic is here, but Rhubarb is not
    bundled with the addon. If the binary is on the user's PATH (or
    ``rhubarb_path``) it will be used; otherwise this raises
    BackendUnavailable so the dispatcher can fall back.

    The CLI returns JSON shaped like::

        {"mouthCues": [{"start": 0.00, "end": 0.12, "value": "X"}, ...]}

    We translate each cue's start time + ``value`` letter into a PhonemeCue
    using the RHUBARB_TO_VISEME map.
    """
    binary = rhubarb_path.strip() if rhubarb_path.strip() else shutil.which("rhubarb")
    if not binary:
        raise BackendUnavailable("rhubarb executable not found")

    try:
        completed = subprocess.run(  # noqa: S603 — args list, no shell
            [binary, "-f", "json", audio_path],
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BackendUnavailable(f"rhubarb subprocess failed: {exc}") from exc

    if completed.returncode != 0:
        raise BackendUnavailable(
            f"rhubarb exited {completed.returncode}: {completed.stderr[:200]}"
        )

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise BackendUnavailable(f"rhubarb output not valid JSON: {exc}") from exc

    cues: list[PhonemeCue] = []
    for entry in payload.get("mouthCues", []):
        start = float(entry.get("start", 0.0))
        letter = str(entry.get("value", "X"))
        viseme = RHUBARB_TO_VISEME.get(letter, "rest")
        cues.append(PhonemeCue(time_seconds=start, viseme_name=viseme))
    return cues
