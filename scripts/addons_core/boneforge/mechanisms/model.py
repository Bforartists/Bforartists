"""BoneCraft Mechanisms records as plain data (no bpy).

Units: hinge values are degrees, slide values are scene units; the planner
converts to radians for constraints. Ids are 8 hex characters.
"""
from __future__ import annotations

import re
import secrets
from dataclasses import dataclass, field

JOINT_TYPES = ("HINGE", "SLIDE", "TELESCOPE")
LINK_TYPES = ("PISTON", "GEAR", "FOLLOW")
TYPES = JOINT_TYPES + LINK_TYPES
GEAR_KINDS = ("GEAR", "BELT", "RACK")
EASES = ("LINEAR", "EASE_IN", "EASE_OUT", "EASE_IN_OUT", "SNAP")

# Settings drawn per type. Fields a type does not list are ignored and never drawn.
FIELDS = {
    "HINGE": ("name", "axis", "min", "max"),
    "SLIDE": ("name", "axis", "min", "max"),
    "TELESCOPE": ("name", "axis", "length", "shares"),
    "PISTON": ("name", "stretch"),
    "GEAR": ("name", "gear_kind", "ratio", "teeth_source", "teeth_target", "reverse", "pinion_radius"),
    "FOLLOW": ("name", "source_range", "target_range", "curve"),
}
HANDLE_FIELDS = ("handle_widget", "handle_size", "handle_color")   # joints only
DEFAULT_WIDGET = {"HINGE": "eyelid", "SLIDE": "arrow", "TELESCOPE": "arrow"}
TYPE_LABEL = {"HINGE": "Hinge", "SLIDE": "Slide", "TELESCOPE": "Telescope",
              "PISTON": "Piston", "GEAR": "Gear Link", "FOLLOW": "Follow"}


@dataclass
class Part:
    id: str
    name: str
    kind: str = "OBJECT"               # OBJECT | LOOSE
    object_name: str = ""
    vertex_group: str = ""             # LOOSE: the island's vertex group
    parent: str = ""                   # parent part id; "" rides on root
    pivot: tuple = (0.0, 0.0, 0.0)     # armature space
    size: float = 0.2                  # bone length


@dataclass
class Mechanism:
    id: str
    type: str
    name: str
    parts: list = field(default_factory=list)      # HINGE/SLIDE [part]; TELESCOPE [base, seg...]; PISTON [cylinder, rod]
    axis: tuple = (1.0, 0.0, 0.0)                  # armature-space direction
    min: float = 0.0
    max: float = 90.0
    source: str = ""                               # GEAR, FOLLOW: source joint id
    target: str = ""                               # GEAR, FOLLOW: target joint id
    ratio: float = 1.0
    teeth_source: int = 0
    teeth_target: int = 0
    gear_kind: str = "GEAR"
    reverse: bool = False
    pinion_radius: float = 0.05
    source_range: tuple = (0.0, 90.0)
    target_range: tuple = (0.0, 40.0)
    curve: bool = False
    stretch: bool = False
    length: float = 0.0
    shares: list = field(default_factory=list)
    handle_widget: str = ""
    handle_size: float = 1.0
    handle_color: str = "special"


@dataclass
class Step:
    target: str                        # joint id
    value: float                       # joint value when the step ends (degrees / units)
    start: float = 0.0
    end: float = 1.0
    ease: str = "EASE_IN_OUT"


@dataclass
class Sequence:
    id: str
    name: str
    steps: list = field(default_factory=list)


@dataclass
class Form:
    name: str
    values: dict = field(default_factory=dict)     # control id -> value


@dataclass
class MechRig:
    parts: list = field(default_factory=list)
    mechanisms: list = field(default_factory=list)
    sequences: list = field(default_factory=list)
    forms: list = field(default_factory=list)
    missing: set = field(default_factory=set)      # part ids whose object or vertex group is gone

    def part(self, pid):
        return next((p for p in self.parts if p.id == pid), None)

    def mech(self, mid):
        return next((m for m in self.mechanisms if m.id == mid), None)

    def seq(self, sid):
        return next((s for s in self.sequences if s.id == sid), None)

    def ids(self):
        return {x.id for x in self.parts + self.mechanisms + self.sequences}


def new_id(taken, token=lambda: secrets.token_hex(4)):
    """A fresh 8-hex id, never ``root`` and never in ``taken``."""
    while True:
        rid = token()
        if rid not in taken and rid != "root":
            return rid


_UNSAFE = re.compile(r'["\\]')          # would break 'pose.bones["..."]' data paths


def clean_name(text):
    text = _UNSAFE.sub("_", " ".join(str(text).split()))
    return text or "Part"


def unique_name(base, taken):
    if base not in taken:
        return base
    i = 1
    while f"{base}.{i:03d}" in taken:
        i += 1
    return f"{base}.{i:03d}"


def default_name(part_name, mech_type):
    return f"{clean_name(part_name)} {TYPE_LABEL[mech_type]}"


def controls(rig):
    """(control id, label) for every joint handle and Sequence slider, in panel order."""
    return ([(m.id, m.name) for m in rig.mechanisms if m.type in JOINT_TYPES]
            + [(s.id, s.name) for s in rig.sequences])


def step_window(spans):
    """(start, end) for the next captured step, after existing ``(start, end)`` spans.

    The next free quarter; once the Sequence is full, the last quarter again (which overlaps)."""
    start = max((end for _start, end in spans), default=0.0)
    if start >= 1.0 - 1e-6:
        start = 0.75
    return start, min(1.0, start + 0.25)


def overlapping_steps(spans, start, end):
    """Indexes of the ``(start, end)`` spans the window ``start..end`` overlaps."""
    return [i for i, (s, e) in enumerate(spans) if s < end and e > start]


def gear_ratio(m):
    """Source teeth / target teeth when both are set, else the typed ratio."""
    if m.teeth_source > 0 and m.teeth_target > 0:
        return m.teeth_source / m.teeth_target
    return m.ratio
