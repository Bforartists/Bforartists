"""
utils.py — Shared utility functions used across Ghost Tool modules.

Contains coordinate conversion, color math, bone lookups, Blender
version compatibility helpers, and a unified logging facility.

Every module in Ghost Tool should use ``log()``, ``warn()``, or
``debug()`` from this file instead of bare ``print()`` calls, so
diagnostic output can be filtered from a single location.
"""

from __future__ import annotations

import math
from contextlib import contextmanager
from functools import wraps
from typing import Optional

import bpy
from bpy_extras import view3d_utils
from mathutils import Vector, Matrix


# ---------------------------------------------------------------------------
# Logging — single point of control for all Ghost Tool console output
# ---------------------------------------------------------------------------

# Set to False to suppress verbose debug output in production.
# Set to True during development for diagnostic tracing.
ENABLE_DEBUG_OUTPUT: bool = False

_LOG_PREFIX: str = "[Ghost Tool]"


# ---------------------------------------------------------------------------
# Stable scene identity
# ---------------------------------------------------------------------------

_SCENE_ID_KEY = "ghost_tool_scene_id"

def get_scene_id(scene) -> str:
    """Return a stable unique ID for a scene, creating one if needed.

    Uses runtime identity, independent of scene names and duplicated properties.
    JSON export/import handles persistence; file loading clears transient stores.
    """
    # A persisted custom property is copied by Scene.copy(), causing two
    # scenes to share every transient store. RNA session identity is unique.
    return str(getattr(scene, 'session_uid', scene.as_pointer()))


def log(message: str) -> None:
    """Print an informational message to the Blender console.

    Always shown regardless of debug settings. Use for important
    state changes like registration, generation counts, etc.

    Args:
        message: Human-readable description of what happened.
    """
    print(f"{_LOG_PREFIX} {message}")


def warn(message: str) -> None:
    """Print a warning message to the Blender console.

    Always shown regardless of debug settings. Use when something
    unexpected happens but execution can continue safely.

    Args:
        message: Description of the unexpected condition.
    """
    print(f"{_LOG_PREFIX} WARNING: {message}")


def debug(message: str) -> None:
    """Print a debug-level message to the Blender console.

    Only shown when ``ENABLE_DEBUG_OUTPUT`` is True. Use for
    verbose diagnostic tracing that would be noisy in production.

    Args:
        message: Detailed diagnostic information.
    """
    if ENABLE_DEBUG_OUTPUT:
        print(f"{_LOG_PREFIX} [debug] {message}")


def tag_viewport_redraw(context: bpy.types.Context) -> None:
    """Request a redraw of all 3D Viewport areas.

    This is the standard way to tell Blender to repaint after ghost data
    changes.  Safe to call when ``context.screen`` is None (e.g. during
    background processing) — it simply does nothing.
    """
    screen = getattr(context, 'screen', None)
    if screen is None:
        return
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()


# ---------------------------------------------------------------------------
# Blender Version Compatibility — Slotted Actions (Blender 4.4+ / 5.x)
# ---------------------------------------------------------------------------
#
# Blender 4.4 introduced "Slotted Actions" where action.fcurves was moved
# to a channelbag accessed via the animation slot system.  Blender 5.0
# removed action.fcurves entirely.  Bforartists 5.x inherits this change.
#
# These helpers provide a single entry point that works across versions.

_BLENDER_VERSION: tuple[int, int, int] = bpy.app.version

_USE_SLOTTED_API: bool = _BLENDER_VERSION >= (4, 4, 0)
"""True on Blender 4.4+ / Bforartists 5.x+ where slotted Actions
are the only way to access f-curves. ``action.fcurves`` does not
exist on these builds and must never be accessed directly."""


