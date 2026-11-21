# --- LIPSYNC LAYER PANELS (Phase 12 / v12.0.0) ---
"""Sidebar panel for the Phase 12 lipsync system.

v12 additions
-------------
- PREVIEW <-> SHIPPED mode toggle button
- Target dropdown (Shape Keys / Bones / Both)
- Mesh picker for shape key target
- Shape Key Wiring section (parallel to Rig Wiring)
- Explicit callout that the audio waveform is visible in the dope sheet
  (per the mythologist dissent - make the user's mental model visible)
"""

from __future__ import annotations

import bpy
from bpy.types import UIList

from .. import constants
from ..core import p12_audio_utils as au
from ..core import p12_properties as p12_props
from ..core import p12_session as session
from ..ui import ui_helpers as uh
from ..ui.editor_placement import View3DSidebarPanel
from ..ui.panel_anatomy import PanelAnatomyMixin


class ANIMASSIST_UL_p12_layer_links(UIList):
    bl_idname = "ANIMASSIST_UL_p12_layer_links"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        if item.mode == "PREVIEW":
            row.label(text="", icon="DRIVER")
        elif item.is_stale:
            row.label(text="", icon="ERROR")
        else:
            row.label(text="", icon="PLAY_SOUND")
        row.label(text=item.layer_name or "(unnamed)")
        sub = row.row(align=True)
        sub.scale_x = 0.6
        sub.label(text=item.target_kind)
        if item.audio_path:
            row.label(text=item.audio_path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1])
        if item.is_stale:
            row.label(text=constants.P12_STALE_SUFFIX)


class ANIMASSIST_UL_p12_visemes(UIList):
    bl_idname = "ANIMASSIST_UL_p12_visemes"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.label(text=item.viseme_name, icon="USER")
        sub = row.row(align=True)
        sub.enabled = False
        sub.label(text=("(builtin)" if item.is_builtin else "(captured)"))


class ANIMASSIST_UL_p12_shape_key_wiring(UIList):
    """v12: viseme -> shape_key wiring rows."""
    bl_idname = "ANIMASSIST_UL_p12_shape_key_wiring"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split(factor=0.4, align=True)
        split.label(text=item.viseme_name, icon="DOT")
        # Try to use prop_search against the wired mesh's shape keys.
        mesh = None
        p12 = p12_props.get_p12(context)
        if p12 and p12.layer_links and 0 <= p12.active_link_index < len(p12.layer_links):
            link = p12.layer_links[p12.active_link_index]
            if link.mesh_name:
                mesh = bpy.data.objects.get(link.mesh_name)
        if mesh is not None and mesh.type == "MESH" and mesh.data.shape_keys is not None:
            split.prop_search(item, "shape_key_name", mesh.data.shape_keys, "key_blocks", text="")
        else:
            split.prop(item, "shape_key_name", text="")


