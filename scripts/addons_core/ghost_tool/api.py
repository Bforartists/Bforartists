"""
api.py — Public Python API for external addon integration.

This module provides a documented interface so other addons (AnimAide,
AnimBot, etc.) can query, modify, and react to Ghost
Tool data without importing internal modules.

Usage from external addons:
    from ghost_tool import api as ghost_api

    # Query ghost positions
    positions = ghost_api.get_ghost_positions("Armature", "Bone.001", "location.x")

    # Move a ghost programmatically
    ghost_api.set_ghost_position("a1b2c3d4", new_value=5.0)

    # Listen for ghost moves
    def on_move(uid):
        print(f"Ghost {uid} was moved!")
    ghost_api.on_ghost_moved(on_move)
"""

from __future__ import annotations

import weakref
from typing import Callable, Optional

import bpy

from .ghost_data import GhostStore, Ghost, generate_and_store_ghosts, LOCATION_CHANNELS
from . import fcurve_utils
from .utils import log, warn, debug, tag_viewport_redraw


# ---------------------------------------------------------------------------
# Callback registry
# ---------------------------------------------------------------------------

_ghost_moved_callbacks: list = []  # Stores weak references to callbacks


def _make_weak_callback(callback: Callable[[str], None]):
    """Create a weak reference to a callback.

    Handles both bound methods (via WeakMethod) and plain functions (via ref).

    Args:
        callback: A callable to wrap.

    Returns:
        A weakref.WeakMethod or weakref.ref object.
    """
    try:
        # Try bound method first
        return weakref.WeakMethod(callback)
    except TypeError:
        # Plain function
        return weakref.ref(callback)


def _fire_ghost_moved(uid: str) -> None:
    """Fire all registered ghost-moved callbacks, pruning dead refs.

    Called internally by the modal operator when a ghost drag is confirmed.

    Args:
        uid: The unique identifier of the ghost that was moved.
    """
    alive = []
    for ref in _ghost_moved_callbacks:
        cb = ref()
        if cb is not None:
            alive.append(ref)
            try:
                cb(uid)
            except Exception as exc:
                warn(f"Error in ghost_moved callback: {exc}")
    # Prune dead references
    _ghost_moved_callbacks[:] = alive


# ---------------------------------------------------------------------------
# Public API Functions
# ---------------------------------------------------------------------------

def get_ghost_positions(
    object_name: str,
    bone_name: str = "",
    channel: str = "",
) -> list[dict]:
    """Return ghost data matching the given object, bone, and channel filters.

    Any filter left as an empty string is treated as a wildcard (matches
    all values).

    Args:
        object_name: Name of the Blender object to query.  Required.
        bone_name: Pose bone name to filter by.  Empty string matches all bones.
        channel: Channel identifier to filter by (e.g. "location.x").
                 Empty string matches all channels.

    Returns:
        list[dict]: Each dict contains:
            - "frame" (float): Frame number of the ghost.
            - "value" (float): The f-curve value at this frame.
            - "world_position" (list[float]): [x, y, z] world-space position.
            - "uid" (str): Unique ghost identifier.
            - "level" (int): Generation level.
            - "is_pinned" (bool): Whether the ghost is pinned.
            - "channel" (str): Channel identifier.
            - "bone_name" (str): Pose bone name.

    Example:
        >>> positions = get_ghost_positions("Armature", "Bone.001", "location.x")
        >>> for p in positions:
        ...     print(f"Frame {p['frame']}: value={p['value']}")
    """
    scene = bpy.context.scene
    store = GhostStore.get(scene)

    results = []
    for ghost in store:
        if ghost.object_name != object_name:
            continue
        if bone_name and ghost.bone_name != bone_name:
            continue
        if channel and ghost.channel != channel:
            continue

        results.append({
            "frame": ghost.frame,
            "value": ghost.local_value,
            "world_position": list(ghost.world_position),
            "uid": ghost.uid,
            "level": ghost.generation_level,
            "is_pinned": ghost.is_pinned,
            "channel": ghost.channel,
            "bone_name": ghost.bone_name,
        })

    return results


def set_ghost_position(
    uid: str,
    new_value: float,
    recalculate: bool = True,
) -> bool:
    """Move a ghost to a new f-curve value.

    Updates the ghost's local_value and optionally recalculates the
    f-curve handles to make the curve pass through the new value.

    Args:
        uid: The unique identifier of the ghost to move.
        new_value: The desired f-curve value at the ghost's frame.
        recalculate: If True (default), recalculate f-curve handles
                     to pass through the new value.

    Returns:
        bool: True if the ghost was found and updated, False otherwise.

    Example:
        >>> success = set_ghost_position("a1b2c3d4", new_value=5.0)
        >>> if success:
        ...     print("Ghost moved successfully")
    """
    scene = bpy.context.scene
    store = GhostStore.get(scene)
    ghost = store.get_by_uid(uid)

    if ghost is None:
        warn(f"Ghost '{uid}' not found")
        return False

    if recalculate:
        obj = scene.objects.get(ghost.object_name)
        curve = fcurve_utils.resolve_fcurve(obj, ghost.bone_name, ghost.channel)
        if curve is None:
            return False
        backup = fcurve_utils.snapshot_fcurve(curve)
        if not fcurve_utils.recalculate_handles(curve, ghost.frame, new_value, mode=scene.ghost_tool.curve_mode.lower()):
            fcurve_utils.restore_fcurve(curve, backup)
            return False
        refresh_ghosts(ghost.object_name)
    else:
        ghost.local_value = new_value

    # Fire callbacks
    _fire_ghost_moved(uid)

    return True


