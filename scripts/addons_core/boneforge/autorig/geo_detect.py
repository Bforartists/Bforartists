"""BoneCraft - landmark detection geometry kernel (Task 3, BF-GAP-01).

PURE geometry math over a point cloud (mesh vertices, world space). No bpy,
no model files. This is the deterministic fallback path of smart marker
detection: bounds, centroid, mirror-axis detection, extremity finding, and
heuristic body-landmark guesses with confidence.

The mesh-reading glue (sampling ``bpy`` vertices) lives in ``inference.py``.
This kernel owns the pure robustness pass: finite-point cleanup, loose
connected-component filtering for disconnected props/clothing, scale
normalization helpers, guarded symmetry-axis choice, and conservative
confidence on non-upright clouds.

Clean-room: first-principles geometry; no third-party detection code.
"""
import math

UP = 2  # Z-up world convention


def _as_point(p):
    return (float(p[0]), float(p[1]), float(p[2]))


def _finite_points(points):
    clean = []
    for p in points:
        if p is None or len(p) < 3:
            continue
        q = _as_point(p)
        if all(math.isfinite(v) for v in q):
            clean.append(q)
    return clean


def _require_points(points):
    pts = _finite_points(points)
    if not pts:
        raise ValueError("point cloud is empty")
    return pts


def _axis_vals(points, axis):
    return [p[axis] for p in points]


def bounds(points):
    points = _require_points(points)
    xs, ys, zs = (_axis_vals(points, 0), _axis_vals(points, 1),
                  _axis_vals(points, 2))
    return ((min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs)))


def centroid(points):
    points = _require_points(points)
    n = float(len(points))
    return tuple(sum(_axis_vals(points, a)) / n for a in range(3))


def extent(points):
    lo, hi = bounds(points)
    return tuple(hi[a] - lo[a] for a in range(3))


