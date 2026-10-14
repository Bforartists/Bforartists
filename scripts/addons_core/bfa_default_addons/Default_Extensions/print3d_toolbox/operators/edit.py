# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2013-2022 Campbell Barton
# SPDX-FileCopyrightText: 2016-2026 Mikhail Rachinskiy
# SPDX-FileCopyrightText: 2022 Align XY by Jaggz H.
# SPDX-FileCopyrightText: 2024-2025 Hollow, Bisect by Ubiratan Freitas

import math

import bpy
from bpy.app.translations import pgettext_tip as tip_
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty
from bpy.types import Object, Operator


class MESH_OT_bisect(Operator):
    bl_idname = "mesh.print3d_bisect"
    bl_label = "Bisect"
    bl_description = "Cut geometry along a plane"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    bisect_x: BoolProperty(
        name="X",
        description="Slice on axis",
    )
    bisect_y: BoolProperty(
        name="Y",
        description="Slice on axis",
    )
    bisect_z: BoolProperty(
        name="Z",
        description="Slice on axis",
    )

    flip_x: BoolProperty(
        name="Flip",
        description="Flips the direction of the slice",
    )
    flip_y: BoolProperty(
        name="Flip",
        description="Flips the direction of the slice",
    )
    flip_z: BoolProperty(
        name="Flip",
        description="Flips the direction of the slice",
    )

    factor_x: FloatProperty(
        name="Factor",
        description="Cutting plane position",
        subtype="FACTOR",
        min=0.0,
        max=1.0,
        default=0.5,
    )
    factor_y: FloatProperty(
        name="Factor",
        description="Cutting plane position",
        subtype="FACTOR",
        min=0.0,
        max=1.0,
        default=0.5,
    )
    factor_z: FloatProperty(
        name="Factor",
        description="Cutting plane position",
        subtype="FACTOR",
        min=0.0,
        max=1.0,
        default=0.5,
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.separator()

        box = layout.box()
        col = box.column()
        col.use_property_split = False
        col.prop(self, "bisect_x")
        col = box.column()
        col.enabled = self.bisect_x
        col.prop(self, "factor_x")
        col.prop(self, "flip_x")

        layout.separator()

        box = layout.box()
        col = box.column()
        col.use_property_split = False
        col.prop(self, "bisect_y")
        col = box.column()
        col.enabled = self.bisect_y
        col.prop(self, "factor_y")
        col.prop(self, "flip_y")

        layout.separator()

        box = layout.box()
        col = box.column()
        col.use_property_split = False
        col.prop(self, "bisect_z")
        col = box.column()
        col.enabled = self.bisect_z
        col.prop(self, "factor_z")
        col.prop(self, "flip_z")

    @classmethod
    def poll(cls, context):
        return bpy.app.version >= (4, 5, 0)

    def execute(self, context):
        from .. import lib

        md = lib.gn_setup("Bisect", context.object)

        lib.md_input_set(md, "Socket_12", self.bisect_x)
        lib.md_input_set(md, "Socket_3", self.factor_x)
        lib.md_input_set(md, "Socket_4", self.flip_x)

        lib.md_input_set(md, "Socket_16", self.bisect_y)
        lib.md_input_set(md, "Socket_6", self.factor_y)
        lib.md_input_set(md, "Socket_7", self.flip_y)

        lib.md_input_set(md, "Socket_14", self.bisect_z)
        lib.md_input_set(md, "Socket_9", self.factor_z)
        lib.md_input_set(md, "Socket_10", self.flip_z)

        panels = lib.md_get_panels(md)

        lib.md_panel_set(md, panels["X"], self.bisect_x)
        lib.md_panel_set(md, panels["Y"], self.bisect_y)
        lib.md_panel_set(md, panels["Z"], self.bisect_z)

        return {"FINISHED"}

    def invoke(self, context, event):
        if context.object is None or not context.object.select_get():
            return {"CANCELLED"}

        if context.mode == "EDIT_MESH":
            bpy.ops.object.mode_set(mode="OBJECT")

        wm = context.window_manager
        return wm.invoke_props_popup(self, event)


class MESH_OT_hollow(Operator):
    bl_idname = "mesh.print3d_hollow"
    bl_label = "Hollow"
    bl_description = "Create offset surface"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    offset_direction: EnumProperty(
        name="Offset Direction",
        description="Offset direction relative to the object surface",
        items=(
            ("INSIDE", "Inside", ""),
            ("OUTSIDE", "Outside", ""),
        ),
        default="INSIDE",
    )
    offset: FloatProperty(
        name="Offset",
        description="Surface offset in relation to original mesh",
        subtype="DISTANCE",
        min=0.0,
        step=1,
        default=1.0,
    )
    voxel_size: FloatProperty(
        name="Voxel Size",
        description="Size of the voxel used for volume evaluation. Lower values preserve finer details",
        subtype="DISTANCE",
        min=0.0001,
        step=1,
        default=1.0,
    )
    make_hollow_duplicate: BoolProperty(
        name="Hollow Duplicate",
        description="Create hollowed out copy of the object",
    )
    offset_surface_only: BoolProperty(
        name="Offset Surface Only",
        description="Remove original and keep offset surface",
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.separator()

        layout.prop(self, "offset_direction", expand=True)
        layout.prop(self, "offset")
        layout.prop(self, "voxel_size")
        if bpy.app.version >= (5, 0, 0):
            layout.prop(self, "offset_surface_only")
        else:
            layout.prop(self, "make_hollow_duplicate")

    def execute(self, context):
        if not self.offset:
            return {"FINISHED"}

        if bpy.app.version >= (5, 0, 0):
            self.hollow_gn(context)
        else:
            self.hollow_openvdb(context)

        return {"FINISHED"}

    def invoke(self, context, event):
        if context.object is None or not context.object.select_get():
            return {"CANCELLED"}

        if context.mode == "EDIT_MESH":
            bpy.ops.object.mode_set(mode="OBJECT")

        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def hollow_gn(self, context):
        from .. import lib

        md = lib.gn_setup("Hollow", context.object)
        lib.md_input_set(md, "Socket_5", self.offset_direction.title(), lib.EnumProp(self, "offset_direction"))
        lib.md_input_set(md, "Socket_3", self.offset)
        lib.md_input_set(md, "Socket_2", self.voxel_size)
        lib.md_input_set(md, "Socket_4", self.offset_surface_only)

        context.view_layer.update()
        if md.node_warnings:
            md.id_data.modifiers.remove(md)
            self.report({"ERROR"}, "Make sure target mesh has closed surface and offset value is less than half of target thickness")

    def hollow_openvdb(self, context):
        import numpy as np

        if bpy.app.version >= (4, 4, 0):
            import openvdb as vdb
        else:
            import pyopenvdb as vdb

        obj = context.object
        depsgraph = context.evaluated_depsgraph_get()
        mesh_target = bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph))

        # Apply transforms, avoid translating the mesh
        mat = obj.matrix_world.copy()
        mat.translation.zero()
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
        half_width = max(3.0, math.ceil(self.offset / self.voxel_size) + 2.0) # half_width has to envelop offset
        trans = vdb.createLinearTransform(self.voxel_size)
        levelset = vdb.FloatGrid.createLevelSetFromPolygons(verts, triangles=tris, transform=trans, halfWidth=half_width)

        # Generate offset surface
        if self.offset_direction == "INSIDE":
            newverts, newquads = levelset.convertToQuads(-self.offset)
            if newquads.size == 0:
                self.report({"ERROR"}, "Make sure target mesh has closed surface and offset value is less than half of target thickness")
                return
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
        import bmesh
        from mathutils import Vector

        is_edit_mesh = context.mode == "EDIT_MESH"
        skip_invalid = []

        for obj in (ob for ob in context.selected_objects if ob.type == "MESH"):
            orig_loc = obj.location.copy()
            orig_scale = obj.scale.copy()

            # When in edit mode, do as the edit mode does.
            if is_edit_mesh:
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
                    if is_edit_mesh:
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

        if skip_invalid:
            if len(skip_invalid) == 1:
                self.report({"WARNING"}, tip_("Skipping object {}. No faces selected").format(skip_invalid[0]))
            else:
                self.report({"WARNING"}, "Skipping some objects. No faces selected. See terminal")

                for name in skip_invalid:
                    print(tip_("Align to XY: Skipping object {}. No faces selected").format(name))

        return {"FINISHED"}

    def invoke(self, context, event):
        if not [ob for ob in context.selected_objects if ob.type == "MESH"]:
            self.report({"ERROR"}, "At least one mesh object must be selected")
            return {"CANCELLED"}

        return self.execute(context)


