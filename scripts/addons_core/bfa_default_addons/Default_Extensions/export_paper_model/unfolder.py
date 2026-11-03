# unfolder.py: processing of geometry and representation of the resulting net

# todo: rename neighbor_left, neighbor_right -> neighbor_next, neighbor_prev

import os.path as os_path
from functools import cached_property
from itertools import chain, product, combinations
from math import pi, atan2, hypot, radians
import bpy
import bmesh
from mathutils import Matrix, Vector
from mathutils.geometry import convex_hull_2d

from .nesting import get_nester

default_priority_effect = {
    'CONVEX': 0.5,
    'CONCAVE': 1,
    'LENGTH': -0.05
}

obtuse_angle = radians(105)

def is_upsidedown_wrong(name):
    """Tell if the string would get a different meaning if written upside down"""
    chars = set(name)
    mistakable = set("69NZMWpbqd")
    rotatable = set("80oOxXIl").union(mistakable)
    return chars.issubset(rotatable) and not chars.isdisjoint(mistakable)


def pairs(sequence):
    """Generate consecutive pairs throughout the given sequence; at last, it gives elements last, first."""
    i = iter(sequence)
    previous = first = next(i)
    for this in i:
        yield previous, this
        previous = this
    yield this, first


def sin_from_cos(cos):
    return (1 - cos**2)**0.5 if abs(cos) < 1 else 0


def rotation_matrix(sin, cos):
    return Matrix(((cos, -sin), (sin, cos)))


def fitting_matrix(v1, v2):
    """Get a matrix that rotates v1 to the same direction as v2"""
    return (1 / v1.length_squared) * rotation_matrix(v1.x*v2.y - v1.y*v2.x, v1.x*v2.x + v1.y*v2.y)


def rot90(vec):
    return Vector((vec.y, -vec.x))


def z_up_matrix(n):
    """Get a rotation matrix that aligns given vector upwards."""
    b = n.xy.length
    s = n.length
    if b > 0:
        return Matrix((
            (n.x*n.z/(b*s), n.y*n.z/(b*s), -b/s),
            (-n.y/b, n.x/b, 0),
            (0, 0, 0)
        ))
    # no need for rotation
    return Matrix((
        (1, 0, 0),
        (0, (-1 if n.z < 0 else 1), 0),
        (0, 0, 0)
    ))


def cage_fit(points, aspect):
    """Find rotation for a minimum bounding box with a given aspect ratio
    returns a tuple: rotation angle, box height"""
    def guesses(polygon):
        """Yield all tentative extrema of the bounding box height wrt. polygon rotation"""
        for a, b in pairs(polygon):
            if a == b:
                continue
            direction = (b - a).normalized()
            sinx, cosx = -direction.y, direction.x
            rot = rotation_matrix(sinx, cosx)
            rot_polygon = [rot @ p for p in polygon]
            left, right = [fn(rot_polygon, key=lambda p: p.to_tuple()) for fn in (min, max)]
            bottom, top = [fn(rot_polygon, key=lambda p: p.yx.to_tuple()) for fn in (min, max)]
            horz, vert = right - left, top - bottom
            # solve (rot * a).y == (rot * b).y
            yield max(aspect * horz.x, vert.y), sinx, cosx
            # solve (rot * a).x == (rot * b).x
            yield max(horz.x, aspect * vert.y), -cosx, sinx
            # solve aspect * (rot * (right - left)).x == (rot * (top - bottom)).y
            # using substitution t = tan(rot / 2)
            q = aspect * horz.x - vert.y
            r = vert.x + aspect * horz.y
            t = (hypot(q, r) - r) / q if q != 0 else 0
            t = -1 / t if abs(t) > 1 else t  # pick the positive solution
            siny, cosy = 2 * t / (1 + t**2), (1 - t**2) / (1 + t**2)
            rot = rotation_matrix(siny, cosy)
            for p in rot_polygon:
                p[:] = rot @ p  # note: this also modifies left, right, bottom, top
            if left.x < right.x and bottom.y < top.y and all(left.x <= p.x <= right.x and bottom.y <= p.y <= top.y for p in rot_polygon):
                yield max(aspect * (right - left).x, (top - bottom).y), sinx*cosy + cosx*siny, cosx*cosy - sinx*siny
    polygon = [points[i] for i in convex_hull_2d(points)]
    height, sinx, cosx = min(guesses(polygon))
    return height, sinx, cosx


def paginate_islands(islands, cage_size, method='CUSTOM'):  # -> pages
    """Move and rotate islands so that they fit onto pages, based on their bounding boxes"""
    if any(island.bounding_box.x > cage_size.x or island.bounding_box.y > cage_size.y for island in islands):
        raise UnfoldError(
            "An island is too big to fit onto page of the given size. "
            "Either downscale the model or find and split that island manually.\n"
            "Export failed, sorry.")
    fn = get_nester(method)
    return fn(islands, cage_size)


def create_blank_image(image_name, dimensions, alpha=1):
    """Create a new image and assign white color to all its pixels"""
    image_name = image_name[:64]
    width, height = int(dimensions.x), int(dimensions.y)
    image = bpy.data.images.new(image_name, width, height, alpha=True)
    if image.users > 0:
        raise UnfoldError(
            "There is something wrong with the material of the model. "
            "Please report this on the BlenderArtists forum. Export failed.")
    image.pixels = [1, 1, 1, alpha] * (width * height)
    image.file_format = 'PNG'
    return image


def store_rna_properties(*datablocks):
    return [{prop.identifier: getattr(data, prop.identifier) for prop in data.rna_type.properties if not prop.is_readonly} for data in datablocks]


def apply_rna_properties(memory, *datablocks):
    for recall, data in zip(memory, datablocks):
        for key, value in recall.items():
            setattr(data, key, value)


class UnfoldError(ValueError):
    def mesh_select(self):
        if len(self.args) >= 3:
            elems, bm = self.args[1:3]
            bpy.context.tool_settings.mesh_select_mode = [bool(elems[key]) for key in ("verts", "edges", "faces")]
            for elem in chain(bm.verts, bm.edges, bm.faces):
                elem.select = False
            for elem in chain(*elems.values()):
                elem.select_set(True)
            bmesh.update_edit_mesh(bpy.context.object.data, loop_triangles=False, destructive=False)

    def __str__(self):
        return f'{type(self).__name__}("""{self.args[0]}""")'


