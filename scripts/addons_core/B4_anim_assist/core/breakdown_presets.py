"""Built-in + user breakdown presets.

A preset is a small dict that names a factor / mode / mask combination.
Applying a preset is a pure function that builds a
``BreakdownOptions`` from the preset and hands it to
``breakdown_core.apply_breakdown``.

User presets are persisted on the breakdown Scene PropertyGroup so they
survive save/reload without a filesystem dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .breakdown_core import (
    BreakdownOptions,
    MODE_PULL_NEXT,
    MODE_PULL_PREV,
    MODE_PUSH_NEXT,
    MODE_PUSH_PREV,
    MODE_REPLACE,
)
from .breakdown_masks import BreakdownMask

if TYPE_CHECKING:
    pass

__all__ = [
    "BreakdownPreset",
    "BUILTIN_PRESETS",
    "list_builtin_presets",
    "find_builtin_preset",
    "options_from_preset",
    "PRESET_ENUM_ITEMS",
    "preset_enum_items",
    "preset_enum_items_callback",
]


@dataclass(frozen=True)
class BreakdownPreset:
    """Immutable preset storing slider position and mode for breakdown breakdown operations.

    Presets let animators reuse their favorite breakdown ratios (e.g., "60% toward next,
    push rotation 10%") across scenes. Built-in presets are frozen dataclasses for
    type safety and IDE autocomplete.
    """
    name: str
    description: str
    factor: float
    mode: str
    mask_kind: str  # "ALL" / "LOCATION" / "ROTATION" / "SCALE" / "TRANSFORM"
    category: str = "Breakdown"


def _mask_from_kind(kind: str) -> BreakdownMask:
    if kind == "LOCATION":
        return BreakdownMask.location_only()
    if kind == "ROTATION":
        return BreakdownMask.rotation_only()
    if kind == "SCALE":
        return BreakdownMask.scale_only()
    if kind == "TRANSFORM":
        return BreakdownMask.transform_only()
    return BreakdownMask()


BUILTIN_PRESETS: tuple[BreakdownPreset, ...] = (
    BreakdownPreset(
        name="25% Favor Previous",
        description="Weighted 25% breakdown biased toward the previous pose.",
        factor=0.25,
        mode=MODE_REPLACE,
        mask_kind="ALL",
    ),
    BreakdownPreset(
        name="Midpoint",
        description="Clean 50/50 midpoint between previous and next pose.",
        factor=0.50,
        mode=MODE_REPLACE,
        mask_kind="ALL",
    ),
    BreakdownPreset(
        name="75% Favor Next",
        description="Weighted 75% breakdown biased toward the next pose.",
        factor=0.75,
        mode=MODE_REPLACE,
        mask_kind="ALL",
    ),
    BreakdownPreset(
        name="Rotation Midpoint",
        description="Midpoint affecting rotation channels only.",
        factor=0.50,
        mode=MODE_REPLACE,
        mask_kind="ROTATION",
    ),
    BreakdownPreset(
        name="Location Midpoint",
        description="Midpoint affecting location channels only.",
        factor=0.50,
        mode=MODE_REPLACE,
        mask_kind="LOCATION",
    ),
    BreakdownPreset(
        name="Push From Previous",
        description="Extrapolate past the previous pose for a snappy out.",
        factor=0.25,
        mode=MODE_PUSH_PREV,
        mask_kind="ALL",
    ),
    BreakdownPreset(
        name="Push Into Next",
        description="Extrapolate past the next pose for a heavy anticipation.",
        factor=0.75,
        mode=MODE_PUSH_NEXT,
        mask_kind="ALL",
    ),
    BreakdownPreset(
        name="Pull To Previous",
        description="Pull the new key back toward the previous pose.",
        factor=0.25,
        mode=MODE_PULL_PREV,
        mask_kind="ALL",
    ),
    BreakdownPreset(
        name="Pull To Next",
        description="Pull the new key forward toward the next pose.",
        factor=0.75,
        mode=MODE_PULL_NEXT,
        mask_kind="ALL",
    ),
)


def list_builtin_presets() -> list[BreakdownPreset]:
    """Return a list of all built-in breakdown presets."""
    return list(BUILTIN_PRESETS)


def find_builtin_preset(name: str) -> BreakdownPreset | None:
    """Find a built-in preset by name, or return None."""
    for p in BUILTIN_PRESETS:
        if p.name == name:
            return p
    return None


def options_from_preset(preset: BreakdownPreset) -> BreakdownOptions:
    """Build a BreakdownOptions from a preset."""
    return BreakdownOptions(
        factor=preset.factor,
        mode=preset.mode,
        mask=_mask_from_kind(preset.mask_kind),
    )


#: Module-level tuple of EnumProperty items. Held at module scope so the
#: string objects are retained for the lifetime of the process — Blender
#: does NOT keep strings alive when ``items=`` is handed a freshly
#: constructed list/tuple from a function call at class-body time, which
#: is the canonical source of the "random unicode in dropdowns" bug.
PRESET_ENUM_ITEMS: tuple[tuple[str, str, str], ...] = tuple(
    (p.name, p.name, p.description) for p in BUILTIN_PRESETS
)


def preset_enum_items() -> tuple[tuple[str, str, str], ...]:
    """Return the cached EnumProperty items tuple for built-in presets."""
    return PRESET_ENUM_ITEMS


def preset_enum_items_callback(self, context) -> tuple[tuple[str, str, str], ...]:  # noqa: ARG001
    """Callable form for ``EnumProperty(items=...)`` usage.

    Returning the module-level tuple keeps Blender happy without
    reconstructing strings on every dropdown render.
    """
    return PRESET_ENUM_ITEMS
