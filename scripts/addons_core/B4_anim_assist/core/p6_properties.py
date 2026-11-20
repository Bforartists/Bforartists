# --- RETIME TOOLS ---
"""Scene-scoped PropertyGroup for retiming and timeline manipulation.

Mounted on ``Scene.anim_assist_p6`` so it does not collide with other modules.
Every enum uses the callable-items pattern for Blender string-retention GC safety.
"""

from __future__ import annotations

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
)

__all__ = [
    "AA_P6_Properties",
    "get_p6",
    "register_properties",
    "unregister_properties",
    "ANCHOR_MODE_ITEMS",
    "RANGE_MODE_ITEMS",
    "GAP_FILL_MODE_ITEMS",
    "DIAG_RESULT_ITEMS",
    "P6_SCENE_ATTR",
    "CLASSES",
]

P6_SCENE_ATTR = "anim_assist_p6"


# ---------------------------------------------------------------------------
# Enum item tables (module-level for GC safety)
# ---------------------------------------------------------------------------

ANCHOR_MODE_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("FIRST", "First Key",
     "Scale around the earliest keyframe in the selection/action."),
    ("LAST", "Last Key",
     "Scale around the latest keyframe in the selection/action."),
    ("CURRENT_FRAME", "Current Frame",
     "Scale around the scene's current frame (playhead position)."),
    ("ACTIVE", "Active Key",
     "Scale around the active/highlighted keyframe (falls back to playhead)."),
    ("CUSTOM", "Custom Frame",
     "Scale around a manually specified pivot frame."),
)

RANGE_MODE_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("SELECTION", "From Selection",
     "Derive the active range from the frame span of selected keys."),
    ("SCENE", "Scene Range",
     "Use the scene's playback range (frame_start to frame_end)."),
    ("CUSTOM", "Custom",
     "Specify range start and end frames manually."),
)

GAP_FILL_MODE_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("CONSTANT", "Constant Hold",
     "Fill the gap by inserting a key that holds the last known value."),
    ("LINEAR", "Linear Bridge",
     "Insert a key at the gap midpoint and set interpolation to LINEAR."),
    ("NONE", "Mark Only",
     "Report the gap without inserting any keys."),
)

DIAG_RESULT_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("NONE", "Not Run", "Diagnostics have not been run yet."),
    ("CLEAN", "Clean", "No timing issues detected."),
    ("GAPS", "Gaps Found", "One or more timing gaps were detected."),
    ("CLUSTERS", "Clusters Found", "One or more key clusters were detected."),
    ("BOTH", "Gaps & Clusters", "Both timing gaps and key clusters detected."),
)


def _anchor_items(self, context):   # noqa: ARG001
    return ANCHOR_MODE_ITEMS


def _range_mode_items(self, context):   # noqa: ARG001
    return RANGE_MODE_ITEMS


def _gap_fill_items(self, context):   # noqa: ARG001
    return GAP_FILL_MODE_ITEMS


def _diag_result_items(self, context):   # noqa: ARG001
    return DIAG_RESULT_ITEMS


# ---------------------------------------------------------------------------
# PropertyGroup
# ---------------------------------------------------------------------------