def _percentile(sorted_vals, frac):
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    pos = max(0.0, min(1.0, frac)) * (len(sorted_vals) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return sorted_vals[lo]
    t = pos - lo
    return sorted_vals[lo] * (1.0 - t) + sorted_vals[hi] * t


def _robust_extent(points):
    """5/95-percentile extents, resistant to small disconnected outliers."""
    pts = _require_points(points)
    out = []
    for axis in range(3):
        vals = sorted(_axis_vals(pts, axis))
        out.append(_percentile(vals, 0.95) - _percentile(vals, 0.05))
    return tuple(max(v, 0.0) for v in out)


def _largest_loose_component(points):
    """Keep the largest voxel-connected component.

    Mesh vertex clouds do not carry topology here, so this is deliberately
    loose: a cell size derived from robust body scale connects adjacent body
    parts while dropping far disconnected clothing, props, or scanner debris.
    """
    pts = _require_points(points)
    if len(pts) < 16:
        return pts

    rext = _robust_extent(pts)
    diag = math.sqrt(sum(v * v for v in rext))
    cell_size = max(diag * 0.16, max(rext) * 0.06, 1e-6)
    if cell_size <= 1e-6:
        return pts

    cells = {}
    for idx, p in enumerate(pts):
        key = tuple(int(math.floor(p[a] / cell_size)) for a in range(3))
        cells.setdefault(key, []).append(idx)

    seen = set()
    best = []
    offsets = [(dx, dy, dz)
               for dx in (-1, 0, 1)
               for dy in (-1, 0, 1)
               for dz in (-1, 0, 1)]
    for start in cells:
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        component = []
        while stack:
            key = stack.pop()
            component.extend(cells[key])
            for dx, dy, dz in offsets:
                nb = (key[0] + dx, key[1] + dy, key[2] + dz)
                if nb in cells and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        if len(component) > len(best):
            best = component

    if not best or len(best) == len(pts):
        return pts
    if len(best) < max(8, int(len(pts) * 0.40)):
        return pts
    return [pts[i] for i in sorted(best)]


def preprocess_points(points):
    """Clean and de-clutter a point cloud before landmark heuristics."""
    return _largest_loose_component(_require_points(points))


def normalize_points(points):
    """Return ``(normalized, center, scale)`` for a cleaned point cloud."""
    pts = preprocess_points(points)
    c = centroid(pts)
    scale = max((sum((p[a] - c[a]) ** 2 for a in range(3))) ** 0.5
                for p in pts) or 1.0
    norm = [tuple((p[a] - c[a]) / scale for a in range(3)) for p in pts]
    return norm, c, scale


def symmetry_score(points, axis, sample=300):
    """Reflection-overlap score across the centroid plane on ``axis``.

    Lower means more symmetric.
    """
    points = _require_points(points)
    if len(points) < 2:
        return 0.0
    c = centroid(points)
    pts = points[:sample] if len(points) > sample else points
    score = 0.0
    for p in pts:
        refl = list(p)
        refl[axis] = 2 * c[axis] - p[axis]
        score += min(sum((q[k] - refl[k]) ** 2 for k in range(3)) for q in pts)
    return score


def symmetry_axis(points):
    """Left-right mirror axis of an upright humanoid.

    Heuristic: the mirror axis is the widest horizontal axis (arm span /
    shoulder width). A thin, centred cloud is trivially symmetric across its
    thin axis, so extent leads; the overlap score only breaks ties when the
    two horizontal extents are close. Degenerate clouds fall back to X.
    """
    points = preprocess_points(points)
    ext = extent(points)
    horiz = sorted((a for a in range(3) if a != UP), key=lambda a: -ext[a])
    widest, other = horiz[0], horiz[1]
    if ext[widest] <= 1e-9:
        return 0
    if ext[other] > 0.75 * ext[widest]:
        return widest if symmetry_score(points, widest) <= \
            symmetry_score(points, other) else other
    return widest


def extremities(points, k=6):
    """Return the k points farthest from the centroid (hands/feet/head)."""
    points = preprocess_points(points)
    c = centroid(points)
    ranked = sorted(points,
                    key=lambda p: -sum((p[a] - c[a]) ** 2 for a in range(3)))
    return ranked[:k]


def guess_landmarks(points):
    """Heuristic body landmarks.

    Returns dict with axes + a list of ``{name, pos, confidence, source}``.
    Confidence is in [0, 1].
    """
    points = preprocess_points(points)
    lo, hi = bounds(points)
    c = centroid(points)
    ext = extent(points)
    height = ext[UP] or 1.0
    sym = symmetry_axis(points)
    other = [a for a in (0, 1, 2) if a not in (UP, sym)][0]
    out = []

    horizontal = max(ext[a] for a in range(3) if a != UP) or 1.0
    # uprightness from the robust (5-95%) extent, so a one-sided accessory
    # (robot arm, wings, a prop in hand) does not make a figure look lying
    rext = _robust_extent(points)
    r_horizontal = max(rext[a] for a in range(3) if a != UP) or 1.0
    upright_scale = 1.0 if (height >= 0.75 * horizontal
                            or rext[UP] >= 0.75 * r_horizontal) else 0.65

    def conf(value):
        return max(0.0, min(1.0, value * upright_scale))

    def at_height(frac):
        return lo[UP] + frac * height

    def side_points(positive):
        return [p for p in points if (p[sym] - c[sym] > 0) == positive] or points

    top = max(points, key=lambda p: p[UP])
    out.append({"name": "head", "pos": tuple(top),
                "confidence": conf(0.8), "source": "geometry"})
    hips = list(c); hips[UP] = at_height(0.53)
    out.append({"name": "hips", "pos": tuple(hips),
                "confidence": conf(0.7), "source": "geometry"})
    for positive, tag in ((True, "L"), (False, "R")):
        sp = side_points(positive)
        hand = max(sp, key=lambda p: (p[sym] if positive else -p[sym]))
        out.append({"name": "hand-" + tag, "pos": tuple(hand),
                    "confidence": conf(0.6), "source": "geometry"})
        foot = min(sp, key=lambda p: p[UP])
        out.append({"name": "foot-" + tag, "pos": tuple(foot),
                    "confidence": conf(0.65), "source": "geometry"})
        sh = max(sp, key=lambda p: p[UP] + (p[sym] if positive else -p[sym]))
        shoulder = list(sh); shoulder[UP] = at_height(0.82)
        out.append({"name": "shoulder-" + tag, "pos": tuple(shoulder),
                    "confidence": conf(0.5), "source": "geometry"})
    geo = {"up_axis": UP, "symmetry_axis": sym, "front_axis": other,
           "height": height, "landmarks": out}
    if upright_scale == 1.0:
        try:
            geo["joints"] = refine_joints(points, geo)
        except Exception:
            geo["joints"] = {}     # heuristics above remain the fallback
    return geo


# ------------------------------------------------------------------ joints
#
# Joint refinement: trace each limb from its tip across a voxelised copy of
# the cloud and watch the limb's cross-section (the "ring" of voxels at each
# geodesic distance). A wrist is where the ring narrows past the hand, a
# shoulder is where it jumps into the torso; joint positions are ring
# centroids, so they sit inside the limb rather than on its surface.

_CELL_FRAC = 0.03          # voxel size as a fraction of body height
_OFFSETS = [(dx, dy, dz, math.sqrt(dx * dx + dy * dy + dz * dz))
            for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1)
            if (dx, dy, dz) != (0, 0, 0)]


