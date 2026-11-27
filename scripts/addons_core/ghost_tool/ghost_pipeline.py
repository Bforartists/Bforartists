"""
ghost_pipeline.py — Central orchestrator for the ghost generation pipeline.

This module provides the GhostPipeline class, the single entry point for
all ghost generation flows.  Whether the user clicks "Generate" manually,
or live mode auto-updates on frame change, everything flows through here.

Pipeline stages:
    1. Frame Source — determine which frames to ghost (from settings)
    2. Evaluate — sample f-curves and world positions at those frames
    3. Cache — store results, check dirty flags
    4. Notify — update GhostStore, tag viewport for redraw

The pipeline also manages live-update handlers (frame_change_post,
depsgraph_update_post) that are registered/unregistered based on the
live_point_ghosts / live_mesh_ghosts settings.

CRITICAL DESIGN NOTE:
    Ghost generation calls scene.frame_set(), which is FORBIDDEN inside
    draw handlers and frame_change handlers.  Live updates therefore use
    bpy.app.timers to defer generation to the next idle tick.  The flow:
        frame_change_post → mark_dirty + schedule timer
        timer fires (safe context) → _run_live_update → scene.frame_set OK
        viewport tagged for redraw → draw handler reads GhostStore only

Design goals:
    - Single code path for manual and live generation
    - Throttled updates to prevent performance tanking during scrubbing
    - Dirty-flag system so only changed data is re-evaluated
    - Clean handler lifecycle tied to addon register/unregister
    - Generation NEVER runs inside draw or handler contexts
"""

from __future__ import annotations

import time
import hashlib
from typing import Optional

import bpy

from .ghost_data import (
    Ghost,
    GhostStore,
    generate_ghosts,
    generate_ghosts_frame_step,
    generate_ghosts_at_keyframes,
    build_frame_list_from_settings,
    MOTION_CHANNELS,
)
from .ghost_cache import GhostCache
from .session_state import SessionState
from .utils import (is_sampling, is_native_transform_active, get_fcurves_from_action,
                    _POSE_PROPERTIES, _DELTA_PROPERTIES,
                    log, warn, debug, get_scene_id, tag_viewport_redraw)

# ---------------------------------------------------------------------------
# Bake state flags — read by the 2D draw handler for HUD and preview
# ---------------------------------------------------------------------------

_BAKE_IN_PROGRESS: bool = False
"""True while a bake/generation is running.  The draw handler reads this
to show the warm-up progress ring and render partial ghosts from the
staging store."""

_staging_store: Optional[GhostStore] = None
"""Shadow buffer filled incrementally during a bake pass.  The 2D and 3D
draw handlers render from this store when it is not None, providing a
live preview of partially-baked ghosts.  Set to None when the bake
completes and the results are swapped into the main GhostStore."""


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_THROTTLE_SEC: float = 0.05
"""Minimum seconds between live updates (50ms = ~20 updates/sec max)."""

EDIT_SETTLE_SEC = 0.15
"""Wait for the last authored change before sampling a completed gesture."""


def _rna_controls(block):
    values = []
    for prop in block.bl_rna.properties:
        if prop.is_readonly or prop.identifier in {'name', 'show_expanded', 'select'}:
            continue
        value = getattr(block, prop.identifier)
        if prop.type in {'BOOLEAN', 'INT', 'FLOAT', 'STRING', 'ENUM'}:
            values.append((prop.identifier, tuple(value) if getattr(prop, 'is_array', False) else value))
        elif prop.type == 'POINTER':
            values.append((prop.identifier, value.as_pointer() if value else 0))
    return tuple(values)


def _edit_state(block):
    """Original inputs distinguish edits from selection and our own evaluations."""
    if isinstance(block, bpy.types.Object):
        if block.get('ghost_tool_mesh_ghost') or block.get('ghost_tool_mesh_parent'):
            return None
        holders = [(block, _POSE_PROPERTIES + _DELTA_PROPERTIES)]
        if block.pose:
            holders += [(bone, _POSE_PROPERTIES) for bone in block.pose.bones]
        values = []
        for holder, properties in holders:
            for name in properties:
                value = getattr(holder, name)
                values.append(value if isinstance(value, str) else tuple(value))
            values.append(tuple(sorted((name, value) for name, value in holder.items()
                                       if isinstance(value, (bool, int, float)))))
        values.append(tuple(_rna_controls(c) for c in block.constraints))
        values.append(tuple(_rna_controls(m) for m in block.modifiers))
        if block.pose:
            values.append(tuple(tuple(_rna_controls(c) for c in bone.constraints)
                                for bone in block.pose.bones))
        data = block.animation_data
        values.append((data.action.as_pointer() if data and data.action else 0,
                       getattr(data, 'action_slot_handle', 0) if data else 0))
        return tuple(values)
    if isinstance(block, bpy.types.Action):
        return tuple((fc.data_path, fc.array_index, fc.mute, fc.extrapolation,
                      tuple((tuple(k.co), tuple(k.handle_left), tuple(k.handle_right),
                             k.handle_left_type, k.handle_right_type, k.interpolation,
                             k.easing, k.amplitude, k.back, k.period)
                            for k in fc.keyframe_points),
                      tuple(_rna_controls(m) for m in fc.modifiers))
                     for fc in get_fcurves_from_action(block))
    if isinstance(block, bpy.types.Key):
        return tuple((key.name, key.value, key.mute) for key in block.key_blocks)
    if isinstance(block, bpy.types.Mesh):
        import numpy as np
        if block.is_editmode:
            import bmesh
            mesh = bmesh.from_edit_mesh(block)
            indices = {v: i for i, v in enumerate(mesh.verts)}
            arrays = (np.asarray([tuple(v.co) for v in mesh.verts], dtype=np.float32),
                      np.asarray([[indices[v] for v in edge.verts] for edge in mesh.edges], dtype=np.int32),
                      np.asarray([len(face.verts) for face in mesh.faces], dtype=np.int32),
                      np.asarray([indices[v] for face in mesh.faces for v in face.verts], dtype=np.int32))
        else:
            arrays = []
            for items, attribute, width, dtype in (
                    (block.vertices, 'co', 3, np.float32),
                    (block.edges, 'vertices', 2, np.int32),
                    (block.polygons, 'loop_total', 1, np.int32),
                    (block.loops, 'vertex_index', 1, np.int32)):
                array = np.empty(len(items) * width, dtype=dtype)
                items.foreach_get(attribute, array)
                arrays.append(array)
        return tuple(hashlib.blake2b(array.tobytes(), digest_size=16).digest() for array in arrays)
    return None

