"""Advanced key selection operators (17 ops).

All operators are poll-gated to animation editors and operate on currently
visible FCurves via ``core.context_utils`` / ``core.selection_p2``.
"""

from __future__ import annotations

from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, StringProperty
from bpy.types import Operator

from ..core import selection_p2 as sel
from ..core.context_utils import (
    in_anim_editor,
    iter_visible_fcurves,
    key_identity,
)
from ..core import key_metadata as meta
from ..core.logging import get_logger

_log = get_logger(__name__)


class _AnimEditorOp(Operator):
    @classmethod
    def poll(cls, context):
        return in_anim_editor(context)


# ---------------------------------------------------------------------------
# 1-3. Basic extension operations
# ---------------------------------------------------------------------------

class ANIMASSIST_OT_select_all_visible(_AnimEditorOp):
    bl_idname = "animassist.select_all_visible"
    bl_label = "Select All Visible Keys"
    bl_description = "Select every key on every visible FCurve"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        n = sel.select_all_visible(context, True)
        self.report({"INFO"}, f"Selected {n} keys")
        return {"FINISHED"}


class ANIMASSIST_OT_deselect_all_visible(_AnimEditorOp):
    bl_idname = "animassist.deselect_all_visible"
    bl_label = "Deselect All Visible Keys"
    bl_description = "Deselect every key on every visible FCurve"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        sel.select_all_visible(context, False)
        return {"FINISHED"}


class ANIMASSIST_OT_invert_selection(_AnimEditorOp):
    bl_idname = "animassist.invert_selection"
    bl_label = "Invert Key Selection"
    bl_description = "Invert the selection of keys on visible FCurves"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        sel.invert_visible(context)
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# 4-6. By-type selection
# ---------------------------------------------------------------------------

_KEY_TYPE_ITEMS = [
    ("KEYFRAME", "Keyframe", ""),
    ("BREAKDOWN", "Breakdown", ""),
    ("MOVING_HOLD", "Moving Hold", ""),
    ("EXTREME", "Extreme", ""),
    ("JITTER", "Jitter", ""),
]

_INTERP_ITEMS = [
    ("CONSTANT", "Constant", ""),
    ("LINEAR", "Linear", ""),
    ("BEZIER", "Bezier", ""),
]

_HANDLE_ITEMS = [
    ("AUTO_CLAMPED", "Auto Clamped", ""),
    ("AUTO", "Auto", ""),
    ("VECTOR", "Vector", ""),
    ("ALIGNED", "Aligned", ""),
    ("FREE", "Free", ""),
]


class ANIMASSIST_OT_select_by_type(_AnimEditorOp):
    bl_idname = "animassist.select_by_key_type_adv"
    bl_label = "Select Keys by Type"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Select keys whose Blender key type matches (Keyframe / Breakdown / Hold / Extreme / Jitter)"
    bl_options = {"REGISTER", "UNDO"}

    key_type: EnumProperty(  # type: ignore[valid-type]
        name="Key Type",
        description="Blender key type to match",
        items=_KEY_TYPE_ITEMS,
        default="KEYFRAME",
    )
    additive: BoolProperty(  # type: ignore[valid-type]
        name="Extend",
        description="Add to the existing selection instead of replacing it",
        default=False,
    )

    def execute(self, context):
        kt = self.key_type
        n = sel.select_where(
            context,
            lambda _fc, _i, kp: kp.type == kt,
            additive=self.additive,
        )
        self.report({"INFO"}, f"Selected {n} {kt} keys")
        return {"FINISHED"}


class ANIMASSIST_OT_select_by_interpolation(_AnimEditorOp):
    bl_idname = "animassist.select_by_interpolation"
    bl_label = "Select Keys by Interpolation"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Select keys whose interpolation type matches Constant, Linear, or Bezier"
    bl_options = {"REGISTER", "UNDO"}

    interp: EnumProperty(  # type: ignore[valid-type]
        name="Interpolation",
        description="Interpolation type to match",
        items=_INTERP_ITEMS,
        default="BEZIER",
    )
    additive: BoolProperty(  # type: ignore[valid-type]
        name="Extend",
        description="Add to the existing selection instead of replacing it",
        default=False,
    )

    def execute(self, context):
        ip = self.interp
        n = sel.select_where(
            context,
            lambda _fc, _i, kp: kp.interpolation == ip,
            additive=self.additive,
        )
        self.report({"INFO"}, f"Selected {n} keys")
        return {"FINISHED"}


