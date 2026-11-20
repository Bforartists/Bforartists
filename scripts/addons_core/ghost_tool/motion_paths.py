"""motion_paths.py — Per-bone / per-object motion paths drawn by Ghost Tool.

A path is the world position of a bone head (or tail, or an object origin)
sampled over a frame window.  Samples live in a module cache keyed by
(object_name, bone_name, frame).  Pinned paths come from
scene.ghost_tool.motion_paths; "follow selection" adds transient grey paths
for the current selection.  Drawing is a separate POST_VIEW handler.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, replace
from typing import Optional

import blf
import bmesh
import bpy
import gpu
from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader
from mathutils import Matrix, Vector

from .motion_channels import LOCATION_CHANNELS, MOTION_CHANNELS, channel_family, rest_channel_matrix
from .utils import debug, get_fcurves_from_action, get_scene_id, is_native_transform_active, log, scene_sampling, tag_viewport_redraw, warn

PALETTE: tuple[tuple[float, float, float], ...] = (
    (0.96, 0.71, 0.00), (0.31, 0.76, 0.97), (0.51, 0.78, 0.52), (0.90, 0.45, 0.45),
    (0.73, 0.53, 0.93), (0.98, 0.60, 0.30), (0.36, 0.85, 0.80), (0.85, 0.85, 0.40),
)
FOLLOW_COLOR: tuple[float, float, float] = (0.6, 0.6, 0.6)
SLOW_RGB = (0.2, 0.4, 1.0)
FAST_RGB = (1.0, 0.3, 0.1)
KEY_DOT_COLOR = (1.0, 1.0, 1.0, 0.95)

PathKey = tuple[str, str, int]  # (object_name, bone_name, vertex_index); "" / -1 = object origin
ORIGIN_PATHS = ("location", "delta_location")   # the object channels that move its origin

_cache: dict[tuple[str, str, int, float], Vector] = {}   # (*PathKey, frame)
_dirty: set[PathKey] = set()
# Cache keys a refresh tried and could not sample (a vertex absent at that frame): drawn as a gap,
# never re-requested until the path is dirtied or leaves the window.
_gaps: set[tuple[str, str, int, float]] = set()
# (*PathKey, key frame) -> (left, right) world handle points, or None when that key has no location handle.
_handles: dict[tuple[str, str, int, float], Optional[tuple[Vector, Vector]]] = {}
# Round E: keys whose cached samples came from the fast sampler. A key that stops being fast-eligible
# (a constraint added, a parent animated) is re-stepped even if no depsgraph update dirtied it.
_fast_keys: set = set()
# On: eligible paths may be read straight from their curves. A refresh then no longer leaves the scene
# re-evaluated at the playhead as a side effect of stepping. Off: always step frames.
FAST_SAMPLING = True
# Auto: use the fast sampler only once stepping has been measured slow in this scene. Reading curves in
# Python costs about the same per sample everywhere, while a frame_set covers every path at once: on a
# light rig stepping is faster (~5 vs ~20 ms for the 500-sample gate); on a scene that re-evaluates heavy
# geometry each frame it is far slower (~70 vs ~4 ms for 100 samples). Off: fast whenever eligible.
FAST_AUTO = True
FAST_STEP_MS_PER_FRAME = 0.5   # measured stepping cost at or above which auto mode switches to fast
_step_ms_per_frame: Optional[float] = None   # last measured cost of one stepped frame in the cache's scene
_step_measured_at = 0.0   # perf_counter time of that measurement
# A measurement expires: a scene measured slow is re-measured (one stepped refresh) after this long, so
# deleting the heavy object or hiding its modifiers brings the light rig back to stepping (review a1abef3d).
FAST_REMEASURE_S = 10.0
_draw_handler = None
_draw_handler_2d = None
_last_refresh_ms: float = 0.0
_marker_uids: dict[str, set[str]] = {}   # per scene id: ghost markers created by Markers on Paths
_anchors: dict[PathKey, str] = {}        # anchor each cached path was sampled with
_cache_scene: Optional[str] = None       # scene id the cached positions were sampled in


@dataclass(frozen=True)
class PathTarget:
    key: PathKey
    obj: bpy.types.Object
    anchor: str          # 'HEAD' | 'TAIL'
    color: tuple[float, float, float]
    thickness: int
    pinned: bool
    color_before: tuple[float, float, float] = FOLLOW_COLOR   # style SPLIT: the stretch before the playhead
    dot_size: int = 6
    in_front: bool = True
    frames: tuple[float, ...] = ()   # the frames this path covers: its own range or the global one


def clear_cache() -> None:
    _cache.clear()
    _gaps.clear()
    _handles.clear()
    _fast_keys.clear()
    _dirty.clear()
    _anchors.clear()


RANGE_PROPS = ("use_own_range", "own_range_mode", "own_before", "own_after", "own_step", "own_start", "own_end")


def desired_frames(settings, scene: bpy.types.Scene, entry=None) -> list[float]:
    """Frames of the global range, or of ``entry``'s own range when it overrides it."""
    if settings.paths_use_marker_counts and not (entry is not None and entry.use_own_range):
        step = max(1, settings.paths_step)
        current = scene.frame_current
        return [float(current + i * step)
                for i in range(-settings.paths_markers_before, settings.paths_markers_after + 1)
                if scene.frame_start <= current + i * step <= scene.frame_end]
    if entry is not None and entry.use_own_range:
        mode, before, after, step = entry.own_range_mode, entry.own_before, entry.own_after, entry.own_step
        custom = (entry.own_start, entry.own_end)
    else:
        mode, before, after, step = (settings.paths_range_mode, settings.paths_before,
                                     settings.paths_after, settings.paths_step)
        custom = (settings.custom_range_start, settings.custom_range_end)
    if mode == 'SCENE':
        start, end = scene.frame_start, scene.frame_end
    elif mode == 'CUSTOM':
        start, end = custom
    else:
        start = scene.frame_current - before
        end = scene.frame_current + after
    return [float(f) for f in range(int(start), int(end) + 1, max(1, step))]


def own_range_seed(settings, entry) -> dict:
    """Range fields the settings dialog starts from: a path without its own range starts
    from the global range, so ticking Own Range changes nothing until a field is edited."""
    if entry.use_own_range:
        return {}
    if settings.paths_use_marker_counts:
        return {"own_range_mode": 'AROUND_CURSOR',
                "own_before": settings.paths_markers_before * settings.paths_step,
                "own_after": settings.paths_markers_after * settings.paths_step,
                "own_step": settings.paths_step,
                "own_start": settings.custom_range_start, "own_end": settings.custom_range_end}
    return {"own_range_mode": settings.paths_range_mode, "own_before": settings.paths_before,
            "own_after": settings.paths_after, "own_step": settings.paths_step,
            "own_start": settings.custom_range_start, "own_end": settings.custom_range_end}


def own_range_props(mode: str) -> tuple[str, ...]:
    """The frame fields a path's own range mode needs, as the popover's global fields."""
    if mode == 'AROUND_CURSOR':
        return ("own_before", "own_after")
    if mode == 'CUSTOM':
        return ("own_start", "own_end")
    return ()


def _resolve(scene: bpy.types.Scene, object_name: str, bone_name: str,
             vertex_index: int = -1) -> Optional[bpy.types.Object]:
    obj = scene.objects.get(object_name)   # an object unlinked from this scene has no path here
    if obj is None:
        return None
    if vertex_index >= 0:
        return obj if _vertex_usable(obj, vertex_index) else None
    if bone_name and (obj.type != 'ARMATURE' or bone_name not in obj.pose.bones):
        return None
    return obj


