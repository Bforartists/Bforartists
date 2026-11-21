"""Atlas UV methods for the BoneCraft CATS Material Combiner.

This module reimplements a small atlas-focused UV method layer for BoneCraft. It
is inspired by UVToolkit-style workflows, but it does not vendor UVToolkit source
or register UVToolkit operator names.
"""

import math
import random

import bpy

SOURCE_PRESERVE = "SOURCE_PRESERVE"
SMART_PACK = "BEST_FIT"
GRID_PACK = "GRID"
RANDOMIZED_SMART = "RANDOMIZED_SMART"
ORIENTED_SMART = "ORIENTED_SMART"
FIT_BOUNDS = "FIT_BOUNDS"
ADVANCED_VARIATION = "ADVANCED_VARIATION"
BFA_RANDOM_ORIENTED = ADVANCED_VARIATION
_LEGACY_BFA_RANDOM_ORIENTED = "BFA_RANDOM_ORIENTED"

_OPEN_METHOD_ITEMS = (
    (
        SOURCE_PRESERVE,
        "Preserve Source UVs",
        "Scale original UVs into square atlas tiles without re-unwrapping",
    ),
    (SMART_PACK, "Smart Pack", "Smart UV Project plus Blender island packing"),
    (GRID_PACK, "Grid Pack", "Predictable no-rotation packing for easier atlas review"),
    (RANDOMIZED_SMART, "Seeded Variation", "Deterministic UV island rotation before final packing"),
    (ORIENTED_SMART, "Oriented Pack", "Normalize tall islands before final packing"),
    (FIT_BOUNDS, "Fit 0-1 Bounds", "Smart pack, then normalize the atlas into the 0-1 UV square"),
    (
        ADVANCED_VARIATION,
        "Advanced Variation",
        "Seeded rotation plus orientation normalization for fuller atlas variation",
    ),
)

_METHOD_LABELS = {
    item[0]: item[1]
    for item in _OPEN_METHOD_ITEMS
}

_LEGACY_METHOD_ALIASES = {
    _LEGACY_BFA_RANDOM_ORIENTED: ADVANCED_VARIATION,
}


def atlas_uv_method_items(include_advanced=False):
    """Return Blender EnumProperty items for atlas UV methods."""
    return _OPEN_METHOD_ITEMS


def get_uv_method_label(method):
    """Return a user-facing label for a method id."""
    return _METHOD_LABELS.get(method, _METHOD_LABELS[SMART_PACK])


def method_uses_seed(method):
    """Return True when a method consumes the deterministic random seed."""
    return _LEGACY_METHOD_ALIASES.get(method, method) in {RANDOMIZED_SMART, ADVANCED_VARIATION}


def summarize_atlas_uv_result(result):
    """Return a compact summary line for reports and custom properties."""
    if not result:
        return "UV method: not recorded"
    label = result.get("label") or get_uv_method_label(result.get("method"))
    island_count = result.get("island_count", 0)
    changed = "changed" if result.get("changed") else "unchanged"
    summary = f"{label}: {changed}, islands={island_count}"
    warnings = result.get("warnings") or []
    if warnings:
        summary += "; warnings=" + " | ".join(warnings)
    return summary


def _result(method, changed=False, island_count=0, warnings=None, fallback=False):
    return {
        "method": method,
        "label": get_uv_method_label(method),
        "changed": bool(changed),
        "island_count": int(island_count or 0),
        "warnings": list(warnings or []),
        "fallback": bool(fallback),
    }


def _run_operator_attempts(context, run_operator, op_call, stage, attempts):
    last_error = None
    for kwargs in attempts:
        try:
            return run_operator(context, op_call, stage, **kwargs)
        except RuntimeError as exc:
            last_error = exc
    if last_error is not None:
        raise last_error
    return run_operator(context, op_call, stage)


def _select_all_uv_faces(context, run_operator):
    run_operator(context, bpy.ops.mesh.select_all, "Select atlas UV faces", action="SELECT")


