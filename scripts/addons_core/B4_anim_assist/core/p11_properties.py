# --- ANIMATION LAYERS ---
"""Scene-scoped PropertyGroup for animation layer management and workflows.

Mounted on ``Scene.anim_assist_p11`` so it does not collide with other modules.
Every enum uses the callable-items pattern for Blender string-retention GC safety.

Covers all animation layer features: animation layer stack, per-layer bone/part
assignment, blend modes, weight/influence sliders, solo/mute/lock states,
layer presets, and merge/flatten workflows.

Design inspirations:
    Maya Animation Layers  — override/additive blend modes, per-layer weight
    Blender NLA            — strip stacking, influence slider, blend types
    Cascadeur              — layered editing with part isolation
"""

from __future__ import annotations

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)

from .logging import get_logger

__all__ = [
    "P11_SCENE_ATTR",
    "AA_P11_BoneAssignment",
    "AA_P11_ChannelOverride",
    "AA_P11_AnimLayer",
    "AA_P11_LayerPreset",
    "AA_P11_Properties",
    "CLASSES",
    "get_p11",
    "register_properties",
    "unregister_properties",
]

P11_SCENE_ATTR = "anim_assist_p11"

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Enum item tables (module-level for GC safety)
# ---------------------------------------------------------------------------

BLEND_MODE_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("OVERRIDE", "Override",
     "Layer fully replaces channels below it (scaled by weight). "
     "Equivalent to Maya Override mode"),
    ("ADDITIVE", "Additive",
     "Layer values are added on top of the layer below. "
     "Ideal for secondary motion, breathing, overlap. "
     "Equivalent to Maya Additive mode"),
    ("MULTIPLY", "Multiply",
     "Layer values are multiplied with the layer below. "
     "Useful for scaling existing animation intensities"),
    ("COMBINE", "Combine",
     "Channels are combined using Blender NLA-style mixing. "
     "Location adds, rotation concatenates, scale multiplies"),
)

LAYER_SCOPE_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("ALL", "All Channels",
     "Layer affects all channels on assigned bones"),
    ("LOCATION", "Location Only",
     "Layer only affects location channels"),
    ("ROTATION", "Rotation Only",
     "Layer only affects rotation channels"),
    ("SCALE", "Scale Only",
     "Layer only affects scale channels"),
    ("CUSTOM", "Custom",
     "Layer uses a custom fcurve path filter"),
)

LAYER_COLOR_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("DEFAULT", "Default", "Use theme default color"),
    ("RED", "Red", "Red layer accent"),
    ("ORANGE", "Orange", "Orange layer accent"),
    ("YELLOW", "Yellow", "Yellow layer accent"),
    ("GREEN", "Green", "Green layer accent"),
    ("BLUE", "Blue", "Blue layer accent"),
    ("PURPLE", "Purple", "Purple layer accent"),
    ("CYAN", "Cyan", "Cyan layer accent"),
)

PRESET_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("UPPER_LOWER", "Upper / Lower Body",
     "Split at the spine: upper body on one layer, lower on another"),
    ("FACE_BODY", "Face / Body",
     "Facial bones on one layer, body on another"),
    ("LEFT_RIGHT", "Left / Right",
     "Left side bones on one layer, right side on another"),
    ("FINGERS_HANDS", "Fingers / Hands / Arms",
     "Separate layers for fingers, hands, and arms"),
    ("CUSTOM", "Custom",
     "User-defined layer partition"),
)


def _blend_mode_items(self, context):  # noqa: ARG001
    return BLEND_MODE_ITEMS


def _layer_scope_items(self, context):  # noqa: ARG001
    return LAYER_SCOPE_ITEMS


def _layer_color_items(self, context):  # noqa: ARG001
    return LAYER_COLOR_ITEMS


def _preset_items(self, context):  # noqa: ARG001
    return PRESET_ITEMS


# ---------------------------------------------------------------------------
# Sub-PropertyGroups for collections
# ---------------------------------------------------------------------------

class AA_P11_BoneAssignment(bpy.types.PropertyGroup):
    """A single bone assigned to a layer."""

    bone_name: StringProperty(  # type: ignore[valid-type]
        name="Bone",
        description="Name of the bone assigned to this layer",
        default="",
    )


class AA_P11_ChannelOverride(bpy.types.PropertyGroup):
    """Per-channel weight override within a layer.

    Allows fine-grained control: e.g. location at 80%, rotation at 50%
    on the same layer for the same bone.
    """

    bone_name: StringProperty(  # type: ignore[valid-type]
        name="Bone",
        description="Bone this override applies to",
        default="",
    )

    location_weight: FloatProperty(  # type: ignore[valid-type]
        name="Location Weight",
        description="Override weight for location channels on this bone",
        default=1.0, min=0.0, max=1.0,
        subtype="FACTOR",
    )

    rotation_weight: FloatProperty(  # type: ignore[valid-type]
        name="Rotation Weight",
        description="Override weight for rotation channels on this bone",
        default=1.0, min=0.0, max=1.0,
        subtype="FACTOR",
    )

    scale_weight: FloatProperty(  # type: ignore[valid-type]
        name="Scale Weight",
        description="Override weight for scale channels on this bone",
        default=1.0, min=0.0, max=1.0,
        subtype="FACTOR",
    )


