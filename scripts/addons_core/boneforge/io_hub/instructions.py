"""Manual install instructions dialog.

Surfaces when auto-install + auto-repackage both fail. Shows the user
exactly what to do: open the website, download the right release zip
manually, install via Blender's Preferences → Add-ons → Install from
Disk. Also covers the Blender 4.2+ Extensions case where the addon
should be installed via Edit → Preferences → Get Extensions instead
of the legacy Install from Disk path.

Triggered from any bridge's "still failing?" recovery button — the
operator takes a ``bridge_id`` so the dialog tailors its links
(VRM → vrm-addon repo, MMD → mmd_tools repo, etc.).
"""

from __future__ import annotations

import logging

import bpy
from bpy.props import StringProperty
from bpy.types import Operator

from . import bridges
from boneforge.i18n import T

logger = logging.getLogger(__name__)


class BF_OT_ShowManualInstallInstructions(Operator):
    """Show step-by-step manual install instructions."""

    bl_idname = "boneforge.io_show_manual_install_instructions"
    bl_label = "Manual Install Instructions"
    bl_description = (
        "Show the exact steps to install the format addon manually "
        "if auto-install fails. Useful when the release zip needs "
        "the Blender 4.2+ Extensions installer instead of the legacy "
        "Install from Disk path"
    )
    bl_options = {"REGISTER"}

    bridge_id: StringProperty(
        name="Bridge ID",
        description="Which format bridge's instructions to show",
        default="",
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=520)

    def draw(self, context):
        layout = self.layout

        bridge = next(
            (b for b in bridges.KNOWN_BRIDGES if b["id"] == self.bridge_id),
            None,
        )
        if bridge is None:
            layout.label(
                text=f"Unknown bridge id: {self.bridge_id}",
                icon="ERROR",
            )
            return

        layout.label(
            text=f"Manual install for {bridge['name']} ({bridge['dep_label']})",
            icon="INFO",
        )
        layout.separator()

        # Path A: Blender 4.2+ Extensions
        box = layout.box()
        box.label(
            text=T("Option A — Blender 4.2+ Extensions (recommended for modern Blender):"),
            icon="PLUGIN" if bpy.app.version >= (4, 2, 0) else "INFO",
        )
        col = box.column(align=True)
        col.scale_y = 0.8
        col.label(text=T("1. Edit → Preferences → Get Extensions"))
        col.label(text=f"2. Search for: {bridge['dep_label'].split('_')[0]}")
        col.label(text=T("3. Click Install on the official extension"))
        col.label(text=T("4. Close preferences; BoneCraft auto-detects."))

        layout.separator()

        # Path B: Legacy Add-ons → Install from Disk
        box = layout.box()
        box.label(
            text=T("Option B — Legacy Install from Disk (Blender 3.x or older 4.x):"),
        )
        col = box.column(align=True)
        col.scale_y = 0.8
        col.label(text=T("1. Click 'Open GitHub' below to reach the releases page."))
        col.label(text=T("2. Download the release zip with the addon-style structure"))
        col.label(text="   (i.e. one named e.g. 'mmd_tools-X.Y.Z.zip', NOT 'Source")
        col.label(text="   code (zip)' — the source-code one is flat and won't install).")
        col.label(text=T("3. In Blender: Edit → Preferences → Add-ons → Install from Disk"))
        col.label(text=T("4. Pick the downloaded zip; tick the enable checkbox."))

        layout.separator()

        row = layout.row(align=True)
        if bridge.get("website_op"):
            op = row.operator(
                bridge["website_op"],
                text=T("Open Extensions Page"),
                icon="WORLD",
            )
            if hasattr(op, "target"):
                op.target = "EXTENSIONS"
            op2 = row.operator(
                bridge["website_op"],
                text=T("Open GitHub"),
                icon="URL",
            )
            if hasattr(op2, "target"):
                op2.target = "GITHUB"
        row.operator(
            bridge["manual_op"],
            text=T("Open Add-on Preferences"),
            icon="PREFERENCES",
        )

        layout.separator()
        layout.label(
            text="If you've installed the addon manually, BoneCraft "
                 "will auto-detect it on next sidebar redraw.",
            icon="INFO",
        )

    def execute(self, context):
        return {"FINISHED"}


_classes = (BF_OT_ShowManualInstallInstructions,)


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
