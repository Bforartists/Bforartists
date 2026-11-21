"""Slide: handle locked to local Y location, limits on the handle and on MCH."""
from boneforge.mechanisms import geometry, planner as P


def limits_y(lo, hi):
    """Limit Location fields: Y in lo…hi, X and Z held at 0."""
    return dict(use_min_x=True, use_max_x=True, use_min_y=True, use_max_y=True,
                min_y=lo, max_y=hi, use_min_z=True, use_max_z=True)


def plan(plan, m, rig):
    if m.min > m.max:
        raise P.PlanError(f"'{m.name}': Min is above Max.")
    part = rig.part(m.parts[0])
    ctrl, mch = P.key(m.id, "CTRL"), P.key(part.id, "MCH")
    pose = P.add_bone(plan, ctrl, f"CTRL-{part.name}", part.pivot, geometry.frame_for_slide(m.axis),
                      part.size * 1.2, P.parent_key(rig, part), m.id, "CTRL", hide=False)
    pose.lock_location = (True, False, True)
    P.add_widget(plan, ctrl, m)
    lim = dict(owner_space="LOCAL", **limits_y(m.min, m.max))
    P.add_con(plan, ctrl, "LIMIT_LOCATION", m.id, "handle_limit", P.STAGE_LIMIT, use_transform_limit=True, **lim)
    P.add_con(plan, mch, "COPY_TRANSFORMS", m.id, "copy", P.STAGE_COPY, subtarget=ctrl,
              target_space="LOCAL", owner_space="LOCAL", mix_mode="AFTER_SPLIT")
    P.add_con(plan, mch, "LIMIT_LOCATION", m.id, "limit", P.STAGE_LIMIT, **lim)
    plan.recipe[m.id] = "SLIDE"
