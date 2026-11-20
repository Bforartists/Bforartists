"""BoneCraft VRChat — Viseme/Expression Utility Functions.

Shared helpers for shape key lookup used by both viseme mapping
and face tracking modules.

Category: VRChat Visemes.
"""

import bpy
from typing import Optional, Set


def collect_shape_key_names(mesh_objects: list) -> Set[str]:
    """Collect all shape key names from a list of mesh objects.

    Args:
        mesh_objects: List of Blender mesh objects to scan.

    Returns:
        Set of shape key name strings.
    """
    names = set()
    for mesh in mesh_objects:
        if mesh.data.shape_keys:
            for key in mesh.data.shape_keys.key_blocks:
                names.add(key.name)
    return names


def find_shape_key(target_name: str, all_shape_keys: Set[str],
                   alternates: list = None) -> Optional[str]:
    """Find a shape key by exact match, then case-insensitive, then alternates.

    Args:
        target_name: Primary name to search for.
        all_shape_keys: Set of all available shape key names.
        alternates: Optional list of alternate names to try.

    Returns:
        Matched shape key name, or None if not found.
    """
    # 1. Exact match
    if target_name in all_shape_keys:
        return target_name

    # 2. Case-insensitive match
    target_lower = target_name.lower()
    for key in all_shape_keys:
        if key.lower() == target_lower:
            return key

    # 3. Alternate names (exact then case-insensitive)
    if alternates:
        for alt in alternates:
            if alt in all_shape_keys:
                return alt
            alt_lower = alt.lower()
            for key in all_shape_keys:
                if key.lower() == alt_lower:
                    return key

    return None


def get_mesh_objects(obj: bpy.types.Object) -> list:
    """Get all mesh objects from an armature or its children.

    Args:
        obj: An armature or mesh object.

    Returns:
        List of mesh objects.
    """
    meshes = []
    if obj.type == "ARMATURE":
        for child in obj.children:
            if child.type == "MESH":
                meshes.append(child)
    elif obj.type == "MESH":
        meshes.append(obj)
    return meshes
