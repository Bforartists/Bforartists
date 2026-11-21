"""
physics_suggest.py — Parabolic arc correction for physics-informed ghost suggestions.

This is a Tier 3 stretch-goal feature.  After a ghost is dragged, the user
can invoke "Suggest" to apply a simple parabolic arc correction to nearby
ghosts, simulating gravity.  This is NOT a full physics simulation — it is
a mathematical correction pass.

Suggestions are previewed as a ghost overlay and must be accepted explicitly.
"""

from __future__ import annotations

from typing import Optional

import math
import bpy
from mathutils import Vector

from .ghost_data import GhostStore, Ghost
from . import fcurve_utils
from .utils import debug, warn, tag_viewport_redraw
from .physics_archetypes import ARCHETYPES
from .utils import report_failure


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_GRAVITY_STRENGTH: float = 9.81
"""Default gravity magnitude in scene units per second^2.

Matches real-world gravity (9.81 m/s²) for physically plausible ballistic arcs.
Users may adjust this based on their scene scale and artistic intent.
"""

DEFAULT_GRAVITY_AXIS: str = "Z"
"""Default axis along which gravity acts (negative direction).

Typically Z (up/down in Blender), but X and Y are supported.
Gravity acts in the negative direction of the chosen axis.
"""

GRAVITY_CORRECTION_SCALE: float = 0.1
"""Scale factor applied to displacement-based value corrections.

This factor dampens the raw displacement magnitude (which is in world units)
to produce a reasonable local value delta. It prevents over-correction that
would cause ghosts to "fly away" and maintains visual plausibility while
keeping the f-curve values in a sensible range relative to the scene scale.
"""

POSITION_ADJUSTMENT_SCALE: float = 0.01
"""Scale factor applied to positional adjustments in ballistic preview and correction.

This factor scales the gravitational displacement for visual rendering clarity.
A smaller scale (0.01) produces more subtle arc curvature, allowing the ghost
positions to remain close to the original path while still conveying the
parabolic trajectory. This keeps preview overlays readable without exaggerated
deflections that would obscure the underlying motion.
"""


# ---------------------------------------------------------------------------
# Parabolic Correction
# ---------------------------------------------------------------------------

def _compute_ghost_displacement(
    ghost: Ghost,
    frame_a: float,
    frame_b: float,
    frame_rate: float,
    gravity_strength: float,
    gravity_axis: str,
    axis_idx: int,
) -> dict:
    """Compute physics displacement for a single ghost in a keyframe segment.

    Calculates the parabolic correction and positional adjustment for a ghost
    within a parent keyframe segment, accounting for gravitational acceleration
    over the segment duration.

    The parabolic profile peaks at the segment midpoint (t=0.5) and tapers to
    zero at both parent keyframes (t=0 and t=1), modeling the time-in-air effect
    of projectile motion.

    Args:
        ghost: The ghost to compute displacement for.
        frame_a: Start frame of the parent keyframe segment.
        frame_b: End frame of the parent keyframe segment.
        frame_rate: Scene frame rate (fps).
        gravity_strength: Gravity magnitude in scene units per second^2.
        gravity_axis: Axis of gravity ("X", "Y", or "Z").
        axis_idx: Numeric index of the gravity axis (0=X, 1=Y, 2=Z).

    Returns:
        dict: Displacement result containing:
            - "correction" (float): Value delta to apply to local_value
            - "suggested_position" (Vector): Adjusted world position
            - "delta" (float): Alias for correction
    """
    segment_duration_frames = frame_b - frame_a
    segment_duration_seconds = segment_duration_frames / frame_rate

    # Parametric position within segment [0..1]
    # 0 = at frame_a (start), 1 = at frame_b (end)
    parametric_position = (ghost.frame - frame_a) / segment_duration_frames

    # Parabolic profile: peaks at t=0.5, zero at t=0 and t=1
    # Formula: 4*t*(1-t) models the "time spent in the air" effect.
    # Peak of 1.0 occurs at the midpoint (t=0.5).
    # This ensures strongest correction at segment center, tapering to zero at keyframes.
    parabolic_factor = 4.0 * parametric_position * (1.0 - parametric_position)

    # Time in seconds for this ghost's position in the arc
    # Scales the parametric position into absolute time within the segment
    time_in_segment_seconds = parametric_position * segment_duration_seconds

    # Gravitational displacement: 0.5 * g * t * (T - t)
    # This is the classic ballistic trajectory formula where:
    # - g is gravitational acceleration
    # - t is time elapsed since start
    # - T is total segment time
    # Result is in scene units, accounting for arc drop over the segment duration
    displacement = 0.5 * gravity_strength * time_in_segment_seconds * (segment_duration_seconds - time_in_segment_seconds)

    # Apply correction as a value delta
    # The sign depends on the channel axis matching the gravity axis
    channel_lower = ghost.channel.lower()
    correction = 0.0

    if gravity_axis.lower() in channel_lower:
        # displacement already contains the parabolic shape via 0.5*g*t*(T-t),
        # so we do NOT multiply by parabolic_factor again (that would create quartic).
        correction = -displacement * GRAVITY_CORRECTION_SCALE

    # Compute suggested world position using the same physics displacement
    # that drives the correction, ensuring visual preview matches applied values.
    suggested_pos = ghost.world_position.copy()
    grav_vec_component = -displacement * POSITION_ADJUSTMENT_SCALE
    suggested_pos[axis_idx] += grav_vec_component

    return {
        "correction": correction,
        "suggested_position": suggested_pos,
    }


