# bonecraft/boneforge/mechanisms/build.py
"""Apply a Mechanisms plan to an armature in place; rebuild, detach or delete one record.

Bones are found by tag (pose-bone properties ``bc_mech_id`` / ``bc_mech_role``),
so a renamed bone keeps working. Only what is tagged with the records being
built is created, changed or removed: the rigger's own bones, constraints and
drivers are never touched. Before anything changes, a built record is checked
against the snapshot of what BoneCraft last wrote; a record edited by hand, a
channel driven by hand, or a reshaped curve the record wants to replace holds
the record until Keep mine or Restore. Every change is journalled, so a failed
build puts every old value back. Generated actions are replaced, never edited
in place, and a curve the rigger reshaped is never overwritten.
"""
import contextlib
import json
import math
import re

import bpy
from mathutils import Matrix, Vector

from boneforge.core import rig_ops
from boneforge.mechanisms import model, planner, records
from boneforge.mechanisms.planner import ROOT, ActionRef

PREFIX = "BC·"
PALETTE = {"fk": "THEME03", "ik": "THEME01", "root": "THEME09", "special": "THEME09",
           "deform": "THEME10", "face": "THEME07"}
ROLE_OF = {v: k for k, v in planner.COLLECTIONS.items()}
_MODE = {"POSE": "POSE", "EDIT_ARMATURE": "EDIT", "EDIT_MESH": "EDIT", "PAINT_WEIGHT": "WEIGHT_PAINT"}
_CHANNELS = (("rotation_euler", 0), ("location", 1))


class BuildError(RuntimeError):
    """A build could not finish; every change it made has been put back."""


def tag_of(con_name):
    bits = con_name.split("·")
    return bits[1] if con_name.startswith(PREFIX) and len(bits) >= 3 else None


def _split(bone_key):
    return ("root", "ROOT") if bone_key == ROOT else tuple(bone_key.split(":", 1))


def bone_tags(arm_obj):
    if arm_obj.pose is None:                              # a new armature object has no pose yet
        return {}
    return {(pb.get("bc_mech_id"), pb.get("bc_mech_role")): pb.name
            for pb in arm_obj.pose.bones if pb.get("bc_mech_id")}


def resolve_names(arm_obj, plan):
    tags = bone_tags(arm_obj)
    taken = {b.name for b in arm_obj.data.bones}
    names = {}
    for b in plan.build.bones:
        found = tags.get(_split(b.name))
        if found is None and b.name == ROOT and ROOT in taken:
            found = ROOT                                      # adopt an existing root bone
        if found is None:
            found = model.unique_name(plan.names[b.name], taken)
            taken.add(found)
        names[b.name] = found
    return names


def expand(rig, ids):
    ids = set(ids)
    out = set(ids)
    for m in rig.mechanisms:
        if m.id in ids:
            out.update(m.parts)
            for ref in (m.source, m.target):
                joint = rig.mech(ref)
                if joint is not None:
                    out.update(joint.parts[:1])
        if ids.intersection(m.parts):
            out.add(m.id)
    return out


@contextlib.contextmanager
def _object_mode():
    vl = bpy.context.view_layer
    active, mode = vl.objects.active, bpy.context.mode
    if active is not None and active.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    try:
        yield
    finally:
        vl.objects.active = active
        want = _MODE.get(mode, 'OBJECT')
        if active is not None and active.mode != want:
            try:
                bpy.ops.object.mode_set(mode=want)
            except RuntimeError:
                pass


@contextlib.contextmanager
def _edit(arm_obj):
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    try:
        yield arm_obj.data.edit_bones
    finally:
        bpy.ops.object.mode_set(mode='OBJECT')


def _copy(v):
    """A journal copy of an old value. Data-blocks (actions, widget objects) are kept by reference."""
    if v is None or isinstance(v, bpy.types.ID):
        return v
    if hasattr(v, "copy"):
        return v.copy()
    if hasattr(v, "__len__") and not isinstance(v, str):
        return tuple(v)
    return v


def _same(cur, v):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        if hasattr(cur, "__len__") and not isinstance(cur, str):
            return tuple(cur) == tuple(v)
        return cur == v
    return cur is not None and abs(float(cur) - float(v)) < 1e-4


# -- journal ---------------------------------------------------------------

