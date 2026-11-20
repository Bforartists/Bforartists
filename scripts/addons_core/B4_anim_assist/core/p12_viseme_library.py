# --- VISEME LIBRARY (Phase 12) ---
"""Built-in viseme libraries for the lipsync system.

A *viseme library* is a mapping from viseme name → pose, where a pose is a
mapping from logical face role → (location_offset, rotation_euler, scale).
Roles are rig-agnostic strings ("jaw", "lip_upper", "corner_L"); the
``AA_P12_RigWiring`` collection on the scene maps roles to actual bone names.

This indirection lets one viseme library drive any rig: Rigify, Auto-Rig Pro,
or a custom face rig — only the wiring changes per character.

Library shape
-------------
::

    VisemeLibrary = dict[str, dict[str, tuple[Vec3, Vec3, Vec3]]]
    #               viseme  →  role  →  (loc, rot_euler, scale)

The values stored are *deltas from rest pose*. The bake operator applies them
on top of the rest pose to produce final bone transforms.

Three libraries ship by default:
* ``BASIC_JAW`` — one role, ``jaw`` only, used for amplitude-driven mouth-open.
* ``CARTOON_5`` — A, E, I, O, U + closed; snappy reads suited to stylised work.
* ``REALISTIC_12`` — Preston Blair viseme set with anticipation cues.

Custom poses captured by ``AA_OT_p12_capture_viseme`` are stored on the
scene's ``AA_P12_Properties.viseme_poses`` collection as JSON, not here.
"""

from __future__ import annotations

import json
from typing import Iterable

from .logging import get_logger

__all__ = [
    "VisemePose",
    "VisemeLibrary",
    "BASIC_JAW",
    "CARTOON_5",
    "REALISTIC_12",
    "LIBRARIES",
    "REST_POSE",
    "get_library",
    "library_role_set",
    "pose_to_json",
    "pose_from_json",
]

_log = get_logger(__name__)

# Type aliases — kept lightweight so this module imports without bpy.
Vec3 = tuple[float, float, float]
VisemePose = dict[str, tuple[Vec3, Vec3, Vec3]]
VisemeLibrary = dict[str, VisemePose]

REST_LOC: Vec3 = (0.0, 0.0, 0.0)
REST_ROT: Vec3 = (0.0, 0.0, 0.0)
REST_SCALE: Vec3 = (1.0, 1.0, 1.0)
REST_POSE: VisemePose = {}


# ---------------------------------------------------------------------------
# Built-in libraries — values are intentionally mild; users tune per-rig.
# ---------------------------------------------------------------------------

# Single jaw bone, opened on a roll axis. Conservative default — animator
# scales via AA_P12_Properties.amplitude_jaw_scale.
BASIC_JAW: VisemeLibrary = {
    "rest": {
        "jaw": (REST_LOC, REST_ROT, REST_SCALE),
    },
    "open": {
        "jaw": (REST_LOC, (0.35, 0.0, 0.0), REST_SCALE),
    },
}

