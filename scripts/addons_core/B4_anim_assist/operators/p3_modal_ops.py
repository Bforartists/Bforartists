# --- BREAKDOWN TOOLS ---
"""Modal / preview operators (features 39, 40)."""

from __future__ import annotations

import bpy

from ..constants import BREAKDOWN_ANCHOR_HINT

from ..core import breakdown_core as bc
from ..core.fcurve_compat import get_fcurves
from ..core.p3_properties import get_p3
from .p3_breakdown_ops import (
    _options_from_scene,
    _resolve_target,
    _poll_animated,
)


class AA_OT_modal_drag_breakdown(bpy.types.Operator):
    """Modal drag that scrubs the breakdown factor between the prev/next pose.

    The operator snapshots every target fcurve on ``invoke`` so that
    ``RMB``/``ESC`` can cleanly restore the pre-drag state without
    relying on Blender's undo stack. Only the final commit value on
    ``LMB`` release is kept.
    """

    bl_idname = "animassist.modal_drag_breakdown"
    bl_label = "Modal Drag Breakdown"
    bl_description = (
        "Active object's Action using Breakdown targets and mask. Drag horizontally; "
        "release left mouse to apply, Esc/right mouse restores the pre-drag keys. "
        + BREAKDOWN_ANCHOR_HINT
    )
    bl_options = {"REGISTER", "UNDO", "GRAB_CURSOR", "BLOCKING"}

    @classmethod
    def poll(cls, context):
        return _poll_animated(cls, context)

    # ------------------------------------------------------------------
    # Snapshot / restore helpers
    # ------------------------------------------------------------------
    def _snapshot_fcurves(self, context) -> None:
        """Capture a minimal snapshot of every target fcurve's key state."""
        obj, bones = _resolve_target(context)
        self._snap_obj = obj
        self._snap: list[tuple[bpy.types.FCurve, list[tuple]]] = []
        if obj is None:
            return
        adata = getattr(obj, "animation_data", None)
        if adata is None or adata.action is None:
            return
        for fc in get_fcurves(adata.action, anim_data=adata):
            rows: list[tuple] = []
            for kp in fc.keyframe_points:
                rows.append((
                    float(kp.co[0]),
                    float(kp.co[1]),
                    float(kp.handle_left[0]),
                    float(kp.handle_left[1]),
                    float(kp.handle_right[0]),
                    float(kp.handle_right[1]),
                    str(kp.handle_left_type),
                    str(kp.handle_right_type),
                    str(kp.interpolation),
                    str(kp.type),
                    bool(kp.select_control_point),
                    bool(kp.select_left_handle),
                    bool(kp.select_right_handle),
                    str(kp.easing),
                    float(kp.amplitude),
                    float(kp.back),
                    float(kp.period),
                ))
            self._snap.append((fc, rows))

    def _restore_snapshot(self) -> None:
        obj = getattr(self, "_snap_obj", None)
        if obj is None:
            return
        adata = getattr(obj, "animation_data", None)
        if adata is None or adata.action is None:
            return
        for fc, rows in self._snap:
            try:
                # Clear the fcurve and rebuild from the snapshot rows.
                while len(fc.keyframe_points) > 0:
                    fc.keyframe_points.remove(
                        fc.keyframe_points[0], fast=True
                    )
                for row in rows:
                    kp = fc.keyframe_points.insert(
                        row[0], row[1], options={"FAST"},
                    )
                    kp.handle_left_type = row[6]
                    kp.handle_right_type = row[7]
                    kp.interpolation = row[8]
                    kp.type = row[9]
                    kp.select_control_point = row[10]
                    kp.select_left_handle = row[11]
                    kp.select_right_handle = row[12]
                    kp.easing, kp.amplitude, kp.back, kp.period = row[13:17]
                    kp.handle_left = (row[2], row[3])
                    kp.handle_right = (row[4], row[5])
                fc.update()
            except Exception:
                continue

    def _apply(self, context, factor: float) -> None:
        obj, bones = _resolve_target(context)
        if obj is None:
            return
        options = _options_from_scene(context, factor=factor)
        bc.apply_breakdown(context, obj, bones, options)

    # ------------------------------------------------------------------
    # Invoke / modal
    # ------------------------------------------------------------------
    def _status(self, context):
        if context.workspace:
            obj = self._snap_obj
            context.workspace.status_text_set(
                f"Breakdown {self._p3.factor:.2f} | {obj.name if obj else 'No object'} "
                "| Breakdown targets/mask | Release: apply | Esc: cancel")

    def invoke(self, context, event):
        p3 = get_p3(context)
        if p3 is None:
            return {"CANCELLED"}
        self._p3 = p3
        self._start_x = int(event.mouse_x)
        self._start_factor = float(p3.factor)
        self._sensitivity = max(40, int(p3.modal_sensitivity))
        self._committed = False
        self._snapshot_fcurves(context)
        self._apply(context, self._start_factor)
        self._status(context)
        if context.window is not None:
            context.window.cursor_modal_set("SCROLL_X")
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        if event.type == "MOUSEMOVE":
            delta = (event.mouse_x - self._start_x) / float(self._sensitivity)
            new_factor = max(-1.0, min(2.0, self._start_factor + delta))
            self._p3.factor = new_factor
            # Restore the pre-drag state and reapply at the new factor so
            # the fcurve never accumulates stale scrub keys.
            self._restore_snapshot()
            self._apply(context, new_factor)
            self._status(context)
            if context.area is not None:
                context.area.tag_redraw()
            return {"RUNNING_MODAL"}
        if event.type == "LEFTMOUSE" and event.value == "RELEASE":
            if context.workspace:
                context.workspace.status_text_set(None)
            if context.window is not None:
                context.window.cursor_modal_restore()
            bc.remember_last(_options_from_scene(context))
            self._committed = True
            self.report(
                {"INFO"},
                f"Committed breakdown @ factor {self._p3.factor:.2f}",
            )
            return {"FINISHED"}
        if event.type in {"RIGHTMOUSE", "ESC"}:
            if context.workspace:
                context.workspace.status_text_set(None)
            # Hard-restore the pre-drag state; do NOT write another key.
            self._p3.factor = self._start_factor
            self._restore_snapshot()
            if context.window is not None:
                context.window.cursor_modal_restore()
            if context.area is not None:
                context.area.tag_redraw()
            self.report({"INFO"}, "Modal breakdown cancelled.")
            return {"CANCELLED"}
        return {"RUNNING_MODAL"}


