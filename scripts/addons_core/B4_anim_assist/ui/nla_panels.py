"""NLA sidebar bodies: clip arrangement and transform corrections together."""
import bpy
from bpy.types import Panel

from ..core.nla_context import active_target, correction_reason, is_correction, latest_bake, source_references, targets
from .ui_helpers import wrapped_label


def native(layout, command, text):
    op = layout.operator("animassist.nla_native", text=text)
    op.command = command


def timing(layout, operation, text, frames=1):
    op = layout.operator("animassist.nla_time", text=text)
    op.operation, op.frames = operation, frames


def options(layout, key, label):
    header, body = layout.panel(key, default_closed=True)
    header.label(text=label)
    return body


def editable_body(layout, context):
    item = active_target(context)
    body = layout.column(align=True)
    body.enabled = bool(item and item.owner.is_editable and not item.track.lock
                        and item.strip.type == "CLIP" and item.strip.action and not context.scene.is_nla_tweakmode)
    return body, item


class _NlaPanel:
    bl_space_type = "NLA_EDITOR"
    bl_region_type = "UI"
    bl_category = "Anim Assist"
    bl_options = {"HIDE_HEADER"}


def draw_target(layout, context):
    item = active_target(context)
    if not item:
        layout.label(text="Select an Action clip")
        layout.label(text=f"Selected clips: {len(targets(context))}")
        col = layout.column()
        col.enabled = bool(context.object and context.object.is_editable and not context.scene.is_nla_tweakmode)
        col.operator("animassist.nla_add_clip", text="Add Existing Action Clip")
        return
    col = layout.column(align=True)
    wrapped_label(col, context, f"Owner: {item.owner.name}")
    wrapped_label(col, context, f"Clip: {item.strip.name}")
    if item.strip.type != "CLIP":
        col.label(text=f"Type: {item.strip.type.title()}")
        return
    if not item.strip.action:
        col.label(text="No source Action assigned", icon="INFO")
        col.prop(item.strip, "action", text="Source")
        return
    wrapped_label(col, context, f"Action: {item.strip.action.name}")
    col.label(text=f"Selected clips: {len(targets(context))}")
    if source_references(item.strip.action) > 1:
        wrapped_label(col, context, "Shared Action: source edits affect other clips", icon="INFO")
        col.operator("animassist.nla_unique", text="Make Selected Clips Unique")
    if item.track.lock:
        col.label(text="Track locked: unlock to edit", icon="LOCKED")
    if item.track.mute or item.strip.mute:
        col.label(text="Source is muted", icon="INFO")
    if any(t.is_solo for t in item.owner.animation_data.nla_tracks) and not item.track.is_solo:
        col.label(text="Excluded by another track's Solo", icon="INFO")
    if not item.owner.animation_data.use_nla:
        col.label(text="NLA evaluation is off", icon="INFO")
        col.prop(item.owner.animation_data, "use_nla", text="Evaluate NLA Stack")
    col.label(text=f"Scene: {item.strip.frame_start:g} – {item.strip.frame_end:g}")
    col.label(text=f"Source: {item.strip.action_frame_start:g} – {item.strip.action_frame_end:g}")
    if context.scene.is_nla_tweakmode:
        native(col, "FINISH", "Finish Editing")
        col.label(text="Arrangement is paused during source editing")
    else:
        native(col, "EDIT", "Edit Action")
    for editor, label in (("DOPESHEET_EDITOR", "Open Dope Sheet"), ("GRAPH_EDITOR", "Open Graph Editor")):
        col.operator("animassist.nla_open_editor", text=label).editor = editor


class ANIMASSIST_PT_nla_arrange(_NlaPanel, Panel):
    bl_idname = "ANIMASSIST_PT_nla_arrange"
    bl_label = "Arrange & Time"

    def draw(self, context):
        body, item = editable_body(self.layout, context)
        body.label(text="Selected clips · scene time")
        row = body.row(align=True)
        timing(row, "NUDGE", "−1f", -1)
        timing(row, "NUDGE", "+1f", 1)
        native(body, "MOVE", "Move Selected Clips")
        timing(body, "START", "Align Starts to Active Clip")
        timing(body, "END", "Align Ends to Active Clip")
        timing(body, "SEQUENCE", "Sequence Clips")
        more = options(body, "aa_nla_timing", "Timing Options")
        if more:
            more.label(text="Step and gap: Adjust Last Operation")
            more.label(text="Alignment reference: active selected clip")
            if item and item.strip.type == "CLIP":
                more.label(text=f"Active clip: {item.strip.name}")
                more.prop(item.strip, "scale")
                more.prop(item.strip, "repeat")
                more.prop(item.strip, "use_reverse", text="Reverse Source")
                more.prop(item.strip, "frame_start", text="Scene Start")
                more.prop(item.strip, "frame_end", text="Scene End")