class _Journal:
    """Old values of everything a build changes, so a failed build can put each one back."""

    def __init__(self, arm_obj):
        self.arm = arm_obj
        self.pose = []           # undone first, newest first
        self.edit = []           # undone in one Edit Mode pass
        self.new_actions = []
        self.old_actions = []
        self.old_cons = []       # (bone, name) of constraints set aside by a type change
        self.created = []        # data-blocks this build created: ("collection", name) / ("object", ID) / ("widgets", ID)
        self.tagged = []         # existing bone collections this build tagged with a role

    def _owner(self, where):
        pb = self.arm.pose.bones.get(where[1])
        if pb is None:
            return None
        if where[0] == "pb":
            return pb
        if where[0] == "color":
            return pb.color
        return pb.constraints.get(where[2])

    def set(self, owner, attr, value, where):
        cur = getattr(owner, attr)
        changed = (cur != value) if hasattr(value, "bl_rna") else not _same(cur, value)
        if changed:
            self.pose.append(("attr", where, attr, _copy(cur)))
            setattr(owner, attr, value)

    def prop(self, pb, key, value):
        if pb.get(key) != value:
            self.pose.append(("prop", ("pb", pb.name), key, pb.get(key)))
            pb[key] = value

    def undo(self):
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        for kind, where, key, old in reversed(self.pose):
            owner = self._owner(where) if kind in ("attr", "prop") else None
            if kind == "attr" and owner is not None:
                setattr(owner, key, old)
            elif kind == "prop" and owner is not None:
                if old is None:
                    owner.pop(key, None)
                else:
                    owner[key] = old
            elif kind == "newcon":
                pb = self.arm.pose.bones.get(where[1])
                con = pb.constraints.get(key) if pb else None
                if con is not None:
                    pb.constraints.remove(con)
            elif kind == "rename":
                pb = self.arm.pose.bones.get(where[1])
                con = pb.constraints.get(key) if pb else None
                if con is not None:
                    con.name = old
            elif kind == "assign":
                coll = next((c for c in self.arm.data.collections_all if c.get("bc_mech_role") == key), None)
                bone = self.arm.data.bones.get(where[1])
                if coll is not None and bone is not None:
                    coll.unassign(bone)
            elif kind == "order":
                pb = self.arm.pose.bones.get(where[1])
                if pb is not None:
                    _reorder(pb, old)
            elif kind == "driver":
                _undo_driver(self.arm, where, key, old)
        if self.edit:
            with _edit(self.arm) as ebs:
                for item in reversed(self.edit):
                    eb = ebs.get(item[1])
                    if eb is None:
                        continue
                    if item[0] == "new":
                        ebs.remove(eb)
                    else:
                        _, _, head, tail, roll, parent, deform, connect = item
                        eb.head, eb.tail, eb.roll = head, tail, roll
                        eb.parent = ebs.get(parent) if parent else None
                        eb.use_deform, eb.use_connect = deform, connect
        for act in self.new_actions:
            rig_ops.release_action(act)
        for name in self.tagged:
            coll = self.arm.data.collections_all.get(name)
            if coll is not None:
                coll.pop("bc_mech_role", None)
        for kind, ref in reversed(self.created):
            if kind == "collection":
                coll = self.arm.data.collections_all.get(ref)
                if coll is not None:
                    self.arm.data.collections.remove(coll)
            elif kind == "object":
                mesh = ref.data
                bpy.data.objects.remove(ref)
                if mesh is not None and mesh.users == 0:
                    bpy.data.meshes.remove(mesh)
            elif kind == "widgets" and not ref.objects:
                bpy.data.collections.remove(ref)

    def commit(self):
        for bone, name in self.old_cons:
            pb = self.arm.pose.bones.get(bone)
            if pb is not None and pb.constraints.get(name) is not None:
                pb.constraints.remove(pb.constraints[name])
        for act in self.old_actions:
            rig_ops.release_action(act)
        for act in self.new_actions:
            if act.users and act.get("bc_name"):
                act.name = act["bc_name"]                 # take the plain name once the old one is gone


# -- checks before anything changes -------------------------------------------

def snapshot(plan, rid):
    """What BoneCraft writes for record ``rid``: its bones, and {"bone key|constraint": {setting: value}}."""
    out = {"@bones": sorted(b.name for b in plan.build.bones if b.tag == rid)}
    for cd in plan.build.constraints:
        if cd.tag == rid:
            vals = {k: v for k, v in cd.params.items() if not isinstance(v, ActionRef)}
            if cd.subtarget:
                vals["@subtarget"] = cd.subtarget
            out[f"{cd.bone}|{cd.name}"] = vals
    return out


