"""BoneCraft — pose-driven corrective shape keys for elbows and knees.

Linear-blend skinning loses volume when a joint bends (the inside of an elbow
collapses). For each joint this module:

1. bends it to ``BEND_DEG`` on the FK control (the way the joint folds),
2. pushes each vertex near the joint back out to its rest distance from the
   bones — restoring the cross-section locally, which also works on open,
   multi-piece avatar meshes where a volume measure means nothing,
3. carries that push back into rest space through each vertex's skinning
   transform and stores it as a shape key,
4. drives the shape key by the angle between the joint's two deform bones —
   0 when straight, 1 at ``BEND_DEG`` — so the rest pose never changes.

Two contact correctives go further, where flesh meets flesh:

- a **deep-bend key** per elbow / knee (``DEEP_DEG``): in a deep bend the
  forearm sinks into the upper arm, the calf into the thigh. Each vertex on
  the inside of the fold that has crossed the plane bisecting the joint is
  moved back onto it, so the two sides flatten against each other the way
  soft tissue squashes, instead of passing through. Driven from ``BEND_DEG``
  to ``DEEP_DEG``, on top of the first key.

Bforartists-exclusive (registered only behind the BFA guard).
"""
import math

BEND_DEG = 110.0
DEEP_DEG = 150.0
CONTACT_MARGIN = 0.002        # of the rig's height: skin left between touching sides
_JOINTS = (   # (name, upper deform, lower deform, FK control to bend, IK_FK prop)
    ("elbow", "upperarm.def-{s}", "forearm.def-{s}", "forearm.fk-{s}", "IK_FK-arm-{s}"),
    ("knee", "thigh.def-{s}", "shin.def-{s}", "shin.fk-{s}", "IK_FK-leg-{s}"),
)


def corrective_weight(angle_deg, full_deg=BEND_DEG):
    """Shape-key value for a joint angle (pure): 0 straight, 1 at full bend."""
    return max(0.0, min(1.0, angle_deg / full_deg))


def fold_correction(p, joint, up_dir, low_dir, owner_upper, margin):
    """Where a vertex should be in a deep bend so the two sides meet (pure).

    ``up_dir`` / ``low_dir``: unit directions from the joint along the upper
    and lower segment. The plane through the joint bisecting them separates
    the two sides; a vertex on the inside of the fold that has crossed it is
    moved back onto it (``margin`` short). Returns the new point or None.
    """
    n = [up_dir[i] - low_dir[i] for i in range(3)]
    ln = sum(c * c for c in n) ** 0.5
    if ln < 1e-9:
        return None
    n = [c / ln for c in n]                                   # points to the upper side
    inside = [up_dir[i] + low_dir[i] for i in range(3)]       # into the fold
    d = [p[i] - joint[i] for i in range(3)]
    if sum(d[i] * inside[i] for i in range(3)) <= 0.0:
        return None                                           # outer side of the joint
    side = sum(d[i] * n[i] for i in range(3))
    if owner_upper and side < margin:
        shift = margin - side
    elif not owner_upper and side > -margin:
        shift = -margin - side
    else:
        return None
    return tuple(p[i] + n[i] * shift for i in range(3))


def band_falloff(dist, radius):
    """Smooth 1 -> 0 falloff with distance from the joint (pure)."""
    if dist >= radius:
        return 0.0
    t = dist / radius
    return 1.0 - t * t * (3.0 - 2.0 * t)


def _volume(mesh_obj, bpy, bmesh):
    bm = bmesh.new()
    bm.from_object(mesh_obj, bpy.context.evaluated_depsgraph_get())
    bm.transform(mesh_obj.matrix_world)
    vol = bm.calc_volume(signed=False)
    bm.free()
    return vol


