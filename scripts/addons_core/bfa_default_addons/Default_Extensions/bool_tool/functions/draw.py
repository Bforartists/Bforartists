import bpy, gpu, mathutils, math
from gpu_extras.batch import batch_for_shader
from bpy_extras import view3d_utils

magic_number = 1.41

#### ------------------------------ FUNCTIONS ------------------------------ ####

def draw_shader(color, alpha, type, coords, size=1, indices=None):
    """Creates a batch for a draw type"""

    gpu.state.blend_set('ALPHA')

    if type == 'POINTS':
        gpu.state.program_point_size_set(False)
        gpu.state.point_size_set(size)
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        shader.uniform_float("color", (color[0], color[1], color[2], alpha))
        batch = batch_for_shader(shader, type, {"pos": coords}, indices=indices)

    elif type in ('LINES', 'LINE_LOOP'):
        shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        shader.uniform_float("viewportSize", gpu.state.viewport_get()[2:])
        shader.uniform_float("lineWidth", size)
        shader.uniform_float("color", (color[0], color[1], color[2], alpha))
        batch = batch_for_shader(shader, type, {"pos": coords}, indices=indices)

    if type == 'SOLID':
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        shader.uniform_float("color", (color[0], color[1], color[2], alpha))
        batch = batch_for_shader(shader, 'TRIS', {"pos": coords}, indices=indices)

    if type == 'OUTLINE':
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        shader.uniform_float("color", (color[0], color[1], color[2], alpha))
        batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": coords})
        gpu.state.line_width_set(size)

    batch.draw(shader)
    gpu.state.point_size_set(1.0)
    gpu.state.blend_set('NONE')


def carver_overlay(self, context):
    """Shape (rectangle, circle) overlay for carver tool"""

    color = (0.48, 0.04, 0.04, 1.0)
    secondary_color = (0.28, 0.04, 0.04, 1.0)

    if self.shape == 'CIRCLE':
        coords, indices, rows, columns = draw_circle(self, self.subdivision, 0)
        # coords = coords[1:] # remove_extra_vertex
        self.verts = coords
        self.duplicates = {**{f"row_{k}": v for k, v in rows.items()}, **{f"column_{k}": v for k, v in columns.items()}}

        draw_shader(color, 0.4, 'SOLID', coords, size=2, indices=indices[:-2])
        if not self.rotate:
            bounds, __, __ = get_bounding_box_coords(self, coords)
            draw_shader(color, 0.6, 'OUTLINE', bounds, size=2)


    elif self.shape == 'BOX':
        coords, indices, rows, columns = draw_circle(self, 4, 45)
        self.verts = coords
        self.duplicates = {**{f"row_{k}": v for k, v in rows.items()}, **{f"column_{k}": v for k, v in columns.items()}}

        draw_shader(color, 0.4, 'SOLID', coords, size=2, indices=indices[:-2])
        if (self.rotate == False) and (self.bevel == False):
            bounds, __, __ = get_bounding_box_coords(self, coords)
            draw_shader(color, 0.6, 'OUTLINE', bounds, size=2)


    elif self.shape == 'POLYLINE':
        coords, indices, first_point, rows, columns = draw_polygon(self)
        self.verts = list(dict.fromkeys(self.mouse_path))
        self.duplicates = {**{f"row_{k}": v for k, v in rows.items()}, **{f"column_{k}": v for k, v in columns.items()}}

        draw_shader(color, 1.0, 'LINE_LOOP' if self.closed else 'LINES', coords, size=2)
        draw_shader(color, 1.0, 'POINTS', coords, size=5)
        if self.closed and len(self.mouse_path) > 2:
            # polygon_fill
            draw_shader(color, 0.4, 'SOLID', coords, size=2, indices=indices[:-2])

        if (self.closed and len(coords) > 3) or (self.closed == False and len(coords) > 4):
            # circle_around_first_point
            draw_shader(color, 0.8, 'OUTLINE', first_point, size=3)


    # Snapping Grid
    if self.snap and self.move == False:
        mini_grid(self, context)

    # ARRAY
    array_shader = 'LINE_LOOP' if self.shape == 'POLYLINE' and self.closed == False else 'SOLID'
    if self.rows > 1:
        for i, duplicate in rows.items():
            draw_shader(secondary_color, 0.4, array_shader, duplicate, size=2, indices=indices[:-2])
    if self.columns > 1:
        for i, duplicate in columns.items():
            draw_shader(secondary_color, 0.4, array_shader, duplicate, size=2, indices=indices[:-2])

    gpu.state.blend_set('NONE')


