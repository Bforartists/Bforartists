"""Parts: Add Parts from Selection (objects or loose pieces), Apply Transforms, Edit Pivot,
Merge for VRChat, Reassign and Remove (spec §5.2)."""
import bpy
from mathutils import Matrix, Vector

from boneforge.mechanisms import build, model, records

PIVOT_PROP = "bc_pivot_for"


def pivot_markers(arm):
    """This rig's pivot marker objects (normally none or one). Read-only, so safe in draw."""
    return [ob for ob in bpy.data.objects
            if ob.get(PIVOT_PROP) is not None and ob.get("bc_pivot_rig") == arm and ob.users_collection]


def islands(mesh):
    """Vertex index lists, one per loose piece (vertices joined by edges)."""
    parent = list(range(len(mesh.vertices)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for e in mesh.edges:
        x, y = root(e.vertices[0]), root(e.vertices[1])
        if x != y:
            parent[x] = y
    groups = {}
    for v in range(len(mesh.vertices)):
        groups.setdefault(root(v), []).append(v)
    return sorted(groups.values(), key=lambda g: g[0])


def _rig_of(obj):
    p = obj.parent
    return p if p is not None and p.type == 'ARMATURE' else None


def rest_world(obj):
    """The object's world matrix with its rig at rest (a bone parent adds the bone's rotation)."""
    p = _rig_of(obj)
    if p is not None and obj.parent_type == 'BONE' and obj.parent_bone in p.data.bones:
        bone = p.data.bones[obj.parent_bone]
        return (p.matrix_world @ bone.matrix_local @ Matrix.Translation((0.0, bone.length, 0.0))
                @ obj.matrix_parent_inverse @ obj.matrix_basis)
    return obj.matrix_world


def needs_apply(obj):
    """Unapplied rotation or scale tilts the part's axes (spec §5.2)."""
    _, rot, scale = rest_world(obj).decompose()
    return rot.angle > 1e-5 or (scale - Vector((1.0, 1.0, 1.0))).length > 1e-5


def apply_transforms(obj):
    """Apply rotation and scale into the mesh, keeping the object bound to its bone and in place."""
    rig = _rig_of(obj)
    parent_type, parent_bone = obj.parent_type, obj.parent_bone
    pose_position = rig.data.pose_position if rig else None
    if rig:
        rig.data.pose_position = 'REST'
        bpy.context.view_layer.update()
        mw = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = mw
    try:
        with bpy.context.temp_override(active_object=obj, object=obj, selected_objects=[obj],
                                       selected_editable_objects=[obj]):
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    finally:
        if rig:
            mw = obj.matrix_world.copy()
            obj.parent, obj.parent_type, obj.parent_bone = rig, parent_type, parent_bone
            bpy.context.view_layer.update()
            obj.matrix_world = mw
            rig.data.pose_position = pose_position


def _rig_for(context, meshes):
    for ob in [context.active_object] + list(context.selected_objects):
        if ob is not None and ob.type == 'ARMATURE':
            return ob
    for ob in meshes:
        if ob.parent is not None and ob.parent.type == 'ARMATURE':
            return ob.parent
    data = bpy.data.armatures.new("Mechanism Rig")
    arm = bpy.data.objects.new("Mechanism Rig", data)
    meshes[0].users_collection[0].objects.link(arm)
    return arm


def _size(points):
    lo = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    hi = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    return max((hi - lo).length * 0.5, 0.05)


def add_parts_from_selection(context):
    meshes = [o for o in context.selected_objects if o.type == 'MESH']
    if not meshes:
        raise build.BuildError("Select the mesh parts first.")
    arm = _rig_for(context, meshes)
    inv = arm.matrix_world.inverted()
    rec = arm.data.bonecraft_mech
    taken = records.taken_ids(arm.data)
    names = {p.name for p in rec.parts}
    used = {ob.name for ob in map(records.part_object, rec.parts) if ob is not None}
    new = []

    def part(**kw):
        pid = model.new_id(taken)
        taken.add(pid)
        name = model.unique_name(model.clean_name(kw.pop("label")), names)
        names.add(name)
        return model.Part(pid, name, **kw), name

    if len(meshes) == 1 and meshes[0].name not in used and len(islands(meshes[0].data)) > 1:
        ob = meshes[0]
        for i, verts in enumerate(islands(ob.data), 1):
            pts = [ob.matrix_world @ ob.data.vertices[v].co for v in verts]
            p, name = part(label=f"{ob.name} {i}", kind="LOOSE", object_name=ob.name,
                           pivot=tuple(inv @ (sum(pts, Vector()) / len(pts))), size=_size(pts))
            group = ob.vertex_groups.new(name=f"DEF-{name}")
            group.add(verts, 1.0, 'REPLACE')
            p.vertex_group = group.name
            new.append(p)
    else:
        for ob in meshes:
            if ob.name in used:
                continue
            pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
            p, _ = part(label=ob.name, kind="OBJECT", object_name=ob.name,
                        pivot=tuple(inv @ ob.matrix_world.translation), size=_size(pts))
            new.append(p)
    if not new:
        raise build.BuildError("Those parts are already in this rig.")
    for p in new:
        records.add(arm.data, p)
    for p in new:
        tag(bpy.data.objects[p.object_name], arm, p.id)   # the selected object, by reference from here on
    build.rebuild(arm, {p.id for p in new})
    bind(arm, [p.id for p in new])
    objs = {p.id: records.part_object(records.find(arm.data, p.id)) for p in new}
    return arm, [p.id for p in new], [p.name for p in new if p.kind == "OBJECT" and needs_apply(objs[p.id])]


def _elsewhere(arm, pid, ob):
    """Part ``pid`` of ``arm`` belongs to another object than ``ob``: its object reference is set to another
    object or to a deleted one (None); without a reference, the part resolves to an object other than ``ob``."""
    pg = records.find(arm.data, pid)
    had, ref = records._ref(pg)
    if had:
        return ref != ob
    other = records.part_object(pg) if pg is not None else None
    return other is not None and other != ob


def tag(ob, arm, pid):
    """Mark ``ob`` as (one of) the object(s) of part ``pid``, so renaming it keeps the part, and bind the record to it.

    A copy inherits its original's ids: those whose parts belong to another object, or a deleted one, are dropped."""
    ids = records.tag_ids(ob) if ob.get(records.PART_RIG) == arm else []     # tags from another rig do not carry over
    ids = [q for q in ids if q == pid or not _elsewhere(arm, q, ob)]
    if pid not in ids:
        ids.append(pid)
    ob[records.PART_TAG] = ",".join(ids)
    ob[records.PART_RIG] = arm
    pg = records.find(arm.data, pid)
    if pg is not None:
        records.set_object(pg, ob)


def untag(ob, pid):
    if ob is None:
        return
    ids = [x for x in records.tag_ids(ob) if x != pid]
    if ids:
        ob[records.PART_TAG] = ",".join(ids)
    else:
        for k in (records.PART_TAG, records.PART_RIG):
            ob.pop(k, None)


def bind(arm, part_ids):
    """Parent object parts to their DEF bone (keeping their place); skin loose parts to it. Tags each object."""
    bpy.context.view_layer.update()
    records.refresh_object_names(arm.data)
    tags = build.bone_tags(arm)
    for pid in part_ids:
        pg = records.find(arm.data, pid)
        def_name = tags.get((pid, "DEF"))
        ob = records.part_object(pg)
        if ob is None:
            continue
        tag(ob, arm, pid)
        if def_name is None:
            continue
        if pg.kind == "OBJECT":
            mw = ob.matrix_world.copy()
            ob.parent, ob.parent_type, ob.parent_bone = arm, 'BONE', def_name
            ob.matrix_world = mw
            continue
        group = ob.vertex_groups.get(pg.vertex_group)
        if group is not None and group.name != def_name:
            group.name = def_name
            with records.quiet():
                pg.vertex_group = def_name
        if not any(m.type == 'ARMATURE' and m.object == arm for m in ob.modifiers):
            ob.modifiers.new("Mechanism Rig", 'ARMATURE').object = arm


def start_pivot(context, arm, pid):
    pg = records.find(arm.data, pid)
    empty = bpy.data.objects.new(f"Pivot: {pg.name}", None)
    empty.empty_display_type = 'SPHERE'
    empty.empty_display_size = max(pg.size * 0.5, 0.02)
    empty.location = arm.matrix_world @ Vector(pg.pivot)
    empty[PIVOT_PROP] = pid
    empty["bc_pivot_rig"] = arm
    context.scene.collection.objects.link(empty)
    for ob in context.selected_objects:
        ob.select_set(False)
    empty.select_set(True)
    context.view_layer.objects.active = empty
    return empty


def apply_pivot(context, empty):
    context.view_layer.update()                           # the marker's matrix_world is current
    arm, pid = empty["bc_pivot_rig"], empty[PIVOT_PROP]
    with records.quiet():
        records.find(arm.data, pid).pivot = arm.matrix_world.inverted() @ empty.matrix_world.translation
    bpy.data.objects.remove(empty)
    build.rebuild(arm, {pid})                              # keeps every object part's rest placement
    context.view_layer.update()
    context.view_layer.objects.active = arm


def merge_for_vrchat(context, arm):
    """Join object parts into one mesh, one vertex group per part, skinned to the DEF bones."""
    rec = arm.data.bonecraft_mech
    tags = build.bone_tags(arm)
    pgs = [p for p in rec.parts if p.kind == "OBJECT" and records.part_object(p) is not None]
    if len(pgs) < 2:
        raise build.BuildError("Merge for VRChat needs two or more object parts.")
    pose_position = arm.data.pose_position
    arm.data.pose_position = 'REST'                       # join the geometry where it rests
    try:
        context.view_layer.update()
        objs = []
        for p in pgs:
            ob = records.part_object(p)
            mw = ob.matrix_world.copy()
            ob.parent = None
            ob.matrix_world = mw
            for stale in [g for g in ob.vertex_groups
                          if g.name in arm.data.bones and g.name != tags[(p.id, "DEF")]]:
                ob.vertex_groups.remove(stale)            # weights to other bones would double-skin the piece
            group = ob.vertex_groups.get(tags[(p.id, "DEF")]) or ob.vertex_groups.new(name=tags[(p.id, "DEF")])
            group.add(range(len(ob.data.vertices)), 1.0, 'REPLACE')
            objs.append(ob)
        target = objs[0]
        with records.quiet():
            for p in pgs:
                p.object_ref = target                     # a reference holds a user: let the join free the others
        with context.temp_override(active_object=target, object=target, selected_objects=objs,
                                   selected_editable_objects=objs):
            bpy.ops.object.join()
        mw = target.matrix_world.copy()
        target.parent, target.parent_type = arm, 'OBJECT'
        target.matrix_world = mw
        if not any(m.type == 'ARMATURE' and m.object == arm for m in target.modifiers):
            target.modifiers.new("Mechanism Rig", 'ARMATURE').object = arm
        with records.quiet():
            for p in pgs:
                p.kind, p.object_name, p.vertex_group = "LOOSE", target.name, tags[(p.id, "DEF")]
        for p in pgs:
            tag(target, arm, p.id)
    finally:
        arm.data.pose_position = pose_position
    return target


def reassign(arm, pid, obj):
    pg = records.find(arm.data, pid)
    if pg is None:
        raise build.BuildError("That part no longer exists.")
    if obj is None or obj.type != 'MESH':
        raise build.BuildError("Select a mesh object.")
    for other in arm.data.bonecraft_mech.parts:
        if other.id != pid and records.part_object(other) == obj and "OBJECT" in (other.kind, pg.kind):
            raise build.BuildError(f"'{obj.name}' is already the part '{other.name}'.")
    if pg.kind == "LOOSE":
        group = obj.vertex_groups.get(pg.vertex_group)
        if group is None or not any(g.group == group.index and g.weight > 0.0 for v in obj.data.vertices for g in v.groups):
            raise build.BuildError(f"'{obj.name}' has no vertex group '{pg.vertex_group}' for this loose part.")
    old = records.part_object(pg)
    if old is not None and old != obj and pg.kind == "OBJECT" and old.parent == arm:
        mw = old.matrix_world.copy()                      # release the previous object, in place
        old.parent = None
        old.matrix_world = mw
    if old is not None and old != obj:
        untag(old, pid)
    tag(obj, arm, pid)
    build.rebuild(arm, {pid})
    bind(arm, [pid])


def remove_part(arm, pid):
    pg = records.find(arm.data, pid)
    if pg is None:
        raise build.BuildError("That part no longer exists.")
    rig = records.to_model(arm)
    users = [m.name for m in rig.mechanisms if pid in m.parts]
    users += [p.name for p in rig.parts if p.parent == pid]
    if users:
        raise build.BuildError(f"Part '{pg.name}' is used by {', '.join(users)}; delete or change those first.")
    ob = records.part_object(pg)
    if ob is not None and pg.kind == "OBJECT" and ob.parent == arm:
        mw = ob.matrix_world.copy()
        ob.parent = None
        ob.matrix_world = mw
    elif ob is not None and pg.kind == "LOOSE" and ob.vertex_groups.get(pg.vertex_group):
        ob.vertex_groups.remove(ob.vertex_groups[pg.vertex_group])
    build.delete(arm, pid)
    untag(ob, pid)