def _skin_matrices(mesh_obj, armature_obj):
    """Per-vertex 3x3 linear-blend skinning transform (world space)."""
    from mathutils import Matrix
    gid = {g.index: g.name for g in mesh_obj.vertex_groups}
    pose = {}
    aw = armature_obj.matrix_world.to_3x3()
    aw_inv = aw.inverted()
    for pb in armature_obj.pose.bones:
        if pb.bone.use_deform:
            pose[pb.name] = aw @ (pb.matrix.to_3x3() @ pb.bone.matrix_local.to_3x3().inverted()) @ aw_inv
    out = []
    ident = Matrix.Identity(3)
    for v in mesh_obj.data.vertices:
        m = Matrix(((0, 0, 0), (0, 0, 0), (0, 0, 0)))
        total = 0.0
        for ge in v.groups:
            name = gid.get(ge.group)
            if name in pose and ge.weight > 0.0:
                m = m + pose[name] * ge.weight
                total += ge.weight
        out.append(m * (1.0 / total) if total > 1e-9 else ident)
    return out


def _is_watertight(mesh_obj, bmesh):
    bm = bmesh.new()
    bm.from_mesh(mesh_obj.data)
    ok = bool(bm.edges) and all(e.is_manifold for e in bm.edges)
    bm.free()
    return ok