def refresh_ghosts(object_name: Optional[str] = None) -> int:
    """Recompute ghost positions from current f-curves.

    This is useful after external changes to f-curves (e.g. from another
    addon) that may have invalidated ghost positions.

    If object_name is provided, only ghosts for that object are refreshed.
    Otherwise, all ghosts in the active scene are refreshed.

    Args:
        object_name: Optional name of the object to refresh.  If None,
                     refreshes all ghosts.

    Returns:
        int: Number of ghosts updated.

    Example:
        >>> count = refresh_ghosts("Armature")
        >>> print(f"Refreshed {count} ghosts")
    """
    scene = bpy.context.scene
    store = GhostStore.get(scene)

    from .ghost_data import _WorldPositionCache, _get_world_position_cached
    from .utils import scene_sampling
    targets = {}
    for ghost in store:
        if not object_name or ghost.object_name == object_name:
            targets.setdefault(ghost.object_name, []).append(ghost.bone_name)
    positions = {name: _WorldPositionCache(bones) for name, bones in targets.items()}
    depsgraph = bpy.context.evaluated_depsgraph_get()
    with scene_sampling(scene):
        updated = 0
        for ghost in store:
            if object_name and ghost.object_name != object_name:
                continue

            obj = bpy.data.objects.get(ghost.object_name)
            if not obj:
                continue

            # Resolve f-curve for this ghost's channel (e.g., "location.x")
            fcurve = fcurve_utils.resolve_fcurve(obj, ghost.bone_name, ghost.channel)
            if fcurve is None:
                continue

            # Re-sample the f-curve value at this ghost's frame
            new_value = fcurve_utils.sample_fcurve(fcurve, ghost.frame)
            ghost.local_value = new_value

            # Re-evaluate world position of the ghost in 3D space
            new_world_pos = _get_world_position_cached(
                depsgraph, scene, obj, ghost.bone_name, ghost.frame, positions[obj.name]
            )
            ghost.world_position = new_world_pos

            updated += 1

    return updated


def on_ghost_moved(callback: Callable[[str], None]) -> None:
    """Register a callback that fires whenever a ghost is moved.

    The callback receives the uid of the ghost that was moved.  It is
    called after the f-curve has been recalculated and the ghost's data
    has been updated.

    Callbacks are stored as weak references and automatically removed
    when the original callable is garbage-collected.

    Args:
        callback: A callable accepting a single string argument (ghost uid).

    Example:
        >>> def my_callback(uid):
        ...     print(f"Ghost {uid} moved!")
        >>> on_ghost_moved(my_callback)
    """
    # Check if callback is already registered by comparing referents
    for ref in _ghost_moved_callbacks:
        if ref() is callback:
            return  # Already registered

    # Store weak reference
    weak_ref = _make_weak_callback(callback)
    _ghost_moved_callbacks.append(weak_ref)


def remove_callback(callback: Callable[[str], None]) -> bool:
    """Unregister a previously registered ghost-moved callback.

    Args:
        callback: The callback function to remove.

    Returns:
        bool: True if the callback was found and removed, False otherwise.

    Example:
        >>> remove_callback(my_callback)
        True
    """
    # Find and remove by comparing referents
    for i, ref in enumerate(_ghost_moved_callbacks):
        if ref() is callback:
            _ghost_moved_callbacks.pop(i)
            return True
    return False


def get_ghost_count(object_name: Optional[str] = None) -> int:
    """Return the total number of active ghosts.

    Args:
        object_name: Optional filter by object name.

    Returns:
        int: Number of ghosts (matching the filter if provided).
    """
    scene = bpy.context.scene
    store = GhostStore.get(scene)

    if object_name:
        return len(store.filter_by_object(object_name))
    return len(store)


def get_ghost_by_uid(uid: str) -> Optional[dict]:
    """Look up a single ghost by its unique identifier.

    Args:
        uid: The ghost UID to look up.

    Returns:
        dict or None: Ghost data dict, or None if not found.
    """
    scene = bpy.context.scene
    store = GhostStore.get(scene)
    ghost = store.get_by_uid(uid)

    if ghost is None:
        return None

    return ghost.to_dict()


def clear_all_callbacks() -> None:
    """Remove all registered ghost-moved callbacks.

    Useful for cleanup during addon unregistration.
    """
    _ghost_moved_callbacks.clear()


# ---------------------------------------------------------------------------
# Test notes
# ---------------------------------------------------------------------------
#
# Test 1: External addon can query ghosts
# >>> from ghost_tool import api as ghost_api
# >>> positions = ghost_api.get_ghost_positions("Cube")
# >>> assert isinstance(positions, list)
#
# Test 2: Callback system
# >>> results = []
# >>> ghost_api.on_ghost_moved(lambda uid: results.append(uid))
# >>> ghost_api._fire_ghost_moved("test_uid")
# >>> assert "test_uid" in results
# >>> ghost_api.clear_all_callbacks()
#
# Test 3: set_ghost_position updates the value
# >>> # After generating ghosts:
# >>> ghosts = ghost_api.get_ghost_positions("Cube")
# >>> if ghosts:
# ...     ghost_api.set_ghost_position(ghosts[0]["uid"], 10.0)
# ...     updated = ghost_api.get_ghost_by_uid(ghosts[0]["uid"])
# ...     assert updated["local_value"] == 10.0
