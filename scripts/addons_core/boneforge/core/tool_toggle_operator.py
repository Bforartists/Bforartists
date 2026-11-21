"""User-facing tool toggle operator (v3.3.0).

Inherits :class:`DeferredMutationOperator` so the registration-mutating
work runs from a timer callback, not inside ``execute``. Without the
deferred pattern, toggling a tool would unregister classes that are
currently on the call stack — the same crash mode as the v3.2.x
Reload button hit.
"""

from __future__ import annotations

import logging

import bpy

from .deferred import DeferredMutationOperator
from .tool_registry import get_registry

logger = logging.getLogger(__name__)


class BF_OT_ToggleTool(DeferredMutationOperator):
    """Toggle a BoneCraft tool on/off via the registry.

    Reads ``self.tool_id``, captures it for the deferred work, and
    schedules ``registry.enable(id)`` or ``registry.disable(id)`` on
    a timer. The user sees an INFO toast at click time; the actual
    toggle happens ~50 ms later when no operator is on the stack.
    """

    bl_idname = "boneforge.toggle_tool"
    bl_label = "Toggle Tool"
    bl_description = (
        "Enable or disable a BoneCraft tool. Disabling actually "
        "unregisters the tool's classes, properties, and handlers — "
        "not just hides them in the UI"
    )
    bl_options = {"REGISTER"}

    tool_id: bpy.props.StringProperty(options={'HIDDEN', 'SKIP_SAVE'}, name="Tool ID")

    def _capture(self):
        return {"tool_id": self.tool_id}

    def _scheduled_message(self):
        registry = get_registry()
        if not registry.is_registered(self.tool_id):
            return f"Unknown tool: {self.tool_id}"
        manifest = registry.get(self.tool_id)
        action = "Disabling" if registry.is_enabled(self.tool_id) else "Enabling"
        return f"{action} {manifest.name}…"

    @staticmethod
    def _deferred_work(args):
        tool_id = args.get("tool_id", "")
        if not tool_id:
            logger.error("[BoneCraft] toggle: no tool_id supplied")
            return

        registry = get_registry()
        if not registry.is_registered(tool_id):
            logger.error("[BoneCraft] toggle: unknown tool %r", tool_id)
            return

        from boneforge import tab_sides
        try:
            if registry.is_enabled(tool_id):
                registry.disable(tool_id)
            else:
                tab_sides.place_all()                     # parents first: a side change may still wait for its timer
                with tab_sides.placing():                 # its panels register straight on their tab's side
                    registry.enable(tool_id)
        except (ValueError, KeyError) as exc:
            logger.error("[BoneCraft] toggle %s failed: %s", tool_id, exc)
            return

        # Persist the enabled set so the toggle survives Blender restarts.
        try:
            from boneforge import _save_enabled_set
            _save_enabled_set()
        except Exception:
            logger.warning(
                "[BoneCraft] could not persist enabled set after toggle",
            )
            import traceback
            traceback.print_exc()

        # A tool switched on registers its panels where its code puts them: move them to their tab's side.
        try:
            from boneforge import tab_sides
            tab_sides.place_all()
        except Exception:
            logger.warning("[BoneCraft] could not place the viewport tabs after toggle")

        # The Properties > Scene tab copies of the CATS tab must follow the toggle.
        try:
            from boneforge.core import scene_tab_mirror
            scene_tab_mirror.register()
        except Exception:
            logger.warning("[BoneCraft] could not rebuild Scene-tab copies after toggle")


_classes = (BF_OT_ToggleTool,)


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