def _smart_project(context, run_operator, margin, angle_limit=66.0):
    run_operator(
        context,
        bpy.ops.uv.smart_project,
        "Smart UV Project atlas",
        angle_limit=angle_limit,
        island_margin=margin,
    )


def _pack_islands(context, run_operator, margin, rotate=True):
    return _run_operator_attempts(
        context,
        run_operator,
        bpy.ops.uv.pack_islands,
        "Pack atlas UV islands",
        (
            {"margin": margin, "rotate": rotate},
            {"margin": margin},
        ),
    )


def _enter_edit_mode(context, obj, run_operator, stage):
    context.view_layer.objects.active = obj
    obj.select_set(True)
    run_operator(context, bpy.ops.object.mode_set, stage, mode="EDIT")


def _leave_edit_mode(context, run_operator):
    run_operator(context, bpy.ops.object.mode_set, "Leave atlas UV edit mode", mode="OBJECT")


def _active_uv_layer(obj):
    mesh = getattr(obj, "data", None)
    if mesh is None or not mesh.uv_layers:
        return None
    return mesh.uv_layers.active or mesh.uv_layers[0]


def _activate_uv_layer(mesh, uv_name, render=False):
    if mesh is None or uv_name not in mesh.uv_layers:
        return False
    for index, uv in enumerate(mesh.uv_layers):
        is_target = uv.name == uv_name
        if render:
            uv.active_render = is_target
        if is_target:
            try:
                mesh.uv_layers.active_index = index
            except Exception:
                uv.active = True
    return True


def _normalized_tile_coordinate(value):
    if -0.000001 <= value <= 1.000001:
        return max(0.0, min(float(value), 1.0)), False
    return float(value) % 1.0, True


