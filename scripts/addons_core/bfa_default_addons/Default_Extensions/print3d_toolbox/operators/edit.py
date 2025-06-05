# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2013-2022 Campbell Barton
# SPDX-FileContributor: Mikhail Rachinskiy
# SPDX-FileContributor: Align XY by Jaggz H.
# SPDX-FileContributor: Hollow by Ubiratan Freitas


import math

import bmesh
import bpy
from bpy.app.translations import pgettext_tip as tip_
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty
from bpy.types import Operator


class MESH_OT_hollow(Operator):
    bl_idname = "mesh.print3d_hollow"
    bl_label = "Hollow"
    bl_description = "Create offset surface"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    offset_direction: EnumProperty(
        items=[
            ("INSIDE", "Inside", "Offset surface inside of object"),
            ("OUTSIDE", "Outside", "Offset surface outside of object"),
        ],
        name="Offset Direction",
        description="Where the offset surface is created relative to the object",
        default="INSIDE",
    )
    offset: FloatProperty(
        name="Offset",
        description="Surface offset in relation to original mesh",
        default=1.0,
        subtype="DISTANCE",
        min=0.0,
        step=1,
    )
    voxel_size: FloatProperty(
        name="Voxel size",
        description="Size of the voxel used for volume evaluation. Lower values preserve finer details",
        default=1.0,
        min=0.0001,
        step=1,
        subtype="DISTANCE",
    )
    make_hollow_duplicate: BoolProperty(
        name="Hollow Duplicate",
        description="Create hollowed out copy of the object",
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.separator()

        layout.prop(self, "offset_direction", expand=True)
        layout.prop(self, "offset")
        layout.prop(self, "voxel_size")
        layout.prop(self, "make_hollow_duplicate")

    def execute(self, context):
        import numpy as np
        import pyopenvdb as vdb

        if not self.offset:
            return {"FINISHED"}

        obj = context.active_object
        depsgraph = context.evaluated_depsgraph_get()
        mesh_target = bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph))

        # Apply transforms, avoid translating the mesh
        mat = obj.matrix_world.copy()
        mat.translation = 0, 0, 0
        mesh_target.transform(mat)

        # Read mesh to numpy arrays
        nverts = len(mesh_target.vertices)
        ntris = len(mesh_target.loop_triangles)
        verts = np.zeros(3 * nverts, dtype=np.float32)
        tris = np.zeros(3 * ntris, dtype=np.int32)
        mesh_target.vertices.foreach_get("co", verts)
        verts.shape = (-1, 3)
        mesh_target.loop_triangles.foreach_get("vertices", tris)
        tris.shape = (-1, 3)

        # Generate VDB levelset
        half_width = max(3.0, math.ceil(abs(self.offset) / self.voxel_size) + 2.0) # half_width has to envelop offset
        trans = vdb.Transform()
        trans.scale(self.voxel_size)
        levelset = vdb.FloatGrid.createLevelSetFromPolygons(verts, triangles=tris, transform=trans, halfWidth=half_width)

        # Generate offset surface
        if self.offset_direction == "INSIDE":
            newverts, newquads = levelset.convertToQuads(-self.offset)
            if newquads.size == 0:
                self.report({"ERROR"}, "Make sure target mesh has closed surface and offset value is less than half of target thickness")
                return {"FINISHED"}
        else:
            newverts, newquads = levelset.convertToQuads(self.offset)

        bpy.ops.object.select_all(action="DESELECT")
        mesh_offset = bpy.data.meshes.new(mesh_target.name + " offset")
        mesh_offset.from_pydata(newverts, [], list(newquads))

        # For some reason OpenVDB has inverted normals
        mesh_offset.flip_normals()
        obj_offset = bpy.data.objects.new(obj.name + " offset", mesh_offset)
        obj_offset.matrix_world.translation = obj.matrix_world.translation
        bpy.context.collection.objects.link(obj_offset)
        obj_offset.select_set(True)
        context.view_layer.objects.active = obj_offset

        if self.make_hollow_duplicate:
            obj_hollow = bpy.data.objects.new(obj.name + " hollow", mesh_target)
            bpy.context.collection.objects.link(obj_hollow)
            obj_hollow.matrix_world.translation = obj.matrix_world.translation
            obj_hollow.select_set(True)
            if self.offset_direction == "INSIDE":
                mesh_offset.flip_normals()
            else:
                mesh_target.flip_normals()
            context.view_layer.objects.active = obj_hollow
            bpy.ops.object.join()
        else:
            bpy.data.meshes.remove(mesh_target)

        return {"FINISHED"}

    def invoke(self, context, event):
        if context.mode == "EDIT_MESH":
            bpy.ops.object.mode_set(mode="OBJECT")
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class OBJECT_OT_align_xy(Operator):
    bl_idname = "object.print3d_align_xy"
    bl_label = "Align XY"
    bl_description = "Rotate object so the selected faces lie, on average, parallel to the XY plane"
    bl_options = {"REGISTER", "UNDO"}

    use_face_area: BoolProperty(
        name="Weight by Face Area",
        description="Take face area into account when calculating rotation",
        default=True,
    )

    def execute(self, context):
        # FIXME: Undo is inconsistent.
        # FIXME: Would be nicer if rotate could pick some object-local axis.

        from mathutils import Vector

        self.context = context
        mode_orig = context.mode
        skip_invalid = []

        for obj in context.selected_objects:
            orig_loc = obj.location.copy()
            orig_scale = obj.scale.copy()

            # When in edit mode, do as the edit mode does.
            if mode_orig == "EDIT_MESH":
                bm = bmesh.from_edit_mesh(obj.data)
                faces = [f for f in bm.faces if f.select]
            else:
                faces = [p for p in obj.data.polygons if p.select]

            if not faces:
                skip_invalid.append(obj.name)
                continue

            # Rotate object so average normal of selected faces points down.
            normal = Vector((0.0, 0.0, 0.0))
            if self.use_face_area:
                for face in faces:
                    if mode_orig == "EDIT_MESH":
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
                self.report({"WARNING"}, tip_("Skipping object {}. No faces selected").format(skip_invalid[0]))
            else:
                self.report({"WARNING"}, "Skipping some objects. No faces selected. See terminal")
        return {"FINISHED"}

    def invoke(self, context, event):
        if context.mode not in {"EDIT_MESH", "OBJECT"}:
            return {"CANCELLED"}
        return self.execute(context)


