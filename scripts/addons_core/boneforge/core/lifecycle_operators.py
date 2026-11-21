"""User-facing reload / state-purge operators (v3.3.0 — crash-safe).

Both operators inherit :class:`DeferredMutationOperator` so the actual
unregister + re-import work runs from a timer callback AFTER the
operator's own class has finished executing. Tearing down the running
operator's class mid-execute (which the v3.2.x implementation did)
causes a Blender segfault — that's what made the Reload / Purge buttons
crash. The deferred pattern is the fix.

Both deferred work functions are ``@staticmethod`` and do not touch
``self``. Reporting back to the user from inside a timer is not
possible (no operator context), so the deferred work logs at INFO /
WARNING / ERROR. The user sees a "scheduled" toast at click time and
the result in the system console + status bar after the timer fires.
"""

from __future__ import annotations

import importlib
import logging
import sys
import traceback

import bpy

from . import lifecycle
from .deferred import DeferredMutationOperator
from boneforge.i18n import T

logger = logging.getLogger(__name__)


class BF_OT_ReloadBoneForge(DeferredMutationOperator):
    """Hot-reload BoneCraft. No Blender restart needed.

    Sequence (runs from the deferred timer, not in execute):

    1. Call ``boneforge.unregister()``.
    2. Run :func:`lifecycle.unregister_lingering_classes`,
       :func:`lifecycle.scrub_scene_properties`, and
       :func:`lifecycle.purge_pycache` (the last is gated by the
       boneforge-root validator added in 3.2.4).
    3. Drop every ``boneforge.*`` from ``sys.modules`` so the next
       import reads source from disk.
    4. ``importlib.import_module("boneforge")`` and call ``register()``.

    On failure, logs the traceback to the system console.
    """

    bl_idname = "boneforge.reload_addon"
    bl_label = "Reload BoneCraft"
    bl_description = (
        "Hot-reload the BoneCraft add-on without restarting Blender. "
        "Useful after upgrading or developing locally"
    )
    bl_options = {"REGISTER"}

    def _scheduled_message(self):
        return (
            "Reloading BoneCraft — watch the system console for progress."
        )

    @staticmethod
    def _deferred_work(args):
        # Step 1: unregister the running copy.
        try:
            import boneforge
            boneforge.unregister()
        except Exception:
            logger.warning("[BoneCraft] reload: unregister raised:")
            traceback.print_exc()

        # Step 2: defensive sweep.
        try:
            lifecycle.unregister_lingering_classes()
            lifecycle.scrub_scene_properties()
            dirs, files = lifecycle.purge_pycache()
            if dirs:
                logger.info(
                    "[BoneCraft] reload purged %d __pycache__ dir(s)", dirs,
                )
        except Exception:
            logger.warning("[BoneCraft] reload: sweep raised:")
            traceback.print_exc()

        # Step 3: drop sys.modules. We're in a timer callback now —
        # no operator on the stack — so it's safe to drop everything.
        purged = 0
        for name in list(sys.modules):
            if name == "boneforge" or name.startswith("boneforge."):
                try:
                    del sys.modules[name]
                    purged += 1
                except KeyError:
                    pass

        # Step 4: re-import + register.
        try:
            boneforge = importlib.import_module("boneforge")
            boneforge.register()
            logger.info(
                "[BoneCraft] reload complete (%d module(s) refreshed)",
                purged,
            )
        except Exception:
            logger.error("[BoneCraft] reload failed during re-import:")
            traceback.print_exc()


class BF_OT_PurgeState(DeferredMutationOperator):
    """Strip BoneCraft state from this Blender session (advanced).

    Drops every BoneCraft class registration, removes every Scene-level
    property attribute, and clears ``__pycache__``. Does NOT touch
    user data — custom properties stamped on objects, meshes, bones,
    armatures, and inside saved blend files are left alone.
    """

    bl_idname = "boneforge.purge_state"
    bl_label = "Purge BoneCraft State (Advanced)"
    bl_description = (
        "Strip every BoneCraft class registration and Scene property "
        "from the current Blender session. Custom properties on your "
        "rig data are NOT touched. Use the Reload button afterwards "
        "to bring BoneCraft back, or remove the add-on for a clean "
        "Blender"
    )
    bl_options = {"REGISTER"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def draw(self, context):
        layout = self.layout
        layout.label(
            text=T("Unregister BoneCraft from this Blender session."),
        )
        layout.label(
            text=T("Custom properties on your rig data are kept."),
        )
        layout.label(
            text=T("Run 'Reload BoneCraft' afterwards to bring it back."),
        )

    def _scheduled_message(self):
        return "Purging BoneCraft state — Blender will not crash."

    @staticmethod
    def _deferred_work(args):
        try:
            import boneforge
            boneforge.unregister()
        except Exception:
            logger.warning("[BoneCraft] purge: unregister raised:")
            traceback.print_exc()

        try:
            lifecycle.unregister_lingering_classes()
            removed = lifecycle.scrub_scene_properties()
            dirs, files = lifecycle.purge_pycache()
            logger.info(
                "[BoneCraft] purged: %d Scene props, %d __pycache__ dirs "
                "(%d files)",
                len(removed), dirs, files,
            )
        except Exception:
            logger.error("[BoneCraft] purge failed:")
            traceback.print_exc()


_classes = (BF_OT_ReloadBoneForge, BF_OT_PurgeState)


def register():
    for cls in _classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError:
            pass


def unregister():
    for cls in reversed(_classes):
        try:
            bpy.utils.unregister_class(cls)
        except (RuntimeError, ValueError):
            pass
