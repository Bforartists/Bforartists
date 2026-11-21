"""BoneCraft Phase 3 — Auto-Rig Wizard UI State Machine.

Implements the step-by-step wizard for guided auto-rigging: mesh
selection, rig type, body marker placement, facial marker placement,
review/validation, generation, and completion summary.

The wizard is a linear state machine.  Each step has validation
requirements that must pass before advancing to the next step.
"""

import bpy
import blf
import gpu
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatVectorProperty,
    IntProperty,
    StringProperty,
)

from boneforge.i18n import T
from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader
from mathutils import Vector

from boneforge.core import addon_prefs
from boneforge.autorig.constants import (
    BODY_MARKERS,
    BODY_SYMMETRY_PAIRS,
    FACE_MARKERS,
    FACE_SYMMETRY_PAIRS,
    FINGER_COUNT_ITEMS,
    FINGER_MARKER_LABELS,
    FINGER_MARKERS_BY_COUNT,
    FINGER_SYMMETRY_PAIRS,
    OPTIONAL_BODY_MARKERS,
    REQUIRED_BODY_MARKERS,
    RIG_TYPE_ITEMS,
    STEP_INACTIVE,
    STEP_SELECT_MESH,
    STEP_RIG_TYPE,
    STEP_BODY_MARKERS,
    STEP_FINGER_MARKERS,
    STEP_FACE_MARKERS,
    STEP_REVIEW,
    STEP_GENERATE,
    STEP_DONE,
    STEP_LABELS,
    STAGING_COLLECTION_NAME,
)
from boneforge.autorig.session import (
    _ensure_marker_slots,
    get_body_marker,
    get_face_marker,
    get_finger_marker,
    is_position_placed,
    recalculate_derived_joints,
    reset_session,
    rollback_scene_changes,
    save_session_backup,
    restore_session_backup,
)
from boneforge.autorig.geo_detect import confidence_category

import logging

logger = logging.getLogger(__name__)

# Precomputed frozensets for O(1) paired-marker lookup.
_BODY_PAIRED_MARKERS = frozenset(
    name for pair in BODY_SYMMETRY_PAIRS for name in pair
)
_FACE_PAIRED_MARKERS = frozenset(
    name for pair in FACE_SYMMETRY_PAIRS for name in pair
)
_FINGER_PAIRED_MARKERS = frozenset(
    name for pair in FINGER_SYMMETRY_PAIRS for name in pair
)

# Midline markers — anything in BODY_MARKERS / FACE_MARKERS that is NOT part of
# a left/right pair is considered to lie on the body's central YZ plane.
# When one of these is selected for placement, the axis-lock toolbar defaults
# to Y + Z on / X off so the marker stays on the midline. The toggles are
# still freely user-overridable.
_MIDLINE_BODY_MARKERS = frozenset(BODY_MARKERS) - _BODY_PAIRED_MARKERS
_MIDLINE_FACE_MARKERS = frozenset(FACE_MARKERS) - _FACE_PAIRED_MARKERS


def _apply_default_axis_lock_for_marker(session, marker_name, marker_type):
    """Default the placement-axis toggles based on the marker being placed.

    Midline markers (pelvis, neck base, head top, nose tip, chin, lips) get
    X off / Y on / Z on so they snap to the body centerline; everything else
    gets all three axes on. The user can still toggle freely after this runs
    — it only sets the starting state for the newly-selected marker.
    """
    if marker_type == 'BODY':
        is_midline = marker_name in _MIDLINE_BODY_MARKERS
    elif marker_type == 'FACE':
        is_midline = marker_name in _MIDLINE_FACE_MARKERS
    else:
        # Finger markers are all paired (L/R), never midline.
        is_midline = False

    if is_midline:
        session.placement_axis_x = False
        session.placement_axis_y = True
        session.placement_axis_z = True
    else:
        session.placement_axis_x = True
        session.placement_axis_y = True
        session.placement_axis_z = True

# Bounding box expansion factor for marker clamping.
_BOUNDS_EXPANSION = 0.1

# ── Marker visualization colours ────────────────────────────
_COLOR_UNCONFIRMED = (1.0, 0.75, 0.0, 0.85)   # amber
_COLOR_CONFIRMED = (0.2, 0.85, 0.2, 0.85)      # green
_COLOR_UNPLACED = (0.5, 0.5, 0.5, 0.3)         # gray ghost
_COLOR_ACTIVE = (1.0, 1.0, 1.0, 0.95)          # white (being placed)
_COLOR_MIRRORED = (0.4, 0.7, 1.0, 0.8)        # blue (mirrored right hand)
_MARKER_DRAW_RADIUS = 0.012  # fraction of mesh bounding box diagonal
_LABEL_FONT_SIZE = 13

# Module-level draw handler storage (set during register/unregister).
# Phase 4: Will be populated when modal operators are completed
_draw_handle_3d = None
_draw_handle_2d = None

# Live placement preview state (written by the modal, read by draw callbacks).
_preview_position = None     # Vector or None when no placement is active
_preview_marker_name = ""    # Display name shown next to the preview dot
_preview_mirror_position = None   # Mirrored preview Vector, or None
_preview_mirror_name = ""         # Display name of the symmetry pair

# Active placement modal tracking — allows toggling off by re-clicking.
_active_placement_marker = ""   # marker_name of the running modal, or ""
_cancel_active_placement = False  # set True to tell the modal to exit


# ── Shared helpers ───────────────────────────────────────────

def _get_marker_status_icon(marker):
    """Return the appropriate icon for a marker's current state.

    Returns:
        ``'CHECKMARK'`` if confirmed,
        ``'DOT'`` if placed but unconfirmed,
        ``'ADD'`` if not yet placed.
    """
    if marker.confirmed:
        return 'CHECKMARK'
    if is_position_placed(Vector(marker.position)):
        return 'DOT'
    return 'ADD'


def _confidence_icon(category):
    return {
        'CONFIRMED': 'CHECKMARK',
        'REVIEW': 'INFO',
        'ADJUST': 'ERROR',
    }.get(category, 'QUESTION')


def _find_symmetry_pair_name(marker_name, symmetry_pairs):
    """Return the name of the symmetry partner, or None if unpaired."""
    for left, right in symmetry_pairs:
        if marker_name == left:
            return right
        if marker_name == right:
            return left
    return None


def _get_mesh_center_x(session):
    """Return the X coordinate of the target mesh's bounding-box center.

    Symmetry mirroring reflects around this X value rather than the
    global origin, so meshes that aren't centered at X=0 still mirror
    correctly.  Falls back to 0.0 if the mesh isn't found.
    """
    mesh_obj = bpy.data.objects.get(session.mesh_object_name) if session else None
    if mesh_obj is None:
        return 0.0
    # Use the mesh object's world-space bounding box center
    bbox = [mesh_obj.matrix_world @ Vector(corner) for corner in mesh_obj.bound_box]
    min_x = min(v.x for v in bbox)
    max_x = max(v.x for v in bbox)
    return (min_x + max_x) * 0.5


def _mirror_x_around_center(position, center_x):
    """Return a copy of *position* reflected across the given X center.

    ``mirrored.x = 2 * center_x - position.x`` reflects position.x
    across the line ``x = center_x``.
    """
    mirrored = Vector(position)
    mirrored.x = 2.0 * center_x - mirrored.x
    return mirrored


def _mirror_symmetry_pair(marker_name, target_position, symmetry_pairs,
                          get_fn, center_x=0.0):
    """Mirror a marker position to its symmetry pair if both are locked.

    Reflects across the mesh's X center (not the global origin).

    Args:
        marker_name: Name of the marker that was moved.
        target_position: New position as a Vector.
        symmetry_pairs: The symmetry pairs tuple (body or face).
        get_fn: Callable(name) -> marker or None.
        center_x: X coordinate of the mesh center for mirroring.
    """
    for left, right in symmetry_pairs:
        pair_name = None
        if marker_name == left:
            pair_name = right
        elif marker_name == right:
            pair_name = left

        if pair_name is None:
            continue

        pair_marker = get_fn(pair_name)
        if pair_marker is not None and pair_marker.symmetry_locked:
            mirrored = _mirror_x_around_center(target_position, center_x)
            pair_marker.position = tuple(mirrored)
        return  # Each marker belongs to at most one pair


def _check_pairwise_distances(marker_names, marker_positions, threshold):
    """Check all pairwise distances between placed markers.

    Args:
        marker_names: List of marker display names.
        marker_positions: List of Vector positions (parallel to names).
        threshold: Minimum acceptable distance between markers.

    Returns:
        List of warning strings for markers that are too close.
    """
    warnings = []
    for i in range(len(marker_positions)):
        for j in range(i + 1, len(marker_positions)):
            distance = (marker_positions[i] - marker_positions[j]).length
            if distance < threshold:
                warnings.append(
                    f"{marker_names[i]} and {marker_names[j]} are less than "
                    f"{threshold:.3f} apart — review placement"
                )
    return warnings


def _snap_to_mesh_surface(target_position, snap_object):
    """Snap a world-space position to the nearest point on a mesh surface.

    Args:
        target_position: World-space Vector to snap.
        snap_object: Mesh object to snap to.

    Returns:
        Tuple of ``(snapped_position, success)`` where snapped_position
        is a world-space Vector.
    """
    local_position = snap_object.matrix_world.inverted() @ target_position
    try:
        success, closest, normal, face_index = snap_object.closest_point_on_mesh(
            local_position,
        )
    except RuntimeError:
        # Mesh cannot build internal BVH data (e.g. modifiers, zero geometry).
        # Fall back gracefully — caller will warn and continue without snap.
        return target_position, False
    if success:
        snapped = snap_object.matrix_world @ closest
        return snapped, True
    return target_position, False


def _clamp_to_bounding_box(position, mesh_obj):
    """Clamp a world-space position to the mesh's expanded bounding box.

    The bounding box is expanded by ``_BOUNDS_EXPANSION`` on each side
    to allow markers slightly outside the mesh surface.

    Args:
        position: World-space Vector to clamp.
        mesh_obj: Mesh object providing the bounding box.

    Returns:
        Clamped Vector.
    """
    bounding_box = mesh_obj.bound_box
    box_min = Vector(bounding_box[0])
    box_max = Vector(bounding_box[6])
    expansion = (box_max - box_min) * _BOUNDS_EXPANSION

    box_min_world = mesh_obj.matrix_world @ (box_min - expansion)
    box_max_world = mesh_obj.matrix_world @ (box_max + expansion)

    clamped = Vector(position)
    for axis in range(3):
        axis_min = min(box_min_world[axis], box_max_world[axis])
        axis_max = max(box_min_world[axis], box_max_world[axis])
        clamped[axis] = max(axis_min, min(axis_max, clamped[axis]))
    return clamped


def _compute_mesh_max_dimension(mesh_obj):
    """Compute the largest axis-aligned dimension of a mesh's bounding box.

    Returns:
        The maximum dimension, or 1.0 if the mesh is degenerate.
    """
    bounding_box = mesh_obj.bound_box
    box_min = Vector(bounding_box[0])
    box_max = Vector(bounding_box[6])
    dimensions = box_max - box_min
    max_dimension = max(dimensions.x, dimensions.y, dimensions.z)
    if max_dimension < 0.001:
        return 1.0
    return max_dimension


def _next_step_for_rig_type(current_step, rig_type, finger_count=5):
    """Compute the next wizard step, skipping steps irrelevant to rig type.

    Args:
        current_step: Current step number.
        rig_type: One of ``'BODY_AND_FACE'``, ``'BODY_ONLY'``, ``'FACE_ONLY'``.
        finger_count: Number of fingers (0 skips the finger step).

    Returns:
        The next step number.
    """
    next_step = current_step + 1

    if next_step == STEP_BODY_MARKERS and rig_type == 'FACE_ONLY':
        next_step = STEP_FINGER_MARKERS

    # v3.0.23: only FACE_ONLY skips the finger step.  BODY_ONLY /
    # BODY_AND_FACE always visit it so users can pick the finger
    # detail level (including "No Fingers") from the descriptive
    # selector rather than having it silently skipped.
    if next_step == STEP_FINGER_MARKERS:
        if rig_type == 'FACE_ONLY':
            next_step = STEP_FACE_MARKERS

    if next_step == STEP_FACE_MARKERS and rig_type == 'BODY_ONLY':
        next_step = STEP_REVIEW

    return next_step


def _prev_step_for_rig_type(current_step, rig_type, finger_count=5):
    """Compute the previous wizard step, skipping irrelevant steps.

    Args:
        current_step: Current step number.
        rig_type: One of ``'BODY_AND_FACE'``, ``'BODY_ONLY'``, ``'FACE_ONLY'``.
        finger_count: Number of fingers (0 skips the finger step).

    Returns:
        The previous step number.
    """
    prev_step = current_step - 1

    if prev_step == STEP_FACE_MARKERS and rig_type == 'BODY_ONLY':
        prev_step = STEP_FINGER_MARKERS

    # v3.0.23: symmetrical to next-step — only FACE_ONLY skips fingers.
    if prev_step == STEP_FINGER_MARKERS:
        if rig_type == 'FACE_ONLY':
            prev_step = STEP_BODY_MARKERS

    if prev_step == STEP_BODY_MARKERS and rig_type == 'FACE_ONLY':
        prev_step = STEP_RIG_TYPE

    return prev_step


def _visible_step_number(current_step, rig_type, finger_count=5):
    """Return (visible_index, total_visible_steps) for display.

    The wizard skips body markers for face-only and face markers for
    body-only.  The Generate step is transient (not user-navigable),
    so it's excluded from the total.  This gives a clean "Step 3/4"
    style header that matches what the user actually sees.
    """
    # Build the ordered list of steps the user actually visits.
    all_steps = [STEP_SELECT_MESH, STEP_RIG_TYPE]
    if rig_type in ('BODY_AND_FACE', 'BODY_ONLY'):
        all_steps.append(STEP_BODY_MARKERS)
    # v3.0.23: always count the finger step for body rig types —
    # it doubles as the "pick your finger detail" selector.
    if rig_type in ('BODY_AND_FACE', 'BODY_ONLY'):
        all_steps.append(STEP_FINGER_MARKERS)
    if rig_type in ('BODY_AND_FACE', 'FACE_ONLY'):
        all_steps.append(STEP_FACE_MARKERS)
    all_steps.append(STEP_REVIEW)
    # STEP_GENERATE is transient — don't count it
    all_steps.append(STEP_DONE)

    total = len(all_steps)

    if current_step == STEP_GENERATE:
        # Show same number as Review during the brief generate flash
        try:
            visible = all_steps.index(STEP_REVIEW) + 1
        except ValueError:
            visible = total - 1
    elif current_step in all_steps:
        visible = all_steps.index(current_step) + 1
    else:
        visible = current_step

    return visible, total


# ── Validation helpers ────────────────────────────────────────

def _validate_mesh(session):
    """Validate the selected mesh is suitable for rigging.

    Returns:
        Tuple of ``(is_valid, error_message)``.
    """
    if not session.mesh_object_name:
        return False, "No mesh selected"

    mesh_obj = bpy.data.objects.get(session.mesh_object_name)
    if mesh_obj is None:
        return False, f"Mesh '{session.mesh_object_name}' not found"

    if mesh_obj.type != 'MESH':
        return False, f"'{session.mesh_object_name}' is not a mesh object"

    if len(mesh_obj.data.polygons) == 0:
        return False, "This mesh has no geometry. Please select a mesh with faces."

    return True, ""