# Timestamp (monotonic) of the last depsgraph_update_post callback execution.
# Used to throttle expensive handler work during rapid scene updates.
_last_depsgraph_check: float = 0.0

# Timestamp (monotonic) of the last stale-instance pruning pass.
# Prevents orphaned GhostPipeline/GhostCache objects from accumulating.
_last_prune_time: float = 0.0

# Whether a deferred live-update timer is already scheduled.
# Prevents stacking multiple timers during rapid scrubbing.
_deferred_update_pending: bool = False


# ---------------------------------------------------------------------------
# GhostPipeline — per-scene orchestrator
# ---------------------------------------------------------------------------

class GhostPipeline:
    """Central orchestrator for ghost generation, caching, and live updates.

    One GhostPipeline instance exists per scene, mirroring the GhostStore
    and GhostCache singletons.  It coordinates:

    - Manual generation (user clicks Generate)
    - Live point ghost updates (frame_change_post)
    - Live mesh ghost updates (frame_change_post, throttled)
    - Dirty detection (settings changed, keyframe edited, frame moved)
    - Throttling to prevent performance issues during scrubbing

    Usage:
        pipeline = GhostPipeline.get(scene)
        pipeline.generate_manual(context)     # manual mode
        pipeline.mark_dirty()                 # flag for live update
        pipeline.update_if_needed(context)    # called from deferred timer
    """

    # Per-scene singleton instances
    _instances: dict[str, GhostPipeline] = {}

    # =========================================================================
    # Initialization
    # =========================================================================

    def __init__(self, scene_id: str) -> None:
        """Initialize the pipeline for a scene.

        Args:
            scene_id: The stable unique ID of the Blender scene this pipeline manages.
        """
        self._scene_id: str = scene_id
        self._cache: Optional[GhostCache] = None
        self._edit_states = {}
        self._edit_pending = False
        self._last_edit_time = 0.0

    # --- Singleton access ---

    @classmethod
    def get(cls, scene: bpy.types.Scene) -> GhostPipeline:
        """Retrieve or create the GhostPipeline for a scene.

        Args:
            scene: The Blender scene.

        Returns:
            GhostPipeline: The pipeline instance for this scene.
        """
        key = get_scene_id(scene)
        if key not in cls._instances:
            cls._instances[key] = cls(key)
            cls._instances[key].remember_edit_state(scene)
        return cls._instances[key]

    @classmethod
    def clear_instance(cls, scene_name: str) -> None:
        """Remove the pipeline instance for a scene."""
        cls._instances.pop(scene_name, None)

    @classmethod
    def clear_all_instances(cls) -> None:
        """Remove all pipeline instances (addon unregistration)."""
        cls._instances.clear()

    @classmethod
    def prune_stale(cls) -> int:
        """Remove pipeline instances for scenes that no longer exist."""
        import bpy
        current_scene_ids = {get_scene_id(s) for s in bpy.data.scenes}
        stale = [key for key in cls._instances if key not in current_scene_ids]
        for key in stale:
            del cls._instances[key]
        return len(stale)

    # --- Cache access ---

    def _get_cache(self) -> GhostCache:
        """Lazily get or create the cache for this scene.

        Returns:
            GhostCache: The cache instance.
        """
        if self._cache is None:
            self._cache = GhostCache.get(self._scene_id)
        return self._cache

    # --- Dirty flag pass-through ---

    def remember_edit_state(self, scene):
        """Establish the settled pose without treating a seek or bake as an edit."""
        blocks = list(scene.objects) + list(bpy.data.actions)
        blocks += [obj.data for obj in scene.objects if obj.type == 'MESH'
                   and not obj.get('ghost_tool_mesh_ghost')]
        blocks += [obj.data.shape_keys for obj in scene.objects
                   if getattr(obj.data, 'shape_keys', None)]
        self._edit_states = {block.as_pointer(): state for block in blocks
                             if (state := _edit_state(block)) is not None}

    def note_animation_edit(self, block):
        # Bakes update ghost mesh datablocks too. Only original source geometry
        # belongs to the input baseline; never feed our output back into a bake.
        if isinstance(block, bpy.types.Mesh) and block.as_pointer() not in self._edit_states:
            return False
        state = _edit_state(block)
        if state is None or self._edit_states.get(block.as_pointer()) == state:
            return False
        self._edit_states[block.as_pointer()] = state
        self._edit_pending = True
        self._last_edit_time = time.monotonic()
        self.mark_dirty()
        return True

    def edit_wait(self):
        if self._edit_pending:
            return max(0.0, EDIT_SETTLE_SEC - (time.monotonic() - self._last_edit_time))
        return 0.0

    def mark_dirty(self) -> None:
        """Mark the pipeline as needing regeneration.

        Called by frame_change or depsgraph_update handlers, or when
        the user changes settings.
        """
        self._get_cache().mark_dirty()

    def mark_object_dirty(self, object_name: str) -> None:
        """Mark a specific object as needing re-evaluation.

        Called when a keyframe is edited on a specific object.

        Args:
            object_name: The name of the modified object.
        """
        self._get_cache().mark_object_dirty(object_name)

    # --- Manual generation (user clicks Generate) ---

    def generate_manual(
        self,
        context: bpy.types.Context,
        obj: bpy.types.Object,
        armature: Optional[bpy.types.Object],
        bones: list[str],
        channels: list[str],
        level: int,
        frame_range: Optional[tuple[int, int]] = None,
        clear_existing: bool = True,
    ) -> int:
        """Run a full ghost generation pass (manual / button-press mode).

        This is the equivalent of the old generate_and_store_ghosts() but
        routed through the pipeline for cache awareness.

        Args:
            context: The current Blender context.
            obj: The object to generate ghosts for.
            armature: The armature (or None).
            bones: Pose bone names.
            channels: Channel identifiers.
            level: Subdivision depth (for SUBDIVISION mode).
            frame_range: Optional frame range.
            clear_existing: Whether to clear existing ghosts first.

        Returns:
            int: Number of ghosts generated.
        """
        cache = self._get_cache()
        store = GhostStore.get(context.scene)
        settings = context.scene.ghost_tool

        # Determine generation mode from settings; ghost_mode: SUBDIVISION, FRAME_STEP, or KEYFRAMES_ONLY
        mode = settings.ghost_mode

        debug(f"Manual generate: mode={mode}, obj={obj.name}")

        # Run the appropriate generator
        ghosts = self._evaluate_ghosts(
            context, obj, armature, bones, channels, level, frame_range, mode, settings
        )

        # Publish only after evaluation succeeds.
        if clear_existing:
            cache.invalidate_all()
        fresh, owned = _defer_to_path_markers(context.scene, ghosts)
        store.replace_all(fresh + owned if clear_existing else store.all_ghosts + fresh)

        # Update cache metadata
        cache.last_frame = context.scene.frame_current
        cache.update_settings_hash(compute_settings_hash(settings))
        cache.mark_clean()
        self.remember_edit_state(context.scene)

        debug(f"Generated {len(ghosts)} ghosts, cache clean.")

        return len(ghosts)

    def generate_manual_with_preview(
        self,
        context: bpy.types.Context,
        obj: bpy.types.Object,
        armature: Optional[bpy.types.Object],
        bones: list[str],
        channels: list[str],
        level: int,
        frame_range: Optional[tuple[int, int]] = None,
        clear_existing: bool = True,
    ) -> int:
        """Run a full ghost generation pass with live preview via shadow buffer.

        Identical to ``generate_manual()`` but populates ``_staging_store``
        ghost-by-ghost so the draw handler can render partial results while
        the bake is in progress.  The ``_BAKE_IN_PROGRESS`` flag is set for
        the duration of the bake so the Mode Label HUD and Progress Ring are
        active.

        On completion the staging contents are atomically swapped into the
        main ``GhostStore`` and the bake flags are cleared.

        Args:
            context: The current Blender context.
            obj: The object to generate ghosts for.
            armature: The armature (or None).
            bones: Pose bone names.
            channels: Channel identifiers.
            level: Subdivision depth (for SUBDIVISION mode).
            frame_range: Optional frame range.
            clear_existing: Whether to clear existing ghosts first.

        Returns:
            int: Number of ghosts generated.
        """
        global _BAKE_IN_PROGRESS, _staging_store

        cache = self._get_cache()
        store = GhostStore.get(context.scene)
        settings = context.scene.ghost_tool

        mode = settings.ghost_mode
        debug(f"Manual generate (with preview): mode={mode}, obj={obj.name}")

        # --- Shadow buffer setup ---
        _staging_store = GhostStore()
        _BAKE_IN_PROGRESS = True
        # Initialize here so the finally block always has a valid reference
        # even if _evaluate_ghosts raises before populating the staging store.
        final_ghosts: list[Ghost] = []

        try:
            # Evaluate all ghosts first, then populate the staging store atomically.
            # True ghost-by-ghost streaming would require converting _evaluate_ghosts
            # to a generator; the current batch-populate approach means the staging
            # store is fully populated before the first viewport preview, but the
            # _BAKE_IN_PROGRESS flag and progress ring are still visible during the
            # evaluation phase.
            all_ghosts: list[Ghost] = self._evaluate_ghosts(
                context, obj, armature, bones, channels, level, frame_range, mode, settings
            )
            _staging_store.replace_all(all_ghosts)
            final_ghosts = all_ghosts
            if clear_existing:
                cache.invalidate_all()
            fresh, owned = _defer_to_path_markers(context.scene, all_ghosts)
            store.replace_all(fresh + owned if clear_existing else store.all_ghosts + fresh)
            tag_viewport_redraw(context)

        finally:
            # Failed evaluation leaves the previous store intact.
            _BAKE_IN_PROGRESS = False
            _staging_store = None

        # Update cache metadata
        cache.last_frame = context.scene.frame_current
        cache.update_settings_hash(compute_settings_hash(settings))
        cache.mark_clean()
        self.remember_edit_state(context.scene)

        debug(f"Generated {len(final_ghosts)} ghosts (with preview), cache clean.")
        tag_viewport_redraw(context)
        return len(final_ghosts)

    # --- Live update check (called from draw handler or timer) ---

    def update_if_needed(self, context: bpy.types.Context) -> bool:
        """Check if regeneration is needed and run it if so.

        This is designed to be called frequently (e.g., every draw cycle).
        It checks dirty flags and throttle timing before doing any work.

        Args:
            context: The current Blender context.

        Returns:
            bool: True if an update was performed.
        """
        scene = context.scene
        if not hasattr(scene, 'ghost_tool'):
            return False

        settings = scene.ghost_tool

        # Only run if any live mode is enabled
        if not _any_live(settings) and not self._edit_pending:
            return False

        # Keep the store stable while a modal drag holds ghost references.
        if SessionState.get(scene).drag_active or is_native_transform_active(context):
            return False
        if self.edit_wait():
            return False

        # Check freeze
        if settings.live_freeze:
            return False

        # Skip during playback to avoid performance issues
        if context.screen and context.screen.is_animation_playing:
            return False

        cache = self._get_cache()

        # Check if anything changed
        current_frame = scene.frame_current
        new_hash = compute_settings_hash(settings)

        frame_changed = cache.last_frame != current_frame
        settings_changed = cache.needs_settings_update(new_hash)

        if not frame_changed and not settings_changed and not cache.is_dirty:
            debug("Settings hash unchanged, skipping regeneration")
            return False

        # Throttle check
        throttle_ms = settings.live_throttle_ms
        throttle_sec = throttle_ms / 1000.0
        now = time.monotonic()
        if now - cache.last_update_time <= throttle_sec:
            return False

        reason = []
        if frame_changed:
            reason.append(f"frame:{cache.last_frame}->{current_frame}")
        if settings_changed:
            reason.append("settings")
        if cache.is_dirty:
            reason.append("dirty")
        debug(f"Live update triggered: {', '.join(reason)}")

        # Run the generation
        self._run_live_update(context, settings, new_hash)
        return True

    # =========================================================================
    # Live Updates
    # =========================================================================

    def _run_live_update(
        self,
        context: bpy.types.Context,
        settings: bpy.types.PropertyGroup,
        settings_hash: str,
    ) -> None:
        """Execute a live regeneration pass.

        Uses the same generation logic as manual mode but operates on
        the active object automatically.

        Args:
            context: The Blender context.
            settings: GhostToolSceneSettings.
            settings_hash: Pre-computed hash of current settings.
        """
        if settings.paths_enabled:
            try:
                from . import motion_paths
                motion_paths.refresh_paths(context)
                if settings.paths_show_markers:
                    motion_paths.sync_markers(context)   # keep markers on the moving window
            except Exception as exc:
                warn(f"Motion paths refresh error: {exc}")

        obj = context.active_object
        if not obj:
            return

        cache = self._get_cache()

        # Scrub toggles control timeline following. Completed edits also refresh
        # existing snapshots, even when timeline following is disabled.
        from .motion_paths import owned_markers
        owned = {g.uid for g in owned_markers(context.scene)}
        live_points = settings.live_point_ghosts or (
            self._edit_pending and any(g.uid not in owned for g in GhostStore.get(context.scene)))
        from .mesh_ghosts import _private_mesh_collection
        collection = _private_mesh_collection(context.scene)
        live_mesh = settings.live_mesh_ghosts or (
            self._edit_pending and collection is not None
            and any(obj.get('ghost_tool_mesh_ghost') for obj in collection.objects))

        # Update point ghosts if enabled
        if live_points:
            self._update_point_ghosts_live(context, obj, settings)

        # Update cache state
        cache.last_frame = context.scene.frame_current
        cache.update_settings_hash(settings_hash)
        cache.mark_clean()

        # Update mesh ghosts if enabled
        if live_mesh and settings.show_mesh_ghosts:
            self._update_mesh_ghosts_live(context, settings)

        self._edit_pending = False
        self.remember_edit_state(context.scene)

        # Tag viewport for redraw
        tag_viewport_redraw(context)

    def _update_point_ghosts_live(
        self,
        context: bpy.types.Context,
        obj: bpy.types.Object,
        settings: bpy.types.PropertyGroup,
    ) -> None:
        """Update point ghosts in live mode.

        Evaluates and stores point ghosts for the active object if it has
        animation data. Skips silently if there's no animation.

        Args:
            context: Blender context.
            obj: The object to update point ghosts for.
            settings: GhostToolSceneSettings.
        """
        if not obj.animation_data or not obj.animation_data.action:
            # No animation data — can't generate point ghosts
            debug(f"No animation data on {obj.name}, skipping live update")
            return

        store = GhostStore.get(context.scene)

        # Determine bones and armature
        bones: list[str] = []
        armature = None
        if obj.type == 'ARMATURE':
            armature = obj
            # Try selected pose bones first (Pose Mode)
            if context.selected_pose_bones:
                bones = [b.name for b in context.selected_pose_bones]
            elif obj.data.bones:
                # Try bones marked as selected
                bones = [b.name for b in obj.pose.bones if getattr(b, "select", getattr(b.bone, "select", False))]
            # Fallback: use all bones if none are selected (e.g. Object Mode)
            if not bones and obj.pose and obj.pose.bones:
                bones = [b.name for b in obj.pose.bones]

        # Determine frame range; ghost_range_mode: AROUND_CURSOR, FULL_TIMELINE, BETWEEN_KEYS, or CUSTOM
        frame_range = None
        range_mode = settings.ghost_range_mode
        if range_mode == "CUSTOM":
            frame_range = (settings.custom_range_start, settings.custom_range_end)
        elif range_mode == "FULL_TIMELINE":
            frame_range = (context.scene.frame_start, context.scene.frame_end)

        mode = settings.ghost_mode
        # Every animated location and rotation channel; rotation markers follow the bone tail.
        channels = MOTION_CHANNELS

        # Evaluate and store
        ghosts = self._evaluate_ghosts(
            context, obj, armature, bones, channels,
            settings.subdivision_level, frame_range, mode, settings
        )
        fresh, owned = _defer_to_path_markers(context.scene, ghosts)
        store.replace_all(fresh + owned)

    def _update_mesh_ghosts_live(
        self,
        context: bpy.types.Context,
        settings: bpy.types.PropertyGroup,
    ) -> None:
        """Attempt incremental mesh ghost update; fall back to full rebuild.

        First tries the fast foreach_set path.  If that fails (frame window
        shifted, topology changed, no existing ghosts), does a full
        generate_mesh_ghosts() call instead.

        Args:
            context: Blender context.
            settings: GhostToolSceneSettings.
        """
        try:
            from .mesh_ghosts import (
                update_mesh_ghosts_incremental,
                generate_mesh_ghosts,
                resolve_mesh_objects,
                ghost_source_objects,
                _compute_desired_mesh_frames_from_settings,
            )

            # Try incremental first (fast path)
            success = update_mesh_ghosts_incremental(context)

            if not success:
                # Need full rebuild — frame window shifted or no existing ghosts
                obj = ghost_source_objects(context)
                if not resolve_mesh_objects(obj):
                    return

                current_frame = context.scene.frame_current
                past_count = settings.mesh_ghost_past_count
                future_count = settings.mesh_ghost_future_count
                # mesh_ghost_mode: display style for mesh ghosts (SOLID, WIREFRAME, BOUNDS)
                mode = settings.mesh_ghost_mode

                # Use the unified frame computation (handles both STEP and KEYFRAMES modes)
                ghost_frames = sorted(
                    _compute_desired_mesh_frames_from_settings(
                        settings, current_frame, context.scene, obj
                    )
                )

                generate_mesh_ghosts(
                    context=context,
                    source_obj=obj,
                    ghost_frames=ghost_frames,
                    mode=mode,
                    past_count=past_count,
                    future_count=future_count,
                    step=1,
                )

                debug("Mesh ghosts: full rebuild")
            else:
                debug("Mesh ghosts: incremental update")

        except Exception as exc:
            warn(f"Mesh ghost update error: {exc}")

    # =========================================================================
    # Ghost Evaluation (shared by manual and live)
    # =========================================================================

    def _evaluate_ghosts(
        self,
        context: bpy.types.Context,
        obj: bpy.types.Object,
        armature: Optional[bpy.types.Object],
        bones: list[str],
        channels: list[str],
        level: int,
        frame_range: Optional[tuple[int, int]],
        mode: str,
        settings: bpy.types.PropertyGroup,
    ) -> list[Ghost]:
        """Evaluate ghosts using the appropriate generator.

        This is the shared evaluation logic used by both manual and live
        generation paths.

        Args:
            context: Blender context.
            obj: Target object.
            armature: Armature (or None).
            bones: Bone names.
            channels: Channel identifiers.
            level: Subdivision depth.
            frame_range: Optional frame range.
            mode: Ghost mode string (SUBDIVISION, FRAME_STEP, KEYFRAMES_ONLY).
            settings: GhostToolSceneSettings.

        Returns:
            list[Ghost]: Evaluated ghost objects.
        """
        # FRAME_STEP mode: generate ghosts at fixed frame intervals
        if mode == "FRAME_STEP":
            frame_list = build_frame_list_from_settings(settings, context.scene)
            return generate_ghosts_frame_step(obj, armature, bones, channels, frame_list)
        # KEYFRAMES_ONLY mode: generate ghosts only at existing keyframes
        elif mode == "KEYFRAMES_ONLY":
            return generate_ghosts_at_keyframes(obj, armature, bones, channels, frame_range)
        else:
            # SUBDIVISION — original mode or unknown mode fallback
            if mode != "SUBDIVISION":
                warn(f"Unknown ghost mode '{mode}', falling back to SUBDIVISION")
            return generate_ghosts(obj, armature, bones, channels, level, frame_range)

    # =========================================================================
    # Cache Management
    # =========================================================================

    def clear(self, context: bpy.types.Context) -> int:
        """Clear all ghosts and cache for this scene.

        Args:
            context: Blender context.

        Returns:
            int: Number of ghosts that were cleared.
        """
        store = GhostStore.get(context.scene)
        count = len(store)
        store.clear()

        cache = self._get_cache()
        cache.invalidate_all()

        debug(f"Cleared {count} ghosts + cache.")

        return count


