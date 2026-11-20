# bonecraft/boneforge/mechanisms/records.py
"""Mechanism records on the armature (``Armature.bonecraft_mech``).

Records travel with the armature when it is appended or linked. ``to_model``
converts them to ``model.py`` dataclasses for the planner. Editing a record
property runs EDIT_HOOKS (build.py adds its rebuild); changing the selected
mechanism runs SELECT_HOOKS. Writes inside ``quiet()`` run no hooks.
"""
import contextlib
import dataclasses
import json

import bpy
from bpy.props import (BoolProperty, CollectionProperty, EnumProperty, FloatProperty,
                       FloatVectorProperty, IntProperty, PointerProperty, StringProperty)

from boneforge.mechanisms import model

EDIT_HOOKS = []
SELECT_HOOKS = []
_quiet = [0]
STATES = ("OK", "MISSING_PART", "CHANGED_BY_HAND")
PART_TAG = "bc_mech_part"          # on a part's object: comma-separated part ids (a loose mesh holds several)
PART_RIG = "bc_mech_rig"           # ...and the rig those parts belong to


@contextlib.contextmanager
def quiet():
    _quiet[0] += 1
    try:
        yield
    finally:
        _quiet[0] -= 1


def _run(hooks, pg, context):
    if not _quiet[0]:
        for hook in list(hooks):
            hook(pg, context)


def _on_edit(self, context):
    _run(EDIT_HOOKS, self, context)


def _on_structural_edit(self, context):
    """Type, parts or links changed: the old constraints are replaced, not compared."""
    if not _quiet[0] and hasattr(self, "built"):
        with quiet():
            self.built, self.snapshot = False, ""
    _run(EDIT_HOOKS, self, context)


def _on_select(self, context):
    _run(SELECT_HOOKS, self, context)


def _items(values):
    return [(v, v.replace("_", " ").title(), "") for v in values]


V = {"update": _on_edit}
S = {"update": _on_structural_edit}


class BC_PG_MechPart(bpy.types.PropertyGroup):
    id: StringProperty()
    name: StringProperty(name="Name", default="Part", **V)
    kind: EnumProperty(items=_items(("OBJECT", "LOOSE")))
    object_name: StringProperty()
    object_ref: PointerProperty(type=bpy.types.Object, options={'HIDDEN'})   # set when bound: a copy never inherits it
    vertex_group: StringProperty()
    parent: StringProperty(**V)
    pivot: FloatVectorProperty(name="Pivot", size=3, subtype='TRANSLATION', **V)
    size: FloatProperty(name="Size", default=0.2, min=0.001, **V)
    state: EnumProperty(items=_items(STATES), default="OK")
    message: StringProperty()
    built: BoolProperty()
    snapshot: StringProperty()        # JSON: what BoneCraft last wrote (build.snapshot)


class BC_PG_MechStep(bpy.types.PropertyGroup):
    seq_id: StringProperty()
    target: StringProperty(**S)
    value: FloatProperty(name="Target", **V)
    start: FloatProperty(name="Start", min=0.0, max=1.0, **V)
    end: FloatProperty(name="End", default=1.0, min=0.0, max=1.0, **V)
    ease: EnumProperty(name="Ease", items=_items(model.EASES), default="EASE_IN_OUT", **V)


_ENUM_CACHE = {}                        # Blender keeps pointers into the item strings: cached lists, never mutated
_COLOR_LABEL = {"special": "Orange (special)", "fk": "Green (FK)", "ik": "Red (IK)",
                "root": "Orange (root)", "deform": "Blue (deform)", "face": "Purple (face)"}


def _enum_items(kind, values, current):
    """A stable item list for ``(kind, values, current)``; an unknown stored value rides along as "(custom)"."""
    key = (kind, tuple(values), current)
    if key not in _ENUM_CACHE:
        if kind == "widget":
            items = [("DEFAULT", "Default", "The joint type's own shape")]
            items += [(w, w.replace("_", " ").title(), "") for w in values]
        else:
            items = [(c, _COLOR_LABEL.get(c, c.title()), "") for c in values]
        if current and all(i[0] != current for i in items):
            items.append((current, f"{current} (custom)", ""))
        _ENUM_CACHE[key] = items
    return _ENUM_CACHE[key]


def _widget_items(self, context):
    from boneforge.weights import widgets
    return _enum_items("widget", sorted(widgets.WIDGET_LIBRARY), self.handle_widget or "DEFAULT")


def _color_items(self, context):
    from boneforge.mechanisms.build import PALETTE
    return _enum_items("color", list(PALETTE), self.handle_color or "special")


def _widget_get(self):
    current = self.handle_widget or "DEFAULT"
    return next((i for i, it in enumerate(_widget_items(self, None)) if it[0] == current), 0)


