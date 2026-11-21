# --- TRAJECTORY TOOLS ---
"""Help entries for trajectory visualization and analysis tools.

45 entries across 7 categories matching the trajectory feature set.
Category names correspond to the sidebar panel sections so the
Help Browser and panel UI stay in sync.
"""

from __future__ import annotations

from .help_registry import (
    HelpEntry,
    register_phase_help,
    unregister_phase_help,
)

__all__ = [
    "PHASE5_ENTRIES",
    "register",
    "unregister",
]

_PHASE = "phase5"


def _H(id_: str, label: str, tooltip: str, description: str, category: str) -> HelpEntry:
    return HelpEntry(
        id=id_,
        label=label,
        tooltip=tooltip,
        description=description,
        phase=_PHASE,
        category=category,
    )


PHASE5_ENTRIES: tuple[HelpEntry, ...] = (
    # ====================================================================
    # Trajectory Display
    # ====================================================================
    _H("op.animassist.p5_enable_overlay",
       "Enable Overlay",
       "Register viewport draw handlers and display trajectory paths",
       "Registers a POST_VIEW handler for 3D trajectory geometry and a "
       "POST_PIXEL handler for 2D labels and the arc score badge. Triggers "
       "an initial sampling pass for all visible targets.",
       "Trajectory Display"),
    _H("op.animassist.p5_disable_overlay",
       "Disable Overlay",
       "Unregister draw handlers and clear trajectory display",
       "Tears down both draw handlers, clears the draw data buffer, resets "
       "RuntimeState.overlay_enabled, and invalidates the path cache.",
       "Trajectory Display"),
    _H("op.animassist.p5_refresh_overlay",
       "Refresh Overlay",
       "Invalidate cache and re-sample all visible trajectory paths",
       "Bumps the SessionCache generation counter to invalidate all cached "
       "entries, then re-samples every target and rebuilds the draw data. "
       "Use this after editing keyframes if auto-refresh is not active.",
       "Trajectory Display"),
    _H("prop.p5_display_mode",
       "Display Mode",
       "Choose which targets show trajectory overlays",
       "Active Control shows only the active bone or object. Multi Control "
       "shows every selected bone or object (up to Max Display Targets). "
       "Isolate shows only the explicitly named target.",
       "Trajectory Display"),
    _H("prop.p5_color_preset",
       "Color Preset",
       "Colour palette for the trajectory overlay",
       "Three built-in palettes: Default (blue path, yellow keyframes), "
       "Contrast (high-contrast colours for bright scenes), and Pastel "
       "(muted tones that reduce visual noise).",
       "Trajectory Display"),
    _H("prop.p5_path_width",
       "Path Width",
       "Line width for the trajectory path in pixels",
       "Controls the GPU line width used for the main trajectory path. "
       "Increase for visibility on high-DPI displays or crowded scenes.",
       "Trajectory Display"),
    _H("prop.p5_max_display_targets",
       "Max Display Targets",
       "Limit simultaneous trajectories to prevent viewport stalls",
       "In Multi Control mode, only the first N selected targets will have "
       "their trajectories drawn. Increase for rigs with many controls, "
       "decrease if the viewport is lagging. The default is conservative "
       "so turning the overlay on does not slow down pose work.",
       "Trajectory Display"),

    # ====================================================================
    # Path Overlays
    # ====================================================================
    _H("prop.p5_show_frame_ticks",
       "Frame Ticks",
       "Draw small dots at every sampled frame position",
       "When enabled, each sampled frame along the path is marked with a "
       "small grey dot. Useful for visualising frame spacing at a glance.",
       "Path Overlays"),
    _H("prop.p5_show_keyframe_ticks",
       "Keyframe Ticks",
       "Draw highlighted dots at keyframe positions",
       "Yellow dots mark the positions of actual keyframes on the path. "
       "Frame numbers can optionally be drawn next to these ticks.",
       "Path Overlays"),
    _H("prop.p5_show_frame_numbers",
       "Frame Numbers",
       "Draw frame-number labels next to keyframe ticks",
       "Adds text labels with the frame number beside each keyframe tick. "
       "Useful for identifying which key corresponds to which frame.",
       "Path Overlays"),
    _H("prop.p5_show_velocity",
       "Velocity Vectors",
       "Draw velocity direction arrows at each sample point",
       "Green lines extending from each sample point in the direction of "
       "motion. Length is proportional to speed. Helps visualise easing.",
       "Path Overlays"),
    _H("prop.p5_show_tangent",
       "Tangent Lines",
       "Draw path tangent lines at keyframe positions",
       "Blue lines through keyframe positions showing the direction of the "
       "trajectory at that point. Useful for checking handle alignment.",
       "Path Overlays"),
    _H("prop.p5_show_ghost_points",
       "Ghost Points",
       "Draw faded points near the current frame",
       "Shows the 2 frames before and after the current frame as faded "
       "dots, providing local context without cluttering the full path.",
       "Path Overlays"),

    # ====================================================================
    # Spacing Analysis
    # ====================================================================
    _H("prop.p5_show_spacing_color",
       "Spacing Colorization",
       "Colour path segments by their spacing relative to the median",
       "Segments longer than the median are tinted toward the issue-high "
       "colour; shorter segments toward the issue-low colour. The base "
       "path colour represents median spacing.",
       "Spacing Analysis"),
    _H("prop.p5_show_deviation_heatmap",
       "Arc Deviation Heatmap",
       "Colour the path by deviation from a locally-fit arc",
       "Uses a blue-to-red colour ramp where blue indicates good arc "
       "conformance and red indicates high deviation. Overrides spacing "
       "colorization when both are enabled.",
       "Spacing Analysis"),
    _H("prop.p5_spacing_hi",
       "Overspaced Ratio",
       "Segments exceeding this multiple of the median are flagged",
       "When a segment between two consecutive samples is longer than "
       "spacing_hi times the median segment length, an OVERSPACED issue "
       "is reported. Default is 1.8.",
       "Spacing Analysis"),
    _H("prop.p5_spacing_lo",
       "Underspaced Ratio",
       "Segments shorter than this multiple of the median are flagged",
       "When a segment is shorter than spacing_lo times the median, an "
       "UNDERSPACED issue is reported. Default is 0.4.",
       "Spacing Analysis"),

    # ====================================================================
    # Arc Diagnostics
    # ====================================================================
    _H("op.animassist.p5_run_diagnostics",
       "Run Diagnostics",
       "Run all enabled detectors and update the issue list",
       "Executes every enabled detector (drift, flat arc, zig-zag, pop, "
       "spacing, reversal, stop, apex/contact) and replaces the current "
       "issue list. Results are drawn as red marker dots in the viewport.",
       "Arc Diagnostics"),
    _H("prop.p5_enable_drift_detect",
       "Arc Drift Detector",
       "Detect points that deviate from a locally-fit arc",
       "Uses a 3-point circumradius fit to measure how far each sample "
       "deviates from a smooth arc. Points exceeding the drift tolerance "
       "are flagged as ARC_DRIFT issues.",
       "Arc Diagnostics"),
    _H("prop.p5_enable_flat_detect",
       "Flat Arc Detector",
       "Detect near-zero curvature stretches",
       "Analyses variance along each axis in a sliding window. If the two "
       "smallest variances are both below the threshold, the segment is "
       "flagged as FLAT_ARC — indicating a linear motion that might lack "
       "arc appeal.",
       "Arc Diagnostics"),
    _H("prop.p5_enable_zigzag_detect",
       "Zig-Zag Detector",
       "Detect rapid direction reversals in a short window",
       "Counts velocity sign changes in a sliding window. If the reversal "
       "count exceeds the threshold, a ZIGZAG issue is flagged — often "
       "indicating jitter or over-keying.",
       "Arc Diagnostics"),
    _H("prop.p5_enable_pop_detect",
       "Pop Detector",
       "Detect sudden speed jumps between consecutive samples",
       "Compares each sample's speed against the median. Samples exceeding "
       "the pop ratio are flagged as POP issues — indicating a potential "
       "interpolation glitch or missing ease.",
       "Arc Diagnostics"),
    _H("prop.p5_enable_reversal_detect",
       "Reversal Detector",
       "Detect velocity direction reversals",
       "Flags points where the velocity dot product with the previous "
       "sample is negative, indicating the motion changed direction.",
       "Arc Diagnostics"),
    _H("prop.p5_enable_stop_detect",
       "Stop Detector",
       "Detect near-zero-speed holds",
       "Flags frames where the computed speed falls below the stop "
       "threshold. Useful for finding unintended holds or plateaus.",
       "Arc Diagnostics"),
    _H("prop.p5_enable_apex_contact_detect",
       "Apex/Contact Detector",
       "Detect local maxima and minima on the gravity axis",
       "Marks local highs as APEX and local lows as CONTACT on the "
       "Z-axis (configurable). Useful for timing checks on jump arcs.",
       "Arc Diagnostics"),
    _H("prop.p5_drift_tolerance",
       "Drift Tolerance",
       "Normalised deviation threshold for the arc drift detector",
       "Points where the normalised deviation (deviation / circumradius) "
       "exceeds this value are flagged. Lower values catch subtler "
       "deviations but may produce more false positives.",
       "Arc Diagnostics"),
    _H("prop.p5_pop_ratio",
       "Pop Ratio",
       "Speed multiple threshold for the pop detector",
       "A sample's speed must exceed this multiple of the median speed "
       "to be flagged as a pop. Default is 4.0.",
       "Arc Diagnostics"),

    # ====================================================================
    # Issue Navigation
    # ====================================================================
    _H("op.animassist.p5_jump_next_issue",
       "Next Issue",
       "Jump the playhead to the next detected issue",
       "Moves the scene's current frame to the frame of the next issue "
       "after the current position. Wraps around to the first issue if "
       "there are no more issues ahead.",
       "Issue Navigation"),
    _H("op.animassist.p5_jump_prev_issue",
       "Previous Issue",
       "Jump the playhead to the previous detected issue",
       "Moves the scene's current frame to the frame of the most recent "
       "issue before the current position. Wraps to the last issue if "
       "there are no issues behind.",
       "Issue Navigation"),
    _H("op.animassist.p5_select_bad_arc_keys",
       "Select Bad-Arc Keys",
       "Select keyframes near detected arc issues",
       "Walks all location-channel keyframe points and selects those "
       "within the proximity radius of a detected issue. Deselects "
       "keyframes that are not near any issue.",
       "Issue Navigation"),
    _H("op.animassist.p5_suggest_candidates",
       "Suggest Candidate Keys",
       "Identify frames where adding a key might improve the arc",
       "Sorts issues by severity and reports the top N frames where a "
       "new keyframe insertion could reduce arc deviation. Deduplicates "
       "within a 2-frame radius.",
       "Issue Navigation"),

    # ====================================================================
    # Path Configuration
    # ====================================================================
    _H("prop.p5_scope_mode",
       "Scope Mode",
       "How the sample window is determined",
       "Around Current Frame samples a window centred on the playhead. "
       "Full Playback Range uses the scene's start/end frames. Custom "
       "Range lets you set explicit start and end frames.",
       "Path Configuration"),
    _H("prop.p5_window_before",
       "Frames Before",
       "Number of frames before the current frame to sample",
       "Only applies in Around Current Frame mode. Increase for a wider "
       "view of the trajectory history.",
       "Path Configuration"),
    _H("prop.p5_window_after",
       "Frames After",
       "Number of frames after the current frame to sample",
       "Only applies in Around Current Frame mode. Increase to see more "
       "of the upcoming trajectory.",
       "Path Configuration"),
    _H("prop.p5_space_mode",
       "Space Mode",
       "Coordinate space for trajectory drawing",
       "World draws the path in absolute world coordinates. Camera "
       "projects relative to the active camera. Local draws in the "
       "object's own coordinate space.",
       "Path Configuration"),
    _H("op.animassist.p5_isolate_target",
       "Isolate Target",
       "Show only one target's trajectory",
       "Switches display mode to Isolate and sets the named target as "
       "the sole visible trajectory. Useful for focusing on a specific "
       "bone in a complex rig.",
       "Path Configuration"),
    _H("op.animassist.p5_mute_unselected",
       "Mute Unselected",
       "Hide trajectories for non-selected targets",
       "Switches display mode to Multi Control, which inherently only "
       "shows selected bones or objects. Provides a quick way to "
       "declutter the viewport.",
       "Path Configuration"),
    _H("prop.p5_comparison_enabled",
       "Comparison Mode",
       "Show two trajectories side-by-side with delta overlay",
       "When enabled, a second target's trajectory is drawn alongside "
       "the primary target using the comparison palette colours.",
       "Path Configuration"),

    # ====================================================================
    # Sampling Options
    # ====================================================================
    _H("prop.p5_sample_step",
       "Sample Step",
       "Frame step between samples (1.0 = one per frame)",
       "Controls the density of samples along the trajectory. Values "
       "below 1.0 enable subframe sampling for smoother paths at the "
       "cost of increased computation.",
       "Sampling Options"),
    _H("prop.p5_max_samples",
       "Max Samples",
       "Cap on total samples per target",
       "Prevents viewport stalls on long frame ranges. If the range "
       "divided by the step would exceed this value, sampling stops "
       "early. Default is 160.",
       "Sampling Options"),
    _H("prop.p5_use_subframe",
       "Subframe Sampling",
       "Sample at sub-frame intervals for smoother trajectories",
       "Enables sampling at fractional frame positions. The step property "
       "can be set below 1.0 when this is active. Increases computation "
       "cost proportionally.",
       "Sampling Options"),
    _H("prop.p5_use_constraints",
       "Constraint Evaluation",
       "Evaluate the depsgraph at each sample for constraint accuracy",
       "When enabled, the sampler calls scene.frame_set() and "
       "depsgraph.update() for every sample, producing positions that "
       "reflect IK, Copy Rotation, and other constraints. Much slower "
       "than fcurve-only mode — recommended only when constraints drive "
       "the motion.",
       "Sampling Options"),
    _H("prop.p5_custom_start",
       "Custom Start Frame",
       "First frame for Custom Range scope",
       "Sets the beginning of the sampling window when scope mode is set "
       "to Custom Range.",
       "Sampling Options"),
    _H("prop.p5_custom_end",
       "Custom End Frame",
       "Last frame for Custom Range scope",
       "Sets the end of the sampling window when scope mode is set "
       "to Custom Range.",
       "Sampling Options"),
)


def register() -> None:
    """Seed trajectory help entries into the help registry."""
    register_phase_help(_PHASE, PHASE5_ENTRIES)


def unregister() -> None:
    """Remove all trajectory help entries."""
    unregister_phase_help(_PHASE)
