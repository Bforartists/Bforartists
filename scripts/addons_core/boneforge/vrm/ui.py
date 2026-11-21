"""Sidebar panel for the BoneCraft VRM bridge.

Layout, top to bottom:

    [Add-on status row]
        ✓ VRM Add-on detected (1.x.y)        OR        ⚠ Not installed
                                                       [Install / Enable]

    [Import]
        [Import VRM…]

    [Export]
        Target: <enum>
        [ ] Skip lint
        [Export…]

    [Lint]
        Target: <enum>
        [Lint Now]
        (most-recent results pretty-printed below)

    [Meta viewer]
        ▾ Author       : <name>
        ▾ License      : <name + URL>
        ▾ Spec         : VRM 1.0 / 0.x
        (collapsed by default)
"""

from __future__ import annotations

import bpy
from bpy.props import EnumProperty, BoolProperty, StringProperty, IntProperty
from bpy.types import Panel, PropertyGroup

from boneforge.core import active_armature

from . import bridge, exporter, meta as meta_mod
from boneforge.i18n import T


class BF_VRMSettings(PropertyGroup):
    export_target: EnumProperty(
        name="Export Target",
        items=[(tid, label, desc) for tid, label, desc in exporter.TARGETS],
        default="VRM_1_0",
    )
    lint_target: EnumProperty(
        name="Lint Target",
        items=[(tid, label, desc) for tid, label, desc in exporter.TARGETS],
        default="VRM_1_0",
    )
    skip_lint: BoolProperty(
        name="Skip Lint on Export",
        description="Bypass target-specific validation when exporting",
        default=False,
    )
    export_path: StringProperty(
        name="Export Folder",
        description="Folder for VRM/VRChat-FBX exports",
        subtype="DIR_PATH",
        default="//",
    )
    export_name: StringProperty(
        name="File Name",
        description="Export file name; extension is selected by target",
        default="Avatar",
    )
    export_scope: EnumProperty(
        name="Scope",
        description="Which armature(s) to export",
        items=exporter.SCOPE_ITEMS,
        default="ACTIVE",
    )
    show_meta: BoolProperty(
        name="Show Meta",
        default=False,
    )
    # ── VRoid project hand-off (8.5.3) ───────────────────────────
    # Populated when the user picks a .vroid in the VRoid importer.
    # BoneForge cannot convert the project payload, so these drive a
    # confirm-and-hand-off card instead of an import.
    vroid_project_path: StringProperty(
        name="VRoid Project",
        description="Last inspected .vroid project file",
        subtype="FILE_PATH",
        default="",
    )
    vroid_project_version: StringProperty(
        name="VRoid Studio Version",
        default="",
    )
    vroid_project_summary: StringProperty(
        name="Project Summary",
        default="",
    )
    vroid_thumbnail_icon: IntProperty(
        name="Thumbnail Icon ID",
        default=0,
    )
    vroid_last_folder: StringProperty(
        name="VRoid Folder",
        description="Folder the .vroid came from; VRoid Studio exports here by default",
        subtype="DIR_PATH",
        default="",
    )


def _draw_vroid_project_card(layout, settings):
    """Draw the hand-off card for an inspected ``.vroid`` project.

    Only appears once the user has picked a ``.vroid``. BoneCraft cannot
    convert the project payload, so the card confirms *which* avatar the
    file holds and puts VRoid Studio's Export → VRM one click away.
    """
    if settings is None or not settings.vroid_project_path:
        return

    box = layout.box()
    header = box.row()
    header.label(text=T("VRoid Studio Project"))
    header.operator(
        "boneforge.vroid_clear_project", text="", icon="X", emboss=False
    )

    if settings.vroid_thumbnail_icon:
        preview = box.row()
        preview.alignment = "CENTER"
        preview.template_icon(
            icon_value=settings.vroid_thumbnail_icon, scale=6.0
        )

    if settings.vroid_project_summary:
        box.label(text=settings.vroid_project_summary)
    if settings.vroid_project_version:
        box.label(
            text=T("Made with VRoid Studio ") + settings.vroid_project_version
        )

    note = box.column(align=True)
    note.label(
        text=T("BoneCraft cannot convert .vroid directly"), icon="INFO"
    )
    note.label(text=T("Export it to VRM in VRoid Studio, then import that"))

    box.operator(
        "boneforge.vroid_open_in_studio",
        text=T("Open in VRoid Studio"),
        icon='WINDOW',
    )
    follow = box.operator(
        "boneforge.vrm_import",
        text=T("Import Exported VRM…"),
        icon="IMPORT",
    )
    # Land the file browser in the project's folder — VRoid Studio
    # defaults its VRM export alongside the project.
    follow.filepath = settings.vroid_last_folder


