"""BoneCraft Phase 3B — Production Skinning Pipeline.

Multi-stage weight assignment pipeline that replaces the single-call
``bpy.ops.object.parent_set(type='ARMATURE_AUTO')`` with a 7-step
production workflow:

    1. Mesh validation
    2. Base weight assignment (AUTO → ENVELOPE → distance fallback)
    3. Face / body weight isolation
    4. Laplacian weight smoothing
    5. Weight normalization (influence limit + sum-to-one)
    6. Corrective presets (shoulder, elbow, hip, knee)
    7. Quality scoring

All steps use only Blender's Python API (bpy, bmesh, mathutils).
No external dependencies.

The pipeline ALWAYS produces output — the quality score tells the
user how good the result is; the pipeline never refuses.
"""

import bmesh
import bpy
from mathutils import Vector

from boneforge.autorig.constants import (
    FACE_CONTROLS_COLLECTION,
    FACE_DEFORM_COLLECTION,
    FACE_MARKERS,
    CORRECTIVE_PRESETS,
    NON_MANIFOLD_AUTO_WEIGHT_THRESHOLD,
    WEIGHT_DISCONTINUITY_THRESHOLD,
    ZERO_AREA_THRESHOLD,
    FACE_RADIUS_MULTIPLIER,
    MIN_WEIGHT_EPSILON,
)
from boneforge.autorig.session import get_face_marker, is_position_placed

import logging

logger = logging.getLogger(__name__)

# ── Module constants ───────────────────────────────────────────

# SIG-5: Laplacian smoothing blend factor (self weight vs neighbor average).
# Higher values preserve each vertex's original weight and limit neighbor
# bleed; 0.75 keeps smoothing useful near bone boundaries while avoiding
# the mushy, over-blended distributions that ARMATURE_AUTO tends to
# produce on organic meshes.
_LAPLACIAN_SELF_WEIGHT: float = 0.75

# Power curve applied to vertex weights before the final normalization pass.
# Values >1 sharpen: after raising each weight to this power, the subsequent
# divide-by-sum step concentrates influence onto the dominant bones.
# Lowered v3.0.9 from 2.0 → 1.5 so fingertips and eyelid weights (which
# are legitimately small but non-trivial on humanoid avatars) don't get
# crushed. 1.5 still produces noticeably crisper deformations than 1.0.
# Set to 1.0 to disable sharpening entirely.
_WEIGHT_SHARPEN_POWER: float = 1.5

# MIN-4: Maximum discontinuity count before flagging in quality report
_DISCONTINUITY_SEVERITY_THRESHOLD: int = 10

# SIG-6: Face/body boundary margin as a fraction of face_radius
# Raised v3.0.9 from 0.1 → 0.25 so the neck/jaw transition gets a
# proper smooth blend band rather than a visible hard seam on stock
# humanoid avatars.
_FACE_BORDER_MARGIN_RATIO: float = 0.25

# SIG-7: Weight re-balancing factor at face/body border
# Conservative: 30% toward target, 70% retain original
_BORDER_REBALANCE_FACTOR: float = 0.3

# v3.0.10 — Island rigidification thresholds for stylized humanoid avatars
# (VRoid / VRChat / cyberpunk mech-style models with many separate mesh
# pieces: halos, armor plates, hair crystals, boots, skirts, etc.)
#
# An island is treated as rigid (all verts pinned to its dominant bone
# with weight 1.0) when EITHER condition is met:
#   - vertex count is below _RIGID_ISLAND_MAX_VERTS
#   - OR its bounding box diagonal is below _RIGID_ISLAND_SIZE_RATIO
#     times the largest island's diagonal
#
# Heat-diffusion weights cannot cross island gaps, so without this pass
# every disconnected accessory fractures along its own internal seams
# on any pose — each vertex picks a different "nearest bone" and they
# tear apart.  Rigidifying the whole island to its mass-center's nearest
# bone makes accessories ride with the limb they visually belong to.
_RIGID_ISLAND_MAX_VERTS: int = 500
_RIGID_ISLAND_SIZE_RATIO: float = 0.25

# Progress-bar milestones (percent complete after each pipeline step)
_PROGRESS_TOTAL: int = 100
_PROGRESS_STEP_VALIDATE: int = 5
_PROGRESS_STEP_BASE_WEIGHTS: int = 20
_PROGRESS_STEP_FACE_ISOLATION: int = 40
_PROGRESS_STEP_SMOOTHING: int = 55
_PROGRESS_STEP_NORMALIZE: int = 70
_PROGRESS_STEP_CORRECTIVES: int = 85
_PROGRESS_STEP_QUALITY: int = 95


# ── Registration (no-op — this is a pure library module) ─────

def register():
    """No-op: skin_gen has no Blender classes to register."""


def unregister():
    """No-op: skin_gen has no Blender classes to unregister."""


# ── Result types ─────────────────────────────────────────────

class MeshValidationResult:
    """Result of pre-flight mesh topology check.

    Attributes:
        is_valid: True if mesh has no topology issues at all.
        can_auto_weight: True if ARMATURE_AUTO is likely to succeed.
            Heuristic: fails when >5% non-manifold edges or loose verts exist.
        issues: Human-readable descriptions of detected problems.
        non_manifold_count: Number of non-manifold edges.
        loose_vertex_count: Vertices not connected to any face.
        zero_area_face_count: Degenerate faces below area threshold.
    """

    __slots__ = (
        'is_valid', 'can_auto_weight', 'issues',
        'non_manifold_count', 'loose_vertex_count', 'zero_area_face_count',
    )

    def __init__(
        self,
        is_valid=True,
        can_auto_weight=True,
        issues=None,
        non_manifold_count=0,
        loose_vertex_count=0,
        zero_area_face_count=0,
    ):
        self.is_valid = is_valid
        self.can_auto_weight = can_auto_weight
        self.issues = issues if issues is not None else []
        self.non_manifold_count = non_manifold_count
        self.loose_vertex_count = loose_vertex_count
        self.zero_area_face_count = zero_area_face_count


class SkinningQualityReport:
    """Automated quality assessment of the final weight assignment.

    Attributes:
        overall_score: 0.0–1.0 geometric mean of sub-scores.
        per_bone_scores: Per-bone coverage scores {bone_name: float}.
        unweighted_vertices: Count of verts with zero total weight.
        discontinuity_count: Adjacent vert pairs with weight delta > threshold.
        max_influence_violations: Verts exceeding the influence budget.
        flagged_regions: List of (description_str,) for problem areas.
    """

    __slots__ = (
        'overall_score', 'per_bone_scores', 'unweighted_vertices',
        'discontinuity_count', 'max_influence_violations', 'flagged_regions',
    )

    def __init__(
        self,
        overall_score=0.0,
        per_bone_scores=None,
        unweighted_vertices=0,
        discontinuity_count=0,
        max_influence_violations=0,
        flagged_regions=None,
    ):
        self.overall_score = overall_score
        self.per_bone_scores = per_bone_scores if per_bone_scores is not None else {}
        self.unweighted_vertices = unweighted_vertices
        self.discontinuity_count = discontinuity_count
        self.max_influence_violations = max_influence_violations
        self.flagged_regions = flagged_regions if flagged_regions is not None else []


class SkinningResult:
    """Final outcome of the production skinning pipeline.

    Attributes:
        success: True if weights were assigned (always True due to fallback).
        method: Which base weight method was used: 'AUTO', 'ENVELOPE', or 'FALLBACK'.
        quality_report: The quality assessment from step 7.
        warnings: Human-readable warnings accumulated during the pipeline.
        face_isolation_applied: Whether face/body isolation ran.
        correctives_applied: Whether corrective presets were applied.
    """

    __slots__ = (
        'success', 'method', 'quality_report', 'warnings',
        'face_isolation_applied', 'correctives_applied',
    )

    def __init__(
        self,
        success=False,
        method='',
        quality_report=None,
        warnings=None,
        face_isolation_applied=False,
        correctives_applied=False,
    ):
        self.success = success
        self.method = method
        self.quality_report = quality_report if quality_report is not None else SkinningQualityReport()
        self.warnings = warnings if warnings is not None else []
        self.face_isolation_applied = face_isolation_applied
        self.correctives_applied = correctives_applied


# ── Step 1: Mesh validation ──────────────────────────────────

def validate_mesh(mesh_obj, depsgraph):
    """Pre-flight mesh check before weight assignment.

    Evaluates the mesh for topology issues that commonly cause
    Blender's automatic weight painting to fail or produce poor
    results.  Does NOT modify the mesh — only reports issues.

    Uses bmesh for efficient topology queries.  The bmesh is
    created from the evaluated (modifier-applied) mesh to catch
    issues introduced by modifiers.

    Args:
        mesh_obj: The target mesh object.
        depsgraph: Blender's evaluated dependency graph.

    Returns:
        MeshValidationResult with topology analysis.
    """
    # CRIT-3 fix: ensure bmesh and evaluated_mesh are always freed
    bm = bmesh.new()
    evaluated_obj = None
    evaluated_mesh = None
    try:
        evaluated_obj = mesh_obj.evaluated_get(depsgraph)
        evaluated_mesh = evaluated_obj.to_mesh()
        bm.from_mesh(evaluated_mesh)
    except (RuntimeError, AttributeError) as error:
        return MeshValidationResult(
            is_valid=False,
            can_auto_weight=False,
            issues=[f"Failed to evaluate mesh: {error}"],
        )
    finally:
        # CRIT-3 fix: cleanup in finally block to prevent leaks
        if evaluated_mesh is not None and evaluated_obj is not None:
            evaluated_obj.to_mesh_clear()

    # v3.3.17: wrap the BMesh-walking comprehensions so bm.free runs
    # on exception (e.g. from .is_manifold or .calc_area on degenerate
    # geometry). The previous bm.free() was unreachable from raised
    # exceptions inside the comprehensions.
    try:
        non_manifold_edges = [e for e in bm.edges if not e.is_manifold]
        loose_verts = [v for v in bm.verts if not v.link_faces]
        zero_area_faces = [f for f in bm.faces if f.calc_area() < ZERO_AREA_THRESHOLD]
        edge_count = max(len(bm.edges), 1)
    finally:
        bm.free()

    issues = []
    if non_manifold_edges:
        issues.append(
            f"{len(non_manifold_edges)} non-manifold edge(s) detected — "
            "auto-weights may fail on open or intersecting geometry"
        )
    if loose_verts:
        issues.append(
            f"{len(loose_verts)} loose vertex/vertices not connected to any face"
        )
    if zero_area_faces:
        issues.append(
            f"{len(zero_area_faces)} degenerate face(s) with near-zero area"
        )

    non_manifold_ratio = len(non_manifold_edges) / edge_count
    can_auto = (
        non_manifold_ratio < NON_MANIFOLD_AUTO_WEIGHT_THRESHOLD
        and len(loose_verts) == 0
    )

    return MeshValidationResult(
        is_valid=len(non_manifold_edges) == 0 and len(loose_verts) == 0,
        can_auto_weight=can_auto,
        issues=issues,
        non_manifold_count=len(non_manifold_edges),
        loose_vertex_count=len(loose_verts),
        zero_area_face_count=len(zero_area_faces),
    )


