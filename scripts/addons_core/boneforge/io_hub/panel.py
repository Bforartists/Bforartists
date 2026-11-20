"""IO Hub sidebar panel (BF_PT_sb_io).

The single home for every BoneCraft format-bridge UI. Renders:

* A status section listing every known bridge (VRM, MMD, …) with an
  icon, the dep's name, and a status indicator.
* For active bridges: a [✓ Active] indicator and a hint that the
  bridge's full sub-panel is below.
* For inactive bridges: per-bridge [Install] buttons (auto-download,
  install from disk, open website) plus a top-level [Install All
  Format Bridges] button when more than one is missing.

The bridges' main panels (BONEFORGE_PT_vrm, BONEFORGE_PT_mmd, etc.)
are children of this hub via ``bl_parent_id = "BF_PT_sb_io"``. Each
child polls on its own dep being available, so when a dep is missing
the child panel hides and the user only sees the install row in this
hub. When the dep is detected, the child panel appears with the full
import / export UI.
"""

from __future__ import annotations

import bpy
from bpy.types import Panel

from . import bridges
from boneforge.i18n import T


def _draw_bridge_inline(box, b, context):
    """Draw full bridge UI inline inside an active bridge's box."""
    bridge_id = b["id"]

    if bridge_id == "vrm":
        try:
            from boneforge.vrm.ui import draw_panel_content
            draw_panel_content(box, context)
        except Exception:
            box.label(text=T("VRM panel unavailable"), icon="ERROR")

    elif bridge_id == "mmd":
        try:
            from boneforge.mmd.ui import draw_panel_content
            draw_panel_content(box, context)
        except Exception:
            box.label(text=T("MMD ops unavailable"), icon="INFO")


class BF_PT_sb_io(Panel):
    """CATS -> Import / Export hub: format bridges and install paths."""

    bl_label       = " "
    bl_idname      = "BF_PT_sb_io"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "CATS"
    bl_order       = 50      # last section in the CATS tab, after VRChat (35)
    bl_options     = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Import / Export"))

    @classmethod
    def poll(cls, context):
        try:
            prefs = context.preferences.addons["boneforge"].preferences
            if not prefs.show_tab_cats:
                return False
        except Exception:
            pass
        return True

    def draw(self, context):
        layout = self.layout

        # ── Status section ──────────────────────────────────────
        active_count = len(bridges.all_active_ids())
        inactive_bridges = bridges.all_inactive_bridges()
        total = len(bridges.KNOWN_BRIDGES)

        header = layout.row(align=True)
        if total == 0:
            header.label(text=T("No format bridges declared."), icon="INFO")
            return

        header.label(
            text=f"Format Bridges  ({active_count}/{total} active)",
        )

        # ── Per-bridge rows ─────────────────────────────────────
        for b in bridges.KNOWN_BRIDGES:
            box = layout.box()
            row = box.row(align=True)
            is_active = bridges.is_bridge_active(b["id"])

            row.label(
                text=b["name"],
                icon=b["icon"],
            )
            if is_active:
                row.label(text=T("✓ Active"), icon="CHECKMARK")
                _draw_bridge_inline(box, b, context)
            else:
                row.label(text=f"needs {b['dep_label']}", icon="ERROR")

            if not is_active:
                col = box.column(align=True)
                col.operator(
                    b["auto_install_op"],
                    text=T("Auto-Install Latest from GitHub"),
                    icon="URL",
                )
                sub = col.row(align=True)
                sub.operator(
                    b["manual_op"],
                    text=T("Open Add-on Preferences"),
                    icon="PREFERENCES",
                )
                if b.get("website_op"):
                    op = sub.operator(
                        b["website_op"],
                        text=T("Website"),
                        icon="WORLD",
                    )
                    if hasattr(op, "target"):
                        op.target = "EXTENSIONS"
                # v3.3.13: manual install instructions fallback
                op_inst = col.operator(
                    "boneforge.io_show_manual_install_instructions",
                    text=T("Show Manual Instructions"),
                    icon="QUESTION",
                )
                op_inst.bridge_id = b["id"]

        # ── Install All ─────────────────────────────────────────
        if len(inactive_bridges) >= 2:
            layout.separator()
            row = layout.row(align=True)
            row.scale_y = 1.3
            row.operator(
                "boneforge.io_install_all_bridges",
                text=f"Install All ({len(inactive_bridges)} missing)",
                icon='PLUGIN',
            )

        # ── Game Engine Export ──────────────────────────────────────
        layout.separator()
        layout.label(text=T("Game Engine Export"))

        unity_box = layout.box()
        unity_box.label(text=T("Unity / VRChat"))
        try:
            from boneforge.vrchat.export.vrchat_export import draw_export_settings
            draw_export_settings(unity_box, context)
            ucol = unity_box.column(align=True)
            ucol.scale_y = 1.1
            ucol.operator(
                "boneforge.vrc_export_to_unity",
                text=T("Export to VRChat (Unity)"),
                icon='EXPORT',
            )
            ucol.operator(
                "boneforge.vrc_calculate_rank",
                text=T("Check Performance Rank"),
                icon='FILE_REFRESH',
            )
        except Exception:
            unity_box.label(text=T("Enable VRChat phase for Unity export"), icon='INFO')

        ue_box = layout.box()
        ue_box.label(text=T("Unreal Engine 5"))
        from boneforge.io_hub import game_export
        game_export.draw_unreal_export_settings(ue_box, context)
        ue_col = ue_box.column(align=True)
        ue_col.scale_y = 1.1
        settings = context.scene.boneforge_game_export_settings
        export_path = game_export.build_unreal_export_filepath(settings, context)
        ue_col.operator_context = 'EXEC_DEFAULT'
        op = ue_col.operator(
            "boneforge.export_unreal_fbx",
            text=T("Export to Unreal (FBX)"),
            icon='EXPORT',
        )
        op.filepath = export_path
        op.use_selection = settings.unreal_use_selection
        op.apply_unit_scale = settings.unreal_apply_unit_scale
        op.add_leaf_bones = settings.unreal_add_leaf_bones
        op.bake_anim = settings.unreal_bake_anim
        op.embed_textures = settings.unreal_embed_textures
        op.bone_naming = settings.bone_naming
        ue_col.operator_context = 'INVOKE_DEFAULT'
        ue_col.operator(
            "boneforge.import_unreal_fbx",
            text=T("Import from Unreal (FBX)"),
            icon='IMPORT',
        )

        # ── Footer ──────────────────────────────────────────────
        layout.separator()
        if active_count == 0:
            layout.label(
                text=T("No bridges active yet — install one above to get import / export buttons."),
                icon="INFO",
            )
        else:
            layout.label(
                text=T("Active bridges show their import/export buttons in their own sub-panels below."),
                icon="INFO",
            )


_classes = (BF_PT_sb_io,)


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
