"""Shared context helpers for key selection and channel animation editor operators."""

from __future__ import annotations

import bpy

from .fcurve_compat import get_fcurves

__all__ = [
    "ANIM_EDITOR_SPACES",
    "in_anim_editor",
    "iter_visible_fcurves",
    "iter_selected_keys",
    "key_identity",
]

ANIM_EDITOR_SPACES = {"GRAPH_EDITOR", "DOPESHEET_EDITOR"}


def in_anim_editor(context: bpy.types.Context) -> bool:
    """Return True if the current context is a Graph Editor or Dopesheet view.

    Used as a poll() guard to disable key selection and channel keyframe operators outside
    animation editors where they would have no meaning.
    """
    space = getattr(context, "space_data", None)
    return bool(space) and space.type in ANIM_EDITOR_SPACES


def iter_visible_fcurves(context: bpy.types.Context, only_selected: bool = False):
    """Yield editable object-Action FCurves in the current editor.

    Filters by visibility (``fc.hide``), mute, and editability. When
    *only_selected* is ``True`` also restricts to selected channels.
    """
    space = getattr(context, "space_data", None)
    if space is None or space.type not in ANIM_EDITOR_SPACES:
        return
    if space.type == "GRAPH_EDITOR" and getattr(space, "mode", "") == "DRIVERS":
        return  # Drivers are not Action keys.
    # Native collections honor editor filters and channel visibility.
    # Detached pinned Actions and non-object sources have no supported owner here;
    # the sidebar explicitly identifies excluded source channels.
    # An empty collection is meaningful: never broaden it to an object's Action.
    native = getattr(context, "editable_fcurves", ()) or ()
    visible = {fc.as_pointer() for fc in native
               if not fc.hide and not fc.lock and not fc.mute
               and (not only_selected or fc.select)}
    seen = set()
    for obj in context.view_layer.objects:
        ad = obj.animation_data
        if not ad or not ad.action or not ad.action.is_editable:
            continue
        # Resolve each bound slot before deduplication: shared Actions may have
        # distinct slots and must not be deduplicated by Action identity alone.
        for fc in get_fcurves(ad.action, anim_data=ad):
            ptr = fc.as_pointer()
            if ptr in visible and ptr not in seen:
                seen.add(ptr)
                yield obj, ad.action, fc


def iter_selected_keys(context: bpy.types.Context):
    """Yield ``(obj, action, fcurve, kp_index, kp)`` for selected keyframes."""
    for obj, action, fc in iter_visible_fcurves(context):
        for i, kp in enumerate(fc.keyframe_points):
            if kp.select_control_point:
                yield obj, action, fc, i, kp


def key_identity(obj_name: str, fc: bpy.types.FCurve, frame: float) -> tuple:
    """Create a hashable identity tuple for a specific keyframe (object, path, index, frame).

    Used by the metadata system (key selection and channel) to index per-key data without relying on
    collection indices, which change when keys are added/deleted.
    """
    return (obj_name, fc.data_path, fc.array_index, round(float(frame), 4))
