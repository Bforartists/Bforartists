# --- OFFSET TOOLS ---
"""Modal drag offset operator.

Snapshot-on-invoke, restore-on-cancel architecture matching the pattern
validated in the breakdown modal operator:

1. ``invoke`` — resolve targets, snapshot every affected fcurve, start
   the modal context, and apply the initial delta (zero).
2. ``modal`` — on MOUSEMOVE recompute the drag delta from mouse
   displacement, ``_restore_snapshot()``, then ``_apply(delta)``. On
   SHIFT → fine, CTRL → coarse. Digit keys populate the numeric
   buffer displayed in the header. LMB/ENTER commit. RMB/ESC cancel.
3. ``_snapshot_fcurves`` — capture (frame, value, handle_left_x,
   handle_left_y, handle_right_x, handle_right_y, handle_left_type,
   handle_right_type, interpolation) per keyframe_point per fcurve.
4. ``_restore_snapshot`` — remove all current keyframe_points and
   recreate from the snapshot.

The operator exposes features 9/10 (screen-space H/V drag), 41 (ghost
header), 42 (commit/cancel), and 43 (numeric entry) for offset operations.
"""

from __future__ import annotations

from typing import Optional

import bpy
from bpy.props import FloatProperty

try:
    from mathutils import Vector
except Exception:  # pragma: no cover
    Vector = None  # type: ignore[assignment]

from ..core import p4_offset_math as om
from ..core import p4_targets as tg
from ..core.logging import get_logger
from ..core.p4_properties import get_p4

from .p4_offset_ops import (
    _resolve_options,
    _frames_from_scope,
    _run_offset,
    _valid_context,
)


# ---------------------------------------------------------------------------
# Snapshot helpers
# ---------------------------------------------------------------------------

def _snapshot_fcurves(action, fc_list):
    """Return a snapshot dict: ``id(fc) → list[tuple]`` with every kf row."""
    snap: dict[int, list[tuple]] = {}
    for fc in fc_list:
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
            ))
        snap[id(fc)] = rows
    return snap


_log = get_logger(__name__)


def _restore_snapshot(fc_list, snap: dict):
    """Remove all keys and recreate from the snapshot."""
    for fc in fc_list:
        fid = id(fc)
        rows = snap.get(fid)
        if rows is None:
            continue
        kps = fc.keyframe_points
        # Remove keys backwards so indices stay valid.
        count = len(kps)
        for i in range(count - 1, -1, -1):
            try:
                kps.remove(kps[i])
            except Exception:
                _log.debug("keyframe remove failed on %s[%d]", fc.data_path, fc.array_index, exc_info=True)
        # A failed remove leaves stale keys under the rebuild; ``insert`` at an
        # existing frame updates rather than duplicates, but keys at frames the
        # snapshot never held would survive.  Make that visible instead of silent.
        if len(kps):
            _log.warning(
                "cancel restore left %d stale key(s) on %s[%d]; curve may not "
                "match its pre-drag state", len(kps), fc.data_path, fc.array_index,
            )
        # Rebuild.
        for row in rows:
            frame, value, hlx, hly, hrx, hry, hlt, hrt, interp = row
            kp = kps.insert(frame, value, options={"FAST"})
            kp.handle_left = (hlx, hly)
            kp.handle_right = (hrx, hry)
            kp.handle_left_type = hlt
            kp.handle_right_type = hrt
            kp.interpolation = interp
        try:
            fc.update()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Numeric buffer
# ---------------------------------------------------------------------------

class _NumericBuffer:
    __slots__ = ("_buf",)

    def __init__(self):
        self._buf: str = ""

    def append(self, char: str) -> None:
        if char in "0123456789.":
            self._buf += char
        elif char == "-":
            if self._buf.startswith("-"):
                self._buf = self._buf[1:]
            else:
                self._buf = "-" + self._buf

    def clear(self) -> None:
        self._buf = ""

    def backspace(self) -> None:
        self._buf = self._buf[:-1]

    def value(self) -> Optional[float]:
        try:
            return float(self._buf) if self._buf else None
        except ValueError:
            return None

    def display(self) -> str:
        return self._buf or ""


# ---------------------------------------------------------------------------
# Modal operator
# ---------------------------------------------------------------------------

