"""Channel isolation/filtering operators (10 ops)."""

from __future__ import annotations

from bpy.props import EnumProperty, StringProperty
from bpy.types import Operator

from ..core import channel_iso as ch
from ..core.context_utils import in_anim_editor
from ..core.logging import get_logger
from ..core.helpers import report_failure

_log = get_logger(__name__)


class _AnimEditorOp(Operator):
    @classmethod
    def poll(cls, context):
        return in_anim_editor(context)


class ANIMASSIST_OT_isolate_selected_channels(_AnimEditorOp):
    bl_idname = "animassist.isolate_selected_channels"
    bl_label = "Isolate Selected Channels"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Hide every FCurve except the ones currently selected"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        shown = ch.isolate_where(context, lambda _o, _a, fc: fc.select)
        self.report({"INFO"}, f"Isolated {shown} channels")
        return {"FINISHED"}


class ANIMASSIST_OT_isolate_transform(_AnimEditorOp):
    bl_idname = "animassist.isolate_transform"
    bl_label = "Isolate Transform Channels"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Hide every FCurve except the chosen transform group"
    bl_options = {"REGISTER", "UNDO"}

    channel: EnumProperty(  # type: ignore[valid-type]
        name="Channel Group",
        description="Which transform group to isolate",
        items=[
            ("loc", "Location", "Isolate Location FCurves"),
            ("rot", "Rotation", "Isolate Rotation FCurves"),
            ("scale", "Scale", "Isolate Scale FCurves"),
            ("all_transform", "All Transforms", "Isolate every transform FCurve"),
        ],
        default="loc",
    )

    def execute(self, context):
        pred = ch.match_transform_channel(self.channel)
        shown = ch.isolate_where(context, pred)
        self.report({"INFO"}, f"Isolated {shown} {self.channel} channels")
        return {"FINISHED"}


class ANIMASSIST_OT_isolate_selected_bones(_AnimEditorOp):
    bl_idname = "animassist.isolate_selected_bones"
    bl_label = "Isolate Selected Bones"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Hide every FCurve that does not belong to a selected pose bone"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return in_anim_editor(context) and context.object and context.object.type == "ARMATURE"

    def execute(self, context):
        pred = ch.match_selected_bones(context)
        shown = ch.isolate_where(context, pred)
        self.report({"INFO"}, f"Isolated {shown} bone channels")
        return {"FINISHED"}


class ANIMASSIST_OT_isolate_custom_props(_AnimEditorOp):
    bl_idname = "animassist.isolate_custom_props"
    bl_label = "Isolate Custom Properties"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Hide every FCurve except those targeting custom properties"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        shown = ch.isolate_where(context, ch.match_custom_property())
        self.report({"INFO"}, f"Isolated {shown} custom props")
        return {"FINISHED"}


class ANIMASSIST_OT_isolate_by_regex(_AnimEditorOp):
    bl_idname = "animassist.isolate_by_regex"
    bl_label = "Isolate Channels by Regex"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Hide every FCurve whose data path does not match the supplied Python regex"
    bl_options = {"REGISTER", "UNDO"}

    pattern: StringProperty(  # type: ignore[valid-type]
        name="Regex",
        description="Python regular expression matched against fc.data_path",
        default="",
    )

    def execute(self, context):
        if not self.pattern:
            self.report({"WARNING"}, "Empty regex")
            return {"CANCELLED"}
        try:
            pred = ch.match_data_path_regex(self.pattern)
        except Exception as exc:  # noqa: BLE001
            report_failure(self, "The pattern is not a valid regular expression", "Fix the pattern and try again", exc, detail=str(exc))
            return {"CANCELLED"}
        shown = ch.isolate_where(context, pred)
        self.report({"INFO"}, f"Isolated {shown} channels")
        return {"FINISHED"}


class ANIMASSIST_OT_show_all_channels(_AnimEditorOp):
    bl_idname = "animassist.show_all_channels"
    bl_label = "Show All Channels"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Unhide every FCurve in the active animation editor"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        n = 0
        for _o, _a, fc in ch.iter_action_fcurves(context):
            fc.hide = False
            n += 1
        self.report({"INFO"}, f"Showed {n} channels")
        return {"FINISHED"}


class ANIMASSIST_OT_invert_channel_visibility(_AnimEditorOp):
    bl_idname = "animassist.invert_channel_visibility"
    bl_label = "Invert Channel Visibility"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Flip the hide flag on every FCurve in the active editor"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        for _o, _a, fc in ch.iter_action_fcurves(context):
            fc.hide = not fc.hide
        return {"FINISHED"}


class ANIMASSIST_OT_push_isolation(_AnimEditorOp):
    bl_idname = "animassist.push_channel_isolation"
    bl_label = "Save Channel Isolation State"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Push the current channel hide and select state onto the isolation stack"
    bl_options = {"REGISTER"}

    def execute(self, context):
        ch.push_isolation(context)
        self.report({"INFO"}, "Isolation state saved")
        return {"FINISHED"}


class ANIMASSIST_OT_pop_isolation(_AnimEditorOp):
    bl_idname = "animassist.pop_channel_isolation"
    bl_label = "Restore Channel Isolation State"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Pop the most recently saved channel isolation snapshot off the stack"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        if not ch.pop_isolation(context):
            self.report({"WARNING"}, "No saved isolation state")
            return {"CANCELLED"}
        return {"FINISHED"}


class ANIMASSIST_OT_mute_unselected_channels(_AnimEditorOp):
    bl_idname = "animassist.mute_unselected_channels"
    bl_label = "Mute Unselected Channels"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Mute every FCurve except the currently selected ones"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        n = 0
        for _o, _a, fc in ch.iter_action_fcurves(context):
            fc.mute = not fc.select
            if fc.mute:
                n += 1
        self.report({"INFO"}, f"Muted {n} channels")
        return {"FINISHED"}


classes: tuple[type, ...] = (
    ANIMASSIST_OT_isolate_selected_channels,
    ANIMASSIST_OT_isolate_transform,
    ANIMASSIST_OT_isolate_selected_bones,
    ANIMASSIST_OT_isolate_custom_props,
    ANIMASSIST_OT_isolate_by_regex,
    ANIMASSIST_OT_show_all_channels,
    ANIMASSIST_OT_invert_channel_visibility,
    ANIMASSIST_OT_push_isolation,
    ANIMASSIST_OT_pop_isolation,
    ANIMASSIST_OT_mute_unselected_channels,
)
