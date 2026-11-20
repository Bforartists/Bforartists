# --- LIPSYNC LAYER PROPERTIES (Phase 12) ---
"""PropertyGroups for the Phase 12 lipsync system.

v12 additions
-------------
- AA_P12_CueRow: one row in the cue table on each lipsync link.
- AA_P12_ShapeKeyWiringEntry: viseme -> shape key name mapping.
- AA_P12_LipsyncLayerLink gains: mode (PREVIEW/SHIPPED), target_kind
  (BONES/SHAPE_KEYS/BOTH), mesh_name, cue_table.
- AA_P12_Properties gains: shape_key_wiring collection.
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

from .. import constants
from .logging import get_logger

__all__ = [
    "AA_P12_CueRow",
    "AA_P12_ShapeKeyWiringEntry",
    "AA_P12_VisemePoseEntry",
    "AA_P12_RigWiringEntry",
    "AA_P12_LipsyncLayerLink",
    "AA_P12_Properties",
    "CLASSES",
    "register_properties",
    "unregister_properties",
    "get_p12",
    "find_layer_link",
]

_log = get_logger(__name__)


def _viseme_library_items(self, context):
    return (
        ("BASIC_JAW", "Basic Mouth Open", "Single jaw bone driven by audio amplitude"),
        ("CARTOON_5", "Cartoon (5 visemes)", "A, E, I, O, U + closed - snappy stylised reads"),
        ("REALISTIC_12", "Realistic (12 visemes)", "Preston Blair viseme set with anticipation"),
    )


def _backend_items(self, context):
    return (
        ("AMPLITUDE", "Amplitude Only", "Use audio RMS envelope - always available"),
        ("RHUBARB", "Rhubarb Lip Sync", "External Rhubarb CLI for phoneme-accurate visemes"),
    )


def _setup_mode_items(self, context):
    return (
        ("AUTO_BAKE", "Auto Bake", "Run audio analysis immediately and write viseme keys"),
        ("MARKER_ONLY", "Markers Only", "Place phoneme markers on the timeline; key by hand"),
    )


def _layer_mode_items(self, context):
    """v12: PREVIEW vs SHIPPED evaluation mode for the lipsync layer."""
    return (
        ("PREVIEW", "Preview (Live)", "Drivers respond to scrubbing/playback - fast iteration"),
        ("SHIPPED", "Shipped (Baked)", "Shape key/bone fcurves written - render-ready, NLA-safe"),
    )


def _target_kind_items(self, context):
    """v12: Which surface the lipsync drives."""
    return (
        ("SHAPE_KEYS", "Shape Keys", "Drive mouth shape keys (cartoon/blendshape rigs)"),
        ("BONES", "Bones", "Drive face bones (Rigify-style face rigs)"),
        ("BOTH", "Both", "Drive shape keys AND bones (combined rigs)"),
    )


# ---------------------------------------------------------------------------
# v12: Cue row (stored on each lipsync link)
# ---------------------------------------------------------------------------

class AA_P12_CueRow(bpy.types.PropertyGroup):
    """One phoneme cue: timestamp + viseme name. Used by both PREVIEW and SHIPPED."""

    time_seconds: FloatProperty(  # type: ignore[valid-type]
        name="Time",
        description="Cue timestamp in seconds from start of audio",
        default=0.0,
        min=0.0,
    )
    viseme_name: StringProperty(  # type: ignore[valid-type]
        name="Viseme",
        description="Logical viseme name from the active library",
        default="rest",
    )


# ---------------------------------------------------------------------------
# v12: Shape key wiring (parallel to rig wiring)
# ---------------------------------------------------------------------------

class AA_P12_ShapeKeyWiringEntry(bpy.types.PropertyGroup):
    """Logical viseme name -> shape_key name on the wired mesh."""

    viseme_name: StringProperty(  # type: ignore[valid-type]
        name="Viseme",
        description="Logical viseme name (matches a viseme in the active library)",
        default="A",
    )
    shape_key_name: StringProperty(  # type: ignore[valid-type]
        name="Shape Key",
        description="Shape key (key block) on the mesh that holds this viseme pose",
        default="",
    )


# ---------------------------------------------------------------------------
# Existing (v11): viseme pose entries + rig wiring
# ---------------------------------------------------------------------------

class AA_P12_VisemePoseEntry(bpy.types.PropertyGroup):
    """One captured viseme pose: name + serialized bone transforms (JSON)."""

    viseme_name: StringProperty(  # type: ignore[valid-type]
        name="Viseme",
        default="rest",
    )
    pose_json: StringProperty(  # type: ignore[valid-type]
        name="Pose JSON",
        default="{}",
    )
    is_builtin: BoolProperty(  # type: ignore[valid-type]
        name="Built-in",
        default=False,
    )


class AA_P12_RigWiringEntry(bpy.types.PropertyGroup):
    """Logical face role -> bone name on the active armature."""

    role: StringProperty(  # type: ignore[valid-type]
        name="Role",
        default="jaw",
    )
    bone_name: StringProperty(  # type: ignore[valid-type]
        name="Bone",
        description="Bone assigned to this logical facial role",
        default="",
    )


# ---------------------------------------------------------------------------
# Lipsync layer link (v11 + v12 fields)
# ---------------------------------------------------------------------------

class AA_P12_LipsyncLayerLink(bpy.types.PropertyGroup):
    """Configuration that binds an audio source to a Phase 11 animation layer."""

    layer_name: StringProperty(  # type: ignore[valid-type]
        name="Layer Name",
        default="",
    )
    armature_name: StringProperty(  # type: ignore[valid-type]
        name="Armature",
        default="",
    )
    audio_path: StringProperty(  # type: ignore[valid-type]
        name="Audio File",
        description="WAV audio file used to generate this lipsync layer",
        subtype="FILE_PATH",
        default="",
    )
    audio_sha256: StringProperty(  # type: ignore[valid-type]
        name="Audio Hash",
        default="",
    )
    speaker_strip_name: StringProperty(  # type: ignore[valid-type]
        name="Sequencer Strip",
        default="",
    )
    viseme_library: EnumProperty(  # type: ignore[valid-type]
        name="Viseme Library",
        description="Viseme naming and pose library used for speech shapes",
        items=_viseme_library_items,
        default=0,
    )
    backend: EnumProperty(  # type: ignore[valid-type]
        name="Backend",
        description="Speech-analysis backend used to generate viseme cues",
        items=_backend_items,
        default=0,
    )
    setup_mode: EnumProperty(  # type: ignore[valid-type]
        name="Setup Mode",
        description="Whether setup creates markers only or also performs the initial bake",
        items=_setup_mode_items,
        default=0,
    )
    frame_offset: IntProperty(  # type: ignore[valid-type]
        name="Frame Offset",
        description="Shift generated lipsync cues by this many frames",
        default=1,
        min=0,
    )
    anticipation_frames: IntProperty(  # type: ignore[valid-type]
        name="Anticipation",
        description="Move mouth-shape cues earlier by this many frames",
        default=2,
        min=0,
        max=12,
    )
    last_baked_start: IntProperty(  # type: ignore[valid-type]
        name="Bake Range Start",
        default=0,
    )
    last_baked_end: IntProperty(  # type: ignore[valid-type]
        name="Bake Range End",
        default=0,
    )
    is_stale: BoolProperty(  # type: ignore[valid-type]
        name="Audio Changed",
        default=False,
    )
    # ----- v12 additions -----
    mode: EnumProperty(  # type: ignore[valid-type]
        name="Mode",
        description="PREVIEW = live drivers; SHIPPED = baked fcurves",
        items=_layer_mode_items,
        default=0,
    )
    target_kind: EnumProperty(  # type: ignore[valid-type]
        name="Target",
        description="What surface the lipsync drives",
        items=_target_kind_items,
        default=0,
    )
    mesh_name: StringProperty(  # type: ignore[valid-type]
        name="Mesh",
        description="Object whose shape keys are driven (usually the head mesh)",
        default="",
    )
    cue_table: CollectionProperty(  # type: ignore[valid-type]
        type=AA_P12_CueRow,
        name="Cue Table",
        description="Phoneme/viseme schedule shared by PREVIEW drivers and SHIPPED bake",
    )
    active_cue_index: IntProperty(  # type: ignore[valid-type]
        name="Active Cue",
        default=0,
        min=0,
    )


# ---------------------------------------------------------------------------
# Top-level p12 properties on the scene
# ---------------------------------------------------------------------------

class AA_P12_Properties(bpy.types.PropertyGroup):
    """Scene-level container for the lipsync system."""

    enabled: BoolProperty(  # type: ignore[valid-type]
        name="Enable Lipsync",
        description="Enable Anim Assist lipsync evaluation for this scene",
        default=True,
    )
    viseme_poses: CollectionProperty(  # type: ignore[valid-type]
        type=AA_P12_VisemePoseEntry,
        name="Viseme Poses",
    )
    active_viseme_index: IntProperty(  # type: ignore[valid-type]
        name="Active Viseme",
        default=0,
        min=0,
    )
    rig_wiring: CollectionProperty(  # type: ignore[valid-type]
        type=AA_P12_RigWiringEntry,
        name="Rig Wiring",
    )
    layer_links: CollectionProperty(  # type: ignore[valid-type]
        type=AA_P12_LipsyncLayerLink,
        name="Lipsync Layer Links",
    )
    active_link_index: IntProperty(  # type: ignore[valid-type]
        name="Active Link",
        default=0,
        min=0,
    )
    show_manual_overrides: BoolProperty(  # type: ignore[valid-type]
        name="Highlight Manual Overrides",
        description="Highlight keys protected from automatic lipsync rebaking",
        default=True,
    )
    rhubarb_path: StringProperty(  # type: ignore[valid-type]
        name="Rhubarb Path",
        description="Path to the optional Rhubarb Lip Sync executable",
        subtype="FILE_PATH",
        default="",
    )
    amplitude_jaw_scale: FloatProperty(  # type: ignore[valid-type]
        name="Jaw Amplitude Scale",
        description="Multiplier applied to generated jaw movement",
        default=1.0,
        min=0.0,
        max=10.0,
    )
    # ----- v12 additions -----
    shape_key_wiring: CollectionProperty(  # type: ignore[valid-type]
        type=AA_P12_ShapeKeyWiringEntry,
        name="Shape Key Wiring",
        description="Logical viseme -> shape_key mapping for the active mesh",
    )
    active_shape_key_index: IntProperty(  # type: ignore[valid-type]
        name="Active Shape Key Wiring Row",
        default=0,
        min=0,
    )
    warn_on_render_in_preview: BoolProperty(  # type: ignore[valid-type]
        name="Warn If Rendering in PREVIEW",
        description=(
            "Print a console warning if a render starts while a lipsync layer "
            "is still in PREVIEW (driver) mode - drivers may not evaluate the "
            "way you expect across all render engines"
        ),
        default=True,
    )


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

CLASSES: tuple[type, ...] = (
    AA_P12_CueRow,
    AA_P12_ShapeKeyWiringEntry,
    AA_P12_VisemePoseEntry,
    AA_P12_RigWiringEntry,
    AA_P12_LipsyncLayerLink,
    AA_P12_Properties,
)


def get_p12(context):
    scene = getattr(context, "scene", None)
    if scene is None:
        return None
    return getattr(scene, constants.P12_SCENE_ATTR, None)


def find_layer_link(p12, layer_name: str):
    if p12 is None or not layer_name:
        return None
    for link in p12.layer_links:
        if link.layer_name == layer_name:
            return link
    return None


def register_properties() -> None:
    setattr(
        bpy.types.Scene,
        constants.P12_SCENE_ATTR,
        PointerProperty(type=AA_P12_Properties, name="Anim Assist P12"),
    )
    _log.debug("p12 properties attached to Scene.%s", constants.P12_SCENE_ATTR)


def unregister_properties() -> None:
    try:
        delattr(bpy.types.Scene, constants.P12_SCENE_ATTR)
    except AttributeError:
        pass
