"""Channel mask and exclusion-set resolution for breakdown breakdown ops.

A :class:`BreakdownMask` describes which transform kinds (location,
rotation, scale, custom) and which axis indices (0..3) are eligible for
a breakdown operation. An :class:`ExclusionSet` is a named list of
``data_path`` substrings that must never be touched.

This module has no Blender dependency beyond ``bpy.types.FCurve`` so it
is easy to unit-test offline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import bpy

from .fcurve_utils import (
    classify_transform_channel,
    get_sub_path_from_bone_fcurve,
)

__all__ = [
    "BreakdownMask",
    "ExclusionSet",
    "apply_exclusion",
    "KIND_LOCATION",
    "KIND_ROTATION",
    "KIND_SCALE",
    "KIND_CUSTOM",
    "ALL_KINDS",
]


# ---------------------------------------------------------------------------
# Transform kinds
# ---------------------------------------------------------------------------

KIND_LOCATION = "LOCATION"
KIND_ROTATION = "ROTATION"
KIND_SCALE = "SCALE"
KIND_CUSTOM = "CUSTOM"

ALL_KINDS: tuple[str, ...] = (
    KIND_LOCATION,
    KIND_ROTATION,
    KIND_SCALE,
    KIND_CUSTOM,
)


@dataclass(frozen=True)
class BreakdownMask:
    """Immutable selector for which channels a breakdown is allowed to hit."""

    location: bool = True
    rotation: bool = True
    scale: bool = True
    custom: bool = True
    axes: frozenset = field(default_factory=lambda: frozenset({0, 1, 2, 3}))
    skip_locked: bool = True
    skip_hidden: bool = False
    skip_muted: bool = False

    def allows_kind(self, kind: str | None) -> bool:
        """Return True when the mask permits the given transform kind (LOCATION, ROTATION, SCALE, or CUSTOM)."""
        if kind == KIND_LOCATION:
            return self.location
        if kind == KIND_ROTATION:
            return self.rotation
        if kind == KIND_SCALE:
            return self.scale
        return self.custom

    def allows_axis(self, array_index: int) -> bool:
        """Return True when the mask permits the given array index (0=X/W, 1=Y/X, 2=Z/Y, 3=W/Z)."""
        return int(array_index) in self.axes

    def allows_fcurve(self, fcurve: bpy.types.FCurve) -> bool:
        """Return True when ``fcurve`` passes every mask rule."""
        if self.skip_locked and bool(getattr(fcurve, "lock", False)):
            return False
        if self.skip_hidden and bool(getattr(fcurve, "hide", False)):
            return False
        if self.skip_muted and bool(getattr(fcurve, "mute", False)):
            return False

        kind = classify_transform_channel(
            get_sub_path_from_bone_fcurve(fcurve) or fcurve.data_path
        )
        if not self.allows_kind(kind):
            return False

        return self.allows_axis(int(getattr(fcurve, "array_index", 0)))

    # ---- Convenience constructors ----

    @classmethod
    def location_only(cls) -> "BreakdownMask":
        """Create a preset mask that allows only location channels."""
        return cls(location=True, rotation=False, scale=False, custom=False)

    @classmethod
    def rotation_only(cls) -> "BreakdownMask":
        """Create a preset mask that allows only rotation channels."""
        return cls(location=False, rotation=True, scale=False, custom=False)

    @classmethod
    def scale_only(cls) -> "BreakdownMask":
        """Create a preset mask that allows only scale channels."""
        return cls(location=False, rotation=False, scale=True, custom=False)

    @classmethod
    def transform_only(cls) -> "BreakdownMask":
        """Create a preset mask that allows location, rotation, and scale but not custom channels."""
        return cls(location=True, rotation=True, scale=True, custom=False)


# ---------------------------------------------------------------------------
# Exclusion sets
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ExclusionSet:
    """A named bag of data_path substring patterns that must be ignored."""

    name: str
    patterns: tuple[str, ...]

    def matches(self, fcurve: bpy.types.FCurve) -> bool:
        """Return True when ``fcurve``'s data_path matches any pattern."""
        dp = fcurve.data_path
        return any(pat in dp for pat in self.patterns)


def apply_exclusion(
    fcurves: Iterable[bpy.types.FCurve],
    exclusion: ExclusionSet | None,
) -> list[bpy.types.FCurve]:
    """Filter out fcurves matching the exclusion set, or return all if None."""
    if exclusion is None or not exclusion.patterns:
        return list(fcurves)
    return [fc for fc in fcurves if not exclusion.matches(fc)]
