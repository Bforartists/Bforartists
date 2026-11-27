"""Help entries for tool organization, macros, and advanced diagnostics.

Provides 45 HelpEntry records covering shelf, menu, tools, macros, and diagnostics features, organized
into 11 categories that align with the panel section structure.
"""

from __future__ import annotations

from .help_registry import HelpEntry, register_phase_help, unregister_phase_help

__all__ = [
    "PHASE10_ENTRIES",
    "register",
    "unregister",
]

_PHASE = "phase10"


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
#   Quick Shelf, Pie Menus, Tool Access, Macro Operations,
#   Batch Processing, Presets, Recovery, Audit Trail,
#   Diagnostics, Setup & Validation, Help & Debug
# ---------------------------------------------------------------------------

PHASE10_ENTRIES: tuple[HelpEntry, ...] = (
    # ── Quick Shelf ───────────────────────────────────────────────────────
    _H(
        "op.animassist.p10_quick_shelf",
        "Quick Shelf",
        "Access frequently-used operators from a compact shelf",
        "Displays a horizontal or vertical toolbar with pinned operators and "
        "macros.  Customizable buttons for instant access to your favorite tools.  "
        "Reduces clicks and speeds up workflow.",
        "Quick Shelf",
    ),
    _H(
        "op.animassist.p10_shelf_compact_mode",
        "Compact Mode",
        "Minimize shelf to icon-only display",
        "Hides labels and shows only icons on shelf buttons.  Saves screen space "
        "while maintaining visual recognition.  Useful on smaller monitors or "
        "crowded UI layouts.",
        "Quick Shelf",
    ),
    _H(
        "op.animassist.p10_shelf_expanded_mode",
        "Expanded Mode",
        "Display shelf with full button labels",
        "Shows both icon and label text on every shelf button.  Clearer for "
        "discovery and onboarding.  Takes more space but improves readability.",
        "Quick Shelf",
    ),
    _H(
        "op.animassist.p10_context_sensitive_shelf",
        "Context-Sensitive",
        "Show different buttons based on current context",
        "The shelf adapts to show relevant tools depending on the active object "
        "type, mode, or selection.  For example, rigging tools appear when an "
        "armature is selected.",
        "Quick Shelf",
    ),
    _H(
        "op.animassist.p10_shelf_favorites",
        "Favorites",
        "Manage and pin favorite operators to the shelf",
        "Opens a menu to select operators and macros to add as shelf buttons.  "
        "Star-mark your most-used tools.  Favorites are saved per-project or globally.",
        "Quick Shelf",
    ),
    _H(
        "op.animassist.p10_shelf_filter",
        "Shelf Filter",
        "Filter shelf contents by category or search term",
        "Type to search shelf buttons by name, category, or shortcut.  Reduces "
        "visual clutter and helps locate tools in large shelves.  Filter state "
        "persists during the session.",
        "Quick Shelf",
    ),

    # ── Pie Menus ──────────────────────────────────────────────────────────
    _H(
        "op.animassist.p10_pie_key_tools",
        "Key Tools Pie",
        "Radial menu of essential keyframing tools",
        "Pie menu (RMB or hotkey) with Insert Keyframe, Delete Keyframe, Clear "
        "Keyframe, and other key operations arranged in 8 directions.  Fast "
        "access without submenus.",
        "Pie Menus",
    ),
    _H(
        "op.animassist.p10_pie_breakdown",
        "Breakdown Pie",
        "Radial menu for breakdown and offset operations",
        "Pie menu with Breakdown, Offset, Retime, and related tools.  Useful "
        "for spacing and timing adjustments in the middle of your animation.",
        "Pie Menus",
    ),
    _H(
        "op.animassist.p10_pie_transform",
        "Transform Pie",
        "Radial menu of transform tools",
        "Pie menu with Move, Rotate, Scale, and space toggles (Local/World/Normal).  "
        "Quick switching between transform modes without leaving the pie.",
        "Pie Menus",
    ),
    _H(
        "op.animassist.p10_pie_proxy",
        "Proxy Pie",
        "Radial menu for proxy and IK/FK switching",
        "Pie menu with Toggle IK/FK, Switch Target, Mirror Targets, and proxy "
        "helper controls.  Streamlines constraint and proxy workflows.",
        "Pie Menus",
    ),
    _H(
        "op.animassist.p10_pie_switch",
        "Switch Pie",
        "Radial menu for mode and state switching",
        "Pie menu with Object/Edit/Pose mode toggles, shape-key or driver switches, "
        "and other mode-based operations.  One-click context switching.",
        "Pie Menus",
    ),
    _H(
        "op.animassist.p10_pie_symmetry",
        "Symmetry Pie",
        "Radial menu for mirroring and symmetry operations",
        "Pie menu with Mirror Pose, Mirror Selected, Swap Poses, and axis toggles.  "
        "Fastest way to access your mirror settings.",
        "Pie Menus",
    ),

    # ── Tool Access ────────────────────────────────────────────────────────
    _H(
        "op.animassist.p10_quick_search",
        "Quick Search",
        "Search and launch operators by keyword",
        "Opens a search dialog (like Blender's F3 menu) filtering AnimAssist "
        "operators.  Type to find and run any tool without menus or hotkeys.",
        "Tool Access",
    ),
    _H(
        "op.animassist.p10_recent_tools",
        "Recent Tools",
        "Access your most-recently-used operators",
        "Displays a list of the last N operators you ran, in reverse chronological "
        "order.  Click to repeat or re-open with settings.  Quick re-access without "
        "digging through menus.",
        "Tool Access",
    ),
    _H(
        "op.animassist.p10_repeat_last",
        "Repeat Last",
        "Re-run the previous operator with same settings",
        "Repeats the last operator execution using the previous settings and scope.  "
        "Useful for applying the same operation multiple times in a row.",
        "Tool Access",
    ),
    _H(
        "op.animassist.p10_repeat_with_settings",
        "Repeat with Settings",
        "Re-run previous operator with a settings dialog",
        "Repeats the last operation but pops up the settings dialog first, allowing "
        "you to tweak parameters before re-execution.  Faster than running from "
        "scratch.",
        "Tool Access",
    ),

    # ── Macro Operations ───────────────────────────────────────────────────
    _H(
        "op.animassist.p10_macro_breakdown_offset",
        "Breakdown + Offset",
        "Combined breakdown and offset macro",
        "A single operation that applies a breakdown frame at the playhead and "
        "then offsets it by a configurable amount.  Useful for quick timing tweaks.",
        "Macro Operations",
    ),
    _H(
        "op.animassist.p10_macro_proxy_workflow",
        "Proxy Workflow",
        "Multi-step proxy helper setup macro",
        "Automatically creates and configures proxy bones, parent constraints, "
        "and visibility toggles for the selected control.  Streamlines IK/FK proxy setup.",
        "Macro Operations",
    ),
    _H(
        "op.animassist.p10_macro_switch_compensate",
        "Switch + Compensate",
        "Switch constraint target and adjust poses",
        "Toggles an IK/FK constraint and automatically adjusts the opposite chain "
        "to match current position, eliminating pops.  One-click seamless switching.",
        "Macro Operations",
    ),
    _H(
        "op.animassist.p10_macro_diagnose_jump",
        "Diagnose + Jump",
        "Identify and navigate to the next problem frame",
        "Scans the timeline for frames with warnings (gimbal lock, popping, etc.) "
        "and jumps the playhead to the next one.  Guides you through problem areas.",
        "Macro Operations",
    ),
    _H(
        "op.animassist.p10_macro_mirror_match",
        "Mirror + Match",
        "Mirror pose and match opposite to maintain offset",
        "Mirrors one side to the opposite while preserving any intentional asymmetry "
        "or offset.  Creates mirrored poses without losing character.",
        "Macro Operations",
    ),

    # ── Batch Processing ───────────────────────────────────────────────────
    _H(
        "op.animassist.p10_batch_selected_targets",
        "Selected Targets",
        "Run operator on all selected bones/objects",
        "Applies an operator (e.g., Bake, Simplify, Clean Keys) to every item in "
        "the current selection.  Saves time when processing multiple targets at once.",
        "Batch Processing",
    ),
    _H(
        "op.animassist.p10_batch_bookmarked_channels",
        "Bookmarked Channels",
        "Run operator on all bookmarked channels",
        "Applies an operation to a pre-defined set of channels across multiple bones.  "
        "Useful for processing a consistent set of properties on every rig.",
        "Batch Processing",
    ),
    _H(
        "op.animassist.p10_batch_frame_steps",
        "Frame Steps",
        "Apply operator at regular frame intervals",
        "Runs an operation every N frames across a time range.  Useful for adding "
        "keys, baking, or processing at consistent intervals without manual stepping.",
        "Batch Processing",
    ),

    # ── Presets ───────────────────────────────────────────────────────────
    _H(
        "op.animassist.p10_preset_browser",
        "Preset Browser",
        "Browse and load operator setting presets",
        "Opens a file browser showing saved presets for operators.  Select and "
        "apply a preset to instantly configure an operator with pre-tuned settings.",
        "Presets",
    ),
    _H(
        "op.animassist.p10_preset_tagging",
        "Tagging",
        "Assign tags and categories to presets",
        "Organize presets with user-defined tags (e.g., 'Walk', 'Run', 'Idle').  "
        "Filter and search presets by tag for faster discovery.",
        "Presets",
    ),
    _H(
        "op.animassist.p10_preset_export_import",
        "Export / Import",
        "Save and load preset collections",
        "Export presets to a file for sharing or backup.  Import presets from "
        "files to add them to your library.  Facilitates team workflows.",
        "Presets",
    ),
    _H(
        "op.animassist.p10_workspace_profiles",
        "Workspace Profiles",
        "Save and restore complete UI and operator configurations",
        "Captures the current shelf, pie menus, hotkeys, and preferences.  Swap "
        "between different profiles for different tasks (e.g., FK vs. IK focus).",
        "Presets",
    ),

    # ── Recovery ───────────────────────────────────────────────────────────
    _H(
        "op.animassist.p10_snapshot",
        "Snapshot",
        "Capture current armature state for recovery",
        "Records the current pose, keyframes, and rig configuration to an in-memory "
        "snapshot.  Use before risky operations.  Multiple snapshots can be stored.",
        "Recovery",
    ),
    _H(
        "op.animassist.p10_restore",
        "Restore",
        "Restore armature from a saved snapshot",
        "Revert the armature (pose, keys, properties) to a previously-saved snapshot.  "
        "Useful for undoing complex multi-step operations or recovering from mistakes.",
        "Recovery",
    ),

    # ── Audit Trail ────────────────────────────────────────────────────────
    _H(
        "op.animassist.p10_transaction_history",
        "Transaction History",
        "View log of all executed operations",
        "Displays a timeline of every operator, macro, and batch operation run in "
        "the session.  Click to jump to that point in history or re-execute.",
        "Audit Trail",
    ),
    _H(
        "op.animassist.p10_operation_audit",
        "Operation Audit",
        "Detailed record of parameters and results for each operation",
        "For each logged operation, shows input parameters, target bones, affected "
        "frames, and result summary.  Useful for understanding what happened.",
        "Audit Trail",
    ),
    _H(
        "op.animassist.p10_error_log",
        "Error Log",
        "View warnings and errors from operations",
        "Collects and displays all errors, warnings, and info messages generated "
        "by operations.  Helps debug issues and understand why an operation failed.",
        "Audit Trail",
    ),

    # ── Diagnostics ────────────────────────────────────────────────────────
    _H(
        "op.animassist.p10_system_diagnostics",
        "System Diagnostics",
        "Check Blender and system health",
        "Runs checks on available memory, GPU support, plugin load state, and "
        "Blender version compatibility.  Generates a report of potential issues.",
        "Diagnostics",
    ),
    _H(
        "op.animassist.p10_leak_checker",
        "Leak Checker",
        "Scan for memory leaks in addon data structures",
        "Inspects registered handlers, callbacks, and persistent data to find "
        "unreleased resources.  Reports orphaned objects that should be cleaned.",
        "Diagnostics",
    ),
    _H(
        "op.animassist.p10_stale_cleanup",
        "Stale Cleanup",
        "Remove orphaned or expired data",
        "Deletes expired snapshots, unused presets, and orphaned cached data.  "
        "Frees memory and keeps the addon lightweight.",
        "Diagnostics",
    ),
    _H(
        "op.animassist.p10_metadata_cleanup",
        "Metadata Cleanup",
        "Verify and repair custom property data",
        "Scans the armature for corrupted or inconsistent custom properties.  "
        "Repairs or removes invalid metadata.  Prevents crashes from bad data.",
        "Diagnostics",
    ),
    _H(
        "op.animassist.p10_rebuild_caches",
        "Rebuild Caches",
        "Refresh all internal caches and lookups",
        "Clears and rebuilds the pair cache, tool lookup table, and other internal "
        "caches.  Use if you suspect stale data after editing the rig.",
        "Diagnostics",
    ),
    _H(
        "op.animassist.p10_reset_ui",
        "Reset UI",
        "Clear all shelf and pie menu customizations",
        "Restores the default shelf and pie menus.  Clears custom buttons and "
        "favorites.  Useful if the UI becomes unusable.",
        "Diagnostics",
    ),

    # ── Setup & Validation ─────────────────────────────────────────────────
    _H(
        "op.animassist.p10_safe_disable",
        "Safe Disable",
        "Disable addon features gracefully without data loss",
        "Saves state and configuration, then disables the addon.  Re-enabling "
        "restores everything.  Prevents corruption or lost settings.",
        "Setup & Validation",
    ),
    _H(
        "op.animassist.p10_hotkey_conflicts",
        "Hotkey Conflicts",
        "Detect and resolve hotkey collisions",
        "Scans for overlapping keybindings with other addons or Blender defaults.  "
        "Suggests remapping or disabling conflicting keys.",
        "Setup & Validation",
    ),
    _H(
        "op.animassist.p10_first_run_setup",
        "First-Run Setup",
        "Guide for initial configuration and onboarding",
        "Wizard to configure basic preferences, create default presets, and "
        "populate the shelf.  Customizes the addon for the user's workflow.",
        "Setup & Validation",
    ),
    _H(
        "op.animassist.p10_demo_config",
        "Demo Config",
        "Load a demonstration configuration for tutorial",
        "Applies a pre-built shelf, pie menus, and hotkeys designed for learning.  "
        "Resets to sensible defaults for new users.",
        "Setup & Validation",
    ),

    # ── Help & Debug ───────────────────────────────────────────────────────
    _H(
        "op.animassist.p10_tooltip_help",
        "Tooltip / Help Link",
        "View detailed tooltip or open documentation",
        "Hover over any operator or UI element to see a tooltip.  Click the help "
        "icon to open the full documentation page in a browser.",
        "Help & Debug",
    ),
    _H(
        "op.animassist.p10_debug_toggle",
        "Debug Toggle",
        "Enable verbose logging and diagnostic output",
        "Switches the addon into debug mode, printing detailed logs to the console.  "
        "Useful for troubleshooting or reporting bugs.",
        "Help & Debug",
    ),
    _H(
        "op.animassist.p10_final_validation",
        "Final Validation",
        "Run comprehensive checks before saving",
        "Scans the current file for common issues (missing targets, broken constraints, "
        "etc.) before saving.  Prevents corrupted saves.",
        "Help & Debug",
    ),
)


def register() -> None:
    """Register tool and diagnostics help entries into the Help Browser registry.

    Called during addon initialization so tool and diagnostics operators and properties
    appear in the context-sensitive Help Browser documentation.
    """
    register_phase_help(_PHASE, PHASE10_ENTRIES)


def unregister() -> None:
    """Unregister tool and diagnostics help entries from the Help Browser registry.

    Called during addon teardown to clean up help documentation.
    """
    unregister_phase_help(_PHASE)