def generate_joint_corrective(mesh_obj, armature_obj, joint, side, context=None,
                              bend_deg=BEND_DEG, volume_match=True):
    """Build and drive one corrective shape key. Returns (key name, info)."""
    import bpy
    import bmesh
    from mathutils import Vector
    if context is None:
        context = bpy.context
    _name, upper, lower, ctrl, prop = next(j for j in _JOINTS if j[0] == joint)
    upper, lower, ctrl, prop = (x.format(s=side) for x in (upper, lower, ctrl, prop))
    pb = armature_obj.pose.bones
    if ctrl not in pb or lower not in pb or upper not in pb:
        return None, {"skipped": "rig has no %s/%s" % (ctrl, lower)}
    key_name = "BF_corrective_%s_%s" % (joint, side)
    if mesh_obj.data.shape_keys is None:
        mesh_obj.shape_key_add(name="Basis", from_mix=False)
    old = mesh_obj.data.shape_keys.key_blocks.get(key_name)
    if old is not None:
        # drop its driver too, or a stale driver keeps erroring on a key
        # that no longer exists
        try:
            mesh_obj.data.shape_keys.driver_remove('key_blocks["%s"].value' % key_name)
        except (TypeError, RuntimeError):
            pass
        mesh_obj.shape_key_remove(old)

    props = pb.get("properties")
    prev_blend = props[prop] if props is not None and prop in props.keys() else None
    if props is not None and prop in props.keys():
        props[prop] = 0.0
        armature_obj.update_tag()
    bend = pb[ctrl]
    prev_mode, prev_rot = bend.rotation_mode, tuple(bend.rotation_euler)
    context.view_layer.update()
    v_rest = _volume(mesh_obj, bpy, bmesh)
    # bend the way the joint folds: away from its IK pole (elbows point to
    # the pole behind them, knees to the pole in front)
    pole = pb.get(("arm.pole-%s" if joint == "elbow" else "leg.pole-%s") % side)
    aw = armature_obj.matrix_world
    tail0 = aw @ pb[lower].tail
    bend.rotation_mode = 'XYZ'
    sign = 1.0
    if pole is not None:
        bend.rotation_euler = (math.radians(30.0), 0.0, 0.0)
        context.view_layer.update()
        moved = (aw @ pb[lower].tail) - tail0
        pole_dir = (aw @ pole.head) - (aw @ pb[lower].head)
        sign = -1.0 if moved.dot(pole_dir) > 0 else 1.0
    bend.rotation_euler = (sign * math.radians(bend_deg), 0.0, 0.0)
    context.view_layer.update()
    v_bent = _volume(mesh_obj, bpy, bmesh)

    # joint = head of the lower deform bone (posed), band radius from its length
    aw = armature_obj.matrix_world
    joint_pos = aw @ pb[lower].head
    radius = 0.6 * pb[lower].bone.length * aw.to_scale()[0]
    dg = context.evaluated_depsgraph_get()
    ev = mesh_obj.evaluated_get(dg).data
    mw = mesh_obj.matrix_world
    posed = [mw @ v.co for v in ev.vertices]
    rest = [mw @ v.co for v in mesh_obj.data.vertices]
    rest_segs = [(aw @ armature_obj.data.bones[n].head_local, aw @ armature_obj.data.bones[n].tail_local)
                 for n in (upper, lower)]
    posed_segs = [(aw @ pb[n].head, aw @ pb[n].tail) for n in (upper, lower)]

    def nearest(p, segs):
        best = None
        for h, t in segs:
            d = t - h
            dd = d.dot(d)
            u = 0.0 if dd <= 0 else max(0.0, min(1.0, (p - h).dot(d) / dd))
            q = h + d * u
            if best is None or (p - q).length < best[0]:
                best = ((p - q).length, q)
        return best

    # Restore each vertex's rest distance from the bones (its cross-section),
    # fading out away from the joint. Local, so it works on open, multi-piece
    # avatar meshes where a volume measure means nothing.
    skin = _skin_matrices(mesh_obj, armature_obj)
    mw_inv3 = mw.to_3x3().inverted()
    key = mesh_obj.shape_key_add(name=key_name, from_mix=False)
    moved = 0
    offsets = []
    gid = {g.index: g.name for g in mesh_obj.vertex_groups}
    for i, v in enumerate(mesh_obj.data.vertices):
        f = band_falloff((posed[i] - joint_pos).length, radius)
        if f <= 0.0:
            continue
        # distance to the vertex's OWN bone (the one of the pair it follows
        # most): at a sharp bend inner vertices fold past the joint, so the
        # nearest-bone distance hides the collapse
        w_up = w_lo = 0.0
        for ge in v.groups:
            name = gid.get(ge.group)
            if name == upper:
                w_up = ge.weight
            elif name == lower:
                w_lo = ge.weight
        k = 0 if w_up >= w_lo else 1
        r0 = nearest(rest[i], [rest_segs[k]])[0]
        r1, foot = nearest(posed[i], [posed_segs[k]])
        out = posed[i] - foot
        if out.length < 1e-9 or r0 <= r1:
            continue                     # only undo collapse, never inflate
        d_world = out.normalized() * ((r0 - r1) * f)
        offsets.append((i, mw_inv3 @ (skin[i].inverted_safe() @ d_world)))
        moved += 1

    def apply(gain):
        for i, off in offsets:
            key.data[i].co = mesh_obj.data.vertices[i].co + off * gain

    apply(1.0)
    key.value = 1.0
    context.view_layer.update()
    v_now = _volume(mesh_obj, bpy, bmesh)
    # On a watertight mesh the volume is measurable: scale the same local
    # shape until the bent joint holds its rest volume (secant steps). Open,
    # multi-piece meshes keep the local cross-section fix as it is.
    gain = 1.0
    if volume_match and _is_watertight(mesh_obj, bmesh) and v_now < v_rest:
        g0, e0 = 0.0, v_bent - v_rest
        g1, e1 = 1.0, v_now - v_rest
        for _ in range(4):
            if abs(e1 - e0) < 1e-12:
                break
            g2 = max(0.0, min(8.0, g1 - e1 * (g1 - g0) / (e1 - e0)))
            apply(g2)
            context.view_layer.update()
            v_now = _volume(mesh_obj, bpy, bmesh)
            g0, e0, g1, e1 = g1, e1, g2, v_now - v_rest
            if abs(e1) <= 0.002 * v_rest:
                break
        gain = g1
    # restore the pose, then drive the key by the bend angle
    bend.rotation_euler = prev_rot
    bend.rotation_mode = prev_mode
    if prev_blend is not None:
        props[prop] = prev_blend
        armature_obj.update_tag()
    key.value = 0.0
    fcurve = key.driver_add("value")
    drv = fcurve.driver
    drv.type = 'SCRIPTED'
    for var in list(drv.variables):
        drv.variables.remove(var)
    var = drv.variables.new()
    var.name = "a"
    var.type = 'ROTATION_DIFF'
    var.targets[0].id = armature_obj
    var.targets[0].bone_target = upper
    var.targets[1].id = armature_obj
    var.targets[1].bone_target = lower
    # the bones may not be perfectly straight at rest (A-pose elbows): measure
    # from the rest angle so the key is exactly 0 in the rest pose
    ub, lb = armature_obj.data.bones[upper], armature_obj.data.bones[lower]
    rest_angle = ub.matrix_local.to_quaternion().rotation_difference(
        lb.matrix_local.to_quaternion()).angle
    # (+0.01 rad dead zone: posed-vs-rest angle noise must not leave the key
    # a hair above 0 in the rest pose)
    start = rest_angle + 0.01
    drv.expression = "min(1.0, max(0.0, (a - %.6f) / %.6f))" % (
        start, math.radians(bend_deg) - 0.01)
    context.view_layer.update()
    return key_name, {"volume_loss_pct_before": round((v_rest - v_bent) / v_rest * 100, 3),
                      "volume_loss_pct_after": round((v_rest - v_now) / v_rest * 100, 3),
                      "band_radius": round(radius, 4), "bend_sign": sign,
                      "vertices_moved": moved, "volume_gain": round(gain, 3)}


