"""Mechanisms checks for the Rig Validator that need only the records (pure; no bpy)."""
from boneforge.mechanisms import planner


def record_checks(rig):
    """[(status, message, subject)]: plan errors, loops, missing parts, free-gear warnings."""
    out = []
    for p in rig.parts:
        if p.id in rig.missing:
            out.append(("fail", f"Part '{p.name}' is missing: Reassign it or delete it.", p.name))
    try:
        plan = planner.plan_rig(rig)
    except planner.PlanError as exc:
        return [("fail", str(exc), "")] + out
    return out + gear_warnings(rig, plan)


def _driver_chain(rig, plan, jid):
    """Joints whose handles a driver-kind gear into ``jid`` reads."""
    seen, todo = set(), [jid]
    while todo:
        j = todo.pop()
        if j not in seen:
            seen.add(j)
            todo += [g.source for g in rig.mechanisms
                     if g.type == "GEAR" and g.target == j and plan.recipe.get(g.id) == "DRIVER"]
    return seen


def gear_warnings(rig, plan):
    """A free-spinning Gear Link follows handles and gears only (D11): say when a Sequence or Follow is lost."""
    moved = {m.target for m in rig.mechanisms if m.type == "FOLLOW"}
    moved |= {st.target for s in rig.sequences for st in s.steps}
    out = []
    for g in rig.mechanisms:
        if g.type == "GEAR" and plan.recipe.get(g.id) == "DRIVER":
            hit = sorted(rig.mech(j).name for j in _driver_chain(rig, plan, g.source) & moved)
            if hit:
                out.append(("warn", f"'{g.name}' spins freely, so it follows only handles and gears: "
                                    f"what a Sequence or Follow does to {', '.join(hit)} is not passed on.", g.name))
    return out
