# SPDX-FileCopyrightText: 2013-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

# Interface for this addon.


from bpy.types import Panel
import bmesh

from . import report


class View3DPrintPanel:
    bl_category = "3D-Print"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'MESH' and obj.mode in {'OBJECT', 'EDIT'}


class VIEW3D_PT_print3d_analyze(View3DPrintPanel, Panel):
    bl_label = "Analyze"

    _type_to_icon = {
        bmesh.types.BMVert: 'VERTEXSEL',
        bmesh.types.BMEdge: 'EDGESEL',
        bmesh.types.BMFace: 'FACESEL',
    }

    def draw_report(self, context):
        layout = self.layout
        info = report.info()

        if info:
            is_edit = context.edit_object is not None

            layout.label(text="Result")
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


class VIEW3D_PT_print3d_cleanup(View3DPrintPanel, Panel):
    bl_label = "Clean Up"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        print_3d = context.scene.print_3d

        row = layout.row(align=True)
        row.operator("mesh.print3d_clean_distorted", text="Distorted")
        row.prop(print_3d, "angle_distort", text="")
        layout.operator("mesh.print3d_clean_non_manifold", text="Make Manifold")
        # XXX TODO
        # layout.operator("mesh.print3d_clean_thin", text="Wall Thickness")


class VIEW3D_PT_print3d_transform(View3DPrintPanel, Panel):
    bl_label = "Transform"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        print_3d = context.scene.print_3d

        layout.label(text="Scale To")
        row = layout.row(align=True)
        row.operator("mesh.print3d_scale_to_volume", text="Volume")
        row.operator("mesh.print3d_scale_to_bounds", text="Bounds")
        row = layout.row(align=True)
        row.operator("mesh.print3d_align_to_xy", text="Align XY")
        row.prop(print_3d, "use_alignxy_face_area")


class VIEW3D_PT_print3d_export(View3DPrintPanel, Panel):
    bl_label = "Export"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        print_3d = context.scene.print_3d

        layout.prop(print_3d, "export_path", text="")
        layout.prop(print_3d, "export_format")

        col = layout.column()
        col.prop(print_3d, "use_apply_scale")
        col.prop(print_3d, "use_export_texture")
        sub = col.column()
        sub.active = print_3d.export_format != "STL"
        sub.prop(print_3d, "use_data_layers")

        layout.operator("mesh.print3d_export", text="Export", icon='EXPORT')