def _new_key(mesh_obj, key_name):
    if mesh_obj.data.shape_keys is None:
        mesh_obj.shape_key_add(name="Basis", from_mix=False)
    old = mesh_obj.data.shape_keys.key_blocks.get(key_name)
    if old is not None:
        try:
            mesh_obj.data.shape_keys.driver_remove('key_blocks["%s"].value' % key_name)
        except (TypeError, RuntimeError):
            pass
        mesh_obj.shape_key_remove(old)
    return mesh_obj.shape_key_add(name=key_name, from_mix=False)


def _owners(mesh_obj, upper, lower):
    """Per vertex: True if it follows ``upper`` more than ``lower``, None if neither."""
    gid = {g.index: g.name for g in mesh_obj.vertex_groups}
    out = []
    for v in mesh_obj.data.vertices:
        w_up = w_lo = 0.0
        for ge in v.groups:
            name = gid.get(ge.group)
            if name == upper:
                w_up = ge.weight
            elif name == lower:
                w_lo = ge.weight
        out.append(None if w_up + w_lo < 0.3 else w_up >= w_lo)
    return out


def _store_offsets(mesh_obj, armature_obj, key, targets, posed):
    """World-space target positions (posed) -> shape-key rest positions."""
    skin = _skin_matrices(mesh_obj, armature_obj)
    mw_inv3 = mesh_obj.matrix_world.to_3x3().inverted()
    for i, q in targets.items():
        d_world = q - posed[i]
        key.data[i].co = mesh_obj.data.vertices[i].co + mw_inv3 @ (skin[i].inverted_safe() @ d_world)


def _rig_height(armature_obj):
    zs = [(armature_obj.matrix_world @ b.head_local).z for b in armature_obj.data.bones]
    zs += [(armature_obj.matrix_world @ b.tail_local).z for b in armature_obj.data.bones]
    return max(max(zs) - min(zs), 1e-6)