def _widget_set(self, index):
    value = _widget_items(self, None)[index][0]
    self.handle_widget = "" if value == "DEFAULT" else value


def _color_get(self):
    current = self.handle_color or "special"              # the planner treats empty as special
    return next((i for i, it in enumerate(_color_items(self, None)) if it[0] == current), 0)


def _color_set(self, index):
    self.handle_color = _color_items(self, None)[index][0]


class BC_PG_Mechanism(bpy.types.PropertyGroup):
    id: StringProperty()
    type: EnumProperty(name="Type", items=_items(model.TYPES), **S)
    name: StringProperty(name="Name", **V)
    parts: StringProperty(**S)                                  # comma-separated part ids
    axis: FloatVectorProperty(name="Axis", size=3, default=(1.0, 0.0, 0.0), **V)
    min: FloatProperty(name="Min", default=0.0, **V)
    max: FloatProperty(name="Max", default=90.0, **V)
    source: StringProperty(**S)
    target: StringProperty(**S)
    ratio: FloatProperty(name="Ratio", default=1.0, min=0.0, **V)
    teeth_source: IntProperty(name="Source Teeth", default=0, min=0, **V)
    teeth_target: IntProperty(name="Target Teeth", default=0, min=0, **V)
    gear_kind: EnumProperty(name="Kind", items=_items(model.GEAR_KINDS), **S)
    reverse: BoolProperty(name="Reverse", **V)
    pinion_radius: FloatProperty(name="Pinion Radius", default=0.05, min=0.0, **V)
    source_range: FloatVectorProperty(name="Source Range", size=2, default=(0.0, 90.0), **V)
    target_range: FloatVectorProperty(name="Target Range", size=2, default=(0.0, 40.0), **V)
    curve: BoolProperty(name="Curve", **S)
    stretch: BoolProperty(name="Stretch", **S)
    length: FloatProperty(name="Length", default=0.0, min=0.0, **V)
    shares: StringProperty(name="Shares", **V)                   # comma-separated; empty = even
    handle_widget: StringProperty(name="Handle Shape", **V)
    handle_size: FloatProperty(name="Handle Size", default=1.0, min=0.01, **V)
    handle_color: StringProperty(name="Handle Colour", default="special", **V)
    handle_widget_ui: EnumProperty(name="Handle Shape", description="The handle's viewport shape",
                                   items=_widget_items, get=_widget_get, set=_widget_set)
    handle_color_ui: EnumProperty(name="Handle Colour", description="The handle's viewport colour",
                                  items=_color_items, get=_color_get, set=_color_set)
    state: EnumProperty(items=_items(STATES), default="OK")
    message: StringProperty()
    built: BoolProperty()
    snapshot: StringProperty()        # JSON: what BoneCraft last wrote (build.snapshot)
    show_note: BoolProperty(name="How this works")


def _progress_get(self):
    """The Sequence's handle value as 0-100, read live from the rig (never stored)."""
    from boneforge.mechanisms import build
    ob = owner(self.id_data)
    if ob is None:
        return 0.0
    try:
        return build.get_value(ob, to_model(ob), self.id) * 100.0
    except Exception:                                     # noqa: BLE001 - a half-built rig draws as 0
        return 0.0


def _progress_set(self, value):
    from boneforge.mechanisms import build
    ob = owner(self.id_data)
    if ob is None:
        return
    try:
        build.set_value(ob, to_model(ob), self.id, value / 100.0)
    except Exception:                                     # noqa: BLE001 - a half-built rig ignores the slide
        pass


class BC_PG_MechSequence(bpy.types.PropertyGroup):
    id: StringProperty()
    name: StringProperty(name="Name", **V)
    steps: CollectionProperty(type=BC_PG_MechStep)
    active_step: IntProperty()
    progress: FloatProperty(name="Progress", subtype='PERCENTAGE', min=0.0, max=100.0,
                            get=_progress_get, set=_progress_set, options=set(),
                            description="How far along the Sequence is (a view of the handle bone, not a saved value)")
    state: EnumProperty(items=_items(STATES), default="OK")
    message: StringProperty()
    built: BoolProperty()
    snapshot: StringProperty()        # JSON: what BoneCraft last wrote (build.snapshot)


class BC_PG_MechFormValue(bpy.types.PropertyGroup):
    key: StringProperty()
    value: FloatProperty()


class BC_PG_MechForm(bpy.types.PropertyGroup):
    name: StringProperty(name="Name")
    control_values: CollectionProperty(type=BC_PG_MechFormValue)


class BC_PG_MechRig(bpy.types.PropertyGroup):
    parts: CollectionProperty(type=BC_PG_MechPart)
    mechanisms: CollectionProperty(type=BC_PG_Mechanism)
    sequences: CollectionProperty(type=BC_PG_MechSequence)
    forms: CollectionProperty(type=BC_PG_MechForm)
    active_part: IntProperty()
    active_mech: IntProperty(update=_on_select)
    active_seq: IntProperty()
    active_form: IntProperty()
    last_error: StringProperty()


