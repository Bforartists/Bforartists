# --- OFFSET TOOLS ---
"""Scene-scoped PropertyGroup for offset and transform settings.

Mounted on :class:`bpy.types.Scene` under the attribute
``anim_assist_p4`` so it does not collide with the core
``anim_assist`` or breakdown tool ``anim_assist_p3``.

Every user-facing property carries a meaningful ``description=`` string
per the UI/UX directive.
"""

from __future__ import annotations

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
)

from .p4_presets import preset_enum_items_callback
from .p4_space import space_enum_items

P4_SCENE_ATTR = "anim_assist_p4"

__all__ = [
    "P4_SCENE_ATTR",
    "AA_P4_Properties",
    "CLASSES",
    "register_properties",
    "unregister_properties",
    "get_p4",
]


# ---------------------------------------------------------------------------
# Enum item tables (module-level constants for Blender retention safety)
# ---------------------------------------------------------------------------

CHANNEL_MASK_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("T", "Translation", "Offset only translation channels (location)."),
    ("R", "Rotation", "Offset only rotation channels (euler or quaternion)."),
    ("S", "Scale", "Offset only scale channels."),
    ("TRS", "Translation + Rotation + Scale", "Offset every transform channel."),
)


SCOPE_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("CURRENT_FRAME", "Current Frame",
     "Apply the offset at the scene's current frame only."),
    ("SELECTED_KEYS", "Selected Keys",
     "Apply the offset to every selected keyframe on the target channels."),
    ("FRAME_RANGE", "Frame Range",
     "Apply the offset to every key inside an explicit frame range."),
)


# R2 audit fix: Only INDIVIDUAL is currently wired through the pipeline.
# Pivot-relative rotation/scale orbiting is not yet implemented, so the
# remaining modes are kept here commented-out for future use but hidden
# from the UI to avoid dead switches.
PIVOT_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("INDIVIDUAL", "Individual Origins",
     "Each target rotates and scales around its own origin — the default for pose workflows."),
    # TODO: implement pivot-relative rotation/scale orbit, then
    # re-enable these modes.
    # ("AVERAGE", "Median of Selection",
    #  "Use the average of all selected target origins as the pivot."),
    # ("ACTIVE", "Active Target",
    #  "Use the active target's origin as the pivot for every offset."),
    # ("CURSOR", "3D Cursor",
    #  "Use the 3D cursor as the pivot point."),
    # ("CUSTOM", "Custom Point",
    #  "Use the custom pivot vector set on the offset panel."),
    # ("BONE_HEAD", "Active Bone Head",
    #  "Use the active pose bone's head as the pivot."),
    # ("BONE_TAIL", "Active Bone Tail",
    #  "Use the active pose bone's tail as the pivot."),
)


FALLOFF_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("NONE", "None",
     "Every affected frame receives the full offset — no falloff."),
    ("LINEAR", "Linear",
     "Triangular weight peaking at the window midpoint, fading to zero at the edges."),
    ("EASE_IN", "Ease In (Distribution)",
     (
        "Distributes the offset amount as an ease-in curve: small at the start, "
        "full at the end. Does not touch fcurve tangents."
     )),
    ("EASE_OUT", "Ease Out (Distribution)",
     (
        "Distributes the offset amount as an ease-out curve: full at the start, "
        "small at the end. Does not touch fcurve tangents."
     )),
    ("BELL", "Bell",
     "Smooth cosine bell: zero at the edges, full at the midpoint."),
)


PRESERVE_CONTACT_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("NONE", "None",
     "No axis is locked. All three translation axes are offset."),
    ("X", "Preserve X",
     (
        "Force the X translation component of every offset to zero. "
        "Useful for keeping foot contacts glued sideways."
     )),
    ("Y", "Preserve Y",
     "Force the Y translation component of every offset to zero."),
    ("Z", "Preserve Z",
     (
        "Force the Z translation component of every offset to zero. "
        "The most common setting for keeping feet planted."
     )),
)


