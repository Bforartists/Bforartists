# --- IK CHAIN RESOLVER ---
"""IK chain detection and resolution engine for armature rigs.

Problem
-------
When animators switch between IK and FK modes, they need to know which
bones belong to an IK chain so the correct transforms can be matched,
baked, or compensated.  Blender stores IK constraints on individual bones
but provides no built-in API to walk the chain from tip to root.  This
module fills that gap with rig-agnostic chain detection that works across
Rigify, BlenRig, Game-Rig, and custom rigs alike.

Key concepts
------------
* **IK tip** — the bone that carries the ``INVERSE_KINEMATICS`` constraint.
* **Chain length** — how many parent bones the IK solver affects
  (``constraint.chain_count``; 0 means "solve to root").
* **IK target** — the object or bone the solver aims toward.
* **Pole target** — the object or bone that controls the plane of the chain
  (e.g. knee direction).
* **Chain root** — the highest bone in the chain; determined by walking
  *chain_length* parents from the tip, or reaching the armature root.

Usage
-----
::

    from .p8_chain_resolver import detect_ik_chains, IKChain

    chains = detect_ik_chains(armature_obj)
    for chain in chains:
        print(chain.tip_bone, "→", chain.root_bone, f"({chain.length} bones)")
        print("  members:", chain.bone_names)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .logging import get_logger

if TYPE_CHECKING:
    import bpy

__all__ = [
    "IKChainConstraintInfo",
    "IKChain",
    "detect_ik_chains",
    "detect_ik_chains_for_bone",
    "get_chain_bone_names",
    "get_chain_root",
    "get_chain_length",
    "is_bone_in_ik_chain",
    "find_chains_involving_bone",
    "get_ik_target_info",
    "get_chain_summary",
    "invalidate_chain_cache",
]

_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IKChainConstraintInfo:
    """Metadata extracted from a single IK constraint.

    Captures the essential solver parameters without holding a live Blender
    reference, so the data remains valid after undo/redo cycles.
    """

    constraint_name: str
    """Name of the INVERSE_KINEMATICS constraint on the tip bone."""

    target_object: str
    """Name of the target object (empty string if unset)."""

    target_bone: str
    """Name of the target subtarget bone (empty string if object-level)."""

    pole_object: str
    """Name of the pole-target object (empty string if unset)."""

    pole_bone: str
    """Name of the pole subtarget bone (empty string if object-level)."""

    influence: float
    """Constraint influence at detection time (0.0–1.0)."""

    use_rotation: bool
    """Whether the IK solver also drives rotation."""

    iterations: int
    """Maximum solver iterations configured on the constraint."""


@dataclass(frozen=True)
class IKChain:
    """A resolved IK chain from tip bone to chain root.

    Immutable snapshot of a detected chain so it can be safely cached,
    compared, and passed to operators without risk of stale pointers.
    """

    tip_bone: str
    """Name of the bone carrying the IK constraint (chain end)."""

    root_bone: str
    """Name of the highest bone the IK solver affects (chain start)."""

    bone_names: tuple[str, ...]
    """Ordered bone names from tip → root (inclusive)."""

    length: int
    """Number of bones in the chain (== len(bone_names))."""

    constraint_info: IKChainConstraintInfo
    """Solver parameters extracted from the IK constraint."""

    is_active: bool
    """True if the constraint is unmuted and influence > 0."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _walk_parents(
    armature_obj: bpy.types.Object,
    tip_name: str,
    chain_count: int,
) -> list[str]:
    """Walk parent bones from *tip_name* up to *chain_count* levels.

    Parameters
    ----------
    armature_obj
        The armature object whose pose bones define the hierarchy.
    tip_name
        Name of the starting (tip) bone.
    chain_count
        Number of parent bones to walk.  ``0`` means walk to the root.

    Returns
    -------
    list[str]
        Bone names from tip to root (inclusive).
    """
    pose = getattr(armature_obj, "pose", None)
    if pose is None:
        return [tip_name]

    names: list[str] = [tip_name]
    bone = pose.bones.get(tip_name)
    if bone is None:
        return names

    steps = 0
    limit = chain_count if chain_count > 0 else 512  # safety ceiling
    current = bone.parent
    while current is not None and steps < limit:
        names.append(current.name)
        current = current.parent
        steps += 1

    return names


def _extract_constraint_info(
    con: bpy.types.Constraint,
) -> IKChainConstraintInfo:
    """Pull solver metadata out of a live IK constraint."""
    target_obj = getattr(con.target, "name", "") if con.target else ""
    target_bone = getattr(con, "subtarget", "") or ""
    pole_obj = ""
    pole_bone = ""
    if hasattr(con, "pole_target") and con.pole_target is not None:
        pole_obj = con.pole_target.name
        pole_bone = getattr(con, "pole_subtarget", "") or ""

    return IKChainConstraintInfo(
        constraint_name=con.name,
        target_object=target_obj,
        target_bone=target_bone,
        pole_object=pole_obj,
        pole_bone=pole_bone,
        influence=con.influence,
        use_rotation=getattr(con, "use_rotation", False),
        iterations=getattr(con, "iterations", 500),
    )


