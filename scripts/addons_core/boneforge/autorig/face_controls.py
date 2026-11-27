"""Working face controls for wizard characters (BFA).

The wizard's face markers give landmark bones (eyes, brows, lips, chin, jaw
hinge). This pass turns them into an animatable face on the control rig:

- **Eye aim** - each eye bone is moved to the centre of its eyeball mesh and
  tracks an ``eye.ik`` target in front of the face; both targets hang from an
  ``eye_master`` control. The eyeball's vertices are bound to the eye bone
  alone; the skin the landmark bone used to move goes to an ``eye_area`` bone
  at the old landmark, so nothing it did is lost.
- **Lids** - a ``blink`` property per side drives blink shape keys
  (``BF_blink_half.<side>`` and ``BF_blink.<side>``). Each lid vertex turns
  about the eyeball centre by its own share of the close angle, so the lid
  slides over the eyeball instead of cutting through it (two lid bones blended
  linearly did, and the lid crumpled); the share fades toward the eye corners,
  where the lids already meet, and away from the rim. The half-blink key keeps
  the lid on the eyeball's curve mid-blink. The upper lid does most of the
  travel, as in a real blink. Shape keys also survive game export.
- **Lip follow** - mouth-corner bones follow the jaw by ``soft_lips`` x 0.5,
  reduced toward zero by ``sticky_lips``, so an open jaw stretches the corners
  instead of leaving them behind or dragging them fully.

Everything is measured from the character (eyeball islands, lid rims, marker
spacing); nothing is a fixed template size. Clean-room, first-principles.
"""
import math

PROPS_BONE = "face_props"
EYE_MASTER = "eye_master"
BLINK_UPPER_SHARE = 0.75      # share of the opening the upper lid travels


# ------------------------------------------------------------ pure helpers

def smoothstep(e0, e1, x):
    if e1 == e0:
        return 1.0 if x >= e1 else 0.0
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3.0 - 2.0 * t)


def lid_close_angles(theta_upper, theta_lower, upper_share=BLINK_UPPER_SHARE):
    """Rotations (radians) that bring the upper rim (elevation ``theta_upper``
    above the eye's forward axis) and lower rim (``theta_lower``, negative) to
    a common meeting line. Upper closes by a positive angle, lower by negative.
    """
    gap = max(theta_upper - theta_lower, 0.0)
    return upper_share * gap, -(1.0 - upper_share) * gap


def lid_lateral_share(lateral, eye_radius):
    """How much of the close angle a lid vertex gets across the eye's width:
    full over the pupil, easing to none at the corners, where the lids
    already meet (a lid closing evenly to its corners folded there)."""
    x = abs(lateral) / max(1.15 * eye_radius, 1e-9)
    return max(0.0, 1.0 - x * x) ** 0.5 if x < 1.0 else 0.0


def meet_line(theta_upper, theta_lower, upper_share=BLINK_UPPER_SHARE):
    """Elevation where the lids meet when closed (see lid_close_angles)."""
    return theta_upper - upper_share * max(theta_upper - theta_lower, 0.0)


def interpolate(points, x):
    """Piecewise-linear lookup in sorted (x, y) points, clamped at the ends."""
    if not points:
        return 0.0
    if x <= points[0][0]:
        return points[0][1]
    if x >= points[-1][0]:
        return points[-1][1]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * ((x - x0) / (x1 - x0) if x1 > x0 else 0.0)
    return points[-1][1]


def opening_profile(samples, centre_gap):
    """Normalised eye opening across the eye's width from measured slices.

    ``samples`` are (lateral in eye radii, rim gap or None). Returns a sorted
    list of (lateral, share 0..1), or None when too few slices were readable
    (a coarse mesh), in which case :func:`lid_lateral_share` is used.
    """
    good = [(x, g) for x, g in samples if g is not None]
    if len(good) < 5 or centre_gap <= 0.0:
        return None
    good.sort()
    # rims are read slice by slice; a 3-slice average removes the jitter
    # that turned into spikes along the closed lid
    smooth = []
    for i, (x, _g) in enumerate(good):
        window = [g for _x, g in good[max(0, i - 1):i + 2]]
        smooth.append((x, max(0.0, min(1.0, sum(window) / len(window) / centre_gap))))
    return smooth


