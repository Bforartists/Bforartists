"""BoneCraft — control-widget shape library (Task 5, BF-DATA-01).

Original, BoneCraft-native control widgets (vertex/edge data only) plus a
role->widget/colour map and a lazy ``ensure_widget_object`` that realises a
widget as a hidden mesh for ``PoseBone.custom_shape``.

Clean-room: every shape is generated procedurally from first principles in
this file. No control-shape mesh, icon, or asset from any third-party rig
is imported or reproduced.
"""
import math

WIDGET_COLLECTION = "BoneForge_Widgets"


# -- procedural shape generators (pure: return (verts, edges)) ----------

def _ring(radius=1.0, segments=16, axis="Z"):
    verts = []
    for i in range(segments):
        a = (i / segments) * 2 * math.pi
        c, s = radius * math.cos(a), radius * math.sin(a)
        if axis == "Z":
            verts.append((c, s, 0.0))
        elif axis == "X":
            verts.append((0.0, c, s))
        else:
            verts.append((c, 0.0, s))
    edges = [(i, (i + 1) % segments) for i in range(segments)]
    return verts, edges


def w_fk_ring():
    return _ring(0.12, 16, axis="X")


def w_circle():
    return _ring(0.12, 24)


def w_circle_small():
    return _ring(0.04, 12)


def w_root_circle():
    return _ring(0.30, 32)


def w_cube():
    s = 0.1
    v = [(-s, -s, -s), (s, -s, -s), (s, s, -s), (-s, s, -s),
         (-s, -s, s), (s, -s, s), (s, s, s), (-s, s, s)]
    e = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4),
         (0, 4), (1, 5), (2, 6), (3, 7)]
    return v, e


def w_diamond():
    s = 0.08
    v = [(s, 0, 0), (0, s, 0), (-s, 0, 0), (0, -s, 0),
         (0, 0, s), (0, 0, -s)]
    e = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 4), (1, 4), (2, 4), (3, 4),
         (0, 5), (1, 5), (2, 5), (3, 5)]
    return v, e


def w_sphere():
    v, e = [], []
    for ai, axis in enumerate(("Z", "X", "Y")):
        rv, re = _ring(0.1, 16, axis=axis)
        off = len(v)
        v.extend(rv)
        e.extend([(off + a, off + b) for (a, b) in re])
    return v, e


def w_ik_pin():
    rv, re = _ring(0.06, 12)
    v = list(rv) + [(0, 0, 0), (0, 0, 0.18)]
    e = list(re) + [(len(rv), len(rv) + 1)]
    return v, e


def w_foot_plate():
    v = [(-0.08, -0.10, 0), (0.08, -0.10, 0),
         (0.08, 0.22, 0), (-0.08, 0.22, 0)]
    e = [(0, 1), (1, 2), (2, 3), (3, 0)]
    return v, e


def w_gear():
    v, e = [], []
    teeth = 8
    for i in range(teeth * 2):
        a = (i / (teeth * 2)) * 2 * math.pi
        r = 0.12 if i % 2 == 0 else 0.08
        v.append((r * math.cos(a), r * math.sin(a), 0))
    e = [(i, (i + 1) % len(v)) for i in range(len(v))]
    return v, e


def w_eye_target():
    rv, re = _ring(0.05, 16)
    return rv, re


def w_arrow():
    v = [(0, 0, 0), (0, 0.15, 0), (-0.04, 0.10, 0),
         (0, 0.15, 0), (0.04, 0.10, 0)]
    e = [(0, 1), (1, 2), (3, 4)]
    return v, e


# id -> generator
WIDGET_LIBRARY = {
    "fk_ring": w_fk_ring,
    "circle": w_circle,
    "circle_small": w_circle_small,
    "root_circle": w_root_circle,
    "cube": w_cube,
    "diamond": w_diamond,
    "sphere": w_sphere,
    "ik_pin": w_ik_pin,
    "foot_plate": w_foot_plate,
    "gear": w_gear,
    "eye_target": w_eye_target,
    "arrow": w_arrow,
}

# role -> bone-collection colour palette index / rgb (BoneForge-native)
COLOR_GROUPS = {
    "fk":      (0.18, 0.55, 0.90),   # blue
    "ik":      (0.90, 0.45, 0.15),   # orange
    "root":    (0.95, 0.85, 0.20),   # yellow
    "special": (0.55, 0.30, 0.85),   # purple
    "deform":  (0.40, 0.40, 0.40),   # grey
}


def coverage_report(referenced_ids):
    """Return ids referenced by a plan that the library does not define."""
    return sorted(set(referenced_ids) - set(WIDGET_LIBRARY))


# -- bpy realisation (lazy) --------------------------------------------

def ensure_widget_object(widget_id, context=None):
    """Create (or reuse) a hidden mesh object for ``widget_id``."""
    import bpy
    gen = WIDGET_LIBRARY.get(widget_id)
    if gen is None:
        return None
    obj_name = "WGT-" + widget_id
    existing = bpy.data.objects.get(obj_name)
    if existing is not None:
        return existing
    verts, edges = gen()
    mesh = bpy.data.meshes.new(obj_name)
    mesh.from_pydata([tuple(v) for v in verts], [tuple(e) for e in edges], [])
    mesh.update()
    obj = bpy.data.objects.new(obj_name, mesh)
    # park in a hidden widget collection
    coll = bpy.data.collections.get(WIDGET_COLLECTION)
    if coll is None:
        coll = bpy.data.collections.new(WIDGET_COLLECTION)
        try:
            context = context or bpy.context
            context.scene.collection.children.link(coll)
            coll.hide_viewport = True
            coll.hide_render = True
        except Exception:
            pass
    coll.objects.link(obj)
    return obj


# -- Task 5+ : additional face / control widgets (appended) -------------

def w_lip():
    # shallow downward arc
    import math as _m
    v = [(-0.06 + 0.012 * i, -0.02 * _m.sin(_m.pi * i / 10.0), 0)
         for i in range(11)]
    e = [(i, i + 1) for i in range(len(v) - 1)]
    return v, e


def w_brow():
    import math as _m
    v = [(-0.05 + 0.01 * i, 0.015 * _m.sin(_m.pi * i / 10.0), 0)
         for i in range(11)]
    e = [(i, i + 1) for i in range(len(v) - 1)]
    return v, e


def w_jaw():
    v = [(-0.05, 0.0, 0), (-0.04, -0.06, 0), (0.04, -0.06, 0), (0.05, 0.0, 0)]
    e = [(0, 1), (1, 2), (2, 3)]
    return v, e


def w_half_circle():   # eyelids
    import math as _m
    seg = 10
    v = [(0.04 * _m.cos(_m.pi * i / seg), 0.04 * _m.sin(_m.pi * i / seg), 0)
         for i in range(seg + 1)]
    e = [(i, i + 1) for i in range(len(v) - 1)]
    return v, e


def w_crosshair():
    s = 0.05
    v = [(-s, 0, 0), (s, 0, 0), (0, -s, 0), (0, s, 0)]
    e = [(0, 1), (2, 3)]
    return v, e


def w_square():
    s = 0.06
    v = [(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)]
    e = [(0, 1), (1, 2), (2, 3), (3, 0)]
    return v, e


WIDGET_LIBRARY.update({
    "lip": w_lip,
    "brow": w_brow,
    "jaw": w_jaw,
    "eyelid": w_half_circle,
    "crosshair": w_crosshair,
    "square": w_square,
})

COLOR_GROUPS["face"] = (0.20, 0.80, 0.55)   # teal for facial controls
