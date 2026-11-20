# --- RETIMING TOOLS ---
"""Timing diagnostic operators.

Operators for running a full timing diagnostic pass, navigating to detected
gaps and clusters, copying the diagnostic report, and clearing cached results.

Gap and cluster state is shared via ``p6_gap_ops.get_cached_gaps()`` (populated
by ``AA_OT_p6_detect_gaps``) and this module's ``_cached_diag`` for the full
diagnostics run.
"""

from __future__ import annotations

import bpy

from ..core.logging import get_logger
from ..core.p6_properties import get_p6
from ..core import p6_diagnostics as diag
from ..core.fcurve_compat import get_fcurves
from .p6_gap_ops import get_cached_gaps, clear_cached_gaps

_log = get_logger(__name__)

# Full diagnostics result cache (module-level, cleared on Blender shutdown/reload).
_cached_diag: diag.TimingDiagnostics | None = None
_cached_diag_obj: str = ""


def get_cached_diag() -> diag.TimingDiagnostics | None:
    return _cached_diag


def clear_cached_diag() -> None:
    """Clear the full diagnostics cache.  Called on file load and addon disable."""
    global _cached_diag, _cached_diag_obj
    _cached_diag = None
    _cached_diag_obj = ""


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _get_fcurves(context: bpy.types.Context):
    obj = getattr(context, "active_object", None)
    if obj is None:
        return [], ""
    adata = getattr(obj, "animation_data", None)
    action = getattr(adata, "action", None) if adata else None
    if action is None:
        return [], getattr(obj, "name", "")
    return get_fcurves(action, anim_data=adata), obj.name


def _tag_redraw(context: bpy.types.Context) -> None:
    if getattr(context, "screen", None) is None:
        return
    for area in context.screen.areas:
        area.tag_redraw()


def _p6_base_poll(context: bpy.types.Context) -> bool:
    if not hasattr(context, "scene") or context.scene is None:
        return False
    obj = getattr(context, "active_object", None)
    if obj is None:
        return False
    adata = getattr(obj, "animation_data", None)
    return adata is not None and getattr(adata, "action", None) is not None


# ---------------------------------------------------------------------------
# 1. Run Diagnostics
# ---------------------------------------------------------------------------

class AA_OT_p6_run_diagnostics(bpy.types.Operator):
    """Run a full timing diagnostic pass on the active action."""

    bl_idname = "animassist.p6_run_diagnostics"
    bl_label = "Run Diagnostics"
    bl_description = "Analyse gaps, clusters, and timing regularity for the active action"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return _p6_base_poll(context)

    def execute(self, context):
        global _cached_diag, _cached_diag_obj

        p6 = get_p6(context)
        if p6 is None:
            self.report({"WARNING"}, "Retiming properties not available")
            return {"CANCELLED"}

        fcurves, obj_name = _get_fcurves(context)
        if not fcurves:
            self.report({"WARNING"}, "No action on active object")
            return {"CANCELLED"}

        result = diag.run_diagnostics(
            fcurves,
            gap_threshold=p6.gap_threshold,
            cluster_radius=p6.cluster_radius,
        )
        _cached_diag = result
        _cached_diag_obj = obj_name

        # Persist summary on PropertyGroup so the panel can display it
        # without holding a reference to the diagnostics object.
        p6.last_diag_result        = result.result_enum
        p6.last_diag_gap_count     = len(result.gaps)
        p6.last_diag_cluster_count = len(result.clusters)
        p6.last_diag_score         = result.score

        parts = []
        if result.gaps:
            parts.append(f"{len(result.gaps)} gap(s)")
        if result.clusters:
            parts.append(f"{len(result.clusters)} cluster(s)")
        summary = ", ".join(parts) if parts else "clean"
        self.report(
            {"INFO"},
            f"Diagnostics: {summary}  |  Score {result.score:.0f}/100",
        )

        _tag_redraw(context)
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# 2. Jump to Next Gap
# ---------------------------------------------------------------------------

class AA_OT_p6_jump_next_gap(bpy.types.Operator):
    """Advance the playhead to the start of the next detected timing gap."""

    bl_idname = "animassist.p6_jump_next_gap"
    bl_label = "Next Gap"
    bl_description = "Move playhead to the start of the next timing gap"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if not hasattr(context, "scene") or context.scene is None:
            return False
        return bool(get_cached_gaps())

    def execute(self, context):
        gaps = get_cached_gaps()
        if not gaps:
            self.report({"INFO"}, "No gaps cached — run Detect Gaps first")
            return {"CANCELLED"}

        current = float(context.scene.frame_current)
        forward = [g for g in gaps if g.start_frame > current + 0.5]
        if not forward:
            # Wrap around.
            target = min(gaps, key=lambda g: g.start_frame)
        else:
            target = min(forward, key=lambda g: g.start_frame)

        context.scene.frame_set(int(round(target.start_frame)))
        self.report(
            {"INFO"},
            f"Gap {target.start_frame:.0f}→{target.end_frame:.0f} ({target.size:.0f}f)",
        )
        _tag_redraw(context)
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# 3. Jump to Previous Gap
# ---------------------------------------------------------------------------