# ---------------------------------------------------------------------------
# Settings hash — detect when properties change
# ---------------------------------------------------------------------------

def _any_live(settings) -> bool:
    return bool(settings.live_point_ghosts or settings.live_mesh_ghosts or settings.paths_enabled)


def _defer_to_path_markers(scene, ghosts: list) -> tuple[list, list]:
    """(generated ghosts not already covered by a path marker, the path markers).

    Markers on Paths live in the same store; a rebuild keeps them, and a generated ghost
    on the same object/bone/channel/frame defers to the path marker instead of doubling it."""
    from . import motion_paths
    owned = motion_paths.owned_markers(scene)
    taken = {(g.object_name, g.bone_name, g.channel, g.frame) for g in owned}
    fresh = [g for g in ghosts if (g.object_name, g.bone_name, g.channel, g.frame) not in taken]
    pinned = {(g.object_name, g.bone_name, g.channel, g.frame)
              for g in GhostStore.get(scene).get_pinned()}
    for ghost in fresh + owned:
        if (ghost.object_name, ghost.bone_name, ghost.channel, ghost.frame) in pinned:
            ghost.is_pinned = True
    return fresh, owned


# WARNING: When adding new settings properties to GhostToolSceneSettings,
# you MUST add them here too, or cache invalidation will silently break.
def compute_settings_hash(settings: bpy.types.PropertyGroup) -> str:
    """Compute a hash string from ghost tool settings for change detection.

    This captures all settings that affect ghost generation so the pipeline
    can detect when regeneration is needed. Any change to these properties
    invalidates the cache and triggers a full regeneration on the next update.

    Args:
        settings: GhostToolSceneSettings PropertyGroup.

    Returns:
        str: A short hash string representing the current settings state.
    """
    # Only include properties that affect ghost GENERATION (positions, frames, counts).
    # Rendering-only properties (colors, visibility, line styles) should NOT be included
    # because they don't change which ghosts exist or where they are.
    # Current generation-affecting property count: 16
    # Collect all generation-affecting properties into a fingerprint tuple
    # NOTE: When adding new settings to GhostToolSceneSettings, add them here too
    settings_fingerprint = (
        settings.ghost_mode,
        settings.ghost_range_mode,
        settings.subdivision_level,
        settings.frame_step,
        settings.ghosts_before,
        settings.ghosts_after,
        settings.custom_range_start,
        settings.custom_range_end,
        settings.show_mesh_ghosts,
        settings.mesh_ghost_past_count,
        settings.mesh_ghost_future_count,
        settings.mesh_ghost_step,
        settings.mesh_ghost_opacity,
        settings.mesh_ghost_frame_mode,
        settings.mesh_ghost_keyframe_skip,
        settings.mesh_ghost_keyframe_skip_custom,
        settings.paths_enabled,
        settings.paths_follow_selection,
        settings.paths_range_mode,
        settings.paths_before,
        settings.paths_after,
        settings.paths_step,
    )

    # Use a fast hash — we don't need cryptographic strength
    return str(hash(settings_fingerprint))