# Cartoon 5: classic broad-stroke read. Lip + jaw work together. Roles
# referenced: jaw, lip_upper, lip_lower, corner_L, corner_R.
CARTOON_5: VisemeLibrary = {
    "rest": {
        "jaw": (REST_LOC, REST_ROT, REST_SCALE),
        "lip_upper": (REST_LOC, REST_ROT, REST_SCALE),
        "lip_lower": (REST_LOC, REST_ROT, REST_SCALE),
        "corner_L": (REST_LOC, REST_ROT, REST_SCALE),
        "corner_R": (REST_LOC, REST_ROT, REST_SCALE),
    },
    "A": {
        "jaw": (REST_LOC, (0.45, 0.0, 0.0), REST_SCALE),
        "lip_upper": ((0.0, 0.0, 0.005), REST_ROT, REST_SCALE),
        "lip_lower": ((0.0, 0.0, -0.012), REST_ROT, REST_SCALE),
    },
    "E": {
        "jaw": (REST_LOC, (0.18, 0.0, 0.0), REST_SCALE),
        "corner_L": ((0.012, 0.0, 0.005), REST_ROT, REST_SCALE),
        "corner_R": ((-0.012, 0.0, 0.005), REST_ROT, REST_SCALE),
    },
    "I": {
        "jaw": (REST_LOC, (0.12, 0.0, 0.0), REST_SCALE),
        "lip_upper": ((0.0, 0.0, 0.003), REST_ROT, REST_SCALE),
        "corner_L": ((0.018, 0.0, 0.0), REST_ROT, REST_SCALE),
        "corner_R": ((-0.018, 0.0, 0.0), REST_ROT, REST_SCALE),
    },
    "O": {
        "jaw": (REST_LOC, (0.32, 0.0, 0.0), REST_SCALE),
        "lip_upper": ((0.0, 0.005, 0.004), REST_ROT, REST_SCALE),
        "lip_lower": ((0.0, 0.005, -0.004), REST_ROT, REST_SCALE),
        "corner_L": ((-0.005, 0.005, 0.0), REST_ROT, REST_SCALE),
        "corner_R": ((0.005, 0.005, 0.0), REST_ROT, REST_SCALE),
    },
    "U": {
        "jaw": (REST_LOC, (0.20, 0.0, 0.0), REST_SCALE),
        "lip_upper": ((0.0, 0.008, 0.002), REST_ROT, REST_SCALE),
        "lip_lower": ((0.0, 0.008, -0.002), REST_ROT, REST_SCALE),
        "corner_L": ((-0.010, 0.008, 0.0), REST_ROT, REST_SCALE),
        "corner_R": ((0.010, 0.008, 0.0), REST_ROT, REST_SCALE),
    },
}

# Preston Blair 12 — phonetic groupings used by Rhubarb (A, B, C, D, E, F,
# G, H, X mapped here to the classic 12-mouth-shape set). Same role
# vocabulary as CARTOON_5 plus tongue.
REALISTIC_12: VisemeLibrary = {
    "rest": {
        "jaw": (REST_LOC, REST_ROT, REST_SCALE),
        "lip_upper": (REST_LOC, REST_ROT, REST_SCALE),
        "lip_lower": (REST_LOC, REST_ROT, REST_SCALE),
        "corner_L": (REST_LOC, REST_ROT, REST_SCALE),
        "corner_R": (REST_LOC, REST_ROT, REST_SCALE),
        "tongue": (REST_LOC, REST_ROT, REST_SCALE),
    },
    "A_I": {  # ah, eye — open mouth
        "jaw": (REST_LOC, (0.40, 0.0, 0.0), REST_SCALE),
    },
    "E": {
        "jaw": (REST_LOC, (0.18, 0.0, 0.0), REST_SCALE),
        "corner_L": ((0.012, 0.0, 0.005), REST_ROT, REST_SCALE),
        "corner_R": ((-0.012, 0.0, 0.005), REST_ROT, REST_SCALE),
    },
    "O": {
        "jaw": (REST_LOC, (0.30, 0.0, 0.0), REST_SCALE),
        "lip_upper": ((0.0, 0.005, 0.004), REST_ROT, REST_SCALE),
        "lip_lower": ((0.0, 0.005, -0.004), REST_ROT, REST_SCALE),
    },
    "U": {
        "jaw": (REST_LOC, (0.18, 0.0, 0.0), REST_SCALE),
        "lip_upper": ((0.0, 0.010, 0.002), REST_ROT, REST_SCALE),
        "lip_lower": ((0.0, 0.010, -0.002), REST_ROT, REST_SCALE),
    },
    "M_B_P": {  # closed lips
        "jaw": (REST_LOC, (0.02, 0.0, 0.0), REST_SCALE),
        "lip_upper": ((0.0, 0.0, -0.003), REST_ROT, REST_SCALE),
        "lip_lower": ((0.0, 0.0, 0.003), REST_ROT, REST_SCALE),
    },
    "F_V": {  # lip-on-teeth
        "jaw": (REST_LOC, (0.06, 0.0, 0.0), REST_SCALE),
        "lip_lower": ((0.0, 0.004, 0.002), REST_ROT, REST_SCALE),
    },
    "L": {
        "jaw": (REST_LOC, (0.20, 0.0, 0.0), REST_SCALE),
        "tongue": ((0.0, 0.008, 0.005), REST_ROT, REST_SCALE),
    },
    "S_Z": {
        "jaw": (REST_LOC, (0.08, 0.0, 0.0), REST_SCALE),
        "corner_L": ((0.008, 0.0, 0.0), REST_ROT, REST_SCALE),
        "corner_R": ((-0.008, 0.0, 0.0), REST_ROT, REST_SCALE),
    },
    "Th": {
        "jaw": (REST_LOC, (0.14, 0.0, 0.0), REST_SCALE),
        "tongue": ((0.0, 0.012, 0.0), REST_ROT, REST_SCALE),
    },
    "Sh_Ch": {
        "jaw": (REST_LOC, (0.16, 0.0, 0.0), REST_SCALE),
        "lip_upper": ((0.0, 0.006, 0.0), REST_ROT, REST_SCALE),
        "lip_lower": ((0.0, 0.006, 0.0), REST_ROT, REST_SCALE),
    },
    "K_G": {
        "jaw": (REST_LOC, (0.12, 0.0, 0.0), REST_SCALE),
    },
}


