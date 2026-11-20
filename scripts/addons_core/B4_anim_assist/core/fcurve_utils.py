"""FCurve inspection, snapshot, and classification helpers."""

from __future__ import annotations

from dataclasses import dataclass

import bpy

__all__ = [
    "classify_transform_channel",
    "KeyframeSnapshot",
    "get_keyframe_snapshots",
    "get_selected_key_snapshots",
    "get_selected_key_frames",
    "is_channel_locked",
    "is_channel_muted",
    "is_channel_hidden",
    "get_locked_channels",
    "get_muted_channels",
    "get_hidden_channels",
    "get_visible_unlocked_channels",
    "ChannelSnapshot",
    "get_channel_snapshots",
    "get_selected_channel_snapshots",
    "get_bone_name_from_fcurve",
    "get_sub_path_from_bone_fcurve",
]


# ---------------------------------------------------------------------------
# Transform classifier
# ---------------------------------------------------------------------------

_TRANSFORM_SUBPATHS: dict[str, str] = {
    "location": "LOCATION",
    "rotation_euler": "ROTATION",
    "rotation_quaternion": "ROTATION",
    "rotation_axis_angle": "ROTATION",
    "scale": "SCALE",
}


def classify_transform_channel(data_path: str) -> str | None:
    """Map an FCurve data_path to a transform category: LOCATION, ROTATION, or SCALE.

    Returns None if the path is not a standard transform property. Used by filter
    and isolation operators to work with groups of related channels without naming
    them individually (e.g., "show only arm rotation").
    """
    if '"].' in data_path:
        sub = data_path.split('"].', 1)[-1]
    else:
        sub = data_path
    return _TRANSFORM_SUBPATHS.get(sub)


# ---------------------------------------------------------------------------
# Keyframe snapshots
# ---------------------------------------------------------------------------

@dataclass
class KeyframeSnapshot:
    """Frozen copy of a keyframe's state including handles and interpolation.

    Captured before destructive operations (offset, retime, mirror) so the
    original values are available for undo or delta computation.
    """

    frame: float
    value: float
    selected: bool
    interpolation: str
    handle_left: tuple[float, float]
    handle_right: tuple[float, float]


def get_keyframe_snapshots(
    fcurve: bpy.types.FCurve,
    selected_only: bool = False,
) -> list[KeyframeSnapshot]:
    """Capture complete keyframe state (position, value, handles, interpolation) before mutations.

    Creates immutable snapshots so operators can undo destructive transformations.
    When *selected_only* is True, returns only selected keyframe points.
    """
    results: list[KeyframeSnapshot] = []
    for kp in fcurve.keyframe_points:
        if selected_only and not kp.select_control_point:
            continue
        results.append(
            KeyframeSnapshot(
                frame=float(kp.co[0]),
                value=float(kp.co[1]),
                selected=bool(kp.select_control_point),
                interpolation=kp.interpolation,
                handle_left=(float(kp.handle_left[0]), float(kp.handle_left[1])),
                handle_right=(
                    float(kp.handle_right[0]),
                    float(kp.handle_right[1]),
                ),
            )
        )
    return results


def get_selected_key_snapshots(
    fcurve: bpy.types.FCurve,
) -> list[KeyframeSnapshot]:
    """Return snapshots for **selected** keyframe points only."""
    return get_keyframe_snapshots(fcurve, selected_only=True)


def get_selected_key_frames(fcurve: bpy.types.FCurve) -> list[float]:
    """Return frame numbers of all selected keypoints in an FCurve, sorted in time order.

    Used by offset, retime, and trajectory operators to iterate selected keyframes.
    """
    return sorted(
        float(kp.co[0])
        for kp in fcurve.keyframe_points
        if kp.select_control_point
    )


# ---------------------------------------------------------------------------
# Per-channel queries
# ---------------------------------------------------------------------------

def is_channel_locked(fcurve: bpy.types.FCurve) -> bool:
    """Return True if the FCurve is locked against editing."""
    return bool(fcurve.lock)


def is_channel_muted(fcurve: bpy.types.FCurve) -> bool:
    """Return True if the FCurve is muted (not evaluated during playback)."""
    return bool(fcurve.mute)