def changed_by_hand(arm_obj, snap):
    """[(what, field)] where the rig no longer matches what BoneCraft last wrote."""
    tags = bone_tags(arm_obj)
    out = []
    if arm_obj.pose is None:
        return out
    for where, vals in (snap or {}).items():
        if where == "@bones":
            out += [(k, "bone removed") for k in vals if k != ROOT and _split(k) not in tags]
            continue
        key, cname = where.split("|", 1)
        pb = arm_obj.pose.bones.get(tags.get(_split(key), ""))
        if pb is None:
            continue
        con = pb.constraints.get(cname)
        if con is None:
            out.append((cname, "removed or renamed"))
            continue
        for k, v in vals.items():
            if k == "@subtarget":
                if getattr(con, "subtarget", "") != tags.get(_split(v)):
                    out.append((cname, "target"))
            elif not _same(getattr(con, k, None), v):
                out.append((cname, k))
    return out


def _describe(diffs):
    return "; ".join(f"{name.split('·', 2)[-1]}: {field}" for name, field in diffs) + " (changed by hand)"


def _fcurve(arm_obj, path, index):
    ad = arm_obj.animation_data
    return next((f for f in (ad.drivers if ad else ()) if f.data_path == path and f.array_index == index), None)


def _ours(fc):
    vs = fc.driver.variables
    return len(vs) > 0 and all(v.name.startswith("bc") for v in vs)


def _driver_conflicts(arm_obj, plan, names, ids):
    """{record id: reason} for planned gear drivers whose channel the rigger drives by hand."""
    out = {}
    for d in plan.build.drivers:
        if d.tag in ids:
            fc = _fcurve(arm_obj, f'pose.bones["{names[d.bone]}"].{d.data_path_suffix}', d.index)
            if fc is not None and not _ours(fc):
                out[d.tag] = f"{names[d.bone]} {d.data_path_suffix} is driven by hand"
    return out


def _curve(act):
    try:
        fc = act.layers[0].strips[0].channelbag(act.slots[0]).fcurves[0]
    except (IndexError, AttributeError):
        return None
    return [[round(k.co[0], 4), round(k.co[1], 6)] for k in fc.keyframe_points]


def _made(ad):
    return [[round(f, 4), round(v, 6)] for f, v, _, _ in ad.keys]


def _curve_state(con, ad):
    """"keep", "pinned", "reshaped" (the rigger's curve and the record now differ) or "new"."""
    act = con.action if con is not None else None
    if act is None or act.get("bc_mech_id") != ad.tag or act.get("bc_key") != ad.key or act.get("bc_regen"):
        return "new"
    if act.get("bc_pinned"):
        return "pinned"
    made = json.loads(act.get("bc_keys", "null"))
    if made == _made(ad) and act.get("bc_where") == f"{ad.bone}|{ad.channel}|{ad.index}":
        return "keep"                                 # (shared or not: actions are never edited in place)
    return "reshaped" if _curve(act) != made else "new"


def _curve_conflicts(arm_obj, plan, names, ids):
    out = {}
    if arm_obj.pose is None:
        return out
    for cd in plan.build.constraints:
        ref = cd.params.get("action")
        if cd.tag in ids and isinstance(ref, ActionRef):
            pb = arm_obj.pose.bones.get(names[cd.bone])
            con = pb.constraints.get(cd.name) if pb else None
            ad = next(a for a in plan.actions if a.key == ref.key)
            if _curve_state(con, ad) == "reshaped":
                out[cd.tag] = f"{cd.name.split('·', 2)[-1]}: curve reshaped by hand"
    return out


# -- applying ------------------------------------------------------------------

def _differs(arm, b, names, plan):
    bone = arm.bones.get(names[b.name])
    if bone is None:
        return True
    parent = names.get(b.parent) if b.parent else None
    return ((bone.head_local - Vector(b.head)).length > 1e-5
            or (bone.tail_local - Vector(b.tail)).length > 1e-5
            or (bone.z_axis - Vector(plan.align_z[b.name])).length > 1e-4
            or (bone.parent.name if bone.parent else None) != parent
            or bone.use_deform != b.deform)


def _bones(arm_obj, plan, names, ids, j):
    arm = arm_obj.data
    todo = [b for b in plan.build.bones
            if (b.name == ROOT and names[ROOT] not in arm.bones)
            or (b.name != ROOT and b.tag in ids and _differs(arm, b, names, plan))]
    if not todo:
        return
    with _edit(arm_obj) as ebs:
        for b in todo:
            eb = ebs.get(names[b.name])
            if eb is None:
                eb = ebs.new(names[b.name])
                j.edit.append(("new", eb.name))
            else:
                j.edit.append(("geom", eb.name, eb.head.copy(), eb.tail.copy(), eb.roll,
                               eb.parent.name if eb.parent else None, eb.use_deform, eb.use_connect))
            eb.head, eb.tail = b.head, b.tail
            if b.name != ROOT:
                eb.align_roll(Vector(plan.align_z[b.name]))
            eb.use_deform, eb.use_connect = b.deform, False
        for b in todo:
            if b.name != ROOT:
                ebs[names[b.name]].parent = ebs.get(names[b.parent]) if b.parent else None


