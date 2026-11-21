# --- OFFSET TOOLS ---
"""Help entries for animation offset and transform operators.

45 entries — one per offset feature. Category names
match the groupings the animator sees in the sidebar panel so the
Help Browser and the panel UI stay in sync.

Every id uses the ``op.animassist.<name>`` convention for operator
helps (so ``explained_op`` can auto-resolve the icon) or
``prop.p4_<name>`` for property helps.
"""

from __future__ import annotations

import re

from .help_registry import (
    HelpEntry,
    register_phase_help,
    unregister_phase_help,
)

__all__ = [
    "PHASE4_ENTRIES",
    "register",
    "unregister",
]

_PHASE = "phase4"


def _H(id_: str, label: str, tooltip: str, description: str, category: str) -> HelpEntry:
    return HelpEntry(
        id=id_,
        label=label,
        tooltip=tooltip,
        description=description,
        phase=_PHASE,
        category=category,
    )


PHASE4_ENTRIES: tuple[HelpEntry, ...] = (
    # ====================================================================
    # Transform Nudge
    # ====================================================================
    _H("op.animassist.p4_nudge_current",
       "Nudge Current Frame",
       "Apply a keyed transform offset at the current frame",
       "Applies the current translate, rotate, and scale amounts to every selected "
       "target at the scene's current frame. Honours channel mask, space, pivot, "
       "preserve-contact, and mirror-sign options. Writes keys only on channels "
       "that already have a key unless Auto-Key Missing is enabled.",
       "Transform Nudge"),
    _H("op.animassist.p4_offset_selected",
       "Offset Selected Keys",
       "Apply a transform offset to every selected key",
       "Walks every selected keyframe point on the target channels and applies "
       "the offset delta at that frame. Falloff and mirror sign are applied per "
       "frame. Frames without any selected key are skipped entirely.",
       "Transform Nudge"),

    # ====================================================================
    # Push/Pull
    # ====================================================================
    _H("op.animassist.p4_push_x",
       "Push X",
       "Push selected targets on the X axis",
       "Applies a positive translation delta on X using the current push/pull "
       "amount. Space, falloff, and mirror sign apply. Useful for adding "
       "overshoot and snappier anticipation on sideways motion.",
       "Push/Pull"),
    _H("op.animassist.p4_push_y",
       "Push Y",
       "Push selected targets on the Y axis",
       "Applies a positive translation delta on Y using the current push/pull "
       "amount. Space, falloff, and mirror sign apply.",
       "Push/Pull"),
    _H("op.animassist.p4_push_z",
       "Push Z",
       "Push selected targets on the Z axis",
       "Applies a positive translation delta on Z. Space, falloff, and mirror "
       "sign apply. Common for adding vertical overshoot on jumps and squashes.",
       "Push/Pull"),
    _H("op.animassist.p4_pull_x",
       "Pull X",
       "Pull selected targets on the X axis",
       "Applies a negative translation delta on X using the current push/pull "
       "amount. Inverse of Push X.",
       "Push/Pull"),
    _H("op.animassist.p4_pull_y",
       "Pull Y",
       "Pull selected targets on the Y axis",
       "Applies a negative translation delta on Y. Inverse of Push Y.",
       "Push/Pull"),
    _H("op.animassist.p4_pull_z",
       "Pull Z",
       "Pull selected targets on the Z axis",
       "Applies a negative translation delta on Z. Inverse of Push Z.",
       "Push/Pull"),

    # ====================================================================
    # Space Modes
    # ====================================================================
    _H("prop.p4_space_local",
       "Local Space",
       "Interpret offsets in the target's own basis",
       "The fastest space because no conversion is performed. Offsets feed "
       "straight into location / rotation / scale channels. Best for "
       "per-bone-local pose tweaks.",
       "Space Modes"),
    _H("prop.p4_space_world",
       "World Space",
       "Interpret offsets in world coordinates",
       "Offsets are rotated from world space into the target's basis before "
       "being written. Use this when you want a single direction (e.g. +Z up) "
       "to mean the same thing regardless of how a bone is rotated.",
       "Space Modes"),
    _H("prop.p4_space_parent",
       "Parent Space",
       "Interpret offsets in the parent's space",
       "Offsets are converted from the parent bone or parent object's local "
       "space into the target's basis. Useful for propagating a consistent "
       "nudge down a chain.",
       "Space Modes"),
    _H("prop.p4_space_visual",
       "Visual Space",
       "Interpret offsets in depsgraph-evaluated world space",
       "Identical to World Space but the world matrix is read from the "
       "depsgraph-evaluated object, so constraints and drivers contribute to "
       "the reference frame. Writes still land on the basis channels.",
       "Space Modes"),
    _H("prop.p4_space_gimbal",
       "Gimbal Space",
       "Rotation-only mode aligned to the current rotation order",
       "Rotation deltas are applied axis-aligned in the target's own rotation "
       "order. Useful for keeping euler curves clean when tweaking a single "
       "axis. Falls back to Local Space on quaternion targets.",
       "Space Modes"),

    # ====================================================================
    # Axis Filtering
    # ====================================================================
    _H("op.animassist.p4_offset_translate_only",
       "Translation Only",
       "Offset only translation channels",
       "Applies the current translate delta and ignores rotation and scale "
       "amounts. Equivalent to setting channel mask to Translation and running "
       "Nudge.",
       "Axis Filtering"),
    _H("op.animassist.p4_offset_rotate_only",
       "Rotation Only",
       "Offset only rotation channels",
       "Applies the current rotate delta and ignores translation and scale.",
       "Axis Filtering"),
    _H("op.animassist.p4_offset_scale_only",
       "Scale Only",
       "Offset only scale channels",
       "Applies the current scale delta and ignores translation and rotation.",
       "Axis Filtering"),
    _H("op.animassist.p4_offset_trs_combined",
       "Combined TRS",
       "Offset translation, rotation, and scale in one pass",
       "Applies the full T+R+S delta in one atomic write. Use for compound "
       "pose tweaks where you want the whole offset to land as a single undo "
       "step.",
       "Axis Filtering"),

    # ====================================================================
    # Offset Targets
    # ====================================================================
    _H("prop.p4_selected_channels_only",
       "Selected Channels Only",
       "Limit offsets to selected fcurves",
       "When on, only fcurves whose keyframe points are selected in the Dope "
       "Sheet or Graph Editor are written. Safer for surgical edits.",
       "Offset Targets"),
    _H("prop.p4_selected_targets_only",
       "Selected Targets Only",
       "Limit offsets to selected bones or objects",
       "Targets are always resolved from the current selection — this entry "
       "documents that behavior for the Help Browser.",
       "Offset Targets"),
    _H("prop.p4_keyed_channels_only",
       "Keyed Channels Only",
       "Skip channels that have no keys",
       "Prevents creating new fcurves during an offset. Recommended for "
       "polishing passes where you only want to modify existing keys.",
       "Offset Targets"),

    # ====================================================================
    # Pivot Modes
    # ====================================================================
    _H("prop.p4_pivot_average",
       "Median of Selection",
       "Use the average origin as the pivot",
       "Rotation and scale offsets rotate and scale around the averaged origin "
       "of the selected targets.",
       "Pivot Modes"),
    _H("prop.p4_pivot_active",
       "Active Target Pivot",
       "Use the active target as the pivot",
       "Rotation and scale offsets rotate and scale around the active object "
       "or active pose bone, regardless of how many other targets are selected.",
       "Pivot Modes"),
    _H("prop.p4_pivot_individual",
       "Individual Origins",
       "Each target pivots around its own origin",
       "Default mode. Each selected target is offset independently around its "
       "own origin. Best for mass pose tweaks.",
       "Pivot Modes"),
    _H("prop.p4_pivot_custom",
       "Custom Pivot Point",
       "Use an explicit custom pivot vector",
       "Rotation and scale offsets use the world-space custom pivot set on "
       "the offsetpanel. Useful for rotating a group around a scene landmark.",
       "Pivot Modes"),
    _H("prop.p4_pivot_cursor",
       "3D Cursor Pivot",
       "Use the 3D cursor as the pivot",
       "Rotation and scale offsets pivot around the scene's 3D cursor.",
       "Pivot Modes"),
    _H("prop.p4_pivot_bone_head",
       "Active Bone Head",
       "Use the active bone's head as the pivot",
       "Only meaningful in Pose Mode. Rotation and scale offsets pivot around "
       "the head of the active pose bone.",
       "Pivot Modes"),
    _H("prop.p4_pivot_bone_tail",
       "Active Bone Tail",
       "Use the active bone's tail as the pivot",
       "Only meaningful in Pose Mode. Rotation and scale offsets pivot around "
       "the tail of the active pose bone.",
       "Pivot Modes"),

    # ====================================================================
    # Offset Presets
    # ====================================================================
    _H("op.animassist.p4_apply_preset",
       "Apply Preset",
       "Multiply the entered offset by a preset factor and apply",
       "Applies the currently selected transform multiplier preset (Tiny / "
       "Small / Normal / Big / Huge) to the entered offset amounts and runs "
       "Nudge Current Frame.",
       "Offset Presets"),
    _H("prop.p4_fine_step",
       "Fine Step",
       "Multiply offset amounts by 0.1 for fine nudges",
       "When on, every offset operator reduces its entered amounts by a factor "
       "of ten. Modal drag also honours this while Shift is held.",
       "Offset Presets"),
    _H("op.animassist.p4_reapply_last",
       "Reapply Last",
       "Run the most recent offset with the same delta",
       "Re-runs the most recent offset request with identical amounts, space, "
       "pivot, scope, and falloff. Useful for stepping through a sequence of "
       "identical nudges.",
       "Offset Presets"),
    _H("op.animassist.p4_invert_last",
       "Invert Last",
       "Run the most recent offset with the sign flipped",
       "Negates every T/R/S component of the most recent offset and re-runs "
       "with the same options. Effectively an explicit 'undo the offset' that "
       "survives non-offset edits in between.",
       "Offset Presets"),

    # ====================================================================
    # Falloff
    # ====================================================================
    _H("prop.p4_falloff_linear",
       "Linear Falloff",
       "Triangular weight peaking at the window midpoint",
       "Offsets ramp in from 0 at the window start to 1 at the midpoint and "
       "back to 0 at the window end.",
       "Falloff"),
    _H("prop.p4_falloff_ease_in",
       "Ease-In Distribution",
       "Distributes the offset amount as a quadratic ease-in",
       "Applies less of the offset at the start of the window and more at the "
       "end. Does not modify fcurve tangents — it only weights the amount of "
       "the delta applied per frame.",
       "Falloff"),
    _H("prop.p4_falloff_ease_out",
       "Ease-Out Distribution",
       "Distributes the offset amount as a quadratic ease-out",
       "Applies more of the offset at the start of the window and less at the "
       "end. Does not modify fcurve tangents.",
       "Falloff"),
    _H("prop.p4_falloff_bell",
       "Bell Falloff",
       "Smooth cosine bell peaking at the midpoint",
       "Offset weight rises smoothly from zero at each edge of the window to "
       "full weight at the midpoint. Use for tapered nudges over a range.",
       "Falloff"),
    _H("prop.p4_frame_range_falloff",
       "Frame Range Falloff",
       "Constrain falloff to an explicit frame range",
       "Sets Scope to Frame Range and uses Range Start / Range End as the "
       "falloff window regardless of which keys are currently selected.",
       "Falloff"),

    # ====================================================================
    # Modal Offset
    # ====================================================================
    _H("op.animassist.p4_modal_offset",
       "Modal Drag Offset",
       "Drag to offset interactively with live preview",
       "Invokes a modal drag: mouse X maps to horizontal delta, mouse Y to "
       "vertical delta, Shift for fine, Ctrl for coarse, LMB or Enter to "
       "commit, RMB or Esc to cancel. On cancel the scene is restored to its "
       "pre-drag state.",
       "Modal Offset"),
    _H("prop.p4_modal_screen_h",
       "Screen-Space Horizontal Drag",
       "Mouse X drives horizontal offset",
       "While modal, the horizontal mouse movement is mapped to the horizontal "
       "offset axis in the current space.",
       "Modal Offset"),
    _H("prop.p4_modal_screen_v",
       "Screen-Space Vertical Drag",
       "Mouse Y drives vertical offset",
       "While modal, the vertical mouse movement is mapped to the vertical "
       "offset axis in the current space.",
       "Modal Offset"),
    _H("prop.p4_modal_commit_cancel",
       "Commit / Cancel",
       "LMB or Enter commits, RMB or Esc cancels",
       "Commit finalises the offset and records it as Last Offset. Cancel "
       "restores every affected fcurve to its exact pre-drag state using the "
       "snapshot taken on invoke.",
       "Modal Offset"),
    _H("prop.p4_modal_numeric_entry",
       "Numeric Offset Entry",
       "Type an exact delta during modal drag",
       "While in modal drag, typing digits, minus, and dot populates a numeric "
       "buffer shown in the header. Enter commits the typed value as the exact "
       "offset and exits modal.",
       "Modal Offset"),
    _H("prop.p4_modal_preview_ghost",
       "Preview Ghost",
       "Non-destructive live preview during modal drag",
       "Shows the current delta in the area header while modal drag is active. "
       "All fcurve writes are reversible by cancelling — the scene is never "
       "committed until the user releases with LMB or Enter.",
       "Modal Offset"),

    # ====================================================================
    # Safety / mirror
    # ====================================================================
    _H("prop.p4_auto_key_missing",
       "Auto-Key Missing",
       "Create new keys on channels without a key at the target frame",
       "When on, offsetinserts a new key on channels that do not already have "
       "one at the affected frame. Off by default to keep offsets strictly "
       "additive to your existing pose.",
       "Offset Targets"),
    _H("prop.p4_preserve_contact",
       "Preserve Contact Axis",
       "Zero one translation axis before applying",
       "Forces the translation delta on one axis to zero before the pipeline "
       "runs. Use Preserve Z to keep feet planted while nudging sideways.",
       "Offset Targets"),
    _H("prop.p4_safety_filters",
       "Locked & Muted Safety Filters",
       "Never modify locked or muted channels",
       "The Skip Locked and Skip Muted filters are on by default. Turning them "
       "off lets offsets write through locked or muted fcurves — do so "
       "deliberately.",
       "Offset Targets"),
    _H("prop.p4_mirror_sign",
       "Mirror Sign by Name",
       "Negate the offset on mirrored targets",
       "When enabled, any target whose name contains a recognised side token "
       "(.L/.R, _L/_R, Left/Right) on the mirrored side receives the delta "
       "negated on the configured mirror axis.",
       "Offset Targets"),
)


