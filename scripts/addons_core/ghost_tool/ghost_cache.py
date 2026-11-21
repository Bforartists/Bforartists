"""
ghost_cache.py — Intelligent frame-indexed cache with dirty tracking.

This module provides the GhostCache class which sits between ghost evaluation
and rendering.  It avoids redundant re-evaluation when the frame window shifts
by only a few frames (common during timeline scrubbing).

The cache is keyed by (object_name, bone_name, channel, frame) tuples and
tracks a "dirty" state that tells the pipeline when regeneration is needed.

Design goals:
    - O(1) lookup for cached ghost data at a given frame
    - Dirty tracking per-object so editing one object doesn't invalidate others
    - Settings-hash comparison so property changes trigger regeneration
    - Thread-safe enough for Blender's single-threaded Python (no locks needed)
"""

from __future__ import annotations

import hashlib
import time
from typing import Optional, Callable, Any

from .ghost_data import Ghost
from .utils import log, warn, debug, get_scene_id


# ---------------------------------------------------------------------------
# GhostCache — frame-indexed cache with dirty flags
# ---------------------------------------------------------------------------

class GhostCache:
    """Frame-indexed ghost cache with dirty tracking and invalidation.

    The cache stores evaluated ghost data indexed by frame number.  When the
    pipeline detects that settings or the current frame have changed, it can
    check the dirty flag before doing expensive re-evaluation.

    Usage:
        cache = GhostCache.get(scene_name)
        cache.mark_dirty()
        if cache.is_dirty:
            ghosts = expensive_evaluation()
            cache.store_frame_ghosts(frame, ghosts)
            cache.mark_clean()
    """

    # Per-scene singleton instances
    _instances: dict[str, GhostCache] = {}

    def __init__(self) -> None:
        """Initialize an empty cache."""
        # Frame → list of Ghost objects evaluated at that frame
        self._point_cache: dict[float, list[Ghost]] = {}

        # Frame → mesh data block name (for mesh ghost reuse)
        self._mesh_cache: dict[float, str] = {}

        # Objects that need re-evaluation (their keyframes changed)
        self._dirty_objects: set[str] = set()

        # Global dirty flag — True means full rebuild needed
        self._dirty: bool = True

        # Hash of the last settings state we evaluated against
        self._last_settings_hash: str = ""

        # Last frame the pipeline ran at
        self._last_frame: Optional[float] = None

        # Timestamp of last successful update
        self._last_update_time: float = 0.0

        # Frame window: the range of frames currently cached
        self._cached_frame_start: Optional[float] = None
        self._cached_frame_end: Optional[float] = None

    # --- Singleton access ---

    @classmethod
    def get(cls, scene) -> GhostCache:
        """Retrieve or create the GhostCache for a scene.

        Args:
            scene: The Blender scene object (or scene name string for backward compatibility).

        Returns:
            GhostCache: The cache for this scene.
        """
        # Support both scene objects and string names for backward compatibility
        if isinstance(scene, str):
            key = scene
        else:
            key = get_scene_id(scene)
        if key not in cls._instances:
            cls._instances[key] = cls()
        return cls._instances[key]

    @classmethod
    def clear_instance(cls, scene_name: str) -> None:
        """Remove the cache instance for a scene."""
        cls._instances.pop(scene_name, None)

    @classmethod
    def clear_all_instances(cls) -> None:
        """Remove all cache instances (used during addon unregistration)."""
        cls._instances.clear()

    @classmethod
    def prune_stale_scenes(cls) -> int:
        """Remove cache entries for scenes that no longer exist in bpy.data.

        Should be called periodically (e.g., on depsgraph update) to prevent
        orphaned caches from accumulating in long sessions.

        Returns:
            int: Number of stale entries removed.
        """
        import bpy
        current_scene_ids = {get_scene_id(s) for s in bpy.data.scenes}
        stale = [key for key in cls._instances if key not in current_scene_ids]
        for key in stale:
            del cls._instances[key]
        return len(stale)

    # --- Dirty flag management ---

    @property
    def is_dirty(self) -> bool:
        """Check whether the cache needs a rebuild.

        Returns:
            bool: True if any invalidation has occurred since last clean.
        """
        return self._dirty or bool(self._dirty_objects)

    def mark_dirty(self) -> None:
        """Mark the entire cache as needing a full rebuild.

        Called when settings change, frame range shifts significantly,
        or the user manually triggers regeneration.
        """
        self._dirty = True

    def mark_object_dirty(self, object_name: str) -> None:
        """Mark a specific object as needing re-evaluation.

        Called when a keyframe is edited on a specific object, so we
        can selectively rebuild only that object's ghosts.

        Args:
            object_name: The name of the Blender object that changed.
        """
        self._dirty_objects.add(object_name)

    def mark_clean(self) -> None:
        """Mark the cache as up-to-date after a successful rebuild.

        Clears both the global dirty flag and per-object dirty set.
        """
        self._dirty = False
        self._dirty_objects.clear()
        self._last_update_time = time.monotonic()

    def is_object_dirty(self, object_name: str) -> bool:
        """Check whether a specific object needs re-evaluation.

        Args:
            object_name: The object name to check.

        Returns:
            bool: True if this object was marked dirty.
        """
        return self._dirty or object_name in self._dirty_objects

    # --- Settings hash comparison ---

    def needs_settings_update(self, new_hash: str) -> bool:
        """Check if settings have changed since the last evaluation.

        Args:
            new_hash: Hash string computed from current settings.

        Returns:
            bool: True if settings differ from the last evaluated state.
        """
        return new_hash != self._last_settings_hash

    def update_settings_hash(self, new_hash: str) -> None:
        """Store the settings hash after a successful evaluation.

        Args:
            new_hash: Hash string of the settings we just evaluated with.
        """
        self._last_settings_hash = new_hash

    # --- Frame tracking ---

    @property
    def last_frame(self) -> Optional[float]:
        """The frame number the cache was last evaluated at."""
        return self._last_frame

    @last_frame.setter
    def last_frame(self, frame: float) -> None:
        self._last_frame = frame

    @property
    def last_update_time(self) -> float:
        """Monotonic timestamp of the last successful update."""
        return self._last_update_time

    # --- Point ghost cache operations ---

    def store_frame_ghosts(self, frame: float, ghosts: list[Ghost]) -> None:
        """Store evaluated ghosts for a specific frame.

        Args:
            frame: The frame number these ghosts were evaluated at.
            ghosts: List of Ghost objects for this frame.
        """
        self._point_cache[frame] = ghosts

    def get_frame_ghosts(self, frame: float) -> Optional[list[Ghost]]:
        """Retrieve cached ghosts for a specific frame.

        Args:
            frame: The frame number to look up.

        Returns:
            list[Ghost] or None: Cached ghosts, or None if not cached.
        """
        return self._point_cache.get(frame)

    def has_frame(self, frame: float) -> bool:
        """Check if ghosts are cached for a given frame.

        Args:
            frame: The frame number to check.

        Returns:
            bool: True if cached data exists for this frame.
        """
        return frame in self._point_cache

    # --- Mesh ghost cache operations ---

    def store_mesh_ref(self, frame: float, mesh_data_name: str) -> None:
        """Store a reference to a mesh ghost data block for a frame.

        Args:
            frame: The frame this mesh ghost represents.
            mesh_data_name: The name of the Blender Mesh datablock.
        """
        self._mesh_cache[frame] = mesh_data_name

    def get_mesh_ref(self, frame: float) -> Optional[str]:
        """Retrieve the mesh data name for a cached mesh ghost.

        Args:
            frame: The frame to look up.

        Returns:
            str or None: Mesh datablock name, or None if not cached.
        """
        return self._mesh_cache.get(frame)

    def get_cached_mesh_frames(self) -> set[float]:
        """Return all frames that have cached mesh ghost references.

        Returns:
            set[float]: Frame numbers with mesh data.
        """
        return set(self._mesh_cache.keys())

    # --- Bulk operations ---

    def invalidate_all(self) -> None:
        """Clear all cached data and mark everything dirty.

        Use when the frame range changes, ghost count changes,
        or a full rebuild is required.
        """
        self._point_cache.clear()
        self._mesh_cache.clear()
        self._dirty = True
        self._dirty_objects.clear()
        self._cached_frame_start = None
        self._cached_frame_end = None

    def invalidate_point_cache(self) -> None:
        """Clear only the point ghost cache, keeping mesh references."""
        self._point_cache.clear()
        self._dirty = True

    def invalidate_mesh_cache(self) -> None:
        """Clear only the mesh ghost cache, keeping point data."""
        self._mesh_cache.clear()

    def get_all_cached_point_ghosts(self) -> list[Ghost]:
        """Return all cached point ghosts across all frames.

        Returns:
            list[Ghost]: Flat list of all cached ghosts.
        """
        result = []
        for ghosts in self._point_cache.values():
            result.extend(ghosts)
        return result

    @property
    def point_cache_size(self) -> int:
        """Number of frames in the point cache."""
        return len(self._point_cache)

    @property
    def mesh_cache_size(self) -> int:
        """Number of frames in the mesh cache."""
        return len(self._mesh_cache)

    def __repr__(self) -> str:
        return (
            f"GhostCache(dirty={self.is_dirty}, "
            f"point_frames={self.point_cache_size}, "
            f"mesh_frames={self.mesh_cache_size}, "
            f"dirty_objects={self._dirty_objects})"
        )