def lateral_share(profile, x, eye_radius, lateral):
    """Share of the close angle at lateral position ``x`` (eye radii):
    interpolated from the measured opening, else the smooth fallback."""
    if not profile:
        return lid_lateral_share(lateral, eye_radius)
    if x <= profile[0][0]:
        return profile[0][1] if x >= profile[0][0] - 0.1 else 0.0
    if x >= profile[-1][0]:
        return profile[-1][1] if x <= profile[-1][0] + 0.1 else 0.0
    for (x0, s0), (x1, s1) in zip(profile, profile[1:]):
        if x0 <= x <= x1:
            t = (x - x0) / (x1 - x0) if x1 > x0 else 0.0
            return s0 + (s1 - s0) * t
    return 0.0


def lip_follow(soft_lips, sticky_lips):
    """Share of the jaw's motion the mouth corners pick up."""
    return max(0.0, min(1.0, 0.5 * soft_lips * (1.0 - sticky_lips)))


# ------------------------------------------------------------ mesh helpers

def _arm_coords(ob, m):
    """Vertex positions of ``ob`` in armature space, (N, 3) numpy array."""
    import numpy as np
    n = len(ob.data.vertices)
    co = np.empty(n * 3, dtype=np.float64)
    ob.data.vertices.foreach_get("co", co)
    mm = np.array(m, dtype=np.float64)
    return co.reshape(n, 3) @ mm[:3, :3].T + mm[:3, 3]


def _near(coords, centre, radius):
    """Indices of the rows of ``coords`` within ``radius`` of ``centre``."""
    import numpy as np
    d = coords - np.array(tuple(centre), dtype=np.float64)
    return np.nonzero((d * d).sum(axis=1) < radius * radius)[0]


def _eyeball(meshes, coords, near, max_dist, max_size):
    """The compact loose part closest to ``near`` (armature space):
    (mesh, vertex indices, centre, radius) or None.

    Only the neighbourhood of ``near`` is examined: loose parts are found
    among the edges inside it, and a part with an edge leaving it is not
    loose (it is a patch of a larger piece, e.g. the face skin).
    """
    import numpy as np
    from mathutils import Vector
    best = None
    for ob in meshes:
        co = coords[ob.name]
        count = len(co)
        region = _near(co, near, max_dist + max_size)
        if len(region) < 8:
            continue
        inside = np.zeros(count, dtype=bool)
        inside[region] = True
        ev = np.empty(len(ob.data.edges) * 2, dtype=np.int64)
        ob.data.edges.foreach_get("vertices", ev)
        ev = ev.reshape(-1, 2)
        a_in, b_in = inside[ev[:, 0]], inside[ev[:, 1]]
        both = ev[a_in & b_in]
        leaving = set(ev[a_in & ~b_in, 0].tolist()) | set(ev[b_in & ~a_in, 1].tolist())
        parent = {int(v): int(v) for v in region}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        for va, vb in both.tolist():
            ra, rb = find(va), find(vb)
            if ra != rb:
                parent[ra] = rb
        parts = {}
        for v in parent:
            parts.setdefault(find(v), []).append(v)
        for idx in parts.values():
            if len(idx) < 8 or len(idx) > count // 4 or any(v in leaving for v in idx):
                continue
            pts = co[idx]
            lo, hi = pts.min(axis=0), pts.max(axis=0)
            size = hi - lo
            if size.max() > max_size or size.min() < 0.5 * size.max():
                continue                                  # not an eyeball
            c = Vector(((lo + hi) * 0.5).tolist())
            d = (c - near).length
            if d < max_dist and (best is None or d < best[0]):
                best = (d, ob, sorted(idx), c, float(size.sum()) / 6.0)
    return None if best is None else best[1:]


def _edge_pairs(ob):
    import numpy as np
    ev = np.empty(len(ob.data.edges) * 2, dtype=np.int64)
    ob.data.edges.foreach_get("vertices", ev)
    return ev.reshape(-1, 2).tolist()


def smooth_over_edges(values, edges, passes=3):
    """Average a per-vertex value with its mesh neighbours (pure).

    Vertices outside ``values`` count as 0 and stay fixed, so the field
    eases to zero at its border. Neighbouring lid vertices turning by very
    different angles is what left a sawtooth along the closed lid.
    """
    neighbours = {}
    for a, b in edges:
        if a in values or b in values:
            neighbours.setdefault(a, []).append(b)
            neighbours.setdefault(b, []).append(a)
    current = dict(values)
    for _ in range(passes):
        nxt = {}
        for v, val in current.items():
            around = neighbours.get(v, [])
            if not around:
                nxt[v] = val
                continue
            mean = sum(current.get(n, 0.0) for n in around) / len(around)
            nxt[v] = 0.5 * val + 0.5 * mean
        current = nxt
    return {v: val for v, val in current.items() if abs(val) > 1e-5}


