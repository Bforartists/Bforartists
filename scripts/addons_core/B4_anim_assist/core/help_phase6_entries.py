# --- RETIME TOOLS ---
"""Help / explainer entries for retiming and timeline manipulation.

47 ``HelpEntry`` records organised into 8 categories:

  1. Retiming Basics       — scale, offset, pivot
  2. Time Warp             — warp, bake, reverse, match
  3. Ripple Edit           — ripple forward/backward, insert/remove time
  4. Timing Ranges         — range definition, selection, store/restore
  5. Gap Tools             — detection, fill, collapse, distribution
  6. Snap & Clean          — snap to frames, remove duplicates
  7. Modal Tools           — interactive scale and offset
  8. Timing Diagnostics    — gap/cluster reports, scoring, navigation
"""

from __future__ import annotations

from .help_registry import (
    HelpEntry,
    register_phase_help,
    unregister_phase_help,
)

__all__ = [
    "PHASE6_ENTRIES",
    "register",
    "unregister",
]

_PHASE = "phase6"


def _H(id_: str, label: str, tooltip: str, description: str, category: str) -> HelpEntry:
    return HelpEntry(
        id=id_,
        label=label,
        tooltip=tooltip,
        description=description,
        phase=_PHASE,
        category=category,
    )


# ---------------------------------------------------------------------------
# Category 1 — Retiming Basics
# ---------------------------------------------------------------------------

