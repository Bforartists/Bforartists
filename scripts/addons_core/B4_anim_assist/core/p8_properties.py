# --- MATCHING AND SPACE SWITCHING ---
"""Scene-scoped PropertyGroup for matching workflows and space switching.

Mounted on ``Scene.anim_assist_p8`` so it does not collide with other modules.
Every enum uses the callable-items pattern for Blender string-retention GC safety.

Covers all matching and switching features: transform matching, space switching,
switch compensation, switch baking, rig pattern detection, switch
history, contact preservation, and switch presets.
"""

from __future__ import annotations

import bpy
from bpy.props import (
    BoolProperty,
    BoolVectorProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    StringProperty,
)

__all__ = [
    "AA_P8_Properties",
    "get_p8",
    "register_properties",
    "unregister_properties",
    "MATCH_SPACE_ITEMS",
    "MATCH_CHANNELS_ITEMS",
    "COMP_RANGE_ITEMS",
    "SWITCH_KIND_ITEMS",
    "P8_SCENE_ATTR",
    "CLASSES",
]

P8_SCENE_ATTR = "anim_assist_p8"


# ---------------------------------------------------------------------------
# Enum item tables (module-level for GC safety)
# ---------------------------------------------------------------------------

MATCH_SPACE_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("WORLD", "World",
     "Match the control to world-space identity or a world-space reference."),
    ("PARENT", "Parent",
     "Match the control to its parent's transform."),
    ("TARGET", "Target",
     "Match the control to another selected object or bone."),
    ("VISUAL", "Visual Matrix",
     "Match using the fully evaluated visual (depsgraph) matrix."),
    ("LOCAL", "Local Matrix",
     "Match using the unevaluated local matrix of the source."),
)

MATCH_CHANNELS_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("ALL", "All (TRS)",
     "Match location, rotation, and scale."),
    ("LOCATION", "Location",
     "Match location channels only."),
    ("ROTATION", "Rotation",
     "Match rotation channels only."),
    ("SCALE", "Scale",
     "Match scale channels only."),
    ("LOC_ROT", "Loc + Rot",
     "Match location and rotation, skip scale."),
)

COMP_RANGE_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("SINGLE", "Current Frame",
     "Compensate only the current frame."),
    ("SELECTION", "Selected Keys",
     "Compensate across selected keyframes."),
    ("CUSTOM", "Custom Range",
     "Compensate within a manually specified frame range."),
    ("PREVIEW", "Preview Range",
     "Compensate across the scene preview/playback range."),
)

SWITCH_KIND_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("ENUM", "Enum / Integer",
     "Switch an integer or enum custom property."),
    ("BOOL", "Boolean",
     "Toggle a boolean (0/1) custom property."),
    ("INFLUENCE", "Constraint Influence",
     "Blend a constraint's influence between 0 and 1."),
    ("CUSTOM", "Custom Property",
     "Switch a generic numeric custom property."),
)


def _match_space_items(self, context):  # noqa: ARG001
    return MATCH_SPACE_ITEMS


def _match_channels_items(self, context):  # noqa: ARG001
    return MATCH_CHANNELS_ITEMS


def _comp_range_items(self, context):  # noqa: ARG001
    return COMP_RANGE_ITEMS


def _switch_kind_items(self, context):  # noqa: ARG001
    return SWITCH_KIND_ITEMS


# ---------------------------------------------------------------------------
# PropertyGroup
# ---------------------------------------------------------------------------

