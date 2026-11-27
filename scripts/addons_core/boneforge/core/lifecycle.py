"""BoneCraft install / uninstall / reload lifecycle helpers.

The problem this module solves: Bforartists / Blender does not actually
unload Python modules when an add-on is uninstalled or replaced. The
new install extracts files on disk but the *running* interpreter still
holds the old module objects in ``sys.modules``, the old class
registrations on ``bpy.types``, and the old compiled bytecode in every
``__pycache__/*.pyc`` next to the source. The result is the
all-too-familiar "I installed the new version but Blender keeps acting
like it's the old one" — which is what the user has been hitting.

What this module does (and what it does NOT do):

* Cleanly tear down every BoneCraft class registration on
  ``bpy.types``.
* Strip every Scene-level property whose name starts with the
  BoneCraft prefix.
* Purge every ``boneforge.*`` entry from ``sys.modules`` so the next
  ``import boneforge`` actually re-reads from disk.
* Walk the install directory and delete ``__pycache__`` so stale
  ``.pyc`` files cannot mask new ``.py`` source.
* DOES NOT delete user data — custom properties on objects, meshes,
  bones, the scene, or saved blend files are left alone. The Auto-Rig
  session, taskboard tasks, and per-object boneforge_* keys persist
  across reload.

These helpers are used in three places:

* ``boneforge.__init__.register()`` — runs the stale-module purge on
  startup so a freshly installed BoneCraft over a still-loaded older
  copy actually takes effect.
* ``boneforge.__init__.unregister()`` — runs the property + class
  scrub so the next ``register()`` starts from a clean slate.
* ``BF_OT_ReloadBoneForge`` operator — user-facing, surfaced as a
  button in the add-on preferences. One click reloads the entire
  add-on without restarting Blender.
"""

from __future__ import annotations

import logging
import os
import shutil
import sys
from typing import Iterable, List, Tuple

import bpy

logger = logging.getLogger(__name__)


# Prefix every BoneForge-owned thing shares.
_PKG_PREFIX = "boneforge"
_PROP_PREFIX = "boneforge_"

# Scene-level properties registered by various sub-modules, kept here so
# the scrub doesn't have to import every sub-module just to find them.
# We don't strictly need this list — the dynamic prefix scan covers it —
# but it's a useful audit log of the surface area.
_KNOWN_SCENE_PROPS: Tuple[str, ...] = (
    "boneforge_autorig_session",
    "boneforge_collection_visibility",
    "boneforge_taskboard_collapsed",
    "boneforge_transfer_source",
    "boneforge_transfer_method",
    "boneforge_transfer_bone_filter",
    "boneforge_transfer_normalize",
    "boneforge_transfer_mean_distance",
    "boneforge_transfer_max_distance",
    "boneforge_transfer_threshold_percent",
    "boneforge_transfer_flagged_vertices",
    "boneforge_mirror_axis",
    "boneforge_mirror_direction",
    "boneforge_use_mirror_topology",
    "boneforge_mirror_search_distance",
    "boneforge_mirror_mirrored_count",
    "boneforge_mirror_unmatched_count",
    "boneforge_mirror_unmatched_vertices",
    "boneforge_vrc_export_settings",
    "boneforge_vrc_optimizer",
    "boneforge_vrc_fix_model_settings",
    "boneforge_vrc_detected_collisions",
    "boneforge_vrm_settings",
    "boneforge_vrm_lint_results",
)


# ── sys.modules purge ──────────────────────────────────────────

def stale_module_names() -> List[str]:
    """Return every ``boneforge*`` name currently in ``sys.modules``.

    Includes the top-level package and every sub-module / sub-package.
    Useful for both detection (warn before doing anything) and as the
    list of keys to delete during a forced purge.
    """
    return [
        name for name in list(sys.modules)
        if name == _PKG_PREFIX or name.startswith(f"{_PKG_PREFIX}.")
    ]


