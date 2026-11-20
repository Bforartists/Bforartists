# --- EXPLAINER SYSTEM EXTENSION ---
"""Help seed entries for core animation assistance features.

Every preference, operator and panel that ships with foundational features is given a
real help record. Additional modules follow the same pattern in their own
``help_phaseN_entries.py`` modules.
"""

from __future__ import annotations

from .help_registry import (
    HelpEntry,
    register_phase_help,
    unregister_phase_help,
)

__all__ = [
    "PHASE1_ENTRIES",
    "register",
    "unregister",
]

_PHASE = "phase1"

PHASE1_ENTRIES: tuple[HelpEntry, ...] = (
    # ------------------------------------------------------------------ General
    HelpEntry(
        id="pref.debug_mode",
        label="Debug Mode",
        tooltip="Enable verbose logging to the Blender console",
        description=(
            "When enabled, Anim Assist logs DEBUG-level messages from every "
            "subsystem to the Blender console.\n\n"
            "Use this when investigating an unexpected behaviour or when "
            "reporting an issue. The log level is applied live the moment you "
            "toggle the checkbox — no reload required."
        ),
        phase=_PHASE,
        category="General",
    ),
    HelpEntry(
        id="pref.performance_mode",
        label="Performance Mode",
        tooltip="Reduce UI updates and diagnostics for better performance",
        description=(
            "Performance Mode suppresses non-essential draw passes and "
            "diagnostic scans while you are actively editing keys on complex "
            "rigs.\n\n"
            "Leave this off during normal work — turn it on only when the "
            "sidebar feels sluggish on very dense actions."
        ),
        phase=_PHASE,
        category="General",
    ),
    HelpEntry(
        id="pref.diagnostics_visible",
        label="Show Diagnostics Panel",
        tooltip="Show the diagnostics panel in Properties > Scene > Anim Assist > Help & Diagnostics",
        description=(
            "Controls whether the Anim Assist Diagnostics panel appears in the "
            "Properties editor: Scene tab > Anim Assist > Help & Diagnostics.\n\n"
            "The panel itself has no performance cost when collapsed; this "
            "toggle is provided so you can hide it entirely when demoing to "
            "artists."
        ),
        phase=_PHASE,
        category="Diagnostics",
    ),
    HelpEntry(
        id="pref.explainer_mode",
        label="Hover Explainers",
        tooltip="Choose Full, Short or Off for Anim Assist hover explanations",
        description=(
            "Full shows the whole explanation when the pointer rests on an Anim "
            "Assist control: what it does, what it works on, what it needs and "
            "how to use it. Short shows the name and a one-line summary. Off "
            "shows no Anim Assist explanation on hover.\n\n"
            "The setting covers the Timeline tool row and every Anim Assist "
            "button. A shortcut line appears only when a key is already bound "
            "to that tool. With Off, Bforartists still shows a button's name, "
            "and setting fields keep their own one-line Bforartists tooltip; "
            "Preferences > Interface > Tooltips turns all tooltips off."
        ),
        phase=_PHASE,
        category="General",
    ),
    HelpEntry(
        id="pref.show_explainer_help",
        label="Show Extended Help Popups",
        tooltip="Show question-mark buttons that open detailed Anim Assist help",
        description=(
            "When enabled, every Anim Assist control that has a registered "
            "help entry gains a small question-mark icon beside it. Clicking "
            "the icon opens a popup with a long-form explanation of the "
            "control.\n\n"
            "Disable this to hide every explainer icon across the addon. Native "
            "Bforartists hover tooltips and the Help Browser remain available."
        ),
        phase=_PHASE,
        category="General",
    ),
    HelpEntry(
        id="pref.compact_ui_mode",
        label="Compact UI Mode",
        tooltip="Draw explainer icons without neighbouring labels to save space",
        description=(
            "Compact UI Mode keeps explainer icons visible but hides their "
            "neighbouring text labels, so sidebar panels remain dense on "
            "small screens.\n\n"
            "Has no effect when Show Extended Help Popups is disabled."
        ),
        phase=_PHASE,
        category="General",
    ),
    # -------------------------------------------------------------- Tool Behaviour
    HelpEntry(
        id="pref.animassist_fast_offset",
        label="Fast Offset Mode",
        tooltip="Only propagate Anim Offset on mouse release",
        description=(
            "In Fast Offset Mode the Anim Offset modal operator defers its "
            "propagation pass until you release the mouse. This is "
            "significantly faster on complex rigs at the cost of not seeing "
            "the final result live during the drag."
        ),
        phase=_PHASE,
        category="Tool Behaviour",
    ),
    HelpEntry(
        id="pref.animassist_autokey_outside_margins",
        label="Auto-key Outside Margins",
        tooltip="Insert keys for frames outside the mask blend region",
        description=(
            "When enabled, Anim Offset auto-inserts keys on frames that fall "
            "outside the active mask's blend region so those frames get "
            "preserved explicitly rather than relying on interpolation."
        ),
        phase=_PHASE,
        category="Tool Behaviour",
    ),
    HelpEntry(
        id="pref.animassist_drag_sensitivity",
        label="Drag Sensitivity",
        tooltip="Mouse pixels needed to reach factor 1.0 in modal operators",
        description=(
            "Number of screen-space pixels the mouse must travel for a modal "
            "drag operator to reach its full factor. Lower values feel "
            "twitchier; higher values give finer control."
        ),
        phase=_PHASE,
        category="Tool Behaviour",
    ),
    # -------------------------------------------------------------- Diagnostics
    HelpEntry(
        id="pref.p2_dense_min_gap",
        label="Dense Key Min Gap",
        tooltip="Frames below this count as 'too dense' in the diagnostics scan",
        description=(
            "The diagnostics scan flags consecutive keys whose gap "
            "falls below this value as 'dense'. Typical values range from "
            "1.0 (sub-frame keys) to 2.0 (back-to-back integer keys)."
        ),
        phase=_PHASE,
        category="Diagnostics",
    ),
    HelpEntry(
        id="pref.p2_redundant_tolerance",
        label="Redundant Key Tolerance",
        tooltip="Value tolerance for flagging a key as redundant",
        description=(
            "A key is flagged as redundant when its value lies within this "
            "tolerance of the straight line between its two neighbours. "
            "Tighten this to catch only exact duplicates; loosen it to "
            "catch near-flat segments."
        ),
        phase=_PHASE,
        category="Diagnostics",
    ),
    HelpEntry(
        id="pref.p2_spike_ratio",
        label="Spike Ratio",
        tooltip="Neighbour deviation ratio at which a key is flagged as a spike",
        description=(
            "The spike detector compares each key's deviation from the local "
            "smoothed curve against the median neighbour deviation. Values at "
            "or above this ratio are flagged as spikes."
        ),
        phase=_PHASE,
        category="Diagnostics",
    ),
    # -------------------------------------------------------------- Modules
    HelpEntry(
        id="pref.enable_selection",
        label="Selection Tools",
        tooltip="Register the Selection module",
        description=(
            "Master switch for the Selection Tools module. Disabling it "
            "prevents its operators and panels from registering at startup."
        ),
        phase=_PHASE,
        category="Modules",
    ),
    HelpEntry(
        id="pref.enable_keys",
        label="Key Utilities",
        tooltip="Register the Key Utilities module",
        description=(
            "Master switch for the Key Utilities module (copy/paste, offset, "
            "mirror, snap, safe delete)."
        ),
        phase=_PHASE,
        category="Modules",
    ),
    HelpEntry(
        id="pref.enable_transform",
        label="Transform Workflows",
        tooltip="Register the Transform Workflows module",
        description=(
            "Master switch for the Transform Workflows module (future phase)."
        ),
        phase=_PHASE,
        category="Modules",
    ),
    HelpEntry(
        id="pref.enable_breakdown",
        label="Breakdown Tools",
        tooltip="Register the Breakdown Tools module",
        description=(
            "Master switch for the Breakdown Tools module (future phase)."
        ),
        phase=_PHASE,
        category="Modules",
    ),
    HelpEntry(
        id="pref.enable_trajectory",
        label="Trajectory Tools",
        tooltip="Register the Trajectory Tools module",
        description=(
            "Master switch for the Trajectory Tools module (future phase)."
        ),
        phase=_PHASE,
        category="Modules",
    ),
    HelpEntry(
        id="pref.enable_retime",
        label="Retime Tools",
        tooltip="Register the Retime Tools module",
        description=(
            "Master switch for the Retime Tools module (future phase)."
        ),
        phase=_PHASE,
        category="Modules",
    ),
    HelpEntry(
        id="pref.enable_controls",
        label="Temp Controls",
        tooltip="Register the Temp Controls module",
        description=(
            "Master switch for the Temp Controls module (future phase)."
        ),
        phase=_PHASE,
        category="Modules",
    ),
    HelpEntry(
        id="pref.enable_matching",
        label="Matching Workflows",
        tooltip="Register the Matching Workflows module",
        description=(
            "Master switch for the Matching Workflows module (future phase)."
        ),
        phase=_PHASE,
        category="Modules",
    ),
    # -------------------------------------------------------------- Operators
    HelpEntry(
        id="op.anim_assist.export_settings",
        label="Export Settings",
        tooltip="Write every Anim Assist preference to a JSON file",
        description=(
            "Exports every Anim Assist preference (general, modules, tool "
            "behaviour, diagnostics settings) to a JSON file you can commit to "
            "a project repo or share with a team-mate.\n\n"
            "The operator never writes scene data — only addon preferences."
        ),
        phase=_PHASE,
        category="Settings",
    ),
    HelpEntry(
        id="op.anim_assist.import_settings",
        label="Import Settings",
        tooltip="Load Anim Assist preferences from a JSON file",
        description=(
            "Loads preferences previously saved with Export Settings. "
            "Unknown fields in the JSON are ignored so a file exported from a "
            "newer build can still be imported into an older one."
        ),
        phase=_PHASE,
        category="Settings",
    ),
    HelpEntry(
        id="op.anim_assist.refresh_diagnostics",
        label="Refresh Diagnostics",
        tooltip="Rebuild the diagnostics snapshot now",
        description=(
            "Forces a fresh capability probe, cache flush and runtime state "
            "rebuild. Use this if an external addon has changed the scene "
            "between your last interaction and now."
        ),
        phase=_PHASE,
        category="Diagnostics",
    ),
    HelpEntry(
        id="op.anim_assist.copy_diagnostics",
        label="Copy Diagnostics",
        tooltip="Copy the diagnostics snapshot to the clipboard",
        description=(
            "Copies a text dump of the diagnostics panel — active target, "
            "timeline range, editor presence, capabilities, runtime cache — "
            "to the system clipboard, suitable for pasting into a bug report."
        ),
        phase=_PHASE,
        category="Diagnostics",
    ),
    # -------------------------------------------------------------- Panels
    HelpEntry(
        id="panel.aa_pt_diagnostics",
        label="Diagnostics Panel",
        tooltip="The Properties panel that surfaces add-on internals",
        description=(
            "The Anim Assist Diagnostics panel lives in the Properties editor: "
            "Scene tab > Anim Assist > Help & Diagnostics. It surfaces the active target, the "
            "effective timeline range, which animation editors are open, the "
            "capabilities registry, and the current runtime cache.\n\n"
            "Everything it shows is read-only; the Refresh and Copy buttons "
            "rebuild or export the snapshot."
        ),
        phase=_PHASE,
        category="Diagnostics",
    ),
)


def register() -> int:
    """Register every core help entry. Returns the count inserted."""
    return register_phase_help(_PHASE, PHASE1_ENTRIES)


def unregister() -> int:
    """Remove every core help entry. Returns the count removed."""
    return unregister_phase_help(_PHASE)
