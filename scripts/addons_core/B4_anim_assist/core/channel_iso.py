"""Channel isolation / filtering helpers (key selection and channel)."""

from __future__ import annotations

import re
from typing import Callable

import bpy

from .fcurve_compat import get_fcurves

__all__ = [
    "iter_action_fcurves",
    "snapshot_state",
    "restore_state",
    "push_isolation",
    "pop_isolation",
    "clear_isolation_stack",
    "isolate_where",
    "match_data_path_regex",
    "match_transform_channel",
    "match_selected_bones",
    "match_custom_property",
]


# Module-level state stack (isolation snapshots).
_isolation_stack: list[dict] = []


def iter_action_fcurves(context: bpy.types.Context):
    """Yield ``(obj, action, fcurve)`` for every action used in the view layer.

    Deduplicates shared actions (linked characters etc.) by ``id(action)``.
    Includes hidden and muted FCurves — use this when you need to operate on
    *all* channels regardless of their visibility state (e.g. isolation ops).
    """
    view_layer = getattr(context, "view_layer", None)
    if view_layer is None:
        return
    seen: set[int] = set()
    for obj in view_layer.objects:
        ad = obj.animation_data
        if ad and ad.action and id(ad.action) not in seen:
            seen.add(id(ad.action))
            for fc in get_fcurves(ad.action, anim_data=ad):
                yield obj, ad.action, fc


def snapshot_state(context: bpy.types.Context) -> dict:
    """Capture the current visibility, mute, selection, and lock state of all FCurves.

    Used by the isolation stack to save state before isolation and restore it afterward.
    """
    snap = {}
    for _o, action, fc in iter_action_fcurves(context):
        key = (action.name, fc.data_path, fc.array_index)
        snap[key] = (bool(fc.hide), bool(fc.mute), bool(fc.select), bool(fc.lock))
    return snap


def restore_state(context: bpy.types.Context, snap: dict) -> int:
    """Restore FCurve visibility, mute, selection, and lock state from a snapshot.

    Returns the number of channels successfully restored. Used when popping from the
    isolation stack to return to the previous channel visibility state.
    """
    n = 0
    for _o, action, fc in iter_action_fcurves(context):
        key = (action.name, fc.data_path, fc.array_index)
        state = snap.get(key)
        if state is None:
            continue
        fc.hide, fc.mute, fc.select, fc.lock = state
        n += 1
    return n


def push_isolation(context: bpy.types.Context) -> None:
    """Save the current channel visibility state to the isolation stack.

    Called before isolate_where() to preserve the state for later restoration.
    """
    _isolation_stack.append(snapshot_state(context))


def pop_isolation(context: bpy.types.Context) -> bool:
    """Pop the most recent isolation state from the stack and restore it.

    Returns True if a state was popped, False if the stack was empty.
    Lets animators undo isolation and return to the previous channel view.
    """
    if not _isolation_stack:
        return False
    snap = _isolation_stack.pop()
    restore_state(context, snap)
    return True


def clear_isolation_stack() -> None:
    """Clear all saved isolation states from the stack (used on scene reload or tool cleanup)."""
    _isolation_stack.clear()


def isolate_where(
    context: bpy.types.Context,
    predicate: Callable[[bpy.types.Object, bpy.types.Action, bpy.types.FCurve], bool],
    push: bool = True,
) -> int:
    """Hide all FCurves except those matching *predicate*.

    Optionally pushes the pre-isolation state onto the stack for later restoration.
    Returns the number of channels left visible. Used to implement "show only arm
    rotation" workflows where animators focus on specific bone groups or transform types.
    """
    if push:
        push_isolation(context)
    shown = 0
    for _o, action, fc in iter_action_fcurves(context):
        keep = bool(predicate(_o, action, fc))
        fc.hide = not keep
        if keep:
            shown += 1
    return shown


def match_data_path_regex(
    pattern: str,
) -> Callable[[bpy.types.Object, bpy.types.Action, bpy.types.FCurve], bool]:
    """Return a predicate matching FCurves whose data_path matches the regex pattern."""
    rx = re.compile(pattern)

    def _predicate(_o: bpy.types.Object, _a: bpy.types.Action, fc: bpy.types.FCurve) -> bool:
        return bool(rx.search(fc.data_path))

    return _predicate


def match_transform_channel(
    channel: str,
) -> Callable[[bpy.types.Object, bpy.types.Action, bpy.types.FCurve], bool]:
    """Return a predicate matching FCurves of transform channels.

    Args:
        channel: One of 'loc', 'rot', 'scale', or 'all_transform'.
    """
    mapping = {
        "loc": ("location",),
        "rot": ("rotation_euler", "rotation_quaternion", "rotation_axis_angle"),
        "scale": ("scale",),
    }
    if channel == "all_transform":
        needles = mapping["loc"] + mapping["rot"] + mapping["scale"]
    else:
        needles = mapping.get(channel, ())

    def _predicate(_o: bpy.types.Object, _a: bpy.types.Action, fc: bpy.types.FCurve) -> bool:
        return any(n in fc.data_path for n in needles)

    return _predicate


def match_selected_bones(
    context: bpy.types.Context,
) -> Callable[[bpy.types.Object, bpy.types.Action, bpy.types.FCurve], bool]:
    """Return predicate matching fcurves of currently-selected pose bones."""
    bone_paths: set[str] = set()
    obj = context.object
    if obj and obj.type == "ARMATURE" and obj.mode == "POSE":
        for pb in context.selected_pose_bones or []:
            bone_paths.add(f'pose.bones["{bpy.utils.escape_identifier(pb.name)}"]')

    def _predicate(_o: bpy.types.Object, _a: bpy.types.Action, fc: bpy.types.FCurve) -> bool:
        return any(fc.data_path.startswith(p) for p in bone_paths)

    return _predicate


def match_custom_property(
) -> Callable[[bpy.types.Object, bpy.types.Action, bpy.types.FCurve], bool]:
    """Return a predicate matching custom property FCurves."""

    def _predicate(_o: bpy.types.Object, _a: bpy.types.Action, fc: bpy.types.FCurve) -> bool:
        return fc.data_path.startswith('["') or '][' in fc.data_path

    return _predicate