def _validate_markers(session, marker_names, marker_collection,
                      required_names=None):
    """Check that required markers in a collection are confirmed.

    Optional markers (those not in *required_names*) are allowed to be
    unconfirmed — the system will derive their positions automatically.

    Shared by body and face marker validation.

    Args:
        session: The active wizard session.
        marker_names: Tuple of marker name strings.
        marker_collection: The PropertyGroup collection to check.
        required_names: Optional tuple/set of marker names that must be
            confirmed.  If ``None``, all markers are treated as required
            (backwards-compatible behaviour for face markers).

    Returns:
        Tuple of ``(all_required_confirmed, list_of_warnings)``.
    """
    _ensure_marker_slots(session)
    warnings = []
    all_required_confirmed = True

    # If no required set given, every marker is required
    if required_names is None:
        required_names = set(marker_names)
    else:
        required_names = set(required_names)

    for i, name in enumerate(marker_names):
        marker = marker_collection[i]
        is_required = name in required_names

        if not marker.confirmed:
            if is_required:
                all_required_confirmed = False
                warnings.append(f"{name}: not confirmed (required)")
            # Optional markers that aren't confirmed are fine — skip silently
        elif not is_position_placed(Vector(marker.position)):
            warnings.append(f"{name}: position appears to be at origin")

    return all_required_confirmed, warnings


def _run_review_validation(session):
    """Run full validation for the review step (Step 5).

    Checks marker spacing against a relative threshold derived from
    the mesh bounding box.

    Returns:
        List of warning strings.  Empty list means all checks passed.
    """
    warnings = []
    _ensure_marker_slots(session)

    mesh_obj = bpy.data.objects.get(session.mesh_object_name)
    if mesh_obj is None:
        warnings.append("Target mesh not found — cannot validate")
        return warnings

    max_dimension = _compute_mesh_max_dimension(mesh_obj)
    minimum_distance_threshold = 0.001 * max_dimension

    # Check body marker spacing
    if session.rig_type in ('BODY_AND_FACE', 'BODY_ONLY'):
        body_names = []
        body_positions = []
        for i, name in enumerate(BODY_MARKERS):
            position = Vector(session.body_markers[i].position)
            body_names.append(name)
            body_positions.append(position)

        warnings.extend(
            _check_pairwise_distances(
                body_names, body_positions, minimum_distance_threshold,
            )
        )

    # Check face marker spacing (only placed markers)
    if session.rig_type in ('BODY_AND_FACE', 'FACE_ONLY'):
        face_names = []
        face_positions = []
        for i, name in enumerate(FACE_MARKERS):
            position = Vector(session.face_markers[i].position)
            if is_position_placed(position):
                face_names.append(name)
                face_positions.append(position)

        face_warnings = _check_pairwise_distances(
            face_names, face_positions, minimum_distance_threshold,
        )
        # Use a friendlier message for face overlaps
        for warning in face_warnings:
            warnings.append(
                warning.replace("review placement", "control shapes may overlap")
            )

    return warnings


def _cleanup_staging_collection():
    """Remove the staging collection and all its objects.

    Safe to call even if the staging collection does not exist.
    SIG-8 fix: per-object try/except prevents partial cleanup failures.
    """
    staging = bpy.data.collections.get(STAGING_COLLECTION_NAME)
    if staging is None:
        return
    for obj in list(staging.objects):
        try:
            bpy.data.objects.remove(obj, do_unlink=True)
        except RuntimeError as error:
            logger.warning(f"[BoneCraft] Could not remove staging object "
                  f"'{obj.name}': {error}")
    try:
        bpy.data.collections.remove(staging)
    except RuntimeError as error:
        logger.warning(f"[BoneCraft] Could not remove staging collection: {error}")


def _prepare_staging_collection(context):
    """Create a fresh staging collection for atomic rig generation.

    Removes any leftover staging collection first, then creates a
    new one excluded from all view layers.

    Returns:
        The new staging ``Collection``.
    """
    _cleanup_staging_collection()

    staging = bpy.data.collections.new(STAGING_COLLECTION_NAME)
    context.scene.collection.children.link(staging)

    for view_layer in context.scene.view_layers:
        layer_collection = view_layer.layer_collection.children.get(
            STAGING_COLLECTION_NAME,
        )
        if layer_collection is not None:
            layer_collection.exclude = True

    return staging


# ── Operators ─────────────────────────────────────────────────

class BF_OT_WizardStart(bpy.types.Operator):
    """Start the auto-rig wizard."""

    bl_idname = "boneforge.autorig_wizard_start"
    bl_label = "Start Auto-Rig"
    bl_options = {'REGISTER'}

    def execute(self, context):
        """Initialize a new wizard session at Step 1."""
        session = context.scene.boneforge_autorig_session
        reset_session(session)
        _ensure_marker_slots(session)

        session.is_active = True
        session.wizard_step = STEP_SELECT_MESH
        session.snapshot_blend_data = "{}"

        save_session_backup(context.scene)
        if context.area:
            context.area.tag_redraw()

        self.report({'INFO'}, "Auto-rig wizard started")
        return {'FINISHED'}


class BF_OT_WizardNext(bpy.types.Operator):
    """Advance to the next wizard step after validation."""

    bl_idname = "boneforge.autorig_wizard_next"
    bl_label = "Next Step"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        """Only available when the wizard is active and not on the final step."""
        session = context.scene.boneforge_autorig_session
        return session.is_active and session.wizard_step < STEP_DONE

    def execute(self, context):
        """Validate the current step, then advance to the next."""
        session = context.scene.boneforge_autorig_session
        step = session.wizard_step

        # Validate current step before advancing
        if step == STEP_SELECT_MESH:
            valid, error = _validate_mesh(session)
            if not valid:
                self.report({'WARNING'}, error)
                return {'CANCELLED'}

        elif step == STEP_BODY_MARKERS:
            valid, warnings = _validate_markers(
                session, BODY_MARKERS, session.body_markers,
                required_names=REQUIRED_BODY_MARKERS,
            )
            if not valid:
                self.report({'WARNING'},
                            "Confirm all required body markers before "
                            "continuing (optional markers can be skipped)")
                return {'CANCELLED'}

        elif step == STEP_FINGER_MARKERS:
            # v3.0.12: finger markers are GUIDES, not rules. The user
            # can advance with zero, some, or all markers placed so
            # they can hand-customise finger rigs freely. Any
            # missing markers will be auto-derived by finger_gen.py
            # from the placed ones (and wrist/palm defaults).
            finger_count = session.finger_count
            if finger_count > 0:
                marker_names = FINGER_MARKERS_BY_COUNT.get(finger_count, ())
                placed_count = 0
                for name in marker_names:
                    marker = get_finger_marker(session, name)
                    if marker is not None and marker.confirmed:
                        placed_count += 1
                total = len(marker_names)
                if placed_count < total:
                    missing = total - placed_count
                    self.report(
                        {'INFO'},
                        f"Advancing with {placed_count}/{total} finger "
                        f"markers placed — {missing} will be auto-derived",
                    )

        elif step == STEP_FACE_MARKERS:
            valid, warnings = _validate_markers(
                session, FACE_MARKERS, session.face_markers,
            )
            if not valid:
                self.report({'WARNING'},
                            "Confirm all facial markers before continuing")
                return {'CANCELLED'}

        next_step = _next_step_for_rig_type(step, session.rig_type, finger_count=session.finger_count)
        session.wizard_step = next_step
        save_session_backup(context.scene)
        if context.area:
            context.area.tag_redraw()

        label = STEP_LABELS.get(next_step, f"Step {next_step}")
        self.report({'INFO'}, f"Step {next_step}: {label}")
        return {'FINISHED'}


class BF_OT_WizardBack(bpy.types.Operator):
    """Go back to the previous wizard step."""

    bl_idname = "boneforge.autorig_wizard_back"
    bl_label = "Previous Step"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        """Only available when the wizard can go back (not from Done: the
        step before it is the generate screen, a dead end)."""
        session = context.scene.boneforge_autorig_session
        return (session.is_active
                and STEP_SELECT_MESH < session.wizard_step < STEP_DONE)

    def execute(self, context):
        """Move to the previous step, skipping irrelevant marker steps."""
        session = context.scene.boneforge_autorig_session
        prev_step = _prev_step_for_rig_type(
            session.wizard_step, session.rig_type,
            finger_count=session.finger_count,
        )
        session.wizard_step = prev_step
        save_session_backup(context.scene)
        if context.area:
            context.area.tag_redraw()
        return {'FINISHED'}


class BF_OT_WizardBuildControlRig(bpy.types.Operator):
    """Build the engine control rig (twist and skirt bones, face controls, joint correctives) on the generated armature"""

    bl_idname = "boneforge.autorig_build_control_rig"
    bl_label = "Build Control Rig"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """Only on the Done step, once, while the review options still exist."""
        session = context.scene.boneforge_autorig_session
        if not (session.is_active and session.wizard_step == STEP_DONE):
            return False
        arm = bpy.data.objects.get(session.generated_final_armature)
        if arm is None or arm.type != 'ARMATURE':
            return False
        from boneforge.autorig import rig_integrate
        return rig_integrate.is_wizard_skeleton(b.name for b in arm.data.bones)

    def execute(self, context):
        from boneforge import bfa_guard
        from boneforge.autorig.rig_build import build_control_rig
        bfa_guard.require_bforartists("rig_build")
        session = context.scene.boneforge_autorig_session
        arm = bpy.data.objects[session.generated_final_armature]
        try:
            if context.object is not None and context.object.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            context.view_layer.objects.active = arm
            build_control_rig(arm, context=context)
        except Exception as exc:
            self.report({'ERROR'}, f"Control rig build failed: {exc}. "
                                   "Undo (Ctrl+Z) restores the generated rig.")
            return {'CANCELLED'}
        if context.area:
            context.area.tag_redraw()
        self.report({'INFO'}, "BoneCraft control rig built")
        return {'FINISHED'}


class BF_OT_WizardCancel(bpy.types.Operator):
    """Cancel the auto-rig wizard and revert all changes."""

    bl_idname = "boneforge.autorig_wizard_cancel"
    bl_label = "Cancel Wizard"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def description(cls, context, properties):
        """On the Done step this button is Close Wizard: it keeps the rig."""
        session = context.scene.boneforge_autorig_session
        if session.wizard_step == STEP_DONE:
            return "Close the auto-rig wizard and keep the generated rig"
        return "Cancel the auto-rig wizard and revert all changes"

    @classmethod
    def poll(cls, context):
        """Only available when the wizard is active."""
        session = context.scene.boneforge_autorig_session
        return session.is_active

    def execute(self, context):
        """Roll back scene changes, remove artifacts, and reset session.

        On the Done step this is Close Wizard: the generated rig is the
        result, so nothing it logged (face control shapes) is rolled back.
        """
        session = context.scene.boneforge_autorig_session

        finished = session.wizard_step == STEP_DONE
        if finished:
            reverted = 0
        else:
            reverted = rollback_scene_changes(session)

        # Remove proxy mesh if it exists
        if session.proxy_mesh_name:
            proxy = bpy.data.objects.get(session.proxy_mesh_name)
            if proxy is not None:
                bpy.data.objects.remove(proxy, do_unlink=True)

        _cleanup_staging_collection()
        reset_session(session)

        # Clear JSON backup
        if context.scene.get("boneforge_autorig_session_json"):
            del context.scene["boneforge_autorig_session_json"]

        if context.area:
            context.area.tag_redraw()
        if finished:
            self.report({'INFO'}, "Auto-rig wizard closed")
        else:
            self.report({'INFO'},
                        f"Auto-rig wizard cancelled — {reverted} changes reverted")
        return {'FINISHED'}


class BF_OT_WizardSelectMesh(bpy.types.Operator):
    """Select the target mesh for auto-rigging."""

    bl_idname = "boneforge.autorig_select_mesh"
    bl_label = "Select Mesh"
    bl_options = {'REGISTER'}

    mesh_name: StringProperty(
        name="Mesh",
        description="Name of the mesh object to rig",
        default="",
    )

    @classmethod
    def poll(cls, context):
        """Only available on the mesh selection step."""
        session = context.scene.boneforge_autorig_session
        return session.is_active and session.wizard_step == STEP_SELECT_MESH

    def execute(self, context):
        """Set the session's mesh target from the property or active object."""
        session = context.scene.boneforge_autorig_session

        if self.mesh_name:
            session.mesh_object_name = self.mesh_name
        elif context.active_object and context.active_object.type == 'MESH':
            session.mesh_object_name = context.active_object.name
        else:
            # SIG-4 fix: distinguish between no arg and no active mesh
            self.report({'WARNING'},
                        "Specify a mesh name or select one in the 3D viewport")
            return {'CANCELLED'}

        valid, error = _validate_mesh(session)
        if not valid:
            session.mesh_object_name = ""
            self.report({'WARNING'}, error)
            return {'CANCELLED'}

        self.report({'INFO'}, f"Mesh selected: {session.mesh_object_name}")
        if context.area:
            context.area.tag_redraw()
        return {'FINISHED'}


class BF_OT_WizardSetRigType(bpy.types.Operator):
    """Set the rig type (body, face, or both)."""

    bl_idname = "boneforge.autorig_set_rig_type"
    bl_label = "Set Rig Type"
    bl_options = {'REGISTER'}

    rig_type: EnumProperty(options={'HIDDEN', 'SKIP_SAVE'},
        name="Rig Type",
        items=RIG_TYPE_ITEMS,
        default='BODY_AND_FACE',
    )

    @classmethod
    def poll(cls, context):
        """Only available when the wizard is active."""
        session = context.scene.boneforge_autorig_session
        return session.is_active

    def execute(self, context):
        """Store the chosen rig type on the session."""
        session = context.scene.boneforge_autorig_session
        session.rig_type = self.rig_type
        if context.area:
            context.area.tag_redraw()

        self.report({'INFO'}, f"Rig type: {self.rig_type}")
        return {'FINISHED'}


