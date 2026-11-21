"""Diagnostics sidebar panel."""

from __future__ import annotations

import bpy

from .. import constants
from ..core import cache as cache_mod
from ..core import capabilities as cap_mod
from ..core import runtime as rts_mod
from ..core.context_resolver import AnimContextResolver
# --- EXPLAINER SYSTEM EXTENSION ---
from ..core.help_draw import draw_explainer_icon
from ..core.target_resolver import get_active_target
from ..core.timeline_utils import get_current_frame, get_effective_frame_range


def _get_prefs(context: bpy.types.Context):
    addons = getattr(getattr(context, "preferences", None), "addons", None)
    if addons is None:
        return None
    addon = addons.get(constants.ADDON_PACKAGE)
    if addon is None:
        return None
    return getattr(addon, "preferences", None)


class AA_PT_diagnostics(bpy.types.Panel):
    bl_label = "AnimAssist Diagnostics"
    bl_idname = "AA_PT_diagnostics"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AnimAssist"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout

        # --- EXPLAINER SYSTEM EXTENSION ---
        header = layout.row(align=True)
        header.label(text=f"v{constants.ADDON_VERSION_STRING}", icon="INFO")
        draw_explainer_icon(header, context, "panel.aa_pt_diagnostics")

        # Active target ---------------------------------------------------
        box = layout.box()
        row = box.row(align=True)
        row.label(text="Active Target", icon="OBJECT_DATA")
        draw_explainer_icon(row, context, "panel.aa_pt_diagnostics")
        target = get_active_target(context)
        if target is not None:
            box.label(text=f"Object: {target.obj.name}")
            if target.bone_name:
                box.label(text=f"Bone: {target.bone_name}")
            if target.action:
                box.label(text=f"Action: {target.action.name}")
                box.label(text=f"FCurves: {len(target.fcurves)}")
            else:
                box.label(text="Action: None")
            if target.is_linked:
                box.label(text="(Linked)", icon="LIBRARY_DATA_DIRECT")
        else:
            box.label(text="No active object")

        # Timeline --------------------------------------------------------
        box = layout.box()
        box.label(text="Timeline", icon="TIME")
        frame_range = get_effective_frame_range(context)
        box.label(text=f"Range: {frame_range[0]} \u2013 {frame_range[1]}")
        box.label(text=f"Current: {get_current_frame(context)}")

        # Editors ---------------------------------------------------------
        box = layout.box()
        box.label(text="Editors", icon="WINDOW")
        ge = AnimContextResolver.get_graph_editor(context)
        ds = AnimContextResolver.get_dope_sheet(context)
        tl = AnimContextResolver.get_timeline(context)
        row = box.row()
        row.label(text="Graph: " + ("\u2713" if ge else "\u2717"))
        row.label(text="Dope: " + ("\u2713" if ds else "\u2717"))
        row.label(text="Time: " + ("\u2713" if tl else "\u2717"))

        # Capabilities ----------------------------------------------------
        reg = cap_mod.get_registry()
        caps = reg.all_capabilities()
        box = layout.box()
        box.label(text=f"Capabilities ({len(caps)})", icon="CHECKMARK")
        for name, available in sorted(caps.items()):
            row = box.row()
            row.label(text=name)
            row.label(
                text="OK" if available else "N/A",
                icon="CHECKMARK" if available else "CANCEL",
            )

        # Runtime / cache -------------------------------------------------
        box = layout.box()
        box.label(text="Runtime", icon="SYSTEM")
        state = rts_mod.get_state()
        box.label(text=f"Tool: {state.active_tool_id or '(none)'}")
        box.label(text=f"Batch: {state.is_batch_processing}")
        cache = cache_mod.get_cache()
        box.label(text=f"Selection history: {len(cache.selection_history)}")
        box.label(text=f"Last tool: {cache.last_used_tool or '(none)'}")

        last_target = cache.last_active_target
        if last_target:
            tgt_obj = last_target.get("object_name", "")
            tgt_bone = last_target.get("bone_name") or ""
            label = tgt_obj
            if tgt_bone:
                label += f" > {tgt_bone}"
            box.label(text=f"Last target: {label}")

        # Actions ---------------------------------------------------------
        row = layout.row(align=True)
        row.operator("anim_assist.refresh_diagnostics", icon="FILE_REFRESH")
        draw_explainer_icon(row, context, "op.anim_assist.refresh_diagnostics")
        row.operator("anim_assist.copy_diagnostics", icon="COPYDOWN")
        draw_explainer_icon(row, context, "op.anim_assist.copy_diagnostics")