def draw_polygon(self):
    """Returns polygonal 2d shape in which each cursor click is taken as a new vertice"""

    indices = []
    coords = []
    for idx, vals in enumerate(self.mouse_path):
        vert = mathutils.Vector([vals[0], vals[1], 0.0])
        vert += mathutils.Vector([self.position_x, self.position_y, 0.0])
        coords.append(vert)

        i1 = idx + 1
        i2 = idx + 2 if idx <= len(self.mouse_path) else 1
        indices.append((0, i1, i2))

    # circle_around_first_point
    radius = self.distance_from_first
    segments = 4

    click_point = [coords[0]]
    for i in range(segments + 1):
        angle = i * (2 * math.pi / segments)
        x = coords[0][0] + radius * math.cos(angle)
        y = coords[0][1] + radius * math.sin(angle)
        z = coords[0][2]
        vector = mathutils.Vector((x, y, z))
        click_point.append(vector)

    # remove_duplicate_verts
    # NOTE: This is needed to remove extra vertices for duplicates which are not removed because `dict.fromkeys()`...
    # NOTE: can't be called on `coords` list, because it contains unfrozen Vectors.
    unique_verts = []
    for vert in coords:
        if vert not in unique_verts:
            unique_verts.append(vert)


    # ARRAY
    rows = columns = {}
    if len(self.mouse_path) > 2:
        array_coords = unique_verts if self.closed else unique_verts[:-1]
        get_bounding_box_coords(self, array_coords)
        rows, columns = array(self, array_coords)

    return coords, indices, click_point, rows, columns