class BF_OT_WizardMoveMarker(bpy.types.Operator):
    """Drag a marker to a new position with mesh surface snapping."""

    bl_idname = "boneforge.autorig_move_marker"
    bl_label = "Move Marker"
    bl_options = {'REGISTER', 'UNDO'}

    marker_name: StringProperty(
        name="Marker",
        description="Name of the marker to move",
    )
    marker_type: EnumProperty(options={'HIDDEN', 'SKIP_SAVE'},
        name="Type",
        items=[
            ('BODY', "Body", "Body marker"),
            ('FACE', "Face", "Facial marker"),
            ('FINGER', "Finger", "Finger marker"),
        ],
        default='BODY',
    )
    position: FloatVectorProperty(
        name="Position",
        description="Target position for the marker",
        size=3,
        default=(0, 0, 0),
    )
    snap: BoolProperty(
        name="Snap to Surface",
        description="Snap the marker onto the nearest mesh surface",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        """Only available when the wizard is active."""
        session = context.scene.boneforge_autorig_session
        return session.is_active

    def execute(self, context):
        """Move a marker with surface snapping, bounds clamping, and symmetry."""
        session = context.scene.boneforge_autorig_session
        target_position = Vector(self.position)

        # Attempt mesh surface snap
        mesh_obj = bpy.data.objects.get(session.mesh_object_name)
        if mesh_obj is not None and mesh_obj.type == 'MESH':
            # Use proxy mesh if available for performance
            snap_object = mesh_obj
            proxy = bpy.data.objects.get(session.proxy_mesh_name)
            if proxy is not None:
                snap_object = proxy

            snap_succeeded = True
            if self.snap:
                target_position, snap_succeeded = _snap_to_mesh_surface(
                    target_position, snap_object,
                )
            if not snap_succeeded:
                self.report({'WARNING'},
                            "Surface snap unavailable — "
                            "position the marker manually")

            target_position = _clamp_to_bounding_box(
                target_position, mesh_obj,
            )

        # Dispatch to the correct marker type
        if self.marker_type == 'BODY':
            self._apply_to_body(session, context, target_position)
        elif self.marker_type == 'FACE':
            self._apply_to_face(session, target_position)
        elif self.marker_type == 'FINGER':
            self._apply_to_finger(session, context, target_position)

        if context.area:
            context.area.tag_redraw()
        return {'FINISHED'}

    def _apply_to_body(self, session, context, target_position):
        """Write position to body marker and handle symmetry."""
        marker = get_body_marker(session, self.marker_name)
        if marker is None:
            return

        marker.position = tuple(target_position)

        if marker.symmetry_locked and getattr(session, 'body_symmetry_enabled', True):
            center_x = _get_mesh_center_x(session)

            def get_fn(name):
                return get_body_marker(session, name)

            _mirror_symmetry_pair(
                self.marker_name, target_position,
                BODY_SYMMETRY_PAIRS, get_fn,
                center_x=center_x,
            )

        recalculate_derived_joints(session, context)

    def _apply_to_face(self, session, target_position):
        """Write position to face marker and handle symmetry."""
        marker = get_face_marker(session, self.marker_name)
        if marker is None:
            return

        marker.position = tuple(target_position)

        if marker.symmetry_locked and getattr(session, 'face_symmetry_enabled', True):
            center_x = _get_mesh_center_x(session)

            def get_fn(name):
                return get_face_marker(session, name)

            _mirror_symmetry_pair(
                self.marker_name, target_position,
                FACE_SYMMETRY_PAIRS, get_fn,
                center_x=center_x,
            )

    def _apply_to_finger(self, session, context, target_position):
        """Write position to finger marker and handle symmetry."""
        marker = get_finger_marker(session, self.marker_name)
        if marker is None:
            return

        marker.position = tuple(target_position)

        if marker.symmetry_locked and session.finger_symmetry:
            center_x = _get_mesh_center_x(session)

            def get_fn(name):
                return get_finger_marker(session, name)

            _mirror_symmetry_pair(
                self.marker_name, target_position,
                FINGER_SYMMETRY_PAIRS, get_fn,
                center_x=center_x,
            )


class BF_OT_WizardToggleSymmetry(bpy.types.Operator):
    """Toggle symmetry lock on a marker pair."""

    bl_idname = "boneforge.autorig_toggle_symmetry"
    bl_label = "Toggle Symmetry"
    bl_options = {'REGISTER', 'UNDO'}

    marker_name: StringProperty(options={'HIDDEN', 'SKIP_SAVE'}, name="Marker")
    marker_type: EnumProperty(options={'HIDDEN', 'SKIP_SAVE'},
        name="Type",
        items=[
            ('BODY', "Body", "Body marker"),
            ('FACE', "Face", "Facial marker"),
            ('FINGER', "Finger", "Finger marker"),
        ],
        default='BODY',
    )

    @classmethod
    def poll(cls, context):
        """Only available when the wizard is active."""
        session = context.scene.boneforge_autorig_session
        return session.is_active

    def execute(self, context):
        """Flip the symmetry_locked flag on the named marker."""
        session = context.scene.boneforge_autorig_session

        if self.marker_type == 'BODY':
            marker = get_body_marker(session, self.marker_name)
        elif self.marker_type == 'FACE':
            marker = get_face_marker(session, self.marker_name)
        else:
            marker = get_finger_marker(session, self.marker_name)

        if marker is None:
            return {'CANCELLED'}

        marker.symmetry_locked = not marker.symmetry_locked
        state = "enabled" if marker.symmetry_locked else "disabled"
        self.report({'INFO'}, f"Symmetry {state} for {self.marker_name}")

        if context.area:
            context.area.tag_redraw()
        return {'FINISHED'}


class BF_OT_WizardConfirmMarker(bpy.types.Operator):
    """Confirm a single marker position."""

    bl_idname = "boneforge.autorig_confirm_marker"
    bl_label = "Confirm Marker"
    bl_options = {'REGISTER', 'UNDO'}

    marker_name: StringProperty(options={'HIDDEN', 'SKIP_SAVE'}, name="Marker")
    marker_type: EnumProperty(options={'HIDDEN', 'SKIP_SAVE'},
        name="Type",
        items=[
            ('BODY', "Body", "Body marker"),
            ('FACE', "Face", "Facial marker"),
            ('FINGER', "Finger", "Finger marker"),
        ],
        default='BODY',
    )

    @classmethod
    def poll(cls, context):
        """Only available when the wizard is active."""
        session = context.scene.boneforge_autorig_session
        return session.is_active

    def execute(self, context):
        """Mark the named marker as confirmed."""
        session = context.scene.boneforge_autorig_session

        if self.marker_type == 'BODY':
            marker = get_body_marker(session, self.marker_name)
        elif self.marker_type == 'FACE':
            marker = get_face_marker(session, self.marker_name)
        else:
            marker = get_finger_marker(session, self.marker_name)

        if marker is None:
            self.report({'WARNING'}, f"Marker '{self.marker_name}' not found")
            return {'CANCELLED'}

        marker.confirmed = True
        self.report({'INFO'}, f"Confirmed: {self.marker_name}")
        if context.area:
            context.area.tag_redraw()
        return {'FINISHED'}


class BF_OT_WizardConfirmAllGreen(bpy.types.Operator):
    """Confirm all markers that have non-zero positions."""

    bl_idname = "boneforge.autorig_confirm_all_green"
    bl_label = "Confirm All Placed"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """Only available when the wizard is active."""
        session = context.scene.boneforge_autorig_session
        return session.is_active

    def execute(self, context):
        """Bulk-confirm all placed but unconfirmed markers on the current step."""
        session = context.scene.boneforge_autorig_session
        _ensure_marker_slots(session)
        confirmed_count = 0

        if session.wizard_step == STEP_BODY_MARKERS:
            marker_names = BODY_MARKERS
            marker_collection = session.body_markers
        elif session.wizard_step == STEP_FINGER_MARKERS:
            finger_names = FINGER_MARKERS_BY_COUNT.get(session.finger_count, ())
            # Confirm left markers
            for name in finger_names:
                marker = get_finger_marker(session, name)
                if marker is not None and not marker.confirmed and is_position_placed(Vector(marker.position)):
                    marker.confirmed = True
                    confirmed_count += 1
            # Confirm right markers
            for name in finger_names:
                right_name = name.replace('_L', '_R')
                marker = get_finger_marker(session, right_name)
                if marker is not None and not marker.confirmed and is_position_placed(Vector(marker.position)):
                    marker.confirmed = True
                    confirmed_count += 1
        elif session.wizard_step == STEP_FACE_MARKERS:
            marker_names = FACE_MARKERS
            marker_collection = session.face_markers
        else:
            return {'CANCELLED'}

        if session.wizard_step != STEP_FINGER_MARKERS:
            for i in range(len(marker_names)):
                marker = marker_collection[i]
                if not marker.confirmed and is_position_placed(Vector(marker.position)):
                    marker.confirmed = True
                    confirmed_count += 1

        self.report({'INFO'}, f"Confirmed {confirmed_count} markers")
        if context.area:
            context.area.tag_redraw()
        return {'FINISHED'}


class BF_OT_WizardResetMarker(bpy.types.Operator):
    """Reset a single marker back to unplaced state."""

    bl_idname = "boneforge.autorig_reset_marker"
    bl_label = "Reset Marker"
    bl_options = {'REGISTER', 'UNDO'}

    marker_name: StringProperty(options={'HIDDEN', 'SKIP_SAVE'}, name="Marker")
    marker_type: EnumProperty(options={'HIDDEN', 'SKIP_SAVE'},
        name="Type",
        items=[
            ('BODY', "Body", "Body marker"),
            ('FACE', "Face", "Facial marker"),
            ('FINGER', "Finger", "Finger marker"),
        ],
        default='BODY',
    )

    @classmethod
    def poll(cls, context):
        """Only available when the wizard is active."""
        session = context.scene.boneforge_autorig_session
        return session.is_active

    def execute(self, context):
        """Clear this marker's position, confirmation, and confidence."""
        session = context.scene.boneforge_autorig_session
        _ensure_marker_slots(session)

        if self.marker_type == 'BODY':
            marker = get_body_marker(session, self.marker_name)
        elif self.marker_type == 'FACE':
            marker = get_face_marker(session, self.marker_name)
        else:
            marker = get_finger_marker(session, self.marker_name)

        if marker is None:
            self.report({'WARNING'}, f"Marker '{self.marker_name}' not found")
            return {'CANCELLED'}

        marker.position = (0.0, 0.0, 0.0)
        marker.confirmed = False
        marker.confidence = 0.0

        display = self.marker_name.replace('_', ' ').title()
        self.report({'INFO'}, f"Reset {display}")
        if context.area:
            context.area.tag_redraw()
        return {'FINISHED'}


class BF_OT_WizardGenerate(bpy.types.Operator):
    """Generate the rig from confirmed markers."""

    bl_idname = "boneforge.autorig_generate"
    bl_label = "Generate Rig"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """Available on the review or generate steps."""
        session = context.scene.boneforge_autorig_session
        return (session.is_active
                and session.wizard_step in (STEP_REVIEW, STEP_GENERATE))

    def execute(self, context):
        """Run body/face generators and merge into the final rig."""
        session = context.scene.boneforge_autorig_session
        session.wizard_step = STEP_GENERATE

        window_manager = context.window_manager
        window_manager.progress_begin(0, 100)

        _prepare_staging_collection(context)

        body_result = None
        face_result = None

        try:
            body_result = self._run_body_generator(
                context, session, window_manager,
            )
            face_result = self._run_face_generator(
                context, session, window_manager, body_result,
            )
            merge_result = self._run_merge(
                context, session, window_manager, body_result, face_result,
            )
        except Exception as generation_error:
            _cleanup_staging_collection()
            try:
                rollback_scene_changes(session)
            except Exception:
                pass
            window_manager.progress_end()
            self.report({'ERROR'}, f"Generation failed: {generation_error}")
            session.wizard_step = STEP_REVIEW
            return {'CANCELLED'}

        window_manager.progress_end()
        self.report({'INFO'}, merge_result.message)
        if context.area:
            context.area.tag_redraw()
        return {'FINISHED'}

    def _run_body_generator(self, context, session, window_manager):
        """Run body rig generation if needed (0-30% progress)."""
        window_manager.progress_update(0)
        body_result = None

        if session.rig_type in ('BODY_AND_FACE', 'BODY_ONLY'):
            from boneforge.autorig.body_gen import generate_body_rig
            body_result = generate_body_rig(context, session)
            if not body_result.success:
                raise RuntimeError(
                    f"Body generation failed: {body_result.message}"
                )

            # Generate finger rig if finger_count > 0
            if session.finger_count > 0 and body_result and body_result.success:
                from boneforge.autorig.finger_gen import generate_finger_rig
                armature_obj = bpy.data.objects.get(body_result.armature_object_name)
                if armature_obj is not None:
                    hand_bones = {
                        'hand.L': 'hand.L',
                        'hand.R': 'hand.R',
                    }
                    finger_result = generate_finger_rig(
                        context, session, armature_obj, hand_bones,
                    )
                    if finger_result and not finger_result.success:
                        self.report({'WARNING'},
                                    f"Finger generation warning: {finger_result.message}")
                    elif finger_result and finger_result.success:
                        body_result.bone_count += finger_result.bone_count

        window_manager.progress_update(30)
        return body_result

    def _run_face_generator(self, context, session, window_manager, body_result):
        """Run face rig generation if needed (30-50% progress).

        Face failure is non-fatal when a body rig already succeeded.
        """
        face_result = None

        if session.rig_type in ('BODY_AND_FACE', 'FACE_ONLY'):
            from boneforge.autorig.face_gen import generate_face_rig
            face_result = generate_face_rig(context, session)

            if face_result and not face_result.success:
                body_succeeded = (
                    body_result is not None and body_result.success
                )
                if not body_succeeded:
                    raise RuntimeError(
                        f"Face generation failed: {face_result.message}"
                    )
                self.report({'WARNING'}, face_result.message)

        window_manager.progress_update(50)
        return face_result

    def _run_merge(self, context, session, window_manager,
                   body_result, face_result):
        """Merge body/face armatures and finalize (50-100% progress)."""
        from boneforge.autorig.merge import merge_rigs

        merge_result = merge_rigs(context, session, body_result, face_result)
        if not merge_result.success:
            raise RuntimeError(f"Merge failed: {merge_result.message}")

        window_manager.progress_update(95)

        session.wizard_step = STEP_DONE
        # the rig is the result now: nothing it created may be rolled back
        # later (a failed second generate rolled back this run's objects too)
        session.snapshot_blend_data = "{}"
        save_session_backup(context.scene)
        window_manager.progress_update(100)

        return merge_result


# ── Viewport marker drawing ──────────────────────────────────

def _get_marker_color(marker):
    """Return an RGBA tuple for a marker based on its state."""
    if marker.confirmed:
        return _COLOR_CONFIRMED
    if is_position_placed(Vector(marker.position)):
        return _COLOR_UNCONFIRMED
    return _COLOR_UNPLACED


def _build_circle_verts(center, radius, segments=16):
    """Generate vertices for a flat circle in the XZ plane at *center*.

    Used for the 3D marker dot rendered via GPU shader.
    """
    import math
    verts = []
    for i in range(segments):
        angle = 2.0 * math.pi * i / segments
        x = center.x + radius * math.cos(angle)
        z = center.z + radius * math.sin(angle)
        verts.append((x, center.y, z))
    return verts


def _draw_markers_3d():
    """POST_VIEW callback — draw coloured dots at each placed marker."""
    try:
        context = bpy.context
        scene = context.scene
    except Exception:
        return

    session = scene.boneforge_autorig_session
    if not session.is_active:
        return
    if session.wizard_step not in (
        STEP_BODY_MARKERS, STEP_FINGER_MARKERS, STEP_FACE_MARKERS, STEP_REVIEW,
    ):
        return

    mesh_obj = bpy.data.objects.get(session.mesh_object_name)
    if mesh_obj is None:
        return

    diagonal = _compute_mesh_max_dimension(mesh_obj)
    radius = diagonal * _MARKER_DRAW_RADIUS

    shader = gpu.shader.from_builtin('UNIFORM_COLOR')

    # Collect named markers to draw based on current step / rig type.
    named_draw_list = []  # list of (name, marker, pairs, get_fn)
    if session.rig_type in ('BODY_AND_FACE', 'BODY_ONLY'):
        _ensure_marker_slots(session)

        def get_body(n):
            return get_body_marker(session, n)

        for i, name in enumerate(BODY_MARKERS):
            named_draw_list.append(
                (name, session.body_markers[i],
                 BODY_SYMMETRY_PAIRS, get_body))
    if session.rig_type in ('BODY_AND_FACE', 'FACE_ONLY'):
        _ensure_marker_slots(session)

        def get_face(n):
            return get_face_marker(session, n)

        for i, name in enumerate(FACE_MARKERS):
            named_draw_list.append(
                (name, session.face_markers[i],
                 FACE_SYMMETRY_PAIRS, get_face))

    # Draw finger markers
    if session.wizard_step in (STEP_FINGER_MARKERS, STEP_REVIEW):
        _ensure_marker_slots(session)
        finger_marker_names = FINGER_MARKERS_BY_COUNT.get(session.finger_count, ())
        finger_radius = radius * 0.6  # 60% of body marker size

        def get_finger(n):
            return get_finger_marker(session, n)

        for name in finger_marker_names:
            marker = get_finger_marker(session, name)
            if marker is None:
                continue
            named_draw_list.append(
                (name, marker, FINGER_SYMMETRY_PAIRS, get_finger))
        # Also draw right-hand finger markers
        for name in finger_marker_names:
            right_name = name.replace('_L', '_R')
            marker = get_finger_marker(session, right_name)
            if marker is None:
                continue
            named_draw_list.append(
                (right_name, marker, FINGER_SYMMETRY_PAIRS, get_finger))

    gpu.state.blend_set('ALPHA')
    gpu.state.depth_test_set('LESS_EQUAL')

    for name, marker, pairs, get_fn in named_draw_list:
        pos = Vector(marker.position)
        if not is_position_placed(pos):
            continue

        color = _get_marker_color(marker)
        verts = _build_circle_verts(pos, radius)
        # Triangle fan via index pairs from centre
        indices = []
        n = len(verts)
        for idx in range(n):
            indices.append((0, idx, (idx + 1) % n))
        batch = batch_for_shader(
            shader, 'TRIS',
            {"pos": verts},
            indices=indices,
        )
        shader.bind()
        shader.uniform_float("color", color)
        batch.draw(shader)

    # ── Draw symmetry connection lines between paired markers ─
    sym_line_color = (0.6, 0.85, 1.0, 0.4)
    drawn_pairs = set()
    for name, marker, pairs, get_fn in named_draw_list:
        if not marker.symmetry_locked:
            continue
        pair_name = _find_symmetry_pair_name(name, pairs)
        if pair_name is None:
            continue
        pair_key = tuple(sorted((name, pair_name)))
        if pair_key in drawn_pairs:
            continue
        drawn_pairs.add(pair_key)

        pair_marker = get_fn(pair_name)
        if pair_marker is None or not pair_marker.symmetry_locked:
            continue
        pos_a = Vector(marker.position)
        pos_b = Vector(pair_marker.position)
        if not is_position_placed(pos_a) or not is_position_placed(pos_b):
            continue

        line_batch = batch_for_shader(
            shader, 'LINES', {"pos": [tuple(pos_a), tuple(pos_b)]},
        )
        shader.bind()
        shader.uniform_float("color", sym_line_color)
        gpu.state.line_width_set(1.5)
        line_batch.draw(shader)
        gpu.state.line_width_set(1.0)

    # ── Draw live preview dot if placement modal is active ────
    if _preview_position is not None:
        preview_verts = _build_circle_verts(_preview_position, radius * 1.3)
        n = len(preview_verts)
        preview_indices = [(0, idx, (idx + 1) % n) for idx in range(n)]
        preview_batch = batch_for_shader(
            shader, 'TRIS',
            {"pos": preview_verts},
            indices=preview_indices,
        )
        shader.bind()
        shader.uniform_float("color", _COLOR_ACTIVE)
        preview_batch.draw(shader)

    # ── Draw mirrored symmetry preview dot ───────────────────
    if _preview_mirror_position is not None:
        mirror_color = (0.6, 0.85, 1.0, 0.7)  # light blue for mirror
        mirror_verts = _build_circle_verts(
            _preview_mirror_position, radius * 1.1,
        )
        n = len(mirror_verts)
        mirror_indices = [(0, idx, (idx + 1) % n) for idx in range(n)]
        mirror_batch = batch_for_shader(
            shader, 'TRIS',
            {"pos": mirror_verts},
            indices=mirror_indices,
        )
        shader.bind()
        shader.uniform_float("color", mirror_color)
        mirror_batch.draw(shader)

    gpu.state.blend_set('NONE')
    gpu.state.depth_test_set('NONE')


def _draw_markers_2d():
    """POST_PIXEL callback — draw text labels next to each marker."""
    try:
        context = bpy.context
        scene = context.scene
    except Exception:
        return

    session = scene.boneforge_autorig_session
    if not session.is_active:
        return
    if session.wizard_step not in (
        STEP_BODY_MARKERS, STEP_FINGER_MARKERS, STEP_FACE_MARKERS, STEP_REVIEW,
    ):
        return

    region = context.region
    region_data = context.region_data
    if region is None or region_data is None:
        return

    label_pairs = []
    if session.rig_type in ('BODY_AND_FACE', 'BODY_ONLY'):
        _ensure_marker_slots(session)
        for i, name in enumerate(BODY_MARKERS):
            label_pairs.append((name, session.body_markers[i]))
    if session.rig_type in ('BODY_AND_FACE', 'FACE_ONLY'):
        _ensure_marker_slots(session)
        for i, name in enumerate(FACE_MARKERS):
            label_pairs.append((name, session.face_markers[i]))

    if session.wizard_step in (STEP_FINGER_MARKERS, STEP_REVIEW):
        _ensure_marker_slots(session)
        finger_marker_names = FINGER_MARKERS_BY_COUNT.get(session.finger_count, ())
        for name in finger_marker_names:
            marker = get_finger_marker(session, name)
            if marker is not None:
                label_pairs.append((name, marker))
            right_name = name.replace('_L', '_R')
            right_marker = get_finger_marker(session, right_name)
            if right_marker is not None:
                label_pairs.append((right_name, right_marker))

    font_id = 0
    blf.size(font_id, _LABEL_FONT_SIZE)

    for name, marker in label_pairs:
        pos = Vector(marker.position)
        if not is_position_placed(pos):
            continue

        screen_co = view3d_utils.location_3d_to_region_2d(
            region, region_data, pos,
        )
        if screen_co is None:
            continue

        color = _get_marker_color(marker)
        blf.position(font_id, screen_co.x + 12, screen_co.y - 4, 0)
        blf.color(font_id, color[0], color[1], color[2], 1.0)
        blf.draw(font_id, name.replace('_', ' ').title())

    # ── Draw live preview label ──────────────────────────────
    if _preview_position is not None and _preview_marker_name:
        screen_co = view3d_utils.location_3d_to_region_2d(
            region, region_data, _preview_position,
        )
        if screen_co is not None:
            blf.size(font_id, _LABEL_FONT_SIZE + 2)
            blf.position(font_id, screen_co.x + 14, screen_co.y - 4, 0)
            blf.color(font_id, *_COLOR_ACTIVE)
            blf.draw(font_id, _preview_marker_name)

    # ── Draw mirrored symmetry label ─────────────────────────
    if _preview_mirror_position is not None and _preview_mirror_name:
        mirror_screen = view3d_utils.location_3d_to_region_2d(
            region, region_data, _preview_mirror_position,
        )
        if mirror_screen is not None:
            blf.size(font_id, _LABEL_FONT_SIZE + 1)
            blf.position(font_id, mirror_screen.x + 14,
                         mirror_screen.y - 4, 0)
            blf.color(font_id, 0.6, 0.85, 1.0, 0.9)
            blf.draw(font_id, _preview_mirror_name)


# ── Click-to-place modal operator ────────────────────────────

class BF_OT_WizardPlaceMarker(bpy.types.Operator):
    """Click on the mesh in the viewport to place a marker."""

    bl_idname = "boneforge.autorig_place_marker"
    bl_label = "Place Marker"
    bl_options = {'REGISTER', 'UNDO'}

    marker_name: StringProperty(
        name="Marker",
        description="Name of the marker to place",
    )
    marker_type: EnumProperty(options={'HIDDEN', 'SKIP_SAVE'},
        name="Type",
        items=[
            ('BODY', "Body", "Body marker"),
            ('FACE', "Face", "Facial marker"),
            ('FINGER', "Finger", "Finger marker"),
        ],
        default='BODY',
    )

    @classmethod
    def poll(cls, context):
        session = context.scene.boneforge_autorig_session
        return session.is_active

    def invoke(self, context, event):
        """Enter modal mode, or cancel if the same marker is already active."""
        global _preview_position, _preview_marker_name
        global _active_placement_marker, _cancel_active_placement

        # Toggle-off: if this marker is already being placed, signal cancel.
        if _active_placement_marker == self.marker_name:
            _cancel_active_placement = True
            return {'FINISHED'}

        # If a *different* marker modal is running, cancel it first.
        if _active_placement_marker:
            _cancel_active_placement = True

        session = context.scene.boneforge_autorig_session

        # Verify the target mesh is still valid.
        mesh_obj = bpy.data.objects.get(session.mesh_object_name)
        if mesh_obj is None or mesh_obj.type != 'MESH':
            self.report({'WARNING'}, "Target mesh not found")
            return {'CANCELLED'}

        self._mesh_name = session.mesh_object_name
        self._display_name = self.marker_name.replace('_', ' ').title()

        # v3.0.13: find the 3D-viewport WINDOW region so sidebar clicks
        # pass through without cancelling placement mode.  The invoke
        # itself fires from the N-panel button, so context.region here
        # is the UI region — we have to locate the actual 3D viewport
        # by scanning the current window's areas.
        viewport_region = None
        viewport_area = None
        for area in context.window.screen.areas:
            if area.type != 'VIEW_3D':
                continue
            for region in area.regions:
                if region.type == 'WINDOW':
                    viewport_region = region
                    viewport_area = area
                    break
            if viewport_region is not None:
                break

        if viewport_region is None:
            self.report({'WARNING'}, "No 3D viewport open for placement")
            return {'CANCELLED'}

        self._invoke_region = viewport_region
        self._invoke_area = viewport_area

        # Default the axis-lock toolbar based on the selected marker's
        # midline/paired status. User can still toggle any axis afterward.
        _apply_default_axis_lock_for_marker(
            session, self.marker_name, self.marker_type,
        )

        # Initialise live preview state.
        _preview_position = None
        _preview_marker_name = self._display_name
        _active_placement_marker = self.marker_name

        context.window.cursor_modal_set('CROSSHAIR')
        # Set header on the 3D viewport area (not the N-panel area the
        # button lives in). v3.0.13.
        if self._invoke_area is not None:
            self._invoke_area.header_text_set(
                f"Click on mesh to place {self._display_name}  |  "
                f"RMB / Esc / click button again: Cancel"
            )
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        """Handle mouse movement, clicks, and cancellation."""
        global _preview_position, _cancel_active_placement
        global _preview_mirror_position, _preview_mirror_name

        # Check if another invoke requested cancellation (toggle-off).
        if _cancel_active_placement:
            _cancel_active_placement = False
            self._cleanup(context)
            return {'CANCELLED'}

        # ESC is a global cancel — works from any region/cursor position.
        if event.type == 'ESC':
            self._cleanup(context)
            self.report({'INFO'}, "Marker placement cancelled")
            return {'CANCELLED'}

        # v3.0.12 / v3.0.13: let the user click N-panel buttons (axis
        # lock toggles, symmetry, finger count, etc.) without cancelling
        # placement mode. The modal only claims events that occur inside
        # the 3D viewport region it was invoked from; everything else
        # passes through to the normal UI handler. RMB on an N-panel
        # property (e.g. right-click-to-reset) no longer cancels either.
        event_region = getattr(context, 'region', None)
        if event_region is None or event_region != self._invoke_region:
            return {'PASS_THROUGH'}

        # Viewport-only RMB cancel (below the region gate so UI RMB
        # context menus / property resets are untouched).
        if event.type == 'RIGHTMOUSE':
            self._cleanup(context)
            self.report({'INFO'}, "Marker placement cancelled")
            return {'CANCELLED'}

        # Live preview — update the floating marker on every mouse move.
        if event.type == 'MOUSEMOVE':
            hit = self._raycast_mesh(context, event)
            if hit is not None:
                hit = self._apply_axis_constraints(context, hit)
            _preview_position = hit  # None clears the dot when off-mesh

            # Compute mirrored preview if symmetry is locked.
            _preview_mirror_position = None
            _preview_mirror_name = ""
            if hit is not None:
                mirror_info = self._get_mirror_info(context)
                if mirror_info is not None:
                    session = context.scene.boneforge_autorig_session
                    center_x = _get_mesh_center_x(session)
                    _preview_mirror_position = _mirror_x_around_center(
                        hit, center_x,
                    )
                    _preview_mirror_name = mirror_info.replace(
                        '_', ' ').title()

            if context.area is not None:
                context.area.tag_redraw()
            return {'PASS_THROUGH'}

        # Place marker on LMB press.
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            result = self._raycast_mesh(context, event)
            if result is None:
                # Clicking empty space exits placement mode.
                self._cleanup(context)
                return {'CANCELLED'}

            hit_position = self._apply_axis_constraints(context, result)

            # Delegate to the existing MoveMarker operator logic for
            # surface snap, clamping, symmetry, and derived-joint recalc.
            try:
                bpy.ops.boneforge.autorig_move_marker(
                    marker_name=self.marker_name,
                    marker_type=self.marker_type,
                    position=tuple(hit_position),
                )

                # Auto-confirm the marker after placement.
                bpy.ops.boneforge.autorig_confirm_marker(
                    marker_name=self.marker_name,
                    marker_type=self.marker_type,
                )

                # Also auto-confirm the symmetry pair if it was mirrored.
                pair_name = self._get_mirror_info(context)
                if pair_name is not None:
                    bpy.ops.boneforge.autorig_confirm_marker(
                        marker_name=pair_name,
                        marker_type=self.marker_type,
                    )
            finally:
                self._cleanup(context)
            self.report({'INFO'},
                        f"Placed {self._display_name}")
            return {'FINISHED'}

        return {'PASS_THROUGH'}

    # ── Internal helpers ─────────────────────────────────────

    def _raycast_mesh(self, context, event):
        """Cast a ray from the mouse position through the viewport.

        Returns the world-space hit ``Vector`` or ``None`` on miss.
        """
        region = context.region
        region_data = context.space_data.region_3d
        if region is None or region_data is None:
            return None

        coord = (event.mouse_region_x, event.mouse_region_y)
        origin = view3d_utils.region_2d_to_origin_3d(
            region, region_data, coord,
        )
        direction = view3d_utils.region_2d_to_vector_3d(
            region, region_data, coord,
        )

        # Use scene ray_cast (respects depsgraph transforms).
        depsgraph = context.evaluated_depsgraph_get()
        hit, location, normal, face_index, hit_obj, matrix = (
            context.scene.ray_cast(depsgraph, origin, direction)
        )

        if not hit:
            return None

        # Only accept hits on the wizard's target mesh (or its evaluated
        # duplicate).
        if hit_obj is not None:
            source_name = hit_obj.name.split('.')[0]
            target_name = self._mesh_name.split('.')[0]
            if source_name != target_name:
                return None

        return Vector(location)

    def _apply_axis_constraints(self, context, position):
        """Lock axes the user disabled, keeping the marker's prior value."""
        session = context.scene.boneforge_autorig_session
        if self.marker_type == 'BODY':
            prev_marker = get_body_marker(session, self.marker_name)
        else:
            prev_marker = get_face_marker(session, self.marker_name)

        constrained = Vector(position)
        if prev_marker is not None:
            prev = Vector(prev_marker.position)
            if not session.placement_axis_x:
                constrained.x = prev.x
            if not session.placement_axis_y:
                constrained.y = prev.y
            if not session.placement_axis_z:
                constrained.z = prev.z
        return constrained

    def _get_mirror_info(self, context):
        """Return the symmetry pair marker name if mirroring is active.

        Checks that both the current marker and its pair have
        ``symmetry_locked`` enabled.  Returns ``None`` when no mirror
        should be shown.
        """
        session = context.scene.boneforge_autorig_session
        if self.marker_type == 'BODY':
            pairs = BODY_SYMMETRY_PAIRS

            def get_fn(n):
                return get_body_marker(session, n)
        else:
            pairs = FACE_SYMMETRY_PAIRS

            def get_fn(n):
                return get_face_marker(session, n)

        pair_name = _find_symmetry_pair_name(self.marker_name, pairs)
        if pair_name is None:
            return None

        source_marker = get_fn(self.marker_name)
        pair_marker = get_fn(pair_name)
        if (source_marker is not None and source_marker.symmetry_locked
                and pair_marker is not None and pair_marker.symmetry_locked):
            return pair_name
        return None

    def _cleanup(self, context):
        """Restore cursor, header text, and clear live preview."""
        global _preview_position, _preview_marker_name
        global _active_placement_marker, _cancel_active_placement
        global _preview_mirror_position, _preview_mirror_name

        # Only clear shared state if we're still the active placement;
        # a newer modal may have already taken ownership of these globals.
        if _active_placement_marker == self.marker_name:
            _preview_position = None
            _preview_marker_name = ""
            _preview_mirror_position = None
            _preview_mirror_name = ""
            _active_placement_marker = ""
            _cancel_active_placement = False

        context.window.cursor_modal_restore()
        # v3.0.13: clear header on the viewport area we actually set it
        # on, not whatever random area happened to be under the cursor
        # when the modal ended.
        invoke_area = getattr(self, '_invoke_area', None)
        if invoke_area is not None:
            invoke_area.header_text_set(None)
            invoke_area.tag_redraw()
        elif context.area is not None:
            context.area.header_text_set(None)
            context.area.tag_redraw()


# ── Panel ─────────────────────────────────────────────────────

class BF_PT_WizardPanel(bpy.types.Panel):
    """Auto-rig wizard panel in the 3D viewport sidebar.

    v3.8.0: bl_category moved from "BoneCraft" to "Rig Builder" so the
    standalone wizard panel surfaces in the new Rig Builder tab.
    The sidebar wrapper BF_PT_sb_wizard delegates to this panel and
    is parented under BF_PT_rb_setup.
    """

    bl_idname = "BONEFORGE_PT_autorig_wizard"
    bl_label = " "
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rig Builder"
    # Negative bl_order forces this panel above every other panel in
    # the Rig Builder tab.
    bl_order = -100

    def draw_header(self, context):
        self.layout.label(text=T("Auto-Rig Wizard"))

    def draw(self, context):
        """Draw the wizard panel, dispatching to the active step."""
        layout = self.layout
        session = context.scene.boneforge_autorig_session

        # Attempt crash recovery from JSON backup
        if not session.is_active and session.wizard_step == STEP_INACTIVE:
            if restore_session_backup(context.scene):
                if session.is_active:
                    layout.label(
                        text=(
                            f"Resuming from Step {session.wizard_step} — "
                            f"{STEP_LABELS.get(session.wizard_step, '')}"
                        ),
                        icon='INFO',
                    )

        # Inactive state — show start button
        if not session.is_active:
            layout.operator("boneforge.autorig_wizard_start",
                            text=T("Start Auto-Rig"), icon='OUTLINER_OB_ARMATURE')
            return

        # Step indicator header with dynamic step count
        step = session.wizard_step
        label = STEP_LABELS.get(step, f"Step {step}")
        visible_step, total_steps = _visible_step_number(
            step, session.rig_type, finger_count=session.finger_count,
        )
        header = layout.box()
        header.label(
            text=f"Step {visible_step}/{total_steps}: {label}",
        )

        if step < STEP_DONE:    # Done has its own Close Wizard button
            navigation_row = header.row(align=True)
            navigation_row.operator("boneforge.autorig_wizard_back",
                                    text=T("Back"), icon='BACK')
            navigation_row.operator("boneforge.autorig_wizard_cancel",
                                    text=T("Cancel"), icon='CANCEL')
        layout.separator()

        # Dispatch to step-specific drawing
        # Use BF_PT_WizardPanel explicitly so delegate-draw (where self is
        # a different panel class) does not cause AttributeError lookups.
        WP = BF_PT_WizardPanel
        step_draw_methods = {
            STEP_SELECT_MESH:    WP._draw_step_mesh,
            STEP_RIG_TYPE:       WP._draw_step_rig_type,
            STEP_BODY_MARKERS:   WP._draw_step_body_markers,
            STEP_FINGER_MARKERS: WP._draw_step_finger_markers,
            STEP_FACE_MARKERS:   WP._draw_step_face_markers,
            STEP_REVIEW:         WP._draw_step_review,
            STEP_GENERATE:       WP._draw_step_generating,
            STEP_DONE:           WP._draw_step_done,
        }
        draw_method = step_draw_methods.get(step)
        if draw_method is not None:
            draw_method(self, layout, context, session)

        # Next button — hidden on Review (use Generate Rig), Generate,
        # and Done steps.
        if step < STEP_DONE and step not in (STEP_GENERATE, STEP_REVIEW):
            layout.separator()
            layout.operator("boneforge.autorig_wizard_next",
                            text=T("Next"), icon='FORWARD')

    # ── Step drawing methods ──────────────────────────────────

    def _draw_step_mesh(self, layout, context, session):
        """Draw Step 1: mesh selection."""
        layout.label(text=T("Select the mesh to rig:"))

        col = layout.column(align=True)
        for obj in context.scene.objects:
            if obj.type != 'MESH':
                continue
            is_selected = obj.name == session.mesh_object_name
            icon = 'RADIOBUT_ON' if is_selected else 'RADIOBUT_OFF'
            op = col.operator("boneforge.autorig_select_mesh",
                              text=obj.name, icon=icon)
            op.mesh_name = obj.name

        if session.mesh_object_name:
            layout.label(text=f"Selected: {session.mesh_object_name}",
                         icon='CHECKMARK')

    def _draw_step_rig_type(self, layout, context, session):
        """Draw Step 2: rig type selection."""
        layout.label(text=T("What should be generated?"))

        col = layout.column(align=True)
        for item_id, item_label, item_description in RIG_TYPE_ITEMS:
            is_selected = session.rig_type == item_id
            icon = 'RADIOBUT_ON' if is_selected else 'RADIOBUT_OFF'
            op = col.operator("boneforge.autorig_set_rig_type",
                              text=item_label, icon=icon)
            op.rig_type = item_id

        # ── Rig generation options ────────────────────────────
        layout.separator()
        options_box = layout.box()
        options_box.label(text=T("Generation Options:"))

        # IK/FK mode
        options_box.prop(session, "rig_mode", text=T("Kinematics"))

        # Controller generation
        options_box.prop(session, "generate_controllers",
                         text=T("Generate Control Shapes"))

    def _draw_placement_toolbar(self, layout, session):
        """Draw the shared placement toolbar: viewport helpers + axis constraint."""
        # v3.0.17: Simplified viewport display panel — quick access to the
        # rigging-relevant viewport toggles without hunting through N-panel tabs.
        BF_PT_WizardPanel._draw_viewport_tools(self, layout, session)

        # Axis constraint toggles
        axis_box = layout.box()
        axis_row = axis_box.row(align=True)
        axis_row.label(text=T("Axis Lock:"))
        axis_row.prop(session, "placement_axis_x", toggle=True)
        axis_row.prop(session, "placement_axis_y", toggle=True)
        axis_row.prop(session, "placement_axis_z", toggle=True)
        layout.separator()

    def _draw_viewport_tools(self, layout, session):
        """Draw a collapsible simplified viewport-display panel.

        Exposes the display toggles that professional riggers use most
        (bone shape, names, axes, x-ray, in-front, wireframes) without
        making users dig through the Properties editor.  Each prop binds
        directly to the underlying datablock — no session state needed.
        """
        import bpy  # local import; bpy is always loaded when this draws

        box = layout.box()
        header = box.row(align=True)
        header.prop(
            session, "viewport_tools_expanded",
            icon='TRIA_DOWN' if session.viewport_tools_expanded else 'TRIA_RIGHT',
            emboss=False, text=T("Viewport Display"),
        )
        if not session.viewport_tools_expanded:
            return

        # Find the active armature to drive armature-specific toggles
        armature_obj = None
        ob = bpy.context.active_object
        if ob is not None and ob.type == 'ARMATURE':
            armature_obj = ob
        else:
            for candidate in bpy.context.selected_objects:
                if candidate.type == 'ARMATURE':
                    armature_obj = candidate
                    break

        # Armature display
        if armature_obj is not None:
            arm_col = box.column(align=True)
            arm_col.label(text=T("Armature:"))
            arm_col.prop(armature_obj.data, "display_type", text=T("Shape"))
            row = arm_col.row(align=True)
            row.prop(armature_obj, "show_in_front", text=T("In Front"), toggle=True)
            row.prop(armature_obj.data, "show_names", text=T("Names"), toggle=True)
            row = arm_col.row(align=True)
            row.prop(armature_obj.data, "show_axes", text=T("Axes"), toggle=True)
            row.prop(armature_obj, "show_wire", text=T("Wire"), toggle=True)
        else:
            box.label(text=T("(no armature active)"), icon='INFO')

        # Viewport shading / overlays — look up the active 3D view
        space_data = None
        try:
            for area in bpy.context.window.screen.areas:
                if area.type == 'VIEW_3D':
                    space_data = area.spaces.active
                    break
        except (AttributeError, TypeError):
            space_data = None

        if space_data is not None and hasattr(space_data, 'shading'):
            vp_col = box.column(align=True)
            vp_col.label(text=T("Viewport:"))
            row = vp_col.row(align=True)
            row.prop(space_data.shading, "show_xray", text=T("X-Ray"), toggle=True)
            if hasattr(space_data, 'overlay'):
                row.prop(space_data.overlay, "show_wireframes",
                         text=T("Wireframe"), toggle=True)

        # Perf hint — "In Front" is a known slowdown on dense meshes
        if armature_obj is not None and armature_obj.show_in_front:
            hint = box.row()
            hint.label(text=T("In-Front redraws every frame — toggle off if laggy."),
                       icon='INFO')
        layout.separator()

    def _draw_step_body_markers(self, layout, context, session):
        """Draw Step 3: body marker placement."""
        _ensure_marker_slots(session)
        layout.label(text=T("Place body markers on the mesh:"))

        # v3.0.14: geometric guess — analyses mesh extremes, symmetry,
        # and cross-sections to place the 7 core body markers
        # automatically.  Works best on humanoid T-pose meshes.
        # v3.0.22: precision markers now have their own button in the
        # Optional section below; this button only places the required
        # core 7.
        guess_row = layout.row()
        op = guess_row.operator(
            "boneforge.autorig_guess_body_markers",
            text=T("Guess Markers from Mesh"),
            icon='SHADERFX',
        )
        op.mode = 'CORE'
        layout.separator()
        BF_PT_WizardPanel._draw_smart_detection(self, layout, session)
        layout.separator()

        # Mirror toggle — lets user disable auto-mirroring for asymmetric rigs
        mirror_row = layout.row(align=True)
        mirror_icon = 'MOD_MIRROR' if session.body_symmetry_enabled else 'UNLINKED'
        mirror_row.prop(session, "body_symmetry_enabled", text=T("Mirror Symmetry"),
                        toggle=True, icon=mirror_icon)
        layout.separator()

        BF_PT_WizardPanel._draw_placement_toolbar(self, layout, session)

        BF_PT_WizardPanel._draw_marker_list(
            self, layout, session,
            BODY_MARKERS, session.body_markers,
            BODY_SYMMETRY_PAIRS, _BODY_PAIRED_MARKERS,
            marker_type='BODY',
        )

    def _draw_smart_detection(self, layout, session):
        """Draw smart body-marker detection controls and confidence summary."""
        box = layout.box()
        box.label(text=T("Smart Detection"))

        row = box.row(align=True)
        row.scale_y = 1.1
        row.operator("boneforge.autorig_run_detection",
                     text=T("Detect Markers"), icon='SHADERFX')

        row = box.row(align=True)
        row.operator("boneforge.autorig_accept_high",
                     text=T("Accept High"), icon='CHECKMARK')
        row.operator("boneforge.autorig_reset_low",
                     text=T("Reset Low"), icon='LOOP_BACK')

        mirror_row = box.row(align=True)
        op = mirror_row.operator("boneforge.autorig_mirror_confirmed",
                                 text=T("Mirror L to R"), icon='MOD_MIRROR')
        op.from_side = 'LEFT'
        op = mirror_row.operator("boneforge.autorig_mirror_confirmed",
                                 text=T("Mirror R to L"), icon='MOD_MIRROR')
        op.from_side = 'RIGHT'

        counts = {'CONFIRMED': 0, 'REVIEW': 0, 'ADJUST': 0}
        detected = 0
        for marker in session.body_markers:
            score = float(getattr(marker, "confidence", 0.0) or 0.0)
            if score > 0.0:
                detected += 1
            counts[confidence_category(score)] += 1

        summary = box.row(align=True)
        if detected:
            for category in ('CONFIRMED', 'REVIEW', 'ADJUST'):
                summary.label(text="%s %d" % (category, counts[category]),
                              icon=_confidence_icon(category))
        else:
            summary.label(text=T("No detection results yet"), icon='INFO')

    def _draw_step_finger_markers(self, layout, context, session):
        """Draw Step: finger marker placement."""
        _ensure_marker_slots(session)

        # Finger count selector — vertical with descriptive labels so
        # users know what each option means without having to guess.
        # v3.0.23: labels restored to "No Fingers / Sock Puppet /
        # Mitten / Mitten + Index / Full Hand" wording.
        layout.label(text=T("Finger Detail:"))
        count_col = layout.column(align=True)
        for count_val, count_label, count_desc in FINGER_COUNT_ITEMS:
            is_selected = session.finger_count == count_val
            icon = 'RADIOBUT_ON' if is_selected else 'RADIOBUT_OFF'
            # Prefix numeric count to the descriptive label.
            btn_text = f"{count_val} — {count_label}"
            op = count_col.operator(
                "boneforge.autorig_set_finger_count",
                text=btn_text, icon=icon,
            )
            op.finger_count = count_val

        if session.finger_count == 0:
            box = layout.box()
            box.label(text=T("No finger bones will be generated."),
                      icon='INFO')
            box.label(text=T("Wrist will be a terminal bone."))
            box.label(text=T("Click Next to continue."))
            return

        layout.separator()

        # Symmetry toggle
        sym_row = layout.row()
        sym_row.prop(session, "finger_symmetry",
                     text=T("Mirror left hand to right"),
                     icon='MOD_MIRROR')

        if not session.finger_symmetry:
            layout.prop(session, "finger_active_hand", text=T("Active Hand"))

        layout.separator()

        # v3.0.18: approximate finger guess from wrist + hand extremes
        layout.separator()
        guess_row = layout.row()
        guess_row.operator(
            "boneforge.autorig_guess_finger_markers",
            text=T("Guess Finger Markers"),
            icon='SHADERFX',
        )
        layout.separator()

        # Instruction text
        marker_names = FINGER_MARKERS_BY_COUNT.get(session.finger_count, ())
        layout.label(text=f"Place {len(marker_names)} markers per hand:")

        # Marker checklist — left hand
        box = layout.box()
        box.label(text=T("Left Hand:"))
        for name in marker_names:
            marker = get_finger_marker(session, name)
            if marker is None:
                continue
            icon = _get_marker_status_icon(marker)
            base_name = name.replace('FINGER_', '').replace('_L', '')
            display = FINGER_MARKER_LABELS.get(
                'FINGER_' + base_name, base_name.replace('_', ' ').title(),
            )
            row = box.row(align=True)
            row.label(text=display, icon=icon)

            marker_position = Vector(marker.position)
            if is_position_placed(marker_position):
                row.label(text=f"({marker_position.x:.2f}, {marker_position.y:.2f}, {marker_position.z:.2f})")

            if not marker.confirmed:
                op = row.operator("boneforge.autorig_place_marker",
                                  text="", icon='EYEDROPPER')
                op.marker_name = name
                op.marker_type = 'FINGER'

            if not marker.confirmed and is_position_placed(marker_position):
                op = row.operator("boneforge.autorig_confirm_marker",
                                  text="", icon='CHECKMARK')
                op.marker_name = name
                op.marker_type = 'FINGER'

            if is_position_placed(marker_position) or marker.confirmed:
                op = row.operator("boneforge.autorig_reset_marker",
                                  text="", icon='LOOP_BACK')
                op.marker_name = name
                op.marker_type = 'FINGER'

        # Right hand section
        if session.finger_symmetry:
            layout.separator()
            mirror_box = layout.box()
            mirror_box.label(text=T("Right Hand (mirrored):"))
            for name in marker_names:
                right_name = name.replace('_L', '_R')
                marker = get_finger_marker(session, right_name)
                if marker is None:
                    continue
                base_name = name.replace('FINGER_', '').replace('_L', '')
                display = FINGER_MARKER_LABELS.get(
                    'FINGER_' + base_name, base_name.replace('_', ' ').title(),
                )
                row = mirror_box.row(align=True)
                is_placed = is_position_placed(Vector(marker.position))
                icon = 'CHECKMARK' if is_placed else 'DOT'
                row.label(text=display, icon=icon)
        else:
            # Independent right hand placement
            layout.separator()
            right_box = layout.box()
            right_box.label(text=T("Right Hand:"))
            for name in marker_names:
                right_name = name.replace('_L', '_R')
                marker = get_finger_marker(session, right_name)
                if marker is None:
                    continue
                icon = _get_marker_status_icon(marker)
                base_name = name.replace('FINGER_', '').replace('_L', '')
                display = FINGER_MARKER_LABELS.get(
                    'FINGER_' + base_name, base_name.replace('_', ' ').title(),
                )
                row = right_box.row(align=True)
                row.label(text=display, icon=icon)

                if not marker.confirmed:
                    op = row.operator("boneforge.autorig_place_marker",
                                      text="", icon='EYEDROPPER')
                    op.marker_name = right_name
                    op.marker_type = 'FINGER'

        # Bulk confirm
        layout.separator()
        layout.operator("boneforge.autorig_confirm_all_green",
                        text=T("Confirm All Placed"), icon='CHECKBOX_HLT')

    def _draw_step_face_markers(self, layout, context, session):
        """Draw Step 4: facial marker placement."""
        _ensure_marker_slots(session)
        layout.label(text=T("Place facial markers:"))

        # v3.0.18: proportion-based face guess
        guess_row = layout.row()
        guess_row.operator(
            "boneforge.autorig_guess_face_markers",
            text=T("Guess Face Markers"),
            icon='SHADERFX',
        )
        layout.separator()

        # Mirror toggle for face markers
        mirror_row = layout.row(align=True)
        mirror_icon = 'MOD_MIRROR' if session.face_symmetry_enabled else 'UNLINKED'
        mirror_row.prop(session, "face_symmetry_enabled", text=T("Mirror Symmetry"),
                        toggle=True, icon=mirror_icon)
        layout.separator()

        BF_PT_WizardPanel._draw_placement_toolbar(self, layout, session)

        BF_PT_WizardPanel._draw_marker_list(
            self, layout, session,
            FACE_MARKERS, session.face_markers,
            FACE_SYMMETRY_PAIRS, _FACE_PAIRED_MARKERS,
            marker_type='FACE',
        )

    def _draw_marker_list(self, layout, session,
                          marker_names, marker_collection,
                          symmetry_pairs, paired_set,
                          marker_type):
        """Draw a list of markers with status icons, symmetry toggles, and confirm buttons.

        Shared between body and face marker steps to eliminate duplication.
        For body markers, optional precision markers (shoulder, elbow, knee)
        are shown in a separate section with an "Optional" header.

        Args:
            layout: Blender UI layout.
            session: Active wizard session.
            marker_names: Tuple of marker name strings.
            marker_collection: The marker PropertyGroup collection.
            symmetry_pairs: Tuple of (left, right) pairs.
            paired_set: Frozenset of all names that belong to a pair.
            marker_type: ``'BODY'`` or ``'FACE'``.
        """
        use_box = (marker_type == 'BODY')
        optional_set = frozenset(OPTIONAL_BODY_MARKERS) if marker_type == 'BODY' else frozenset()
        shown_optional_header = False

        for i, name in enumerate(marker_names):
            marker = marker_collection[i]
            icon = _get_marker_status_icon(marker)

            # Show a separator + header before the first optional marker
            if name in optional_set and not shown_optional_header:
                layout.separator()
                row = layout.row()
                row.label(text=T("Precision Markers (Optional)"))
                # v3.0.22: dedicated precision-guess button next to the
                # header so users can skip or accept the precision pass
                # independently of the core marker guess.
                guess_op = row.operator(
                    "boneforge.autorig_guess_body_markers",
                    text=T("Guess Precision"),
                    icon='SHADERFX',
                )
                guess_op.mode = 'PRECISION'
                shown_optional_header = True

            container = layout.box() if use_box else layout
            row = container.row(align=True)
            display_name = name.replace('_', ' ').title()
            if name in optional_set:
                display_name = f"{display_name}"
            row.label(text=display_name, icon=icon)

            # Position display
            marker_position = Vector(marker.position)
            if is_position_placed(marker_position):
                row.label(
                    text=(
                        f"({marker_position.x:.2f}, "
                        f"{marker_position.y:.2f}, "
                        f"{marker_position.z:.2f})"
                    ),
                )

            if marker_type == 'BODY':
                category = confidence_category(
                    float(getattr(marker, "confidence", 0.0) or 0.0)
                )
                row.label(text=category, icon=_confidence_icon(category))

            # Symmetry toggle (only for paired markers)
            if name in paired_set:
                sym_icon = (
                    'MOD_MIRROR' if marker.symmetry_locked
                    else 'MOD_MESHDEFORM'
                )
                op = row.operator("boneforge.autorig_toggle_symmetry",
                                  text="", icon=sym_icon)
                op.marker_name = name
                op.marker_type = marker_type

            # Place button — invokes the click-to-place modal
            if not marker.confirmed:
                op = row.operator("boneforge.autorig_place_marker",
                                  text="", icon='EYEDROPPER')
                op.marker_name = name
                op.marker_type = marker_type

            # Confirm button
            if not marker.confirmed and is_position_placed(marker_position):
                op = row.operator("boneforge.autorig_confirm_marker",
                                  text="", icon='CHECKMARK')
                op.marker_name = name
                op.marker_type = marker_type

            # Per-marker reset button (show if placed or confirmed)
            if is_position_placed(marker_position) or marker.confirmed:
                op = row.operator("boneforge.autorig_reset_marker",
                                  text="", icon='LOOP_BACK')
                op.marker_name = name
                op.marker_type = marker_type

        # Bulk confirm
        layout.separator()
        layout.operator("boneforge.autorig_confirm_all_green",
                        text=T("Confirm All Placed"), icon='CHECKBOX_HLT')

    def _draw_step_review(self, layout, context, session):
        """Draw Step: review, generation options, and Generate button."""
        layout.label(text=T("Review marker placement:"))

        warnings = _run_review_validation(session)
        if warnings:
            box = layout.box()
            box.label(text=T("Warnings:"), icon='ERROR')
            for warning in warnings:
                box.label(text=warning, icon='DOT')
        else:
            layout.label(text=T("All checks passed"), icon='CHECKMARK')

        # ── Generation options ────────────────────────────────
        layout.separator()
        options_box = layout.box()
        options_box.label(text=T("Generation Options:"))
        options_box.prop(session, "rig_mode", text=T("Kinematics"))
        options_box.prop(session, "generate_controllers",
                         text=T("Generate Control Shapes"))

        # ── Controller density ────────────────────────────────
        layout.separator()
        density_box = layout.box()
        density_box.label(text=T("Controller Density:"))

        col = density_box.column(align=True)
        col.prop(session, "spine_segments")
        col.prop(session, "neck_segments")

        density_box.separator()
        density_box.prop(session, "twist_bones")
        if session.twist_bones:
            row = density_box.row()
            row.separator(factor=2.0)
            row.prop(session, "twist_segments")

        density_box.prop(session, "skirt_bones")
        if session.rig_type == "BODY_AND_FACE":
            density_box.prop(session, "face_controls")

        # Skinning options (these settings existed but were never shown)
        skin = getattr(session, "skinning_settings", None)
        if skin is not None:
            skin_box = layout.box()
            skin_box.label(text=T("Skinning:"))
            skin_box.prop(skin, "quality_target")
            skin_box.prop(skin, "preserve_volume")
            skin_box.prop(skin, "joint_correctives")

        # Finger count display
        finger_label = "None"
        for val, label, desc in FINGER_COUNT_ITEMS:
            if val == session.finger_count:
                finger_label = label
                break
        density_box.label(text=f"Fingers: {finger_label}")

        # ── Generate button ───────────────────────────────────
        layout.separator()
        layout.operator("boneforge.autorig_generate",
                        text=T("Generate Rig"), icon='OUTLINER_OB_ARMATURE')

    def _draw_step_generating(self, layout, context, session):
        """Draw Step 6: generation in progress."""
        layout.label(text=T("Generating rig..."))

    def _draw_step_done(self, layout, context, session):
        """Draw Step 7: completion summary."""
        layout.label(text=T("Rig generated successfully!"), icon='CHECKMARK')

        if session.generated_final_armature:
            layout.label(
                text=f"Armature: {session.generated_final_armature}",
            )

        layout.separator()

        # Integration checklist
        box = layout.box()
        box.label(text=T("Integrations:"))
        armature_obj = bpy.data.objects.get(session.generated_final_armature)
        if armature_obj is not None:
            box.label(text=T("Rigify-compatible bone names"),
                      icon='CHECKMARK')
            if hasattr(armature_obj, 'boneforge_settings'):
                box.label(text=T("Collection UI populated"),
                          icon='CHECKMARK')
            if hasattr(armature_obj, 'boneforge_bookmark_settings'):
                box.label(text=T("Visibility bookmarks created"),
                          icon='CHECKMARK')

        layout.separator()

        # v3.8.0: cross-tab handoff hint. The user just finished a
        # creation workflow in the Rig Builder tab; the next likely
        # actions live on the BoneForge tab.
        box2 = layout.box()
        box2.label(text=T("Next Steps:"))
        box2.label(text=T("Switch to the BoneCraft tab for posing,"))
        box2.label(text=T("weight tools, and VRChat optimization."))
        box2.label(text=T("Retarget and Cats cleanup all live there."))

        # Optional mannequin offer — useful right after generation
        # if the user has no mesh yet.
        layout.separator(factor=0.5)
        mannequin_box = layout.box()
        mannequin_box.scale_y = 0.9
        mannequin_box.label(
            text=T("No mesh yet? Add a Mannequin to preview deformation."),
            icon='INFO',
        )
        mannequin_box.operator(
            "boneforge.quick_mannequin",
            text=T("Quick Mannequin"),
            icon='OUTLINER_OB_MESH',
        )

        # Engine control rig: reads the review-step options, which Close
        # Wizard resets, so it is offered here before closing.
        layout.separator()
        rig_box = layout.box()
        rig_box.label(text=T("Twist/Skirt Bones, Face Controls, Joint Correctives:"))
        rig_box.operator("boneforge.autorig_build_control_rig",
                         text=T("Build Control Rig"), icon='CONSTRAINT_BONE')

        # Close wizard
        layout.separator()
        layout.operator("boneforge.autorig_wizard_cancel",
                        text=T("Close Wizard"), icon='CANCEL')


class BF_OT_WizardSetFingerCount(bpy.types.Operator):
    """Set the finger count for auto-rigging."""

    bl_idname = "boneforge.autorig_set_finger_count"
    bl_label = "Set Finger Count"
    bl_options = {'REGISTER'}

    finger_count: IntProperty(
        name="Finger Count",
        description="Number of fingers per hand",
        default=5, min=0, max=5,
    )

    _FINGER_COUNT_TOOLTIPS = {
        0: 'No fingers — wrist bone only, no finger bones generated',
        1: 'Single bone — whole hand as one solid "sock puppet"',
        2: 'Thumb + four-finger group — "mitten mode"',
        3: 'Thumb, index, and remaining three as a group — "one finger mitten mode"',
        5: 'Full hand — individual thumb, index, middle, ring, and pinky (3 bones each)',
    }

    @classmethod
    def description(cls, context, properties):
        return cls._FINGER_COUNT_TOOLTIPS.get(
            properties.finger_count,
            "Number of fingers per hand",
        )

    @classmethod
    def poll(cls, context):
        session = context.scene.boneforge_autorig_session
        return session.is_active

    def execute(self, context):
        session = context.scene.boneforge_autorig_session
        old_count = session.finger_count
        session.finger_count = self.finger_count

        # Clear finger markers when count changes
        if old_count != self.finger_count:
            _ensure_marker_slots(session)
            for i in range(len(session.finger_markers)):
                marker = session.finger_markers[i]
                marker.position = (0.0, 0.0, 0.0)
                marker.confirmed = False
                marker.confidence = 0.0

        if context.area:
            context.area.tag_redraw()
        self.report({'INFO'}, f"Finger count: {self.finger_count}")
        return {'FINISHED'}


# ── Marker guessing (v3.0.14) ─────────────────────────────────

def _guess_body_markers_from_mesh(mesh_obj):
    """Infer body marker world-space positions from a mesh.

    v3.0.18: Extended to return all 19 body markers (7 core + 12 optional
    precision markers: shoulders, elbows, hips, knees, toes, heels).
    Uses improved wrist/ankle detection via cross-section analysis, and
    derives precision markers from the core landmarks using anatomical
    proportions.

    Assumptions (standard humanoid convention):
      - Mesh is roughly symmetric about X = (min_x + max_x) / 2
      - Character faces +Y (Blender convention) or is Y-neutral
      - Up axis is +Z
      - T-pose or A-pose with arms extended laterally

    Returns:
        dict[str, Vector] keyed by marker name. Empty if the mesh
        has no vertices.
    """
    world = mesh_obj.matrix_world
    world_verts = [world @ vertex.co for vertex in mesh_obj.data.vertices]
    if not world_verts:
        return {}

    min_x = min(vertex.x for vertex in world_verts)
    max_x = max(vertex.x for vertex in world_verts)
    min_y = min(vertex.y for vertex in world_verts)
    max_y = max(vertex.y for vertex in world_verts)
    min_z = min(vertex.z for vertex in world_verts)
    max_z = max(vertex.z for vertex in world_verts)

    center_x = (min_x + max_x) * 0.5
    center_y = (min_y + max_y) * 0.5
    height = max(max_z - min_z, 1e-6)
    width = max(max_x - min_x, 1e-6)

    # HEAD_TOP — highest vertex on the mesh.
    head_top = max(world_verts, key=lambda v: v.z)

    # WRIST detection — the extreme ±X vertex is the fingertip, NOT the
    # wrist.  Walk inward from the fingertip in X and find the slice
    # with the smallest cross-section (Y + Z extent combined) — that's
    # the wrist's anatomical "narrow point".
    def _find_wrist(fingertip_x):
        """Walk X-slices inward from fingertip_x toward center_x and
        return the narrowest (Vector) position along the way."""
        arm_span = fingertip_x - center_x
        if abs(arm_span) < 1e-3:
            return Vector((fingertip_x, center_y, (min_z + max_z) * 0.5))

        # Only consider upper half (arms are above pelvis in T-pose).
        upper_verts = [v for v in world_verts if v.z > min_z + 0.50 * height]
        if len(upper_verts) < 20:
            upper_verts = world_verts

        band_width = abs(arm_span) * 0.025  # slice thickness
        best_pos = Vector((fingertip_x, center_y, (min_z + max_z) * 0.5))
        best_cross = float('inf')

        # Scan from 8% to 40% of the way from fingertip toward centre.
        for step in range(8, 41, 2):
            slice_x = fingertip_x - arm_span * (step / 100.0)
            slice_verts = [v for v in upper_verts
                           if abs(v.x - slice_x) < band_width]
            if len(slice_verts) < 4:
                continue
            y_span = max(v.y for v in slice_verts) - min(v.y for v in slice_verts)
            z_span = max(v.z for v in slice_verts) - min(v.z for v in slice_verts)
            cross = y_span + z_span
            if cross < best_cross:
                best_cross = cross
                best_pos = Vector((
                    slice_x,
                    sum(v.y for v in slice_verts) / len(slice_verts),
                    sum(v.z for v in slice_verts) / len(slice_verts),
                ))
        return best_pos

    wrist_left = _find_wrist(max_x)
    wrist_right = _find_wrist(min_x)

    # NECK_BASE — scan horizontal-slice widths from top down; the
    # first slice materially wider than the narrowest upper slice
    # is the shoulder line.  Neck Z sits just above it.
    slice_count = 80
    slice_x_values = [[] for _ in range(slice_count)]
    slice_y_values = [[] for _ in range(slice_count)]
    for world_vertex in world_verts:
        normalised = (world_vertex.z - min_z) / height
        slice_index = min(int(normalised * slice_count), slice_count - 1)
        slice_x_values[slice_index].append(world_vertex.x)
        slice_y_values[slice_index].append(world_vertex.y)

    slice_widths = [
        (max(xs) - min(xs)) if xs else 0.0
        for xs in slice_x_values
    ]

    upper_start = int(slice_count * 0.75)
    upper_widths = [w for w in slice_widths[upper_start:] if w > 0.0]
    head_width = min(upper_widths) if upper_widths else 0.0
    shoulder_threshold = head_width * 1.8

    neck_z = None
    if shoulder_threshold > 0.0:
        for slice_index in range(slice_count - 1, upper_start - 1, -1):
            if slice_widths[slice_index] > shoulder_threshold:
                neck_z = min_z + (slice_index / slice_count) * height
                break
    if neck_z is None:
        # Fallback: standard anatomical proportion.
        neck_z = min_z + 0.83 * height

    neck_base = Vector((center_x, head_top.y, neck_z))

    # ANKLE detection — find bottom-most verts on each side, then raise
    # the Z up to ~7% of total height so the marker sits at the actual
    # ankle joint rather than the sole of the foot.
    floor_threshold = min_z + 0.04 * height
    bottom_verts = [v for v in world_verts if v.z < floor_threshold]
    left_foot_verts = [v for v in bottom_verts if v.x > center_x]
    right_foot_verts = [v for v in bottom_verts if v.x < center_x]

    def _centroid(points, fallback):
        if not points:
            return fallback
        total = Vector((0.0, 0.0, 0.0))
        for point in points:
            total += point
        return total / len(points)

    foot_half_width = width * 0.1
    ankle_z = min_z + 0.08 * height
    ankle_left = _centroid(
        left_foot_verts,
        Vector((center_x + foot_half_width, center_y, ankle_z)),
    )
    ankle_left.z = ankle_z
    ankle_right = _centroid(
        right_foot_verts,
        Vector((center_x - foot_half_width, center_y, ankle_z)),
    )
    ankle_right.z = ankle_z

    # PELVIS — centerline point at ~53% of height from the floor.
    pelvis = Vector((center_x, center_y, min_z + 0.53 * height))

    # ── Precision (optional) markers ───────────────────────────
    # Shoulders — sit at ~22% of the arm span from neck toward wrist,
    # slightly below the neck.  Tuned to match Rigify's shoulder pivot.
    def _shoulder(wrist_pos):
        t = 0.22
        return Vector((
            neck_base.x + (wrist_pos.x - neck_base.x) * t,
            neck_base.y + (wrist_pos.y - neck_base.y) * t,
            neck_z - height * 0.03,
        ))

    shoulder_left = _shoulder(wrist_left)
    shoulder_right = _shoulder(wrist_right)

    # Elbows — midpoint of shoulder/wrist, slight back-bend (-Y nudge).
    def _elbow(shoulder_pos, wrist_pos):
        mid = (shoulder_pos + wrist_pos) * 0.5
        mid.y -= height * 0.005
        return mid

    elbow_left = _elbow(shoulder_left, wrist_left)
    elbow_right = _elbow(shoulder_right, wrist_right)

    # Hips — left/right of pelvis centerline, at ~48% of height.
    hip_z = min_z + 0.48 * height
    hip_half_span = (abs(ankle_left.x - ankle_right.x)) * 0.5
    # Use ~65% of ankle span as hip width (hips narrower than stance).
    hip_offset = max(hip_half_span * 0.65, width * 0.08)
    hip_left = Vector((center_x + hip_offset, center_y, hip_z))
    hip_right = Vector((center_x - hip_offset, center_y, hip_z))

    # Knees — midpoint hip/ankle, slight forward (+Y nudge for natural flex).
    def _knee(hip_pos, ankle_pos):
        mid = (hip_pos + ankle_pos) * 0.5
        mid.y += height * 0.01
        return mid

    knee_left = _knee(hip_left, ankle_left)
    knee_right = _knee(hip_right, ankle_right)

    # Toes — forward-most (+Y) verts on each foot, at ~3% of height.
    toe_z = min_z + 0.03 * height

    def _toe(foot_verts, fallback_x):
        if not foot_verts:
            return Vector((fallback_x, max_y, toe_z))
        # Pick the +Y-most 10% of foot verts
        sorted_by_y = sorted(foot_verts, key=lambda v: -v.y)
        sample = sorted_by_y[: max(1, len(sorted_by_y) // 10)]
        return Vector((
            sum(v.x for v in sample) / len(sample),
            sum(v.y for v in sample) / len(sample),
            toe_z,
        ))

    toe_left = _toe(left_foot_verts, ankle_left.x)
    toe_right = _toe(right_foot_verts, ankle_right.x)

    # Heels — rearmost (-Y) verts on each foot.
    def _heel(foot_verts, fallback_x):
        if not foot_verts:
            return Vector((fallback_x, min_y, toe_z))
        sorted_by_y = sorted(foot_verts, key=lambda v: v.y)
        sample = sorted_by_y[: max(1, len(sorted_by_y) // 10)]
        return Vector((
            sum(v.x for v in sample) / len(sample),
            sum(v.y for v in sample) / len(sample),
            toe_z,
        ))

    heel_left = _heel(left_foot_verts, ankle_left.x)
    heel_right = _heel(right_foot_verts, ankle_right.x)

    return {
        'HEAD_TOP': head_top,
        'NECK_BASE': neck_base,
        'WRIST_LEFT': wrist_left,
        'WRIST_RIGHT': wrist_right,
        'ANKLE_LEFT': ankle_left,
        'ANKLE_RIGHT': ankle_right,
        'PELVIS': pelvis,
        'SHOULDER_LEFT': shoulder_left,
        'SHOULDER_RIGHT': shoulder_right,
        'ELBOW_LEFT': elbow_left,
        'ELBOW_RIGHT': elbow_right,
        'HIP_LEFT': hip_left,
        'HIP_RIGHT': hip_right,
        'KNEE_LEFT': knee_left,
        'KNEE_RIGHT': knee_right,
        'TOE_LEFT': toe_left,
        'TOE_RIGHT': toe_right,
        'HEEL_LEFT': heel_left,
        'HEEL_RIGHT': heel_right,
    }


def _find_eyeball_centres(mesh_obj, face_cx, z_lo, z_hi, fwd, front_f, back_f, head_height):
    """Centres of a left/right pair of separate eyeball meshes, if present.

    An eyeball is a small, compact loose part in the front half of the head
    between ``z_lo`` and ``z_hi``; the pair is the best mirror match across
    the face centre. Returns ``{'L': Vector, 'R': Vector}`` or ``{}``.
    """
    import numpy as np
    mesh = mesh_obj.data
    count = len(mesh.vertices)
    # Perf (8.9.x): only the eye band of the head is searched. Loose parts are
    # found among the edges inside the band; a part with an edge leaving the
    # band belongs to a larger piece and is not an eyeball.
    co = np.empty(count * 3, dtype=np.float64)
    mesh.vertices.foreach_get("co", co)
    m = np.array(mesh_obj.matrix_world, dtype=np.float64)
    co = co.reshape(count, 3) @ m[:3, :3].T + m[:3, 3]
    margin = 0.2 * head_height                     # the largest eyeball accepted
    inside = (co[:, 2] >= z_lo - margin) & (co[:, 2] <= z_hi + margin)
    ev = np.empty(len(mesh.edges) * 2, dtype=np.int64)
    mesh.edges.foreach_get("vertices", ev)
    ev = ev.reshape(-1, 2)
    a_in, b_in = inside[ev[:, 0]], inside[ev[:, 1]]
    leaving = set(ev[a_in & ~b_in, 0].tolist()) | set(ev[b_in & ~a_in, 1].tolist())
    parent = {int(v): int(v) for v in np.nonzero(inside)[0]}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for va, vb in ev[a_in & b_in].tolist():
        ra, rb = find(va), find(vb)
        if ra != rb:
            parent[ra] = rb
    islands = {}
    for i in parent:
        islands.setdefault(find(i), []).append(i)
    mid_f = 0.5 * (front_f + back_f)
    cands = []
    for idx in islands.values():
        if len(idx) < 8 or len(idx) > count // 4 or any(i in leaving for i in idx):
            continue
        pts = co[idx]
        lo, hi = Vector(pts.min(axis=0).tolist()), Vector(pts.max(axis=0).tolist())
        size = hi - lo
        centre = (lo + hi) * 0.5
        if max(size) > 0.2 * head_height or min(size) < 0.25 * max(size):
            continue                                   # not small and compact
        if not (z_lo <= centre.z <= z_hi) or fwd(centre) < mid_f:
            continue                                   # not eye height / not front half
        cands.append(centre)
    best = None
    for a in cands:
        for b in cands:
            if a.x <= face_cx or b.x >= face_cx:
                continue
            score = abs(a.z - b.z) + abs((a.x - face_cx) + (b.x - face_cx))
            if best is None or score < best[0]:
                best = (score, a, b)
    return {'L': best[1], 'R': best[2]} if best else {}


def _guess_face_markers_from_mesh(mesh_obj, neck_base, front_sign=-1.0):
    """Facial markers from the head's own shape.

    The face is on the character's front (Blender -Y unless ``front_sign``
    says otherwise; the caller reads it from the feet). Along the face's
    midline profile the nose tip is the most forward point and the chin is
    the lowest point before the profile recedes into the neck; eyes are
    separate eyeball meshes when the character has them, else half way from
    chin to crown; mouth and lips sit between nose and chin. (This used to
    distribute fixed proportions of neck-base-to-crown on the +Y side, i.e.
    on the back of the head, with the chin on the neck.)
    """
    world = mesh_obj.matrix_world
    world_verts = [world @ v.co for v in mesh_obj.data.vertices]
    head_verts = [v for v in world_verts if v.z >= neck_base.z]
    if len(head_verts) < 20:
        return {}
    crown = max(v.z for v in head_verts)
    region_h = max(crown - neck_base.z, 1e-6)
    upper = [v for v in head_verts if v.z >= neck_base.z + 0.4 * region_h] or head_verts
    face_cx = 0.5 * (min(v.x for v in upper) + max(v.x for v in upper))
    face_hw = 0.5 * (max(v.x for v in upper) - min(v.x for v in upper))

    def fwd(p):                         # larger = more toward the face
        return p.y if front_sign > 0 else -p.y
    front_f = max(fwd(v) for v in head_verts)
    back_f = min(fwd(v) for v in head_verts)
    depth = max(front_f - back_f, 1e-6)

    def to_y(f):
        return f if front_sign > 0 else -f

    # midline profile: most forward point per height slice
    step = 0.01 * region_h
    profile = {}
    for v in head_verts:
        if abs(v.x - face_cx) <= 0.2 * face_hw:
            k = int((v.z - neck_base.z) / step)
            profile[k] = max(profile.get(k, -1e9), fwd(v))
    if not profile:
        return {}
    ks = sorted(profile)
    band = [k for k in ks if 0.35 * 100 <= k <= 0.85 * 100] or ks
    nose_k = max(band, key=lambda k: profile[k])
    nose_z = neck_base.z + (nose_k + 0.5) * step
    nose_f = profile[nose_k]
    chin_k = nose_k
    for k in range(nose_k - 1, ks[0] - 1, -1):
        if k not in profile:
            continue
        if profile[k] < nose_f - 0.5 * depth:
            break                       # receded into the neck
        if profile[k] >= nose_f - 0.25 * depth:
            chin_k = k
    chin_z = neck_base.z + (chin_k + 0.5) * step
    span = max(crown - chin_z, 1e-6)

    def surface(z, x):
        near = [v for v in head_verts if abs(v.z - z) <= 0.03 * span and abs(v.x - x) <= 0.12 * face_hw]
        return max((fwd(v) for v in near), default=front_f)

    eyes = _find_eyeball_centres(mesh_obj, face_cx, nose_z, nose_z + 0.5 * (crown - nose_z),
                                 fwd, front_f, back_f, span)
    eye_x = 0.36 * face_hw
    if eyes:
        eye_z = 0.5 * (eyes['L'].z + eyes['R'].z)
        left_eye, right_eye = eyes['L'], eyes['R']
    else:
        eye_z = chin_z + 0.5 * span
        ef = surface(eye_z, face_cx + eye_x) - 0.12 * depth
        left_eye = Vector((face_cx + eye_x, to_y(ef), eye_z))
        right_eye = Vector((face_cx - eye_x, to_y(ef), eye_z))
    brow_z = eye_z + 0.10 * span
    nose_to_chin = max(nose_z - chin_z, 1e-6)
    upper_lip_z = nose_z - 0.35 * nose_to_chin
    lower_lip_z = nose_z - 0.55 * nose_to_chin
    cheek_z = nose_z - 0.15 * nose_to_chin
    jaw_z = chin_z + 0.45 * nose_to_chin
    brow_x, cheek_x, jaw_x = 0.36 * face_hw, 0.55 * face_hw, 0.8 * face_hw
    return {
        'BROW_LEFT':  Vector((face_cx + brow_x, to_y(surface(brow_z, face_cx + brow_x)), brow_z)),
        'BROW_RIGHT': Vector((face_cx - brow_x, to_y(surface(brow_z, face_cx - brow_x)), brow_z)),
        'EYE_LEFT':   left_eye,
        'EYE_RIGHT':  right_eye,
        'NOSE_TIP':   Vector((face_cx, to_y(nose_f), nose_z)),
        'CHEEK_LEFT':  Vector((face_cx + cheek_x, to_y(surface(cheek_z, face_cx + cheek_x)), cheek_z)),
        'CHEEK_RIGHT': Vector((face_cx - cheek_x, to_y(surface(cheek_z, face_cx - cheek_x)), cheek_z)),
        'UPPER_LIP':  Vector((face_cx, to_y(surface(upper_lip_z, face_cx)), upper_lip_z)),
        'LOWER_LIP':  Vector((face_cx, to_y(surface(lower_lip_z, face_cx)), lower_lip_z)),
        'CHIN':       Vector((face_cx, to_y(profile[chin_k]), chin_z)),
        'JAW_LEFT':   Vector((face_cx + jaw_x, to_y(front_f - 0.55 * depth), jaw_z)),
        'JAW_RIGHT':  Vector((face_cx - jaw_x, to_y(front_f - 0.55 * depth), jaw_z)),
    }


def _guess_finger_markers_from_mesh(mesh_obj, wrist_pos, is_left, elbow_pos=None):
    """Finger markers from the mesh: the hand's own shape when readable
    (``geo_detect.finger_markers``), else the proportional fan below."""
    from boneforge.autorig import geo_detect
    world = mesh_obj.matrix_world
    pts = [tuple(world @ v.co) for v in mesh_obj.data.vertices]
    found = geo_detect.finger_markers(
        pts, tuple(wrist_pos), tuple(elbow_pos) if elbow_pos is not None else None,
        'L' if is_left else 'R')
    if found:
        return {k: Vector(v) for k, v in found.items()}
    return _guess_finger_markers_fan(mesh_obj, wrist_pos, is_left)


def _guess_finger_markers_fan(mesh_obj, wrist_pos, is_left):
    """Approximate finger marker positions from wrist and hand extremes.

    Very approximate — distributes finger MCP/PIP/DIP/tip joints along
    a fan from the wrist toward the hand's X-extreme, spread by Y.
    User is strongly encouraged to review these manually.

    Args:
        mesh_obj: the target mesh.
        wrist_pos: world-space wrist Vector.
        is_left: True for left hand (+X direction), False for right.

    Returns:
        dict[str, Vector] of FINGER_* markers for one hand.
    """
    world = mesh_obj.matrix_world
    world_verts = [world @ v.co for v in mesh_obj.data.vertices]
    if not world_verts:
        return {}

    direction = 1.0 if is_left else -1.0
    # Hand region: verts beyond the wrist in the arm direction.
    hand_verts = [
        v for v in world_verts
        if (direction * (v.x - wrist_pos.x)) > 0.0
        and abs(v.z - wrist_pos.z) < 0.20 * max(
            max(w.z for w in world_verts) - min(w.z for w in world_verts), 1.0,
        )
    ]
    if len(hand_verts) < 10:
        return {}

    if is_left:
        fingertip_x = max(v.x for v in hand_verts)
    else:
        fingertip_x = min(v.x for v in hand_verts)

    hand_length = abs(fingertip_x - wrist_pos.x)
    if hand_length < 1e-4:
        return {}

    # Y span of hand → finger spread axis.
    hand_y_min = min(v.y for v in hand_verts)
    hand_y_max = max(v.y for v in hand_verts)
    hand_y_span = max(hand_y_max - hand_y_min, hand_length * 0.3)
    hand_cy = (hand_y_min + hand_y_max) * 0.5

    suffix = 'L' if is_left else 'R'
    # Finger Y offsets from center (palm-relative): index is pinky-side
    # of thumb, pinky is opposite. Y+ is "forward" in Blender.
    finger_offsets = {
        'INDEX':  0.38,
        'MIDDLE': 0.13,
        'RING':  -0.13,
        'PINKY': -0.38,
    }

    result = {}

    # Palm marker — centre of the hand, ~25% out from wrist.
    result[f'FINGER_PALM_{suffix}'] = Vector((
        wrist_pos.x + direction * hand_length * 0.25,
        hand_cy,
        wrist_pos.z,
    ))

    # Non-thumb fingers — BASE at ~45% of hand length, TIP at ~100%.
    for finger, y_frac in finger_offsets.items():
        finger_y = hand_cy + hand_y_span * y_frac * 0.5
        base_x = wrist_pos.x + direction * hand_length * 0.45
        tip_x = wrist_pos.x + direction * hand_length * 1.0
        result[f'FINGER_{finger}_BASE_{suffix}'] = Vector(
            (base_x, finger_y, wrist_pos.z)
        )
        result[f'FINGER_{finger}_TIP_{suffix}'] = Vector(
            (tip_x, finger_y, wrist_pos.z)
        )

    # Thumb — shorter, fans out along +Y (palm-forward), from wrist.
    result[f'FINGER_THUMB_BASE_{suffix}'] = Vector((
        wrist_pos.x + direction * hand_length * 0.15,
        hand_cy + hand_y_span * 0.40,
        wrist_pos.z,
    ))
    result[f'FINGER_THUMB_TIP_{suffix}'] = Vector((
        wrist_pos.x + direction * hand_length * 0.40,
        hand_cy + hand_y_span * 0.75,
        wrist_pos.z,
    ))

    # Generic "FINGER_TIP" single-marker fallback used by count=1.
    result[f'FINGER_TIP_{suffix}'] = Vector((
        wrist_pos.x + direction * hand_length,
        hand_cy,
        wrist_pos.z,
    ))
    return result


class BF_OT_WizardGuessBodyMarkers(bpy.types.Operator):
    """Guess body marker positions from mesh geometry.

    v3.0.22: Split into two modes.  ``CORE`` places the 7 required
    markers (head, neck, wrists, ankles, pelvis).  ``PRECISION``
    places the 12 optional refinement markers (shoulders, elbows,
    hips, knees, toes, heels).  The two buttons let users accept or
    skip the extra precision pass independently.
    """

    bl_idname = "boneforge.autorig_guess_body_markers"
    bl_description = "Guess where the body markers go from the mesh's shape. Check them before generating"
    bl_label = "Guess Body Markers"
    bl_options = {'REGISTER', 'UNDO'}

    mode: bpy.props.EnumProperty(options={'HIDDEN', 'SKIP_SAVE'},
        name="Mode",
        items=[
            ('CORE', "Core Markers",
             "Guess the 7 required body markers"),
            ('PRECISION', "Precision Markers",
             "Guess the 12 optional precision markers "
             "(shoulders, elbows, hips, knees, toes, heels)"),
        ],
        default='CORE',
    )

    @classmethod
    def poll(cls, context):
        session = context.scene.boneforge_autorig_session
        return (
            session.is_active
            and session.wizard_step == STEP_BODY_MARKERS
            and session.mesh_object_name
        )

    def execute(self, context):
        session = context.scene.boneforge_autorig_session
        mesh_obj = bpy.data.objects.get(session.mesh_object_name)
        if mesh_obj is None or mesh_obj.type != 'MESH':
            self.report({'WARNING'}, "Target mesh not found")
            return {'CANCELLED'}

        guesses = _guess_body_markers_from_mesh(mesh_obj)
        if not guesses:
            self.report({'WARNING'}, "Mesh has no vertices to analyse")
            return {'CANCELLED'}

        # Pick the marker subset matching the requested mode.
        if self.mode == 'CORE':
            wanted = set(REQUIRED_BODY_MARKERS)
            label = "core"
        else:
            wanted = set(OPTIONAL_BODY_MARKERS)
            label = "precision"

        placed = 0
        for marker_name, world_position in guesses.items():
            if marker_name not in wanted:
                continue
            bpy.ops.boneforge.autorig_move_marker(
                marker_name=marker_name,
                marker_type='BODY',
                position=tuple(world_position),
            )
            bpy.ops.boneforge.autorig_confirm_marker(
                marker_name=marker_name,
                marker_type='BODY',
            )
            placed += 1

        self.report(
            {'INFO'},
            f"Guessed {placed} {label} marker(s) — review and re-place "
            "any that look off before continuing",
        )
        if context.area:
            context.area.tag_redraw()
        return {'FINISHED'}


class BF_OT_WizardGuessFaceMarkers(bpy.types.Operator):
    """Guess facial marker positions from head proportions.

    Best-effort — analyses the head region (verts above neck base) and
    distributes facial landmarks by canonical face proportions. Always
    review before generating.
    """

    bl_idname = "boneforge.autorig_guess_face_markers"
    bl_description = "Guess where the face markers go from the head's proportions. Check them before generating"
    bl_label = "Guess Face Markers"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        session = context.scene.boneforge_autorig_session
        return (
            session.is_active
            and session.wizard_step == STEP_FACE_MARKERS
            and session.mesh_object_name
        )

    def execute(self, context):
        session = context.scene.boneforge_autorig_session
        mesh_obj = bpy.data.objects.get(session.mesh_object_name)
        if mesh_obj is None or mesh_obj.type != 'MESH':
            self.report({'WARNING'}, "Target mesh not found")
            return {'CANCELLED'}

        # Pull neck_base from the already-confirmed body markers.
        # v3.0.21: body markers are indexed in a CollectionProperty;
        # look them up by the session helper, not by a .name attribute.
        neck_marker = get_body_marker(session, 'NECK_BASE')
        if neck_marker is None or not is_position_placed(
            Vector(neck_marker.position)
        ):
            self.report({'WARNING'},
                        "Neck Base marker must be placed first")
            return {'CANCELLED'}
        neck_base = Vector(neck_marker.position)

        # the face is on the side the toes point to (default Blender -Y)
        front_sign = -1.0
        toe = get_body_marker(session, 'TOE_LEFT')
        ankle = get_body_marker(session, 'ANKLE_LEFT')
        if toe is not None and ankle is not None                 and is_position_placed(Vector(toe.position))                 and is_position_placed(Vector(ankle.position)):
            dy = toe.position[1] - ankle.position[1]
            if abs(dy) > 1e-4:
                front_sign = 1.0 if dy > 0 else -1.0
        guesses = _guess_face_markers_from_mesh(mesh_obj, neck_base, front_sign)
        if not guesses:
            self.report({'WARNING'},
                        "Could not locate enough head vertices")
            return {'CANCELLED'}

        placed = 0
        for marker_name, world_position in guesses.items():
            # eye markers are the eyeball's pivot, inside it: snapping them
            # to the nearest surface lifted them onto the lid
            bpy.ops.boneforge.autorig_move_marker(
                marker_name=marker_name,
                marker_type='FACE',
                position=tuple(world_position),
                snap=not marker_name.startswith("EYE_"),
            )
            bpy.ops.boneforge.autorig_confirm_marker(
                marker_name=marker_name,
                marker_type='FACE',
            )
            placed += 1

        self.report({'INFO'},
                    f"Guessed {placed} face marker(s) — review each one")
        if context.area:
            context.area.tag_redraw()
        return {'FINISHED'}


class BF_OT_WizardGuessFingerMarkers(bpy.types.Operator):
    """Guess finger marker positions from wrist and hand extremes.

    Very approximate — uses wrist position and hand bounding box to
    fan out finger joints. Expect to fine-tune manually, especially
    for stylised or non-human hands.
    """

    bl_idname = "boneforge.autorig_guess_finger_markers"
    bl_description = "Roughly guess the finger markers from the wrist and the hand's size. Expect to adjust them"
    bl_label = "Guess Finger Markers"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        session = context.scene.boneforge_autorig_session
        return (
            session.is_active
            and session.wizard_step == STEP_FINGER_MARKERS
            and session.mesh_object_name
            and session.finger_count > 0
        )

    def execute(self, context):
        session = context.scene.boneforge_autorig_session
        mesh_obj = bpy.data.objects.get(session.mesh_object_name)
        if mesh_obj is None or mesh_obj.type != 'MESH':
            self.report({'WARNING'}, "Target mesh not found")
            return {'CANCELLED'}

        # Need confirmed WRIST_LEFT / WRIST_RIGHT from the body step.
        # v3.0.21: use get_body_marker — body markers have no .name
        # attribute, they're indexed by position in BODY_MARKERS.
        wrist_positions = {}
        for side, marker_name in (('L', 'WRIST_LEFT'),
                                  ('R', 'WRIST_RIGHT')):
            m = get_body_marker(session, marker_name)
            if m is None or not is_position_placed(Vector(m.position)):
                self.report({'WARNING'},
                            f"{marker_name} must be placed first")
                return {'CANCELLED'}
            wrist_positions[side] = Vector(m.position)

        wanted = set(FINGER_MARKERS_BY_COUNT.get(session.finger_count, ()))
        # Right-hand mirrored names are always placed too.
        wanted = wanted | {n.replace('_L', '_R') for n in wanted}

        placed = 0
        for side, wrist_pos in wrist_positions.items():
            is_left = (side == 'L')
            elbow = Vector(session.derived_elbow_left if is_left
                           else session.derived_elbow_right)
            guesses = _guess_finger_markers_from_mesh(
                mesh_obj, wrist_pos, is_left,
                elbow if is_position_placed(elbow) else None,
            )
            for marker_name, world_position in guesses.items():
                if marker_name not in wanted:
                    continue
                bpy.ops.boneforge.autorig_move_marker(
                    marker_name=marker_name,
                    marker_type='FINGER',
                    position=tuple(world_position),
                )
                bpy.ops.boneforge.autorig_confirm_marker(
                    marker_name=marker_name,
                    marker_type='FINGER',
                )
                placed += 1

        self.report(
            {'INFO'},
            f"Guessed {placed} finger marker(s) — "
            "review each one (finger guesses are approximate)",
        )
        if context.area:
            context.area.tag_redraw()
        return {'FINISHED'}


# ── Registration ──────────────────────────────────────────────

# v3.2.5: BF_PT_WizardPanel intentionally NOT in this tuple. The
# class definition is kept (taskboard/sidebar.py's BF_PT_sb_wizard
# delegates its draw via _delegate_draw), but the standalone N-panel
# was a duplicate of the Setup hub's child Auto-Rig Wizard sub-panel.
# Removing it from registration deletes the duplicate without losing
# any UI — the Setup hub renders the same draw method.
classes = (
    BF_OT_WizardStart,
    BF_OT_WizardNext,
    BF_OT_WizardBack,
    BF_OT_WizardBuildControlRig,
    BF_OT_WizardCancel,
    BF_OT_WizardSelectMesh,
    BF_OT_WizardSetRigType,
    BF_OT_WizardMoveMarker,
    BF_OT_WizardPlaceMarker,
    BF_OT_WizardToggleSymmetry,
    BF_OT_WizardConfirmMarker,
    BF_OT_WizardConfirmAllGreen,
    BF_OT_WizardGuessBodyMarkers,
    BF_OT_WizardGuessFaceMarkers,
    BF_OT_WizardGuessFingerMarkers,
    BF_OT_WizardResetMarker,
    BF_OT_WizardSetFingerCount,
    BF_OT_WizardGenerate,
)


def register():
    """Register wizard operators, panel, and viewport draw handlers."""
    global _draw_handle_3d, _draw_handle_2d
    for cls in classes:
        bpy.utils.register_class(cls)

    _draw_handle_3d = bpy.types.SpaceView3D.draw_handler_add(
        _draw_markers_3d, (), 'WINDOW', 'POST_VIEW',
    )
    _draw_handle_2d = bpy.types.SpaceView3D.draw_handler_add(
        _draw_markers_2d, (), 'WINDOW', 'POST_PIXEL',
    )


def unregister():
    """Unregister wizard operators, panel, and viewport draw handlers."""
    global _draw_handle_3d, _draw_handle_2d
    if _draw_handle_2d is not None:
        bpy.types.SpaceView3D.draw_handler_remove(
            _draw_handle_2d, 'WINDOW',
        )
        _draw_handle_2d = None
    if _draw_handle_3d is not None:
        bpy.types.SpaceView3D.draw_handler_remove(
            _draw_handle_3d, 'WINDOW',
        )
        _draw_handle_3d = None
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
