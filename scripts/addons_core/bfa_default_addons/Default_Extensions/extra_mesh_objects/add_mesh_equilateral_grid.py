# SPDX-FileCopyrightText: 2026 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Author: Luis-Lerga


import bpy
import bmesh
from math import sqrt
from bpy_extras import object_utils


class MESH_OT_add_equilateral_grid(bpy.types.Operator):
    """Add an equilateral triangular grid with hexagonal pattern"""
    bl_idname = "mesh.add_equilateral_grid"
    bl_label = "Add Equilateral Grid"
    bl_options = {'REGISTER', 'UNDO'}

    # Dimensions
    width: bpy.props.FloatProperty(
        name="Width",
        description="Horizontal width of the rectangle",
        default=10.0,
        min=0.1,
        max=100.0,
        step=100,
        precision=2,
        unit='LENGTH'
    )

    height: bpy.props.FloatProperty(
        name="Height",
        description="Vertical height of the rectangle",
        default=10.0,
        min=0.1,
        max=100.0,
        step=100,
        precision=2,
        unit='LENGTH'
    )

    density: bpy.props.IntProperty(
        name="Density",
        description="Number of horizontal segments",
        default=20,
        min=4,
        max=200,
        step=1
    )

    # UVs
    use_uv: bpy.props.BoolProperty(
        name="Generate UVs",
        description="Generate UV coordinates for the mesh",
        default=True
    )

    # Alignment
    align: bpy.props.EnumProperty(
        name="Align",
        description="Mesh alignment orientation",
        items=[
            ('WORLD', "World", "Align to world origin"),
            ('VIEW', "View", "Align to current view"),
            ('CURSOR', "3D Cursor", "Align to 3D cursor position"),
        ],
        default='WORLD'
    )

    # Transformations
    location: bpy.props.FloatVectorProperty(
        name="Location",
        description="Object location",
        subtype='TRANSLATION',
        default=(0.0, 0.0, 0.0),
        unit='LENGTH'
    )

    rotation: bpy.props.FloatVectorProperty(
        name="Rotation",
        description="Object rotation (Euler XYZ)",
        subtype='EULER',
        default=(0.0, 0.0, 0.0),
        unit='ROTATION'
    )


    def execute(self, context):
        # Create geometry & mesh.
        verts, faces = self.create_geometry(context)
        mesh = bpy.data.meshes.new("Equilateral Grid")
        mesh.from_pydata(verts, [], faces)
        mesh.update()

        # Clean-up.
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(mesh)
        bm.free()

        # Generate UVs.
        if self.use_uv:
            self.generate_uvs(mesh)

        # Create an object.
        obj = object_utils.object_data_add(context, mesh, operator=self)

        if context.preferences.edit.use_enter_edit_mode:
            bpy.ops.object.mode_set(mode = 'EDIT')

        return {'FINISHED'}


    def create_geometry(self, context):
        """Generate geometry with equilateral triangles and perfect rectangular borders"""

        L = self.width / self.density
        tri_height = L * sqrt(3) / 2

        # Calculate EVEN number of triangle rows for straight top/bottom borders
        target_rows = self.height / tri_height
        rows = int(round(target_rows / 2.0)) * 2  # Always even
        rows = max(2, rows)

        # Actual adjusted dimensions
        actual_width = self.density * L
        actual_height = rows * tri_height

        # === Generate vertices WITHOUT protruding vertices ===
        verts = []
        row_offsets = []  # Track starting index of each row

        for row in range(rows + 1):  # rows+1 vertex rows
            y = -actual_height / 2 + row * tri_height
            row_offsets.append(len(verts))

            if row % 2 == 0:
                # Even rows: density+1 vertices spanning full width
                num_verts = self.density + 1
                offset = 0.0
            else:
                # Odd rows: density vertices (NO protruding vertex)
                num_verts = self.density
                offset = L * 0.5

            for col in range(num_verts):
                x = -actual_width / 2 + col * L + offset
                verts.append((x, y, 0.0))

        # === Generate interior faces (equilateral triangles) ===
        faces = []
        for row in range(rows):
            if row % 2 == 0:
                # Even row → next row is odd (fewer vertices)
                for col in range(self.density):
                    i00 = row_offsets[row] + col
                    i01 = i00 + 1
                    i10 = row_offsets[row + 1] + col
                    i11 = i10 + 1 if col < self.density - 1 else None

                    faces.append((i00, i10, i01))
                    if i11 is not None:
                        faces.append((i01, i10, i11))
            else:
                # Odd row → next row is even (more vertices)
                for col in range(self.density):
                    i00 = row_offsets[row] + col
                    i01 = i00 + 1 if col < self.density - 1 else None
                    i10 = row_offsets[row + 1] + col
                    i11 = i10 + 1

                    if i01 is not None:
                        faces.append((i00, i11, i01))
                    faces.append((i00, i10, i11))

        # === Fill LEFT/RIGHT borders for odd rows ===
        for row in range(1, rows, 2):  # Only odd rows (1, 3, 5...)
            y = -actual_height / 2 + row * tri_height

            # Add LEFT border vertex at exact x = -width/2
            left_idx = len(verts)
            verts.append((-actual_width / 2, y, 0.0))

            # Add RIGHT border vertex at exact x = +width/2
            right_idx = len(verts)
            verts.append((actual_width / 2, y, 0.0))

            # Connect LEFT border vertex
            base_idx = row_offsets[row]
            above_idx = row_offsets[row - 1]  # Even row above
            below_idx = row_offsets[row + 1]  # Even row below

            # Upper triangle: left border → first interior → vertex above first interior
            faces.append((left_idx, base_idx, above_idx))
            # Lower triangle: left border → vertex below first interior → first interior
            faces.append((left_idx, below_idx, base_idx))

            # Connect RIGHT border vertex
            last_interior = base_idx + self.density - 1
            above_last = above_idx + self.density  # Last vertex of even row above
            below_last = below_idx + self.density  # Last vertex of even row below

            # Upper triangle: right border → last interior → vertex above last interior
            faces.append((right_idx, last_interior, above_last))
            # Lower triangle: right border → vertex below last interior → last interior
            faces.append((right_idx, below_last, last_interior))

        return verts, faces


    def generate_uvs(self, mesh):
        """Generate simple 0-1 UV coordinates based on X,Y coordinates"""
        if not mesh.uv_layers:
            mesh.uv_layers.new(name="UVMap")

        uv_layer = mesh.uv_layers.active.data

        # Calculate bounds for normalization
        xs = [v.co.x for v in mesh.vertices]
        ys = [v.co.y for v in mesh.vertices]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        width = max_x - min_x or 1.0
        height = max_y - min_y or 1.0

        # Assign UVs
        for poly in mesh.polygons:
            for loop_idx in poly.loop_indices:
                vert_idx = mesh.loops[loop_idx].vertex_index
                v = mesh.vertices[vert_idx].co
                uv = (
                    (v.x - min_x) / width,
                    (v.y - min_y) / height
                )
                uv_layer[loop_idx].uv = uv


    def draw(self, context):
        """Draw the options panel in the dialog"""
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        # Dimensions
        layout.label(text="Dimensions:")
        col = layout.column(align=True)
        col.prop(self, "width")
        col.prop(self, "height")
        col.prop(self, "density")

        # Additional options
        layout.separator()
        layout.prop(self, "use_uv")
        layout.prop(self, "align")

        # Transformations
        layout.separator()

        col = layout.column(align=True)
        col.prop(self, "location", text="Location X", index=0)
        col.prop(self, "location", text="Y", index=1)
        col.prop(self, "location", text="Z", index=2)

        col = layout.column(align=True)
        col.prop(self, "rotation", text="Rotation X", index=0)
        col.prop(self, "rotation", text="Y", index=1)
        col.prop(self, "rotation", text="Z", index=2)