def get_fcurves_from_action(
    action: bpy.types.Action,
    obj: Optional[bpy.types.Object] = None,
) -> list:
    """Get all f-curves from an Action, handling both legacy and slotted APIs.

    In Blender < 4.4 (and some 4.x builds), action.fcurves exists directly.
    In Blender 4.4+ / 5.x / Bforartists 5.x, f-curves live inside a
    channelbag accessed via the object's animation_data.action_slot.

    Args:
        action: The Blender Action to read f-curves from.
        obj: The object that owns this action (needed for slotted API
             to resolve the correct slot/channelbag).  If None, the
             function attempts legacy access first, then iterates all
             slots.

    Returns:
        list: A list-like collection of FCurve objects.  May be empty
              if no f-curves exist or the action cannot be resolved.
    """
    if action is None:
        return []

    debug(f"get_fcurves_from_action: Blender {bpy.app.version}, "
          f"slotted={_USE_SLOTTED_API}, action='{action.name}', "
          f"obj={f'<{obj.name}>' if obj else 'None'}")

    # --- Slotted Actions API (Blender 4.4+ / 5.x) — try FIRST on new builds ---
    # On Blender 5.x, action.fcurves does NOT exist.  We MUST go through
    # the channelbag system.  Try this path first to avoid any legacy access.
    if _USE_SLOTTED_API:
        # Path A: Use object's animation_data.action_slot to find the channelbag
        if obj is not None and hasattr(obj, 'animation_data') and obj.animation_data:
            anim_data = obj.animation_data
            slot = getattr(anim_data, 'action_slot', None)
            debug(f"Slotted path A: anim_data exists, "
                  f"action_slot={f'<{slot}>' if slot else 'None'}")
            if slot is not None:
                channelbag = _get_channelbag_for_slot(action, slot)
                debug(f"channelbag={channelbag}")
                if channelbag is not None and hasattr(channelbag, 'fcurves'):
                    result = list(channelbag.fcurves)
                    debug(f"Found {len(result)} fcurves via channelbag")
                    return result

        # Path B: Brute-force walk all layers/strips/channelbags
        all_fcurves = _collect_all_fcurves_from_action(action)
        if all_fcurves:
            debug(f"Brute-force walk found {len(all_fcurves)} fcurves")
            return all_fcurves

        # Path C: Last resort — maybe this Blender build still has action.fcurves?
        try:
            fc_collection = action.fcurves
            if fc_collection is not None:
                result = list(fc_collection)
                debug(f"Legacy fallback: {len(result)} fcurves")
                return result
        except (AttributeError, TypeError, RuntimeError):
            debug("Legacy fallback failed (expected on 5.x)")

        warn("No fcurves found via any method for action "
             f"'{action.name}'")
        return []

    # --- Legacy API (Blender < 4.4) ---
    try:
        fc_collection = action.fcurves
        if fc_collection is not None and len(fc_collection) > 0:
            return list(fc_collection)
    except (AttributeError, TypeError, RuntimeError):
        debug("Legacy API access to action.fcurves failed (expected on 5.x)")

    # Legacy build but no action.fcurves — try slotted as fallback
    if obj is not None and hasattr(obj, 'animation_data') and obj.animation_data:
        anim_data = obj.animation_data
        slot = getattr(anim_data, 'action_slot', None)
        if slot is not None:
            channelbag = _get_channelbag_for_slot(action, slot)
            if channelbag is not None and hasattr(channelbag, 'fcurves'):
                return list(channelbag.fcurves)

    all_fcurves = _collect_all_fcurves_from_action(action)
    if all_fcurves:
        return all_fcurves

    return []


def find_fcurve_in_action(
    action: bpy.types.Action,
    data_path: str,
    array_index: int = 0,
    obj: Optional[bpy.types.Object] = None,
) -> Optional[bpy.types.FCurve]:
    """Find a specific f-curve by data_path and array_index.

    Works across both legacy and slotted Action APIs.

    Args:
        action: The Action to search.
        data_path: The RNA data path (e.g. 'pose.bones["Bone"].location').
        array_index: The array index (0 for X, 1 for Y, 2 for Z, etc.).
        obj: The owning object (needed for slotted API resolution).

    Returns:
        FCurve or None: The matching f-curve, or None if not found.
    """
    fcurves = get_fcurves_from_action(action, obj)
    for fc in fcurves:
        if fc.data_path == data_path and fc.array_index == array_index:
            return fc
    return None