# ---------------------------------------------------------------------------
# Handler Management for Live Mode
# ---------------------------------------------------------------------------

# Module-level references for handler registration/removal.
# These store handler function objects to enable safe unregistration later.
_frame_change_handler = None
_depsgraph_update_handler = None


# ---------------------------------------------------------------------------
# Deferred live update — runs generation via bpy.app.timers, outside draw
# ---------------------------------------------------------------------------

def _schedule_deferred_update() -> None:
    """Schedule a deferred live update if one isn't already pending.

    Uses bpy.app.timers to run the generation on the next idle tick,
    safely outside any draw handler or frame_change handler context
    where scene.frame_set() is forbidden.
    """
    global _deferred_update_pending
    if _deferred_update_pending:
        return
    _deferred_update_pending = True
    bpy.app.timers.register(_deferred_live_update, first_interval=0.0)


def _deferred_live_update() -> Optional[float]:
    """Timer callback that performs the actual live ghost regeneration.

    This runs in a safe context where scene.frame_set() is allowed.
    Returns a delay when throttled or dragging; None finishes the timer.
    """
    global _deferred_update_pending
    _deferred_update_pending = False

    try:
        context = bpy.context
        scene = context.scene
        if not scene or not hasattr(scene, 'ghost_tool'):
            return None

        settings = scene.ghost_tool
        if not settings.is_active:
            return None

        pipeline = GhostPipeline.get(scene)
        if not _any_live(settings) and not pipeline._edit_pending:
            return None

        if settings.live_freeze:
            return None

        if SessionState.get(scene).drag_active or is_native_transform_active(context):
            if pipeline._edit_pending:
                pipeline._last_edit_time = time.monotonic()
            _deferred_update_pending = True
            return 0.05

        wait = pipeline.edit_wait()
        if wait:
            _deferred_update_pending = True
            return max(0.01, wait)

        # Playback: wait and retry, so the frame it stops on gets ghosts even
        # if nothing fires a frame_change afterwards.
        if context.screen and context.screen.is_animation_playing:
            _deferred_update_pending = True
            return 0.25

        cache = pipeline._get_cache()

        # Throttle check
        throttle_ms = settings.live_throttle_ms
        throttle_sec = throttle_ms / 1000.0
        now = time.monotonic()
        if now - cache.last_update_time <= throttle_sec:
            # Let Blender reschedule this same timer while still dirty
            if cache.is_dirty:
                _deferred_update_pending = True
                return max(0.01, throttle_sec - (now - cache.last_update_time))
            return None

        # Check if anything actually changed
        current_frame = scene.frame_current
        new_hash = compute_settings_hash(settings)
        frame_changed = cache.last_frame != current_frame
        settings_changed = cache.needs_settings_update(new_hash)

        if not frame_changed and not settings_changed and not cache.is_dirty:
            return None

        reason = []
        if frame_changed:
            reason.append(f"frame:{cache.last_frame}->{current_frame}")
        if settings_changed:
            reason.append("settings")
        if cache.is_dirty:
            reason.append("dirty")
        debug(f"Deferred live update triggered: {', '.join(reason)}")

        # Run the actual generation
        pipeline._run_live_update(context, settings, new_hash)

        # Tag viewport for redraw to show the new ghosts
        tag_viewport_redraw(context)

    except Exception as exc:
        warn(f"Deferred live update error: {exc}")

    return None