# ---------------------------------------------------------------------------
# Module-level cache
# ---------------------------------------------------------------------------

class _ChainCache:
    """Session-scoped cache for resolved IK chains.

    Invalidated on undo, redo, file-load, or explicit request.
    Avoids redundant hierarchy walks when multiple operators query chains
    for the same armature within a single edit cycle.
    """

    __slots__ = ("_store",)

    def __init__(self) -> None:
        self._store: dict[str, list[IKChain]] = {}

    def get(self, armature_name: str) -> list[IKChain] | None:
        return self._store.get(armature_name)

    def put(self, armature_name: str, chains: list[IKChain]) -> None:
        self._store[armature_name] = chains

    def invalidate(self, armature_name: str | None = None) -> None:
        if armature_name is None:
            self._store.clear()
        else:
            self._store.pop(armature_name, None)

    def size(self) -> int:
        return len(self._store)


_cache = _ChainCache()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_ik_chains(
    armature_obj: bpy.types.Object,
    *,
    include_muted: bool = False,
    min_influence: float = 0.0,
    use_cache: bool = True,
) -> list[IKChain]:
    """Detect all IK chains on an armature by scanning every pose bone.

    Walks the bone hierarchy from each IK-constrained tip upward to
    determine the full chain membership.  Results are cached per armature
    to avoid repeated hierarchy traversals during a single edit session.

    Parameters
    ----------
    armature_obj
        Must be an ``ARMATURE``-type object.  Returns empty list otherwise.
    include_muted
        When True, also include chains whose IK constraint is muted.
    min_influence
        Skip constraints below this influence threshold (0.0–1.0).
    use_cache
        When True, return cached results if available.

    Returns
    -------
    list[IKChain]
        All detected chains, sorted by chain length (longest first).
    """
    if armature_obj is None or armature_obj.type != "ARMATURE":
        return []

    arm_name = armature_obj.name

    if use_cache:
        cached = _cache.get(arm_name)
        if cached is not None:
            _log.debug("Chain cache hit for %s (%d chains)", arm_name, len(cached))
            return cached

    pose = getattr(armature_obj, "pose", None)
    if pose is None:
        return []

    chains: list[IKChain] = []

    for pbone in pose.bones:
        for con in pbone.constraints:
            if con.type != "INVERSE_KINEMATICS":
                continue
            if con.mute and not include_muted:
                continue
            if con.influence < min_influence:
                continue

            chain_count = getattr(con, "chain_count", 0)
            bone_names = _walk_parents(armature_obj, pbone.name, chain_count)
            info = _extract_constraint_info(con)
            is_active = not con.mute and con.influence > 0.0

            chain = IKChain(
                tip_bone=pbone.name,
                root_bone=bone_names[-1],
                bone_names=tuple(bone_names),
                length=len(bone_names),
                constraint_info=info,
                is_active=is_active,
            )
            chains.append(chain)
            _log.debug(
                "Detected IK chain: %s → %s (%d bones, active=%s)",
                chain.tip_bone, chain.root_bone, chain.length, is_active,
            )

    chains.sort(key=lambda c: c.length, reverse=True)

    if use_cache:
        _cache.put(arm_name, chains)

    _log.debug("Total chains detected on %s: %d", arm_name, len(chains))
    return chains


def detect_ik_chains_for_bone(
    armature_obj: bpy.types.Object,
    bone_name: str,
    *,
    include_muted: bool = False,
) -> list[IKChain]:
    """Detect IK chains originating from a specific bone.

    Only returns chains where *bone_name* is the IK tip — not chains
    that merely pass through the bone.  Use :func:`find_chains_involving_bone`
    for the broader query.

    Parameters
    ----------
    armature_obj
        The armature to scan.
    bone_name
        Name of the pose bone to check for IK constraints.
    include_muted
        When True, include muted IK constraints.

    Returns
    -------
    list[IKChain]
        Chains whose tip is *bone_name*.
    """
    all_chains = detect_ik_chains(
        armature_obj, include_muted=include_muted,
    )
    return [c for c in all_chains if c.tip_bone == bone_name]


def get_chain_bone_names(
    armature_obj: bpy.types.Object,
    tip_bone: str,
    chain_count: int = 0,
) -> tuple[str, ...]:
    """Return the ordered bone names from tip to root for a given chain spec.

    This is a lightweight wrapper around the internal parent-walk logic,
    useful when you already know the tip and chain length but don't need
    a full :class:`IKChain` object.

    Parameters
    ----------
    armature_obj
        The armature object.
    tip_bone
        Name of the chain's tip bone.
    chain_count
        Number of parents to walk (0 = walk to root).

    Returns
    -------
    tuple[str, ...]
        Bone names from tip to root.
    """
    return tuple(_walk_parents(armature_obj, tip_bone, chain_count))


def get_chain_root(
    armature_obj: bpy.types.Object,
    tip_bone: str,
    chain_count: int = 0,
) -> str:
    """Return the root bone name for a chain starting at *tip_bone*.

    Parameters
    ----------
    armature_obj
        The armature object.
    tip_bone
        Name of the chain's tip bone.
    chain_count
        Number of parents to walk (0 = walk to root).

    Returns
    -------
    str
        Name of the root bone (last in the parent walk).
    """
    names = _walk_parents(armature_obj, tip_bone, chain_count)
    return names[-1] if names else tip_bone


