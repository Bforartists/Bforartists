# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2013-2022 Campbell Barton
# SPDX-FileContributor: Mikhail Rachinskiy


import math

import bmesh
import bpy
from bpy.app.translations import pgettext_tip as tip_
from bpy.props import IntProperty
from bpy.types import Operator

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
    bl_label = "3D Print Info Volume"
    bl_description = "Report the volume of the active mesh"

    def execute(self, context):
        from .. import lib

        scene = context.scene
        unit = scene.unit_settings
        scale = 1.0 if unit.system == "NONE" else unit.scale_length
        obj = context.active_object

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

        report.update((tip_("Volume: {}³").format(volume_fmt), None))

        return {"FINISHED"}


class MESH_OT_info_area(Operator):
    bl_idname = "mesh.print3d_info_area"
    bl_label = "3D Print Info Area"
    bl_description = "Report the surface area of the active mesh"

    def execute(self, context):
        from .. import lib

        scene = context.scene
        unit = scene.unit_settings
        scale = 1.0 if unit.system == "NONE" else unit.scale_length
        obj = context.active_object

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

        report.update((tip_("Area: {}²").format(area_fmt), None))

        return {"FINISHED"}


# ---------------
# Geometry Checks


def execute_check(self, context):
    obj = context.active_object

    info = []
    self.main_check(obj, info)
    report.update(*info)

    multiple_obj_warning(self, context)

    return {"FINISHED"}


def multiple_obj_warning(self, context):
    if len(context.selected_objects) > 1:
        self.report({"INFO"}, "Multiple selected objects. Only the active one will be evaluated")


class MESH_OT_check_solid(Operator):
    bl_idname = "mesh.print3d_check_solid"
    bl_label = "3D Print Check Solid"
    bl_description = "Check for geometry is solid (has valid inside/outside) and correct normals"

    @staticmethod
    def main_check(obj, info):
        # TODO bow-tie quads

        import array
        from .. import lib

        bm = lib.bmesh_copy_from_object(obj, transform=False, triangulate=False)

        edges_non_manifold = array.array("i", (i for i, ele in enumerate(bm.edges) if not ele.is_manifold))
        edges_non_contig = array.array(
            "i",
            (i for i, ele in enumerate(bm.edges) if ele.is_manifold and (not ele.is_contiguous)),
        )

        info.append(
            (tip_("Non Manifold Edges: {}").format(
                len(edges_non_manifold)),
                (bmesh.types.BMEdge,
                 edges_non_manifold)))
        info.append((tip_("Bad Contiguous Edges: {}").format(len(edges_non_contig)), (bmesh.types.BMEdge, edges_non_contig)))

        bm.free()

    def execute(self, context):
        return execute_check(self, context)


class MESH_OT_check_intersections(Operator):
    bl_idname = "mesh.print3d_check_intersect"
    bl_label = "3D Print Check Intersections"
    bl_description = "Check geometry for self intersections"

    @staticmethod
    def main_check(obj, info):
        from .. import lib

        faces_intersect = lib.bmesh_check_self_intersect_object(obj)
        info.append((tip_("Intersect Face: {}").format(len(faces_intersect)), (bmesh.types.BMFace, faces_intersect)))

    def execute(self, context):
        return execute_check(self, context)


class MESH_OT_check_degenerate(Operator):
    bl_idname = "mesh.print3d_check_degenerate"
    bl_label = "3D Print Check Degenerate"
    bl_description = (
        "Check for degenerate geometry that may not print properly "
        "(zero area faces, zero length edges)"
    )

    @staticmethod
    def main_check(obj, info):
        import array
        from .. import lib

        scene = bpy.context.scene
        print_3d = scene.print_3d
        threshold = print_3d.threshold_zero

        bm = lib.bmesh_copy_from_object(obj, transform=False, triangulate=False)

        faces_zero = array.array("i", (i for i, ele in enumerate(bm.faces) if ele.calc_area() <= threshold))
        edges_zero = array.array("i", (i for i, ele in enumerate(bm.edges) if ele.calc_length() <= threshold))

        info.append((tip_("Zero Faces: {}").format(len(faces_zero)), (bmesh.types.BMFace, faces_zero)))
        info.append((tip_("Zero Edges: {}").format(len(edges_zero)), (bmesh.types.BMEdge, edges_zero)))

        bm.free()

    def execute(self, context):
        return execute_check(self, context)


class MESH_OT_check_distorted(Operator):
    bl_idname = "mesh.print3d_check_distort"
    bl_label = "3D Print Check Distorted Faces"
    bl_description = "Check for non-flat faces"

    @staticmethod
    def main_check(obj, info):
        import array
        from .. import lib

        scene = bpy.context.scene
        print_3d = scene.print_3d
        angle_distort = print_3d.angle_distort

        bm = lib.bmesh_copy_from_object(obj, transform=True, triangulate=False)
        bm.normal_update()

        faces_distort = array.array(
            "i",
            (i for i, ele in enumerate(bm.faces) if lib.face_is_distorted(ele, angle_distort))
        )

        info.append((tip_("Non-Flat Faces: {}").format(len(faces_distort)), (bmesh.types.BMFace, faces_distort)))

        bm.free()

    def execute(self, context):
        return execute_check(self, context)


