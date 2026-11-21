# --- MIRRORING AND SYMMETRY HELPERS ---
"""Scene-scoped PropertyGroup for mirroring and pair detection.

Mounted on ``Scene.anim_assist_p9`` so it does not collide with other modules.
Every enum uses the callable-items pattern for Blender string-retention GC safety.

Covers all mirroring and symmetry features: bone pair mirroring, axis selection, space modes,
naming pattern detection, manual pair overrides, and naming exceptions.
"""

from __future__ import annotations

import bpy
from bpy.props import (
    BoolProperty,
    BoolVectorProperty,
    CollectionProperty,
    EnumProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)

from .logging import get_logger

__all__ = [
    "P9_SCENE_ATTR",
    "AA_P9_PairOverride",
    "AA_P9_NamingException",
    "AA_P9_Properties",
    "CLASSES",
    "get_p9",
    "register_properties",
    "unregister_properties",
]

P9_SCENE_ATTR = "anim_assist_p9"

# --- Logger (for future use) ---
log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Enum item tables (module-level for GC safety)
# ---------------------------------------------------------------------------

MIRROR_AXIS_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("X", "X Axis",
     "Mirror across X axis (left/right)"),
    ("Y", "Y Axis",
     "Mirror across Y axis (front/back)"),
    ("Z", "Z Axis",
     "Mirror across Z axis (up/down)"),
)

MIRROR_SPACE_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("LOCAL", "Local",
     "Mirror using local space (standard for most rigs)"),
    ("WORLD", "World",
     "Mirror using world space"),
    ("VISUAL", "Visual",
     "Mirror using evaluated visual matrices (for constrained rigs)"),
)

NAMING_PATTERN_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("AUTO", "Auto Detect",
     "Automatically detect naming convention"),
    ("DOT_LR", ".L/.R",
     "Detect bones ending in .L and .R"),
    ("UNDER_LR", "_L/_R",
     "Detect bones ending in _L and _R"),
    ("WORD_LR", "Left/Right",
     "Detect bones containing Left or Right in the name"),
    ("CUSTOM", "Custom",
     "Use custom regex patterns"),
)


def _mirror_axis_items(self, context):  # noqa: ARG001
    return MIRROR_AXIS_ITEMS


def _mirror_space_items(self, context):  # noqa: ARG001
    return MIRROR_SPACE_ITEMS


def _naming_pattern_items(self, context):  # noqa: ARG001
    return NAMING_PATTERN_ITEMS


# ---------------------------------------------------------------------------
# PropertyGroups for collections
# ---------------------------------------------------------------------------

class AA_P9_PairOverride(bpy.types.PropertyGroup):
    """Manual bone pair definition for mirror operations."""

    bone_a: StringProperty(  # type: ignore[valid-type]
        name="Bone A",
        description="First bone in the manual pair",
        default="",
    )

    bone_b: StringProperty(  # type: ignore[valid-type]
        name="Bone B",
        description="Second bone in the manual pair (opposite side)",
        default="",
    )


class AA_P9_NamingException(bpy.types.PropertyGroup):
    """Non-standard naming override for bone pairing."""

    original: StringProperty(  # type: ignore[valid-type]
        name="Original",
        description="Original bone name",
        default="",
    )

    opposite: StringProperty(  # type: ignore[valid-type]
        name="Opposite",
        description="Opposite bone name override",
        default="",
    )


# ---------------------------------------------------------------------------
# Main PropertyGroup
# ---------------------------------------------------------------------------

