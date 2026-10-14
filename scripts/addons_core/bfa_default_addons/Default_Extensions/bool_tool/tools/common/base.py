import bpy
import bmesh
import math
import mathutils
from bpy_extras import view3d_utils
from mathutils import Vector, Matrix

from ...functions.cutter import (
    make_cutter,
)
from ...functions.draw import (
    draw_shader,
    draw_bmesh_faces,
    draw_circle_billboard,
)
from ...functions.mesh import (
    is_instanced_mesh,
    extrude_face,
    are_intersecting,
)
from ...functions.modifier import (
    add_boolean_modifier,
    apply_modifiers,
    get_modifiers_to_apply,
)
from ...functions.object import (
    is_linked,
    set_object_origin,
    delete_object,
)
from ...functions.scene import (
    delete_empty_collection,
    raycast,
)
from ...functions.view import (
    distance_from_point_to_segment,
    region_2d_to_ray_3d,
    region_2d_to_plane_3d,
)

from .events import (
    CarverEvents,
)
from .properties import (
    CarverPropsOperator,
    CarverPropsShape,
    CarverPropsModifier,
    CarverPropsCutter,
    CarverPropsArray,
)


#### ------------------------------ CLASSES ------------------------------ ####

class CarverBase(bpy.types.Operator,
                 CarverEvents,
                 CarverPropsOperator,
                 CarverPropsShape,
                 CarverPropsModifier,
                 CarverPropsCutter,
                 CarverPropsArray):
    """Base class for Carver operators."""

    # Core Methods
    def validate_selection(self, context):
        """Filter out selection to get the list of viable canvases."""

        if context.mode == 'OBJECT':
            initial_selection = context.selected_objects
        elif context.mode == 'EDIT_MESH':
            initial_selection = context.objects_in_mode

        # Filter out selected objects that are not usable as canvases.
        selected = []
        for obj in initial_selection:
            if obj.type != 'MESH':
                continue
            if tuple(round(v, 4) for v in obj.dimensions) == (0.0, 0.0, 0.0):
                continue
            if is_linked(context, obj):
                self.report({'WARNING'}, f"{obj.name} is linked and can not be carved")
                continue

            if self.mode == 'DESTRUCTIVE':
                if is_instanced_mesh(obj.data):
                    self.report({'WARNING'}, f"Modifiers cannot be applied to {obj.name} because it has instanced object data")
                    continue

                if obj.data.shape_keys:
                    self.report({'WARNING'}, f"Modifiers cannot be applied to {obj.name} because it has shape keys")
                    continue

            selected.append(obj)

        # Ensure the active object.
        if context.active_object and context.active_object in selected:
            active = context.active_object
        else:
            if len(selected) > 0:
                active = selected[0]
            else:
                active = None

        return selected, active


    def calculate_workplane(self, context):
        """
        Calculates matrix, location (origin point), and normal (direction)
        of the workplane based on the chosen alignment method.
        """

        if self.alignment == 'SURFACE':
            matrix, location, normal = self._align_to_surface(context)

        if self.alignment == 'VIEW':
            matrix, location, normal = self._align_to_view(context)

        if self.alignment == 'GRID':
            if context.region_data.is_orthographic_side_view:
                matrix, location, normal = self._align_to_view(context)
            else:
                matrix, location, normal = self._align_to_grid(context)

        if self.alignment == 'CURSOR':
            matrix, location, normal = self._align_to_cursor(context)

        return (matrix, location, normal)


    def create_cutter(self, context):
        """Creates a cutter object with correct properties & initializes `bmesh`."""

        # Create the Mesh & bmesh
        mesh = bpy.data.meshes.new(name="boolean_cutter")
        bm = bmesh.new()

        # Create the Object
        obj = bpy.data.objects.new("boolean_cutter", mesh)
        obj.matrix_world = self.workplane.matrix
        make_cutter(context, obj, "Difference", collection=True,
                    display='WIRE' if self.shape == 'POLYLINE' else self.display)
        obj.booleans.carver = True

        # Initial Rotation
        if self.rotation != 0:
            rotation_matrix = Matrix.Rotation(self.rotation, 4, self.workplane.normal)
            rotation_matrix = rotation_matrix @ obj.matrix_world
            obj.rotation_euler = rotation_matrix.to_euler()

        # Create Verts
        if self.shape == 'BOX':
            subdivision = 4
        if self.shape == 'CIRCLE':
            subdivision = self.subdivision
        if self.shape == 'POLYLINE':
            subdivision = 2

        verts = []
        for i in range(subdivision):
            v = bm.verts.new((0, 0, 0))
            verts.append(v)

        bm.verts.ensure_lookup_table()
        bm.verts.index_update()

        # Create Face or Edge.
        if len(verts) > 2:
            face = bm.faces.new(verts)
            face.normal = self.workplane.normal
        else:
            face = None
            bm.edges.new(verts)

        # Update bmesh.
        bm.faces.ensure_lookup_table()
        bm.faces.index_update()
        bm.to_mesh(obj.data)

        return obj, mesh, bm, [face], verts


    def draw_shaders(self, context):
        """
        Creates a drawing from bmesh faces of the cutter.
        Evaluated cutter object is used to draw modifier effects as well (bevel, array).
        """

        obj = self.cutter.obj

        # Get evaluated cutter object.
        depsgraph = context.evaluated_depsgraph_get()
        eval_cutter_obj = obj.evaluated_get(depsgraph)
        eval_cutter_mesh = eval_cutter_obj.to_mesh()

        # Create temporary bmesh.
        temp_bm = bmesh.new()
        temp_bm.from_mesh(eval_cutter_mesh)
        temp_bm.faces.ensure_lookup_table()
        faces = temp_bm.faces

        # Draw Faces
        vertices, indices = draw_bmesh_faces(faces, obj.matrix_world)
        if vertices is not None and indices is not None:
            draw_shader('SOLID', (0.48, 0.04, 0.04), 0.4, vertices, indices=indices)

        # Draw Line
        if self.phase in ("BEVEL", "ROTATE", "ARRAY"):
            current_mouse_pos_3d = region_2d_to_plane_3d(context.region, context.region_data,
                                                         self.mouse.current,
                                                         (self.workplane.location, self.workplane.normal))
            if current_mouse_pos_3d is not None:
                vertices = [self.cutter.center, current_mouse_pos_3d]
                if vertices is not None:
                    draw_shader('LINES', (0.00, 0.00, 0.00), 1.0, vertices)

        # Draw circle around first vertex.
        if self.shape == 'POLYLINE' and self.phase == 'DRAW':
            verts = self.cutter.verts
            if len(verts) > 3:
                vertices = draw_circle_billboard(context,
                                                 obj.matrix_world @ verts[0].co,
                                                 radius=self._distance_from_first,
                                                 segments=4)
                if len(vertices) > 0:
                    draw_shader('LINE_LOOP', (0, 0, 0), 1.0, vertices)

        temp_bm.free()


    def update_cutter_shape(self, context):
        """Updates vertex positions of the cutter mesh based on the current mouse location."""

        region = context.region
        rv3d = context.region_data
        bm = self.cutter.bm
        face = self.cutter.faces[0]

        # Get the mouse positon x, y on the workplane.
        current_mouse_pos_3d = region_2d_to_plane_3d(region, rv3d,
                                                     self.mouse.current,
                                                     (self.workplane.location, self.workplane.normal))
        if current_mouse_pos_3d is None:
            return

        current_mouse_local = self.cutter.obj.matrix_world.inverted() @ current_mouse_pos_3d
        self.mouse.current_3d = current_mouse_local
        x, y = current_mouse_local.x, current_mouse_local.y
        if self.aspect == 'FIXED':
            y = math.copysign(abs(x), y)

        # Calculate the bounding box of the drawing to determine the origin point.
        multiplier = 2 if self.origin == 'CENTER' else 1
        size_x, size_y = x * multiplier, y * multiplier

        if self.shape == 'BOX':
            corner_signs = [
                (0, 0), # bottom-left
                (1, 0), # bottom-right
                (1, 1), # top-right
                (0, 1), # top-left
            ]

            for i, v in enumerate(face.verts):
                vert_x, vert_y = corner_signs[i]

                if self.origin == 'CENTER':
                    v.co = Vector((vert_x * size_x - size_x / 2, vert_y * size_y - size_y / 2, 0))
                elif self.origin == 'EDGE':
                    v.co = Vector((vert_x * x, vert_y * y, 0))

        if self.shape == 'CIRCLE':
            angle_step = 2 * math.pi / len(face.verts)

            for i, v in enumerate(face.verts):
                angle = i * angle_step

                vert_x = (math.cos(angle) + 1.0) * 0.5 * size_x
                vert_y = (math.sin(angle) + 1.0) * 0.5 * size_y

                if self.origin == 'CENTER':
                    v.co = Vector((vert_x - size_x / 2, vert_y - size_y / 2, 0))
                elif self.origin == 'EDGE':
                    v.co = Vector((vert_x, vert_y, 0))

        if self.shape == 'POLYLINE':
            vert = self.cutter.verts[-1]
            vert.co = Vector((x, y, 0))

        # Update Mesh & bmesh
        bm.to_mesh(self.cutter.mesh)


    def extrude_cutter(self, context):
        """
        Extrudes the original face of the cutter to create a manifold mesh.
        If the "depth" property of the operator is set to manual, the extruded face is
        left in the same position as the original (with slight offset) and its position
        is updated in `self.set_extrude_depth`. If the "depth" property is not manual,
        it's extruded according to the chosen depth calculation method.
        """

        self.mouse.extrude = self.mouse.current

        region = context.region
        rv3d = context.region_data
        normal = self.cutter.obj.matrix_world.to_3x3().inverted() @ self.workplane.normal
        location = self.cutter.obj.matrix_world.inverted() @ self.workplane.location

        obj = self.cutter.obj
        bm = self.cutter.bm
        face = self.cutter.faces[0]

        # Extrude the original face.
        extruded_verts, __, extruded_faces = extrude_face(bm, face)
        self.cutter.faces += extruded_faces

        # Automatic depth, end of the operation.
        if self.depth != 'MANUAL':
            """3D Cursor can't be both the workplane and the depth point, fall back to auto."""
            if self.alignment == 'CURSOR' and self.depth == 'CURSOR':
                self.depth = 'AUTO'

            # Push the extruded face towards the furthest point of the collective bounding box.
            if self.depth == 'AUTO':
                corners = []
                for ob in self.objects.selected:
                    corners.extend(ob.matrix_world @ Vector(c) for c in ob.bound_box)

                furthest_corner = 0.0
                for corner in corners:
                    local_corner = self.cutter.obj.matrix_world.inverted() @ corner
                    t = (local_corner - location).dot(normal)
                    if t < furthest_corner:
                        furthest_corner = t

                offset = self.offset if self.alignment == 'SURFACE' else 0.1

                for v in face.verts:
                    v.co += normal * (furthest_corner - offset)

            # Push the extruded face towards the plane of the 3D cursor.
            elif self.depth == 'CURSOR':
                local_cursor = self.cutter.obj.matrix_world.inverted() @ context.scene.cursor.location
                for v in extruded_verts:
                    distance = (local_cursor - v.co).dot(-normal)
                    v.co += -normal * distance

            # Recalculate normals.
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        # Manual depth, continuing with modal.
        else:
            """
            NOTE: Slight early offset exists to avoid two faces of the cube
            overlapping with each other, creating a non-manifold geometry and corrupting
            the Boolean modifier. Having a manifold geometry also allows us to reliably
            recalculate normals.
            """
            for v in extruded_verts:
                v.co += -normal * Vector((0.001, 0.001, 0.001))
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

            # Store values.
            self._extrude_origin = region_2d_to_plane_3d(region, rv3d,
                                                         self.mouse.extrude,
                                                         (self.workplane.location, self.workplane.normal))
            self._extrude_verts_co = [v.co.copy() for v in extruded_faces[-1].verts]
            self._extrude_faces = extruded_faces

        # Transfer vertex bevel to edge bevel.
        if getattr(self.effects, "bevel", None):
            self.effects.transfer_bevel_weights(self)

        bm.to_mesh(obj.data)
        obj.data.update()
        context.view_layer.update()

        self.phase = "EXTRUDE"


    def set_extrusion_depth(self, context):
        """Change extude depth during modal."""

        region = context.region
        rv3d = context.region_data

        # Convert the mouse position into a 3D ray and find closest points between...
        # that ray and the line coming from the extrude origin along the workplane normal.
        ray_origin, ray_direction = region_2d_to_ray_3d(region, rv3d, self.mouse.current)
        closest_points = mathutils.geometry.intersect_line_line(ray_origin,
                                                                ray_origin + ray_direction,
                                                                self._extrude_origin,
                                                                self._extrude_origin + self.workplane.normal)

        if closest_points is None:
            return

        # Calculate the distance between the extrude origin and mouse position.
        offset_vector = closest_points[1] - self._extrude_origin
        distance = offset_vector.dot(self.workplane.normal)

        # Offset vertices of the extruded face from their their original coordinates.
        normal = self.cutter.obj.matrix_world.to_3x3().inverted() @ self.workplane.normal
        if distance is not None:
            for v, vert_co in zip(self._extrude_faces[-1].verts, self._extrude_verts_co):
                offset = normal * distance
                displacement = (offset).dot(normal)

                # Don't allow moving vertices in both directions.
                if self.flip_direction:
                    if displacement < 0:
                        offset = normal * 0
                else:
                    if displacement > 0:
                        offset = normal * 0

                v.co = vert_co + offset

        self.cutter.bm.to_mesh(self.cutter.mesh)


    # Alignment Methods
    def _align_to_surface(self, context):
        """Align workplane to the surface normal under the cursor."""

        # Cast Ray
        objects = list(context.scene.objects) if self.align_to_all else self.objects.selected
        ray = raycast(context, self.mouse.initial, objects)

        # Fallback to view alignment if no surface is hit.
        if not ray.hit:
            self.alignment = 'VIEW'
            return None, None, None

        ray_obj_matrix = ray.obj.matrix_world
        mesh = ray.obj.evaluated_get(context.view_layer.depsgraph).to_mesh()

        if mesh is None:
            self.alignment = 'VIEW'
            return None, None, None

        # Create temporary `bmesh`.
        temp_bm = bmesh.new()
        temp_bm.from_mesh(mesh)
        temp_bm.faces.ensure_lookup_table()

        face = temp_bm.faces[ray.index]

        if self.orientation == 'FACE':
            # Get the tangent, normal, and bitangent from the face normal.
            tangent = face.calc_tangent_edge()
            normal = face.normal
            bitangent = normal.cross(tangent)

        elif self.orientation in ('CLOSEST_EDGE', 'LONGEST_EDGE'):
            # Get the tangent, normal, and bitangent from the longest or the closest edge of the face.

            if self.orientation == 'LONGEST_EDGE':
                lengths = [
                    (ray_obj_matrix @ edge.verts[0].co - ray_obj_matrix @ edge.verts[1].co).length
                    for edge in face.edges
                ]
                longest_edge = sorted(zip(lengths, face.edges), key=lambda x: x[0], reverse=True)[0][1]
                edge = longest_edge

            elif self.orientation == 'CLOSEST_EDGE':
                distances = [
                    distance_from_point_to_segment(
                        ray.location,
                        ray_obj_matrix @ edge.verts[0].co,
                        ray_obj_matrix @ edge.verts[1].co,
                    )
                    for edge in face.edges
                ]
                closest_edge = sorted(zip(distances, face.edges), key=lambda x: x[0])[0][1]
                edge = closest_edge

            # Get the loop (face corner) for the edge that is also in the face.
            face_corner = next(loop for loop in edge.link_loops if loop.face == face)

            start = face_corner.vert
            end = face_corner.link_loop_next.vert
            direction = (end.co - start.co)

            tangent = edge.calc_tangent(face_corner)
            normal = direction.cross(tangent)
            bitangent = normal.cross(tangent)

        # Construct Matrix
        matrix = Matrix.Identity(4)
        matrix[0].xyz = (ray_obj_matrix.to_3x3() @ tangent).normalized()
        matrix[1].xyz = (ray_obj_matrix.to_3x3() @ bitangent).normalized()
        matrix[2].xyz = (ray_obj_matrix.to_3x3() @ normal).normalized()
        matrix[3].xyz = ray.location + (ray.normal * self.offset)

        # destroy_temporary_bmesh
        temp_bm.free()
        del mesh

        matrix = matrix.transposed()
        location = ray.location + (ray.normal * self.offset)
        normal = ray.normal

        return matrix, location, normal


    def _align_to_view(self, context):
        """Align workplane to the current view."""

        region = context.region
        rv3d = context.region_data

        normal = view3d_utils.region_2d_to_vector_3d(region, rv3d, self.mouse.initial).normalized()

        if len(self.objects.selected) == 0:
            # Put the location at the 3D cursor position.
            location = view3d_utils.region_2d_to_location_3d(region, rv3d,
                                                             self.mouse.current,
                                                             context.scene.cursor.location)
        else:
            # Put the location at the closest point of the bounding box of all selected objects.
            ray_origin, ray_direction = region_2d_to_ray_3d(region, rv3d, self.mouse.initial)

            corners = []
            for obj in self.objects.selected:
                corners.extend(obj.matrix_world @ Vector(c) for c in obj.bound_box)

            closest = min(corners, key=lambda c: (c - ray_origin).dot(ray_direction))
            t = (closest - ray_origin).dot(normal)
            location = ray_origin + normal * (t - 0.1)

        # Construct the world-space matrix.
        matrix = rv3d.view_matrix.inverted().to_3x3().to_4x4()
        matrix.translation = location

        return matrix, location, -normal


    def _align_to_grid(self, context):
        """Align workplane to the world grid."""

        region = context.region
        rv3d = context.region_data

        matrix = Matrix.Identity(4)
        normal = matrix.col[2].xyz

        ray_origin, ray_direction = region_2d_to_ray_3d(region, rv3d, self.mouse.initial)
        t = (matrix.translation.z - ray_origin.z) / ray_direction.z
        location = ray_origin + ray_direction * t
        matrix.translation = location

        return matrix, location, -normal


    def _align_to_cursor(self, context):
        """Align workplane to the 3D cursor orientation."""

        region = context.region
        rv3d = context.region_data
        cursor = context.scene.cursor

        matrix = cursor.matrix.copy()

        if self.alignment_axis == 'X':
            """TODO: Aligning on actual X axis doesn't work, possible bug in `intersect_line_plane`."""
            normal = matrix.col[1].xyz
        elif self.alignment_axis == 'Y':
            normal = matrix.col[1].xyz
        elif self.alignment_axis == 'Z':
            normal = matrix.col[2].xyz

        location = region_2d_to_plane_3d(region, rv3d,
                                         self.mouse.initial,
                                         (matrix.translation, normal))

        # Regrettable fallback for orthographic side views when cursor is at world origin.
        if location is None:
            location = 0

        matrix.translation = location

        return matrix, location, normal


    # Finalization Methods
    def Cut(self, context):
        """
        Add Boolean modifiers on selected objects.
        NOTE: The operator may or may not end after this step. Shouldn't be treated as a final step.
        """

        cutter = self.cutter.obj

        for obj in self.objects.selected:
            mod = add_boolean_modifier(self, context, obj,
                                       cutter, "DIFFERENCE",
                                       self.solver, pin=self.pin, redo=False)
            self.objects.modifiers[obj] = mod


    def confirm(self, context):
        """
        Final set of steps for successfully finished operations.
        Applying modifiers in the "Destructive" mode, and preparing
        the cutter and canvas objects in the "Modifier" mode.
        """

        cutter = self.cutter.obj

        # Remove modifiers from selected objects that don't intersect with the cutter.
        intersecting_canvases = []
        for obj, mod in self.objects.modifiers.items():
            if are_intersecting(obj, cutter):
                intersecting_canvases.append(obj)
            else:
                obj.modifiers.remove(mod)

        if not intersecting_canvases:
            self.finalize(context)
            return

        # Select all faces of the cutter so that newly created faces in canvas
        # are also selected after applying the modifier.
        for face in self.cutter.mesh.polygons:
            face.select = True

        if self.mode == 'MODIFIER':
            cutter.display_type = self.display

            # Set the object origin of the cutter.
            if self.cutter_origin == 'FACE_CENTER':
                point = 'CUSTOM'
                custom = self.cutter.faces[0].calc_center_median()
            elif self.cutter_origin == 'MOUSE_INITIAL':
                point = 'CUSTOM'
                initial_mouse_pos_3d = region_2d_to_plane_3d(context.region, context.region_data,
                                                             self.mouse.initial,
                                                             (self.workplane.location, self.workplane.normal))
                custom = cutter.matrix_world.inverted() @ initial_mouse_pos_3d
            elif self.cutter_origin == 'CANVAS':
                point = 'CUSTOM'
                custom = cutter.matrix_world.inverted() @ self.objects.active.matrix_world.translation
            else:
                point = self.cutter_origin
                custom = None

            set_object_origin(cutter, self.cutter.bm, point=point, custom=custom)

            # Parent cutter to canvas.
            if self.parent:
                cutter.parent = self.objects.active
                cutter.matrix_parent_inverse = self.objects.active.matrix_world.inverted()

            # Hide cutter.
            if self.hide:
                cutter.hide_set(True)

            # Set Boolean properties to canvases.
            for obj in intersecting_canvases:
                obj.booleans.canvas = True

            self.finalize(context, clean_up=False)
            return

        elif self.mode == 'DESTRUCTIVE':
            # Apply modifiers & delete the cutter.
            for obj, modifiers in self.objects.modifiers.items():
                if obj in intersecting_canvases:
                    modifiers = get_modifiers_to_apply(context, obj, [modifiers])
                    apply_modifiers(context, obj, modifiers, force_clean=True)

            self.finalize(context)
            return


    def finalize(self, context, clean_up=True, abort=False):
        """
        Finalize and clean-up after the operation ends.
        Regardless of whether it was confirmed or cancelled.
        """

        # Operation was aborted, or successfully finished in the Destructive mode.
        # Delete everything created by the operator (i.e. cutter).
        if clean_up:
            delete_object(self.cutter.obj)
            self.cutter.bm.free()
            delete_empty_collection(context)

            # Remove modifiers added by the operator.
            if abort:
                for obj, mod in self.objects.modifiers.items():
                    obj.modifiers.remove(mod)

        # Clean-up temporary changes made by operator.
        if self.effects.array:
            self.effects.array.use_pin_to_last = False

        bpy.types.SpaceView3D.draw_handler_remove(self._handler, 'WINDOW')
        context.workspace.status_text_set(None)
        context.window.cursor_set('DEFAULT' if context.mode == 'OBJECT' else 'CROSSHAIR')