def compute_parabolic_suggestion(
    ghost: Ghost,
    store: GhostStore,
    gravity_strength: float = DEFAULT_GRAVITY_STRENGTH,
    gravity_axis: str = DEFAULT_GRAVITY_AXIS,
    frame_rate: float = 24.0,
) -> list[dict]:
    """Compute parabolic arc corrections for ghosts near a reference ghost.

    Given a ghost (typically one just dragged by the user), this function
    identifies the ghost chain it belongs to and applies a parabolic offset
    based on the assumption that the object is under constant gravitational
    acceleration.

    The correction is strongest at the midpoint of the arc and tapers to
    zero at the parent keyframes.

    Args:
        ghost: The reference ghost (usually the one just moved).
        store: The GhostStore containing all ghosts.
        gravity_strength: Magnitude of gravity in scene units per second^2.
        gravity_axis: Axis of gravity ("X", "Y", or "Z").
        frame_rate: Scene frame rate for time conversion.

    Returns:
        list[dict]: Suggested corrections, each containing:
            - "uid" (str): Ghost UID
            - "suggested_value" (float): New local value
            - "suggested_position" (Vector): New world position
            - "delta" (float): The applied correction amount
    """
    if frame_rate <= 0 or not math.isfinite(frame_rate):
        return []

    # Get the chain this ghost belongs to
    chain = store.get_chain(ghost.object_name, ghost.bone_name, ghost.channel)

    if len(chain) < 3:
        return []

    # Determine gravity axis index
    axis_idx = {"X": 0, "Y": 1, "Z": 2}.get(gravity_axis.upper(), 2)

    # Find the parent keyframe frames for the affected range
    frame_a = ghost.parent_frame_a
    frame_b = ghost.parent_frame_b
    segment_duration_frames = frame_b - frame_a
    segment_duration_seconds = segment_duration_frames / frame_rate

    if segment_duration_seconds < 0.001:
        return []

    suggestions = []

    for g in chain:
        # Only affect ghosts in the same parent segment
        if g.parent_frame_a != frame_a or g.parent_frame_b != frame_b:
            continue

        displacement = _compute_ghost_displacement(
            g,
            frame_a,
            frame_b,
            frame_rate,
            gravity_strength,
            gravity_axis,
            axis_idx,
        )

        suggested_value = g.local_value + displacement["correction"]

        suggestions.append({
            "uid": g.uid,
            "suggested_value": suggested_value,
            "suggested_position": displacement["suggested_position"],
            "delta": displacement["correction"],
        })

    return suggestions