class AA_P11_AnimLayer(bpy.types.PropertyGroup):
    """A single animation layer in the stack.

    Each layer has its own weight, blend mode, solo/mute/lock state,
    and a collection of assigned bones. When ``assigned_bones`` is empty
    the layer affects ALL bones (whole-body layer).
    """

    # ---- Identity ----

    name: StringProperty(  # type: ignore[valid-type]
        name="Layer Name",
        description="Display name for this animation layer",
        default="Layer",
    )

    layer_color: EnumProperty(  # type: ignore[valid-type]
        name="Color",
        description="Visual accent color for this layer in the UI",
        items=_layer_color_items,
        default=0,
    )

    # ---- Blending ----

    weight: FloatProperty(  # type: ignore[valid-type]
        name="Weight",
        description=(
            "Influence of this layer on the final result (0%% = no effect, "
            "100%% = full contribution). Drag to blend between layers"
        ),
        default=1.0, min=0.0, max=1.0,
        subtype="FACTOR",
    )

    blend_mode: EnumProperty(  # type: ignore[valid-type]
        name="Blend Mode",
        description=(
            "How this layer combines with layers below it in the stack"
        ),
        items=_blend_mode_items,
        default=0,
    )

    # ---- State flags ----

    mute: BoolProperty(  # type: ignore[valid-type]
        name="Mute",
        description="Disable this layer without removing it",
        default=False,
    )

    solo: BoolProperty(  # type: ignore[valid-type]
        name="Solo",
        description=(
            "Only evaluate this layer (and the base layer). "
            "Other layers are temporarily muted"
        ),
        default=False,
    )

    locked: BoolProperty(  # type: ignore[valid-type]
        name="Lock",
        description="Prevent editing on this layer (read-only)",
        default=False,
    )

    protected: BoolProperty(  # type: ignore[valid-type]
        name="Protected",
        description="Prevent accidental deletion of this layer",
        default=False,
    )

    auto_key: BoolProperty(  # type: ignore[valid-type]
        name="Auto Key",
        description=(
            "Automatically insert keyframes on this layer's Action "
            "when you move, rotate, or scale assigned bones. "
            "Works independently of Blender's global auto-keying"
        ),
        default=False,
    )

    # ---- Scope ----

    layer_scope: EnumProperty(  # type: ignore[valid-type]
        name="Scope",
        description="Which transform channels this layer affects",
        items=_layer_scope_items,
        default=0,
    )

    custom_filter: StringProperty(  # type: ignore[valid-type]
        name="Custom Filter",
        description=(
            "Comma-separated fcurve data_path substrings to include "
            "(e.g. 'location,rotation_euler'). Used when scope is Custom"
        ),
        default="",
    )

    # ---- Part assignment ----

    assigned_bones: CollectionProperty(  # type: ignore[valid-type]
        type=AA_P11_BoneAssignment,
        name="Assigned Bones",
        description=(
            "Bones that this layer is allowed to edit. "
            "Empty means ALL bones (whole-body layer)"
        ),
    )

    assigned_bones_index: IntProperty(  # type: ignore[valid-type]
        name="Active Bone",
        default=0,
        min=0,
    )

    # ---- Per-channel weight overrides ----

    channel_overrides: CollectionProperty(  # type: ignore[valid-type]
        type=AA_P11_ChannelOverride,
        name="Channel Overrides",
        description=(
            "Per-bone channel weight overrides. "
            "Allows different blend percentages for loc/rot/scale "
            "on individual bones within this layer"
        ),
    )

    channel_overrides_index: IntProperty(  # type: ignore[valid-type]
        name="Active Override",
        default=0,
        min=0,
    )

    # ---- Metadata ----

    is_base_layer: BoolProperty(  # type: ignore[valid-type]
        name="Base Layer",
        description=(
            "Whether this is the base (bottom) layer. "
            "The base layer always uses Override mode at 100%% weight"
        ),
        default=False,
    )

    action_name: StringProperty(  # type: ignore[valid-type]
        name="Action",
        description=(
            "Name of the Blender Action backing this layer's keyframes. "
            "Each layer stores its animation in a separate Action"
        ),
        default="",
    )


