"""Digit component: FK finger chains for one hand (deform + control)."""
from . import BoneDef, WidgetAssign, sided

# 5 fingers, 3 segments; offsets from the hand tip along +X (left hand)
_FINGERS = ["thumb", "index", "middle", "ring", "pinky"]


def build_hand_digits(plan, side, hand_bone=None):
    if hand_bone is None:
        hand_bone = sided("hand.def", side)
    base_x = 0.85 if side == "L" else -0.85
    sgn = 1.0 if side == "L" else -1.0
    names = []
    for fi, finger in enumerate(_FINGERS):
        spread = (fi - 2) * 0.025
        prev = hand_bone
        x = base_x
        for seg in range(3):
            n = sided(f"{finger}.{seg+1:02d}", side)
            head = (x, spread, 1.45)
            x = x + sgn * 0.04
            tail = (x, spread, 1.45)
            plan.add_bone(n, head, tail, parent=prev,
                          use_connect=(seg > 0), deform=True,
                          collection="Fingers")
            plan.add_widget(n, "circle_small", "fk", 0.6)
            prev = n
            names.append(n)
    return names
