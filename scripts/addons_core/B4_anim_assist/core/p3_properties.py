"""Scene-scoped PropertyGroup for breakdown tool settings.

Mounted on :class:`bpy.types.Scene` under the attribute ``anim_assist_p3``
so it does not collide with the core ``anim_assist`` group.
All breakdown tool panels and operators read defaults from this PropertyGroup.

Every user-facing property carries a meaningful ``description=`` string
per the UI/UX directive.
"""

from __future__ import annotations

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    StringProperty,
)

from .breakdown_presets import (
    preset_enum_items_callback,
)

__all__ = [
    "P3_SCENE_ATTR",
    "AA_P3_UserPreset",
    "AA_P3_ExclusionPattern",
    "AA_P3_Properties",
    "CLASSES",
    "register_properties",
    "unregister_properties",
    "get_p3",
]

P3_SCENE_ATTR = "anim_assist_p3"


# ---------------------------------------------------------------------------
# Supporting collection items
# ---------------------------------------------------------------------------

class AA_P3_UserPreset(bpy.types.PropertyGroup):
    """User-defined breakdown preset saved to the breakdown PropertyGroup collection.

    Stores slider position and mode so animators can save custom breakdown
    configurations as items in a persistent scene list.
    """
    name: StringProperty(  # type: ignore[valid-type]
        name="Preset Name",
        description="Name shown in the breakdown preset picker.",
        default="Custom Preset",
    )
    factor: FloatProperty(  # type: ignore[valid-type]
        name="Factor",
        description="Breakdown blend factor, where 0 is the previous pose and 1 is the next pose.",
        default=0.5, min=-1.0, max=2.0,
    )
    mode: StringProperty(  # type: ignore[valid-type]
        name="Mode",
        description="Blend mode identifier used by the breakdown engine.",
        default="REPLACE",
    )
    mask_kind: StringProperty(  # type: ignore[valid-type]
        name="Mask",
        description=(
            "Channel mask kind applied when this preset runs "
            "(ALL, LOCATION, ROTATION, SCALE, or TRANSFORM)."
        ),
        default="ALL",
    )


class AA_P3_ExclusionPattern(bpy.types.PropertyGroup):
    """Named data_path pattern for excluding channels from breakdown breakdown.

    The animator might want to exclude certain rig constraints (e.g., "FK_Control")
    or spine channels during a walk cycle breakdown. Each pattern is a substring
    matched against fcurve data_paths.
    """
    pattern: StringProperty(  # type: ignore[valid-type]
        name="Pattern",
        description=(
            "Substring matched against fcurve data_paths to exclude channels "
            "from breakdown breakdown operations."
        ),
        default="",
    )


# ---------------------------------------------------------------------------
# Main breakdown PropertyGroup
# ---------------------------------------------------------------------------

_BREAKDOWN_MODE_ITEMS = (
    ("REPLACE", "Replace",
     "Write a fresh blended value at the target frame, replacing any existing key."),
    ("OFFSET", "Offset",
     "Add a relative offset to the currently evaluated value at the target frame."),
    ("PUSH_PREV", "Push From Previous",
     "Extrapolate past the previous pose for a snappier out-curve."),
    ("PUSH_NEXT", "Push Into Next",
     "Extrapolate past the next pose for a heavier anticipation."),
    ("PULL_PREV", "Pull To Previous",
     "Pull the new key back toward the previous pose, softening the move."),
    ("PULL_NEXT", "Pull To Next",
     "Pull the new key forward toward the next pose, softening the in."),
)

_SPACE_ITEMS = (
    ("LOCAL", "Local",
     "Sample and write values in the channel's own local transform space."),
    ("WORLD", "World",
     "Sample values in world space and convert back to the channel space where practical."),
)


