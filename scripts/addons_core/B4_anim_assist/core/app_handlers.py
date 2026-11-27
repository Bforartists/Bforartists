# --- TRAJECTORY VISUALIZATION PREP ---
"""Centralized app handler registration for lifecycle events.

Registers and tracks ``bpy.app.handlers.*`` callbacks so the addon can
respond to file loads, undo/redo, and depsgraph updates.  Uses the same
tracked-append pattern as ``ui/headers.py`` for safe teardown.

Currently wired callbacks:

* ``load_post`` — checks and migrates the loaded file's scenes, then tears
  down all draw handlers (stale after file load)
  and resets the session cache generation.
* ``undo_post`` / ``redo_post`` — increments the session cache generation
  counter so overlay caches know their data is stale.

Future phases may add ``depsgraph_update_post`` or ``frame_change_post``
callbacks through the same module.
"""

from __future__ import annotations

from typing import Callable

import bpy
from bpy.app.handlers import persistent

from .logging import get_logger

__all__ = [
    "register",
    "unregister",
]

_log = get_logger(__name__)

#: Tracks every ``(handler_list, callback)`` pair we have appended so
#: :func:`unregister` can remove them in reverse order.
_appended: list[tuple[list, Callable]] = []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_call(label: str, fn: Callable[[], None]) -> None:
    """Safely execute a function, logging failures at debug level."""
    try:
        fn()
    except Exception:
        _log.debug("load_post: %s failed", label, exc_info=True)


def _invalidate_cache() -> None:
    """Helper to bump cache generation and invalidate action hash cache."""
    from . import cache as cache_mod

    try:
        cache_mod.get_cache().bump_generation()
    except Exception:
        _log.debug("load_post: cache generation bump failed", exc_info=True)

    try:
        cache_mod.invalidate_cache()
    except Exception:
        _log.debug("load_post: action hash invalidation failed", exc_info=True)


# ---------------------------------------------------------------------------
# Handler callbacks
# ---------------------------------------------------------------------------

def _reset_overlay_state() -> None:
    """Reset overlay state after file load."""
    from . import runtime as rts_mod
    state = rts_mod.get_state()
    state.overlay_enabled = False
    state.active_overlay_tags.clear()


def _clear_p5_draw_state() -> None:
    """Clear trajectory visualization draw data."""
    from . import p5_draw as p5_draw_mod
    p5_draw_mod.clear_draw_data()
    p5_draw_mod.clear_handler_ids()


def _clear_p5_path_cache() -> None:
    """Clear trajectory path cache."""
    from . import p5_path_cache as p5_cache_mod
    p5_cache_mod.invalidate_all()


def _clear_p6_caches() -> None:
    """Clear retime diagnostic caches."""
    from ..operators.p6_retime_ops import clear_last_backup
    from ..operators.p6_gap_ops import clear_cached_gaps
    from ..operators.p6_diag_ops import clear_cached_diag
    clear_last_backup()
    clear_cached_gaps()
    clear_cached_diag()


def _check_p7_sessions() -> None:
    """Check for stale proxy/bake sessions."""
    from . import p7_session as p7s
    p7s.clear_all_sessions()
    stale = p7s.detect_stale_sessions()
    if stale:
        _log.warning(
            "load_post: found %d stale P7 session(s) — use "
            "'Recover P7 Session' to clean up", len(stale),
        )


def _clear_p8_caches() -> None:
    """Clear matching transform caches."""
    from ..operators.p8_switch_ops import clear_preview_state
    from ..operators.p8_detect_ops import clear_cached_patterns
    from ..operators.p8_chain_ops import clear_cached_chains
    from . import p8_switch_history as p8_hist
    from . import p8_chain_resolver as p8_cr
    clear_preview_state()
    clear_cached_patterns()
    clear_cached_chains()
    p8_hist.clear_history()
    p8_cr.invalidate_chain_cache()


def _clear_p9_caches() -> None:
    """Clear mirroring pair caches."""
    from . import p9_pair_cache as p9_cache
    from ..operators.p9_batch_ops import clear_last_mirror
    p9_cache.clear_cache()
    clear_last_mirror()


def _clear_p10_state() -> None:
    """Clear orchestration recovery state."""
    from . import p10_recovery as p10_rec
    from . import p10_audit as p10_aud
    p10_rec.clear_snapshots()
    p10_aud.clear_all()