def _voxelize(points, cell):
    grid = {}
    for p in points:
        key = (int(math.floor(p[0] / cell)), int(math.floor(p[1] / cell)),
               int(math.floor(p[2] / cell)))
        grid.setdefault(key, []).append(p)
    return grid


def _key_of(p, cell):
    return (int(math.floor(p[0] / cell)), int(math.floor(p[1] / cell)),
            int(math.floor(p[2] / cell)))


def _geodesic_rings(grid, start, max_cells):
    """Dijkstra over occupied voxels; returns ``{ring_index: [keys]}``."""
    import heapq
    dist = {start: 0.0}
    heap = [(0.0, start)]
    while heap:
        d, key = heapq.heappop(heap)
        if d > dist.get(key, float("inf")) or d > max_cells:
            continue
        for dx, dy, dz, w in _OFFSETS:
            nb = (key[0] + dx, key[1] + dy, key[2] + dz)
            if nb in grid:
                nd = d + w
                if nd < dist.get(nb, float("inf")):
                    dist[nb] = nd
                    heapq.heappush(heap, (nd, nb))
    rings = {}
    for key, d in dist.items():
        if d <= max_cells:
            rings.setdefault(int(d), []).append(key)
    return rings


def _ring_profile(grid, rings, n):
    sizes, cents = [], []
    for i in range(n + 1):
        keys = rings.get(i, [])
        sizes.append(len(keys))
        pts = [p for k in keys for p in grid[k]]
        cents.append(centroid(pts) if pts else None)
    smooth = [sum(sizes[max(0, i - 1):i + 2]) / len(sizes[max(0, i - 1):i + 2])
              for i in range(len(sizes))]
    return smooth, cents


def _nearest_cent(cents, i):
    for off in range(len(cents)):
        for j in (i - off, i + off):
            if 0 <= j < len(cents) and cents[j] is not None:
                return cents[j]
    return None


def _unit(v):
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return tuple(x / n for x in v)