class ANIMASSIST_OT_select_by_handle_type(_AnimEditorOp):
    bl_idname = "animassist.select_by_handle_type_adv"
    bl_label = "Select Keys by Handle Type"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Select keys whose left or right handle matches the chosen handle type"
    bl_options = {"REGISTER", "UNDO"}

    handle_type: EnumProperty(  # type: ignore[valid-type]
        name="Handle Type",
        description="Handle type to match on either side of the key",
        items=_HANDLE_ITEMS,
        default="AUTO_CLAMPED",
    )
    additive: BoolProperty(  # type: ignore[valid-type]
        name="Extend",
        description="Add to the existing selection instead of replacing it",
        default=False,
    )

    def execute(self, context):
        ht = self.handle_type
        n = sel.select_where(
            context,
            lambda _fc, _i, kp: kp.handle_left_type == ht or kp.handle_right_type == ht,
            additive=self.additive,
        )
        self.report({"INFO"}, f"Selected {n} keys")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# 7-9. Range-based selection
# ---------------------------------------------------------------------------

class ANIMASSIST_OT_select_frame_range(_AnimEditorOp):
    bl_idname = "animassist.select_frame_range"
    bl_label = "Select Keys in Frame Range"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Select every key whose frame falls inside [start, end]"
    bl_options = {"REGISTER", "UNDO"}

    start: FloatProperty(  # type: ignore[valid-type]
        name="Start",
        description="First frame of the inclusive selection range",
        default=1.0,
    )
    end: FloatProperty(  # type: ignore[valid-type]
        name="End",
        description="Last frame of the inclusive selection range",
        default=250.0,
    )

    def execute(self, context):
        n = sel.select_frame_range(context, self.start, self.end)
        self.report({"INFO"}, f"Selected {n} keys in [{self.start}, {self.end}]")
        return {"FINISHED"}


class ANIMASSIST_OT_select_playback_range(_AnimEditorOp):
    bl_idname = "animassist.select_playback_range"
    bl_label = "Select Keys in Playback Range"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Select every key inside the scene playback range"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scn = context.scene
        n = sel.select_frame_range(context, scn.frame_start, scn.frame_end)
        self.report({"INFO"}, f"Selected {n} keys")
        return {"FINISHED"}


class ANIMASSIST_OT_select_preview_range(_AnimEditorOp):
    bl_idname = "animassist.select_preview_range"
    bl_label = "Select Keys in Preview Range"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Select every key inside the scene preview range (only enabled when Use Preview Range is on)"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return in_anim_editor(context) and context.scene.use_preview_range

    def execute(self, context):
        scn = context.scene
        n = sel.select_frame_range(context, scn.frame_preview_start, scn.frame_preview_end)
        self.report({"INFO"}, f"Selected {n} keys")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# 10-12. Structural selection
# ---------------------------------------------------------------------------

class ANIMASSIST_OT_select_every_nth(_AnimEditorOp):
    bl_idname = "animassist.select_every_nth"
    bl_label = "Select Every Nth Key"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Select every Nth key on each visible FCurve, starting at the supplied offset"
    bl_options = {"REGISTER", "UNDO"}

    n: IntProperty(  # type: ignore[valid-type]
        name="N",
        description="Stride between selected keys (1 selects every key)",
        default=2, min=1, max=1000,
    )
    offset: IntProperty(  # type: ignore[valid-type]
        name="Offset",
        description="Index of the first key to select on each FCurve",
        default=0, min=0, max=1000,
    )

    def execute(self, context):
        count = sel.select_every_nth(context, self.n, self.offset)
        self.report({"INFO"}, f"Selected {count} keys")
        return {"FINISHED"}