class AA_OT_p6_jump_prev_gap(bpy.types.Operator):
    """Rewind the playhead to the start of the previous detected timing gap."""

    bl_idname = "animassist.p6_jump_prev_gap"
    bl_label = "Previous Gap"
    bl_description = "Move playhead to the start of the previous timing gap"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if not hasattr(context, "scene") or context.scene is None:
            return False
        return bool(get_cached_gaps())

    def execute(self, context):
        gaps = get_cached_gaps()
        if not gaps:
            self.report({"INFO"}, "No gaps cached — run Detect Gaps first")
            return {"CANCELLED"}

        current = float(context.scene.frame_current)
        backward = [g for g in gaps if g.start_frame < current - 0.5]
        if not backward:
            # Wrap around.
            target = max(gaps, key=lambda g: g.start_frame)
        else:
            target = max(backward, key=lambda g: g.start_frame)

        context.scene.frame_set(int(round(target.start_frame)))
        self.report(
            {"INFO"},
            f"Gap {target.start_frame:.0f}→{target.end_frame:.0f} ({target.size:.0f}f)",
        )
        _tag_redraw(context)
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# 4. Jump to Next Cluster
# ---------------------------------------------------------------------------

class AA_OT_p6_jump_next_cluster(bpy.types.Operator):
    """Advance the playhead to the centre of the next detected key cluster."""

    bl_idname = "animassist.p6_jump_next_cluster"
    bl_label = "Next Cluster"
    bl_description = "Move playhead to the centre of the next key cluster"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if not hasattr(context, "scene") or context.scene is None:
            return False
        d = get_cached_diag()
        return d is not None and bool(d.clusters)

    def execute(self, context):
        d = get_cached_diag()
        if d is None or not d.clusters:
            self.report({"INFO"}, "No clusters — run Diagnostics first")
            return {"CANCELLED"}

        current = float(context.scene.frame_current)
        forward = [c for c in d.clusters if c.center > current + 0.5]
        if not forward:
            target = min(d.clusters, key=lambda c: c.center)
        else:
            target = min(forward, key=lambda c: c.center)

        context.scene.frame_set(int(round(target.center)))
        self.report(
            {"INFO"},
            f"Cluster at ~{target.center:.0f} ({len(target.frames)} keys, "
            f"spread {target.spread:.1f}f)",
        )
        _tag_redraw(context)
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# 5. Copy Diagnostics Report
# ---------------------------------------------------------------------------

class AA_OT_p6_copy_diag_report(bpy.types.Operator):
    """Copy the full diagnostics text to the clipboard."""

    bl_idname = "animassist.p6_copy_diag_report"
    bl_label = "Copy Report"
    bl_description = "Copy the full timing diagnostics report to the clipboard"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return get_cached_diag() is not None

    def execute(self, context):
        d = get_cached_diag()
        if d is None:
            self.report({"WARNING"}, "No diagnostics to copy — run first")
            return {"CANCELLED"}

        report = diag.format_diagnostics_report(d, label=_cached_diag_obj)
        context.window_manager.clipboard = report
        self.report({"INFO"}, "Diagnostics report copied to clipboard")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# 6. Clear Diagnostics
# ---------------------------------------------------------------------------

class AA_OT_p6_clear_diagnostics(bpy.types.Operator):
    """Reset stored diagnostic results and clear gap/cluster caches."""

    bl_idname = "animassist.p6_clear_diagnostics"
    bl_label = "Clear Diagnostics"
    bl_description = "Clear cached diagnostic results and reset the report panel"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return get_cached_diag() is not None or bool(get_cached_gaps())

    def execute(self, context):
        global _cached_diag, _cached_diag_obj
        _cached_diag = None
        _cached_diag_obj = ""
        clear_cached_gaps()

        p6 = get_p6(context)
        if p6 is not None:
            p6.last_diag_result        = "NONE"
            p6.last_diag_gap_count     = 0
            p6.last_diag_cluster_count = 0
            p6.last_diag_score         = -1.0

        _tag_redraw(context)
        self.report({"INFO"}, "Diagnostic results cleared")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Class list
# ---------------------------------------------------------------------------

CLASSES: tuple[type, ...] = (
    AA_OT_p6_run_diagnostics,
    AA_OT_p6_jump_next_gap,
    AA_OT_p6_jump_prev_gap,
    AA_OT_p6_jump_next_cluster,
    AA_OT_p6_copy_diag_report,
    AA_OT_p6_clear_diagnostics,
)
