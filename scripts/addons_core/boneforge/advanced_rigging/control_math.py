"""BoneCraft — control-layer math (pure, no ``bpy``).

The headlessly-testable kernel behind the animator control layer
(``control_layer.py``): pole-vector placement for IK/FK matching, and the
canonical engine bone-name map for a limb. Kept free of ``bpy`` so the
maths that guarantees "no control pop" on an IK/FK switch can be unit
tested without a host.

Clean-room: standard vector geometry (projection of the mid joint onto the
root→end line, offset along the in-plane bend direction). Bone names mirror
the BoneCraft-native scheme emitted by ``autorig.components.limb`` — hyphen
side suffix, e.g. ``forearm.fk-L``.
"""
import math

Vec = tuple  # a 3-tuple (x, y, z)


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _mul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _length(a):
    return math.sqrt(_dot(a, a))


def _normalize(a):
    n = _length(a)
    if n < 1e-12:
        return (0.0, 0.0, 0.0)
    return (a[0] / n, a[1] / n, a[2] / n)


def pole_position(root, mid, end, distance=0.4):
    """Pole-target location reproducing the *root→mid→end* bend plane.

    ``root`` (shoulder/hip), ``mid`` (elbow/knee) and ``end`` (wrist/ankle)
    are world or armature-space points. The pole is placed in the plane of
    the three joints, on the side the mid joint bends toward, ``distance``
    away from the mid joint. Placing an IK pole here makes an IK solve match
    the FK chain's bend *and* roll, so switching does not pop.

    Degenerate (perfectly straight) chains fall back to a stable offset so
    callers never get a zero vector.
    """
    line = _sub(end, root)
    line_len_sq = _dot(line, line)
    if line_len_sq < 1e-12:
        # root and end coincide — no defined plane; offset along mid.
        return _add(mid, (0.0, -distance, 0.0))
    t = _dot(_sub(mid, root), line) / line_len_sq
    proj = _add(root, _mul(line, t))           # mid projected onto root→end
    bend_dir = _sub(mid, proj)
    if _length(bend_dir) < 1e-9:
        # straight chain: pick a deterministic perpendicular in -Y.
        bend_dir = (0.0, -1.0, 0.0)
    return _add(mid, _mul(_normalize(bend_dir), distance))


def bend_plane_normal(root, mid, end):
    """Unit normal of the limb's bend plane (cross of the two segments)."""
    u = _sub(mid, root)
    v = _sub(end, mid)
    n = (u[1] * v[2] - u[2] * v[1],
         u[2] * v[0] - u[0] * v[2],
         u[0] * v[1] - u[1] * v[0])
    return _normalize(n)


# -- engine bone naming (BoneForge-native) -----------------------------

_ARM_SEG = ("upperarm", "forearm", "hand")
_LEG_SEG = ("thigh", "shin", "foot")


def limb_segments(kind):
    return list(_ARM_SEG if kind == "arm" else _LEG_SEG)


def limb_bone_names(kind, side, tag=""):
    """Canonical bone-name map for one engine limb.

    Mirrors ``autorig.components.limb.build_limb`` exactly so the control
    layer addresses the right bones. ``tag`` matches the quadruped
    front/back limbs (``front``/``back``); default is the biped limb.
    """
    seg = limb_segments(kind)
    pre = (tag + "_") if tag else ""
    limb_id = ("%s-%s" % (tag, kind)) if tag else kind

    def s(base):
        return "%s-%s" % (base, side)

    return {
        "kind": kind,
        "side": side,
        "tag": tag,
        "seg": seg,
        "fk": [s("%s%s.fk" % (pre, x)) for x in seg],
        "def": [s("%s%s.def" % (pre, x)) for x in seg],
        "mch": [s("%s%s.mch_ik" % (pre, x)) for x in seg[:2]],
        "ik": s("%s%s.ik" % (pre, seg[1])),
        "pole": s("%s%s.pole" % (pre, kind)),
        "prop": "IK_FK-%s-%s" % (limb_id, side),
    }


def parse_limb_prop(prop_name):
    """Inverse of the ``IK_FK-<limb_id>-<side>`` property name.

    Returns ``(kind, side, tag)`` or ``None`` if ``prop_name`` is not an
    IK/FK blend property. ``limb_id`` is ``<kind>`` or ``<tag>-<kind>``.
    """
    if not prop_name.startswith("IK_FK-"):
        return None
    body = prop_name[len("IK_FK-"):]
    parts = body.split("-")
    if len(parts) < 2:
        return None
    side = parts[-1]
    limb_id = "-".join(parts[:-1])
    if "-" in limb_id:
        tag, kind = limb_id.split("-", 1)
    else:
        tag, kind = "", limb_id
    return (kind, side, tag)
