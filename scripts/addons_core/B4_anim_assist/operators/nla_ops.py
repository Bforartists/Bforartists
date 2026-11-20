"""Native NLA workflows with explicit clip scope and preserved source data."""
import math

import bpy
from bpy.props import EnumProperty, FloatProperty, IntProperty, StringProperty
from bpy.types import Operator

from ..core.nla_context import (
    active_target, correction_reason, in_nla, is_correction, latest_bake, require_editable, strip_curves, targets,
)


def _run(operator, fn):
    try:
        fn()
    except (ValueError, RuntimeError) as exc:
        operator.report({"WARNING"}, str(exc))
        return {"CANCELLED"}
    return {"FINISHED"}


class _NlaOperator:
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if not in_nla(context):
            cls.poll_message_set("Use the NLA Editor")
            return False
        return True


def _active(context):
    item = active_target(context)
    require_editable(context, [item] if item else [], single=True)
    return item


def apply_positions(items, starts):
    """Validate the entire batch, then move without transient collisions.

    Rejected destinations and API failures leave every strip where it started.
    frame_start_raw translates the entire clip while retaining scale/repeat.
    """
    original = [(i.strip, float(i.strip.frame_start), float(i.strip.frame_end)) for i in items]
    desired = {i.strip.as_pointer(): (float(start), float(start + end - old))
               for i, start, (_s, old, end) in zip(items, starts, original)}
    for i in items:
        a, b = desired[i.strip.as_pointer()]
        if not math.isfinite(a) or not math.isfinite(b):
            raise ValueError("Clip positions must be finite")
        for other in i.track.strips:
            if other == i.strip:
                continue
            c, d = desired.get(other.as_pointer(), (other.frame_start, other.frame_end))
            if min(b, d) - max(a, c) > 1e-5:
                raise ValueError(f"Clips would overlap on {i.owner.name}: {i.track.name}")
    # Raw setters do not clamp against intermediate neighbors. A second pass
    # verifies the complete result and restores the source on any API failure.
    try:
        for i in items:
            start, end = desired[i.strip.as_pointer()]
            i.strip.frame_start_raw = start
            i.strip.frame_end_raw = end
        for i in items:
            a, b = desired[i.strip.as_pointer()]
            if abs(i.strip.frame_start - a) > 1e-4 or abs(i.strip.frame_end - b) > 1e-4:
                raise ValueError("The host could not place this batch without changing clip timing")
    except Exception:
        for strip, a, b in original:
            strip.frame_start_raw = a
            strip.frame_end_raw = b
        raise


class ANIMASSIST_OT_nla_time(_NlaOperator, Operator):
    bl_idname = "animassist.nla_time"
    bl_label = "Arrange Selected Clips"
    bl_description = "Move the selected Action clips in scene time; reject overlapping or locked targets together"

    operation: EnumProperty(name="Operation", description="How to arrange the selected clips", items=[
        ("NUDGE", "Nudge", "Move every selected clip by the frame step"),
        ("START", "Align Starts", "Align to the active selected clip's start"),
        ("END", "Align Ends", "Align to the active selected clip's end"),
        ("SEQUENCE", "Sequence Clips", "Place clips by scene start, then track order, from the active clip's start"),
    ])
    frames: FloatProperty(name="Frame Step", description="Scene frames to move the selected clips", default=1)
    gap: FloatProperty(name="Gap", description="Scene frames between sequenced clips", default=0, min=0)

    def execute(self, context):
        def perform():
            items = require_editable(context, targets(context))
            active = active_target(context)
            if self.operation != "NUDGE" and (not active or active.strip not in [i.strip for i in items]):
                raise ValueError("Make one selected clip active as the timing reference")
            if self.operation == "NUDGE":
                starts = [i.strip.frame_start + self.frames for i in items]
            elif self.operation == "START":
                starts = [active.strip.frame_start for i in items]
            elif self.operation == "END":
                starts = [active.strip.frame_end - (i.strip.frame_end - i.strip.frame_start) for i in items]
            else:
                items = sorted(items, key=lambda i: (i.strip.frame_start, i.track_index, i.owner.name, i.strip.name))
                cursor = active.strip.frame_start
                starts = []
                for i in items:
                    starts.append(cursor)
                    cursor += i.strip.frame_end - i.strip.frame_start + self.gap
            apply_positions(items, starts)
            context.area.tag_redraw()
            self.report({"INFO"}, f"Arranged {len(items)} selected clips")
        return _run(self, perform)


