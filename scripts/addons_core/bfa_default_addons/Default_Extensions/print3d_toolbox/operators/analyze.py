# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2013-2022 Campbell Barton
# SPDX-FileCopyrightText: 2016-2026 Mikhail Rachinskiy

import math

import bpy
from bpy.props import IntProperty
from bpy.types import Object, Operator

from .. import report


def _get_unit(unit_system: str, unit: str) -> tuple[float, str]:
    # Returns unit length relative to meter and unit symbol

    units = {
        "METRIC": {
            "KILOMETERS": (1000.0, "km"),
            "METERS": (1.0, "m"),
            "CENTIMETERS": (0.01, "cm"),
            "MILLIMETERS": (0.001, "mm"),
            "MICROMETERS": (0.000001, "µm"),
        },
        "IMPERIAL": {
            "MILES": (1609.344, "mi"),
            "FEET": (0.3048, "\'"),
            "INCHES": (0.0254, "\""),
            "THOU": (0.0000254, "thou"),
        },
    }

    try:
        return units[unit_system][unit]
    except KeyError:
        fallback_unit = "CENTIMETERS" if unit_system == "METRIC" else "INCHES"
        return units[unit_system][fallback_unit]


class MESH_OT_info_volume(Operator):
    bl_idname = "mesh.print3d_info_volume"
    bl_label = "Calculate Volume"
    bl_description = "Report the volume of the active mesh"

    def execute(self, context):
        from .. import lib

        scene = context.scene
        unit = scene.unit_settings
        scale = 1.0 if unit.system == "NONE" else unit.scale_length
        obj = context.object

        bm = lib.bmesh_copy_from_object(obj, apply_modifiers=True)
        volume = bm.calc_volume()
        bm.free()

        if unit.system == "NONE":
            volume_fmt = lib.clean_float(volume, 8)
        else:
            length, symbol = _get_unit(unit.system, unit.length_unit)

            volume_unit = volume * (scale ** 3.0) / (length ** 3.0)
            volume_str = lib.clean_float(volume_unit, 4)
            volume_fmt = f"{volume_str} {symbol}"

        report.update(report.info("Volume", f"{volume_fmt}³"))

        return {"FINISHED"}


class MESH_OT_info_area(Operator):
    bl_idname = "mesh.print3d_info_area"
    bl_label = "Calculate Area"
    bl_description = "Report the surface area of the active mesh"

    def execute(self, context):
        from .. import lib

        scene = context.scene
        unit = scene.unit_settings
        scale = 1.0 if unit.system == "NONE" else unit.scale_length
        obj = context.object

        bm = lib.bmesh_copy_from_object(obj, apply_modifiers=True)
        area = lib.bmesh_calc_area(bm)
        bm.free()

        if unit.system == "NONE":
            area_fmt = lib.clean_float(area, 8)
        else:
            length, symbol = _get_unit(unit.system, unit.length_unit)

            area_unit = area * (scale ** 2.0) / (length ** 2.0)
            area_str = lib.clean_float(area_unit, 4)
            area_fmt = f"{area_str} {symbol}"

        report.update(report.info("Area", f"{area_fmt}²"))

        return {"FINISHED"}


# ---------------
# Geometry Checks


def execute_check(self, context):
    obj = context.object

    data = []
    self.main_check(obj, data)
    report.update(*data)

    multiple_obj_warning(self, context)

    return {"FINISHED"}


def multiple_obj_warning(self, context) -> None:
    if len(context.selected_objects) > 1:
        self.report({"WARNING"}, "Multiple selected objects. Only the active one will be evaluated")


class MESH_OT_check_solid(Operator):
    bl_idname = "mesh.print3d_check_solid"
    bl_label = "Solid"
    bl_description = "Check for geometry is solid (has valid inside/outside) and correct normals"

    @staticmethod
    def main_check(obj: Object, data: list):
        import array
        from .. import lib

        # TODO bow-tie quads

        bm = lib.bmesh_copy_from_object(obj, transform=False, triangulate=False)
        edges_non_manifold = array.array("i", (i for i, ele in enumerate(bm.edges) if not ele.is_manifold))
        edges_non_contig = array.array("i", (i for i, ele in enumerate(bm.edges) if ele.is_manifold and (not ele.is_contiguous)))
        bm.free()

        data.append(report.edge("Non-manifold Edges", len(edges_non_manifold), edges_non_manifold))
        data.append(report.edge("Bad Contiguous Edges", len(edges_non_contig), edges_non_contig))

    def execute(self, context):
        return execute_check(self, context)