def _collection(arm, role, j):
    for c in arm.collections_all:
        if c.get("bc_mech_role") == role:
            return c
    c = arm.collections_all.get(planner.COLLECTIONS[role])
    if c is None:
        c = arm.collections.new(planner.COLLECTIONS[role])
        j.created.append(("collection", c.name))
    else:
        j.tagged.append(c.name)
    c["bc_mech_role"] = role
    return c


def _widget(widget_id, j):
    """The widget object, journalling it (and the widget collection) if this build creates them."""
    from boneforge.weights import widgets
    had_obj = bpy.data.objects.get("WGT-" + widget_id)
    had_coll = bpy.data.collections.get(widgets.WIDGET_COLLECTION)
    shape = widgets.ensure_widget_object(widget_id)
    if shape is not None and had_obj is None:
        j.created.append(("object", shape))
        coll = bpy.data.collections.get(widgets.WIDGET_COLLECTION)
        if had_coll is None and coll is not None:
            j.created.insert(0, ("widgets", coll))         # removed last, once it is empty
    return shape


def _pose(arm_obj, plan, names, ids, j):
    arm = arm_obj.data
    for b in plan.build.bones:
        if b.tag not in ids and b.name != ROOT:
            continue
        pb = arm_obj.pose.bones[names[b.name]]
        rid, role = _split(b.name)
        j.prop(pb, "bc_mech_id", rid)
        j.prop(pb, "bc_mech_role", role)
        if b.name == ROOT:
            continue
        pd = plan.pose[b.name]
        for attr in ("rotation_mode", "lock_location", "lock_rotation", "lock_scale", "hide"):
            j.set(pb, attr, getattr(pd, attr), ("pb", pb.name))
        role = ROLE_OF[b.collection]
        coll = _collection(arm, role, j)
        if pb.name not in coll.bones:
            coll.assign(pb)
            j.pose.append(("assign", ("pb", pb.name), role, None))
    for w in plan.build.widgets:
        if plan.bone(w.bone).tag in ids:
            pb = arm_obj.pose.bones[names[w.bone]]
            shape = _widget(w.widget, j)
            if shape is not None:
                j.set(pb, "custom_shape", shape, ("pb", pb.name))
                j.set(pb, "custom_shape_scale_xyz", (w.scale,) * 3, ("pb", pb.name))
            j.set(pb.color, "palette", PALETTE.get(w.color_group or "special", "THEME09"), ("color", pb.name))


def _set_action(arm_obj, plan, names, con, akey, j, where):
    ad = next(a for a in plan.actions if a.key == akey)
    if _curve_state(con, ad) in ("keep", "pinned"):
        return                                        # unchanged, or the rigger's reshaped / pinned curve
    path = f'pose.bones["{names[ad.bone]}"].{ad.channel}'
    act, slot = rig_ops.ensure_action(ad.name + " (new)", ad.tag, ad.key, path, ad.index, ad.keys)
    act["bc_name"], act["bc_keys"] = ad.name, json.dumps(_made(ad))
    act["bc_where"] = f"{ad.bone}|{ad.channel}|{ad.index}"
    j.new_actions.append(act)
    if con.action is not None:
        j.old_actions.append(con.action)
    j.set(con, "action", act, where)
    j.set(con, "action_slot", slot, where)


def _reorder(pb, want):
    want = [n for n in want if n in pb.constraints]
    for i, name in enumerate(want):
        cur = pb.constraints.find(name)
        if cur != i:
            pb.constraints.move(cur, i)


def _constraints(arm_obj, plan, names, ids, j):
    touched = []
    for cd in plan.build.constraints:
        if cd.tag not in ids:
            continue
        pb = arm_obj.pose.bones[names[cd.bone]]
        if cd.bone not in touched:
            touched.append(cd.bone)
            j.pose.append(("order", ("pb", pb.name), None, [c.name for c in pb.constraints]))
        con = pb.constraints.get(cd.name)
        if con is not None and con.type != cd.type:          # a type change: set the old one aside
            old_name = con.name
            con.name = cd.name + " (old)"
            j.pose.append(("rename", ("pb", pb.name), con.name, old_name))
            j.old_cons.append((pb.name, con.name))
            con = None
        if con is None:
            con = pb.constraints.new(cd.type)
            con.name = cd.name
            j.pose.append(("newcon", ("pb", pb.name), con.name, None))
        where = ("con", pb.name, con.name)
        if hasattr(con, "target"):
            j.set(con, "target", arm_obj, where)
        if cd.subtarget:
            j.set(con, "subtarget", names[cd.subtarget], where)
        for k, v in cd.params.items():
            if isinstance(v, ActionRef):
                _set_action(arm_obj, plan, names, con, v.key, j, where)
            else:
                j.set(con, k, v, where)               # an unknown setting is a plan bug: let it raise
    for key in touched:
        _reorder(arm_obj.pose.bones[names[key]], [c.name for c in plan.constraints_on(key)])


