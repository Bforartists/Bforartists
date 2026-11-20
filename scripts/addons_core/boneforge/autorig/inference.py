"""BoneCraft — smart landmark detection (BF-GAP-01 / R1).

Two-tier marker proposal for the auto-rig wizard:

1. **Geometry fallback** — always available, pure ``geo_detect`` kernel over
   the mesh's evaluated world-space vertices. Produces confidence-tagged
   proposals for every body marker (intermediate joints interpolated).
2. **Optional local model** — if a local model file *and* its runtime are
   present, a provider is loaded lazily and used; on any absence or error the
   detection silently falls back to geometry. Missing model files never break
   registration.

Proposals are written to the wizard session with their confidence, but are
**never auto-confirmed** — the animator accepts high-confidence markers in
bulk, resets low-confidence ones, or mirrors a confirmed side.

Clean-room: first-principles geometry + a generic provider interface; no
third-party detection source or model is shipped or required.
"""

import os
from dataclasses import dataclass, field

import bpy

# Pure helper lives in the kernel (importable without bpy); re-exported here.
from boneforge.autorig.geo_detect import confidence_category  # noqa: F401


# ── Result dataclass ──────────────────────────────────────────

@dataclass
class InferenceResult:
    """Result of running marker detection.

    ``proposals`` maps a BODY_MARKERS name to ``(position_tuple, confidence)``;
    position is world-space, confidence is in [0, 1].
    """
    success: bool = False
    message: str = ""
    proposals: dict = field(default_factory=dict)


# Markers at/above this confidence are offered for bulk-accept; below it they
# are the "review/adjust" set that "reset low-confidence" clears.
ACCEPT_THRESHOLD = 0.6


# ── Mesh sampling (in-host) ───────────────────────────────────