class Unfolder:
    def __init__(self, ob):
        self.do_create_uvmap = False
        bm = bmesh.from_edit_mesh(ob.data)
        self.mesh = Mesh(bm, ob.matrix_world)
        # api bug workaround to make mesh.save_uv work correctly
        # (the bug is that BMLoop[BMLayerItem] always modifies the active layer)
        ob.data.uv_layers.active = ob.data.uv_layers[self.mesh.looptex.name]

    def __del__(self):
        if not self.do_create_uvmap:
            self.mesh.delete_uvmap()

    def prepare(self, cage_size=None, priority_effect=default_priority_effect, scale=1, limit_by_page=False):
        """Create the islands of the net"""
        self.mesh.check_correct()
        self.mesh.generate_cuts(cage_size / scale if limit_by_page and cage_size else None, priority_effect)
        self.mesh.finalize_islands(cage_size or Vector((1, 1)))
        self.mesh.enumerate_islands()
        self.mesh.save_uv()

    def copy_island_names(self, island_list):
        """Copy island label and abbreviation from the best matching island in the list"""
        orig_islands = [{face.id for face in item.faces} for item in island_list]
        matching = []
        for i, island in enumerate(self.mesh.islands):
            islfaces = {face.index for face in island.faces}
            matching.extend((len(islfaces.intersection(item)), i, j) for j, item in enumerate(orig_islands))
        matching.sort(reverse=True)
        available_new = [True for island in self.mesh.islands]
        available_orig = [True for item in island_list]
        for face_count, i, j in matching:
            if available_new[i] and available_orig[j]:
                available_new[i] = available_orig[j] = False
                self.mesh.islands[i].label = island_list[j].label
                self.mesh.islands[i].abbreviation = island_list[j].abbreviation

    def save(self, properties, exporter):
        """Export the document"""
        # Note about scale: input is directly in blender length
        # Mesh.scale_islands multiplies everything by a user-defined ratio
        # exporters (SVG or PDF) multiply everything by 1000 (output in millimeters)
        filepath = properties.filepath
        extension = properties.file_format.lower()
        filepath = bpy.path.ensure_ext(filepath, "." + extension)
        # page size in meters
        page_size = Vector((properties.output_size_x, properties.output_size_y))
        # printable area size in meters
        printable_size = page_size - 2 * properties.output_margin * Vector((1, 1))
        unit_scale = bpy.context.scene.unit_settings.scale_length
        ppm = properties.output_dpi * 100 / 2.54  # pixels per meter

        # after this call, all dimensions will be in meters
        self.mesh.scale_islands(unit_scale/properties.scale)
        if properties.tab_style == 'STICKER':
            self.mesh.generate_stickers(properties.sticker_width, properties.number_style, properties.paper_thickness)
        elif properties.number_style != 'NONE':
            self.mesh.generate_numbers_alone(properties.sticker_width, properties.number_style == 'INSIDE')

        text_height = properties.sticker_width if (properties.number_style != 'NONE' and len(self.mesh.islands) > 1) else 0
        # title height must be somewhat larger that text size, glyphs go below the baseline
        self.mesh.finalize_islands(printable_size, title_height=text_height * 1.2)
        self.mesh.pages = paginate_islands(self.mesh.islands, printable_size, properties.nesting_method)

        if properties.texture_type != 'NONE':
            # bake an image and save it as a PNG to disk or into memory
            image_packing = properties.image_packing if properties.file_format == 'SVG' else 'ISLAND_EMBED'
            use_separate_images = image_packing in ('ISLAND_LINK', 'ISLAND_EMBED')
            self.mesh.save_uv(cage_size=printable_size, separate_image=use_separate_images)

            sce = bpy.context.scene
            rd = sce.render
            bk = rd.bake
            recall = store_rna_properties(rd, bk, sce.cycles)
            rd.engine = 'CYCLES'
            for p in ('color', 'diffuse', 'direct', 'emit', 'glossy', 'indirect', 'transmission'):
                setattr(bk, f"use_pass_{p}", (properties.texture_type != 'TEXTURE'))
            lookup = {'TEXTURE': 'DIFFUSE', 'AMBIENT_OCCLUSION': 'AO', 'RENDER': 'COMBINED', 'SELECTED_TO_ACTIVE': 'COMBINED'}
            sce.cycles.bake_type = lookup[properties.texture_type]
            bk.use_selected_to_active = (properties.texture_type == 'SELECTED_TO_ACTIVE')
            bk.margin, bk.cage_extrusion, bk.use_cage, bk.use_clear = 1, 10, False, False
            if properties.texture_type == 'TEXTURE':
                bk.use_pass_direct, bk.use_pass_indirect, bk.use_pass_color = False, False, True
                sce.cycles.samples = 1
            else:
                sce.cycles.samples = properties.bake_samples
            if sce.cycles.bake_type == 'COMBINED':
                bk.use_pass_direct, bk.use_pass_indirect = True, True
                bk.use_pass_diffuse, bk.use_pass_glossy, bk.use_pass_transmission, bk.use_pass_emit = True, False, False, True

            if image_packing == 'PAGE_LINK':
                self.mesh.save_image(printable_size * ppm, filepath)
            elif image_packing == 'ISLAND_LINK':
                image_dir = filepath[:filepath.rfind(".")]
                self.mesh.save_separate_images(ppm, image_dir)
            elif image_packing == 'ISLAND_EMBED':
                self.mesh.save_separate_images(ppm, filepath, embed=exporter.encode_image)

            apply_rna_properties(recall, rd, bk, sce.cycles)
        exporter.write(self.mesh, filepath)


