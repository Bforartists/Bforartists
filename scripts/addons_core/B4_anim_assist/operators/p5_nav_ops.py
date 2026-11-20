# --- TRAJECTORY VISUALIZATION ---
"""Arc-issue navigation operators.

Operators for stepping through detected trajectory issues:

* **Jump Next Issue** — advance the playhead to the next issue frame.
* **Jump Prev Issue** — rewind the playhead to the previous issue frame.
* **Select Bad-Arc Keys** — select keyframes near detected issues.
* **Suggest Candidate Keys** — report frames where inserting a key might
  improve the arc (based on high-deviation regions).
"""

from __future__ import annotations

import bpy

from ..core.fcurve_compat import get_fcurves
from ..core.logging import get_logger
from ..core.p5_properties import get_p5
from ..core import p5_draw as p5_draw_mod
from ..core.p5_issues import (
    IssueMarker,
)

_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Shared poll
# ---------------------------------------------------------------------------

def _p5_nav_poll(context) -> bool:
    """Poll for nav operators: need a scene and overlay must be active."""
    if not hasattr(context, "scene") or context.scene is None:
        return False
    p5 = get_p5(context)
    return p5 is not None and p5.overlay_enabled


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_issues() -> list:
    """Return the current draw-time issue list."""
    return p5_draw_mod.get_issues()


def _tag_redraw(context):
    for area in context.screen.areas:
        if area.type == "VIEW_3D":
            area.tag_redraw()


# ---------------------------------------------------------------------------
# Jump to next issue
# ---------------------------------------------------------------------------

class AA_OT_p5_jump_next_issue(bpy.types.Operator):
    """Jump the playhead to the next detected issue frame."""

    bl_idname = "animassist.p5_jump_next_issue"
    bl_label = "Next Issue"
    bl_description = "Move the playhead forward to the next trajectory issue"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _p5_nav_poll(context)

    def execute(self, context):
        issues = _get_issues()
        if not issues:
            self.report({"INFO"}, "No issues detected")
            return {"CANCELLED"}

        current = float(context.scene.frame_current)
        # Find the first issue whose frame is strictly after the current frame.
        candidates = [m for m in issues if m.frame > current + 0.5]
        if not candidates:
            # Wrap around to the first issue.
            candidates = sorted(issues, key=lambda m: m.frame)

        if candidates:
            target = candidates[0]
            context.scene.frame_set(int(round(target.frame)))
            self.report({"INFO"}, f"{target.issue_type} at frame {int(round(target.frame))}")
            _tag_redraw(context)
            return {"FINISHED"}

        self.report({"INFO"}, "No more issues")
        return {"CANCELLED"}


# ---------------------------------------------------------------------------
# Jump to previous issue
# ---------------------------------------------------------------------------

class AA_OT_p5_jump_prev_issue(bpy.types.Operator):
    """Jump the playhead to the previous detected issue frame."""

    bl_idname = "animassist.p5_jump_prev_issue"
    bl_label = "Previous Issue"
    bl_description = "Move the playhead backward to the previous trajectory issue"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _p5_nav_poll(context)

    def execute(self, context):
        issues = _get_issues()
        if not issues:
            self.report({"INFO"}, "No issues detected")
            return {"CANCELLED"}

        current = float(context.scene.frame_current)
        # Find the last issue whose frame is strictly before the current frame.
        candidates = [m for m in issues if m.frame < current - 0.5]
        if not candidates:
            # Wrap around to the last issue.
            candidates = sorted(issues, key=lambda m: m.frame, reverse=True)

        if candidates:
            target = candidates[-1] if candidates[0].frame < current else candidates[0]
            # For the wrap-around case, pick the last issue.
            if all(m.frame >= current - 0.5 for m in issues):
                target = max(issues, key=lambda m: m.frame)
            else:
                target = max(
                    (m for m in issues if m.frame < current - 0.5),
                    key=lambda m: m.frame,
                )
            context.scene.frame_set(int(round(target.frame)))
            self.report({"INFO"}, f"{target.issue_type} at frame {int(round(target.frame))}")
            _tag_redraw(context)
            return {"FINISHED"}

        self.report({"INFO"}, "No more issues")
        return {"CANCELLED"}