class AA_P3_Properties(bpy.types.PropertyGroup):
    """Scene-scoped defaults for every breakdown breakdown tool."""

    # --- Core blend -------------------------------------------------------
    factor: FloatProperty(  # type: ignore[valid-type]
        name="Factor",
        description=(
            "Breakdown blend factor. 0.0 produces the previous pose, "
            "0.5 a clean midpoint, and 1.0 the next pose. Modal drag and "
            "numeric breakdown seed from this value."
        ),
        default=0.5, min=-1.0, max=2.0, subtype="FACTOR",
    )
    mode: EnumProperty(  # type: ignore[valid-type]
        name="Mode",
        description="Blend mode applied by the breakdown engine.",
        items=_BREAKDOWN_MODE_ITEMS,
        default="REPLACE",
    )
    push_strength: FloatProperty(  # type: ignore[valid-type]
        name="Push Strength",
        description="Multiplier applied when extrapolating past a neighbour pose (Push modes).",
        default=1.25, min=1.0, max=3.0,
    )
    pull_strength: FloatProperty(  # type: ignore[valid-type]
        name="Pull Strength",
        description="Blend factor used by the Pull modes, clamped between 0 and 1.",
        default=0.75, min=0.0, max=1.0,
    )
    offset_amount: FloatProperty(  # type: ignore[valid-type]
        name="Offset Amount",
        description="Relative offset added to the current evaluated value when using Offset mode.",
        default=0.0,
    )

    # --- Masks ------------------------------------------------------------
    mask_location: BoolProperty(  # type: ignore[valid-type]
        name="Location",
        description="When enabled, breakdown operators may write location channels.",
        default=True,
    )
    mask_rotation: BoolProperty(  # type: ignore[valid-type]
        name="Rotation",
        description=(
            "When enabled, breakdown operators may write rotation channels "
            "(Euler and quaternion)."
        ),
        default=True,
    )
    mask_scale: BoolProperty(  # type: ignore[valid-type]
        name="Scale",
        description="When enabled, breakdown operators may write scale channels.",
        default=True,
    )
    mask_custom: BoolProperty(  # type: ignore[valid-type]
        name="Custom",
        description="When enabled, breakdown operators may write custom (non-transform) channels.",
        default=False,
    )
    mask_axis_x: BoolProperty(  # type: ignore[valid-type]
        name="X",
        description=(
            "Allow breakdown writes to array index 0 "
            "(X axis, or W component for quaternions)."
        ),
        default=True,
    )
    mask_axis_y: BoolProperty(  # type: ignore[valid-type]
        name="Y",
        description=(
            "Allow breakdown writes to array index 1 "
            "(Y axis, or X component for quaternions)."
        ),
        default=True,
    )
    mask_axis_z: BoolProperty(  # type: ignore[valid-type]
        name="Z",
        description=(
            "Allow breakdown writes to array index 2 "
            "(Z axis, or Y component for quaternions)."
        ),
        default=True,
    )
    mask_axis_w: BoolProperty(  # type: ignore[valid-type]
        name="W",
        description="Allow breakdown writes to array index 3 (Z component for quaternions).",
        default=True,
    )
    skip_locked: BoolProperty(  # type: ignore[valid-type]
        name="Ignore Locked Axes",
        description=(
            "Skip fcurves whose lock flag is set so locked transforms "
            "stay untouched."
        ),
        default=True,
    )
    respect_exclusions: BoolProperty(  # type: ignore[valid-type]
        name="Respect Exclusion Set",
        description=(
            "When enabled, fcurves matching the active exclusion set are "
            "ignored by all breakdown operators."
        ),
        default=True,
    )

    # --- Interpolation options -------------------------------------------
    quaternion_aware: BoolProperty(  # type: ignore[valid-type]
        name="Quaternion-Aware",
        description=(
            "Blend quaternion rotation channels with a true slerp across "
            "all four components so the resulting rotation never flips "
            "mid-arc."
        ),
        default=True,
    )
    euler_wrap_aware: BoolProperty(  # type: ignore[valid-type]
        name="Euler Continuity",
        description="Pick the shortest arc when blending Euler rotations that cross a ±π boundary.",
        default=True,
    )
    visual_transform: BoolProperty(  # type: ignore[valid-type]
        name="Visual Transform",
        description=(
            "Sample the final evaluated curve value (respecting modifiers) "
            "instead of a pure neighbour blend. Useful for constrained rigs."
        ),
        default=False,
    )
    preserve_world_contact: BoolProperty(  # type: ignore[valid-type]
        name="Preserve World Contact",
        description=(
            "Best-effort attempt to keep world-space contact channels "
            "(feet, hands) stable during the breakdown. Depends on rig setup."
        ),
        default=False,
    )
    preserve_child_contact: BoolProperty(  # type: ignore[valid-type]
        name="Preserve Child Contact",
        description=(
            "Best-effort attempt to keep child-object contacts stable "
            "during the breakdown."
        ),
        default=False,
    )
    match_tangents: BoolProperty(  # type: ignore[valid-type]
        name="Match Tangents",
        description=(
            "Copy handle types from the closer neighbour key so the new "
            "breakdown flows cleanly."
        ),
        default=True,
    )
    auto_key_missing: BoolProperty(  # type: ignore[valid-type]
        name="Auto-Key Missing Channels",
        description=(
            "When a channel has no neighbouring keys, insert a key with "
            "its currently evaluated value so the breakdown still has "
            "something to blend next time."
        ),
        default=False,
    )
    space: EnumProperty(  # type: ignore[valid-type]
        name="Space",
        description="Transform space used for visual-transform sampling.",
        items=_SPACE_ITEMS,
        default="LOCAL",
    )

    # --- Inbetween --------------------------------------------------------
    inbetween_count: IntProperty(  # type: ignore[valid-type]
        name="Inbetween Count",
        description="Number of inbetween keys to distribute inside the current selection gap.",
        default=1, min=1, max=32,
    )

    # --- Batch ------------------------------------------------------------
    batch_use_selection: BoolProperty(  # type: ignore[valid-type]
        name="Use Selected Keys",
        description=(
            "When batching, run the breakdown at every selected keyframe "
            "instead of a single target frame."
        ),
        default=True,
    )

    # --- Preset / exclusion collections ----------------------------------
    active_preset: EnumProperty(  # type: ignore[valid-type]
        name="Active Preset",
        description="Built-in breakdown preset selected for the Apply Preset operator.",
        # Use the callable form so Blender retains a reference to the
        # module-level PRESET_ENUM_ITEMS tuple rather than a temporary
        # value captured at class-body time. Avoids the classic Blender
        # EnumProperty "random unicode" garbage-collection bug.
        items=preset_enum_items_callback,
    )
    user_presets: CollectionProperty(type=AA_P3_UserPreset)  # type: ignore[valid-type]
    user_preset_index: IntProperty(  # type: ignore[valid-type]
        name="User Preset Index",
        description="Active row in the user preset list.",
        default=0,
    )
    exclusion_patterns: CollectionProperty(type=AA_P3_ExclusionPattern)  # type: ignore[valid-type]
    exclusion_index: IntProperty(  # type: ignore[valid-type]
        name="Exclusion Index",
        description="Active row in the exclusion-pattern list.",
        default=0,
    )

    # --- Modal ------------------------------------------------------------
    modal_sensitivity: IntProperty(  # type: ignore[valid-type]
        name="Modal Sensitivity",
        description=(
            "Horizontal pixels required to cover the full 0 → 1 factor range "
            "during modal drag breakdown."
        ),
        default=220, min=40, max=2000,
    )
    preview_active: BoolProperty(  # type: ignore[valid-type]
        name="Preview Active",
        description="Internal flag set while a preview-before-commit breakdown is pending.",
        default=False,
    )
    preview_frame: FloatProperty(  # type: ignore[valid-type]
        name="Preview Frame",
        description="Frame at which the current preview breakdown was staged.",
        default=0.0,
    )


CLASSES: tuple[type, ...] = (
    AA_P3_UserPreset,
    AA_P3_ExclusionPattern,
    AA_P3_Properties,
)


def register_properties() -> None:
    """Attach breakdown PropertyGroup to Scene so settings persist when the .blend is saved."""
    bpy.types.Scene.anim_assist_p3 = bpy.props.PointerProperty(  # type: ignore[attr-defined]
        type=AA_P3_Properties,
        name="Anim Assist breakdown",
        description="Scene-scoped defaults for the Anim Assist breakdown breakdown tools.",
    )


def unregister_properties() -> None:
    """Detach breakdown PropertyGroup from Scene on addon unregister."""
    if hasattr(bpy.types.Scene, "anim_assist_p3"):
        try:
            del bpy.types.Scene.anim_assist_p3  # type: ignore[attr-defined]
        except Exception:  # pragma: no cover
            pass


def get_p3(context: bpy.types.Context) -> AA_P3_Properties | None:
    """Get the breakdown properties from context, or None if unavailable."""
    scene = getattr(context, "scene", None)
    if scene is None:
        return None
    return getattr(scene, P3_SCENE_ATTR, None)