class ANIMASSIST_OT_nla_unique(_NlaOperator, Operator):
    bl_idname = "animassist.nla_unique"
    bl_label = "Make Selected Clips Unique"
    bl_description = "Give each selected clip an independent source Action, preserving its assigned slot and timing"

    def execute(self, context):
        def perform():
            items = require_editable(context, targets(context))
            originals = [(i.strip, i.strip.action, i.strip.action_slot) for i in items]
            copies = []
            try:
                for strip, action, slot in originals:
                    new = action.copy()
                    copies.append(new)
                    strip.action = new
                    if slot:
                        strip.action_slot = next(s for s in new.slots if s.identifier == slot.identifier)
            except Exception:
                for strip, action, slot in originals:
                    strip.action = action
                    if slot:
                        strip.action_slot = slot
                for action in copies:
                    bpy.data.actions.remove(action)
                raise
            self.report({"INFO"}, f"Made {len(items)} source Actions independent")
        return _run(self, perform)


class ANIMASSIST_OT_nla_native(_NlaOperator, Operator):
    bl_idname = "animassist.nla_native"
    bl_label = "NLA Clip Action"
    bl_description = "Run a native NLA action on the stated clip selection"

    command: EnumProperty(name="Action", description="Native NLA action", items=[
        ("MOVE", "Move Selected Clips", "Move selected clips interactively"),
        ("DUPLICATE", "Duplicate Independent", "Duplicate selected clips with independent Actions"),
        ("LINKED", "Duplicate Linked", "Duplicate clips sharing their source Actions"),
        ("UP", "Move Tracks Up", "Move selected tracks up in the evaluation stack"),
        ("DOWN", "Move Tracks Down", "Move selected tracks down in the evaluation stack"),
        ("EDIT", "Edit Action", "Enter native Tweak Mode for the active source clip"),
        ("FINISH", "Finish Editing", "Leave native Tweak Mode"),
        ("CORRECTION", "Edit Correction", "Edit a recognized Combine transform correction"),
        ("PUSHDOWN", "Push Down Action", "Push the owner's active Action into the NLA stack"),
        ("STASH", "Stash Action", "Stash the owner's active Action in a muted track"),
    ], default="EDIT")

    def execute(self, context):
        return self.invoke(context, None)

    def invoke(self, context, event):
        def perform():
            if self.command == "FINISH":
                if not context.scene.is_nla_tweakmode:
                    raise ValueError("No Action is being edited")
                if bpy.ops.nla.tweakmode_exit() != {"FINISHED"}:
                    raise ValueError("The host could not finish Tweak Mode")
                return
            if self.command in {"PUSHDOWN", "STASH"}:
                obj = context.object
                ad = obj.animation_data if obj else None
                if context.scene.is_nla_tweakmode or not obj or not obj.is_editable or not ad or not ad.action:
                    raise ValueError("Select an editable owner with an active Action outside Tweak Mode")
                if self.command == "PUSHDOWN" and not ad.use_nla:
                    raise ValueError("Enable NLA evaluation before pushing down the active Action")
                # The native operator targets the active NLA data expander,
                # which can belong to a different object than this stated owner.
                # Create native NLA data directly so owner scope is deterministic.
                action, slot = ad.action, ad.action_slot
                track = ad.nla_tracks.new()
                try:
                    strip = track.strips.new(action.name, int(math.floor(action.frame_range[0])), action)
                    if slot:
                        strip.action_slot = slot
                    strip.frame_start_raw = action.frame_range[0]
                    strip.frame_end_raw = max(action.frame_range[1], action.frame_range[0] + 1)
                    strip.blend_type = ad.action_blend_type
                    strip.extrapolation = ad.action_extrapolation
                    strip.influence = ad.action_influence
                    if ad.action_influence < 1:
                        strip.use_animated_influence = True
                        strip.keyframe_insert("influence", frame=strip.frame_start)
                    track.name = f"Stash: {action.name}" if self.command == "STASH" else action.name
                    track.mute = self.command == "STASH"
                    ad.action = None
                    self.report({"INFO"}, f"{obj.name}: Action moved to {track.name}; select its clip to edit")
                except Exception:
                    ad.nla_tracks.remove(track)
                    ad.action = action
                    if slot:
                        ad.action_slot = slot
                    raise
                return
            elif self.command in {"EDIT", "CORRECTION"}:
                item = _active(context)
                selected = targets(context)
                if len(selected) != 1 or selected[0].strip != item.strip:
                    raise ValueError("Select only the active Action clip before editing its source")
                if not item.strip.action.is_editable:
                    raise ValueError("Make the source Action local before editing")
                if self.command == "CORRECTION" and not is_correction(item.strip):
                    raise ValueError("Select an Anim Assist Combine correction; use Edit Action for ordinary clips")
                op = bpy.ops.nla.tweakmode_enter
            elif self.command in {"UP", "DOWN"}:
                # Native movement uses track selection, a separate scope.
                if context.scene.is_nla_tweakmode:
                    raise ValueError("Finish editing the Action before reordering tracks")
                if any(t.select and (t.lock or not obj.is_editable) for obj in context.scene.objects if obj.animation_data
                       for t in obj.animation_data.nla_tracks):
                    raise ValueError("Unlock selected tracks before moving them")
                if not any(t.select for obj in context.scene.objects if obj.animation_data for t in obj.animation_data.nla_tracks):
                    raise ValueError("Select tracks in the NLA channel list before reordering")
                if bpy.ops.anim.channels_move(direction=self.command) != {"FINISHED"}:
                    raise ValueError("The host could not reorder selected tracks")
                return
            else:
                require_editable(context, targets(context))
                if self.command == "MOVE":
                    result = bpy.ops.transform.translate("INVOKE_DEFAULT")
                    if "CANCELLED" in result:
                        raise ValueError("The host could not start moving clips")
                    return
                else:
                    result = bpy.ops.nla.duplicate(linked=self.command == "LINKED")
                    if result != {"FINISHED"}:
                        raise ValueError("The host could not duplicate the clips")
                    return
            if op() != {"FINISHED"}:
                raise ValueError("The native NLA action was unavailable for this target")
        return _run(self, perform)