PHASE6_ENTRIES: tuple[HelpEntry, ...] = (

    # Retiming Basics
    _H("op.animassist.p6_scale_keys",
       "Scale Keys",
       "Scale keyframe timing around a chosen pivot point",
       "All keys (or only those inside the active range) are rescaled around "
       "the chosen anchor frame. A factor > 1 spreads keys apart (slower animation); "
       "a factor < 1 compresses them (faster animation). Bézier handles are scaled "
       "proportionally to preserve curve shape. Use the Anchor Mode drop-down to "
       "choose whether to scale from the first key, last key, playhead, active key, "
       "or a manually specified custom frame.",
       "Retiming Basics"),

    _H("op.animassist.p6_offset_keys",
       "Offset Keys",
       "Shift all keys (or a range) by a fixed number of frames",
       "The Offset field sets the number of frames to move. Positive values push "
       "keys later in time; negative values pull them earlier. When a timing range "
       "is active only keys inside that range are affected. Bézier handles shift "
       "by the same amount so the curve shape is perfectly preserved.",
       "Retiming Basics"),

    _H("op.animassist.p6_set_pivot",
       "Set Pivot from Playhead",
       "Capture the current scene frame as the custom scale pivot",
       "Sets the Custom Frame pivot to the current playhead position. Switch "
       "Anchor Mode to 'Custom Frame' to use this value in all subsequent "
       "scale operations. Useful for keeping a specific pose locked in place "
       "while expanding or contracting the animation on either side.",
       "Retiming Basics"),

    _H("prop.p6_anchor_mode",
       "Anchor Mode",
       "Pivot point that stays fixed during scale operations",
       "First Key — pivot at the earliest keyframe of the action. "
       "Last Key — pivot at the latest keyframe. "
       "Current Frame — pivot at the playhead (most common for in-context edits). "
       "Active Key — pivot at the highlighted keyframe; falls back to the playhead "
       "when no specific key is active. "
       "Custom Frame — pivot at the value stored in the Custom Frame field.",
       "Retiming Basics"),

    _H("prop.p6_scale_factor",
       "Scale Factor",
       "Timing multiplier applied by Scale Keys. 1.0 = unchanged",
       "2.0 doubles the animation duration (everything runs at half-speed). "
       "0.5 halves the duration (double speed). The formula is: "
       "new_x = pivot + (old_x - pivot) × factor. "
       "Handles are rescaled by the same factor to preserve tangent continuity.",
       "Retiming Basics"),

    _H("prop.p6_offset_frames",
       "Offset Frames",
       "Frame count to add to every affected key's timing",
       "Positive = shift later; negative = shift earlier. Both the key position "
       "and its Bézier handles are translated by the same amount, so no curve "
       "distortion occurs.",
       "Retiming Basics"),

    # Time Warp
    _H("op.animassist.p6_time_warp",
       "Time Warp %",
       "Scale timing by a percentage (100 % = unchanged, 200 % = half speed)",
       "A convenience wrapper around Scale Keys that accepts a percentage directly. "
       "Enter 200 to make the animation run at half speed, 50 to make it run at "
       "double speed. Internally this is just (percentage / 100) used as the scale "
       "factor. The same Anchor Mode and range restrictions apply.",
       "Time Warp"),

    _H("op.animassist.p6_reverse_keys",
       "Reverse Keys",
       "Mirror keyframe timing within the active range",
       "The first key's timing becomes the last and vice-versa. All key values "
       "are untouched; only the x (time) coordinates are mirrored around the "
       "range's midpoint. Useful for creating reversed or palindrome cycles. "
       "The formula is: new_x = (range_start + range_end) - old_x.",
       "Time Warp"),

    _H("op.animassist.p6_bake_timing",
       "Bake to Integer Frames",
       "Round all keyframe positions to the nearest whole frame",
       "Sub-frame keyframes introduced by slow-motion retiming or fractional "
       "offset operations are rounded to the nearest integer frame. Bézier handles "
       "shift by the same correction delta so curve shape is preserved. Returns "
       "a count of how many keys were moved.",
       "Time Warp"),

    _H("op.animassist.p6_reset_timing",
       "Reset Timing",
       "Restore key positions from the last automatic timing snapshot",
       "The addon stores a keyframe snapshot before each destructive retiming "
       "operation (Scale, Offset, Ripple, etc.). Reset Timing rolls back to that "
       "snapshot in a single undo step. Only the most recent snapshot is kept; "
       "the snapshot is cleared when the file is closed or reloaded.",
       "Time Warp"),

    _H("op.animassist.p6_match_timing",
       "Match Timing",
       "Scale the active object's duration to match a reference object",
       "The reference is the previously active (or second-most-recently selected) "
       "object. The active object's action is scaled — using the FIRST anchor — "
       "so that its total key span equals the reference's total key span. "
       "Useful for syncing secondary characters or props to a hero rig.",
       "Time Warp"),

    # Ripple Edit
    _H("op.animassist.p6_ripple_forward",
       "Ripple Forward",
       "Push all keys after the playhead later by the ripple amount",
       "All keyframes with a time value strictly greater than the current frame "
       "are shifted forward by the configured Ripple Amount. Keys at or before "
       "the playhead are untouched. This is equivalent to inserting blank time "
       "after the playhead without creating new keys.",
       "Ripple Edit"),

    _H("op.animassist.p6_ripple_backward",
       "Ripple Backward",
       "Pull all keys before the playhead earlier by the ripple amount",
       "All keyframes strictly before the current frame are shifted backward by "
       "the Ripple Amount. Useful for pulling in a wind-up or anticipation section "
       "when the performance needs more preparation before a hit.",
       "Ripple Edit"),

    _H("op.animassist.p6_insert_time",
       "Insert Time",
       "Insert N blank frames at the playhead, shifting later keys forward",
       "A ripple-forward operation sized to exactly N frames (the Frame Count "
       "property). No new keyframes are created; existing keys after the "
       "playhead are translated to make room. Equivalent to Blender's "
       "Timeline → Insert Frames but scoped to the active action.",
       "Ripple Edit"),

    _H("op.animassist.p6_remove_time",
       "Remove Time",
       "Collapse N frames at the playhead by pulling later keys backward",
       "Keys inside the removed window (playhead to playhead + N) are deleted "
       "first, then all keys after the window's end are rippled backward to close "
       "the gap. Equivalent to cutting a section of time from the animation.",
       "Ripple Edit"),

    _H("op.animassist.p6_ripple_to_end",
       "Ripple to End",
       "Shift all keys from the playhead to the last key by the ripple amount",
       "Identical to Ripple Forward but applies only from the playhead to the "
       "end of the action rather than to every subsequent key. Useful for "
       "quickly closing a gap created by deleting a section of animation.",
       "Ripple Edit"),

    _H("op.animassist.p6_compress_timing",
       "Compress Timing",
       "Scale timing in the active range to fit a shorter duration",
       "Computes the scale factor needed to make the current range's content "
       "fit into the target duration, then applies it. Useful when a walk cycle "
       "needs to be tightened to match a shorter audio cue.",
       "Ripple Edit"),

    _H("prop.p6_ripple_delta",
       "Ripple Amount",
       "Frames to shift per ripple operation",
       "Positive = shift forward; negative = shift backward. For Ripple Backward "
       "the value is automatically negated so you can always enter a magnitude.",
       "Ripple Edit"),

    _H("prop.p6_insert_frames",
       "Frame Count",
       "Number of frames to insert or remove at the playhead",
       "Used by Insert Time (adds blank frames) and Remove Time (collapses a "
       "window of frames). Minimum 1.",
       "Ripple Edit"),

    # Timing Ranges
    _H("op.animassist.p6_set_range_start",
       "Set Range Start",
       "Capture the current frame as the custom range start",
       "Sets the Custom Start field to the current playhead position. Switch "
       "Range Mode to 'Custom' to make range-aware operators use this value.",
       "Timing Ranges"),

    _H("op.animassist.p6_set_range_end",
       "Set Range End",
       "Capture the current frame as the custom range end",
       "Sets the Custom End field to the current playhead position. Switch "
       "Range Mode to 'Custom' to make range-aware operators use this value.",
       "Timing Ranges"),

    _H("op.animassist.p6_select_keys_in_range",
       "Select Keys in Range",
       "Select all keyframes whose timing falls within the active range",
       "Uses whichever Range Mode is currently active (From Selection, Scene "
       "Range, or Custom). Combines naturally with Scale Range and Offset Range "
       "for surgical edits on a specific time window.",
       "Timing Ranges"),

    _H("op.animassist.p6_scale_range",
       "Scale Range",
       "Scale only the keys inside the active timing range",
       "Identical to Scale Keys but with an implicit frame_range filter applied. "
       "Keys outside the active range are completely unaffected.",
       "Timing Ranges"),

    _H("op.animassist.p6_offset_range",
       "Offset Range",
       "Shift only the keys inside the active timing range",
       "Identical to Offset Keys but with an implicit frame_range filter applied. "
       "Keys outside the active range are completely unaffected.",
       "Timing Ranges"),

    _H("op.animassist.p6_store_range",
       "Store Range",
       "Save the current range as a reusable preset on the scene",
       "The stored range survives file save and reload. Use Restore Range to "
       "recall it. Only one preset is stored at a time; calling Store Range "
       "again replaces the previous one.",
       "Timing Ranges"),

    _H("op.animassist.p6_restore_range",
       "Restore Range",
       "Load the previously stored range back into start/end",
       "Only available after Store Range has been called at least once on this "
       "scene. The Range Mode is automatically switched to Custom so the "
       "restored values take effect immediately.",
       "Timing Ranges"),

    _H("op.animassist.p6_clear_range",
       "Clear Range",
       "Reset range start/end to the scene's playback range and clear stored preset",
       "Also clears the stored range preset flag. After this operation Restore "
       "Range becomes unavailable until Store Range is called again.",
       "Timing Ranges"),

    _H("prop.p6_range_mode",
       "Range Mode",
       "How the active timing range is determined",
       "From Selection — derives the range from the frame extents of currently "
       "selected keyframes. Scene Range — uses the scene's frame_start and frame_end. "
       "Custom — uses the manually entered Start and End values. All range-aware "
       "operators (Scale Range, Offset Range, Distribute Keys, etc.) respect this "
       "setting.",
       "Timing Ranges"),

    # Gap Tools
    _H("op.animassist.p6_detect_gaps",
       "Detect Gaps",
       "Scan the active action for timing gaps wider than the threshold",
       "A gap is a contiguous window where no FCurve has a keyframe. Only gaps "
       "at least as wide as the Gap Threshold are reported. Results are stored "
       "on the scene and displayed in the diagnostics sub-panel. The Jump "
       "Next/Prev Gap operators use these cached results.",
       "Gap Tools"),

    _H("op.animassist.p6_fill_gaps",
       "Fill Gaps",
       "Insert keys into every detected gap using the chosen fill mode",
       "Constant Hold — inserts a key at the gap midpoint on every FCurve, "
       "holding the value from the key before the gap. Linear Bridge — inserts "
       "a midpoint key with LINEAR interpolation to smoothly bridge the gap. "
       "Mark Only — reports gaps without inserting any keys.",
       "Gap Tools"),

    _H("op.animassist.p6_collapse_gap",
       "Collapse Gap at Playhead",
       "Remove the gap nearest the playhead by ripple-shifting later keys",
       "Finds the detected gap whose midpoint is nearest the current frame, "
       "then ripple-shifts all keys after the gap's start frame backward by "
       "the gap's size. This closes the gap without affecting values or "
       "relative key spacing outside the collapsed region.",
       "Gap Tools"),

    _H("op.animassist.p6_distribute_keys",
       "Distribute Keys",
       "Evenly space all keys within the active range",
       "The first and last keys in the range are fixed (boundary keys stay put). "
       "All inner keys are repositioned at equal time intervals between the "
       "boundaries. Enable 'Snap to Frames' in modal preferences to round "
       "the result to integer frames.",
       "Gap Tools"),

    _H("op.animassist.p6_normalize_spacing",
       "Normalize Spacing",
       "Scale inter-key spacings toward the average spacing",
       "Each consecutive key pair's spacing is compared to the mean spacing for "
       "the range. Pairs wider than the mean are compressed; pairs narrower are "
       "expanded. This reduces spacing variance without dramatically reshuffling "
       "the animation. Multiple passes may be needed for highly irregular timing.",
       "Gap Tools"),

    _H("prop.p6_gap_threshold",
       "Gap Threshold",
       "Minimum frame gap to detect and report",
       "Gaps narrower than this value are silently ignored by Detect Gaps and "
       "Fill Gaps. Increase when working with densely keyed actions where small "
       "gaps are intentional.",
       "Gap Tools"),

    _H("prop.p6_gap_fill_mode",
       "Fill Mode",
       "How Fill Gaps inserts keys into detected gaps",
       "Constant Hold — holds the value from the key immediately before the gap. "
       "Linear Bridge — inserts a midpoint key and sets interpolation to LINEAR. "
       "Mark Only — reports the gap location without inserting any new keys.",
       "Gap Tools"),

    # Snap & Clean
    _H("op.animassist.p6_snap_to_frames",
       "Snap to Frames",
       "Round all keyframe positions to the nearest integer frame",
       "Sub-frame keyframes (e.g. frame 12.37) are nudged to the nearest whole "
       "frame. Bézier handles move by the same correction delta so the curve "
       "shape is preserved. Reports the count of keys that were moved.",
       "Snap & Clean"),

    _H("op.animassist.p6_clear_doubles",
       "Remove Duplicates",
       "Delete keyframes that share the same rounded frame as another key",
       "When two or more keys land on the same integer frame, all but the first "
       "are removed. This prevents doubled-up keys that cause interpolation "
       "glitches and inflated key counts. Useful after ripple or scale "
       "operations that may overlap keys.",
       "Snap & Clean"),

    # Modal Tools
    _H("op.animassist.p6_modal_scale",
       "Interactive Scale",
       "Drag the mouse to scale keyframe timing live",
       "Move the mouse left/right after invoking to preview timing scale changes "
       "in real-time. The scale factor is displayed in the header. "
       "LMB or Enter confirms and pushes an undo step. "
       "RMB or Esc cancels and restores original positions. "
       "Hold Shift for 0.1× precision. Hold Ctrl to snap results to whole frames.",
       "Modal Tools"),

    _H("op.animassist.p6_modal_offset",
       "Interactive Offset",
       "Drag the mouse to shift keyframe timing live",
       "Move the mouse left/right after invoking to preview offset changes in "
       "real-time. The frame delta is displayed in the header. "
       "LMB or Enter confirms and pushes an undo step. "
       "RMB or Esc cancels and restores original positions. "
       "Hold Shift for sub-frame precision. Hold Ctrl to snap to whole frames.",
       "Modal Tools"),

    _H("prop.p6_modal_snap",
       "Snap in Modal",
       "Round key positions to integer frames during interactive operations",
       "When enabled, the modal operator rounds the result to the nearest frame "
       "after each mouse move. Can also be toggled mid-operation by holding Ctrl.",
       "Modal Tools"),

    # Timing Diagnostics
    _H("op.animassist.p6_run_diagnostics",
       "Run Diagnostics",
       "Analyse the active action for gaps, clusters, and spacing regularity",
       "Scans all FCurves in the active action and reports: "
       "(1) Timing gaps wider than the Gap Threshold. "
       "(2) Key clusters tighter than the Cluster Radius. "
       "(3) A Timing Score (0–100) based on spacing variance — 100 is perfectly "
       "even spacing, 0 is maximally erratic. "
       "Results are cached on the scene for Jump operators and the report panel.",
       "Timing Diagnostics"),

    _H("op.animassist.p6_jump_next_gap",
       "Jump to Next Gap",
       "Advance the playhead to the start of the next detected timing gap",
       "Requires Detect Gaps to have been run first. Wraps around to the first "
       "gap after the last one. The gap start frame is set as the scene's "
       "current frame.",
       "Timing Diagnostics"),

    _H("op.animassist.p6_jump_prev_gap",
       "Jump to Previous Gap",
       "Rewind the playhead to the start of the previous detected timing gap",
       "Requires Detect Gaps to have been run first. Wraps around to the last "
       "gap after the first one.",
       "Timing Diagnostics"),

    _H("op.animassist.p6_jump_next_cluster",
       "Jump to Next Cluster",
       "Advance the playhead to the centre of the next detected key cluster",
       "Requires Run Diagnostics to have been run first. A cluster is a group "
       "of two or more keys within the Cluster Radius of each other. Jumps to "
       "the arithmetic centre of the cluster's frame range.",
       "Timing Diagnostics"),

    _H("op.animassist.p6_copy_diag_report",
       "Copy Diagnostics Report",
       "Copy the full diagnostics text to the system clipboard",
       "The report includes key count, frame span, average spacing, timing score, "
       "and listings of all detected gaps and clusters. Useful for pasting into "
       "production notes or sharing with collaborators.",
       "Timing Diagnostics"),

    _H("op.animassist.p6_clear_diagnostics",
       "Clear Diagnostics",
       "Reset stored diagnostic results and hide the report section",
       "Clears the gap/cluster caches and resets the timing score stored on the "
       "scene. The Jump Next/Prev Gap operators become unavailable until the "
       "next Detect Gaps run.",
       "Timing Diagnostics"),

    _H("prop.p6_cluster_radius",
       "Cluster Radius",
       "Keys within this many frames of each other form a cluster",
       "A cluster of two or more keys within this radius is flagged as potential "
       "over-keying. Adjust to match the key density of your animation style — "
       "a lower value catches very tight clusters; a higher value is more lenient.",
       "Timing Diagnostics"),
)


# ---------------------------------------------------------------------------
# Registration shim
# ---------------------------------------------------------------------------

def register() -> None:
    """Register retime help entries into the Help Browser registry.

    Called during addon initialization so retime operators and properties
    appear in the context-sensitive Help Browser documentation.
    """
    register_phase_help(_PHASE, PHASE6_ENTRIES)


def unregister() -> None:
    """Unregister retime help entries from the Help Browser registry.

    Called during addon teardown to clean up help documentation.
    """
    unregister_phase_help(_PHASE)
