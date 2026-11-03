# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2013-2022 Campbell Barton
# SPDX-FileCopyrightText: 2017-2026 Mikhail Rachinskiy

import bpy
from bpy.types import Menu, Object, Panel

from . import report


def _is_mesh(ob: Object) -> bool:
    return ob is not None and ob.type == "MESH"


# Menus
# ---------------------------


def draw_print3d_menu(self, context):
    layout = self.layout
    layout.separator()
    layout.menu("VIEW3D_MT_print3d")


class VIEW3D_MT_print3d(Menu):
    bl_label = "3D Print Toolbox"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = "INVOKE_DEFAULT"
        layout.operator("wm.call_panel", text="Analyze", text_ctxt="*", icon="WINDOW").name = "VIEW3D_PT_print3d_analyze"
        layout.separator()
        layout.operator("mesh.print3d_clean_non_manifold")
        layout.separator()
        layout.operator("mesh.print3d_hollow")
        if bpy.app.version >= (4, 5, 0):
            layout.operator("mesh.print3d_bisect")
        layout.operator("object.print3d_align_xy")
        layout.operator("mesh.print3d_scale_to_volume")
        layout.operator("mesh.print3d_scale_to_bounds")
        layout.separator()
        layout.operator("wm.call_panel", text="Export", text_ctxt="*", icon="WINDOW").name = "VIEW3D_PT_print3d_export"


# Panels
# ---------------------------


class Sidebar:
    bl_category = "3D Print"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    @classmethod
    def poll(cls, context):
        return context.mode in {"OBJECT", "EDIT_MESH"}

    def popover_header(self):
        if self.is_popover:
            layout = self.layout
            layout.emboss = "NONE"  # Changes text color to white
            layout.label(text=self.bl_label)
            layout.emboss = "NORMAL"
            layout.separator(type="LINE")


class VIEW3D_PT_print3d_analyze(Sidebar, Panel):
    bl_label = "Analyze"

    def draw_report(self, context):
        layout = self.layout
        data = report.get()

        if data:
            is_edit = context.edit_object is not None

            row = layout.row()
            row.label(text="Result")
            row.operator("wm.print3d_report_clear", text="", icon="X")

            row = layout.box().row()
            col1 = row.column()
            col2 = row.column()
            row.alignment = col1.alignment = col2.alignment = "LEFT"

            for i, item in enumerate(data):
                col1.label(text=item.name)
                if is_edit and item.indices:
                    col2.operator("mesh.print3d_select_report", text=item.value, icon=item.icon).index = i
                else:
                    col2.label(text=item.value)

    def draw(self, context):
        layout = self.layout
        layout.enabled = _is_mesh(context.object)

        self.popover_header()

        props = context.scene.print3d_toolbox

        layout.label(text="Statistics")

        row = layout.row(align=True)
        row.operator("mesh.print3d_info_volume", text="Volume")
        row.operator("mesh.print3d_info_area", text="Area")

        layout.label(text="Checks")

        col = layout.column(align=True)
        col.operator("mesh.print3d_check_solid")
        col.operator("mesh.print3d_check_intersect")
        if bpy.app.version >= (4, 3, 0):
            col.operator("mesh.print3d_check_shells")
        row = col.row(align=True)
        row.operator("mesh.print3d_check_degenerate")
        row.prop(props, "threshold_zero", text="")
        row = col.row(align=True)
        row.operator("mesh.print3d_check_nonplanar")
        row.prop(props, "angle_nonplanar", text="")
        row = col.row(align=True)
        row.operator("mesh.print3d_check_thick")
        row.prop(props, "thickness_min", text="")
        row = col.row(align=True)
        row.operator("mesh.print3d_check_sharp")
        row.prop(props, "angle_sharp", text="")
        row = col.row(align=True)
        row.operator("mesh.print3d_check_overhang")
        row.prop(props, "angle_overhang", text="")

        layout.operator("mesh.print3d_check_all")

        self.draw_report(context)


class VIEW3D_PT_print3d_cleanup(Sidebar, Panel):
    bl_label = "Clean Up"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        layout.operator("mesh.print3d_clean_non_manifold")


class VIEW3D_PT_print3d_edit(Sidebar, Panel):
    bl_label = "Edit"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        layout.enabled = context.object is not None

        col = layout.column(align=True)
        col.operator("mesh.print3d_hollow")
        if bpy.app.version >= (4, 5, 0):
            col.operator("mesh.print3d_bisect")
        sub = col.row(align=True)
        sub.enabled = _is_mesh(context.object)
        sub.operator("object.print3d_align_xy")

        layout.label(text="Scale To")
        row = layout.row(align=True)
        row.operator("mesh.print3d_scale_to_volume", text="Volume")
        row.operator("mesh.print3d_scale_to_bounds", text="Bounds")


class VIEW3D_PT_print3d_export(Sidebar, Panel):
    bl_label = "Export"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        self.popover_header()

        props = context.scene.print3d_toolbox

        layout.prop(props, "export_path", text="")
        layout.prop(props, "export_format")

        layout.operator("export_scene.print3d_export", icon="EXPORT")

        header, panel = layout.panel("options", default_closed=True)
        header.label(text="Options")
        if panel:
            col = panel.column()
            col.active = context.scene.unit_settings.system != "NONE"
            col.prop(props, "export_unit_scale")

            col = panel.column(heading="General")
            col.active = props.export_format != "OBJ"
            col.prop(props, "use_ascii_format")

            col = panel.column(heading="Geometry")
            col.active = props.export_format != "STL"
            col.prop(props, "use_uv")
            col.prop(props, "use_normals", text="Normals")
            col.prop(props, "use_colors", text="Colors")

            col = panel.column(heading="Materials")
            col.prop(props, "use_copy_textures")