class ANIMASSIST_OT_nla_open_editor(_NlaOperator, Operator):
    bl_idname = "animassist.nla_open_editor"
    bl_label = "Open Source Editor"
    bl_description = "Open the current source in an unpinned animation editor; retain this area's NLA space when switching it"
    editor: EnumProperty(name="Editor", description="Editor for inspecting source keys", items=[
        ("DOPESHEET_EDITOR", "Dope Sheet", "Inspect source key timing"),
        ("GRAPH_EDITOR", "Graph Editor", "Inspect source curves"),
    ])

    def execute(self, context):
        def perform():
            item = active_target(context)
            if not item:
                raise ValueError("Make an Action clip active first")
            if not context.scene.is_nla_tweakmode:
                result = bpy.ops.animassist.nla_native(command="EDIT")
                if result != {"FINISHED"}:
                    raise ValueError("Select only the active clip to edit its source")
            # Reuse only an unpinned editor already showing this same owner.
            # Never change another editor's pinned Action or its filters.
            for area in context.screen.areas:
                if area.type != self.editor:
                    continue
                space = area.spaces.active
                if getattr(space, "pin", False):
                    continue
                suitable = (self.editor == "GRAPH_EDITOR" and getattr(space, "mode", "") == "FCURVES"
                            and getattr(space.dopesheet, "show_only_selected", False)
                            and context.object == item.owner)
                suitable |= (self.editor == "DOPESHEET_EDITOR" and getattr(space, "mode", "") == "ACTION"
                             and getattr(space, "action", None) == item.strip.action)
                if suitable:
                    area.tag_redraw()
                    self.report({"INFO"}, "Source is open in the existing animation editor")
                    return
            context.area.type = self.editor
            if self.editor == "DOPESHEET_EDITOR":
                context.area.spaces.active.mode = "ACTION"
                context.area.spaces.active.pin = False
            else:
                context.area.spaces.active.mode = "FCURVES"
                context.area.spaces.active.dopesheet.show_only_selected = True
            self.report({"INFO"}, "Source editing: use the editor selector to return to NLA, then Finish Editing")
        return _run(self, perform)