def _get_channelbag_for_slot(action, slot):
    """Get the channelbag for a given action slot.

    Tries the bpy_extras.anim_utils helper first, then manual iteration.

    Args:
        action: The Blender Action.
        slot: The animation slot from animation_data.action_slot.

    Returns:
        ActionChannelbag or None.
    """
    # Try the convenience function from bpy_extras
    try:
        from bpy_extras import anim_utils
        if hasattr(anim_utils, 'action_get_channelbag_for_slot'):
            return anim_utils.action_get_channelbag_for_slot(action, slot)
    except (ImportError, AttributeError):
        pass

    # Manual iteration: walk action layers -> strips -> channelbags
    # to find the channelbag whose slot matches ours.
    try:
        if not hasattr(action, 'layers'):
            return None

        for layer in action.layers:
            if not hasattr(layer, 'strips'):
                continue
            for strip in layer.strips:
                if not hasattr(strip, 'channelbags'):
                    continue

                for bag in strip.channelbags:
                    bag_slot = getattr(bag, 'slot', None)
                    bag_slot_handle = getattr(bag, 'slot_handle', None)
                    slot_handle = getattr(slot, 'handle', None)
                    if bag_slot == slot or bag_slot_handle == slot_handle:
                        return bag

                # If the strip has exactly one channelbag, use it
                # as a reasonable fallback when slot matching fails.
                if len(strip.channelbags) == 1:
                    return strip.channelbags[0]

    except (AttributeError, TypeError, RuntimeError) as exc:
        warn(f"Error walking action layers for channelbag: {exc}")

    return None


def _collect_all_fcurves_from_action(action) -> list:
    """Brute-force collect all f-curves from any action structure.

    Walks layers -> strips -> channelbags -> fcurves as a last resort.

    Args:
        action: The Blender Action.

    Returns:
        list: All FCurve objects found.
    """
    all_fcurves: list = []
    try:
        if not hasattr(action, 'layers'):
            return all_fcurves

        for layer in action.layers:
            if not hasattr(layer, 'strips'):
                continue
            for strip in layer.strips:
                if not hasattr(strip, 'channelbags'):
                    continue
                for bag in strip.channelbags:
                    if hasattr(bag, 'fcurves'):
                        all_fcurves.extend(bag.fcurves)

    except (AttributeError, TypeError, RuntimeError) as exc:
        warn(f"Error collecting fcurves from action: {exc}")

    return all_fcurves


# ---------------------------------------------------------------------------
# Coordinate Conversion
# ---------------------------------------------------------------------------

def world_to_screen(
    context: bpy.types.Context,
    world_pos: Vector,
) -> tuple[float, float]:
    """Project a 3D world-space point to 2D screen coordinates.

    Args:
        context: The current Blender context (must have a 3D viewport region).
        world_pos: The point in world space.

    Returns:
        tuple[float, float]: Screen coordinates (x, y).  Returns (-1, -1)
            if the point is behind the camera or the region is unavailable.
    """
    region = context.region
    region_3d = context.region_data
    if not region or not region_3d:
        return (-1.0, -1.0)

    result = view3d_utils.location_3d_to_region_2d(region, region_3d, world_pos)
    if result is None:
        return (-1.0, -1.0)
    return (result.x, result.y)


def screen_to_world_ray(
    context: bpy.types.Context,
    mouse_pos: tuple[float, float],
) -> tuple[Vector, Vector]:
    """Convert a 2D screen position to a 3D world-space ray.

    Args:
        context: The current Blender context.
        mouse_pos: Screen coordinates (x, y) within the 3D viewport region.

    Returns:
        tuple[Vector, Vector]: (ray_origin, ray_direction).  Both are zero
            vectors if the region is unavailable.
    """
    region = context.region
    region_3d = context.region_data
    if not region or not region_3d:
        return (Vector((0, 0, 0)), Vector((0, 0, -1)))

    origin = view3d_utils.region_2d_to_origin_3d(region, region_3d, mouse_pos)
    direction = view3d_utils.region_2d_to_vector_3d(region, region_3d, mouse_pos)

    return (origin, direction)


# Threshold for ray-plane parallelism (dot product below this means parallel)
RAY_PARALLEL_THRESHOLD = 1e-8

