# --- BREAKDOWN TOOLS ---
"""Inbetween operators (Features 16, 17, 30)."""

from __future__ import annotations

import bpy

from ..core import breakdown_core as bc
from ..core.fcurve_compat import get_fcurves
from ..core.p3_properties import get_p3
from .p3_breakdown_ops import _options_from_scene, _resolve_target, _poll_animated


def _selected_frames(obj: bpy.types.Object) -> list[float]:
    adata = getattr(obj, "animation_data", None)
    if adata is None or adata.action is None:
        return []
    frames: set[float] = set()
    for fc in get_fcurves(adata.action, anim_data=adata):
        for kp in fc.keyframe_points:
            if kp.select_control_point:
                frames.add(float(kp.co[0]))
    return sorted(frames)


class AA_OT_inbetween_selected_gap(bpy.types.Operator):
    bl_idname = "animassist.inbetween_selected_gap"
    bl_label = "Inbetween in Selected Gap"
    bl_description = (
        "Insert a single inbetween key between the two currently selected "
        "keyframes using the breakdown factor slider"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _poll_animated(cls, context)

    def execute(self, context):
        obj, _ = _resolve_target(context)
        if obj is None:
            self.report({"WARNING"}, "No active object.")
            return {"CANCELLED"}
        frames = _selected_frames(obj)
        if len(frames) < 2:
            self.report({"WARNING"}, "Need at least two selected keys.")
            return {"CANCELLED"}
        start, end = frames[0], frames[-1]
        if end <= start:
            self.report({"WARNING"}, "Selected keys collapse to a single frame.")
            return {"CANCELLED"}
        p3 = get_p3(context)
        t = float(p3.factor) if p3 else 0.5
        target = start + (end - start) * t
        opts = _options_from_scene(context, target_frame=target)
        result = bc.apply_breakdown(context, obj, None, opts, frames=[target])
        bc.remember_last(opts)
        self.report({"INFO"}, result.messages[-1] if result.messages else "Done.")
        return {"FINISHED"}


class AA_OT_inbetween_distribute(bpy.types.Operator):
    bl_idname = "animassist.inbetween_distribute"
    bl_label = "Evenly Distribute Inbetweens"
    bl_description = (
        "Distribute ``Inbetween Count`` evenly-spaced breakdowns inside "
        "the gap formed by the currently selected keys"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _poll_animated(cls, context)

    def execute(self, context):
        obj, _ = _resolve_target(context)
        if obj is None:
            return {"CANCELLED"}
        frames = _selected_frames(obj)
        if len(frames) < 2:
            self.report({"WARNING"}, "Need at least two selected keys.")
            return {"CANCELLED"}
        start, end = frames[0], frames[-1]
        p3 = get_p3(context)
        count = int(p3.inbetween_count) if p3 else 1
        if count < 1 or end <= start:
            return {"CANCELLED"}
        step = (end - start) / float(count + 1)
        targets = [start + step * (i + 1) for i in range(count)]
        opts = _options_from_scene(context)
        total = 0
        for f in targets:
            res = bc.apply_breakdown(context, obj, None, opts, frames=[f])
            total += res.keys_written
        bc.remember_last(opts)
        self.report({"INFO"}, f"Distributed {count} inbetweens ({total} keys written).")
        return {"FINISHED"}


class AA_OT_inbetween_on_clusters(bpy.types.Operator):
    bl_idname = "animassist.inbetween_on_clusters"
    bl_label = "Inbetween on Clusters"
    bl_description = (
        "Group selected keys into clusters and insert inbetweens between "
        "each adjacent cluster"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _poll_animated(cls, context)

    def execute(self, context):
        obj, _ = _resolve_target(context)
        if obj is None:
            return {"CANCELLED"}
        frames = _selected_frames(obj)
        if len(frames) < 2:
            self.report({"WARNING"}, "Need at least two selected keys.")
            return {"CANCELLED"}
        # Cluster by 2-frame proximity.
        clusters: list[list[float]] = []
        current: list[float] = [frames[0]]
        for f in frames[1:]:
            if f - current[-1] <= 2.0:
                current.append(f)
            else:
                clusters.append(current)
                current = [f]
        clusters.append(current)
        if len(clusters) < 2:
            self.report({"WARNING"}, "Only one cluster detected.")
            return {"CANCELLED"}
        opts = _options_from_scene(context)
        total = 0
        for a, b in zip(clusters, clusters[1:]):
            midpoint = (a[-1] + b[0]) / 2.0
            res = bc.apply_breakdown(context, obj, None, opts, frames=[midpoint])
            total += res.keys_written
        bc.remember_last(opts)
        self.report({"INFO"}, f"Inbetweens inserted between {len(clusters)} clusters ({total} keys).")
        return {"FINISHED"}


CLASSES: tuple[type, ...] = (
    AA_OT_inbetween_selected_gap,
    AA_OT_inbetween_distribute,
    AA_OT_inbetween_on_clusters,
)
