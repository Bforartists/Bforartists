"""Test: sweep one mechanism through its range and back on a timer; no keyframes; pose restored (spec §7.4)."""
import bpy
from bpy.props import StringProperty

from boneforge.mechanisms import build, model, planner, records


def sweep_values(lo, hi, frames=24):
    up = [lo + (hi - lo) * i / frames for i in range(frames + 1)]
    return up + up[-2::-1]


def _moving_ancestor(rig, part_ids):
    for pid in part_ids:
        p = rig.part(pid)
        while p is not None and p.parent:
            p = rig.part(p.parent)
            joint = planner.joint_for_part(rig, p.id) if p is not None else None
            if joint is not None and joint.type in model.JOINT_TYPES:
                return joint
    return None


def driver_of(rig, rid):
    """(control id, lo, hi) that the Test of record ``rid`` sweeps."""
    m = rig.mech(rid)
    if m is None:
        if rig.seq(rid) is None:
            raise build.BuildError("That record no longer exists.")
        return rid, 0.0, 1.0
    if m.type in ("GEAR", "FOLLOW"):
        m = rig.mech(m.source)
    elif m.type == "PISTON":
        m = _moving_ancestor(rig, m.parts)
        if m is None:
            raise build.BuildError("Nothing moves this Piston yet: give a part it rides on a joint first.")
    if m.type == "TELESCOPE":
        return m.id, 0.0, m.length
    if m.type == "HINGE" and m.max - m.min >= 360.0:
        return m.id, 0.0, 360.0                    # a full turn or more spins freely (spec §6): sweep one turn
    return m.id, float(m.min), float(m.max)


class Sweep:
    """Steps one control through ``sweep_values``; ``stop`` (or the last step) restores every control."""

    def __init__(self, arm_obj, rig, rid, frames=24):
        self.arm, self.rig = arm_obj, rig
        self.cid, lo, hi = driver_of(rig, rid)
        self.saved = {cid: build.get_value(arm_obj, rig, cid) for cid, _ in model.controls(rig)}
        self.values = sweep_values(lo, hi, frames)
        self.i = 0

    def step(self):
        if self.i >= len(self.values):
            self.stop()
            return False
        build.set_value(self.arm, self.rig, self.cid, self.values[self.i])
        self.i += 1
        return True

    def stop(self):
        for cid, v in self.saved.items():
            build.set_value(self.arm, self.rig, cid, v)
        self.i = len(self.values)


class BC_OT_mech_test(bpy.types.Operator):
    bl_idname = "boneforge.mech_test"
    bl_label = "Test"
    bl_description = "Sweep this mechanism through its range and back. Writes no keys; Esc stops"
    bl_options = {'REGISTER'}
    target: StringProperty(options={'HIDDEN', 'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        if records.active_rig(context) is None:
            cls.poll_message_set("Select a mechanism rig or one of its parts.")
            return False
        return True

    def invoke(self, context, event):
        arm = records.active_rig(context)
        try:
            self.sweep = Sweep(arm, records.to_model(arm), self.target)
        except build.BuildError as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
        self.timer = context.window_manager.event_timer_add(1.0 / 24.0, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):                          # scripts: run the sweep at once
        arm = records.active_rig(context)
        try:
            sweep = Sweep(arm, records.to_model(arm), self.target)
        except build.BuildError as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
        while sweep.step():
            context.view_layer.update()
        return {'FINISHED'}

    def modal(self, context, event):
        if event.type in {'ESC', 'RIGHTMOUSE'}:
            self.sweep.stop()
            return self._end(context, {'CANCELLED'})
        if event.type == 'TIMER':
            if context.area is not None:
                context.area.tag_redraw()
            target = int(self.timer.time_duration * 24) + 1     # paced by elapsed time: other window timers cannot speed it up
            while self.sweep.i < target:
                if not self.sweep.step():
                    return self._end(context, {'FINISHED'})
        return {'PASS_THROUGH'}

    def cancel(self, context):
        """Blender ends the modal (window closed, file loaded): put the pose back and remove the timer."""
        try:
            self.sweep.stop()
        finally:
            self._end(context, {'CANCELLED'})

    def _end(self, context, result):
        context.window_manager.event_timer_remove(self.timer)
        return result


def register():
    bpy.utils.register_class(BC_OT_mech_test)


def unregister():
    try:
        bpy.utils.unregister_class(BC_OT_mech_test)
    except RuntimeError:
        pass
