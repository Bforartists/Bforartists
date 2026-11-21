# --- RETIMING TOOLS ---
"""Gap and distribution operators.

Operators for detecting, filling, collapsing timing gaps; distributing keys
evenly; normalizing spacing; snapping to integer frames; and removing
duplicate-frame keys.

Gap detection results are cached in module-level state for the navigation
operators (jump-to-gap) and the diagnostics panel.
"""

from __future__ import annotations

import bpy

from ..core.logging import get_logger
from ..core.p6_properties import get_p6
from ..core import p6_retime_math as rm
from ..core import p6_diagnostics as diag
from ..core.fcurve_compat import get_fcurves

_log = get_logger(__name__)

# Module-level gap cache (populated by Detect Gaps, consumed by jump ops).
_cached_gaps: list[diag.TimingGap] = []
_cached_gaps_obj: str = ""


def get_cached_gaps() -> list[diag.TimingGap]:
    """Public accessor used by jump-to-gap diagnostic operators."""
    return _cached_gaps


def clear_cached_gaps() -> None:
    global _cached_gaps, _cached_gaps_obj
    _cached_gaps = []
    _cached_gaps_obj = ""


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
# Internal logic helpers — used by individual operators AND the combo op.
# By sharing these functions we avoid bpy.ops.* chaining, which is unsafe
# inside execute() due to context-override requirements.
# ---------------------------------------------------------------------------

def _run_detect_gaps(p6, fcurves, obj_name: str) -> list[diag.TimingGap]:
    """Detect gaps, update the module cache, and return the gap list."""
    global _cached_gaps, _cached_gaps_obj
    gaps = diag.detect_timing_gaps(fcurves, threshold=p6.gap_threshold)
    _cached_gaps = gaps
    _cached_gaps_obj = obj_name
    p6.last_diag_gap_count = len(gaps)
    return gaps


def _run_fill_gaps(p6, fcurves) -> int:
    """Fill all currently cached gaps. Returns the number of keys inserted."""
    mode = p6.gap_fill_mode
    if mode == "NONE":
        return 0
    inserted = 0
    for gap in _cached_gaps:
        mid = gap.mid_frame
        for fc in fcurves:
            try:
                val = fc.evaluate(mid)
            except Exception:
                val = 0.0
            kp = fc.keyframe_points.insert(mid, val, options={"NEEDED"})
            if kp is not None:
                kp.interpolation = "LINEAR" if mode == "LINEAR" else "CONSTANT"
                inserted += 1
        for fc in fcurves:
            fc.update()
    return inserted


# ---------------------------------------------------------------------------
# 1. Detect Gaps
# ---------------------------------------------------------------------------

class AA_OT_p6_detect_gaps(bpy.types.Operator):
    """Scan the active action for timing gaps wider than the threshold."""

    bl_idname = "animassist.p6_detect_gaps"
    bl_label = "Detect Gaps"
    bl_description = "Find timing gaps in the active action and cache results"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return _p6_base_poll(context)

    def execute(self, context):
        p6 = get_p6(context)
        if p6 is None:
            self.report({"WARNING"}, "Retiming properties not available")
            return {"CANCELLED"}

        fcurves, obj_name = _get_fcurves(context)
        if not fcurves:
            self.report({"WARNING"}, "No action on active object")
            return {"CANCELLED"}

        gaps = _run_detect_gaps(p6, fcurves, obj_name)

        if gaps:
            self.report(
                {"INFO"},
                f"Found {len(gaps)} gap(s) wider than {p6.gap_threshold:.0f}f",
            )
        else:
            self.report({"INFO"}, "No significant gaps found")

        _tag_redraw(context)
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# 2. Fill Gaps
# ---------------------------------------------------------------------------

class AA_OT_p6_fill_gaps(bpy.types.Operator):
    """Insert keys into every detected gap using the configured fill mode."""

    bl_idname = "animassist.p6_fill_gaps"
    bl_label = "Fill Gaps"
    bl_description = "Insert keys into detected gaps (run Detect Gaps first)"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _p6_base_poll(context) and bool(_cached_gaps)

    def execute(self, context):
        p6 = get_p6(context)
        if p6 is None:
            self.report({"WARNING"}, "Retiming properties not available")
            return {"CANCELLED"}

        if not _cached_gaps:
            self.report({"WARNING"}, "No gap cache — run Detect Gaps first")
            return {"CANCELLED"}

        fcurves, _ = _get_fcurves(context)
        if not fcurves:
            self.report({"WARNING"}, "No action on active object")
            return {"CANCELLED"}

        if p6.gap_fill_mode == "NONE":
            self.report({"INFO"}, "Fill Mode is 'Mark Only' — no keys inserted")
            return {"FINISHED"}

        n_gaps = len(_cached_gaps)
        inserted = _run_fill_gaps(p6, fcurves)

        _tag_redraw(context)
        self.report({"INFO"}, f"Inserted {inserted} fill key(s) in {n_gaps} gap(s)")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# 3. Collapse Gap at Playhead