def draw_panel_content(layout, context):
    """Draw the full VRM / VRoid UI.

    Called by the IO hub when VRM is active (inline, beneath the Active
    row) and by BONEFORGE_PT_vrm.draw() when used as a standalone panel.
    """
    settings = context.scene.boneforge_vrm_settings
    status = bridge.vrm_addon_status()
    arm = active_armature(context)

    # ── Add-on status ───────────────────────────────────────
    box = layout.box()
    if status["enabled"] and status["import_op_available"]:
        ver = status.get("version") or ()
        ver_text = ".".join(str(n) for n in ver) if ver else "unknown"
        box.label(
            text=f"VRM Add-on: enabled (v{ver_text})",
            icon="CHECKMARK",
        )
    elif status["installed"] and not status["enabled"]:
        box.label(text=T("VRM Add-on: installed but disabled"), icon="ERROR")
        box.operator(
            "boneforge.install_vrm_addon",
            text=T("Open Add-on Preferences"),
            icon="PREFERENCES",
        )
    else:
        box.label(text=T("VRM Add-on: not installed"), icon="ERROR")
        box.label(text=T("Pick how you'd like to install it:"), icon="INFO")
        col = box.column(align=True)
        col.operator(
            "boneforge.vrm_install_auto",
            text=T("Auto-Install Latest from GitHub"),
            icon="URL",
        )
        col.operator(
            "boneforge.vrm_install_from_disk",
            text=T("Install from .zip on Disk…"),
            icon="FILE_FOLDER",
        )
        row = col.row(align=True)
        op_ext = row.operator(
            "boneforge.vrm_open_website",
            text=T("Open Extensions Page"),
            icon='URL',
        )
        op_ext.target = "EXTENSIONS"
        op_gh = row.operator(
            "boneforge.vrm_open_website",
            text=T("GitHub"),
            icon="URL",
        )
        op_gh.target = "GITHUB"
        box.separator()
        box.operator(
            "boneforge.install_vrm_addon",
            text=T("Open Add-on Preferences (manual)"),
            icon="PREFERENCES",
        )
        box.label(text=T("Required for .vrm import / export"), icon="INFO")

    layout.separator()

    # ── Import ──────────────────────────────────────────────
    col = layout.column(align=True)
    col.label(text=T("Import:"))
    row = col.row()
    row.enabled = status["import_op_available"]
    row.operator("boneforge.vrm_import", text=T("Import VRM…"), icon="IMPORT")
    row = col.row()
    row.enabled = status["import_op_available"]
    row.operator(
        "boneforge.vroid_import",
        text=T("Import VRoid (.vroid / .zip)…"),
        icon="PACKAGE",
    )

    _draw_vroid_project_card(layout, settings)

    layout.separator()

    # ── Export ──────────────────────────────────────────────
    col = layout.column(align=True)
    col.label(text=T("Export:"))
    col.prop(settings, "export_path", text=T("Folder"))
    col.prop(settings, "export_name", text=T("File"))
    col.prop(settings, "export_target", text=T("Target"))
    col.prop(settings, "export_scope", text=T("Scope"))
    col.prop(settings, "skip_lint")

    export_path = exporter.build_export_filepath(settings, arm)
    export_row = col.row()
    export_row.enabled = arm is not None and (
        settings.export_target == "VRCHAT_FBX"
        or status["export_op_available"]
    ) and bool(export_path)
    export_row.operator_context = 'EXEC_DEFAULT'
    op = export_row.operator(
        "boneforge.vrm_export",
        text=T("Export…"),
        icon="EXPORT",
    )
    op.filepath = export_path
    op.target = settings.export_target
    op.skip_lint = settings.skip_lint
    op.scope = settings.export_scope
    if not export_path:
        col.label(text=T("Save the .blend or choose an export folder"), icon="INFO")

    layout.separator()

    # ── Lint ────────────────────────────────────────────────
    col = layout.column(align=True)
    col.label(text=T("Lint:"))
    col.prop(settings, "lint_target", text=T("Target"))
    row = col.row(align=True)
    op = row.operator("boneforge.vrm_lint", text=T("Lint Now"), icon="VIEWZOOM")
    op.target = settings.lint_target
    fix_op = row.operator(
        "boneforge.vrm_fix_humanoid_aliases",
        text=T("Fix Humanoid Map"),
        icon='SORTALPHA',
    )
    fix_op.target = settings.lint_target

    results = context.scene.get("boneforge_vrm_lint_results")
    if results:
        box = col.box()
        errors = [r for r in results if r["severity"] == "ERROR"]
        warns = [r for r in results if r["severity"] == "WARNING"]
        box.label(
            text=f"{len(errors)} error(s), {len(warns)} warning(s)",
            icon="INFO",
        )
        for r in (errors + warns)[:6]:
            row = box.row()
            row.label(
                text=r["message"],
                icon="ERROR" if r["severity"] == "ERROR" else "INFO",
            )
        if len(errors) + len(warns) > 6:
            box.label(text=f"… and {len(errors) + len(warns) - 6} more")

    layout.separator()

    # ── BoneForge Assist ────────────────────────────────────
    assist = layout.box()
    assist.label(text=T("BoneCraft Assist"))
    col = assist.column(align=True)
    col.scale_y = 0.95

    has_springs = (
        arm is not None and arm.get("boneforge_vrm_spring_groups") is not None
    )
    spring_row = col.row()
    spring_row.enabled = has_springs
    spring_row.operator(
        "boneforge.vrm_convert_springbones",
        text=T("Convert SpringBones → PhysBones"),
        icon="PHYSICS",
    )
    if not has_springs:
        assist.label(
            text=T("Import a VRM to enable SpringBone convert"),
            icon="INFO",
        )

    col.operator(
        "boneforge.vroid_map_visemes",
        text=T("Map VRoid Visemes"),
        icon="SHAPEKEY_DATA",
    )

    layout.separator()

    # ── Meta viewer ─────────────────────────────────────────
    if arm is not None:
        preserved = meta_mod.read_preserved_meta(arm)
        box = layout.box()
        row = box.row()
        row.prop(
            settings, "show_meta",
            icon="TRIA_DOWN" if settings.show_meta else "TRIA_RIGHT",
            text=T("VRM Meta"),
            emboss=False,
        )

        if settings.show_meta:
            if preserved is None:
                box.label(
                    text=T("No VRM meta preserved on this armature."),
                    icon="INFO",
                )
            else:
                spec = preserved.get("_vrm_spec", "?")
                box.label(text=f"Spec: VRM {spec}")
                title = (preserved.get("vrm_name")
                         or preserved.get("title")
                         or "(untitled)")
                box.label(text=f"Title: {title}")
                authors = preserved.get("authors") or preserved.get("author")
                if authors:
                    if isinstance(authors, list):
                        authors = ", ".join(str(a) for a in authors)
                    box.label(text=f"Author(s): {authors}")
                license_url = (preserved.get("license_url")
                               or preserved.get("other_license_url")
                               or preserved.get("license_name"))
                if license_url:
                    box.label(text=f"License: {license_url}")
                redistribution = preserved.get("allow_redistribution")
                if redistribution is not None:
                    box.label(
                        text=f"Redistribution allowed: {redistribution}",
                        icon="CHECKMARK" if redistribution else "X",
                    )


class BONEFORGE_PT_vrm(Panel):
    """BoneCraft VRM bridge panel — child of the Import / Export hub.

    v3.3.12: moved from top-level to a child of BF_PT_sb_io so the
    Import / Export hub is the single home for format bridges. The
    panel hides via poll() when the upstream vrm-addon-for-blender
    isn't installed — in that state the hub renders the install row
    instead, so users don't see a half-functional panel.
    """

    bl_label = " "
    bl_idname = "BONEFORGE_PT_vrm"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CATS"
    bl_parent_id = "BF_PT_sb_io"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        self.layout.label(text=T("VRM / VRoid"))

    @classmethod
    def poll(cls, context):
        # Suppressed: the IO hub now draws VRM content inline directly
        # beneath the "✓ Active" row, so the child panel is not needed.
        return False

    def draw(self, context):
        draw_panel_content(self.layout, context)