class ANIMASSIST_OT_select_neighbors(_AnimEditorOp):
    bl_idname = "animassist.select_neighbors"
    bl_label = "Extend Selection to Neighbours"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Grow the selection one step to the left, right, or both directions"
    bl_options = {"REGISTER", "UNDO"}

    direction: EnumProperty(  # type: ignore[valid-type]
        name="Direction",
        description="Which neighbours to add to the selection",
        items=[
            ("LEFT", "Left", "Add the immediate left neighbour of every selected key"),
            ("RIGHT", "Right", "Add the immediate right neighbour of every selected key"),
            ("BOTH", "Both", "Add both neighbours of every selected key"),
        ],
        default="BOTH",
    )

    def execute(self, context):
        sel.select_neighbors(context, self.direction)
        return {"FINISHED"}


class ANIMASSIST_OT_select_between_selected(_AnimEditorOp):
    bl_idname = "animassist.select_between_selected"
    bl_label = "Select Between First/Last Selected"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Select every key between the earliest and latest currently-selected key"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        bounds = sel.selection_bounds(context)
        if bounds is None:
            self.report({"WARNING"}, "No keys selected")
            return {"CANCELLED"}
        sel.select_frame_range(context, *bounds)
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# 13-15. Extremes / first / last
# ---------------------------------------------------------------------------

class ANIMASSIST_OT_select_first_last(_AnimEditorOp):
    bl_idname = "animassist.select_first_last"
    bl_label = "Select First/Last Keys"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Select the endpoint keys (first, last, or both) on every visible FCurve"
    bl_options = {"REGISTER", "UNDO"}

    mode: EnumProperty(  # type: ignore[valid-type]
        name="Endpoint",
        description="Which endpoint keys to select",
        items=[
            ("FIRST", "First", "Select only the first key of each FCurve"),
            ("LAST", "Last", "Select only the last key of each FCurve"),
            ("BOTH", "Both", "Select both endpoint keys of each FCurve"),
        ],
        default="BOTH",
    )

    def execute(self, context):
        count = 0
        for _o, _a, fc in iter_visible_fcurves(context):
            n = len(fc.keyframe_points)
            if n == 0:
                continue
            for i, kp in enumerate(fc.keyframe_points):
                keep = (
                    (self.mode in ("FIRST", "BOTH") and i == 0)
                    or (self.mode in ("LAST", "BOTH") and i == n - 1)
                )
                kp.select_control_point = keep
                kp.select_left_handle = keep
                kp.select_right_handle = keep
                if keep:
                    count += 1
        self.report({"INFO"}, f"Selected {count} keys")
        return {"FINISHED"}


class ANIMASSIST_OT_select_local_extremes(_AnimEditorOp):
    bl_idname = "animassist.select_local_extremes"
    bl_label = "Select Local Extremes"
    bl_description = "Select keys that are local min or max on their curve"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        count = 0
        for _o, _a, fc in iter_visible_fcurves(context):
            kps = fc.keyframe_points
            for i, kp in enumerate(kps):
                is_ext = False
                if 0 < i < len(kps) - 1:
                    a, b, c = kps[i - 1].co.y, kp.co.y, kps[i + 1].co.y
                    is_ext = (b > a and b > c) or (b < a and b < c)
                elif i == 0 and len(kps) > 1:
                    is_ext = kp.co.y != kps[1].co.y
                elif i == len(kps) - 1 and len(kps) > 1:
                    is_ext = kp.co.y != kps[-2].co.y
                kp.select_control_point = is_ext
                kp.select_left_handle = is_ext
                kp.select_right_handle = is_ext
                if is_ext:
                    count += 1
        self.report({"INFO"}, f"Selected {count} extremes")
        return {"FINISHED"}


class ANIMASSIST_OT_select_flat_segments(_AnimEditorOp):
    bl_idname = "animassist.select_flat_segments"
    bl_label = "Select Keys in Flat Segments"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Select keys whose value matches at least one neighbour within the supplied tolerance"
    bl_options = {"REGISTER", "UNDO"}

    tol: FloatProperty(  # type: ignore[valid-type]
        name="Tolerance",
        description="Maximum value delta to a neighbour that still counts as flat",
        default=1e-4, min=0.0,
    )

    def execute(self, context):
        t = self.tol
        n = sel.select_where(
            context,
            lambda fc, i, kp: (
                (i > 0 and abs(fc.keyframe_points[i - 1].co.y - kp.co.y) <= t)
                or (
                    i < len(fc.keyframe_points) - 1
                    and abs(fc.keyframe_points[i + 1].co.y - kp.co.y) <= t
                )
            ),
        )
        self.report({"INFO"}, f"Selected {n} flat-segment keys")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# 16-17. Metadata-based selection
