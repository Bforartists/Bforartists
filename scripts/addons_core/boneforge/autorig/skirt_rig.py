"""Skirt bones for dresses and skirts (BFA).

A dress bound only to the hips stays put when a leg lifts, and the thigh
punches through the front of it. This pass finds skin that hangs below the
hips all the way around the body (a skirt, not trousers: trousers are
weighted to the legs), puts a ring of two-bone chains from the hips to the
hem (``skirt.NN`` waist -> middle, ``skirt.NN.lower`` middle -> hem), and
gives the fabric to them, fading in from the waist.

The upper bone aims at a middle target, the lower bone at a hem target
(damped track); each target is carried
partly by the hips and partly by the thighs, weighted by how much that part of
the hem sits in front of or beside each leg (an Armature constraint blends
the three bones), and is pushed out of a leg's way: it never comes closer to
points along the thigh than it sits at rest. With one bone per panel the
fabric near the waist pivot could not move and a high kick came through the
top of the dress; the middle joint lets the upper half flare out of the way. Lifting a leg swings the panels in
front of it forward with it; the back of the skirt keeps hanging from the
hips.

Clean-room: a first-principles ring of aim bones; no third-party rig is
referenced.
"""
import math

SKIRT_SECTORS = 8
MIN_SECTOR_VERTICES = 6
MIN_SECTORS = 6              # hangs (nearly) all the way around the body
MAX_LEG_SHARE = 1.0          # both legs together at most fully carry a hem target
SKIRT_MID = 0.45             # where each panel's two bones meet, down from the waist


# ------------------------------------------------------------ pure helpers

def sector_of(angle, count=SKIRT_SECTORS):
    """Sector index for an angle in radians (sector 0 centred on angle 0)."""
    step = 2.0 * math.pi / count
    return int(math.floor((angle + 0.5 * step) / step)) % count