class AA_P9_Properties(bpy.types.PropertyGroup):
    """Scene-scoped defaults for mirroring mirroring tools."""

    # ----- Mirror Settings -----

    mirror_axis: EnumProperty(  # type: ignore[valid-type]
        name="Mirror Axis",
        description="Axis to mirror transforms across",
        items=_mirror_axis_items,
        default=0,
    )

    mirror_space: EnumProperty(  # type: ignore[valid-type]
        name="Mirror Space",
        description="Coordinate space for mirror operations",
        items=_mirror_space_items,
        default=0,
    )

    naming_pattern: EnumProperty(  # type: ignore[valid-type]
        name="Naming Pattern",
        description="Bone naming convention for pair detection",
        items=_naming_pattern_items,
        default=0,
    )

    custom_left_pattern: StringProperty(  # type: ignore[valid-type]
        name="Left Pattern",
        description="Regex pattern matching left-side bones",
        default="",
    )

    custom_right_pattern: StringProperty(  # type: ignore[valid-type]
        name="Right Pattern",
        description="Regex pattern matching right-side bones",
        default="",
    )

    # ----- Channel Filters -----

    mirror_location: BoolProperty(  # type: ignore[valid-type]
        name="Location",
        description="Include location channels in mirror",
        default=True,
    )

    mirror_rotation: BoolProperty(  # type: ignore[valid-type]
        name="Rotation",
        description="Include rotation channels in mirror",
        default=True,
    )

    mirror_scale: BoolProperty(  # type: ignore[valid-type]
        name="Scale",
        description="Include scale channels in mirror",
        default=True,
    )

    axis_mask: BoolVectorProperty(  # type: ignore[valid-type]
        name="Axis Mask",
        description="Per-axis enable mask for mirroring",
        size=3,
        default=(True, True, True),
        subtype="XYZ",
    )

    # ----- Safety -----

    respect_locks: BoolProperty(  # type: ignore[valid-type]
        name="Respect Locks",
        description="Skip locked transform channels during mirror",
        default=True,
    )

    respect_drivers: BoolProperty(  # type: ignore[valid-type]
        name="Respect Drivers",
        description="Skip driven channels during mirror",
        default=True,
    )

    auto_key_mirror: BoolProperty(  # type: ignore[valid-type]
        name="Auto Key",
        description="Automatically insert keyframes after mirror operations",
        default=True,
    )

    maintain_offset: BoolProperty(  # type: ignore[valid-type]
        name="Maintain Offset",
        description=(
            "Preserve existing offset between source and target during mirror"
        ),
        default=False,
    )

    # ----- Scope -----

    mirror_keyed_only: BoolProperty(  # type: ignore[valid-type]
        name="Keyed Only",
        description="Only mirror channels that have keyframes",
        default=False,
    )

    mirror_visible_only: BoolProperty(  # type: ignore[valid-type]
        name="Visible Only",
        description="Only mirror channels visible in the editor",
        default=False,
    )

    # ----- Pair Management -----

    pair_overrides: CollectionProperty(  # type: ignore[valid-type]
        type=AA_P9_PairOverride,
        name="Pair Overrides",
        description="Manual bone pair definitions that override auto-detection",
    )

    pair_overrides_index: IntProperty(  # type: ignore[valid-type]
        name="Active Override",
        default=0,
        min=0,
    )

    naming_exceptions: CollectionProperty(  # type: ignore[valid-type]
        type=AA_P9_NamingException,
        name="Naming Exceptions",
        description="Bone naming overrides for non-standard names",
    )

    naming_exceptions_index: IntProperty(  # type: ignore[valid-type]
        name="Active Exception",
        default=0,
        min=0,
    )


# ---------------------------------------------------------------------------
# Registration helpers
# ---------------------------------------------------------------------------

CLASSES: tuple[type, ...] = (
    AA_P9_PairOverride,
    AA_P9_NamingException,
    AA_P9_Properties,
)


def get_p9(context: bpy.types.Context) -> AA_P9_Properties | None:
    """Return the mirroring PropertyGroup from the current scene, or None."""
    scene = getattr(context, "scene", None)
    if scene is None:
        return None
    return getattr(scene, P9_SCENE_ATTR, None)


def register_properties() -> None:
    """Register mirroring properties on Scene.

    Attaches mirror axis settings, naming pattern detection, and pair
    override rules to the scene so they persist across file saves and are
    accessible to all mirroring mirroring operators.
    """
    bpy.types.Scene.anim_assist_p9 = PointerProperty(  # type: ignore[assignment]
        type=AA_P9_Properties,
        name="Anim Assist P9",
    )


def unregister_properties() -> None:
    """Unregister mirroring properties from Scene.

    Safe to call even if properties were never registered.
    """
    try:
        del bpy.types.Scene.anim_assist_p9
    except AttributeError:
        pass
