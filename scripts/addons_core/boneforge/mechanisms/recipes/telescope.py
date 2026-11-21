"""Telescope: stacked segments; one handle on the base drives every segment by its share."""
import math

from boneforge.mechanisms import geometry, planner as P
from boneforge.mechanisms.recipes.slide import limits_y


def shares(m):
    n = len(m.parts) - 1
    if n < 1:
        raise P.PlanError(f"'{m.name}': a Telescope needs at least one segment.")
    if not math.isfinite(m.length) or m.length <= 0:
        raise P.PlanError(f"'{m.name}': the total length must be above zero.")
    if not m.shares:
        return [m.length / n] * n
    if len(m.shares) != n or not all(math.isfinite(x) for x in m.shares) or min(m.shares) < 0 or abs(sum(m.shares) - m.length) > 1e-6:
        raise P.PlanError(f"'{m.name}': {n} segment shares must add up to the total length {m.length:g}.")
    return list(m.shares)


def plan(plan, m, rig):
    base, segs = rig.part(m.parts[0]), [rig.part(p) for p in m.parts[1:]]
    prev = base
    for seg in segs:
        if seg.parent != prev.id:
            raise P.PlanError(f"'{m.name}': segment '{seg.name}' must ride on '{prev.name}'.")
        prev = seg
    cuts = shares(m)
    ctrl = P.key(m.id, "CTRL")
    pose = P.add_bone(plan, ctrl, f"CTRL-{m.name}", base.pivot, geometry.frame_for_slide(m.axis),
                      base.size * 1.2, P.key(base.id, "DEF"), m.id, "CTRL", hide=False)
    pose.lock_location = (True, False, True)
    P.add_widget(plan, ctrl, m)
    P.add_con(plan, ctrl, "LIMIT_LOCATION", m.id, "handle_limit", P.STAGE_LIMIT,
              owner_space="LOCAL", use_transform_limit=True, **limits_y(0.0, m.length))
    for i, (seg, share) in enumerate(zip(segs, cuts), 1):
        mch = P.key(seg.id, "MCH")
        P.add_con(plan, mch, "TRANSFORM", m.id, f"seg{i}", P.STAGE_LINK, subtarget=ctrl,
                  target_space="LOCAL", owner_space="LOCAL", map_from="LOCATION",
                  from_min_y=0.0, from_max_y=m.length, map_to="LOCATION", map_to_y_from="Y",
                  to_min_y=0.0, to_max_y=share, mix_mode="ADD", use_motion_extrapolate=False)
        P.add_con(plan, mch, "LIMIT_LOCATION", m.id, f"limit{i}", P.STAGE_LIMIT,
                  owner_space="LOCAL", **limits_y(0.0, share))
    plan.recipe[m.id] = "TELESCOPE"