def generate_deep_corrective(mesh_obj, armature_obj, joint, side, context=None,
                             start_deg=BEND_DEG, deep_deg=DEEP_DEG):
    """Deep-bend contact key for one elbow / knee. Returns (key name, info)."""
    import bpy
    from mathutils import Vector
    if context is None:
        context = bpy.context
    _name, upper, lower, ctrl, prop = next(j for j in _JOINTS if j[0] == joint)
    upper, lower, ctrl, prop = (x.format(s=side) for x in (upper, lower, ctrl, prop))
    pb = armature_obj.pose.bones
    if ctrl not in pb or lower not in pb or upper not in pb:
        return None, {"skipped": "rig has no %s/%s" % (ctrl, lower)}
    key_name = "BF_corrective_%s_deep_%s" % (joint, side)
    props = pb.get("properties")
    prev_blend = props[prop] if props is not None and prop in props.keys() else None
    if props is not None and prop in props.keys():
        props[prop] = 0.0
        armature_obj.update_tag()
    bend = pb[ctrl]
    prev_mode, prev_rot = bend.rotation_mode, tuple(bend.rotation_euler)
    aw = armature_obj.matrix_world
    # fold direction: the one the first corrective key found (away from the pole)
    pole = pb.get(("arm.pole-%s" if joint == "elbow" else "leg.pole-%s") % side)
    bend.rotation_mode = 'XYZ'
    sign = 1.0
    context.view_layer.update()
    if pole is not None:
        tail0 = aw @ pb[lower].tail
        bend.rotation_euler = (math.radians(30.0), 0.0, 0.0)
        context.view_layer.update()
        moved = (aw @ pb[lower].tail) - tail0
        pole_dir = (aw @ pole.head) - (aw @ pb[lower].head)
        sign = -1.0 if moved.dot(pole_dir) > 0 else 1.0
    bend.rotation_euler = (sign * math.radians(deep_deg), 0.0, 0.0)
    context.view_layer.update()
    joint_pos = aw @ pb[lower].head
    up_dir = ((aw @ pb[upper].head) - joint_pos).normalized()
    low_dir = ((aw @ pb[lower].tail) - joint_pos).normalized()
    radius = 0.7 * pb[lower].bone.length * aw.to_scale()[0]
    margin = CONTACT_MARGIN * _rig_height(armature_obj)
    ev = mesh_obj.evaluated_get(context.evaluated_depsgraph_get()).data
    mw = mesh_obj.matrix_world
    posed = [mw @ v.co for v in ev.vertices]
    owners = _owners(mesh_obj, upper, lower)
    targets = {}
    for i, p in enumerate(posed):
        if owners[i] is None:
            continue
        dist = (p - joint_pos).length
        if dist > radius:
            continue
        q = fold_correction(tuple(p), tuple(joint_pos), tuple(up_dir), tuple(low_dir),
                            owners[i], margin)
        if q is not None:
            f = band_falloff(dist, radius) ** 0.5
            targets[i] = p + (Vector(q) - p) * f
    key = _new_key(mesh_obj, key_name)
    _store_offsets(mesh_obj, armature_obj, key, targets, posed)
    bend.rotation_euler = prev_rot
    bend.rotation_mode = prev_mode
    if prev_blend is not None:
        props[prop] = prev_blend
        armature_obj.update_tag()
    key.value = 0.0
    drv = key.driver_add("value").driver
    drv.type = 'SCRIPTED'
    var = drv.variables.new()
    var.name, var.type = "a", 'ROTATION_DIFF'
    var.targets[0].id, var.targets[0].bone_target = armature_obj, upper
    var.targets[1].id, var.targets[1].bone_target = armature_obj, lower
    ub, lb = armature_obj.data.bones[upper], armature_obj.data.bones[lower]
    rest_angle = ub.matrix_local.to_quaternion().rotation_difference(lb.matrix_local.to_quaternion()).angle
    drv.expression = "min(1.0, max(0.0, (a - %.6f) / %.6f))" % (
        rest_angle + math.radians(start_deg), math.radians(deep_deg - start_deg))
    context.view_layer.update()
    return key_name, {"vertices_moved": len(targets), "deep_deg": deep_deg}