def _vertex_usable(obj: bpy.types.Object, index: int) -> bool:
    """A vertex path needs a mesh whose evaluated vertex count matches its own: a modifier that
    changes topology (Subdivision) renumbers the vertices, so the index no longer names one."""
    if obj.type != 'MESH' or index >= len(obj.data.vertices):
        return False
    try:
        ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        return len(ev.data.vertices) == len(obj.data.vertices)
    except Exception:
        return False


def entry_key(entry) -> PathKey:
    return (entry.object_name, entry.bone_name, entry.vertex_index)


def entry_is_missing(entry) -> bool:
    if entry.is_folder:
        return False
    return _resolve(entry.id_data, *entry_key(entry)) is None   # id_data: the owning scene


def folder_rows(settings) -> dict:
    """Folder rows by key."""
    return {e.folder_key: e for e in settings.motion_paths if e.is_folder}


def entry_shown(entry, folders: dict) -> bool:
    """A path draws when it and its folder are visible. A path whose folder is gone is a top-level path."""
    if not entry.visible:
        return False
    parent = folders.get(entry.folder) if entry.folder else None
    return parent is None or parent.visible


def list_rows(settings) -> list[tuple[int, bool]]:
    """(index, shown) in list order: top-level paths, then each folder followed by its paths.
    A collapsed folder hides its paths."""
    paths = settings.motion_paths
    folders = folder_rows(settings)
    children: dict[str, list[int]] = {}
    rows: list[tuple[int, bool]] = []
    for index, entry in enumerate(paths):
        if entry.is_folder:
            continue
        if entry.folder in folders:
            children.setdefault(entry.folder, []).append(index)
        else:
            rows.append((index, True))
    for index, entry in enumerate(paths):
        if entry.is_folder:
            rows.append((index, True))
            rows += [(child, not entry.collapsed) for child in children.get(entry.folder_key, [])]
    return rows


def pinned_targets(scene: bpy.types.Scene) -> list[PathTarget]:
    settings = scene.ghost_tool
    shared = tuple(desired_frames(settings, scene))
    folders = folder_rows(settings)
    targets: list[PathTarget] = []
    for entry in settings.motion_paths:
        if entry.is_folder or not entry_shown(entry, folders):
            continue
        obj = _resolve(scene, *entry_key(entry))
        if obj is None:
            continue
        frames = tuple(desired_frames(settings, scene, entry)) if entry.use_own_range else shared
        target = PathTarget(entry_key(entry), obj, entry.anchor,
                                  tuple(entry.color), entry.thickness, True,
                                  color_before=tuple(entry.color_before), dot_size=entry.dot_size,
                                  in_front=entry.in_front, frames=frames)
        targets.append(_with_sampling_mode(target, settings, scene, entry))
    return targets


def selected_keys(context: bpy.types.Context) -> list[tuple[PathKey, bpy.types.Object]]:
    """(key, object) for the selection: pose bones in Pose mode, mesh vertices in Edit Mode, else objects."""
    result: list[tuple[PathKey, bpy.types.Object]] = []
    if context.mode == 'EDIT_MESH':
        for obj in getattr(context, 'objects_in_mode', None) or []:
            if obj.type == 'MESH':
                bm = bmesh.from_edit_mesh(obj.data)
                bm.verts.index_update()   # vertices added in Edit Mode carry stale or -1 indices until renumbered
                result += [((obj.name, "", v.index), obj) for v in bm.verts if v.select]
        return result
    if context.mode == 'POSE':
        for pb in getattr(context, 'selected_pose_bones', None) or []:
            result.append(((pb.id_data.name, pb.name, -1), pb.id_data))
        return result
    for obj in getattr(context, 'selected_objects', None) or []:
        if obj.get("ghost_tool_mesh_ghost"):
            continue
        if obj.type == 'ARMATURE':
            roots = [b for b in obj.pose.bones if b.parent is None]
            if roots:
                result.append(((obj.name, roots[0].name, -1), obj))
                continue
        result.append(((obj.name, "", -1), obj))
    return result


def follow_targets(context: bpy.types.Context, pinned_keys: set[PathKey]) -> list[PathTarget]:
    settings = context.scene.ghost_tool
    if not settings.paths_follow_selection:
        return []
    frames = tuple(desired_frames(settings, context.scene))
    seen: set[PathKey] = set(pinned_keys)
    targets: list[PathTarget] = []
    for key, obj in selected_keys(context):
        if key in seen or key[2] >= 0:   # Follow is for bones and objects: an Edit Mode selection can be thousands
            continue
        seen.add(key)
        target = PathTarget(key, obj, 'HEAD', FOLLOW_COLOR, 1, False, frames=frames)
        targets.append(_with_sampling_mode(target, settings, context.scene))
    return targets


def all_targets(context: bpy.types.Context) -> list[PathTarget]:
    pinned = pinned_targets(context.scene)
    # Follow is for unpinned selections: a pinned path hidden by its eye or its folder stays hidden.
    pinned_keys = {entry_key(e) for e in context.scene.ghost_tool.motion_paths if not e.is_folder}
    return pinned + follow_targets(context, pinned_keys)


def _sample(depsgraph, obj: bpy.types.Object, bone_name: str, anchor: str,
            vertex_index: int = -1) -> Optional[Vector]:
    ev = obj.evaluated_get(depsgraph)
    if vertex_index >= 0:
        verts = ev.data.vertices   # the evaluated mesh: armature, shape keys and other deformers applied
        # Topology can change per frame (an animated modifier): then the index names no vertex here,
        # and the path gets a gap, not a point at the object origin.
        if len(verts) != len(obj.data.vertices) or vertex_index >= len(verts):
            return None
        return (ev.matrix_world @ verts[vertex_index].co).copy()
    if bone_name:
        pb = ev.pose.bones[bone_name]
        local = pb.tail if anchor == 'TAIL' else pb.head
        return (ev.matrix_world @ local).copy()
    return ev.matrix_world.translation.copy()


def mark_dirty(key: PathKey) -> None:
    _dirty.add(key)


def forget(key) -> None:
    """Drop one path's cached positions, so a draw sees it as unsampled and asks for a refresh.
    An (object, bone) pair means vertex -1: the Head/Tail callback passes one, and only bones have a tail."""
    key = tuple(key) if len(key) == 3 else (*key, -1)
    for stale in [c for c in _cache if c[:3] == key]:
        del _cache[stale]
    _gaps.difference_update([g for g in _gaps if g[:3] == key])
    for stale in [h for h in _handles if h[:3] == key]:
        del _handles[stale]
    _fast_keys.discard(key)
    _anchors.pop(key, None)


def _dependencies(obj: bpy.types.Object) -> set[str]:
    """Names of the objects whose motion can move ``obj``: parents and constraint
    targets, followed transitively (a parent's parent, a target's parent)."""
    seen: set[str] = set()
    stack = [obj]
    while stack:
        o = stack.pop()
        refs = [o.parent] + [getattr(c, 'target', None) for c in o.constraints]
        # Deformers (Armature, Hook, Lattice...) move a vertex path's vertices.
        refs += [m.object for m in getattr(o, 'modifiers', ())
                 if isinstance(getattr(m, 'object', None), bpy.types.Object)]
        if o.type == 'ARMATURE' and o.pose is not None:
            refs += [getattr(c, 'target', None) for pb in o.pose.bones for c in pb.constraints]
        for ref in refs:
            if ref is not None and ref.name not in seen and ref is not obj:
                seen.add(ref.name)
                stack.append(ref)
    return seen


