# --- BREAKDOWN TOOLS ---
"""Breakdown operators (Features 1–15, 22–29, 41, 42).

Every operator is a thin shell:
    1. resolve scene + object + optional bones,
    2. build a ``BreakdownOptions`` from the Scene PropertyGroup
       (optionally overriding mask / factor / mode),
    3. call ``breakdown_core.apply_breakdown``,
    4. remember the options for Repeat Last,
    5. report the result through ``self.report``.

All operators declare ``bl_options = {"REGISTER", "UNDO"}`` so Blender's
undo stack wraps their effects. None of them mutate scene state outside
``apply_breakdown`` + Repeat Last memory.
"""

from __future__ import annotations

from typing import Iterable, Optional

import bpy
from bpy.props import EnumProperty, FloatProperty, IntProperty

from .. import constants

from ..core import breakdown_core as bc
from ..core.breakdown_masks import BreakdownMask, ExclusionSet
from ..core.fcurve_compat import get_fcurves
from ..core.p3_properties import get_p3


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _resolve_target(context: bpy.types.Context):
    """Return ``(obj, bone_names_or_None)`` or ``(None, None)``."""
    obj = getattr(context, "active_object", None)
    if obj is None:
        return None, None
    if obj.type == "ARMATURE" and obj.mode == "POSE":
        sel = getattr(context, "selected_pose_bones", None) or []
        if sel:
            return obj, [b.name for b in sel]
        active = getattr(context, "active_pose_bone", None)
        if active is not None:
            return obj, [active.name]
        return obj, None  # no bones selected → object-level fcurves
    return obj, None


def _exclusion_from_scene(p3) -> ExclusionSet | None:
    if p3 is None or not p3.respect_exclusions:
        return None
    patterns = tuple(
        p.pattern for p in p3.exclusion_patterns if p.pattern.strip()
    )
    if not patterns:
        return None
    return ExclusionSet(name="scene", patterns=patterns)


def _mask_from_scene(p3, *, override: BreakdownMask | None = None) -> BreakdownMask:
    if override is not None:
        return override
    if p3 is None:
        return BreakdownMask()
    axes = set()
    if p3.mask_axis_x:
        axes.add(0)
    if p3.mask_axis_y:
        axes.add(1)
    if p3.mask_axis_z:
        axes.add(2)
    if p3.mask_axis_w:
        axes.add(3)
    return BreakdownMask(
        location=bool(p3.mask_location),
        rotation=bool(p3.mask_rotation),
        scale=bool(p3.mask_scale),
        custom=bool(p3.mask_custom),
        axes=frozenset(axes) or frozenset({0, 1, 2, 3}),
        skip_locked=bool(p3.skip_locked),
    )


def _options_from_scene(
    context: bpy.types.Context,
    *,
    factor: Optional[float] = None,
    mode: Optional[str] = None,
    mask_override: Optional[BreakdownMask] = None,
    target_frame: Optional[float] = None,
) -> bc.BreakdownOptions:
    p3 = get_p3(context)
    return bc.BreakdownOptions(
        factor=float(factor) if factor is not None else float(p3.factor if p3 else 0.5),
        mode=mode or (p3.mode if p3 else bc.MODE_REPLACE),
        mask=_mask_from_scene(p3, override=mask_override),
        exclusion=_exclusion_from_scene(p3),
        space=(p3.space if p3 else bc.SPACE_LOCAL),
        visual_transform=bool(p3.visual_transform) if p3 else False,
        quaternion_aware=bool(p3.quaternion_aware) if p3 else True,
        euler_wrap_aware=bool(p3.euler_wrap_aware) if p3 else True,
        preserve_world_contact=bool(p3.preserve_world_contact) if p3 else False,
        preserve_child_contact=bool(p3.preserve_child_contact) if p3 else False,
        match_tangents=bool(p3.match_tangents) if p3 else True,
        auto_key_missing=bool(p3.auto_key_missing) if p3 else False,
        target_frame=target_frame,
        offset_amount=float(p3.offset_amount) if p3 else 0.0,
        push_strength=float(p3.push_strength) if p3 else 1.25,
        pull_strength=float(p3.pull_strength) if p3 else 0.75,
    )


