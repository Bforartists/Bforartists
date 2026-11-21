"""BoneCraft — retargeting core (pure, no ``bpy``) for R4 (BF-GAP-04).

The headlessly-testable heart of the complete retargeting workflow:

* **map consumption + namespace** — turn a ``maps/`` preset into a concrete
  source->target mapping against a source armature's bone names, stripping
  motion-capture namespaces (``mixamorig:Hips`` -> ``Hips``) and reporting
  missing source/target bones (diagnostics, not silent drops);
* **per-bone tweaks** — additive location/rotation offsets and a rotation
  multiplier stored per mapping, with a clean reset;
* **rotation retarget math** — conjugate a source local rotation by the
  rest-orientation delta so the motion lands in the target bone's frame
  (this is what makes the result match the source instead of just sharing
  bone names). Quaternions are plain ``(w, x, y, z)`` tuples.

Clean-room: standard quaternion algebra + first-principles mapping logic.
"""
from dataclasses import dataclass, field


# ── namespace handling ────────────────────────────────────────

def strip_namespace(name):
    """Drop a leading ``prefix:`` or ``prefix|`` motion-capture namespace."""
    for sep in (":", "|"):
        if sep in name:
            name = name.rsplit(sep, 1)[-1]
    return name


# ── map consumption + diagnostics ─────────────────────────────

def build_mappings(preset, source_names, target_names, strip_ns=True):
    """Resolve a ``maps/`` preset against real bone-name sets.

    ``preset`` is the loaded map dict (``{"name", "bones": {src: tgt}}``).
    Returns ``{"mappings": [...], "missing_source": [...],
    "missing_target": [...]}`` where each mapping is
    ``{"source", "target", "matched"}``. A source bone is matched if it (or
    its namespace-stripped form) exists in ``source_names`` and its target
    exists in ``target_names``.
    """
    source_set = set(source_names)
    stripped_index = {}
    if strip_ns:
        for n in source_names:
            stripped_index.setdefault(strip_namespace(n), n)
    target_set = set(target_names)

    mappings, missing_source, missing_target = [], [], []
    for src, tgt in preset.get("bones", {}).items():
        actual_src = None
        if src in source_set:
            actual_src = src
        elif strip_ns and strip_namespace(src) in stripped_index:
            actual_src = stripped_index[strip_namespace(src)]
        elif strip_ns and src in stripped_index:
            actual_src = stripped_index[src]

        tgt_ok = tgt in target_set
        matched = actual_src is not None and tgt_ok
        mappings.append({"source": actual_src or src, "target": tgt,
                         "matched": matched})
        if actual_src is None:
            missing_source.append(src)
        if not tgt_ok:
            missing_target.append(tgt)
    return {"mappings": mappings, "missing_source": missing_source,
            "missing_target": missing_target}


def matched_name_map(result):
    """``{source: target}`` for the matched entries of a build_mappings result."""
    return {m["source"]: m["target"] for m in result["mappings"] if m["matched"]}


# ── per-bone tweaks ───────────────────────────────────────────

@dataclass
class BoneTweak:
    """Per-mapping correction applied on top of a retargeted transform."""
    loc_offset: tuple = (0.0, 0.0, 0.0)
    rot_offset: tuple = (0.0, 0.0, 0.0)      # euler radians
    rot_multiplier: float = 1.0

    def is_identity(self):
        return (self.loc_offset == (0.0, 0.0, 0.0)
                and self.rot_offset == (0.0, 0.0, 0.0)
                and self.rot_multiplier == 1.0)


def reset_tweak():
    return BoneTweak()


def apply_tweak(loc, rot_euler, tweak):
    """Apply a tweak to a (location, euler-rotation) pair. Pure."""
    loc2 = tuple(loc[i] + tweak.loc_offset[i] for i in range(3))
    rot2 = tuple(rot_euler[i] * tweak.rot_multiplier + tweak.rot_offset[i]
                 for i in range(3))
    return loc2, rot2


# ── quaternion algebra (w, x, y, z) ───────────────────────────

def q_mul(a, b):
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return (aw * bw - ax * bx - ay * by - az * bz,
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw)


def q_conj(q):
    w, x, y, z = q
    return (w, -x, -y, -z)


def q_norm(q):
    import math
    n = math.sqrt(sum(c * c for c in q)) or 1.0
    return tuple(c / n for c in q)


def retarget_quat(rest_delta, source_local):
    """Map a source bone's local rotation into the target frame.

    ``rest_delta`` is the unit quaternion rotating the source rest orientation
    onto the target rest orientation; ``source_local`` is the source bone's
    local rotation. Returns the target local rotation
    ``delta * source_local * delta⁻¹`` (conjugation preserves the motion while
    re-expressing it in the target's rest frame). When ``rest_delta`` is
    identity the source rotation passes through unchanged.
    """
    return q_norm(q_mul(q_mul(rest_delta, source_local), q_conj(rest_delta)))