# ── Step 2: Base weight assignment ───────────────────────────

def _select_pair(context, mesh_obj, armature_obj):
    """Select mesh + armature with armature as active for parenting ops.

    Both objects must be in Object mode and in the active view layer.
    """
    if context.view_layer.objects.active is None:
        context.view_layer.objects.active = armature_obj   # mode_set needs one
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    mesh_obj.select_set(True)
    armature_obj.select_set(True)
    context.view_layer.objects.active = armature_obj


def _clear_existing_vertex_groups(mesh_obj):
    """Remove all vertex groups from *mesh_obj*.

    Called before fallback weight methods to prevent stale data from
    a prior failed attempt mixing with fresh weights.
    """
    mesh_obj.vertex_groups.clear()


def _bone_world_center(armature_obj, bone):
    """Compute the world-space center of an armature bone.

    Uses the bone's head and tail positions, transformed by the
    armature's world matrix.
    """
    world_matrix = armature_obj.matrix_world
    head_world = world_matrix @ bone.head_local
    tail_world = world_matrix @ bone.tail_local
    return (head_world + tail_world) * 0.5


def _apply_distance_weights(mesh_obj, armature_obj):
    """Pure-Python distance-based weight assignment fallback.

    For each vertex, finds the closest bone (by world-space distance
    to bone center) and assigns weight 1.0 to that bone.  Also assigns
    partial weight to the second-closest bone for smoother transitions.

    This always succeeds regardless of mesh topology.  Quality is
    lower than AUTO or ENVELOPE but guarantees coverage.
    """
    armature_data = armature_obj.data
    world_matrix = mesh_obj.matrix_world

    # Pre-compute bone centers in world space
    bone_centers = {}
    for bone in armature_data.bones:
        bone_centers[bone.name] = _bone_world_center(armature_obj, bone)

    if not bone_centers:
        return

    # Create vertex groups for all bones
    for bone_name in bone_centers:
        if mesh_obj.vertex_groups.get(bone_name) is None:
            mesh_obj.vertex_groups.new(name=bone_name)

    # Assign each vertex to nearest and second-nearest bone
    mesh_data = mesh_obj.data
    for vertex in mesh_data.vertices:
        vertex_world = world_matrix @ vertex.co

        # Find two closest bones by distance (running two-minimum, no sort)
        nearest_dist, nearest_name = float('inf'), None
        second_dist, second_name = float('inf'), None
        for bone_name, center in bone_centers.items():
            dist = (vertex_world - center).length
            if dist < nearest_dist:
                second_dist, second_name = nearest_dist, nearest_name
                nearest_dist, nearest_name = dist, bone_name
            elif dist < second_dist:
                second_dist, second_name = dist, bone_name

        nearest_group = mesh_obj.vertex_groups[nearest_name]

        if second_name is not None:
            second_group = mesh_obj.vertex_groups[second_name]

            # Blend ratio based on relative distance
            total_dist = nearest_dist + second_dist
            if total_dist > 0:
                nearest_weight = second_dist / total_dist
                second_weight = nearest_dist / total_dist
            else:
                nearest_weight = 1.0
                second_weight = 0.0

            nearest_group.add([vertex.index], nearest_weight, 'REPLACE')
            if second_weight > MIN_WEIGHT_EPSILON:
                second_group.add([vertex.index], second_weight, 'REPLACE')
        else:
            nearest_group.add([vertex.index], 1.0, 'REPLACE')


def _apply_segment_weights(mesh_obj, armature_obj, max_bones=4, power=4.0):
    """Inverse-distance-to-bone-segment weights (topology independent).

    For each vertex, the distance to every deform bone *segment* (not its
    centre) decides the weights: ``w ~ 1 / d**power`` over the nearest
    ``max_bones``. Boundaries land on the bisector between neighbouring
    segments, i.e. at the joints, and nothing depends on the mesh being
    watertight — the case where heat diffusion refuses to run.

    Distances are computed for all vertices at once (numpy); weights are
    written in 1/1024 steps so each (bone, weight) pair is a single
    ``VertexGroup.add`` call instead of one call per vertex.
    """
    import numpy as np
    world = armature_obj.matrix_world
    names, segs = [], []
    for bone in armature_obj.data.bones:
        if bone.use_deform:
            names.append(bone.name)
            segs.append((world @ bone.head_local, world @ bone.tail_local))
    if not segs:
        return False
    groups = [mesh_obj.vertex_groups.get(n) or mesh_obj.vertex_groups.new(name=n)
              for n in names]
    dist = _segment_distances_np(_world_coords_np(mesh_obj), segs)
    k = min(max_bones, len(segs))
    near = np.argpartition(dist, k - 1, axis=1)[:, :k] if k < len(segs) \
        else np.tile(np.arange(len(segs)), (len(dist), 1))
    d = np.take_along_axis(dist, near, axis=1)
    on_bone = d.min(axis=1) <= 1e-9
    w = 1.0 / np.maximum(d, 1e-12) ** power
    w /= w.sum(axis=1, keepdims=True)
    # a vertex on a bone belongs to that bone alone
    first = d.argmin(axis=1)
    w[on_bone] = 0.0
    w[on_bone, first[on_bone]] = 1.0
    q = np.rint(w * 1024.0).astype(np.int64)
    rows = np.repeat(np.arange(len(dist)), k)
    bones = near.ravel()
    steps = q.ravel()
    keep = steps > int(MIN_WEIGHT_EPSILON * 1024.0)
    rows, bones, steps = rows[keep], bones[keep], steps[keep]
    order = np.lexsort((steps, bones))
    rows, bones, steps = rows[order], bones[order], steps[order]
    cut = np.nonzero(np.diff(bones * 2048 + steps))[0] + 1
    for start, end in zip(np.r_[0, cut], np.r_[cut, len(rows)]):
        if end > start:
            groups[int(bones[start])].add(rows[start:end].tolist(),
                                           float(steps[start]) / 1024.0, 'REPLACE')
    return True


# Bone heat is solved per bone over the whole mesh: on dense meshes it gets
# slow and then fails outright (measured on a 678k-vertex body: 134 s, and
# 97% of vertices left unweighted). Above this size heat runs on a decimated
# copy and the weights are interpolated back onto the full mesh.
_HEAT_PROXY_VERTS = 60000
_HEAT_PROXY_TARGET = 40000
# heat that leaves more than this share of vertices unweighted has failed.
# Heat never reaches separate pieces (accessories, clothing islands: pinned
# later by the island passes), so some unweighted vertices are normal; a
# failed solve leaves most of the body unweighted (97% on the 678k body).
_HEAT_MAX_UNWEIGHTED = 0.25


def _count_unweighted(mesh_obj):
    return sum(1 for v in mesh_obj.data.vertices
               if not any(ge.weight > MIN_WEIGHT_EPSILON for ge in v.groups))


def _heat_via_proxy(context, mesh_obj, armature_obj, target=_HEAT_PROXY_TARGET):
    """Bone heat on a decimated copy of ``mesh_obj``, interpolated back.

    The copy drops shape keys and modifiers, is decimated to about
    ``target`` vertices and skinned with bone heat; the Data Transfer
    operator then interpolates its weights onto the full mesh (nearest face,
    barycentric), which also works on meshes with shape keys.
    """
    count = len(mesh_obj.data.vertices)
    proxy_mesh = mesh_obj.data.copy()
    proxy = bpy.data.objects.new(mesh_obj.name + "_BFheat", proxy_mesh)
    context.scene.collection.objects.link(proxy)
    try:
        proxy.matrix_world = mesh_obj.matrix_world.copy()
        if proxy_mesh.shape_keys is not None:
            proxy.shape_key_clear()
        proxy.vertex_groups.clear()
        dec = proxy.modifiers.new("BF_decimate", 'DECIMATE')
        dec.ratio = max(0.01, min(1.0, target / max(count, 1)))
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        proxy.select_set(True)
        context.view_layer.objects.active = proxy
        bpy.ops.object.modifier_apply(modifier=dec.name)
        _select_pair(context, proxy, armature_obj)
        bpy.ops.object.parent_set(type='ARMATURE_AUTO')
        if _count_unweighted(proxy) > _HEAT_MAX_UNWEIGHTED * len(proxy.data.vertices):
            return False
        mesh_obj.vertex_groups.clear()
        for group in proxy.vertex_groups:
            mesh_obj.vertex_groups.new(name=group.name)
        bpy.ops.object.select_all(action='DESELECT')
        mesh_obj.select_set(True)
        proxy.select_set(True)
        context.view_layer.objects.active = proxy          # source = active
        bpy.ops.object.data_transfer(
            data_type='VGROUP_WEIGHTS', vert_mapping='POLYINTERP_NEAREST',
            layers_select_src='ALL', layers_select_dst='NAME',
            use_create=True, mix_mode='REPLACE')
    finally:
        bpy.data.objects.remove(proxy, do_unlink=True)
        if proxy_mesh.users == 0:
            bpy.data.meshes.remove(proxy_mesh)
    _select_pair(context, mesh_obj, armature_obj)
    bpy.ops.object.parent_set(type='ARMATURE')              # parent, keep weights
    return True


