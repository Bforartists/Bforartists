"""BoneCraft VRM bridge — VRoid / VRM import and export for VTuber + VRChat.

This module is the *bridge*, not the I/O. We soft-depend on
``vrm-addon-for-blender`` (saturday06) for actual VRM read/write — five
years of upstream bug fixes that we'd be foolish to duplicate. BoneCraft
handles:

* Soft-detect whether the VRM Add-on is installed; offer to install if not.
* Run post-import passes (bone-name aliasing, viseme blendshape surface,
  spring-bone catalog, meta/license preservation).
* Provide per-target export presets that dispatch to the upstream exporter
  for VRM targets and to Blender's FBX exporter (VRChat-tuned) for FBX.
* Lint the active rig against each target's requirements before export.

See ``CHANGELOG_3.2.0.md`` for the design rationale (Brainstorm Council
session 2026-04-25, Team D — The Stress Lab).
"""

import bpy

from . import (bridge, importer, exporter, lint, ui, springbone_convert,
               vroid_morph_map, vroid_project)


_classes = (
    importer.BF_OT_VRMImport,
    importer.BF_OT_VRoidImport,
    vroid_project.BF_OT_VRoidOpenInStudio,
    vroid_project.BF_OT_VRoidClearProject,
    exporter.BF_OT_VRMExport,
    lint.BF_OT_VRMLint,
    lint.BF_OT_VRMFixHumanoidAliases,
    bridge.BF_OT_InstallVRMAddon,
    bridge.BF_OT_VRMInstallFromDisk,
    bridge.BF_OT_VRMOpenWebsite,
    bridge.BF_OT_VRMInstallAuto,
    springbone_convert.BF_OT_VRMConvertSpringBones,
    vroid_morph_map.BF_OT_VRoidMapVisemes,
    ui.BF_VRMSettings,
    ui.BONEFORGE_PT_vrm,
)


def register():
    """Register VRM bridge classes and the scene settings pointer."""
    vroid_project.register_previews()
    for cls in _classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError:
            # Already registered (reload). Re-registration is idempotent.
            pass
    bpy.types.Scene.boneforge_vrm_settings = bpy.props.PointerProperty(
        type=ui.BF_VRMSettings
    )


def unregister():
    """Unregister in reverse order; tolerate missing classes on reload."""
    vroid_project.unregister_previews()
    if hasattr(bpy.types.Scene, "boneforge_vrm_settings"):
        del bpy.types.Scene.boneforge_vrm_settings
    for cls in reversed(_classes):
        try:
            bpy.utils.unregister_class(cls)
        except (RuntimeError, ValueError):
            pass

# ── v3.3.0 Tool Registry ────────────────────────────────────────

def _get_manifest():
    """Return this phase's :class:`ToolManifest`.

    Lazy-imported because the registry module lives under
    ``boneforge.core`` and we want to avoid an eager dependency cycle
    if this phase is imported before ``boneforge.core``.
    """
    from boneforge.core.tool_registry import ToolManifest
    return ToolManifest(
        id='vrm_bridge',
        name='VRM / VRoid Bridge',
        description='Import/export VRM files for VTuber and VRChat workflows. Soft-depends on vrm-addon-for-blender.',
        icon='WORLD',
        default_enabled=True,
        # v3.3.15: declares the structural panel-parent dependency on
        # io_hub (BONEFORGE_PT_vrm uses bl_parent_id="BF_PT_sb_io").
        # The Tool Registry refuses to disable io_hub while this is enabled.
        depends_on=("io_hub",),
        register_fn=register,
        unregister_fn=unregister,
    )