def _trace_arm(grid, cell, tip, height):
    """Wrist / elbow / shoulder joint centres for the arm ending at ``tip``."""
    hc = height / cell
    n = int(0.60 * hc)
    rings = _geodesic_rings(grid, _key_of(tip, cell), n)
    size, cent = _ring_profile(grid, rings, n)
    lo_i, hi_i = max(1, int(0.12 * hc)), max(2, int(0.22 * hc))
    ref = sorted(size[lo_i:hi_i + 1])
    ref = ref[len(ref) // 2] if ref else 1.0
    # the shoulder is where the cross-section has tripled (into the torso)
    shoulder_i, found = int(0.40 * hc), False
    for i in range(int(0.18 * hc), n + 1):
        if size[i] > 3.0 * max(ref, 1.0):
            shoulder_i, found = i, True
            break
    shoulder = _nearest_cent(cent, shoulder_i)
    if shoulder is None:
        raise ValueError("arm trace failed")
    # proportions hold for realistic and stylised figures alike: the hand is
    # ~25% of shoulder-to-fingertip, the elbow ~53% of shoulder-to-wrist
    wrist_i = int(round(0.25 * shoulder_i))
    elbow_i = int(round(wrist_i + 0.47 * (shoulder_i - wrist_i)))
    wrist = _nearest_cent(cent, wrist_i)
    elbow = _nearest_cent(cent, elbow_i)
    conf = 0.62 if found else 0.42
    return wrist, elbow, shoulder, conf


def _slice_centre(points, lo_z, hi_z, near=None, radius=None):
    band = [p for p in points if lo_z <= p[UP] <= hi_z]
    if near is not None and radius is not None:
        band = [p for p in band
                if (p[0] - near[0]) ** 2 + (p[1] - near[1]) ** 2 <= radius * radius]
    if not band:
        return None
    xs = sorted(p[0] for p in band)
    ys = sorted(p[1] for p in band)
    return (_percentile(xs, 0.5), _percentile(ys, 0.5), 0.5 * (lo_z + hi_z))


def refine_joints(points, geo):
    """Joint-centre estimates for all BODY_MARKERS on an upright figure.

    Returns ``{MARKER: (pos, confidence)}``; empty when the figure is not
    readable (callers then keep the coarse landmark heuristics).
    """
    sym, front, height = geo["symmetry_axis"], geo["front_axis"], geo["height"]
    lo, _hi = bounds(points)
    # median centre: a one-sided accessory cannot drag it off the body's
    # midline the way it drags the mean
    c = tuple(_percentile(sorted(_axis_vals(points, a)), 0.5) for a in range(3))
    floor_z = lo[UP]
    cell = _CELL_FRAC * height
    grid = _voxelize(points, cell)
    out = {}

    def z_at(frac):
        return floor_z + frac * height

    # --- arms: trace from the lateral tip above hip height
    arm = {}
    for positive, side in ((True, "LEFT"), (False, "RIGHT")):
        sgn = 1.0 if positive else -1.0
        cand = [p for p in points if (p[sym] - c[sym]) * sgn > 0 and p[UP] > z_at(0.35)]
        if not cand:
            continue
        # a real arm has a mirror twin; a one-sided accessory (wing, robot
        # arm, prop) does not — take the farthest tip that is mirrored
        cand.sort(key=lambda p: -(p[sym] - c[sym]) * sgn)
        tip = cand[0]
        for p in cand[:: max(1, len(cand) // 400)]:
            m = list(p)
            m[sym] = 2 * c[sym] - p[sym]
            mk = _key_of(m, cell)
            if any((mk[0] + dx, mk[1] + dy, mk[2] + dz) in grid
                   for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1)):
                tip = p
                break
        wrist, elbow, shoulder, conf = _trace_arm(grid, cell, tip, height)
        # sanity: a T/A-pose arm runs outward shoulder -> elbow -> wrist and
        # its wrist is well above the floor. Arms hanging down (walk / I-pose)
        # or a body facing sideways break that: say so with a low confidence
        # (the wizard then asks for manual placement) instead of passing a
        # confident-looking wrong guess.
        out_d = [(j[sym] - c[sym]) * sgn for j in (shoulder, elbow, wrist)]
        if not (out_d[0] < out_d[1] < out_d[2]) or wrist[UP] < z_at(0.45)                 or out_d[2] < 0.15 * height:
            conf = 0.2
        arm[side] = (wrist, elbow, shoulder, conf)
        out["WRIST_" + side] = (wrist, conf)
        out["ELBOW_" + side] = (elbow, conf - 0.05)
        out["SHOULDER_" + side] = (shoulder, conf - 0.05)

    # --- a rigging pose is mirror-symmetric, but each arm is traced on its
    # own, so hair, a collar or a strap on one side pulls that side's
    # shoulder up and forward. When the two traces roughly mirror each other,
    # keep the cleaner side (its shoulder closest to the line its own wrist
    # and elbow give) and mirror it onto the other, about the arms' own
    # midline (a backpack can shift the body's median centre).
    if "LEFT" in arm and "RIGHT" in arm and min(arm["LEFT"][3], arm["RIGHT"][3]) > 0.3:
        mid = sum(jl[sym] + jr[sym] for jl, jr in
                  zip(arm["LEFT"][:3], arm["RIGHT"][:3])) / 6.0

        def mirror(p):
            m = list(p)
            m[sym] = 2 * mid - p[sym]
            return tuple(m)

        # elbows are noisy (a puffy sleeve moves one); average them mirrored
        el_avg = tuple(0.5 * (a + b) for a, b in
                       zip(arm["LEFT"][1], mirror(arm["RIGHT"][1])))

        def off_line(side):
            w, _e, s_ = arm[side][:3]
            e = el_avg if side == "LEFT" else mirror(el_avg)
            d = _unit(tuple(e[a] - w[a] for a in range(3)))
            v = tuple(s_[a] - e[a] for a in range(3))
            t = sum(v[a] * d[a] for a in range(3))
            return math.sqrt(max(0.0, sum(x * x for x in v) - t * t))

        pairs = list(zip(arm["LEFT"][:3], arm["RIGHT"][:3]))
        if all(math.dist(jl, mirror(jr)) < 0.10 * height for jl, jr in pairs):
            good, bad = (("LEFT", "RIGHT") if off_line("LEFT") <= off_line("RIGHT")
                         else ("RIGHT", "LEFT"))
            if off_line(bad) - off_line(good) > 0.01 * height:
                sh = mirror(arm[good][2])
                out["SHOULDER_" + bad] = (sh, out["SHOULDER_" + bad][1])
                arm[bad] = (arm[bad][0], arm[bad][1], sh, arm[bad][3])

    # --- head / neck
    top = max(p[UP] for p in points)
    head_band = [p for p in points if p[UP] >= top - 0.12 * height]
    hc = tuple(_percentile(sorted(_axis_vals(head_band, a)), 0.5) for a in range(3))
    head = [0.0, 0.0, 0.0]
    head[sym], head[front], head[UP] = c[sym], hc[front], top
    out["HEAD_TOP"] = (tuple(head), 0.7)
    if "LEFT" in arm and "RIGHT" in arm:
        sl, sr = arm["LEFT"][2], arm["RIGHT"][2]
        neck = [0.5 * (sl[a] + sr[a]) for a in range(3)]
        neck[sym] = c[sym]
        neck[UP] = max(sl[UP], sr[UP]) + 0.03 * height
        out["NECK_BASE"] = (tuple(neck), 0.6)
        shoulder_z = 0.5 * (sl[UP] + sr[UP])
    else:
        shoulder_z = z_at(0.80)

    # --- pelvis: just above the crotch (where the legs meet), found as the
    # first height with sustained dense occupancy on the midline; body
    # proportion is the fallback when that is unreadable
    pelvis_z = floor_z + 0.75 * (shoulder_z - floor_z)
    step = 0.02 * height
    bins = []
    z = z_at(0.20)
    while z < z_at(0.75):
        bins.append((z, sum(1 for p in points
                            if abs(p[sym] - c[sym]) < 0.02 * height and z <= p[UP] < z + step)))
        z += step
    peak = max((n for _z, n in bins), default=0)
    crotch = None
    for (z0, n0), (_z1, n1) in zip(bins, bins[1:]):
        if peak and n0 >= 0.35 * peak and n1 >= 0.35 * peak:
            crotch = z0
            break
    # Rigs disagree on the pelvis bone (at the hip joints vs well above them),
    # and clothing hides the crotch, so no single cue is right for every
    # figure. Average independent estimates: body proportion from the
    # shoulders, the typical hip height and the crotch. The crotch, when
    # readable, counts double: it is the one cue measured on this body, and
    # the proportion cues assume adult proportions that stylised (big-head,
    # short-leg) characters do not have.
    estimates = [pelvis_z, z_at(0.54)]
    if crotch is not None and z_at(0.35) <= crotch <= z_at(0.62):
        estimates += [crotch + 0.035 * height] * 2
    pelvis_z = sum(estimates) / len(estimates)
    pelvis = [0.0, 0.0, 0.0]
    pelvis[sym], pelvis[front], pelvis[UP] = c[sym], c[front], pelvis_z
    out["PELVIS"] = (tuple(pelvis), 0.6)

    # --- legs: ankle / knee / hip columns, toe direction from the foot
    hip_z = pelvis_z - 0.010 * height
    for positive, side in ((True, "LEFT"), (False, "RIGHT")):
        sgn = 1.0 if positive else -1.0
        sp = [p for p in points if (p[sym] - c[sym]) * sgn > 0.01 * height]
        if not sp:
            continue
        col = _slice_centre(sp, z_at(0.15), z_at(0.30))
        if col is None:
            continue
        r = 0.10 * height
        ank = _slice_centre(sp, z_at(0.08), z_at(0.11), col, r)
        foot = [p for p in sp if p[UP] <= z_at(0.05)
                and (p[0] - col[0]) ** 2 + (p[1] - col[1]) ** 2 <= (0.18 * height) ** 2]
        if ank is None or not foot:
            continue
        fmean = centroid(foot)
        fdir = 1.0 if fmean[front] - ank[front] > 0 else -1.0
        tip = max(foot, key=lambda p: p[front] * fdir)
        ankle = list(ank)
        ankle[UP] = z_at(0.075)
        toe = [ankle[a] + 0.7 * (tip[a] - ankle[a]) for a in range(3)]
        heel = list(ankle)
        heel[front] -= fdir * 0.035 * height
        heel[UP] = floor_z
        knee_z = ankle[UP] + 0.50 * (hip_z - ankle[UP])
        kn = _slice_centre(sp, knee_z - 0.02 * height, knee_z + 0.02 * height, ank, r) or ank
        knee = (kn[0], kn[1], knee_z)
        hp = _slice_centre(sp, hip_z - 0.12 * height, hip_z - 0.06 * height, kn, 0.12 * height) or kn
        hip = [hp[0], hp[1], hip_z]
        out["ANKLE_" + side] = (tuple(ankle), 0.6)
        out["TOE_" + side] = (tuple(toe), 0.5)
        out["HEEL_" + side] = (tuple(heel), 0.45)
        out["KNEE_" + side] = (knee, 0.5)
        out["HIP_" + side] = (tuple(hip), 0.5)
    # the pelvis sits between the feet: a one-sided accessory can pull the
    # median centre off the midline, the ankles cannot
    if "ANKLE_LEFT" in out and "ANKLE_RIGHT" in out and "PELVIS" in out:
        pel = list(out["PELVIS"][0])
        pel[sym] = 0.5 * (out["ANKLE_LEFT"][0][sym] + out["ANKLE_RIGHT"][0][sym])
        out["PELVIS"] = (tuple(pel), out["PELVIS"][1])
    return out


def confidence_category(score):
    """``'CONFIRMED'`` (>=0.85), ``'REVIEW'`` (>=0.6), else ``'ADJUST'``.

    Pure logic kept in the kernel so it is testable without ``bpy``; the
    detection layer re-exports it.
    """
    if score >= 0.85:
        return 'CONFIRMED'
    if score >= 0.6:
        return 'REVIEW'
    return 'ADJUST'


def _lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def body_marker_proposals(geo):
    """Map geometry landmarks onto the wizard's BODY_MARKERS.

    Intermediate joints (neck, elbows, hips, knees, toes, heels) are derived
    by interpolation. Pure: returns ``{MARKER_NAME: {"pos": (x,y,z),
    "confidence": float, "source": str}}``. Confidence stays modest for
    derived joints so they land in the REVIEW/ADJUST band and are never
    silently auto-confirmed.
    """
    lm = {d["name"]: (d["pos"], d["confidence"]) for d in geo["landmarks"]}
    up, sym, front = geo["up_axis"], geo["symmetry_axis"], geo["front_axis"]
    height = geo["height"]
    out = {}

    def put(name, pos, conf, source="geometry"):
        out[name] = {"pos": tuple(float(x) for x in pos),
                     "confidence": round(float(conf), 3), "source": source}

    if "head" in lm:
        put("HEAD_TOP", *lm["head"])
    if "hips" in lm:
        put("PELVIS", *lm["hips"])
    if "shoulder-L" in lm and "shoulder-R" in lm:
        put("NECK_BASE", _lerp(lm["shoulder-L"][0], lm["shoulder-R"][0], 0.5),
            0.5, "derived")
    elif "head" in lm and "hips" in lm:
        put("NECK_BASE", _lerp(lm["hips"][0], lm["head"][0], 0.78), 0.4,
            "derived")

    for tag, side in (("L", "LEFT"), ("R", "RIGHT")):
        sh = lm.get("shoulder-" + tag)
        wr = lm.get("hand-" + tag)
        ft = lm.get("foot-" + tag)
        if sh:
            put("SHOULDER_" + side, *sh)
        if wr:
            put("WRIST_" + side, *wr)
        if ft:
            put("ANKLE_" + side, *ft)
        if sh and wr:
            put("ELBOW_" + side, _lerp(sh[0], wr[0], 0.5), 0.4, "derived")
        if "hips" in lm and ft:
            hip = list(lm["hips"][0])
            hip[sym] = 0.5 * ft[0][sym] + 0.5 * lm["hips"][0][sym]
            put("HIP_" + side, hip, 0.45, "derived")
            put("KNEE_" + side, _lerp(hip, ft[0], 0.5), 0.4, "derived")
        if ft:
            toe = list(ft[0]); toe[front] += 0.08 * height; toe[up] -= 0.02 * height
            heel = list(ft[0]); heel[front] -= 0.05 * height; heel[up] -= 0.02 * height
            put("TOE_" + side, toe, 0.35, "derived")
            put("HEEL_" + side, heel, 0.35, "derived")
    # limb-traced joint centres replace the coarse guesses where available
    for name, (pos, conf) in (geo.get("joints") or {}).items():
        put(name, pos, min(conf, 0.84), "traced")
    return out


# ------------------------------------------------------------------ fingers

def _vsub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def _vadd(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def _vmul(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def _vdot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _vunit(a):
    n = math.sqrt(_vdot(a, a)) or 1.0
    return (a[0] / n, a[1] / n, a[2] / n)


def _vcross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


FINGER_BASE_FRACTION = 0.49    # MCP knuckles sit ~half way down the hand
_FINGERS = ("INDEX", "MIDDLE", "RING", "PINKY")


def finger_markers(points, wrist, elbow=None, side="L", front=(0.0, -1.0, 0.0)):
    """Finger markers for one hand from the mesh points (pure).

    The hand is the part of the mesh just beyond the wrist along the forearm
    (and connected to it, so a prop or accessory beside the hand is ignored).
    Four finger bands split the hand's width, index on the thumb side; each
    tip is the end of the mesh in its band, bases sit at
    ``FINGER_BASE_FRACTION`` of the hand length; the thumb is the part that
    sticks out sideways part-way down the hand.

    Returns ``{FINGER_*_<side>: (x, y, z)}`` or ``{}`` when no hand is found.
    """
    if elbow is not None and _vdot(_vsub(wrist, elbow), _vsub(wrist, elbow)) > 1e-10:
        axis = _vunit(_vsub(wrist, elbow))
        reach = math.sqrt(_vdot(_vsub(wrist, elbow), _vsub(wrist, elbow))) * 0.9
    else:
        axis = (1.0, 0.0, 0.0) if side == "L" else (-1.0, 0.0, 0.0)
        reach = 0.2
    lat = _vcross((0.0, 0.0, 1.0), axis)
    if _vdot(lat, lat) < 1e-8:
        lat = (0.0, 1.0, 0.0)
    lat = _vunit(lat)

    def s_of(p):
        return _vdot(_vsub(p, wrist), axis)

    def l_of(p):
        return _vdot(_vsub(p, wrist), lat)

    def radial(p):
        d = _vsub(p, wrist)
        return math.sqrt(max(_vdot(d, d) - s_of(p) ** 2, 0.0))

    near = [p for p in points if -0.05 * reach < s_of(p) <= reach and radial(p) <= 0.6 * reach]
    if len(near) < 20:
        return {}
    # keep the piece connected to the wrist (drops props / accessories)
    cell = max(reach / 14.0, 1e-4)
    grid = _voxelize(near, cell)
    start = min(grid, key=lambda k: sum(((k[i] + 0.5) * cell - wrist[i]) ** 2 for i in range(3)))
    seen, stack = {start}, [start]
    while stack:
        k = stack.pop()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    nb = (k[0] + dx, k[1] + dy, k[2] + dz)
                    if nb in grid and nb not in seen:
                        seen.add(nb)
                        stack.append(nb)
    hand = [p for k in seen for p in grid[k] if s_of(p) > 0.0]
    if len(hand) < 20:
        return {}
    hand_len = _percentile(sorted(s_of(p) for p in hand), 0.99)
    if hand_len <= 1e-6:
        return {}

    tipzone = [p for p in hand if s_of(p) >= 0.70 * hand_len] or hand
    lats = sorted(l_of(p) for p in tipzone)
    lo, hi = _percentile(lats, 0.05), _percentile(lats, 0.95)
    mid = [p for p in hand if 0.15 * hand_len <= s_of(p) <= 0.65 * hand_len] or hand
    mlats = sorted(l_of(p) for p in mid)
    stick_pos = _percentile(mlats, 0.98) - hi
    stick_neg = lo - _percentile(mlats, 0.02)
    if abs(stick_pos - stick_neg) > 0.02 * hand_len:
        thumb_sign = 1.0 if stick_pos > stick_neg else -1.0
    else:   # no clear thumb: it points to the character's front
        thumb_sign = 1.0 if _vdot(lat, front) > 0 else -1.0
    width = max(hi - lo, 1e-6)
    edge = hi if thumb_sign > 0 else lo

    def at(s, l, dz=0.0):
        return _vadd(_vadd(_vadd(wrist, _vmul(axis, s)), _vmul(lat, l)), (0.0, 0.0, dz))

    def band_dz(pts):
        return _percentile(sorted(p[2] - wrist[2] for p in pts), 0.5) if pts else 0.0

    tag = "_" + side
    out = {"FINGER_PALM" + tag: at(0.25 * hand_len, 0.5 * (lo + hi), band_dz(mid))}
    for i, finger in enumerate(_FINGERS):
        c = edge - thumb_sign * width * (i + 0.5) / 4.0
        band = [p for p in tipzone if abs(l_of(p) - c) <= width / 8.0] or tipzone
        s_max = max(s_of(p) for p in band)
        tip_pts = [p for p in band if s_of(p) >= s_max - 0.06 * hand_len]
        out["FINGER_%s_TIP%s" % (finger, tag)] = tuple(
            sum(p[a] for p in tip_pts) / len(tip_pts) for a in range(3))
        base_pts = [p for p in hand if abs(s_of(p) - FINGER_BASE_FRACTION * hand_len)
                    <= 0.08 * hand_len and abs(l_of(p) - c) <= width / 8.0]
        out["FINGER_%s_BASE%s" % (finger, tag)] = at(
            FINGER_BASE_FRACTION * hand_len, c, band_dz(base_pts))
    thumb_zone = [p for p in hand if 0.05 * hand_len <= s_of(p) <= 0.75 * hand_len
                  and (l_of(p) - edge) * thumb_sign > -0.1 * width]
    if thumb_zone:
        t_tip = max(thumb_zone, key=lambda p: (l_of(p) - edge) * thumb_sign + 0.5 * s_of(p))
    else:
        t_tip = at(0.45 * hand_len, edge + thumb_sign * 0.3 * width)
    out["FINGER_THUMB_TIP" + tag] = tuple(t_tip)
    out["FINGER_THUMB_BASE" + tag] = at(0.08 * hand_len, edge - thumb_sign * 0.1 * width,
                                        band_dz(mid))
    out["FINGER_TIP" + tag] = out["FINGER_MIDDLE_TIP" + tag]
    return out