def apply_base_weights(context, mesh_obj, armature_obj, validation):
    """Apply initial bone weights using the best available method.

    Attempts methods in order of quality:
        1. ARMATURE_AUTO — bone heat diffusion (best quality)
        2. ARMATURE_ENVELOPE — distance-based (acceptable quality)
        3. Distance fallback — pure Python (always works)

    The validation result guides method selection: if ``can_auto_weight``
    is False, the first method is skipped to avoid a guaranteed failure.

    Args:
        context: Blender context.
        mesh_obj: Target mesh object.
        armature_obj: Source armature object.
        validation: MeshValidationResult from step 1.

    Returns:
        Tuple of (method_name: str, warnings: list[str]).
    """
    warnings = []

    # Method 1: Bone heat diffusion (skip if mesh validation says it will fail)
    if validation.can_auto_weight:
        count = len(mesh_obj.data.vertices)
        try:
            if count > _HEAT_PROXY_VERTS:
                done = _heat_via_proxy(context, mesh_obj, armature_obj)
                method = 'AUTO_PROXY'
            else:
                _select_pair(context, mesh_obj, armature_obj)
                bpy.ops.object.parent_set(type='ARMATURE_AUTO')
                done, method = True, 'AUTO'
            missing = _count_unweighted(mesh_obj) if done else count
            if missing <= _HEAT_MAX_UNWEIGHTED * count:
                if method == 'AUTO_PROXY':
                    warnings.append(
                        f"Dense mesh ({count} vertices): bone heat ran on a "
                        f"{_HEAT_PROXY_TARGET}-vertex copy and was interpolated back")
                return method, warnings
            # Blender reports heat failure only as a console warning and
            # leaves the vertices unweighted; do not call that AUTO
            warnings.append(
                f"Bone heat left {missing} of {count} vertices unweighted; "
                "using bone-segment weights instead")
        except RuntimeError as error:
            warnings.append(
                f"Auto-weights failed ({error}), falling back to segment weights"
            )

    # Method 2: bone-segment distance weights (non-watertight meshes)
    _clear_existing_vertex_groups(mesh_obj)
    if _apply_segment_weights(mesh_obj, armature_obj):
        _select_pair(context, mesh_obj, armature_obj)
        bpy.ops.object.parent_set(type='ARMATURE')     # parent, keep weights
        return 'SEGMENT', warnings

    # Method 3: Envelope weights
    try:
        _clear_existing_vertex_groups(mesh_obj)
        _select_pair(context, mesh_obj, armature_obj)
        bpy.ops.object.parent_set(type='ARMATURE_ENVELOPE')
        return 'ENVELOPE', warnings
    except RuntimeError as error:
        warnings.append(
            f"Envelope weights failed ({error}), falling back to distance-based"
        )

    # Method 3: Distance-based fallback (always works)
    _clear_existing_vertex_groups(mesh_obj)
    _apply_distance_weights(mesh_obj, armature_obj)
    warnings.append(
        "Used distance-based fallback weights — manual touch-up recommended"
    )
    return 'FALLBACK', warnings


# ── Step 3: Face/body weight isolation ───────────────────────

def _compute_face_centroid(session):
    """Compute the centroid of all placed facial markers.

    Returns a world-space Vector, or None if no face markers are placed.
    """
    positions = []
    for i, marker_name in enumerate(FACE_MARKERS):
        marker = get_face_marker(session, marker_name)
        if marker is not None and is_position_placed(marker.position):
            positions.append(Vector(marker.position))

    if not positions:
        return None
    return sum(positions, Vector((0, 0, 0))) / len(positions)


def _compute_face_radius(session, centroid):
    """Compute the face region radius from marker spread.

    The radius is FACE_RADIUS_MULTIPLIER times the maximum distance
    from the centroid to any placed face marker.  This generous boundary
    captures the full facial region including ears and jaw.
    """
    max_dist = 0.0
    for i, marker_name in enumerate(FACE_MARKERS):
        marker = get_face_marker(session, marker_name)
        if marker is not None and is_position_placed(marker.position):
            dist = (Vector(marker.position) - centroid).length
            max_dist = max(max_dist, dist)

    return max_dist * FACE_RADIUS_MULTIPLIER


def _get_face_bone_names(armature_obj):
    """Collect bone names that belong to face collections.

    Scans the armature's BoneCollections for the Face Controls and
    Face Deform collections.  Returns a frozenset of bone names.
    """
    face_names = set()
    armature_data = armature_obj.data

    for coll_name in (FACE_CONTROLS_COLLECTION, FACE_DEFORM_COLLECTION):
        coll = armature_data.collections.get(coll_name)
        if coll is not None:
            for bone in coll.bones:
                face_names.add(bone.name)

    return frozenset(face_names)


def _get_body_bone_names(armature_obj):
    """Collect bone names that are NOT in face collections.

    Any bone that doesn't belong to Face Controls or Face Deform
    is considered a body bone.
    """
    face_names = _get_face_bone_names(armature_obj)
    all_names = {bone.name for bone in armature_obj.data.bones}
    return frozenset(all_names - face_names)


def _find_face_body_border(mesh_obj, face_centroid, face_radius):
    """Identify vertex indices that lie on the face/body boundary.

    A vertex is on the border if it is within a thin shell around
    the face radius.  This set is used by the smoothing step to
    preserve the isolation boundary.

    Returns:
        frozenset of vertex indices on the boundary.
    """
    # SIG-3 fix: skip boundary detection if face_radius is degenerate
    if face_radius < MIN_WEIGHT_EPSILON:
        return frozenset()

    border_margin = face_radius * _FACE_BORDER_MARGIN_RATIO
    inner = max(face_radius - border_margin, 0.0)  # SIG-3 fix: prevent negative
    outer = face_radius + border_margin

    border_indices = set()
    world_matrix = mesh_obj.matrix_world
    for vertex in mesh_obj.data.vertices:
        world_pos = world_matrix @ vertex.co
        dist = (world_pos - face_centroid).length
        if inner <= dist <= outer:
            border_indices.add(vertex.index)

    return frozenset(border_indices)


def apply_jaw_region(mesh_obj, armature_obj, session):
    """Give the lower face to the jaw so opening it opens the mouth.

    Face bones placed on landmarks only claim the vertices nearest them, so
    ``jaw_root`` ended up with a handful of chin vertices and opening it
    barely moved the face. The jaw region is the part of the head below the
    mouth line, in front of the jaw hinge and within the jaw's width; each
    vertex there follows ``jaw_root`` with a weight that fades to zero at the
    mouth line (reaching full strength across the lower lip) and at the
    hinge. Other weights are scaled down to make room.

    Returns:
        int — number of vertices given jaw weight.
    """
    from boneforge.autorig.session import get_face_marker, is_position_placed
    jaw_bone = armature_obj.data.bones.get("jaw_root")
    if jaw_bone is None:
        return 0

    def marker(name):
        m = get_face_marker(session, name)
        if m is None or not is_position_placed(Vector(m.position)):
            return None
        return Vector(m.position)

    upper, lower, chin = marker("UPPER_LIP"), marker("LOWER_LIP"), marker("CHIN")
    eye_l, eye_r = marker("EYE_LEFT"), marker("EYE_RIGHT")
    jaw_l, jaw_r = marker("JAW_LEFT"), marker("JAW_RIGHT")
    if None in (upper, lower, chin, jaw_l, jaw_r):
        return 0
    hinge = armature_obj.matrix_world @ jaw_bone.head_local
    mouth_z = 0.5 * (upper.z + lower.z)
    drop = max(mouth_z - chin.z, 1e-6)
    # The lower lip rides the jaw fully by its marker, tapering like an oval
    # toward the mouth corners (a ramp down to the chin left the lip's sides
    # behind — a V mouth; a full-width lip tore at the corners — a box).
    # Below the lip the pull keeps growing toward the chin as before.
    lip_ramp = max(mouth_z - lower.z, 0.1 * drop)
    mouth_half = (0.38 * abs(eye_l.x - eye_r.x)) if eye_l is not None and eye_r is not None \
        else 0.35 * abs(jaw_l.x - jaw_r.x)
    bottom_z = chin.z - 0.6 * drop
    half_w = 0.5 * abs(jaw_l.x - jaw_r.x) * 1.15
    cx = 0.5 * (jaw_l.x + jaw_r.x)
    ahead = chin.y - hinge.y
    sign = 1.0 if ahead >= 0 else -1.0
    depth = max(abs(ahead), 1e-6)

    jaw_group = mesh_obj.vertex_groups.get("jaw_root") or mesh_obj.vertex_groups.new(name="jaw_root")
    names = {g.index: g for g in mesh_obj.vertex_groups}
    world = mesh_obj.matrix_world
    changed = 0
    for v in mesh_obj.data.vertices:
        p = world @ v.co
        if not (bottom_z < p.z < mouth_z) or abs(p.x - cx) > half_w:
            continue
        forward = (p.y - hinge.y) * sign
        if forward <= 0.0:
            continue
        across = abs(p.x - lower.x) / max(mouth_half, 1e-6)
        oval = (1.0 - across * across) ** 0.5 if across < 1.0 else 0.0
        w_mouth = max(min(1.0, (mouth_z - p.z) / lip_ramp) * oval,
                      min(1.0, (mouth_z - p.z) / drop))
        w_hinge = min(1.0, forward / depth) ** 0.5
        w_side = min(1.0, (half_w - abs(p.x - cx)) / (0.3 * half_w))
        w = max(0.0, w_mouth * w_hinge * w_side)
        if w <= 0.01:
            continue
        existing_jaw = 0.0
        for vge in v.groups:
            if vge.group == jaw_group.index:
                existing_jaw = vge.weight
        for vge in list(v.groups):
            if vge.group != jaw_group.index and vge.weight > 0.0:
                names[vge.group].add([v.index], vge.weight * (1.0 - w), 'REPLACE')
        jaw_group.add([v.index], w + existing_jaw * (1.0 - w), 'REPLACE')
        changed += 1
    return changed


def isolate_face_weights(mesh_obj, armature_obj, session):
    """Zero out cross-region bone influences between face and body.

    Determines the face/body vertex boundary using proximity to the
    face marker centroid.  Vertices within the face radius are assigned
    exclusively to face bones; vertices outside are assigned exclusively
    to body bones.

    This prevents artifacts like the jaw bone pulling on chest vertices
    or the spine bone distorting the face during animation.

    Args:
        mesh_obj: Target mesh object with vertex groups.
        armature_obj: Armature with face/body bone collections.
        session: AutoRig session with face marker data.

    Returns:
        Tuple of (applied: bool, face_body_border: frozenset, warnings: list).
    """
    warnings = []

    face_centroid = _compute_face_centroid(session)
    if face_centroid is None:
        warnings.append("No face markers placed — skipping face isolation")
        return False, frozenset(), warnings

    face_radius = _compute_face_radius(session, face_centroid)
    if face_radius < MIN_WEIGHT_EPSILON:
        warnings.append("Face markers too close together — skipping face isolation")
        return False, frozenset(), warnings

    face_bone_names = _get_face_bone_names(armature_obj)
    body_bone_names = _get_body_bone_names(armature_obj)
    # The bones the face hangs from (head, neck ...) stay allowed inside the
    # face region: zeroing them handed the scalp and back of the skull to the
    # face bones, so opening the jaw or turning an eye moved the crown.
    face_parents = set()
    for name in face_bone_names:
        bone = armature_obj.data.bones.get(name)
        parent = bone.parent if bone is not None else None
        while parent is not None:
            if parent.name not in face_bone_names:
                face_parents.add(parent.name)
            parent = parent.parent
    body_bone_names = frozenset(body_bone_names - face_parents)

    if not face_bone_names:
        warnings.append("No face bone collections found — skipping face isolation")
        return False, frozenset(), warnings

    # Perf (8.9.x): one table read, numpy masks, write only changed vertices.
    import numpy as np
    points = _world_coords_np(mesh_obj)
    centre = np.array(tuple(face_centroid), dtype=np.float64)
    in_face = np.sqrt(((points - centre) ** 2).sum(axis=1)) < face_radius
    body_index = [g.index for g in mesh_obj.vertex_groups if g.name in body_bone_names]
    face_index = [g.index for g in mesh_obj.vertex_groups if g.name in face_bone_names]
    vi, gi, w = _weight_table(mesh_obj)
    zero = ((in_face[vi] & np.isin(gi, body_index))
            | (~in_face[vi] & np.isin(gi, face_index)))
    _write_weight_table(mesh_obj, np.where(zero, 0.0, w), vi, w)

    border = _find_face_body_border(mesh_obj, face_centroid, face_radius)
    return True, border, warnings