LIFT_START_DEG = 35.0      # skirt bones alone keep the dress clear up to here
LIFT_DEG = 80.0            # the dress-over-thigh key is built (and full) here


def drape_over(p, head, axis, length, up, radius, was_in_front=False):
    """Where a dress point near a lifted thigh should go (pure), or None.

    The thigh is a cylinder from ``head`` along unit ``axis``; ``radius(u)``
    gives its radius at ``u`` (0 hip .. 1 knee). A point inside it, or one
    that hung in front of the thigh at rest (``was_in_front``) and is now
    below its top within its width, is moved straight up (perpendicular to
    the thigh) onto the top surface, keeping its sideways offset: the dress
    drapes over the thigh instead of the thigh passing through it.
    """
    d = [p[i] - head[i] for i in range(3)]
    along = sum(d[i] * axis[i] for i in range(3))
    u = along / length if length > 0 else 0.0
    if u < 0.0 or u > 1.05:
        return None
    q = [head[i] + axis[i] * min(along, length) for i in range(3)]
    w = [p[i] - q[i] for i in range(3)]
    up_n = [up[i] - axis[i] * sum(up[j] * axis[j] for j in range(3)) for i in range(3)]
    n = math.sqrt(sum(x * x for x in up_n)) or 1.0
    up_n = [x / n for x in up_n]
    side = (axis[1] * up_n[2] - axis[2] * up_n[1],
            axis[2] * up_n[0] - axis[0] * up_n[2],
            axis[0] * up_n[1] - axis[1] * up_n[0])
    lat = sum(w[i] * side[i] for i in range(3))
    h = sum(w[i] * up_n[i] for i in range(3))
    r = radius(min(u, 1.0))
    if lat * lat >= r * r:
        return None                                  # beside the thigh
    top = math.sqrt(max(0.0, r * r - lat * lat))
    inside = lat * lat + h * h < r * r
    if h >= top or not (inside or was_in_front):
        return None
    return tuple(q[i] + side[i] * lat + up_n[i] * top for i in range(3))


