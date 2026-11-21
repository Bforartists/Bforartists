"""Per-key metadata store (tags, notes, protection, flavor flags).

Persisted via a ``CollectionProperty`` on ``AA_SceneProperties`` and indexed
by an in-memory lookup rebuilt on-demand.

Index is keyed per scene (``scene.name_full``) so multi-scene files never
cross-contaminate each other's lookups.
"""

from __future__ import annotations

from typing import Iterable

import bpy

from .. import constants
from .context_utils import key_identity, iter_visible_fcurves, iter_selected_keys

__all__ = [
    "mark_dirty",
    "rebuild_index",
    "get_meta",
    "upsert_meta",
    "delete_meta",
    "is_protected",
    "iter_selected_idents",
    "iter_tagged",
    "prune_orphans",
]


# ---------------------------------------------------------------------------
# Per-scene in-memory index
# ---------------------------------------------------------------------------

# scene.name_full -> { (obj_name, data_path, array_index, frame) : coll_index }
_indexes: dict[str, dict[tuple, int]] = {}
_dirty_scenes: set[str] = set()


def _get_collection(scene: bpy.types.Scene) -> bpy.types.bpy_prop_collection | None:
    pg = getattr(scene, constants.SCENE_PROP_ATTR, None)
    if pg is None:
        return None
    return getattr(pg, "key_metadata", None)


def mark_dirty(scene: bpy.types.Scene | None = None) -> None:
    """Mark the index for *scene* (or all scenes when *scene* is ``None``) as stale."""
    if scene is None:
        _dirty_scenes.update(_indexes.keys())
    else:
        _dirty_scenes.add(scene.name_full)


def rebuild_index(scene: bpy.types.Scene) -> None:
    """Rebuild the identity→collection-index map for *scene*."""
    key = scene.name_full
    idx: dict[tuple, int] = {}
    coll = _get_collection(scene)
    if coll is not None:
        for i, item in enumerate(coll):
            ident = (
                item.object_name,
                item.data_path,
                item.array_index,
                round(item.frame, 4),
            )
            idx[ident] = i
    _indexes[key] = idx
    _dirty_scenes.discard(key)


def _ensure_index(scene: bpy.types.Scene) -> dict[tuple, int]:
    key = scene.name_full
    if key in _dirty_scenes or key not in _indexes:
        rebuild_index(scene)
    return _indexes[key]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_meta(scene: bpy.types.Scene, ident: tuple):
    """Return the ``AA_KeyMetaItem`` for *ident* in *scene*, or ``None``."""
    index = _ensure_index(scene)
    coll = _get_collection(scene)
    if coll is None:
        return None
    idx = index.get(ident)
    if idx is None or idx >= len(coll):
        return None
    return coll[idx]


def upsert_meta(
    scene: bpy.types.Scene,
    ident: tuple,
    *,
    tag: str | None = None,
    note: str | None = None,
    protected: bool | None = None,
    flavor: str | None = None,
):
    """Create or update the metadata record for *ident* in *scene*.

    Only keyword arguments that are not ``None`` are written, so callers can
    update a single field without touching the others.
    """
    coll = _get_collection(scene)
    if coll is None:
        return None
    item = get_meta(scene, ident)
    if item is None:
        item = coll.add()
        item.object_name = ident[0]
        item.data_path = ident[1]
        item.array_index = ident[2]
        item.frame = float(ident[3])
        mark_dirty(scene)
    if tag is not None:
        item.tag = tag
    if note is not None:
        item.note = note
    if protected is not None:
        item.protected = bool(protected)
    if flavor is not None:
        item.flavor = flavor
    return item


def delete_meta(scene: bpy.types.Scene, ident: tuple) -> bool:
    """Remove the metadata record for *ident*.  Returns ``True`` on success."""
    coll = _get_collection(scene)
    if coll is None:
        return False
    index = _ensure_index(scene)
    idx = index.get(ident)
    if idx is None:
        return False
    coll.remove(idx)
    mark_dirty(scene)
    return True


def is_protected(scene: bpy.types.Scene, ident: tuple) -> bool:
    """Return True if a keyframe is marked as protected (cannot be deleted by batch cleanup).

    Called by delete operators before removing keys to preserve important pose frames
    (e.g., contact poses) from accidental loss.
    """
    item = get_meta(scene, ident)
    return bool(item and item.protected)


def iter_selected_idents(context: bpy.types.Context) -> Iterable[tuple]:
    """Yield identity tuples for every currently selected keyframe."""
    for obj, _a, fc, _i, kp in iter_selected_keys(context):
        yield key_identity(obj.name, fc, kp.co.x)


def iter_tagged(scene: bpy.types.Scene, tag: str) -> Iterable:
    """Yield all ``AA_KeyMetaItem`` records in *scene* whose tag matches."""
    coll = _get_collection(scene)
    if coll is None:
        return
    for item in coll:
        if item.tag == tag:
            yield item


def prune_orphans(context: bpy.types.Context) -> int:
    """Remove metadata records whose keyframe no longer exists in *context*.

    Walks every visible FCurve to build a live identity set, then removes any
    collection entry not in that set.  Rebuilds the index once at the end.
    """
    scene = context.scene
    coll = _get_collection(scene)
    if coll is None:
        return 0

    live: set[tuple] = set()
    for obj, _a, fc in iter_visible_fcurves(context):
        for kp in fc.keyframe_points:
            live.add(key_identity(obj.name, fc, kp.co.x))

    removed = 0
    i = len(coll) - 1
    while i >= 0:
        item = coll[i]
        ident = (
            item.object_name,
            item.data_path,
            item.array_index,
            round(item.frame, 4),
        )
        if ident not in live:
            coll.remove(i)
            removed += 1
        i -= 1

    mark_dirty(scene)
    return removed
