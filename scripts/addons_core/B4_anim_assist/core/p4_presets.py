"""Transform multiplier presets for offset tool operators.

A preset multiplies the user-entered offset amounts by a fixed factor
before they hit the pipeline. This gives animators a quick way to apply
"Tiny", "Normal", "Big" style nudges without editing the sliders each
time.

These are NOT curve-shape presets and they do NOT touch fcurve tangents.
They are scalar multipliers on the already-computed ``(tx, ty, tz, rx,
ry, rz, sx, sy, sz)`` delta.

The preset list is exposed as a Blender-safe tuple of
``(identifier, label, description)`` so ``EnumProperty(items=...)`` can
reference it directly. The callable form is also provided for enum-item retention.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "OffsetPreset",
    "BUILTIN_PRESETS",
    "PRESET_ENUM_ITEMS",
    "preset_enum_items_callback",
    "preset_by_id",
]


@dataclass(frozen=True)
class OffsetPreset:
    """Immutable multiplier preset for scaling offset amounts.

    Presets (Tiny, Small, Normal, Big, Huge) let animators apply quick nudges
    without tweaking sliders. The multiplier scales the user-entered delta
    before it enters the basis-conversion pipeline.
    """
    name: str
    multiplier: float
    description: str


BUILTIN_PRESETS: tuple[OffsetPreset, ...] = (
    OffsetPreset(
        name="Tiny",
        multiplier=0.1,
        description="Reduces the entered offset to one tenth for subtle nudges.",
    ),
    OffsetPreset(
        name="Small",
        multiplier=0.25,
        description="Reduces the entered offset to a quarter.",
    ),
    OffsetPreset(
        name="Normal",
        multiplier=1.0,
        description="Applies the entered offset verbatim. The default preset.",
    ),
    OffsetPreset(
        name="Big",
        multiplier=2.0,
        description="Doubles the entered offset for exaggerated pushes.",
    ),
    OffsetPreset(
        name="Huge",
        multiplier=4.0,
        description="Quadruples the entered offset for extreme stylised pushes.",
    ),
)


# Module-level constant so Blender's EnumProperty retains the string
# references across registration and reload (same pattern as breakdown presets).
PRESET_ENUM_ITEMS: tuple[tuple[str, str, str], ...] = tuple(
    (p.name.upper(), p.name, p.description) for p in BUILTIN_PRESETS
)


def preset_enum_items_callback(self, context) -> tuple[tuple[str, str, str], ...]:  # noqa: ARG001
    """Callable form required by ``EnumProperty(items=...)`` to avoid the
    Blender string-retention bug."""
    return PRESET_ENUM_ITEMS


def preset_by_id(identifier: str) -> OffsetPreset | None:
    """Return the preset whose upper-case name matches ``identifier``."""
    if not identifier:
        return None
    target = identifier.upper()
    for preset in BUILTIN_PRESETS:
        if preset.name.upper() == target:
            return preset
    return None