class Mesh:
    """Wrapper for Bpy BMesh"""

    # see BMesh documentation for info about loops, edges etc.: https://developer.blender.org/docs/features/objects/mesh/bmesh/
    def __init__(self, bm, matrix):
        self.data = bm
        self.matrix = matrix.to_3x3()
        self.looptex = bm.loops.layers.uv.new("Unfolded")
        edge_layers = bm.edges.layers.bool
        freestyle_layer = edge_layers.get("freestyle_edge")
        self.edges = {bmedge: Edge(bmedge, freestyle_layer) for bmedge in bm.edges}
        self.islands = []
        self.pages = []
        for edge in self.edges.values():
            edge.choose_main_faces()
            if edge.main_faces:
                edge.calculate_angle()

    def delete_uvmap(self):
        if self.looptex:
            self.data.loops.layers.uv.remove(self.looptex)

    def mark_cuts(self):
        for bmedge, edge in self.edges.items():
            if edge.is_main_cut and not bmedge.is_boundary:
                bmedge.seam = True

    def check_correct(self, epsilon=1e-6):
        """Check for invalid geometry"""
        def is_twisted(face):
            if len(face.verts) <= 3:
                return False
            center = face.calc_center_median()
            plane_d = center.dot(face.normal)
            diameter = max((center - vertex.co).length for vertex in face.verts)
            threshold = 0.01 * diameter
            return any(abs(v.co.dot(face.normal) - plane_d) > threshold for v in face.verts)

        null_edges = {e for e in self.edges.keys() if e.calc_length() < epsilon and e.link_faces}
        null_faces = {f for f in self.data.faces if f.calc_area() < epsilon}
        twisted_faces = {f for f in self.data.faces if is_twisted(f)}
        inverted_scale = self.matrix.determinant() <= 0
        if not (null_edges or null_faces or twisted_faces or inverted_scale):
            return True
        if inverted_scale:
            raise UnfoldError(
                "The object is flipped inside-out.\n"
                "You can use Object -> Apply -> Scale to fix it. Export failed.")
        disease = [("Remove Doubles", null_edges or null_faces), ("Triangulate", twisted_faces)]
        cure = " and ".join(s for s, k in disease if k)
        raise UnfoldError(
            "The model contains:\n" +
            (f" {len(null_edges)} zero-length edge(s)\n" if null_edges else "") +
            (f" {len(null_faces)} zero-area face(s)\n" if null_faces else "") +
            (f" {len(twisted_faces)} twisted polygon(s)\n" if twisted_faces else "") +
            f"The offenders are selected and you can use {cure} to fix them. Export failed.",
            {"verts": set(), "edges": null_edges, "faces": null_faces | twisted_faces}, self.data)

    def generate_cuts(self, page_size, priority_effect):
        """Cut the mesh so that it can be unfolded to a flat net."""
        normal_matrix = self.matrix.inverted().transposed()
        islands = {Island(self, face, self.matrix, normal_matrix) for face in self.data.faces}
        uvfaces = {face: uvface for island in islands for face, uvface in island.faces.items()}
        uvedges = {loop: uvedge for island in islands for loop, uvedge in island.edges.items()}
        for loop, uvedge in uvedges.items():
            self.edges[loop.edge].uvedges.append(uvedge)
        # check for edges that are cut permanently
        edges = [edge for edge in self.edges.values() if not edge.force_cut and edge.main_faces]

        if edges:
            average_length = sum(edge.vector.length for edge in edges) / len(edges)
            for edge in edges:
                edge.generate_priority(priority_effect, average_length)
            edges.sort(reverse=False, key=lambda edge: edge.priority)
            for edge in edges:
                if not edge.vector:
                    continue
                edge_a, edge_b = (uvedges[l] for l in edge.main_faces)
                old_island = join(edge_a, edge_b, size_limit=page_size)
                if old_island:
                    islands.remove(old_island)

        self.islands = sorted(islands, reverse=True, key=lambda island: len(island.faces))

        for edge in self.edges.values():
            # some edges did not know until now whether their angle is convex or concave
            if edge.main_faces and (uvfaces[edge.main_faces[0].face].flipped or uvfaces[edge.main_faces[1].face].flipped):
                edge.calculate_angle()
            # ensure that the order of faces corresponds to the order of uvedges
            if edge.main_faces:
                reordered = [None, None]
                for uvedge in edge.uvedges:
                    try:
                        index = edge.main_faces.index(uvedge.loop)
                        reordered[index] = uvedge
                    except ValueError:
                        reordered.append(uvedge)
                edge.uvedges = reordered

        for island in self.islands:
            # if the normals are ambiguous, flip them so that there are more convex edges than concave ones
            if any(uvface.flipped for uvface in island.faces.values()):
                island_edges = {self.edges[uvedge.edge] for uvedge in island.edges}
                balance = sum((+1 if edge.angle > 0 else -1) for edge in island_edges)
                if balance < 0:
                    island.is_inside_out = True

            # construct a linked list from each island's boundary
            # uvedge.neighbor_right is clockwise = forward = via uvedge.vb if not uvface.flipped
            neighbor_lookup, conflicts = {}, {}
            for uvedge in island.boundary:
                uvvertex = uvedge.va if uvedge.uvface.flipped else uvedge.vb
                if uvvertex not in neighbor_lookup:
                    neighbor_lookup[uvvertex] = uvedge
                else:
                    if uvvertex not in conflicts:
                        conflicts[uvvertex] = [neighbor_lookup[uvvertex], uvedge]
                    else:
                        conflicts[uvvertex].append(uvedge)

            for uvedge in island.boundary:
                uvvertex = uvedge.vb if uvedge.uvface.flipped else uvedge.va
                if uvvertex not in conflicts:
                    # using the 'get' method so as to handle single-connected vertices properly
                    uvedge.neighbor_right = neighbor_lookup.get(uvvertex, uvedge)
                    uvedge.neighbor_right.neighbor_left = uvedge
                else:
                    conflicts[uvvertex].append(uvedge)

            # resolve merged vertices with more boundaries crossing
            def direction_to_float(vector):
                return (1 - vector.x/vector.length) if vector.y > 0 else (vector.x/vector.length - 1)
            for uvvertex, uvedges in conflicts.items():
                def is_inwards(uvedge):
                    return uvedge.uvface.flipped == (uvedge.va is uvvertex)

                def uvedge_sortkey(uvedge):
                    if is_inwards(uvedge):
                        return direction_to_float(uvedge.va.co - uvedge.vb.co)
                    else:
                        return direction_to_float(uvedge.vb.co - uvedge.va.co)

                uvedges.sort(key=uvedge_sortkey)
                for right, left in (
                        zip(uvedges[:-1:2], uvedges[1::2]) if is_inwards(uvedges[0])
                        else zip([uvedges[-1]] + uvedges[1::2], uvedges[:-1:2])):
                    left.neighbor_right = right
                    right.neighbor_left = left
        return True

    def generate_stickers(self, default_width, number_style, paper_thickness=0.0):
        """Add sticker faces where they are needed."""
        def uvedge_priority(uvedge):
            """Returns whether it is a good idea to stick something on this edge's face"""
            # TODO: it should take into account overlaps with faces and with other stickers
            face = uvedge.uvface.face
            return face.calc_area() / face.calc_perimeter()

        def is_index_obvious(uvedge, target):
            """Check if it is easy to guess that `uvedge` belongs to `target`"""
            if uvedge in (target.neighbor_left, target.neighbor_right):
                # direct neighbor
                return True
            if (uvedge.neighbor_left.loop.edge is target.neighbor_right.loop.edge
                    and uvedge.neighbor_right.loop.edge is target.neighbor_left.loop.edge):
                # consecutive string of stickers
                return True
            return False

        planned_stickers = {}  # source -> target
        for edge in self.edges.values():
            target = edge.uvedges[0]
            if edge.is_main_cut and len(edge.uvedges) >= 2 and edge.vector.length_squared > 0:
                source = edge.uvedges[1]
                if uvedge_priority(target) < uvedge_priority(source):
                    target, source = source, target
                planned_stickers[source] = target
            if len(edge.uvedges) > 2:
                # todo: paper_thickness compensation is not correct for multiple stacked stickers
                for source in edge.uvedges[2:]:
                    planned_stickers[source] = target
        if paper_thickness:
            new_edges = []
            # neighbors will change when in/outsetting stickers so we better precalculate the neighbor angles
            neighbor_angle = {edge: [pi + edge.neighbor_right.vector.angle_signed(edge.vector),
                    pi + edge.vector.angle_signed(edge.neighbor_left.vector)]
                for edge in planned_stickers}
            for source, target in planned_stickers.items():
                loop_right, loop_left = source.loop.link_loop_prev, source.loop.link_loop_next
                if source.uvface.flipped:
                    loop_right, loop_left = loop_left, loop_right
                is_double_vertex = [False, False]
                if source.uvface.edges[loop_right] not in planned_stickers and neighbor_angle[source][0] >= obtuse_angle:
                    new_edges.append(source.insert_neighbor_right())
                    is_double_vertex[0] = True
                if source.uvface.edges[loop_left] not in planned_stickers and neighbor_angle[source][1] >= obtuse_angle:
                    new_edges.append(source.insert_neighbor_left())
                    is_double_vertex[1] = True
                cos_angle = source.uvface.face.normal.dot(target.uvface.face.normal)
                sign = -1 if self.edges[source.loop.edge].is_convex() ^ source.uvface.island.is_inside_out else 1
                offset = sign * paper_thickness / sin_from_cos(cos_angle)
                source.slide(offset, is_double_vertex)
            # TODO: merge zero-length new_edges
        for source, target in planned_stickers.items():
            index = None
            if number_style != 'NONE':
                target_island = target.uvface.island
                for uvedge in [source] + edge.uvedges[2:]:
                    # create numbers (and arrows) only if necessary for understanding
                    if not is_index_obvious(uvedge, target):
                        target_island.sticker_numbering += 1
                        index = str(target_island.sticker_numbering)
                        if is_upsidedown_wrong(index):
                            index += "."
                        if number_style == 'INSIDE':
                            target_island.add_marker(NumberAlone(target, default_width, index, True))
                        else:
                            target_island.add_marker(Arrow(target, default_width, index))
                        break
            source.sticker = Sticker(source, default_width, index, target)
            source.uvface.island.add_marker(source.sticker)

    def generate_numbers_alone(self, size, numbers_inside=True):
        global_numbering = 0
        for edge in self.edges.values():
            if edge.is_main_cut and len(edge.uvedges) >= 2:
                global_numbering += 1
                index = str(global_numbering)
                if is_upsidedown_wrong(index):
                    index += "."
                for uvedge in edge.uvedges:
                    uvedge.uvface.island.add_marker(NumberAlone(uvedge, size, index, numbers_inside))

    def enumerate_islands(self):
        for num, island in enumerate(self.islands, 1):
            island.generate_label(num)

    def scale_islands(self, scale):
        for island in self.islands:
            vertices = set(island.vertices.values())
            for point in chain((vertex.co for vertex in vertices), island.fake_vertices):
                point *= scale

    def finalize_islands(self, cage_size, title_height=0):
        for island in self.islands:
            if title_height:
                island.title = "[{}] {}".format(island.abbreviation, island.label)
            points = [vertex.co for vertex in set(island.vertices.values())] + island.fake_vertices
            _, sinx, cosx = cage_fit(points, (cage_size.y - title_height) / cage_size.x)
            rot = rotation_matrix(sinx, cosx)
            for point in points:
                point.rotate(rot)
            for marker in island.markers:
                marker.rot = rot @ marker.rot
            bottom_left = Vector((min(v.x for v in points), min(v.y for v in points) - title_height))
            # DEBUG
            # top_right = Vector((max(v.x for v in points), max(v.y for v in points) - title_height))
            # print(f"fitted aspect: {(top_right.y - bottom_left.y) / (top_right.x - bottom_left.x)}")
            for point in points:
                point -= bottom_left
            island.bounding_box = Vector((max(v.x for v in points), max(v.y for v in points)))

    def largest_island_ratio(self, cage_size):
        return max(i / p for island in self.islands for (i, p) in zip(island.bounding_box, cage_size))

    def save_uv(self, cage_size=Vector((1, 1)), separate_image=False):
        if separate_image:
            for island in self.islands:
                island.save_uv_separate(self.looptex)
        else:
            for island in self.islands:
                island.save_uv(self.looptex, cage_size)

    def save_image(self, page_size_pixels: Vector, filename):
        for page in self.pages:
            image = create_blank_image("Page {}".format(page.name), page_size_pixels, alpha=1)
            image.filepath_raw = page.image_path = "{}_{}.png".format(filename, page.name)
            faces = [face for island in page.islands for face in island.faces]
            self.bake(faces, image)
            image.save()
            image.user_clear()
            bpy.data.images.remove(image)

    def save_separate_images(self, scale, filepath, embed=None):
        for i, island in enumerate(self.islands):
            image_name = "Island {}".format(i)
            image = create_blank_image(image_name, island.bounding_box * scale, alpha=0)
            self.bake(island.faces.keys(), image)
            if embed:
                island.embedded_image = embed(image)
            else:
                from os import makedirs
                image_dir = filepath
                makedirs(image_dir, exist_ok=True)
                image_path = os_path.join(image_dir, "island{}.png".format(i))
                image.filepath_raw = image_path
                image.save()
                island.image_path = image_path
            image.user_clear()
            bpy.data.images.remove(image)

    def bake(self, faces, image):
        # FIXME: as of 3.5.0, this detection does not work properly
        # and one of existing 8 UVLayers would be overwritten
        if not self.looptex:
            raise UnfoldError("The mesh has no UV Map slots left. Either delete a UV Map or export the net without textures.")
        ob = bpy.context.active_object
        me = ob.data
        # in Cycles, the image for baking is defined by the active Image Node
        temp_nodes = {}
        temp_mat = None
        if not any(me.materials):
            temp_mat = bpy.data.materials.new("Unfolded")
            me.materials.append(temp_mat)
        for mat in filter(None, me.materials):
            mat.use_nodes = True
            img = mat.node_tree.nodes.new('ShaderNodeTexImage')
            img.image = image
            temp_nodes[mat] = img
            mat.node_tree.nodes.active = img
        # move all excess faces to negative numbers (that is the only way to disable them)
        ignored_uvs = [loop[self.looptex].uv for f in self.data.faces if f not in faces for loop in f.loops]
        for uv in ignored_uvs:
            uv *= -1
        bake_type = bpy.context.scene.cycles.bake_type
        sta = bpy.context.scene.render.bake.use_selected_to_active
        try:
            ob.update_from_editmode()
            me.uv_layers.active = me.uv_layers[self.looptex.name]
            bpy.ops.object.bake(type=bake_type, margin=1, use_selected_to_active=sta, cage_extrusion=100, use_clear=False)
        except RuntimeError as e:
            raise UnfoldError(*e.args)
        finally:
            for mat, node in temp_nodes.items():
                mat.node_tree.nodes.remove(node)
            if temp_mat:
                me.materials.pop()
                bpy.data.materials.remove(temp_mat)
        for uv in ignored_uvs:
            uv *= -1