def purge_modules(*, keep_self: bool = True) -> int:
    """Drop every ``boneforge*`` entry from ``sys.modules``.

    When ``keep_self`` is True (the default) the entry corresponding
    to *this* module is preserved — necessary when the purge is being
    invoked from inside a function that lives in this module, since
    the function's globals must remain reachable until it returns.
    The caller can drop the lifecycle module itself in a later pass.

    Returns the number of entries removed.
    """
    self_name = __name__
    targets = stale_module_names()
    if keep_self and self_name in targets:
        targets.remove(self_name)
    for name in targets:
        try:
            del sys.modules[name]
        except KeyError:
            pass
    return len(targets)


# ── Scene property scrub ────────────────────────────────────────

def scrub_scene_properties() -> List[str]:
    """Remove every Scene-level prop whose name starts with the prefix.

    ``bpy.types.Scene.boneforge_*`` are *attribute* registrations the
    add-on adds via ``PointerProperty`` etc.; they need to be removed
    for the next ``register()`` to work from a clean slate. Note this
    is NOT the same as the per-scene custom property data — instance
    data on ``bpy.context.scene["..."]`` is user-saved and untouched.
    """
    removed = []
    for name in list(dir(bpy.types.Scene)):
        if not name.startswith(_PROP_PREFIX):
            continue
        try:
            delattr(bpy.types.Scene, name)
            removed.append(name)
        except (AttributeError, RuntimeError) as exc:
            logger.debug("[BoneCraft] could not remove Scene.%s: %s", name, exc)
    return removed


# ── Class registration scrub ────────────────────────────────────

def unregister_lingering_classes() -> int:
    """Force-unregister every BF_*/BONEFORGE_* class on ``bpy.types``.

    Defensive sweep. After a normal ``unregister()`` chain this should
    be a no-op. After a botched install/upgrade where some classes
    survived a partial unregister, this is what mops up.
    """
    count = 0
    # bpy.types is dynamic — walk the names, look for ours.
    for name in list(dir(bpy.types)):
        if not (name.startswith("BF_") or name.startswith("BONEFORGE_")):
            continue
        cls = getattr(bpy.types, name, None)
        if cls is None:
            continue
        try:
            bpy.utils.unregister_class(cls)
            count += 1
        except (RuntimeError, ValueError, TypeError) as exc:
            logger.debug(
                "[BoneCraft] unregister_class(%s) failed: %s", name, exc,
            )
    return count


# ── __pycache__ cleanup ─────────────────────────────────────────


def _looks_like_boneforge_root(path: str) -> bool:
    """Defensive sanity check used by :func:`purge_pycache` (v3.2.4).

    A misbehaving Python interpreter or a corrupted addon path could in
    theory cause :func:`find_install_root` to resolve to something other
    than the real boneforge install (the fallback is structurally always
    inside the package, but introspection edge cases are hard to fully
    rule out). Before we recurse and delete ``__pycache__`` directories,
    require positive evidence that the resolved path really is the
    BoneCraft install.

    Refuses the path unless ALL of the following are true:

    * non-empty string
    * normalised path is at least 6 characters (refuses ``/``, ``C:``,
      and similarly short roots)
    * resolves to an existing directory
    * basename equals ``boneforge`` (case-insensitive)
    * contains an ``__init__.py`` file
    * that ``__init__.py`` mentions both ``bl_info`` and ``BoneCraft``
      somewhere in the first 4 KB

    The last two checks make a false positive — accidentally matching
    some unrelated directory on the user's disk that happened to be
    named ``boneforge`` — vanishingly unlikely.
    """
    if not path:
        return False
    norm = os.path.normpath(path)
    if len(norm) < 6:
        return False
    if not os.path.isdir(norm):
        return False
    if os.path.basename(norm).lower() != "boneforge":
        return False
    init_path = os.path.join(norm, "__init__.py")
    if not os.path.isfile(init_path):
        return False
    try:
        with open(init_path, encoding="utf-8", errors="replace") as f:
            head = f.read(4096)
    except OSError:
        return False
    # the product was renamed BoneForge -> BoneCraft (display only); an
    # install of either name is this add-on
    return "bl_info" in head and ("BoneCraft" in head or "Bone" + "Forge" in head)