class ANIMASSIST_PT_nla_blend(_NlaPanel, Panel):
    bl_idname = "ANIMASSIST_PT_nla_blend"
    bl_label = "Blend & Corrections"

    def draw(self, context):
        body, item = editable_body(self.layout, context)
        reason = correction_reason(item) if item and item.strip.type == "CLIP" else "Select one source Action clip"
        new = body.column()
        new.enabled = not reason and len(targets(context)) == 1
        new.operator("animassist.nla_correction", text="New Transform Correction")
        if reason:
            # Native wrapping keeps the explanation readable in narrow sidebars.
            wrapped_label(self.layout, context, reason)
        edit = body.column()
        edit.enabled = bool(item and is_correction(item.strip))
        native(edit, "CORRECTION", "Edit Correction")
        if item and not is_correction(item.strip):
            body.label(text="Ordinary clip: use Edit Action")
        if item and item.strip.type == "CLIP":
            wrapped_label(body, context, f"Active clip: {item.strip.name}")
            body.prop(item.strip, "blend_type", text="Blend")
            body.prop(item.strip, "use_animated_influence", text="Animated Influence")
            if item.strip.use_animated_influence:
                body.prop(item.strip, "influence", slider=True)
            else:
                wrapped_label(body, context, "Influence: automatic blend envelope")
            body.label(text="Key influence at the playhead")
            row = body.row(align=True)
            for value, label in ((0, "0%"), (.5, "50%"), (1, "100%")):
                row.operator("animassist.nla_influence", text=label).value = value
            more = options(body, "aa_nla_blend", "Blend Options")
            if more:
                more.prop(item.strip, "use_auto_blend", text="Automatic Blend")
                more.prop(item.strip, "blend_in")
                more.prop(item.strip, "blend_out")
                more.prop(item.strip, "extrapolation")
                more.label(text="Neutral correction: zero location/rotation, unit scale")


class ANIMASSIST_PT_nla_actions(_NlaPanel, Panel):
    bl_idname = "ANIMASSIST_PT_nla_actions"
    bl_label = "Actions & Tracks"

    def draw(self, context):
        body, item = editable_body(self.layout, context)
        native(body, "DUPLICATE", "Duplicate Independent")
        native(body, "LINKED", "Duplicate Linked")
        body.operator("animassist.nla_unique", text="Make Selected Clips Unique")
        tracks = self.layout.column(align=True)
        tracks.enabled = not context.scene.is_nla_tweakmode
        native(tracks, "UP", "Move Selected Tracks Up")
        native(tracks, "DOWN", "Move Selected Tracks Down")
        if item:
            body.prop(item.strip, "name", text="Clip")
            body.prop(item.track, "name", text="Track")
            body.prop(item.track, "mute", text="Mute Track")
            body.prop(item.track, "is_solo", text="Solo Track")
        col = self.layout.column(align=True)
        obj = context.object
        col.enabled = bool(obj and obj.is_editable and obj.animation_data and obj.animation_data.action
                           and not context.scene.is_nla_tweakmode)
        push = col.column()
        push.enabled = bool(obj and obj.animation_data and obj.animation_data.use_nla)
        native(push, "PUSHDOWN", "Push Down Active Action")
        if obj and obj.animation_data and not obj.animation_data.use_nla:
            wrapped_label(self.layout, context, "Enable NLA evaluation before pushing down")
        native(col, "STASH", "Stash Active Action")
        if not col.enabled:
            self.layout.label(text="Push/Stash needs an active owner Action")


class ANIMASSIST_PT_nla_bake(_NlaPanel, Panel):
    bl_idname = "ANIMASSIST_PT_nla_bake"
    bl_label = "Bake & Finish"

    def draw(self, context):
        body, item = editable_body(self.layout, context)
        body.label(text=f"Owner: {item.owner.name}" if item else "Select an owner clip")
        body.label(text=f"Scene range: {context.scene.frame_start} – {context.scene.frame_end}")
        body.operator("animassist.nla_bake", text="Bake to New Action")
        body.label(text="Originals kept · output unassigned")
        if item:
            output = latest_bake(item.owner)
            if output:
                wrapped_label(body, context, f"Output: {output.name}")
                body.label(text=f"Range: {list(output.get('animassist_nla_bake_range', []))}")
                body.operator("animassist.nla_activate_bake", text="Use Latest Bake (NLA Off)")
        body.operator("animassist.nla_empty_tracks", text="Remove Empty Tracks")
        more = options(body, "aa_nla_bake", "Bake Options")
        if more:
            more.label(text="Range and step: Adjust Last Operation")
            more.label(text="Evaluated object and pose transforms")
            more.label(text="Constraints and parents are preserved")


class ANIMASSIST_PT_nla_shelf(_NlaPanel, Panel):
    bl_idname = "ANIMASSIST_PT_nla_shelf"
    bl_label = "Quick Shelf"

    def draw(self, context):
        body, _item = editable_body(self.layout, context)
        body.operator("animassist.nla_unique", text="Make Selected Clips Unique")
        native(body, "EDIT", "Edit Active Source")
        body.operator("animassist.nla_bake", text="Bake Owner to New Action")


CLASSES = (ANIMASSIST_PT_nla_arrange, ANIMASSIST_PT_nla_blend, ANIMASSIST_PT_nla_actions,
           ANIMASSIST_PT_nla_bake, ANIMASSIST_PT_nla_shelf)
