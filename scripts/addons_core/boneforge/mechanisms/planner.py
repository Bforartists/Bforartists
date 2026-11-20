"""Mechanism records -> MechPlan (pure; no bpy).

Bone keys are "<record id>:<role>". build.py maps keys to real bone names
through the bones' tags, so renamed bones keep working. Constraint names are
"BC·<record id>·<role>". Every bone, constraint, driver and action carries the
id of the record that owns it: a part owns its MCH and DEF bones; a joint owns
its handle, the handle copy and the limits; a link owns its contributions.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from boneforge.autorig.components import BuildPlan, validate_plan
from boneforge.mechanisms import geometry, model

ROOT = "root"
COLLECTIONS = {"CTRL": "Mechanism Controls", "MCH": "Mechanism MCH", "DEF": "Mechanism DEF"}
STAGE_COPY, STAGE_FOLLOW, STAGE_LINK, STAGE_LIMIT = 0, 5, 10, 90


class PlanError(ValueError):
    """A record set that cannot be built; the message is shown to the rigger."""


@dataclass
class ActionRef:
    key: str


@dataclass
class ActionDef:
    key: str
    name: str
    tag: str
    bone: str                 # key of the bone whose channel is keyed
    channel: str              # "rotation_euler" | "location"
    index: int
    keys: list                # [(frame, value, interpolation, easing)]


@dataclass
class PoseDef:
    lock_location: tuple = (True, True, True)
    lock_rotation: tuple = (True, True, True)
    lock_scale: tuple = (True, True, True)
    hide: bool = True
    rotation_mode: str = "XYZ"


@dataclass
class MechPlan:
    build: BuildPlan = field(default_factory=BuildPlan)
    names: dict = field(default_factory=dict)        # bone key -> wanted name
    align_z: dict = field(default_factory=dict)      # bone key -> z for align_roll
    pose: dict = field(default_factory=dict)         # bone key -> PoseDef
    stage: dict = field(default_factory=dict)        # (bone key, constraint name) -> stage
    actions: list = field(default_factory=list)
    skipped: list = field(default_factory=list)      # [(record id, reason)]
    recipe: dict = field(default_factory=dict)       # mechanism id -> recipe used

    def bone(self, k):
        return next((b for b in self.build.bones if b.name == k), None)

    def constraints_on(self, k):
        return [c for c in self.build.constraints if c.bone == k]


def key(rid, role):
    return f"{rid}:{role}"


def cname(rid, role):
    return f"BC·{rid}·{role}"


def add_bone(plan, k, name, head, frame, size, parent, tag, role, deform=False, hide=True):
    y, z = frame
    plan.build.add_bone(name=k, head=tuple(head), tail=geometry.tail(head, y, size), parent=parent,
                        deform=deform, collection=COLLECTIONS[role], tag=tag)
    plan.names[k] = name
    plan.align_z[k] = z
    plan.pose[k] = PoseDef(hide=hide)
    return plan.pose[k]


def add_con(plan, bone_key, ctype, rid, role, stage, subtarget=None, **params):
    c = plan.build.add_constraint(bone=bone_key, type=ctype, name=cname(rid, role),
                                  subtarget=subtarget, params=params, tag=rid)
    plan.stage[(bone_key, c.name)] = stage
    return c


def add_widget(plan, bone_key, m):
    plan.build.add_widget(bone=bone_key, widget=m.handle_widget or model.DEFAULT_WIDGET[m.type],
                          color_group=m.handle_color or "special", scale=m.handle_size)


def joint_for_part(rig, pid):
    """The mechanism that moves part ``pid`` (Hinge, Slide, Telescope segment or Piston end)."""
    for m in rig.mechanisms:
        if m.type in ("HINGE", "SLIDE") and m.parts[:1] == [pid]:
            return m
        if m.type == "TELESCOPE" and pid in m.parts[1:]:
            return m
        if m.type == "PISTON" and pid in m.parts:
            return m
    return None


def driven_part(joint):
    return joint.parts[0]


def parent_key(rig, part):
    return key(part.parent, "DEF") if part.parent else ROOT


def _part_frame(rig, part):
    m = joint_for_part(rig, part.id)
    if m is None:
        return geometry.frame_for_slide((0.0, 0.0, 1.0))
    if m.type == "HINGE":
        return geometry.frame_for_hinge(m.axis)
    if m.type == "PISTON":
        other = rig.part(m.parts[1] if m.parts[0] == part.id else m.parts[0])
        return geometry.frame_toward(part.pivot, other.pivot)
    return geometry.frame_for_slide(m.axis)


def _plan_part(plan, rig, part):
    frame = _part_frame(rig, part)
    parent = parent_key(rig, part)
    mch, dfm = key(part.id, "MCH"), key(part.id, "DEF")
    add_bone(plan, mch, f"MCH-{part.name}", part.pivot, frame, part.size, parent, part.id, "MCH")
    add_bone(plan, dfm, f"DEF-{part.name}", part.pivot, frame, part.size, parent, part.id, "DEF", deform=True)
    add_con(plan, dfm, "COPY_TRANSFORMS", part.id, "def", STAGE_COPY, subtarget=mch,
            target_space="WORLD", owner_space="WORLD")


def _owned_parts(m):
    if m.type in ("HINGE", "SLIDE"):
        return m.parts[:1]
    if m.type == "TELESCOPE":
        return m.parts[1:]
    if m.type == "PISTON":
        return list(m.parts)
    return []


PART_COUNT = {"HINGE": lambda n: n == 1, "SLIDE": lambda n: n == 1,
              "TELESCOPE": lambda n: n >= 2, "PISTON": lambda n: n == 2}
PART_HINT = {"HINGE": "a Hinge moves exactly one part.", "SLIDE": "a Slide moves exactly one part.",
             "TELESCOPE": "a Telescope needs a base part and at least one segment.",
             "PISTON": "a Piston needs a cylinder part and a rod part."}


def check_records(rig):
    by_id = {p.id: p for p in rig.parts}
    for p in rig.parts:
        seen, cur = set(), p
        while cur.parent:
            if cur.id in seen:
                raise PlanError(f"Part '{p.name}' rides on itself.")
            seen.add(cur.id)
            cur = by_id.get(cur.parent)
            if cur is None:
                raise PlanError(f"Part '{p.name}' rides on a part that no longer exists.")
    owners = {}
    for m in rig.mechanisms:
        need = PART_COUNT.get(m.type)
        if need is not None and not need(len(m.parts)):
            raise PlanError(f"'{m.name}': {PART_HINT[m.type]}")
        if m.type in ("GEAR", "FOLLOW") and not (m.source and m.target):
            raise PlanError(f"'{m.name}': pick both the source joint and the target joint.")
        for pid in m.parts:
            if pid not in by_id:
                raise PlanError(f"'{m.name}' uses a part that no longer exists.")
        for pid in _owned_parts(m):
            if pid in owners:
                raise PlanError(f"Part '{by_id[pid].name}' already moves with '{owners[pid]}'.")
            owners[pid] = m.name
        for ref in (m.source, m.target):
            if ref and rig.mech(ref) is None:
                raise PlanError(f"'{m.name}' links to a joint that no longer exists.")
        if m.type == "PISTON":                    # checked here: part frames aim one end at the other
            a, b = by_id[m.parts[0]], by_id[m.parts[1]]
            if geometry.length(geometry.sub(a.pivot, b.pivot)) < 1e-6:
                raise PlanError(f"'{m.name}': the cylinder and rod pivots are at the same spot.")


def ordered_parts(rig):
    """Parents before children, otherwise record order."""
    done, out = set(), []

    def visit(p):
        if p.id in done:
            return
        if p.parent:
            visit(rig.part(p.parent))
        done.add(p.id)
        out.append(p)

    for p in rig.parts:
        visit(p)
    return out


def skipped(rig):
    """{record id: reason} for parts and mechanisms that cannot be built right now."""
    out = {p.id: f"Part '{p.name}' is missing" for p in rig.parts if p.id in rig.missing}
    changed = True
    while changed:
        changed = False
        for p in rig.parts:
            if p.id not in out and p.parent in out:
                out[p.id] = out[p.parent]
                changed = True
        for m in rig.mechanisms:
            if m.id in out:
                continue
            hit = next((d for d in list(m.parts) + [m.source, m.target] if d and d in out), None)
            if hit:
                out[m.id] = out[hit]
                changed = True
    return out


def _edges(rig):
    """(from part id, to part id, link name or "") for every motion dependency."""
    edges = [(p.parent, p.id, "") for p in rig.parts if p.parent]
    for m in rig.mechanisms:
        if m.type in ("GEAR", "FOLLOW"):
            src, tgt = rig.mech(m.source), rig.mech(m.target)
            if src and tgt and src.parts and tgt.parts:
                edges.append((driven_part(src), driven_part(tgt), m.name))
        elif m.type == "PISTON" and len(m.parts) == 2:
            a, b = rig.part(m.parts[0]), rig.part(m.parts[1])
            for me, other in ((a, b), (b, a)):
                if other.parent:
                    edges.append((other.parent, me.id, m.name))
        elif m.type == "TELESCOPE":
            for seg in m.parts[1:]:
                edges.append((m.parts[0], seg, m.name))
    return edges


def _label(rig, part):
    m = joint_for_part(rig, part.id)
    return m.name if m is not None and m.type in ("HINGE", "SLIDE") else part.name


def find_loop(rig):
    """A plain-words description of the first dependency loop, or None."""
    nxt_of = {}
    for a, b, lab in _edges(rig):
        nxt_of.setdefault(a, []).append((b, lab))
    state = {}

    def dfs(n, path, labels):
        state[n] = 1
        for nxt, lab in nxt_of.get(n, ()):
            if state.get(nxt) == 1:
                i = path.index(nxt)
                return path[i:] + [nxt], labels[i:] + [lab]
            if nxt not in state:
                found = dfs(nxt, path + [nxt], labels + [lab])
                if found:
                    return found
        state[n] = 2
        return None

    for p in rig.parts:
        if p.id in state:
            continue
        found = dfs(p.id, [p.id], [""])
        if found:
            nodes, labs = found
            words = [_label(rig, rig.part(nodes[0]))]
            for node, lab in zip(nodes[1:], labs[1:]):
                if lab:
                    words.append(lab)
                words.append(_label(rig, rig.part(node)))
            return " → ".join(words) + " would loop."
    return None


def _sort(plan):
    """BoneCraft's constraints in fixed order per bone: copy, follow, links, limits."""
    order = {id(c): i for i, c in enumerate(plan.build.constraints)}
    plan.build.constraints.sort(key=lambda c: (c.bone, plan.stage.get((c.bone, c.name), 50), order[id(c)]))


def plan_rig(rig):
    from boneforge.mechanisms import recipes
    check_records(rig)
    loop = find_loop(rig)
    if loop:
        raise PlanError(loop)
    plan = MechPlan()
    plan.build.add_bone(name=ROOT, head=(0.0, 0.0, 0.0), tail=(0.0, 0.3, 0.0), collection=COLLECTIONS["CTRL"])
    plan.names[ROOT] = ROOT
    skip = skipped(rig)
    plan.skipped = sorted(skip.items())
    try:
        for part in ordered_parts(rig):
            if part.id not in skip:
                _plan_part(plan, rig, part)
        for m in rig.mechanisms:
            if m.id not in skip:
                recipes.RECIPES[m.type](plan, m, rig)
        for post in recipes.POST:
            post(plan, rig, skip)
    except geometry.GeometryError as exc:
        raise PlanError(f"An axis or pivot is degenerate: {exc}") from exc
    _sort(plan)
    problems = validate_plan(plan.build)
    if problems:
        raise PlanError("; ".join(problems))
    return plan
