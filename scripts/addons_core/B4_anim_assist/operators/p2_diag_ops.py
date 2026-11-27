"""Diagnostic scan operators (3 ops)."""

from __future__ import annotations

from bpy.props import FloatProperty
from bpy.types import Operator

from ..core import key_diag as diag
from ..core.context_utils import in_anim_editor, iter_visible_fcurves
from ..core.logging import get_logger

_log = get_logger(__name__)


# Session-transient last-scan results (exposed for the diagnostic panel).
_last_results: list[dict] = []
_last_summary: dict = {}


def get_last_results() -> list[dict]:
    return _last_results


def get_last_summary() -> dict:
    return _last_summary


def _select_hits(context, hits):
    frames_by_fc: dict[tuple, set[float]] = {}
    for h in hits:
        frames_by_fc.setdefault((h["obj"], h["data_path"], h["array_index"]), set()).add(
            round(h["frame"], 4)
        )
    count = 0
    for obj, _a, fc in iter_visible_fcurves(context):
        key = (obj.name, fc.data_path, fc.array_index)
        frames = frames_by_fc.get(key)
        if not frames:
            for kp in fc.keyframe_points:
                kp.select_control_point = False
                kp.select_left_handle = False
                kp.select_right_handle = False
            continue
        for kp in fc.keyframe_points:
            hit = round(float(kp.co.x), 4) in frames
            kp.select_control_point = hit
            kp.select_left_handle = hit
            kp.select_right_handle = hit
            if hit:
                count += 1
    return count


class _DiagOpBase(Operator):
    @classmethod
    def poll(cls, context):
        return in_anim_editor(context)


class ANIMASSIST_OT_scan_dense_keys(_DiagOpBase):
    bl_idname = "animassist.scan_dense_keys"
    bl_label = "Scan Dense Keys"
    bl_description = "Select keys closer than *min_gap* frames to their neighbour"
    bl_options = {"REGISTER", "UNDO"}

    min_gap: FloatProperty(default=1.0, min=0.0)  # type: ignore[valid-type]

    def execute(self, context):
        global _last_results, _last_summary
        results = diag.scan_density(context, self.min_gap)
        _last_results = results
        _last_summary = diag.summarise(results)
        count = _select_hits(context, results)
        self.report({"INFO"}, f"{count} dense keys")
        return {"FINISHED"}


class ANIMASSIST_OT_scan_redundant_keys(_DiagOpBase):
    bl_idname = "animassist.scan_redundant_keys"
    bl_label = "Scan Redundant Keys"
    bl_description = "Select keys that lie on a straight line between neighbours"
    bl_options = {"REGISTER", "UNDO"}

    tol: FloatProperty(default=1e-4, min=0.0)  # type: ignore[valid-type]

    def execute(self, context):
        global _last_results, _last_summary
        results = diag.scan_redundant(context, self.tol)
        _last_results = results
        _last_summary = diag.summarise(results)
        count = _select_hits(context, results)
        self.report({"INFO"}, f"{count} redundant keys")
        return {"FINISHED"}


class ANIMASSIST_OT_scan_spike_keys(_DiagOpBase):
    bl_idname = "animassist.scan_spike_keys"
    bl_label = "Scan Spike Keys"
    bl_description = "Select keys whose value deviates sharply from their neighbours"
    bl_options = {"REGISTER", "UNDO"}

    ratio: FloatProperty(default=4.0, min=1.0)  # type: ignore[valid-type]

    def execute(self, context):
        global _last_results, _last_summary
        results = diag.scan_spikes(context, self.ratio)
        _last_results = results
        _last_summary = diag.summarise(results)
        count = _select_hits(context, results)
        self.report({"INFO"}, f"{count} spike keys")
        return {"FINISHED"}


classes: tuple[type, ...] = (
    ANIMASSIST_OT_scan_dense_keys,
    ANIMASSIST_OT_scan_redundant_keys,
    ANIMASSIST_OT_scan_spike_keys,
)