def _driver_state(arm_obj, path, index):
    fc = _fcurve(arm_obj, path, index)
    if fc is None:
        return None
    return (fc.driver.expression, [dict(name=v.name, id=v.targets[0].id, bone=v.targets[0].bone_target,
                                        transform_type=v.targets[0].transform_type,
                                        space=v.targets[0].transform_space) for v in fc.driver.variables])


def _drivers(arm_obj, plan, names, ids, j):
    want = {(f'pose.bones["{names[d.bone]}"].{d.data_path_suffix}', d.index): d
            for d in plan.build.drivers if d.tag in ids}
    for b in plan.build.bones:
        if b.tag not in ids or not b.name.endswith(":MCH"):
            continue
        pb = arm_obj.pose.bones[names[b.name]]
        for suffix, index in _CHANNELS:
            path = f'pose.bones["{pb.name}"].{suffix}'
            fc, d = _fcurve(arm_obj, path, index), want.get((path, index))
            if fc is not None and not _ours(fc):
                continue                                  # the rigger's driver (a conflict was held earlier)
            old = _driver_state(arm_obj, path, index)
            if d is None and fc is None:
                continue
            j.pose.append(("driver", ("pb", pb.name), (path, index, suffix), (old, getattr(pb, suffix)[index])))
            if d is None:
                arm_obj.driver_remove(path, index)
                getattr(pb, suffix)[index] = 0.0          # the MCH basis is used only by gear drivers
            else:
                variables = [dict(v, id=arm_obj, bone=names[v["bone"]]) for v in d.variables]
                rig_ops.add_driver(arm_obj, path, index, d.expression, variables)


def _undo_driver(arm_obj, where, key, old):
    (path, index, suffix), (state, basis) = key, old
    arm_obj.driver_remove(path, index)
    if state is not None:
        rig_ops.add_driver(arm_obj, path, index, state[0], state[1])
    pb = arm_obj.pose.bones.get(where[1])
    if pb is not None:
        getattr(pb, suffix)[index] = basis


def _prune(arm_obj, plan, names, ids, keep):
    """Remove what records in ``ids`` no longer want. Runs only after every change succeeded."""
    want = {(names[c.bone], c.name) for c in plan.build.constraints if c.tag in ids}
    for pb in arm_obj.pose.bones:
        for con in list(pb.constraints):
            if tag_of(con.name) in ids and (pb.name, con.name) not in want and con.name not in keep:
                act = con.action if con.type == 'ACTION' else None
                pb.constraints.remove(con)
                rig_ops.release_action(act)
    planned = set(names.values())
    stale = [pb for pb in arm_obj.pose.bones if pb.get("bc_mech_id") in ids and pb.name not in planned]
    for pb in stale:
        for suffix, index in _CHANNELS:
            fc = _fcurve(arm_obj, f'pose.bones["{pb.name}"].{suffix}', index)
            if fc is not None and _ours(fc):
                arm_obj.driver_remove(fc.data_path, index)
    if stale:
        gone = [pb.name for pb in stale]
        with _edit(arm_obj) as ebs:
            for n in gone:
                if n in ebs:
                    ebs.remove(ebs[n])


def _bone_keys(plan, rid):
    """Keys of every bone record ``rid`` plans a bone, constraint, driver or action on."""
    keys = set()
    for b in plan.build.bones:
        if b.tag == rid:
            keys.update(k for k in (b.name, b.parent) if k)
    for cd in plan.build.constraints:
        if cd.tag == rid:
            keys.update(k for k in (cd.bone, cd.subtarget) if k)
    for d in plan.build.drivers:
        if d.tag == rid:
            keys.add(d.bone)
            keys.update(v["bone"] for v in d.variables)
    keys.update(a.bone for a in plan.actions if a.tag == rid)
    return keys