def mouth_follow_target(across, depth, corner_follow):
    """How much of the jaw's motion a lower-lip vertex should follow (pure).

    ``across``: 0 at the mouth centre, 1 at a corner. ``depth``: 0 at the lip
    seam, 1 a lip-thickness-and-a-half below it. On the lip the follow is an
    oval — full at the centre, easing to the corner's own follow at the
    corners — and it blends to full follow below the lip. A box (full follow
    to the corners) tore at the corners; a V (follow falling off from the
    centre) left the lip's sides behind.
    """
    oval = (1.0 - across * across) ** 0.5 if across < 1.0 else 0.0
    on_lip = corner_follow + (1.0 - corner_follow) * oval
    span = mouth_depth_span(across)
    return on_lip + (1.0 - on_lip) * smoothstep(0.4, 1.0, depth / span)


def mouth_depth_span(across):
    """How far below the lip seam (in ``depth`` units) the lip's follow
    blends to full, per position across the mouth (pure). At the centre the
    chin takes over right under the lip; toward and past the corners the
    blend runs three times deeper — reaching full follow right under the
    corner cut a vertical slit there, the corner looked pinched shut."""
    a = min(max(across, 0.0), 1.3)
    return 1.0 + 2.0 * min(1.0, a * a)


def _shape_mouth_opening(armature_obj, meshes, coords, B, corners, up, corner_follow):
    """Cap each lower-lip vertex's jaw follow at :func:`mouth_follow_target`,
    handing the excess to the static face bone the jaw hangs from."""
    from mathutils import Vector
    bones = armature_obj.data.bones
    jaw = bones.get("jaw_root")
    if jaw is None:
        return 0
    static = jaw.parent.name if jaw.parent is not None else None
    followers = {b.name for b in bones if b.use_deform and
                 (b.name == "jaw_root" or any(p.name == "jaw_root" for p in b.parent_recursive))}
    corner_names = {"lip.corner." + s for s in corners}
    seam_z = 0.5 * (B["lip_upper"][0].z + B["lip_lower"][0].z)
    thick = max(seam_z - B["lip_lower"][0].z, 1e-4) * 1.5
    mid = (B["lip_upper"][0] + B["lip_lower"][0]) * 0.5

    def flat(p):   # horizontal distance from the mouth centre
        d = p - mid
        return (d - up * d.dot(up)).length
    half = max((flat(p) for p in corners.values()), default=0.0)
    if half <= 0.0 or static is None:
        return 0
    shaped = 0
    for ob in meshes:
        co = coords[ob.name]
        names = {g.index: g.name for g in ob.vertex_groups}
        static_group = ob.vertex_groups.get(static) or ob.vertex_groups.new(name=static)
        for vi in _near(co, mid, 1.3 * half + 3.0 * thick).tolist():
            p = Vector(co[vi])
            depth = (seam_z - p.z) / thick
            across = flat(p) / half
            if depth < 0.0 or depth > mouth_depth_span(across):
                continue
            target = mouth_follow_target(min(across, 1.0), depth, corner_follow)
            v = ob.data.vertices[vi]
            follow_w = sum(ge.weight for ge in v.groups if names[ge.group] in followers)
            corner_w = sum(ge.weight for ge in v.groups if names[ge.group] in corner_names)
            total = sum(ge.weight for ge in v.groups if ge.weight > 0.0) or 1.0
            follow = (follow_w + corner_follow * corner_w) / total
            if follow <= target + 1e-3 or follow_w <= 0.0:
                continue
            # scale the jaw-following weights down; the static bone takes the rest
            keep = max(0.0, (target * total - corner_follow * corner_w) / follow_w)
            moved = 0.0
            for ge in v.groups:
                if names[ge.group] in followers:
                    moved += ge.weight * (1.0 - keep)
                    ge.weight *= keep
            static_group.add([vi], moved, 'ADD')
            shaped += 1
    return shaped


JAW_OPEN_DEG = 20.0


def _jaw_open_corrective(armature_obj, meshes, corners, context, jaw_deg=JAW_OPEN_DEG):
    """Both jaw-open keys: free corners, and corners held by sticky lips."""
    free = _jaw_open_key(armature_obj, meshes, corners, context, jaw_deg, sticky=False)
    held = _jaw_open_key(armature_obj, meshes, corners, context, jaw_deg, sticky=True)
    return {"free": free, "sticky": held}