class ANIMASSIST_PT_p12_lipsync_v3d(PanelAnatomyMixin, View3DSidebarPanel):
    bl_idname = "ANIMASSIST_PT_p12_lipsync_v3d"
    bl_label = "Lipsync"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        return p12_props.get_p12(context) is not None

    def draw(self, context):
        layout = self.layout
        p12 = p12_props.get_p12(context)
        if p12 is None:
            layout.label(text="Lipsync system unavailable", icon="ERROR")
            return

        layout.prop(p12, "enabled", text="Enable Lipsync", toggle=False)
        if not p12.enabled:
            layout.label(text="Lipsync system disabled", icon="INFO")
            return

        # ----- Layer links list -----
        uh.separator(layout)
        layout.label(text="Lipsync Layers", icon="RENDERLAYERS")
        row = layout.row()
        row.template_list(
            "ANIMASSIST_UL_p12_layer_links", "v3d",
            p12, "layer_links", p12, "active_link_index",
            rows=2, maxrows=4,
        )
        col = row.column(align=True)
        col.operator("animassist.p12_setup_lipsync", text="", icon="ADD")
        col.separator()
        active_layer_name = ""
        if 0 <= p12.active_link_index < len(p12.layer_links):
            active_layer_name = p12.layer_links[p12.active_link_index].layer_name
        op_refresh = col.operator("animassist.p12_refresh_audio_hash", text="", icon="FILE_REFRESH")
        op_refresh.layer_name = active_layer_name

        if not p12.layer_links:
            layout.label(text="Add a lipsync layer with +", icon="INFO")

        if 0 <= p12.active_link_index < len(p12.layer_links):
            link = p12.layer_links[p12.active_link_index]
            box = layout.box()
            header = box.row(align=True)
            header.label(text=link.layer_name)
            mode_icon = "DRIVER" if link.mode == "PREVIEW" else "RENDER_ANIMATION"
            mode_btn = header.operator("animassist.p12_toggle_mode",
                                       text=("Live Preview" if link.mode == "PREVIEW" else "Baked"),
                                       icon=mode_icon)
            mode_btn.layer_name = link.layer_name

            box.prop(link, "audio_path", text="Audio")
            if not link.audio_path:
                box.label(text="Choose a WAV file", icon="INFO")
            elif not au.is_supported_audio(link.audio_path):
                box.label(text="Choose a .wav audio file", icon="ERROR")

            # Audio-in-dope-sheet callout (mythologist dissent)
            if link.speaker_strip_name:
                callout = box.row()
                callout.scale_y = 0.85
                callout.label(
                    text="Audio waveform shows in Dope Sheet/Timeline as a speaker overlay",
                    icon="SOUND",
                )

            row = box.row(align=True)
            row.prop(link, "target_kind", text="")
            row.prop(link, "viseme_library", text="")
            row = box.row(align=True)
            row.prop(link, "backend", text="")
            row.prop(link, "anticipation_frames", text="Antic.")
            box.prop(link, "frame_offset", text="Frame Offset")

            if link.target_kind in ("SHAPE_KEYS", "BOTH"):
                mesh_row = box.row(align=True)
                mesh_row.prop_search(link, "mesh_name", bpy.data, "objects", text="Mesh")
                mesh_row.operator("animassist.p12_pick_mesh", text="", icon="EYEDROPPER")

            if link.is_stale:
                row = box.row()
                row.alert = True
                row.label(text="Audio changed - rebake recommended", icon="ERROR")

            # Bake / clear / rebake buttons
            row = box.row(align=True)
            op_bake = row.operator("animassist.p12_bake_lipsync", text="Bake", icon="REC")
            op_bake.layer_name = link.layer_name
            op_clear = row.operator("animassist.p12_clear_auto_keys", text="Clear", icon="X")
            op_clear.layer_name = link.layer_name
            op_rebake = row.operator("animassist.p12_rebake", text="Rebake", icon="FILE_REFRESH")
            op_rebake.layer_name = link.layer_name

            row = box.row(align=True)
            op_mark = row.operator("animassist.p12_mark_manual", text="Lock Selected Keys", icon="LOCKED")
            op_mark.layer_name = link.layer_name

            # Cue table info
            cue_count = len(link.cue_table)
            sub = box.column(align=True)
            sub.scale_y = 0.85
            sub.label(text="Cue table: " + str(cue_count) + " cue(s)")

            record = session.get_last_bake(link.layer_name)
            if record is not None:
                sub.label(text="Last bake: " + str(record.keys_written) + " keys / "
                          + str(record.bones_touched) + " bones")
                if record.fallback_used:
                    sub.label(text="Fallback: " + record.fallback_reason, icon="INFO")

        # ----- Shape Key Wiring (v12) -----
        uh.separator(layout)
        header = layout.row(align=True)
        header.label(text="Shape Key Wiring", icon="SHAPEKEY_DATA")
        active_lib = "CARTOON_5"
        if 0 <= p12.active_link_index < len(p12.layer_links):
            active_lib = p12.layer_links[p12.active_link_index].viseme_library
        op_sk_fill = header.operator("animassist.p12_autofill_shape_key_wiring",
                                     text="Autofill", icon="FILE_REFRESH")
        op_sk_fill.library_id = active_lib

        if p12.shape_key_wiring:
            layout.template_list(
                "ANIMASSIST_UL_p12_shape_key_wiring", "v3d",
                p12, "shape_key_wiring", p12, "active_shape_key_index",
                rows=3, maxrows=8,
            )
        else:
            layout.label(text="No shape key wiring - run Autofill", icon="INFO")

        # ----- Bone Rig Wiring (v11) -----
        uh.separator(layout)
        header = layout.row(align=True)
        header.label(text="Bone Rig Wiring", icon="BONE_DATA")
        op_fill = header.operator("animassist.p12_autofill_wiring", text="Autofill", icon="OUTLINER_OB_ARMATURE")
        op_fill.library_id = active_lib

        wiring_col = layout.column(align=True)
        for entry in p12.rig_wiring:
            row = wiring_col.row(align=True)
            row.label(text=entry.role, icon="DOT")
            arm = context.active_object
            if arm is not None and arm.type == "ARMATURE":
                row.prop_search(entry, "bone_name", arm.data, "bones", text="")
            else:
                row.prop(entry, "bone_name", text="")
        if not p12.rig_wiring:
            layout.label(text="No bone wiring - run Autofill or Setup", icon="INFO")

        # ----- Viseme captures (v11) -----
        uh.separator(layout)
        header = layout.row(align=True)
        header.label(text="Viseme Captures", icon="USER")
        header.operator("animassist.p12_capture_viseme", text="Capture", icon="ADD")
        if p12.viseme_poses:
            layout.template_list(
                "ANIMASSIST_UL_p12_visemes", "v3d",
                p12, "viseme_poses", p12, "active_viseme_index",
                rows=2, maxrows=4,
            )

        # ----- Settings -----
        uh.separator(layout)
        col = layout.column(align=True)
        col.prop(p12, "show_manual_overrides", text="Highlight Manual Keys")
        col.prop(p12, "warn_on_render_in_preview", text="Warn If Rendering In PREVIEW")
        col.prop(p12, "amplitude_jaw_scale", text="Jaw Scale")
        col.prop(p12, "rhubarb_path", text="Rhubarb Path")


CLASSES: tuple[type, ...] = (
    ANIMASSIST_UL_p12_layer_links,
    ANIMASSIST_UL_p12_visemes,
    ANIMASSIST_UL_p12_shape_key_wiring,
    ANIMASSIST_PT_p12_lipsync_v3d,
)
