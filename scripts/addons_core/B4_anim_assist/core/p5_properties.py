# --- TRAJECTORY TOOLS ---
"""Scene-scoped PropertyGroup for trajectory visualization and analysis.

Mounted on ``Scene.anim_assist_p5`` so it does not collide with
other modules.  Every enum uses the callable-items pattern for
Blender string-retention GC safety.
"""

from __future__ import annotations

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
)

from .p5_colors import palette_enum_items_callback

P5_SCENE_ATTR = "anim_assist_p5"

__all__ = [
    "P5_SCENE_ATTR",
    "AA_P5_Properties",
    "CLASSES",
    "register_properties",
    "unregister_properties",
    "get_p5",
]


# ---------------------------------------------------------------------------
# Enum item tables (module-level for GC safety)
# ---------------------------------------------------------------------------

DISPLAY_MODE_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("ACTIVE", "Active Control",
     "Show the trajectory for the active bone or object only."),
    ("MULTI", "Multi Control",
     "Show trajectories for every selected bone or object."),
    ("ISOLATE", "Isolate",
     "Show only the explicitly isolated target."),
)

SPACE_MODE_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("WORLD", "World",
     "Draw the trajectory in world space."),
    # TODO: Camera and Local modes require coordinate transforms in the
    # draw callback.  Deferred to trajectory.1.
    # ("CAMERA", "Camera",
    #  "Project the trajectory relative to the active camera."),
    # ("LOCAL", "Local",
    #  "Draw the trajectory in the object's local space."),
)

SCOPE_MODE_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("AROUND_CURRENT", "Around Current Frame",
     "Sample a window centred on the scene's current frame."),
    ("FULL_RANGE", "Full Playback Range",
     "Sample across the scene's full playback range."),
    ("CUSTOM", "Custom Range",
     "Sample between explicit start and end frames."),
)


def _display_mode_items(self, context):  # noqa: ARG001
    return DISPLAY_MODE_ITEMS


def _space_mode_items(self, context):  # noqa: ARG001
    return SPACE_MODE_ITEMS


def _scope_mode_items(self, context):  # noqa: ARG001
    return SCOPE_MODE_ITEMS


# ---------------------------------------------------------------------------
# PropertyGroup
# ---------------------------------------------------------------------------