def compute_ballistic_preview(
    store: GhostStore,
    gravity_strength: float = DEFAULT_GRAVITY_STRENGTH,
    gravity_axis: str = DEFAULT_GRAVITY_AXIS,
    offset: tuple[float, float, float] = (0.0, 0.0, 0.0),
    frame_rate: float = 24.0,
) -> list[dict]:
    """Compute ballistic preview positions for all ghosts in the store.

    Projects each ghost's position along a parabolic arc based on gravity,
    producing preview positions that can be drawn as an overlay in the viewport.

    Unlike ``compute_parabolic_suggestion`` (which modifies values), this
    function is purely visual — it does not alter ghost data or f-curves.

    Args:
        store: The GhostStore containing ghosts to preview.
        gravity_strength: Gravity magnitude (m/s²).
        gravity_axis: Axis of gravity ("X", "Y", or "Z").
        offset: Manual offset vector applied to all preview positions.
        frame_rate: Scene frame rate for time conversion.

    Returns:
        list[dict]: Preview entries, each with:
            - "uid" (str): Ghost UID
            - "preview_position" (Vector): Predicted world position
            - "frame" (float): Ghost frame
    """
    all_ghosts = sorted(store.all_ghosts, key=lambda ghost: ghost.frame)
    if len(all_ghosts) < 2:
        return []

    # Map gravity axis name to numeric index: X=0, Y=1, Z=2
    axis_idx = {"X": 0, "Y": 1, "Z": 2}.get(gravity_axis.upper(), 2)
    offset_vec = Vector(offset)

    # Determine the total time span of the animation
    first_frame = all_ghosts[0].frame
    last_frame = all_ghosts[-1].frame
    total_frames = last_frame - first_frame
    if total_frames <= 0:
        return []

    if frame_rate <= 0 or not math.isfinite(frame_rate):
        return []

    total_time_seconds = total_frames / frame_rate
    previews = []

    for ghost in all_ghosts:
        # Time elapsed since the start frame (in seconds)
        time_elapsed_seconds = (ghost.frame - first_frame) / frame_rate

        # Parabolic displacement peaking at midpoint: 0.5 * g * t * (T - t)
        # This is the classic ballistic trajectory formula
        displacement = 0.5 * gravity_strength * time_elapsed_seconds * (total_time_seconds - time_elapsed_seconds)

        # Create preview position by applying gravity displacement
        preview_pos = ghost.world_position.copy()
        # Subtract displacement to move downward along gravity axis
        preview_pos[axis_idx] -= displacement * POSITION_ADJUSTMENT_SCALE
        preview_pos += offset_vec

        previews.append({
            "uid": ghost.uid,
            "preview_position": preview_pos,
            "frame": ghost.frame,
        })

    return previews


def apply_suggestions(
    suggestions: list[dict],
    store: GhostStore,
    scene: bpy.types.Scene,
) -> int:
    """Apply physics suggestions to ghosts and their f-curves.

    Iterates over suggestions and updates each ghost's value and position,
    then recalculates f-curve handles to match the new value.

    Args:
        suggestions: List of suggestion dicts from compute_parabolic_suggestion.
        store: The GhostStore containing the ghosts to update.
        scene: The Blender scene.

    Returns:
        int: Number of ghosts updated.
    """
    applied = 0
    seen = set()
    for suggestion in suggestions:
        uid = suggestion['uid']
        if uid in seen:
            continue
        seen.add(uid)
        ghost = store.get_by_uid(uid)
        if ghost is None or ghost.is_pinned:
            continue
        obj = scene.objects.get(ghost.object_name)
        if obj is None or _has_active_nla_strips(obj):
            continue
        curve = fcurve_utils.resolve_fcurve(obj, ghost.bone_name, ghost.channel)
        if curve is None:
            continue
        backup = fcurve_utils.snapshot_fcurve(curve)
        mode = scene.ghost_tool.curve_mode.lower()
        try:
            success = fcurve_utils.recalculate_handles(curve, ghost.frame, suggestion['suggested_value'], mode=mode)
        except Exception as exc:
            warn(f"Physics curve update failed: {exc}")
            success = False
        if not success:
            fcurve_utils.restore_fcurve(curve, backup)
            continue
        ghost.local_value = suggestion['suggested_value']
        ghost.world_position = suggestion['suggested_position'].copy()
        applied += 1
    if applied:
        from .ghost_pipeline import GhostPipeline
        GhostPipeline.get(scene).mark_dirty()
        if scene == bpy.context.scene:
            from .api import refresh_ghosts
            refresh_ghosts()
    return applied