# ---------------------------------------------------------------------------
# Select bad-arc keys
# ---------------------------------------------------------------------------

class AA_OT_p5_select_bad_arc_keys(bpy.types.Operator):
    """Select keyframe points near detected arc issues."""

    bl_idname = "animassist.p5_select_bad_arc_keys"
    bl_label = "Select Bad-Arc Keys"
    bl_description = (
        "Select keyframes that are closest to detected arc drift, "
        "pop, zig-zag, and spacing issues"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _p5_nav_poll(context)

    proximity: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Proximity",
        description="Frame distance within which a keyframe is considered 'near' an issue",
        default=2.0, min=0.5, soft_max=10.0,
    )

    def execute(self, context):
        issues = _get_issues()
        if not issues:
            self.report({"INFO"}, "No issues detected — run diagnostics first")
            return {"CANCELLED"}

        obj = getattr(context, "active_object", None)
        if obj is None:
            self.report({"WARNING"}, "No active object. Select an object and try again")
            return {"CANCELLED"}

        adata = getattr(obj, "animation_data", None)
        action = getattr(adata, "action", None) if adata else None
        if action is None:
            self.report({"WARNING"}, "No action on active object")
            return {"CANCELLED"}

        # Collect issue frames.
        issue_frames = {round(m.frame) for m in issues}

        # Walk all keyframe points on location channels and select those
        # near an issue frame.
        selected_count = 0
        for fc in get_fcurves(action, anim_data=adata):
            if "location" not in fc.data_path:
                continue
            for kp in fc.keyframe_points:
                kf = round(kp.co.x)
                for issue_f in issue_frames:
                    if abs(kf - issue_f) <= self.proximity:
                        kp.select_control_point = True
                        selected_count += 1
                        break
                else:
                    kp.select_control_point = False

        self.report({"INFO"}, f"Selected {selected_count} keyframe(s) near issues")
        _tag_redraw(context)
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Suggest candidate keys
# ---------------------------------------------------------------------------

class AA_OT_p5_suggest_candidates(bpy.types.Operator):
    """Report frames where inserting a key might improve the arc."""

    bl_idname = "animassist.p5_suggest_candidates"
    bl_label = "Suggest Candidate Keys"
    bl_description = (
        "Identify frames with high deviation where inserting a keyframe "
        "might improve the arc quality"
    )
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return _p5_nav_poll(context)

    max_suggestions: bpy.props.IntProperty(  # type: ignore[valid-type]
        name="Max Suggestions",
        description="Maximum number of candidate frames to report",
        default=5, min=1, soft_max=20,
    )

    def execute(self, context):
        issues = _get_issues()
        if not issues:
            self.report({"INFO"}, "No issues — arc looks clean")
            return {"CANCELLED"}

        # Focus on high-severity drift and spacing issues.
        high_sev = sorted(
            [m for m in issues if m.severity > 0.3],
            key=lambda m: -m.severity,
        )

        if not high_sev:
            self.report({"INFO"}, "No high-severity issues found")
            return {"CANCELLED"}

        # Deduplicate by frame (within 2-frame radius).
        suggestions: list[IssueMarker] = []
        used_frames: set[int] = set()
        for m in high_sev:
            f = int(round(m.frame))
            if f not in used_frames:
                suggestions.append(m)
                # Mark nearby frames as used.
                for offset in range(-2, 3):
                    used_frames.add(f + offset)
            if len(suggestions) >= self.max_suggestions:
                break

        lines = [f"  Frame {int(round(m.frame))}: {m.issue_type} (severity {m.severity:.2f})"
                 for m in suggestions]
        msg = "Candidate frames for new keys:\n" + "\n".join(lines)
        self.report({"INFO"}, msg)
        _log.info(msg)

        return {"FINISHED"}


CLASSES: tuple[type, ...] = (
    AA_OT_p5_jump_next_issue,
    AA_OT_p5_jump_prev_issue,
    AA_OT_p5_select_bad_arc_keys,
    AA_OT_p5_suggest_candidates,
)