def mark_dirty_for_id(block) -> None:
    """A depsgraph update on this ID: re-sample the paths that depend on it, including
    paths of children and constraint users whose position follows the changed object."""
    if isinstance(block, bpy.types.Object):
        changed = {block.name}
    elif isinstance(block, bpy.types.Action):
        changed = {obj.name for obj in bpy.data.objects
                   if (obj.animation_data and obj.animation_data.action == block)
                   or _shape_key_action(obj) == block}
    elif isinstance(block, (bpy.types.Key, bpy.types.Mesh)):
        # Shape-key or mesh edits move a vertex path's vertex, never an origin or a bone.
        changed = {obj.name for obj in bpy.data.objects
                   if obj.data is block or getattr(obj.data, 'shape_keys', None) is block}
    else:
        return
    if not changed:
        return
    affected: dict[str, bool] = {}
    for key in _cache_keys():
        name = key[0]
        if name not in affected:
            obj = bpy.data.objects.get(name)
            affected[name] = name in changed or (obj is not None and not changed.isdisjoint(_dependencies(obj)))
        if affected[name]:
            _dirty.add(key)


def _cache_keys() -> set[PathKey]:
    # Gaps count: a path made only of gaps must still be dirtied when its mesh or deformer changes.
    return {c[:3] for c in _cache} | {g[:3] for g in _gaps}


def refresh_paths(context: bpy.types.Context) -> int:
    """Sample what the window needs and the cache lacks. Returns samples taken.

    The timing behind the slow warning always describes this refresh: one that
    samples nothing costs nothing, so the warning clears."""
    global _cache_scene, _last_refresh_ms
    scene = context.scene
    settings = scene.ghost_tool
    if not settings.paths_enabled:
        _last_refresh_ms = 0.0
        return 0
    global _step_ms_per_frame, _step_measured_at
    if get_scene_id(scene) != _cache_scene:
        clear_cache()   # positions sampled in another scene may differ (drivers, constraints)
        _cache_scene = get_scene_id(scene)
        _step_ms_per_frame = None   # another scene steps at its own cost
    targets = all_targets(context)
    from .path_fast_sampler import fast_eligible, sample_fast
    measured_slow = (_step_ms_per_frame is not None and _step_ms_per_frame >= FAST_STEP_MS_PER_FRAME
                     and time.perf_counter() - _step_measured_at < FAST_REMEASURE_S)
    use_fast = FAST_SAMPLING and (not FAST_AUTO or measured_slow)
    # Eligibility and mode are separate: a fast-sampled path that is still eligible keeps its samples
    # (they are right) when auto mode steps again to re-measure; only a path that lost eligibility is
    # re-stepped in full (review 898f536d).
    eligible = {t.key for t in targets if FAST_SAMPLING and fast_eligible(t.obj, t.key[1], t.key[2], scene=scene)}
    fast = eligible if use_fast else set()
    for t in targets:
        if _anchors.get(t.key, t.anchor) != t.anchor:
            _dirty.add(t.key)   # HEAD <-> TAIL: the cached positions belong to the other point
        _anchors[t.key] = t.anchor
        if t.key in _fast_keys and t.key not in eligible:
            _dirty.add(t.key)   # sampled fast but no longer eligible: re-step every frame
            _fast_keys.discard(t.key)
    # Each path keeps the frames of its own window, so a wider per-path range keeps its extras.
    wanted = {(*t.key, f) for t in targets for f in t.frames}
    for stale in [c for c in _cache if c not in wanted]:
        del _cache[stale]
    _gaps.intersection_update(wanted)
    for stale in [h for h in _handles if h not in wanted]:
        del _handles[stale]
    for t in targets:
        if t.key in _dirty:
            for f in t.frames:
                _cache.pop((*t.key, f), None)
                _gaps.discard((*t.key, f))
                _handles.pop((*t.key, f), None)
    _dirty.clear()   # a dirty key that is no longer a target lost its samples with the wanted set
    missing: dict[float, list[PathTarget]] = {}
    fast_missing: dict = {}
    for t in targets:
        for f in t.frames:
            if (*t.key, f) not in _cache and (*t.key, f) not in _gaps:
                if t.key in fast:
                    fast_missing.setdefault(t.key, (t, []))[1].append(f)
                else:
                    missing.setdefault(f, []).append(t)
    handle_needs: dict[float, list[PathTarget]] = {}
    if settings.paths_show_handles:
        for t in targets:
            for f in _handle_frames(t):
                if (*t.key, f) not in _handles:
                    handle_needs.setdefault(f, []).append(t)
    if not missing and not handle_needs and not fast_missing:
        _last_refresh_ms = 0.0
        return 0
    count = 0
    t0 = time.perf_counter()
    for key, (t, frames) in fast_missing.items():   # no frame_set: positions straight from the curves
        for f, point in zip(frames, sample_fast(t.obj, t.key[1], t.anchor, frames)):
            _cache[(*key, f)] = point
        _fast_keys.add(key)
        count += len(frames)
    if not missing and not handle_needs:
        _last_refresh_ms = (time.perf_counter() - t0) * 1000.0
        debug(f"Motion paths: fast-sampled {count} positions in {_last_refresh_ms:.1f} ms")
        return count
    stepped = sorted(set(missing) | set(handle_needs))
    t_step = time.perf_counter()
    with scene_sampling(scene):
        for f in stepped:
            scene.frame_set(int(f), subframe=f - int(f))
            depsgraph = context.evaluated_depsgraph_get()
            for t in missing.get(f, ()):
                point = _sample(depsgraph, t.obj, t.key[1], t.anchor, t.key[2])
                if point is None:
                    _gaps.add((*t.key, f))
                else:
                    _cache[(*t.key, f)] = point
                count += 1
            for t in handle_needs.get(f, ()):
                _handles[(*t.key, f)] = key_handles(t, f, depsgraph)
    if stepped:
        _step_ms_per_frame = (time.perf_counter() - t_step) * 1000.0 / len(stepped)
        _step_measured_at = time.perf_counter()
    _last_refresh_ms = (time.perf_counter() - t0) * 1000.0
    debug(f"Motion paths: sampled {count} positions in {_last_refresh_ms:.1f} ms")
    return count


def last_refresh_ms() -> float:
    return _last_refresh_ms


def _shape_key_action(obj) -> Optional[bpy.types.Action]:
    keys = getattr(getattr(obj, 'data', None), 'shape_keys', None)
    ad = getattr(keys, 'animation_data', None)
    return ad.action if ad else None


def key_frames(target: PathTarget) -> list[float]:
    """Frames with a keyframe on channels that move this target."""
    obj = target.obj
    ad = obj.animation_data
    frames: set[float] = set()
    if target.key[2] >= 0:
        # A vertex moves with its object and with its shape keys (deformer keys belong to other objects).
        action = _shape_key_action(obj)
        for fc in get_fcurves_from_action(action, None) if action else ():
            if fc.data_path.startswith("key_blocks[") and fc.data_path.endswith(".value"):
                frames.update(float(k.co.x) for k in fc.keyframe_points)
    if not ad or not ad.action:
        return sorted(frames)
    if target.key[2] >= 0:
        paths = set(ORIGIN_PATHS)
    elif target.key[1]:
        # Same channels as the path's markers: a head moves only by location, a tail also by rotation.
        bone = f'pose.bones["{bpy.utils.escape_identifier(target.key[1])}"].'
        channels = MOTION_CHANNELS if target.anchor == 'TAIL' else LOCATION_CHANNELS
        paths = {bone + channel_family(c) for c in channels}
    else:
        paths = set(ORIGIN_PATHS)
    for fc in get_fcurves_from_action(ad.action, obj):
        if fc.data_path in paths:
            frames.update(float(k.co.x) for k in fc.keyframe_points)
    return sorted(frames)