def ray_plane_intersect(
    origin: Vector,
    direction: Vector,
    plane_point: Vector,
    plane_normal: Vector,
) -> Optional[Vector]:
    """Compute the intersection of a ray with an infinite plane.

    Args:
        origin: Starting point of the ray.
        direction: Direction of the ray (does not need to be normalized).
        plane_point: Any point lying on the plane.
        plane_normal: Normal vector of the plane (does not need to be normalized).

    Returns:
        Vector or None: The intersection point in world space, or None if
            the ray is parallel to the plane or points away from it.
    """
    denominator = plane_normal.dot(direction)
    if abs(denominator) < RAY_PARALLEL_THRESHOLD:
        # Ray is parallel to the plane — no intersection.
        return None

    distance_along_ray = plane_normal.dot(plane_point - origin) / denominator
    if distance_along_ray < 0:
        # Intersection is behind the ray origin.
        return None

    return origin + direction * distance_along_ray


# ---------------------------------------------------------------------------
# Bone Utilities
# ---------------------------------------------------------------------------

def bone_world_matrix(
    armature_object: bpy.types.Object,
    pose_bone: bpy.types.PoseBone,
) -> Matrix:
    """Compute the world-space transformation matrix of a pose bone.

    Args:
        armature_object: The armature object containing the bone.
        pose_bone: The pose bone to compute the matrix for.

    Returns:
        Matrix: 4x4 world-space transformation matrix of the bone.
    """
    return armature_object.matrix_world @ pose_bone.matrix


def get_pose_bone(
    armature_object: bpy.types.Object,
    bone_name: str,
) -> Optional[bpy.types.PoseBone]:
    """Safely retrieve a pose bone by name.

    Args:
        armature_object: The armature object to search.
        bone_name: The name of the bone to find.

    Returns:
        PoseBone or None: The pose bone, or None if not found or
            the object is not an armature.
    """
    if not armature_object or armature_object.type != 'ARMATURE':
        return None
    return armature_object.pose.bones.get(bone_name)


def get_selected_bone_names(context: bpy.types.Context) -> list[str]:
    """Return the names of all selected pose bones in the active armature.

    Args:
        context: The current Blender context.

    Returns:
        list[str]: Names of selected pose bones.  Empty list if no
            armature is active or no bones are selected.
    """
    obj = context.active_object
    if not obj or obj.type != 'ARMATURE':
        return []

    if context.selected_pose_bones:
        return [b.name for b in context.selected_pose_bones]

    # Fallback: check bone selection state directly
    return [b.name for b in obj.pose.bones if getattr(b, "select", getattr(b.bone, "select", False))]


# ---------------------------------------------------------------------------
# Color Utilities
# ---------------------------------------------------------------------------

def lerp_color(
    color_a: tuple[float, float, float, float],
    color_b: tuple[float, float, float, float],
    t: float,
) -> tuple[float, float, float, float]:
    """Linearly interpolate between two RGBA colors.

    Args:
        color_a: Start color (t=0).
        color_b: End color (t=1).
        t: Interpolation factor, clamped to [0, 1].

    Returns:
        tuple[float, float, float, float]: Interpolated RGBA color.
    """
    t = clamp(t, 0.0, 1.0)
    return (
        color_a[0] + (color_b[0] - color_a[0]) * t,
        color_a[1] + (color_b[1] - color_a[1]) * t,
        color_a[2] + (color_b[2] - color_a[2]) * t,
        color_a[3] + (color_b[3] - color_a[3]) * t,
    )


def generate_color_palette(n: int) -> list[tuple[float, float, float, float]]:
    """Generate n visually distinct RGBA colors using HSV spacing.

    Colors are evenly distributed around the HSV hue wheel with
    consistent saturation and value for good visibility in the viewport.

    Args:
        n: Number of distinct colors to generate.  Must be >= 1.

    Returns:
        list[tuple]: List of n RGBA color tuples with alpha = 0.85.
    """
    if n < 1:
        return []

    colors = []
    for i in range(n):
        hue = i / n
        # Convert HSV to RGB
        r, g, b = _hsv_to_rgb(hue, 0.75, 0.9)
        colors.append((r, g, b, 0.85))

    return colors


