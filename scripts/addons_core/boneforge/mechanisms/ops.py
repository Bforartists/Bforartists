# bonecraft/boneforge/mechanisms/ops.py
"""Mechanisms operators. Each is one undo step; build and plan errors are reported, not raised."""
import bmesh
import bpy
from bpy.props import BoolProperty, EnumProperty, IntProperty, StringProperty
from mathutils import Vector

from boneforge.mechanisms import build, model, parts, planner, records
from boneforge.mechanisms.recipes import sequence as seq_recipe

AXES = {"X": (1.0, 0.0, 0.0), "Y": (0.0, 1.0, 0.0), "Z": (0.0, 0.0, 1.0)}
_AXIS_ITEMS = [("X", "X", "The part's X axis"), ("Y", "Y", "The part's Y axis"), ("Z", "Z", "The part's Z axis"),
               ("SELECTION", "Align to Selection", "The active edge or face selected in Edit Mode")]


def _items(values, labels=None):
    return [(v, (labels or {}).get(v, v.replace("_", " ").title()), "") for v in values]


def part_axis(arm, part_pg, mode):
    if mode == "SELECTION":
        return selection_axis(arm)
    v = Vector(AXES[mode])
    if part_pg.kind == "OBJECT":
        ob = records.part_object(part_pg)
        if ob is None:
            raise build.BuildError(f"Part '{part_pg.name}' has no mesh: Reassign it first.")
        v = parts.rest_world(ob).to_3x3() @ v             # the object's own axes, at rest
    v = (arm.matrix_world.inverted().to_3x3() @ v).normalized()
    return tuple(round(c, 6) + 0.0 for c in v)              # drop float noise (and -0.0)


def selection_axis(arm):
    """The active edge's direction or the selected face's normal, in armature space."""
    ob = bpy.context.edit_object
    if ob is None or ob.type != 'MESH':
        raise build.BuildError("Align to Selection needs an edge or a face selected in Edit Mode.")
    bm = bmesh.from_edit_mesh(ob.data)
    act = bm.select_history.active
    faces = [f for f in bm.faces if f.select]
    edges = [e for e in bm.edges if e.select]
    if isinstance(act, bmesh.types.BMFace) or (act is None and len(faces) == 1):
        n = (act if isinstance(act, bmesh.types.BMFace) else faces[0]).normal.copy()
        world = ob.matrix_world.inverted().transposed().to_3x3() @ n      # a normal takes the inverse transpose
    elif isinstance(act, bmesh.types.BMEdge) or (act is None and len(edges) == 1):
        e = act if isinstance(act, bmesh.types.BMEdge) else edges[0]
        world = ob.matrix_world.to_3x3() @ (e.verts[1].co - e.verts[0].co)
    else:
        raise build.BuildError("Align to Selection needs exactly one edge or one face selected.")
    v = arm.matrix_world.inverted().to_3x3() @ world
    if v.length < 1e-9:
        raise build.BuildError("The selected edge has no length.")
    return tuple(round(c, 6) + 0.0 for c in v.normalized())


class _MechOp:
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if records.active_rig(context) is None:
            cls.poll_message_set("Select a mechanism rig or one of its parts.")
            return False
        return True

    def execute(self, context):
        try:
            msg = self.run(context, records.active_rig(context))
        except (build.BuildError, planner.PlanError) as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
        if msg:
            self.report({'INFO'}, msg)
        return {'FINISHED'}


def _new_record(arm, m, extra_undo=None):
    """Add record ``m`` and build it; on failure remove it again and undo ``extra_undo``."""
    records.add(arm.data, m)
    try:
        build.rebuild(arm, {m.id})
    except Exception:
        records.remove(arm.data, m.id)
        if extra_undo:
            extra_undo()
        raise
    rec = arm.data.bonecraft_mech
    with records.quiet():
        rec.active_mech = next((i for i, x in enumerate(rec.mechanisms) if x.id == m.id), rec.active_mech)