# ---------------------------------------------------------------------------
# Forced mesh ghost regeneration — bypasses live-mode checks
# ---------------------------------------------------------------------------
_forced_mesh_regen_pending = False
_in_forced_regen = False  # Guard: suppresses depsgraph handler during forced rebuild


def _schedule_forced_mesh_regen() -> None:
    """Schedule a forced mesh ghost regeneration via timer.

    Unlike _schedule_deferred_update(), this bypasses the live-mode gate
    so that settings changes (e.g. switching Frame Step <-> Keyframes Only)
    take effect immediately regardless of whether live mode is on or off.
    """
    global _forced_mesh_regen_pending
    if _forced_mesh_regen_pending:
        return
    _forced_mesh_regen_pending = True
    bpy.app.timers.register(_forced_mesh_regen_callback, first_interval=0.0)


def _forced_mesh_regen_callback() -> Optional[float]:
    """Timer callback that forces a FULL mesh ghost rebuild.

    Unlike _update_mesh_ghosts_live which tries incremental first,
    this always clears and fully regenerates so that frame list changes
    (e.g. switching Frame Step <-> Keyframes Only) take effect immediately.
    """
    global _forced_mesh_regen_pending, _in_forced_regen
    _forced_mesh_regen_pending = False

    try:
        context = bpy.context
        scene = context.scene
        if not scene or not hasattr(scene, 'ghost_tool'):
            return None

        settings = scene.ghost_tool
        if not settings.is_active or not settings.show_mesh_ghosts:
            return None

        if SessionState.get(scene).drag_active or is_native_transform_active(context):
            _forced_mesh_regen_pending = True
            return 0.05

        pipeline = GhostPipeline.get(scene)
        wait = pipeline.edit_wait()
        if wait:
            _forced_mesh_regen_pending = True
            return max(0.01, wait)

        from .mesh_ghosts import (
            clear_mesh_ghosts,
            generate_mesh_ghosts,
            resolve_mesh_objects,
            ghost_source_objects,
            _compute_desired_mesh_frames_from_settings,
        )

        # Set guard so depsgraph handler ignores our clear/generate operations
        _in_forced_regen = True

        frame_mode = settings.mesh_ghost_frame_mode
        print(f"[GhostTool] Forced regen START (frame_mode={frame_mode})")

        obj = ghost_source_objects(context)
        if not obj:
            print("[GhostTool] Forced regen ABORT: no character selected")
            return None

        if not resolve_mesh_objects(obj):
            print(f"[GhostTool] Forced regen ABORT: no mesh for {[o.name for o in obj]}")
            return None

        current_frame = scene.frame_current
        past_count = settings.mesh_ghost_past_count
        future_count = settings.mesh_ghost_future_count
        mode = settings.mesh_ghost_mode

        ghost_frames = sorted(
            _compute_desired_mesh_frames_from_settings(
                settings, current_frame, scene, obj
            )
        )

        print(f"[GhostTool] Forced regen: {len(ghost_frames)} frames "
              f"(mode={frame_mode}, past={past_count}, future={future_count}, "
              f"cur={current_frame}) → {ghost_frames[:8]}{'...' if len(ghost_frames) > 8 else ''}")

        if ghost_frames:
            generate_mesh_ghosts(
                context=context,
                source_obj=obj,
                ghost_frames=ghost_frames,
                mode=mode,
                past_count=past_count,
                future_count=future_count,
                step=1,
            )

        else:
            clear_mesh_ghosts(context)

        # Update cache state so the pipeline knows we're current
        pipeline = GhostPipeline.get(scene)
        cache = pipeline._get_cache()
        cache.last_frame = current_frame
        new_hash = compute_settings_hash(settings)
        cache.update_settings_hash(new_hash)
        cache.mark_clean()
        pipeline._edit_pending = False
        pipeline.remember_edit_state(scene)

        # Tag viewport for redraw
        tag_viewport_redraw(context)

        print(f"[GhostTool] Forced regen DONE")

    except Exception as exc:
        warn(f"Forced mesh regen error: {exc}")
    finally:
        _in_forced_regen = False

    return None