class Edge:
    """Wrapper for BPy Edge"""
    __slots__ = (
        'data', 'va', 'vb', 'main_faces', 'uvedges',
        'vector', 'angle',
        'is_main_cut', 'force_cut', 'priority', 'freestyle')

    def __init__(self, bmedge, freestyle_layer):
        self.data = bmedge
        self.va, self.vb = bmedge.verts
        self.vector = self.vb.co - self.va.co
        # if self.main_faces is set, then self.uvedges[:2] must correspond to self.main_faces, in their order
        # this constraint is assured at the time of finishing mesh.generate_cuts
        self.uvedges = []

        self.force_cut = bmedge.seam  # such edges will always be cut
        self.main_faces = None  # two faces that may be connected in the island
        # is_main_cut defines whether the two main faces are connected
        # all the others will be assumed to be cut
        self.is_main_cut = True
        self.priority = None
        self.angle = None
        self.freestyle = bmedge[freestyle_layer] if freestyle_layer else False

    def choose_main_faces(self):
        """Choose two main faces that might get connected in an island"""

        def score(pair):
            return abs(pair[0].face.normal.dot(pair[1].face.normal))

        loops = self.data.link_loops
        if len(loops) == 2:
            self.main_faces = list(loops)
        elif len(loops) > 2:
            # find (with brute force) the pair of indices whose loops have the most similar normals
            self.main_faces = max(combinations(loops, 2), key=score)
        if self.main_faces and self.main_faces[1].vert == self.va:
            self.main_faces = self.main_faces[::-1]

    def calculate_angle(self):
        """Calculate the angle between the main faces"""
        loop_a, loop_b = self.main_faces
        x = loop_a.face.normal.dot(loop_b.face.normal)
        y = -loop_b.calc_tangent().dot(loop_a.face.normal)
        self.angle = atan2(y, x)

    def is_convex(self):
        return (self.angle > 0) ^ self.uvedges[0].uvface.flipped

    def generate_priority(self, priority_effect, average_length):
        """Calculate the priority value for cutting"""
        angle = self.angle
        if angle > 0:
            self.priority = priority_effect['CONVEX'] * angle / pi
        else:
            self.priority = priority_effect['CONCAVE'] * (-angle) / pi
        self.priority += (self.vector.length / average_length) * priority_effect['LENGTH']

    def is_cut(self, face):
        """Return False if this edge will the given face to another one in the resulting net
        (useful for edges with more than two faces connected)"""
        # Return whether there is a cut between the two main faces
        if self.main_faces and face in {loop.face for loop in self.main_faces}:
            return self.is_main_cut
        # All other faces (third and more) are automatically treated as cut
        else:
            return True

    def other_uvedge(self, this):
        """Get an uvedge of this edge that is not the given one
        causes an IndexError if case of less than two adjacent edges"""
        return self.uvedges[1] if this is self.uvedges[0] else self.uvedges[0]