LIBRARIES: dict[str, VisemeLibrary] = {
    "BASIC_JAW": BASIC_JAW,
    "CARTOON_5": CARTOON_5,
    "REALISTIC_12": REALISTIC_12,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_library(library_id: str) -> VisemeLibrary:
    """Return the named built-in library, or raise KeyError.

    Unknown ids return an empty dict so callers can fall back to amplitude
    behaviour without crashing — but they should ideally check first.
    """
    lib = LIBRARIES.get(library_id)
    if lib is None:
        _log.warning("Unknown viseme library '%s' — returning empty", library_id)
        return {}
    return lib


def library_role_set(library_id: str) -> set[str]:
    """Return the union of all face roles referenced by *library_id*."""
    lib = get_library(library_id)
    roles: set[str] = set()
    for pose in lib.values():
        roles.update(pose.keys())
    return roles


def pose_to_json(pose: VisemePose) -> str:
    """Serialise a pose to compact JSON (used when persisting user captures)."""
    serialisable = {
        role: {
            "loc": list(loc),
            "rot": list(rot),
            "scale": list(scale),
        }
        for role, (loc, rot, scale) in pose.items()
    }
    return json.dumps(serialisable, separators=(",", ":"))


def pose_from_json(payload: str) -> VisemePose:
    """Parse a pose previously serialised with ``pose_to_json``.

    Returns ``REST_POSE`` (empty) if *payload* is empty or malformed — the
    bake operator treats that as "no override, use rest" rather than crashing.
    """
    if not payload:
        return {}
    try:
        data = json.loads(payload)
    except (json.JSONDecodeError, TypeError):
        _log.warning("Could not decode viseme pose JSON: %r", payload[:60])
        return {}
    out: VisemePose = {}
    for role, channels in data.items():
        try:
            loc = tuple(channels.get("loc", REST_LOC))
            rot = tuple(channels.get("rot", REST_ROT))
            scale = tuple(channels.get("scale", REST_SCALE))
            out[role] = (loc, rot, scale)  # type: ignore[assignment]
        except (AttributeError, TypeError):
            continue
    return out


def merge_user_overrides(
    library_id: str,
    user_poses: Iterable[tuple[str, str]],
) -> VisemeLibrary:
    """Return a copy of the named library with user-captured poses overlaid.

    *user_poses* is an iterable of ``(viseme_name, pose_json)`` tuples — the
    shape stored on ``AA_P12_Properties.viseme_poses``. User captures replace
    built-in poses for the same viseme; built-ins not overridden survive.
    """
    base = dict(get_library(library_id))
    for viseme_name, payload in user_poses:
        parsed = pose_from_json(payload)
        if parsed:
            base[viseme_name] = parsed
    return base
