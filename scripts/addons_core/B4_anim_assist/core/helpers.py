"""Shared utility helpers: auto-key, undo, redraw, depsgraph."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import bpy

from .logging import get_logger

__all__ = [
    "confirm_dialog",
    "report_failure",
    "is_auto_key_enabled",
    "auto_key_guard",
    "undo_transaction",
    "redraw_notify",
    "safe_depsgraph_update",
]

_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Auto-key
# ---------------------------------------------------------------------------

def is_auto_key_enabled(context: bpy.types.Context | None = None) -> bool:
    """Check if Blender's auto-keying is currently enabled."""
    ctx = context or bpy.context
    scene = getattr(ctx, "scene", None)
    if scene is None:
        return False
    ts = getattr(scene, "tool_settings", None)
    if ts is None:
        return False
    return bool(ts.use_keyframe_insert_auto)


@contextmanager
def auto_key_guard(
    context: bpy.types.Context | None = None,
    force_off: bool = True,
) -> Iterator[bool]:
    """Temporarily disable auto-keying.  Yields the original state."""
    ctx = context or bpy.context
    scene = getattr(ctx, "scene", None)
    ts = getattr(scene, "tool_settings", None) if scene else None
    if ts is None:
        yield False
        return

    was_on = ts.use_keyframe_insert_auto
    if force_off and was_on:
        ts.use_keyframe_insert_auto = False

    try:
        yield was_on
    finally:
        ts.use_keyframe_insert_auto = was_on


# ---------------------------------------------------------------------------
# Undo
# ---------------------------------------------------------------------------

@contextmanager
def undo_transaction(
    name: str = "Anim Assist",
    context: bpy.types.Context | None = None,
) -> Iterator[None]:
    """Best-effort undo marker for non-operator .blend edits."""
    ctx = context or bpy.context
    window = getattr(ctx, "window", None)
    area = getattr(ctx, "area", None)
    region = getattr(ctx, "region", None)

    if window is not None and area is not None and region is not None:
        try:
            with ctx.temp_override(window=window, area=area, region=region):
                if bpy.ops.ed.undo_push.poll():
                    bpy.ops.ed.undo_push(message=name)
        except Exception:
            _log.debug("undo_push unavailable; proceeding without", exc_info=True)
    else:
        _log.debug("undo_push skipped: no valid UI context")

    try:
        yield
    except Exception:
        _log.exception("Operation after undo marker '%s' failed", name)
        raise


# ---------------------------------------------------------------------------
# Redraw / depsgraph
# ---------------------------------------------------------------------------

def redraw_notify(context: bpy.types.Context | None = None) -> None:
    """Tag animation editors and viewports for refresh after programmatic keyframe changes."""
    ctx = context or bpy.context
    screen = getattr(ctx, "screen", None)
    if screen is None:
        return
    redraw_types = {"GRAPH_EDITOR", "DOPESHEET_EDITOR", "VIEW_3D", "PROPERTIES"}
    for area in screen.areas:
        if area.type in redraw_types:
            area.tag_redraw()


def safe_depsgraph_update(context: bpy.types.Context | None = None) -> None:
    """Force Blender to re-evaluate the dependency graph after transform writes, with error handling."""
    ctx = context or bpy.context
    vl = getattr(ctx, "view_layer", None)
    if vl is None:
        return
    try:
        vl.update()
    except Exception:
        _log.debug("view_layer.update() skipped", exc_info=True)


def report_failure(
    operator: bpy.types.Operator,
    what: str,
    fix: str,
    exc: BaseException | None = None,
    *,
    detail: str | None = None,
    level: str = "ERROR",
) -> set[str]:
    """Report a failure the animator can act on: what happened + what to do next.

    The raw exception goes to the log (with traceback), never to the UI.
    *detail* is user-meaningful text worth showing inline (e.g. a regex error).
    Returns ``{"CANCELLED"}`` so callers can ``return report_failure(...)``.
    """
    if exc is not None:
        _log.error("%s [%s]", what, getattr(operator, "bl_idname", "?"), exc_info=exc)
    msg = f"{what} ({detail}). {fix}" if detail else f"{what}. {fix}"
    operator.report({level}, msg)
    return {"CANCELLED"}


def confirm_dialog(operator: bpy.types.Operator, context: bpy.types.Context, event, message: str) -> set[str]:  # type: ignore[no-untyped-def]
    """Ask before a consequential action, stating the consequence.

    Uses the richer dialog when the running Blender has it (4.1+) and falls
    back to the plain confirm on older builds.
    """
    wm = context.window_manager
    try:
        return wm.invoke_confirm(operator, event, message=message, confirm_text=operator.bl_label, icon="WARNING")
    except TypeError:  # pragma: no cover - Blender < 4.1
        return wm.invoke_confirm(operator, event)