def _run(
    self: bpy.types.Operator,
    context: bpy.types.Context,
    options: bc.BreakdownOptions,
    *,
    frames: Optional[Iterable[float]] = None,
) -> set[str]:
    obj, bones = _resolve_target(context)
    if obj is None:
        self.report({"WARNING"}, "No active object.")
        return {"CANCELLED"}
    adata = getattr(obj, "animation_data", None)
    if adata is None or adata.action is None:
        self.report({"WARNING"}, f"{obj.name}: no action.")
        return {"CANCELLED"}

    result = bc.apply_breakdown(
        context, obj, bones, options, frames=frames
    )
    bc.remember_last(options)
    msg = result.messages[-1] if result.messages else "Done."
    self.report({"INFO"}, msg)
    return {"FINISHED"}


def _poll_animated(cls, context: bpy.types.Context) -> bool:
    obj = getattr(context, "active_object", None)
    if obj is None:
        cls.poll_message_set("Select an animated object to insert a breakdown")
        return False
    adata = getattr(obj, "animation_data", None)
    if adata is None or adata.action is None:
        cls.poll_message_set("Add keyframes to the active object before inserting a breakdown")
        return False
    return True


# ---------------------------------------------------------------------------
# Core breakdown operators
# ---------------------------------------------------------------------------

