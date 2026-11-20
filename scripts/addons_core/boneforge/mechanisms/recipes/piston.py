"""Piston: each end aims at a fixed, constraint-free point on the other side (no cycle).

planner.check_records has already refused a wrong part count and coincident pivots.
"""
from boneforge.mechanisms import geometry, planner as P


def plan(plan, m, rig):
    cyl, rod = rig.part(m.parts[0]), rig.part(m.parts[1])
    dist = geometry.length(geometry.sub(rod.pivot, cyl.pivot))
    for end, me, other in (("A", cyl, rod), ("B", rod, cyl)):
        aim, tgt = P.key(m.id, f"AIM_{end}"), P.key(m.id, f"TGT_{end}")
        frame = geometry.frame_toward(me.pivot, other.pivot)
        P.add_bone(plan, aim, f"MCH-{me.name}-aim", me.pivot, frame, me.size, P.parent_key(rig, me), m.id, "MCH")
        P.add_bone(plan, tgt, f"MCH-{me.name}-target", other.pivot, frame, me.size * 0.25,
                   P.parent_key(rig, other), m.id, "MCH")
        if end == "B" and m.stretch:
            P.add_con(plan, aim, "STRETCH_TO", m.id, "stretch_b", P.STAGE_LINK, subtarget=tgt,
                      rest_length=dist, volume="NO_VOLUME", keep_axis="PLANE_X")
        else:
            P.add_con(plan, aim, "DAMPED_TRACK", m.id, f"aim_{end.lower()}", P.STAGE_LINK,
                      subtarget=tgt, track_axis="TRACK_Y")
        P.add_con(plan, P.key(me.id, "MCH"), "COPY_TRANSFORMS", m.id, f"follow_{end.lower()}",
                  P.STAGE_FOLLOW, subtarget=aim, target_space="WORLD", owner_space="WORLD")
    plan.recipe[m.id] = "PISTON"