def _jaw_open_key(armature_obj, meshes, corners, context, jaw_deg, sticky):
    """A shape key that rounds the mouth corners when the jaw opens.

    Weights alone leave the corners creased: the upper lip, the lower lip
    and the cheek meet there and follow the jaw by different amounts, so the
    open mouth shows a sharp bend in the lip line and a squeezed fold at each
    corner. With the jaw open ``jaw_deg``, the skin around each corner is
    relaxed (averaged with its neighbours, fading out away from the corner);
    the result is stored as ``BF_jaw_open`` and driven by the jaw angle.
    With sticky lips the corners stay put while the jaw drops, which creased
    them into sharp slits; ``BF_jaw_open_sticky`` is built with sticky lips
    on and relaxes the skin around each corner while leaving the corner
    itself where sticky lips hold it. The jaw angle drives both, the free key
    times (1 - sticky), the sticky key times sticky.
    """
    from mathutils import Vector
    from .joint_correctives import _new_key, _store_offsets
    pb = armature_obj.pose.bones.get("jaw_root")
    if pb is None or not corners:
        return {"skipped": "no jaw / corners"}
    aw = armature_obj.matrix_world
    wc = [aw @ c for c in corners.values()]
    half = 0.5 * (wc[0] - wc[-1]).length if len(wc) > 1 else 0.02
    # 0.9 of the half-width: wider (1.1) smoothed away the upper lip's shape
    radius = 0.9 * half
    iters = 8
    props = armature_obj.pose.bones.get(PROPS_BONE)
    prev_sticky = props["sticky_lips"] if props is not None and "sticky_lips" in props else None
    if prev_sticky is not None:
        props["sticky_lips"] = 1.0 if sticky else 0.0
    prev_mode, prev_rot = pb.rotation_mode, tuple(pb.rotation_euler)
    pb.rotation_mode = 'XYZ'
    pb.rotation_euler = (math.radians(jaw_deg), 0.0, 0.0)
    armature_obj.update_tag()
    context.view_layer.update()
    moved_total = 0
    try:
        for ob in meshes:
            mw = ob.matrix_world
            ev = ob.evaluated_get(context.evaluated_depsgraph_get()).data
            if len(ev.vertices) != len(ob.data.vertices):
                continue
            posed = [mw @ v.co for v in ev.vertices]
            rest = [mw @ v.co for v in ob.data.vertices]
            w = {}
            for i, p in enumerate(rest):
                d = min((p - c).length for c in wc)
                if d < radius:
                    w[i] = 1.0 - smoothstep(0.3 * radius, radius, d)
                    if sticky:          # the held corner is an anchor, not smoothed
                        w[i] *= smoothstep(0.1 * radius, 0.3 * radius, d)
            if not w:
                continue
            nbrs = {}
            for e in ob.data.edges:
                a, b = e.vertices
                if a in w or b in w:
                    nbrs.setdefault(a, []).append(b)
                    nbrs.setdefault(b, []).append(a)
            cur = {i: posed[i].copy() for i in set(nbrs) | set(w)}
            for _ in range(iters):
                nxt = dict(cur)
                for i, wi in w.items():
                    around = nbrs.get(i)
                    if not around:
                        continue
                    mean = sum((cur.get(n, posed[n]) for n in around), Vector()) / len(around)
                    nxt[i] = cur[i] + (mean - cur[i]) * 0.5 * wi
                cur = nxt
            targets = {i: cur[i] for i in w if (cur[i] - posed[i]).length > 1e-6}
            if not targets:
                continue
            key = _new_key(ob, "BF_jaw_open_sticky" if sticky else "BF_jaw_open")
            _store_offsets(ob, armature_obj, key, targets, posed)
            key.value = 0.0
            drv = key.driver_add("value").driver
            drv.type = 'SCRIPTED'
            var = drv.variables.new()
            var.name, var.type = "a", 'TRANSFORMS'
            t = var.targets[0]
            t.id, t.bone_target, t.transform_type, t.transform_space = armature_obj, "jaw_root", 'ROT_X', 'LOCAL_SPACE'
            # sticky lips hold the corners, so the corner smoothing fades with it
            k = drv.variables.new()
            k.name, k.type = "k", 'SINGLE_PROP'
            k.targets[0].id = armature_obj
            k.targets[0].data_path = 'pose.bones["%s"]["sticky_lips"]' % PROPS_BONE
            drv.expression = "min(1.5, max(0.0, a / %.6f)) * %s" % (
                math.radians(jaw_deg), "k" if sticky else "(1.0 - k)")
            moved_total += len(targets)
    finally:
        pb.rotation_euler = prev_rot
        pb.rotation_mode = prev_mode
        if prev_sticky is not None:
            props["sticky_lips"] = prev_sticky
        armature_obj.update_tag()
        context.view_layer.update()
    return {"vertices_moved": moved_total, "jaw_deg": jaw_deg}