def sample_point_cloud(mesh_obj, num_points=5000, context=None):
    """World-space points from the *evaluated* mesh (modifiers applied).

    Strides the evaluated vertices down to about ``num_points`` so detection
    stays fast on dense meshes. Returns ``list[tuple[float,float,float]]``.
    """
    ctx = context or bpy.context
    deps = ctx.evaluated_depsgraph_get()
    eval_obj = mesh_obj.evaluated_get(deps)
    mesh = eval_obj.to_mesh()
    try:
        verts = mesh.vertices
        count = len(verts)
        if count == 0:
            return []
        matrix_world = mesh_obj.matrix_world
        step = max(1, count // max(1, num_points))
        return [tuple(matrix_world @ verts[i].co)
                for i in range(0, count, step)]
    finally:
        eval_obj.to_mesh_clear()


def normalize_point_cloud(points):
    """Center at origin and scale to a unit sphere.

    Returns ``(normalized_points, center, scale)`` — the inverse transform a
    model provider needs to map normalized predictions back to world space.
    """
    from boneforge.autorig import geo_detect
    return geo_detect.normalize_points(points)


# ── Optional local-model provider (lazy, falls back) ──────────

def _model_path(context=None):
    """Resolve an optional local model file path from preferences, or None.

    Never raises and never imports a heavy runtime; just a path string check.
    """
    try:
        from boneforge.core import addon_prefs
        prefs = addon_prefs(context or bpy.context)
        path = getattr(prefs, "detection_model_path", "") if prefs else ""
        if path and os.path.exists(path):
            return path
    except Exception:
        pass
    return None


def _load_model_provider(model_path):
    """Load a local detection model if its runtime is available, else None.

    The runtime (e.g. onnxruntime) is imported lazily and optionally; any
    failure returns None so detection falls back to geometry.
    """
    if not model_path or not os.path.exists(model_path):
        return None
    try:  # pragma: no cover - exercised only when a model+runtime exist
        import onnxruntime  # noqa: F401  (optional, never a hard dependency)
    except Exception:
        return None
    try:  # pragma: no cover
        session = onnxruntime.InferenceSession(model_path)
        return _OnnxProvider(session)
    except Exception:
        return None


class _OnnxProvider:  # pragma: no cover - requires a model file at runtime
    """Adapter around a local ONNX session. Output: (N, 4) = (x, y, z, conf)
    in normalized space; mapped back to world via the normalize transform."""

    def __init__(self, session):
        self._session = session

    def infer(self, points):
        import numpy as np
        from boneforge.autorig import geo_detect
        norm, center, scale = normalize_point_cloud(points)
        arr = np.asarray(norm, dtype="float32")[None, ...]
        name = self._session.get_inputs()[0].name
        out = self._session.run(None, {name: arr})[0]
        geo = geo_detect.guess_landmarks(points)        # names for the rows
        proposals = {}
        order = list(geo_detect.body_marker_proposals(geo).keys())
        for i, row in enumerate(out.reshape(-1, 4)):
            if i >= len(order):
                break
            world = tuple(float(row[a]) * scale + center[a] for a in range(3))
            proposals[order[i]] = (world, float(row[3]))
        return InferenceResult(success=True, message="model", proposals=proposals)


# ── Detection (two-tier) ──────────────────────────────────────

def detect_landmarks(points, model_path=None):
    """Run detection: optional model first, geometry fallback always.

    ``points`` is a world-space point cloud. Returns an ``InferenceResult``.
    """
    if not points:
        return InferenceResult(False, "No geometry to analyse", {})
    from boneforge.autorig import geo_detect
    try:
        points = geo_detect.preprocess_points(points)
    except ValueError:
        return InferenceResult(False, "No geometry to analyse", {})

    provider = _load_model_provider(model_path)
    if provider is not None:
        try:
            result = provider.infer(points)
            if result.success and result.proposals:
                return result
        except Exception:
            pass  # fall back to geometry

    geo = geo_detect.guess_landmarks(points)
    props = geo_detect.body_marker_proposals(geo)
    proposals = {name: (p["pos"], p["confidence"]) for name, p in props.items()}
    return InferenceResult(True, "geometry", proposals)


def _write_proposals_to_session(session, proposals):
    """Write detected proposals to body markers (never auto-confirms)."""
    from boneforge.autorig.session import get_body_marker, _ensure_marker_slots
    _ensure_marker_slots(session)
    written = 0
    high = 0
    for name, (pos, conf) in proposals.items():
        marker = get_body_marker(session, name)
        if marker is None:
            continue
        marker.position = tuple(pos)
        marker.confidence = float(conf)
        marker.confirmed = False                 # never silently accepted
        written += 1
        if conf >= ACCEPT_THRESHOLD:
            high += 1
    return written, high


# ── Operators ─────────────────────────────────────────────────

def _session(context):
    return context.scene.boneforge_autorig_session


class BF_OT_RunDetection(bpy.types.Operator):
    """Propose joint markers automatically from the selected mesh"""

    bl_idname = "boneforge.autorig_run_detection"
    bl_label = "Auto-Detect Joints"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        session = getattr(context.scene, "boneforge_autorig_session", None)
        if session is None:
            return False
        mesh = bpy.data.objects.get(session.mesh_object_name)
        if mesh is None and context.active_object is not None:
            mesh = context.active_object
        return mesh is not None and mesh.type == 'MESH'

    def execute(self, context):
        from boneforge import bfa_guard
        bfa_guard.require_bforartists("inference")     # BFA-only, even via script
        session = _session(context)
        mesh = bpy.data.objects.get(session.mesh_object_name) \
            or context.active_object
        if mesh is None or mesh.type != 'MESH':
            self.report({'ERROR'}, "Select a mesh to detect")
            return {'CANCELLED'}
        points = sample_point_cloud(mesh, context=context)
        result = detect_landmarks(points, model_path=_model_path(context))
        if not result.success:
            self.report({'WARNING'}, result.message)
            return {'CANCELLED'}
        written, high = _write_proposals_to_session(session, result.proposals)
        if context.area:
            context.area.tag_redraw()
        self.report({'INFO'},
                    "Detected %d markers (%s); %d high-confidence — review "
                    "before confirming" % (written, result.message, high))
        return {'FINISHED'}


class BF_OT_AcceptHighConfidence(bpy.types.Operator):
    """Confirm all placed markers at or above the accept threshold"""

    bl_idname = "boneforge.autorig_accept_high"
    bl_label = "Accept High-Confidence"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        session = getattr(context.scene, "boneforge_autorig_session", None)
        return session is not None and session.is_active

    def execute(self, context):
        from boneforge.autorig.constants import BODY_MARKERS
        from boneforge.autorig.session import _ensure_marker_slots
        session = _session(context)
        _ensure_marker_slots(session)
        n = 0
        for i in range(len(BODY_MARKERS)):
            marker = session.body_markers[i]
            if not marker.confirmed and marker.confidence >= ACCEPT_THRESHOLD:
                marker.confirmed = True
                n += 1
        if context.area:
            context.area.tag_redraw()
        self.report({'INFO'}, "Accepted %d high-confidence markers" % n)
        return {'FINISHED'}


class BF_OT_ResetLowConfidence(bpy.types.Operator):
    """Clear placed markers below the accept threshold for re-placement"""

    bl_idname = "boneforge.autorig_reset_low"
    bl_label = "Reset Low-Confidence"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        session = getattr(context.scene, "boneforge_autorig_session", None)
        return session is not None and session.is_active

    def execute(self, context):
        from boneforge.autorig.constants import BODY_MARKERS
        from boneforge.autorig.session import _ensure_marker_slots
        session = _session(context)
        _ensure_marker_slots(session)
        n = 0
        for i in range(len(BODY_MARKERS)):
            marker = session.body_markers[i]
            if not marker.confirmed and 0.0 < marker.confidence < ACCEPT_THRESHOLD:
                marker.position = (0.0, 0.0, 0.0)
                marker.confidence = 0.0
                n += 1
        if context.area:
            context.area.tag_redraw()
        self.report({'INFO'}, "Reset %d low-confidence markers" % n)
        return {'FINISHED'}


class BF_OT_MirrorConfirmed(bpy.types.Operator):
    """Mirror confirmed markers from one side to their symmetry partner"""

    bl_idname = "boneforge.autorig_mirror_confirmed"
    bl_label = "Mirror Confirmed Side"
    bl_options = {'REGISTER', 'UNDO'}

    from_side: bpy.props.EnumProperty(options={'HIDDEN', 'SKIP_SAVE'},
        name="From",
        items=[('LEFT', "Left", "Copy left to right"),
               ('RIGHT', "Right", "Copy right to left")],
        default='LEFT',
    )

    @classmethod
    def poll(cls, context):
        session = getattr(context.scene, "boneforge_autorig_session", None)
        return session is not None and session.is_active

    def execute(self, context):
        from boneforge.autorig.constants import BODY_SYMMETRY_PAIRS
        from boneforge.autorig.session import get_body_marker, _ensure_marker_slots
        session = _session(context)
        _ensure_marker_slots(session)
        center_x = self._mesh_center_x(session)
        n = 0
        for left, right in BODY_SYMMETRY_PAIRS:
            src_name, dst_name = (left, right) if self.from_side == 'LEFT' \
                else (right, left)
            src = get_body_marker(session, src_name)
            dst = get_body_marker(session, dst_name)
            if src is None or dst is None or not src.confirmed:
                continue
            mx, my, mz = src.position
            dst.position = (2.0 * center_x - mx, my, mz)
            dst.confidence = src.confidence
            dst.confirmed = True
            n += 1
        if context.area:
            context.area.tag_redraw()
        self.report({'INFO'}, "Mirrored %d markers" % n)
        return {'FINISHED'}

    @staticmethod
    def _mesh_center_x(session):
        mesh = bpy.data.objects.get(session.mesh_object_name) if session else None
        if mesh is None:
            return 0.0
        from mathutils import Vector
        xs = [(mesh.matrix_world @ Vector(c)).x for c in mesh.bound_box]
        return (min(xs) + max(xs)) * 0.5


class BF_OT_CancelDetection(bpy.types.Operator):
    """Cancel a running detection"""

    bl_idname = "boneforge.autorig_cancel_detection"
    bl_label = "Cancel Detection"
    bl_options = {'REGISTER'}

    def execute(self, context):
        return {'CANCELLED'}


# ── Registration ──────────────────────────────────────────────

classes = (
    BF_OT_RunDetection,
    BF_OT_AcceptHighConfidence,
    BF_OT_ResetLowConfidence,
    BF_OT_MirrorConfirmed,
    BF_OT_CancelDetection,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