class BC_OT_mech_add_parts(bpy.types.Operator):
    bl_idname = "boneforge.mech_add_parts"
    bl_label = "Add Parts from Selection"
    bl_description = "Selected objects become one part each; one mesh with loose pieces becomes one part per piece"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not any(o.type == 'MESH' for o in context.selected_objects):
            cls.poll_message_set("Select the mesh parts first.")
            return False
        if context.mode != 'OBJECT':
            cls.poll_message_set("Switch to Object Mode.")
            return False
        return True

    def execute(self, context):
        try:
            arm, pids, warn = parts.add_parts_from_selection(context)
        except (build.BuildError, planner.PlanError) as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
        _show_section(context, "bonecraft_mech_show_parts")
        if warn:
            self.report({'WARNING'}, "Apply Transforms on " + ", ".join(warn) + ": unapplied rotation or scale tilts the axes.")
        else:
            self.report({'INFO'}, f"Added {len(pids)} part(s).")
        return {'FINISHED'}


class BC_OT_mech_add_joint(_MechOp, bpy.types.Operator):
    bl_idname = "boneforge.mech_add_joint"
    bl_label = "Add Joint"
    bl_description = "Make a part move: a Hinge turns it, a Slide moves it, a Telescope extends segments"
    type: EnumProperty(description='Kind of joint', items=_items(model.JOINT_TYPES))
    parts: StringProperty(description="Part ids: the part, or the base then each segment")
    axis: EnumProperty(description='Axis the joint turns or slides along', items=_AXIS_ITEMS, default="X")

    def run(self, context, arm):
        rec = arm.data.bonecraft_mech
        pids = [x for x in self.parts.split(",") if x]
        pgs = [records.find(arm.data, p) for p in pids]
        if not pids or any(p is None for p in pgs):
            raise build.BuildError("Pick the parts first.")
        lead = pgs[-1] if self.type == "TELESCOPE" else pgs[0]
        m = model.Mechanism(model.new_id(records.taken_ids(arm.data)), self.type, "", parts=pids,
                            axis=part_axis(arm, lead, self.axis))
        m.name = model.unique_name(model.default_name(pgs[0].name, self.type), {x.name for x in rec.mechanisms})
        if self.type == "SLIDE":
            m.min, m.max = 0.0, round(pgs[0].size, 4)
        undo = None
        if self.type == "TELESCOPE":
            m.length = round(sum(p.size for p in pgs[1:]), 4)
            old = [(p, p.parent) for p in pgs[1:]]
            with records.quiet():
                for prev, seg in zip(pgs, pgs[1:]):
                    seg.parent = prev.id

            def undo():
                with records.quiet():
                    for p, parent in old:
                        p.parent = parent
        _new_record(arm, m, undo)
        _show_section(context, "bonecraft_mech_show_links")
        return f"Added {m.name}."


class BC_OT_mech_add_link(_MechOp, bpy.types.Operator):
    bl_idname = "boneforge.mech_add_link"
    bl_label = "Add Link"
    bl_description = "Make one part move another: Piston, Gear Link or Follow"
    type: EnumProperty(description='Kind of link', items=_items(model.LINK_TYPES, {"GEAR": "Gear Link"}))
    source: StringProperty(description="Gear Link, Follow: the part whose joint drives")
    target: StringProperty(description="Gear Link, Follow: the part whose joint is driven")
    parts: StringProperty(description="Piston: the cylinder part id, then the rod part id")
    gear_kind: EnumProperty(description='Gear, belt or rack: how the motion passes from one part to the other', items=_items(model.GEAR_KINDS))
    curve: BoolProperty(description="Follow: a curve you can reshape in the Graph Editor")

    def run(self, context, arm):
        rec = arm.data.bonecraft_mech
        rig = records.to_model(arm)
        rid = model.new_id(records.taken_ids(arm.data))
        taken = {x.name for x in rec.mechanisms}
        if self.type == "PISTON":
            pids = [x for x in self.parts.split(",") if x]
            if len(pids) != 2 or None in (rig.part(p) for p in pids):
                raise build.BuildError("Pick the cylinder part, then the rod part.")
            m = model.Mechanism(rid, "PISTON", model.unique_name(model.default_name(rig.part(pids[0]).name, "PISTON"), taken),
                                parts=pids)
        else:
            src, tgt = planner.joint_for_part(rig, self.source), planner.joint_for_part(rig, self.target)
            if src is None or tgt is None:
                raise build.BuildError("Both parts need a joint first (Add Joint).")
            m = model.Mechanism(rid, self.type, model.unique_name(model.default_name(rig.part(self.target).name, self.type), taken),
                                source=src.id, target=tgt.id, gear_kind=self.gear_kind, curve=self.curve)
            if self.type == "FOLLOW":
                m.source_range, m.target_range = _range(src), _range(tgt)
        _new_record(arm, m)
        _show_section(context, "bonecraft_mech_show_links")
        return f"Added {m.name}."