def _reweight(ob, vi, group, w, deform_names, names):
    """Give ``w`` of vertex ``vi`` to ``group``, scaling its other deform
    weights by (1 - w) so the total is unchanged. ``names`` maps group
    index to name."""
    if w <= 0.0:
        return
    v = ob.data.vertices[vi]
    for ge in v.groups:
        if names[ge.group] in deform_names and names[ge.group] != group.name:
            ge.weight *= (1.0 - w)
    group.add([vi], w, 'ADD')


# ------------------------------------------------------------ main

def add_face_controls(armature_obj, context=None, soft_lips=0.6):
    """Add eye aim, lids and lip follow to a rig carrying wizard face bones.

    Returns an info dict (what was built, measured sizes, anything skipped).
    Idempotent: a rig that already has ``eye_master`` is left alone.
    """
    import bpy
    from mathutils import Vector, Matrix
    from .rig_integrate import _skinned_meshes
    if context is None:
        context = bpy.context
    arm = armature_obj.data
    info = {"built": [], "skipped": []}
    if EYE_MASTER in arm.bones or PROPS_BONE in arm.bones:
        info["skipped"].append("already has face controls")
        return info
    if "eye.L" not in arm.bones or "eye.R" not in arm.bones:
        info["skipped"].append("no wizard eye bones")
        return info
    meshes = _skinned_meshes(bpy, armature_obj)
    arm_inv = armature_obj.matrix_world.inverted()
    to_arm = {ob.name: arm_inv @ ob.matrix_world for ob in meshes}
    # every search below is local (eyes, lids, mouth corners): read the
    # positions once and visit only the vertices near each feature
    coords = {ob.name: _arm_coords(ob, to_arm[ob.name]) for ob in meshes}
    deform_names = {b.name for b in arm.bones if b.use_deform}

    B = {b.name: (b.head_local.copy(), b.tail_local.copy()) for b in arm.bones}
    eye_mk = {s: B["eye." + s][0] for s in ("L", "R")}
    spacing = (eye_mk["L"] - eye_mk["R"]).length
    up = Vector((0, 0, 1))
    if "nose_tip" in B and "jaw.L" in B and "jaw.R" in B:
        fwd = B["nose_tip"][0] - (B["jaw.L"][0] + B["jaw.R"][0]) * 0.5
    else:
        fwd = B["eye.L"][1] - B["eye.L"][0]
    fwd.z = 0.0
    fwd = fwd.normalized() if fwd.length > 1e-9 else Vector((0, -1, 0))
    lid_axis = up.cross(fwd).normalized()             # +rotation turns fwd -> down
    info["spacing"] = round(spacing, 4)

    # --- eyeballs -------------------------------------------------------
    eyes = {}
    for s in ("L", "R"):
        found = _eyeball(meshes, coords, eye_mk[s], 0.5 * spacing, 0.6 * spacing)
        if found is None:
            info["skipped"].append("no eyeball mesh for eye.%s (aim and lids need one)" % s)
            continue
        ob, idx, c, r = found
        eyes[s] = {"ob": ob, "idx": set(idx), "c": c, "r": r}
    if not eyes:
        return info

    # --- lid rims (the skin edge nearest the eye's forward axis) ---------
    def eye_coords(p, e):
        d = p - e["c"]
        return d.dot(fwd), d.dot(up), d.dot(lid_axis), d.length

    lids = {}
    def rims(e, band, at=0.0):
        """Upper / lower rim elevation of the eye opening, measured in the
        slice ``|lateral - at| <= band * r`` in front of the eyeball."""
        up_t, lo_t = None, None
        for ob in meshes:
            co = coords[ob.name]
            skip = e["idx"] if ob is e["ob"] else ()
            for vi in _near(co, e["c"], 1.6 * e["r"] + 1e-6).tolist():
                if vi in skip:
                    continue
                f, u, l, dist = eye_coords(Vector(co[vi]), e)
                if f <= 0.0 or abs(l - at * e["r"]) > band * e["r"] or dist > 1.6 * e["r"]:
                    continue
                t = math.atan2(u, f)
                if t >= 0 and (up_t is None or t < up_t):
                    up_t = t
                if t < 0 and (lo_t is None or t > lo_t):
                    lo_t = t
        return up_t, lo_t

    for s, e in eyes.items():
        # rims on the eye's own axis; widen the band for coarse meshes
        up_t, lo_t = rims(e, 0.3)
        if up_t is None or lo_t is None:
            up_t, lo_t = rims(e, 0.7)
        if up_t is None or lo_t is None:
            info["skipped"].append("no lid rims around eye.%s" % s)
            continue
        cu, cl = lid_close_angles(up_t, lo_t)
        # the opening across the eye's width: at each lateral slice, how far
        # apart the rims are relative to the centre (0 at the corners)
        profile, meets = [], []
        for k in range(-16, 17):
            su, sl = rims(e, 0.06, at=0.1 * k)
            gap = (su - sl) if su is not None and sl is not None else None
            profile.append((0.1 * k, gap))
            if gap is not None:
                meets.append((0.1 * k, meet_line(su, sl)))
        lids[s] = {"up_t": up_t, "lo_t": lo_t, "close_u": cu, "close_l": cl,
                   "profile": opening_profile(profile, up_t - lo_t),
                   "meet": meets if len(meets) >= 5 else [(0.0, meet_line(up_t, lo_t))]}
    info["lid_rims_deg"] = {s: [round(math.degrees(v["up_t"]), 1), round(math.degrees(v["lo_t"]), 1)]
                            for s, v in lids.items()}

    # --- mouth corners ----------------------------------------------------
    corners = {}
    if "lip_upper" in B and "lip_lower" in B and "jaw_root" in B:
        mid = (B["lip_upper"][0] + B["lip_lower"][0]) * 0.5
        side_dir = {"L": (eye_mk["L"] - eye_mk["R"]).normalized()}
        side_dir["R"] = -side_dir["L"]
        want = 0.38 * spacing
        tol = 0.08 * spacing
        for s in ("L", "R"):
            best = None
            for ob in meshes:
                co = coords[ob.name]
                for vi in _near(co, mid, 1.5 * spacing).tolist():
                    p = Vector(co[vi])
                    d = p - mid
                    if abs(d.dot(up)) > tol or abs(d.dot(side_dir[s]) - want) > tol:
                        continue
                    f = d.dot(fwd)
                    if best is None or f > best[0]:
                        best = (f, p)
            if best is not None:
                corners[s] = best[1]

    # --- bones --------------------------------------------------------------
    context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='EDIT')
    try:
        ebs = arm.edit_bones
        face_parent = ebs["eye.L"].parent

        def new(name, head, tail, parent, deform, roll_z=None):
            eb = ebs.new(name)
            eb.head, eb.tail = head, tail
            if roll_z is not None:
                eb.align_roll(roll_z)
            eb.parent = parent
            eb.use_connect = False
            eb.use_deform = deform
            info["built"].append(name)
            return eb

        mid_c = sum((e["c"] for e in eyes.values()), Vector()) / len(eyes)
        props = new(PROPS_BONE, mid_c + up * 0.9 * spacing,
                    mid_c + up * 1.1 * spacing, face_parent, False)
        dist = 2.0 * spacing
        master = new(EYE_MASTER, mid_c + fwd * dist, mid_c + fwd * (dist + 0.3 * spacing),
                     face_parent, False)
        for s, e in eyes.items():
            eye = ebs["eye." + s]
            # keep what the landmark bone did to the skin around the eye
            new("eye_area." + s, eye.head.copy(), eye.tail.copy(), eye.parent, True)
            eye.head = e["c"]
            eye.tail = e["c"] + fwd * 1.5 * e["r"]
            eye.align_roll(up)
            new("eye.ik." + s, e["c"] + fwd * dist, e["c"] + fwd * (dist + 0.2 * spacing),
                master, False)
        jaw = ebs.get("jaw_root")
        for s, p in corners.items():
            new("MCH-lip.corner.rest." + s, p, p + fwd * 0.1 * spacing, face_parent, False)
            new("MCH-lip.corner.jaw." + s, p, p + fwd * 0.1 * spacing, jaw, False)
            new("lip.corner." + s, p, p + fwd * 0.1 * spacing,
                ebs["MCH-lip.corner.rest." + s], True)
    finally:
        bpy.ops.object.mode_set(mode='POSE')

    pbs = armature_obj.pose.bones
    pp = pbs[PROPS_BONE]
    pp["soft_lips"] = soft_lips
    pp["sticky_lips"] = 0.0
    for s in lids:
        pp["blink." + s] = 0.0
    for key in pp.keys():
        ui = pp.id_properties_ui(key)
        ui.update(min=0.0, max=1.0, soft_min=0.0, soft_max=1.0)

    def driver(owner_path_obj, path, index, expr, var_props):
        fc = owner_path_obj.driver_add(path, index) if index is not None else owner_path_obj.driver_add(path)
        d = fc.driver
        d.type = 'SCRIPTED'
        for vname, prop in var_props:
            var = d.variables.new()
            var.name = vname
            var.type = 'SINGLE_PROP'
            var.targets[0].id = armature_obj
            var.targets[0].data_path = 'pose.bones["%s"]["%s"]' % (PROPS_BONE, prop)
        d.expression = expr

    for s in eyes:
        con = pbs["eye." + s].constraints.new('DAMPED_TRACK')
        con.name = "BF_EYE_AIM"
        con.target, con.subtarget = armature_obj, "eye.ik." + s
        con.track_axis = 'TRACK_Y'
    for s in corners:
        con = pbs["MCH-lip.corner.rest." + s].constraints.new('COPY_TRANSFORMS')
        con.name = "BF_LIP_FOLLOW"
        con.target, con.subtarget = armature_obj, "MCH-lip.corner.jaw." + s
        con.influence = lip_follow(soft_lips, 0.0)
        driver(con, "influence", None, "max(0.0, min(1.0, 0.5 * s * (1.0 - k)))",
               [("s", "soft_lips"), ("k", "sticky_lips")])

    for name in info["built"]:
        b = arm.bones[name]
        target = "Deform" if b.use_deform else ("MCH" if name.startswith("MCH") or name == PROPS_BONE else "Face")
        coll = arm.collections.get(target) or arm.collections.get("Face") or arm.collections.new(target)
        coll.assign(b)
        if name.startswith("MCH") or name == PROPS_BONE:
            b.hide = True
    bpy.ops.object.mode_set(mode='OBJECT')

    # --- weights ----------------------------------------------------------
    deform_names |= {n for n in info["built"] if arm.bones[n].use_deform}
    from .skin_gen import _weight_table
    tables = {ob.name: _weight_table(ob) for ob in meshes}     # one read per mesh
    for s, e in eyes.items():
        eye_name = "eye." + s
        for ob in meshes:
            src = ob.vertex_groups.get(eye_name)
            area = ob.vertex_groups.get("eye_area." + s) or ob.vertex_groups.new(name="eye_area." + s)
            if src is not None:
                vi, gi, w = tables[ob.name]
                rows = gi == src.index
                moves = [(v, wt) for v, wt in zip(vi[rows].tolist(), w[rows].tolist())
                         if not (ob is e["ob"] and v in e["idx"])]
                for vi_, wt in moves:
                    area.add([vi_], wt, 'ADD')
                src.remove([vi_ for vi_, _wt in moves])
        # eyeball: the eye bone alone
        ob = e["ob"]
        eg = ob.vertex_groups.get(eye_name) or ob.vertex_groups.new(name=eye_name)
        for vi in e["idx"]:
            for ge in list(ob.data.vertices[vi].groups):
                ob.vertex_groups[ge.group].remove([vi])
            eg.add([vi], 1.0, 'REPLACE')
    band = math.radians(40.0)
    blink_keys = []
    for s, L in lids.items():
        e = eyes[s]
        for ob in meshes:
            co = coords[ob.name]
            m = to_arm[ob.name]
            m_inv = m.inverted()
            shares = {}
            for vi in _near(co, e["c"], 1.9 * e["r"] + 1e-6).tolist():
                if ob is e["ob"] and vi in e["idx"]:
                    continue
                f, u, l, dist = eye_coords(Vector(co[vi]), e)
                if f < -0.3 * e["r"] or dist > 1.9 * e["r"]:
                    continue
                t = math.atan2(u, f)
                radial = 1.0 - smoothstep(1.35 * e["r"], 1.9 * e["r"], dist)
                lateral = lateral_share(L["profile"], l / e["r"], e["r"], l)
                meet = interpolate(L["meet"], l / e["r"])
                if u >= 0.0:
                    angular = 1.0 - smoothstep(L["up_t"] + 0.35 * band, L["up_t"] + band, max(t, L["up_t"]))
                    # never turn past the line where the lids meet: upper
                    # skin crossing lower skin is what folds the lid
                    angle = min(L["close_u"] * angular * radial * lateral, max(0.0, t - meet))
                else:
                    angular = 1.0 - smoothstep(-L["lo_t"] + 0.25 * band, -L["lo_t"] + 0.6 * band, max(-t, -L["lo_t"]))
                    angle = -min(-L["close_l"] * angular * radial * lateral, max(0.0, meet - t))
                if abs(angle) > 1e-5:
                    shares[vi] = angle
            if not shares:
                continue
            shares = smooth_over_edges(shares, _edge_pairs(ob), passes=3)
            if ob.data.shape_keys is None:
                ob.shape_key_add(name="Basis", from_mix=False)
            for key_name, fraction in (("BF_blink_half." + s, 0.5), ("BF_blink." + s, 1.0)):
                old = ob.data.shape_keys.key_blocks.get(key_name)
                if old is not None:
                    ob.shape_key_remove(old)
                key = ob.shape_key_add(name=key_name, from_mix=False)
                for vi, angle in shares.items():
                    rot = Matrix.Rotation(angle * fraction, 3, lid_axis)
                    p_arm = m @ ob.data.vertices[vi].co
                    key.data[vi].co = m_inv @ (e["c"] + rot @ (p_arm - e["c"]))
                blink_keys.append((ob, key_name, s))
            info.setdefault("blink_vertices", {})[s] = len(shares)
    # half key peaks at blink 0.5; the full key takes over from 0.5 to 1, so
    # the lid moves along two chords of its arc instead of one
    for ob, key_name, s in blink_keys:
        expr = ("max(0.0, 1.0 - abs(2.0 * b - 1.0))" if "_half." in key_name
                else "max(0.0, 2.0 * b - 1.0)")
        driver(ob.data.shape_keys, 'key_blocks["%s"].value' % key_name, None, expr,
               [("b", "blink." + s)])
    # How far the corner control reaches shapes the open mouth: at 0.3 x eye
    # spacing the lower lip lagged the jaw almost to its centre (a V mouth),
    # at 0.15 it followed fully up to the corners and tore there (a box).
    # 0.19 gives an oval: the lip follows ~0.8 at 60% of the way to the
    # corner and ~0.3 at the corner itself.
    radius = 0.19 * spacing
    for s, p in corners.items():
        for ob in meshes:
            co = coords[ob.name]
            g = ob.vertex_groups.get("lip.corner." + s) or ob.vertex_groups.new(name="lip.corner." + s)
            names = {gg.index: gg.name for gg in ob.vertex_groups}
            for vi in _near(co, p, radius).tolist():
                w = 1.0 - smoothstep(0.35 * radius, radius, (Vector(co[vi]) - p).length)
                _reweight(ob, vi, g, w, deform_names, names)
    if corners and "lip_upper" in B and "lip_lower" in B:
        info["mouth_shaped_vertices"] = _shape_mouth_opening(
            armature_obj, meshes, coords, B, corners, up,
            lip_follow(soft_lips, 0.0))
        info["jaw_open_corrective"] = _jaw_open_corrective(
            armature_obj, meshes, corners, context)
    info["eye_radius_mm"] = {s: round(e["r"] * 1000, 1) for s, e in eyes.items()}
    info["corners"] = sorted(corners)
    info["lids"] = sorted(lids)
    return info


