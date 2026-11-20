"""Timeline and preview-range resolvers."""

from __future__ import annotations

import bpy

from .logging import get_logger

__all__ = [
    "get_scene_frame_range",
    "get_preview_range",
    "get_effective_frame_range",
    "get_current_frame",
]

_log = get_logger(__name__)


def get_scene_frame_range(
    context: bpy.types.Context | None = None,
) -> tuple[int, int]:
    """Return the full animation frame range stored in the scene (frame_start, frame_end).

    This is the complete animation duration, regardless of preview range status.
    """
    ctx = context or bpy.context
    scene = getattr(ctx, "scene", None)
    if scene is None:
        return (1, 250)
    return (scene.frame_start, scene.frame_end)


def get_preview_range(
    context: bpy.types.Context | None = None,
) -> tuple[int, int] | None:
    """Return the preview range (frame_preview_start, frame_preview_end) if enabled, else None.

    The preview range is a subset used for playback testing; when disabled, the scene
    range is used instead.
    """
    ctx = context or bpy.context
    scene = getattr(ctx, "scene", None)
    if scene is None:
        return None
    if not scene.use_preview_range:
        return None
    return (scene.frame_preview_start, scene.frame_preview_end)


def get_effective_frame_range(
    context: bpy.types.Context | None = None,
) -> tuple[int, int]:
    """Return preview range if active, otherwise scene range."""
    preview = get_preview_range(context)
    if preview is not None:
        return preview
    return get_scene_frame_range(context)


def get_current_frame(
    context: bpy.types.Context | None = None,
) -> int:
    """Return the playhead position (current frame) in the timeline."""
    ctx = context or bpy.context
    scene = getattr(ctx, "scene", None)
    if scene is None:
        return 1
    return scene.frame_current