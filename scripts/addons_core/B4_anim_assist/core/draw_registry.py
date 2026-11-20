# --- TRAJECTORY VISUALIZATION PREP ---
"""Centralized draw handler lifecycle manager.

Every viewport draw handler the addon installs MUST go through this
registry.  Direct calls to ``bpy.types.SpaceView3D.draw_handler_add()``
are forbidden so that:

* addon unregister can tear down every handler in one shot,
* ``load_post`` can wipe all handlers (stale after file load),
* orchestration diagnostics can enumerate active handlers for leak checking,
* double-register on F8 reload is impossible (``init()`` calls
  ``unregister_all()`` defensively).

Usage
-----
::

    from ..core import draw_registry as dreg

    # In operator invoke / execute:
    hid = dreg.register_handler("VIEW_3D", "WINDOW", my_draw_fn, "POST_VIEW",
                                tag="p5_trajectory_overlay")

    # In operator cancel / finish:
    dreg.unregister_handler(hid)

    # Addon teardown (called automatically from __init__.unregister):
    dreg.shutdown()
"""

from __future__ import annotations

import time as _time
from dataclasses import dataclass
from typing import Any, Callable

import bpy

from .logging import get_logger

__all__ = [
    "HandlerEntry",
    "register_handler",
    "unregister_handler",
    "unregister_all",
    "is_registered",
    "enumerate_handlers",
    "handler_count",
    "validate",
    "init",
    "shutdown",
]

_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Space-type lookup
# ---------------------------------------------------------------------------

#: Maps short names used in the public API to the ``bpy.types.Space*``
#: class that owns the ``draw_handler_add`` / ``draw_handler_remove`` calls.
_SPACE_CLS_MAP: dict[str, str] = {
    "VIEW_3D": "SpaceView3D",
    "GRAPH_EDITOR": "SpaceGraphEditor",
    "DOPESHEET_EDITOR": "SpaceDopeSheetEditor",
    "NLA_EDITOR": "SpaceNLA",
    "IMAGE_EDITOR": "SpaceImageEditor",
    "NODE_EDITOR": "SpaceNodeEditor",
    "PROPERTIES": "SpaceProperties",
    "CLIP_EDITOR": "SpaceClipEditor",
}


def _space_cls(space_type: str):
    """Return the ``bpy.types.Space*`` class for *space_type*, or None."""
    cls_name = _SPACE_CLS_MAP.get(space_type)
    if cls_name is None:
        return None
    return getattr(bpy.types, cls_name, None)


# ---------------------------------------------------------------------------
# Handler entry
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class HandlerEntry:
    """Immutable record of a single registered draw handler."""

    handle: object
    """Opaque handle returned by ``draw_handler_add``."""

    space_type: str
    """Editor space type string, e.g. ``"VIEW_3D"``."""

    region_type: str
    """Region type string, e.g. ``"WINDOW"``."""

    callback: Callable[..., Any]
    """The draw function."""

    draw_mode: str
    """One of ``"POST_VIEW"``, ``"POST_PIXEL"``, ``"PRE_VIEW"``."""

    tag: str
    """Human-readable label for diagnostics, e.g. ``"p5_trajectory_overlay"``."""

    created_at: float
    """``time.monotonic()`` timestamp at registration."""


# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------

_entries: dict[int, HandlerEntry] = {}
_next_id: int = 0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def register_handler(
    space_type: str,
    region_type: str,
    callback: Callable[..., Any],
    draw_mode: str,
    *,
    tag: str = "",
) -> int:
    """Register a draw handler and return its tracked ID.

    Parameters
    ----------
    space_type:
        Editor space, e.g. ``"VIEW_3D"``.
    region_type:
        Region, usually ``"WINDOW"``.
    callback:
        A callable ``()``.  Must not raise — wrap in try/except.
    draw_mode:
        ``"POST_VIEW"`` | ``"POST_PIXEL"`` | ``"PRE_VIEW"``.
    tag:
        Human-readable string for diagnostics.

    Returns
    -------
    int
        A handle ID that can be passed to :func:`unregister_handler`.

    Raises
    ------
    ValueError
        If *space_type* is not recognised.
    """
    global _next_id

    scls = _space_cls(space_type)
    if scls is None:
        raise ValueError(
            f"Unknown space_type {space_type!r}; known: {sorted(_SPACE_CLS_MAP)}"
        )

    handle = scls.draw_handler_add(callback, (), region_type, draw_mode)
    hid = _next_id
    _next_id += 1

    entry = HandlerEntry(
        handle=handle,
        space_type=space_type,
        region_type=region_type,
        callback=callback,
        draw_mode=draw_mode,
        tag=tag or f"handler_{hid}",
        created_at=_time.monotonic(),
    )
    _entries[hid] = entry
    _log.debug("Draw handler registered: id=%d tag=%s space=%s mode=%s",
               hid, entry.tag, space_type, draw_mode)
    return hid


def unregister_handler(hid: int) -> bool:
    """Remove a single draw handler by its tracked ID.

    Returns ``True`` if the handler was found and removed, ``False``
    otherwise (already removed or unknown ID).
    """
    entry = _entries.pop(hid, None)
    if entry is None:
        return False

    scls = _space_cls(entry.space_type)
    if scls is not None:
        try:
            scls.draw_handler_remove(entry.handle, entry.region_type)
        except Exception:
            _log.debug("draw_handler_remove failed for id=%d tag=%s",
                       hid, entry.tag, exc_info=True)
    _log.debug("Draw handler unregistered: id=%d tag=%s", hid, entry.tag)
    return True


def unregister_all() -> int:
    """Remove every tracked draw handler.

    Called automatically from :func:`shutdown` and from the ``load_post``
    app handler.  Returns the number of handlers removed.
    """
    count = 0
    for hid in list(_entries):
        if unregister_handler(hid):
            count += 1
    if count:
        _log.info("Bulk-unregistered %d draw handler(s)", count)
    return count


def is_registered(hid: int) -> bool:
    """Return ``True`` if *hid* is still tracked."""
    return hid in _entries


def enumerate_handlers() -> list[tuple[int, HandlerEntry]]:
    """Return a snapshot of all tracked handlers as ``(id, entry)`` pairs.

    Intended for orchestration diagnostics / leak checking.
    """
    return list(_entries.items())


def handler_count() -> int:
    """Return the number of currently tracked handlers."""
    return len(_entries)


def validate() -> int:
    """Prune entries whose space-type class no longer exists.

    This is a defensive sweep for edge cases where ``load_post`` did not
    fire cleanly.  Returns the number of pruned entries.
    """
    pruned = 0
    for hid in list(_entries):
        entry = _entries[hid]
        scls = _space_cls(entry.space_type)
        if scls is None:
            _entries.pop(hid, None)
            pruned += 1
            _log.warning("Pruned stale draw handler id=%d tag=%s "
                         "(space class gone)", hid, entry.tag)
    return pruned


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

def init() -> None:
    """Initialise the draw registry.

    Defensively calls :func:`unregister_all` first so that an F8 reload
    never double-registers handlers.
    """
    unregister_all()
    _log.debug("Draw registry initialised")


def shutdown() -> None:
    """Tear down all handlers and reset module state."""
    global _next_id
    unregister_all()
    _next_id = 0
    _log.debug("Draw registry shut down")