def generate_dress_lift_corrective(mesh_obj, armature_obj, side, context=None,
                                   lift_deg=LIFT_DEG, start_deg=LIFT_START_DEG):
    """Dress-over-thigh key for one leg (needs skirt bones). Returns (key, info).

    Skirt bones swing the hem with a lifted leg, but the fabric near the
    waist pivots too little and a high kick came through the top of the
    dress. Here the leg is lifted to ``lift_deg``; dress skin inside the thigh
    is moved onto its top surface, neighbouring dress skin eases along, and
    the key is driven by how far the thigh points forward.
    """
    import bpy
    import numpy as np
    from mathutils import Vector
    if context is None:
        context = bpy.context
    pb = armature_obj.pose.bones
    bones = armature_obj.data.bones
    thigh, shin, ctrl = "thigh.def-%s" % side, "shin.def-%s" % side, "thigh.fk-%s" % side
    if thigh not in pb or shin not in pb or ctrl not in pb:
        return None, {"skipped": "rig has no %s" % ctrl}
    gid = {g.index: g.name for g in mesh_obj.vertex_groups}
    skirt_ids = {i for i, n in gid.items() if n.startswith("skirt.")}
    if not skirt_ids:
        return None, {"skipped": "no skirt bones"}
    thigh_id = next((i for i, n in gid.items() if n == thigh), None)
    verts = mesh_obj.data.vertices
    dress, leg = [], []
    for v in verts:
        ws = sum(ge.weight for ge in v.groups if ge.group in skirt_ids)
        wt = sum(ge.weight for ge in v.groups if ge.group == thigh_id)
        if ws >= 0.1:                     # the waist fades into the skirt
            dress.append(v.index)
        elif wt >= 0.5:
            leg.append(v.index)
    if not dress or len(leg) < 12:
        return None, {"skipped": "no dress / thigh skin"}
    aw = armature_obj.matrix_world
    mw = mesh_obj.matrix_world
    # thigh radius along its length, from the leg's own skin at rest
    tb = bones[thigh]
    h0, t0 = aw @ tb.head_local, aw @ tb.tail_local
    ax0 = (t0 - h0)
    length0 = ax0.length
    ax0 = ax0.normalized()
    bins = [[] for _ in range(6)]
    for i in leg:
        p = mw @ verts[i].co
        along = (p - h0).dot(ax0)
        u = along / length0
        if 0.0 <= u <= 1.0:
            r = (p - (h0 + ax0 * along)).length
            bins[min(5, int(u * 6))].append(r)
    rad = [sorted(b)[int(0.9 * (len(b) - 1))] if b else None for b in bins]
    known = [r for r in rad if r is not None]
    if not known:
        return None, {"skipped": "thigh radius unreadable"}
    rad = [r if r is not None else max(known) for r in rad]
    margin = CONTACT_MARGIN * _rig_height(armature_obj)

    def radius(u):
        return rad[min(5, int(u * 6))] + margin

    # front: the way the foot points
    fb = bones.get("foot.def-%s" % side)
    front = (aw.to_3x3() @ (fb.tail_local - fb.head_local)) if fb else Vector((0, -1, 0))
    front.z = 0.0
    front = front.normalized() if front.length > 1e-9 else Vector((0, -1, 0))

    props = pb.get("properties")
    prop = "IK_FK-leg-%s" % side
    prev_blend = props[prop] if props is not None and prop in props.keys() else None
    if prev_blend is not None:
        props[prop] = 0.0
        armature_obj.update_tag()
    bend = pb[ctrl]
    prev_mode, prev_rot = bend.rotation_mode, tuple(bend.rotation_euler)
    bend.rotation_mode = 'XYZ'
    knee0 = aw @ pb[shin].head
    bend.rotation_euler = (math.radians(30.0), 0.0, 0.0)
    context.view_layer.update()
    sign = 1.0 if ((aw @ pb[shin].head) - knee0).dot(front) > 0 else -1.0
    bend.rotation_euler = (sign * math.radians(lift_deg), 0.0, 0.0)
    context.view_layer.update()
    head, tail = aw @ pb[thigh].head, aw @ pb[thigh].tail
    axis = (tail - head)
    length = axis.length
    axis = axis.normalized()
    ev = mesh_obj.evaluated_get(context.evaluated_depsgraph_get()).data
    posed = [mw @ v.co for v in ev.vertices]
    # which dress skin hung in front of this thigh at rest (and within reach
    # of it: the thigh's own length ahead of it)
    in_front = set()
    for i in dress:
        p = mw @ verts[i].co
        along = (p - h0).dot(ax0)
        if 0.0 <= along <= length0:
            off = p - (h0 + ax0 * along)
            ahead = off.dot(front)
            if 0.0 < ahead < length0 and (off - front * ahead).length < 1.5 * max(known):
                in_front.add(i)
    disp = {}
    for i in dress:
        q = drape_over(tuple(posed[i]), tuple(head), tuple(axis), length, (0.0, 0.0, 1.0),
                       radius, i in in_front)
        if q is not None:
            disp[i] = Vector(q) - posed[i]
    # ease the neighbouring dress skin along, so the fabric bends over the
    # thigh instead of tearing around it
    fixed = set(disp)
    dress_set = set(dress)
    nbrs = {}
    for e in mesh_obj.data.edges:
        a, b = e.vertices
        if a in dress_set and b in dress_set:
            nbrs.setdefault(a, []).append(b)
            nbrs.setdefault(b, []).append(a)
    zero = Vector((0.0, 0.0, 0.0))
    for _ in range(6):
        nxt = dict(disp)
        for i in dress:
            if i in fixed or i not in nbrs:
                continue
            s = sum((disp.get(n, zero) for n in nbrs[i]), Vector())
            m = s / len(nbrs[i]) * 0.85
            if m.length > 1e-6:
                nxt[i] = m
        disp = nxt
    targets = {i: posed[i] + d for i, d in disp.items()}
    key = _new_key(mesh_obj, "BF_corrective_dress_lift_%s" % side)
    _store_offsets(mesh_obj, armature_obj, key, targets, posed)
    bend.rotation_euler = prev_rot
    bend.rotation_mode = prev_mode
    if prev_blend is not None:
        props[prop] = prev_blend
        armature_obj.update_tag()
    key.value = 0.0
    # driver: how far the knee has swung forward of the hip, as an angle
    drv = key.driver_add("value").driver
    drv.type = 'SCRIPTED'
    for var in list(drv.variables):
        drv.variables.remove(var)
    for name, bone, chan in (("hx", thigh, 'LOC_X'), ("hy", thigh, 'LOC_Y'), ("hz", thigh, 'LOC_Z'),
                             ("kx", shin, 'LOC_X'), ("ky", shin, 'LOC_Y'), ("kz", shin, 'LOC_Z')):
        var = drv.variables.new()
        var.name, var.type = name, 'TRANSFORMS'
        t = var.targets[0]
        t.id, t.bone_target, t.transform_type, t.transform_space = armature_obj, bone, chan, 'WORLD_SPACE'
    drv.expression = ("min(1.0, max(0.0, (atan2(%.5f*(kx-hx) + %.5f*(ky-hy), hz-kz) - %.6f) / %.6f))"
                      % (front.x, front.y, math.radians(start_deg), math.radians(lift_deg - start_deg)))
    context.view_layer.update()
    return key.name, {"vertices_moved": len(disp), "inside_thigh": len(fixed),
                      "lift_deg": lift_deg}