class AA_OT_p4_modal_offset(bpy.types.Operator):
    bl_idname = "animassist.p4_modal_offset"
    bl_label = "Modal Drag Offset"
    bl_description = (
        "Drag to offset the selected targets. Shift: fine, Ctrl: coarse. Click or Enter commits, Esc cancels"
    )
    bl_options = {"REGISTER", "UNDO"}

    sensitivity: FloatProperty(  # type: ignore[valid-type]
        name="Sensitivity",
        description="Pixels per unit of offset delta during modal drag.",
        default=100.0, min=1.0, soft_max=500.0,
    )

    @classmethod
    def poll(cls, context):
        return _valid_context(context)

    def invoke(self, context, event):
        opts = _resolve_options(context)
        if opts is None:
            self.report({"WARNING"}, "Offset properties unavailable.")
            return {"CANCELLED"}

        targets = tg.resolve_targets(context, pivot_mode=opts.pivot_mode)
        if not targets:
            self.report({"INFO"}, "No targets selected.")
            return {"CANCELLED"}

        action = context.active_object.animation_data.action
        frames = _frames_from_scope(context, opts, targets, action)
        if not frames:
            self.report({"INFO"}, "No frames matched the current scope.")
            return {"CANCELLED"}

        # Collect the full fcurve set for snapshotting.
        all_fcs: list[bpy.types.FCurve] = []
        for target in targets:
            for fc in tg.iter_target_fcurves(
                target,
                action,
                channel_mask=opts.channel_mask,
                skip_locked=opts.skip_locked,
                skip_muted=opts.skip_muted,
                keyed_only=opts.keyed_channels_only,
                selected_only=opts.selected_channels_only,
            ):
                if fc not in all_fcs:
                    all_fcs.append(fc)

        if not all_fcs:
            self.report({"INFO"}, "No writable channels to offset.")
            return {"CANCELLED"}

        self._snap = _snapshot_fcurves(action, all_fcs)
        self._fcs = all_fcs
        self._targets = targets
        self._opts = opts
        self._action = action
        self._frames = frames
        self._initial_mouse = (event.mouse_region_x, event.mouse_region_y)
        self._numeric = _NumericBuffer()
        self._current_delta = (0.0, 0.0)

        # Mark preview active.
        p4 = get_p4(context)
        if p4 is not None:
            p4.modal_preview_active = True

        context.window_manager.modal_handler_add(self)
        if context.area is not None:
            context.area.header_text_set("Drag to offset | Shift=Fine | Ctrl=Coarse | LMB/Enter=Commit | RMB/Esc=Cancel")
        return {"RUNNING_MODAL"}

    def _apply(self, context, dx: float, dy: float) -> None:
        # Override the translate amounts with the drag delta.
        self._opts.translate = (dx, dy, 0.0)
        self._opts.rotate = (0.0, 0.0, 0.0)
        self._opts.scale = (0.0, 0.0, 0.0)
        self._opts.channel_mask = "T"
        self._opts.fine_step = False
        self._opts.preset_multiplier = 1.0
        _run_offset(
            context, self._opts, self._targets, self._action, self._frames,
        )

    def modal(self, context, event):
        if event.type == "MOUSEMOVE":
            mx = event.mouse_region_x - self._initial_mouse[0]
            my = event.mouse_region_y - self._initial_mouse[1]
            scale = 1.0 / self.sensitivity
            if event.shift:
                scale *= 0.1
            if event.ctrl:
                scale *= 10.0
            dx = mx * scale
            dy = my * scale

            # Numeric override.
            nv = self._numeric.value()
            if nv is not None:
                dx = nv
                dy = 0.0

            # Restore then apply.
            _restore_snapshot(self._fcs, self._snap)
            self._apply(context, dx, dy)
            self._current_delta = (dx, dy)

            if context.area is not None:
                context.area.header_text_set(
                    f"Offset Δ = ({dx:.4f}, {dy:.4f})  [{self._numeric.display()}]"
                )
            return {"RUNNING_MODAL"}

        if event.type in {"LEFTMOUSE", "RET", "NUMPAD_ENTER"} and event.value == "PRESS":
            # Commit.
            delta = om.build_delta(
                translation=(self._current_delta[0], self._current_delta[1], 0.0),
                rotation_euler=(0.0, 0.0, 0.0),
                scale=(0.0, 0.0, 0.0),
                channel_mask="T",
                fine_step=False,
                multiplier=1.0,
            )
            om.remember_last(
                om.LastOffsetRecord(
                    delta=delta,
                    space=self._opts.space,
                    pivot_mode=self._opts.pivot_mode,
                    scope=self._opts.scope,
                    falloff_shape=self._opts.falloff_shape,
                )
            )
            self._header_restore(context)
            self.report({"INFO"}, f"Offset committed: Δ=({self._current_delta[0]:.4f}, {self._current_delta[1]:.4f}).")
            return {"FINISHED"}

        if event.type in {"RIGHTMOUSE", "ESC"} and event.value == "PRESS":
            # Cancel — restore pristine state.
            _restore_snapshot(self._fcs, self._snap)
            self._header_restore(context)
            self.report({"INFO"}, "Offset cancelled.")
            return {"CANCELLED"}

        # Numeric input.
        if event.value == "PRESS":
            ch = event.unicode
            if ch in "0123456789.-":
                self._numeric.append(ch)
                return {"RUNNING_MODAL"}
            if event.type == "BACK_SPACE":
                self._numeric.backspace()
                return {"RUNNING_MODAL"}

        return {"PASS_THROUGH"}

    def _header_restore(self, context):
        p4 = get_p4(context)
        if p4 is not None:
            p4.modal_preview_active = False
        if context.area is not None:
            context.area.header_text_set(None)