@bpy.app.handlers.persistent
def _on_frame_change_pipeline(scene: bpy.types.Scene, depsgraph=None) -> None:
    """Handler called on frame_change_post.

    Schedules a deferred live update via bpy.app.timers so that ghost
    generation (which calls scene.frame_set) runs outside the draw/handler
    context where frame_set is forbidden.

    Args:
        scene: The scene that changed.
        depsgraph: The dependency graph (unused, but required by Blender).
    """
    if is_sampling() or not hasattr(scene, 'ghost_tool'):
        return

    settings = scene.ghost_tool
    if not settings.is_active:
        return

    # Evaluated movement caused by seeking is not an animation edit. Keep the
    # baseline current even when scrub updates are disabled.
    pipeline = GhostPipeline.get(scene)
    pipeline.remember_edit_state(scene)

    # Only schedule if any live mode is enabled
    if not _any_live(settings):
        return

    if settings.live_freeze:
        return

    pipeline.mark_dirty()
    _schedule_deferred_update()


@bpy.app.handlers.persistent
def _on_playback_post(scene: bpy.types.Scene, *_args) -> None:
    """Playback stopped: bring live ghosts to the frame it stopped on."""
    if is_sampling() or not hasattr(scene, 'ghost_tool'):
        return
    settings = scene.ghost_tool
    if not settings.is_active or settings.live_freeze:
        return
    if not _any_live(settings):
        return
    GhostPipeline.get(scene).mark_dirty()
    _schedule_deferred_update()