def _pose_snapshot(context, obj):
    context.view_layer.update()
    evaluated = obj.evaluated_get(context.evaluated_depsgraph_get())
    return [evaluated.matrix_world.copy(), *([b.matrix.copy() for b in evaluated.pose.bones] if evaluated.pose else [])]


class ANIMASSIST_OT_nla_correction(_NlaOperator, Operator):
    bl_idname = "animassist.nla_correction"
    bl_label = "New Transform Correction"
    bl_description = "Create an independent neutral Combine correction above the source motion; supports unconstrained transform channels"

    def execute(self, context):
        def perform():
            items = require_editable(context, targets(context), single=True)
            item = items[0]
            reason = correction_reason(item)
            if reason:
                raise ValueError(reason)
            from bpy_extras.anim_utils import action_ensure_channelbag_for_slot
            before = _pose_snapshot(context, item.owner)
            action = bpy.data.actions.new(f"{item.owner.name} Correction")
            track = None
            try:
                slot = action.slots.new(id_type="OBJECT", name=item.owner.name)
                bag = action_ensure_channelbag_for_slot(action, slot)
                # Populate only the source slot's transform targets, with complete
                # vectors so quaternion identities never have a missing W channel.
                paths = {fc.data_path for fc in strip_curves(item.strip)}
                start, end = float(item.strip.frame_start), float(item.strip.frame_end)
                for path in sorted(paths):
                    prop = path.rsplit(".", 1)[-1]
                    values = ((1, 0, 0, 0) if prop == "rotation_quaternion" else
                              (0, 0, 1, 0) if prop == "rotation_axis_angle" else
                              (1, 1, 1) if prop == "scale" else (0, 0, 0))
                    for index, value in enumerate(values):
                        fc = bag.fcurves.new(path, index=index)
                        for frame in (start, end):
                            key = fc.keyframe_points.insert(frame, value)
                            key.interpolation = "LINEAR"
                action["animassist_nla_correction"] = 1
                track = item.owner.animation_data.nla_tracks.new()
                track.name = "Anim Assist Correction"
                strip = track.strips.new(action.name, int(math.floor(start)), action)
                strip.action_slot = slot
                strip.frame_start_raw = start
                strip.frame_end_raw = end
                strip.blend_type = "COMBINE"
                strip.extrapolation = "NOTHING"
                after = _pose_snapshot(context, item.owner)
                if any(abs(x - y) > 1e-5 for a, b in zip(before, after) for ra, rb in zip(a, b) for x, y in zip(ra, rb)):
                    raise ValueError("This rig's evaluated pose changed; neutral correction was rolled back")
                # Source selection remains intact. Select the new correction using
                # the native editor before Edit Correction (no hidden mode entry).
                self.report({"INFO"}, f"Created {action.name}; select its clip to edit the correction")
            except Exception:
                if track is not None:
                    item.owner.animation_data.nla_tracks.remove(track)
                bpy.data.actions.remove(action)
                context.view_layer.update()
                raise
        return _run(self, perform)