def _with_sampling_mode(target, settings, scene, entry=None):
    """Key counts walk keys on each side; frame spacing never filters out keys."""
    if settings.paths_sampling_mode != 'KEYFRAMES':
        return target
    keys = [f for f in key_frames(target) if scene.frame_start <= f <= scene.frame_end]
    skip = settings.paths_keyframe_skip
    if settings.paths_use_marker_counts and not (entry is not None and entry.use_own_range):
        current = scene.frame_current
        past = [f for f in reversed(keys) if f < current][::skip][:settings.paths_markers_before]
        ahead = [f for f in keys if f > current][::skip][:settings.paths_markers_after]
        frames = sorted(past + [f for f in keys if f == current] + ahead)
    elif target.frames:
        frames = [f for f in keys if target.frames[0] <= f <= target.frames[-1]][::skip]
    else:
        frames = []
    return replace(target, frames=tuple(frames))


def handle_eligible(target: PathTarget) -> bool:
    """Handles exist for a path the location curves move directly: an object origin or a bone head. A tail
    has no location curve of its own, a vertex has none, and a connected bone ignores its location."""
    if target.key[2] >= 0 or target.anchor == 'TAIL':
        return False
    if target.key[1]:
        pb = target.obj.pose.bones.get(target.key[1]) if target.obj.pose else None
        return pb is not None and not pb.bone.use_connect
    return True


def _handle_frames(target: PathTarget) -> list[float]:
    if not handle_eligible(target):
        return []
    frames = set(target.frames)
    return [f for f in key_frames(target) if f in frames]


def handle_transform(target: PathTarget, depsgraph=None):
    """(location data path, to_world, offset, current location) for a handle-eligible target, or None:
    world point = to_world @ (location values + offset). Object: parent world @ parent inverse, offset =
    delta location. Bone head: armature world @ rest_channel_matrix(bone, posed parent), no offset. Read at
    the scene's current frame; key_handles and the handle drag both use it, so a drag inverts exactly the
    map the drawn handles come from."""
    if not handle_eligible(target):
        return None
    obj = target.obj
    if not obj.animation_data or not obj.animation_data.action:
        return None
    return location_world_map(obj, target.key[1], depsgraph)


def location_world_map(obj: bpy.types.Object, bone_name: str = "", depsgraph=None):
    """(location data path, to_world, offset, current location): world point = to_world @ (location + offset)
    for an object origin or a bone head, at the scene's current frame. Shared by the handle drawing and drag
    and by Draw to Keys, which inverts it to key a world point. Constraints are not applied."""
    depsgraph = depsgraph or bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(depsgraph)
    if bone_name:
        pb = ev.pose.bones[bone_name]
        data_path = f'pose.bones["{bpy.utils.escape_identifier(bone_name)}"].location'
        to_world = ev.matrix_world @ rest_channel_matrix(pb, pb.parent.matrix if pb.parent else None)
        return data_path, to_world, Vector(), Vector(pb.location)
    to_world = (ev.parent.matrix_world @ ev.matrix_parent_inverse) if ev.parent else Matrix.Identity(4)
    return "location", to_world, Vector(ev.delta_location), Vector(ev.location)


def key_handles(target: PathTarget, frame: float, depsgraph=None) -> Optional[tuple[Vector, Vector]]:
    """(left, right) world points of the location handles of the key at ``frame``, or None.

    Built through the same local -> world map as the key value itself: the channel values of a key on
    location X/Y/Z are replaced by that curve's handle values (a curve without a key at this frame
    contributes its evaluated value). Object: parent world @ parent inverse @ (location + delta).
    Bone head: armature world @ rest_channel_matrix(bone, posed parent) @ location. The scene must be
    at ``frame`` (refresh_paths calls it while sampling). Constraints are not applied."""
    transform = handle_transform(target, depsgraph)
    if transform is None:
        return None
    data_path, to_world, offset, current = transform
    obj = target.obj
    ad = obj.animation_data
    curves = {fc.array_index: fc for fc in get_fcurves_from_action(ad.action, obj) if fc.data_path == data_path}
    left, right, keyed = [], [], False
    for axis in range(3):
        fc = curves.get(axis)
        key = next((k for k in fc.keyframe_points if abs(k.co.x - frame) < 1e-4), None) if fc else None
        if key is not None:
            left.append(key.handle_left.y)
            right.append(key.handle_right.y)
            keyed = True
        else:
            value = fc.evaluate(frame) if fc else current[axis]
            left.append(value)
            right.append(value)
    if not keyed:
        return None
    return to_world @ (Vector(left) + offset), to_world @ (Vector(right) + offset)


HANDLE_DOT_SIZE = 4.0


def path_segments(context, target: PathTarget, frames=None) -> list[tuple[Vector, Vector, tuple]]:
    """Coloured line segments of one path over ``frames`` (default: the path's own frames)."""
    frames = target.frames if frames is None else frames
    settings = context.scene.ghost_tool
    current = float(context.scene.frame_current)
    pts = [(f, _cache.get((*target.key, f))) for f in frames]
    # Only neighbouring frames join: a gap (a vertex absent at that frame) or a frame not yet sampled
    # breaks the line instead of being bridged by a straight segment.
    pairs = [(a, b) for a, b in zip(pts, pts[1:]) if a[1] is not None and b[1] is not None]
    if not pairs:
        return []
    r, g, b = target.color
    style = settings.paths_style
    span = max(frames[-1] - frames[0], 1.0)
    lengths = [(p1 - p0).length for (_f0, p0), (_f1, p1) in pairs]
    longest = max(lengths) or 1.0
    segs = []
    for i, ((f0, p0), (f1, p1)) in enumerate(pairs):
        if style == 'SPLIT':
            before, after = (*target.color_before, 0.9), (r, g, b, 0.9)
            if f0 < current < f1:
                # Split on the drawn straight line, so the colour change sits exactly on the path.
                mid = p0.lerp(p1, (current - f0) / (f1 - f0))
                segs += [(p0, mid, before), (mid, p1, after)]
                continue
            color = before if (f0 + f1) * 0.5 < current else after
        elif style == 'SPEED':
            t = lengths[i] / longest
            color = (SLOW_RGB[0] + (FAST_RGB[0] - SLOW_RGB[0]) * t,
                     SLOW_RGB[1] + (FAST_RGB[1] - SLOW_RGB[1]) * t,
                     SLOW_RGB[2] + (FAST_RGB[2] - SLOW_RGB[2]) * t, 0.9)
        elif style == 'FADE':
            d = min(abs((f0 + f1) * 0.5 - current) / span, 1.0)
            color = (r, g, b, max(0.9 * (1.0 - d), 0.1))
        else:
            color = (r, g, b, 0.9)
        segs.append((p0, p1, color))
    return segs


def _active_key(context) -> Optional[PathKey]:
    pb = getattr(context, 'active_pose_bone', None)
    if pb is not None:
        return (pb.id_data.name, pb.name, -1)
    obj = getattr(context, 'active_object', None)
    return (obj.name, "", -1) if obj is not None else None


def active_entry_index(context) -> int:
    """Index of the pinned path that follows the active bone or object, or -1."""
    key = _active_key(context)
    for index, entry in enumerate(context.scene.ghost_tool.motion_paths):
        if not entry.is_folder and entry_key(entry) == key:   # a folder may share an object's name
            return index
    return -1


def dialog_props(entry) -> tuple[str, ...]:
    """Properties the path settings dialog shows: the before-colour only for style Split,
    the anchor only for bones (an object origin has no tail)."""
    names = ["color"]
    if entry.id_data.ghost_tool.paths_style == 'SPLIT':   # id_data: the owning scene
        names.append("color_before")
    names += ["thickness", "dot_size"]
    if entry.bone_name:
        names.append("anchor")
    return tuple(names) + RANGE_PROPS


