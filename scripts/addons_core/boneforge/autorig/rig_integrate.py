"""BoneCraft — fit the control-rig engine onto a generated, skinned skeleton.

The rig engine (:mod:`rig_build`) lays its bones out on a fixed biped
template. On its own that is fine for a blank armature, but on a skeleton the
Auto-Rig wizard already generated and skinned it produced a *second*,
unweighted skeleton: the controls moved nothing, and the engine's ``neck`` /
``head`` overwrote the wizard's skinned bones of the same name.

This module makes the two one rig:

1. read the wizard skeleton's joints,
2. fit every engine bone onto them (pure, :func:`fit_plan`),
3. build the engine rig,
4. move the mesh weights onto the engine's deform bones, keep any extra
   skinned bones (fingers, toes, face) parented to the nearest engine bone,
   and delete the leftover wizard bones — leaving exactly one deform skeleton.

Pure helpers (no ``bpy``) are unit-testable headlessly; Blender work is in
:func:`integrate_control_rig`. Bforartists-exclusive (lives only in this repo).
"""
import math

from .components import limb as _limb
from .components import spine as _spine

WIZ_PREFIX = "WIZ-"

# Engine limb segment -> wizard bone base name.
_WIZARD_LIMB = {
    "upperarm": "upper_arm", "forearm": "forearm", "hand": "hand",
    "thigh": "thigh", "shin": "shin", "foot": "foot", "toe": "toe",
}
# Engine deform bone for each limb segment (toe has no engine deform bone).
_ENGINE_DEF = {
    "upperarm": "upperarm.def", "forearm": "forearm.def", "hand": "hand.def",
    "thigh": "thigh.def", "shin": "shin.def", "foot": "foot.def",
}
_ENGINE_SPINE = [name for (name, _h, _t, _d) in _spine._SPINE
                 if name not in ("neck", "head")]
_FINGER_WORDS = ("thumb", "index", "middle", "ring", "pinky", "finger")


# ------------------------------------------------------------ vector math

