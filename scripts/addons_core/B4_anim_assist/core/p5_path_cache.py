# --- TRAJECTORY VISUALIZATION ---
"""Per-target cached path samples with generation-based invalidation.

The cache is keyed by ``"object_name::bone_name"`` (or
``"object_name::"`` for plain objects).  Each entry stores its
``generation`` at build-time and is considered stale when the live
``SessionCache.generation`` has advanced.

GPU batches are built lazily alongside the sample data so the draw
callback pays zero Python overhead on cache hits.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from . import cache as cache_mod
from .p5_sampling import SamplePoint

__all__ = [
    "PathCacheEntry",
    "make_target_key",
    "get_entry",
    "store_entry",
    "invalidate",
    "invalidate_all",
    "all_entries",
    "cache_size",
]


# ---------------------------------------------------------------------------
# Cache entry
# ---------------------------------------------------------------------------

@dataclass
class PathCacheEntry:
    """Cached sample array for one target."""

    target_key: str
    samples: list[SamplePoint] = field(default_factory=list)
    generation: int = -1
    config_hash: str = ""
    # GPU batch built lazily by the draw module. Stored here so it is
    # invalidated together with the sample data.
    gpu_batch_3d: Any = field(default=None, repr=False)
    gpu_batch_ticks: Any = field(default=None, repr=False)


# ---------------------------------------------------------------------------
# Module-level cache
# ---------------------------------------------------------------------------

_cache: dict[str, PathCacheEntry] = {}


def make_target_key(obj_name: str, bone_name: str | None = None) -> str:
    """Build the cache lookup key for a target."""
    return f"{obj_name}::{bone_name or ''}"


def _config_hash(
    frame_start: float,
    frame_end: float,
    step: float,
    use_constraints: bool,
    space_mode: str,
) -> str:
    """Deterministic hash of sampling configuration."""
    raw = f"{frame_start:.2f}|{frame_end:.2f}|{step:.3f}|{use_constraints}|{space_mode}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def get_entry(key: str) -> PathCacheEntry | None:
    """Return a cache entry if it exists and is fresh, else ``None``."""
    entry = _cache.get(key)
    if entry is None:
        return None
    current_gen = cache_mod.get_cache().generation
    if entry.generation != current_gen:
        return None
    return entry


def store_entry(
    key: str,
    samples: list[SamplePoint],
    *,
    frame_start: float,
    frame_end: float,
    step: float,
    use_constraints: bool,
    space_mode: str,
) -> PathCacheEntry:
    """Store (or replace) a cache entry, tagging it with the current generation."""
    entry = PathCacheEntry(
        target_key=key,
        samples=samples,
        generation=cache_mod.get_cache().generation,
        config_hash=_config_hash(frame_start, frame_end, step, use_constraints, space_mode),
    )
    _cache[key] = entry
    return entry


def invalidate(key: str) -> bool:
    """Remove a single cache entry. Returns True if it existed."""
    return _cache.pop(key, None) is not None


def invalidate_all() -> int:
    """Remove every cached path. Returns count removed."""
    count = len(_cache)
    _cache.clear()
    return count


def all_entries() -> list[PathCacheEntry]:
    """Return a snapshot of all cache entries (for diagnostics)."""
    return list(_cache.values())


def cache_size() -> int:
    """Number of cached paths."""
    return len(_cache)
