# --- TEMP CONTROLS AND PROXY WORKFLOWS ---
"""Help / explainer entries for temporary controls and proxy constraints.

45 ``HelpEntry`` records organised into 8 categories:

  1. Temp Locators       — Temporary control creation and management
  2. Proxy Constraints   — Constraint-based proxy workflows
  3. Proxy Display       — Proxy visualization and drawing
  4. Session Management  — Session save/restore and persistence
  5. Bake Workflows      — Baking and consolidation
  6. Proxy Cleanup       — Cleanup and removal
  7. Batch Proxy         — Batch proxy operations
  8. One-Click Workflows — Automated workflows
"""

from __future__ import annotations

from .help_registry import (
    HelpEntry,
    register_phase_help,
    unregister_phase_help,
)

__all__ = [
    "PHASE7_ENTRIES",
    "register",
    "unregister",
]

_PHASE = "phase7"


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
# All 45 entries
# ---------------------------------------------------------------------------

PHASE7_ENTRIES: tuple[HelpEntry, ...] = (

    # ===== Temp Locators (Features 1-10) =====

    # Feature 1
    _H("op.animassist.p7_create_locator",
       "Create Locator",
       "Create an empty at the active object or bone's position",
       "Adds a plain-axes empty snapped to the active object's world-space "
       "position (or the active bone's head if an armature bone is selected). "
       "The locator is tagged as a temporarytemporary artifact and tracked by "
       "the active session.",
       "Temp Locators"),

    # Feature 2
    _H("op.animassist.p7_create_locator_average",
       "Locator at Average",
       "Create a locator at the average position of all selected objects",
       "Computes the centroid of every selected object's world position and "
       "places a new locator empty there. Useful for finding the centre of "
       "a group of controls.",
       "Temp Locators"),

    # Feature 3
    _H("op.animassist.p7_create_locator_cursor",
       "Locator at Cursor",
       "Create a locator at the 3D cursor position",
       "Places a new locator empty at the exact position of the 3D cursor. "
       "Allows manual placement independent of any selected object.",
       "Temp Locators"),

    # Feature 4
    _H("op.animassist.p7_parent_locator",
       "Parent to Locator",
       "Parent the active object to the most recently created locator",
       "Sets the locator as the active object's parent without affecting "
       "the object's world transform (uses Blender's 'keep transform' "
       "parent mode).",
       "Temp Locators"),

    # Feature 5
    _H("op.animassist.p7_constrain_target_to_locator",
       "Constrain Target → Locator",
       "Add a Copy Location constraint on the target aimed at the locator",
       "Injects a Copy Location constraint on the active object (or active "
       "pose bone) with the locator as target. The constraint is named with "
       "the session prefix so it can be cleaned up on rollback.",
       "Temp Locators"),

    # Feature 6
    _H("op.animassist.p7_constrain_locator_to_target",
       "Constrain Locator → Target",
       "Add a Copy Location constraint on the locator aimed at the target",
       "Injects a Copy Location constraint on the session's locator with "
       "the active object as target. The locator then follows the target.",
       "Temp Locators"),

    # Feature 7
    _H("op.animassist.p7_bake_locator_from_target",
       "Bake Locator from Target",
       "Bake the target's world position onto the locator as keyframes",
       "Iterates over the bake frame range, evaluating the active object's "
       "world matrix at each frame and inserting location keyframes on the "
       "target locator.",
       "Temp Locators"),

    # Feature 8
    _H("op.animassist.p7_bake_target_from_locator",
       "Bake Target from Locator",
       "Bake the locator's position onto the target as keyframes",
       "Iterates over the bake frame range, sampling the locator's world "
       "position and inserting keyframes on the active object's location "
       "channels.",
       "Temp Locators"),

    # Feature 9
    _H("op.animassist.p7_match_target_to_locator",
       "Match Target → Locator",
       "Snap the target's transform to match the locator at the current frame",
       "Copies world-space location from the session locator to the active "
       "object at the current frame. No keyframe is inserted automatically.",
       "Temp Locators"),

    # Feature 10
    _H("op.animassist.p7_match_locator_to_target",
       "Match Locator → Target",
       "Snap the locator to match the target's current position",
       "Reads the active object's world matrix at the current frame and "
       "sets the locator's location to match.",
       "Temp Locators"),

    # ===== Proxy Constraints (Features 11-19) =====

    # Feature 11
    _H("op.animassist.p7_create_proxy.ORIENTATION",
       "Orientation Proxy",
       "Proxy that mirrors the target's rotation via Copy Rotation",
       "Creates a single-arrow empty and adds a Copy Rotation constraint "
       "from the target to the proxy. Animate the proxy's rotation to "
       "control the target's orientation indirectly.",
       "Proxy Constraints"),

    # Feature 12
    _H("op.animassist.p7_create_proxy.TRANSLATION",
       "Translation Proxy",
       "Proxy that mirrors the target's position via Copy Location",
       "Creates a plain-axes empty and adds a Copy Location constraint. "
       "Animate the proxy to drive the target's position. Useful for "
       "space-switching or offset workflows.",
       "Proxy Constraints"),

    # Feature 13
    _H("op.animassist.p7_create_proxy.AIM",
       "Aim Proxy",
       "Proxy used as a Track To target for aim/look-at setups",
       "Creates a cone empty and adds a Track To constraint on the target "
       "aimed at the proxy. Move the proxy to control where the target "
       "looks.",
       "Proxy Constraints"),

    # Feature 14
    _H("op.animassist.p7_create_proxy.POLE",
       "Pole Helper",
       "Unlinked empty used as an IK pole target reference",
       "Creates a sphere empty at the target's position with no automatic "
       "constraint. Position the helper to serve as an IK pole-target "
       "reference.",
       "Proxy Constraints"),

    # Feature 15
    _H("op.animassist.p7_create_proxy.UP_VECTOR",
       "Up-Vector Helper",
       "Reference empty for aim/track-to up-axis alignment",
       "Creates a single-arrow empty with no automatic constraint. Use it "
       "as the up-target in Track To or Damped Track setups to control "
       "the rolling axis.",
       "Proxy Constraints"),

    # Feature 16
    _H("op.animassist.p7_create_proxy.MULTI_TARGET",
       "Multi-Target Average",
       "Proxy driven by the average position of multiple targets",
       "Creates a cube empty at the centroid of all selected objects. No "
       "automatic constraint is added; set up a Copy Location with "
       "multiple targets manually.",
       "Proxy Constraints"),

    # Feature 17
    _H("op.animassist.p7_create_proxy.PARENT_SPACE",
       "Parent-Space Proxy",
       "Proxy for temporary re-parenting via Child Of constraint",
       "Creates a cube empty and adds a Child Of constraint. The target "
       "follows the proxy as if parented, and the constraint can be keyed "
       "on/off for dynamic parenting changes.",
       "Proxy Constraints"),

    # Feature 18
    _H("op.animassist.p7_create_proxy.WORLD_SPACE",
       "World-Space Proxy",
       "Proxy that mirrors the full transform via Copy Transforms",
       "Creates an arrows empty and adds a Copy Transforms constraint. "
       "The proxy drives the target's full world-space transform.",
       "Proxy Constraints"),

    # Feature 19
    _H("op.animassist.p7_create_proxy.CAMERA_SPACE",
       "Camera-Space Proxy",
       "Proxy for camera-relative motion with keyed influence",
       "Creates a camera-data empty with no auto constraint. Designed for "
       "manual constraint setups where influence is keyed between 0 and 1 "
       "to blend camera-relative motion over time.",
       "Proxy Constraints"),

    # ===== Proxy Display (Features 20-23) =====

    # Feature 20
    _H("op.animassist.p7_toggle_display",
       "Toggle Proxy Display",
       "Cycle proxy visibility between full, dimmed, and hidden",
       "Cycles through the three display modes: Full (normal size and "
       "colour), Dimmed (reduced size and muted colour), Hidden (not "
       "visible in the viewport). Affects all proxies in the active session.",
       "Proxy Display"),

    # Feature 21
    _H("op.animassist.p7_set_proxy_color",
       "Set Proxy Color",
       "Change the wireframe colour of the selected proxy",
       "Reads the Proxy Color value from the temporarysettings and applies "
       "it to the active proxy object's display colour.",
       "Proxy Display"),

    # Feature 22
    _H("op.animassist.p7_rename_proxy",
       "Rename Proxy",
       "Rename the active proxy following the standard naming convention",
       "Rebuilds the proxy object's name using the standard pattern: "
       "AA_P7_Proxy_<target>_<type>_<session>. Useful after the target "
       "object has been renamed.",
       "Proxy Display"),

    # Feature 23
    _H("op.animassist.p7_toggle_collection",
       "Toggle Collection",
       "Toggle visibility of the session's temporary collection",
       "Shows or hides the session's AA_P7_Temp collection in the "
       "viewport. Useful for quickly decluttering the scene without "
       "changing individual proxy visibility.",
       "Proxy Display"),

    # ===== Proxy Cleanup (Features 24-25) =====

    # Feature 24
    _H("op.animassist.p7_cleanup_session",
       "Cleanup Session",
       "Remove all temporary artifacts from the active session",
       "Rolls back the current session: removes constraints first (safe "
       "for rigs), then deletes proxy/locator objects, then removes empty "
       "collections.",
       "Proxy Cleanup"),

    # Feature 25
    _H("op.animassist.p7_cleanup_all",
       "Cleanup All Sessions",
       "Purge all temporaryartifacts from the entire file",
       "Scans every object, pose bone, and collection for P7 tags and "
       "removes all matching artifacts. Use as a last-resort cleanup.",
       "Proxy Cleanup"),

    # ===== Session Management (Features 26-30) =====

    # Feature 26
    _H("op.animassist.p7_reconnect_session",
       "Reconnect Session",
       "Scan scene for P7-tagged objects and reconstruct a session",
       "Detects orphaned P7 artifacts in the scene and rebuilds a session "
       "from them, restoring cleanup and management capabilities.",
       "Session Management"),

    # Feature 27
    _H("op.animassist.p7_show_session_info",
       "Session Info",
       "Show detailed information about the active session",
       "Displays session ID, stage, scene, number of tracked objects, "
       "constraints, and collections in the info area.",
       "Session Management"),

    # Feature 28
    _H("op.animassist.p7_mute_constraints",
       "Mute/Unmute Constraints",
       "Toggle mute on all session-managed constraints",
       "Mutes or unmutes every constraint registered under the active "
       "session. Muted constraints are ignored during evaluation, letting "
       "you preview the original animation.",
       "Session Management"),

    # Feature 29
    _H("op.animassist.p7_lock_target",
       "Lock Original Target",
       "Freeze the target's transform channels while proxy is active",
       "Locks location, rotation, and scale on the original target object "
       "to prevent accidental edits while a proxy is driving it.",
       "Session Management"),

    # Feature 30
    _H("op.animassist.p7_switch_proxy_mode",
       "Switch Proxy Mode",
       "Toggle between Constrain and Offset proxy modes",
       "Switches the active proxy mode between Constrain (proxy replaces "
       "target motion) and Offset (proxy adds on top of existing motion).",
       "Session Management"),

    # ===== Bake Workflows (Features 31-35) =====

    # Feature 31
    _H("op.animassist.p7_bake_range",
       "Bake Range",
       "Bake only within the configured frame range",
       "Uses the Bake Range Mode (Scene, Action, Custom, Selection, or "
       "Preview) to determine start and end frames, then bakes the active "
       "object's evaluated transform within that range.",
       "Bake Workflows"),

    # Feature 32
    _H("op.animassist.p7_bake_preview",
       "Bake Preview Range",
       "Bake within the scene's preview/playback range markers",
       "Uses the scene's preview range (frame_preview_start/end) as the "
       "bake range. Only available when Use Preview Range is enabled.",
       "Bake Workflows"),

    # Feature 33
    _H("op.animassist.p7_bake_selected_channels",
       "Bake Selected Channels",
       "Bake only channels that have existing keyframes",
       "Determines which transform channels already have animation and "
       "bakes only those, leaving un-keyed channels untouched.",
       "Bake Workflows"),

    # Feature 34
    _H("op.animassist.p7_smart_bake",
       "Smart Bake",
       "Bake with automatic key reduction to minimize keyframe count",
       "Performs a full-range bake then applies Ramer-Douglas-Peucker "
       "simplification to remove keys whose deletion causes less than the "
       "Smart Bake Tolerance deviation.",
       "Bake Workflows"),

    # Feature 35
    _H("op.animassist.p7_bake_preserve_timing",
       "Preserve Timing Bake",
       "Bake while preserving existing keyframe positions",
       "Only updates values at frames where keyframes already exist, "
       "preserving the animator's original timing decisions. Does not "
       "insert new keyframes.",
       "Bake Workflows"),

    # ===== Batch Proxy (Features 36-39, 40-44) =====

    # Feature 36
    _H("op.animassist.p7_apply_offset",
       "Apply Offset",
       "Apply the proxy offset as additive on top of existing animation",
       "Reads the proxy's current offset from its target and applies it "
       "as an additive layer on the target's animation.",
       "Batch Proxy"),

    # Feature 37
    _H("op.animassist.p7_zero_proxy",
       "Zero-Out Proxy",
       "Reset proxy transforms to identity",
       "Sets the active proxy's location to (0,0,0), rotation to zero, "
       "and scale to (1,1,1). Useful as a quick reset before re-posing.",
       "Batch Proxy"),

    # Feature 38
    _H("op.animassist.p7_recenter_proxy",
       "Recenter Proxy",
       "Snap the proxy to the driven target's current position",
       "Reads the target's current world-space position and moves the "
       "proxy to match. Useful after the target has drifted or been "
       "manually adjusted.",
       "Batch Proxy"),

    # Feature 39
    _H("op.animassist.p7_temp_pivot",
       "Temporary Pivot",
       "Create a free-standing pivot proxy at the cursor",
       "Places a POLE-type empty at the 3D cursor with no constraint or "
       "owner. Acts as a general-purpose pivot point for manual workflows.",
       "Batch Proxy"),

    # Feature 40
    _H("op.animassist.p7_batch_create_proxies",
       "Batch Create Proxies",
       "Create proxies for all selected objects at once",
       "For each selected object, creates a proxy of the configured type "
       "and adds the appropriate constraint. All proxies share one session.",
       "Batch Proxy"),

    # Feature 41
    _H("op.animassist.p7_auto_cleanup",
       "Auto Cleanup",
       "Detect and remove orphaned temporaryartifacts",
       "Scans for P7-tagged objects not tracked by any active session "
       "and removes them automatically.",
       "Batch Proxy"),

    # Feature 42
    _H("op.animassist.p7_validate_session",
       "Validate Session",
       "Check for orphaned artifacts or missing targets",
       "Scans the session's artifact registry against the actual scene "
       "data and reports any mismatches: deleted objects, missing "
       "constraints, or unsupported configurations.",
       "Batch Proxy"),

    # Feature 43
    _H("op.animassist.p7_check_setup",
       "Check Setup",
       "Warn about unsupported or conflicting constraint setups",
       "Examines the target object for pre-existing constraints or "
       "transform issues that may conflict with proxy operation.",
       "Batch Proxy"),

    # Feature 44
    _H("op.animassist.p7_mirror_proxy",
       "Mirror Proxy",
       "Create a mirrored copy of the selected proxy",
       "Duplicates the proxy and mirrors its position across the YZ plane. "
       "Uses L/R naming convention swap for the mirrored copy.",
       "Batch Proxy"),

    # ===== One-Click Workflows (Feature 45) =====

    _H("op.animassist.p7_one_click_proxy_bake",
       "One-Click Proxy & Bake",
       "Create a proxy, bake, and clean up in one operation",
       "Records the active object's world motion on a temporary Translation "
       "proxy, constrains the object to it, bakes the result to keys and removes "
       "the proxy. Net result: world motion baked to keys with no lingering "
       "temporary objects. Other proxy sessions are left alone.",
       "One-Click Workflows"),

    _H("op.animassist.p7_one_click_cleanup",
       "One-Click Cleanup",
       "Bake all session constraints and clean up all artifacts",
       "First bakes every constrained object in the session, then performs "
       "a full session cleanup.",
       "One-Click Workflows"),

    _H("op.animassist.p7_quick_proxy",
       "Quick Proxy",
       "Create a translation proxy with default settings",
       "Shortcut that skips the proxy-type selection: creates a Translation "
       "Proxy with current defaults, auto-constrained to the active object.",
       "One-Click Workflows"),

    _H("op.animassist.p7_export_session",
       "Export Session",
       "Export session data as JSON to the clipboard",
       "Serializes the active session's full state to a JSON string and "
       "copies it to the system clipboard.",
       "One-Click Workflows"),

    _H("op.animassist.p7_list_sessions",
       "List Sessions",
       "Print a summary of all active P7 sessions",
       "Reports session ID, stage, object count, and constraint count "
       "for every session in the Python-side registry.",
       "One-Click Workflows"),
)


# ---------------------------------------------------------------------------
# Registration shim
# ---------------------------------------------------------------------------

def register() -> None:
    """Register temporary control help entries into the Help Browser registry.

    Called during addon initialization so temporary control operators and properties
    appear in the context-sensitive Help Browser documentation.
    """
    register_phase_help(_PHASE, PHASE7_ENTRIES)


def unregister() -> None:
    """Unregister temporary control help entries from the Help Browser registry.

    Called during addon teardown to clean up help documentation.
    """
    unregister_phase_help(_PHASE)
