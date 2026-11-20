"""Sequence: one slider (local Y 0…1). Each step plays an eased generated action over its slice."""
import math

from boneforge.mechanisms import geometry, model, planner as P
from boneforge.mechanisms.recipes.slide import limits_y


def eased(t, ease):
    """The fraction of a step done at slice position t (Blender's SINE easing)."""
    t = min(1.0, max(0.0, t))
    if ease == "EASE_IN":
        return 1.0 - math.cos(t * math.pi / 2)
    if ease == "EASE_OUT":
        return math.sin(t * math.pi / 2)
    if ease == "EASE_IN_OUT":
        return (1.0 - math.cos(math.pi * t)) / 2
    if ease == "SNAP":
        return 1.0 if t >= 1.0 else 0.0
    return t


def ease_keys(delta, ease):
    if ease == "LINEAR":
        return [(0.0, 0.0, "LINEAR", ""), (10.0, delta, "LINEAR", "")]
    if ease == "SNAP":
        return [(0.0, 0.0, "CONSTANT", ""), (10.0, delta, "CONSTANT", "")]
    return [(0.0, 0.0, "SINE", ease), (10.0, delta, "LINEAR", "")]


def deltas(seq):
    """[(step index, step, delta)]: each step adds its target minus the joint's previous target."""
    out, prev = [], {}
    order = sorted(range(len(seq.steps)), key=lambda i: (seq.steps[i].start, i))
    for i in order:
        st = seq.steps[i]
        out.append((i, st, st.value - prev.get(st.target, 0.0)))
        prev[st.target] = st.value
    return sorted(out, key=lambda x: x[0])


def value(rig, seq, joint_id, x):
    """The joint value this Sequence adds at slider x (degrees or units)."""
    total = 0.0
    for _, st, d in deltas(seq):
        if st.target == joint_id and st.end > st.start:
            total += d * eased((x - st.start) / (st.end - st.start), st.ease)
    return total


def plan_all(plan, rig, skip):
    for n, seq in enumerate(rig.sequences):
        slider = P.key(seq.id, "CTRL")
        pose = P.add_bone(plan, slider, f"CTRL-SEQ-{seq.name}", (0.25 * n, -0.5, 0.0),
                          geometry.frame_for_slide((0.0, 1.0, 0.0)), 0.2, P.ROOT, seq.id, "CTRL", hide=False)
        pose.lock_location = (True, False, True)
        plan.build.add_widget(bone=slider, widget="arrow", color_group="special", scale=1.0)
        P.add_con(plan, slider, "LIMIT_LOCATION", seq.id, "handle_limit", P.STAGE_LIMIT,
                  owner_space="LOCAL", use_transform_limit=True, **limits_y(0.0, 1.0))
        for i, st, d in deltas(seq):
            joint = rig.mech(st.target)
            if joint is None or joint.type not in model.JOINT_TYPES:
                raise P.PlanError(f"Sequence '{seq.name}': step {i + 1} has no joint.")
            if not (0.0 <= st.start < st.end <= 1.0):
                raise P.PlanError(f"Sequence '{seq.name}': step {i + 1} must start before it ends, within 0…1.")
            if joint.id in skip:
                plan.skipped.append((f"{seq.id}:s{i}", skip[joint.id]))
                continue
            rot = joint.type == "HINGE"
            bone = P.key(joint.id, "CTRL") if joint.type == "TELESCOPE" else P.key(joint.parts[0], "MCH")
            akey = P.key(seq.id, f"s{i}")
            P.add_con(plan, bone, "ACTION", seq.id, f"s{i}", P.STAGE_LINK, subtarget=slider,
                      target_space="LOCAL", transform_channel="LOCATION_Y", min=st.start, max=st.end,
                      frame_start=0, frame_end=10, mix_mode="AFTER_SPLIT", action=P.ActionRef(akey))
            plan.actions.append(P.ActionDef(akey, f"BC {seq.name} {i + 1}", seq.id, bone,
                                            "rotation_euler" if rot else "location", 0 if rot else 1,
                                            ease_keys(math.radians(d) if rot else d, st.ease)))