class Island:
    """Part of the net to be exported"""
    __slots__ = (
        'mesh', 'faces', 'edges', 'vertices', 'fake_vertices', 'boundary', 'markers',
        'pos', 'bounding_box',
        'image_path', 'embedded_image',
        'label', 'abbreviation', 'title',
        'has_safe_geometry', 'is_inside_out',
        'sticker_numbering')

    def __init__(self, mesh, face, matrix, normal_matrix):
        """Create an Island from a single Face"""
        self.mesh = mesh
        self.faces = {}  # face -> uvface
        self.edges = {}  # loop -> uvedge
        self.vertices = {}  # loop -> uvvertex
        self.fake_vertices = []
        self.markers = []
        self.label = None
        self.abbreviation = None
        self.title = None
        self.pos = Vector((0, 0))
        self.image_path = None
        self.embedded_image = None
        self.is_inside_out = False  # swaps concave <-> convex edges
        self.has_safe_geometry = True
        self.sticker_numbering = 0

        uvface = UVFace(face, self, matrix, normal_matrix)
        self.vertices.update(uvface.vertices)
        self.edges.update(uvface.edges)
        self.faces[face] = uvface
        # UVEdges on the boundary
        self.boundary = list(self.edges.values())

    def add_marker(self, marker):
        self.fake_vertices.extend(marker.bounds)
        self.markers.append(marker)

    def generate_label(self, number):
        """Assign a name to this island automatically"""
        abbr = self.abbreviation or str(number)
        # TODO: dots should be added in the last instant when outputting any text
        if is_upsidedown_wrong(abbr):
            abbr += "."
        self.label = self.label or f"Island {number}"
        self.abbreviation = abbr

    def save_uv(self, tex, cage_size):
        """Save UV Coordinates of all UVFaces to a given UV texture
        tex: UV Texture layer to use (BMLayerItem)
        page_size: size of the page in pixels (vector)"""
        scale_x, scale_y = 1 / cage_size.x, 1 / cage_size.y
        for loop, uvvertex in self.vertices.items():
            uv = uvvertex.co + self.pos
            loop[tex].uv = uv.x * scale_x, uv.y * scale_y

    def save_uv_separate(self, tex):
        """Save UV Coordinates of all UVFaces to a given UV texture, spanning from 0 to 1
        tex: UV Texture layer to use (BMLayerItem)
        page_size: size of the page in pixels (vector)"""
        scale_x, scale_y = 1 / self.bounding_box.x, 1 / self.bounding_box.y
        for loop, uvvertex in self.vertices.items():
            loop[tex].uv = uvvertex.co.x * scale_x, uvvertex.co.y * scale_y


