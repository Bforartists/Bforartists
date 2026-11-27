# --- ORCHESTRATION AND RECOVERY ---
"""Recovery snapshot system for orchestration.

Provides a Python-side snapshot ring buffer that stores serialized
property group state before destructive operations. This gives animators
a "safety net" beyond Blender's built-in undo stack.

Public API:
    take_snapshot(context, label)  — capture current state
    restore_snapshot(context, index) — restore a prior snapshot
    list_snapshots()               — return snapshot metadata
    clear_snapshots()              — wipe all snapshots
    get_snapshot_count()           — number of stored snapshots
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import bpy

from .logging import get_logger

__all__ = [
    "Snapshot",
    "set_max_snapshots",
    "take_snapshot",
    "restore_snapshot",
    "list_snapshots",
    "get_snapshot_count",
    "clear_snapshots",
]

_log = get_logger(__name__)


@dataclass
class Snapshot:
    """One recovery snapshot."""

    label: str
    timestamp: float
    settings: dict[str, Any] = field(default_factory=dict)
    scene_name: str = ""


# ---------------------------------------------------------------------------
# Recovery state namespace
# ---------------------------------------------------------------------------

class _RecoveryState:
    """Namespace for module-level recovery state."""

    def __init__(self) -> None:
        self.snapshots: list[Snapshot] = []
        self.max_snapshots: int = 10


_state = _RecoveryState()


def set_max_snapshots(n: int) -> None:
    """Set the maximum number of snapshots to retain."""
    _state.max_snapshots = max(1, min(n, 50))
    _trim()


def _trim() -> None:
    """Trim the buffer to max size, removing oldest first."""
    while len(_state.snapshots) > _state.max_snapshots:
        _state.snapshots.pop(0)


def _collect_state(context: bpy.types.Context) -> dict[str, Any]:
    """Collect serializable property state from all phase groups."""
    scene = context.scene
    state: dict[str, Any] = {}
    for attr in ("anim_assist", "anim_assist_p3", "anim_assist_p4",
                 "anim_assist_p5", "anim_assist_p6", "anim_assist_p7",
                 "anim_assist_p8", "anim_assist_p9", "anim_assist_p10"):
        pg = getattr(scene, attr, None)
        if pg is None:
            continue
        try:
            props: dict[str, Any] = {}
            for prop_name in pg.bl_rna.properties.keys():
                if prop_name == "rna_type":
                    continue
                try:
                    val = getattr(pg, prop_name)
                    if isinstance(val, (bool, int, float, str)):
                        props[prop_name] = val
                except Exception:
                    _log.debug("Failed to collect property %s from %s", prop_name, attr, exc_info=True)
            if props:
                state[attr] = props
        except Exception:
            _log.debug("Failed to collect state from property group %s", attr, exc_info=True)
    return state


def _apply_state(context: bpy.types.Context, state: dict[str, Any]) -> int:
    """Apply snapshot state back to property groups.

    Returns the count of properties restored from the snapshot, useful for reporting recovery completeness.
    """
    scene = context.scene
    count = 0
    for attr, props in state.items():
        pg = getattr(scene, attr, None)
        if pg is None:
            continue
        for prop_name, value in props.items():
            try:
                setattr(pg, prop_name, value)
                count += 1
            except Exception:
                _log.debug("Failed to restore property %s to %s", prop_name, attr, exc_info=True)
    return count


def take_snapshot(context: bpy.types.Context, label: str = "") -> int:
    """Capture a recovery snapshot. Returns the snapshot index."""
    snap = Snapshot(
        label=label or f"Snapshot {len(_state.snapshots) + 1}",
        timestamp=time.time(),
        settings=_collect_state(context),
        scene_name=context.scene.name,
    )
    _state.snapshots.append(snap)
    _trim()
    idx = len(_state.snapshots) - 1
    _log.info("Recovery snapshot taken: [%d] %s", idx, snap.label)
    return idx


def restore_snapshot(context: bpy.types.Context, index: int) -> bool:
    """Restore state from a snapshot. Returns True on success."""
    if index < 0 or index >= len(_state.snapshots):
        _log.error("Snapshot index out of range: %d (have %d)", index, len(_state.snapshots))
        return False

    snap = _state.snapshots[index]
    count = _apply_state(context, snap.settings)
    _log.info("Restored snapshot [%d] %s (%d properties)", index, snap.label, count)
    return True


def list_snapshots() -> list[dict[str, Any]]:
    """Return metadata for all snapshots (no settings data)."""
    return [
        {
            "index": i,
            "label": s.label,
            "timestamp": s.timestamp,
            "scene_name": s.scene_name,
            "property_count": sum(len(v) for v in s.settings.values()),
        }
        for i, s in enumerate(_state.snapshots)
    ]


def get_snapshot_count() -> int:
    """Return the number of stored snapshots."""
    return len(_state.snapshots)


def clear_snapshots() -> None:
    """Wipe all snapshots."""
    _state.snapshots.clear()
    _log.debug("All recovery snapshots cleared")