def _copy_source_uvs_to_atlas_tiles(
    obj,
    padding,
    source_uv_name="UVMap_pre_atlas",
    atlas_uv_name="atlas_uv",
):
    """Copy source UV shapes into square atlas tiles without geometry re-unwrap."""
    mesh = getattr(obj, "data", None)
    if mesh is None or not mesh.uv_layers:
        return None

    source_uv = mesh.uv_layers.get(source_uv_name)
    atlas_uv = mesh.uv_layers.get(atlas_uv_name)
    if source_uv is None or atlas_uv is None:
        return None

    material_indices = sorted(
        {
            poly.material_index
            for poly in mesh.polygons
            if poly.loop_indices
        }
    )
    if not material_indices:
        return None

    grid_size = max(1, math.ceil(math.sqrt(len(material_indices))))
    tile_size = 1.0 / grid_size
    pad = max(0.0, min(float(padding), tile_size * 0.2))
    inner_size = max(0.000001, tile_size - (pad * 2.0))
    tile_for_material = {
        material_index: (slot % grid_size, slot // grid_size)
        for slot, material_index in enumerate(material_indices)
    }

    wrapped = False
    for poly in mesh.polygons:
        tile = tile_for_material.get(poly.material_index)
        if tile is None:
            continue
        col, row = tile
        x_offset = (col * tile_size) + pad
        y_offset = (row * tile_size) + pad
        for loop_index in poly.loop_indices:
            source = source_uv.data[loop_index].uv
            u, wrapped_u = _normalized_tile_coordinate(source.x)
            v, wrapped_v = _normalized_tile_coordinate(source.y)
            target = atlas_uv.data[loop_index].uv
            target.x = x_offset + (u * inner_size)
            target.y = y_offset + (v * inner_size)
            wrapped = wrapped or wrapped_u or wrapped_v

    _activate_uv_layer(mesh, atlas_uv_name, render=True)
    mesh.update()
    return {
        "material_count": len(material_indices),
        "grid_size": grid_size,
        "wrapped": wrapped,
    }


def _face_islands(mesh):
    """Return topology-connected face islands for stable UV post-processing."""
    if not mesh.polygons:
        return []

    edge_to_faces = {}
    for poly in mesh.polygons:
        for edge_key in poly.edge_keys:
            edge_to_faces.setdefault(tuple(sorted(edge_key)), []).append(poly.index)

    neighbors = {poly.index: set() for poly in mesh.polygons}
    for face_indices in edge_to_faces.values():
        if len(face_indices) < 2:
            continue
        for face_index in face_indices:
            neighbors[face_index].update(i for i in face_indices if i != face_index)

    islands = []
    visited = set()
    for poly in mesh.polygons:
        if poly.index in visited:
            continue
        stack = [poly.index]
        visited.add(poly.index)
        island = []
        while stack:
            current = stack.pop()
            island.append(current)
            for neighbor in neighbors[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    stack.append(neighbor)
        islands.append(island)
    return islands


def _loop_indices_for_faces(mesh, face_indices):
    loop_indices = []
    for face_index in face_indices:
        poly = mesh.polygons[face_index]
        loop_indices.extend(poly.loop_indices)
    return loop_indices


def _bounds_for_loops(uv_layer, loop_indices):
    if not loop_indices:
        return None
    xs = [uv_layer.data[i].uv.x for i in loop_indices]
    ys = [uv_layer.data[i].uv.y for i in loop_indices]
    return min(xs), min(ys), max(xs), max(ys)


def _rotate_loops(uv_layer, loop_indices, radians):
    bounds = _bounds_for_loops(uv_layer, loop_indices)
    if bounds is None:
        return False
    min_x, min_y, max_x, max_y = bounds
    cx = (min_x + max_x) * 0.5
    cy = (min_y + max_y) * 0.5
    cos_v = math.cos(radians)
    sin_v = math.sin(radians)
    for loop_index in loop_indices:
        uv = uv_layer.data[loop_index].uv
        x = uv.x - cx
        y = uv.y - cy
        uv.x = cx + (x * cos_v - y * sin_v)
        uv.y = cy + (x * sin_v + y * cos_v)
    return True


def _seeded_rotate_islands(obj, seed, rotation_step):
    uv_layer = _active_uv_layer(obj)
    if uv_layer is None:
        return 0
    mesh = obj.data
    islands = _face_islands(mesh)
    if not islands:
        return 0

    try:
        step = max(1, int(rotation_step))
    except (TypeError, ValueError):
        step = 90
    choices = list(range(0, 360, step)) or [0, 90, 180, 270]
    rng = random.Random(int(seed))

    changed = 0
    for island in islands:
        angle = rng.choice(choices)
        if angle and _rotate_loops(uv_layer, _loop_indices_for_faces(mesh, island), math.radians(angle)):
            changed += 1
    mesh.update()
    return changed


def _orient_tall_islands(obj):
    uv_layer = _active_uv_layer(obj)
    if uv_layer is None:
        return 0
    mesh = obj.data
    changed = 0
    for island in _face_islands(mesh):
        loop_indices = _loop_indices_for_faces(mesh, island)
        bounds = _bounds_for_loops(uv_layer, loop_indices)
        if bounds is None:
            continue
        min_x, min_y, max_x, max_y = bounds
        width = max_x - min_x
        height = max_y - min_y
        if height > width * 1.15 and _rotate_loops(uv_layer, loop_indices, math.radians(90)):
            changed += 1
    mesh.update()
    return changed


def _fit_uvs_to_bounds(obj, padding):
    uv_layer = _active_uv_layer(obj)
    if uv_layer is None:
        return False

    mesh = obj.data
    loop_indices = [loop.index for loop in mesh.loops]
    bounds = _bounds_for_loops(uv_layer, loop_indices)
    if bounds is None:
        return False

    min_x, min_y, max_x, max_y = bounds
    width = max_x - min_x
    height = max_y - min_y
    if width <= 0.000001 or height <= 0.000001:
        return False

    pad = max(0.0, min(float(padding), 0.25))
    usable = max(0.001, 1.0 - (2.0 * pad))
    scale = min(usable / width, usable / height)
    x_offset = pad + (usable - width * scale) * 0.5
    y_offset = pad + (usable - height * scale) * 0.5

    for loop_index in loop_indices:
        uv = uv_layer.data[loop_index].uv
        uv.x = ((uv.x - min_x) * scale) + x_offset
        uv.y = ((uv.y - min_y) * scale) + y_offset
    mesh.update()
    return True


def apply_atlas_uv_method(context, obj, settings, run_operator):
    """Apply the selected atlas UV method to a joined atlas work mesh.

    `run_operator` must have the signature used by material_atlas:
    `(context, op_call, stage, **kwargs)`.
    """
    method = getattr(settings, "pack_method", SMART_PACK) or SMART_PACK
    method = _LEGACY_METHOD_ALIASES.get(method, method)
    valid_methods = {item[0] for item in atlas_uv_method_items(include_advanced=True)}
    warnings = []
    if method not in valid_methods:
        warnings.append(f"Unknown UV method {method}; used Smart Pack")
        method = SMART_PACK

    margin = float(getattr(settings, "uv_margin", 0.02))
    seed = int(getattr(settings, "uv_random_seed", 1337))
    rotation_step = getattr(settings, "uv_rotation_step", 90)
    island_count = len(_face_islands(obj.data))

    context.view_layer.objects.active = obj
    obj.select_set(True)
    _activate_uv_layer(obj.data, "atlas_uv", render=True)

    if method == SOURCE_PRESERVE:
        preserved = _copy_source_uvs_to_atlas_tiles(obj, margin)
        if preserved:
            if preserved["wrapped"]:
                warnings.append("Source UVs outside 0-1 were wrapped into atlas tiles")
            warnings.append(
                f"Preserved source UV shapes in {preserved['grid_size']}x{preserved['grid_size']} material tiles"
            )
            return _result(
                method,
                changed=True,
                island_count=preserved["material_count"],
                warnings=warnings,
            )
        warnings.append("Source UV maps missing; used Smart Pack")
        method = SMART_PACK

    # Base unwrap/pack. Every method starts from a clean atlas UV projection.
    _enter_edit_mode(context, obj, run_operator, "Enter atlas UV edit mode")
    try:
        _select_all_uv_faces(context, run_operator)
        if method == ORIENTED_SMART:
            _smart_project(context, run_operator, margin, angle_limit=75.0)
        else:
            _smart_project(context, run_operator, margin, angle_limit=66.0)
        _pack_islands(context, run_operator, margin, rotate=(method != GRID_PACK))
    finally:
        _leave_edit_mode(context, run_operator)

    changed = True

    if method in {RANDOMIZED_SMART, ADVANCED_VARIATION}:
        rotated = _seeded_rotate_islands(obj, seed, rotation_step)
        if rotated == 0:
            warnings.append("No UV islands were rotated")

    if method in {ORIENTED_SMART, ADVANCED_VARIATION}:
        oriented = _orient_tall_islands(obj)
        if oriented == 0:
            warnings.append("No tall UV islands needed orientation")

    if method in {RANDOMIZED_SMART, ORIENTED_SMART, ADVANCED_VARIATION}:
        _enter_edit_mode(context, obj, run_operator, "Re-enter atlas UV edit mode")
        try:
            _select_all_uv_faces(context, run_operator)
            _pack_islands(context, run_operator, margin, rotate=(method != GRID_PACK))
        finally:
            _leave_edit_mode(context, run_operator)

    if method in {GRID_PACK, RANDOMIZED_SMART, ORIENTED_SMART, FIT_BOUNDS, ADVANCED_VARIATION}:
        if not _fit_uvs_to_bounds(obj, margin):
            warnings.append("Could not normalize UVs into 0-1 bounds")

    return _result(method, changed=changed, island_count=island_count, warnings=warnings)