def join(uvedge_a, uvedge_b, size_limit=None, epsilon=1e-6):
    """
    Try to join other island on given edge
    Returns False if they would overlap
    """

    class Intersection(Exception):
        pass

    class GeometryError(Exception):
        pass

    def is_below(self, other, correct_geometry=True):
        if self is other:
            return False
        if self.top < other.bottom:
            return True
        if other.top < self.bottom:
            return False
        if self.max.tup <= other.min.tup:
            return True
        if other.max.tup <= self.min.tup:
            return False
        self_vector = self.max.co - self.min.co
        min_to_min = other.min.co - self.min.co
        cross_b1 = self_vector.cross(min_to_min)
        cross_b2 = self_vector.cross(other.max.co - self.min.co)
        if cross_b2 < cross_b1:
            cross_b1, cross_b2 = cross_b2, cross_b1
        if cross_b2 > 0 and (cross_b1 > 0 or (cross_b1 == 0 and not self.is_uvface_upwards())):
            return True
        if cross_b1 < 0 and (cross_b2 < 0 or (cross_b2 == 0 and self.is_uvface_upwards())):
            return False
        other_vector = other.max.co - other.min.co
        cross_a1 = other_vector.cross(-min_to_min)
        cross_a2 = other_vector.cross(self.max.co - other.min.co)
        if cross_a2 < cross_a1:
            cross_a1, cross_a2 = cross_a2, cross_a1
        if cross_a2 > 0 and (cross_a1 > 0 or (cross_a1 == 0 and not other.is_uvface_upwards())):
            return False
        if cross_a1 < 0 and (cross_a2 < 0 or (cross_a2 == 0 and other.is_uvface_upwards())):
            return True
        if cross_a1 == cross_b1 == cross_a2 == cross_b2 == 0:
            if correct_geometry:
                raise GeometryError
            elif self.is_uvface_upwards() == other.is_uvface_upwards():
                raise Intersection
            return False
        if self.min.tup == other.min.tup or self.max.tup == other.max.tup:
            return cross_a2 > cross_b2
        raise Intersection

    class QuickSweepline:
        """Efficient sweepline based on binary search, checking neighbors only"""
        def __init__(self):
            self.children = []

        def add(self, item, cmp=is_below):
            low, high = 0, len(self.children)
            while low < high:
                mid = (low + high) // 2
                if cmp(self.children[mid], item):
                    low = mid + 1
                else:
                    high = mid
            self.children.insert(low, item)

        def remove(self, item, cmp=is_below):
            index = self.children.index(item)
            self.children.pop(index)
            if index > 0 and index < len(self.children):
                # check for intersection
                if cmp(self.children[index], self.children[index-1]):
                    raise GeometryError

    class BruteSweepline:
        """Safe sweepline which checks all its members pairwise"""
        def __init__(self):
            self.children = set()

        def add(self, item, cmp=is_below):
            for child in self.children:
                if child.min is not item.min and child.max is not item.max:
                    cmp(item, child, False)
            self.children.add(item)

        def remove(self, item):
            self.children.remove(item)

    def sweep(sweepline, segments):
        """Sweep across the segments and raise an exception if necessary"""
        # careful, 'segments' may be a use-once iterator
        events_add = sorted(segments, reverse=True, key=lambda uvedge: uvedge.min.tup)
        events_remove = sorted(events_add, reverse=True, key=lambda uvedge: uvedge.max.tup)
        while events_remove:
            while events_add and events_add[-1].min.tup <= events_remove[-1].max.tup:
                sweepline.add(events_add.pop())
            sweepline.remove(events_remove.pop())

    def root_find(value, tree):
        """Find the root of a given value in a forest-like dictionary
        also updates the dictionary using path compression"""
        parent, relink = tree.get(value), []
        while parent is not None:
            relink.append(value)
            value, parent = parent, tree.get(parent)
        tree.update(dict.fromkeys(relink, value))
        return value

    def slope_from(position):
        def slope(uvedge):
            vec = (uvedge.vb.co - uvedge.va.co) if uvedge.va.tup == position else (uvedge.va.co - uvedge.vb.co)
            return (vec.y / vec.length + 1) if ((vec.x, vec.y) > (0, 0)) else (-1 - vec.y / vec.length)
        return slope

    island_a, island_b = (e.uvface.island for e in (uvedge_a, uvedge_b))
    if island_a is island_b:
        return False
    elif len(island_b.faces) > len(island_a.faces):
        uvedge_a, uvedge_b = uvedge_b, uvedge_a
        island_a, island_b = island_b, island_a
    # check if vertices and normals are aligned correctly
    verts_flipped = uvedge_b.loop.vert is uvedge_a.loop.vert
    flipped = verts_flipped ^ uvedge_a.uvface.flipped ^ uvedge_b.uvface.flipped
    # determine rotation
    # NOTE: if the edges differ in length, the matrix will involve uniform scaling.
    # Such situation may occur in the case of twisted n-gons
    first_b, second_b = (uvedge_b.va, uvedge_b.vb) if not verts_flipped else (uvedge_b.vb, uvedge_b.va)
    if not flipped:
        rot = fitting_matrix(first_b.co - second_b.co, uvedge_a.vb.co - uvedge_a.va.co)
    else:
        flip = Matrix(((-1, 0), (0, 1)))
        rot = fitting_matrix(flip @ (first_b.co - second_b.co), uvedge_a.vb.co - uvedge_a.va.co) @ flip
    trans = uvedge_a.vb.co - rot @ first_b.co
    # preview of island_b's vertices after the join operation
    phantoms = {uvvertex: UVVertex(rot @ uvvertex.co + trans) for uvvertex in island_b.vertices.values()}

    # check the size of the resulting island
    if size_limit:
        points = [vert.co for vert in chain(island_a.vertices.values(), phantoms.values())]
        left, right, bottom, top = (fn(co[i] for co in points) for i in (0, 1) for fn in (min, max))
        bbox_width = right - left
        bbox_height = top - bottom
        if min(bbox_width, bbox_height)**2 > size_limit.x**2 + size_limit.y**2:
            return False
        if (bbox_width > size_limit.x or bbox_height > size_limit.y) and (bbox_height > size_limit.x or bbox_width > size_limit.y):
            height, *_ = cage_fit(points, size_limit.y / size_limit.x)
            if height > size_limit.y:
                return False

    distance_limit = uvedge_a.loop.edge.calc_length() * epsilon
    # try and merge UVVertices closer than sqrt(distance_limit)
    merged_uvedges = set()
    merged_uvedge_pairs = []

    # merge all uvvertices that are close enough using a union-find structure
    # uvvertices will be merged only in cases island_b->island_a and island_a->island_a
    # all resulting groups are merged together to a uvvertex of island_a
    is_merged_mine = False
    shared_vertices = {loop.vert for loop in chain(island_a.vertices, island_b.vertices)}
    for vertex in shared_vertices:
        uvs_a = {island_a.vertices.get(loop) for loop in vertex.link_loops} - {None}
        uvs_b = {island_b.vertices.get(loop) for loop in vertex.link_loops} - {None}
        for a, b in product(uvs_a, uvs_b):
            if (a.co - phantoms[b].co).length_squared < distance_limit:
                phantoms[b] = root_find(a, phantoms)
        for a1, a2 in combinations(uvs_a, 2):
            if (a1.co - a2.co).length_squared < distance_limit:
                a1, a2 = (root_find(a, phantoms) for a in (a1, a2))
                if a1 is not a2:
                    phantoms[a2] = a1
                    is_merged_mine = True
        for source, target in phantoms.items():
            target = root_find(target, phantoms)
            phantoms[source] = target

    for uvedge in (chain(island_a.boundary, island_b.boundary) if is_merged_mine else island_b.boundary):
        for loop in uvedge.loop.link_loops:
            partner = island_b.edges.get(loop) or island_a.edges.get(loop)
            if partner is not None and partner is not uvedge:
                paired_a, paired_b = phantoms.get(partner.vb, partner.vb), phantoms.get(partner.va, partner.va)
                if (partner.uvface.flipped ^ flipped) != uvedge.uvface.flipped:
                    paired_a, paired_b = paired_b, paired_a
                if phantoms.get(uvedge.va, uvedge.va) is paired_a and phantoms.get(uvedge.vb, uvedge.vb) is paired_b:
                    # if these two edges will get merged, add them both to the set
                    merged_uvedges.update((uvedge, partner))
                    merged_uvedge_pairs.append((uvedge, partner))
                    break

    if uvedge_b not in merged_uvedges:
        raise UnfoldError("Export failed. Please report this error, including the model if you can.")

    boundary_other = [
        PhantomUVEdge(phantoms[uvedge.va], phantoms[uvedge.vb], flipped ^ uvedge.uvface.flipped)
        for uvedge in island_b.boundary if uvedge not in merged_uvedges]
    # TODO: if is_merged_mine, it might make sense to create a similar list from island_a.boundary as well

    incidence = {vertex.tup for vertex in phantoms.values()}.intersection(vertex.tup for vertex in island_a.vertices.values())
    incidence = {position: [] for position in incidence}  # from now on, 'incidence' is a dict
    for uvedge in chain(boundary_other, island_a.boundary):
        if uvedge.va.co == uvedge.vb.co:
            continue
        for vertex in (uvedge.va, uvedge.vb):
            site = incidence.get(vertex.tup)
            if site is not None:
                site.append(uvedge)
    for position, segments in incidence.items():
        if len(segments) <= 2:
            continue
        segments.sort(key=slope_from(position))
        for right, left in pairs(segments):
            is_left_ccw = left.is_uvface_upwards() ^ (left.max.tup == position)
            is_right_ccw = right.is_uvface_upwards() ^ (right.max.tup == position)
            if is_right_ccw and not is_left_ccw and type(right) is not type(left) and right not in merged_uvedges and left not in merged_uvedges:
                return False
            if (not is_right_ccw and right not in merged_uvedges) ^ (is_left_ccw and left not in merged_uvedges):
                return False

    # check for self-intersections
    try:
        try:
            sweepline = QuickSweepline() if island_a.has_safe_geometry and island_b.has_safe_geometry else BruteSweepline()
            sweep(sweepline, (uvedge for uvedge in chain(boundary_other, island_a.boundary)))
            island_a.has_safe_geometry &= island_b.has_safe_geometry
        except GeometryError:
            sweep(BruteSweepline(), (uvedge for uvedge in chain(boundary_other, island_a.boundary)))
            island_a.has_safe_geometry = False
    except Intersection:
        return False

    # mark all edges that connect the islands as not cut
    for uvedge in merged_uvedges:
        island_a.mesh.edges[uvedge.loop.edge].is_main_cut = False

    # include all trasformed vertices as mine
    island_a.vertices.update({loop: phantoms[uvvertex] for loop, uvvertex in island_b.vertices.items()})

    # re-link uvedges and uvfaces to their transformed locations
    for uvedge in island_b.edges.values():
        uvedge.va = phantoms[uvedge.va]
        uvedge.vb = phantoms[uvedge.vb]
        uvedge.update()
    if is_merged_mine:
        for uvedge in island_a.edges.values():
            uvedge.va = phantoms.get(uvedge.va, uvedge.va)
            uvedge.vb = phantoms.get(uvedge.vb, uvedge.vb)
    island_a.edges.update(island_b.edges)

    for uvface in island_b.faces.values():
        uvface.island = island_a
        uvface.vertices = {loop: phantoms[uvvertex] for loop, uvvertex in uvface.vertices.items()}
        uvface.flipped ^= flipped
    if is_merged_mine:
        # there may be own uvvertices that need to be replaced by phantoms
        for uvface in island_a.faces.values():
            if any(uvvertex in phantoms for uvvertex in uvface.vertices):
                uvface.vertices = {loop: phantoms.get(uvvertex, uvvertex) for loop, uvvertex in uvface.vertices.items()}
    island_a.faces.update(island_b.faces)

    island_a.boundary = [
        uvedge for uvedge in chain(island_a.boundary, island_b.boundary)
        if uvedge not in merged_uvedges]

    for uvedge, partner in merged_uvedge_pairs:
        # make sure that main faces are the ones actually merged (this changes nothing in most cases)
        edge = island_a.mesh.edges[uvedge.loop.edge]
        edge.main_faces = uvedge.loop, partner.loop

    # everything seems to be OK
    return island_b