# ---------------------------------------------------------------------------
# NLA Strip Guard
# ---------------------------------------------------------------------------

def _has_active_nla_strips(obj: bpy.types.Object) -> bool:
    """Return True if the object has NLA strips that could conflict with baking.

    When NLA is active, ``keyframe_insert`` behaviour changes and the output
    may not land where expected.  Both the archetype preview and the bake
    operator call this guard before touching fcurves.

    Args:
        obj: The Blender object to inspect.

    Returns:
        bool: True when NLA data is present and the NLA editor is in use.
    """
    if not obj or not obj.animation_data:
        return False
    animation = obj.animation_data
    if not animation.use_nla:
        return False
    tracks = [track for track in animation.nla_tracks if not track.mute]
    solo = [track for track in tracks if track.is_solo]
    return any(not strip.mute for track in (solo or tracks) for strip in track.strips)


# ---------------------------------------------------------------------------
# Physics Preview State (module-level for draw handler access)
#
# Mutual exclusion contract
# -------------------------
# Only ONE source may populate _physics_preview_data at a time.
# Before calling _set_physics_preview(), always call _clear_physics_preview()
# first.  Both GHOST_OT_physics_suggest and GHOST_OT_archetype_bake honour
# this by clearing before activating.  The draw handler (viewport_draw.py)
# reads this list without regard for which operator produced it.
# ---------------------------------------------------------------------------

_physics_preview_data: list[dict] = []
_physics_preview_scene = None


def _set_physics_preview(suggestions: list[dict]) -> None:
    """Store preview entries for the draw handler.

    Callers must call _clear_physics_preview() first to honour the mutual
    exclusion contract documented above.

    Args:
        suggestions: List of dicts, each containing at minimum
            ``"suggested_position"`` (Vector) keyed for the draw handler.
    """
    global _physics_preview_data, _physics_preview_scene
    from .utils import get_scene_id
    _physics_preview_scene = get_scene_id(bpy.context.scene)
    _physics_preview_data = list(suggestions)


def _clear_physics_preview() -> None:
    """Clear all preview entries.

    Call this before activating a new preview source (mutual exclusion).
    """
    global _physics_preview_data, _physics_preview_scene
    _physics_preview_scene = None
    _physics_preview_data = []


def get_physics_preview() -> list[dict]:
    """Return current physics preview data.

    Called each frame by ``viewport_draw.draw_ghosts_3d``.  Returns an empty
    list when no preview is active.

    Returns:
        list[dict]: Current preview entries, or [].
    """
    from .utils import get_scene_id
    if bpy.context.scene is None or get_scene_id(bpy.context.scene) != _physics_preview_scene:
        return []
    return _physics_preview_data


# ---------------------------------------------------------------------------
# Operator
# ---------------------------------------------------------------------------