def _range(joint):
    """A joint's full range as a Follow default; a Hinge source must stay within ±180°."""
    if joint.type == "HINGE":
        return max(joint.min, -180.0), min(joint.max, 180.0)
    return joint.min, joint.max


class _TargetOp(_MechOp):
    target: StringProperty(description="Record id")


class BC_OT_mech_set_limit(_TargetOp, bpy.types.Operator):
    bl_idname = "boneforge.mech_set_limit"
    bl_label = "Set Limit"
    bl_description = "Use the handle's current pose as this joint's Min or Max"
    which: EnumProperty(options={'HIDDEN', 'SKIP_SAVE'}, items=[("MIN", "Set Min", ""), ("MAX", "Set Max", "")])

    def run(self, context, arm):
        rig = records.to_model(arm)
        m = rig.mech(self.target)
        if m is None or m.type not in model.JOINT_TYPES:
            raise build.BuildError("Pick a joint first.")
        value = round(build.get_value(arm, rig, m.id), 4)
        field = "length" if m.type == "TELESCOPE" else ("min" if self.which == "MIN" else "max")
        setattr(records.find(arm.data, m.id), field, value)            # edit hook rebuilds in place
        if arm.data.bonecraft_mech.last_error:
            raise build.BuildError(arm.data.bonecraft_mech.last_error)
        return f"{field.title()} set to {value:g}."


def _show_section(context, flag):
    """X4: adding into a folded section opens it, so the new row is never hidden."""
    wm = getattr(context, "window_manager", None)
    if wm is not None and hasattr(wm, flag):
        setattr(wm, flag, True)


def _plural(n, one, many=None):
    return f"{n} {one if n == 1 else (many or one + 's')}"


def delete_impact(arm, rid):
    """One sentence naming what depends on the record, or empty when nothing does (X8)."""
    rig = records.to_model(arm)
    if rig.part(rid) is not None:
        bits = ([_plural(n, "mechanism")] if (n := sum(1 for m in rig.mechanisms if rid in m.parts)) else [])
        bits += [_plural(n, "riding part")] if (n := sum(1 for p in rig.parts if p.parent == rid)) else []
        return f"Used by {' and '.join(bits)}." if bits else ""
    if rig.mech(rid) is not None:
        bits = ([_plural(n, "link")] if (n := sum(1 for x in rig.mechanisms if rid in (x.source, x.target))) else [])
        bits += [_plural(n, "sequence step")] if (n := sum(1 for s in rig.sequences for st in s.steps if st.target == rid)) else []
        return f"Used by {' and '.join(bits)}." if bits else ""
    s = rig.seq(rid)
    return f"Has {_plural(len(s.steps), 'step')}." if s is not None and s.steps else ""


def delete_refusal(arm, rid):
    """Non-empty when build.delete would refuse: a used part or mechanism is stopped before any dialog."""
    rig = records.to_model(arm)
    if rig.seq(rid) is not None:                           # a Sequence's own steps go with it
        return ""
    impact = delete_impact(arm, rid)
    return f"Can't delete: {impact[0].lower()}{impact[1:]} Delete or change those first." if impact else ""


def _simple(cls_name, idname, label, desc, fn):
    """An operator that runs ``fn(arm, record id)``."""
    def run(self, context, arm):
        return fn(arm, self.target)
    return type(cls_name, (_TargetOp, bpy.types.Operator),
                {"bl_idname": idname, "bl_label": label, "bl_description": desc, "run": run})


def _rebuild(arm, rid):
    build.rebuild(arm, {rid})


def _restore(arm, rid):
    build.restore(arm, rid)
    return "Restored from the record."


def _keep(arm, rid):
    build.keep_mine(arm, rid)
    return "Your values were copied into the record."


def _detach(arm, rid):
    build.detach(arm, rid)
    return "Detached: the bones and constraints are now your own."


def _delete(arm, rid):
    if records.find(arm.data, rid) in list(arm.data.bonecraft_mech.parts):
        parts.remove_part(arm, rid)
    else:
        build.delete(arm, rid)
    return "Deleted."


def _apply_transforms(arm, pid):
    pg = records.find(arm.data, pid)
    ob = records.part_object(pg) if pg is not None else None
    if ob is None:
        raise build.BuildError("That part's object is missing.")
    parts.apply_transforms(ob)
    build.rebuild(arm, {pid})
    return f"Applied rotation and scale on {ob.name}."