@bpy.app.handlers.persistent
def _on_depsgraph_update_pipeline(scene: bpy.types.Scene, depsgraph=None) -> None:
    """Handler called on depsgraph_update_post.

    Detects keyframe edits and marks the affected object dirty so live update
    will regenerate ghosts on the next draw cycle.

    Args:
        scene: The scene that was updated.
        depsgraph: The dependency graph with update info.
    """
    if is_sampling() or not hasattr(scene, 'ghost_tool'):
        return

    # Skip if a forced regen is in progress — our own clear/generate
    # operations trigger depsgraph updates that would cause a race condition
    if _in_forced_regen:
        return

    settings = scene.ghost_tool
    if not settings.is_active:
        return

    # Completed animation edits refresh visible snapshots too. The live toggles
    # decide only whether the snapshots follow timeline movement.
    from .mesh_ghosts import _private_mesh_collection
    collection = _private_mesh_collection(scene)
    if (not _any_live(settings) and not GhostStore.get(scene).all_ghosts
            and not (settings.show_mesh_ghosts and collection is not None and collection.objects)):
        return

    if depsgraph is None:
        return

    # Time-based debounce to cap at ~60Hz
    global _last_depsgraph_check, _last_prune_time
    now = time.monotonic()
    if now - _last_depsgraph_check < 0.016:  # Cap at ~60Hz
        return
    _last_depsgraph_check = now

    # Periodically prune caches for deleted scenes (every ~60 seconds)
    if now - _last_prune_time > 60.0:
        GhostCache.prune_stale_scenes()
        GhostPipeline.prune_stale()
        _last_prune_time = now

    pipeline = GhostPipeline.get(scene)

    changed = False
    for update in depsgraph.updates:
        if hasattr(update, 'id') and update.id is not None:
            block = getattr(update.id, 'original', update.id)
            if not pipeline.note_animation_edit(block):
                continue
            changed = True
            try:
                from . import motion_paths
                motion_paths.mark_dirty_for_id(block)
            except Exception:
                pass
    if changed:
        _schedule_deferred_update()