class ANIMASSIST_OT_nla_bake(_NlaOperator, Operator):
    bl_idname = "animassist.nla_bake"
    bl_label = "Bake to New Action"
    bl_description = "Bake the active clip owner's evaluated transform stack to a retained, unassigned Action; preserve source Actions and tracks"
    start: IntProperty(name="Scene Start", description="First scene frame to sample", default=1)
    end: IntProperty(name="Scene End", description="Last scene frame to sample", default=250)
    step: IntProperty(name="Step", description="Scene frame sampling interval", default=1, min=1)

    def invoke(self, context, event):
        self.start, self.end = context.scene.frame_start, context.scene.frame_end
        return self.execute(context)

    def execute(self, context):
        def perform():
            item = _active(context)
            obj, ad = item.owner, item.owner.animation_data
            if self.end < self.start:
                raise ValueError("Scene end must not precede scene start")
            if (self.end - self.start) // self.step > 100000:
                raise ValueError("Choose a shorter range or larger sampling step")
            from bpy_extras.anim_utils import BakeOptions, bake_action_objects
            old = (ad.action, ad.action_slot, ad.action_blend_type, ad.action_influence,
                   ad.action_extrapolation, ad.use_nla, context.scene.frame_current,
                   context.scene.frame_subframe)
            transforms = [(o, o.matrix_basis.copy()) for o in [obj, *list(obj.pose.bones if obj.pose else [])]]
            existing = {a.as_pointer() for a in bpy.data.actions}
            output = None
            try:
                options = BakeOptions(only_selected=False, do_pose=bool(obj.pose), do_object=True,
                    do_visual_keying=True, do_constraint_clear=False, do_parents_clear=False,
                    do_clean=False, do_location=True, do_rotation=True, do_scale=True,
                    do_bbone=False, do_custom_props=False)
                frames = list(range(self.start, self.end + 1, self.step))
                if frames[-1] != self.end:
                    frames.append(self.end)
                output, = bake_action_objects([(obj, None)], frames=frames, bake_options=options)
                output.name = f"{obj.name} NLA Bake"
                output.use_fake_user = True
                output["animassist_nla_bake_owner"] = obj.name
                output["animassist_nla_bake_target"] = obj
                output["animassist_nla_bake_range"] = [self.start, self.end, self.step]
                output["animassist_nla_bake_order"] = 1 + max(
                    (int(a.get("animassist_nla_bake_order", 0)) for a in bpy.data.actions), default=0)
            finally:
                ad.action = old[0]
                if old[0] and old[1]:
                    ad.action_slot = old[1]
                ad.action_blend_type, ad.action_influence = old[2:4]
                ad.action_extrapolation, ad.use_nla = old[4:6]
                for target, matrix in transforms:
                    target.matrix_basis = matrix
                context.scene.frame_set(old[6], subframe=old[7])
                context.view_layer.update()
                if output is None:
                    for action in list(bpy.data.actions):
                        if action.as_pointer() not in existing:
                            bpy.data.actions.remove(action)
            self.report({"INFO"}, f"Saved {output.name}, scene {self.start}–{self.end}; source stack unchanged")
        return _run(self, perform)