def get_chain_length(
    armature_obj: bpy.types.Object,
    tip_bone: str,
    chain_count: int = 0,
) -> int:
    """Return how many bones a chain contains.

    Parameters
    ----------
    armature_obj
        The armature object.
    tip_bone
        Name of the chain's tip bone.
    chain_count
        Number of parents to walk (0 = walk to root).

    Returns
    -------
    int
        Total bone count in the chain.
    """
    return len(_walk_parents(armature_obj, tip_bone, chain_count))


def is_bone_in_ik_chain(
    armature_obj: bpy.types.Object,
    bone_name: str,
    *,
    include_muted: bool = False,
) -> bool:
    """Check whether a bone participates in any IK chain.

    Parameters
    ----------
    armature_obj
        The armature to scan.
    bone_name
        Name of the pose bone to check.
    include_muted
        When True, include muted IK chains in the search.

    Returns
    -------
    bool
        True if *bone_name* appears in any detected chain's bone list.
    """
    chains = detect_ik_chains(armature_obj, include_muted=include_muted)
    return any(bone_name in c.bone_names for c in chains)


def find_chains_involving_bone(
    armature_obj: bpy.types.Object,
    bone_name: str,
    *,
    include_muted: bool = False,
) -> list[IKChain]:
    """Find all chains that a bone participates in (as tip, root, or member).

    Unlike :func:`detect_ik_chains_for_bone` which only checks the tip,
    this returns every chain whose ``bone_names`` tuple contains *bone_name*.

    Parameters
    ----------
    armature_obj
        The armature to scan.
    bone_name
        Name of the pose bone to search for.
    include_muted
        When True, include muted IK chains.

    Returns
    -------
    list[IKChain]
        All chains containing *bone_name*.
    """
    chains = detect_ik_chains(armature_obj, include_muted=include_muted)
    return [c for c in chains if bone_name in c.bone_names]


def get_ik_target_info(
    armature_obj: bpy.types.Object,
    tip_bone: str,
) -> list[IKChainConstraintInfo]:
    """Return constraint metadata for all IK constraints on a bone.

    Useful for inspecting target/pole-target assignments without needing
    the full chain resolution.

    Parameters
    ----------
    armature_obj
        The armature object.
    tip_bone
        Name of the pose bone to inspect.

    Returns
    -------
    list[IKChainConstraintInfo]
        Info for each IK constraint found on the bone.
    """
    if armature_obj is None or armature_obj.type != "ARMATURE":
        return []
    pose = getattr(armature_obj, "pose", None)
    if pose is None:
        return []
    pbone = pose.bones.get(tip_bone)
    if pbone is None:
        return []

    results: list[IKChainConstraintInfo] = []
    for con in pbone.constraints:
        if con.type == "INVERSE_KINEMATICS":
            try:
                results.append(_extract_constraint_info(con))
            except Exception:
                _log.exception(
                    "Failed to extract IK info from %s.%s",
                    tip_bone, con.name,
                )
    return results


def get_chain_summary(
    armature_obj: bpy.types.Object,
    *,
    include_muted: bool = False,
) -> dict[str, object]:
    """Return a human-readable summary dict of all IK chains on an armature.

    Intended for diagnostic panels and logging.

    Parameters
    ----------
    armature_obj
        The armature to scan.
    include_muted
        When True, include muted IK chains.

    Returns
    -------
    dict[str, object]
        Keys: ``armature``, ``total_chains``, ``active_chains``,
        ``muted_chains``, ``longest_chain``, ``chains`` (list of dicts).
    """
    chains = detect_ik_chains(armature_obj, include_muted=include_muted)
    active = [c for c in chains if c.is_active]
    muted = [c for c in chains if not c.is_active]
    longest = max((c.length for c in chains), default=0)

    chain_dicts = []
    for c in chains:
        chain_dicts.append({
            "tip": c.tip_bone,
            "root": c.root_bone,
            "length": c.length,
            "active": c.is_active,
            "target": c.constraint_info.target_object or "(none)",
            "pole": c.constraint_info.pole_object or "(none)",
            "influence": round(c.constraint_info.influence, 3),
        })

    return {
        "armature": getattr(armature_obj, "name", "?"),
        "total_chains": len(chains),
        "active_chains": len(active),
        "muted_chains": len(muted),
        "longest_chain": longest,
        "chains": chain_dicts,
    }


def invalidate_chain_cache(armature_name: str | None = None) -> None:
    """Clear the IK chain cache.

    Called automatically on undo, redo, and file-load via app_handlers.
    Can also be called manually after rig edits that change bone hierarchy.

    Parameters
    ----------
    armature_name
        Clear only the cache for this armature.  ``None`` clears everything.
    """
    _cache.invalidate(armature_name)
    if armature_name:
        _log.debug("Chain cache invalidated for %s", armature_name)
    else:
        _log.debug("Chain cache fully invalidated")