def is_channel_hidden(fcurve: bpy.types.FCurve) -> bool:
    """Return True if the FCurve is hidden from the Graph Editor or Dopesheet."""
    return bool(fcurve.hide)


# ---------------------------------------------------------------------------
# Bulk channel filters
# ---------------------------------------------------------------------------

def get_locked_channels(
    fcurves: list[bpy.types.FCurve] | None,
) -> list[bpy.types.FCurve]:
    """Filter a list of FCurves to return only locked channels."""
    if not fcurves:
        return []
    return [fc for fc in fcurves if fc.lock]


def get_muted_channels(
    fcurves: list[bpy.types.FCurve] | None,
) -> list[bpy.types.FCurve]:
    """Filter a list of FCurves to return only muted channels."""
    if not fcurves:
        return []
    return [fc for fc in fcurves if fc.mute]


def get_hidden_channels(
    fcurves: list[bpy.types.FCurve] | None,
) -> list[bpy.types.FCurve]:
    """Filter a list of FCurves to return only hidden channels."""
    if not fcurves:
        return []
    return [fc for fc in fcurves if fc.hide]


def get_visible_unlocked_channels(
    fcurves: list[bpy.types.FCurve] | None,
) -> list[bpy.types.FCurve]:
    """Filter a list of FCurves to return only visible, unlocked, editable channels.

    Used by batch transformation operators to avoid modifying protected animation.
    """
    if not fcurves:
        return []
    return [fc for fc in fcurves if not fc.hide and not fc.lock]


# ---------------------------------------------------------------------------
# Channel snapshots
# ---------------------------------------------------------------------------

@dataclass
class ChannelSnapshot:
    """Frozen copy of an FCurve channel's visibility, lock, and selection state.

    Used by isolation (key selection and channel) and diagnostics to inspect channel properties
    without mutating the live FCurve.
    """

    data_path: str
    array_index: int
    is_locked: bool
    is_muted: bool
    is_hidden: bool
    is_selected: bool
    transform_type: str | None


def get_channel_snapshots(
    fcurves: list[bpy.types.FCurve] | None,
) -> list[ChannelSnapshot]:
    """Capture visibility, lock, mute, and selection state of FCurves for undo support.

    Snapshots include transform classification so callers can filter by channel type
    when restoring or comparing channel visibility.
    """
    if not fcurves:
        return []
    results: list[ChannelSnapshot] = []
    for fc in fcurves:
        results.append(
            ChannelSnapshot(
                data_path=fc.data_path,
                array_index=fc.array_index,
                is_locked=bool(fc.lock),
                is_muted=bool(fc.mute),
                is_hidden=bool(fc.hide),
                is_selected=bool(getattr(fc, "select", False)),
                transform_type=classify_transform_channel(fc.data_path),
            )
        )
    return results


def get_selected_channel_snapshots(
    fcurves: list[bpy.types.FCurve] | None,
) -> list[ChannelSnapshot]:
    """Return snapshots for **selected** channels only.

    Uses RNA ``FCurve.select`` as the selection signal.
    """
    return [s for s in get_channel_snapshots(fcurves) if s.is_selected]


# ---------------------------------------------------------------------------
# Bone-related FCurve parsing
# ---------------------------------------------------------------------------

def get_bone_name_from_fcurve(fcurve: bpy.types.FCurve) -> str | None:
    """Extract pose bone name from an FCurve data_path (e.g., 'pose.bones[\"Hand.L\"].location').

    Returns None if the path is not a bone property. Used to correlate animation
    channels with their source bones for batch operations.
    """
    dp = fcurve.data_path
    if not dp.startswith('pose.bones["'):
        return None
    start = len('pose.bones["')
    end = dp.find('"]', start)
    if end < 0:
        return None
    return dp[start:end]


def get_sub_path_from_bone_fcurve(fcurve: bpy.types.FCurve) -> str | None:
    """Extract the property name suffix from a bone FCurve path (e.g., 'location', 'rotation_euler').

    Returns None if the path is not a bone property. Useful for identifying which
    transform or custom property is being animated.
    """
    dp = fcurve.data_path
    idx = dp.find('"].')
    if idx < 0:
        return None
    return dp[idx + 3:]