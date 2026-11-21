# --- BREAKDOWN TOOLS ---
"""Help entries for breakdown analysis and visualization features.

Every breakdown tool feature gets one :class:`HelpEntry`. Categories follow the
sidebar panel layout in the UI so the Help Browser groups
match what animators see in the sidebar.

Entries use ``phase="phase3"`` to participate in the existing bulk
teardown via :func:`unregister_phase_help`.
"""

from __future__ import annotations

from ..constants import BREAKDOWN_ANCHOR_HINT

from .help_registry import (
    HelpEntry,
    register_phase_help,
    unregister_phase_help,
)

__all__ = [
    "PHASE3_ENTRIES",
    "register",
    "unregister",
]

_PHASE = "phase3"


def _H(id_: str, label: str, tooltip: str, description: str, category: str) -> HelpEntry:
    return HelpEntry(
        id=id_,
        label=label,
        tooltip=tooltip,
        description=description,
        phase=_PHASE,
        category=category,
    )


PHASE3_ENTRIES: tuple[HelpEntry, ...] = (
    # ====================================================================
    # Breakdown Core
    # ====================================================================
    _H("op.animassist.breakdown_current_frame",
       "Breakdown at Current Frame",
       "Create a weighted breakdown key at the current frame",
       "Inserts a new key at the scene's current frame on every targeted fcurve, "
       "blended between the previous and next pose using the factor on the breakdown"
       "panel. Honours the active mask, exclusion set, and interpolation options.",
       "Breakdown Core"),
    _H("op.animassist.breakdown_weighted",
       "Weighted Previous/Next",
       "Weighted breakdown using the factor slider",
       "Identical to Breakdown at Current Frame but explicitly reads the factor "
       "slider so animators can scrub it while the operator re-runs via repeat-last. "
       "Use this for quick A/B comparisons of different blend weights.",
       "Breakdown Core"),
    _H("op.animassist.breakdown_favor_prev",
       "Favor Previous Pose",
       "75% bias toward the previous pose",
       "Writes a breakdown heavily biased toward the previous pose (factor 0.25). "
       "Useful for snappy outs where most of the pose should hold on the starting key.",
       "Breakdown Core"),
    _H("op.animassist.breakdown_favor_next",
       "Favor Next Pose",
       "75% bias toward the next pose",
       "Writes a breakdown heavily biased toward the next pose (factor 0.75). "
       "Useful for heavy anticipation where the pose should lean into the next key.",
       "Breakdown Core"),
    _H("op.animassist.breakdown_midpoint",
       "Midpoint Breakdown",
       "Clean 50/50 midpoint between neighbours",
       "Writes a perfect midpoint (factor 0.5) on every targeted fcurve. The cleanest "
       "starting point for pose-to-pose inbetweens.",
       "Breakdown Core"),
    _H("op.animassist.breakdown_push_prev",
       "Push From Previous",
       "Extrapolate past the previous pose",
       "Extrapolates the new key past the previous pose using the Push Strength "
       "setting. Produces a snappier out than a vanilla weighted breakdown.",
       "Breakdown Core"),
    _H("op.animassist.breakdown_push_next",
       "Push Into Next",
       "Extrapolate past the next pose",
       "Extrapolates the new key past the next pose using the Push Strength "
       "setting. Produces a heavier anticipation than a vanilla weighted breakdown.",
       "Breakdown Core"),
    _H("op.animassist.breakdown_pull_prev",
       "Pull To Previous",
       "Soften the breakdown toward the previous pose",
       "Softens the new key toward the previous pose using the Pull Strength "
       "setting (clamped 0..1). Useful for easing into a hold.",
       "Breakdown Core"),
    _H("op.animassist.breakdown_pull_next",
       "Pull To Next",
       "Soften the breakdown toward the next pose",
       "Softens the new key toward the next pose using the Pull Strength "
       "setting (clamped 0..1). Useful for easing out of a hold.",
       "Breakdown Core"),
    _H("op.animassist.breakdown_percentage",
       "25 / 50 / 75 Quick Buttons",
       "Quick percentage breakdowns via one-click buttons",
       "Writes a breakdown at a fixed percentage (25%, 50%, or 75%) without "
       "touching the factor slider. " + BREAKDOWN_ANCHOR_HINT + " "
       "Example: keys at frames 1=0 and 11=10 give 2.5 at an empty frame 6 "
       "with 25%. If frame 6 already has a key valued 3, it becomes the previous "
       "anchor and the same button gives 4.75 (3 + 25% of the way to 10).",
       "Breakdown Core"),
    _H("op.animassist.breakdown_offset",
       "Relative Offset",
       "Add a relative offset after the breakdown",
       "Adds a numeric offset to the currently evaluated value at the target frame "
       "instead of blending between neighbours. Useful for nudging a key without "
       "touching the blend factor.",
       "Breakdown Core"),
    _H("op.animassist.breakdown_batch_frames",
       "Batch Over Selected Frames",
       "Run the current breakdown on every selected key frame",
       "Reads the set of selected key frames and runs the current breakdown "
       "recipe at each one in turn. Respects the active mask and exclusion set. "
       "Large selections can be slow — watch the console.",
       "Breakdown Core"),
    _H("op.animassist.breakdown_numeric",
       "Numeric Breakdown",
       "Enter an explicit factor and frame, then apply",
       "Opens a numeric prompt for factor, frame, and mode and runs a single "
       "breakdown. The most precise entry point when you already know the exact "
       "percentage you want.",
       "Breakdown Core"),
    _H("op.animassist.breakdown_repeat_last",
       "Repeat Last Breakdown",
       "Re-run the most recent breakdown recipe",
       "Re-runs the last breakdown recipe (factor, mode, mask) on the current "
       "selection. Useful when stepping frame-by-frame through a block.",
       "Breakdown Core"),

    # ====================================================================
    # Breakdown Subsets
    # ====================================================================
    _H("op.animassist.breakdown_transform_only",
       "Transform Only",
       "Breakdown on transform channels only",
       "Applies the breakdown only to location, rotation, and scale channels, "
       "leaving custom properties untouched.",
       "Breakdown Subsets"),
    _H("op.animassist.breakdown_rotation_only",
       "Rotation Only",
       "Breakdown on rotation channels only",
       "Applies the breakdown only to rotation channels (Euler and quaternion). "
       "Location and scale are left untouched.",
       "Breakdown Subsets"),
    _H("op.animassist.breakdown_location_only",
       "Location Only",
       "Breakdown on location channels only",
       "Applies the breakdown only to location channels. Rotation and scale are "
       "left untouched.",
       "Breakdown Subsets"),
    _H("op.animassist.breakdown_scale_only",
       "Scale Only",
       "Breakdown on scale channels only",
       "Applies the breakdown only to scale channels. Location and rotation are "
       "left untouched.",
       "Breakdown Subsets"),
    _H("op.animassist.breakdown_selected_controls",
       "Selected Controls Only",
       "Restrict breakdown to currently selected controls",
       "Limits the breakdown target set to the currently selected pose bones or "
       "objects. When nothing is selected the operator cancels with a report.",
       "Breakdown Subsets"),
    _H("op.animassist.breakdown_channel_subset",
       "Custom Channel Subset",
       "Breakdown on a user-defined channel mask",
       "Runs the breakdown using the kind and per-axis checkboxes on the breakdown"
       "mask panel. Combine with the exclusion set for precise scoping.",
       "Breakdown Subsets"),
    _H("prop.p3_mask_axis",
       "Per-Axis Masking",
       "Checkbox row for per-axis breakdown masking",
       "Per-axis checkboxes let you restrict a breakdown to, for example, only the "
       "Y component of location channels. Axis indices map to 0=X, 1=Y, 2=Z, and "
       "3=W for quaternion channels.",
       "Breakdown Subsets"),
    _H("prop.p3_skip_locked",
       "Ignore Locked Axes",
       "Skip fcurves whose lock flag is set",
       "When enabled, the breakdown engine silently skips any fcurve with its lock "
       "flag set so locked transforms stay untouched.",
       "Breakdown Subsets"),
    _H("prop.p3_respect_exclusions",
       "Respect Exclusion Set",
       "Honour the active breakdownexclusion set",
       "When enabled, every fcurve whose data_path matches any pattern in the "
       "active exclusion set is skipped by every breakdownbreakdown operator.",
       "Breakdown Subsets"),

    # ====================================================================
    # Inbetween Tools
    # ====================================================================
    _H("op.animassist.inbetween_selected_gap",
       "Inbetween in Selected Gap",
       "Insert an inbetween inside the selected key gap",
       "Detects the gap between the two currently selected keys on each fcurve "
       "and inserts a fresh inbetween using the factor on the breakdownpanel. "
       "Ignores fcurves that do not have exactly two selected keys.",
       "Inbetween Tools"),
    _H("op.animassist.inbetween_distribute",
       "Evenly Distribute Inbetweens",
       "Distribute N inbetweens evenly inside the selected gap",
       "Inserts ``Inbetween Count`` keys evenly spaced inside the gap between the "
       "two selected keys on each fcurve. Uses the active interpolation options.",
       "Inbetween Tools"),
    _H("op.animassist.inbetween_on_clusters",
       "Inbetween on Key Clusters",
       "Insert inbetweens on every selected key cluster",
       "Walks the selected keys, groups consecutive keys into clusters, and "
       "inserts inbetweens between clusters. Useful for cleaning up rough block "
       "passes where you blocked with multiple keys per pose.",
       "Inbetween Tools"),
    _H("prop.p3_inbetween_count",
       "Inbetween Count",
       "Number of inbetweens to insert",
       "Controls how many inbetween keys the Evenly Distribute and Clusters "
       "operators insert inside each gap.",
       "Inbetween Tools"),

    # ====================================================================
    # Pose Compare
    # ====================================================================
    _H("op.animassist.pose_snapshot_prev",
       "Snapshot Previous Pose",
       "Snapshot the pose at the previous key as 'previous'",
       "Walks every fcurve on the active object, evaluates its value at the "
       "previous key frame, and stores the result in the Previous slot of the "
       "pose compare state. Used by the Pose Compare Report.",
       "Pose Compare"),
    _H("op.animassist.pose_snapshot_next",
       "Snapshot Next Pose",
       "Snapshot the pose at the next key as 'next'",
       "Walks every fcurve on the active object, evaluates its value at the "
       "next key frame, and stores the result in the Next slot of the pose "
       "compare state.",
       "Pose Compare"),
    _H("op.animassist.pose_snapshot_reference",
       "Snapshot Reference Pose",
       "Snapshot the current pose as a reference",
       "Stores the current-frame pose as a reference that other breakdown tools "
       "can blend toward. Used by Blend Toward Reference.",
       "Pose Compare"),
    _H("op.animassist.pose_compare_report",
       "Pose Compare Report",
       "Report differences between the previous and next pose snapshots",
       "Reports channel-by-channel differences between the Previous and Next "
       "pose snapshots in the Info editor, with a one-row summary box shown on "
       "the breakdownpanel.",
       "Pose Compare"),
    _H("op.animassist.breakdown_from_clipboard",
       "Breakdown From Clipboard A/B",
       "Blend toward pose A or pose B from the snapshot clipboard",
       "Uses the Previous (A) and Next (B) pose snapshots as the blend targets "
       "instead of the nearest keys. Runs the breakdown at the current frame.",
       "Pose Compare"),
    _H("op.animassist.blend_toward_reference",
       "Blend Toward Reference",
       "Blend the current frame toward the reference pose",
       "Blends the current-frame pose toward the stored reference snapshot by "
       "the current factor. Useful for gradually pulling a frame back to a "
       "canonical pose without resetting it.",
       "Pose Compare"),

    # ====================================================================
    # Breakdown Presets
    # ====================================================================
    _H("op.animassist.apply_preset",
       "Apply Breakdown Preset",
       "Apply the selected breakdown preset",
       "Applies the built-in preset selected on the breakdownpanel. Each preset "
       "bundles a factor, mode, and mask kind so you can swap between common "
       "pose-to-pose recipes with one click.",
       "Breakdown Presets"),
    _H("op.animassist.save_preset",
       "Save Current As Preset",
       "Save the current settings as a user preset",
       "Captures the current factor, mode, and mask kind into a new user preset "
       "stored on the Scene. User presets persist across save/reload alongside "
       "the blend file.",
       "Breakdown Presets"),
    _H("op.animassist.delete_preset",
       "Delete User Preset",
       "Delete the active user preset",
       "Removes the active user preset from the Scene. Built-in presets cannot "
       "be deleted.",
       "Breakdown Presets"),
    _H("op.animassist.manage_exclusion_set",
       "Manage Exclusion Set",
       "Add or remove exclusion-set entries",
       "Adds or removes an fcurve data_path substring from the breakdownexclusion "
       "set. Fcurves matching any pattern are skipped by every breakdownbreakdown "
       "operator.",
       "Breakdown Presets"),

    # ====================================================================
    # Interpolation Options
    # ====================================================================
    _H("prop.p3_quaternion_aware",
       "Quaternion-Aware Interpolation",
       "True slerp across all four quaternion components",
       "When enabled, rotation_quaternion channels are blended with a true slerp "
       "across all four components so the resulting rotation never flips "
       "mid-arc. Strongly recommended for any rig using quaternion rotations.",
       "Interpolation Options"),
    _H("prop.p3_euler_wrap_aware",
       "Euler Continuity",
       "Pick the shortest arc for Euler rotations",
       "When enabled, Euler rotations that cross a ±π boundary take the shortest "
       "path instead of the long way round.",
       "Interpolation Options"),
    _H("prop.p3_visual_transform",
       "Visual Transform",
       "Sample the final evaluated curve value",
       "When enabled, the breakdown samples ``fcurve.evaluate()`` at the target "
       "frame instead of linearly interpolating between neighbour keys. Useful "
       "for constrained rigs where the visible pose diverges from the raw key "
       "values.",
       "Interpolation Options"),
    _H("prop.p3_space_toggle",
       "Local / World Computation",
       "Transform space for visual sampling",
       "Switches visual-transform sampling between the channel's own local "
       "space and world space. The world branch converts the sampled value back "
       "into the channel space when possible.",
       "Interpolation Options"),
    _H("prop.p3_preserve_world_contact",
       "Preserve World Contact",
       "Best-effort world-space contact preservation",
       "When enabled, the breakdown attempts to keep world-space contacts "
       "(feet, hands) stable. Depends heavily on rig setup and constraint "
       "topology.",
       "Interpolation Options"),
    _H("prop.p3_preserve_child_contact",
       "Preserve Child Contact",
       "Best-effort child contact preservation",
       "When enabled, the breakdown attempts to keep parented child-object "
       "contacts stable. Depends on rig setup.",
       "Interpolation Options"),
    _H("prop.p3_match_tangents",
       "Preserve Tangent Continuity",
       "Copy handle types from the closer neighbour",
       "When enabled, the new breakdown key inherits its handle type from the "
       "closer neighbour key so the resulting curve flows cleanly instead of "
       "defaulting to Auto Clamped.",
       "Interpolation Options"),
    _H("prop.p3_auto_key_missing",
       "Auto-Key Missing Channels",
       "Seed anchor keys on empty channels",
       "When enabled, channels with no neighbouring keys receive an anchor key "
       "at their currently evaluated value so the breakdown has something to "
       "blend off next time.",
       "Interpolation Options"),

    # ====================================================================
    # Modal Breakdown
    # ====================================================================
    _H("op.animassist.modal_drag_breakdown",
       "Modal Drag Breakdown",
       "Interactive drag to set the breakdown factor",
       "Enter modal mode and drag the mouse horizontally to scrub the breakdown "
       "factor between the previous and next pose. Release LMB to apply; RMB / Esc "
       "cancels and restores the pre-drag key state, including selection and type. "
       + BREAKDOWN_ANCHOR_HINT,
       "Modal Breakdown"),
    _H("op.animassist.preview_breakdown",
       "Preview Breakdown",
       "Stage a preview breakdown before committing",
       "Writes a preview breakdown at the current frame without marking it as "
       "committed. Animators can inspect the result and either press Commit "
       "Preview to keep it or run any other operator to discard it.",
       "Modal Breakdown"),
    _H("op.animassist.commit_preview",
       "Commit Preview",
       "Commit the staged preview breakdown",
       "Marks the currently staged preview breakdown as committed so it is no "
       "longer rolled back by the next preview operator.",
       "Modal Breakdown"),
)


def register() -> None:
    """Register breakdown help entries into the Help Browser registry.

    Called during addon initialization so breakdown operators and properties
    appear in the context-sensitive Help Browser documentation.
    """
    register_phase_help(_PHASE, PHASE3_ENTRIES)


def unregister() -> None:
    """Unregister breakdown help entries from the Help Browser registry.

    Called during addon teardown to clean up help documentation.
    """
    unregister_phase_help(_PHASE)
