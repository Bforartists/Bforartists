"""Spline-chain component: deform chain + 3 controls + spline-IK marker.

Plan-level: records a SPLINE_IK constraint on the chain tip. The apply
layer wires it to a generated curve in-host (deferred).
"""
from . import sided


def build_spline_chain(plan, name, count=6, start=(0.0, 0.0, 1.0),
                       end=(0.0, 0.0, 1.6), attach=None):
    def lerp(a, b, t):
        return tuple(a[k] + (b[k] - a[k]) * t for k in range(3))

    prev = attach
    defs = []
    for i in range(count):
        bn = "%s.%02d" % (name, i + 1)
        plan.add_bone(bn, lerp(start, end, i / count),
                      lerp(start, end, (i + 1) / count),
                      parent=prev, use_connect=(i > 0), deform=True,
                      collection="Spline")
        prev = bn
        defs.append(bn)
    for j, frac in enumerate((0.0, 0.5, 1.0)):
        cn = "%s_ctrl.%02d" % (name, j + 1)
        pos = lerp(start, end, frac)
        plan.add_bone(cn, pos, (pos[0], pos[1], pos[2] + 0.05),
                      parent=attach, collection="IK")
        plan.add_widget(cn, "cube", "ik", 0.8)
    plan.add_constraint(defs[-1], "SPLINE_IK", "BF_SPLINEIK-%s" % name,
                        params={"chain_count": count})
    return defs
