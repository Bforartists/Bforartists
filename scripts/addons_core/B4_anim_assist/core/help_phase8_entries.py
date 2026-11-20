# --- MATCHING AND SPACE SWITCHING HELP ENTRIES ---
"""Help entries for matching workflows, space switching, and pose compensation.

Provides 54 HelpEntry records covering all matching and switching features, organized
into 8 categories that align with the panel section structure.
"""

from __future__ import annotations

from .help_registry import HelpEntry, register_phase_help, unregister_phase_help

__all__ = [
    "PHASE8_ENTRIES",
    "register",
    "unregister",
]

_PHASE = "phase8"


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
# Categories:
#   Transform Matching, Space Switching, Switch Compensation,
#   Switch Baking, Rig Detection, Switch History,
#   Contact Preservation, Switch Presets
# ---------------------------------------------------------------------------

PHASE8_ENTRIES: tuple[HelpEntry, ...] = (
    # ── Transform Matching ─────────────────────────────────────────────
    _H(
        "op.animassist.p8_match_to_world",
        "Match to World",
        "Match the active object's transform to world origin",
        "Resets the active control so its visual world-space transform "
        "matches the scene origin (identity matrix).  Useful for zeroing "
        "out a control relative to world space.  Respects channel filters "
        "and lock settings.",
        "Transform Matching",
    ),
    _H(
        "op.animassist.p8_match_to_parent",
        "Match to Parent",
        "Match the active object's transform to its parent",
        "Sets the active control's local transform to identity so it sits "
        "exactly at its parent's position and orientation.  Equivalent to "
        "zeroing the local offset.",
        "Transform Matching",
    ),
    _H(
        "op.animassist.p8_match_to_target",
        "Match to Target",
        "Match the active object to another selected object",
        "Snaps the active object's visual transform to match the other "
        "selected object's world-space pose.  Requires exactly two objects "
        "selected: the active is the target, the other is the source.",
        "Transform Matching",
    ),
    _H(
        "op.animassist.p8_match_selected_to_active",
        "Match Selected to Active",
        "Match all selected objects to the active object's transform",
        "Batch-matches every selected object (except the active) so they "
        "all share the active object's visual world-space pose.  Useful "
        "for snapping multiple controls to one reference.",
        "Transform Matching",
    ),
    _H(
        "op.animassist.p8_visual_match",
        "Visual Transform Match",
        "Match using the fully evaluated depsgraph visual matrix",
        "Performs the match using the depsgraph-evaluated visual matrix, "
        "which accounts for all constraints, drivers, and modifiers.  This "
        "is the most accurate match mode for constrained rigs.",
        "Transform Matching",
    ),
    _H(
        "op.animassist.p8_match_location",
        "Location Match",
        "Match location channels only",
        "Matches only the position (XYZ location) of the target to the "
        "source, leaving rotation and scale unchanged.  Respects per-axis "
        "filtering and transform locks.",
        "Transform Matching",
    ),
    _H(
        "op.animassist.p8_match_rotation",
        "Rotation Match",
        "Match rotation channels only",
        "Matches only the orientation (Euler rotation) of the target to "
        "the source, leaving location and scale unchanged.",
        "Transform Matching",
    ),
    _H(
        "op.animassist.p8_match_scale",
        "Scale Match",
        "Match scale channels only",
        "Matches only the scale of the target to the source, leaving "
        "location and rotation unchanged.",
        "Transform Matching",
    ),
    _H(
        "op.animassist.p8_match_trs",
        "Full TRS Match",
        "Match all transform channels (location, rotation, scale)",
        "Performs a complete transform match covering all channels.  This "
        "is the default match mode that snaps the target to the source "
        "across all axes and all transform types.",
        "Transform Matching",
    ),
    _H(
        "op.animassist.p8_match_axis_filtered",
        "Axis-Filtered Match",
        "Match with per-axis filtering from the axis toggle checkboxes",
        "Uses the X/Y/Z axis checkboxes in the panel to selectively match "
        "only certain axes.  Combined with the channel mode, this gives "
        "fine-grained control over which components are affected.",
        "Transform Matching",
    ),
    _H(
        "op.animassist.p8_match_with_offset",
        "Match with Offset",
        "Match while preserving the existing spatial offset",
        "Computes the match but preserves the original offset between the "
        "source and target.  Useful when you want to maintain relative "
        "positioning while updating the match relationship.",
        "Transform Matching",
    ),
    _H(
        "op.animassist.p8_match_without_offset",
        "Match without Offset",
        "Match by snapping exactly to the source with no offset",
        "Forces an exact snap to the source transform with zero offset, "
        "regardless of the Maintain Offset checkbox state.  Use this for "
        "a one-shot precise alignment.",
        "Transform Matching",
    ),

    # ── Space Switching ────────────────────────────────────────────────
    _H(
        "op.animassist.p8_compensate_single",
        "Single-Frame Compensation",
        "Change a space-switch property and compensate on this frame",
        "Records the control's visual world matrix, changes the specified "
        "switch property, forces a depsgraph update, then computes and "
        "applies the local transform that recovers the original visual "
        "result.  Optionally inserts keyframes on both the switch property "
        "and the compensated transform channels.",
        "Space Switching",
    ),
    _H(
        "op.animassist.p8_compensate_multi",
        "Multi-Frame Compensation",
        "Compensate a space switch across a range of frames",
        "Applies single-frame compensation at every frame in the selected "
        "range.  For each frame: moves playhead, records visual state, "
        "applies switch, updates depsgraph, compensates, and keys.  "
        "Restores the playhead to the original frame when done.",
        "Space Switching",
    ),
    _H(
        "op.animassist.p8_switch_enum",
        "Switch Enum Property",
        "Switch an integer or enum custom property with compensation",
        "Changes a detected enum/integer switch property to a specified "
        "value and immediately compensates the transform to prevent visual "
        "popping.  The new value is passed as an operator property.",
        "Space Switching",
    ),
    _H(
        "op.animassist.p8_switch_bool",
        "Switch Boolean Property",
        "Toggle a boolean switch property with compensation",
        "Flips a boolean (0/1) custom property (typically a follow or "
        "IK/FK toggle) and compensates the visual transform.  Reads the "
        "current value and sets it to the opposite.",
        "Space Switching",
    ),
    _H(
        "op.animassist.p8_switch_influence",
        "Switch Influence Property",
        "Set a constraint influence value with compensation",
        "Changes a constraint's influence (0.0–1.0) and compensates the "
        "resulting transform change.  Useful for blending between "
        "constraint targets (e.g. Child Of, Copy Transforms).",
        "Space Switching",
    ),
    _H(
        "op.animassist.p8_restore_switch",
        "Restore Previous Switch",
        "Undo the last switch by restoring its previous value",
        "Reads the most recent switch event from history and reverses it "
        "by setting the property back to its old value, then compensates.  "
        "Acts like a targeted undo for the switch operation.",
        "Space Switching",
    ),
    _H(
        "op.animassist.p8_toggle_preview",
        "Switch Preview Mode",
        "Toggle preview mode for switch operations",
        "When enabled, switch operations show a preview of the result "
        "without committing.  Disabling preview mode restores the original "
        "state.  Useful for testing different switch values.",
        "Space Switching",
    ),

    # ── Switch Compensation ────────────────────────────────────────────
    _H(
        "prop.p8_auto_compensate",
        "Auto Compensate",
        "Automatically compensate transforms when switching spaces",
        "When enabled, any switch operation automatically records the "
        "visual matrix beforehand and applies compensation afterward.  "
        "Disable this to perform raw switches without compensation.",
        "Switch Compensation",
    ),
    _H(
        "prop.p8_auto_key_switch",
        "Auto-Key Compensated Channels",
        "Insert keyframes on compensated channels after a switch",
        "Automatically inserts keyframes on both the switch property and "
        "all compensated transform channels.  Requires Blender's auto-key "
        "to be independent of this setting — this controls only matching"
        "switch-specific keying.",
        "Switch Compensation",
    ),
    _H(
        "prop.p8_respect_locks",
        "Respect Locked Transforms",
        "Skip locked transform channels during matching and compensation",
        "Prevents the match or compensation from overriding channels the "
        "animator has explicitly locked.  Locked axes are silently skipped "
        "rather than producing an error.",
        "Switch Compensation",
    ),
    _H(
        "prop.p8_respect_drivers",
        "Respect Driven Channels",
        "Skip driven or constrained channels during matching",
        "Avoids overwriting transform channels that are controlled by "
        "drivers.  Writing to driven channels can cause dependency cycles "
        "or unexpected behavior.",
        "Switch Compensation",
    ),
    _H(
        "prop.p8_match_channels",
        "Match Channels",
        "Select which transform channels to include in operations",
        "Controls whether matching and compensation affect all channels, "
        "location only, rotation only, scale only, or location+rotation.  "
        "Combined with per-axis toggles for precise control.",
        "Switch Compensation",
    ),
    _H(
        "prop.p8_match_axis",
        "Axis Filter",
        "Per-axis X/Y/Z toggle for matching operations",
        "Enable or disable individual axes for matching.  When used with "
        "the axis-filtered match operator, only checked axes are affected.  "
        "Useful for constraining a match to a single plane or axis.",
        "Switch Compensation",
    ),

    # ── Switch Baking ──────────────────────────────────────────────────
    _H(
        "op.animassist.p8_bake_switch_range",
        "Bake Switch (Selected Range)",
        "Bake compensation across selected keyframes",
        "Identifies the frame range of selected keyframes, applies the "
        "switch property change, and bakes compensation at every frame "
        "in that range.  Produces clean animation across the transition.",
        "Switch Baking",
    ),
    _H(
        "op.animassist.p8_bake_switch_preview",
        "Bake Switch (Preview Range)",
        "Bake compensation across the preview/playback range",
        "Uses the scene's preview range (or full scene range) and bakes "
        "compensation at every frame.  Ideal for processing an entire "
        "shot's worth of space-switch animation.",
        "Switch Baking",
    ),
    _H(
        "op.animassist.p8_batch_switch",
        "Batch Switch",
        "Apply a switch with compensation to all selected objects at once",
        "Iterates through every selected object, applies the configured "
        "switch property change, and compensates each one independently.  "
        "Handles per-target bone resolution when a bone name is specified.",
        "Switch Baking",
    ),
    _H(
        "op.animassist.p8_switch_marker",
        "Switch Marker",
        "Place a timeline marker at the current frame to mark a switch point",
        "Adds a named marker to the timeline at the playhead position.  "
        "Markers serve as visual reference points for where space switches "
        "occur in the animation.",
        "Switch Baking",
    ),

    # ── Rig Detection ──────────────────────────────────────────────────
    _H(
        "op.animassist.p8_detect_space_enums",
        "Detect Space Enums",
        "Scan the active rig for custom enum properties that look like space switches",
        "Examines object-level and pose-bone custom properties whose names "
        "contain keywords like 'space', 'switch', 'parent', or 'follow'.  "
        "Results are ranked by confidence and cached for the panel list.",
        "Rig Detection",
    ),
    _H(
        "op.animassist.p8_detect_parent_patterns",
        "Detect Parent Patterns",
        "Scan for boolean properties that toggle parent spaces",
        "Looks for 0/1 custom properties on bones that suggest parent-space "
        "toggles (e.g. IK/FK switches, follow toggles).",
        "Rig Detection",
    ),
    _H(
        "op.animassist.p8_detect_influence_patterns",
        "Detect Influence Patterns",
        "Scan constraints for influence-based space switching",
        "Identifies Child Of, Copy Transforms, and similar constraints "
        "whose influence values may be used as space switches.  Scores "
        "higher when constraint names contain switch keywords.",
        "Rig Detection",
    ),
    _H(
        "op.animassist.p8_detect_custom_props",
        "Detect Custom Properties",
        "Broad scan for any numeric custom properties on the rig",
        "Catch-all detector that finds all numeric custom properties.  "
        "Lower confidence than specific detectors but ensures nothing is "
        "missed on custom rigs.",
        "Rig Detection",
    ),
    _H(
        "op.animassist.p8_detect_all",
        "Detect All Patterns",
        "Run all rig pattern detectors at once",
        "Combines enum, boolean, influence, and custom-property detection "
        "into a single pass.  Deduplicates results and ranks by confidence.  "
        "This is the recommended starting point for new rigs.",
        "Rig Detection",
    ),
    _H(
        "op.animassist.p8_apply_detected_pattern",
        "Apply Detected Pattern",
        "Apply the selected detected pattern to the switch settings",
        "Copies the detected pattern's property path, bone name, and switch "
        "type into the matchingsettings so you can immediately use the "
        "compensation and switching tools with that pattern.",
        "Rig Detection",
    ),
    _H(
        "op.animassist.p8_debug_diagnostics",
        "Debug Diagnostics",
        "Run detailed diagnostic analysis on the active rig",
        "Generates a comprehensive report including constraint types, driver "
        "count, custom property inventory, and bone hierarchy analysis.  "
        "Copies the report to the clipboard for sharing with TD support.",
        "Rig Detection",
    ),

    # ── Switch History ─────────────────────────────────────────────────
    _H(
        "op.animassist.p8_nav_next_switch",
        "Next Switch Event",
        "Jump the playhead to the next switch event in the history",
        "Finds the first recorded switch event after the current frame "
        "and moves the playhead there.  Skips forward through the timeline "
        "switch-by-switch.",
        "Switch History",
    ),
    _H(
        "op.animassist.p8_nav_prev_switch",
        "Previous Switch Event",
        "Jump the playhead to the previous switch event in the history",
        "Finds the last recorded switch event before the current frame "
        "and moves the playhead there.",
        "Switch History",
    ),
    _H(
        "op.animassist.p8_clear_history",
        "Clear Switch History",
        "Remove all recorded switch events from the history stack",
        "Wipes the ephemeral switch history.  This cannot be undone.  "
        "History is session-only and does not survive file save/reload.",
        "Switch History",
    ),
    _H(
        "op.animassist.p8_repeat_last_switch",
        "Repeat Last Switch",
        "Re-apply the most recent switch operation at the current frame",
        "Reads the last switch event from history and performs the same "
        "property change with compensation at the current playhead frame.  "
        "Useful for applying the same space switch at different frames.",
        "Switch History",
    ),

    # ── Contact Preservation ───────────────────────────────────────────
    _H(
        "prop.p8_contact_preserve",
        "Contact Preservation",
        "Preserve hand and foot contact during multi-frame compensation",
        "When enabled, the compensation algorithm records contact-bone "
        "world positions and blends the result to keep those bones planted.  "
        "Reduces sliding on IK hands and feet during space switches.",
        "Contact Preservation",
    ),
    _H(
        "prop.p8_contact_mask",
        "Contact Mask",
        "Comma-separated list of bone names treated as contact points",
        "Specify which bones should be considered contact points.  Typical "
        "values: foot_ik_L, foot_ik_R, hand_ik_L, hand_ik_R.  Use the "
        "'Mask from Selection' button to populate from selected bones.",
        "Contact Preservation",
    ),
    _H(
        "op.animassist.p8_contact_preserve_match",
        "Contact-Preserving Match",
        "Match while keeping contact bones planted",
        "Performs a standard match on the target but then adjusts the "
        "result so that contact-mask bones maintain their world positions.  "
        "Requires contact preservation to be enabled with at least one bone "
        "in the mask.",
        "Contact Preservation",
    ),
    _H(
        "op.animassist.p8_contact_mask_from_selection",
        "Mask from Selection",
        "Set the contact mask from currently selected bones",
        "In Pose mode, reads the names of all selected pose bones and "
        "writes them as a comma-separated list into the contact mask field.  "
        "Quick alternative to manually typing bone names.",
        "Contact Preservation",
    ),

    # ── Switch Presets ─────────────────────────────────────────────────
    _H(
        "op.animassist.p8_save_switch_preset",
        "Save Switch Preset",
        "Save current switch configuration as a reusable preset",
        "Stores the current property path, bone name, switch type, and "
        "default value as a named preset on the scene.  Presets persist "
        "with the .blend file and can be shared between shots.",
        "Switch Presets",
    ),
    _H(
        "op.animassist.p8_load_switch_preset",
        "Load Switch Preset",
        "Load a previously saved switch configuration preset",
        "Applies the stored property path, bone name, switch type, and "
        "default value from the named preset back into the matching"
        "settings panel.",
        "Switch Presets",
    ),
    _H(
        "op.animassist.p8_delete_switch_preset",
        "Delete Switch Preset",
        "Remove a saved switch preset from the scene",
        "Permanently deletes the named preset from the scene's stored "
        "presets.  This cannot be undone.",
        "Switch Presets",
    ),
    _H(
        "op.animassist.p8_compensation_report",
        "Compensation Report",
        "Generate a report of recent switch and compensation activity",
        "Summarizes all switch events in the history stack, listing frames, "
        "properties changed, old and new values, and channels compensated.  "
        "Copies the report to the clipboard.",
        "Switch Presets",
    ),
    _H(
        "op.animassist.p8_unsupported_warning",
        "Unsupported Setup Check",
        "Check the active rig for setups that may not compensate cleanly",
        "Scans for potential issues: missing animation data, complex "
        "constraint stacks, drivers on transform channels, and locked "
        "transforms.  Reports warnings so the user can work around them.",
        "Switch Presets",
    ),
    _H(
        "op.animassist.p8_quick_match",
        "Quick Match",
        "One-click match with default settings at the current frame",
        "Performs a full TRS visual match from the source to the active "
        "object using default channel settings.  Auto-keys if the auto-key "
        "option is enabled.  The fastest way to snap-match two objects.",
        "Transform Matching",
    ),
    _H(
        "op.animassist.p8_match_visual_matrix",
        "Match Visual Matrix",
        "Match using the depsgraph-evaluated visual world matrix",
        "Explicitly uses the evaluated depsgraph for both source and target "
        "matrices.  Accounts for all constraints and drivers in the rig "
        "hierarchy.  This is the most accurate match mode.",
        "Transform Matching",
    ),
    _H(
        "op.animassist.p8_match_local_matrix",
        "Match Local Matrix",
        "Match using the unevaluated local matrix of the source",
        "Uses the source object's local matrix (pre-constraint) as the "
        "match target.  Useful when you want to match the authored "
        "transform rather than the visual result.",
        "Transform Matching",
    ),
    _H(
        "op.animassist.p8_match_opposite",
        "Match Opposite Side",
        "Match to the mirrored bone on the opposite side of the rig",
        "Finds the opposite-side bone by mirror-naming convention "
        "(L↔R, Left↔Right) and matches the active bone to it.  Only "
        "available in Pose mode with a valid mirror naming pattern.",
        "Transform Matching",
    ),
)


def register() -> None:
    """Register matching help entries into the Help Browser registry.

    Called during addon initialization so matching operators and properties
    appear in the context-sensitive Help Browser documentation.
    """
    register_phase_help(_PHASE, PHASE8_ENTRIES)


def unregister() -> None:
    """Unregister matching help entries from the Help Browser registry.

    Called during addon teardown to clean up help documentation.
    """
    unregister_phase_help(_PHASE)
