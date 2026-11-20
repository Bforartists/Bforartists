# --- ANIMATION LAYERS HELP ENTRIES ---
"""Help entries for animation layers and advanced layer workflows.

Provides HelpEntry records covering all animation layer features, organized
into categories that align with the panel section structure.
"""

from __future__ import annotations

from .help_registry import HelpEntry, register_phase_help, unregister_phase_help

__all__ = [
    "PHASE11_ENTRIES",
    "register",
    "unregister",
]

_PHASE = "phase11"


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
#   Layer Stack, Blend Modes, Part Assignment, Layer States,
#   Blend & Merge, Presets, Editing
# ---------------------------------------------------------------------------

PHASE11_ENTRIES: tuple[HelpEntry, ...] = (
    # ── Layer Stack ──────────────────────────────────────────────────────
    _H(
        "p11.layers_enabled",
        "Enable Animation Layers",
        "Master toggle for the animation layer system",
        "Master toggle for the animation layer system.  When disabled, "
        "only the object's base Action is used.  Enable this to start "
        "layering animations on top of each other — similar to Maya's "
        "Animation Layer stack or Blender's NLA strips, but with "
        "direct keyframe editing per layer.",
        "Layer Stack",
    ),
    _H(
        "p11.edit_active_only",
        "Edit Active Layer Only",
        "Keyframe insertion only affects bones assigned to the active layer",
        "When enabled, keyframe insertion and posing only affect bones "
        "assigned to the active layer.  Bones not assigned to the active "
        "layer are read-only.  This is the core of part-based editing: "
        "put arms on one layer, legs on another, and edit each in isolation "
        "without accidentally modifying the other.\n\n"
        "Inspired by Maya's 'Selected Layer' editing mode where keyframes "
        "only go to the currently active animation layer.",
        "Layer Stack",
    ),
    _H(
        "p11.auto_assign_on_key",
        "Auto-Assign on Key",
        "Automatically assign a bone to the active layer when keyed",
        "When enabled, inserting a keyframe on a bone that is NOT assigned "
        "to the active layer will automatically add that bone to the layer.  "
        "This provides a convenient workflow: just start animating and bones "
        "are added to your active layer as you key them.\n\n"
        "Disable this for strict layer control where you explicitly assign "
        "bones before keying.",
        "Layer Stack",
    ),

    # ── Blend Modes ──────────────────────────────────────────────────────
    _H(
        "p11.blend_mode",
        "Layer Blend Mode",
        "Controls how a layer's values combine with layers below it",
        "Controls how a layer's values combine with layers below it:\n\n"
        "OVERRIDE — Lerp between the base and layer values.  At 100% weight "
        "the layer fully replaces the base.  Standard for primary poses.\n\n"
        "ADDITIVE — Layer values are added ON TOP of the base as deltas from "
        "the rest pose.  Ideal for secondary motion, breathing, overlap, "
        "and adjustments that should combine with any base animation.\n\n"
        "MULTIPLY — Scale existing animation values.  Useful for dampening "
        "or amplifying motion on specific parts.\n\n"
        "COMBINE — NLA-style: location adds, rotation concatenates, scale "
        "multiplies.  Matches Blender's NLA Combine strip type.",
        "Blend Modes",
    ),
    _H(
        "p11.weight",
        "Layer Weight / Influence",
        "Controls the strength of this layer's contribution (0-100%)",
        "Controls the strength of this layer's contribution (0%–100%).  "
        "Drag this slider to blend between having no effect (0%) and "
        "full contribution (100%).  This is the primary way to create "
        "seamless partial animations — e.g. set an arm correction layer "
        "to 60% to only partially apply the fix.\n\n"
        "Per-channel weight overrides (in Advanced) let you set different "
        "weights for location vs rotation vs scale on individual bones.",
        "Blend Modes",
    ),

    # ── Part Assignment ──────────────────────────────────────────────────
    _H(
        "p11.assigned_bones",
        "Assigned Bones / Parts",
        "The bones (body parts) that this layer is allowed to edit",
        "The bones (body parts) that this layer is allowed to edit.  "
        "When empty, the layer affects ALL bones (whole-body layer).\n\n"
        "Assign bones to create part-specific layers:\n"
        "  - Upper body layer (spine, arms, head)\n"
        "  - Lower body layer (hips, legs, feet)\n"
        "  - Face layer (facial bones)\n"
        "  - Fingers layer\n\n"
        "With 'Edit Active Only' enabled, you can only key bones that "
        "are assigned to the active layer.  This prevents accidental "
        "edits to other body parts while you work.",
        "Part Assignment",
    ),
    _H(
        "p11.channel_overrides",
        "Per-Channel Weight Overrides",
        "Fine-grained weight control per bone per channel",
        "Fine-grained control over blend weights per bone per channel.  "
        "For example, you might want a layer's location changes at 100% "
        "but its rotation at only 50% on a specific bone.\n\n"
        "Add overrides for individual bones when the global layer weight "
        "doesn't give you enough control.  Leave a bone without an "
        "override to use the layer's global weight.",
        "Part Assignment",
    ),
    _H(
        "p11.preset_upper_lower",
        "Upper / Lower Body Preset",
        "Auto-partition rig into upper and lower body layers",
        "Creates a two-layer setup: Upper Body (spine and above) and "
        "Lower Body (hips and below).  The split point is auto-detected "
        "from the rig hierarchy.  Useful for blocking body mechanics "
        "on separate layers.",
        "Part Assignment",
    ),

    # ── Layer States ─────────────────────────────────────────────────────
    _H(
        "p11.solo",
        "Solo Layer",
        "Only evaluate this layer (and the base layer)",
        "When solo is enabled, ONLY this layer (and the base layer) are "
        "evaluated.  All other layers are temporarily muted.  This is "
        "useful for isolating a layer to see its contribution in "
        "isolation.\n\n"
        "If multiple layers have solo enabled, all soloed layers "
        "are evaluated.",
        "Layer States",
    ),
    _H(
        "p11.mute",
        "Mute Layer",
        "Temporarily disable a layer without removing it",
        "Temporarily disable a layer without removing it.  The layer's "
        "keyframes and settings are preserved but it has no effect on "
        "the final result.  Toggle mute to A/B compare with and "
        "without a layer's contribution.",
        "Layer States",
    ),
    _H(
        "p11.locked",
        "Lock Layer",
        "Prevent any editing on this layer",
        "Prevent any editing on this layer.  Keyframe insertion, "
        "deletion, and value changes are blocked.  Use this to protect "
        "approved animation while you work on other layers.",
        "Layer States",
    ),

    # ── Blend & Merge ────────────────────────────────────────────────────
    _H(
        "op.animassist.p11_merge_down",
        "Merge Layer Down",
        "Bake the current layer into the one below",
        "Bakes the current layer's contribution into the layer below it.  "
        "The blend mode and weight are evaluated at every keyed frame, "
        "and the combined result is written into the lower layer's Action.  "
        "The upper layer is then removed.\n\n"
        "Use this to 'commit' a layer when you're happy with the blend.",
        "Blend & Merge",
    ),
    _H(
        "op.animassist.p11_flatten_all",
        "Flatten All Layers",
        "Collapse the entire layer stack into the base layer",
        "Collapses the entire layer stack into the base layer.  "
        "All layers are merged from top to bottom, evaluating blend "
        "modes and weights.  The result is a single Action with the "
        "combined animation.\n\n"
        "WARNING: This is destructive — layer separation is lost.",
        "Blend & Merge",
    ),
    _H(
        "op.animassist.p11_blend_layers",
        "Blend Between Layers",
        "Interactive slider to blend between two layers",
        "Interactive slider that blends between two layers.  "
        "Select a source and target layer, then drag the factor "
        "to interpolate between them.  Useful for creating in-between "
        "poses across layer variations.\n\n"
        "Rotation uses quaternion slerp for smooth interpolation.",
        "Blend & Merge",
    ),

    # ── Editing ──────────────────────────────────────────────────────────
    _H(
        "p11.layer_scope",
        "Layer Scope",
        "Controls which transform channels this layer affects",
        "Controls which transform channels this layer affects:\n\n"
        "ALL — Location, rotation, and scale.\n"
        "LOCATION ONLY — Only location channels.\n"
        "ROTATION ONLY — Only rotation channels.\n"
        "SCALE ONLY — Only scale channels.\n"
        "CUSTOM — Use a comma-separated filter string.\n\n"
        "Combined with part assignment, this gives very precise control "
        "over what a layer can modify.",
        "Editing",
    ),
)


def register() -> None:
    """Register animation layer help entries into the Help Browser registry.

    Called during addon initialization so animation layer operators and properties
    appear in the context-sensitive Help Browser documentation.
    """
    register_phase_help(_PHASE, PHASE11_ENTRIES)


def unregister() -> None:
    """Unregister animation layer help entries from the Help Browser registry.

    Called during addon teardown to clean up help documentation.
    """
    unregister_phase_help(_PHASE)
