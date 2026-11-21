"""BoneCraft IO Hub — single home for format bridges (VRM / MMD / …).

Aggregates the BoneCraft-bridge UIs for every external-addon-backed
import/export format under one collapsible sidebar section. Each
bridge's full panel becomes a child of this hub; the hub itself
renders status + install buttons for missing dependencies, plus an
Install All shortcut for the common "fresh install" case.

v3.3.12: this hub replaces the previous design where each format
bridge (VRM, MMD) was its own top-level sidebar panel. Consolidation
makes "where do I import a PMX from?" easier to answer — it's all
under Import / Export.
"""

from . import bridges, game_export, installer, instructions, panel, profile_export


def register():
    """Register hub panel + Install All operator + instructions dialog."""
    game_export.register()
    panel.register()
    profile_export.register()
    installer.register()
    instructions.register()


def unregister():
    """Unregister in reverse order."""
    instructions.unregister()
    installer.unregister()
    profile_export.unregister()
    panel.unregister()
    game_export.unregister()


# v3.3.0 Tool Registry manifest

def _get_manifest():
    """Return the IO hub's :class:`ToolManifest`."""
    from boneforge.core.tool_registry import ToolManifest
    return ToolManifest(
        id="io_hub",
        name="Import / Export Hub",
        description="Consolidated home for format bridges (VRM, MMD, "
                    "and any future formats). Hosts install buttons, "
                    "active-bridge status, and per-bridge sub-panels.",
        icon="FILE_FOLDER",
        default_enabled=True,
        register_fn=register,
        unregister_fn=unregister,
    )