# ---------------------------------------------------------------------------

class AA_OT_p6_collapse_gap(bpy.types.Operator):
    """Remove the timing gap nearest the playhead by ripple-shifting later keys."""

    bl_idname = "animassist.p6_collapse_gap"
    bl_label = "Collapse Gap at Playhead"
    bl_description = "Close the nearest detected gap by ripple-shifting later keys"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _p6_base_poll(context) and bool(_cached_gaps)

    def execute(self, context):
        if not _cached_gaps:
            self.report({"WARNING"}, "No gap cache — run Detect Gaps first")
            return {"CANCELLED"}

        fcurves, _ = _get_fcurves(context)
        if not fcurves:
            self.report({"WARNING"}, "No action on active object")
            return {"CANCELLED"}

        current = float(context.scene.frame_current)
        # Find the gap whose midpoint is nearest the playhead.
        nearest = min(_cached_gaps, key=lambda g: abs(g.mid_frame - current))

        # Ripple-shift keys after the gap start backward by the gap's size.
        rm.apply_ripple(
            fcurves,
            nearest.start_frame,
            -nearest.size,
            direction="FORWARD",
        )

        _tag_redraw(context)
        self.report(
            {"INFO"},
            f"Collapsed {nearest.size:.0f}f gap at frame {nearest.start_frame:.0f}",
        )
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# 4. Distribute Keys
# ---------------------------------------------------------------------------

class AA_OT_p6_distribute_keys(bpy.types.Operator):
    """Evenly space all keys within the active range."""

    bl_idname = "animassist.p6_distribute_keys"
    bl_label = "Distribute Keys"
    bl_description = "Evenly space keys within the active timing range"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _p6_base_poll(context)

    def execute(self, context):
        p6 = get_p6(context)
        if p6 is None:
            self.report({"WARNING"}, "Retiming properties not available")
            return {"CANCELLED"}

        fcurves, _ = _get_fcurves(context)
        if not fcurves:
            self.report({"WARNING"}, "No action on active object")
            return {"CANCELLED"}

        lo, hi = rm.resolve_active_range(p6, context)
        moved = rm.distribute_keys(fcurves, lo, hi, snap=p6.modal_snap)

        _tag_redraw(context)
        if moved:
            self.report({"INFO"}, f"Distributed {moved} key(s) in [{lo:.0f}, {hi:.0f}]")
        else:
            self.report({"INFO"}, "Need at least 3 keys in range to distribute")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# 5. Normalize Spacing
# ---------------------------------------------------------------------------

class AA_OT_p6_normalize_spacing(bpy.types.Operator):
    """Scale inter-key spacings toward the average spacing in the active range."""

    bl_idname = "animassist.p6_normalize_spacing"
    bl_label = "Normalize Spacing"
    bl_description = "Reduce spacing variance by nudging keys toward even spacing"
    bl_options = {"REGISTER", "UNDO"}

    strength: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Strength",
        description="How strongly to pull toward even spacing (0 = no change, 1 = full distribute)",
        default=0.5,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
    )

    @classmethod
    def poll(cls, context):
        return _p6_base_poll(context)

    def execute(self, context):
        p6 = get_p6(context)
        if p6 is None:
            self.report({"WARNING"}, "Retiming properties not available")
            return {"CANCELLED"}

        fcurves, _ = _get_fcurves(context)
        if not fcurves:
            self.report({"WARNING"}, "No action on active object")
            return {"CANCELLED"}

        lo, hi = rm.resolve_active_range(p6, context)

        # Collect in-range frames.
        frames = rm.collect_key_frames(fcurves)
        frames = [f for f in frames if lo <= f <= hi]
        n = len(frames)
        if n < 3:
            self.report({"INFO"}, "Need at least 3 keys in range")
            return {"FINISHED"}

        # Compute target positions (evenly distributed).
        span = frames[-1] - frames[0]
        step = span / (n - 1)
        targets = {f: frames[0] + i * step for i, f in enumerate(frames)}

        # Blend each key between current and target by strength.
        new_positions: dict[float, float] = {
            f: f + self.strength * (targets[f] - f) for f in frames
        }

        for fc in fcurves:
            for kp in fc.keyframe_points:
                x = kp.co.x
                # Match to closest in-range frame.
                closest = min(frames, key=lambda f: abs(f - x), default=None)
                if closest is not None and abs(x - closest) < 0.01:
                    new_x = new_positions.get(closest, x)
                    dx = new_x - kp.co.x
                    kp.co.x            = new_x
                    kp.handle_left.x  += dx
                    kp.handle_right.x += dx
            fc.update()

        _tag_redraw(context)
        self.report({"INFO"}, f"Normalized spacing for {n} keys (strength {self.strength:.0%})")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# 6. Snap to Integer Frames
