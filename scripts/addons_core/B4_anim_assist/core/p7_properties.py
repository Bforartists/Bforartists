# --- TEMPORARY CONTROLS AND PROXY WORKFLOWS ---
"""Scene-scoped PropertyGroup for temporary controls and proxy constraints.

Mounted on ``Scene.anim_assist_p7`` so it does not collide with other modules.
Every enum uses the callable-items pattern for Blender string-retention GC safety.

Covers all temporary control features: temp locators, proxy helpers, bake workflows,
session tracking, display, and cleanup.
"""

from __future__ import annotations

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
    IntProperty,
    StringProperty,
)

__all__ = [
    "AA_P7_Properties",
    "get_p7",
    "register_properties",
    "unregister_properties",
    "PROXY_TYPE_ITEMS",
    "BAKE_RANGE_MODE_ITEMS",
    "BAKE_CHANNELS_ITEMS",
    "DISPLAY_MODE_ITEMS",
    "PROXY_MODE_ITEMS",
    "P7_SCENE_ATTR",
    "CLASSES",
]

P7_SCENE_ATTR = "anim_assist_p7"


# ---------------------------------------------------------------------------
# Enum item tables (module-level for GC safety)
# ---------------------------------------------------------------------------

PROXY_TYPE_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("ORIENTATION", "Orientation",
     "Temporary rotation proxy — mirrors target orientation via Copy Rotation."),
    ("TRANSLATION", "Translation",
     "Temporary translation proxy — mirrors target position via Copy Location."),
    ("AIM", "Aim",
     "Temporary aim proxy — drives target aim via Track To constraint."),
    ("POLE", "Pole",
     "Temporary pole helper — IK pole target reference with no auto-constraint."),
    ("UP_VECTOR", "Up-Vector",
     "Temporary up-vector helper — reference for aim/track-to up axis."),
    ("MULTI_TARGET", "Multi-Target Avg",
     "Average-position proxy driven by multiple targets."),
    ("PARENT_SPACE", "Parent-Space",
     "Parent-space proxy — temporary re-parenting via Child Of constraint."),
    ("WORLD_SPACE", "World-Space",
     "World-space proxy — mirrors full transform via Copy Transforms."),
    ("CAMERA_SPACE", "Camera-Space",
     "Camera-space proxy — constraint influence keyed for camera-relative motion."),
)

BAKE_RANGE_MODE_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("SCENE", "Scene Range",
     "Bake across the full scene playback range."),
    ("ACTION", "Action Range",
     "Bake across the frame range of the active action."),
    ("CUSTOM", "Custom Range",
     "Bake between manually specified start and end frames."),
    ("SELECTION", "Selection",
     "Derive bake range from selected keyframes."),
    ("PREVIEW", "Preview Range",
     "Bake across the scene's preview/playback range markers."),
)

BAKE_CHANNELS_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("ALL", "All Channels",
     "Bake location, rotation, and scale."),
    ("LOC", "Location Only",
     "Bake only location channels."),
    ("ROT", "Rotation Only",
     "Bake only rotation channels."),
    ("LOCROT", "Loc + Rot",
     "Bake location and rotation, skip scale."),
    ("SELECTED", "Selected Only",
     "Bake only channels that are currently selected in the channel list."),
)

DISPLAY_MODE_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("FULL", "Full Display",
     "Show proxies at normal size with full wireframe colour."),
    ("DIM", "Dimmed",
     "Reduce proxy size and mute colour for less viewport clutter."),
    ("HIDDEN", "Hidden",
     "Hide proxy empties from the viewport entirely."),
)

PROXY_MODE_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("CONSTRAIN", "Constrain",
     "Proxy drives the target via constraint."),
    ("OFFSET", "Offset",
     "Proxy provides an additive offset layered on top of existing animation."),
)


def _proxy_type_items(self, context):  # noqa: ARG001
    return PROXY_TYPE_ITEMS


def _bake_range_items(self, context):  # noqa: ARG001
    return BAKE_RANGE_MODE_ITEMS


def _bake_channels_items(self, context):  # noqa: ARG001
    return BAKE_CHANNELS_ITEMS


def _display_mode_items(self, context):  # noqa: ARG001
    return DISPLAY_MODE_ITEMS


def _proxy_mode_items(self, context):  # noqa: ARG001
    return PROXY_MODE_ITEMS


# ---------------------------------------------------------------------------
# PropertyGroup
# ---------------------------------------------------------------------------