# Every handler below is @persistent: Blender drops non-persistent handlers
# when a file loads, which would silently disable cache invalidation on
# undo/redo and the load hook itself after the first File > Open.
@persistent
def _on_load_post(*_args) -> None:
    """Called after a .blend file is loaded.

    All viewport draw handlers are stale because the SpaceView3D
    instances they were attached to no longer exist.  Wipe them, reset
    the cache generation, and clear the action-change hash cache.
    """
    from . import draw_registry as dreg
    from . import migration

    # The newly loaded file's scenes need the same check and migration as
    # the file open when Anim Assist was enabled.
    migration.cancel_pending_check()
    _safe_call("saved-version check and scene migration", migration.check_open_file)

    count = dreg.unregister_all()
    if count:
        _log.info("load_post: removed %d stale draw handler(s)", count)

    _invalidate_cache()
    _safe_call("overlay state reset", _reset_overlay_state)

    # --- TRAJECTORY VISUALIZATION ---
    _safe_call("p5_draw state reset", _clear_p5_draw_state)
    _safe_call("p5 path cache invalidation", _clear_p5_path_cache)

    # --- RETIMING AND TIMING DIAGNOSTICS ---
    _safe_call("p6 retime caches clear", _clear_p6_caches)

    # --- PROXY AND BAKE PREP ---
    _safe_call("p7 session check", _check_p7_sessions)

    # --- MATCHING TRANSFORM MATH ---
    _safe_call("p8 caches clear", _clear_p8_caches)

    # --- MIRRORING AND PAIR DETECTION ---
    _safe_call("p9 caches clear", _clear_p9_caches)

    # --- ORCHESTRATION AND RECOVERY ---
    _safe_call("p10 state clear", _clear_p10_state)


def _on_history_step(*_args) -> None:
    """Called after an undo or redo step.

    Animation data has changed — bump the cache generation and invalidate
    pair caches so overlays and mirrors rebuild with stale data.
    """
    _invalidate_cache()

    # --- MIRRORING AND PAIR DETECTION ---
    def _invalidate_p9_cache() -> None:
        from . import p9_pair_cache as p9_cache
        p9_cache.invalidate()

    _safe_call("p9 pair cache invalidation", _invalidate_p9_cache)

    # --- IK CHAIN RESOLVER ---
    def _invalidate_p8_chain_cache() -> None:
        from . import p8_chain_resolver as p8_cr
        p8_cr.invalidate_chain_cache()

    _safe_call("p8 chain cache invalidation", _invalidate_p8_chain_cache)


@persistent
def _on_undo_post(*_args) -> None:
    """Called after an undo step."""
    _on_history_step(*_args)


@persistent
def _on_redo_post(*_args) -> None:
    """Called after a redo step."""
    _on_history_step(*_args)


# ---------------------------------------------------------------------------
# Register / unregister
# ---------------------------------------------------------------------------

def register() -> None:
    """Append all app handler callbacks.  Safe to call multiple times."""
    _pairs: list[tuple[list, Callable]] = [
        (bpy.app.handlers.load_post, _on_load_post),
        (bpy.app.handlers.undo_post, _on_undo_post),
        (bpy.app.handlers.redo_post, _on_redo_post),
    ]
    for handler_list, callback in _pairs:
        # Guard against double-append (e.g. F8 reload without unregister).
        if callback not in handler_list:
            handler_list.append(callback)
            _appended.append((handler_list, callback))
            _log.debug("App handler registered: %s → %s",
                       _handler_list_name(handler_list), callback.__name__)


def unregister() -> None:
    """Remove all tracked app handler callbacks."""
    for handler_list, callback in reversed(_appended):
        try:
            handler_list.remove(callback)
        except ValueError:
            # Handler already removed by another path; harmless.
            pass
    _appended.clear()
    _log.debug("All app handlers unregistered")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _handler_list_name(handler_list: list) -> str:
    """Best-effort human-readable name for a ``bpy.app.handlers.*`` list."""
    for attr in dir(bpy.app.handlers):
        if getattr(bpy.app.handlers, attr, None) is handler_list:
            return f"bpy.app.handlers.{attr}"
    return repr(handler_list)