def _sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def _add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def _mul(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def _dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def _len(a): return math.sqrt(_dot(a, a))
def _lerp(a, b, t): return _add(a, _mul(_sub(b, a), t))
def _mirror_y(p): return (p[0], -p[1], p[2])


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _rotate_between(v, src_dir, dst_dir):
    """Rotate ``v`` by the shortest rotation taking ``src_dir`` to ``dst_dir``."""
    ls, ld = _len(src_dir), _len(dst_dir)
    if ls < 1e-12 or ld < 1e-12:
        return v
    a, b = _mul(src_dir, 1.0 / ls), _mul(dst_dir, 1.0 / ld)
    c = max(-1.0, min(1.0, _dot(a, b)))
    axis = _cross(a, b)
    s = _len(axis)
    if s < 1e-9:
        if c > 0:
            return v
        # 180 degrees: any axis perpendicular to a
        perp = _cross(a, (1.0, 0.0, 0.0))
        if _len(perp) < 1e-6:
            perp = _cross(a, (0.0, 1.0, 0.0))
        axis, s = perp, _len(perp)
    k = _mul(axis, 1.0 / s)
    ang = math.atan2(s, c)
    # Rodrigues' rotation formula
    cos_a, sin_a = math.cos(ang), math.sin(ang)
    return _add(_add(_mul(v, cos_a), _mul(_cross(k, v), sin_a)),
                _mul(k, _dot(k, v) * (1.0 - cos_a)))


def _closest_param(p, head, tail):
    d = _sub(tail, head)
    dd = _dot(d, d)
    if dd < 1e-12:
        return 0.0
    return max(0.0, min(1.0, _dot(_sub(p, head), d) / dd))


def _point_segment_dist(p, head, tail):
    t = _closest_param(p, head, tail)
    return _len(_sub(p, _lerp(head, tail, t))), t


# ------------------------------------------------------------ pure fitting

def template_segments(sides=("L", "R")):
    """Engine template segments ``{key: (head, tail)}`` (keys like ``forearm-L``)."""
    segs = {}
    for name, head, tail, _deform in _spine._SPINE:
        segs[name] = (head, tail)
    for side in sides:
        def m(p, side=side):
            return (p[0] if side == "L" else -p[0], p[1], p[2])
        for tmpl in (_limb._ARM, _limb._LEG):
            for key, (head, tail) in tmpl.items():
                segs["%s-%s" % (key, side)] = (m(head), m(tail))
    return segs


def segment_hint(bone_name):
    """Template segment a plan bone belongs to, from its name (or ``None``).

    ``upperarm.fk-L`` -> ``upperarm-L``; foot-roll bones belong to the foot.
    Bones with no own segment (poles, root, properties) are placed by nearest
    segment instead.
    """
    base, _sep, side = bone_name.rpartition("-")
    if side not in ("L", "R"):
        base, side = bone_name, ""
    seg = base.split(".")[0]
    if seg.startswith("roll_"):
        seg = "foot"
    if seg in ("hips", "spine", "chest", "neck", "head") and not side:
        return bone_name
    if seg in _limb._ARM or seg in _limb._LEG:
        return "%s-%s" % (seg, side) if side else None
    return None


def fit_point(p, template, targets, hint=None):
    """Map template-space point ``p`` onto the target skeleton.

    ``p`` is expressed relative to its nearest template segment (parameter
    along it + perpendicular offset), then re-expressed on the matching target
    segment with the offset rotated and scaled to the new segment.
    """
    best = None
    for key, (th, tt) in template.items():
        if key not in targets or (hint in targets and key != hint):
            continue
        dist, t = _point_segment_dist(p, th, tt)
        if best is None or dist < best[0] - 1e-9:
            best = (dist, key, t)
    if best is None:
        return tuple(p)
    _dist, key, t = best
    th, tt = template[key]
    gh, gt = targets[key]
    tdir, gdir = _sub(tt, th), _sub(gt, gh)
    tlen, glen = _len(tdir), _len(gdir)
    # parameter may run past the segment end (e.g. a tip beyond the hand)
    if tlen > 1e-12:
        t_raw = _dot(_sub(p, th), tdir) / (tlen * tlen)
    else:
        t_raw = t
    on_seg = _add(th, _mul(tdir, t_raw))
    offset = _sub(p, on_seg)
    scale = glen / tlen if tlen > 1e-12 else 1.0
    offset = _mul(_rotate_between(offset, tdir, gdir), scale)
    return _add(_add(gh, _mul(gdir, t_raw)), offset)


def fit_plan(plan, targets, template=None):
    """Rewrite every bone head/tail in ``plan`` onto ``targets`` (in place)."""
    template = template or template_segments()
    # The engine template's feet point +Y while its poles assume a -Y facing
    # character. A foot that points the other way is a mirror, not a
    # rotation, so mirror the foot pieces front-to-back before fitting.
    flipped = dict(template)
    flip_sides = set()
    for side in ("L", "R"):
        key = "foot-%s" % side
        if key in template and key in targets:
            tdy = template[key][1][1] - template[key][0][1]
            gdy = targets[key][1][1] - targets[key][0][1]
            if tdy * gdy < 0:
                flip_sides.add(side)
                for k in ("foot-%s" % side, "toe-%s" % side):
                    h, t = template[k]
                    flipped[k] = (_mirror_y(h), _mirror_y(t))
    for bd in plan.bones:
        hint = segment_hint(bd.name)
        if hint and hint[-1] in flip_sides and hint.split("-")[0] in ("foot", "toe"):
            bd.head = fit_point(_mirror_y(bd.head), flipped, targets, hint)
            bd.tail = fit_point(_mirror_y(bd.tail), flipped, targets, hint)
        else:
            bd.head = fit_point(bd.head, template, targets, hint)
            bd.tail = fit_point(bd.tail, template, targets, hint)
    return plan


def spine_targets(spine_points, neck=None, head=None):
    """Split a wizard spine polyline into the engine's spine segments.

    ``spine_points`` runs pelvis -> neck base. Each engine spine bone keeps its
    template share of the pelvis-to-chest span.
    """
    tmpl = [(n, h, t) for (n, h, t, _d) in _spine._SPINE if n in _ENGINE_SPINE]
    z0, z1 = tmpl[0][1][2], tmpl[-1][2][2]
    lengths = [_len(_sub(b, a)) for a, b in zip(spine_points, spine_points[1:])]
    total = sum(lengths) or 1.0

    def at(frac):
        want = frac * total
        for (a, b), seg_len in zip(zip(spine_points, spine_points[1:]), lengths):
            if want <= seg_len + 1e-12:
                return _lerp(a, b, want / seg_len if seg_len else 0.0)
            want -= seg_len
        return spine_points[-1]

    out = {}
    for name, h, t in tmpl:
        out[name] = (at((h[2] - z0) / (z1 - z0)), at((t[2] - z0) / (z1 - z0)))
    if neck:
        out["neck"] = neck
    if head:
        out["head"] = head
    return out


def wizard_joint_targets(bones, sides=("L", "R")):
    """Engine segment targets from wizard bones ``{name: (head, tail)}``."""
    targets = {}
    spine_names = sorted((n for n in bones if n == "spine" or n.startswith("spine.")),
                         key=lambda n: (n != "spine", n))
    neck_names = sorted((n for n in bones if n == "neck" or n.startswith("neck.")),
                        key=lambda n: (n != "neck", n))
    if spine_names:
        pts = [bones[spine_names[0]][0]] + [bones[n][1] for n in spine_names]
        neck = ((bones[neck_names[0]][0], bones[neck_names[-1]][1])
                if neck_names else None)
        targets.update(spine_targets(pts, neck, bones.get("head")))
    for side in sides:
        for eng, wiz in _WIZARD_LIMB.items():
            name = "%s.%s" % (wiz, side)
            if name in bones:
                targets["%s-%s" % (eng, side)] = bones[name]
        # clavicle: chest top toward the shoulder (the wizard has none)
        ua = targets.get("upperarm-%s" % side)
        chest = targets.get("chest")
        if ua and chest:
            targets["clavicle-%s" % side] = (_lerp(chest[1], ua[0], 0.2), ua[0])
    return targets


def weight_transfer_map(wizard_bone_names, sides=("L", "R")):
    """Wizard skinned bone -> engine deform bone for 1:1 segments."""
    out = {}
    for side in sides:
        for eng, wiz in _WIZARD_LIMB.items():
            if eng in _ENGINE_DEF and "%s.%s" % (wiz, side) in wizard_bone_names:
                out["%s.%s" % (wiz, side)] = "%s-%s" % (_ENGINE_DEF[eng], side)
    for n in wizard_bone_names:
        if n == "neck" or n.startswith("neck."):
            out[n] = "neck"
    if "head" in wizard_bone_names:
        out["head"] = "head"
    return out


def spine_split(param, centers):
    """Split one unit of spine weight between the two bracketing bone centres."""
    if param <= centers[0]:
        return {0: 1.0}
    if param >= centers[-1]:
        return {len(centers) - 1: 1.0}
    for i in range(len(centers) - 1):
        a, b = centers[i], centers[i + 1]
        if a <= param <= b:
            f = (param - a) / (b - a) if b > a else 0.0
            return {i: 1.0 - f, i + 1: f}
    return {len(centers) - 1: 1.0}


def is_wizard_skeleton(bone_names):
    """True for an Auto-Rig wizard skeleton that has no engine rig yet."""
    names = set(bone_names)
    return ({"upper_arm.L", "forearm.L", "thigh.L", "shin.L"} <= names
            and "upperarm.def-L" not in names)


# ------------------------------------------------------------ Blender side

def _skinned_meshes(bpy, armature_obj):
    out = []
    for ob in bpy.data.objects:
        if ob.type != 'MESH':
            continue
        if any(m.type == 'ARMATURE' and m.object == armature_obj for m in ob.modifiers):
            out.append(ob)
    return out


def _rename_group(mesh_obj, old, new):
    vg = mesh_obj.vertex_groups.get(old)
    if vg is not None and mesh_obj.vertex_groups.get(new) is None:
        vg.name = new


def _weighted_group_names(meshes):
    names = set()
    for ob in meshes:
        gid = {g.index: g.name for g in ob.vertex_groups}
        for v in ob.data.vertices:
            for ge in v.groups:
                if ge.weight > 0.0:
                    names.add(gid[ge.group])
    return names


def _transfer_weights(mesh_obj, armature_obj, one_to_one, spine_groups, spine_segs):
    """Move WIZ- groups onto engine deform groups (1:1 + spine split)."""
    groups = mesh_obj.vertex_groups
    gid = {g.index: g.name for g in groups}

    def target(name):
        return groups.get(name) or groups.new(name=name)

    arm_inv = armature_obj.matrix_world.inverted()
    to_arm = arm_inv @ mesh_obj.matrix_world
    # cumulative spine parameter at each engine spine bone centre
    lens = [_len(_sub(t, h)) for (_n, h, t) in spine_segs]
    starts, acc = [], 0.0
    for seg_len in lens:
        starts.append(acc)
        acc += seg_len
    centers = [s + l * 0.5 for s, l in zip(starts, lens)]

    def spine_param(co):
        best = None
        for i, (_n, h, t) in enumerate(spine_segs):
            dist, u = _point_segment_dist(co, h, t)
            if best is None or dist < best[0]:
                best = (dist, starts[i] + u * lens[i])
        return best[1]

    # Perf (8.9.x): a 1:1 group whose target is new and fed by nothing else is
    # simply renamed (same weights, no per-vertex copy); only the rest, and
    # the spine split, are walked vertex by vertex.
    import numpy as np
    from .skin_gen import _weight_table
    spine_targets = {seg[0] for seg in spine_segs}
    fed = {}
    for src, dst in one_to_one.items():
        fed.setdefault(dst, []).append(src)
    renamed = set()
    for dst, sources in fed.items():
        src = sources[0]
        if (len(sources) == 1 and dst not in spine_targets and groups.get(dst) is None
                and groups.get(src) is not None):
            groups[src].name = dst
            renamed.add(src)
    gid = {g.index: g.name for g in groups}
    vi, gi, w = _weight_table(mesh_obj)
    live = w > 0.0
    adds = {}
    copy_index = {g.index: one_to_one[g.name] for g in groups
                  if g.name in one_to_one and g.name not in renamed}
    for index, dst in copy_index.items():
        rows = live & (gi == index)
        adds.setdefault(dst, []).extend(zip(vi[rows].tolist(), w[rows].tolist()))
    spine_index = [g.index for g in groups if g.name in spine_groups]
    if spine_index and spine_segs:
        rows = live & np.isin(gi, spine_index)
        spine_w = np.bincount(vi[rows], weights=w[rows], minlength=len(mesh_obj.data.vertices))
        verts = np.nonzero(spine_w > 0.0)[0]
        m = np.array(to_arm, dtype=np.float64)
        co = np.empty(len(mesh_obj.data.vertices) * 3, dtype=np.float64)
        mesh_obj.data.vertices.foreach_get("co", co)
        pts = co.reshape(-1, 3)[verts] @ m[:3, :3].T + m[:3, 3]
        best_d = np.full(len(verts), np.inf)
        param = np.zeros(len(verts))
        for i, (_n, h, t) in enumerate(spine_segs):
            h = np.array(h, dtype=np.float64)
            d = np.array(t, dtype=np.float64) - h
            dd = max(float(d @ d), 1e-12)
            u = np.clip((pts - h) @ d / dd, 0.0, 1.0)
            diff = pts - h - u[:, None] * d
            dist = np.sqrt((diff * diff).sum(axis=1))
            closer = dist < best_d
            best_d[closer] = dist[closer]
            param[closer] = starts[i] + u[closer] * lens[i]
        for vert, total, prm in zip(verts.tolist(), spine_w[verts].tolist(), param.tolist()):
            for i, f in spine_split(prm, centers).items():
                if f > 0.0:
                    adds.setdefault(spine_segs[i][0], []).append((vert, total * f))
    for gname, entries in adds.items():
        vg = target(gname)
        for idx, weight in entries:
            vg.add([idx], weight, 'ADD')
    for name in list(one_to_one) + list(spine_groups):
        vg = groups.get(name)
        if vg is not None:
            groups.remove(vg)


def integrate_control_rig(armature_obj, spec=None, context=None):
    """Build the engine rig fitted to, and driving, a wizard skeleton."""
    import bpy
    from . import rig_build
    if context is None:
        context = bpy.context
    arm = armature_obj.data
    meshes = _skinned_meshes(bpy, armature_obj)

    # 1) wizard joints (armature space) before anything changes
    wiz_bones = {b.name: (tuple(b.head_local), tuple(b.tail_local)) for b in arm.bones}
    wiz_deform = {b.name for b in arm.bones if b.use_deform}
    targets = wizard_joint_targets(wiz_bones)

    # 2) move every wizard bone aside so no engine name can collide
    for b in list(arm.bones):
        old = b.name
        b.name = WIZ_PREFIX + old
        for ob in meshes:
            _rename_group(ob, old, WIZ_PREFIX + old)

    # 3) build the engine rig on the fitted template (fingers stay the
    # wizard's own, if any, so the engine does not add unweighted digits)
    spec = spec or rig_build.RigSpec()
    spec = rig_build.RigSpec(**{**spec.__dict__, "fingers": False})
    plan = rig_build.compute_build_plan(spec)
    fit_plan(plan, targets)
    rig_build.apply_build_plan(plan, armature_obj, context)

    # 4) weights: 1:1 limbs/neck/head, spine split by height
    one_to_one = {WIZ_PREFIX + k: v for k, v in weight_transfer_map(wiz_bones).items()}
    spine_groups = {WIZ_PREFIX + n for n in wiz_bones
                    if n == "spine" or n.startswith("spine.")}
    spine_segs = [(n,) + plan_bone for n in _ENGINE_SPINE
                  for plan_bone in [next(((bd.head, bd.tail) for bd in plan.bones
                                          if bd.name == n), None)] if plan_bone]
    for ob in meshes:
        _transfer_weights(ob, armature_obj, one_to_one, spine_groups, spine_segs)

    # 5) keep other skinned wizard bones (fingers, toes, face) following the
    # nearest engine deform bone; delete every other wizard bone
    still_weighted = _weighted_group_names(meshes)
    engine_def = [bd for bd in plan.bones if bd.deform]
    keep = [name for name in wiz_bones
            if name in wiz_deform and WIZ_PREFIX + name in still_weighted]
    # also keep the structure those bones hang from (e.g. a face rig's
    # face_root / jaw_root: dropping them would stop the jaw opening), up to
    # the first wizard bone the engine replaces (spine / limbs / neck / head)
    replaced = set(weight_transfer_map(wiz_bones)) | {
        n for n in wiz_bones if n == "spine" or n.startswith("spine.")}
    parent_of = {b.name[len(WIZ_PREFIX):]: (b.parent.name[len(WIZ_PREFIX):] if b.parent else None)
                 for b in arm.bones}
    for name in list(keep):
        p = parent_of.get(name)
        while p is not None and p not in replaced and p not in keep:
            keep.append(p)
            p = parent_of.get(p)
    drop = [WIZ_PREFIX + name for name in wiz_bones if name not in keep]
    context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='EDIT')
    try:
        ebs = arm.edit_bones
        kept_names = {}
        for name in keep:
            eb = ebs.get(WIZ_PREFIX + name)
            if eb is None:
                continue
            best = min(engine_def, key=lambda bd: _point_segment_dist(
                tuple(eb.head), bd.head, bd.tail)[0])
            # a kept wizard bone keeps its wizard parent when that is kept too
            parent = eb.parent
            if parent is None or parent.name[len(WIZ_PREFIX):] not in keep:
                eb.parent = ebs.get(best.name)
                eb.use_connect = False
            new = name if ebs.get(name) is None else name + ".wiz"
            kept_names[WIZ_PREFIX + name] = new
        for wname in drop:
            eb = ebs.get(wname)
            if eb is not None:
                ebs.remove(eb)
        for wname, new in kept_names.items():
            eb = ebs.get(wname)
            if eb is not None:
                eb.name = new
    finally:
        bpy.ops.object.mode_set(mode='POSE')
    for ob in meshes:
        for wname, new in kept_names.items():
            _rename_group(ob, wname, new)
        for wname in drop:
            vg = ob.vertex_groups.get(wname)
            if vg is not None:
                ob.vertex_groups.remove(vg)
    bpy.ops.object.mode_set(mode='OBJECT')
    return plan