# ── Step 4: Laplacian weight smoothing ───────────────────────

def _weight_table(mesh_obj):
    """All vertex-group weights as flat numpy arrays, in element order.

    Returns ``(vertex, group, weight)``: one entry per vertex-group element,
    visited vertex by vertex. :func:`_write_weight_table` writes a same-length
    array back in the same order, so a pass that keeps every vertex's group
    membership (smoothing, normalising) costs one read and one write however
    many bones there are.
    """
    import numpy as np
    rows = [(v.index, ge.group, ge.weight)
            for v in mesh_obj.data.vertices for ge in v.groups]
    if not rows:
        empty = np.zeros(0, dtype=np.int64)
        return empty, empty.copy(), np.zeros(0, dtype=np.float64)
    table = np.array(rows, dtype=np.float64)
    return table[:, 0].astype(np.int64), table[:, 1].astype(np.int64), table[:, 2]


def _write_weight_table(mesh_obj, weights, vertex=None, old=None):
    """Write weights back in the element order of :func:`_weight_table`.

    With the table's ``vertex`` column and the ``old`` weights, only the
    vertices whose weights changed are visited.
    """
    import numpy as np
    vertices = mesh_obj.data.vertices
    if vertex is None or old is None:
        values = iter(weights.tolist())
        for v in vertices:
            for vertex_group_element in v.groups:
                vertex_group_element.weight = next(values)
        return
    changed = np.nonzero(_as_stored(weights) != _as_stored(old))[0]
    if not len(changed):
        return
    starts = np.searchsorted(vertex, np.arange(len(vertices)))
    values = weights.tolist()
    for vi in np.unique(vertex[changed]).tolist():
        k = int(starts[vi])
        for vertex_group_element in vertices[vi].groups:
            vertex_group_element.weight = values[k]
            k += 1


def _as_stored(weights):
    """Round to the float32 precision vertex groups store."""
    import numpy as np
    return weights.astype(np.float32).astype(np.float64)


def _edge_array(mesh_obj):
    import numpy as np
    edges = np.empty(len(mesh_obj.data.edges) * 2, dtype=np.int64)
    mesh_obj.data.edges.foreach_get("vertices", edges)
    return edges.reshape(-1, 2)


def smooth_weights(mesh_obj, iterations, face_body_border):
    """Laplacian smoothing of vertex weights.

    For each vertex, replaces its weight with the average of its
    connected neighbors' weights.  Repeated over multiple iterations,
    this produces smooth weight gradients across the mesh surface.

    The face_body_border frozenset defines a hard boundary where
    smoothing does NOT cross.  This preserves the face/body
    isolation from step 3.

    Args:
        mesh_obj: Target mesh object with vertex groups.
        iterations: Number of smoothing passes (0 = skip).
        face_body_border: frozenset of border vertex indices.
    """
    if iterations <= 0:
        return
    import numpy as np

    # Perf (8.9.x): numpy over the edge list. Same Laplacian as before:
    # members of a group move toward the mean over *all* their neighbours
    # (non-members count as 0), edges across the face/body border are cut,
    # and a vertex with no neighbours keeps its weight.
    vi, gi, w = _weight_table(mesh_obj)
    if not len(w):
        return
    count = len(mesh_obj.data.vertices)
    edges = _edge_array(mesh_obj)
    if face_body_border and len(edges):
        in_border = np.zeros(count, dtype=bool)
        in_border[list(face_body_border)] = True
        edges = edges[in_border[edges[:, 0]] == in_border[edges[:, 1]]]
    a, b = edges[:, 0], edges[:, 1]
    degree = np.bincount(a, minlength=count) + np.bincount(b, minlength=count)
    members = {int(g): np.nonzero(gi == g)[0] for g in np.unique(gi)}
    w = _as_stored(w)
    for _pass in range(iterations):
        new = w.copy()
        for rows in members.values():
            verts = vi[rows]
            field = np.zeros(count, dtype=np.float64)
            field[verts] = w[rows]
            neighbour_sum = (np.bincount(a, weights=field[b], minlength=count)
                             + np.bincount(b, weights=field[a], minlength=count))
            deg = degree[verts]
            has = deg > 0
            smoothed = w[rows].copy()
            smoothed[has] = (w[rows][has] * _LAPLACIAN_SELF_WEIGHT
                             + neighbour_sum[verts][has] / deg[has]
                             * (1.0 - _LAPLACIAN_SELF_WEIGHT))
            new[rows] = smoothed
        w = _as_stored(new)
    _write_weight_table(mesh_obj, w)


# ── Step 4b: Weight sharpening ───────────────────────────────

def sharpen_weights(mesh_obj, power):
    """Raise every non-trivial vertex weight to *power*.

    The subsequent :func:`normalize_weights` pass divides each vertex's
    weights by their sum, so pre-scaling by a power curve concentrates
    influence onto the dominant bone(s) without changing which bones
    touch a vertex. Passing ``power <= 1.0`` is a no-op.

    Args:
        mesh_obj: Target mesh object.
        power: Exponent applied to each weight. ``2.0`` produces a
            visibly crisper result than the blurry Blender
            ARMATURE_AUTO default.
    """
    if power <= 1.0:
        return

    # Perf (v3.0.11): mutate VertexGroupElement.weight in place rather
    # than routing every update through vertex_groups[i].add(). The add()
    # path costs one PyAPI round trip per (vertex × influence) — on a
    # 40 k-vert humanoid with 4 influences that's 160 000 calls. Direct
    # assignment on the existing element is ~10× faster and is stable
    # in the Blender API because we're not changing which group a
    # vertex belongs to, only the existing weight value.
    for vertex in mesh_obj.data.vertices:
        for vertex_group_element in vertex.groups:
            weight = vertex_group_element.weight
            if weight > MIN_WEIGHT_EPSILON:
                vertex_group_element.weight = weight ** power


# ── Step 5: Weight normalization ─────────────────────────────