class AA_OT_breakdown_current_frame(bpy.types.Operator):
    bl_idname = "animassist.breakdown_current_frame"
    bl_label = "Breakdown at Current Frame"
    bl_description = (
        "Insert a weighted breakdown key at the current frame on every "
        "targeted fcurve using the breakdown factor slider"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _poll_animated(cls, context)

    def execute(self, context):
        return _run(self, context, _options_from_scene(context))


class AA_OT_breakdown_weighted(bpy.types.Operator):
    bl_idname = "animassist.breakdown_weighted"
    bl_label = "Weighted Previous/Next"
    bl_description = (
        "Weighted breakdown reading the factor slider live so it can be "
        "scrubbed through repeat-last"
    )
    bl_options = {"REGISTER", "UNDO"}

    factor: FloatProperty(  # type: ignore[valid-type]
        name="Factor",
        description="Override factor for this run. 0 favours the previous pose, 1 favours the next.",
        default=0.5, min=-1.0, max=2.0,
    )

    @classmethod
    def poll(cls, context):
        return _poll_animated(cls, context)

    def execute(self, context):
        return _run(self, context, _options_from_scene(context, factor=self.factor))


class AA_OT_breakdown_favor_prev(bpy.types.Operator):
    bl_idname = "animassist.breakdown_favor_prev"
    bl_label = "Favor Previous Pose"
    bl_description = "Breakdown heavily biased toward the previous pose (factor 0.25)"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _poll_animated(cls, context)

    def execute(self, context):
        return _run(self, context, _options_from_scene(context, factor=0.25))


class AA_OT_breakdown_favor_next(bpy.types.Operator):
    bl_idname = "animassist.breakdown_favor_next"
    bl_label = "Favor Next Pose"
    bl_description = "Breakdown heavily biased toward the next pose (factor 0.75)"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _poll_animated(cls, context)

    def execute(self, context):
        return _run(self, context, _options_from_scene(context, factor=0.75))


class AA_OT_breakdown_midpoint(bpy.types.Operator):
    bl_idname = "animassist.breakdown_midpoint"
    bl_label = "Midpoint Breakdown"
    bl_description = "Write a clean 50/50 midpoint breakdown at the current frame"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _poll_animated(cls, context)

    def execute(self, context):
        return _run(self, context, _options_from_scene(context, factor=0.5))


class AA_OT_breakdown_push_prev(bpy.types.Operator):
    bl_idname = "animassist.breakdown_push_prev"
    bl_label = "Push From Previous"
    bl_description = "Extrapolate past the previous pose using the Push Strength setting"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _poll_animated(cls, context)

    def execute(self, context):
        return _run(self, context, _options_from_scene(context, mode=bc.MODE_PUSH_PREV))


class AA_OT_breakdown_push_next(bpy.types.Operator):
    bl_idname = "animassist.breakdown_push_next"
    bl_label = "Push Into Next"
    bl_description = "Extrapolate past the next pose using the Push Strength setting"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _poll_animated(cls, context)

    def execute(self, context):
        return _run(self, context, _options_from_scene(context, mode=bc.MODE_PUSH_NEXT))


class AA_OT_breakdown_pull_prev(bpy.types.Operator):
    bl_idname = "animassist.breakdown_pull_prev"
    bl_label = "Pull To Previous"
    bl_description = "Soften the breakdown toward the previous pose using Pull Strength"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _poll_animated(cls, context)

    def execute(self, context):
        return _run(self, context, _options_from_scene(context, mode=bc.MODE_PULL_PREV))


class AA_OT_breakdown_pull_next(bpy.types.Operator):
    bl_idname = "animassist.breakdown_pull_next"
    bl_label = "Pull To Next"
    bl_description = "Soften the breakdown toward the next pose using Pull Strength"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _poll_animated(cls, context)

    def execute(self, context):
        return _run(self, context, _options_from_scene(context, mode=bc.MODE_PULL_NEXT))


class AA_OT_breakdown_percentage(bpy.types.Operator):
    bl_idname = "animassist.breakdown_percentage"
    bl_label = "Quick Percentage Breakdown"
    bl_description = (
        "Write a breakdown at a fixed percentage on the active object's Action "
        "using Breakdown targets and mask. " + constants.BREAKDOWN_ANCHOR_HINT
    )
    bl_options = {"REGISTER", "UNDO"}

    percent: IntProperty(  # type: ignore[valid-type]
        name="Percent",
        description="Fixed breakdown percentage, 0 favours the previous pose and 100 favours the next.",
        default=50, min=0, max=100,
    )

    @classmethod
    def poll(cls, context):
        return _poll_animated(cls, context)

    def execute(self, context):
        return _run(
            self, context,
            _options_from_scene(context, factor=float(self.percent) / 100.0),
        )


class AA_OT_breakdown_offset(bpy.types.Operator):
    bl_idname = "animassist.breakdown_offset"
    bl_label = "Relative Offset"
    bl_description = "Add a relative offset to the currently evaluated value at the target frame"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _poll_animated(cls, context)

    def execute(self, context):
        return _run(self, context, _options_from_scene(context, mode=bc.MODE_OFFSET))


class AA_OT_breakdown_batch_frames(bpy.types.Operator):
    bl_idname = "animassist.breakdown_batch_frames"
    bl_label = "Batch Over Selected Frames"
    bl_description = (
        "Run the current breakdown recipe at every selected key frame "
        "across the active action"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _poll_animated(cls, context)

    def execute(self, context):
        obj, _ = _resolve_target(context)
        if obj is None or obj.animation_data is None or obj.animation_data.action is None:
            self.report({"WARNING"}, "No animated object.")
            return {"CANCELLED"}
        frames: set[float] = set()
        for fc in get_fcurves(obj.animation_data.action, anim_data=obj.animation_data):
            for kp in fc.keyframe_points:
                if kp.select_control_point:
                    frames.add(float(kp.co[0]))
        if not frames:
            self.report({"WARNING"}, "No selected keys to batch over.")
            return {"CANCELLED"}
        return _run(
            self, context,
            _options_from_scene(context),
            frames=sorted(frames),
        )


class AA_OT_breakdown_numeric(bpy.types.Operator):
    bl_idname = "animassist.breakdown_numeric"
    bl_label = "Numeric Breakdown"
    bl_description = "Enter an explicit factor, frame and mode then apply a single breakdown"
    bl_options = {"REGISTER", "UNDO"}

    factor: FloatProperty(  # type: ignore[valid-type]
        name="Factor",
        description="Blend factor. 0 favours the previous pose, 1 favours the next.",
        default=0.5, min=-1.0, max=2.0,
    )
    target_frame: FloatProperty(  # type: ignore[valid-type]
        name="Frame",
        description="Frame at which to insert the new breakdown key.",
        default=1.0,
    )
    mode: EnumProperty(  # type: ignore[valid-type]
        name="Mode",
        description="Blend mode for this numeric breakdown.",
        items=(
            ("REPLACE", "Replace", "Clean blend"),
            ("OFFSET", "Offset", "Offset current value"),
            ("PUSH_PREV", "Push Prev", "Extrapolate past prev"),
            ("PUSH_NEXT", "Push Next", "Extrapolate past next"),
            ("PULL_PREV", "Pull Prev", "Soften toward prev"),
            ("PULL_NEXT", "Pull Next", "Soften toward next"),
        ),
        default="REPLACE",
    )

    @classmethod
    def poll(cls, context):
        return _poll_animated(cls, context)

    def invoke(self, context, event):
        self.target_frame = float(context.scene.frame_current_final)
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        opts = _options_from_scene(
            context, factor=self.factor, mode=self.mode, target_frame=self.target_frame,
        )
        return _run(self, context, opts)


class AA_OT_breakdown_repeat_last(bpy.types.Operator):
    bl_idname = "animassist.breakdown_repeat_last"
    bl_label = "Repeat Last Breakdown"
    bl_description = "Re-run the most recent breakdown recipe on the current selection"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _poll_animated(cls, context) and bc.get_last() is not None

    def execute(self, context):
        last = bc.get_last()
        if last is None:
            self.report({"WARNING"}, "No previous breakdown to repeat.")
            return {"CANCELLED"}
        return _run(self, context, last)


# ---------------------------------------------------------------------------
# Subset breakdown operators
# ---------------------------------------------------------------------------

class AA_OT_breakdown_transform_only(bpy.types.Operator):
    bl_idname = "animassist.breakdown_transform_only"
    bl_label = "Transform Only"
    bl_description = "Apply the current breakdown to transform channels only (location, rotation, scale)"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _poll_animated(cls, context)

    def execute(self, context):
        return _run(
            self, context,
            _options_from_scene(context, mask_override=BreakdownMask.transform_only()),
        )


class AA_OT_breakdown_rotation_only(bpy.types.Operator):
    bl_idname = "animassist.breakdown_rotation_only"
    bl_label = "Rotation Only"
    bl_description = "Apply the current breakdown to rotation channels only"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _poll_animated(cls, context)

    def execute(self, context):
        return _run(
            self, context,
            _options_from_scene(context, mask_override=BreakdownMask.rotation_only()),
        )


class AA_OT_breakdown_location_only(bpy.types.Operator):
    bl_idname = "animassist.breakdown_location_only"
    bl_label = "Location Only"
    bl_description = "Apply the current breakdown to location channels only"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _poll_animated(cls, context)

    def execute(self, context):
        return _run(
            self, context,
            _options_from_scene(context, mask_override=BreakdownMask.location_only()),
        )


class AA_OT_breakdown_scale_only(bpy.types.Operator):
    bl_idname = "animassist.breakdown_scale_only"
    bl_label = "Scale Only"
    bl_description = "Apply the current breakdown to scale channels only"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _poll_animated(cls, context)

    def execute(self, context):
        return _run(
            self, context,
            _options_from_scene(context, mask_override=BreakdownMask.scale_only()),
        )


class AA_OT_breakdown_selected_controls(bpy.types.Operator):
    bl_idname = "animassist.breakdown_selected_controls"
    bl_label = "Selected Controls Only"
    bl_description = (
        "Restrict the breakdown to the currently selected pose bones or "
        "active object. Cancels with a report if nothing is selected"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _poll_animated(cls, context)

    def execute(self, context):
        obj, bones = _resolve_target(context)
        if obj is None:
            self.report({"WARNING"}, "No active object.")
            return {"CANCELLED"}
        if obj.type == "ARMATURE" and obj.mode == "POSE" and not bones:
            self.report({"WARNING"}, "No pose bones selected.")
            return {"CANCELLED"}
        return _run(self, context, _options_from_scene(context))


class AA_OT_breakdown_channel_subset(bpy.types.Operator):
    bl_idname = "animassist.breakdown_channel_subset"
    bl_label = "Custom Channel Subset"
    bl_description = (
        "Run the breakdown using the per-kind and per-axis checkboxes on "
        "the mask panel"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _poll_animated(cls, context)

    def execute(self, context):
        return _run(self, context, _options_from_scene(context))


CLASSES: tuple[type, ...] = (
    AA_OT_breakdown_current_frame,
    AA_OT_breakdown_weighted,
    AA_OT_breakdown_favor_prev,
    AA_OT_breakdown_favor_next,
    AA_OT_breakdown_midpoint,
    AA_OT_breakdown_push_prev,
    AA_OT_breakdown_push_next,
    AA_OT_breakdown_pull_prev,
    AA_OT_breakdown_pull_next,
    AA_OT_breakdown_percentage,
    AA_OT_breakdown_offset,
    AA_OT_breakdown_batch_frames,
    AA_OT_breakdown_numeric,
    AA_OT_breakdown_repeat_last,
    AA_OT_breakdown_transform_only,
    AA_OT_breakdown_rotation_only,
    AA_OT_breakdown_location_only,
    AA_OT_breakdown_scale_only,
    AA_OT_breakdown_selected_controls,
    AA_OT_breakdown_channel_subset,
)
