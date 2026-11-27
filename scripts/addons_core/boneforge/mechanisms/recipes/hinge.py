"""Hinge: handle locked to local X rotation, limits on the handle (gizmo stops) and on MCH."""
import math

from boneforge.mechanisms import geometry, planner as P


def limits(m):
    """(limited, lo_rad, hi_rad). A range of 360° or more spins freely."""
    if m.min > m.max:
        raise P.PlanError(f"'{m.name}': Min is above Max.")
    limited = (m.max - m.min) < 360.0
    if limited and (m.min < -180.0 or m.max > 180.0):
        raise P.PlanError(f"'{m.name}': limits must stay within −180°…180°. "
                          "For a free-spinning hinge, set a range of 360° or more.")
    return limited, math.radians(m.min), math.radians(m.max)


def plan(plan, m, rig):
    part = rig.part(m.parts[0])
    limited, lo, hi = limits(m)
    ctrl, mch = P.key(m.id, "CTRL"), P.key(part.id, "MCH")
    pose = P.add_bone(plan, ctrl, f"CTRL-{part.name}", part.pivot, geometry.frame_for_hinge(m.axis),
                      part.size * 1.2, P.parent_key(rig, part), m.id, "CTRL", hide=False)
    pose.lock_rotation = (False, True, True)
    P.add_widget(plan, ctrl, m)
    lim = dict(owner_space="LOCAL", use_limit_x=limited, min_x=lo, max_x=hi, use_limit_y=True, use_limit_z=True)
    P.add_con(plan, ctrl, "LIMIT_ROTATION", m.id, "handle_limit", P.STAGE_LIMIT, use_transform_limit=True, **lim)
    P.add_con(plan, mch, "COPY_TRANSFORMS", m.id, "copy", P.STAGE_COPY, subtarget=ctrl,
              target_space="LOCAL", owner_space="LOCAL", mix_mode="AFTER_SPLIT")
    P.add_con(plan, mch, "LIMIT_ROTATION", m.id, "limit", P.STAGE_LIMIT, **lim)
    plan.recipe[m.id] = "HINGE"