def normalize_weights(mesh_obj, armature_obj, max_influences, sharpen_power=1.0):
    """Normalize vertex weights and limit influence count.

    Two passes per vertex:
        1. Keep only the top N bones by weight, zero the rest.
        2. Scale remaining weights so they sum to exactly 1.0.

    Vertices with zero total weight after normalization are assigned
    to their nearest bone with weight 1.0 as a safety fallback.

    ``sharpen_power`` > 1 first applies :func:`sharpen_weights` in the same
    pass (one read and one write of the weights instead of two).

    Args:
        mesh_obj: Target mesh object.
        armature_obj: Armature (for nearest-bone fallback).
        max_influences: Maximum bone influences per vertex.

    Returns:
        Number of vertices that required nearest-bone fallback.
    """
    import numpy as np
    count = len(mesh_obj.data.vertices)
    # Perf (8.9.x): one read, numpy, one in-place write. Per vertex: the
    # top ``max_influences`` weights above epsilon (ties keep element order)
    # are scaled to sum 1, every other weight is zeroed; a vertex with
    # nothing above epsilon is left as is and rescued to its nearest bone.
    vi, gi, w = _weight_table(mesh_obj)
    read = w
    if sharpen_power > 1.0:
        w = np.where(w > MIN_WEIGHT_EPSILON, _as_stored(w ** sharpen_power), w)
    active = w > MIN_WEIGHT_EPSILON
    weighted = np.zeros(count, dtype=bool)
    weighted[vi[active]] = True
    if len(w):
        order = np.lexsort((np.arange(len(w)), -w, vi))
        order = order[active[order]]
        run_vertex = vi[order]
        starts = np.r_[0, np.nonzero(np.diff(run_vertex))[0] + 1]
        run_start = np.zeros(len(order), dtype=np.int64)
        run_start[starts] = starts
        rank = np.arange(len(order)) - np.maximum.accumulate(run_start)
        kept = order[rank < max_influences]
        total = np.bincount(vi[kept], weights=w[kept], minlength=count)
        new = np.where(weighted[vi], 0.0, w)
        new[kept] = w[kept] * (1.0 / total[vi[kept]])
        _write_weight_table(mesh_obj, new, vi, read)

    rescue = np.nonzero(~weighted)[0]
    if len(rescue):
        names = [bone.name for bone in armature_obj.data.bones]
        centers = np.array([tuple(_bone_world_center(armature_obj, bone))
                            for bone in armature_obj.data.bones], dtype=np.float64)
        points = _world_coords_np(mesh_obj)[rescue]
        nearest = np.zeros(len(rescue), dtype=np.int64)
        for start in range(0, len(rescue) if len(centers) else 0, 20000):  # bounded memory
            chunk = points[start:start + 20000]
            nearest[start:start + 20000] = np.argmin(
                ((chunk[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2), axis=1)
        for bone_index in np.unique(nearest):
            group = (mesh_obj.vertex_groups.get(names[bone_index])
                     or mesh_obj.vertex_groups.new(name=names[bone_index]))
            group.add(rescue[nearest == bone_index].tolist(), 1.0, 'REPLACE')
    return int(len(rescue))


# ── Step 6: Corrective presets ───────────────────────────────

def _find_joint_vertices(mesh_obj, armature_obj, bone_name_a, bone_name_b, blend_width):
    """Find vertices near the joint between two bones.

    The joint position is the shared head/tail point between the two
    bones.  Vertices within *blend_width* world units of the joint
    are returned.

    Returns:
        list of (vertex_index, distance_to_joint) tuples.
    """
    arm_data = armature_obj.data
    bone_a = arm_data.bones.get(bone_name_a)
    bone_b = arm_data.bones.get(bone_name_b)

    if bone_a is None or bone_b is None:
        return []

    # Find the shared joint — could be bone_a.tail == bone_b.head
    world = armature_obj.matrix_world
    joint_candidates = [
        world @ bone_a.head_local,
        world @ bone_a.tail_local,
        world @ bone_b.head_local,
        world @ bone_b.tail_local,
    ]

    # The joint is the point where two endpoints are closest
    best_joint = None
    best_dist = float('inf')
    for i in range(len(joint_candidates)):
        for j in range(i + 1, len(joint_candidates)):
            dist = (joint_candidates[i] - joint_candidates[j]).length
            if dist < best_dist:
                best_dist = dist
                best_joint = (joint_candidates[i] + joint_candidates[j]) * 0.5

    if best_joint is None:
        return []

    # Find vertices within blend_width of the joint
    mesh_world = mesh_obj.matrix_world
    result = []
    for vertex in mesh_obj.data.vertices:
        world_pos = mesh_world @ vertex.co
        dist = (world_pos - best_joint).length
        if dist <= blend_width:
            result.append((vertex.index, dist))

    return result


# Preset widths/margins are authored for a ~1.75 m human; rigs of any other
# size scale them by their own height.
_PRESET_REFERENCE_HEIGHT = 1.75


def _bone_side(name):
    """'L', 'R' or '' from a bone name (``foo.L`` / ``foo-L`` / ``foo_L``)."""
    for sep in (".", "-", "_"):
        for side in ("L", "R"):
            if name.endswith(sep + side):
                return side
    return ""


def _rig_scale(armature_obj):
    """Rig height relative to the preset reference height (>= a small floor)."""
    zs = []
    world = armature_obj.matrix_world
    for bone in armature_obj.data.bones:
        if bone.use_deform:
            zs.append((world @ bone.head_local).z)
            zs.append((world @ bone.tail_local).z)
    if len(zs) < 2:
        return 1.0
    return max((max(zs) - min(zs)) / _PRESET_REFERENCE_HEIGHT, 0.05)


def _joint_pairs(armature_obj, names):
    """Pairs of listed bones that really meet at a joint on the same side.

    The preset lists name bones, not joints: pairing list neighbours made
    ``forearm.L`` blend with ``forearm.R`` (a "joint" across the body) and
    leaked one arm's weight into the other. Only same-side bones whose
    endpoints touch form a joint.
    """
    bones = armature_obj.data.bones
    present = [n for n in names if bones.get(n) is not None]
    pairs = []
    for i, a in enumerate(present):
        for b in present[i + 1:]:
            if _bone_side(a) != _bone_side(b):
                continue
            ba, bb = bones[a], bones[b]
            ends_a = (ba.head_local, ba.tail_local)
            ends_b = (bb.head_local, bb.tail_local)
            gap = min((p - q).length for p in ends_a for q in ends_b)
            scale = max(min(ba.length, bb.length), 1e-6)
            if gap <= 0.05 * scale:
                pairs.append((a, b))
    return pairs


def _apply_gradient_blend(mesh_obj, armature_obj, preset):
    """Apply gradient_blend corrective: smooth weight transition at a joint.

    Blends the weights of affected bones for vertices near the joint,
    using a distance-based falloff curve.  Only modifies vertices
    whose current weight distribution is sharp (delta > 0.3).
    """
    affected_bones = preset['affected_bones']
    blend_width = preset['parameters']['blend_width'] * _rig_scale(armature_obj)
    falloff = preset['parameters']['falloff']

    for bone_a, bone_b in _joint_pairs(armature_obj, affected_bones):

        joint_verts = _find_joint_vertices(
            mesh_obj, armature_obj, bone_a, bone_b, blend_width,
        )

        group_a = mesh_obj.vertex_groups.get(bone_a)
        group_b = mesh_obj.vertex_groups.get(bone_b)
        if group_a is None or group_b is None:
            continue

        for vertex_index, distance in joint_verts:
            # Compute blend factor based on distance and falloff
            normalized_dist = distance / max(blend_width, MIN_WEIGHT_EPSILON)

            if falloff == 'SMOOTH':
                # Smooth hermite interpolation
                blend_factor = normalized_dist * normalized_dist * (3 - 2 * normalized_dist)
            else:
                # Sharp linear falloff
                blend_factor = normalized_dist

            # Read current weights
            vertex = mesh_obj.data.vertices[vertex_index]
            weight_a = 0.0
            weight_b = 0.0
            for vge in vertex.groups:
                if vge.group == group_a.index:
                    weight_a = vge.weight
                elif vge.group == group_b.index:
                    weight_b = vge.weight

            # Only correct if there's a sharp discontinuity
            delta = abs(weight_a - weight_b)
            if delta < WEIGHT_DISCONTINUITY_THRESHOLD:
                continue

            # Blend toward more even distribution at the joint center
            total = weight_a + weight_b
            if total <= 0:
                continue

            target_a = total * (1.0 - blend_factor * 0.5)
            target_b = total * blend_factor * 0.5

            # Conservative: blend toward target to avoid over-correction
            _keep = 1.0 - _BORDER_REBALANCE_FACTOR
            new_a = weight_a * _keep + target_a * _BORDER_REBALANCE_FACTOR
            new_b = weight_b * _keep + target_b * _BORDER_REBALANCE_FACTOR

            group_a.add([vertex_index], new_a, 'REPLACE')
            group_b.add([vertex_index], new_b, 'REPLACE')


def _apply_midplane_clip(mesh_obj, armature_obj, preset):
    """Apply midplane_clip corrective: zero cross-side bone influence.

    Prevents one leg's bones from affecting the opposite leg's vertices.
    (The preset's ``clip_axis`` / ``blend_margin`` are no longer needed:
    sides are decided by bone proximity.)
    """
    affected_bones = preset['affected_bones']
    # Side by proximity, not by a midline: each vertex belongs to the side
    # whose listed bones are clearly nearer. This holds for legs that almost
    # touch (a midline margin would leave their inner surfaces unprotected)
    # and for characters that do not stand at the world origin.
    world = armature_obj.matrix_world
    segs = {"L": [], "R": []}
    for bone_name in affected_bones:
        side = _bone_side(bone_name)
        bone = armature_obj.data.bones.get(bone_name)
        group = mesh_obj.vertex_groups.get(bone_name)
        if side in segs and bone is not None and group is not None:
            segs[side].append((group, world @ bone.head_local, world @ bone.tail_local))
    if not segs["L"] or not segs["R"]:
        return

    import numpy as np
    points = _world_coords_np(mesh_obj)
    d_l = _segment_distances_np(points, [(h, t) for _g, h, t in segs["L"]]).min(axis=1)
    d_r = _segment_distances_np(points, [(h, t) for _g, h, t in segs["R"]]).min(axis=1)
    # a vertex clearly nearer one side loses the other side's bones;
    # genuinely between the legs (within 10%) it is left alone
    for side, mask in (("R", d_l < 0.9 * d_r), ("L", d_r < 0.9 * d_l)):
        indices = np.nonzero(mask)[0].tolist()
        if indices:
            for group, _h, _t in segs[side]:
                group.add(indices, 0.0, 'REPLACE')


def apply_corrective_presets(mesh_obj, armature_obj):
    """Apply all corrective presets from constants.py.

    Each preset defines a correction method and affected bones.
    Methods are dispatched via a lookup table.

    Conservative approach: each corrective only modifies vertices
    where the current weights show known problem patterns.

    Args:
        mesh_obj: Target mesh with vertex groups.
        armature_obj: Armature with posed bones.

    Returns:
        Number of presets successfully applied.
    """
    method_dispatch = {
        'gradient_blend': _apply_gradient_blend,
        'angle_split': _apply_gradient_blend,  # Reuse gradient as conservative fallback
        'midplane_clip': _apply_midplane_clip,
    }

    applied_count = 0
    for preset_name, preset in CORRECTIVE_PRESETS.items():
        method_name = preset['method']
        handler = method_dispatch.get(method_name)
        if handler is None:
            continue

        try:
            handler(mesh_obj, armature_obj, preset)
            applied_count += 1
        except KeyError as error:
            # SIG-6 fix: separate handler for configuration errors
            logger.info(f"[BoneCraft] Corrective preset '{preset_name}' "
                  f"missing required key: {error}")
        except (AttributeError, TypeError) as error:
            # SIG-6 fix: separate handler for rig compatibility issues
            logger.warning(f"[BoneCraft] Corrective preset '{preset_name}' "
                  f"incompatible with current rig: {error}")

    return applied_count


# ── Step 7: Quality scoring ──────────────────────────────────

# How far each base-weight method can be trusted before any other evidence:
# heat diffusion follows the surface; the others only see distances.
_METHOD_CONFIDENCE = {'AUTO': 1.0, 'AUTO_PROXY': 0.95, 'SEGMENT': 0.8, 'ENVELOPE': 0.7,
                      'FALLBACK': 0.5}


def score_weight_quality(mesh_obj, armature_obj, max_influences, method=None,
                         validation=None, rescued_vertices=0):
    """Score the overall skinning quality.

    Evaluates three dimensions:
        1. Coverage — percentage of vertices with non-zero weights
        2. Smoothness — average weight delta between adjacent vertices
        3. Influence budget — percentage of vertices within max_influences

    The overall score is the geometric mean of the three sub-scores,
    scaled to 0.0–1.0.

    Args:
        mesh_obj: Target mesh with completed vertex groups.
        armature_obj: Armature for bone reference.
        max_influences: Maximum intended influences per vertex.

    Returns:
        SkinningQualityReport.
    """
    mesh_data = mesh_obj.data
    vertex_count = len(mesh_data.vertices)

    if vertex_count == 0:
        return SkinningQualityReport(overall_score=1.0)

    import numpy as np
    # Perf (8.9.x): every sub-score from one weight table and the edge list.
    vi, gi, w = _weight_table(mesh_obj)
    elements = np.arange(len(w))

    # Sub-score 1: Coverage
    total = np.bincount(vi, weights=w, minlength=vertex_count)
    unweighted = int((total < MIN_WEIGHT_EPSILON).sum())
    coverage_score = 1.0 - (unweighted / vertex_count)

    # Sub-score 2: Smoothness — dominant bone per vertex (first strict max
    # above zero, as before), compared across every edge
    dom_group = np.full(vertex_count, -1, dtype=np.int64)
    dom_weight = np.zeros(vertex_count, dtype=np.float64)
    if len(w):
        order = np.lexsort((elements, -w, vi))
        first = np.r_[0, np.nonzero(np.diff(vi[order]))[0] + 1]
        top = order[first]
        top = top[w[top] > 0.0]
        dom_group[vi[top]] = gi[top]
        dom_weight[vi[top]] = w[top]
    edges = _edge_array(mesh_obj)
    edge_count_checked = len(edges)
    if edge_count_checked:
        ga, gb = dom_group[edges[:, 0]], dom_group[edges[:, 1]]
        delta = np.abs(dom_weight[edges[:, 0]] - dom_weight[edges[:, 1]])
        discontinuity_count = int(((ga != gb) & (delta > WEIGHT_DISCONTINUITY_THRESHOLD)).sum())
    else:
        discontinuity_count = 0

    if edge_count_checked > 0:
        smoothness_score = 1.0 - min(
            discontinuity_count / edge_count_checked, 1.0
        )
    else:
        smoothness_score = 1.0

    # Sub-score 3: Influence budget compliance
    active = w > MIN_WEIGHT_EPSILON
    influences = np.bincount(vi[active], minlength=vertex_count)
    influence_violations = int((influences > max_influences).sum())

    budget_score = 1.0 - (influence_violations / vertex_count)

    # Geometric mean of sub-scores
    product = coverage_score * smoothness_score * budget_score
    overall_score = max(product ** (1.0 / 3.0), 0.0)

    # Honesty factors (v8.6.7): the three sub-scores above are ~1.0 for any
    # result, so on their own they called an envelope-fallback bind "perfect".
    # Scale by what is actually known to limit quality.
    notes = []
    method_factor = _METHOD_CONFIDENCE.get(method, 1.0) if method else 1.0
    if method == 'AUTO_PROXY':
        notes.append("base weights by bone heat on a decimated copy (dense mesh), interpolated back")
    elif method and method_factor < 1.0:
        notes.append(f"base weights by {method} (mesh not suitable for surface diffusion)")
    geometry_factor = 1.0
    if validation is not None and len(mesh_data.edges):
        bad_share = validation.non_manifold_count / len(mesh_data.edges)
        geometry_factor = max(0.5, 1.0 - 0.5 * bad_share)
    rescue_factor = max(0.5, 1.0 - 2.0 * rescued_vertices / vertex_count)
    if rescued_vertices:
        notes.append(f"{rescued_vertices} vertices had no weight and were rescued")
    groups_by_index = {g.index: g.name for g in mesh_obj.vertex_groups}
    # limb bones only: on the face, left and right bones (brows, cheeks,
    # lids) rightly share the vertices along the midline
    limb_side = {}
    for index, name in groups_by_index.items():
        side = _bone_side(name)
        if side and (_bone_kind(name) != "torso" and _bone_kind(name) not in ("neck", "head")
                     or name.replace("DEF-", "").startswith(_LIMB_ROOT_PREFIXES)):
            limb_side[index] = side
    pulled = w > 0.02
    left = np.zeros(vertex_count, dtype=bool)
    right = np.zeros(vertex_count, dtype=bool)
    for index, side in limb_side.items():
        rows = pulled & (gi == index)
        (left if side == "L" else right)[vi[rows]] = True
    both_sides = int((left & right).sum())
    side_share = both_sides / vertex_count
    side_factor = max(0.3, 1.0 - 10.0 * side_share)
    if both_sides:
        notes.append(f"{both_sides} vertices pulled by both left and right limbs")
    overall_score *= method_factor * geometry_factor * rescue_factor * side_factor

    # v3.1.6 (M-6): invert the scoring loop. The previous version
    # iterated every vertex inside every group (O(V * G)); here we walk
    # vertices once and bucket by their assigned groups.
    bone_lookup = armature_obj.data.bones
    counts = np.bincount(gi[active], minlength=len(mesh_obj.vertex_groups))
    per_bone_counts = {g: int(c) for g, c in enumerate(counts.tolist()) if c}

    per_bone_scores = {}
    for group in mesh_obj.vertex_groups:
        if bone_lookup.get(group.name) is None:
            continue
        per_bone_scores[group.name] = (
            per_bone_counts.get(group.index, 0) / max(vertex_count, 1)
        )

    # Flagged regions
    flagged = list(notes)
    if unweighted > 0:
        flagged.append(f"{unweighted} unweighted vertices need manual assignment")
    if discontinuity_count > _DISCONTINUITY_SEVERITY_THRESHOLD:
        flagged.append(
            f"{discontinuity_count} weight discontinuities may cause "
            "visible seams during animation"
        )
    if influence_violations > 0:
        flagged.append(
            f"{influence_violations} vertices exceed the {max_influences} "
            "influence budget"
        )

    return SkinningQualityReport(
        overall_score=round(overall_score, 4),
        per_bone_scores=per_bone_scores,
        unweighted_vertices=unweighted,
        discontinuity_count=discontinuity_count,
        max_influence_violations=influence_violations,
        flagged_regions=flagged,
    )


# ── Step 2b: Island rigidification (stylized humanoid fix) ───

def _find_mesh_islands(mesh_obj):
    """Partition mesh vertices into connected-component islands.

    Two vertices are in the same island iff there is a path of shared
    edges between them.  Uses union-find over edges for O(E α(V)) time.

    Returns:
        list[list[int]] — each inner list is the vertex indices of one
        island, in no particular order.  Empty if mesh has no verts.
    """
    vertex_count = len(mesh_obj.data.vertices)
    if vertex_count == 0:
        return []

    parent = list(range(vertex_count))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for edge in mesh_obj.data.edges:
        v0, v1 = edge.vertices
        union(v0, v1)

    islands = {}
    for vertex_index in range(vertex_count):
        root = find(vertex_index)
        islands.setdefault(root, []).append(vertex_index)

    return list(islands.values())


def _island_bbox_diagonal(mesh_obj, vertex_indices, world_matrix):
    """Return the world-space bounding-box diagonal length of an island."""
    if not vertex_indices:
        return 0.0
    vertices = mesh_obj.data.vertices
    first = world_matrix @ vertices[vertex_indices[0]].co
    min_x = max_x = first.x
    min_y = max_y = first.y
    min_z = max_z = first.z
    for vertex_index in vertex_indices[1:]:
        world_co = world_matrix @ vertices[vertex_index].co
        if world_co.x < min_x:
            min_x = world_co.x
        elif world_co.x > max_x:
            max_x = world_co.x
        if world_co.y < min_y:
            min_y = world_co.y
        elif world_co.y > max_y:
            max_y = world_co.y
        if world_co.z < min_z:
            min_z = world_co.z
        elif world_co.z > max_z:
            max_z = world_co.z
    dx = max_x - min_x
    dy = max_y - min_y
    dz = max_z - min_z
    return (dx * dx + dy * dy + dz * dz) ** 0.5


def _island_centroid(mesh_obj, vertex_indices, world_matrix):
    """World-space centroid (arithmetic mean of vertex positions)."""
    total = Vector((0.0, 0.0, 0.0))
    vertices = mesh_obj.data.vertices
    for vertex_index in vertex_indices:
        total += world_matrix @ vertices[vertex_index].co
    return total / max(len(vertex_indices), 1)


def _nearest_deform_bone(world_point, bone_centers):
    """Return the name of the closest bone to *world_point*, or None."""
    nearest_name = None
    nearest_dist = float('inf')
    for bone_name, center in bone_centers.items():
        distance = (world_point - center).length
        if distance < nearest_dist:
            nearest_dist = distance
            nearest_name = bone_name
    return nearest_name


_PROTRUDE_MEMBER_RATIO: float = 2.0    # piece joins an accessory assembly
_PROTRUDE_ASSEMBLY_RATIO: float = 3.0  # assembly must reach this far out
_PROTRUDE_ATTACH_SHARE: float = 0.05   # assembly verts closest to the body


def _world_coords_np(mesh_obj):
    """World-space vertex positions as an (N, 3) numpy array (one C call)."""
    import numpy as np
    n = len(mesh_obj.data.vertices)
    co = np.empty(n * 3, dtype=np.float64)
    mesh_obj.data.vertices.foreach_get("co", co)
    co = co.reshape(n, 3)
    m = np.array(mesh_obj.matrix_world, dtype=np.float64)
    return co @ m[:3, :3].T + m[:3, 3]


def _segment_distances_np(points, segments):
    """Distance from every point to every segment: (N, S) numpy array.

    ``segments`` is a list of (head, tail) 3-vectors; ``points`` an (N, 3)
    array. Same clamped-projection formula as the per-vertex Python loops.
    """
    import numpy as np
    heads = np.array([tuple(h) for h, _t in segments], dtype=np.float64)
    dirs = np.array([tuple(t) for _h, t in segments], dtype=np.float64) - heads
    dd = np.maximum((dirs * dirs).sum(axis=1), 1e-12)
    out = np.empty((len(points), len(segments)), dtype=np.float64)
    for j in range(len(segments)):
        rel = points - heads[j]
        u = np.clip(rel @ dirs[j] / dd[j], 0.0, 1.0)
        diff = rel - u[:, None] * dirs[j]
        out[:, j] = np.sqrt((diff * diff).sum(axis=1))
    return out


def pin_protruding_islands(mesh_obj, armature_obj, islands=None):
    """Rigidly attach accessories that stick out of the body to their anchor.

    A robot arm on the back, wings, a tail: the base pass weights such a part
    to whatever limb runs alongside it, so it swings with that limb. Distance
    is measured against the *skeleton*: a mesh piece whose vertices sit, on
    median, more than ``_PROTRUDE_MEMBER_RATIO`` times farther from the bones
    than skin typically does is a candidate; touching candidates form one
    assembly; an assembly that somewhere reaches ``_PROTRUDE_ASSEMBLY_RATIO``
    is an accessory. It then follows, rigidly, the bone that owns the body
    surface it touches (read from the body's own weights there).

    Clothing that wraps the body and hats/hair that hug the head stay under
    the ratios and keep their normal weights.

    Returns:
        int — number of assemblies pinned.
    """
    import statistics
    from mathutils.kdtree import KDTree

    if islands is None:
        islands = _find_mesh_islands(mesh_obj)
    if len(islands) < 2:
        return 0
    world_m = armature_obj.matrix_world
    segs = [(world_m @ bone.head_local, world_m @ bone.tail_local)
            for bone in armature_obj.data.bones if bone.use_deform]
    if not segs:
        return 0
    mw = mesh_obj.matrix_world
    verts = mesh_obj.data.vertices
    pos = [mw @ v.co for v in verts]
    dist = _segment_distances_np(_world_coords_np(mesh_obj), segs).min(axis=1).tolist()
    typical = statistics.median(dist) or 1e-6

    candidates = []
    ratio = {}
    for idx, island in enumerate(islands):
        med = statistics.median(dist[vi] for vi in island) / typical
        if med > _PROTRUDE_MEMBER_RATIO:
            candidates.append(idx)
            ratio[idx] = med
    if not candidates:
        return 0

    # group touching candidate pieces into assemblies (voxel adjacency)
    cell = max(_rig_scale(armature_obj) * _PRESET_REFERENCE_HEIGHT * 0.03, 1e-6)
    owner = {}
    parent = {i: i for i in candidates}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for idx in candidates:
        keys = {(int(pos[vi].x // cell), int(pos[vi].y // cell), int(pos[vi].z // cell))
                for vi in islands[idx]}
        for k in keys:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        other = owner.get((k[0] + dx, k[1] + dy, k[2] + dz))
                        if other is not None and find(other) != find(idx):
                            parent[find(other)] = find(idx)
        for k in keys:
            owner.setdefault(k, idx)
    assemblies = {}
    for idx in candidates:
        assemblies.setdefault(find(idx), []).append(idx)

    in_candidate = {vi for idx in candidates for vi in islands[idx]}
    surface = [vi for vi in range(len(verts)) if vi not in in_candidate]
    if not surface:
        return 0
    tree = KDTree(len(surface))
    for vi in surface:
        tree.insert(pos[vi], vi)
    tree.balance()
    names = {g.index: g.name for g in mesh_obj.vertex_groups}
    deform = {b.name for b in armature_obj.data.bones if b.use_deform}

    pinned = 0
    for members in assemblies.values():
        if max(ratio[i] for i in members) <= _PROTRUDE_ASSEMBLY_RATIO:
            continue
        part = [vi for i in members for vi in islands[i]]
        touch = sorted((hit[2], hit[1]) for hit in (tree.find(pos[vi]) for vi in part))
        anchor = touch[:max(1, int(len(touch) * _PROTRUDE_ATTACH_SHARE))]
        votes = {}
        for _d, body_vi in anchor:
            for vge in verts[body_vi].groups:
                name = names.get(vge.group)
                if name in deform and vge.weight > 0.0:
                    votes[name] = votes.get(name, 0.0) + vge.weight
        if not votes:
            continue
        target = max(votes.items(), key=lambda kv: kv[1])[0]
        touching = {vge.group for vi in part for vge in verts[vi].groups}
        for gi in touching:
            if names.get(gi) != target:
                mesh_obj.vertex_groups[gi].remove(part)
        mesh_obj.vertex_groups[target].add(part, 1.0, 'REPLACE')
        pinned += 1
    return pinned


# sided bones that belong to a limb although their kind reads as torso
_LIMB_ROOT_PREFIXES = ("shoulder", "clavicle", "thumb", "index", "middle", "ring",
                       "pinky", "f_", "finger")


def shoulder_seam_share(along, radius):
    """Arm share of a shoulder vertex by its position along the arm (pure).

    ``along`` is the signed distance from the shoulder joint along the upper
    arm (negative = toward the body). The share rises smoothly from 0 at 0.3
    of the radius inside the joint to 1 at 0.8 of it down the arm, so the
    skin across the joint blends like a deltoid (a narrower band crumpled the
    shoulder cap when the arm lowered).
    """
    t = along / max(radius, 1e-9)
    if t <= -0.3:
        return 0.0
    if t >= 0.8:
        return 1.0
    x = (t + 0.3) / 1.1
    return x * x * (3.0 - 2.0 * x)


def blend_shoulder_seams(mesh_obj, armature_obj):
    """Blend skin across each shoulder joint between the upper arm and the
    torso bones it meets (shoulder / clavicle / chest).

    A sleeve bound to the arm and a shirt bound to the chest meet in a hard
    seam at the shoulder; lowering the arm swung the sleeve's top away from
    the shirt and the shoulder tore open (measured on a real avatar). Around
    the joint the combined arm + torso weight of each vertex is split by
    :func:`shoulder_seam_share`, so both sides of the seam move together.

    Returns:
        int — vertices re-blended.
    """
    bones = armature_obj.data.bones
    world = armature_obj.matrix_world
    mw = mesh_obj.matrix_world
    names = {g.index: g.name for g in mesh_obj.vertex_groups}
    changed = 0
    for side in ("L", "R"):
        arm_name = next((n for n in ("upperarm.def-" + side, "upper_arm." + side, "DEF-upper_arm." + side)
                         if bones.get(n) is not None and bones[n].use_deform), None)
        if arm_name is None:
            continue
        arm_bone = bones[arm_name]
        torso_names = set()
        parent = arm_bone.parent
        while parent is not None:                   # the chain the arm hangs from
            if parent.use_deform:
                torso_names.add(parent.name)
            parent = parent.parent
        if not torso_names:
            continue
        head = world @ arm_bone.head_local
        axis = (world @ arm_bone.tail_local) - head
        length = axis.length
        if length < 1e-9:
            continue
        axis /= length
        radius = 0.55 * length
        arm_group = mesh_obj.vertex_groups.get(arm_name) or mesh_obj.vertex_groups.new(name=arm_name)
        for v in mesh_obj.data.vertices:
            p = mw @ v.co
            rel = p - head
            if rel.length > radius:
                continue
            w_arm, w_torso = 0.0, 0.0
            for ge in v.groups:
                name = names.get(ge.group)
                if name == arm_name:
                    w_arm += ge.weight
                elif name in torso_names:
                    w_torso += ge.weight
            both = w_arm + w_torso
            if both < 0.5 or (w_arm == 0.0 and rel.dot(axis) < 0.0):
                continue                        # not on the seam / chest skin inside the joint
            target = shoulder_seam_share(rel.dot(axis), radius) * both
            if abs(target - w_arm) < 1e-4:
                continue
            scale = (both - target) / w_torso if w_torso > 0.0 else 0.0
            for ge in v.groups:
                if names.get(ge.group) in torso_names:
                    ge.weight *= scale
            if w_torso == 0.0 and target < both:
                # all arm so far: give the torso part to the arm's parent
                parent_name = next(iter(torso_names & {arm_bone.parent.name})) \
                    if arm_bone.parent is not None and arm_bone.parent.name in torso_names \
                    else next(iter(torso_names))
                g = mesh_obj.vertex_groups.get(parent_name) or mesh_obj.vertex_groups.new(name=parent_name)
                g.add([v.index], both - target, 'ADD')
            arm_group.add([v.index], target, 'REPLACE')
            changed += 1
    return changed


def _bone_kind(name):
    n = name.replace("DEF-", "")
    for kind in ("upper_arm", "forearm", "hand", "thigh", "shin", "foot", "toe", "heel",
                 "neck", "head"):
        if n.startswith(kind):
            return "foot" if kind in ("toe", "heel") else kind
    return "torso"


def _body_part(name):
    """(kind, side) — the part of the body a deform bone belongs to."""
    side = name[-2:] if name[-2:] in (".L", ".R", "-L", "-R") else ""
    kind = _bone_kind(name)
    return kind, (side[-1] if side and kind != "torso" else "")


# joints a garment island may bend across: inside a limb, and neck-to-head.
# At a limb root (shoulder, hip) clothing stays with the torso, as artists
# weight it. Neck-to-chest is left out on purpose: long hair runs head -> neck
# -> chest, and bending it there dragged it onto the chest (measured on a real
# avatar with detected markers: 89.0% -> 87.3% agreement with it, 91.9% without).
_BENDABLE_JOINTS = {
    frozenset(("upper_arm", "forearm")), frozenset(("forearm", "hand")),
    frozenset(("thigh", "shin")), frozenset(("shin", "foot")),
    frozenset(("neck", "head")),
}


def _joint_span(mesh_obj, armature_obj, vertex_indices, share=0.95, cover=0.80):
    """The bones of the joint chain an island's base weights run along, or None.

    Vertices are counted per body part (a foot is foot + heel + toe bones).
    Starting from the leading part, parts that meet it at a joint a garment
    bends across (``_BENDABLE_JOINTS``, parent/child bones) are gathered; when
    no single part owns ``share`` of the island and the gathered chain covers
    ``cover`` of it, the island straddles those joints: a sleeve over the
    elbow, a boot over the ankle, or a whole limb
    modelled as its own piece. Returns that chain's bone names.
    """
    names = {g.index: g.name for g in mesh_obj.vertex_groups}
    bones = armature_obj.data.bones
    counts = {}
    for vi in vertex_indices:
        best, bw = None, 0.0
        for ge in mesh_obj.data.vertices[vi].groups:
            if ge.weight > bw:
                best, bw = names[ge.group], ge.weight
        if best is not None and best in bones:
            part = _body_part(best)
            counts[part] = counts.get(part, 0) + 1
    total = len(vertex_indices)
    if len(counts) < 2 or max(counts.values()) >= share * total:
        return None

    def deform_parent(bone):
        p = bone.parent
        while p is not None and not p.use_deform:
            p = p.parent
        return p
    # part adjacency through bendable parent/child joints
    links = {}
    for bone in bones:
        if not bone.use_deform:
            continue
        p = deform_parent(bone)
        if p is None:
            continue
        a, b = _body_part(bone.name), _body_part(p.name)
        if a == b or frozenset((a[0], b[0])) not in _BENDABLE_JOINTS:
            continue
        if a[1] and b[1] and a[1] != b[1]:
            continue
        links.setdefault(a, set()).add(b)
        links.setdefault(b, set()).add(a)
    # walk the bendable joints from the leading part (through parts that own
    # no vertex themselves, e.g. a short forearm part between elbow and wrist)
    start = max(counts, key=counts.get)
    chain, todo = {start}, [start]
    while todo:
        for nxt in links.get(todo.pop(), ()):
            if nxt not in chain:
                chain.add(nxt)
                todo.append(nxt)
    owned = [p for p in chain if p in counts]
    if len(owned) < 2 or sum(counts[p] for p in owned) < cover * total:
        return None
    return tuple(b.name for b in bones if b.use_deform and _body_part(b.name) in chain)


def _bind_to_joint(mesh_obj, vertex_indices, bone_names):
    """Keep only the joint's bones' weights on an island, renormalised."""
    names = {g.index: g.name for g in mesh_obj.vertex_groups}
    keep_set = set(bone_names)
    for vi in vertex_indices:
        v = mesh_obj.data.vertices[vi]
        keep = {}
        drop = []
        for ge in v.groups:
            n = names[ge.group]
            if n in keep_set:
                keep[n] = ge.weight
            else:
                drop.append(ge.group)
        total = sum(keep.values())
        if total <= 0.0:
            continue
        for gi in drop:
            mesh_obj.vertex_groups[gi].remove([vi])
        for n, w in keep.items():
            if w > 0.0:
                mesh_obj.vertex_groups[n].add([vi], w / total, 'REPLACE')


def rigidify_small_islands(mesh_obj, armature_obj, base_method=None, islands=None):
    """Pin each small/rigid disconnected mesh island to a single bone.

    Stylized humanoid avatars (VRoid / VRChat / mech characters) have
    many separate mesh pieces (halos, armor plates, boots, hair crystals,
    skirt panels, etc.).  Heat-diffusion auto-weights cannot reach across
    island gaps, so each vertex in a separate piece ends up picking an
    essentially arbitrary closest bone — the piece then fractures across
    those bones on any pose.

    This pass identifies "rigid-looking" islands by size and rewrites
    each such island's vertex weights so every vertex in the island is
    assigned weight 1.0 to the bone nearest the island's centroid.  The
    largest island (typically the body skin) is always preserved.

    With ``base_method='SEGMENT'`` the base weights are continuous in space
    (they do not need the islands to be connected), so an island whose
    weights run across limb joints — a sleeve over the elbow, a boot over the
    ankle, a limb modelled as its own piece (see ``_joint_span``) — keeps its
    weights on that joint chain's bones and bends with it instead of going
    rigid.

    Returns:
        int — count of islands that were rigidified.
    """
    if islands is None:
        islands = _find_mesh_islands(mesh_obj)
    if len(islands) < 2:
        # Single-island mesh; nothing to rigidify.
        return 0

    world_matrix = mesh_obj.matrix_world

    # Compute diagonals so we can identify the "body" island (largest)
    # and measure small islands relative to it.
    diagonals = [
        _island_bbox_diagonal(mesh_obj, island, world_matrix)
        for island in islands
    ]
    largest_diagonal = max(diagonals) if diagonals else 0.0
    if largest_diagonal <= 0.0:
        return 0

    size_threshold = largest_diagonal * _RIGID_ISLAND_SIZE_RATIO
    largest_index = diagonals.index(largest_diagonal)

    # Pre-compute deform-bone world centers once.
    bone_centers = {}
    for bone in armature_obj.data.bones:
        if bone.use_deform:
            bone_centers[bone.name] = _bone_world_center(armature_obj, bone)
    if not bone_centers:
        return 0

    rigidified = 0
    for island_index, vertex_indices in enumerate(islands):
        if island_index == largest_index:
            continue  # Never rigidify the body skin itself.

        is_small_by_count = len(vertex_indices) < _RIGID_ISLAND_MAX_VERTS
        is_small_by_size = diagonals[island_index] < size_threshold
        if not (is_small_by_count or is_small_by_size):
            continue
        if base_method == 'SEGMENT':
            pair = _joint_span(mesh_obj, armature_obj, vertex_indices)
            if pair is not None:
                _bind_to_joint(mesh_obj, vertex_indices, pair)
                continue

        # Nearest bone centre. (Tried and measured worse on a real avatar,
        # 2026-09-25: majority vote of base weights — hanging hair followed
        # the arm; nearest bone segment — hair followed the neck.)
        centroid_world = _island_centroid(
            mesh_obj, vertex_indices, world_matrix,
        )
        target_bone = _nearest_deform_bone(centroid_world, bone_centers)
        if target_bone is None:
            continue

        target_group = mesh_obj.vertex_groups.get(target_bone)
        if target_group is None:
            target_group = mesh_obj.vertex_groups.new(name=target_bone)

        # Perf (v3.0.11): wipe only the groups that actually touch
        # this island's verts, not every bone in the rig. On a 60-bone
        # rig with 20 small accessory islands, the naive version hits
        # `.remove()` 1200 times; this typically hits it <100 times.
        groups_touching_island = set()
        for vertex_index in vertex_indices:
            for vge in mesh_obj.data.vertices[vertex_index].groups:
                groups_touching_island.add(vge.group)

        for group_index in groups_touching_island:
            vertex_group = mesh_obj.vertex_groups[group_index]
            if vertex_group.name == target_bone:
                continue
            vertex_group.remove(vertex_indices)
        target_group.add(vertex_indices, 1.0, 'REPLACE')
        rigidified += 1

    return rigidified


# ── Main pipeline entry point ────────────────────────────────

def apply_production_weights(context, mesh_obj, armature_obj, session):
    """Execute the full 7-step production skinning pipeline.

    This is the single entry point called by ``merge.py`` after
    armature assembly.  It replaces the old inline
    ``parent_set(type='ARMATURE_AUTO')`` call.

    The pipeline ALWAYS produces output — the quality score tells
    the user how good the result is; the pipeline never refuses.

    Args:
        context: Blender context.
        mesh_obj: Target mesh object.
        armature_obj: Final merged armature object.
        session: BF_AutoRigSession PropertyGroup.

    Returns:
        SkinningResult with pipeline outcome.
    """
    all_warnings = []

    # Read settings from session (with defaults for backward compat)
    skinning_settings = getattr(session, 'skinning_settings', None)

    if skinning_settings is not None:
        quality_target = skinning_settings.quality_target
        max_influences = skinning_settings.max_influences
        smooth_iterations = skinning_settings.smooth_iterations
        do_face_isolation = skinning_settings.face_isolation
        do_correctives = skinning_settings.corrective_presets
    else:
        # Defaults matching GAME quality target
        quality_target = 'GAME'
        max_influences = 4
        smooth_iterations = 2
        do_face_isolation = True
        do_correctives = True

    # Override settings for DRAFT mode
    if quality_target == 'DRAFT':
        smooth_iterations = 0
        do_face_isolation = False
        do_correctives = False

    # Override settings for FILM mode
    if quality_target == 'FILM':
        if skinning_settings is None:
            max_influences = 8
            smooth_iterations = 1

    # Progress reporting via window manager
    # v3.1.6 (M-7): wrap the pipeline so progress_end runs even on
    # exception — otherwise Blender's progress bar gets stuck.
    wm = context.window_manager
    wm.progress_begin(0, _PROGRESS_TOTAL)
    try:
        # ── Step 1: Mesh validation ──────────────────────────────
        wm.progress_update(_PROGRESS_STEP_VALIDATE)
        depsgraph = context.evaluated_depsgraph_get()
        validation = validate_mesh(mesh_obj, depsgraph)

        if validation.issues:
            all_warnings.extend(validation.issues)

        # ── Step 2: Base weights ─────────────────────────────────
        wm.progress_update(_PROGRESS_STEP_BASE_WEIGHTS)
        method, base_warnings = apply_base_weights(
            context, mesh_obj, armature_obj, validation,
        )
        all_warnings.extend(base_warnings)

        # ── Step 2b: Rigidify small disconnected islands ─────────
        # Stylized humanoid avatars (VRChat/VRM/mech characters) routinely
        # have dozens of separate mesh pieces that heat diffusion cannot
        # reach across.  Without this pass those pieces fracture on pose
        # because each vertex picks its own arbitrary nearest bone.
        islands = _find_mesh_islands(mesh_obj)     # topology is fixed: find once
        rigidified_count = rigidify_small_islands(mesh_obj, armature_obj, method, islands)
        protruding_count = pin_protruding_islands(mesh_obj, armature_obj, islands)
        if protruding_count > 0:
            all_warnings.append(
                f"{protruding_count} protruding piece(s) (accessory, wings, "
                "hair, skirt) attached rigidly to the bone they grow from"
            )
        if rigidified_count > 0:
            all_warnings.append(
                f"{rigidified_count} small disconnected island(s) pinned "
                "to their nearest bone (stylized-avatar rigidification)"
            )
        seam_count = blend_shoulder_seams(mesh_obj, armature_obj)
        if seam_count:
            all_warnings.append(
                f"{seam_count} shoulder vertices blended between arm and torso")

        # ── Step 3: Face/body isolation ──────────────────────────
        face_isolation_applied = False
        face_body_border = frozenset()
        if do_face_isolation and session.rig_type in ('BODY_AND_FACE', 'FACE_ONLY'):
            wm.progress_update(_PROGRESS_STEP_FACE_ISOLATION)
            face_isolation_applied, face_body_border, iso_warnings = (
                isolate_face_weights(mesh_obj, armature_obj, session)
            )
            all_warnings.extend(iso_warnings)
            jaw_count = apply_jaw_region(mesh_obj, armature_obj, session)
            if jaw_count:
                all_warnings.append(f"{jaw_count} lower-face vertices follow the jaw")
        else:
            wm.progress_update(_PROGRESS_STEP_FACE_ISOLATION)

        # ── Step 4: Laplacian smoothing ──────────────────────────
        wm.progress_update(_PROGRESS_STEP_SMOOTHING)
        smooth_weights(mesh_obj, smooth_iterations, face_body_border)

        # ── Step 4b: Sharpen before normalization ────────────────
        # Concentrates each vertex's weights onto its dominant bone(s)
        # so the finished skin has crisper transitions rather than the
        # diffuse ARMATURE_AUTO default.
        # (applied inside the normalization pass below: one read + write)

        # ── Step 5: Normalization ────────────────────────────────
        wm.progress_update(_PROGRESS_STEP_NORMALIZE)
        fallback_count = normalize_weights(mesh_obj, armature_obj, max_influences,
                                           sharpen_power=_WEIGHT_SHARPEN_POWER)
        if fallback_count > 0:
            all_warnings.append(
                f"{fallback_count} vertices had zero weight and were "
                "assigned to their nearest bone"
            )

        # ── Step 6: Corrective presets ───────────────────────────
        correctives_applied = False
        if do_correctives:
            wm.progress_update(_PROGRESS_STEP_CORRECTIVES)
            preset_count = apply_corrective_presets(mesh_obj, armature_obj)
            correctives_applied = preset_count > 0

            # Re-normalize after correctives to ensure sum = 1.0
            if correctives_applied:
                normalize_weights(mesh_obj, armature_obj, max_influences)
        else:
            wm.progress_update(_PROGRESS_STEP_CORRECTIVES)

        # ── Step 7: Quality scoring ──────────────────────────────
        wm.progress_update(_PROGRESS_STEP_QUALITY)
        quality_report = score_weight_quality(
            mesh_obj, armature_obj, max_influences, method=method,
            validation=validation, rescued_vertices=fallback_count)

        # optional volume preservation (dual-quaternion skinning)
        if skinning_settings is not None and getattr(skinning_settings, "preserve_volume", False):
            for mod in mesh_obj.modifiers:
                if mod.type == 'ARMATURE' and mod.object == armature_obj:
                    mod.use_deform_preserve_volume = True

        return SkinningResult(
            success=True,
            method=method,
            quality_report=quality_report,
            warnings=all_warnings,
            face_isolation_applied=face_isolation_applied,
            correctives_applied=correctives_applied,
        )
    finally:
        wm.progress_end()