def list_active_key(settings) -> Optional[PathKey]:
    """Key of the path selected in the list, or None."""
    paths = settings.motion_paths
    if 0 <= settings.motion_paths_index < len(paths):
        entry = paths[settings.motion_paths_index]
        return None if entry.is_folder else entry_key(entry)
    return None


def _depth_mode(target: PathTarget) -> str:
    """Draw handlers run with no depth test, so 'in front' needs none; 'behind' turns it on."""
    return 'NONE' if target.in_front else 'LESS_EQUAL'


def _passes_for(target: PathTarget, is_list_active: bool, glow_on: bool) -> list[tuple[int, Optional[float]]]:
    """(extra width, alpha or None for the segment's own) per line pass, drawn in order:
    the list's active entry gets a wide faint glow under its line."""
    if is_list_active and glow_on:
        return [(4, 0.25), (0, None)]
    return [(0, None)]


def draw_parts(context, target: PathTarget) -> tuple[list, list[Vector], list[Vector], list[Vector]]:
    """What one path draws: (line segments, key dots, handle line vertices, handle end points).
    A path without a segment (a one-frame window) still shows its key dots and handles."""
    settings = context.scene.ghost_tool
    segs = path_segments(context, target)
    dots: list[Vector] = []
    if settings.paths_show_key_dots:
        dots = [_cache[(*target.key, f)] for f in key_frames(target) if (*target.key, f) in _cache]
    lines: list[Vector] = []
    ends: list[Vector] = []
    if settings.paths_show_handles and target.pinned:
        for f in _handle_frames(target):
            handle, point = _handles.get((*target.key, f)), _cache.get((*target.key, f))
            if handle is None or point is None:
                continue
            lines += [point, handle[0], point, handle[1]]
            ends += list(handle)
    return segs, dots, lines, ends


def draw_motion_paths() -> None:
    context = bpy.context
    scene = context.scene
    if not hasattr(scene, 'ghost_tool'):
        return
    settings = scene.ghost_tool
    if not settings.is_active or not settings.paths_enabled:
        return
    if request_missing_samples(context) and get_scene_id(scene) != _cache_scene:
        return   # cache belongs to another scene; the scheduled refresh replaces it
    active = _active_key(context)
    list_active = list_active_key(settings)
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    gpu.state.blend_set('ALPHA')
    try:
        for target in all_targets(context):
            segs, dots, lines, ends = draw_parts(context, target)
            if not (segs or dots or lines):
                continue
            gpu.state.depth_test_set(_depth_mode(target))
            width = target.thickness + (1 if target.key == active else 0)
            is_list_active = target.pinned and target.key == list_active
            for extra, alpha in _passes_for(target, is_list_active, settings.paths_active_glow) if segs else ():
                gpu.state.line_width_set(float(width + extra))
                buckets: dict[tuple, list[Vector]] = {}
                for p0, p1, color in segs:
                    if alpha is not None:
                        color = (*color[:3], alpha)
                    buckets.setdefault(tuple(round(c, 2) for c in color), []).extend((p0, p1))
                for color, verts in buckets.items():
                    batch = batch_for_shader(shader, 'LINES', {"pos": verts})
                    shader.bind(); shader.uniform_float("color", color); batch.draw(shader)
            if dots:
                gpu.state.point_size_set(float(target.dot_size))
                batch = batch_for_shader(shader, 'POINTS', {"pos": dots})
                shader.bind(); shader.uniform_float("color", KEY_DOT_COLOR); batch.draw(shader)
            if lines:
                color = (*target.color, 0.6)
                gpu.state.line_width_set(1.0)
                batch = batch_for_shader(shader, 'LINES', {"pos": lines})
                shader.bind(); shader.uniform_float("color", color); batch.draw(shader)
                gpu.state.point_size_set(HANDLE_DOT_SIZE)
                batch = batch_for_shader(shader, 'POINTS', {"pos": ends})
                shader.bind(); shader.uniform_float("color", color); batch.draw(shader)
    finally:
        gpu.state.line_width_set(1.0)
        gpu.state.point_size_set(1.0)
        gpu.state.depth_test_set('NONE')   # the state the handler was called with
        gpu.state.blend_set('NONE')


def draw_frame_numbers() -> None:
    context = bpy.context
    scene = context.scene
    if not hasattr(scene, 'ghost_tool'):
        return
    settings = scene.ghost_tool
    if not (settings.is_active and settings.paths_enabled and settings.paths_show_frame_numbers):
        return
    if get_scene_id(scene) != _cache_scene:
        return   # cached positions belong to another scene
    region, rv3d = context.region, context.region_data
    if region is None or rv3d is None:
        return
    font = 0
    blf.size(font, 11)
    blf.color(font, 0.9, 0.9, 0.9, 0.9)
    for target in all_targets(context):
        for f in target.frames:
            pos = _cache.get((*target.key, f))
            if pos is None:
                continue
            p2 = view3d_utils.location_3d_to_region_2d(region, rv3d, pos)
            if p2 is None:
                continue
            blf.position(font, p2.x + 4, p2.y + 4, 0)
            blf.draw(font, f"{int(f)}")


def sync_markers(context) -> int:
    """Markers on paths: ghost markers for the pinned paths, or none.

    Only markers this function owns are touched; Generate's markers stay, except one on the
    same key as a path marker, which it takes over (and removes with it when turned off). A re-sync
    reconciles instead of rebuilding: a marker whose (object, bone, channel, frame) is
    still wanted keeps its uid, pin and selection and only takes the new position; a
    pinned marker that left the window stays until Markers on Paths is turned off.

    Markers sit on the path: keys on sampled frames in a legacy frame window,
    all sampled frames in a count window, at the path's anchor. A bone's
    own rotation never moves its head, and a rotation drag aims the tail, so a HEAD path
    carries location markers only and a TAIL path carries location and rotation markers."""
    from .ghost_data import (GhostStore, generate_ghosts_at_keyframes,
                             generate_ghosts_frame_step, LOCATION_CHANNELS, MOTION_CHANNELS)
    scene = context.scene
    settings = scene.ghost_tool
    store = GhostStore.get(scene)
    owned = _marker_uids.setdefault(get_scene_id(scene), set())
    current = {g.uid: g for g in (store.get_by_uid(uid) for uid in owned) if g is not None}
    if not settings.paths_show_markers:
        for uid in current:
            store.remove(uid)
        owned.clear()
        tag_viewport_redraw(context)
        return 0
    by_identity = {(g.object_name, g.bone_name, g.channel, g.frame): g for g in current.values()}
    # A Generate marker on the same key is taken over, never doubled: it moves onto the path and
    # becomes a path marker (owned), the same way Generate defers to path markers on a rebuild.
    others = {(g.object_name, g.bone_name, g.channel, g.frame): g for g in store if g.uid not in current}
    wanted: set[str] = set()
    # One job per object, anchor and window: paths with their own range get their own window.
    # A path with an empty window wants no markers; the reconcile below still removes old ones.
    bones_by_job: dict[tuple[str, str, tuple[float, ...]], list[str]] = {}
    object_paths: list[tuple[str, tuple[float, ...]]] = []
    for t in pinned_targets(scene):
        if not t.frames or t.key[2] >= 0:   # a vertex has no key of its own to drag
            continue
        if t.key[1]:
            bones_by_job.setdefault((t.key[0], t.anchor, t.frames), []).append(t.key[1])
        else:
            object_paths.append((t.key[0], t.frames))
    jobs = [(name, bones, bpy.data.objects[name], anchor,
             MOTION_CHANNELS if anchor == 'TAIL' else LOCATION_CHANNELS, frames)
            for (name, anchor, frames), bones in bones_by_job.items()]
    jobs += [(name, [], None, None, MOTION_CHANNELS, frames) for name, frames in object_paths]
    moved = relevelled = False
    for object_name, bones, armature, anchor, channels, frames in jobs:
        window = (frames[0], frames[-1])   # fractional animation keys are valid too
        sampled = set(frames)   # with Every > 1 a key between samples has no point on the path
        ghosts = generate_ghosts_at_keyframes(bpy.data.objects[object_name], armature, bones, channels,
                                              frame_range=window, anchor=anchor, frames=sampled)
        if settings.paths_use_marker_counts:
            # Counts include in-between samples, not just keys that happen to
            # fall on the line. Keep the current-frame pose out of this pair.
            samples = [f for f in frames if f != scene.frame_current]
            ghosts = [g for g in ghosts if g.frame != scene.frame_current]
            ghosts += generate_ghosts_frame_step(bpy.data.objects[object_name], armature, bones,
                                                 channels, samples, anchor=anchor)
        for g in ghosts:
            identity = (g.object_name, g.bone_name, g.channel, g.frame)
            kept = by_identity.get(identity) or others.get(identity)
            if kept is not None:
                if tuple(kept.world_position) != tuple(g.world_position) or kept.local_value != g.local_value:
                    moved = True
                kept.world_position, kept.local_value = g.world_position, g.local_value
                kept.parent_frame_a, kept.parent_frame_b = g.parent_frame_a, g.parent_frame_b
                if kept.generation_level != g.generation_level:   # a taken-over marker is a keyframe marker now
                    kept.generation_level = g.generation_level
                    relevelled = moved = True
                wanted.add(kept.uid)
            else:
                store.add(g)
                wanted.add(g.uid)
    for uid, g in current.items():
        if uid not in wanted and not g.is_pinned:
            store.remove(uid)
    owned.clear()
    owned.update(wanted | {uid for uid, g in current.items() if g.is_pinned})
    if relevelled:
        store._update_level_counts()   # count_by_level caches per-level totals at add/remove time
    if moved:
        store._bump_version()   # in-place moves are invisible to version-keyed caches otherwise
    tag_viewport_redraw(context)
    return len(wanted)