class AA_P11_LayerPreset(bpy.types.PropertyGroup):
    """User-saved layer stack configuration preset."""

    name: StringProperty(  # type: ignore[valid-type]
        name="Preset Name",
        description="Display name for this layer preset",
        default="Preset",
    )

    preset_json: StringProperty(  # type: ignore[valid-type]
        name="Preset Data",
        description="JSON-encoded layer stack configuration",
        default="",
    )


# ---------------------------------------------------------------------------
# Main PropertyGroup
# ---------------------------------------------------------------------------

class AA_P11_Properties(bpy.types.PropertyGroup):
    """Scene-scoped defaults for animation layer animation layer tools."""

    # ---- Layer stack ----

    layers: CollectionProperty(  # type: ignore[valid-type]
        type=AA_P11_AnimLayer,
        name="Animation Layers",
        description="Stack of animation layers, evaluated bottom to top",
    )

    active_layer_index: IntProperty(  # type: ignore[valid-type]
        name="Active Layer",
        description="Index of the currently active layer for editing",
        default=0,
        min=0,
    )

    # ---- Global toggles ----

    layers_enabled: BoolProperty(  # type: ignore[valid-type]
        name="Enable Layers",
        description=(
            "Master toggle for the animation layer system. "
            "When disabled, only the base action is used"
        ),
        default=True,
    )

    edit_active_only: BoolProperty(  # type: ignore[valid-type]
        name="Edit Active Only",
        description=(
            "When enabled, keyframe insertion and editing only affect "
            "bones assigned to the active layer. "
            "Inspired by Maya's 'Selected Layer' editing mode"
        ),
        default=True,
    )

    auto_assign_on_key: BoolProperty(  # type: ignore[valid-type]
        name="Auto-Assign on Key",
        description=(
            "Automatically assign a bone to the active layer when "
            "a keyframe is inserted on it (if not already assigned)"
        ),
        default=False,
    )

    show_layer_colors: BoolProperty(  # type: ignore[valid-type]
        name="Show Layer Colors",
        description="Color-code bones in the viewport by their layer assignment",
        default=True,
    )

    show_unassigned_warning: BoolProperty(  # type: ignore[valid-type]
        name="Warn Unassigned",
        description=(
            "Show a warning when attempting to key a bone that is not "
            "assigned to any layer"
        ),
        default=True,
    )

    # ---- Interactive blend ----

    blend_source_index: IntProperty(  # type: ignore[valid-type]
        name="Blend Source",
        description="Index of the source layer for interactive blend",
        default=0,
        min=0,
    )

    blend_target_index: IntProperty(  # type: ignore[valid-type]
        name="Blend Target",
        description="Index of the target layer for interactive blend",
        default=1,
        min=0,
    )

    blend_factor: FloatProperty(  # type: ignore[valid-type]
        name="Blend Factor",
        description=(
            "Interpolation factor between source and target layers "
            "(0.0 = fully source, 1.0 = fully target)"
        ),
        default=0.5, min=0.0, max=1.0,
        subtype="FACTOR",
    )

    # ---- Presets ----

    user_presets: CollectionProperty(  # type: ignore[valid-type]
        type=AA_P11_LayerPreset,
        name="Layer Presets",
        description="Saved layer stack configurations",
    )

    user_presets_index: IntProperty(  # type: ignore[valid-type]
        name="Active Preset",
        description="Index of the selected animation-layer preset",
        default=0,
        min=0,
    )

    # ---- Evaluation cache generation ----

    eval_generation: IntProperty(  # type: ignore[valid-type]
        name="Eval Generation",
        description="Incremented when layer stack changes to invalidate caches",
        default=0,
    )


# ---------------------------------------------------------------------------
# Registration helpers
# ---------------------------------------------------------------------------

CLASSES: tuple[type, ...] = (
    AA_P11_BoneAssignment,
    AA_P11_ChannelOverride,
    AA_P11_AnimLayer,
    AA_P11_LayerPreset,
    AA_P11_Properties,
)


def get_p11(context: bpy.types.Context) -> AA_P11_Properties | None:
    """Return the animation layer PropertyGroup from the current scene, or None."""
    scene = getattr(context, "scene", None)
    if scene is None:
        return None
    return getattr(scene, P11_SCENE_ATTR, None)


def register_properties() -> None:
    """Register animation layer properties on Scene.

    Attaches the animation layer stack, blend modes, per-layer weights,
    and layer presets to the scene so they persist across file saves and
    are accessible to all animation layer layer blending and evaluation operators.
    """
    bpy.types.Scene.anim_assist_p11 = PointerProperty(  # type: ignore[assignment]
        type=AA_P11_Properties,
        name="Anim Assist P11",
    )


def unregister_properties() -> None:
    """Unregister animation layer properties from Scene.

    Safe to call even if properties were never registered.
    """
    try:
        del bpy.types.Scene.anim_assist_p11
    except AttributeError:
        pass
