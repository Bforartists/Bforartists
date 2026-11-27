# --- PROXY AND BAKE CONTROLS ---
"""Pure-Python helpers for proxy creation, transform sampling, and key reduction.

All functions in this module are free of ``bpy`` side-effects and can be
unit-tested outside Blender (except those that require a live scene).
The heavy bpy work is confined to thin wrappers in the operator modules.

Proxy types match the proxy spec features 11-19:
  11 — Orientation proxy
  12 — Translation proxy
  13 — Aim proxy
  14 — Pole helper
  15 — Up-vector helper
  16 — Multi-target average proxy
  17 — Parent-space proxy
  18 — World-space proxy
  19 — Camera-space proxy
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from .logging import get_logger

_log = get_logger(__name__)

__all__ = [
    "ProxyConfig",
    "PROXY_CONFIGS",
    "resolve_bake_range",
    "KeySample",
    "reduce_keys",
    "CHANNEL_GROUPS",
    "channels_for_mode",
    "proxy_object_name",
    "locator_object_name",
    "mirror_name",
]


# ---------------------------------------------------------------------------
# Proxy configuration registry (Features 11-19)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProxyConfig:
    """Describes how to set up one proxy type."""

    display_type: str = "EMPTY"
    empty_display: str = "PLAIN_AXES"
    constraint_type: str | None = None
    constraint_suffix: str = ""
    #: If True, the constraint's influence starts at 0.0 and must be keyed.
    keyed_influence: bool = False
    #: Brief label used for UI display.
    label: str = ""
    #: Feature number in the spec.
    feature: int = 0


PROXY_CONFIGS: dict[str, ProxyConfig] = {
    "ORIENTATION": ProxyConfig(
        empty_display="SINGLE_ARROW",
        constraint_type="COPY_ROTATION",
        constraint_suffix="CopyRot",
        label="Orientation Proxy",
        feature=11,
    ),
    "TRANSLATION": ProxyConfig(
        empty_display="PLAIN_AXES",
        constraint_type="COPY_LOCATION",
        constraint_suffix="CopyLoc",
        label="Translation Proxy",
        feature=12,
    ),
    "AIM": ProxyConfig(
        empty_display="CONE",
        constraint_type="TRACK_TO",
        constraint_suffix="TrackTo",
        label="Aim Proxy",
        feature=13,
    ),
    "POLE": ProxyConfig(
        empty_display="SPHERE",
        constraint_type=None,
        constraint_suffix="Pole",
        label="Pole Helper",
        feature=14,
    ),
    "UP_VECTOR": ProxyConfig(
        empty_display="SINGLE_ARROW",
        constraint_type=None,
        constraint_suffix="UpVec",
        label="Up-Vector Helper",
        feature=15,
    ),
    "MULTI_TARGET": ProxyConfig(
        empty_display="CUBE",
        constraint_type=None,
        constraint_suffix="MultiAvg",
        label="Multi-Target Average",
        feature=16,
    ),
    "PARENT_SPACE": ProxyConfig(
        empty_display="CUBE",
        constraint_type="CHILD_OF",
        constraint_suffix="ChildOf",
        label="Parent-Space Proxy",
        feature=17,
    ),
    "WORLD_SPACE": ProxyConfig(
        empty_display="ARROWS",
        constraint_type="COPY_TRANSFORMS",
        constraint_suffix="CopyTfm",
        label="World-Space Proxy",
        feature=18,
    ),
    "CAMERA_SPACE": ProxyConfig(
        empty_display="CAMERA_DATA",
        constraint_type=None,
        constraint_suffix="CamSpace",
        label="Camera-Space Proxy",
        feature=19,
        keyed_influence=True,
    ),
}


# ---------------------------------------------------------------------------
# Bake frame range resolution
# ---------------------------------------------------------------------------

def resolve_bake_range(
    mode: str,
    scene_start: int,
    scene_end: int,
    action_start: float | None,
    action_end: float | None,
    custom_start: float,
    custom_end: float,
    selected_frames: Sequence[float] | None = None,  # type: ignore[type-arg]
    preview_start: int | None = None,
    preview_end: int | None = None,
) -> tuple[int, int]:
    """Return ``(start, end)`` integer frame range for baking.

    Falls back to scene range if the requested mode cannot be resolved.
    """
    if mode == "ACTION" and action_start is not None and action_end is not None:
        return int(math.floor(action_start)), int(math.ceil(action_end))
    if mode == "CUSTOM":
        lo = int(min(custom_start, custom_end))
        hi = int(max(custom_start, custom_end))
        return lo, hi
    if mode == "SELECTION" and selected_frames:
        return int(min(selected_frames)), int(max(selected_frames))
    if mode == "PREVIEW" and preview_start is not None and preview_end is not None:
        return int(preview_start), int(preview_end)
    # Default: SCENE
    return int(scene_start), int(scene_end)


# ---------------------------------------------------------------------------
# Key reduction (Douglas-Peucker-style on 2-D (frame, value) points)
# ---------------------------------------------------------------------------

@dataclass
class KeySample:
    """A single (frame, value) sample used during bake and reduction."""

    frame: float
    value: float


def reduce_keys(
    samples: list[KeySample],
    tolerance: float,
) -> list[KeySample]:
    """Remove redundant keys using a Ramer-Douglas-Peucker simplification.

    *samples* must be sorted by frame. Returns a subset of the original
    list preserving the first and last samples and every sample whose
    removal would cause a deviation larger than *tolerance*.
    """
    if len(samples) <= 2:
        return list(samples)
    return _rdp(samples, 0, len(samples) - 1, tolerance)


def _rdp(
    pts: list[KeySample],
    lo: int,
    hi: int,
    eps: float,
) -> list[KeySample]:
    """Recursive Ramer-Douglas-Peucker on (frame, value) pairs."""
    if hi - lo < 2:
        return [pts[lo], pts[hi]]

    dx = pts[hi].frame - pts[lo].frame
    dy = pts[hi].value - pts[lo].value
    line_len = math.hypot(dx, dy)

    max_dist = 0.0
    max_idx = lo
    for i in range(lo + 1, hi):
        if line_len < 1e-12:
            dist = math.hypot(pts[i].frame - pts[lo].frame,
                              pts[i].value - pts[lo].value)
        else:
            cross = abs(dx * (pts[lo].value - pts[i].value) -
                        (pts[lo].frame - pts[i].frame) * dy)
            dist = cross / line_len
        if dist > max_dist:
            max_dist = dist
            max_idx = i

    if max_dist > eps:
        left = _rdp(pts, lo, max_idx, eps)
        right = _rdp(pts, max_idx, hi, eps)
        return left + right[1:]
    return [pts[lo], pts[hi]]


# ---------------------------------------------------------------------------
# Transform channel helpers
# ---------------------------------------------------------------------------

CHANNEL_GROUPS: dict[str, tuple[str, ...]] = {
    "ALL": ("location", "rotation_euler", "rotation_quaternion", "scale"),
    "LOC": ("location",),
    "ROT": ("rotation_euler", "rotation_quaternion"),
    "LOCROT": ("location", "rotation_euler", "rotation_quaternion"),
    "SELECTED": (),  # resolved dynamically by bake ops
}


def channels_for_mode(mode: str) -> tuple[str, ...]:
    """Return the RNA data-path prefixes for *mode* (ALL, LOC, ROT, LOCROT)."""
    return CHANNEL_GROUPS.get(mode, CHANNEL_GROUPS["ALL"])


# ---------------------------------------------------------------------------
# Proxy naming
# ---------------------------------------------------------------------------

def proxy_object_name(target_name: str, proxy_type: str, short_id: str) -> str:
    """Generate a descriptive name for a new proxy empty.

    Example: ``"AA_P7_Proxy_Armature_Orientation_a3f8c12b"``
    """
    return f"AA_P7_Proxy_{target_name}_{proxy_type}_{short_id}"


def locator_object_name(target_name: str, short_id: str) -> str:
    """Generate a name for a locator empty.

    Example: ``"AA_P7_Loc_BoneName_a3f8c12b"``
    """
    return f"AA_P7_Loc_{target_name}_{short_id}"


# ---------------------------------------------------------------------------
# Mirror naming helper
# ---------------------------------------------------------------------------

_MIRROR_PAIRS: tuple[tuple[str, str], ...] = (
    (".L", ".R"),
    ("_L", "_R"),
    (".l", ".r"),
    ("_l", "_r"),
    ("Left", "Right"),
    ("left", "right"),
)


def mirror_name(name: str) -> str:
    """Swap L/R naming tokens. Returns the original if no pattern found."""
    for left, right in _MIRROR_PAIRS:
        if left in name:
            return name.replace(left, right, 1)
        if right in name:
            return name.replace(right, left, 1)
    return name
