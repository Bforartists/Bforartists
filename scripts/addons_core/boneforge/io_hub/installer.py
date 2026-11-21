"""Install All operator — batch-install every missing format-bridge dep.

Iterates the registry of known format bridges, identifies which have
missing external deps, and fires each bridge's auto-install operator
in sequence. Each install op already has its own confirm dialog +
download progress, so this is a sequential dispatch — not a single
mega-install.

Reports a one-line summary at the end (how many succeeded, how many
the user cancelled, how many errored).
"""

from __future__ import annotations

import logging

import bpy
from bpy.types import Operator

from . import bridges
from boneforge.i18n import T

logger = logging.getLogger(__name__)


class BF_OT_InstallAllBridges(Operator):
    """Install every missing format-bridge dependency in sequence."""

    bl_idname = "boneforge.io_install_all_bridges"
    bl_label = "Install All Format Bridges"
    bl_description = (
        "Find every BoneCraft format bridge with a missing external "
        "dependency (VRM, MMD, etc.) and run each one's auto-installer "
        "in sequence. Each install shows its own confirm dialog before "
        "downloading"
    )
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return bool(bridges.all_inactive_bridges())

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def draw(self, context):
        layout = self.layout
        inactive = bridges.all_inactive_bridges()
        if not inactive:
            layout.label(
                text=T("All format bridges are already installed."),
                icon="CHECKMARK",
            )
            return
        layout.label(
            text=f"BoneCraft will install {len(inactive)} missing dependency:",
            icon='INFO',
        )
        for b in inactive:
            layout.label(
                text=f"  • {b['name']} ({b['dep_label']})",
                icon=b['icon'],
            )
        layout.label(
            text=T("Each install opens its own confirm dialog with the "
                 "source URL and download size."),
            icon="INFO",
        )

    def execute(self, context):
        inactive = bridges.all_inactive_bridges()
        if not inactive:
            self.report({"INFO"}, "All format bridges already installed.")
            return {"FINISHED"}

        succeeded = 0
        failed: list[tuple[str, str]] = []
        for b in inactive:
            op_path = b["auto_install_op"]
            try:
                module_name, op_name = op_path.split(".", 1)
                result = getattr(getattr(bpy.ops, module_name), op_name)("INVOKE_DEFAULT")
                if result in ({"FINISHED"}, {"RUNNING_MODAL"}):
                    succeeded += 1
                else:
                    failed.append((b["name"], "cancelled or no-op"))
            except (AttributeError, RuntimeError) as exc:
                logger.warning("[BoneCraft] Install All — %s: %s", b["name"], exc)
                failed.append((b["name"], str(exc)))

        for name, reason in failed:
            self.report({"WARNING"}, f"{name}: {reason}")
        self.report(
            {"INFO"},
            f"Install All — fired {succeeded} install dialog(s); "
            f"{len(failed)} could not start. Each install completes "
            "independently — watch their dialogs.",
        )
        return {"FINISHED"}


_classes = (BF_OT_InstallAllBridges,)


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