def skirt_sectors(points, centre, top_z, count=SKIRT_SECTORS):
    """Per-sector shape of a skirt from its vertex positions (pure).

    ``points`` are (x, y, z); ``centre`` the (x, y) of the body axis. Returns
    ``{sector: {"angle", "r_top", "r_mid", "z_mid", "r_hem", "z_hem", "n"}}``:
    ``r_top`` is the median radius in the top fifth, ``r_mid`` the median
    radius around ``z_mid`` (``SKIRT_MID`` of the way down), ``r_hem`` /
    ``z_hem`` the median radius and the lowest height of the bottom fifth.
    """
    by = {}
    for x, y, z in points:
        dx, dy = x - centre[0], y - centre[1]
        by.setdefault(sector_of(math.atan2(dy, dx), count), []).append((math.hypot(dx, dy), z))
    out = {}
    step = 2.0 * math.pi / count
    for k, pts in by.items():
        zs = sorted(z for _r, z in pts)
        z_lo, z_hi = zs[0], zs[-1]
        span = max(z_hi - z_lo, 1e-9)
        top = sorted(r for r, z in pts if z >= z_hi - 0.2 * span) or [0.0]
        hem = sorted(r for r, z in pts if z <= z_lo + 0.2 * span) or [0.0]
        z_mid = top_z - SKIRT_MID * (top_z - z_lo)
        mid = sorted(r for r, z in pts if abs(z - z_mid) <= 0.12 * span) or \
            [0.5 * (top[len(top) // 2] + hem[len(hem) // 2])]
        out[k] = {"angle": k * step, "r_top": top[len(top) // 2],
                  "r_mid": mid[len(mid) // 2], "z_mid": z_mid,
                  "r_hem": hem[len(hem) // 2], "z_hem": z_lo, "n": len(pts)}
    return out


def leg_shares(direction, lateral_left, forward):
    """How much a hem point in ``direction`` (unit 2D) follows each thigh.

    A leg lifts forward, so a point follows a leg by how much it faces that
    leg's front-side diagonal. Returns (left, right, hips), summing to 1.
    """
    def unit(v):
        n = math.hypot(v[0], v[1]) or 1.0
        return (v[0] / n, v[1] / n)
    diag_l = unit((lateral_left[0] + forward[0], lateral_left[1] + forward[1]))
    diag_r = unit((-lateral_left[0] + forward[0], -lateral_left[1] + forward[1]))
    # a panel facing a leg follows it fully (it starts outside the thigh, so
    # following keeps it outside; a partial follow let the thigh through the
    # front and side of a dress at a high kick); the reach tapers round to
    # the back, which keeps hanging from the hips
    wl = min(1.0, 1.25 * max(0.0, direction[0] * diag_l[0] + direction[1] * diag_l[1]) ** 0.7)
    wr = min(1.0, 1.25 * max(0.0, direction[0] * diag_r[0] + direction[1] * diag_r[1]) ** 0.7)
    total = wl + wr
    if total > MAX_LEG_SHARE:
        wl, wr = wl * MAX_LEG_SHARE / total, wr * MAX_LEG_SHARE / total
    return wl, wr, 1.0 - wl - wr


def chain_split(depth, mid=SKIRT_MID, blend=0.12):
    """Share of a skirt vertex on the (upper, lower) bone of its panel (pure);
    ``depth`` runs 0 at the waist to 1 at the hem."""
    lower = smoothstep(mid - blend, mid + blend, depth)
    return 1.0 - lower, lower


def angular_blend(angle, sector_angles):
    """The two nearest bones around the ring and their shares (pure).

    ``sector_angles`` maps bone index -> angle. Returns [(index, share), ...]
    with shares summing to 1 (one entry when only one bone exists).
    """
    if not sector_angles:
        return []
    def gap(a, b):
        d = (a - b) % (2.0 * math.pi)
        return min(d, 2.0 * math.pi - d)
    near = sorted(sector_angles.items(), key=lambda kv: gap(angle, kv[1]))[:2]
    if len(near) == 1:
        return [(near[0][0], 1.0)]
    (i0, a0), (i1, a1) = near
    d0, d1 = gap(angle, a0), gap(angle, a1)
    total = d0 + d1
    if total <= 1e-12:
        return [(i0, 1.0)]
    return [(i0, d1 / total), (i1, d0 / total)]


def smoothstep(e0, e1, x):
    if e1 == e0:
        return 1.0 if x >= e1 else 0.0
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3.0 - 2.0 * t)


# ------------------------------------------------------------ main

def _pieces_with(bpy, meshes, candidates, min_hits=20):
    """Per mesh, ``{vertex: True}`` for vertices whose loose piece holds at
    least ``min_hits`` of ``candidates``."""
    import numpy as np
    out = {}
    for ob in meshes:
        hits = {vi for vi, _p in candidates.get(ob.name, [])}
        if len(hits) < min_hits:
            continue
        n = len(ob.data.vertices)
        parent = np.arange(n)

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        ev = np.empty(len(ob.data.edges) * 2, dtype=np.int64)
        ob.data.edges.foreach_get("vertices", ev)
        for a, b in ev.reshape(-1, 2).tolist():
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
        count = {}
        for vi in hits:
            r = find(vi)
            count[r] = count.get(r, 0) + 1
        good = {r for r, c in count.items() if c >= min_hits}
        out[ob.name] = {vi: True for vi in range(n) if find(vi) in good}
    return out


def add_skirt_bones(armature_obj, context=None):
    """Give a skirt / dress its own bones on an integrated control rig.

    Returns an info dict; skips (with a reason) when the rig has no hips /
    thighs, already has skirt bones, or no skin hangs below the hips all the
    way around.
    """
    import bpy
    from mathutils import Vector
    from .rig_integrate import _skinned_meshes
    from .skin_gen import _bone_kind, _bone_side
    if context is None:
        context = bpy.context
    arm = armature_obj.data
    info = {"built": [], "skipped": []}
    if any(b.name.startswith("skirt.") for b in arm.bones):
        info["skipped"].append("already has skirt bones")
        return info
    hips, thigh_l, thigh_r = arm.bones.get("hips"), arm.bones.get("thigh.def-L"), arm.bones.get("thigh.def-R")
    if hips is None or thigh_l is None or thigh_r is None:
        info["skipped"].append("no hips / thigh deform bones")
        return info
    aw = armature_obj.matrix_world
    arm_inv = aw.inverted()
    hl, hr = thigh_l.head_local, thigh_r.head_local
    thigh_len = 0.5 * (thigh_l.length + thigh_r.length)
    # the ring starts a little above the hip joints: a lifted thigh's top
    # rises above the joint into the fabric there, which must be free to lift
    top_z = 0.5 * (hl.z + hr.z) + 0.12 * thigh_len                 # armature space
    centre = ((hl.x + hr.x) * 0.5, (hl.y + hr.y) * 0.5)
    lateral_left = ((hl.x - hr.x), (hl.y - hr.y))
    # the front: the way the knees point from the hips
    knee_mid = (thigh_l.tail_local + thigh_r.tail_local) * 0.5
    fwd = (knee_mid.x - centre[0], knee_mid.y - centre[1])
    if math.hypot(*fwd) < 1e-4 * thigh_len:
        fwd = (0.0, -1.0)
    n = math.hypot(*fwd)
    fwd = (fwd[0] / n, fwd[1] / n)

    # Skirt fabric: skin below the hips that is not hugging a leg. Leg skin
    # and boots sit within about a leg radius of the thigh / shin bones; the
    # fabric and anything hanging from it (hem trim pinned to whichever bone
    # was nearest) hangs well away from them.
    torso = {b.name for b in arm.bones if b.use_deform and _bone_kind(b.name) == "torso"
             and not _bone_side(b.name)}
    legs = [(b.head_local, b.tail_local) for b in arm.bones if b.use_deform
            and _bone_kind(b.name) in ("thigh", "shin")]
    leg_kinds = ("thigh", "shin", "foot")

    def leg_dist(p):
        best = float("inf")
        for h, t in legs:
            d = t - h
            u = max(0.0, min(1.0, (p - h).dot(d) / max(d.dot(d), 1e-12)))
            best = min(best, (p - (h + d * u)).length)
        return best

    meshes = _skinned_meshes(bpy, armature_obj)
    below = []
    radii = []
    for ob in meshes:
        m = arm_inv @ ob.matrix_world
        names = {g.index: g.name for g in ob.vertex_groups}
        for v in ob.data.vertices:
            if not len(v.groups):
                continue
            p = m @ v.co
            if p.z >= top_z - 0.05 * thigh_len:
                continue
            owner = names.get(max(v.groups, key=lambda ge: ge.weight).group, "")
            dist = leg_dist(p)
            below.append((ob.name, v.index, p, owner, dist))
            if _bone_kind(owner) in ("thigh", "shin"):
                radii.append(dist)
    radii.sort()
    leg_radius = radii[len(radii) // 2] if radii else 0.1 * thigh_len
    # pass 1: the fabric the torso owns gives the skirt's shape
    candidates = {}
    points = []
    for ob_name, vi, p, owner, dist in below:
        if owner in torso and dist >= 1.6 * leg_radius:
            candidates.setdefault(ob_name, []).append((vi, p))
            points.append((p.x, p.y, p.z))
    # pass 1b: the rest of those same pieces of cloth. Around the hips the
    # dress (and any inner layer) sits close to the top of the thigh and was
    # often weighted to it; left on the thigh / hips there, a lifted thigh
    # dragged it or came through it. Anything below the waist that belongs to
    # a loose piece already found to be skirt fabric is fabric too (the body
    # under the dress is a different piece).
    fabric_parts = _pieces_with(bpy, meshes, candidates, min_hits=20)
    have = {(o, vi) for o, lst in candidates.items() for vi, _p in lst}
    for ob_name, vi, p, owner, dist in below:
        if (ob_name, vi) in have or _bone_kind(owner) == "foot" or dist < 1.2 * leg_radius:
            continue
        if fabric_parts.get(ob_name, {}).get(vi):
            candidates.setdefault(ob_name, []).append((vi, p))
            points.append((p.x, p.y, p.z))
    shape = skirt_sectors(points, centre, top_z) if points else {}
    # pass 2: pieces hanging within that outline (hem trim pinned elsewhere):
    # from the waist to a little below the hem, at least as far out as the
    # fabric on that side, not on a leg, not a foot
    taken = {(ob_name, vi) for ob_name, lst in candidates.items() for vi, _p in lst}
    for ob_name, vi, p, owner, dist in below:
        if (ob_name, vi) in taken or _bone_kind(owner) == "foot" or dist < 2.0 * leg_radius:
            continue
        sct = shape.get(sector_of(math.atan2(p.y - centre[1], p.x - centre[0])))
        if sct is None or sct["n"] < MIN_SECTOR_VERTICES:
            continue
        span = max(top_z - sct["z_hem"], 1e-6)
        radius = math.hypot(p.x - centre[0], p.y - centre[1])
        if p.z >= sct["z_hem"] - 0.3 * span and radius >= 0.8 * min(sct["r_top"], sct["r_hem"]):
            candidates.setdefault(ob_name, []).append((vi, p))
            points.append((p.x, p.y, p.z))
    info["leg_radius"] = round(leg_radius, 4)
    sectors = skirt_sectors(points, centre, top_z)
    used = {k: sct for k, sct in sectors.items() if sct["n"] >= MIN_SECTOR_VERTICES}
    info["sectors"] = {k: sct["n"] for k, sct in sorted(sectors.items())}
    if len(used) < MIN_SECTORS:
        info["skipped"].append("no skirt: skin below the hips covers %d of %d sides"
                               % (len(used), SKIRT_SECTORS))
        return info

    # --- bones
    context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='EDIT')
    try:
        ebs = arm.edit_bones
        parent = ebs["hips"]
        for k, sct in sorted(used.items()):
            d = (math.cos(sct["angle"]), math.sin(sct["angle"]))
            head = Vector((centre[0] + d[0] * 0.5 * sct["r_top"],
                           centre[1] + d[1] * 0.5 * sct["r_top"], top_z))
            midp = Vector((centre[0] + d[0] * sct["r_mid"], centre[1] + d[1] * sct["r_mid"], sct["z_mid"]))
            tail = Vector((centre[0] + d[0] * sct["r_hem"], centre[1] + d[1] * sct["r_hem"], sct["z_hem"]))
            if (tail - head).length < 0.05 * thigh_len:
                continue
            up_b = ebs.new("skirt.%02d" % k)
            up_b.head, up_b.tail = head, midp
            up_b.parent, up_b.use_connect, up_b.use_deform = parent, False, True
            up_b.align_roll(Vector((d[0], d[1], 0.0)))
            lo_b = ebs.new("skirt.%02d.lower" % k)
            lo_b.head, lo_b.tail = midp, tail
            lo_b.parent, lo_b.use_connect, lo_b.use_deform = up_b, True, True
            lo_b.align_roll(Vector((d[0], d[1], 0.0)))
            info["built"] += [up_b.name, lo_b.name]
            for tname, at in (("MCH-skirt_mid.%02d" % k, midp), ("MCH-skirt_target.%02d" % k, tail)):
                tb = ebs.new(tname)
                tb.head, tb.tail = at, at + Vector((0, 0, -0.05 * thigh_len))
                tb.parent, tb.use_deform = None, False
                info["built"].append(tname)
    finally:
        bpy.ops.object.mode_set(mode='POSE')

    pbs = armature_obj.pose.bones
    angles = {}
    for k, sct in used.items():
        name = "skirt.%02d" % k
        if name not in pbs:
            continue
        angles[k] = sct["angle"]
        d = (math.cos(sct["angle"]), math.sin(sct["angle"]))
        wl, wr, wh = leg_shares(d, lateral_left, fwd)
        # each target: carried by hips + thighs, then pushed out of a leg's
        # way — it never comes closer to points along the thigh than at rest
        # (a fixed blend cannot know which leg moves; the panels between the
        # legs lagged a single kick)
        for tname, bone_name, alongs in (("MCH-skirt_mid.%02d" % k, name, (0.15, 0.4, 0.7)),
                                         ("MCH-skirt_target.%02d" % k, name + ".lower", (0.6, 1.0))):
            tpb = pbs[tname]
            con = tpb.constraints.new('ARMATURE')
            con.name = "BF_SKIRT_CARRY"
            for bone, w in (("hips", wh), ("thigh.def-L", wl), ("thigh.def-R", wr)):
                if w > 1e-4:
                    t = con.targets.new()
                    t.target, t.subtarget, t.weight = armature_obj, bone, w
            rest = arm.bones[tname].head_local
            for leg in ("thigh.def-L", "thigh.def-R"):
                lb = arm.bones[leg]
                for along in alongs:
                    push = tpb.constraints.new('LIMIT_DISTANCE')
                    push.name = "BF_SKIRT_PUSH"
                    push.target, push.subtarget, push.head_tail = armature_obj, leg, along
                    push.limit_mode = 'LIMITDIST_OUTSIDE'
                    push.distance = (rest - lb.head_local.lerp(lb.tail_local, along)).length
            aim = pbs[bone_name].constraints.new('DAMPED_TRACK')
            aim.name = "BF_SKIRT_AIM"
            aim.target, aim.subtarget, aim.track_axis = armature_obj, tname, 'TRACK_Y'
        info.setdefault("leg_shares", {})[name] = [round(wl, 2), round(wr, 2)]
    for bname in info["built"]:
        b = arm.bones[bname]
        coll_name = "Deform" if b.use_deform else "MCH"
        coll = arm.collections.get(coll_name) or arm.collections.new(coll_name)
        coll.assign(b)
        if not b.use_deform:
            b.hide = True
    bpy.ops.object.mode_set(mode='OBJECT')

    # --- weights: fabric fades from the torso (waist) onto the ring
    moved = 0
    for ob in meshes:
        groups = {}
        for k in angles:
            for suffix in ("", ".lower"):
                gname = "skirt.%02d%s" % (k, suffix)
                groups[(k, suffix)] = ob.vertex_groups.get(gname) or ob.vertex_groups.new(name=gname)
        names = {g.index: g.name for g in ob.vertex_groups}
        for vi, p in candidates.get(ob.name, []):
            ang = math.atan2(p.y - centre[1], p.x - centre[0])
            k0 = sector_of(ang)
            hem_z = used.get(k0, {}).get("z_hem", min(s["z_hem"] for s in used.values()))
            depth = (top_z - p.z) / max(top_z - hem_z, 1e-6)
            v_share = smoothstep(0.0, 0.15, depth)
            if v_share <= 0.0:
                continue
            v = ob.data.vertices[vi]
            for ge in v.groups:
                if not names.get(ge.group, "").startswith("skirt."):
                    ge.weight *= (1.0 - v_share)
            upper, lower = chain_split(depth)
            for k, share in angular_blend(ang, angles):
                if upper > 0.0:
                    groups[(k, "")].add([vi], v_share * share * upper, 'ADD')
                if lower > 0.0:
                    groups[(k, ".lower")].add([vi], v_share * share * lower, 'ADD')
            moved += 1
    info["vertices"] = moved
    return info


# ------------------------------------------------------------ operator

def _register_classes():
    import bpy

    class BONEFORGE_OT_add_skirt_bones(bpy.types.Operator):
        """Add a ring of two-bone skirt chains that follow the legs to a rig with a dress or skirt"""
        bl_idname = "boneforge.add_skirt_bones"
        bl_label = "Add Skirt Bones"
        bl_options = {'REGISTER', 'UNDO'}

        @classmethod
        def poll(cls, context):
            ob = context.active_object
            return ob is not None and ob.type == 'ARMATURE' and "hips" in ob.data.bones

        def execute(self, context):
            info = add_skirt_bones(context.active_object, context)
            if not info["built"]:
                self.report({'WARNING'}, "; ".join(info["skipped"]) or "nothing to add")
                return {'CANCELLED'}
            self.report({'INFO'}, "Skirt: %d bones, %d vertices"
                        % (len([b for b in info["built"] if b.startswith("skirt.")]), info["vertices"]))
            return {'FINISHED'}

    return (BONEFORGE_OT_add_skirt_bones,)


_classes = ()


def register():
    import bpy
    global _classes
    _classes = _register_classes()
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    import bpy
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