def reset_for_new_file() -> None:
    """A loaded file has new ghosts and scenes: forget cached positions and marker ownership."""
    global _cache_scene
    clear_cache()
    _marker_uids.clear()
    _cache_scene = None


def owned_markers(scene) -> list:
    """The markers Markers on Paths created in this scene, so a store rebuild can keep them."""
    from .ghost_data import GhostStore
    owned = _marker_uids.get(get_scene_id(scene), set())
    return [g for g in GhostStore.get(scene) if g.uid in owned]


def request_missing_samples(context) -> bool:
    """Schedule a pipeline refresh when a drawn path lacks samples. Safe in a draw handler:
    it only registers a timer, never samples. Returns True when a refresh was requested."""
    scene = context.scene
    settings = scene.ghost_tool
    if not settings.paths_enabled:
        return False
    stale = get_scene_id(scene) != _cache_scene
    targets = all_targets(context)
    if (not stale and all((*t.key, f) in _cache or (*t.key, f) in _gaps for t in targets for f in t.frames)
            and (not settings.paths_show_handles
                 or all((*t.key, f) in _handles for t in targets for f in _handle_frames(t)))):
        return False
    from .ghost_pipeline import GhostPipeline, _schedule_deferred_update
    GhostPipeline.get(scene).mark_dirty()
    _schedule_deferred_update()
    return True


def _deferred_marker_sync() -> Optional[float]:
    """Timer body: marker generation calls frame_set, which a property update callback must not."""
    try:
        if is_native_transform_active(bpy.context):
            return 0.05
        sync_markers(bpy.context)
    except Exception as exc:
        warn(f"Motion paths markers: {exc}")
    return None


def request_marker_sync() -> None:
    if not bpy.app.timers.is_registered(_deferred_marker_sync):
        bpy.app.timers.register(_deferred_marker_sync, first_interval=0.0)


def _sync_markers_if_shown(context) -> None:
    """Operators that change the pinned list keep Markers on Paths in step with it."""
    if context.scene.ghost_tool.paths_show_markers:
        sync_markers(context)


VERTEX_ADD_LIMIT = 50   # design §8 decision 12


def _next_color(settings) -> tuple[float, float, float]:
    return PALETTE[sum(1 for e in settings.motion_paths if not e.is_folder) % len(PALETTE)]


def remove_rows(context, indexes) -> int:
    """Remove list rows. A removed folder's paths move to the top level first, so removing a
    folder never removes paths. Returns how many rows went."""
    settings = context.scene.ghost_tool
    paths = settings.motion_paths
    doomed = sorted({i for i in indexes if 0 <= i < len(paths)}, reverse=True)
    gone_folders = {paths[i].folder_key for i in doomed if paths[i].is_folder}
    for entry in paths:
        if entry.folder in gone_folders:
            entry.folder = ""
    for i in doomed:   # highest first, so the lower indexes stay valid
        entry = paths[i]
        key = None if entry.is_folder else entry_key(entry)
        paths.remove(i)
        if key is not None and key not in {entry_key(e) for e in paths if not e.is_folder}:
            forget(key)
    if doomed:
        settings.motion_paths_index = min(settings.motion_paths_index, len(paths) - 1)
        _sync_markers_if_shown(context)
        tag_viewport_redraw(context)
    return len(doomed)


APPLY_PROPS = ("color", "thickness", "dot_size", "in_front")


def checked_paths(settings) -> list[int]:
    """Indexes of the paths that path actions (Apply, Reset Range, Move, Add Folder) act on:
    checked paths, and every path of a checked folder."""
    checked_folders = {key for key, f in folder_rows(settings).items() if f.checked}
    return [i for i, e in enumerate(settings.motion_paths)
            if not e.is_folder and (e.checked or e.folder in checked_folders)]


def apply_to_checked(settings, include_range: bool) -> int:
    """Copy the list's active path's look (and its range override when asked) to every other
    checked path. Folders are never written to. Returns how many paths changed."""
    paths = settings.motion_paths
    if not 0 <= settings.motion_paths_index < len(paths):
        return 0
    source = paths[settings.motion_paths_index]
    if source.is_folder:
        return 0
    names = APPLY_PROPS + (RANGE_PROPS if include_range else ())
    count = 0
    for index in checked_paths(settings):
        if index == settings.motion_paths_index:
            continue
        entry = paths[index]
        for name in names:
            setattr(entry, name, getattr(source, name))
        # Colour-before: copy the stored choice, or none, so a following path keeps following.
        if "color_before_value" in source:
            entry.color_before = source.color_before
        elif "color_before_value" in entry:
            del entry["color_before_value"]
        if source.bone_name and entry.bone_name and entry.anchor != source.anchor:
            entry.anchor = source.anchor   # an object origin has no tail; same anchor would re-sample
        count += 1
    return count


class GHOST_OT_paths_add_selected(bpy.types.Operator):
    bl_idname = "ghost_tool.paths_add_selected"
    bl_label = "Add Path for Selected"
    bl_description = ("Pin a motion path for each selected bone (Pose mode), vertex (Edit Mode, "
                      "up to 50 per click) or object")
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if selected_keys(context):
            return True
        cls.poll_message_set("Select bones, objects or (in Edit Mode) vertices first")
        return False

    def execute(self, context):
        settings = context.scene.ghost_tool
        existing = {entry_key(e) for e in settings.motion_paths if not e.is_folder}
        added = vertices = 0
        wanted = [key for key, _obj in selected_keys(context) if key not in existing]
        skipped = 0
        for key in wanted:
            if key in existing:
                continue
            if key[2] >= 0:
                if vertices >= VERTEX_ADD_LIMIT:   # every vertex path re-samples each frame window
                    skipped += 1
                    continue
                vertices += 1
            entry = settings.motion_paths.add()
            entry.object_name, entry.bone_name, entry.vertex_index = key
            entry.color = _next_color(settings)
            entry.color_before = tuple(c * 0.55 for c in entry.color)
            existing.add(key)
            added += 1
        settings["paths_enabled"] = True
        settings.motion_paths_index = len(settings.motion_paths) - 1
        refresh_paths(context)  # draw the new paths now, not on the next frame change
        _sync_markers_if_shown(context)
        tag_viewport_redraw(context)
        if skipped:
            self.report({'WARNING'}, f"Pinned {added} motion path(s); {skipped} more selected vertices skipped "
                                     f"(at most {VERTEX_ADD_LIMIT} per click)")
        else:
            self.report({'INFO'}, f"Pinned {added} motion path(s)")
        return {'FINISHED'}


