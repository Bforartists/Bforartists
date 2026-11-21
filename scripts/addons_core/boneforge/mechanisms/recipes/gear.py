"""Gear Link: Gear, Belt or Rack. D11: Transform within ±180°, simple-expression driver beyond."""
from boneforge.mechanisms import model, planner as P
from boneforge.mechanisms.recipes import hinge


def factor(m):
    r = model.gear_ratio(m)
    if r <= 0:
        raise P.PlanError(f"'{m.name}': the ratio must be above zero.")
    if m.gear_kind == "RACK" and m.pinion_radius <= 0:
        raise P.PlanError(f"'{m.name}': the pinion radius must be above zero.")
    k = {"GEAR": -r, "BELT": r, "RACK": r * m.pinion_radius}[m.gear_kind]
    return -k if m.reverse else k


def kind(rig, m):
    limited, _, _ = hinge.limits(rig.mech(m.source))
    return "TRANSFORM" if limited else "DRIVER"


def _joints(rig, m):
    src, tgt = rig.mech(m.source), rig.mech(m.target)
    if src is None or src.type != "HINGE":
        raise P.PlanError(f"'{m.name}': the source must be a Hinge.")
    want = "SLIDE" if m.gear_kind == "RACK" else "HINGE"
    if tgt is None or tgt.type != want:
        raise P.PlanError(f"'{m.name}': the target must be a {want.title()}.")
    return src, tgt


def plan(plan, m, rig):
    src, tgt = _joints(rig, m)
    k = factor(m)
    plan.recipe[m.id] = kind(rig, m)
    if plan.recipe[m.id] == "DRIVER":
        return                                   # summed per target joint in plan_drivers
    params = dict(target_space="LOCAL", owner_space="LOCAL", map_from="ROTATION",
                  from_min_x_rot=0.0, from_max_x_rot=1.0, use_motion_extrapolate=True)
    if m.gear_kind == "RACK":
        params.update(map_to="LOCATION", map_to_y_from="X", to_min_y=0.0, to_max_y=k, mix_mode="ADD")
    else:
        params.update(map_to="ROTATION", map_to_x_from="X", to_min_x_rot=0.0, to_max_x_rot=k, mix_mode_rot="ADD")
    P.add_con(plan, P.key(tgt.parts[0], "MCH"), "TRANSFORM", m.id, "gear", P.STAGE_LINK,
              subtarget=P.key(src.parts[0], "MCH"), **params)


def _add(terms, more, k=1.0):
    for t, c in more.items():
        terms[t] = terms.get(t, 0.0) + k * c


def _driver_incoming(rig, plan, jid):
    """Driver-kind gears into ``jid``, as {(bone key, space): coefficient}."""
    terms = {}
    for g in rig.mechanisms:
        if g.type == "GEAR" and g.target == jid and plan.recipe.get(g.id) == "DRIVER":
            _add(terms, handle_terms(rig, plan, g.source), factor(g))
    return terms


def handle_terms(rig, plan, jid):
    """Joint ``jid``'s value as {(bone key, space): coefficient}.

    Its own handle and every driver-kind gear chain into it are read raw in
    TRANSFORM_SPACE (no wrap). A Transform-kind gear into it has a limited
    source, so that source's MCH is read in LOCAL_SPACE: it never leaves ±180°.
    """
    terms = {(P.key(jid, "CTRL"), "TRANSFORM_SPACE"): 1.0}
    _add(terms, _driver_incoming(rig, plan, jid))
    for g in rig.mechanisms:
        if g.type == "GEAR" and g.target == jid and plan.recipe.get(g.id) == "TRANSFORM":
            src = rig.mech(g.source)
            _add(terms, {(P.key(src.parts[0], "MCH"), "LOCAL_SPACE"): 1.0}, factor(g))
    return terms


def plan_drivers(plan, rig, skip):
    for tgt in rig.mechanisms:
        if tgt.id in skip or tgt.type not in ("HINGE", "SLIDE"):
            continue
        terms = {t: c for t, c in _driver_incoming(rig, plan, tgt.id).items() if abs(c) > 1e-12}
        if not terms:
            continue
        order = sorted(terms)
        rack = tgt.type == "SLIDE"
        part = tgt.parts[0]
        plan.build.add_driver(
            bone=P.key(part, "MCH"),
            data_path_suffix="location" if rack else "rotation_euler",
            index=1 if rack else 0,
            expression=" + ".join(f"bc{i} * {terms[t]:.9g}" for i, t in enumerate(order)),
            variables=[dict(name=f"bc{i}", bone=bone, transform_type="ROT_X", space=space)
                       for i, (bone, space) in enumerate(order)],
            tag=part,
        )