class UVVertex:
    """Vertex in 2D"""
    __slots__ = ('co', 'tup')

    def __init__(self, vector):
        self.co = vector.xy
        self.tup = tuple(self.co)


class UVEdge:
    """Edge in 2D"""
    # Every UVEdge is attached to only one UVFace
    # UVEdges are doubled as needed because they both have to point counter-clockwise around their faces
    __slots__ = (
        'va', 'vb', 'uvface', 'loop',
        'min', 'max', 'bottom', 'top',
        'neighbor_left', 'neighbor_right', 'sticker')

    # uvface.flipped changes the meaning of va <-> vb
    # if neither of faces is flipped, uvedge.va == uvedge.neighbor_right.vb
    # neighbor_right is always clockwise around the island boundary

    def __init__(self, vertex1: UVVertex, vertex2: UVVertex, uvface, loop):
        self.va = vertex1
        self.vb = vertex2
        self.update()
        self.uvface = uvface
        self.sticker = None
        self.loop = loop

    @property
    def vector(self):
        return self.vb.co - self.va.co if not self.uvface.flipped else self.va.co - self.vb.co

    def update(self):
        """Update data if UVVertices have moved"""
        self.min, self.max = (self.va, self.vb) if (self.va.tup < self.vb.tup) else (self.vb, self.va)
        y1, y2 = self.va.co.y, self.vb.co.y
        self.bottom, self.top = (y1, y2) if y1 < y2 else (y2, y1)

    def is_uvface_upwards(self):
        return (self.va.tup < self.vb.tup) ^ self.uvface.flipped

    def slide(self, offset, allow_orthogonal=(True, True)):
        normal = rot90(self.vector).normalized()
        def slide_vertex(vertex, rail_loop, orthogonal):
            rail = self.uvface.edges[rail_loop].vector.normalized()
            rail *= -1 if normal.dot(rail) < 0 else 1
            direction = normal if offset > 0 or orthogonal else rail
            distance = offset / max(abs(normal.dot(direction)), 0.1)
            vertex.co += direction * distance

        slide_vertex(self.va, self.loop.link_loop_prev, self.loop.calc_angle() >= obtuse_angle and allow_orthogonal[0])
        slide_vertex(self.vb, self.loop.link_loop_next, self.loop.link_loop_next.calc_angle() >= obtuse_angle and allow_orthogonal[1])
        self.update()

    def insert_neighbor_left(self):
        vertex_left = "vb" if not self.uvface.flipped else "va"
        vb = getattr(self, vertex_left)
        va = UVVertex(vb.co.copy())
        self.uvface.island.fake_vertices.append(va.co)
        setattr(self, vertex_left, va)
        if self.uvface.flipped:
            va, vb = vb, va
        uvedge = UVEdge(va, vb, self.uvface, self.loop)
        self.uvface.island.boundary.append(uvedge)
        uvedge.neighbor_left = self.neighbor_left
        uvedge.neighbor_right = self
        self.neighbor_left.neighbor_right = self.neighbor_left = uvedge
        self.update()
        return uvedge

    def insert_neighbor_right(self):
        vertex_right = "va" if not self.uvface.flipped else "vb"
        va = getattr(self, vertex_right)
        vb = UVVertex(va.co.copy())
        self.uvface.island.fake_vertices.append(vb.co)
        setattr(self, vertex_right, vb)
        if self.uvface.flipped:
            va, vb = vb, va
        uvedge = UVEdge(va, vb, self.uvface, self.loop)
        self.uvface.island.boundary.append(uvedge)
        uvedge.neighbor_right = self.neighbor_right
        uvedge.neighbor_left = self
        self.neighbor_right.neighbor_left = self.neighbor_right = uvedge
        self.update()
        return uvedge

    def __repr__(self):
        return "({0.va} - {0.vb})".format(self)


