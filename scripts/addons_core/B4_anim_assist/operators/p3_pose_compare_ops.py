# --- BREAKDOWN TOOLS ---
"""Pose-compare operators.

Implements features 18, 19, 32 and 33:

* ``animassist.pose_snapshot_prev``      — capture the "previous pose" slot
* ``animassist.pose_snapshot_next``      — capture the "next pose" slot
* ``animassist.pose_snapshot_reference`` — capture a reference pose slot
* ``animassist.pose_compare_report``     — print a diff between prev and next
* ``animassist.breakdown_from_clipboard``— breakdown toward snapshot A or B
* ``animassist.blend_toward_reference``  — blend current values toward reference

All operators are thin wrappers over :mod:`anim_assist.core.pose_compare`
and :mod:`anim_assist.core.breakdown_core`.
"""

from __future__ import annotations

from typing import Optional

import bpy
from bpy.props import EnumProperty, FloatProperty

from ..core import breakdown_core as bc
from ..core import pose_compare as pc
from ..core.p3_properties import get_p3
from .p3_breakdown_ops import _options_from_scene, _resolve_target, _poll_animated


# ---------------------------------------------------------------------------
# Snapshot capture
# ---------------------------------------------------------------------------

def _active_frame(context: bpy.types.Context) -> float:
    return float(context.scene.frame_current_final)


class AA_OT_pose_snapshot_prev(bpy.types.Operator):
    """Capture the current pose into the 'previous pose' compare slot."""

    bl_idname = "animassist.pose_snapshot_prev"
    bl_label = "Set Previous Pose"
    bl_description = (
        "Capture the evaluated fcurve values of the active object at the "
        "current frame into the 'previous pose' compare slot"
    )
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return _poll_animated(cls, context)

    def execute(self, context):
        obj, _ = _resolve_target(context)
        if obj is None:
            self.report({"WARNING"}, "No active object.")
            return {"CANCELLED"}
        snap = pc.set_prev(obj, _active_frame(context))
        self.report(
            {"INFO"},
            f"Previous pose captured at frame {snap.frame:.1f} "
            f"({len(snap.values)} channels).",
        )
        return {"FINISHED"}


class AA_OT_pose_snapshot_next(bpy.types.Operator):
    """Capture the current pose into the 'next pose' compare slot."""

    bl_idname = "animassist.pose_snapshot_next"
    bl_label = "Set Next Pose"
    bl_description = (
        "Capture the evaluated fcurve values of the active object at the "
        "current frame into the 'next pose' compare slot"
    )
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return _poll_animated(cls, context)

    def execute(self, context):
        obj, _ = _resolve_target(context)
        if obj is None:
            self.report({"WARNING"}, "No active object.")
            return {"CANCELLED"}
        snap = pc.set_next(obj, _active_frame(context))
        self.report(
            {"INFO"},
            f"Next pose captured at frame {snap.frame:.1f} "
            f"({len(snap.values)} channels).",
        )
        return {"FINISHED"}


class AA_OT_pose_snapshot_reference(bpy.types.Operator):
    """Capture the current pose into the 'reference pose' compare slot."""

    bl_idname = "animassist.pose_snapshot_reference"
    bl_label = "Set Reference Pose"
    bl_description = (
        "Capture the active object's current pose as the reference for Blend Toward Reference"
    )
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return _poll_animated(cls, context)

    def execute(self, context):
        obj, _ = _resolve_target(context)
        if obj is None:
            self.report({"WARNING"}, "No active object.")
            return {"CANCELLED"}
        snap = pc.set_reference(obj, _active_frame(context))
        self.report(
            {"INFO"},
            f"Reference pose captured at frame {snap.frame:.1f} "
            f"({len(snap.values)} channels).",
        )
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Compare report
# ---------------------------------------------------------------------------

class AA_OT_pose_compare_report(bpy.types.Operator):
    """Produce a human-readable diff between the two pose compare slots."""

    bl_idname = "animassist.pose_compare_report"
    bl_label = "Pose Compare Report"
    bl_description = (
        "Compare the previous and next pose compare slots and print a "
        "per-channel diff report to the info log"
    )
    bl_options = {"REGISTER", "INTERNAL"}

    tolerance: FloatProperty(  # type: ignore[valid-type]
        name="Tolerance",
        description="Channels whose absolute difference is below this value are treated as equal.",
        default=1.0e-5, min=0.0, max=1.0,
    )

    @classmethod
    def poll(cls, context):
        state = pc.get_state()
        return (
            state.prev_snapshot is not None
            and state.next_snapshot is not None
        )

    def execute(self, context):
        state = pc.get_state()
        if state.prev_snapshot is None or state.next_snapshot is None:
            self.report(
                {"WARNING"},
                "Both previous and next pose snapshots must be set before comparing.",
            )
            return {"CANCELLED"}

        diffs = pc.compare_snapshots(
            state.prev_snapshot,
            state.next_snapshot,
            tolerance=float(self.tolerance),
        )
        state.last_report = diffs

        if not diffs:
            self.report({"INFO"}, "Pose compare: poses are identical.")
            return {"FINISHED"}

        self.report({"INFO"}, f"Pose compare: {len(diffs)} differing channel(s).")
        for line in diffs[:25]:
            self.report({"INFO"}, line)
        if len(diffs) > 25:
            self.report({"INFO"}, f"…and {len(diffs) - 25} more.")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Breakdown from clipboard / blend toward reference