class GHOST_OT_paths_remove(bpy.types.Operator):
    bl_idname = "ghost_tool.paths_remove"
    bl_label = "Remove Path"
    bl_description = "Unpin this motion path; removing a folder moves its paths to the top level"
    bl_options = {'REGISTER', 'UNDO'}
    index: bpy.props.IntProperty(default=-1)  # type: ignore[assignment]

    def execute(self, context):
        settings = context.scene.ghost_tool
        idx = self.index if self.index >= 0 else settings.motion_paths_index
        if not 0 <= idx < len(settings.motion_paths):
            return {'CANCELLED'}
        remove_rows(context, [idx])
        settings.motion_paths_index = min(idx, len(settings.motion_paths) - 1)
        return {'FINISHED'}


class GHOST_OT_paths_add_folder(bpy.types.Operator):
    bl_idname = "ghost_tool.paths_add_folder"
    bl_label = "Add Folder"
    bl_description = "Add a folder row to group motion paths; checked paths move into it"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.ghost_tool
        paths = settings.motion_paths
        names = {e.object_name for e in paths if e.is_folder}
        name, n = "Folder", 1
        while name in names:
            n += 1
            name = f"Folder {n}"
        keys = {e.folder_key for e in paths if e.is_folder}
        key = uuid.uuid4().hex[:8]
        while key in keys:
            key = uuid.uuid4().hex[:8]
        folder = paths.add()
        folder.is_folder, folder.object_name, folder.folder_key = True, name, key
        moved, emptied = 0, set()
        for index in checked_paths(settings):
            emptied.add(paths[index].folder)
            paths[index].folder, paths[index].checked = key, False
            moved += 1
        for entry in paths:
            if entry.is_folder and entry.folder_key in emptied:
                entry.checked = False   # its paths moved out; left checked it would act on nothing
        settings.motion_paths_index = len(paths) - 1
        tag_viewport_redraw(context)
        self.report({'INFO'}, f"Added {name}" + (f" with {moved} path(s)" if moved else ""))
        return {'FINISHED'}


class GHOST_OT_paths_toggle_folder(bpy.types.Operator):
    bl_idname = "ghost_tool.paths_toggle_folder"
    bl_label = "Open or Close Folder"
    bl_description = "Show or hide this folder's paths in the list"
    bl_options = {'REGISTER', 'UNDO'}
    index: bpy.props.IntProperty(default=-1)  # type: ignore[assignment]

    def execute(self, context):
        paths = context.scene.ghost_tool.motion_paths
        if not 0 <= self.index < len(paths) or not paths[self.index].is_folder:
            return {'CANCELLED'}
        paths[self.index].collapsed = not paths[self.index].collapsed
        return {'FINISHED'}


class GHOST_OT_paths_apply_to_checked(bpy.types.Operator):
    bl_idname = "ghost_tool.paths_apply_to_checked"
    bl_label = "Apply to Checked"
    bl_description = ("Copy the selected path's colours, thickness, dot size, in front and traced point "
                      "to every checked path")
    bl_options = {'REGISTER', 'UNDO'}
    include_range: bpy.props.BoolProperty(
        name="Include Range", description="Also copy the selected path's own frame range", default=False,
    )  # type: ignore[assignment]

    @classmethod
    def poll(cls, context):
        settings = context.scene.ghost_tool
        paths = settings.motion_paths
        if not 0 <= settings.motion_paths_index < len(paths) or paths[settings.motion_paths_index].is_folder:
            cls.poll_message_set("Select a path in the list to copy from")
            return False
        if not any(i != settings.motion_paths_index for i in checked_paths(settings)):
            cls.poll_message_set("Check the paths to copy to")
            return False
        return True

    def execute(self, context):
        count = apply_to_checked(context.scene.ghost_tool, self.include_range)
        _sync_markers_if_shown(context)
        tag_viewport_redraw(context)
        self.report({'INFO'}, f"Applied to {count} path(s)")
        return {'FINISHED'}


class GHOST_OT_paths_checked_action(bpy.types.Operator):
    bl_idname = "ghost_tool.paths_checked_action"
    bl_label = "Checked Paths"
    bl_description = "Show, hide, remove, reset the range of, or move the checked rows"
    bl_options = {'REGISTER', 'UNDO'}
    action: bpy.props.EnumProperty(
        name="Action",
        description="What to do with the checked rows",
        items=[
            ('SHOW', "Show", "Show the checked rows"),
            ('HIDE', "Hide", "Hide the checked rows"),
            ('REMOVE', "Remove", "Remove the checked rows; a removed folder's paths move to the top level"),
            ('RESET_RANGE', "Reset Range", "Checked paths follow the global range again"),
            ('MOVE', "Move to Folder", "Move the checked paths into a folder, or to the top level"),
        ],
        default='SHOW',
    )  # type: ignore[assignment]
    folder: bpy.props.StringProperty(
        name="Folder", description="Key of the folder to move into; empty moves to the top level", default="",
    )  # type: ignore[assignment]

    def execute(self, context):
        settings = context.scene.ghost_tool
        paths = settings.motion_paths
        checked = [i for i, e in enumerate(paths) if e.checked]
        if not checked:
            self.report({'WARNING'}, "No rows are checked")
            return {'CANCELLED'}
        if self.action == 'REMOVE':
            count = remove_rows(context, checked)
            self.report({'INFO'}, f"Removed {count} row(s)")
            return {'FINISHED'}
        if self.action == 'MOVE' and self.folder and self.folder not in folder_rows(settings):
            self.report({'WARNING'}, "That folder no longer exists")
            return {'CANCELLED'}
        if self.action in {'SHOW', 'HIDE'}:   # rows: a checked folder shows or hides as a whole
            for i in checked:
                paths[i].visible = self.action == 'SHOW'
        else:   # paths: a checked folder stands for its paths (folders have no range and do not nest)
            for i in checked_paths(settings):
                if self.action == 'RESET_RANGE':
                    paths[i].use_own_range = False
                else:
                    paths[i].folder = self.folder
        _sync_markers_if_shown(context)
        tag_viewport_redraw(context)
        return {'FINISHED'}


class GHOST_OT_paths_clear(bpy.types.Operator):
    bl_idname = "ghost_tool.paths_clear"
    bl_label = "Clear Paths"
    bl_description = "Unpin every motion path"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.ghost_tool.motion_paths.clear()
        context.scene.ghost_tool.motion_paths_index = -1
        clear_cache()
        _sync_markers_if_shown(context)
        tag_viewport_redraw(context)
        return {'FINISHED'}