def _hsv_to_rgb(h: float, s: float, v: float) -> tuple[float, float, float]:
    """Convert HSV color to RGB.

    Args:
        h: Hue (0.0 to 1.0).
        s: Saturation (0.0 to 1.0).
        v: Value/brightness (0.0 to 1.0).

    Returns:
        tuple[float, float, float]: RGB values in [0, 1] range.
    """
    if s == 0.0:
        return (v, v, v)

    hue_sector = h * 6.0
    hue_sector = hue_sector % 6.0

    sector_index = int(hue_sector)
    fractional = hue_sector - sector_index

    # Pre-computed terms for the standard HSV-to-RGB conversion.
    chroma_min = v * (1.0 - s)
    chroma_descending = v * (1.0 - s * fractional)
    chroma_ascending = v * (1.0 - s * (1.0 - fractional))

    # Each hue sector maps to a different RGB channel arrangement.
    if sector_index == 0:
        return (v, chroma_ascending, chroma_min)
    elif sector_index == 1:
        return (chroma_descending, v, chroma_min)
    elif sector_index == 2:
        return (chroma_min, v, chroma_ascending)
    elif sector_index == 3:
        return (chroma_min, chroma_descending, v)
    elif sector_index == 4:
        return (chroma_ascending, chroma_min, v)
    else:
        return (v, chroma_min, chroma_descending)


# ---------------------------------------------------------------------------
# Math Utilities
# ---------------------------------------------------------------------------

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value to a minimum and maximum range.

    Args:
        value: The value to clamp.
        min_val: The minimum allowed value.
        max_val: The maximum allowed value.

    Returns:
        float: The clamped value.
    """
    return max(min_val, min(value, max_val))


def distance_point_to_line_segment(
    point: Vector,
    line_start: Vector,
    line_end: Vector,
) -> float:
    """Compute the shortest distance from a point to a line segment.

    Useful for determining if a mouse click is near a motion arc.

    Args:
        point: The point to measure from.
        line_start: Start of the line segment.
        line_end: End of the line segment.

    Returns:
        float: The shortest distance.
    """
    line_vec = line_end - line_start
    line_len_sq = line_vec.length_squared

    if line_len_sq < 1e-10:
        return (point - line_start).length

    # Parametric position of closest point on the line
    t = clamp(
        (point - line_start).dot(line_vec) / line_len_sq,
        0.0,
        1.0,
    )

    closest = line_start + line_vec * t
    return (point - closest).length


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between two values.

    Args:
        a: Start value (t=0).
        b: End value (t=1).
        t: Interpolation factor.

    Returns:
        float: Interpolated value.
    """
    return a + (b - a) * t


# ---------------------------------------------------------------------------
# Test notes
# ---------------------------------------------------------------------------
#
# Test 1: Color palette generates distinct colors
# >>> colors = generate_color_palette(5)
# >>> assert len(colors) == 5
# >>> assert all(len(c) == 4 for c in colors)
# >>> # Visual check: colors should be red, yellow, green, cyan, blue-ish
#
# Test 2: Clamp
# >>> assert clamp(5, 0, 10) == 5
# >>> assert clamp(-1, 0, 10) == 0
# >>> assert clamp(15, 0, 10) == 10
#
# Test 3: lerp_color
# >>> c = lerp_color((0,0,0,1), (1,1,1,1), 0.5)
# >>> assert abs(c[0] - 0.5) < 0.001
#
# Test 4: ray_plane_intersect
# >>> hit = ray_plane_intersect(
# ...     Vector((0, 0, 5)), Vector((0, 0, -1)),
# ...     Vector((0, 0, 0)), Vector((0, 0, 1))
# ... )
# >>> assert hit is not None
# >>> assert abs(hit.z) < 0.001

# Internal sampling must neither move the user's playhead permanently nor
# enqueue another live bake through our own frame/depsgraph handlers.
_SAMPLING_DEPTH = 0


def is_sampling() -> bool:
    return _SAMPLING_DEPTH > 0