def _edit_pivot(arm, pid):
    parts.start_pivot(bpy.context, arm, pid)
    return "Drag the pivot marker, then click Apply Pivot."


def _reassign(arm, pid):
    ob = bpy.context.active_object
    if ob is None or ob.type != 'MESH':
        raise build.BuildError("Select the mesh that should become this part.")
    parts.reassign(arm, pid, ob)
    return f"Part now uses {ob.name}."


BC_OT_mech_rebuild = _simple("BC_OT_mech_rebuild", "boneforge.mech_rebuild", "Rebuild", "Build this record again from its settings", _rebuild)
BC_OT_mech_restore = _simple("BC_OT_mech_restore", "boneforge.mech_restore", "Restore", "Throw away hand edits and rebuild from the record", _restore)
BC_OT_mech_keep_mine = _simple("BC_OT_mech_keep_mine", "boneforge.mech_keep_mine", "Keep mine", "Copy your hand edits into the record", _keep)
BC_OT_mech_detach = _simple("BC_OT_mech_detach", "boneforge.mech_detach", "Detach", "Keep the bones and constraints as your own and forget the record", _detach)
BC_OT_mech_apply_transforms = _simple("BC_OT_mech_apply_transforms", "boneforge.mech_apply_transforms", "Apply Transforms", "Apply the part's rotation and scale so its axes are straight", _apply_transforms)
BC_OT_mech_edit_pivot = _simple("BC_OT_mech_edit_pivot", "boneforge.mech_edit_pivot", "Edit Pivot", "Place a marker to move this part's pivot", _edit_pivot)
BC_OT_mech_reassign = _simple("BC_OT_mech_reassign", "boneforge.mech_reassign", "Reassign", "Use the selected mesh for this part", _reassign)


class BC_OT_mech_delete(_TargetOp, bpy.types.Operator):
    bl_idname = "boneforge.mech_delete"
    bl_label = "Delete"
    bl_description = "Remove this record and everything BoneCraft built for it"

    def invoke(self, context, event):
        """A click asks first, naming what depends on the record (X8); scripts call execute as before."""
        arm = records.active_rig(context)
        if arm is not None:
            refusal = delete_refusal(arm, self.target)
            if refusal:                                    # the delete would be refused: say so instead of asking
                self.report({'ERROR'}, refusal)
                return {'CANCELLED'}
        pg = records.find(arm.data, self.target) if arm is not None else None
        impact = delete_impact(arm, self.target) if arm is not None else ""
        name = pg.name if pg is not None else "this record"
        message = f"Delete {name}? " + (impact + " " if impact else "") + "Ctrl+Z undoes this."
        try:
            return context.window_manager.invoke_confirm(self, event, title="Delete", message=message,
                                                         confirm_text="Delete", icon='WARNING')
        except TypeError:                                  # an older host without the message arguments
            return context.window_manager.invoke_confirm(self, event)

    def run(self, context, arm):
        return _delete(arm, self.target)


class BC_OT_mech_cancel_pivot(_MechOp, bpy.types.Operator):
    bl_idname = "boneforge.mech_cancel_pivot"
    bl_label = "Cancel Pivot"
    bl_description = "Remove the pivot marker without moving the pivot"

    def run(self, context, arm):
        markers = parts.pivot_markers(arm)
        if not markers:
            raise build.BuildError("No pivot is being edited.")
        for ob in markers:
            bpy.data.objects.remove(ob)
        context.view_layer.objects.active = arm
        return "Pivot cancelled."


class BC_OT_mech_cancel_capture(_TargetOp, bpy.types.Operator):
    bl_idname = "boneforge.mech_cancel_capture"
    bl_label = "Cancel Capture"
    bl_description = "Put the Sequence slider back to the start without recording a step"

    def run(self, context, arm):
        rig = records.to_model(arm)
        if rig.seq(self.target) is None:
            raise build.BuildError("Pick a Sequence first.")
        build.set_value(arm, rig, self.target, 0.0)
        return "Capture cancelled: the slider is back at the start."