class AA_P7_Properties(bpy.types.PropertyGroup):
    """Scene-scoped defaults for proxy proxy, bake, and session tools."""

    # ----- Proxy Creation (Features 11-19) -----

    proxy_type: EnumProperty(  # type: ignore[valid-type]
        name="Proxy Type",
        description=(
            "Type of temporary proxy helper to create "
            "(orientation, translation, aim, pole, etc.)"
        ),
        items=_proxy_type_items,
        default=0,
    )

    proxy_size: FloatProperty(  # type: ignore[valid-type]
        name="Proxy Size",
        description="Display size of newly created proxy empties in viewport units",
        default=0.5,
        min=0.01,
        max=10.0,
        soft_min=0.1,
        soft_max=2.0,
        step=10,
        precision=2,
    )

    proxy_color: FloatVectorProperty(  # type: ignore[valid-type]
        name="Proxy Color",
        description="Wireframe colour assigned to new proxy objects for visual identification",
        subtype="COLOR",
        size=3,
        default=(0.2, 0.8, 1.0),
        min=0.0,
        max=1.0,
    )

    auto_constrain: BoolProperty(  # type: ignore[valid-type]
        name="Auto-Constrain",
        description=(
            "Automatically add the appropriate constraint between proxy "
            "and target on creation. Disable for manual constraint setup."
        ),
        default=True,
    )

    # ----- Proxy Mode (Feature 30, 36) -----

    proxy_mode: EnumProperty(  # type: ignore[valid-type]
        name="Proxy Mode",
        description="How the proxy drives the target: Constrain replaces, Offset adds on top",
        items=_proxy_mode_items,
        default=0,
    )

    # ----- Locator Tools (Features 1-10) -----

    locator_snap_to_bone: BoolProperty(  # type: ignore[valid-type]
        name="Snap to Bone",
        description=(
            "When creating a locator from a bone, snap the empty to the "
            "bone's head position"
        ),
        default=True,
    )

    # ----- Bake Settings (Features 31-35) -----

    bake_range_mode: EnumProperty(  # type: ignore[valid-type]
        name="Bake Range",
        description="How to determine the frame range for baking operations",
        items=_bake_range_items,
        default=0,
    )

    bake_range_start: FloatProperty(  # type: ignore[valid-type]
        name="Start",
        description="Custom bake range start frame",
        default=1.0,
        precision=1,
    )

    bake_range_end: FloatProperty(  # type: ignore[valid-type]
        name="End",
        description="Custom bake range end frame",
        default=250.0,
        precision=1,
    )

    bake_step: IntProperty(  # type: ignore[valid-type]
        name="Frame Step",
        description="Bake every Nth frame. 1 = every frame, 2 = every other frame",
        default=1,
        min=1,
        max=24,
    )

    bake_channels: EnumProperty(  # type: ignore[valid-type]
        name="Channels",
        description=(
            "Which transform channels to bake: all, location-only, "
            "rotation-only, or selected"
        ),
        items=_bake_channels_items,
        default=0,
    )

    smart_bake_tolerance: FloatProperty(  # type: ignore[valid-type]
        name="Key Reduction Tolerance",
        description=(
            "Maximum deviation allowed when removing redundant keys. "
            "Lower = more keys retained, higher = fewer keys."
        ),
        default=0.01,
        min=0.0001,
        max=1.0,
        precision=4,
    )

    preserve_timing: BoolProperty(  # type: ignore[valid-type]
        name="Preserve Existing Timing",
        description=(
            "When baking, preserve existing keyframe positions and only update "
            "values at those frames instead of inserting a key on every frame"
        ),
        default=False,
    )

    # ----- Display (Features 20-23) -----

    display_mode: EnumProperty(  # type: ignore[valid-type]
        name="Display Mode",
        description="How proxy objects are displayed in the viewport: full, dimmed, or hidden",
        items=_display_mode_items,
        default=0,
    )

    show_proxy_names: BoolProperty(  # type: ignore[valid-type]
        name="Show Names",
        description="Display proxy object names in the viewport for quick identification",
        default=True,
    )

    # ----- Session (Features 26-27) -----

    active_session_id: StringProperty(  # type: ignore[valid-type]
        name="Active Session",
        description="UUID of the currently active P7 session",
        default="",
        options={"HIDDEN"},
    )

    # ----- Lock (Feature 29) -----

    lock_original_target: BoolProperty(  # type: ignore[valid-type]
        name="Lock Original Target",
        description=(
            "Freeze the original target's transform channels while "
            "a proxy is actively driving it, preventing accidental edits"
        ),
        default=False,
    )


# ---------------------------------------------------------------------------
# Registration helpers
# ---------------------------------------------------------------------------

CLASSES: tuple[type, ...] = (AA_P7_Properties,)


def get_p7(context: bpy.types.Context) -> AA_P7_Properties | None:
    """Return the proxy PropertyGroup from the current scene, or None."""
    scene = getattr(context, "scene", None)
    if scene is None:
        return None
    return getattr(scene, P7_SCENE_ATTR, None)


def register_properties() -> None:
    """Register proxy properties on Scene.

    Attaches proxy settings, bake configuration, and session tracking
    to the scene so they persist across file saves and are accessible
    to all proxy operators.
    """
    bpy.types.Scene.anim_assist_p7 = bpy.props.PointerProperty(  # type: ignore[assignment]
        type=AA_P7_Properties,
        name="Anim Assist P7",
    )


def unregister_properties() -> None:
    """Unregister proxy properties from Scene.

    Safe to call even if properties were never registered.
    """
    try:
        del bpy.types.Scene.anim_assist_p7
    except AttributeError:
        pass