def is_native_transform_active(context) -> bool:
    """Hold snapshots throughout native modal operations, including gizmos and scrubs.

    A gizmo or macro can own the modal handler instead of TRANSFORM_OT_*.
    Our own gestures use SessionState.drag_active and controlled sampling;
    native gestures must finish before any frame stepping is safe.
    """
    manager = getattr(context, 'window_manager', None)
    for window in getattr(manager, 'windows', ()):
        for operator in getattr(window, 'modal_operators', ()):
            # BFA - Anim Assist's persistent timeline pointer only routes UI events;
            # its active slider/edit operators have separate modal handlers.
            # Exempt only the audited observer, keeping unknown modals guarded.
            if operator.bl_idname == 'ANIMASSIST_OT_timeline_pointer':
                continue
            if not operator.bl_idname.startswith((
                    'ghost_tool.', 'GHOST_TOOL_OT_', 'GHOSTTOOL_OT_')):
                return True
    return False


_POSE_PROPERTIES = (
    'location', 'rotation_mode', 'rotation_euler', 'rotation_quaternion',
    'rotation_axis_angle', 'scale',
)
_DELTA_PROPERTIES = (
    'delta_location', 'delta_rotation_euler', 'delta_rotation_quaternion', 'delta_scale',
)


def _capture_authoring_pose(scene):
    """Save original RNA inputs, never evaluated constraint/driver matrices.

    frame_set re-evaluates keyed channels even when the playhead returns to
    the same frame. Keep unkeyed edits on every rig, including deselected
    controls and shape keys, so the next key insertion gets the user's pose.
    """
    state = []
    for obj in scene.objects:
        if obj.get('ghost_tool_mesh_ghost'):
            continue
        holders = [(obj, _POSE_PROPERTIES + _DELTA_PROPERTIES)]
        if obj.pose:
            holders.extend((bone, _POSE_PROPERTIES) for bone in obj.pose.bones)
        for holder, properties in holders:
            for name in properties:
                value = getattr(holder, name)
                state.append((holder, name, False,
                              value if isinstance(value, str) else tuple(value)))
            for name, value in holder.items():
                if isinstance(value, (bool, int, float)):
                    state.append((holder, name, True, value))
        keys = getattr(obj.data, 'shape_keys', None)
        if keys:
            state.extend((key, 'value', False, key.value) for key in keys.key_blocks)
    return state


def _restore_authoring_pose(state, scene):
    changed = False
    for holder, name, custom, value in state:
        try:
            current = holder[name] if custom else getattr(holder, name)
            if isinstance(value, tuple):
                current = tuple(current)
            if current == value:
                continue
            if custom:
                holder[name] = value
            else:
                setattr(holder, name, value)
            changed = True
        except ReferenceError:
            # A callback may remove an object while frames are sampled.
            continue
    if changed:
        for layer in scene.view_layers:
            layer.update()


@contextmanager
def scene_sampling(scene, *, preserve_pose=True):
    global _SAMPLING_DEPTH
    from . import ghost_data
    if ghost_data._IN_DRAW_HANDLER:
        raise RuntimeError("Scene sampling is forbidden inside a draw handler")
    if is_native_transform_active(bpy.context):
        raise RuntimeError("Scene sampling must wait until the native gesture finishes")
    frame, subframe = scene.frame_current, scene.frame_subframe
    pose = _capture_authoring_pose(scene) if preserve_pose else []
    _SAMPLING_DEPTH += 1
    try:
        yield
    finally:
        try:
            try:
                if (scene.frame_current, scene.frame_subframe) != (frame, subframe):
                    scene.frame_set(frame, subframe=subframe)
            finally:
                _restore_authoring_pose(pose, scene)
        finally:
            _SAMPLING_DEPTH -= 1


def sampling_operation(function):
    """Protect an entire point or mesh sampling pass, including error paths."""
    @wraps(function)
    def wrapped(*args, **kwargs):
        context = kwargs.get('context')
        if context is None:
            context = args[0] if args and isinstance(args[0], bpy.types.Context) else bpy.context
        with scene_sampling(context.scene):
            return function(*args, **kwargs)
    return wrapped


def report_failure(operator, what: str, fix: str, exc=None, *, detail: str | None = None, level: str = "ERROR"):  # type: ignore[no-untyped-def]
    """Report a failure the animator can act on; the exception goes to the log, not the UI."""
    if exc is not None:
        log(f"{what}: {exc!r}")
    msg = f"{what} ({detail}). {fix}" if detail else f"{what}. {fix}"
    operator.report({level}, msg)
    return {"CANCELLED"}
