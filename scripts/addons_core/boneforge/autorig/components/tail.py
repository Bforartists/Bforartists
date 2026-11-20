"""Tail component: FK deform chain (creature/quadruped preset)."""
from . import sided


def build_tail(plan, segments=5, attach="hips", base=(0.0, -0.06, 0.95)):
    prev = attach
    names = []
    for i in range(segments):
        n = "tail.%02d" % (i + 1)
        head = (0.0, base[1] - i * 0.10, base[2] - i * 0.02)
        tail = (0.0, base[1] - (i + 1) * 0.10, base[2] - (i + 1) * 0.02)
        plan.add_bone(n, head, tail, parent=prev, use_connect=(i > 0),
                      deform=True, collection="Tail")
        plan.add_widget(n, "fk_ring", "fk", 0.8)
        prev = n
        names.append(n)
    return names