# ---------------------------------------------------------------------------
# Pivot-from-cursor / head / tail convenience
# ---------------------------------------------------------------------------

class AA_OT_p4_set_pivot_from_cursor(bpy.types.Operator):
    bl_idname = "animassist.p4_set_pivot_cursor"
    bl_label = "Pivot from 3D Cursor"
    bl_description = (
        "Set the custom pivot vector to the current 3D cursor location."
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return get_p4(context) is not None

    def execute(self, context):
        p4 = get_p4(context)
        if p4 is None:
            return {"CANCELLED"}
        cursor = context.scene.cursor.location
        p4.custom_pivot = (cursor.x, cursor.y, cursor.z)
        self.report({"INFO"}, f"Custom pivot set to ({cursor.x:.3f}, {cursor.y:.3f}, {cursor.z:.3f}).")
        return {"FINISHED"}


class AA_OT_p4_set_pivot_head(bpy.types.Operator):
    bl_idname = "animassist.p4_set_pivot_head"
    bl_label = "Pivot from Bone Head"
    bl_description = (
        "Set the custom pivot vector to the active pose bone's head."
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if get_p4(context) is None:
            return False
        obj = getattr(context, "active_object", None)
        if obj is None or obj.mode != "POSE":
            return False
        return getattr(context, "active_pose_bone", None) is not None

    def execute(self, context):
        p4 = get_p4(context)
        obj = context.active_object
        pb = context.active_pose_bone
        if p4 is None or pb is None:
            return {"CANCELLED"}
        world = obj.matrix_world @ pb.bone.head_local
        p4.custom_pivot = (world.x, world.y, world.z)
        self.report({"INFO"}, f"Pivot set to bone head ({world.x:.3f}, {world.y:.3f}, {world.z:.3f}).")
        return {"FINISHED"}


class AA_OT_p4_set_pivot_tail(bpy.types.Operator):
    bl_idname = "animassist.p4_set_pivot_tail"
    bl_label = "Pivot from Bone Tail"
    bl_description = (
        "Set the custom pivot vector to the active pose bone's tail."
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if get_p4(context) is None:
            return False
        obj = getattr(context, "active_object", None)
        if obj is None or obj.mode != "POSE":
            return False
        return getattr(context, "active_pose_bone", None) is not None

    def execute(self, context):
        p4 = get_p4(context)
        obj = context.active_object
        pb = context.active_pose_bone
        if p4 is None or pb is None:
            return {"CANCELLED"}
        world = obj.matrix_world @ pb.bone.tail_local
        p4.custom_pivot = (world.x, world.y, world.z)
        self.report({"INFO"}, f"Pivot set to bone tail ({world.x:.3f}, {world.y:.3f}, {world.z:.3f}).")
        return {"FINISHED"}


CLASSES: tuple[type, ...] = (
    AA_OT_p4_modal_offset,
    AA_OT_p4_set_pivot_from_cursor,
    AA_OT_p4_set_pivot_head,
    AA_OT_p4_set_pivot_tail,
)
