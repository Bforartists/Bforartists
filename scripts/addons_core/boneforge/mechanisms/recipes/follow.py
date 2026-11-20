"""Follow: a source range maps onto a target range, clamped. Straight = Transform; Curve = Action."""
import math

from boneforge.mechanisms import planner as P
from boneforge.mechanisms.recipes import hinge


def _channel(joint):
    """(map type, axis letter, is rotation)."""
    return ("ROTATION", "X", True) if joint.type == "HINGE" else ("LOCATION", "Y", False)


def plan(plan, m, rig):
    src, tgt = rig.mech(m.source), rig.mech(m.target)
    for joint, role in ((src, "source"), (tgt, "target")):
        if joint is None or joint.type not in ("HINGE", "SLIDE"):
            raise P.PlanError(f"'{m.name}': the {role} must be a Hinge or Slide.")
    if src.type == "HINGE" and not hinge.limits(src)[0]:
        raise P.PlanError(f"'{m.name}': the source Hinge must have limits under a full turn.")   # a spinning input wraps
    (s0, s1), (t0, t1) = m.source_range, m.target_range
    if s0 == s1:
        raise P.PlanError(f"'{m.name}': the source range is empty.")
    if src.type == "HINGE" and (min(s0, s1) < -180 or max(s0, s1) > 180):
        raise P.PlanError(f"'{m.name}': a Hinge source range must stay within −180°…180°.")
    smap, sax, srot = _channel(src)
    tmap, tax, trot = _channel(tgt)
    cs = math.radians if srot else float
    ct = math.radians if trot else float
    bone, sub = P.key(tgt.parts[0], "MCH"), P.key(src.parts[0], "MCH")
    if m.curve:
        akey = P.key(m.id, "curve")
        P.add_con(plan, bone, "ACTION", m.id, "follow", P.STAGE_LINK, subtarget=sub, target_space="LOCAL",
                  transform_channel=f"{smap}_{sax}", min=cs(s0), max=cs(s1), frame_start=0, frame_end=10,
                  mix_mode="AFTER_SPLIT", action=P.ActionRef(akey))
        plan.actions.append(P.ActionDef(akey, f"BC {m.name}", m.id, bone,
                                        "rotation_euler" if trot else "location", 0 if trot else 1,
                                        [(0.0, ct(t0), "BEZIER", "AUTO"), (10.0, ct(t1), "BEZIER", "AUTO")]))
        plan.recipe[m.id] = "CURVE"
        return
    sfx, tfx = ("_rot" if srot else ""), ("_rot" if trot else "")
    params = dict(target_space="LOCAL", owner_space="LOCAL", map_from=smap, map_to=tmap, use_motion_extrapolate=False)
    params[f"from_min_{sax.lower()}{sfx}"], params[f"from_max_{sax.lower()}{sfx}"] = cs(s0), cs(s1)
    params[f"map_to_{tax.lower()}_from"] = sax
    params[f"to_min_{tax.lower()}{tfx}"], params[f"to_max_{tax.lower()}{tfx}"] = ct(t0), ct(t1)
    params["mix_mode_rot" if trot else "mix_mode"] = "ADD"
    P.add_con(plan, bone, "TRANSFORM", m.id, "follow", P.STAGE_LINK, subtarget=sub, **params)
    plan.recipe[m.id] = "STRAIGHT"
