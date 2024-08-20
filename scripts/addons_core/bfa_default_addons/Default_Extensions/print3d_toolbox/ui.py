# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2013-2022 Campbell Barton
# SPDX-FileContributor: Mikhail Rachinskiy


import bmesh
from bpy.types import Panel

from . import report


class Sidebar:
    bl_category = "3D Print"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == "MESH" and obj.mode in {"OBJECT", "EDIT"}


class VIEW3D_PT_print3d_analyze(Sidebar, Panel):
    bl_label = "Analyze"

    _type_to_icon = {
        bmesh.types.BMVert: "VERTEXSEL",
        bmesh.types.BMEdge: "EDGESEL",
        bmesh.types.BMFace: "FACESEL",
    }

    def draw_report(self, context):
        layout = self.layout
        info = report.info()

        if info:
            is_edit = context.edit_object is not None

            row = layout.row()
            row.label(text="Result")
            row.operator("wm.print3d_report_clear", text="", icon="X")

            box = layout.box()
            col = box.column()

            for i, (text, data) in enumerate(info):
                if is_edit and data and data[1]:
                    bm_type, _bm_array = data
                    col.operator("mesh.print3d_select_report", text=text, icon=self._type_to_icon[bm_type],).index = i
                else:
                    col.label(text=text)

    def draw(self, context):
        layout = self.layout

        print_3d = context.scene.print_3d

        # TODO, presets

        layout.label(text="Statistics")
        row = layout.row(align=True)
        row.operator("mesh.print3d_info_volume", text="Volume")
        row.operator("mesh.print3d_info_area", text="Area")

        layout.label(text="Checks")
        col = layout.column(align=True)
        col.operator("mesh.print3d_check_solid", text="Solid")
        col.operator("mesh.print3d_check_intersect", text="Intersections")
        row = col.row(align=True)
        row.operator("mesh.print3d_check_degenerate", text="Degenerate")
        row.prop(print_3d, "threshold_zero", text="")
        row = col.row(align=True)
        row.operator("mesh.print3d_check_distort", text="Distorted")
        row.prop(print_3d, "angle_distort", text="")
        row = col.row(align=True)
        row.operator("mesh.print3d_check_thick", text="Thickness")
        row.prop(print_3d, "thickness_min", text="")
        row = col.row(align=True)
        row.operator("mesh.print3d_check_sharp", text="Edge Sharp")
        row.prop(print_3d, "angle_sharp", text="")
        row = col.row(align=True)
        row.operator("mesh.print3d_check_overhang", text="Overhang")
        row.prop(print_3d, "angle_overhang", text="")
        layout.operator("mesh.print3d_check_all", text="Check All")

        self.draw_report(context)


class VIEW3D_PT_print3d_cleanup(Sidebar, Panel):
    bl_label = "Clean Up"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        layout.operator("mesh.print3d_clean_distorted", text="Distorted")
        layout.operator("mesh.print3d_clean_non_manifold", text="Make Manifold")


class VIEW3D_PT_print3d_edit(Sidebar, Panel):
    bl_label = "Edit"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        layout.operator("mesh.print3d_hollow")
        layout.operator("object.print3d_align_xy")

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

        props = context.scene.print_3d

        layout.prop(props, "export_path", text="")
        layout.prop(props, "export_format")

        layout.operator("io.print3d_export", text="Export", icon="EXPORT")


class VIEW3D_PT_print3d_export_options(Sidebar, Panel):
    bl_label = "Options"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = "VIEW3D_PT_print3d_export"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        props = context.scene.print_3d

        col = layout.column(heading="General")
        sub = col.column()
        sub.active = props.export_format != "OBJ"
        sub.prop(props, "use_ascii_format")
        col.prop(props, "use_scene_scale")

        col = layout.column(heading="Geometry")
        col.active = props.export_format != "STL"
        col.prop(props, "use_uv")
        col.prop(props, "use_normals", text="Normals")
        col.prop(props, "use_colors", text="Colors")

        col = layout.column(heading="Materials")
        col.prop(props, "use_copy_textures")
