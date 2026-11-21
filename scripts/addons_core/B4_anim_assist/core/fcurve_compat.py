# --- FCURVE API COMPATIBILITY ---
"""Compatibility helpers for accessing F-Curves across Blender/Bforartists versions.

Blender 4.4 introduced "layered actions" (slots, layers, strips, channelbags),
and Blender 5.0 removed the legacy ``action.fcurves`` attribute entirely.
Bforartists 5.x inherits this change.

This module provides a single import point so the rest of the addon never
touches ``action.fcurves`` directly.  Every helper gracefully falls back
between the legacy and layered APIs.

Usage
-----
::

    from .fcurve_compat import get_fcurves, find_fcurve, ensure_fcurve

    # Iterating — pass the animation_data when available for accuracy:
    for fc in get_fcurves(action, anim_data=obj.animation_data):
        ...

    # Finding an existing fcurve:
    fc = find_fcurve(action, data_path, index, anim_data=adata)

    # Creating or ensuring an fcurve exists:
    fc = ensure_fcurve(action, data_path, index, anim_data=adata)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bpy

# ---------------------------------------------------------------------------
# Internal: resolve a channelbag from a layered action
# ---------------------------------------------------------------------------

def _get_channelbag(
    action: "bpy.types.Action",
    anim_data: "bpy.types.AnimData | None" = None,
):
    """Return the first matching ActionChannelbag for *action*.

    Tries to resolve the correct slot in this order:

    1. ``anim_data.action_slot`` (the slot bound to the animated ID)
    2. ``action.slots[0]`` (fallback for detached actions)
    3. ``None`` if the action has no slots at all
    """
    slot = None

    if anim_data is not None:
        slot = getattr(anim_data, "action_slot", None)

    if slot is None:
        slots = getattr(action, "slots", None)
        if slots and len(slots) > 0:
            slot = slots[0]

    if slot is None:
        return None

    # Walk the layer stack and return the first channelbag for this slot.
    try:
        from bpy_extras import anim_utils
        return anim_utils.action_get_channelbag_for_slot(action, slot)
    except (ImportError, AttributeError):
        pass

    # Manual fallback if bpy_extras helper is unavailable.
    for layer in getattr(action, "layers", ()):
        for strip in getattr(layer, "strips", ()):
            channelbag_fn = getattr(strip, "channelbag", None)
            if channelbag_fn is not None:
                channelbag = channelbag_fn(slot)
                if channelbag is not None:
                    return channelbag

    return None


def _ensure_channelbag(
    action: "bpy.types.Action",
    anim_data: "bpy.types.AnimData | None" = None,
):
    """Return (or create) a channelbag for writing fcurves into *action*.

    Uses ``bpy_extras.anim_utils.action_ensure_channelbag_for_slot`` when
    available, which will create a layer and keyframe strip if needed.
    """
    slot = None

    if anim_data is not None:
        slot = getattr(anim_data, "action_slot", None)

    if slot is None:
        slots = getattr(action, "slots", None)
        if slots is not None and len(slots) > 0:
            slot = slots[0]
        elif slots is not None:
            # Blender 4.4+: a freshly created Action has NO slots, so there is
            # nowhere to put fcurves and new_fcurve() would return None.
            # Create one, typed for the owner when known, and bind it.
            try:
                owner = getattr(anim_data, "id_data", None)
                id_type = getattr(owner, "id_type", None) or "OBJECT"
                name = getattr(owner, "name", None) or "Slot"
                slot = slots.new(id_type=id_type, name=name)
                if anim_data is not None and getattr(anim_data, "action", None) == action:
                    try:
                        anim_data.action_slot = slot
                    except (AttributeError, TypeError, RuntimeError):
                        pass
            except (AttributeError, TypeError, RuntimeError):
                slot = None

    if slot is None:
        return None

    try:
        from bpy_extras import anim_utils
        return anim_utils.action_ensure_channelbag_for_slot(action, slot)
    except (ImportError, AttributeError):
        pass

    # Fallback to read-only fetch.
    return _get_channelbag(action, anim_data)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_LEGACY_API: bool | None = None


def _has_legacy_api(action: "bpy.types.Action") -> bool:
    """Check once whether ``action.fcurves`` exists (legacy Blender < 5.0)."""
    global _LEGACY_API
    if _LEGACY_API is not None:
        return _LEGACY_API
    _LEGACY_API = hasattr(action, "fcurves")
    return _LEGACY_API


def get_fcurves(
    action: "bpy.types.Action",
    *,
    anim_data: "bpy.types.AnimData | None" = None,
) -> list:
    """Return a list of all F-Curves in *action*.

    Parameters
    ----------
    action : bpy.types.Action
        The action to read from.
    anim_data : bpy.types.AnimData, optional
        The AnimData block that owns this action.  Providing it allows
        the correct action slot to be resolved automatically.

    Returns
    -------
    list[bpy.types.FCurve]
        A plain list of fcurves, safe to iterate and index.
    """
    if action is None:
        return []

    # Legacy path (Blender < 5.0).
    if _has_legacy_api(action):
        try:
            return list(action.fcurves)
        except (AttributeError, TypeError):
            pass

    # Layered path (Blender 5.0+ / Bforartists 5.x).
    channelbag = _get_channelbag(action, anim_data)
    if channelbag is None:
        return []
    return list(channelbag.fcurves)


def find_fcurve(
    action: "bpy.types.Action",
    data_path: str,
    index: int = 0,
    *,
    anim_data: "bpy.types.AnimData | None" = None,
):
    """Find an existing F-Curve by *data_path* and *index*.

    Returns the F-Curve or ``None`` if not found.
    """
    if action is None:
        return None

    if _has_legacy_api(action):
        try:
            return action.fcurves.find(data_path, index=index)
        except (AttributeError, TypeError):
            pass

    channelbag = _get_channelbag(action, anim_data)
    if channelbag is None:
        return None

    fcurves_collection = getattr(channelbag, "fcurves", None)
    if fcurves_collection is None:
        return None

    find_fn = getattr(fcurves_collection, "find", None)
    if find_fn is not None:
        return find_fn(data_path, index=index)

    # Manual search fallback.
    for fc in fcurves_collection:
        if fc.data_path == data_path and fc.array_index == index:
            return fc
    return None


def new_fcurve(
    action: "bpy.types.Action",
    data_path: str,
    index: int = 0,
    *,
    anim_data: "bpy.types.AnimData | None" = None,
):
    """Create a new F-Curve on *action* for *data_path* and *index*.

    Returns the newly created F-Curve, or ``None`` if creation failed.
    """
    if action is None:
        return None

    if _has_legacy_api(action):
        try:
            return action.fcurves.new(data_path, index=index)
        except (AttributeError, TypeError):
            pass

    channelbag = _ensure_channelbag(action, anim_data)
    if channelbag is None:
        return None

    fcurves_collection = getattr(channelbag, "fcurves", None)
    if fcurves_collection is None:
        return None

    new_fn = getattr(fcurves_collection, "new", None)
    if new_fn is not None:
        return new_fn(data_path, index=index)
    return None


def ensure_fcurve(
    action: "bpy.types.Action",
    data_path: str,
    index: int = 0,
    *,
    anim_data: "bpy.types.AnimData | None" = None,
):
    """Return an existing F-Curve or create one if it does not exist.

    Convenience wrapper combining :func:`find_fcurve` and :func:`new_fcurve`.
    """
    fc = find_fcurve(action, data_path, index, anim_data=anim_data)
    if fc is not None:
        return fc
    return new_fcurve(action, data_path, index, anim_data=anim_data)
