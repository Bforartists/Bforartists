# --- LIPSYNC BAKE ENGINE (Phase 12) ---
"""Bake engine for the Phase 12 lipsync system.

v12 additions
-------------
- bake_shape_keys(): writes shape key fcurves from a cue list (mirror of
  bake_lipsync but for Object.data.shape_keys.key_blocks[name].value).
- clear_auto_shape_key_keys(): mirror of clear_auto_keys for shape keys.
- Both honour the manual override sanctuary identically to the bone path.

Manual override sanctuary
-------------------------
Per-keyframe flags stored on the Action's id_data, keyed by fcurve
(data_path + array_index) and by frame number. Bake skips writes to manual
frames; clear_auto_keys deletes only non-manual keyframes.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from types import SimpleNamespace

from . import p12_viseme_library as vl
from .fcurve_compat import get_fcurves, find_fcurve, ensure_fcurve
from .logging import get_logger

_KEY_MANUAL_OVERRIDE = "aa_p12_manual"
_KEY_AUTO_BAKED = "aa_p12_auto"

__all__ = [
    "BakeRequest", "BakeReport", "bake_lipsync", "clear_auto_keys",
    "bake_shape_keys", "clear_auto_shape_key_keys",
    "is_manual_override", "mark_manual_override", "frame_for_time",
]

_log = get_logger(__name__)


def action_context(action, owner=None, anim_data=None, create=True):
    """Resolve the actual owner's slot, including detached layer Actions.

    With ``create=False`` (read-only callers) no slot is added; None is
    returned when the owner has no slot yet.

    Never redirect a live AnimData block to a different Action. Legacy/stub
    Actions retain their existing interface and manual-flag storage.
    """
    if hasattr(action, "fcurves"):
        return anim_data
    owner = owner or getattr(anim_data, "id_data", None)
    if anim_data is None and owner is not None:
        anim_data = getattr(owner, "animation_data", None)
    if anim_data is not None and getattr(anim_data, "action", None) == action:
        if getattr(anim_data, "action_slot", None) is not None:
            return anim_data
    slots = getattr(action, "slots", ())
    if owner is None:
        if len(slots) != 1:
            raise ValueError("Lipsync requires an animated owner to resolve this Action slot")
        return SimpleNamespace(action=action, action_slot=slots[0], id_data=None)
    matches = [slot for slot in slots if slot.target_id_type == owner.id_type
               and (slot.name_display == owner.name or owner in slot.users())]
    if len(matches) > 1:
        raise ValueError("Lipsync Action has multiple slots for this owner; bind the intended slot first")
    if not matches:
        # Detached layer Actions are keyed and read without an owner, through
        # their only slot (generic "Slot", or the owner's name before a rename).
        # Reuse it: a second slot would hide lipsync keys from the layer stack.
        matches = [slot for slot in slots
                   if slot.target_id_type in (owner.id_type, 'UNSPECIFIED')]
        if len(matches) != 1 or len(slots) != 1:
            matches = []
    if not matches and not create:
        return None
    slot = matches[0] if matches else action.slots.new(id_type=owner.id_type, name=owner.name)
    if anim_data is not None and getattr(anim_data, "action", None) == action:
        anim_data.action_slot = slot
        return anim_data
    return SimpleNamespace(action=action, action_slot=slot, id_data=owner)


@dataclass
class BakeRequest:
    armature: object
    action: object
    cues: list
    library_id: str
    user_pose_overrides: list
    rig_wiring: dict
    fps: float
    frame_offset: int
    anticipation_frames: int


@dataclass
class BakeReport:
    keys_written: int
    keys_skipped_manual: int
    bones_touched: int
    cue_count: int
    range_start: int
    range_end: int


def frame_for_time(time_seconds, fps, frame_offset):
    if fps <= 0:
        return frame_offset
    return frame_offset + int(round(time_seconds * fps))


# ---------------------------------------------------------------------------
# Manual flag storage - keyed by (data_path, array_index) -> set of frames
# ---------------------------------------------------------------------------

def _flag_storage_key(curve_path, curve_index):
    return _KEY_MANUAL_OVERRIDE + "::" + curve_path + "::" + str(curve_index)


def _read_manual_frames(action, key):
    payload = action.get(key) if hasattr(action, "get") else None
    if payload is None:
        return set()
    if isinstance(payload, str):
        try:
            decoded = json.loads(payload)
        except json.JSONDecodeError:
            return set()
    else:
        decoded = payload
    out = set()
    if isinstance(decoded, (list, tuple, set)):
        for item in decoded:
            try:
                out.add(int(item))
            except (TypeError, ValueError):
                continue
    return out


def _write_manual_frames(action, key, frames):
    if not hasattr(action, "__setitem__"):
        return
    action[key] = json.dumps(sorted(int(f) for f in frames))


def is_manual_override(action, curve_path, curve_index, key_index_or_frame, *, anim_data=None):
    frame = _resolve_to_frame(action, curve_path, curve_index, key_index_or_frame, anim_data=anim_data)
    if frame is None:
        return False
    return frame in _read_manual_frames(action, _flag_storage_key(curve_path, curve_index))


def mark_manual_override(action, curve_path, curve_index, key_index_or_frame, *, anim_data=None):
    frame = _resolve_to_frame(action, curve_path, curve_index, key_index_or_frame, anim_data=anim_data)
    if frame is None:
        return
    key = _flag_storage_key(curve_path, curve_index)
    frames = _read_manual_frames(action, key)
    frames.add(frame)
    _write_manual_frames(action, key, frames)


def _resolve_to_frame(action, curve_path, curve_index, value, *, anim_data=None):
    curve = find_fcurve(action, curve_path, curve_index, anim_data=anim_data)
    if curve is None:
        return int(value)
    points = list(getattr(curve, "keyframe_points", []))
    if 0 <= int(value) < len(points):
        co = getattr(points[int(value)], "co", None)
        if co is not None:
            return int(round(co[0]))
    return int(value)


# ---------------------------------------------------------------------------
# Bone bake (existing v11 path)
# ---------------------------------------------------------------------------

def bake_lipsync(req):
    anim_data = action_context(req.action, owner=req.armature)
    library = vl.merge_user_overrides(req.library_id, req.user_pose_overrides)
    bones_touched = set()
    keys_written = 0
    keys_skipped = 0
    frames_seen = []

    for cue in req.cues:
        pose = library.get(cue.viseme_name) or library.get("rest") or {}
        if not pose:
            continue
        primary_frame = frame_for_time(cue.time_seconds, req.fps, req.frame_offset)
        antic_frame = primary_frame - max(0, req.anticipation_frames)
        if antic_frame == primary_frame:
            target_frames = (primary_frame,)
        else:
            target_frames = (antic_frame, primary_frame)
        frames_seen.extend(target_frames)
        for role, transforms in pose.items():
            loc, rot, scale = transforms
            bone_name = req.rig_wiring.get(role, "")
            if not bone_name:
                continue
            bones_touched.add(bone_name)
            for frame in target_frames:
                wrote, skipped = _write_bone_keys(
                    action=req.action, bone_name=bone_name, frame=frame,
                    loc=loc, rot=rot, scale=scale, anim_data=anim_data,
                )
                keys_written += wrote
                keys_skipped += skipped

    if not frames_seen:
        return BakeReport(0, 0, 0, len(req.cues), req.frame_offset, req.frame_offset)

    return BakeReport(
        keys_written, keys_skipped, len(bones_touched), len(req.cues),
        min(frames_seen), max(frames_seen),
    )


def clear_auto_keys(action, bone_names, *, anim_data=None):
    if action is None or not bone_names:
        return 0
    fcurves = get_fcurves(action, anim_data=anim_data)
    deleted = 0
    for bone_name in bone_names:
        prefix = 'pose.bones["' + bone_name + '"].'
        for curve in list(fcurves):
            data_path = getattr(curve, "data_path", "")
            if not data_path.startswith(prefix):
                continue
            curve_index = getattr(curve, "array_index", 0)
            manual_frames = _read_manual_frames(action, _flag_storage_key(data_path, curve_index))
            keyframe_points = list(getattr(curve, "keyframe_points", []))
            for i in range(len(keyframe_points) - 1, -1, -1):
                co = getattr(keyframe_points[i], "co", None)
                if co is None:
                    continue
                frame = int(round(co[0]))
                if frame in manual_frames:
                    continue
                try:
                    curve.keyframe_points.remove(keyframe_points[i])
                    deleted += 1
                except (RuntimeError, ReferenceError):
                    pass
    return deleted


def _write_bone_keys(action, bone_name, frame, loc, rot, scale, *, anim_data=None):
    written = 0
    skipped = 0
    channels = (
        ('pose.bones["' + bone_name + '"].location', loc),
        ('pose.bones["' + bone_name + '"].rotation_euler', rot),
        ('pose.bones["' + bone_name + '"].scale', scale),
    )
    for path, values in channels:
        for axis, value in enumerate(values):
            curve = _ensure_fcurve(action, path, axis, anim_data=anim_data)
            if curve is None:
                continue
            manual_frames = _read_manual_frames(action, _flag_storage_key(path, axis))
            if frame in manual_frames:
                skipped += 1
                continue
            inserted = _insert_or_replace_key(curve, frame, value)
            if inserted is not None:
                written += 1
    return written, skipped


def _ensure_fcurve(action, data_path, array_index, *, anim_data=None):
    return ensure_fcurve(action, data_path, array_index, anim_data=anim_data)


def _find_point_at_frame(curve, frame):
    points = getattr(curve, "keyframe_points", None)
    if not points:
        return None
    for i, point in enumerate(points):
        co = getattr(point, "co", None)
        if co is None:
            continue
        if int(round(co[0])) == frame:
            return i
    return None


def _insert_or_replace_key(curve, frame, value):
    insert = getattr(curve.keyframe_points, "insert", None)
    if insert is None:
        return None
    try:
        options = {"REPLACE"} if _find_point_at_frame(curve, frame) is not None else set()
        insert(frame, value, options=options)
    except TypeError:
        try:
            insert(frame, value)
        except (RuntimeError, TypeError):
            return None
    except RuntimeError:
        return None
    return _find_point_at_frame(curve, frame)


# ===========================================================================
# v12: SHAPE KEY BAKE PATH
# ===========================================================================

def bake_shape_keys(action, cues, shape_key_wiring, fps, frame_offset, anticipation_frames=2, *, anim_data=None):
    """Write shape key fcurves from *cues* onto the shape-keys *action*.

    Parameters
    ----------
    action : the ShapeKey block's animation_data.action (NOT the armature's action)
    cues : list of objects with .time_seconds and .viseme_name (Cue or AA_P12_CueRow)
    shape_key_wiring : dict {viseme_name: shape_key_block_name}
    fps : scene fps
    frame_offset : the audio strip's start frame
    anticipation_frames : how many frames before each cue to pre-shape the mouth

    Returns BakeReport. Manual override sanctuary applies.
    """
    if action is None or not cues or not shape_key_wiring:
        return BakeReport(0, 0, 0, len(cues) if cues else 0, frame_offset, frame_offset)
    anim_data = action_context(action, anim_data=anim_data)

    keys_written = 0
    keys_skipped = 0
    keys_touched: set = set()
    frames_seen = []

    # Build a value-per-frame map per shape key. Each viseme key gets value
    # 1.0 at its cue frame, 0.0 at the frame right after (for sharp reads).
    # For more polished blending, the SHIPPED bake just writes 1.0 at the
    # active cue frame and lets fcurve interpolation handle in/out.
    for cue in cues:
        viseme = cue.viseme_name
        primary_frame = frame_for_time(cue.time_seconds, fps, frame_offset)
        antic_frame = primary_frame - max(0, anticipation_frames)
        target_frames = (antic_frame, primary_frame) if antic_frame != primary_frame else (primary_frame,)
        frames_seen.extend(target_frames)

        # For every wired shape key, write a value: 1.0 if its viseme matches
        # this cue, 0.0 otherwise. This produces clean per-viseme channels.
        for v_name, key_name in shape_key_wiring.items():
            if not key_name:
                continue
            data_path = 'key_blocks["' + key_name + '"].value'
            curve = _ensure_fcurve(action, data_path, 0, anim_data=anim_data)
            if curve is None:
                continue
            keys_touched.add(key_name)
            value = 1.0 if v_name == viseme else 0.0
            for frame in target_frames:
                manual_frames = _read_manual_frames(action, _flag_storage_key(data_path, 0))
                if frame in manual_frames:
                    keys_skipped += 1
                    continue
                inserted = _insert_or_replace_key(curve, frame, value)
                if inserted is not None:
                    keys_written += 1

    if not frames_seen:
        return BakeReport(0, 0, 0, len(cues), frame_offset, frame_offset)

    return BakeReport(
        keys_written=keys_written,
        keys_skipped_manual=keys_skipped,
        bones_touched=len(keys_touched),  # repurposed to "shape keys touched"
        cue_count=len(cues),
        range_start=min(frames_seen),
        range_end=max(frames_seen),
    )


def clear_auto_shape_key_keys(action, key_block_names, *, anim_data=None):
    """Remove auto-baked shape key keys; preserve manual override frames."""
    if action is None or not key_block_names:
        return 0
    fcurves = get_fcurves(action, anim_data=anim_data)
    deleted = 0
    for key_name in key_block_names:
        if not key_name:
            continue
        data_path = 'key_blocks["' + key_name + '"].value'
        for curve in list(fcurves):
            if getattr(curve, "data_path", "") != data_path:
                continue
            manual_frames = _read_manual_frames(action, _flag_storage_key(data_path, 0))
            keyframe_points = list(getattr(curve, "keyframe_points", []))
            for i in range(len(keyframe_points) - 1, -1, -1):
                co = getattr(keyframe_points[i], "co", None)
                if co is None:
                    continue
                frame = int(round(co[0]))
                if frame in manual_frames:
                    continue
                try:
                    curve.keyframe_points.remove(keyframe_points[i])
                    deleted += 1
                except (RuntimeError, ReferenceError):
                    pass
    return deleted