def _number(text):
    """A share as typed; a typo becomes NaN, which telescope.shares refuses with a plain message."""
    try:
        return float(text)
    except ValueError:
        return float("nan")


_CSV = {"parts": str, "shares": _number}


def _value(name, v):
    if name in _CSV:
        return [_CSV[name](x) for x in v.split(",") if x.strip()]
    if hasattr(v, "__len__") and not isinstance(v, str):
        return tuple(v)
    return v


def _to(cls, pg):
    return cls(**{f.name: _value(f.name, getattr(pg, f.name))
                  for f in dataclasses.fields(cls) if f.name not in ("steps", "values")})


def write(pg, obj):
    """Copy a model dataclass onto its PropertyGroup without running hooks."""
    with quiet():
        for f in dataclasses.fields(obj):
            if f.name in ("steps", "values"):
                continue
            v = getattr(obj, f.name)
            setattr(pg, f.name, ",".join(str(x) for x in v) if f.name in _CSV else v)


def _all(r):
    return list(r.parts) + list(r.mechanisms) + list(r.sequences)


def has_records(arm_data):
    r = arm_data.bonecraft_mech
    return bool(len(r.parts) or len(r.mechanisms) or len(r.sequences))


def tag_ids(ob):
    """The part ids an object is tagged with."""
    return [x for x in str(ob.get(PART_TAG, "")).split(",") if x]


def _tagged_for(ob, pg):
    rig = ob.get(PART_RIG)
    return pg.id in tag_ids(ob) and getattr(rig, "data", None) == pg.id_data


def _bound(ob, pg):
    """``ob`` (tagged for ``pg``) sits on the part's DEF bone, or is skinned to the rig through the part's group."""
    rig = ob.get(PART_RIG)
    if pg.kind == "LOOSE":
        return (ob.vertex_groups.get(pg.vertex_group) is not None
                and any(m.type == 'ARMATURE' and m.object == rig for m in ob.modifiers))
    if ob.parent != rig or ob.parent_type != 'BONE' or rig.pose is None:
        return False
    pb = rig.pose.bones.get(ob.parent_bone)
    return pb is not None and pb.get("bc_mech_id") == pg.id and pb.get("bc_mech_role") == "DEF"


def _name_fits(ob, pg):
    """The object found by the stored name is this part's: untagged, tagged for it, or a loose mesh with its group."""
    ids = tag_ids(ob)
    if not ids or pg.id in ids:
        return True
    return pg.kind == "LOOSE" and ob.vertex_groups.get(pg.vertex_group) is not None


def _ref(pg):
    """``(had, ob)``: whether ``pg`` has its object reference set, and that object (None when deleted or unset).

    Reading an unset reference (``hasattr`` included) would set it: check first. Mechanism and sequence records
    have no reference."""
    had = pg is not None and "object_ref" in pg.bl_rna.properties and pg.is_property_set("object_ref")
    return had, (pg.object_ref if had else None)


def part_object(pg):
    """The part's object, or None when it is gone or cannot be told apart from a copy.

    A bound part keeps a reference to its object: renaming the object keeps it, deleting it leaves the part
    missing, and a copy (Shift+D, copy/paste) never inherits it. A record without a reference goes by its tag:
    the stored name if that object is tagged for the part, else the one tagged object (preferring the one still
    bound to the part), else the untagged object at the stored name. Read-only, so safe in draw."""
    had, ob = _ref(pg)
    if had:
        if ob is None or not ob.users_collection:
            return None                               # deleted (an operator delete leaves it held only by the reference)
        if _tagged_for(ob, pg):
            return ob
    ob = bpy.data.objects.get(pg.object_name) if pg.object_name else None
    if ob is not None and _tagged_for(ob, pg):
        return ob
    tagged = [o for o in bpy.data.objects if _tagged_for(o, pg)]
    if len(tagged) > 1:
        tagged = [o for o in tagged if _bound(o, pg)]
        return tagged[0] if len(tagged) == 1 else None     # never a guess between copies
    if tagged:
        return tagged[0]
    return ob if ob is not None and _name_fits(ob, pg) else None


def set_object(pg, ob):
    """Bind the record to ``ob`` (operators only: never from a draw)."""
    with quiet():
        pg.object_ref = ob
        pg.object_name = ob.name


def refresh_object_names(arm_data):
    """Write each part's current object name back into its record (operators only: never from a draw).

    A reference to an object deleted from every collection is cleared, so Blender can free the object."""
    with quiet():
        for p in arm_data.bonecraft_mech.parts:
            ob = _ref(p)[1]
            if ob is not None and not ob.users_collection:
                p.object_ref = None
            ob = part_object(p)
            if ob is not None and ob.name != p.object_name:
                p.object_name = ob.name


