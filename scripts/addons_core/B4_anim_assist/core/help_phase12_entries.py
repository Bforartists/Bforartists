# --- LIPSYNC HELP ENTRIES (Phase 12) ---
"""Help entries for the Phase 12 lipsync system.

Mirrors the ``help_phase11_entries.py`` shape: defines a tuple of ``HelpEntry``
records and provides ``register`` / ``unregister`` functions called by
``__init__.py`` during the addon's startup/teardown sequence.
"""

from __future__ import annotations

from .help_registry import HelpEntry, register_phase_help, unregister_phase_help

__all__ = [
    "PHASE12_ENTRIES",
    "register",
    "unregister",
]

_PHASE = "phase12"


def _H(id_: str, label: str, tooltip: str, description: str, category: str) -> HelpEntry:
    return HelpEntry(
        id=id_,
        label=label,
        tooltip=tooltip,
        description=description,
        phase=_PHASE,
        category=category,
    )


PHASE12_ENTRIES: tuple[HelpEntry, ...] = (
    # ── Setup ────────────────────────────────────────────────────────────
    _H(
        "p12.setup_lipsync",
        "Setup Lipsync",
        "Create a lipsync layer wired to an audio file in one step",
        "Creates a Phase 11 override layer scoped to the face bone group, "
        "drops the chosen audio file as a sequencer sound strip, binds the "
        "layer to that strip, and loads the selected viseme library. After "
        "this runs, hit 'Bake Lipsync' to generate viseme keys, or pick "
        "'Markers Only' mode to place phoneme markers without writing keys.",
        "Setup",
    ),
    _H(
        "p12.viseme_library",
        "Viseme Library",
        "Pick the viseme set used to translate phonemes into mouth shapes",
        "Three built-in libraries ship by default:\n\n"
        "Basic Mouth Open — single jaw bone driven by audio amplitude. The "
        "safest choice; works on any rig with a 'jaw' bone.\n\n"
        "Cartoon (5 visemes) — A, E, I, O, U + closed. Snappy, stylised "
        "reads. Good fit for animated shorts and stylised game work.\n\n"
        "Realistic (12 visemes) — Preston Blair viseme set with anticipation. "
        "Used for naturalistic dialogue performance. Requires more bones to "
        "be wired in the Rig Wiring section.",
        "Setup",
    ),
    _H(
        "p12.backend",
        "Backend",
        "Which audio analysis engine drives bake output",
        "Amplitude Only — always available. Reads the WAV envelope and "
        "drives the jaw between rest and open across speech onsets. "
        "Approximate but reliable.\n\n"
        "Rhubarb Lip Sync — invokes the external Rhubarb CLI for phoneme-"
        "accurate viseme output. Requires the Rhubarb binary to be on your "
        "PATH or specified in the Rhubarb Path field. If not available, the "
        "system falls back to amplitude-only and surfaces a notice.",
        "Setup",
    ),
    _H(
        "p12.setup_mode",
        "Setup Mode",
        "Auto-bake versus markers-only on setup",
        "Auto Bake — runs analysis immediately and writes viseme keys to "
        "the layer. Best for blocking-stage performance.\n\n"
        "Markers Only — drops phoneme markers on the timeline but does not "
        "write keys. Hand-key against the markers, or hit Bake later. Best "
        "when you don't trust the auto output and want the markers as "
        "timing reference only.",
        "Setup",
    ),
    # ── Bake & rebake ───────────────────────────────────────────────────
    _H(
        "p12.bake_lipsync",
        "Bake Lipsync",
        "Run audio analysis and write viseme keyframes to the layer",
        "Analyses the bound audio with the selected backend and writes "
        "viseme-derived keyframes onto the layer's underlying Action. "
        "Anticipation frames pre-shape the mouth ahead of each phoneme "
        "onset for snappier reads.\n\n"
        "Manual Override Sanctuary: any keyframe you have hand-edited is "
        "flagged as a manual override and is preserved across rebakes. "
        "Only auto-baked keys are replaced. Your polish is safe.",
        "Bake",
    ),
    _H(
        "p12.clear_auto_keys",
        "Clear Auto Keys",
        "Remove auto-generated lipsync keys; preserve manual edits",
        "Walks the layer's Action and deletes every keyframe flagged as "
        "auto-baked. Manual override keys are preserved. Useful when you "
        "want to rebake from scratch with a different viseme library or "
        "backend setting.",
        "Bake",
    ),
    _H(
        "p12.rebake",
        "Rebake",
        "Clear auto keys then bake again — safe re-run",
        "Convenience: clear-auto-keys followed by bake. Manual override "
        "keys survive both steps. Run this when audio has changed (the "
        "layer header turns amber to flag stale audio) or when you want "
        "to apply new bake settings.",
        "Bake",
    ),
    # ── Audio binding ───────────────────────────────────────────────────
    _H(
        "p12.audio_path",
        "Audio File",
        "WAV file used for analysis",
        "Path to the audio file used to drive the lipsync layer. v11.0.0 "
        "supports .wav only. The file's SHA-256 is recorded at bake time; "
        "if the file changes later, the layer header turns amber to prompt "
        "a rebake. Manual override keys still survive that rebake.",
        "Audio",
    ),
    _H(
        "p12.is_stale",
        "Audio Changed",
        "True when the bound audio's hash differs from the last bake",
        "Set automatically when the system re-hashes the audio file and "
        "finds the digest no longer matches the one recorded at the last "
        "bake. Indicates that the lipsync no longer matches the audio. Hit "
        "Rebake to refresh — your manual edits are preserved.",
        "Audio",
    ),
    # ── Viseme editing ──────────────────────────────────────────────────
    _H(
        "p12.capture_viseme",
        "Capture Viseme",
        "Save the current pose as the named viseme",
        "Reads the current pose of the wired face bones and stores it as "
        "the named viseme in the scene's viseme library. Overrides the "
        "built-in for that viseme. Use this when a built-in pose doesn't "
        "fit your character — pose the face manually, hit Capture.",
        "Visemes",
    ),
    _H(
        "p12.rig_wiring",
        "Rig Wiring",
        "Map logical face roles to actual bones on this rig",
        "Viseme libraries reference logical roles (jaw, lip_upper, "
        "lip_lower, corner_L, corner_R, tongue) so the same library drives "
        "any rig. The rig wiring table maps each role to a concrete bone "
        "name on the active armature. Save the wiring as a preset to reuse "
        "it across shots for the same character.",
        "Visemes",
    ),
    # ── Manual overrides ────────────────────────────────────────────────
    _H(
        "p12.show_manual_overrides",
        "Highlight Manual Overrides",
        "Tint hand-edited keys differently from auto-baked keys",
        "When enabled, the panel marks keyframes the animator has touched "
        "with a distinct visual indicator so you can see at a glance which "
        "polish would survive a rebake versus which would be regenerated. "
        "Does not change behaviour — purely informational.",
        "Workflow",
    ),
)


def register() -> None:
    """Register lipsync help entries into the Help Browser registry."""
    register_phase_help(_PHASE, PHASE12_ENTRIES)


def unregister() -> None:
    """Unregister lipsync help entries from the Help Browser registry."""
    unregister_phase_help(_PHASE)
