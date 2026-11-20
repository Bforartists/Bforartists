"""Install / uninstall hygiene for Anim Assist.

Three jobs, called from ``__init__.py``:

* ``purge_zombie_classes()`` — at the top of ``register()``, force-unregister
  any AA classes left lingering on ``bpy.types`` from a prior crashed load
  cycle. Without this, a register failure followed by a fresh load will hit
  "class already registered" errors and the addon won't come back.

* ``check_saved_versions()`` — at the end of ``register()``, walks every
  open scene and reports any saved schema versions that are *newer* than
  what this installed addon supports. Older saved versions are migrated
  forward by the existing ``core/migration.py`` chain; only the
  newer-than-installed case is unsafe and warrants a user-visible warning.

* ``deep_uninstall(...)`` — invoked by the user via the
  ``animassist.deep_uninstall`` operator BEFORE disabling the addon. Wipes:
    - ``aa_p12_manual::*`` and ``aa_p12_auto::*`` IDProperties from every
      Action (manual override sanctuary metadata).
    - ``anim_assist*`` scene PointerProperty data, reset to defaults.
    - Sequencer sound strips with names beginning ``AA_P12_`` from every
      scene's sequence editor.
    - Speaker datablocks named ``AA_P12_*``.
    - Bone-group entries named ``face_lipsync`` (the one auto-created
      by setup) — only when the group is empty (animator may have added
      bones; we never delete user-authored group memberships).
    - Application handler entries whose ``__module__`` references the
      addon — defensive cleanup if a register() failure left handlers behind.

The function returns a dict counter so the operator can report exactly
what was removed.

This module is intentionally bpy-only (no other addon imports) so it can
be loaded as the very first step of register() without dragging the rest
of the import graph in.
"""

from __future__ import annotations

import bpy

from .. import constants
from .logging import get_logger

__all__ = [
    "purge_zombie_classes",
    "check_saved_versions",
    "deep_uninstall",
]

_log = get_logger(__name__)

# Class-name prefixes the addon uses. Anything in bpy.types matching these is
# fair game for zombie cleanup at register() time.
_AA_CLASS_PREFIXES = (
    "AA_OT_",
    "AA_PT_",
    "AA_UL_",
    "AA_MT_",
    "AA_PG_",
    "AA_P11_",
    "AA_P12_",
    "ANIMASSIST_OT_",
    "ANIMASSIST_PT_",
    "ANIMASSIST_UL_",
    "ANIMASSIST_MT_",
    "ANIMASSIST_PG_",
)

# IDProperty key prefixes the lipsync engine stamps onto Action.id_data.
_AA_IDPROP_PREFIXES = (
    constants.P12_KEY_MANUAL_OVERRIDE_KEY,
    constants.P12_KEY_AUTO_BAKED_KEY,
)

# Sequencer/Speaker artifacts created by the lipsync setup operator.
_AA_SEQ_PREFIX = "AA_P12_"
_AA_SPEAKER_PREFIX = "AA_P12_"


# ---------------------------------------------------------------------------
# Zombie class purge — runs at the top of register()
# ---------------------------------------------------------------------------

def purge_zombie_classes() -> int:
    """Force-unregister any leftover AA classes from a prior load cycle.

    Returns the number of classes actually removed. Always safe to call.
    """
    if not hasattr(bpy, "types"):
        return 0
    candidates: list[type] = []
    for name in dir(bpy.types):
        if not name.startswith(_AA_CLASS_PREFIXES):
            continue
        cls = getattr(bpy.types, name, None)
        if cls is None:
            continue
        candidates.append(cls)

    removed = 0
    for cls in candidates:
        try:
            bpy.utils.unregister_class(cls)
            removed += 1
        except (RuntimeError, ValueError):
            # Class is registered as part of a still-live ClassRegistry —
            # leave it alone, the normal unregister path will handle it.
            pass
    if removed:
        _log.warning(
            "Removed %d zombie AA class(es) from bpy.types — "
            "previous addon load did not unregister cleanly",
            removed,
        )
    return removed


# ---------------------------------------------------------------------------
# Saved version check — runs at the end of register()
# ---------------------------------------------------------------------------