class MESH_OT_check_intersections(Operator):
    bl_idname = "mesh.print3d_check_intersect"
    bl_label = "Intersections"
    bl_description = "Check for self intersections"

    @staticmethod
    def main_check(obj: Object, data: list):
        from .. import lib

        faces_intersect = lib.bmesh_check_self_intersect_object(obj)
        data.append(report.face("Intersect Faces", len(faces_intersect), faces_intersect))

    def execute(self, context):
        return execute_check(self, context)


class MESH_OT_check_shells(Operator):
    bl_idname = "mesh.print3d_check_shells"
    bl_label = "Shells"
    bl_description = "Count mesh islands"

    @staticmethod
    def main_check(obj: Object, data: list):
        if bpy.app.version < (4, 3, 0):
            return

        ng = bpy.data.node_groups.new(".shells", "GeometryNodeTree")

        sock_geo_in = ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
        sock_geo_out = ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

        nodes = ng.nodes

        in_ = nodes.new("NodeGroupInput")
        in_.location.x = -200
        in_.select = False
        in_geo = in_.outputs[sock_geo_in.identifier]

        out = nodes.new("NodeGroupOutput")
        out.location.x = 400
        out.select = False
        out_geo = out.inputs[sock_geo_out.identifier]

        stats = nodes.new("GeometryNodeAttributeStatistic")
        stats.location.y = -60
        stats.select = False
        stats.domain = "FACE"

        island = nodes.new("GeometryNodeInputMeshIsland")
        island.location = -200, -350
        island.select = False

        tostring = nodes.new("FunctionNodeValueToString")
        tostring.location = 200, -150
        tostring.select = False
        tostring.data_type = "INT"

        warn = nodes.new("GeometryNodeWarning")
        warn.location = 400, -150
        warn.select = False
        warn.warning_type = "INFO"

        ng.links.new(in_geo, out_geo)
        ng.links.new(in_geo, stats.inputs["Geometry"])
        ng.links.new(island.outputs["Island Count"], stats.inputs["Attribute"])
        ng.links.new(stats.outputs["Max"], tostring.inputs["Value"])
        ng.links.new(tostring.outputs["String"], warn.inputs["Message"])

        md = obj.modifiers.new(ng.name, "NODES")
        md.node_group = ng

        bpy.context.view_layer.update()
        try:
            shells = md.node_warnings[0].message
        except:
            shells = "ERROR"

        obj.modifiers.remove(md)
        bpy.data.node_groups.remove(ng)

        data.append(report.info("Shells", shells))

    def execute(self, context):
        return execute_check(self, context)


class MESH_OT_check_degenerate(Operator):
    bl_idname = "mesh.print3d_check_degenerate"
    bl_label = "Degenerate"
    bl_description = "Check for zero area faces and zero length edges"

    @staticmethod
    def main_check(obj: Object, data: list):
        import array
        from .. import lib

        thr_length = bpy.context.scene.print3d_toolbox.threshold_zero
        thr_area = thr_length ** 2.0

        bm = lib.bmesh_copy_from_object(obj, transform=False, triangulate=False)
        faces_zero = array.array("i", (i for i, ele in enumerate(bm.faces) if ele.calc_area() <= thr_area))
        edges_zero = array.array("i", (i for i, ele in enumerate(bm.edges) if ele.calc_length() <= thr_length))
        bm.free()

        data.append(report.face("Zero Faces", len(faces_zero), faces_zero))
        data.append(report.edge("Zero Edges", len(edges_zero), edges_zero))

    def execute(self, context):
        return execute_check(self, context)


class MESH_OT_check_nonplanar(Operator):
    bl_idname = "mesh.print3d_check_nonplanar"
    bl_label = "Non-Planar"
    bl_description = "Check for non-flat faces"

    @staticmethod
    def main_check(obj: Object, data: list):
        import array
        from .. import lib

        angle_nonplanar = bpy.context.scene.print3d_toolbox.angle_nonplanar

        bm = lib.bmesh_copy_from_object(obj, transform=True, triangulate=False)
        bm.normal_update()

        faces_distort = array.array("i", (i for i, ele in enumerate(bm.faces) if lib.face_is_distorted(ele, angle_nonplanar)))
        bm.free()

        data.append(report.face("Non-flat Faces", len(faces_distort), faces_distort))

    def execute(self, context):
        return execute_check(self, context)


