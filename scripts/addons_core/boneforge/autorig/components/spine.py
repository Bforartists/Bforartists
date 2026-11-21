"""Spine component: root + COG + properties bone + FK spine/neck/head.

Also creates the shared ``properties`` bone that limb/foot components hang
their custom blend/roll properties on.
"""
from . import BoneDef, WidgetAssign

PROPS_BONE = "properties"
_SPINE = [
    ("hips",     (0.0, 0.0, 0.95), (0.0, 0.0, 1.02), True),
    ("spine.01", (0.0, 0.0, 1.02), (0.0, 0.0, 1.15), True),
    ("spine.02", (0.0, 0.0, 1.15), (0.0, 0.0, 1.30), True),
    ("chest",    (0.0, 0.0, 1.30), (0.0, 0.0, 1.45), True),
    ("neck",     (0.0, 0.0, 1.48), (0.0, 0.0, 1.58), True),
    ("head",     (0.0, 0.0, 1.58), (0.0, 0.0, 1.75), True),
]


def build_spine(plan):
    # ground root control
    plan.add_bone("root", (0.0, 0.0, 0.0), (0.0, 0.30, 0.0),
                  collection="Root")
    plan.add_widget("root", "root_circle", "root", 1.0)
    # COG / torso master
    plan.add_bone("COG", (0.0, 0.0, 0.95), (0.0, 0.0, 1.05), parent="root",
                  collection="Controls")
    plan.add_widget("COG", "cube", "special", 1.4)
    # properties holder (hidden MCH)
    plan.add_bone(PROPS_BONE, (0.0, -0.20, 0.95), (0.0, -0.20, 1.0),
                  parent="root", collection="MCH")

    prev = "COG"
    for name, head, tail, deform in _SPINE:
        plan.add_bone(name, head, tail, parent=prev, use_connect=False,
                      deform=deform, collection="FK")
        plan.add_widget(name, "fk_ring", "fk",
                        1.3 if name in ("hips", "chest") else 1.0)
        prev = name
    return [n for (n, _, _, d) in _SPINE if d]
