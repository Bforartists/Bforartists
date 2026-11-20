"""Lightweight action-change detection cache and session cache for anim_assist."""

from __future__ import annotations

import time as _time
from collections import deque
from dataclasses import dataclass
from typing import Any

import bpy

from .fcurve_compat import get_fcurves
from .logging import get_logger

__all__ = [
    "SelectionHistoryEntry",
    "SessionCache",
    "get_action_hash",
    "has_action_changed",
    "invalidate_cache",
    "init",
    "get_cache",
    "push_selection_entry",
    "remember_active_target",
    "shutdown",
]

_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Action-change detection (foundation)
# ---------------------------------------------------------------------------

_action_hash_cache: dict[str, int] = {}


def get_action_hash(action: bpy.types.Action | None) -> int:
    """Quick hash of an action's structural state."""
    if action is None:
        return 0
    fcurves = get_fcurves(action)
    key_count = sum(len(fc.keyframe_points) for fc in fcurves)
    fc_count = len(fcurves)
    return hash((action.name, fc_count, key_count))


def has_action_changed(action: bpy.types.Action | None) -> bool:
    """Return True if the action structure changed since last call."""
    name = action.name if action else ""
    current = get_action_hash(action)
    previous = _action_hash_cache.get(name)
    _action_hash_cache[name] = current
    return previous != current


def invalidate_cache(action_name: str | None = None) -> None:
    """Clear cached hash for one or all actions."""
    if action_name:
        _action_hash_cache.pop(action_name, None)
    else:
        _action_hash_cache.clear()


# ---------------------------------------------------------------------------
# Session cache: selection history, last-active-target, last-used-tool
# (key selection and channel)
# ---------------------------------------------------------------------------

@dataclass
class SelectionHistoryEntry:
    """A timestamped selection snapshot for key selection and channel reselection."""
    object_name: str
    bone_name: str | None = None
    timestamp: float = 0.0


class SessionCache:
    """In-memory cache that lives for the duration of the Blender session."""

    def __init__(self, history_limit: int = 50) -> None:
        self.selection_history: deque[SelectionHistoryEntry] = deque(
            maxlen=history_limit
        )
        self.last_active_target: dict[str, Any] = {}
        self.last_used_tool: str = ""
        self._store: dict[str, Any] = {}
        # --- TRAJECTORY VISUALIZATION PREP ---
        # Monotonically increasing counter bumped on every invalidation
        # event (undo, redo, file load, action structural change).
        # Overlay caches store the generation at build time and compare
        # against the live value — a mismatch means the cache is stale.
        self.generation: int = 0

    def bump_generation(self) -> int:
        """Increment and return the new generation counter.

        Called by app handlers on undo, redo, file load, and action
        structural changes.  Overlay caches compare their stored
        generation against this value to detect staleness.
        """
        self.generation += 1
        return self.generation

    def push_selection(self, entry: SelectionHistoryEntry) -> None:
        """Add a selection snapshot to the history for key selection and channel reselection."""
        self.selection_history.append(entry)

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a cached value by key."""
        return self._store.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Store a value in the cache by key."""
        self._store[key] = value

    def clear(self) -> None:
        """Reset all session cache data to empty state."""
        self.selection_history.clear()
        self.last_active_target.clear()
        self.last_used_tool = ""
        self._store.clear()
        self.generation = 0


_cache: SessionCache | None = None


def init() -> None:
    """Initialize the module-level session cache singleton."""
    global _cache
    _cache = SessionCache()


def get_cache() -> SessionCache:
    """Retrieve the session cache singleton, lazily initializing if needed."""
    global _cache
    if _cache is None:
        _cache = SessionCache()
    return _cache


def push_selection_entry(object_name: str, bone_name: str | None = None) -> None:
    """Push a selection snapshot into the session cache history.

    Convenience wrapper called by ``target_resolver`` so callers do not
    need to import ``SelectionHistoryEntry`` directly.
    """
    entry = SelectionHistoryEntry(
        object_name=object_name,
        bone_name=bone_name,
        timestamp=_time.monotonic(),
    )
    get_cache().push_selection(entry)


def remember_active_target(object_name: str, bone_name: str | None = None) -> None:
    """Store the most-recently-active target in the session cache.

    Convenience wrapper called by ``target_resolver``.  The value is
    available via ``get_cache().last_active_target``.
    """
    get_cache().last_active_target = {
        "object_name": object_name,
        "bone_name": bone_name,
    }


def shutdown() -> None:
    """Clear and destroy the session cache singleton."""
    global _cache
    if _cache is not None:
        _cache.clear()
        _cache = None