def _carry_holds(arm_obj, plan, ids, held):
    """Hold every record in ``ids`` that plans items on the bones of a held record, until stable."""
    held = dict(held)
    while True:
        more = {}
        for rid in ids:
            if rid in held:
                continue
            for k in sorted(_bone_keys(plan, rid)):
                owner = _split(k)[0] if k != ROOT else None
                if owner in held and owner != rid:
                    pg = records.find(arm_obj.data, owner)
                    more[rid] = f"uses {pg.name if pg is not None else owner} (changed by hand)"
                    break
        if not more:
            return held
        held.update(more)


def apply(arm_obj, plan, ids, check=None, keep=()):
    """Build everything tagged with ``ids`` from ``plan``. Returns {held record id: reason}.

    ``check`` maps record id -> the snapshot BoneCraft last wrote for it. Records
    edited by hand, gears whose channel is driven by hand, and records that would
    replace a reshaped curve are held before anything changes.
    """
    names = resolve_names(arm_obj, plan)
    held = {}
    for rid, snap in (check or {}).items():
        diffs = changed_by_hand(arm_obj, snap)
        if diffs:
            held[rid] = _describe(diffs)
    held.update({k: v for k, v in _driver_conflicts(arm_obj, plan, names, ids).items() if k not in held})
    held.update({k: v for k, v in _curve_conflicts(arm_obj, plan, names, ids).items() if k not in held})
    held = _carry_holds(arm_obj, plan, ids, held)
    ids = set(ids) - set(held)
    if not ids:
        return held                                   # everything is held: nothing may change, not even the root
    j = _Journal(arm_obj)
    with _object_mode():
        try:
            _bones(arm_obj, plan, names, ids, j)
            _pose(arm_obj, plan, names, ids, j)
            _constraints(arm_obj, plan, names, ids, j)
            _drivers(arm_obj, plan, names, ids, j)
        except Exception as exc:
            j.undo()
            raise BuildError(f"The build stopped and every change was put back: {exc}") from exc
        j.commit()
        _prune(arm_obj, plan, names, ids, set(keep))
    return held


def rebuild(arm_obj, ids=None, force=False):
    """Plan the whole rig, then build only ``ids`` (default: every record)."""
    rig = records.to_model(arm_obj)
    try:
        plan = planner.plan_rig(rig)
    except planner.PlanError as exc:
        records.set_error(arm_obj.data, str(exc))
        raise
    skipped = dict(plan.skipped)
    want = expand(rig, rig.ids() if ids is None else ids) - set(skipped)
    check = {} if force else {rid: snap for rid in want
                              if (snap := records.snapshot_of(records.find(arm_obj.data, rid))) is not None}
    keep = {planner.cname(*k.split(":", 1)) for k in skipped if ":" in k}
    objects = keep_objects(arm_obj)
    held = apply(arm_obj, plan, want, check=check, keep=keep)
    done = want - set(held)
    records.set_error(arm_obj.data, "")
    records.mark(arm_obj.data, built=done, skipped=skipped, held=held,
                 snapshots={rid: snapshot(plan, rid) for rid in done})
    restore_objects(objects)
    return plan, held


def _bone_parent_rest(ob):
    """What Blender multiplies a bone-parented object's parent-inverse by, with the rig at rest."""
    arm, bone = ob.parent, ob.parent.data.bones.get(ob.parent_bone)
    if bone is None:
        return None
    return arm.matrix_world @ bone.matrix_local @ Matrix.Translation((0.0, bone.length, 0.0))


def keep_objects(arm_obj):
    """Rest-pose world matrices of the objects parented to ``arm_obj``'s bones (object parts), to put back
    after a build: a joint re-orients the part's DEF bone, and a bone-parented object would turn with it.
    The rest pose, not the current one: the rig may be posed when the build starts and differently posed
    when it ends (a new Sequence step with its slider already up), and a world matrix taken from a pose
    would bake that pose into the object."""
    out = {}
    for ob in bpy.data.objects:
        if ob.parent == arm_obj and ob.parent_type == 'BONE':
            rest = _bone_parent_rest(ob)
            if rest is not None:
                out[ob] = rest @ ob.matrix_parent_inverse @ ob.matrix_basis
    return out


def restore_objects(objects):
    for ob, rest_world in objects.items():
        rest = _bone_parent_rest(ob)
        if rest is not None:
            ob.matrix_parent_inverse = rest.inverted() @ rest_world @ ob.matrix_basis.inverted()


def _actions_of(arm_obj, rid):
    return [c.action for pb in arm_obj.pose.bones for c in pb.constraints
            if tag_of(c.name) == rid and c.type == 'ACTION' and c.action is not None]


