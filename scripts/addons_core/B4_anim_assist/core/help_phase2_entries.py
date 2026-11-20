# --- EXPLAINER HELP INTEGRATION ---
"""Help seed entries for key diagnostics and selection operators.

One :class:`HelpEntry` per diagnostics operator (45 total). Categories follow the
five panels in the diagnostics UI so the Help Browser groups stay
aligned with the sidebar layout.
"""

from __future__ import annotations

from .help_registry import (
    HelpEntry,
    register_phase_help,
    unregister_phase_help,
)

__all__ = [
    "PHASE2_ENTRIES",
    "register",
    "unregister",
]

_PHASE = "phase2"

PHASE2_ENTRIES: tuple[HelpEntry, ...] = (
    # ====================================================================
    # Key Selection (17 ops)
    # ====================================================================
    HelpEntry(
        id="op.animassist.select_all_visible",
        label="Select All Visible Keys",
        tooltip="Select every key on every visible FCurve",
        description=(
            "Selects every key on every FCurve currently visible in the "
            "active animation editor. Hidden, muted, or filtered FCurves "
            "are skipped."
        ),
        phase=_PHASE,
        category="Key Selection",
    ),
    HelpEntry(
        id="op.animassist.deselect_all_visible",
        label="Deselect All Visible Keys",
        tooltip="Deselect every key on every visible FCurve",
        description=(
            "Clears the selection on every visible FCurve. Use this as a "
            "reset before building a new selection with the predicate "
            "operators."
        ),
        phase=_PHASE,
        category="Key Selection",
    ),
    HelpEntry(
        id="op.animassist.invert_selection",
        label="Invert Key Selection",
        tooltip="Invert the selection of keys on visible FCurves",
        description=(
            "Inverts the per-key selection state on every visible FCurve. "
            "Selected keys become deselected and vice versa."
        ),
        phase=_PHASE,
        category="Key Selection",
    ),
    HelpEntry(
        id="op.animassist.select_by_key_type_adv",
        label="Select Keys by Type",
        tooltip="Select keys whose type matches (Keyframe, Breakdown, Hold, ...)",
        description=(
            "Selects every key whose Blender key type matches the chosen "
            "value: Keyframe, Breakdown, Moving Hold, Extreme, or Jitter.\n\n"
            "Enable Extend to add to the existing selection instead of "
            "replacing it."
        ),
        phase=_PHASE,
        category="Key Selection",
    ),
    HelpEntry(
        id="op.animassist.select_by_interpolation",
        label="Select Keys by Interpolation",
        tooltip="Select keys whose interpolation matches the chosen value",
        description=(
            "Selects keys whose interpolation type matches Constant, "
            "Linear, or Bezier. Useful when reviewing curves for stepped "
            "animation passes."
        ),
        phase=_PHASE,
        category="Key Selection",
    ),
    HelpEntry(
        id="op.animassist.select_by_handle_type_adv",
        label="Select Keys by Handle Type",
        tooltip="Select keys whose left or right handle matches the chosen type",
        description=(
            "Selects keys whose left or right handle type matches Auto "
            "Clamped, Auto, Vector, Aligned, or Free."
        ),
        phase=_PHASE,
        category="Key Selection",
    ),
    HelpEntry(
        id="op.animassist.select_frame_range",
        label="Select Keys in Frame Range",
        tooltip="Select keys whose frame falls inside [start, end]",
        description=(
            "Selects every key on visible FCurves whose frame coordinate "
            "lies inside the supplied [start, end] interval (inclusive)."
        ),
        phase=_PHASE,
        category="Key Selection",
    ),
    HelpEntry(
        id="op.animassist.select_playback_range",
        label="Select Keys in Playback Range",
        tooltip="Select keys inside the scene playback range",
        description=(
            "Shortcut for Select Keys in Frame Range using the scene's "
            "frame_start and frame_end. Respects the current scene only."
        ),
        phase=_PHASE,
        category="Key Selection",
    ),
    HelpEntry(
        id="op.animassist.select_preview_range",
        label="Select Keys in Preview Range",
        tooltip="Select keys inside the scene preview range",
        description=(
            "Shortcut for Select Keys in Frame Range using the scene's "
            "frame_preview_start and frame_preview_end. Only enabled when "
            "Use Preview Range is on."
        ),
        phase=_PHASE,
        category="Key Selection",
    ),
    HelpEntry(
        id="op.animassist.select_every_nth",
        label="Select Every Nth Key",
        tooltip="Select every Nth key on each visible FCurve",
        description=(
            "Selects keys at index 0, N, 2N, ... on each visible FCurve. "
            "Use the Offset property to start the stride at a different "
            "index. Useful for thinning dense pose tests."
        ),
        phase=_PHASE,
        category="Key Selection",
    ),
    HelpEntry(
        id="op.animassist.select_neighbors",
        label="Extend Selection to Neighbours",
        tooltip="Grow the selection one step left, right, or both",
        description=(
            "Adds the immediate neighbours of every currently-selected key "
            "to the selection. Direction can be Left, Right, or Both."
        ),
        phase=_PHASE,
        category="Key Selection",
    ),
    HelpEntry(
        id="op.animassist.select_between_selected",
        label="Select Between First/Last Selected",
        tooltip="Select every key between the earliest and latest selected key",
        description=(
            "Computes the bounding frame interval of the current selection "
            "and selects every key inside that interval. Reports a warning "
            "if nothing is currently selected."
        ),
        phase=_PHASE,
        category="Key Selection",
    ),
    HelpEntry(
        id="op.animassist.select_first_last",
        label="Select First/Last Keys",
        tooltip="Select the endpoint keys on each visible FCurve",
        description=(
            "Selects only the first key, the last key, or both endpoints "
            "of every visible FCurve. Use this to grab anchor poses "
            "without dragging through the timeline."
        ),
        phase=_PHASE,
        category="Key Selection",
    ),
    HelpEntry(
        id="op.animassist.select_local_extremes",
        label="Select Local Extremes",
        tooltip="Select keys that are local minima or maxima on their curve",
        description=(
            "Walks each visible FCurve and selects every key whose value "
            "is strictly greater (peak) or strictly less (valley) than "
            "both immediate neighbours. Endpoints are included if they "
            "differ from their single neighbour."
        ),
        phase=_PHASE,
        category="Key Selection",
    ),
    HelpEntry(
        id="op.animassist.select_flat_segments",
        label="Select Keys in Flat Segments",
        tooltip="Select keys belonging to a near-flat segment",
        description=(
            "Selects keys whose value matches at least one neighbour "
            "within the supplied tolerance. Use this to identify hold "
            "regions inside otherwise active curves."
        ),
        phase=_PHASE,
        category="Key Selection",
    ),
    HelpEntry(
        id="op.animassist.select_by_value_range",
        label="Select Keys by Value Range",
        tooltip="Select keys whose value falls inside [Min, Max]",
        description=(
            "Selects every key whose Y value lies inside the supplied "
            "value range. Min and Max are sorted automatically. Enable "
            "Extend to add to the current selection."
        ),
        phase=_PHASE,
        category="Key Selection",
    ),
    HelpEntry(
        id="op.animassist.select_by_tag",
        label="Select Keys by Tag",
        tooltip="Select every key whose metadata tag exactly matches",
        description=(
            "Looks up every key against the per-scene metadata registry "
            "and selects those whose stored tag exactly equals the "
            "supplied string. Empty tag selects nothing."
        ),
        phase=_PHASE,
        category="Key Selection",
    ),
    HelpEntry(
        id="op.animassist.select_protected",
        label="Select Protected Keys",
        tooltip="Select keys flagged as protected (or invert)",
        description=(
            "Selects every key whose metadata record carries the "
            "Protected flag. Toggle Invert to select unprotected keys "
            "instead.\n\n"
            "Protected keys are exempted from Safe Delete."
        ),
        phase=_PHASE,
        category="Key Selection",
    ),

    # ====================================================================
    # Channel Isolation (5 ops)
    # ====================================================================
    HelpEntry(
        id="op.animassist.isolate_selected_channels",
        label="Isolate Selected Channels",
        tooltip="Hide every FCurve except the ones currently selected",
        description=(
            "Hides every FCurve in the active editor whose select flag "
            "is False, leaving only the currently selected curves "
            "visible. Restore the previous state with Restore Channel "
            "Isolation State."
        ),
        phase=_PHASE,
        category="Channel Isolation",
    ),
    HelpEntry(
        id="op.animassist.isolate_transform",
        label="Isolate Transform Channels",
        tooltip="Hide every FCurve except the chosen transform group",
        description=(
            "Filters visible FCurves to one transform group: Location, "
            "Rotation, Scale, or all three combined. Curves on custom "
            "properties or constraints are hidden."
        ),
        phase=_PHASE,
        category="Channel Isolation",
    ),
    HelpEntry(
        id="op.animassist.isolate_selected_bones",
        label="Isolate Selected Bones",
        tooltip="Hide every FCurve that does not belong to a selected pose bone",
        description=(
            "Restricted to armature objects. Hides every FCurve whose "
            "data path does not target one of the currently selected "
            "pose bones."
        ),
        phase=_PHASE,
        category="Channel Isolation",
    ),
    HelpEntry(
        id="op.animassist.isolate_custom_props",
        label="Isolate Custom Properties",
        tooltip="Hide every FCurve except those targeting custom properties",
        description=(
            "Hides every FCurve except those whose data path targets a "
            "custom (ID) property — useful when tuning rig sliders."
        ),
        phase=_PHASE,
        category="Channel Isolation",
    ),
    HelpEntry(
        id="op.animassist.isolate_by_regex",
        label="Isolate Channels by Regex",
        tooltip="Hide every FCurve whose data path does not match a regex",
        description=(
            "Hides every FCurve whose data_path string does not match "
            "the supplied Python regular expression. Compilation errors "
            "are reported and the operation is cancelled."
        ),
        phase=_PHASE,
        category="Channel Isolation",
    ),

    # ====================================================================
    # Channel Filtering (5 ops)
    # ====================================================================
    HelpEntry(
        id="op.animassist.show_all_channels",
        label="Show All Channels",
        tooltip="Unhide every FCurve in the active editor",
        description=(
            "Sets fc.hide = False on every FCurve reachable through the "
            "active animation editor. Resets any previous isolation."
        ),
        phase=_PHASE,
        category="Channel Filtering",
    ),
    HelpEntry(
        id="op.animassist.invert_channel_visibility",
        label="Invert Channel Visibility",
        tooltip="Flip the hide flag on every FCurve",
        description=(
            "Toggles fc.hide on every visible FCurve. Hidden becomes "
            "visible and vice versa."
        ),
        phase=_PHASE,
        category="Channel Filtering",
    ),
    HelpEntry(
        id="op.animassist.mute_unselected_channels",
        label="Mute Unselected Channels",
        tooltip="Mute every FCurve except the currently selected ones",
        description=(
            "Sets fc.mute on every FCurve whose select flag is False, "
            "leaving the selected curves audible. Use this for solo-style "
            "evaluation tests."
        ),
        phase=_PHASE,
        category="Channel Filtering",
    ),
    HelpEntry(
        id="op.animassist.push_channel_isolation",
        label="Save Channel Isolation State",
        tooltip="Push the current hide/select state onto the isolation stack",
        description=(
            "Snapshots every FCurve's hide and select state and pushes "
            "the snapshot onto an internal stack so you can restore it "
            "later with Restore Channel Isolation State."
        ),
        phase=_PHASE,
        category="Channel Filtering",
    ),
    HelpEntry(
        id="op.animassist.pop_channel_isolation",
        label="Restore Channel Isolation State",
        tooltip="Pop the last saved isolation snapshot off the stack",
        description=(
            "Restores hide and select on every FCurve to the most "
            "recently pushed snapshot. Reports a warning if the stack is "
            "empty."
        ),
        phase=_PHASE,
        category="Channel Filtering",
    ),

    # ====================================================================
    # Key Metadata (7 ops)
    # ====================================================================
    HelpEntry(
        id="op.animassist.tag_selected_keys",
        label="Tag Selected Keys",
        tooltip="Stamp a string tag onto every selected key",
        description=(
            "Writes the supplied tag string into the per-scene metadata "
            "record for every selected key. Empty tag is rejected. Use "
            "Select Keys by Tag to query the result later."
        ),
        phase=_PHASE,
        category="Key Metadata",
    ),
    HelpEntry(
        id="op.animassist.clear_tag_selected_keys",
        label="Clear Tags on Selected Keys",
        tooltip="Erase the tag field on every selected key",
        description=(
            "Sets the tag field to an empty string on every selected "
            "key's metadata record. Other metadata fields (note, flavor, "
            "protected) are left untouched."
        ),
        phase=_PHASE,
        category="Key Metadata",
    ),
    HelpEntry(
        id="op.animassist.set_key_note",
        label="Set Note on Selected Keys",
        tooltip="Attach a free-form note to every selected key",
        description=(
            "Stores the supplied note string in the metadata record of "
            "every selected key. Notes are free-form and intended for "
            "human-readable annotations."
        ),
        phase=_PHASE,
        category="Key Metadata",
    ),
    HelpEntry(
        id="op.animassist.set_key_flavor",
        label="Set Key Flavor",
        tooltip="Stamp a 'flavor' tag onto every selected key",
        description=(
            "Stores the supplied flavor string on every selected key. "
            "Flavor is a secondary tag axis distinct from the main tag, "
            "intended for keying-pass labels such as 'block', 'spline', "
            "or 'polish'."
        ),
        phase=_PHASE,
        category="Key Metadata",
    ),
    HelpEntry(
        id="op.animassist.protect_selected_keys",
        label="Protect / Unprotect Selected Keys",
        tooltip="Mark selected keys as protected from Safe Delete",
        description=(
            "Toggles the Protected flag on every selected key's metadata "
            "record. Protected keys are skipped by Safe Delete and shown "
            "in their own selection filter.\n\n"
            "The same operator runs both Protect and Unprotect via the "
            "'protected' boolean property; the panel exposes both as "
            "separate buttons."
        ),
        phase=_PHASE,
        category="Key Metadata",
    ),
    HelpEntry(
        id="op.animassist.prune_orphan_key_metadata",
        label="Prune Orphan Key Metadata",
        tooltip="Drop metadata whose keyframe no longer exists",
        description=(
            "Walks every metadata record and removes those whose "
            "(object, data_path, array_index, frame) identity no longer "
            "matches a real keyframe. Run after large key edits or "
            "object renames."
        ),
        phase=_PHASE,
        category="Key Metadata",
    ),
    HelpEntry(
        id="op.animassist.clear_all_key_metadata",
        label="Clear All Key Metadata",
        tooltip="Remove every key metadata record from the current scene",
        description=(
            "Empties the per-scene metadata collection. Tags, notes, "
            "flavors and protection flags are all wiped. There is no "
            "undo for this — only the operator's own undo step."
        ),
        phase=_PHASE,
        category="Key Metadata",
    ),

    # ====================================================================
    # Key Analysis (3 ops)
    # ====================================================================
    HelpEntry(
        id="op.animassist.scan_dense_keys",
        label="Scan Dense Keys",
        tooltip="Select keys closer than the configured min gap to a neighbour",
        description=(
            "Scans every visible FCurve for adjacent keys whose frame "
            "gap is below the supplied min_gap. Hits are selected and a "
            "summary is stored for the panel readout."
        ),
        phase=_PHASE,
        category="Key Analysis",
    ),
    HelpEntry(
        id="op.animassist.scan_redundant_keys",
        label="Scan Redundant Keys",
        tooltip="Select keys that lie on a straight line between neighbours",
        description=(
            "Flags any key whose value is within the supplied tolerance "
            "of the linear interpolation between its two immediate "
            "neighbours. Useful for cleaning up over-keyed curves."
        ),
        phase=_PHASE,
        category="Key Analysis",
    ),
    HelpEntry(
        id="op.animassist.scan_spike_keys",
        label="Scan Spike Keys",
        tooltip="Select keys whose value deviates sharply from their neighbours",
        description=(
            "Flags any key whose deviation from the local smoothed curve "
            "exceeds the supplied ratio compared to the median neighbour "
            "deviation. Hits are selected and counted."
        ),
        phase=_PHASE,
        category="Key Analysis",
    ),

    # ====================================================================
    # Key Editing (8 ops)
    # ====================================================================
    HelpEntry(
        id="op.animassist.copy_selected_keys",
        label="Copy Selected Keys",
        tooltip="Copy the selected keys (frame, value, handles) to the clipboard",
        description=(
            "Stores every selected key's frame, value and both handles "
            "in an in-process clipboard. Subsequent Paste operators read "
            "from this clipboard."
        ),
        phase=_PHASE,
        category="Key Editing",
    ),
    HelpEntry(
        id="op.animassist.paste_keys_at_frame",
        label="Paste Keys at Frame",
        tooltip="Paste clipboard keys with an optional frame offset",
        description=(
            "Inserts every key from the in-process clipboard at its "
            "original frame plus the supplied frame_offset. Existing "
            "keys at the target frames are overwritten. Reports a "
            "warning if the clipboard is empty."
        ),
        phase=_PHASE,
        category="Key Editing",
    ),
    HelpEntry(
        id="op.animassist.offset_selected_frames",
        label="Offset Selected Keys (Frame)",
        tooltip="Shift every selected key by dx frames",
        description=(
            "Adds dx to the X coordinate of every selected key. Handles "
            "are translated together so curve shape is preserved. Only "
            "FCurves that actually changed get fc.update() called."
        ),
        phase=_PHASE,
        category="Key Editing",
    ),
    HelpEntry(
        id="op.animassist.offset_selected_values",
        label="Offset Selected Keys (Value)",
        tooltip="Shift every selected key by dy on the Y axis",
        description=(
            "Adds dy to the Y coordinate of every selected key. Handles "
            "are translated together so curve shape is preserved."
        ),
        phase=_PHASE,
        category="Key Editing",
    ),
    HelpEntry(
        id="op.animassist.snap_keys_to_integer_frames",
        label="Snap Selected Keys to Integer Frames",
        tooltip="Round every selected key's frame to the nearest integer",
        description=(
            "Rounds every selected key's X coordinate to the nearest "
            "integer frame and translates its handles by the same delta "
            "so the curve shape stays intact."
        ),
        phase=_PHASE,
        category="Key Editing",
    ),
    HelpEntry(
        id="op.animassist.mirror_selected_keys",
        label="Mirror Selected Keys at Current Frame",
        tooltip="Mirror selected keys around the current playhead frame",
        description=(
            "Reflects every selected key across the current frame on "
            "the X axis. Handle X positions are swapped relative to the "
            "pivot and handle Y values are swapped between left and "
            "right so bezier curvature stays correct."
        ),
        phase=_PHASE,
        category="Key Editing",
    ),
    HelpEntry(
        id="op.animassist.safe_delete_selected_keys",
        label="Safe Delete Selected Keys",
        tooltip="Delete selected keys except those marked Protected",
        description=(
            "Walks the current selection, skips any key whose metadata "
            "carries the Protected flag, and removes the rest. Reports "
            "the number deleted and the number skipped."
        ),
        phase=_PHASE,
        category="Key Editing",
    ),
)


def register() -> int:
    """Register every diagnostics help entry. Returns the count inserted."""
    return register_phase_help(_PHASE, PHASE2_ENTRIES)


def unregister() -> int:
    """Remove every diagnostics help entry. Returns the count removed."""
    return unregister_phase_help(_PHASE)