# ---------------------------------------------------------------------------

def _apply_breakdown_from_snapshot(
    self: bpy.types.Operator,
    context: bpy.types.Context,
    snapshot: Optional[pc.PoseSnapshot],
    *,
    label: str,
) -> set[str]:
    """Blend current frame toward the provided snapshot at ``p3.factor``.

    Honours the mask, exclusion set, skip-locked flag, and bone
    filter exactly like the regular breakdown operators by routing the
    fcurve selection through :func:`breakdown_core.iter_target_fcurves`.
    """
    if snapshot is None:
        self.report({"WARNING"}, f"{label} snapshot is empty — capture it first.")
        return {"CANCELLED"}

    obj, bones = _resolve_target(context)
    if obj is None:
        self.report({"WARNING"}, "No active object.")
        return {"CANCELLED"}
    adata = getattr(obj, "animation_data", None)
    if adata is None or adata.action is None:
        self.report({"WARNING"}, f"{obj.name}: no action.")
        return {"CANCELLED"}

    p3 = get_p3(context)
    factor = float(p3.factor if p3 else 0.5)
    frame = float(context.scene.frame_current_final)

    # Build the same filtered fcurve set that ``apply_breakdown`` would
    # touch, so mask/exclusion/skip_locked/bone selection are honoured.
    options = _options_from_scene(context)
    target_fcurves = bc.iter_target_fcurves(
        obj, bones, options.mask, options.exclusion
    )
    if not target_fcurves:
        self.report({"WARNING"}, "No fcurves matched the current mask.")
        return {"CANCELLED"}

    written = 0
    for fc in target_fcurves:
        ref_val = snapshot.get(fc.data_path, int(fc.array_index))
        if ref_val is None:
            continue
        try:
            cur_val = float(fc.evaluate(frame))
        except Exception:
            continue
        new_val = cur_val + (ref_val - cur_val) * factor
        fc.keyframe_points.insert(
            frame, float(new_val), options={"NEEDED", "FAST"}
        )
        try:
            fc.update()
        except Exception:
            pass
        written += 1

    bc.remember_last(options)
    self.report({"INFO"}, f"Blended {written} channels toward {label}.")
    return {"FINISHED"}


class AA_OT_breakdown_from_clipboard(bpy.types.Operator):
    """Blend the current frame toward a stored pose snapshot slot."""

    bl_idname = "animassist.breakdown_from_clipboard"
    bl_label = "Breakdown From Clipboard"
    bl_description = (
        "Blend the current frame's evaluated values toward a stored pose "
        "snapshot (previous or next) using the breakdown factor slider"
    )
    bl_options = {"REGISTER", "UNDO"}

    slot: EnumProperty(  # type: ignore[valid-type]
        name="Slot",
        description="Which stored pose snapshot to blend toward.",
        items=(
            ("PREV", "Previous Pose", "Use the 'previous pose' compare slot."),
            ("NEXT", "Next Pose", "Use the 'next pose' compare slot."),
        ),
        default="PREV",
    )

    @classmethod
    def poll(cls, context):
        return _poll_animated(cls, context)

    def execute(self, context):
        state = pc.get_state()
        target = state.prev_snapshot if self.slot == "PREV" else state.next_snapshot
        label = "Previous Pose" if self.slot == "PREV" else "Next Pose"
        return _apply_breakdown_from_snapshot(self, context, target, label=label)


class AA_OT_blend_toward_reference(bpy.types.Operator):
    """Blend the current frame toward the stored reference pose snapshot."""

    bl_idname = "animassist.blend_toward_reference"
    bl_label = "Blend Toward Reference"
    bl_description = (
        "Blend the current frame's evaluated values toward the stored "
        "reference pose snapshot using the breakdown factor slider"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _poll_animated(cls, context)

    def execute(self, context):
        state = pc.get_state()
        return _apply_breakdown_from_snapshot(
            self, context, state.reference_snapshot, label="Reference Pose"
        )


CLASSES: tuple[type, ...] = (
    AA_OT_pose_snapshot_prev,
    AA_OT_pose_snapshot_next,
    AA_OT_pose_snapshot_reference,
    AA_OT_pose_compare_report,
    AA_OT_breakdown_from_clipboard,
    AA_OT_blend_toward_reference,
)
