# SPDX-FileCopyrightText: 2013-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

# All Operator


import math

import bpy
from bpy.types import Operator
from bpy.props import (
    IntProperty,
    FloatProperty,
)
import bmesh

from bpy.app.translations import pgettext_tip as tip_

from . import report


def clean_float(value: float, precision: int = 0) -> str:
    # Avoid scientific notation and strip trailing zeros: 0.000 -> 0.0

    text = f"{value:.{precision}f}"
    index = text.rfind(".")

    if index != -1:
        index += 2
        head, tail = text[:index], text[index:]
        tail = tail.rstrip("0")
        text = head + tail

    return text


def get_unit(unit_system: str, unit: str) -> tuple[float, str]:
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


# ---------
# Mesh Info


class MESH_OT_print3d_info_volume(Operator):
    bl_idname = "mesh.print3d_info_volume"
    bl_label = "3D-Print Info Volume"
    bl_description = "Report the volume of the active mesh"

    def execute(self, context):
        from . import mesh_helpers

        scene = context.scene
        unit = scene.unit_settings
        scale = 1.0 if unit.system == 'NONE' else unit.scale_length
        obj = context.active_object

        bm = mesh_helpers.bmesh_copy_from_object(obj, apply_modifiers=True)
        volume = bm.calc_volume()
        bm.free()

        if unit.system == 'NONE':
            volume_fmt = clean_float(volume, 8)
        else:
            length, symbol = get_unit(unit.system, unit.length_unit)

            volume_unit = volume * (scale ** 3.0) / (length ** 3.0)
            volume_str = clean_float(volume_unit, 4)
            volume_fmt = f"{volume_str} {symbol}"

        report.update((tip_("Volume: {}³").format(volume_fmt), None))

        return {'FINISHED'}


class MESH_OT_print3d_info_area(Operator):
    bl_idname = "mesh.print3d_info_area"
    bl_label = "3D-Print Info Area"
    bl_description = "Report the surface area of the active mesh"

    def execute(self, context):
        from . import mesh_helpers

        scene = context.scene
        unit = scene.unit_settings
        scale = 1.0 if unit.system == 'NONE' else unit.scale_length
        obj = context.active_object

        bm = mesh_helpers.bmesh_copy_from_object(obj, apply_modifiers=True)
        area = mesh_helpers.bmesh_calc_area(bm)
        bm.free()

        if unit.system == 'NONE':
            area_fmt = clean_float(area, 8)
        else:
            length, symbol = get_unit(unit.system, unit.length_unit)

            area_unit = area * (scale ** 2.0) / (length ** 2.0)
            area_str = clean_float(area_unit, 4)
            area_fmt = f"{area_str} {symbol}"

        report.update((tip_("Area: {}²").format(area_fmt), None))

        return {'FINISHED'}


# ---------------
# Geometry Checks

def execute_check(self, context):
    obj = context.active_object

    info = []
    self.main_check(obj, info)
    report.update(*info)

    multiple_obj_warning(self, context)

    return {'FINISHED'}


def multiple_obj_warning(self, context):
    if len(context.selected_objects) > 1:
        self.report({"INFO"}, "Multiple selected objects. Only the active one will be evaluated")