def draw_circle(self, subdivision, rotation):
    """Returns the coordinates & indices of a circle using a triangle fan"""
    """NOTE: Origin point code is duplicated on purpose (to experiment with different math easily)"""

    def create_2d_circle(self, step, rotation):
        """Create the vertices of a 2d circle at (0, 0)"""

        modifier = 2 if self.shape == 'CIRCLE' else magic_number
        if self.origin == 'CENTER':
            modifier /= 2

        verts = []
        for i in range(step):
            angle = (360 / step) * i + rotation
            verts.append(math.cos(math.radians(angle)) * ((self.mouse_path[1][0] - self.mouse_path[0][0]) / modifier))
            verts.append(math.sin(math.radians(angle)) * ((self.mouse_path[1][1] - self.mouse_path[0][1]) / modifier))
            verts.append(0.0)

        verts.append(math.cos(math.radians(0.0 + rotation)) * ((self.mouse_path[1][0] - self.mouse_path[0][0]) / modifier))
        verts.append(math.sin(math.radians(0.0 + rotation)) * ((self.mouse_path[1][1] - self.mouse_path[0][1]) / modifier))
        verts.append(0.0)

        return verts

    tris_verts = []
    indices = []
    verts = create_2d_circle(self, int(subdivision), rotation)

    rotation_matrix = mathutils.Matrix.Rotation(self.rotation, 4, 'Z')
    fixed_point = mathutils.Vector((self.mouse_path[0][0], self.mouse_path[0][1], 0.0))
    current_mouse_position = mathutils.Vector((self.mouse_path[1][0], self.mouse_path[1][1], 0.0))
    shape_center = fixed_point + (current_mouse_position - fixed_point) / 2

    min_x = min(verts[0::3]) if self.mouse_path[1][0] > self.mouse_path[0][0] else -min(verts[0::3])
    min_y = min(verts[1::3]) if self.mouse_path[1][1] > self.mouse_path[0][1] else -min(verts[1::3])

    for idx in range((len(verts) // 3) - 1):
        x = verts[idx * 3]
        y = verts[idx * 3 + 1]
        z = verts[idx * 3 + 2]
        vert = mathutils.Vector((x, y, z))
        vert = rotation_matrix @ vert
        vert = vert + fixed_point if self.origin == 'CENTER' else shape_center - vert
        vert += mathutils.Vector((self.position_x, self.position_y, 0.0))
        tris_verts.append(vert)

        i1 = idx + 1
        i2 = idx + 2 if idx + 2 <= ((360 / int(subdivision)) * (idx + 1) + rotation) else 1
        indices.append((0, i1, i2))


    # BEVEL
    if self.use_bevel and self.bevel_radius > 0.01:
        tris_verts, indices = bevel_verts(self, tris_verts, (self.bevel_radius * 50), self.bevel_segments)

    # ARRAY
    rows, columns = array(self, tris_verts)

    return tris_verts, indices, rows, columns


def mini_grid(self, context):
    """Draws snap mini-grid around the cursor based on the overlay grid"""

    region = context.region
    rv3d = context.region_data

    for i, a in enumerate(context.screen.areas):
        if a.type == 'VIEW_3D':
            space = context.screen.areas[i].spaces.active
            screen_height = context.screen.areas[i].height
            screen_width = context.screen.areas[i].width

    # draw_the_snap_grid_(only_in_the_orthographic_view)
    if not space.region_3d.is_perspective:
        grid_scale = space.overlay.grid_scale
        grid_subdivisions = space.overlay.grid_subdivisions
        increment = (grid_scale / grid_subdivisions)

        # get_the_3d_location_of_the_mouse_forced_to_a_snap_value_in_the_operator
        mouse_coord = self.mouse_path[len(self.mouse_path) - 1]
        snap_loc = view3d_utils.region_2d_to_location_3d(region, rv3d, mouse_coord, (0, 0, 0))

        # add_the_increment_to_get_the_closest_location_on_the_grid
        snap_loc[0] += increment
        snap_loc[1] += increment

        # get_the_2d_location_of_the_snap_location
        snap_loc = view3d_utils.location_3d_to_region_2d(region, rv3d, snap_loc)

        # get_the_increment_value
        snap_value = snap_loc[0] - mouse_coord[0]

        # draw_lines_on_x_and_z_axis_from_the_cursor_through_the_screen
        grid_coords = [(0, mouse_coord[1]), (screen_width, mouse_coord[1]),
                        (mouse_coord[0], 0), (mouse_coord[0], screen_height)]

        grid_coords += [(mouse_coord[0] + snap_value, mouse_coord[1] + 25 + snap_value),
                        (mouse_coord[0] + snap_value, mouse_coord[1] - 25 - snap_value),
                        (mouse_coord[0] + 25 + snap_value, mouse_coord[1] + snap_value),
                        (mouse_coord[0] - 25 - snap_value, mouse_coord[1] + snap_value),
                        (mouse_coord[0] - snap_value, mouse_coord[1] + 25 + snap_value),
                        (mouse_coord[0] - snap_value, mouse_coord[1] - 25 - snap_value),
                        (mouse_coord[0] + 25 + snap_value, mouse_coord[1] - snap_value),
                        (mouse_coord[0] - 25 - snap_value, mouse_coord[1] - snap_value),]

        draw_shader((1.0, 1.0, 1.0), 0.66, 'LINES', grid_coords, size=1.5)


def get_bounding_box_coords(self, verts):
    """Calculates the bounding box coordinates from a list of vertices in a counter-clockwise order"""

    min_x = min(v[0] for v in verts)
    max_x = max(v[0] for v in verts)
    min_y = min(v[1] for v in verts)
    max_y = max(v[1] for v in verts)
    self.center_origin = [(min_x, min_y), (max_x, max_y)]

    bounding_box_coords = [
        mathutils.Vector((min_x, min_y, 0)),  # bottom-left
        mathutils.Vector((max_x, min_y, 0)),  # bottom-right
        mathutils.Vector((max_x, max_y, 0)),  # top-right
        mathutils.Vector((min_x, max_y, 0)),  # top-left
        mathutils.Vector((min_x, min_y, 0))   # closing_the_loop_manually
    ]

    width = max_x - min_x
    height = max_y - min_y

    return bounding_box_coords, width, height


def array(self, verts):
    """Duplicates given list of vertices in rows and columns (on x and y axis)"""
    """Returns two dicts of lists of vertices for rows and columns separately"""

    # ensure_bounding_box_(needed_when_array_is_set_before_original_is_drawn)
    if len(self.center_origin) == 0:
        get_bounding_box_coords(self, verts)

    rows = {}
    if self.rows > 1:
        # Offset
        offset = mathutils.Vector((((self.center_origin[1][0] - self.center_origin[0][0]) + (self.rows_gap)), 0.0, 0.0))
        if self.rows_direction == 'LEFT':
            offset.x = -offset.x

        for i in range(self.rows - 1):
            accumulated_offset = offset * (i + 1)
            rows[i] = [vert.copy() + accumulated_offset for vert in verts]

    columns = {}
    if self.columns > 1:
        # Offset
        offset = mathutils.Vector((0.0, -((self.center_origin[1][1] - self.center_origin[0][1]) + (self.columns_gap)), 0.0))
        if self.columns_direction == 'UP':
            offset.y = -offset.y

        for i in range(self.columns - 1):
            accumulated_offset = offset * (i + 1)
            columns[i] = [vert.copy() + accumulated_offset for vert in verts]
            for row_idx, row in rows.items():
                columns[(i, row_idx)] = [vert.copy() + accumulated_offset for vert in row]

    return rows, columns


def bevel_verts(self, verts, radius, segments):
    """Takes in list of verts(Vectors) and bevels them, Returns a new list with new vertices"""

    def get_rounded_corner(self, angular_point, p1, p2, radius, segments):
        # clamp_radius_to_reduce_clipping
        __, width, height = get_bounding_box_coords(self, verts)
        max_radius = min(width / 2.5, height / 2.5)
        clamped_radius = min(radius, max_radius)

        if radius > clamped_radius:
            radius = clamped_radius


        # calculate_vectors (NOTE: Why it only works when reversed like this is unknown to me)
        if self.bevel_profile == 'CONVEX':
            vector1 = -(p1 - angular_point)
            vector2 = -(p2 - angular_point)
        elif self.bevel_profile == 'CONCAVE':
            vector1 = p2 - angular_point
            vector2 = p1 - angular_point

        # compute_lengths_of_vectors
        length1 = vector1.length
        length2 = vector2.length
        if length1 == 0 or length2 == 0:
            return [angular_point] * segments

        vector1.normalize()
        vector2.normalize()

        # calculate_the_angle_between_the_vectors
        dot_product = vector1.dot(vector2)
        angle = math.acos(max(-1.0, min(1.0, dot_product)))

        arc_length = radius * angle
        segment_length = arc_length / (segments - 1)
        bisector = (vector1 + vector2).normalized()

        # generate_points_along_the_arc
        rounded_corners = []
        for i in range(segments):
            fraction = i / (segments - 1)
            theta = angle * fraction
            interpolated_vector = (vector1 * math.sin(theta) + vector2 * math.cos(theta)).normalized() * radius
            if self.bevel_profile == 'CONVEX':
                point_on_arc = angular_point + interpolated_vector - bisector * (clamped_radius * magic_number)
            elif self.bevel_profile == 'CONCAVE':
                point_on_arc = angular_point + interpolated_vector - bisector / (clamped_radius)
            rounded_corners.append(point_on_arc)

        return rounded_corners

    rounded_verts = []
    indices = []
    num_verts = len(verts)

    for idx in range(num_verts):
        angular_point = verts[idx]
        prev_idx = (idx - 1) % num_verts
        next_idx = (idx + 1) % num_verts

        p1 = verts[prev_idx]
        p2 = verts[next_idx]

        corner_points = get_rounded_corner(self, angular_point, p1, p2, radius, segments)
        rounded_verts.extend(corner_points)

    for idx, vert in enumerate(reversed(rounded_verts)):
        i1 = idx + 1
        i2 = idx + 2 if idx + 2 <= len(rounded_verts) else 1
        indices.append((0, i1, i2))

    return rounded_verts, indices