def missing_parts(r):
    out = set()
    for p in r.parts:
        ob = part_object(p)
        if ob is None or (p.kind == "LOOSE" and ob.vertex_groups.get(p.vertex_group) is None):
            out.add(p.id)
    return out


def form_values(form):
    """Read current or legacy form storage without changing saved/linked data."""
    if "control_values" in form:
        return {v.key: v.value for v in form.control_values}
    # Older files used "values", which is a reserved PropertyGroup method name.
    return {v.get("key", ""): v.get("value", 0.0) for v in form.get("values", ())}


def to_model(arm_obj):
    r = arm_obj.data.bonecraft_mech
    return model.MechRig(
        parts=[_to(model.Part, p) for p in r.parts],
        mechanisms=[_to(model.Mechanism, m) for m in r.mechanisms],
        sequences=[model.Sequence(s.id, s.name, [_to(model.Step, st) for st in s.steps]) for s in r.sequences],
        forms=[model.Form(f.name, form_values(f)) for f in r.forms],
        missing=missing_parts(r),
    )


def add(arm_data, obj):
    r = arm_data.bonecraft_mech
    coll = {model.Part: r.parts, model.Mechanism: r.mechanisms, model.Sequence: r.sequences}[type(obj)]
    with quiet():
        pg = coll.add()
    write(pg, obj)
    if isinstance(obj, model.Sequence):
        for st in obj.steps:
            add_step(pg, st)
    return pg


def add_step(seq_pg, step):
    with quiet():
        pg = seq_pg.steps.add()
        pg.seq_id = seq_pg.id
    write(pg, step)
    return pg


def find(arm_data, rid):
    return next((x for x in _all(arm_data.bonecraft_mech) if x.id == rid), None)


def remove(arm_data, rid):
    r = arm_data.bonecraft_mech
    for coll in (r.parts, r.mechanisms, r.sequences):
        i = next((i for i, x in enumerate(coll) if x.id == rid), -1)
        if i >= 0:
            with quiet():
                coll.remove(i)
            return True
    return False


def taken_ids(arm_data):
    return {x.id for x in _all(arm_data.bonecraft_mech)}


def owner(arm_data):
    """The armature object that uses this armature data."""
    return next((o for o in bpy.data.objects if o.type == 'ARMATURE' and o.data == arm_data), None)


def active_rig(context):
    """The mechanism rig for the active object: the armature itself, or a part mesh's rig."""
    ob = context.active_object
    if ob is None:
        return None
    rig = ob.get("bc_pivot_rig")                      # a part's pivot marker belongs to its rig
    if rig is not None and getattr(rig, "type", "") == 'ARMATURE':
        return rig
    if ob.type == 'ARMATURE':
        return ob if has_records(ob.data) else None
    cands = [ob.parent] if ob.parent is not None and ob.parent.type == 'ARMATURE' else []
    cands += [m.object for m in getattr(ob, "modifiers", ()) if m.type == 'ARMATURE' and m.object]
    return next((a for a in cands if has_records(a.data)), None)


def record_id(pg):
    """The id of the record a PropertyGroup belongs to (a step belongs to its Sequence)."""
    return getattr(pg, "seq_id", "") or getattr(pg, "id", "")


def built_ids(arm_data):
    return {x.id for x in _all(arm_data.bonecraft_mech) if x.built}


def mark(arm_data, built, skipped, held, snapshots=None):
    """Record each record's state after a build; ``snapshots`` holds what was just written."""
    snapshots = snapshots or {}
    with quiet():
        for x in _all(arm_data.bonecraft_mech):
            if x.id in skipped:
                x.state, x.message = "MISSING_PART", skipped[x.id]
            elif x.id in held:
                x.state, x.message = "CHANGED_BY_HAND", held[x.id]
            elif x.id in built:
                x.state, x.message, x.built = "OK", "", True
                if x.id in snapshots:
                    x.snapshot = json.dumps(snapshots[x.id], sort_keys=True)


def snapshot_of(pg):
    return json.loads(pg.snapshot) if pg is not None and pg.built and pg.snapshot else None


def set_error(arm_data, text):
    with quiet():
        arm_data.bonecraft_mech.last_error = text


classes = (BC_PG_MechPart, BC_PG_MechStep, BC_PG_Mechanism, BC_PG_MechSequence,
           BC_PG_MechFormValue, BC_PG_MechForm, BC_PG_MechRig)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Armature.bonecraft_mech = PointerProperty(type=BC_PG_MechRig)


def unregister():
    if hasattr(bpy.types.Armature, "bonecraft_mech"):
        del bpy.types.Armature.bonecraft_mech
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