def _sanity_check() -> None:
    """Register-time safeguard: every id must match ``phase_4`` convention
    and every category must be from the spec list."""
    allowed = {
        "Transform Nudge",
        "Push/Pull",
        "Space Modes",
        "Axis Filtering",
        "Offset Targets",
        "Pivot Modes",
        "Falloff",
        "Modal Offset",
        "Offset Presets",
    }
    id_re = re.compile(r"^(op\.animassist\.p4_|prop\.p4_)[a-z0-9_]+$")
    seen_ids: set[str] = set()
    for entry in PHASE4_ENTRIES:
        if not id_re.match(entry.id):
            raise ValueError(f"offsethelp id is not well-formed: {entry.id!r}")
        if entry.id in seen_ids:
            raise ValueError(f"Duplicate offsethelp id: {entry.id!r}")
        seen_ids.add(entry.id)
        if entry.category not in allowed:
            raise ValueError(
                f"offsethelp entry {entry.id!r} has unknown category "
                f"{entry.category!r}"
            )


def register() -> None:
    """Register offset help entries into the Help Browser registry.

    Called during addon initialization so offset operators and properties
    appear in the context-sensitive Help Browser documentation.
    Runs sanity checks on entry categories to catch configuration errors early.
    """
    _sanity_check()
    register_phase_help(_PHASE, PHASE4_ENTRIES)


def unregister() -> None:
    """Unregister offset help entries from the Help Browser registry.

    Called during addon teardown to clean up help documentation.
    """
    unregister_phase_help(_PHASE)


__all__ = [
    "PHASE4_ENTRIES",
    "register",
    "unregister",
]