class MESH_OT_check_thick(Operator):
    bl_idname = "mesh.print3d_check_thick"
    bl_label = "Thickness"
    bl_description = "Check for wall thickness below specified value"

    @staticmethod
    def main_check(obj: Object, data: list):
        from .. import lib

        thickness_min = bpy.context.scene.print3d_toolbox.thickness_min
        faces_error = lib.bmesh_check_thick_object(obj, thickness_min)

        data.append(report.face("Thin Faces", len(faces_error), faces_error))

    def execute(self, context):
        return execute_check(self, context)


class MESH_OT_check_sharp(Operator):
    bl_idname = "mesh.print3d_check_sharp"
    bl_label = "Sharp"
    bl_description = "Check for edges sharper than a specified angle"

    @staticmethod
    def main_check(obj: Object, data: list):
        from .. import lib

        angle_sharp = bpy.context.scene.print3d_toolbox.angle_sharp

        bm = lib.bmesh_copy_from_object(obj, transform=True, triangulate=False)
        bm.normal_update()

        edges_sharp = [
            ele.index for ele in bm.edges
            if ele.is_manifold and ele.calc_face_angle_signed() > angle_sharp
        ]
        bm.free()

        data.append(report.edge("Sharp Edges", len(edges_sharp), edges_sharp))

    def execute(self, context):
        return execute_check(self, context)


class MESH_OT_check_overhang(Operator):
    bl_idname = "mesh.print3d_check_overhang"
    bl_label = "Overhang"
    bl_description = "Check for faces that overhang past a specified angle"

    @staticmethod
    def main_check(obj: Object, data: list):
        from mathutils import Vector
        from .. import lib

        angle_overhang = (math.pi / 2.0) - bpy.context.scene.print3d_toolbox.angle_overhang

        if angle_overhang == math.pi:
            data.append(report.info("Skipping Overhang", ""))
            return

        bm = lib.bmesh_copy_from_object(obj, transform=True, triangulate=False)
        bm.normal_update()

        z_down = Vector((0, 0, -1.0))
        z_down_angle = z_down.angle

        # 4.0 ignores zero area faces
        faces_overhang = [
            ele.index for ele in bm.faces
            if z_down_angle(ele.normal, 4.0) < angle_overhang
        ]
        bm.free()

        data.append(report.face("Overhang Faces", len(faces_overhang), faces_overhang))

    def execute(self, context):
        return execute_check(self, context)


class MESH_OT_check_all(Operator):
    bl_idname = "mesh.print3d_check_all"
    bl_label = "Check All"
    bl_description = "Run all checks"
    bl_options = {"INTERNAL"}

    check_cls = (
        MESH_OT_check_solid,
        MESH_OT_check_intersections,
        MESH_OT_check_shells,
        MESH_OT_check_degenerate,
        MESH_OT_check_nonplanar,
        MESH_OT_check_thick,
        MESH_OT_check_sharp,
        MESH_OT_check_overhang,
    )

    def execute(self, context):
        obj = context.object

        data = []
        for cls in self.check_cls:
            cls.main_check(obj, data)

        report.update(*data)

        multiple_obj_warning(self, context)

        return {"FINISHED"}


class MESH_OT_report_select(Operator):
    bl_idname = "mesh.print3d_select_report"
    bl_label = "Select"
    bl_description = "Select the data associated with this report"
    bl_options = {"INTERNAL"}

    index: IntProperty()

    def execute(self, context):
        import bmesh

        obj = context.edit_object
        item = report.get()[self.index]

        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.mesh.select_mode(type=item.select_mode)

        bm = bmesh.from_edit_mesh(obj.data)
        elems = getattr(bm, item.bm_attribute)[:]

        try:
            for i in item.indices:
                elems[i].select_set(True)
        except:
            # possible arrays are out of sync
            self.report({"ERROR"}, "Report is out of date, re-run check")

        return {"FINISHED"}


class WM_OT_report_clear(Operator):
    bl_idname = "wm.print3d_report_clear"
    bl_label = "Clear Report"
    bl_description = "Clear report"
    bl_options = {"INTERNAL"}

    def execute(self, context):
        report.clear()
        return {"FINISHED"}