def restore(arm_obj, rid):
    """Throw away hand edits (reshaped curves included) and rebuild from the record."""
    acts = _actions_of(arm_obj, rid)
    pinned = [act for act in acts if act.get("bc_pinned")]
    for act in acts:
        act.pop("bc_pinned", None)
        act["bc_regen"] = True                            # regenerate even a reshaped curve
    try:
        return rebuild(arm_obj, {rid}, force=True)
    except Exception:
        for act in acts:                                  # a failed Restore changes nothing: no later rebuild may
            act.pop("bc_regen", None)                     # silently regenerate the rigger's curve (spec §8)
        for act in pinned:
            act["bc_pinned"] = True
        raise


def _read_back(m, role, con):
    """Record fields recovered from a hand-edited constraint, or {} if this role cannot be read back."""
    deg = math.degrees
    if m.type == "HINGE" and role in ("limit", "handle_limit"):
        return {"min": deg(con.min_x), "max": deg(con.max_x)}
    if m.type == "SLIDE" and role in ("limit", "handle_limit"):
        return {"min": con.min_y, "max": con.max_y}
    if m.type == "TELESCOPE" and role == "handle_limit":
        return {"length": con.max_y}
    if m.type == "GEAR" and role == "gear":
        k = con.to_max_y / m.pinion_radius if m.gear_kind == "RACK" else con.to_max_x_rot
        base = -1.0 if m.gear_kind == "GEAR" else 1.0
        return {"ratio": abs(k), "teeth_source": 0, "teeth_target": 0, "reverse": k * base < 0}
    if m.type == "FOLLOW" and role == "follow" and con.type == 'TRANSFORM':
        sax = "x_rot" if con.map_from == 'ROTATION' else "y"
        tax = "x_rot" if con.map_to == 'ROTATION' else "y"
        cs = deg if sax == "x_rot" else float
        ct = deg if tax == "x_rot" else float
        return {"source_range": (cs(getattr(con, f"from_min_{sax}")), cs(getattr(con, f"from_max_{sax}"))),
                "target_range": (ct(getattr(con, f"to_min_{tax}")), ct(getattr(con, f"to_max_{tax}")))}
    return {}


def keep_mine(arm_obj, rid):
    """Copy hand-edited values into the record and pin reshaped curves; refuse what cannot be kept."""
    rig = records.to_model(arm_obj)
    m = rig.mech(rid)
    pg = records.find(arm_obj.data, rid)
    snap = records.snapshot_of(pg) or {}
    diffs = changed_by_hand(arm_obj, snap)
    tags = bone_tags(arm_obj)
    where = {w.split("|", 1)[1]: w.split("|", 1)[0] for w in snap if w != "@bones"}
    updates, refused = {}, []
    for cname in dict.fromkeys(name for name, _ in diffs):
        pb = arm_obj.pose.bones.get(tags.get(_split(where.get(cname, "")), "")) if cname in where else None
        con = pb.constraints.get(cname) if pb is not None else None
        got = _read_back(m, cname.split("·", 2)[2], con) if (m is not None and con is not None) else {}
        if got:
            updates.update(got)
        else:
            refused.append(cname)
    if refused:
        raise BuildError("Keep mine cannot copy " + ", ".join(refused) + " into the record; use Restore or Detach.")
    for act in _actions_of(arm_obj, rid):
        act["bc_pinned"] = True                           # the rigger's reshaped curve stays as it is
    with records.quiet():
        for k, v in updates.items():
            setattr(pg, k, v)
    return rebuild(arm_obj, {rid}, force=True)


def _refuse_if_used(rig, rid, verb):
    users = [m.name for m in rig.mechanisms if m.id != rid and (rid in m.parts or rid in (m.source, m.target))]
    users += [p.name for p in rig.parts if p.parent == rid]
    users += [s.name for s in rig.sequences if s.id != rid and any(st.target == rid for st in s.steps)]
    if users:
        raise BuildError(f"Used by {', '.join(users)}; {verb} or change those first.")


