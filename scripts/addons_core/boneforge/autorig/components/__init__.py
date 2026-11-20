"""BoneCraft — control-rig component builders (pure planning layer).

Each builder in this package appends declarative *definitions* (bones,
constraints, drivers, custom properties, widgets, collections) to a
:class:`BuildPlan`. No ``bpy`` is touched here — the plan is realised
later by ``autorig.rig_build.apply_build_plan`` via ``core.rig_ops``.

This split is deliberate: it lets the rig's structure (the part that
closes the production-rig gap — full IK/FK + pole + stretch + foot-roll
+ driver networks) be unit-tested headlessly, with zero Blender.

Clean-room: rig topology and the IK/FK blend technique are implemented
from first principles / public rigging literature. Bone names and
hierarchy are BoneCraft-native and do not mirror any third-party rig.
"""

from dataclasses import dataclass, field
from typing import Optional


# -- side / naming convention (BoneForge-native) -----------------------

LEFT = "L"
RIGHT = "R"


def sided(base: str, side: Optional[str]) -> str:
    """BoneCraft naming: ``base-Side`` (e.g. ``upperarm.fk-L``)."""
    return f"{base}-{side}" if side else base


# -- declarative definitions -------------------------------------------

@dataclass
class BoneDef:
    name: str
    head: tuple
    tail: tuple
    roll: float = 0.0
    parent: Optional[str] = None
    use_connect: bool = False
    deform: bool = False
    collection: str = "Controls"
    ik_stretch: float = 0.0           # native IK stretch on a solved chain bone
    tag: str = ""                     # owning record id (BoneCraft Mechanisms); "" = untagged


@dataclass
class ConstraintDef:
    bone: str
    type: str
    name: str
    target_self: bool = True          # target the rig's own armature object
    subtarget: Optional[str] = None
    params: dict = field(default_factory=dict)
    tag: str = ""                     # owning record id; the name must start with "BC·<tag>·"


@dataclass
class PropDef:
    bone: str
    name: str
    default: float = 0.0
    soft_min: float = 0.0
    soft_max: float = 1.0
    description: str = ""


@dataclass
class DriverDef:
    bone: str                          # pose bone owning the driven path
    data_path_suffix: str              # e.g. 'constraints["X"].influence'
    index: int = -1
    expression: str = "v"
    variables: list = field(default_factory=list)
    tag: str = ""                     # owning record id


@dataclass
class WidgetAssign:
    bone: str
    widget: str                        # widget id in the shape library
    color_group: Optional[str] = None
    scale: float = 1.0


@dataclass
class CollectionDef:
    name: str
    ui_row: int = 0


class BuildPlan:
    """Accumulates declarative rig definitions; pure data."""

    def __init__(self):
        self.bones: list[BoneDef] = []
        self.constraints: list[ConstraintDef] = []
        self.props: list[PropDef] = []
        self.drivers: list[DriverDef] = []
        self.widgets: list[WidgetAssign] = []
        self.collections: list[CollectionDef] = []

    # convenience adders
    def add_bone(self, *a, **kw):
        self.bones.append(BoneDef(*a, **kw)); return self.bones[-1]

    def add_constraint(self, *a, **kw):
        self.constraints.append(ConstraintDef(*a, **kw)); return self.constraints[-1]

    def add_prop(self, *a, **kw):
        self.props.append(PropDef(*a, **kw)); return self.props[-1]

    def add_driver(self, *a, **kw):
        self.drivers.append(DriverDef(*a, **kw)); return self.drivers[-1]

    def add_widget(self, *a, **kw):
        self.widgets.append(WidgetAssign(*a, **kw)); return self.widgets[-1]

    def add_collection(self, *a, **kw):
        self.collections.append(CollectionDef(*a, **kw)); return self.collections[-1]

    # introspection (used by tests + golden-rig checks)
    def deform_bones(self):
        return [b.name for b in self.bones if b.deform]

    def bones_named(self, substr):
        return [b.name for b in self.bones if substr in b.name]

    def counts(self):
        return {
            "bones": len(self.bones),
            "deform_bones": len(self.deform_bones()),
            "constraints": len(self.constraints),
            "props": len(self.props),
            "drivers": len(self.drivers),
            "widgets": len(self.widgets),
            "collections": len(self.collections),
        }


def validate_plan(plan):
    """Return a list of structural problems in a BuildPlan ([] == valid).

    Catches the mistakes a new preset is most likely to introduce:
    duplicate bone names, dangling parents, and definitions that point at
    a bone the plan never creates.
    """
    problems = []
    names = [b.name for b in plan.bones]
    seen = set()
    for n in names:
        if n in seen:
            problems.append("duplicate bone: %s" % n)
        seen.add(n)
    nameset = set(names)
    for b in plan.bones:
        if b.parent and b.parent not in nameset:
            problems.append("dangling parent: %s -> %s" % (b.name, b.parent))
    for c in plan.constraints:
        if c.bone not in nameset:
            problems.append("constraint on missing bone: %s" % c.bone)
    for d in plan.drivers:
        if d.bone not in nameset:
            problems.append("driver on missing bone: %s" % d.bone)
    for w in plan.widgets:
        if w.bone not in nameset:
            problems.append("widget on missing bone: %s" % w.bone)
    for p in plan.props:
        if p.bone not in nameset:
            problems.append("prop on missing bone: %s" % p.bone)
    # Tagged constraints (BoneCraft Mechanisms): the name carries the tag and
    # fits Blender's 63-byte name limit; one name per bone.
    tagged = set()
    for c in plan.constraints:
        if not c.tag:
            continue
        if not c.name.startswith("BC·%s·" % c.tag):
            problems.append("tag missing from constraint name: %s" % c.name)
        if len(c.name.encode("utf-8")) > 63:
            problems.append("constraint name too long: %s" % c.name)
        if (c.bone, c.name) in tagged:
            problems.append("duplicate constraint: %s on %s" % (c.name, c.bone))
        tagged.add((c.bone, c.name))
    return problems