class BC_OT_mech_apply_pivot(bpy.types.Operator):
    bl_idname = "boneforge.mech_apply_pivot"
    bl_label = "Apply Pivot"
    bl_description = "Move the part's bones to the pivot marker"
    bl_options = {'REGISTER', 'UNDO'}

    marker: StringProperty(description="The marker object's name; empty uses the active object or the rig's one marker")

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        if ob is not None and ob.get(parts.PIVOT_PROP) is not None:
            return True
        rig = records.active_rig(context)
        if rig is None or not parts.pivot_markers(rig):
            cls.poll_message_set("Select a pivot marker first (Edit Pivot).")
            return False
        return True

    def execute(self, context):
        ob = bpy.data.objects.get(self.marker) if self.marker else context.active_object
        if ob is None or ob.get(parts.PIVOT_PROP) is None:
            rig = records.active_rig(context)
            markers = parts.pivot_markers(rig) if rig is not None else []
            ob = markers[0] if markers else None
        if ob is None:
            self.report({'ERROR'}, "No pivot is being edited.")
            return {'CANCELLED'}
        try:
            parts.apply_pivot(context, ob)
        except (build.BuildError, planner.PlanError) as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
        return {'FINISHED'}


class BC_OT_mech_merge_vrchat(_MechOp, bpy.types.Operator):
    bl_idname = "boneforge.mech_merge_vrchat"
    bl_label = "Merge for VRChat"
    bl_description = "Join the object parts into one skinned mesh, one vertex group per part"

    def run(self, context, arm):
        return f"Merged into {parts.merge_for_vrchat(context, arm).name}."


class BC_OT_mech_add_sequence(_MechOp, bpy.types.Operator):
    bl_idname = "boneforge.mech_add_sequence"
    bl_label = "Add Sequence"
    bl_description = "A transformation played by one slider; capture its steps by posing handles"
    name: StringProperty(description='Name of the new sequence', default="Transform")

    def run(self, context, arm):
        rec = arm.data.bonecraft_mech
        s = model.Sequence(model.new_id(records.taken_ids(arm.data)),
                           model.unique_name(model.clean_name(self.name), {x.name for x in rec.sequences}))
        records.add(arm.data, s)
        try:
            build.rebuild(arm, {s.id})
        except Exception:
            records.remove(arm.data, s.id)
            raise
        with records.quiet():
            rec.active_seq = len(rec.sequences) - 1
        _show_section(context, "bonecraft_mech_show_seqs")
        return f"Added {s.name}. Click Capture Step to begin."


class BC_OT_mech_capture_step(_TargetOp, bpy.types.Operator):
    bl_idname = "boneforge.mech_capture_step"
    bl_label = "Capture Step"
    bl_description = "Turn the posed handles into the next step of this Sequence"

    def run(self, context, arm):
        rig = records.to_model(arm)
        s = rig.seq(self.target)
        if s is None:
            raise build.BuildError("Pick a Sequence first.")
        if abs(build.get_value(arm, rig, s.id) - 1.0) > 1e-4:
            build.set_value(arm, rig, s.id, 1.0)
            return "Slider moved to the end. Pose the handles for the next step, then click Capture Step again."
        moved = [(m, build.get_value(arm, rig, m.id)) for m in rig.mechanisms if m.type in model.JOINT_TYPES]
        moved = [(m, v) for m, v in moved if abs(v) > 1e-4]
        if not moved:
            return "Nothing moved: pose at least one handle away from rest."
        start, end = model.step_window([(st.start, st.end) for st in s.steps])
        seq_pg = records.find(arm.data, s.id)
        count = len(seq_pg.steps)
        try:
            for m, v in moved:
                records.add_step(seq_pg, model.Step(m.id, round(seq_recipe.value(rig, s, m.id, 1.0) + v, 4), start, end))
                build.set_value(arm, rig, m.id, 0.0)
            build.rebuild(arm, {s.id})
        except Exception:
            with records.quiet():                       # a CANCELLED operator is not undone: put everything back
                while len(seq_pg.steps) > count:
                    seq_pg.steps.remove(len(seq_pg.steps) - 1)
            for m, v in moved:
                try:
                    build.set_value(arm, rig, m.id, v)
                except Exception:                       # noqa: BLE001 - keep restoring the rest
                    pass
            raise
        return f"Captured {len(moved)} joint(s) as a step."


