"""Limb component: dual IK/FK chain with pole target and IK/FK blend drivers.

``tag`` and ``y_offset`` let the same builder place multiple distinct limbs
(e.g. quadruped front/back legs) without name collisions. With the defaults
(tag="", y_offset=0.0) output is identical to the original biped limb.
"""
from . import sided

_ARM = {
    "clavicle": ((0.03, 0.0, 1.45), (0.16, 0.0, 1.45)),
    "upperarm": ((0.16, 0.0, 1.45), (0.45, 0.0, 1.45)),
    "forearm":  ((0.45, 0.0, 1.45), (0.70, 0.0, 1.45)),
    "hand":     ((0.70, 0.0, 1.45), (0.85, 0.0, 1.45)),
}
_LEG = {
    "thigh": ((0.10, 0.0, 0.95), (0.11, 0.0, 0.52)),
    "shin":  ((0.11, 0.0, 0.52), (0.12, 0.0, 0.10)),
    "foot":  ((0.12, 0.0, 0.10), (0.12, 0.18, 0.03)),
    "toe":   ((0.12, 0.18, 0.03), (0.12, 0.30, 0.03)),
}
PROPS_BONE = "properties"


def build_limb(plan, kind, side, stretch=True, props_bone=PROPS_BONE,
               tag="", y_offset=0.0):
    tmpl = _ARM if kind == "arm" else _LEG
    seg = ["upperarm", "forearm", "hand"] if kind == "arm" \
        else ["thigh", "shin", "foot"]
    root_seg = "clavicle" if kind == "arm" else None
    pre = (tag + "_") if tag else ""
    limb_id = ("%s-%s" % (tag, kind)) if tag else kind

    def _mx(p):
        x = p[0] if side == "L" else -p[0]
        return (x, p[1] + y_offset, p[2])

    def H(name):
        return _mx(tmpl[name][0])

    def T(name):
        return _mx(tmpl[name][1])

    parent_attach = "chest" if kind == "arm" else "hips"
    if root_seg:
        cl = sided("%s%s.fk" % (pre, root_seg), side)
        plan.add_bone(cl, H(root_seg), T(root_seg), parent=parent_attach,
                      deform=True, collection="FK")
        plan.add_widget(cl, "fk_ring", "fk", 1.0)
        attach = cl
    else:
        attach = parent_attach

    def_names = [sided("%s%s.def" % (pre, s), side) for s in seg]
    prev = attach
    for i, s in enumerate(seg):
        plan.add_bone(def_names[i], H(s), T(s), parent=prev,
                      use_connect=(i > 0), deform=True, collection="Deform")
        prev = def_names[i]

    fk_names = [sided("%s%s.fk" % (pre, s), side) for s in seg]
    prev = attach
    for i, s in enumerate(seg):
        plan.add_bone(fk_names[i], H(s), T(s), parent=prev,
                      use_connect=(i > 0), collection="FK")
        plan.add_widget(fk_names[i], "fk_ring", "fk", 1.1)
        prev = fk_names[i]

    mch_names = [sided("%s%s.mch_ik" % (pre, s), side) for s in seg[:2]]
    # IK stretch is native (BoneDef.ik_stretch), not a STRETCH_TO constraint:
    # a STRETCH_TO on the IK bone lets the solver reach any target by
    # stretching, so the elbow never bends. Rigid by default (0.0) so an
    # FK->IK match reproduces the FK pose exactly; with ``stretch`` an
    # ``IK_stretch-<limb>-<side>`` slider (0 = rigid .. 1 = full) drives it.
    stretch_amt = 0.0
    prev = attach
    for i in range(2):
        plan.add_bone(mch_names[i], H(seg[i]), T(seg[i]), parent=prev,
                      use_connect=(i > 0), collection="MCH",
                      ik_stretch=stretch_amt)
        prev = mch_names[i]

    ik_ctrl = sided("%s%s.ik" % (pre, seg[1]), side)
    ik_head = T(seg[1])
    plan.add_bone(ik_ctrl, ik_head, (ik_head[0], ik_head[1] + 0.12, ik_head[2]),
                  collection="IK")
    plan.add_widget(ik_ctrl, "cube", "ik", 1.2)
    pole = sided("%s%s.pole" % (pre, kind), side)
    poff = 0.4 if kind == "arm" else -0.4
    pbase = _mx((tmpl[seg[0]][1][0], poff, tmpl[seg[0]][1][2]))
    plan.add_bone(pole, pbase, (pbase[0], pbase[1], pbase[2] + 0.06),
                  collection="IK")
    plan.add_widget(pole, "diamond", "ik", 1.0)

    ikname = "BF_IK-%s-%s" % (limb_id, side)
    plan.add_constraint(mch_names[1], "IK", ikname, subtarget=ik_ctrl,
                        params={"chain_count": 2, "pole_subtarget": pole,
                                "pole_angle": -1.5708 if kind == "leg" else 1.5708})
    # Stretch is handled by the chain's native ``ik_stretch`` (set on the mch
    # bones above), not a STRETCH_TO constraint — see the note there.

    prop_name = "IK_FK-%s-%s" % (limb_id, side)
    plan.add_prop(props_bone, prop_name, default=0.0,
                  description="IK/FK blend for %s %s" % (limb_id, side))
    for i in range(len(seg)):
        d = def_names[i]
        plan.add_constraint(d, "COPY_ROTATION", "BF_FK-%d" % i,
                            subtarget=fk_names[i], params={"influence": 1.0})
        ik_src = mch_names[i] if i < 2 else ik_ctrl
        cn = "BF_IKblend-%d" % i
        plan.add_constraint(d, "COPY_ROTATION", cn, subtarget=ik_src,
                            params={"influence": 0.0})
        plan.add_driver(d, 'constraints["%s"].influence' % cn, index=-1,
                        expression="v",
                        variables=[{"name": "v", "bone_path":
                                    'pose.bones["%s"]["%s"]' % (props_bone, prop_name)}])
    if stretch:
        # IK stretch that reaches the skin: the slider drives the IK chain's
        # native stretch, and each deform bone copies the chain's lengthening
        # (local Y scale) blended by the IK/FK switch — FK stays rigid.
        # Before this, the chain stretched but the deform bones only copied
        # rotation, so the mesh never did.
        sprop = "IK_stretch-%s-%s" % (limb_id, side)
        plan.add_prop(props_bone, sprop, default=0.0,
                      description="IK stretch for %s %s (0 rigid .. 1 full)" % (limb_id, side))
        svar = [{"name": "v", "bone_path": 'pose.bones["%s"]["%s"]' % (props_bone, sprop)}]
        ikvar = [{"name": "v", "bone_path": 'pose.bones["%s"]["%s"]' % (props_bone, prop_name)}]
        for m in mch_names:
            plan.add_driver(m, "ik_stretch", index=-1, expression="v", variables=svar)
        for i in range(2):
            cn = "BF_IKstretch-%d" % i
            plan.add_constraint(def_names[i], "COPY_SCALE", cn, subtarget=mch_names[i],
                                params={"use_x": False, "use_z": False,
                                        "owner_space": 'LOCAL', "target_space": 'LOCAL',
                                        "influence": 0.0})
            plan.add_driver(def_names[i], 'constraints["%s"].influence' % cn, index=-1,
                            expression="v", variables=ikvar)
    return def_names