def _scale(scale, report=None, report_suffix=""):
    from .. import lib

    if scale != 1.0:
        bpy.ops.transform.resize(value=(scale,) * 3)

    if report is not None:
        scale_fmt = lib.clean_float(scale, 6)
        report({"INFO"}, tip_("Scaled by {}{}").format(scale_fmt, report_suffix))


class MESH_OT_scale_to_volume(Operator):
    bl_idname = "mesh.print3d_scale_to_volume"
    bl_label = "Scale to Volume"
    bl_description = "Scale edit-mesh or selected-objects to a set volume"
    bl_options = {"REGISTER", "UNDO"}

    volume_init: FloatProperty(
        options={"HIDDEN"},
    )
    volume: FloatProperty(
        name="Volume",
        unit="VOLUME",
        min=0.0,
        max=100000.0,
        step=1,
    )

    def execute(self, context):
        from .. import lib
        scale = math.pow(self.volume, 1 / 3) / math.pow(self.volume_init, 1 / 3)
        scale_fmt = lib.clean_float(scale, 6)
        self.report({"INFO"}, tip_("Scaled by {}").format(scale_fmt))
        _scale(scale, self.report)
        return {"FINISHED"}

    def invoke(self, context, event):

        def calc_volume(obj):
            from .. import lib

            bm = lib.bmesh_copy_from_object(obj, apply_modifiers=True)
            volume = bm.calc_volume(signed=True)
            bm.free()
            return volume

        if not context.selectable_objects:
            self.report({"ERROR"}, "At least one mesh object must be selected")
            return {"CANCELLED"}

        if context.mode == "EDIT_MESH":
            volume = calc_volume(context.edit_object)
        else:
            volume = sum(calc_volume(obj) for obj in context.selected_editable_objects if obj.type == "MESH")

        if volume == 0.0:
            self.report({"WARNING"}, "Object has zero volume")
            return {"CANCELLED"}

        self.volume_init = self.volume = abs(volume)

        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class MESH_OT_scale_to_bounds(Operator):
    bl_idname = "mesh.print3d_scale_to_bounds"
    bl_label = "Scale to Bounds"
    bl_description = "Scale edit-mesh or selected-objects to fit within a maximum length"
    bl_options = {"REGISTER", "UNDO"}

    length_init: FloatProperty(
        options={"HIDDEN"},
    )
    axis_init: IntProperty(
        options={"HIDDEN"},
    )
    length: FloatProperty(
        name="Length Limit",
        unit="LENGTH",
        min=0.0,
        max=100000.0,
        step=1,
    )

    def execute(self, context):
        scale = self.length / self.length_init
        axis = "XYZ"[self.axis_init]
        _scale(scale, report=self.report, report_suffix=tip_(", Clamping {}-Axis").format(axis))
        return {"FINISHED"}

    def invoke(self, context, event):
        from mathutils import Vector

        def calc_length(vecs):
            return max(((max(v[i] for v in vecs) - min(v[i] for v in vecs)), i) for i in range(3))

        if not context.selectable_objects:
            self.report({"ERROR"}, "At least one mesh object must be selected")
            return {"CANCELLED"}

        if context.mode == "EDIT_MESH":
            length, axis = calc_length(
                [Vector(v) @ obj.matrix_world for obj in [context.edit_object] for v in obj.bound_box]
            )
        else:
            length, axis = calc_length(
                [
                    Vector(v) @ obj.matrix_world for obj in context.selected_editable_objects
                    if obj.type == "MESH"
                    for v in obj.bound_box
                ]
            )

        if length == 0.0:
            self.report({"WARNING"}, "Object has zero bounds")
            return {"CANCELLED"}

        self.length_init = self.length = length
        self.axis_init = axis

        wm = context.window_manager
        return wm.invoke_props_dialog(self)