class PhantomUVEdge:
    """Temporary 2D Segment for calculations"""
    __slots__ = ('va', 'vb', 'min', 'max', 'bottom', 'top')

    def __init__(self, vertex1: UVVertex, vertex2: UVVertex, flip):
        self.va, self.vb = (vertex2, vertex1) if flip else (vertex1, vertex2)
        self.min, self.max = (self.va, self.vb) if (self.va.tup < self.vb.tup) else (self.vb, self.va)
        y1, y2 = self.va.co.y, self.vb.co.y
        self.bottom, self.top = (y1, y2) if y1 < y2 else (y2, y1)

    @property
    def vector(self):
        return self.vb.co - self.va.co

    def is_uvface_upwards(self):
        return self.va.tup < self.vb.tup

    def __repr__(self):
        return "[{0.va} - {0.vb}]".format(self)


class UVFace:
    """Face in 2D"""
    __slots__ = ('vertices', 'edges', 'face', 'island', 'flipped')

    def __init__(self, face: bmesh.types.BMFace, island: Island, matrix=1, normal_matrix=1):
        self.face = face
        self.island = island
        self.flipped = False  # a flipped UVFace has edges clockwise

        flatten = z_up_matrix(normal_matrix @ face.normal) @ matrix
        self.vertices = {loop: UVVertex(flatten @ loop.vert.co) for loop in face.loops}
        self.edges = {loop: UVEdge(self.vertices[loop], self.vertices[loop.link_loop_next], self, loop) for loop in face.loops}


class Arrow:
    """Mark in the document: an arrow denoting the number of the edge it points to"""
    __slots__ = ('bounds', 'center', 'rot', 'text', 'size')

    def __init__(self, uvedge, size, index):
        self.text = str(index)
        edge = uvedge.vector
        self.center = (uvedge.va.co + uvedge.vb.co) / 2
        self.size = size
        tangent = edge.normalized()
        cos, sin = tangent
        self.rot = rotation_matrix(sin, cos)
        normal = Vector((sin, -cos))
        self.bounds = [self.center, self.center + (1.2 * normal + tangent) * size, self.center + (1.2 * normal - tangent) * size]


class Sticker:
    """Mark in the document: sticker tab"""
    __slots__ = ('bounds', 'center', 'points', 'rot', 'text', 'width')

    def __init__(self, uvedge, default_width, index, other: UVEdge):
        """Sticker is directly attached to the given UVEdge"""
        first_vertex, second_vertex = (uvedge.va, uvedge.vb) if not uvedge.uvface.flipped else (uvedge.vb, uvedge.va)
        edge = first_vertex.co - second_vertex.co
        sticker_width = min(default_width, edge.length / 2)
        other_first, other_second = (other.va, other.vb) if not other.uvface.flipped else (other.vb, other.va)
        other_edge = other_second.co - other_first.co

        # angle a is at vertex uvedge.va, b is at uvedge.vb
        cos_a = cos_b = 0.5
        sin_a = sin_b = sin_from_cos(cos_a)
        # len_a is length of the side adjacent to vertex a, len_b likewise
        len_a = len_b = sticker_width / sin_a

        # fix overlaps with the most often neighbour - its sticking target
        if first_vertex == other_second:
            cos_a = max(cos_a, edge.dot(other_edge) / (edge.length_squared))  # angles between pi/3 and 0
        elif second_vertex == other_first:
            cos_b = max(cos_b, edge.dot(other_edge) / (edge.length_squared))  # angles between pi/3 and 0

        # if the sticking target has sharp angles, make the sticker as sharp
        try:
            other_face_vb = other.uvface.edges[other.loop.link_loop_prev]
            other_face_va = other.uvface.edges[other.loop.link_loop_next]
            other_edge_neighbor_a = other_face_vb.va.co - other.vb.co
            other_edge_neighbor_b = other_face_va.vb.co - other.va.co
            # Adjacent angles in the face
            cos_a = max(cos_a, -other_edge.dot(other_edge_neighbor_a) / (other_edge.length*other_edge_neighbor_a.length))
            cos_b = max(cos_b, other_edge.dot(other_edge_neighbor_b) / (other_edge.length*other_edge_neighbor_b.length))
        except AttributeError:  # neighbor data may be missing for edges with 3+ faces
            pass
        except ZeroDivisionError:
            pass

        # Calculate the lengths of the glue tab edges using the possibly smaller angles
        sin_a = sin_from_cos(cos_a)
        len_b = min(len_a, (edge.length * sin_a) / (sin_a * cos_b + sin_b * cos_a))
        len_a = 0 if sin_a == 0 else min(sticker_width / sin_a, (edge.length - len_b*cos_b) / cos_a)

        sin_b = sin_from_cos(cos_b)
        len_a = min(len_a, (edge.length * sin_b) / (sin_a * cos_b + sin_b * cos_a))
        len_b = 0 if sin_b == 0 else min(sticker_width / sin_b, (edge.length - len_a * cos_a) / cos_b)

        v3 = second_vertex.co + rotation_matrix(sin_b, cos_b) @ edge * len_b / edge.length
        v4 = first_vertex.co + rotation_matrix(sin_a, -cos_a) @ edge * len_a / edge.length
        if v3 != v4:
            self.points = [second_vertex.co, v3, v4, first_vertex.co]
        else:
            self.points = [second_vertex.co, v3, first_vertex.co]

        sin, cos = edge.y / edge.length, edge.x / edge.length
        self.rot = rotation_matrix(sin, cos)
        self.width = sticker_width * 0.9
        if index and uvedge.uvface.island is not other.uvface.island:
            self.text = "{}:{}".format(other.uvface.island.abbreviation, index)
        else:
            self.text = index
        self.center = (uvedge.va.co + uvedge.vb.co) / 2 + self.rot @ Vector((0, self.width * 0.2))
        self.bounds = [v3, v4, self.center] if v3 != v4 else [v3, self.center]


class NumberAlone:
    """Mark in the document: numbering inside the island denoting edges to be sticked"""
    __slots__ = ('bounds', 'center', 'rot', 'text', 'size')

    def __init__(self, uvedge, default_width, index, inside=False):
        """Sticker is directly attached to the given UVEdge"""
        edge = uvedge.vector

        self.size = default_width
        sin, cos = edge.y / edge.length, edge.x / edge.length
        self.rot = rotation_matrix(sin, cos)
        self.text = index
        placement = -0.2 if inside else 1.2
        self.center = (uvedge.va.co + uvedge.vb.co) / 2 - self.rot @ Vector((0, self.size * placement))
        self.bounds = [self.center]


class Exporter:
    def __init__(self, properties):
        self.page_size = Vector((properties.output_size_x, properties.output_size_y))
        self.style = properties.style
        margin = properties.output_margin
        self.margin = Vector((margin, margin))
        self.pure_net = (properties.texture_type == 'NONE')
        self.text_size = properties.sticker_width
        self.angle_epsilon = properties.angle_epsilon