class ANIMASSIST_OT_nla_activate_bake(_NlaOperator, Operator):
    bl_idname = "animassist.nla_activate_bake"
    bl_label = "Use Latest Bake"
    bl_description = "Assign the owner's latest Anim Assist bake and turn off NLA evaluation to avoid evaluating source plus bake"

    def execute(self, context):
        def perform():
            item = _active(context)
            output = latest_bake(item.owner)
            if not output:
                raise ValueError("Bake this owner to a new Action first")
            constraints = list(item.owner.constraints)
            if item.owner.pose:
                constraints.extend(c for bone in item.owner.pose.bones for c in bone.constraints)
            if any(not c.mute and c.influence != 0 for c in constraints):
                raise ValueError("The bake contains evaluated constraints; remove or mute constraints before assigning it")
            ad = item.owner.animation_data
            if ad.action:
                raise ValueError("Stash the current active Action before assigning a bake")
            slots = [s for s in output.slots if s.target_id_type == "OBJECT"]
            if len(slots) != 1:
                raise ValueError("The retained bake no longer has one valid object slot; bake this owner again")
            previous = (ad.action, ad.action_slot, ad.use_nla)
            try:
                ad.action = output
                ad.action_slot = slots[0]
                ad.use_nla = False
            except Exception:
                ad.action = previous[0]
                if previous[0] and previous[1]:
                    ad.action_slot = previous[1]
                ad.use_nla = previous[2]
                raise
            self.report({"INFO"}, "Bake assigned; NLA evaluation is off. Enable NLA in the native Animation Data settings to return")
        return _run(self, perform)


class ANIMASSIST_OT_nla_empty_tracks(_NlaOperator, Operator):
    bl_idname = "animassist.nla_empty_tracks"
    bl_label = "Remove Empty Tracks"
    bl_description = "Remove only empty unlocked tracks from the active clip's editable owner"

    def execute(self, context):
        def perform():
            item = _active(context)
            tracks = item.owner.animation_data.nla_tracks
            for track in list(tracks):
                if not track.strips and not track.lock:
                    tracks.remove(track)
        return _run(self, perform)


class ANIMASSIST_OT_nla_influence(_NlaOperator, Operator):
    bl_idname = "animassist.nla_influence"
    bl_label = "Key Clip Influence"
    bl_description = "Key the active clip's influence at the current scene frame using native NLA control curves"
    value: FloatProperty(name="Influence", description="Clip weight to key at the current scene frame", default=1, min=0, max=1)

    def execute(self, context):
        def perform():
            item = _active(context)
            strip = item.strip
            strip.use_animated_influence = True
            strip.influence = self.value
            strip.keyframe_insert("influence", frame=context.scene.frame_current)
            context.scene.frame_set(context.scene.frame_current, subframe=context.scene.frame_subframe)
        return _run(self, perform)


class ANIMASSIST_OT_nla_add_clip(_NlaOperator, Operator):
    bl_idname = "animassist.nla_add_clip"
    bl_label = "Add Existing Action Clip"
    bl_description = "Add an existing object Action to a new track on the active owner at the playhead"
    action_name: StringProperty(name="Action", description="Existing Action to reference in the new clip")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop_search(self, "action_name", bpy.data, "actions", text="Source Action")

    def execute(self, context):
        def perform():
            obj = context.object
            if not obj or not obj.is_editable or context.scene.is_nla_tweakmode:
                raise ValueError("Select an editable object outside Tweak Mode")
            action = bpy.data.actions.get(self.action_name)
            if not action:
                raise ValueError("Choose an existing Action")
            slot = next((s for s in action.slots if s.target_id_type == "OBJECT"), None)
            if not slot or sum(s.target_id_type == "OBJECT" for s in action.slots) != 1:
                raise ValueError("Choose an Action with exactly one object slot; assign multi-slot Actions using native NLA tools")
            ad = obj.animation_data_create()
            track = ad.nla_tracks.new()
            try:
                strip = track.strips.new(action.name, context.scene.frame_current, action)
                strip.action_slot = slot
            except Exception:
                ad.nla_tracks.remove(track)
                raise
        return _run(self, perform)


CLASSES = (
    ANIMASSIST_OT_nla_time, ANIMASSIST_OT_nla_unique, ANIMASSIST_OT_nla_native,
    ANIMASSIST_OT_nla_open_editor, ANIMASSIST_OT_nla_correction, ANIMASSIST_OT_nla_bake,
    ANIMASSIST_OT_nla_activate_bake, ANIMASSIST_OT_nla_empty_tracks,
    ANIMASSIST_OT_nla_influence, ANIMASSIST_OT_nla_add_clip,
)
