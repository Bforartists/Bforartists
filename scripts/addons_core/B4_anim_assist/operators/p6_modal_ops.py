# --- RETIMING TOOLS ---
"""Interactive modal operators: scale and offset.

Architecture (mirrors p4_modal_ops pattern):

1. ``invoke`` — snapshot all FCurve keypoints, enter modal, draw initial
   header text.
2. ``modal`` — on MOUSEMOVE: restore snapshot, apply scaled delta, redraw.
   SHIFT = 0.1× precision; CTRL = snap to integer frames.
   LMB / ENTER = commit (push undo step). RMB / ESC = cancel (restore).
3. ``cancel`` — restore snapshot and exit.

No ``bpy.ops.*`` calls inside the modal body.
"""

from __future__ import annotations


import bpy

from ..core.logging import get_logger
from ..core.p6_properties import get_p6
from ..core import p6_retime_math as rm
from ..core.fcurve_compat import get_fcurves

_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Snapshot helpers (faster than full p6_retime_math backup for modal use)
# ---------------------------------------------------------------------------

def _snap_fcurves(fcurves) -> dict[int, list[tuple]]:
    """Snapshot each FCurve's keypoints keyed by id(fc)."""
    result: dict[int, list[tuple]] = {}
    for fc in fcurves:
        rows: list[tuple] = []
        for kp in fc.keyframe_points:
            rows.append((
                float(kp.co.x),
                float(kp.co.y),
                float(kp.handle_left.x),
                float(kp.handle_left.y),
                float(kp.handle_right.x),
                float(kp.handle_right.y),
                str(kp.handle_left_type),
                str(kp.handle_right_type),
                str(kp.interpolation),
                str(kp.easing),
            ))
        result[id(fc)] = rows
    return result


def _restore_snap(fcurves, snap: dict[int, list[tuple]]) -> None:
    """Restore FCurves from a snapshot created by ``_snap_fcurves``."""
    for fc in fcurves:
        fid = id(fc)
        rows = snap.get(fid)
        if rows is None:
            continue
        kps = fc.keyframe_points
        # Trim extras.
        while len(kps) > len(rows):
            kps.remove(kps[-1])
        # Add missing.
        while len(kps) < len(rows):
            r = rows[len(kps)]
            kps.insert(r[0], r[1])
        # Restore values.
        for kp, r in zip(kps, rows):
            kp.co.x              = r[0]
            kp.co.y              = r[1]
            kp.handle_left.x     = r[2]
            kp.handle_left.y     = r[3]
            kp.handle_right.x    = r[4]
            kp.handle_right.y    = r[5]
            kp.handle_left_type  = r[6]
            kp.handle_right_type = r[7]
            kp.interpolation     = r[8]
            kp.easing            = r[9]
        fc.update()


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
# Interactive Scale
# ---------------------------------------------------------------------------

class AA_OT_p6_modal_scale(bpy.types.Operator):
    """Drag the mouse to scale keyframe timing live."""

    bl_idname = "animassist.p6_modal_scale"
    bl_label = "Interactive Scale"
    bl_description = "Drag left/right to scale keyframe timing interactively"
    bl_options = {"REGISTER", "UNDO", "BLOCKING"}

    @classmethod
    def poll(cls, context):
        return _p6_base_poll(context)

    def invoke(self, context: bpy.types.Context, event):
        p6 = get_p6(context)
        if p6 is None:
            self.report({"WARNING"}, "Retiming properties not available")
            return {"CANCELLED"}

        self._fcurves, self._obj_name = _get_fcurves(context)
        if not self._fcurves:
            self.report({"WARNING"}, "No action on active object")
            return {"CANCELLED"}

        # Resolve pivot from current properties.
        all_frames = rm.collect_key_frames(self._fcurves)
        self._pivot = rm.resolve_pivot(
            p6.anchor_mode,
            all_frames,
            float(context.scene.frame_current),
            custom_frame=p6.pivot_frame,
        )
        self._snap = p6.modal_snap

        # Snapshot before any mutations.
        self._snap_data = _snap_fcurves(self._fcurves)

        # Track initial mouse position.
        self._init_x = event.mouse_x
        self._current_factor = 1.0

        context.window_manager.modal_handler_add(self)
        self._update_header(context)
        return {"RUNNING_MODAL"}

    def modal(self, context: bpy.types.Context, event):
        if event.type in {"MOUSEMOVE", "INBETWEEN_MOUSEMOVE"}:
            dx = event.mouse_x - self._init_x
            # Sensitivity: 200 px = ×2 scale (0.5% per pixel baseline).
            speed = 0.005
            if event.shift:
                speed *= 0.1
            raw_factor = 1.0 + dx * speed
            factor = max(0.01, raw_factor)
            snap = self._snap or event.ctrl

            _restore_snap(self._fcurves, self._snap_data)
            rm.apply_scale(self._fcurves, self._pivot, factor, snap=snap)
            self._current_factor = factor

            self._update_header(context)
            _tag_redraw(context)

        elif event.type in {"LEFTMOUSE", "RET", "NUMPAD_ENTER"}:
            if event.value == "PRESS":
                self._finish(context)
                return {"FINISHED"}

        elif event.type in {"RIGHTMOUSE", "ESC"}:
            self._cancel(context)
            return {"CANCELLED"}

        return {"RUNNING_MODAL"}

    def _update_header(self, context: bpy.types.Context) -> None:
        p6 = get_p6(context)
        show = p6 is not None and p6.modal_show_header
        if show:
            try:
                context.area.header_text_set(
                    f"Scale: ×{self._current_factor:.3f} | "
                    "LMB/Enter=Confirm  RMB/Esc=Cancel  Shift=Precise  Ctrl=Snap"
                )
            except Exception:
                pass

    def _finish(self, context: bpy.types.Context) -> None:
        try:
            context.area.header_text_set(None)
        except Exception:
            pass
        self.report({"INFO"}, f"Scale ×{self._current_factor:.3f}")

    def _cancel(self, context: bpy.types.Context) -> None:
        _restore_snap(self._fcurves, self._snap_data)
        try:
            context.area.header_text_set(None)
        except Exception:
            pass
        _tag_redraw(context)
        self.report({"INFO"}, "Interactive scale cancelled")

    def cancel(self, context: bpy.types.Context):
        self._cancel(context)


