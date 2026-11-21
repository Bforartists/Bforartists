"""Read-only, editor-local NLA targeting. No active-Action fallback."""
from dataclasses import dataclass

import bpy


@dataclass(frozen=True)
class ClipTarget:
    owner: object
    track: object
    strip: object
    track_index: int


def in_nla(context):
    return getattr(getattr(context, "space_data", None), "type", "") == "NLA_EDITOR"


def targets(context, *, active=False):
    if not in_nla(context):
        return []
    strips = ([getattr(context, "active_nla_strip", None)] if active else
              list(getattr(context, "selected_nla_strips", ()) or ()))
    pointers = {s.as_pointer() for s in strips if s is not None}
    result = []
    for owner in context.scene.objects:
        ad = owner.animation_data
        if not ad:
            continue
        for index, track in enumerate(ad.nla_tracks):
            for strip in track.strips:
                if strip.as_pointer() in pointers:
                    result.append(ClipTarget(owner, track, strip, index))
    return result


def active_target(context):
    found = targets(context, active=True)
    return found[0] if len(found) == 1 else None


def require_editable(context, items, *, single=False):
    if not in_nla(context):
        raise ValueError("Use the NLA Editor")
    if not items or (single and len(items) != 1):
        raise ValueError("Select one Action clip" if single else "Select Action clips in this editor")
    if context.scene.is_nla_tweakmode:
        raise ValueError("Finish editing the Action before arranging clips")
    for item in items:
        if not item.owner.is_editable or item.track.lock:
            raise ValueError(f"Unlock the editable track for {item.owner.name}: {item.track.name}")
        if item.strip.type != "CLIP" or item.strip.action is None:
            raise ValueError("Select Action clips; transition, meta and sound strips are not supported")
    return items


def source_references(action):
    """Actual assignments and clip references, excluding fake-user bookkeeping."""
    if action is None:
        return 0
    def count_strips(strips):
        return sum((int(s.action == action) if s.type == "CLIP" else
                    count_strips(s.strips) if s.type == "META" else 0) for s in strips)
    count = 0
    for obj in bpy.data.objects:
        ad = obj.animation_data
        if not ad:
            continue
        count += int(ad.action == action and not ad.use_tweak_mode)
        for track in ad.nla_tracks:
            count += count_strips(track.strips)
    return count


def strip_curves(strip):
    if strip.type != "CLIP" or not strip.action:
        return []
    from bpy_extras.anim_utils import action_get_channelbag_for_slot
    bag = action_get_channelbag_for_slot(strip.action, strip.action_slot)
    return list(bag.fcurves) if bag else []


def latest_bake(owner):
    return max((a for a in bpy.data.actions if a.get("animassist_nla_bake_target") == owner),
               key=lambda a: int(a.get("animassist_nla_bake_order", 0)), default=None)


def is_correction(strip):
    return bool(strip.type == "CLIP" and strip.action and strip.action.is_editable
                and strip.action.get("animassist_nla_correction") == 1 and strip.blend_type == "COMBINE")


def correction_reason(item):
    """Conservative supported contract for transform-delta correction creation."""
    obj = item.owner
    if item.strip.type != "CLIP" or not item.strip.action:
        return "Assign a source Action to this clip"
    if obj.animation_data.action:
        return "Push down or stash the active Action before adding a correction"
    if item.track.mute or item.strip.mute or any(t.is_solo for t in obj.animation_data.nla_tracks):
        return "Unmute the source and clear track Solo before adding a correction"
    if obj.constraints or (obj.pose and any(b.constraints for b in obj.pose.bones)):
        return "Correction creation supports unconstrained transforms; bake constraints first"
    if obj.animation_data.drivers:
        return "Correction creation does not support driven transforms"
    curves = strip_curves(item.strip)
    if not curves:
        return "The source clip has no transform channels in its assigned Action slot"
    allowed = {"location", "rotation_euler", "rotation_quaternion", "rotation_axis_angle", "scale"}
    for fc in curves:
        path = fc.data_path
        if path not in allowed:
            if not (path.startswith('pose.bones["') and path.rsplit(".", 1)[-1] in allowed):
                return "Correction creation supports object and pose-bone transform channels only"
            try:
                obj.path_resolve(path.rsplit(".", 1)[0])
            except (ValueError, KeyError):
                return "A source bone channel cannot be resolved on this owner"
    return ""