def _scale(scale: float, report=None, report_suffix="") -> None:
    from .. import lib

    if scale != 1.0:
        bpy.ops.transform.resize(value=(scale,) * 3)

    if report is not None:
        scale_fmt = lib.clean_float(scale, 6)
        report({"INFO"}, tip_("Scaled by {}").format(scale_fmt) + report_suffix)


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

        def calc_volume(obj: Object) -> float:
            from .. import lib
            bm = lib.bmesh_copy_from_object(obj, apply_modifiers=True)
            volume = bm.calc_volume(signed=True)
            bm.free()
            return volume

        if not context.selected_objects:
            self.report({"ERROR"}, "At least one mesh object must be selected")
            return {"CANCELLED"}

        if context.mode == "EDIT_MESH":
            volume = calc_volume(context.edit_object)
        else:
            volume = sum(
                calc_volume(obj)
                for obj in context.selected_editable_objects
                if obj.type in {"MESH", "CURVE", "SURFACE", "FONT", "META"}
            )

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
        name="Length",
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

        def calc_length(vecs: list[Vector]) -> tuple[float, int]:
            return max(
                ((max(v[i] for v in vecs) - min(v[i] for v in vecs)), i)
                for i in range(3)
            )

        if not context.selected_objects:
            self.report({"ERROR"}, "At least one mesh object must be selected")
            return {"CANCELLED"}

        if context.mode == "EDIT_MESH":
            obj = context.edit_object
            length, axis = calc_length([Vector(v) @ obj.matrix_world for v in obj.bound_box])
        else:
            length, axis = calc_length([
                Vector(v) @ obj.matrix_world
                for obj in context.selected_editable_objects
                for v in obj.bound_box
            ])

        if length == 0.0:
            self.report({"WARNING"}, "Object has zero bounds")
            return {"CANCELLED"}

        self.length_init = self.length = length
        self.axis_init = axis

        wm = context.window_manager
        return wm.invoke_props_dialog(self)