# ---------------------------------------------------------------------------
# Interactive Offset
# ---------------------------------------------------------------------------

class AA_OT_p6_modal_offset(bpy.types.Operator):
    """Drag the mouse to shift keyframe timing live."""

    bl_idname = "animassist.p6_modal_offset"
    bl_label = "Interactive Offset"
    bl_description = "Drag left/right to offset keyframe timing interactively"
    bl_options = {"REGISTER", "UNDO", "BLOCKING"}

    @classmethod
    def poll(cls, context):
        return _p6_base_poll(context)

    def invoke(self, context: bpy.types.Context, event):
        p6 = get_p6(context)
        if p6 is None:
            self.report({"WARNING"}, "Retiming properties not available")
            return {"CANCELLED"}

        self._fcurves, self._obj_name = _get_fcurves(context)
        if not self._fcurves:
            self.report({"WARNING"}, "No action on active object")
            return {"CANCELLED"}

        self._snap = p6.modal_snap
        self._snap_data = _snap_fcurves(self._fcurves)
        self._init_x = event.mouse_x
        self._current_delta = 0.0

        context.window_manager.modal_handler_add(self)
        self._update_header(context)
        return {"RUNNING_MODAL"}

    def modal(self, context: bpy.types.Context, event):
        if event.type in {"MOUSEMOVE", "INBETWEEN_MOUSEMOVE"}:
            dx = event.mouse_x - self._init_x
            # 10 px ≈ 1 frame baseline.
            speed = 0.1
            if event.shift:
                speed *= 0.1  # Sub-frame precision.
            delta = dx * speed
            snap = self._snap or event.ctrl

            _restore_snap(self._fcurves, self._snap_data)
            rm.apply_offset(self._fcurves, delta, snap=snap)
            self._current_delta = delta

            self._update_header(context)
            _tag_redraw(context)

        elif event.type in {"LEFTMOUSE", "RET", "NUMPAD_ENTER"}:
            if event.value == "PRESS":
                self._finish(context)
                return {"FINISHED"}

        elif event.type in {"RIGHTMOUSE", "ESC"}:
            self._cancel(context)
            return {"CANCELLED"}

        return {"RUNNING_MODAL"}

    def _update_header(self, context: bpy.types.Context) -> None:
        p6 = get_p6(context)
        show = p6 is not None and p6.modal_show_header
        if show:
            try:
                sign = "+" if self._current_delta >= 0 else ""
                context.area.header_text_set(
                    f"Offset: {sign}{self._current_delta:.1f}f | "
                    "LMB/Enter=Confirm  RMB/Esc=Cancel  Shift=Sub-frame  Ctrl=Snap"
                )
            except Exception:
                pass

    def _finish(self, context: bpy.types.Context) -> None:
        try:
            context.area.header_text_set(None)
        except Exception:
            pass
        sign = "+" if self._current_delta >= 0 else ""
        self.report({"INFO"}, f"Offset {sign}{self._current_delta:.1f}f")

    def _cancel(self, context: bpy.types.Context) -> None:
        _restore_snap(self._fcurves, self._snap_data)
        try:
            context.area.header_text_set(None)
        except Exception:
            pass
        _tag_redraw(context)
        self.report({"INFO"}, "Interactive offset cancelled")

    def cancel(self, context: bpy.types.Context):
        self._cancel(context)


# ---------------------------------------------------------------------------
# Class list
# ---------------------------------------------------------------------------

CLASSES: tuple[type, ...] = (
    AA_OT_p6_modal_scale,
    AA_OT_p6_modal_offset,
)