class AA_P6_Properties(bpy.types.PropertyGroup):
    """Scene-scoped defaults for retime retiming and timing tools."""

    # ----- Retiming -----

    anchor_mode: EnumProperty(  # type: ignore[valid-type]
        name="Anchor",
        description="Pivot point for scale operations",
        items=_anchor_items,
        default=0,
    )

    scale_factor: FloatProperty(  # type: ignore[valid-type]
        name="Scale Factor",
        description=(
            "Timing scale factor (1.0 = unchanged, 2.0 = double duration, "
            "0.5 = half duration)"
        ),
        default=1.0,
        min=0.01,
        max=100.0,
        soft_min=0.1,
        soft_max=10.0,
        step=10,
        precision=3,
    )

    pivot_frame: FloatProperty(  # type: ignore[valid-type]
        name="Pivot Frame",
        description=(
            "Custom pivot frame for scale operations. "
            "Only active when Anchor = Custom Frame."
        ),
        default=0.0,
        precision=1,
    )

    offset_frames: FloatProperty(  # type: ignore[valid-type]
        name="Offset",
        description="Number of frames to shift keys by (positive = later)",
        default=1.0,
        soft_min=-500.0,
        soft_max=500.0,
        step=100,
        precision=1,
    )

    # ----- Ripple -----
    # Note: ripple direction is implicit in each dedicated operator
    # (ripple_forward / ripple_backward / ripple_to_end) rather than
    # stored as a property, so there is no ripple_direction field here.

    ripple_delta: FloatProperty(  # type: ignore[valid-type]
        name="Ripple Amount",
        description="How many frames to shift the rippled keys",
        default=1.0,
        soft_min=-500.0,
        soft_max=500.0,
        step=100,
        precision=1,
    )

    insert_frames: IntProperty(  # type: ignore[valid-type]
        name="Frame Count",
        description="Number of frames to insert or remove at the playhead",
        default=1,
        min=1,
        soft_max=500,
    )

    # ----- Timing Range -----

    range_mode: EnumProperty(  # type: ignore[valid-type]
        name="Range Mode",
        description="How to determine the active timing range",
        items=_range_mode_items,
        default=0,
    )

    range_start: FloatProperty(  # type: ignore[valid-type]
        name="Start",
        description="Custom timing range start frame",
        default=1.0,
        precision=1,
    )

    range_end: FloatProperty(  # type: ignore[valid-type]
        name="End",
        description="Custom timing range end frame",
        default=100.0,
        precision=1,
    )

    stored_range_start: FloatProperty(  # type: ignore[valid-type]
        name="Stored Start",
        default=1.0,
        options={"HIDDEN"},
    )

    stored_range_end: FloatProperty(  # type: ignore[valid-type]
        name="Stored End",
        default=100.0,
        options={"HIDDEN"},
    )

    has_stored_range: BoolProperty(  # type: ignore[valid-type]
        name="Has Stored Range",
        default=False,
        options={"HIDDEN"},
    )

    # ----- Gap Tools -----

    gap_threshold: FloatProperty(  # type: ignore[valid-type]
        name="Gap Threshold",
        description="Minimum frame gap to count as a timing gap",
        default=4.0,
        min=1.0,
        soft_max=200.0,
        precision=1,
    )

    gap_fill_mode: EnumProperty(  # type: ignore[valid-type]
        name="Fill Mode",
        description="How to fill detected timing gaps",
        items=_gap_fill_items,
        default=0,
    )

    cluster_radius: FloatProperty(  # type: ignore[valid-type]
        name="Cluster Radius",
        description=(
            "Keys within this many frames of each other are considered a cluster"
        ),
        default=2.0,
        min=0.5,
        soft_max=20.0,
        precision=1,
    )

    # ----- Diagnostics (persisted results) -----

    last_diag_result: EnumProperty(  # type: ignore[valid-type]
        name="Result",
        items=_diag_result_items,
        default=0,
        options={"HIDDEN"},
    )

    last_diag_gap_count: IntProperty(  # type: ignore[valid-type]
        name="Gap Count",
        default=0,
        options={"HIDDEN"},
    )

    last_diag_cluster_count: IntProperty(  # type: ignore[valid-type]
        name="Cluster Count",
        default=0,
        options={"HIDDEN"},
    )

    last_diag_score: FloatProperty(  # type: ignore[valid-type]
        name="Timing Score",
        default=-1.0,
        options={"HIDDEN"},
    )

    show_diag_details: BoolProperty(  # type: ignore[valid-type]
        name="Show Details",
        description="Expand the detailed diagnostic breakdown in the panel",
        default=False,
    )

    # ----- Modal preferences -----

    modal_snap: BoolProperty(  # type: ignore[valid-type]
        name="Snap to Frames",
        description="Snap keyframe positions to integer frames during modal operations",
        default=True,
    )

    modal_show_header: BoolProperty(  # type: ignore[valid-type]
        name="Show Header Delta",
        description="Display the current offset/scale delta in the viewport header",
        default=True,
    )


# ---------------------------------------------------------------------------
# Registration helpers
# ---------------------------------------------------------------------------

CLASSES: tuple[type, ...] = (AA_P6_Properties,)


def get_p6(context: bpy.types.Context) -> AA_P6_Properties | None:
    """Return the retime PropertyGroup from the current scene, or None."""
    scene = getattr(context, "scene", None)
    if scene is None:
        return None
    return getattr(scene, P6_SCENE_ATTR, None)


def register_properties() -> None:
    """Attach retime PropertyGroup to Scene so retime tool settings persist with the .blend file."""
    bpy.types.Scene.anim_assist_p6 = bpy.props.PointerProperty(  # type: ignore[assignment]
        type=AA_P6_Properties,
        name="Anim Assist P6",
    )


def unregister_properties() -> None:
    """Detach retime PropertyGroup from Scene on addon unregister."""
    try:
        del bpy.types.Scene.anim_assist_p6
    except AttributeError:
        pass