class GHOST_OT_paths_toggle_visible(bpy.types.Operator):
    bl_idname = "ghost_tool.paths_toggle_visible"
    bl_label = "Toggle Path"
    bl_description = "Show or hide one motion path, or all of them"
    bl_options = {'REGISTER', 'UNDO'}
    action: bpy.props.EnumProperty(items=[('ONE', "One", ""), ('ALL_ON', "All on", ""), ('ALL_OFF', "All off", "")], default='ONE')  # type: ignore[assignment]
    index: bpy.props.IntProperty(default=-1)  # type: ignore[assignment]

    def execute(self, context):
        paths = context.scene.ghost_tool.motion_paths
        if self.action == 'ONE':
            if not 0 <= self.index < len(paths):
                return {'CANCELLED'}
            paths[self.index].visible = not paths[self.index].visible
        else:
            for entry in paths:
                entry.visible = self.action == 'ALL_ON'
        _sync_markers_if_shown(context)
        tag_viewport_redraw(context)
        return {'FINISHED'}


class GHOST_OT_paths_toggle_front(bpy.types.Operator):
    bl_idname = "ghost_tool.paths_toggle_front"
    bl_label = "Path In Front"
    bl_description = "Draw one motion path, or all of them, in front of the scene or hidden behind geometry"
    bl_options = {'REGISTER', 'UNDO'}
    action: bpy.props.EnumProperty(
        items=[('ONE', "One", "Flip this path"), ('ALL_ON', "All in front", "Every path draws in front"),
               ('ALL_OFF', "All behind", "Every path hides behind geometry")],
        default='ONE',
    )  # type: ignore[assignment]
    index: bpy.props.IntProperty(default=-1)  # type: ignore[assignment]

    def execute(self, context):
        paths = context.scene.ghost_tool.motion_paths
        if self.action == 'ONE':
            if not 0 <= self.index < len(paths):
                return {'CANCELLED'}
            paths[self.index].in_front = not paths[self.index].in_front
        else:
            for entry in paths:
                entry.in_front = self.action == 'ALL_ON'
        tag_viewport_redraw(context)
        return {'FINISHED'}


class GHOST_OT_paths_set_color(bpy.types.Operator):
    bl_idname = "ghost_tool.paths_set_color"
    bl_label = "Path Settings"
    bl_description = "Change the colours, thickness, dot size, traced point and own frame range of this motion path"
    bl_options = {'REGISTER', 'UNDO'}
    index: bpy.props.IntProperty(default=-1)  # type: ignore[assignment]
    color: bpy.props.FloatVectorProperty(
        name="Colour", description="Colour of this path", subtype='COLOR', size=3, min=0.0, max=1.0,
    )  # type: ignore[assignment]
    color_before: bpy.props.FloatVectorProperty(
        name="Colour Before", description="Colour of this path before the playhead (style Split)",
        subtype='COLOR', size=3, min=0.0, max=1.0,
    )  # type: ignore[assignment]
    thickness: bpy.props.IntProperty(
        name="Thickness", description="Line width of this path in pixels", min=1, max=6, default=2,
    )  # type: ignore[assignment]
    dot_size: bpy.props.IntProperty(
        name="Dot Size", description="Size of this path's key dots in pixels", min=1, max=12, default=6,
    )  # type: ignore[assignment]
    anchor: bpy.props.EnumProperty(
        name="Trace",
        description="Which point of the bone the path traces",
        items=[('HEAD', "Head", "Trace the bone head"), ('TAIL', "Tail", "Trace the bone tail")],
        default='HEAD',
    )  # type: ignore[assignment]
    use_own_range: bpy.props.BoolProperty(
        name="Own Range", description="Give this path its own frame range instead of the global one",
    )  # type: ignore[assignment]
    own_range_mode: bpy.props.EnumProperty(
        name="Range",
        description="Which frames this path covers",
        items=[
            ('AROUND_CURSOR', "Around Playhead", "Frames before and after the playhead"),
            ('SCENE', "Scene", "The scene frame range"),
            ('CUSTOM', "Custom", "This path's own start and end frames"),
        ],
        default='AROUND_CURSOR',
    )  # type: ignore[assignment]
    own_before: bpy.props.IntProperty(
        name="Before", description="Frames this path draws before the playhead", min=0, max=500, default=12,
    )  # type: ignore[assignment]
    own_after: bpy.props.IntProperty(
        name="After", description="Frames this path draws after the playhead", min=0, max=500, default=12,
    )  # type: ignore[assignment]
    own_step: bpy.props.IntProperty(
        name="Every", description="Sample every Nth frame along this path", min=1, max=24, default=1,
    )  # type: ignore[assignment]
    own_start: bpy.props.IntProperty(
        name="Start", description="First frame of this path's custom range", default=1,
    )  # type: ignore[assignment]
    own_end: bpy.props.IntProperty(
        name="End", description="Last frame of this path's custom range", default=250,
    )  # type: ignore[assignment]

    def invoke(self, context, event):
        paths = context.scene.ghost_tool.motion_paths
        if not 0 <= self.index < len(paths) or paths[self.index].is_folder:   # -1 would silently pick the last path
            return {'CANCELLED'}
        entry = paths[self.index]
        for name in dialog_props(entry):
            setattr(self, name, getattr(entry, name))
        for name, value in own_range_seed(context.scene.ghost_tool, entry).items():
            setattr(self, name, value)
        return context.window_manager.invoke_props_dialog(self, width=260)

    def draw(self, context):
        paths = context.scene.ghost_tool.motion_paths
        if not 0 <= self.index < len(paths):
            return
        layout = self.layout
        for name in dialog_props(paths[self.index]):
            if name not in RANGE_PROPS:
                layout.prop(self, name, expand=name == "anchor")
        col = layout.column(align=True)
        col.prop(self, "use_own_range")
        if self.use_own_range:   # the dialog's value: the fields appear as soon as it is ticked
            col.prop(self, "own_range_mode", text="")
            fields = own_range_props(self.own_range_mode)
            if fields:
                row = col.row(align=True)
                for name in fields:
                    row.prop(self, name)
            col.prop(self, "own_step")

    def execute(self, context):
        paths = context.scene.ghost_tool.motion_paths
        if not 0 <= self.index < len(paths):
            return {'CANCELLED'}
        entry = paths[self.index]
        # Only what the caller set: the list's Head/Tail button passes the anchor alone.
        for name in dialog_props(entry):
            if not self.properties.is_property_set(name):
                continue
            if name == "anchor" and entry.anchor == self.anchor:
                continue   # rewriting the same anchor would re-sample the whole path
            setattr(entry, name, getattr(self, name))
        tag_viewport_redraw(context)
        return {'FINISHED'}


CLASSES: tuple[type, ...] = (
    GHOST_OT_paths_add_selected,
    GHOST_OT_paths_remove,
    GHOST_OT_paths_add_folder,
    GHOST_OT_paths_toggle_folder,
    GHOST_OT_paths_apply_to_checked,
    GHOST_OT_paths_checked_action,
    GHOST_OT_paths_clear,
    GHOST_OT_paths_toggle_visible,
    GHOST_OT_paths_toggle_front,
    GHOST_OT_paths_set_color,
)


def register() -> None:
    global _draw_handler, _draw_handler_2d
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    _draw_handler = bpy.types.SpaceView3D.draw_handler_add(draw_motion_paths, (), 'WINDOW', 'POST_VIEW')
    _draw_handler_2d = bpy.types.SpaceView3D.draw_handler_add(draw_frame_numbers, (), 'WINDOW', 'POST_PIXEL')
    log("Motion paths module registered.")


def unregister() -> None:
    global _draw_handler, _draw_handler_2d
    if bpy.app.timers.is_registered(_deferred_marker_sync):
        bpy.app.timers.unregister(_deferred_marker_sync)
    _marker_uids.clear()
    if _draw_handler is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handler, 'WINDOW')
        _draw_handler = None
    if _draw_handler_2d is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handler_2d, 'WINDOW')
        _draw_handler_2d = None
    for cls in reversed(CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
    clear_cache()
