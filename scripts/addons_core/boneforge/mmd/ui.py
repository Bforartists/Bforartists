"""Sidebar panel for the BoneCraft MMD bridge."""

from __future__ import annotations

from bpy.props import EnumProperty, StringProperty
from bpy.types import Panel, PropertyGroup

from . import bridge, exporter
from boneforge.i18n import T


class BF_MMDSettings(PropertyGroup):
    export_path: StringProperty(
        name="Export Folder",
        description="Folder for PMX/VMD/VPD exports",
        subtype="DIR_PATH",
        default="//",
    )
    pmx_export_name: StringProperty(
        name="PMX File",
        description="PMX model export file name",
        default="model",
    )
    vmd_export_name: StringProperty(
        name="VMD File",
        description="VMD motion export file name",
        default="motion",
    )
    vpd_export_name: StringProperty(
        name="VPD File",
        description="VPD pose export file name",
        default="pose",
    )
    pmx_scope: EnumProperty(
        name="PMX Scope",
        items=exporter.SCOPE_ITEMS,
        default="ACTIVE",
    )
    vmd_scope: EnumProperty(
        name="VMD Scope",
        items=exporter.SCOPE_ITEMS,
        default="ACTIVE",
    )
    vpd_scope: EnumProperty(
        name="VPD Scope",
        items=exporter.SCOPE_ITEMS,
        default="ACTIVE",
    )


def _active_export_name(context, fallback):
    obj = context.active_object
    return obj.name if obj is not None else fallback


def _draw_mmd_export_button(row, op_id, text, icon, filepath, scope):
    row.operator_context = "EXEC_DEFAULT"
    op = row.operator(op_id, text=text, icon=icon)
    op.filepath = filepath
    op.scope = scope


def draw_panel_content(layout, context):
    status = bridge.mmd_addon_status()
    settings = getattr(context.scene, "boneforge_mmd_settings", None)

    box = layout.box()
    if status["enabled"] and status["import_pmx_available"]:
        ver = status.get("version") or ()
        ver_text = ".".join(str(n) for n in ver) if ver else "unknown"
        box.label(text=f"mmd_tools: enabled (v{ver_text})", icon="CHECKMARK")
    elif status["installed"] and not status["enabled"]:
        box.label(text=T("mmd_tools: installed but disabled"), icon="ERROR")
        box.operator(
            "boneforge.install_mmd_addon",
            text=T("Open Add-on Preferences"),
            icon="PREFERENCES",
        )
    else:
        box.label(text=T("mmd_tools: not installed"), icon="ERROR")
        box.label(text=T("Pick how you'd like to install it:"), icon="INFO")
        col = box.column(align=True)
        col.operator(
            "boneforge.mmd_install_auto",
            text=T("Auto-Install Latest from GitHub"),
            icon="URL",
        )
        col.operator(
            "boneforge.mmd_install_from_disk",
            text=T("Install from .zip on Disk..."),
            icon="FILE_FOLDER",
        )
        row = col.row(align=True)
        op_ext = row.operator(
            "boneforge.mmd_open_website",
            text=T("Open Extensions Page"),
            icon='URL',
        )
        op_ext.target = "EXTENSIONS"
        op_gh = row.operator(
            "boneforge.mmd_open_website",
            text=T("GitHub"),
            icon="URL",
        )
        op_gh.target = "GITHUB"
        box.separator()
        box.operator(
            "boneforge.install_mmd_addon",
            text=T("Open Add-on Preferences (manual)"),
            icon="PREFERENCES",
        )
        box.label(text=T("Required for .pmx / .pmd / .vmd I/O"), icon="INFO")

    layout.separator()

    col = layout.column(align=True)
    col.label(text=T("Import:"))
    row = col.row(align=True)
    row.enabled = status["import_pmx_available"]
    row.operator("boneforge.mmd_import_pmx", text=T("Import PMX / PMD..."), icon="IMPORT")
    row = col.row(align=True)
    row.enabled = status["import_vmd_available"]
    row.operator("boneforge.mmd_import_vmd", text=T("Import VMD Motion..."), icon="ANIM")
    row = col.row(align=True)
    row.enabled = status["import_vpd_available"]
    row.operator("boneforge.mmd_import_vpd", text=T("Import VPD Pose..."), icon="POSE_HLT")

    layout.separator()

    col = layout.column(align=True)
    col.label(text=T("Export:"))
    if settings is None:
        col.label(text=T("MMD export settings unavailable"), icon="ERROR")
    else:
        col.prop(settings, "export_path", text=T("Folder"))

        pmx_path = exporter.build_export_filepath(
            settings.export_path,
            settings.pmx_export_name,
            ".pmx",
            _active_export_name(context, "model"),
        )
        vmd_path = exporter.build_export_filepath(
            settings.export_path,
            settings.vmd_export_name,
            ".vmd",
            _active_export_name(context, "motion"),
        )
        vpd_path = exporter.build_export_filepath(
            settings.export_path,
            settings.vpd_export_name,
            ".vpd",
            _active_export_name(context, "pose"),
        )

        col.prop(settings, "pmx_export_name", text=T("PMX File"))
        col.prop(settings, "pmx_scope", text=T("PMX Scope"))
        row = col.row(align=True)
        row.enabled = status["export_pmx_available"] and bool(pmx_path)
        _draw_mmd_export_button(
            row, "boneforge.mmd_export_pmx", T("Export PMX..."),
            "EXPORT", pmx_path, settings.pmx_scope,
        )

        col.prop(settings, "vmd_export_name", text=T("VMD File"))
        col.prop(settings, "vmd_scope", text=T("VMD Scope"))
        row = col.row(align=True)
        row.enabled = status["export_vmd_available"] and bool(vmd_path)
        _draw_mmd_export_button(
            row, "boneforge.mmd_export_vmd", T("Export VMD Motion..."),
            "ANIM_DATA", vmd_path, settings.vmd_scope,
        )

        col.prop(settings, "vpd_export_name", text=T("VPD File"))
        col.prop(settings, "vpd_scope", text=T("VPD Scope"))
        row = col.row(align=True)
        row.enabled = status["export_vpd_available"] and bool(vpd_path)
        _draw_mmd_export_button(
            row, "boneforge.mmd_export_vpd", T("Export VPD Pose..."),
            "POSE_HLT", vpd_path, settings.vpd_scope,
        )

        if not (pmx_path or vmd_path or vpd_path):
            col.label(text=T("Save the .blend or choose an export folder"), icon="INFO")

    layout.separator()

    assist = layout.box()
    assist.label(text=T("BoneCraft Assist"))
    col = assist.column(align=True)
    col.scale_y = 0.95
    col.operator(
        "boneforge.mmd_convert_bone_names",
        text=T("Convert Bone Names -> Unity"),
        icon='SORTALPHA',
    )
    col.operator(
        "boneforge.mmd_convert_physics",
        text=T("Convert Physics -> PhysBones"),
        icon="RIGID_BODY",
    )
    assist.label(text=T("Tip: run Bone Names first, then Physics"), icon="INFO")


class BONEFORGE_PT_mmd(Panel):
    """BoneCraft MMD bridge panel; rendered inline by the IO hub."""

    bl_label = " "
    bl_idname = "BONEFORGE_PT_mmd"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CATS"
    bl_parent_id = "BF_PT_sb_io"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        self.layout.label(text=T("MMD / PMX"))

    @classmethod
    def poll(cls, context):
        return False

    def draw(self, context):
        draw_panel_content(self.layout, context)