class AA_P5_Properties(bpy.types.PropertyGroup):
    """Scene-scoped defaults for trajectory trajectory overlays."""

    # --- Master controls ---
    overlay_enabled: BoolProperty(  # type: ignore[valid-type]
        name="Enable Overlay",
        description=(
            "Master toggle for the trajectory overlay.  When disabled, no "
            "draw handlers are active and no sampling occurs."
        ),
        default=False,
    )
    display_mode: EnumProperty(  # type: ignore[valid-type]
        name="Display Mode",
        description="Which targets have visible trajectories.",
        items=_display_mode_items,
    )

    # --- Sampling ---
    scope_mode: EnumProperty(  # type: ignore[valid-type]
        name="Scope",
        description="How the sample window is determined.",
        items=_scope_mode_items,
    )
    window_before: IntProperty(  # type: ignore[valid-type]
        name="Frames Before",
        description=(
            "Number of frames before the current frame to sample "
            "when using Around Current Frame."
        ),
        default=25, min=1, soft_max=200,
    )
    window_after: IntProperty(  # type: ignore[valid-type]
        name="Frames After",
        description=(
            "Number of frames after the current frame to sample "
            "when using Around Current Frame."
        ),
        default=25, min=1, soft_max=200,
    )
    custom_start: FloatProperty(  # type: ignore[valid-type]
        name="Start Frame",
        description="First frame for Custom Range scope.",
        default=1.0,
    )
    custom_end: FloatProperty(  # type: ignore[valid-type]
        name="End Frame",
        description="Last frame for Custom Range scope.",
        default=250.0,
    )
    sample_step: FloatProperty(  # type: ignore[valid-type]
        name="Step",
        description=(
            "Frame step between samples.  1.0 = one sample per frame.  "
            "Values below 1.0 enable subframe sampling (more precise but "
            "more expensive)."
        ),
        default=1.0, min=0.1, soft_max=5.0,
    )
    max_samples: IntProperty(  # type: ignore[valid-type]
        name="Max Samples",
        description="Cap on the total number of samples per target to prevent viewport stalls.",
        default=160, min=10, soft_max=2000,
    )
    use_subframe: BoolProperty(  # type: ignore[valid-type]
        name="Subframe Sampling",
        description=(
            "Sample at sub-frame intervals (step < 1.0) for smoother "
            "trajectories.  Increases computation cost proportionally."
        ),
        default=False,
    )
    use_constraints: BoolProperty(  # type: ignore[valid-type]
        name="Constraint Evaluation (Slow)",
        description=(
            "Evaluate the depsgraph at each sample frame for constraint-"
            "accurate positions.  Much slower than fcurve-only mode — "
            "ignored during playback to keep animation interaction smooth."
        ),
        default=False,
    )

    # --- Visual options ---
    space_mode: EnumProperty(  # type: ignore[valid-type]
        name="Space",
        description="Coordinate space for trajectory drawing.",
        items=_space_mode_items,
    )
    show_frame_ticks: BoolProperty(  # type: ignore[valid-type]
        name="Frame Ticks",
        description="Draw small dots at every sampled frame position.",
        default=False,
    )
    show_keyframe_ticks: BoolProperty(  # type: ignore[valid-type]
        name="Keyframe Ticks",
        description="Draw highlighted dots at keyframe positions on the path.",
        default=True,
    )
    show_frame_numbers: BoolProperty(  # type: ignore[valid-type]
        name="Frame Numbers",
        description="Draw frame-number labels next to keyframe ticks.",
        default=False,
    )
    show_velocity: BoolProperty(  # type: ignore[valid-type]
        name="Velocity Vectors",
        description="Draw velocity direction arrows at each sample point.",
        default=False,
    )
    show_tangent: BoolProperty(  # type: ignore[valid-type]
        name="Tangent Lines",
        description="Draw path tangent lines at keyframe positions.",
        default=False,
    )
    show_ghost_points: BoolProperty(  # type: ignore[valid-type]
        name="Ghost Points",
        description="Draw faded points for the 2 frames before and after the current frame.",
        default=True,
    )
    show_spacing_color: BoolProperty(  # type: ignore[valid-type]
        name="Spacing Colorization",
        description="Colour path segments by their spacing relative to the median.",
        default=False,
    )
    show_deviation_heatmap: BoolProperty(  # type: ignore[valid-type]
        name="Arc Deviation Heatmap",
        description="Colour the path by deviation from a locally-fit arc (blue=good, red=bad).",
        default=False,
    )
    color_preset: EnumProperty(  # type: ignore[valid-type]
        name="Color Preset",
        description="Colour palette for the trajectory overlay.",
        items=palette_enum_items_callback,
    )
    path_width: FloatProperty(  # type: ignore[valid-type]
        name="Path Width",
        description="Line width for the trajectory path in pixels.",
        default=2.0, min=0.5, soft_max=6.0,
    )
    max_display_targets: IntProperty(  # type: ignore[valid-type]
        name="Max Display Targets",
        description="Maximum number of simultaneous trajectory targets to avoid viewport stalls.",
        default=3, min=1, soft_max=32,
    )

    # --- Diagnostics ---
    enable_drift_detect: BoolProperty(  # type: ignore[valid-type]
        name="Arc Drift",
        description="Detect points that deviate from a locally-fit arc.",
        default=True,
    )
    enable_flat_detect: BoolProperty(  # type: ignore[valid-type]
        name="Flat Arc",
        description="Detect stretches where the path has near-zero curvature.",
        default=True,
    )
    enable_zigzag_detect: BoolProperty(  # type: ignore[valid-type]
        name="Zig-Zag",
        description="Detect rapid direction reversals in a short window.",
        default=True,
    )
    enable_pop_detect: BoolProperty(  # type: ignore[valid-type]
        name="Pop",
        description="Detect sudden speed jumps between consecutive samples.",
        default=True,
    )
    enable_spacing_detect: BoolProperty(  # type: ignore[valid-type]
        name="Spacing",
        description="Detect over-spaced and under-spaced segments.",
        default=True,
    )
    enable_reversal_detect: BoolProperty(  # type: ignore[valid-type]
        name="Reversal",
        description="Detect velocity direction reversals.",
        default=False,
    )
    enable_stop_detect: BoolProperty(  # type: ignore[valid-type]
        name="Stops",
        description="Detect near-zero-speed holds.",
        default=False,
    )
    enable_apex_contact_detect: BoolProperty(  # type: ignore[valid-type]
        name="Apex/Contact",
        description="Detect local maxima (apex) and minima (contact) on the gravity axis.",
        default=False,
    )

    # Thresholds
    drift_tolerance: FloatProperty(  # type: ignore[valid-type]
        name="Drift Tolerance",
        description="Normalised arc deviation above which a point is flagged as drift.",
        default=0.05, min=0.001, soft_max=0.5,
    )
    pop_ratio: FloatProperty(  # type: ignore[valid-type]
        name="Pop Ratio",
        description="Speed must exceed this multiple of median speed to be flagged as a pop.",
        default=4.0, min=1.5, soft_max=10.0,
    )
    spacing_hi: FloatProperty(  # type: ignore[valid-type]
        name="Overspaced Ratio",
        description="Segments longer than this multiple of median spacing are flagged.",
        default=1.8, min=1.1, soft_max=5.0,
    )
    spacing_lo: FloatProperty(  # type: ignore[valid-type]
        name="Underspaced Ratio",
        description="Segments shorter than this multiple of median spacing are flagged.",
        default=0.4, min=0.01, soft_max=0.9,
    )

    # --- Comparison mode ---
    comparison_enabled: BoolProperty(  # type: ignore[valid-type]
        name="Comparison Mode",
        description="Show trajectories for two targets side-by-side with delta overlay.",
        default=False,
    )
    comparison_target: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Compare Target",
        description="Name of the second bone or object to compare against the active target.",
        default="",
    )

    # --- Isolate ---
    isolate_target: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Isolate Target",
        description=(
            "Name of the bone or object whose trajectory is exclusively "
            "shown in Isolate mode."
        ),
        default="",
    )


CLASSES: tuple[type, ...] = (
    AA_P5_Properties,
)


def register_properties() -> None:
    """Attach trajectory PropertyGroup to Scene so trajectory settings persist with the .blend file."""
    bpy.types.Scene.anim_assist_p5 = bpy.props.PointerProperty(  # type: ignore[attr-defined]
        type=AA_P5_Properties,
        name="Anim Assist trajectory",
        description="Scene-scoped defaults for trajectory trajectory overlays.",
    )


def unregister_properties() -> None:
    """Detach trajectory PropertyGroup from Scene on addon unregister."""
    if hasattr(bpy.types.Scene, P5_SCENE_ATTR):
        try:
            del bpy.types.Scene.anim_assist_p5  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001
            pass  # Attribute may already be removed during hot-reload; harmless.


def get_p5(context) -> AA_P5_Properties | None:
    """Get the trajectory properties from context, or None if unavailable."""
    scene = getattr(context, "scene", None)
    if scene is None:
        return None
    return getattr(scene, P5_SCENE_ATTR, None)
