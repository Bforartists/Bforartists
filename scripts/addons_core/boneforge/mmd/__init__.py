"""BoneCraft MMD bridge — PMX / PMD / VMD import and export.

This module is the *bridge*, not the I/O. We soft-depend on
``mmd_tools`` (UuuNyaa's actively-maintained fork of the canonical
PMX/PMD/VMD addon) for actual file read/write — years of upstream
development that we'd be foolish to duplicate. BoneCraft handles:

* Soft-detect whether mmd_tools is installed and enabled.
* Offer four install paths (auto-download from GitHub, install from
  disk, open Extensions page, manual prefs).
* Wrap mmd_tools' import / export operators with a BoneCraft sidebar
  panel so users don't have to hunt through Blender's File menu.

Same fix-pattern as the v3.2.0 VRM bridge.

Public ops (registered as boneforge.mmd_*):
* boneforge.mmd_import_pmx   — wraps mmd_tools.import_model
* boneforge.mmd_import_vmd   — wraps mmd_tools.import_vmd
* boneforge.mmd_export_pmx   — wraps mmd_tools.export_pmx
* boneforge.mmd_export_vmd   — wraps mmd_tools.export_vmd
* boneforge.mmd_install_*    — four install paths
"""

import bpy

from . import bridge, importer, exporter, ui, bone_names, physics_convert


_classes = (
    importer.BF_OT_MMDImportPMX,
    importer.BF_OT_MMDImportVMD,
    importer.BF_OT_MMDImportVPD,
    exporter.BF_OT_MMDExportPMX,
    exporter.BF_OT_MMDExportVMD,
    exporter.BF_OT_MMDExportVPD,
    bridge.BF_OT_InstallMMDAddon,
    bridge.BF_OT_MMDInstallFromDisk,
    bridge.BF_OT_MMDOpenWebsite,
    bridge.BF_OT_MMDInstallAuto,
    bone_names.BF_OT_MMDConvertBoneNames,
    physics_convert.BF_OT_MMDConvertPhysics,
    ui.BF_MMDSettings,
    ui.BONEFORGE_PT_mmd,
)


def register():
    """Register MMD bridge classes."""
    for cls in _classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError:
            pass
    if not hasattr(bpy.types.Scene, "boneforge_mmd_settings"):
        bpy.types.Scene.boneforge_mmd_settings = bpy.props.PointerProperty(
            type=ui.BF_MMDSettings
        )


def unregister():
    """Unregister in reverse order; tolerate missing classes on reload."""
    if hasattr(bpy.types.Scene, "boneforge_mmd_settings"):
        del bpy.types.Scene.boneforge_mmd_settings
    for cls in reversed(_classes):
        try:
            bpy.utils.unregister_class(cls)
        except (RuntimeError, ValueError):
            pass


# v3.3.0 Tool Registry manifest

def _get_manifest():
    """Return this phase's :class:`ToolManifest`."""
    from boneforge.core.tool_registry import ToolManifest
    return ToolManifest(
        id="mmd_bridge",
        name="MMD / PMX Bridge",
        description="Import/export PMX models and VMD motions for "
                    "MikuMikuDance / vocaloid / VTuber workflows. "
                    "Soft-depends on mmd_tools.",
        icon="OUTLINER_OB_ARMATURE",
        default_enabled=True,
        # v3.3.15: declares the structural panel-parent dependency on
        # io_hub (BONEFORGE_PT_mmd uses bl_parent_id="BF_PT_sb_io").
        # The Tool Registry refuses to disable io_hub while this is enabled.
        depends_on=("io_hub",),
        register_fn=register,
        unregister_fn=unregister,
    )