def generate_all(mesh_obj, armature_obj, context=None, joints=("elbow", "knee")):
    """Corrective shape keys for both sides of every listed joint: the bend
    key and the deep-bend contact key. (The shoulder is handled in the
    weights: see ``skin_gen.blend_shoulder_seams``.)"""
    results = {}
    for joint in joints:
        for side in ("L", "R"):
            name, info = generate_joint_corrective(mesh_obj, armature_obj, joint, side, context)
            results["%s_%s" % (joint, side)] = info if name is None else dict(info, key=name)
            name, info = generate_deep_corrective(mesh_obj, armature_obj, joint, side, context)
            results["%s_deep_%s" % (joint, side)] = info if name is None else dict(info, key=name)
    for side in ("L", "R"):                    # only with skirt bones
        name, info = generate_dress_lift_corrective(mesh_obj, armature_obj, side, context)
        results["dress_lift_%s" % side] = info if name is None else dict(info, key=name)
    return results


# ------------------------------------------------------------ operator

def _register_classes():
    import bpy

    class BONEFORGE_OT_joint_correctives(bpy.types.Operator):
        """Add bend-driven corrective shape keys that keep elbows and knees from collapsing"""
        bl_idname = "boneforge.generate_joint_correctives"
        bl_label = "Generate Joint Correctives"
        bl_options = {'REGISTER', 'UNDO'}

        @classmethod
        def poll(cls, context):
            ob = context.active_object
            return ob is not None and ob.type == 'MESH' and any(
                m.type == 'ARMATURE' and m.object for m in ob.modifiers)

        def execute(self, context):
            from boneforge import bfa_guard
            bfa_guard.require_bforartists("joint_correctives")
            mesh = context.active_object
            arm = next(m.object for m in mesh.modifiers if m.type == 'ARMATURE' and m.object)
            res = generate_all(mesh, arm, context)
            made = [k for k, v in res.items() if "key" in v]
            self.report({'INFO'}, "Corrective shape keys: %s" % (", ".join(made) or "none"))
            return {'FINISHED'} if made else {'CANCELLED'}

    return (BONEFORGE_OT_joint_correctives,)


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