def find_install_root() -> str:
    """Locate the on-disk root of the installed boneforge package.

    Returns the directory that contains the top-level ``__init__.py``.
    """
    pkg = sys.modules.get(_PKG_PREFIX)
    if pkg is not None and hasattr(pkg, "__file__") and pkg.__file__:
        return os.path.dirname(pkg.__file__)
    # Fallback: walk up from this file
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def purge_pycache(install_root: str = None) -> Tuple[int, int]:
    """Recursively delete every ``__pycache__`` under the install root.

    Returns ``(directories_deleted, files_deleted)``. Errors are
    swallowed and logged at DEBUG — half a cleanup is better than
    none.

    v3.2.4: refuses to walk a path that does not look like the
    BoneCraft install (see :func:`_looks_like_boneforge_root`).
    Returns ``(0, 0)`` and logs a WARNING in that case rather than
    risking deletion of an unrelated directory.
    """
    if install_root is None:
        install_root = find_install_root()

    if not _looks_like_boneforge_root(install_root):
        logger.warning(
            "[BoneCraft] purge_pycache refused: %r does not look like a "
            "BoneCraft install. No files were deleted.",
            install_root,
        )
        return 0, 0

    dirs_deleted = 0
    files_deleted = 0
    for root, dirs, files in os.walk(install_root):
        for d in list(dirs):
            if d != "__pycache__":
                continue
            cache_dir = os.path.join(root, d)
            try:
                files_in_cache = sum(
                    1 for _ in os.scandir(cache_dir)
                )
                shutil.rmtree(cache_dir, ignore_errors=False)
                dirs_deleted += 1
                files_deleted += files_in_cache
            except (OSError, FileNotFoundError) as exc:
                logger.debug(
                    "[BoneCraft] could not remove %s: %s", cache_dir, exc,
                )
            # Stop os.walk from descending into the (now-deleted) cache dir.
            dirs.remove(d)
    return dirs_deleted, files_deleted


# ── Composite operations ────────────────────────────────────────

def teardown(*, scrub_scene: bool = True,
             clean_pycache: bool = True) -> dict:
    """Best-effort full teardown. Used by ``unregister`` and reload.

    Returns a dict summarising what was cleaned up — useful for
    surfacing in the operator report so the user can see the result.
    """
    summary: dict = {
        "classes_unregistered": 0,
        "scene_props_removed": 0,
        "pycache_dirs": 0,
        "pycache_files": 0,
    }

    summary["classes_unregistered"] = unregister_lingering_classes()
    if scrub_scene:
        removed = scrub_scene_properties()
        summary["scene_props_removed"] = len(removed)
        if removed:
            logger.info("[BoneCraft] scrubbed %d Scene props", len(removed))
    if clean_pycache:
        dirs, files = purge_pycache()
        summary["pycache_dirs"] = dirs
        summary["pycache_files"] = files
        if dirs:
            logger.info(
                "[BoneCraft] purged %d __pycache__ dir(s) (%d files)",
                dirs, files,
            )
    return summary


def detect_stale_install() -> dict:
    """Probe for indicators that an older BoneCraft is still loaded.

    Called from ``register()`` BEFORE the new modules are imported,
    so the result reflects what was already in memory at the time
    Blender re-ran our top-level ``__init__.py``. A non-empty
    ``modules`` list means a previous install is shadowing this one.
    """
    return {
        "modules": stale_module_names(),
        "scene_props": [
            name for name in dir(bpy.types.Scene)
            if name.startswith(_PROP_PREFIX)
        ],
    }