# ---------------------------------------------------------------------------

class AA_OT_p6_snap_to_frames(bpy.types.Operator):
    """Round all keyframe positions to the nearest integer frame."""

    bl_idname = "animassist.p6_snap_to_frames"
    bl_label = "Snap to Frames"
    bl_description = "Round all sub-frame key positions to nearest integer frame"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _p6_base_poll(context)

    def execute(self, context):
        fcurves, _ = _get_fcurves(context)
        if not fcurves:
            self.report({"WARNING"}, "No action on active object")
            return {"CANCELLED"}

        moved = rm.snap_keys_to_frames(fcurves)
        _tag_redraw(context)
        self.report({"INFO"}, f"Snapped {moved} key(s) to integer frames")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# 7. Remove Duplicate-Frame Keys
# ---------------------------------------------------------------------------

class AA_OT_p6_clear_doubles(bpy.types.Operator):
    """Delete keyframes that share the same integer frame as another key."""

    bl_idname = "animassist.p6_clear_doubles"
    bl_label = "Remove Duplicates"
    bl_description = "Remove keys that share an integer frame with another key"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _p6_base_poll(context)

    def execute(self, context):
        fcurves, _ = _get_fcurves(context)
        if not fcurves:
            self.report({"WARNING"}, "No action on active object")
            return {"CANCELLED"}

        removed = rm.remove_duplicate_frames(fcurves)
        _tag_redraw(context)
        self.report({"INFO"}, f"Removed {removed} duplicate key(s)")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# 8. Detect and Fill (convenience combo)
# ---------------------------------------------------------------------------

class AA_OT_p6_detect_and_fill(bpy.types.Operator):
    """Detect gaps and immediately fill them in one step."""

    bl_idname = "animassist.p6_detect_and_fill"
    bl_label = "Detect & Fill Gaps"
    bl_description = "Run gap detection then fill all found gaps automatically"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _p6_base_poll(context)

    def execute(self, context):
        p6 = get_p6(context)
        if p6 is None:
            self.report({"WARNING"}, "Retiming properties not available")
            return {"CANCELLED"}

        fcurves, obj_name = _get_fcurves(context)
        if not fcurves:
            self.report({"WARNING"}, "No action on active object")
            return {"CANCELLED"}

        # Detect — populates the module-level cache.
        gaps = _run_detect_gaps(p6, fcurves, obj_name)
        if not gaps:
            self.report({"INFO"}, "No gaps found")
            return {"FINISHED"}

        # Fill — reads the module-level cache populated above.
        if p6.gap_fill_mode == "NONE":
            self.report(
                {"INFO"},
                f"Found {len(gaps)} gap(s) — Fill Mode is 'Mark Only', "
                "no keys inserted",
            )
            return {"FINISHED"}

        inserted = _run_fill_gaps(p6, fcurves)
        _tag_redraw(context)
        self.report(
            {"INFO"},
            f"Detected {len(gaps)} gap(s), inserted {inserted} fill key(s)",
        )
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Class list
# ---------------------------------------------------------------------------

CLASSES: tuple[type, ...] = (
    AA_OT_p6_detect_gaps,
    AA_OT_p6_fill_gaps,
    AA_OT_p6_collapse_gap,
    AA_OT_p6_distribute_keys,
    AA_OT_p6_normalize_spacing,
    AA_OT_p6_snap_to_frames,
    AA_OT_p6_clear_doubles,
    AA_OT_p6_detect_and_fill,
)