def detach(arm_obj, rid):
    """Forget record ``rid`` but keep its bones, constraints, actions and drivers as the rigger's own."""
    pg = records.find(arm_obj.data, rid)
    if pg is None:
        raise BuildError("That record no longer exists.")
    rig = records.to_model(arm_obj)
    _refuse_if_used(rig, rid, "detach")
    plan = planner.plan_rig(rig)
    names = resolve_names(arm_obj, plan)
    label = pg.name
    for pb in arm_obj.pose.bones:
        for con in pb.constraints:
            if tag_of(con.name) == rid:
                if con.type == 'ACTION' and con.action is not None:
                    for k in ("bc_mech_id", "bc_key", "bc_keys", "bc_where", "bc_name", "bc_pinned"):
                        con.action.pop(k, None)
                con.name = f"{con.name.split('·', 2)[2]} ({label})"[:60]
        if pb.get("bc_mech_id") == rid:
            del pb["bc_mech_id"]
            del pb["bc_mech_role"]
    m = rig.mech(rid)
    if m is not None and plan.recipe.get(rid) == "DRIVER":
        part = rig.mech(m.target).parts[0]
        pb = arm_obj.pose.bones[names[planner.key(part, "MCH")]]
        for suffix, index in _CHANNELS:
            fc = _fcurve(arm_obj, f'pose.bones["{pb.name}"].{suffix}', index)
            if fc is not None and _ours(fc):                       # the driver becomes the rigger's
                for v in fc.driver.variables:
                    v.name = "dv" + v.name[2:]
                fc.driver.expression = re.sub(r"\bbc(\d+)\b", r"dv\1", fc.driver.expression)
    records.remove(arm_obj.data, rid)


def delete(arm_obj, rid):
    """Remove record ``rid`` and everything tagged with it."""
    rig = records.to_model(arm_obj)
    _refuse_if_used(rig, rid, "delete")
    ids = expand(rig, {rid})
    old = rig.part(rid) or rig.mech(rid) or rig.seq(rid)
    pg = records.find(arm_obj.data, rid)
    coll = next((c for c in (arm_obj.data.bonecraft_mech.parts, arm_obj.data.bonecraft_mech.mechanisms,
                             arm_obj.data.bonecraft_mech.sequences) if any(x.id == rid for x in c)), None)
    saved = (pg.built, pg.snapshot, pg.state, pg.message) if pg is not None else None
    had, ob = records._ref(pg)                            # a part's object reference ("set but None" included)
    index = next((i for i, x in enumerate(coll) if x.id == rid), 0) if coll is not None else 0
    records.remove(arm_obj.data, rid)
    try:
        rebuild(arm_obj, ids)
    except Exception:
        if old is not None:
            new = records.add(arm_obj.data, old)          # the build put every change back: keep the record so Delete can be retried
            with records.quiet():
                new.built, new.snapshot, new.state, new.message = saved
                if had:
                    new.object_ref = ob
                if coll is not None:
                    coll.move(len(coll) - 1, index)
        raise


def handle(arm_obj, cid):
    name = bone_tags(arm_obj).get((cid, "CTRL"))
    return arm_obj.pose.bones.get(name) if name else None


def _channel(rig, cid):
    m = rig.mech(cid)
    return ("rotation_euler", 0, True) if m is not None and m.type == "HINGE" else ("location", 1, False)


def get_value(arm_obj, rig, cid):
    """A control's value: degrees for a Hinge, units for a Slide, Telescope or Sequence slider."""
    pb = handle(arm_obj, cid)
    if pb is None:
        return 0.0
    path, index, rot = _channel(rig, cid)
    v = getattr(pb, path)[index]
    return math.degrees(v) if rot else v


def set_value(arm_obj, rig, cid, value, key=False):
    pb = handle(arm_obj, cid)
    if pb is None:
        return
    path, index, rot = _channel(rig, cid)
    getattr(pb, path)[index] = math.radians(value) if rot else value
    if key:
        pb.keyframe_insert(path, index=index)


def on_record_edit(pg, context):
    arm_obj = records.owner(pg.id_data)
    if arm_obj is None:
        return
    rid = records.record_id(pg)
    try:
        rebuild(arm_obj, {rid} if rid else None)
    except (planner.PlanError, BuildError) as exc:
        records.set_error(arm_obj.data, str(exc))


def on_select(rig_pg, context):
    """Check the newly selected mechanism for hand edits (not on every redraw, spec §8)."""
    arm_obj = records.owner(rig_pg.id_data)
    if arm_obj is None or not (0 <= rig_pg.active_mech < len(rig_pg.mechanisms)):
        return
    pg = rig_pg.mechanisms[rig_pg.active_mech]
    snap = records.snapshot_of(pg)
    if snap is None:
        return
    diffs = changed_by_hand(arm_obj, snap)
    with records.quiet():
        pg.state, pg.message = ("CHANGED_BY_HAND", _describe(diffs)) if diffs else ("OK", "")


def register():
    records.EDIT_HOOKS.append(on_record_edit)
    records.SELECT_HOOKS.append(on_select)


def unregister():
    for hooks, fn in ((records.EDIT_HOOKS, on_record_edit), (records.SELECT_HOOKS, on_select)):
        while fn in hooks:
            hooks.remove(fn)