class GHOST_OT_physics_suggest(bpy.types.Operator):
    """Preview and apply parabolic arc correction to ghosts (physics suggestion).

    Enters a modal preview state showing suggested positions as dashed overlay
    markers. Confirm with LEFTMOUSE or ENTER to apply. Cancel with RIGHTMOUSE
    or ESC to discard.
    """

    bl_idname = "ghost_tool.physics_suggest"
    bl_label = "Physics Suggest (Preview)"
    bl_options = {'REGISTER', 'UNDO'}

    gravity_strength: bpy.props.FloatProperty(
        name="Gravity Strength",
        description="Gravity magnitude in scene units per second squared",
        default=DEFAULT_GRAVITY_STRENGTH,
        min=0.0,
        max=100.0,
    )  # type: ignore[assignment]

    gravity_axis: bpy.props.EnumProperty(
        name="Gravity Axis",
        description="Axis along which gravity acts (negative direction)",
        items=[
            ("X", "X", "Gravity along -X"),
            ("Y", "Y", "Gravity along -Y"),
            ("Z", "Z", "Gravity along -Z"),
        ],
        default="Z",
    )  # type: ignore[assignment]

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        """Require active ghost display with ghosts present."""
        if not hasattr(context.scene, 'ghost_tool'):
            cls.poll_message_set("Initialize Ghost Tool first")
            return False
        store = GhostStore.get(context.scene)
        if not len(store):
            cls.poll_message_set("Generate markers between animation keys first")
            return False
        from .session_state import SessionState
        return SessionState.poll_available(cls)

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        """Compute preview suggestions and enter modal mode.

        Args:
            context: The current Blender context.
            event: The triggering event.

        Returns:
            set[str]: {'RUNNING_MODAL'} on success, {'CANCELLED'} if no suggestions.
        """
        # Guard against double-invoke while a preview is already active
        from .session_state import SessionState
        if not SessionState.available(self):
            self.report({'WARNING'}, "Finish or cancel the current Ghost Tool gesture first")
            return {'CANCELLED'}
        if get_physics_preview():
            self.report({'WARNING'}, "Physics preview already active")
            return {'CANCELLED'}

        # Initialize instance state (NOT class variables — Blender shares those)
        self._preview_suggestions = []
        self._preview_active = False

        store = GhostStore.get(context.scene)
        selected = store.get_selected(context.scene)
        if not selected:
            selected = store.all_ghosts
        if not selected:
            self.report({'WARNING'}, "No ghosts to apply suggestions to")
            return {'CANCELLED'}

        # Compute all suggestions for preview
        frame_rate = context.scene.render.fps / context.scene.render.fps_base
        all_suggestions = []
        visited_segments = set()
        for ghost in selected:
            segment = (ghost.object_name, ghost.bone_name, ghost.channel, ghost.parent_frame_a, ghost.parent_frame_b)
            if segment in visited_segments:
                continue
            visited_segments.add(segment)
            suggestions = compute_parabolic_suggestion(
                ghost, store,
                gravity_strength=self.gravity_strength,
                gravity_axis=self.gravity_axis,
                frame_rate=frame_rate,
            )
            all_suggestions.extend(suggestions)

        if not all_suggestions:
            self.report({'WARNING'}, "No physics suggestions computed")
            return {'CANCELLED'}

        # Store preview data and activate modal
        from .session_state import CurveTransaction
        targets = [store.get_by_uid(s['uid']) for s in all_suggestions]
        try:
            self._transaction = CurveTransaction(context.scene,
                [(context.scene.objects.get(g.object_name), g.bone_name, g.channel) for g in targets if g])
        except ValueError as exc:
            self.report({'WARNING'}, str(exc))
            return {'CANCELLED'}
        SessionState.begin_gesture(self, context.scene, context=context,
            cancel=lambda: self._cancel(bpy.context), validate=self._transaction.valid)
        self._preview_suggestions = all_suggestions
        self._preview_active = True

        # Store preview positions in a module-level list for the draw handler
        _set_physics_preview(all_suggestions)

        try:
            context.window_manager.modal_handler_add(self)
        except Exception:
            self._cancel(context)
            raise
        from .session_state import SessionState
        self._preview_session = SessionState.get(context.scene)
        self._preview_session.drag_active = True
        self.report({'INFO'}, f"Physics preview: {len(all_suggestions)} ghosts. ENTER/LMB to apply, ESC/RMB to cancel.")
        tag_viewport_redraw(context)
        return {'RUNNING_MODAL'}

    def modal(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        from .session_state import SessionState
        if not SessionState.owns_gesture(self, context.scene):
            return self._cancel(context)
        try:
            return self._modal_inner(context, event)
        except Exception as exc:
            self._cancel(context)
            self.report({'ERROR'}, f"Physics preview cancelled: {exc}")
            return {'CANCELLED'}

    def _modal_inner(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        """Handle confirm/cancel during preview.

        Args:
            context: The current Blender context.
            event: The current event.

        Returns:
            set[str]: Modal state.
        """
        # Confirm with ENTER or LMB
        if event.type in {'RET', 'NUMPAD_ENTER'} and event.value == 'PRESS':
            return self._confirm(context)
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            return self._confirm(context)

        # Cancel with ESC or RMB
        if event.type in {'RIGHTMOUSE', 'ESC'} and event.value == 'PRESS':
            return self._cancel(context)

        return {'RUNNING_MODAL'}

    def _confirm(self, context: bpy.types.Context) -> set[str]:
        """Apply the previewed suggestions."""
        transaction = getattr(self, '_transaction', None)
        if transaction is not None and not transaction.valid():
            return self._cancel(context)
        store = GhostStore.get(context.scene)
        applied = apply_suggestions(self._preview_suggestions, store, context.scene)
        if transaction is not None:
            transaction.finish()
        from .session_state import SessionState
        SessionState.end_gesture(self)
        _clear_physics_preview()
        self._preview_active = False
        if getattr(self, "_preview_session", None):
            self._preview_session.drag_active = False
        self.report({'INFO'}, f"Applied physics suggestions to {applied} ghosts")
        tag_viewport_redraw(context)
        return {'FINISHED'}

    def _cancel(self, context: bpy.types.Context) -> set[str]:
        """Discard the preview without applying."""
        transaction = getattr(self, '_transaction', None)
        if transaction is not None:
            transaction.rollback()
            transaction.finish()
        from .session_state import SessionState
        SessionState.end_gesture(self)
        _clear_physics_preview()
        self._preview_active = False
        if getattr(self, "_preview_session", None):
            self._preview_session.drag_active = False
        self.report({'INFO'}, "Physics suggestion cancelled")
        tag_viewport_redraw(context)
        return {'CANCELLED'}


# ---------------------------------------------------------------------------
# Archetype Bake Operator
# ---------------------------------------------------------------------------

class GHOST_OT_archetype_bake(bpy.types.Operator):
    """Stamp archetype-shaped keyframes onto the active object's fcurve.

    Evaluates the selected physics-feel archetype across a frame range and
    writes one keyframe per frame on the target axis channel.  Existing keys
    on that channel are cleared first (REPLACE mode) so the output is clean
    and editable immediately.

    Workflow:
        1. Select archetype, axis, amplitude, and frame range in the panel.
        2. Enable Archetype Preview to see the overlay in the viewport.
        3. Press "Stamp to Keys" to write the keyframes.

    All writes are wrapped in a single undo step — Ctrl+Z restores the
    previous state completely.
    """

    bl_idname = "ghost_tool.archetype_bake"
    bl_label = "Stamp to Keys"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        """Require an active object with animation data.

        Args:
            context: The current Blender context.

        Returns:
            bool: True when stamping can proceed.
        """
        obj = context.active_object
        if not (obj and obj.animation_data and obj.animation_data.action):
            cls.poll_message_set("Select an object with an animation action first")
            return False
        from .session_state import SessionState
        return SessionState.poll_available(cls)

    def execute(self, context: bpy.types.Context) -> set[str]:
        """Write archetype-shaped keyframes to the target channel.

        Args:
            context: The current Blender context.

        Returns:
            set[str]: {'FINISHED'} on success, {'CANCELLED'} on guard failure.
        """
        obj = context.active_object
        settings = context.scene.ghost_tool

        # Guard: NLA strips conflict with direct keyframe writes.
        if _has_active_nla_strips(obj):
            self.report(
                {'WARNING'},
                "Archetype bake skipped: object has active NLA strips. "
                "Exit the NLA editor or disable NLA before stamping.",
            )
            return {'CANCELLED'}

        archetype_name = settings.archetype_active
        archetype_fn = ARCHETYPES.get(archetype_name)
        if archetype_fn is None:
            report_failure(self, "Unknown archetype", "Undo (Ctrl+Z) and try again", archetype_name)
            return {'CANCELLED'}

        start = settings.archetype_start_frame
        end = settings.archetype_end_frame
        if end <= start:
            self.report({'WARNING'}, "End frame must be greater than start frame.")
            return {'CANCELLED'}

        amplitude = settings.archetype_amplitude
        axis = settings.archetype_axis.lower()
        channel = f"location.{axis}"

        # Resolve the fcurve for the target channel.
        # Bone support: use the active pose bone if one is selected.
        bone_name = ""
        if obj.type == 'ARMATURE' and context.active_pose_bone:
            bone_name = context.active_pose_bone.name

        fcurve = fcurve_utils.resolve_fcurve(obj, bone_name, channel)
        if fcurve is None:
            self.report(
                {'WARNING'},
                f"No fcurve found for channel '{channel}' on '{obj.name}'. "
                "Add at least one location keyframe on that axis first.",
            )
            return {'CANCELLED'}

        # Push a single undo step before any writes — unconditional.
        bpy.ops.ed.undo_push(message=f"Archetype Bake: {archetype_name}")

        backup = fcurve_utils.snapshot_fcurve(fcurve)
        total_frames = end - start
        stamped = 0
        try:
            self._clear_channel_keys(fcurve, start, end)
            for frame in range(start, end + 1):
                displacement = archetype_fn((frame - start) / total_frames) * amplitude
                point = fcurve.keyframe_points.insert(float(frame), displacement, options={'FAST'})
                point.handle_left_type = point.handle_right_type = 'AUTO_CLAMPED'
                stamped += 1
        except Exception as exc:
            fcurve_utils.restore_fcurve(fcurve, backup)
            report_failure(self, "Archetype bake cancelled and the curve restored", "Choose a range with at least two keyframes and try again", exc)
            return {'CANCELLED'}

        fcurve.update()
        fcurve_utils.invalidate_keyframe_cache()

        # Regenerate ghosts so the new keys immediately show as ghost-able
        # inbetweens — but only when the ghost tool is live and active.
        self._maybe_regenerate_ghosts(context, settings)

        tag_viewport_redraw(context)
        self.report({'INFO'}, f"Stamped {stamped} keyframes ({archetype_name})")
        return {'FINISHED'}

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _clear_channel_keys(
        fcurve: bpy.types.FCurve,
        start: int,
        end: int,
    ) -> None:
        """Remove all keyframes in [start, end] on the given fcurve.

        Args:
            fcurve: The fcurve to modify.
            start: Inclusive start frame.
            end: Inclusive end frame.
        """
        # Reacquire each key after removal; RNA references can be invalidated.
        for index in range(len(fcurve.keyframe_points) - 1, -1, -1):
            point = fcurve.keyframe_points[index]
            if start <= point.co.x <= end:
                fcurve.keyframe_points.remove(point, fast=True)
        fcurve.update()

    @staticmethod
    def _maybe_regenerate_ghosts(
        context: bpy.types.Context,
        settings,
    ) -> None:
        """Trigger ghost regeneration after a bake if the tool is live.

        The new stamped keyframes create ghost-able inbetweens that won't
        appear until regeneration.  Only runs when ghosts are active and
        live mode is on — no-op otherwise.

        Args:
            context: The current Blender context.
            settings: The GhostToolSceneSettings instance.
        """
        if not getattr(settings, "is_active", False):
            return
        if not getattr(settings, "live_point_ghosts", False):
            return
        try:
            bpy.ops.ghost_tool.generate_ghosts()
        except Exception as exc:
            debug(f"Post-bake ghost regeneration failed (non-fatal): {exc}")


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

CLASSES: tuple[type, ...] = (
    GHOST_OT_physics_suggest,
    GHOST_OT_archetype_bake,
)


def register() -> None:
    """Register physics suggestion and archetype bake classes."""
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    """Unregister physics suggestion and archetype bake classes."""
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