class BC_OT_mech_remove_step(_TargetOp, bpy.types.Operator):
    bl_idname = "boneforge.mech_remove_step"
    bl_label = "Remove Step"
    bl_description = "Remove this step from the Sequence"
    index: IntProperty(options={'HIDDEN', 'SKIP_SAVE'})

    def run(self, context, arm):
        seq_pg = records.find(arm.data, self.target)
        if seq_pg is None or not (0 <= self.index < len(seq_pg.steps)):
            raise build.BuildError("Pick a step first.")
        old = seq_pg.steps[self.index]
        saved = model.Step(old.target, old.value, old.start, old.end, old.ease)
        with records.quiet():
            seq_pg.steps.remove(self.index)
        try:
            build.rebuild(arm, {self.target})
        except Exception:
            restored = records.add_step(seq_pg, saved)       # appended; move it back to where it was
            with records.quiet():
                seq_pg.steps.move(len(seq_pg.steps) - 1, self.index)
            raise


class BC_OT_mech_save_form(_MechOp, bpy.types.Operator):
    bl_idname = "boneforge.mech_save_form"
    bl_label = "Save Form"
    bl_description = "Remember every handle and Sequence slider value under a name"
    name: StringProperty(description='Name of the saved form', default="Form")

    def run(self, context, arm):
        rig = records.to_model(arm)
        rec = arm.data.bonecraft_mech
        form = next((f for f in rec.forms if f.name == self.name), None) or rec.forms.add()
        form.name = self.name
        form.control_values.clear()
        if "values" in form:
            del form["values"]
        for cid, _ in model.controls(rig):
            v = form.control_values.add()
            v.key, v.value = cid, build.get_value(arm, rig, cid)
        return f"Saved form {self.name}."


class BC_OT_mech_go_to_form(_MechOp, bpy.types.Operator):
    bl_idname = "boneforge.mech_go_to_form"
    bl_label = "Go to Form"
    bl_description = "Set every handle and Sequence slider to a saved form"
    name: StringProperty(options={'HIDDEN', 'SKIP_SAVE'})
    insert_keys: BoolProperty(name="Insert Keys", description="Also key the values on the current frame")

    def run(self, context, arm):
        rig = records.to_model(arm)
        form = next((f for f in arm.data.bonecraft_mech.forms if f.name == self.name), None)
        if form is None:
            raise build.BuildError("That form no longer exists.")
        ids = rig.ids()
        for cid, value in records.form_values(form).items():
            if cid in ids:
                build.set_value(arm, rig, cid, value, key=self.insert_keys)
        return f"Went to {self.name}."


class BC_OT_mech_remove_form(_MechOp, bpy.types.Operator):
    bl_idname = "boneforge.mech_remove_form"
    bl_label = "Remove Form"
    bl_description = "Forget this saved form"
    name: StringProperty(options={'HIDDEN', 'SKIP_SAVE'})

    def run(self, context, arm):
        forms = arm.data.bonecraft_mech.forms
        i = next((i for i, f in enumerate(forms) if f.name == self.name), -1)
        if i < 0:
            raise build.BuildError("That form no longer exists.")
        forms.remove(i)


class BC_OT_mech_select_bone(_MechOp, bpy.types.Operator):
    bl_idname = "boneforge.mech_select_bone"
    bl_label = "Select"
    bl_description = "Select this bone to inspect it"
    bone: StringProperty(options={'HIDDEN', 'SKIP_SAVE'})

    def run(self, context, arm):
        pb = arm.pose.bones.get(self.bone)
        if pb is None:
            raise build.BuildError("That bone no longer exists.")
        if context.view_layer.objects.active != arm or arm.mode != 'POSE':
            if context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            context.view_layer.objects.active = arm
            bpy.ops.object.mode_set(mode='POSE')
        for other in arm.pose.bones:
            other.select = False
        pb.hide = False
        pb.select = True
        arm.data.bones.active = pb.bone


classes = (BC_OT_mech_add_parts, BC_OT_mech_add_joint, BC_OT_mech_add_link, BC_OT_mech_set_limit,
           BC_OT_mech_rebuild, BC_OT_mech_restore, BC_OT_mech_keep_mine, BC_OT_mech_detach, BC_OT_mech_delete,
           BC_OT_mech_cancel_pivot, BC_OT_mech_cancel_capture,
           BC_OT_mech_apply_transforms, BC_OT_mech_edit_pivot, BC_OT_mech_apply_pivot, BC_OT_mech_merge_vrchat,
           BC_OT_mech_reassign, BC_OT_mech_add_sequence, BC_OT_mech_capture_step, BC_OT_mech_remove_step,
           BC_OT_mech_save_form, BC_OT_mech_go_to_form, BC_OT_mech_remove_form, BC_OT_mech_select_bone)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