class MESH_OT_print3d_check_solid(Operator):
    bl_idname = "mesh.print3d_check_solid"
    bl_label = "3D-Print Check Solid"
    bl_description = "Check for geometry is solid (has valid inside/outside) and correct normals"

    @staticmethod
    def main_check(obj, info):
        import array
        from . import mesh_helpers

        bm = mesh_helpers.bmesh_copy_from_object(obj, transform=False, triangulate=False)

        edges_non_manifold = array.array('i', (i for i, ele in enumerate(bm.edges) if not ele.is_manifold))
        edges_non_contig = array.array(
            'i',
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


class MESH_OT_print3d_check_intersections(Operator):
    bl_idname = "mesh.print3d_check_intersect"
    bl_label = "3D-Print Check Intersections"
    bl_description = "Check geometry for self intersections"

    @staticmethod
    def main_check(obj, info):
        from . import mesh_helpers

        faces_intersect = mesh_helpers.bmesh_check_self_intersect_object(obj)
        info.append((tip_("Intersect Face: {}").format(len(faces_intersect)), (bmesh.types.BMFace, faces_intersect)))

    def execute(self, context):
        return execute_check(self, context)


class MESH_OT_print3d_check_degenerate(Operator):
    bl_idname = "mesh.print3d_check_degenerate"
    bl_label = "3D-Print Check Degenerate"
    bl_description = (
        "Check for degenerate geometry that may not print properly "
        "(zero area faces, zero length edges)"
    )

    @staticmethod
    def main_check(obj, info):
        import array
        from . import mesh_helpers

        scene = bpy.context.scene
        print_3d = scene.print_3d
        threshold = print_3d.threshold_zero

        bm = mesh_helpers.bmesh_copy_from_object(obj, transform=False, triangulate=False)

        faces_zero = array.array('i', (i for i, ele in enumerate(bm.faces) if ele.calc_area() <= threshold))
        edges_zero = array.array('i', (i for i, ele in enumerate(bm.edges) if ele.calc_length() <= threshold))

        info.append((tip_("Zero Faces: {}").format(len(faces_zero)), (bmesh.types.BMFace, faces_zero)))
        info.append((tip_("Zero Edges: {}").format(len(edges_zero)), (bmesh.types.BMEdge, edges_zero)))

        bm.free()

    def execute(self, context):
        return execute_check(self, context)


class MESH_OT_print3d_check_distorted(Operator):
    bl_idname = "mesh.print3d_check_distort"
    bl_label = "3D-Print Check Distorted Faces"
    bl_description = "Check for non-flat faces"

    @staticmethod
    def main_check(obj, info):
        import array
        from . import mesh_helpers

        scene = bpy.context.scene
        print_3d = scene.print_3d
        angle_distort = print_3d.angle_distort

        bm = mesh_helpers.bmesh_copy_from_object(obj, transform=True, triangulate=False)
        bm.normal_update()

        faces_distort = array.array(
            'i',
            (i for i, ele in enumerate(bm.faces) if mesh_helpers.face_is_distorted(ele, angle_distort))
        )

        info.append((tip_("Non-Flat Faces: {}").format(len(faces_distort)), (bmesh.types.BMFace, faces_distort)))

        bm.free()

    def execute(self, context):
        return execute_check(self, context)


class MESH_OT_print3d_check_thick(Operator):
    bl_idname = "mesh.print3d_check_thick"
    bl_label = "3D-Print Check Thickness"
    bl_description = (
        "Check geometry is above the minimum thickness preference "
        "(relies on correct normals)"
    )

    @staticmethod
    def main_check(obj, info):
        from . import mesh_helpers

        scene = bpy.context.scene
        print_3d = scene.print_3d

        faces_error = mesh_helpers.bmesh_check_thick_object(obj, print_3d.thickness_min)
        info.append((tip_("Thin Faces: {}").format(len(faces_error)), (bmesh.types.BMFace, faces_error)))

    def execute(self, context):
        return execute_check(self, context)


class MESH_OT_print3d_check_sharp(Operator):
    bl_idname = "mesh.print3d_check_sharp"
    bl_label = "3D-Print Check Sharp"
    bl_description = "Check edges are below the sharpness preference"

    @staticmethod
    def main_check(obj, info):
        from . import mesh_helpers

        scene = bpy.context.scene
        print_3d = scene.print_3d
        angle_sharp = print_3d.angle_sharp

        bm = mesh_helpers.bmesh_copy_from_object(obj, transform=True, triangulate=False)
        bm.normal_update()

        edges_sharp = [
            ele.index for ele in bm.edges
            if ele.is_manifold and ele.calc_face_angle_signed() > angle_sharp
        ]

        info.append((tip_("Sharp Edge: {}").format(len(edges_sharp)), (bmesh.types.BMEdge, edges_sharp)))
        bm.free()

    def execute(self, context):
        return execute_check(self, context)


class MESH_OT_print3d_check_overhang(Operator):
    bl_idname = "mesh.print3d_check_overhang"
    bl_label = "3D-Print Check Overhang"
    bl_description = "Check faces don't overhang past a certain angle"

    @staticmethod
    def main_check(obj, info):
        from mathutils import Vector
        from . import mesh_helpers

        scene = bpy.context.scene
        print_3d = scene.print_3d
        angle_overhang = (math.pi / 2.0) - print_3d.angle_overhang

        if angle_overhang == math.pi:
            info.append(("Skipping Overhang", ()))
            return

        bm = mesh_helpers.bmesh_copy_from_object(obj, transform=True, triangulate=False)
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


class MESH_OT_print3d_check_all(Operator):
    bl_idname = "mesh.print3d_check_all"
    bl_label = "3D-Print Check All"
    bl_description = "Run all checks"

    check_cls = (
        MESH_OT_print3d_check_solid,
        MESH_OT_print3d_check_intersections,
        MESH_OT_print3d_check_degenerate,
        MESH_OT_print3d_check_distorted,
        MESH_OT_print3d_check_thick,
        MESH_OT_print3d_check_sharp,
        MESH_OT_print3d_check_overhang,
    )

    def execute(self, context):
        obj = context.active_object

        info = []
        for cls in self.check_cls:
            cls.main_check(obj, info)

        report.update(*info)

        multiple_obj_warning(self, context)

        return {'FINISHED'}


class MESH_OT_print3d_clean_distorted(Operator):
    bl_idname = "mesh.print3d_clean_distorted"
    bl_label = "3D-Print Clean Distorted"
    bl_description = "Tessellate distorted faces"
    bl_options = {'REGISTER', 'UNDO'}

    angle: FloatProperty(
        name="Angle",
        description="Limit for checking distorted faces",
        subtype='ANGLE',
        default=math.radians(45.0),
        min=0.0,
        max=math.radians(180.0),
    )

    def execute(self, context):
        from . import mesh_helpers

        obj = context.active_object
        bm = mesh_helpers.bmesh_from_object(obj)
        bm.normal_update()
        elems_triangulate = [ele for ele in bm.faces if mesh_helpers.face_is_distorted(ele, self.angle)]

        if elems_triangulate:
            bmesh.ops.triangulate(bm, faces=elems_triangulate)
            mesh_helpers.bmesh_to_object(obj, bm)

        self.report({'INFO'}, tip_("Triangulated {} faces").format(len(elems_triangulate)))

        return {'FINISHED'}

    def invoke(self, context, event):
        print_3d = context.scene.print_3d
        self.angle = print_3d.angle_distort

        return self.execute(context)


class MESH_OT_print3d_clean_non_manifold(Operator):
    bl_idname = "mesh.print3d_clean_non_manifold"
    bl_label = "3D-Print Clean Non-Manifold"
    bl_description = "Cleanup problems, like holes, non-manifold vertices and inverted normals"
    bl_options = {'REGISTER', 'UNDO'}

    threshold: FloatProperty(
        name="Merge Distance",
        description="Minimum distance between elements to merge",
        default=0.0001,
    )
    sides: IntProperty(
        name="Sides",
        description="Number of sides in hole required to fill (zero fills all holes)",
        default=0,
    )

    def execute(self, context):
        self.context = context
        mode_orig = context.mode

        self.setup_environment()
        bm_key_orig = self.elem_count(context)

        self.delete_loose()
        self.delete_interior()
        self.remove_doubles(self.threshold)
        self.dissolve_degenerate(self.threshold)
        self.fix_non_manifold(context, self.sides)  # may take a while
        self.make_normals_consistently_outwards()

        bm_key = self.elem_count(context)

        if mode_orig != 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='OBJECT')

        verts = bm_key[0] - bm_key_orig[0]
        edges = bm_key[1] - bm_key_orig[1]
        faces = bm_key[2] - bm_key_orig[2]

        self.report({'INFO'}, tip_("Modified: {:+} vertices, {:+} edges, {:+} faces").format(verts, edges, faces))

        return {'FINISHED'}

    @staticmethod
    def elem_count(context):
        bm = bmesh.from_edit_mesh(context.edit_object.data)
        return len(bm.verts), len(bm.edges), len(bm.faces)

    @staticmethod
    def setup_environment():
        """set the mode as edit, select mode as vertices, and reveal hidden vertices"""
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='VERT')
        bpy.ops.mesh.reveal()

    @staticmethod
    def remove_doubles(threshold):
        """remove duplicate vertices"""
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=threshold)

    @staticmethod
    def delete_loose():
        """delete loose vertices/edges/faces"""
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.delete_loose(use_verts=True, use_edges=True, use_faces=True)

    @staticmethod
    def delete_interior():
        """delete interior faces"""
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_interior_faces()
        bpy.ops.mesh.delete(type='FACE')

    @staticmethod
    def dissolve_degenerate(threshold):
        """dissolve zero area faces and zero length edges"""
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.dissolve_degenerate(threshold=threshold)

    @staticmethod
    def make_normals_consistently_outwards():
        """have all normals face outwards"""
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent()

    @classmethod
    def fix_non_manifold(cls, context, sides):
        """naive iterate-until-no-more approach for fixing manifolds"""
        total_non_manifold = cls.count_non_manifold_verts(context)

        if not total_non_manifold:
            return

        bm_states = set()
        bm_key = cls.elem_count(context)
        bm_states.add(bm_key)

        while True:
            cls.fill_non_manifold(sides)
            cls.delete_newly_generated_non_manifold_verts()

            bm_key = cls.elem_count(context)
            if bm_key in bm_states:
                break
            else:
                bm_states.add(bm_key)

    @staticmethod
    def select_non_manifold_verts(
        use_wire=False,
        use_boundary=False,
        use_multi_face=False,
        use_non_contiguous=False,
        use_verts=False,
    ):
        """select non-manifold vertices"""
        bpy.ops.mesh.select_non_manifold(
            extend=False,
            use_wire=use_wire,
            use_boundary=use_boundary,
            use_multi_face=use_multi_face,
            use_non_contiguous=use_non_contiguous,
            use_verts=use_verts,
        )

    @classmethod
    def count_non_manifold_verts(cls, context):
        """return a set of coordinates of non-manifold vertices"""
        cls.select_non_manifold_verts(use_wire=True, use_boundary=True, use_verts=True)

        bm = bmesh.from_edit_mesh(context.edit_object.data)
        return sum((1 for v in bm.verts if v.select))

    @classmethod
    def fill_non_manifold(cls, sides):
        """fill in any remnant non-manifolds"""
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.fill_holes(sides=sides)

    @classmethod
    def delete_newly_generated_non_manifold_verts(cls):
        """delete any newly generated vertices from the filling repair"""
        cls.select_non_manifold_verts(use_wire=True, use_verts=True)
        bpy.ops.mesh.delete(type='VERT')


