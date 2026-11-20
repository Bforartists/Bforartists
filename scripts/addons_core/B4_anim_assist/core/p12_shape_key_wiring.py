"""Shape key wiring helpers for the lipsync system.

Parallel to ``rig_wiring`` (logical role -> bone name), shape_key_wiring maps
logical viseme names to shape_key names on the wired mesh.

Built-in viseme names match the libraries in p12_viseme_library:
  - BASIC_JAW: 'open' (rest is implied)
  - CARTOON_5: 'A', 'E', 'I', 'O', 'U'
  - REALISTIC_12: 'A_I', 'E', 'O', 'U', 'M_B_P', 'F_V', 'L', 'S_Z',
                  'Th', 'Sh_Ch', 'K_G'

Autofill heuristic: for each library viseme, search the mesh's shape keys
for a name containing the viseme (case-insensitive). Common naming
patterns supported: 'mouth_A', 'A', 'visemeA', 'phoneme_A', 'lipsync.A'.
"""

from __future__ import annotations

from . import p12_viseme_library as vl
from .logging import get_logger

__all__ = [
    "library_viseme_names",
    "autofill_shape_key_wiring",
    "find_shape_key_match",
    "missing_shape_keys",
]

_log = get_logger(__name__)


def library_viseme_names(library_id: str) -> list[str]:
    """Return the user-facing viseme names from a library (excludes 'rest')."""
    lib = vl.get_library(library_id)
    return sorted(name for name in lib.keys() if name != "rest")


def find_shape_key_match(viseme_name: str, key_block_names: list[str]) -> str:
    """Best-guess shape key for a viseme. Returns "" when no match.

    Strategy:
    1. Exact match (case-insensitive) on viseme_name.
    2. Any key containing viseme_name as a substring (case-insensitive).
    3. For phoneme groups like 'M_B_P', also try first letter alone ('M').
    """
    if not key_block_names:
        return ""
    target = viseme_name.lower()
    lower_keys = [(name, name.lower()) for name in key_block_names]

    # 1. Exact match
    for original, lower in lower_keys:
        if lower == target:
            return original

    # 2. Substring containment
    for original, lower in lower_keys:
        if target in lower:
            return original

    # 3. First letter of phoneme group
    if "_" in viseme_name:
        first_letter = viseme_name.split("_", 1)[0].lower()
        for original, lower in lower_keys:
            if first_letter in lower:
                return original

    return ""


def autofill_shape_key_wiring(
    p12,
    mesh_obj,
    library_id: str,
) -> int:
    """Pre-fill p12.shape_key_wiring rows by matching viseme names to shape keys.

    Returns the number of rows added. Skips visemes already in the wiring.
    Empty matches still get a row (with an empty shape_key_name) so the user
    can fill them in by hand without hunting for what's missing.
    """
    if p12 is None or mesh_obj is None:
        return 0
    sk = getattr(mesh_obj.data, "shape_keys", None) if hasattr(mesh_obj, "data") else None
    if sk is None:
        # No shape keys on this mesh - add empty rows for visibility.
        key_names = []
    else:
        key_names = [kb.name for kb in sk.key_blocks if kb.name != "Basis"]

    visemes = library_viseme_names(library_id)
    existing = {entry.viseme_name for entry in p12.shape_key_wiring}
    added = 0
    for viseme in visemes:
        if viseme in existing:
            continue
        match = find_shape_key_match(viseme, key_names)
        entry = p12.shape_key_wiring.add()
        entry.viseme_name = viseme
        entry.shape_key_name = match
        added += 1
    return added


def missing_shape_keys(p12, mesh_obj) -> list[str]:
    """Return the list of viseme names whose wired shape key isn't on the mesh.

    Used by the panel to surface broken wiring.
    """
    if p12 is None or mesh_obj is None:
        return []
    sk = getattr(mesh_obj.data, "shape_keys", None) if hasattr(mesh_obj, "data") else None
    if sk is None:
        return [entry.viseme_name for entry in p12.shape_key_wiring if entry.shape_key_name]
    available = {kb.name for kb in sk.key_blocks}
    out = []
    for entry in p12.shape_key_wiring:
        if entry.shape_key_name and entry.shape_key_name not in available:
            out.append(entry.viseme_name)
    return out