def _register_live_handlers() -> None:
    """Register frame_change and depsgraph handlers for live mode.

    Safe to call multiple times — checks for existing registration.
    """
    global _frame_change_handler, _depsgraph_update_handler

    if _frame_change_handler is None:
        _frame_change_handler = _on_frame_change_pipeline
        if _frame_change_handler not in bpy.app.handlers.frame_change_post:
            bpy.app.handlers.frame_change_post.append(_frame_change_handler)
            debug("Registered frame_change_post handler.")

    if _depsgraph_update_handler is None:
        _depsgraph_update_handler = _on_depsgraph_update_pipeline
        if _depsgraph_update_handler not in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.append(_depsgraph_update_handler)
            debug("Registered depsgraph_update_post handler.")

    if _on_playback_post not in bpy.app.handlers.animation_playback_post:
        bpy.app.handlers.animation_playback_post.append(_on_playback_post)


def _unregister_live_handlers() -> None:
    """Remove frame_change and depsgraph handlers.

    Safe to call multiple times — handles already-removed handlers gracefully.
    """
    global _frame_change_handler, _depsgraph_update_handler

    if _frame_change_handler is not None:
        try:
            bpy.app.handlers.frame_change_post.remove(_frame_change_handler)
        except ValueError:
            debug("Handler frame_change_post already removed")
        _frame_change_handler = None
        debug("Unregistered frame_change_post handler.")

    if _depsgraph_update_handler is not None:
        try:
            bpy.app.handlers.depsgraph_update_post.remove(_depsgraph_update_handler)
        except ValueError:
            debug("Handler depsgraph_update_post already removed")
        _depsgraph_update_handler = None
        debug("Unregistered depsgraph_update_post handler.")

    try:
        bpy.app.handlers.animation_playback_post.remove(_on_playback_post)
    except ValueError:
        pass


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

@bpy.app.handlers.persistent
def _on_file_load(_unused):
    global _deferred_update_pending, _forced_mesh_regen_pending, _in_forced_regen
    global _BAKE_IN_PROGRESS, _staging_store
    _deferred_update_pending = _forced_mesh_regen_pending = _in_forced_regen = False
    _BAKE_IN_PROGRESS = False
    _staging_store = None
    for callback in (_deferred_live_update, _forced_mesh_regen_callback):
        if bpy.app.timers.is_registered(callback):
            bpy.app.timers.unregister(callback)
    GhostPipeline.clear_all_instances()
    GhostCache.clear_all_instances()
    GhostStore.clear_all_instances()
    SessionState.clear_all_instances()
    from . import motion_paths
    motion_paths.reset_for_new_file()
    from .snapshot import SnapshotStore
    from .ghost_data import DiffReference
    from .fcurve_utils import invalidate_keyframe_cache, clear_frame_cache
    from .physics_suggest import _clear_physics_preview
    from .viewport_draw import _batch_cache
    SnapshotStore.clear_all_instances()
    DiffReference.clear_all()
    invalidate_keyframe_cache()
    clear_frame_cache()
    _clear_physics_preview()
    _batch_cache.clear()
    _register_live_handlers()
    if bpy.context.scene and getattr(bpy.context.scene, 'ghost_tool', None):
        _schedule_deferred_update()


def register() -> None:
    """Register the pipeline module.

    Registers live-mode app handlers.  The handlers are lightweight
    (just set a dirty flag) so they're always registered — the pipeline's
    update_if_needed() checks the live toggle before doing real work.
    """
    _register_live_handlers()
    if _on_file_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_on_file_load)
    from .session_state import _on_undo_redo
    if _on_undo_redo not in bpy.app.handlers.undo_post:
        bpy.app.handlers.undo_post.append(_on_undo_redo)
    if _on_undo_redo not in bpy.app.handlers.redo_post:
        bpy.app.handlers.redo_post.append(_on_undo_redo)
    log("Ghost pipeline registered.")


def unregister() -> None:
    """Unregister the pipeline module.

    Removes app handlers and clears all pipeline instances.
    """
    from .session_state import _on_undo_redo
    if _on_file_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_file_load)
    try:
        bpy.app.handlers.undo_post.remove(_on_undo_redo)
    except ValueError:
        debug("Handler already removed")
    try:
        bpy.app.handlers.redo_post.remove(_on_undo_redo)
    except ValueError:
        debug("Handler already removed")
    global _deferred_update_pending, _forced_mesh_regen_pending, _in_forced_regen
    _deferred_update_pending = False
    _forced_mesh_regen_pending = False
    _in_forced_regen = False
    for callback in (_deferred_live_update, _forced_mesh_regen_callback):
        if bpy.app.timers.is_registered(callback):
            bpy.app.timers.unregister(callback)
    _unregister_live_handlers()
    GhostPipeline.clear_all_instances()
    GhostCache.clear_all_instances()
    log("Ghost pipeline unregistered.")