class AA_P8_Properties(bpy.types.PropertyGroup):
    """Scene-scoped defaults for matching and space switching matching and space-switch tools."""

    # ----- Match Settings (Features 1-12, 29-30) -----

    match_space: EnumProperty(  # type: ignore[valid-type]
        name="Match Space",
        description="Reference space for matching: world, parent, target, visual, or local",
        items=_match_space_items,
        default=0,
    )

    match_channels: EnumProperty(  # type: ignore[valid-type]
        name="Match Channels",
        description="Which transform channels to include in the match operation",
        items=_match_channels_items,
        default=0,
    )

    match_axis: BoolVectorProperty(  # type: ignore[valid-type]
        name="Axis Filter",
        description="Per-axis toggle for the match operation (X, Y, Z)",
        size=3,
        default=(True, True, True),
        subtype="XYZ",
    )

    maintain_offset: BoolProperty(  # type: ignore[valid-type]
        name="Maintain Offset",
        description=(
            "Preserve the existing spatial offset between source and target "
            "rather than snapping exactly to the source position"
        ),
        default=False,
    )

    # ----- Compensation / Switch (Features 13-16, 21-28) -----

    comp_range: EnumProperty(  # type: ignore[valid-type]
        name="Compensation Range",
        description="Frame range over which to apply space-switch compensation",
        items=_comp_range_items,
        default=0,
    )

    comp_range_start: FloatProperty(  # type: ignore[valid-type]
        name="Start",
        description="Custom compensation range start frame",
        default=1.0,
        precision=1,
    )

    comp_range_end: FloatProperty(  # type: ignore[valid-type]
        name="End",
        description="Custom compensation range end frame",
        default=250.0,
        precision=1,
    )

    switch_kind: EnumProperty(  # type: ignore[valid-type]
        name="Switch Type",
        description="What kind of property is being switched (enum, boolean, influence, custom)",
        items=_switch_kind_items,
        default=0,
    )

    switch_prop_path: StringProperty(  # type: ignore[valid-type]
        name="Property Path",
        description=(
            "RNA or custom-property data path of the switch control "
            '(e.g. \'["space_switch"]\' or \'constraints["Child Of"].influence\')'
        ),
        default="",
    )

    switch_bone_name: StringProperty(  # type: ignore[valid-type]
        name="Switch Bone",
        description="Name of the pose bone owning the switch property (empty for object-level)",
        default="",
    )

    switch_new_value: FloatProperty(  # type: ignore[valid-type]
        name="New Value",
        description="The value to set the switch property to",
        default=0.0,
        precision=2,
    )

    auto_compensate: BoolProperty(  # type: ignore[valid-type]
        name="Auto Compensate",
        description=(
            "Automatically compensate the visual transform when a space-switch "
            "property is changed so the control does not visually jump"
        ),
        default=True,
    )

    auto_key_switch: BoolProperty(  # type: ignore[valid-type]
        name="Auto-Key Switch",
        description=(
            "Automatically insert keyframes on compensated transform channels "
            "after a space-switch operation"
        ),
        default=True,
    )

    switch_preview: BoolProperty(  # type: ignore[valid-type]
        name="Switch Preview",
        description=(
            "Enable preview mode: show the compensation result before "
            "committing. Cancel to revert."
        ),
        default=False,
    )

    # ----- Safety Flags (Features 27-28) -----

    respect_locks: BoolProperty(  # type: ignore[valid-type]
        name="Respect Locked Transforms",
        description="Skip transform channels that are locked on the target object or bone",
        default=True,
    )

    respect_drivers: BoolProperty(  # type: ignore[valid-type]
        name="Respect Driven Channels",
        description=(
            "Skip transform channels that are controlled by drivers or "
            "constraints, where overriding them would be unsafe"
        ),
        default=True,
    )

    # ----- Contact Preservation (Features 40-41) -----

    contact_preserve: BoolProperty(  # type: ignore[valid-type]
        name="Contact Preservation",
        description=(
            "During multi-frame compensation, try to keep contact points "
            "(hands, feet) planted by blending compensation near contact frames"
        ),
        default=False,
    )

    contact_mask: StringProperty(  # type: ignore[valid-type]
        name="Contact Mask",
        description=(
            "Comma-separated list of bone names to treat as contact points "
            '(e.g. "foot_ik_L, foot_ik_R, hand_ik_L, hand_ik_R")'
        ),
        default="",
    )

    # ----- IK Chain Resolver (Features 46-56) -----

    show_chain_resolver: BoolProperty(  # type: ignore[valid-type]
        name="Show Chain Resolver",
        description="Expand the IK Chain Resolver section in the panel",
        default=False,
    )

    chain_include_muted: BoolProperty(  # type: ignore[valid-type]
        name="Include Muted",
        description=(
            "Include IK constraints that are currently muted in chain detection "
            "results (useful for inspecting disabled setups)"
        ),
        default=False,
    )

    chain_highlight_members: BoolProperty(  # type: ignore[valid-type]
        name="Highlight Chain Members",
        description=(
            "Highlight all bones belonging to the selected IK chain in the "
            "viewport for visual feedback"
        ),
        default=True,
    )

    chain_auto_detect: BoolProperty(  # type: ignore[valid-type]
        name="Auto-Detect on Selection",
        description=(
            "Automatically detect IK chains when the active bone changes, "
            "keeping the chain info panel up to date"
        ),
        default=True,
    )

    chain_selected_index: IntProperty(  # type: ignore[valid-type]
        name="Selected Chain",
        description="Index of the currently inspected IK chain in the results list",
        default=0,
        min=0,
    )

    chain_last_armature: StringProperty(  # type: ignore[valid-type]
        name="Last Armature",
        description="Name of the armature used in the most recent chain detection",
        default="",
    )

    chain_last_count: IntProperty(  # type: ignore[valid-type]
        name="Detected Count",
        description="Number of IK chains found in the most recent detection run",
        default=0,
        min=0,
    )

    # ----- Detection / Presets (Features 17-20, 34) -----

    detected_pattern_index: IntProperty(  # type: ignore[valid-type]
        name="Detected Pattern",
        description="Index of the currently selected detected switch pattern",
        default=0,
        min=0,
    )

    switch_preset_name: StringProperty(  # type: ignore[valid-type]
        name="Preset Name",
        description="Name for saving or loading a switch preset configuration",
        default="",
    )


# ---------------------------------------------------------------------------
# Registration helpers
# ---------------------------------------------------------------------------

CLASSES: tuple[type, ...] = (AA_P8_Properties,)


def get_p8(context: bpy.types.Context) -> AA_P8_Properties | None:
    """Return the matching and space switching PropertyGroup from the current scene, or None."""
    scene = getattr(context, "scene", None)
    if scene is None:
        return None
    return getattr(scene, P8_SCENE_ATTR, None)


def register_properties() -> None:
    """Register matching and space switching properties on Scene.

    Attaches match channel settings, space-switch defaults, and preview
    state to the scene so they persist across file saves and are accessible
    to all matching and space switching matching and space-switch operators.
    """
    bpy.types.Scene.anim_assist_p8 = bpy.props.PointerProperty(  # type: ignore[assignment]
        type=AA_P8_Properties,
        name="Anim Assist P8",
    )


def unregister_properties() -> None:
    """Unregister matching and space switching properties from Scene.

    Safe to call even if properties were never registered.
    """
    try:
        del bpy.types.Scene.anim_assist_p8
    except AttributeError:
        pass
