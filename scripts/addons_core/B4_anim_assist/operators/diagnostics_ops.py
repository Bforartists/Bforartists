"""Diagnostics operators: refresh and copy-to-clipboard."""

from __future__ import annotations

import bpy

from .. import constants
from ..core import cache as cache_mod
from ..core import capabilities as cap_mod
from ..core import runtime as rts_mod
from ..core.context_resolver import AnimContextResolver
from ..core.helpers import redraw_notify
from ..core.logging import get_logger
from ..core.target_resolver import get_active_target

_log = get_logger(__name__)


def _build_diagnostics_text(context: bpy.types.Context) -> str:
    lines: list[str] = []
    lines.append(f"Anim Assist v{constants.ADDON_VERSION_STRING}")
    lines.append(f"Blender {bpy.app.version_string}")
    lines.append("")

    target = get_active_target(context)
    if target is not None:
        lines.append(f"Active Object: {target.obj.name}")
        if target.bone_name:
            lines.append(f"Active Bone: {target.bone_name}")
        if target.action:
            lines.append(
                f"Action: {target.action.name} ({len(target.fcurves)} fcurves)"
            )
        else:
            lines.append("Action: None")
        lines.append(f"Linked: {target.is_linked}")
    else:
        lines.append("Active Object: None")

    lines.append("")

    ge = AnimContextResolver.get_graph_editor(context)
    ds = AnimContextResolver.get_dope_sheet(context)
    tl = AnimContextResolver.get_timeline(context)
    lines.append(f"Graph Editor: {'found' if ge else 'not found'}")
    lines.append(f"Dope Sheet: {'found' if ds else 'not found'}")
    lines.append(f"Timeline: {'found' if tl else 'not found'}")

    lines.append("")

    reg = cap_mod.get_registry()
    caps = reg.all_capabilities()
    lines.append(f"Capabilities ({len(caps)}):")
    for name, available in sorted(caps.items()):
        lines.append(f"  {name}: {'OK' if available else 'UNAVAILABLE'}")

    lines.append("")

    cache = cache_mod.get_cache()
    lines.append(f"Selection history entries: {len(cache.selection_history)}")
    lines.append(f"Last used tool: {cache.last_used_tool or '(none)'}")

    state = rts_mod.get_state()
    lines.append(f"Active tool: {state.active_tool_id or '(none)'}")
    lines.append(f"Batch processing: {state.is_batch_processing}")

    return "\n".join(lines)


class AA_OT_copy_diagnostics(bpy.types.Operator):
    bl_idname = "anim_assist.copy_diagnostics"
    bl_label = "Copy Diagnostics"
    bl_description = "Copy diagnostics information to clipboard"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return getattr(context, "window_manager", None) is not None

    def execute(self, context: bpy.types.Context):
        wm = getattr(context, "window_manager", None)
        if wm is None:
            self.report({"ERROR"}, "Window manager not available. Run this from the Bforartists interface, not a background script")
            return {"CANCELLED"}

        try:
            text = _build_diagnostics_text(context)
        except Exception:
            _log.exception("Failed to build diagnostics text")
            self.report({"ERROR"}, "Could not collect diagnostics. Details are in the system console (Window > Toggle System Console)")
            return {"CANCELLED"}

        wm.clipboard = text
        self.report({"INFO"}, "Diagnostics copied to clipboard")
        return {"FINISHED"}


class AA_OT_refresh_diagnostics(bpy.types.Operator):
    bl_idname = "anim_assist.refresh_diagnostics"
    bl_label = "Refresh Diagnostics"
    bl_description = "Force refresh diagnostics display"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return getattr(context, "screen", None) is not None

    def execute(self, context: bpy.types.Context):
        redraw_notify(context)
        self.report({"INFO"}, "Diagnostics refreshed")
        return {"FINISHED"}