MIRROR_AXIS_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("X", "X", "Flip the X component of the delta on mirrored targets."),
    ("Y", "Y", "Flip the Y component of the delta on mirrored targets."),
    ("Z", "Z", "Flip the Z component of the delta on mirrored targets."),
)


def _channel_mask_items(self, context):  # noqa: ARG001
    return CHANNEL_MASK_ITEMS


def _scope_items(self, context):  # noqa: ARG001
    return SCOPE_ITEMS


def _pivot_items(self, context):  # noqa: ARG001
    return PIVOT_ITEMS


def _falloff_items(self, context):  # noqa: ARG001
    return FALLOFF_ITEMS


def _preserve_contact_items(self, context):  # noqa: ARG001
    return PRESERVE_CONTACT_ITEMS


def _mirror_axis_items(self, context):  # noqa: ARG001
    return MIRROR_AXIS_ITEMS


# ---------------------------------------------------------------------------
# Main PropertyGroup
# ---------------------------------------------------------------------------

class AA_P4_Properties(bpy.types.PropertyGroup):
    """Scene-scoped defaults for the offsetoffset toolkit."""

    # --- Offset amounts ---------------------------------------------------
    translate_amount: FloatVectorProperty(  # type: ignore[valid-type]
        name="Translate Δ",
        description="Translation delta applied by offset operators before space conversion.",
        size=3,
        default=(0.0, 0.0, 0.0),
        subtype="TRANSLATION",
    )
    rotate_amount: FloatVectorProperty(  # type: ignore[valid-type]
        name="Rotate Δ",
        description=(
            "Rotation delta in radians applied by offset operators "
            "before space conversion."
        ),
        size=3,
        default=(0.0, 0.0, 0.0),
        subtype="EULER",
    )
    scale_amount: FloatVectorProperty(  # type: ignore[valid-type]
        name="Scale Δ",
        description="Scale delta applied additively on top of the current scale channels.",
        size=3,
        default=(0.0, 0.0, 0.0),
    )
    push_amount: FloatProperty(  # type: ignore[valid-type]
        name="Push/Pull Amount",
        description="Magnitude used by the Push X/Y/Z and Pull X/Y/Z one-click buttons.",
        default=0.1, min=0.0, soft_max=10.0,
    )

    # --- Channel & scope filters -----------------------------------------
    channel_mask: EnumProperty(  # type: ignore[valid-type]
        name="Channels",
        description="Which transform channels receive the offset.",
        items=_channel_mask_items,
    )
    scope: EnumProperty(  # type: ignore[valid-type]
        name="Scope",
        description=(
            "Whether the offset writes at the current frame, across "
            "selected keys, or over an explicit frame range."
        ),
        items=_scope_items,
    )
    selected_channels_only: BoolProperty(  # type: ignore[valid-type]
        name="Selected Channels Only",
        description=(
            "Restrict offsets to fcurves whose keyframe points are selected "
            "in the Dope Sheet or Graph Editor."
        ),
        default=False,
    )
    keyed_channels_only: BoolProperty(  # type: ignore[valid-type]
        name="Keyed Channels Only",
        description=(
            "Restrict offsets to fcurves that already have keyframes. "
            "Prevents creating keys on untouched channels."
        ),
        default=True,
    )
    skip_locked: BoolProperty(  # type: ignore[valid-type]
        name="Skip Locked",
        description=(
            "Do not modify fcurves marked as locked in the Dope Sheet or "
            "Graph Editor."
        ),
        default=True,
    )
    skip_muted: BoolProperty(  # type: ignore[valid-type]
        name="Skip Muted",
        description="Do not modify fcurves marked as muted.",
        default=True,
    )
    auto_key_missing: BoolProperty(  # type: ignore[valid-type]
        name="Auto-Key Missing",
        description=(
            "Insert new keys on targeted channels that do not have a key "
            "at the current frame. Off by default to respect the user's "
            "existing pose."
        ),
        default=False,
    )

    # --- Range & falloff --------------------------------------------------
    range_start: FloatProperty(  # type: ignore[valid-type]
        name="Range Start",
        description="First frame of the explicit frame-range scope.",
        default=1.0,
    )
    range_end: FloatProperty(  # type: ignore[valid-type]
        name="Range End",
        description="Last frame of the explicit frame-range scope.",
        default=24.0,
    )
    falloff_shape: EnumProperty(  # type: ignore[valid-type]
        name="Falloff",
        description=(
            "How the offset amount is distributed across the affected frame "
            "window. Does not modify fcurve tangents."
        ),
        items=_falloff_items,
    )

    # --- Space & pivot ----------------------------------------------------
    space: EnumProperty(  # type: ignore[valid-type]
        name="Space",
        description=(
            "Reference space in which the offset amounts are interpreted "
            "before being converted to the target's basis."
        ),
        items=space_enum_items,
    )
    pivot_mode: EnumProperty(  # type: ignore[valid-type]
        name="Pivot",
        description="Pivot point used for rotation and scale offsets.",
        items=_pivot_items,
    )
    custom_pivot: FloatVectorProperty(  # type: ignore[valid-type]
        name="Custom Pivot",
        description="World-space custom pivot point. Only used when pivot mode is Custom Point.",
        size=3,
        default=(0.0, 0.0, 0.0),
        subtype="TRANSLATION",
    )

    # --- Contact / mirror -------------------------------------------------
    preserve_contact_axis: EnumProperty(  # type: ignore[valid-type]
        name="Preserve Contact",
        description=(
            "Zero the translation delta on one axis before applying. "
            "Keeps foot contacts planted when nudging elsewhere."
        ),
        items=_preserve_contact_items,
    )
    mirror_sign_enabled: BoolProperty(  # type: ignore[valid-type]
        name="Mirror Sign",
        description=(
            "Negate the offset on the configured axis for targets whose name "
            "indicates the mirrored side (.L / .R / Left / Right)."
        ),
        default=False,
    )
    mirror_axis: EnumProperty(  # type: ignore[valid-type]
        name="Mirror Axis",
        description="Which axis of the delta is negated on mirrored targets.",
        items=_mirror_axis_items,
    )

    # --- Stepping & presets -----------------------------------------------
    fine_step: BoolProperty(  # type: ignore[valid-type]
        name="Fine Step",
        description=(
            "Multiply every offset amount by 0.1 for fine nudging. "
            "Modal drag also uses this when Shift is held."
        ),
        default=False,
    )
    active_preset: EnumProperty(  # type: ignore[valid-type]
        name="Preset",
        description="Transform multiplier preset applied on top of the entered offset amounts.",
        items=preset_enum_items_callback,
    )

    # --- Modal preview state ----------------------------------------------
    modal_preview_active: BoolProperty(  # type: ignore[valid-type]
        name="Modal Preview Active",
        description="Internal: true while a modal offset drag is in progress.",
        default=False,
    )


CLASSES: tuple[type, ...] = (
    AA_P4_Properties,
)


def register_properties() -> None:
    """Attach offset PropertyGroup to Scene so offset tool state persists with the .blend file."""
    bpy.types.Scene.anim_assist_p4 = bpy.props.PointerProperty(  # type: ignore[attr-defined]
        type=AA_P4_Properties,
        name="Anim Assist Offset Tools",
        description="Scene-scoped defaults for the Anim Assist offset toolkit.",
    )


def unregister_properties() -> None:
    """Detach offset PropertyGroup from Scene on addon unregister."""
    if hasattr(bpy.types.Scene, "anim_assist_p4"):
        try:
            del bpy.types.Scene.anim_assist_p4  # type: ignore[attr-defined]
        except Exception:  # pragma: no cover
            pass


def get_p4(context: bpy.types.Context) -> AA_P4_Properties | None:
    """Get the offset properties from context, or None if unavailable."""
    scene = getattr(context, "scene", None)
    if scene is None:
        return None
    return getattr(scene, P4_SCENE_ATTR, None)