class MESH_OT_print3d_clean_thin(Operator):
    bl_idname = "mesh.print3d_clean_thin"
    bl_label = "3D-Print Clean Thin"
    bl_description = "Ensure minimum thickness"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # TODO

        return {'FINISHED'}


# -------------
# Select Report
# ... helper function for info UI

class MESH_OT_print3d_select_report(Operator):
    bl_idname = "mesh.print3d_select_report"
    bl_label = "3D-Print Select Report"
    bl_description = "Select the data associated with this report"
    bl_options = {'INTERNAL'}

    index: IntProperty()

    _type_to_mode = {
        bmesh.types.BMVert: 'VERT',
        bmesh.types.BMEdge: 'EDGE',
        bmesh.types.BMFace: 'FACE',
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
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(type=self._type_to_mode[bm_type])

        bm = bmesh.from_edit_mesh(obj.data)
        elems = getattr(bm, MESH_OT_print3d_select_report._type_to_attr[bm_type])[:]

        try:
            for i in bm_array:
                elems[i].select_set(True)
        except:
            # possible arrays are out of sync
            self.report({'WARNING'}, "Report is out of date, re-run check")

        return {'FINISHED'}


# -----------
# Scale to...

def _scale(scale, report=None, report_suffix=""):
    if scale != 1.0:
        bpy.ops.transform.resize(value=(scale,) * 3)
    if report is not None:
        scale_fmt = clean_float(scale, 6)
        report({'INFO'}, tip_("Scaled by {}{}").format(scale_fmt, report_suffix))


class MESH_OT_print3d_scale_to_volume(Operator):
    bl_idname = "mesh.print3d_scale_to_volume"
    bl_label = "Scale to Volume"
    bl_description = "Scale edit-mesh or selected-objects to a set volume"
    bl_options = {'REGISTER', 'UNDO'}

    volume_init: FloatProperty(
        options={'HIDDEN'},
    )
    volume: FloatProperty(
        name="Volume",
        unit='VOLUME',
        min=0.0,
        max=100000.0,
    )

    def execute(self, context):
        scale = math.pow(self.volume, 1 / 3) / math.pow(self.volume_init, 1 / 3)
        scale_fmt = clean_float(scale, 6)
        self.report({'INFO'}, tip_("Scaled by {}").format(scale_fmt))
        _scale(scale, self.report)
        return {'FINISHED'}

    def invoke(self, context, event):

        def calc_volume(obj):
            from . import mesh_helpers

            bm = mesh_helpers.bmesh_copy_from_object(obj, apply_modifiers=True)
            volume = bm.calc_volume(signed=True)
            bm.free()
            return volume

        if context.mode == 'EDIT_MESH':
            volume = calc_volume(context.edit_object)
        else:
            volume = sum(calc_volume(obj) for obj in context.selected_editable_objects if obj.type == 'MESH')

        if volume == 0.0:
            self.report({'WARNING'}, "Object has zero volume")
            return {'CANCELLED'}

        self.volume_init = self.volume = abs(volume)

        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class MESH_OT_print3d_scale_to_bounds(Operator):
    bl_idname = "mesh.print3d_scale_to_bounds"
    bl_label = "Scale to Bounds"
    bl_description = "Scale edit-mesh or selected-objects to fit within a maximum length"
    bl_options = {'REGISTER', 'UNDO'}

    length_init: FloatProperty(
        options={'HIDDEN'},
    )
    axis_init: IntProperty(
        options={'HIDDEN'},
    )
    length: FloatProperty(
        name="Length Limit",
        unit='LENGTH',
        min=0.0,
        max=100000.0,
    )

    def execute(self, context):
        scale = self.length / self.length_init
        axis = "XYZ"[self.axis_init]
        _scale(scale, report=self.report, report_suffix=tip_(", Clamping {}-Axis").format(axis))
        return {'FINISHED'}

    def invoke(self, context, event):
        from mathutils import Vector

        def calc_length(vecs):
            return max(((max(v[i] for v in vecs) - min(v[i] for v in vecs)), i) for i in range(3))

        if context.mode == 'EDIT_MESH':
            length, axis = calc_length(
                [Vector(v) @ obj.matrix_world for obj in [context.edit_object] for v in obj.bound_box]
            )
        else:
            length, axis = calc_length(
                [
                    Vector(v) @ obj.matrix_world for obj in context.selected_editable_objects
                    if obj.type == 'MESH'
                    for v in obj.bound_box
                ]
            )

        if length == 0.0:
            self.report({'WARNING'}, "Object has zero bounds")
            return {'CANCELLED'}

        self.length_init = self.length = length
        self.axis_init = axis

        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class MESH_OT_print3d_align_to_xy(Operator):
    bl_idname = "mesh.print3d_align_to_xy"
    bl_label = "Align (rotate) object to XY plane"
    bl_description = (
        "Rotates entire object (not mesh) so the selected faces/vertices lie, on average, parallel to the XY plane "
        "(it does not adjust Z location)"
    )
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # FIXME: Undo is inconsistent.
        # FIXME: Would be nicer if rotate could pick some object-local axis.

        from mathutils import Vector

        print_3d = context.scene.print_3d
        face_areas = print_3d.use_alignxy_face_area

        self.context = context
        mode_orig = context.mode
        skip_invalid = []

        for obj in context.selected_objects:
            orig_loc = obj.location.copy()
            orig_scale = obj.scale.copy()

            # When in edit mode, do as the edit mode does.
            if mode_orig == 'EDIT_MESH':
                bm = bmesh.from_edit_mesh(obj.data)
                faces = [f for f in bm.faces if f.select]
            else:
                faces = [p for p in obj.data.polygons if p.select]

            if not faces:
                skip_invalid.append(obj.name)
                continue

            # Rotate object so average normal of selected faces points down.
            normal = Vector((0.0, 0.0, 0.0))
            if face_areas:
                for face in faces:
                    if mode_orig == 'EDIT_MESH':
                        normal += (face.normal * face.calc_area())
                    else:
                        normal += (face.normal * face.area)
            else:
                for face in faces:
                    normal += face.normal
            normal = normal.normalized()
            normal.rotate(obj.matrix_world)  # local -> world.
            offset = normal.rotation_difference(Vector((0.0, 0.0, -1.0)))
            offset = offset.to_matrix().to_4x4()
            obj.matrix_world = offset @ obj.matrix_world
            obj.scale = orig_scale
            obj.location = orig_loc

        if len(skip_invalid) > 0:
            for name in skip_invalid:
                print(tip_("Align to XY: Skipping object {}. No faces selected").format(name))
            if len(skip_invalid) == 1:
                self.report({'WARNING'}, tip_("Skipping object {}. No faces selected").format(skip_invalid[0]))
            else:
                self.report({'WARNING'}, "Skipping some objects. No faces selected. See terminal")
        return {'FINISHED'}

    def invoke(self, context, event):
        if context.mode not in {'EDIT_MESH', 'OBJECT'}:
            return {'CANCELLED'}
        return self.execute(context)


# ------
# Export

class MESH_OT_print3d_export(Operator):
    bl_idname = "mesh.print3d_export"
    bl_label = "3D-Print Export"
    bl_description = "Export selected objects using 3D-Print settings"

    def execute(self, context):
        from . import export

        ret = export.write_mesh(context, self.report)

        if ret:
            return {'FINISHED'}

        return {'CANCELLED'}
