# bonecraft/boneforge/mechanisms/guide_steps.py
"""Guided build steps (pure): what to click next, as a full sentence or a short label (spec §7.2-7.3)."""
from dataclasses import dataclass

AXIS_HINT = "press X, Y or Z for the axis, or A to align to the selection"


@dataclass(frozen=True)
class Ask:
    kind: str                 # "part", "parts" (a list ended by Enter) or "axis"
    short: str
    long: str
    needs: str = ""           # "HINGE" or "JOINT": the clicked part must already have one


_AXIS = Ask("axis", "Axis", AXIS_HINT)
STEPS = {
    "HINGE": (Ask("part", "Moving part", "click the part that turns"), _AXIS),
    "SLIDE": (Ask("part", "Moving part", "click the part that slides"), _AXIS),
    "TELESCOPE": (Ask("part", "Base part", "click the base the telescope extends from"),
                  Ask("parts", "Segments", "click each segment from the base outwards, then press Enter"), _AXIS),
    "PISTON": (Ask("part", "Cylinder part", "click the cylinder part"), Ask("part", "Rod part", "click the rod part")),
    "GEAR": (Ask("part", "Driving part", "click the part whose hinge drives", "HINGE"),
             Ask("part", "Driven part", "click the part that is driven", "JOINT")),
    "FOLLOW": (Ask("part", "Leading part", "click the part that leads", "JOINT"),
               Ask("part", "Following part", "click the part that follows", "JOINT")),
}


def header_text(prompt, hover="", picked="", message=""):
    """The viewport header line: the prompt, then picked / hovered part names and the message."""
    bits = [x for x in (picked and f"picked: {picked}", hover and f"over: {hover}", message) if x]
    joined = " \xb7 ".join(bits)
    return prompt + (f"   ({joined})" if bits else "")


class Guide:
    def __init__(self, mech_type):
        self.type = mech_type
        self.steps = STEPS[mech_type]
        self.i = 0
        self.picked = []
        self.axis = None
        self._history = []

    @property
    def done(self):
        return self.i >= len(self.steps)

    def prompt(self, helpers=True):
        if self.done:
            return "Enter keeps it; Esc removes it." if helpers else "Enter / Esc"
        ask = self.steps[self.i]
        if not helpers:
            return ask.short
        return f"Step {self.i + 1} of {len(self.steps)}: {ask.long}. Esc cancels."

    def pick(self, part_id, joint_type):
        if self.done:
            return "Enter keeps it; Esc removes it."
        ask = self.steps[self.i]
        if ask.kind == "axis":
            return AXIS_HINT[0].upper() + AXIS_HINT[1:] + "."
        if part_id in self.picked:
            return "That part is already picked."
        if ask.needs == "HINGE" and joint_type != "HINGE":
            return "That part needs a Hinge first."
        if ask.needs == "JOINT" and joint_type not in ("HINGE", "SLIDE"):
            return "That part needs a Hinge or Slide first."
        self.picked.append(part_id)
        self._history.append(("pick", self.i))
        if ask.kind == "part":
            self.i += 1
        return ""

    def finish_list(self):
        if self.done or self.steps[self.i].kind != "parts":
            return ""
        if len(self.picked) < 2:
            return "Click at least one segment."
        self._history.append(("list", self.i))
        self.i += 1
        return ""

    def choose_axis(self, axis):
        if self.done or self.steps[self.i].kind != "axis":
            return "Click the part first."
        self.axis = axis
        self._history.append(("axis", self.i))
        self.i += 1
        return ""

    def back(self):
        """Undo the last answer (used when building from the answers failed)."""
        if not self._history:
            return
        kind, i = self._history.pop()
        if kind == "pick":
            self.picked.pop()
        elif kind == "axis":
            self.axis = None
        self.i = i

    def op_args(self):
        if self.type in ("HINGE", "SLIDE", "TELESCOPE"):
            return "BC_OT_mech_add_joint", {"type": self.type, "parts": ",".join(self.picked), "axis": self.axis}
        if self.type == "PISTON":
            return "BC_OT_mech_add_link", {"type": "PISTON", "parts": ",".join(self.picked)}
        return "BC_OT_mech_add_link", {"type": self.type, "source": self.picked[0], "target": self.picked[1]}