class MESH_OT_check_thick(Operator):
    bl_idname = "mesh.print3d_check_thick"
    bl_label = "3D Print Check Thickness"
    bl_description = (
        "Check geometry is above the minimum thickness preference "
        "(relies on correct normals)"
    )

    @staticmethod
    def main_check(obj, info):
        from .. import lib

        scene = bpy.context.scene
        print_3d = scene.print_3d

        faces_error = lib.bmesh_check_thick_object(obj, print_3d.thickness_min)
        info.append((tip_("Thin Faces: {}").format(len(faces_error)), (bmesh.types.BMFace, faces_error)))

    def execute(self, context):
        return execute_check(self, context)


class MESH_OT_check_sharp(Operator):
    bl_idname = "mesh.print3d_check_sharp"
    bl_label = "3D Print Check Sharp"
    bl_description = "Check edges are below the sharpness preference"

    @staticmethod
    def main_check(obj, info):
        from .. import lib

        scene = bpy.context.scene
        print_3d = scene.print_3d
        angle_sharp = print_3d.angle_sharp

        bm = lib.bmesh_copy_from_object(obj, transform=True, triangulate=False)
        bm.normal_update()

        edges_sharp = [
            ele.index for ele in bm.edges
            if ele.is_manifold and ele.calc_face_angle_signed() > angle_sharp
        ]

        info.append((tip_("Sharp Edge: {}").format(len(edges_sharp)), (bmesh.types.BMEdge, edges_sharp)))
        bm.free()

    def execute(self, context):
        return execute_check(self, context)


class MESH_OT_check_overhang(Operator):
    bl_idname = "mesh.print3d_check_overhang"
    bl_label = "3D Print Check Overhang"
    bl_description = "Check faces don't overhang past a certain angle"

    @staticmethod
    def main_check(obj, info):
        from mathutils import Vector
        from .. import lib

        scene = bpy.context.scene
        print_3d = scene.print_3d
        angle_overhang = (math.pi / 2.0) - print_3d.angle_overhang

        if angle_overhang == math.pi:
            info.append(("Skipping Overhang", ()))
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

        info.append((tip_("Overhang Face: {}").format(len(faces_overhang)), (bmesh.types.BMFace, faces_overhang)))
        bm.free()

    def execute(self, context):
        return execute_check(self, context)


class MESH_OT_check_all(Operator):
    bl_idname = "mesh.print3d_check_all"
    bl_label = "3D Print Check All"
    bl_description = "Run all checks"

    check_cls = (
        MESH_OT_check_solid,
        MESH_OT_check_intersections,
        MESH_OT_check_degenerate,
        MESH_OT_check_distorted,
        MESH_OT_check_thick,
        MESH_OT_check_sharp,
        MESH_OT_check_overhang,
    )

    def execute(self, context):
        obj = context.active_object

        info = []
        for cls in self.check_cls:
            cls.main_check(obj, info)

        report.update(*info)

        multiple_obj_warning(self, context)

        return {"FINISHED"}


class MESH_OT_report_select(Operator):
    bl_idname = "mesh.print3d_select_report"
    bl_label = "3D Print Select Report"
    bl_description = "Select the data associated with this report"
    bl_options = {"INTERNAL"}

    index: IntProperty()

    _type_to_mode = {
        bmesh.types.BMVert: "VERT",
        bmesh.types.BMEdge: "EDGE",
        bmesh.types.BMFace: "FACE",
    }

    _type_to_attr = {
        bmesh.types.BMVert: "verts",
        bmesh.types.BMEdge: "edges",
        bmesh.types.BMFace: "faces",
    }

    def execute(self, context):
        obj = context.edit_object
        info = report.info()
        _text, data = info[self.index]
        bm_type, bm_array = data

        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.mesh.select_mode(type=self._type_to_mode[bm_type])

        bm = bmesh.from_edit_mesh(obj.data)
        elems = getattr(bm, MESH_OT_report_select._type_to_attr[bm_type])[:]

        try:
            for i in bm_array:
                elems[i].select_set(True)
        except:
            # possible arrays are out of sync
            self.report({"WARNING"}, "Report is out of date, re-run check")

        return {"FINISHED"}


class WM_OT_report_clear(Operator):
    bl_idname = "wm.print3d_report_clear"
    bl_label = "Clear Report"
    bl_description = "Clear report"
    bl_options = {"INTERNAL"}

    def execute(self, context):
        report.clear()

        return {"FINISHED"}
