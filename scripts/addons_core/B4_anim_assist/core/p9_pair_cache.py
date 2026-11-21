"""Pair detection result caching for mirroring workflows.

Caches bone pair detection results to avoid recomputing every frame.
Keyed by armature name; values are bone_name -> opposite_name mappings.
"""

from __future__ import annotations

from .logging import get_logger
from . import p9_pair_detect as det

__all__ = [
    "get_pair_map",
    "build_pair_map",
    "get_opposite",
    "invalidate",
    "clear_cache",
    "get_generation",
    "get_unpaired",
    "get_stats",
]

_log = get_logger(__name__)

# Module-level cache and generation counter
_cache: dict[str, dict[str, str | None]] = {}
_cache_generation: int = 0


def get_pair_map(armature_name: str) -> dict[str, str | None] | None:
    """Return cached pair map for armature, or None if not cached.

    Parameters
    ----------
    armature_name : str
        Name of the armature

    Returns
    -------
    dict[str, str | None] or None
        Dictionary mapping bone names to their opposite names (or None if unpaired),
        or None if no cache entry exists for this armature.
    """
    return _cache.get(armature_name)


def build_pair_map(
    armature_name: str,
    bone_names: list[str] | tuple[str, ...],
    *,
    overrides: dict[str, str] | None = None,
    exceptions: dict[str, str] | None = None,
    custom_patterns: tuple[det.MirrorPattern, ...] | None = None,
) -> dict[str, str | None]:
    """Build and cache pair map for an armature.

    Calls det.find_all_pairs() and stores None for unpaired bones.

    Parameters
    ----------
    armature_name : str
        Name of the armature
    bone_names : list[str] | tuple[str, ...]
        List/tuple of bone names to process
    overrides : dict[str, str], optional
        Overrides dict (passed to det.find_all_pairs)
    exceptions : dict[str, str], optional
        Exceptions dict (passed to det.find_all_pairs)
    custom_patterns : tuple[det.MirrorPattern, ...], optional
        Custom patterns tuple (passed to det.find_all_pairs)

    Returns
    -------
    dict[str, str | None]
        Dictionary mapping bone names to their opposite names (or None if unpaired).
    """
    bone_list = list(bone_names)

    # Call the pair detection function
    pairs = det.find_all_pairs(
        bone_list,
        overrides=overrides,
        exceptions=exceptions,
        custom_patterns=custom_patterns,
    )

    # Build complete map: include bones not in pairs with None value
    pair_map: dict[str, str | None] = {}
    for bone_name in bone_list:
        pair_map[bone_name] = pairs.get(bone_name)

    # Cache the result
    _cache[armature_name] = pair_map
    _log.debug(f"Cached pair map for armature '{armature_name}': {len(pair_map)} bones")

    return pair_map


def get_opposite(armature_name: str, bone_name: str) -> str | None:
    """Get the opposite bone for a given bone from cache.

    Parameters
    ----------
    armature_name : str
        Name of the armature
    bone_name : str
        Name of the bone

    Returns
    -------
    str or None
        Name of opposite bone, None if unpaired, or None if cache miss.
        Caller should build cache if None is returned and no cache exists.
    """
    pair_map = _cache.get(armature_name)
    if pair_map is None:
        return None

    return pair_map.get(bone_name)


def invalidate(armature_name: str | None = None) -> None:
    """Invalidate cache entries.

    Parameters
    ----------
    armature_name : str, optional
        If provided, clear only this armature's cache.
        If None, clear entire cache.
    """
    global _cache_generation

    if armature_name is None:
        _cache.clear()
        _log.debug("Cache cleared (all armatures)")
    else:
        if armature_name in _cache:
            del _cache[armature_name]
            _log.debug(f"Cache cleared for armature '{armature_name}'")

    _cache_generation += 1


def clear_cache() -> None:
    """Clear all cache and reset generation counter.

    Called from load_post handler to ensure clean state on file load.
    """
    global _cache_generation

    _cache.clear()
    _cache_generation = 0
    _log.debug("Cache fully cleared and generation reset")


def get_generation() -> int:
    """Get the current cache generation counter.

    Returns
    -------
    int
        Current generation value (incremented on each invalidation).
    """
    return _cache_generation


def get_unpaired(armature_name: str) -> list[str]:
    """Get list of bones with no detected opposite from cached map.

    Parameters
    ----------
    armature_name : str
        Name of the armature

    Returns
    -------
    list[str]
        List of bone names with None value in pair map.
        Empty list if armature not cached.
    """
    pair_map = _cache.get(armature_name)
    if pair_map is None:
        return []

    return [bone_name for bone_name, opposite in pair_map.items() if opposite is None]


def get_stats(armature_name: str) -> dict[str, int]:
    """Get statistics about cached pair map.

    Parameters
    ----------
    armature_name : str
        Name of the armature

    Returns
    -------
    dict[str, int]
        Dictionary with keys:
            - total: Total number of bones
            - paired: Number of bones with an opposite
            - unpaired: Number of bones without an opposite
            - generation: Current cache generation
        Returns empty dict if armature not cached.
    """
    pair_map = _cache.get(armature_name)
    if pair_map is None:
        return {}

    total = len(pair_map)
    paired = sum(1 for opposite in pair_map.values() if opposite is not None)
    unpaired = total - paired

    return {
        "total": total,
        "paired": paired,
        "unpaired": unpaired,
        "generation": _cache_generation,
    }