# ------------------------------------------------------------ twist bones

def twist_fractions(segments):
    """Share of the hand's twist each forearm twist bone picks up (pure).

    ``segments`` twist bones split the forearm with the plain ``forearm.def``
    part into ``segments + 1`` equal parts; a part picks up the twist in
    proportion to how far along the forearm its centre sits.
    """
    n = segments + 1
    return [(i + 0.5) / n for i in range(1, n)]


def split_weight(param, segments):
    """Split one unit of forearm weight between the forearm part centres."""
    n = segments + 1
    centres = [(i + 0.5) / n for i in range(n)]
    return spine_split(param, centres)


def twist_bone_names(side, segments):
    return ["forearm.twist.%02d-%s" % (i, side) for i in range(1, segments + 1)]


def add_twist_bones(armature_obj, segments=2, context=None):
    """Add forearm twist bones to an integrated rig and share out its skin.

    Each twist bone copies a fraction of the hand's twist (its local Y
    rotation), so a turned wrist twists the forearm gradually instead of
    pinching it at the wrist ("candy wrapper"). Idempotent per side.
    Returns the names of the bones added.
    """
    import bpy
    if context is None:
        context = bpy.context
    arm = armature_obj.data
    meshes = _skinned_meshes(bpy, armature_obj)
    added = []
    context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='EDIT')
    try:
        ebs = arm.edit_bones
        for side in ("L", "R"):
            fore = ebs.get("forearm.def-" + side)
            if fore is None or ebs.get(twist_bone_names(side, segments)[0]) is not None:
                continue
            head, tail, roll = fore.head.copy(), fore.tail.copy(), fore.roll
            n = segments + 1
            for i, name in enumerate(twist_bone_names(side, segments), start=1):
                eb = ebs.new(name)
                eb.head = head.lerp(tail, i / n)
                eb.tail = head.lerp(tail, (i + 1) / n)
                eb.roll = roll
                eb.parent = fore
                eb.use_connect = False
                eb.use_deform = True
                added.append(name)
    finally:
        bpy.ops.object.mode_set(mode='POSE')
    for side in ("L", "R"):
        names = [n for n in twist_bone_names(side, segments) if n in added]
        if not names:
            continue
        for name, frac in zip(names, twist_fractions(segments)):
            con = armature_obj.pose.bones[name].constraints.new('COPY_ROTATION')
            con.name = "BF_TWIST"
            con.target = armature_obj
            con.subtarget = "hand.def-" + side
            con.use_x, con.use_y, con.use_z = False, True, False
            con.owner_space = con.target_space = 'LOCAL'
            con.influence = frac
        coll = arm.collections.get("Deform")
        if coll is not None:
            for name in names:
                coll.assign(arm.bones[name])
        _split_forearm_weights(armature_obj, meshes, side, names, segments)
    bpy.ops.object.mode_set(mode='OBJECT')
    return added


def _split_forearm_weights(armature_obj, meshes, side, names, segments):
    fore = armature_obj.data.bones["forearm.def-" + side]
    world = armature_obj.matrix_world
    h, t = world @ fore.head_local, world @ fore.tail_local
    d = t - h
    dd = max(d.dot(d), 1e-12)
    part_names = ["forearm.def-" + side] + names
    for ob in meshes:
        src = ob.vertex_groups.get("forearm.def-" + side)
        if src is None:
            continue
        groups = [ob.vertex_groups.get(n) or ob.vertex_groups.new(name=n) for n in part_names]
        mw = ob.matrix_world
        moves = []
        for v in ob.data.vertices:
            for ge in v.groups:
                if ge.group == src.index and ge.weight > 0.0:
                    p = mw @ v.co
                    u = max(0.0, min(1.0, (p - h).dot(d) / dd))
                    moves.append((v.index, ge.weight, split_weight(u, segments)))
                    break
        for vi, w, split in moves:
            groups[0].add([vi], w * split.get(0, 0.0), 'REPLACE')
            for k, f in split.items():
                if k > 0 and f > 0.0:
                    groups[k].add([vi], w * f, 'ADD')
