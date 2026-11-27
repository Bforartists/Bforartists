"""Help entries for mirroring, pair detection, and symmetry helpers.

Provides 45 HelpEntry records covering all mirroring and symmetry features, organized
into 8 categories that align with the panel section structure.
"""

from __future__ import annotations

from .help_registry import HelpEntry, register_phase_help, unregister_phase_help

__all__ = [
    "PHASE9_ENTRIES",
    "register",
    "unregister",
]

_PHASE = "phase9"


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
#   Pair Detection, Opposite Selection, Mirror Transforms,
#   Mirror Scope, Mirror Space, Pair Management,
#   Batch Mirror, Mirror Diagnostics
# ---------------------------------------------------------------------------

PHASE9_ENTRIES: tuple[HelpEntry, ...] = (
    # ── Pair Detection ────────────────────────────────────────────────────
    _H(
        "op.animassist.p9_detect_dot_lr",
        "Detect .L/.R",
        "Detect pairs using .L/.R suffix convention",
        "Scans the armature for bones whose names end in .L or .R and builds "
        "a mapping of opposite sides.  Case-sensitive.  Useful for rigs "
        "following Blender's standard naming convention.",
        "Pair Detection",
    ),
    _H(
        "op.animassist.p9_detect_under_lr",
        "Detect _L/_R",
        "Detect pairs using _L/_R suffix convention",
        "Scans the armature for bones whose names end in _L or _R and builds "
        "a mapping of opposite sides.  Case-sensitive.  Common in many "
        "production rigs.",
        "Pair Detection",
    ),
    _H(
        "op.animassist.p9_detect_word_lr",
        "Detect Left/Right",
        "Detect pairs using Left/Right word convention",
        "Scans for bones containing the words 'Left' or 'Right' and builds "
        "a reverse mapping.  Case-insensitive.  Supports variations like "
        "'Arm_Left' or 'LeftFinger'.",
        "Pair Detection",
    ),
    _H(
        "op.animassist.p9_custom_pattern",
        "Custom Pattern",
        "Define a custom naming pattern for pair detection",
        "Opens a dialog to specify a regex pattern or custom naming rule for "
        "detecting bone pairs.  Allows flexibility for non-standard naming "
        "conventions specific to your rig.",
        "Pair Detection",
    ),
    _H(
        "op.animassist.p9_build_cache",
        "Build Pair Cache",
        "Build and cache the opposite target mapping",
        "Runs a pair-detection pass using the currently selected pattern "
        "and stores the mapping in memory.  This cache is used by all "
        "mirror operations to look up opposite-side bones.",
        "Pair Detection",
    ),

    # ── Opposite Selection ────────────────────────────────────────────────
    _H(
        "op.animassist.p9_select_opposite",
        "Select Opposite",
        "Select the opposite-side bone of the active",
        "Deselects all bones and selects only the opposite-side pair of the "
        "currently active bone.  Requires a valid pair cache.  Useful for "
        "switching focus between left and right sides.",
        "Opposite Selection",
    ),
    _H(
        "op.animassist.p9_add_opposite",
        "Add Opposite",
        "Add opposite bones to the current selection",
        "For each selected bone with a known opposite, adds that opposite "
        "to the selection (multi-select).  Keeps existing selections intact.  "
        "Useful for creating symmetric selections.",
        "Opposite Selection",
    ),
    _H(
        "op.animassist.p9_swap_selection",
        "Swap Selection",
        "Swap active and opposite bone selection",
        "Exchanges the active bone with its opposite-side pair.  All other "
        "selections remain unchanged.  The opposite becomes the new active "
        "and active becomes a regular selection.",
        "Opposite Selection",
    ),

    # ── Mirror Transforms ──────────────────────────────────────────────────
    _H(
        "op.animassist.p9_match_to_opposite",
        "Match to Opposite",
        "Match active transform to its opposite",
        "Copies the transform values from the opposite-side bone to the "
        "active bone, including any mirroring of rotation axes if needed.  "
        "Does not affect keyframes, only changes the current pose.",
        "Mirror Transforms",
    ),
    _H(
        "op.animassist.p9_match_opposite_to_active",
        "Match Opposite to Active",
        "Match opposite transform to active",
        "Copies the transform values from the active bone to its opposite, "
        "with automatic axis flipping for rotation.  Useful for creating "
        "symmetric poses by starting with one side.",
        "Mirror Transforms",
    ),
    _H(
        "op.animassist.p9_mirror_pose",
        "Mirror Pose",
        "Mirror the current pose to opposite side",
        "Applies mirroring to all bones in the armature that have a known "
        "opposite pair.  Bones without pairs are left unchanged.  Respects "
        "the current axis mask and transform space settings.",
        "Mirror Transforms",
    ),
    _H(
        "op.animassist.p9_mirror_selected",
        "Mirror Selected",
        "Mirror only selected bones to their opposites",
        "Iterates through selected bones, finds their opposites, and applies "
        "mirroring.  Unselected bones are unaffected.  Useful for mirroring "
        "only part of the pose.",
        "Mirror Transforms",
    ),
    _H(
        "op.animassist.p9_mirror_location",
        "Mirror Location",
        "Mirror location channels only",
        "Mirrors only the position (XYZ location) across the pair axis, "
        "leaving rotation and scale unchanged.  Respects per-axis filtering.",
        "Mirror Transforms",
    ),
    _H(
        "op.animassist.p9_mirror_rotation",
        "Mirror Rotation",
        "Mirror rotation channels only",
        "Mirrors only the rotation (Euler angles) by flipping the side axes "
        "and negating them if needed, leaving location and scale unchanged.",
        "Mirror Transforms",
    ),
    _H(
        "op.animassist.p9_mirror_scale",
        "Mirror Scale",
        "Mirror scale channels only",
        "Mirrors only the scale, typically by negating the side axis.  "
        "Location and rotation are left unchanged.  Less common than location "
        "and rotation mirroring.",
        "Mirror Transforms",
    ),

    # ── Mirror Scope ───────────────────────────────────────────────────────
    _H(
        "p9_axis_mask",
        "Axis Mask",
        "Per-axis enable/disable mask for mirror operations",
        "Checkboxes for X, Y, and Z axes.  When unchecked, that axis is "
        "skipped during mirroring.  Combines with channel mode to give "
        "fine-grained control over which components are affected.",
        "Mirror Scope",
    ),
    _H(
        "op.animassist.p9_naming_exceptions",
        "Naming Exceptions",
        "Table of bone name overrides",
        "Opens a UI table where you can manually specify which bones pair "
        "with which, overriding automatic detection.  Useful for rigs with "
        "naming inconsistencies or special cases.",
        "Mirror Scope",
    ),
    _H(
        "op.animassist.p9_mirror_frame",
        "Mirror Frame",
        "Mirror at the current frame only",
        "Applies mirroring only to the playhead's current frame.  No keyframes "
        "are inserted unless auto-key is enabled.  Useful for tweaking a "
        "single frame.",
        "Mirror Scope",
    ),
    _H(
        "op.animassist.p9_mirror_range",
        "Mirror Range",
        "Mirror across a selected key range",
        "Identifies the frame range of all selected keyframes and applies "
        "mirroring at every frame in that range.  Produces a symmetric "
        "animation across the selection.",
        "Mirror Scope",
    ),
    _H(
        "op.animassist.p9_mirror_preview",
        "Mirror Preview Range",
        "Mirror across the scene preview range",
        "Uses the scene's preview/playback range (or the full frame range if "
        "no preview is set) and mirrors at every frame.  Ideal for processing "
        "an entire shot.",
        "Mirror Scope",
    ),
    _H(
        "op.animassist.p9_mirror_keyed_only",
        "Mirror Keyed Only",
        "Only mirror channels with keyframes",
        "When enabled, the mirror operation skips frames where a channel has "
        "no keyframe.  Prevents creating unintended new animation on "
        "non-keyed channels.",
        "Mirror Scope",
    ),
    _H(
        "op.animassist.p9_mirror_visible_only",
        "Mirror Visible Only",
        "Only mirror visible channels",
        "Respects Blender's channel hide/show toggles in the Graph Editor "
        "or Dopesheet.  Hidden channels are not mirrored.",
        "Mirror Scope",
    ),

    # ── Mirror Space ───────────────────────────────────────────────────────
    _H(
        "p9_mirror_local",
        "Local Space Mirror",
        "Mirror using local bone space",
        "Performs mirroring in the local space of each bone (relative to its "
        "parent).  This is the default for FK rigs and typical animation "
        "workflows.",
        "Mirror Space",
    ),
    _H(
        "p9_mirror_world",
        "World Space Mirror",
        "Mirror using world space coordinates",
        "Performs mirroring in world space, ignoring the bone hierarchy.  "
        "Useful for root-level controls or when you want absolute positioning.",
        "Mirror Space",
    ),
    _H(
        "op.animassist.p9_visual_mirror",
        "Visual Mirror",
        "Mirror using evaluated visual matrices for constrained rigs",
        "Uses the depsgraph-evaluated visual matrices that account for all "
        "constraints and drivers.  The most accurate option for complex rigs "
        "with heavy constraints.",
        "Mirror Space",
    ),
    _H(
        "op.animassist.p9_mirror_with_offset",
        "Mirror With Offset",
        "Mirror while preserving existing offset",
        "Computes the mirror but preserves any existing offset between the "
        "active and opposite bones.  Useful when you want to maintain a "
        "deliberate asymmetry.",
        "Mirror Space",
    ),
    _H(
        "op.animassist.p9_mirror_without_offset",
        "Mirror Without Offset",
        "Mirror with exact value match",
        "Forces an exact mirror with zero offset, overriding any existing "
        "asymmetry.  Use for a clean symmetric result.",
        "Mirror Space",
    ),

    # ── Pair Management ────────────────────────────────────────────────────
    _H(
        "op.animassist.p9_swap_poses",
        "Swap L/R Poses",
        "Swap all left and right bone poses",
        "Exchanges the transforms of every left-right bone pair, including "
        "location, rotation, and scale.  Useful for compositing or reference "
        "work.",
        "Pair Management",
    ),
    _H(
        "op.animassist.p9_pair_manager",
        "Pair Manager",
        "UI for managing bone pair mappings",
        "Opens a dedicated panel where you can view, edit, add, and delete "
        "bone pair overrides.  Provides a centralized interface for all "
        "pair-related settings.",
        "Pair Management",
    ),
    _H(
        "op.animassist.p9_add_pair_override",
        "Add Pair Override",
        "Add a manual bone pair mapping",
        "Manually specify that bone A pairs with bone B, overriding automatic "
        "detection.  Useful for rigs with irregular naming or non-standard "
        "symmetry.",
        "Pair Management",
    ),
    _H(
        "op.animassist.p9_save_pair_preset",
        "Save Pair Preset",
        "Save current pair mapping as a preset",
        "Stores the current pair detection settings and any manual overrides "
        "as a named preset on the scene.  Presets persist with the .blend "
        "and speed up setup for new shots.",
        "Pair Management",
    ),
    _H(
        "op.animassist.p9_mirror_switch_targets",
        "Mirror Switch Targets",
        "Mirror the target of a constraint to its opposite bone",
        "On the active bone, finds a constraint pointing to a target and "
        "repoints it to the opposite-side target.  Useful for swapping IK "
        "targets between limbs.",
        "Pair Management",
    ),
    _H(
        "op.animassist.p9_mirror_proxy_helpers",
        "Mirror Proxy Helpers",
        "Mirror proxy or helper bone configurations to the opposite side",
        "Clones proxy/helper bone setups from one side to the other, "
        "adjusting names and parent relationships appropriately.",
        "Pair Management",
    ),
    _H(
        "op.animassist.p9_mirror_selection_sets",
        "Mirror Selection Sets",
        "Duplicate a selection set to the opposite side",
        "Takes a selection set on one side (e.g., 'Arm_L_All') and creates "
        "a mirrored version on the opposite side (e.g., 'Arm_R_All').",
        "Pair Management",
    ),
    _H(
        "op.animassist.p9_nav_next_unpaired",
        "Next Unpaired",
        "Jump to the next bone without a detected pair",
        "Moves the selection to the next bone that could not be paired.  "
        "Useful for systematically fixing naming issues in the rig.",
        "Pair Management",
    ),
    _H(
        "op.animassist.p9_validate_pairs",
        "Validate Pairs",
        "Check for missing or ambiguous pair mappings",
        "Generates a report listing bones without pairs, bones with multiple "
        "possible pairs, and inconsistencies.  Helps identify rig naming "
        "problems.",
        "Pair Management",
    ),

    # ── Batch Mirror ───────────────────────────────────────────────────────
    _H(
        "op.animassist.p9_batch_mirror",
        "Batch Mirror",
        "Mirror across all selected bones",
        "Iterates through every selected bone, finds its opposite, and applies "
        "mirroring.  Unselected bones are unaffected.  Respects axis mask "
        "and transform space settings.",
        "Batch Mirror",
    ),
    _H(
        "op.animassist.p9_batch_mirror_active_side",
        "Mirror Active Side",
        "Mirror all bones from the active bone's side",
        "Determines whether the active bone is on the left or right side, then "
        "mirrors all bones on that same side to the opposite.  Useful for "
        "mirroring an entire limb at once.",
        "Batch Mirror",
    ),
    _H(
        "op.animassist.p9_channel_resolver",
        "Channel Resolver",
        "Resolve opposite-side channel mappings",
        "Analyzes which channels (Loc X/Y/Z, Rot X/Y/Z, Scale X/Y/Z) exist on "
        "opposite bones and determines how to map them correctly.  Handles "
        "rigs with selective channel visibility.",
        "Batch Mirror",
    ),
    _H(
        "op.animassist.p9_mirror_metadata",
        "Mirror Metadata",
        "Mirror relevant metadata alongside transforms",
        "Copies custom properties, marker data, or other metadata from the "
        "active bone to its opposite.  Preserves secondary data during "
        "mirroring operations.",
        "Batch Mirror",
    ),
    _H(
        "op.animassist.p9_mirror_preset_values",
        "Mirror Preset Values",
        "Mirror transform preset values",
        "For bones with stored preset transforms, mirrors the preset values "
        "to the opposite side.  Useful for syncing rest poses or animation "
        "templates.",
        "Batch Mirror",
    ),
    _H(
        "op.animassist.p9_repeat_mirror",
        "Repeat Last Mirror",
        "Repeat the most recent mirror operation",
        "Re-applies the last mirror operation (same settings, scope, and space) "
        "to the current selection.  Useful for applying the same mirror "
        "multiple times.",
        "Batch Mirror",
    ),

    # ── Mirror Diagnostics ─────────────────────────────────────────────────
    _H(
        "op.animassist.p9_mirror_report",
        "Mirror Report",
        "Per-target summary of mirror results",
        "After a mirror operation, generates a detailed report listing each "
        "bone, its opposite, the transform values applied, and any warnings.  "
        "Copies the report to the clipboard.",
        "Mirror Diagnostics",
    ),
    _H(
        "op.animassist.p9_missing_warning",
        "Missing Opposite",
        "Warning for bones without a detected pair",
        "Alerts when a selected or mirrored bone has no known opposite.  "
        "Provides suggestions for fixing the naming or adding a manual override.",
        "Mirror Diagnostics",
    ),
    _H(
        "op.animassist.p9_ambiguous_warning",
        "Ambiguous Pair",
        "Warning for bones with multiple possible pairs",
        "Alerts when a bone's naming pattern matches multiple candidates on "
        "the opposite side.  Suggests resolving ambiguity via manual overrides.",
        "Mirror Diagnostics",
    ),
)


def register() -> None:
    """Register mirroring help entries into the Help Browser registry.

    Called during addon initialization so mirroring operators and properties
    appear in the context-sensitive Help Browser documentation.
    """
    register_phase_help(_PHASE, PHASE9_ENTRIES)


def unregister() -> None:
    """Unregister mirroring help entries from the Help Browser registry.

    Called during addon teardown to clean up help documentation.
    """
    unregister_phase_help(_PHASE)