# ---------------------------------------------------------------------------

class ANIMASSIST_OT_select_by_tag(_AnimEditorOp):
    bl_idname = "animassist.select_by_tag"
    bl_label = "Select Keys by Tag"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Select every key whose metadata tag matches the supplied string"
    bl_options = {"REGISTER", "UNDO"}

    tag: StringProperty(  # type: ignore[valid-type]
        name="Tag",
        description="Exact tag string to match against each key's metadata record",
        default="",
    )

    def execute(self, context):
        scene = context.scene
        tag = self.tag
        count = 0
        for obj, _a, fc in iter_visible_fcurves(context):
            for kp in fc.keyframe_points:
                ident = key_identity(obj.name, fc, kp.co.x)
                item = meta.get_meta(scene, ident)
                hit = bool(item and item.tag == tag)
                kp.select_control_point = hit
                kp.select_left_handle = hit
                kp.select_right_handle = hit
                if hit:
                    count += 1
        self.report({"INFO"}, f"Selected {count} tagged keys")
        return {"FINISHED"}


class ANIMASSIST_OT_select_by_value_range(_AnimEditorOp):
    bl_idname = "animassist.select_by_value_range"
    bl_label = "Select Keys by Value Range"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Select keys whose value (co.y) lies inside the supplied min/max range"
    bl_options = {"REGISTER", "UNDO"}

    lo: FloatProperty(  # type: ignore[valid-type]
        name="Min",
        description="Lower bound of the inclusive value range",
        default=0.0,
    )
    hi: FloatProperty(  # type: ignore[valid-type]
        name="Max",
        description="Upper bound of the inclusive value range",
        default=1.0,
    )
    additive: BoolProperty(  # type: ignore[valid-type]
        name="Extend",
        description="Add to existing selection instead of replacing it",
        default=False,
    )

    def execute(self, context):
        lo, hi = min(self.lo, self.hi), max(self.lo, self.hi)
        n = sel.select_where(
            context,
            lambda _fc, _i, kp: lo <= kp.co.y <= hi,
            additive=self.additive,
        )
        self.report({"INFO"}, f"Selected {n} keys in value range")
        return {"FINISHED"}


class ANIMASSIST_OT_select_protected(_AnimEditorOp):
    bl_idname = "animassist.select_protected"
    bl_label = "Select Protected Keys"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Select every key whose metadata has the protected flag set"
    bl_options = {"REGISTER", "UNDO"}

    invert: BoolProperty(  # type: ignore[valid-type]
        name="Invert",
        description="Select unprotected keys instead of protected ones",
        default=False,
    )

    def execute(self, context):
        scene = context.scene
        count = 0
        for obj, _a, fc in iter_visible_fcurves(context):
            for kp in fc.keyframe_points:
                ident = key_identity(obj.name, fc, kp.co.x)
                hit = meta.is_protected(scene, ident)
                if self.invert:
                    hit = not hit
                kp.select_control_point = hit
                kp.select_left_handle = hit
                kp.select_right_handle = hit
                if hit:
                    count += 1
        self.report({"INFO"}, f"Selected {count} keys")
        return {"FINISHED"}


classes: tuple[type, ...] = (
    ANIMASSIST_OT_select_all_visible,
    ANIMASSIST_OT_deselect_all_visible,
    ANIMASSIST_OT_invert_selection,
    ANIMASSIST_OT_select_by_type,
    ANIMASSIST_OT_select_by_interpolation,
    ANIMASSIST_OT_select_by_handle_type,
    ANIMASSIST_OT_select_frame_range,
    ANIMASSIST_OT_select_playback_range,
    ANIMASSIST_OT_select_preview_range,
    ANIMASSIST_OT_select_every_nth,
    ANIMASSIST_OT_select_neighbors,
    ANIMASSIST_OT_select_between_selected,
    ANIMASSIST_OT_select_first_last,
    ANIMASSIST_OT_select_local_extremes,
    ANIMASSIST_OT_select_flat_segments,
    ANIMASSIST_OT_select_by_value_range,
    ANIMASSIST_OT_select_by_tag,
    ANIMASSIST_OT_select_protected,
)