class AA_OT_preview_breakdown(bpy.types.Operator):
    """Stage a preview breakdown without marking it as committed."""

    bl_idname = "animassist.preview_breakdown"
    bl_label = "Preview Breakdown"
    bl_description = (
        "Write a breakdown at the current frame using the active "
        "settings and flag it as a preview. Run Commit Preview to keep it"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _poll_animated(cls, context)

    def execute(self, context):
        p3 = get_p3(context)
        if p3 is None:
            self.report({"WARNING"}, "Property group unavailable.")
            return {"CANCELLED"}
        obj, bones = _resolve_target(context)
        if obj is None:
            self.report({"WARNING"}, "No active object.")
            return {"CANCELLED"}
        options = _options_from_scene(context)
        result = bc.apply_breakdown(context, obj, bones, options)
        p3.preview_active = True
        p3.preview_frame = float(context.scene.frame_current_final)
        msg = result.messages[-1] if result.messages else "Preview staged."
        self.report({"INFO"}, f"[Preview] {msg}")
        return {"FINISHED"}


class AA_OT_commit_preview(bpy.types.Operator):
    """Commit the currently staged preview breakdown."""

    bl_idname = "animassist.commit_preview"
    bl_label = "Commit Preview"
    bl_description = (
        "Mark the currently staged preview breakdown as committed and "
        "record it as the last-run options for Repeat Last"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        p3 = get_p3(context)
        if p3 is None or not p3.preview_active:
            self.report({"WARNING"}, "No preview to commit.")
            return {"CANCELLED"}
        bc.remember_last(_options_from_scene(context))
        p3.preview_active = False
        self.report({"INFO"}, f"Preview committed @ frame {p3.preview_frame:.1f}")
        return {"FINISHED"}


CLASSES: tuple[type, ...] = (
    AA_OT_modal_drag_breakdown,
    AA_OT_preview_breakdown,
    AA_OT_commit_preview,
)