# ------------------------------------------------------------ operator

def _classes():
    import bpy

    class BONEFORGE_OT_add_face_controls(bpy.types.Operator):
        """Add eye aim, blinking lids and lip follow to a rig with wizard face bones"""
        bl_idname = "boneforge.add_face_controls"
        bl_label = "Add Face Controls"
        bl_options = {'REGISTER', 'UNDO'}

        @classmethod
        def poll(cls, context):
            ob = context.active_object
            return ob is not None and ob.type == 'ARMATURE' and "eye.L" in ob.data.bones

        def execute(self, context):
            info = add_face_controls(context.active_object, context)
            if not info["built"]:
                self.report({'WARNING'}, "; ".join(info["skipped"]) or "nothing to add")
                return {'CANCELLED'}
            msg = "Face controls: %d bones" % len(info["built"])
            if info["skipped"]:
                msg += " (" + "; ".join(info["skipped"]) + ")"
            self.report({'INFO'}, msg)
            return {'FINISHED'}

    return (BONEFORGE_OT_add_face_controls,)


_registered = []


def register():
    import bpy
    for cls in _classes():
        bpy.utils.register_class(cls)
        _registered.append(cls)


def unregister():
    import bpy
    while _registered:
        bpy.utils.unregister_class(_registered.pop())