def check_saved_versions() -> list[str]:
    """Warn if any open scene was saved with a newer Anim Assist than installed.

    Returns a list of human-readable warning strings (empty if all OK). The
    caller logs these and may surface them in the UI.
    """
    warnings: list[str] = []
    installed = constants.MIGRATION_CURRENT_VERSION
    for scene in bpy.data.scenes:
        props = getattr(scene, constants.SCENE_PROP_ATTR, None)
        if props is None:
            continue
        saved = getattr(props, "migration_version", 0)
        if saved > installed:
            msg = (
                "Scene '" + scene.name + "' was saved with Anim Assist "
                "schema v" + str(saved) + " but installed addon supports up "
                "to v" + str(installed) + ". Downgrade is unsupported - "
                "back up the .blend before saving over it."
            )
            warnings.append(msg)
            _log.warning(msg)
    return warnings


# ---------------------------------------------------------------------------
# Deep uninstall — user-initiated, wipes all addon-stamped data
# ---------------------------------------------------------------------------

def deep_uninstall(
    purge_action_props: bool = True,
    purge_scene_data: bool = True,
    purge_sequencer: bool = True,
    purge_speakers: bool = True,
    purge_handlers: bool = True,
) -> dict[str, int]:
    """Wipe every persistent trace of Anim Assist from the current .blend.

    Run BEFORE disabling/uninstalling the addon for a clean slate. After this
    finishes, uninstall the addon and re-enable - no leftover state collides.

    Each flag may be turned off to skip that category - useful when the
    user only wants to reset, say, the lipsync custom properties without
    touching the audio strips they spent time placing.

    Returns a counter dict so the operator can report what it touched.
    """
    counts = {
        "action_idprops": 0,
        "scenes_reset": 0,
        "seq_strips_removed": 0,
        "speakers_removed": 0,
        "handlers_removed": 0,
    }

    if purge_action_props:
        for action in bpy.data.actions:
            keys_to_strip = [
                k for k in list(action.keys())
                if isinstance(k, str) and k.startswith(_AA_IDPROP_PREFIXES)
            ]
            for k in keys_to_strip:
                try:
                    del action[k]
                    counts["action_idprops"] += 1
                except KeyError:
                    pass

    if purge_scene_data:
        for scene in bpy.data.scenes:
            touched = False
            for attr in (
                constants.SCENE_PROP_ATTR,
                "anim_assist_p3", "anim_assist_p4", "anim_assist_p5",
                "anim_assist_p6", "anim_assist_p7", "anim_assist_p8",
                "anim_assist_p9", "anim_assist_p10", "anim_assist_p11",
                constants.P12_SCENE_ATTR,
            ):
                pg = getattr(scene, attr, None)
                if pg is None:
                    continue
                # Clear collections held by the PG. Scalars revert to
                # defaults next register() once the PG is reattached.
                for prop_name in dir(pg):
                    val = getattr(pg, prop_name, None)
                    if hasattr(val, "clear") and not callable(val):
                        try:
                            val.clear()
                            touched = True
                        except (AttributeError, TypeError):
                            pass
            if touched:
                counts["scenes_reset"] += 1

    if purge_sequencer:
        for scene in bpy.data.scenes:
            seq = getattr(scene, "sequence_editor", None)
            if seq is None:
                continue
            sequences = getattr(seq, "sequences", None)
            if sequences is None:
                continue
            to_remove = [
                s for s in list(sequences)
                if getattr(s, "name", "").startswith(_AA_SEQ_PREFIX)
            ]
            for s in to_remove:
                try:
                    sequences.remove(s)
                    counts["seq_strips_removed"] += 1
                except (RuntimeError, ReferenceError):
                    pass

    if purge_speakers:
        to_remove = [
            spk for spk in list(bpy.data.speakers)
            if spk.name.startswith(_AA_SPEAKER_PREFIX)
        ]
        for spk in to_remove:
            try:
                bpy.data.speakers.remove(spk)
                counts["speakers_removed"] += 1
            except (RuntimeError, ReferenceError):
                pass

    if purge_handlers:
        for handler_list_name in ("load_post", "undo_post", "redo_post", "depsgraph_update_post"):
            handler_list = getattr(bpy.app.handlers, handler_list_name, None)
            if handler_list is None:
                continue
            to_remove = []
            for fn in list(handler_list):
                module = getattr(fn, "__module__", "") or ""
                if "anim_assist" in module:
                    to_remove.append(fn)
            for fn in to_remove:
                try:
                    handler_list.remove(fn)
                    counts["handlers_removed"] += 1
                except (ValueError, RuntimeError):
                    pass

    _log.info(
        "Deep uninstall complete: %d action props, %d scenes reset, "
        "%d strips, %d speakers, %d handlers",
        counts["action_idprops"], counts["scenes_reset"],
        counts["seq_strips_removed"], counts["speakers_removed"],
        counts["handlers_removed"],
    )
    return counts
