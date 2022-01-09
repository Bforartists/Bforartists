# -*- coding: utf-8 -*-
# This script is Free software. Please share and reuse.
# ♡2010-2021 Adam Dominec <adominec@gmail.com>

## Code structure
# This file consists of several components, in this order:
# * Unfolding and baking
# * Export (SVG or PDF)
# * User interface
# During the unfold process, the mesh is mirrored into a 2D structure: UVFace, UVEdge, UVVertex.

bl_info = {
    "name": "Export Paper Model",
    "author": "Addam Dominec",
    "version": (1, 2),
    "blender": (3, 0, 0),
    "location": "File > Export > Paper Model",
    "warning": "",
    "description": "Export printable net of the active mesh",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/import_export/paper_model.html",
    "category": "Import-Export",
}

# Task: split into four files (SVG and PDF separately)
# * does any portion of baking belong into the export module?
# * sketch out the code for GCODE and two-sided export

# TODO:
# QuickSweepline is very much broken -- it throws GeometryError for all nets > ~15 faces
# rotate islands to minimize area -- and change that only if necessary to fill the page size

# check conflicts in island naming and either:
# * append a number to the conflicting names or
# * enumerate faces uniquely within all islands of the same name (requires a check that both label and abbr. equals)

import bpy
import bl_operators
import bmesh
import mathutils as M
from re import compile as re_compile
from itertools import chain, repeat, product, combinations
from math import pi, ceil, asin, atan2
import os.path as os_path

default_priority_effect = {
    'CONVEX': 0.5,
    'CONCAVE': 1,
    'LENGTH': -0.05
}

global_paper_sizes = [
    ('USER', "User defined", "User defined paper size"),
    ('A4', "A4", "International standard paper size"),
    ('A3', "A3", "International standard paper size"),
    ('US_LETTER', "Letter", "North American paper size"),
    ('US_LEGAL', "Legal", "North American paper size")
]


def first_letters(text):
    """Iterator over the first letter of each word"""
    for match in first_letters.pattern.finditer(text):
        yield text[match.start()]
first_letters.pattern = re_compile(r"((?<!\w)\w)|\d")


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


def fitting_matrix(v1, v2):
    """Get a matrix that rotates v1 to the same direction as v2"""
    return (1 / v1.length_squared) * M.Matrix((
        (v1.x*v2.x + v1.y*v2.y, v1.y*v2.x - v1.x*v2.y),
        (v1.x*v2.y - v1.y*v2.x, v1.x*v2.x + v1.y*v2.y)))


def z_up_matrix(n):
    """Get a rotation matrix that aligns given vector upwards."""
    b = n.xy.length
    s = n.length
    if b > 0:
        return M.Matrix((
            (n.x*n.z/(b*s), n.y*n.z/(b*s), -b/s),
            (-n.y/b, n.x/b, 0),
            (0, 0, 0)
        ))
    else:
        # no need for rotation
        return M.Matrix((
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
            rot = M.Matrix(((cosx, -sinx), (sinx, cosx)))
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
            t = ((r**2 + q**2)**0.5 - r) / q if q != 0 else 0
            t = -1 / t if abs(t) > 1 else t  # pick the positive solution
            siny, cosy = 2 * t / (1 + t**2), (1 - t**2) / (1 + t**2)
            rot = M.Matrix(((cosy, -siny), (siny, cosy)))
            for p in rot_polygon:
                p[:] = rot @ p  # note: this also modifies left, right, bottom, top
            if left.x < right.x and bottom.y < top.y and all(left.x <= p.x <= right.x and bottom.y <= p.y <= top.y for p in rot_polygon):
                yield max(aspect * (right - left).x, (top - bottom).y), sinx*cosy + cosx*siny, cosx*cosy - sinx*siny
    polygon = [points[i] for i in M.geometry.convex_hull_2d(points)]
    height, sinx, cosx = min(guesses(polygon))
    return atan2(sinx, cosx), height


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
        if len(self.args) > 1:
            elems, bm = self.args[1:3]
            bpy.context.tool_settings.mesh_select_mode = [bool(elems[key]) for key in ("verts", "edges", "faces")]
            for elem in chain(bm.verts, bm.edges, bm.faces):
                elem.select = False
            for elem in chain(*elems.values()):
                elem.select_set(True)
            bmesh.update_edit_mesh(bpy.context.object.data, loop_triangles=False, destructive=False)


class Unfolder:
    def __init__(self, ob):
        self.do_create_uvmap = False
        bm = bmesh.from_edit_mesh(ob.data)
        self.mesh = Mesh(bm, ob.matrix_world)
        self.mesh.check_correct()

    def __del__(self):
        if not self.do_create_uvmap:
            self.mesh.delete_uvmap()

    def prepare(self, cage_size=None, priority_effect=default_priority_effect, scale=1, limit_by_page=False):
        """Create the islands of the net"""
        self.mesh.generate_cuts(cage_size / scale if limit_by_page and cage_size else None, priority_effect)
        self.mesh.finalize_islands(cage_size or M.Vector((1, 1)))
        self.mesh.enumerate_islands()
        self.mesh.save_uv()

    def copy_island_names(self, island_list):
        """Copy island label and abbreviation from the best matching island in the list"""
        orig_islands = [{face.id for face in item.faces} for item in island_list]
        matching = list()
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

    def save(self, properties):
        """Export the document"""
        # Note about scale: input is directly in blender length
        # Mesh.scale_islands multiplies everything by a user-defined ratio
        # exporters (SVG or PDF) multiply everything by 1000 (output in millimeters)
        Exporter = Svg if properties.file_format == 'SVG' else Pdf
        filepath = properties.filepath
        extension = properties.file_format.lower()
        filepath = bpy.path.ensure_ext(filepath, "." + extension)
        # page size in meters
        page_size = M.Vector((properties.output_size_x, properties.output_size_y))
        # printable area size in meters
        printable_size = page_size - 2 * properties.output_margin * M.Vector((1, 1))
        unit_scale = bpy.context.scene.unit_settings.scale_length
        ppm = properties.output_dpi * 100 / 2.54  # pixels per meter

        # after this call, all dimensions will be in meters
        self.mesh.scale_islands(unit_scale/properties.scale)
        if properties.do_create_stickers:
            self.mesh.generate_stickers(properties.sticker_width, properties.do_create_numbers)
        elif properties.do_create_numbers:
            self.mesh.generate_numbers_alone(properties.sticker_width)

        text_height = properties.sticker_width if (properties.do_create_numbers and len(self.mesh.islands) > 1) else 0
        # title height must be somewhat larger that text size, glyphs go below the baseline
        self.mesh.finalize_islands(printable_size, title_height=text_height * 1.2)
        self.mesh.fit_islands(printable_size)

        if properties.output_type != 'NONE':
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
                setattr(bk, f"use_pass_{p}", (properties.output_type != 'TEXTURE'))
            lookup = {'TEXTURE': 'DIFFUSE', 'AMBIENT_OCCLUSION': 'AO', 'RENDER': 'COMBINED', 'SELECTED_TO_ACTIVE': 'COMBINED'}
            sce.cycles.bake_type = lookup[properties.output_type]
            bk.use_selected_to_active = (properties.output_type == 'SELECTED_TO_ACTIVE')
            bk.margin, bk.cage_extrusion, bk.use_cage, bk.use_clear = 1, 10, False, False
            if properties.output_type == 'TEXTURE':
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
                self.mesh.save_separate_images(ppm, filepath, embed=Exporter.encode_image)

            apply_rna_properties(recall, rd, bk, sce.cycles)

        exporter = Exporter(properties)
        exporter.write(self.mesh, filepath)


class Mesh:
    """Wrapper for Bpy Mesh"""

    def __init__(self, bmesh, matrix):
        self.data = bmesh
        self.matrix = matrix.to_3x3()
        self.looptex = bmesh.loops.layers.uv.new("Unfolded")
        self.edges = {bmedge: Edge(bmedge) for bmedge in bmesh.edges}
        self.islands = list()
        self.pages = list()
        for edge in self.edges.values():
            edge.choose_main_faces()
            if edge.main_faces:
                edge.calculate_angle()
        self.copy_freestyle_marks()

    def delete_uvmap(self):
        self.data.loops.layers.uv.remove(self.looptex) if self.looptex else None

    def copy_freestyle_marks(self):
        # NOTE: this is a workaround for NotImplementedError on bmesh.edges.layers.freestyle
        mesh = bpy.data.meshes.new("unfolder_temp")
        self.data.to_mesh(mesh)
        for bmedge, edge in self.edges.items():
            edge.freestyle = mesh.edges[bmedge.index].use_freestyle_mark
        bpy.data.meshes.remove(mesh)

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
            (" {} zero-length edge(s)\n".format(len(null_edges)) if null_edges else "") +
            (" {} zero-area face(s)\n".format(len(null_faces)) if null_faces else "") +
            (" {} twisted polygon(s)\n".format(len(twisted_faces)) if twisted_faces else "") +
            "The offenders are selected and you can use {} to fix them. Export failed.".format(cure),
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
                balance = sum((+1 if edge.angle > 0 else -1) for edge in island_edges if not edge.is_cut(uvedge.uvface.face))
                if balance < 0:
                    island.is_inside_out = True

            # construct a linked list from each island's boundary
            # uvedge.neighbor_right is clockwise = forward = via uvedge.vb if not uvface.flipped
            neighbor_lookup, conflicts = dict(), dict()
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

    def generate_stickers(self, default_width, do_create_numbers=True):
        """Add sticker faces where they are needed."""
        def uvedge_priority(uvedge):
            """Returns whether it is a good idea to stick something on this edge's face"""
            # TODO: it should take into account overlaps with faces and with other stickers
            face = uvedge.uvface.face
            return face.calc_area() / face.calc_perimeter()

        def add_sticker(uvedge, index, target_uvedge):
            uvedge.sticker = Sticker(uvedge, default_width, index, target_uvedge)
            uvedge.uvface.island.add_marker(uvedge.sticker)

        def is_index_obvious(uvedge, target):
            if uvedge in (target.neighbor_left, target.neighbor_right):
                return True
            if uvedge.neighbor_left.loop.edge is target.neighbor_right.loop.edge and uvedge.neighbor_right.loop.edge is target.neighbor_left.loop.edge:
                return True
            return False

        for edge in self.edges.values():
            index = None
            if edge.is_main_cut and len(edge.uvedges) >= 2 and edge.vector.length_squared > 0:
                target, source = edge.uvedges[:2]
                if uvedge_priority(target) < uvedge_priority(source):
                    target, source = source, target
                target_island = target.uvface.island
                if do_create_numbers:
                    for uvedge in [source] + edge.uvedges[2:]:
                        if not is_index_obvious(uvedge, target):
                            # it will not be clear to see that these uvedges should be sticked together
                            # So, create an arrow and put the index on all stickers
                            target_island.sticker_numbering += 1
                            index = str(target_island.sticker_numbering)
                            if is_upsidedown_wrong(index):
                                index += "."
                            target_island.add_marker(Arrow(target, default_width, index))
                            break
                add_sticker(source, index, target)
            elif len(edge.uvedges) > 2:
                target = edge.uvedges[0]
            if len(edge.uvedges) > 2:
                for source in edge.uvedges[2:]:
                    add_sticker(source, index, target)

    def generate_numbers_alone(self, size):
        global_numbering = 0
        for edge in self.edges.values():
            if edge.is_main_cut and len(edge.uvedges) >= 2:
                global_numbering += 1
                index = str(global_numbering)
                if is_upsidedown_wrong(index):
                    index += "."
                for uvedge in edge.uvedges:
                    uvedge.uvface.island.add_marker(NumberAlone(uvedge, index, size))

    def enumerate_islands(self):
        for num, island in enumerate(self.islands, 1):
            island.number = num
            island.generate_label()

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
            angle, _ = cage_fit(points, (cage_size.y - title_height) / cage_size.x)
            rot = M.Matrix.Rotation(angle, 2)
            for point in points:
                point.rotate(rot)
            for marker in island.markers:
                marker.rot = rot @ marker.rot
            bottom_left = M.Vector((min(v.x for v in points), min(v.y for v in points) - title_height))
            # DEBUG
            # top_right = M.Vector((max(v.x for v in points), max(v.y for v in points) - title_height))
            # print(f"fitted aspect: {(top_right.y - bottom_left.y) / (top_right.x - bottom_left.x)}")
            for point in points:
                point -= bottom_left
            island.bounding_box = M.Vector((max(v.x for v in points), max(v.y for v in points)))

    def largest_island_ratio(self, cage_size):
        return max(i / p for island in self.islands for (i, p) in zip(island.bounding_box, cage_size))

    def fit_islands(self, cage_size):
        """Move islands so that they fit onto pages, based on their bounding boxes"""

        def try_emplace(island, page_islands, stops_x, stops_y, occupied_cache):
            """Tries to put island to each pair from stops_x, stops_y
            and checks if it overlaps with any islands present on the page.
            Returns True and positions the given island on success."""
            bbox_x, bbox_y = island.bounding_box.xy
            for x in stops_x:
                if x + bbox_x > cage_size.x:
                    continue
                for y in stops_y:
                    if y + bbox_y > cage_size.y or (x, y) in occupied_cache:
                        continue
                    for i, obstacle in enumerate(page_islands):
                        # if this obstacle overlaps with the island, try another stop
                        if (x + bbox_x > obstacle.pos.x and
                                obstacle.pos.x + obstacle.bounding_box.x > x and
                                y + bbox_y > obstacle.pos.y and
                                obstacle.pos.y + obstacle.bounding_box.y > y):
                            if x >= obstacle.pos.x and y >= obstacle.pos.y:
                                occupied_cache.add((x, y))
                            # just a stupid heuristic to make subsequent searches faster
                            if i > 0:
                                page_islands[1:i+1] = page_islands[:i]
                                page_islands[0] = obstacle
                            break
                    else:
                        # if no obstacle called break, this position is okay
                        island.pos.xy = x, y
                        page_islands.append(island)
                        stops_x.append(x + bbox_x)
                        stops_y.append(y + bbox_y)
                        return True
            return False

        def drop_portion(stops, border, divisor):
            stops.sort()
            # distance from left neighbor to the right one, excluding the first stop
            distances = [right - left for left, right in zip(stops, chain(stops[2:], [border]))]
            quantile = sorted(distances)[len(distances) // divisor]
            return [stop for stop, distance in zip(stops, chain([quantile], distances)) if distance >= quantile]

        if any(island.bounding_box.x > cage_size.x or island.bounding_box.y > cage_size.y for island in self.islands):
            raise UnfoldError(
                "An island is too big to fit onto page of the given size. "
                "Either downscale the model or find and split that island manually.\n"
                "Export failed, sorry.")
        # sort islands by their diagonal... just a guess
        remaining_islands = sorted(self.islands, reverse=True, key=lambda island: island.bounding_box.length_squared)
        page_num = 1  # TODO delete me

        while remaining_islands:
            # create a new page and try to fit as many islands onto it as possible
            page = Page(page_num)
            page_num += 1
            occupied_cache = set()
            stops_x, stops_y = [0], [0]
            for island in remaining_islands:
                try_emplace(island, page.islands, stops_x, stops_y, occupied_cache)
                # if overwhelmed with stops, drop a quarter of them
                if len(stops_x)**2 > 4 * len(self.islands) + 100:
                    stops_x = drop_portion(stops_x, cage_size.x, 4)
                    stops_y = drop_portion(stops_y, cage_size.y, 4)
            remaining_islands = [island for island in remaining_islands if island not in page.islands]
            self.pages.append(page)

    def save_uv(self, cage_size=M.Vector((1, 1)), separate_image=False):
        if separate_image:
            for island in self.islands:
                island.save_uv_separate(self.looptex)
        else:
            for island in self.islands:
                island.save_uv(self.looptex, cage_size)

    def save_image(self, page_size_pixels: M.Vector, filename):
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
        if not self.looptex:
            raise UnfoldError("The mesh has no UV Map slots left. Either delete a UV Map or export the net without textures.")
        ob = bpy.context.active_object
        me = ob.data
        # in Cycles, the image for baking is defined by the active Image Node
        temp_nodes = dict()
        for mat in me.materials:
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
        for uv in ignored_uvs:
            uv *= -1


class Edge:
    """Wrapper for BPy Edge"""
    __slots__ = (
        'data', 'va', 'vb', 'main_faces', 'uvedges',
        'vector', 'angle',
        'is_main_cut', 'force_cut', 'priority', 'freestyle')

    def __init__(self, edge):
        self.data = edge
        self.va, self.vb = edge.verts
        self.vector = self.vb.co - self.va.co
        # if self.main_faces is set, then self.uvedges[:2] must correspond to self.main_faces, in their order
        # this constraint is assured at the time of finishing mesh.generate_cuts
        self.uvedges = list()

        self.force_cut = edge.seam  # such edges will always be cut
        self.main_faces = None  # two faces that may be connected in the island
        # is_main_cut defines whether the two main faces are connected
        # all the others will be assumed to be cut
        self.is_main_cut = True
        self.priority = None
        self.angle = None
        self.freestyle = False

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
        normal_a, normal_b = (l.face.normal for l in self.main_faces)
        if not normal_a or not normal_b:
            self.angle = -3  # just a very sharp angle
        else:
            s = normal_a.cross(normal_b).dot(self.vector.normalized())
            s = max(min(s, 1.0), -1.0)  # deal with rounding errors
            self.angle = asin(s)
            if loop_a.link_loop_next.vert != loop_b.vert or loop_b.link_loop_next.vert != loop_a.vert:
                self.angle = abs(self.angle)

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
        'number', 'label', 'abbreviation', 'title',
        'has_safe_geometry', 'is_inside_out',
        'sticker_numbering')

    def __init__(self, mesh, face, matrix, normal_matrix):
        """Create an Island from a single Face"""
        self.mesh = mesh
        self.faces = dict()  # face -> uvface
        self.edges = dict()  # loop -> uvedge
        self.vertices = dict()  # loop -> uvvertex
        self.fake_vertices = list()
        self.markers = list()
        self.label = None
        self.abbreviation = None
        self.title = None
        self.pos = M.Vector((0, 0))
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

    def generate_label(self, label=None, abbreviation=None):
        """Assign a name to this island automatically"""
        abbr = abbreviation or self.abbreviation or str(self.number)
        # TODO: dots should be added in the last instant when outputting any text
        if is_upsidedown_wrong(abbr):
            abbr += "."
        self.label = label or self.label or "Island {}".format(self.number)
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
            self.children = list()

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
        parent, relink = tree.get(value), list()
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
        flip = M.Matrix(((-1, 0), (0, 1)))
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
            _, height = cage_fit(points, size_limit.y / size_limit.x)
            if height > size_limit.y:
                return False

    distance_limit = uvedge_a.loop.edge.calc_length() * epsilon
    # try and merge UVVertices closer than sqrt(distance_limit)
    merged_uvedges = set()
    merged_uvedge_pairs = list()

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
    incidence = {position: list() for position in incidence}  # from now on, 'incidence' is a dict
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

    # include all transformed vertices as mine
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


class Page:
    """Container for several Islands"""
    __slots__ = ('islands', 'name', 'image_path')

    def __init__(self, num=1):
        self.islands = list()
        self.name = "page{}".format(num)  # note: this is only used in svg files naming
        self.image_path = None


class UVVertex:
    """Vertex in 2D"""
    __slots__ = ('co', 'tup')

    def __init__(self, vector):
        self.co = vector.xy
        self.tup = tuple(self.co)


class UVEdge:
    """Edge in 2D"""
    # Every UVEdge is attached to only one UVFace
    # UVEdges are doubled as needed because they both have to point clockwise around their faces
    __slots__ = (
        'va', 'vb', 'uvface', 'loop',
        'min', 'max', 'bottom', 'top',
        'neighbor_left', 'neighbor_right', 'sticker')

    def __init__(self, vertex1: UVVertex, vertex2: UVVertex, uvface, loop):
        self.va = vertex1
        self.vb = vertex2
        self.update()
        self.uvface = uvface
        self.sticker = None
        self.loop = loop

    def update(self):
        """Update data if UVVertices have moved"""
        self.min, self.max = (self.va, self.vb) if (self.va.tup < self.vb.tup) else (self.vb, self.va)
        y1, y2 = self.va.co.y, self.vb.co.y
        self.bottom, self.top = (y1, y2) if y1 < y2 else (y2, y1)

    def is_uvface_upwards(self):
        return (self.va.tup < self.vb.tup) ^ self.uvface.flipped

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
        edge = (uvedge.vb.co - uvedge.va.co) if not uvedge.uvface.flipped else (uvedge.va.co - uvedge.vb.co)
        self.center = (uvedge.va.co + uvedge.vb.co) / 2
        self.size = size
        tangent = edge.normalized()
        cos, sin = tangent
        self.rot = M.Matrix(((cos, -sin), (sin, cos)))
        normal = M.Vector((sin, -cos))
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
        sin_a = sin_b = 0.75**0.5
        # len_a is length of the side adjacent to vertex a, len_b likewise
        len_a = len_b = sticker_width / sin_a

        # fix overlaps with the most often neighbour - its sticking target
        if first_vertex == other_second:
            cos_a = max(cos_a, edge.dot(other_edge) / (edge.length_squared))  # angles between pi/3 and 0
        elif second_vertex == other_first:
            cos_b = max(cos_b, edge.dot(other_edge) / (edge.length_squared))  # angles between pi/3 and 0

        # Fix tabs for sticking targets with small angles
        try:
            other_face_neighbor_left = other.neighbor_left
            other_face_neighbor_right = other.neighbor_right
            other_edge_neighbor_a = other_face_neighbor_left.vb.co - other.vb.co
            other_edge_neighbor_b = other_face_neighbor_right.va.co - other.va.co
            # Adjacent angles in the face
            cos_a = max(cos_a, -other_edge.dot(other_edge_neighbor_a) / (other_edge.length*other_edge_neighbor_a.length))
            cos_b = max(cos_b, other_edge.dot(other_edge_neighbor_b) / (other_edge.length*other_edge_neighbor_b.length))
        except AttributeError:  # neighbor data may be missing for edges with 3+ faces
            pass
        except ZeroDivisionError:
            pass

        # Calculate the lengths of the glue tab edges using the possibly smaller angles
        sin_a = abs(1 - cos_a**2)**0.5
        len_b = min(len_a, (edge.length * sin_a) / (sin_a * cos_b + sin_b * cos_a))
        len_a = 0 if sin_a == 0 else min(sticker_width / sin_a, (edge.length - len_b*cos_b) / cos_a)

        sin_b = abs(1 - cos_b**2)**0.5
        len_a = min(len_a, (edge.length * sin_b) / (sin_a * cos_b + sin_b * cos_a))
        len_b = 0 if sin_b == 0 else min(sticker_width / sin_b, (edge.length - len_a * cos_a) / cos_b)

        v3 = second_vertex.co + M.Matrix(((cos_b, -sin_b), (sin_b, cos_b))) @ edge * len_b / edge.length
        v4 = first_vertex.co + M.Matrix(((-cos_a, -sin_a), (sin_a, -cos_a))) @ edge * len_a / edge.length
        if v3 != v4:
            self.points = [second_vertex.co, v3, v4, first_vertex.co]
        else:
            self.points = [second_vertex.co, v3, first_vertex.co]

        sin, cos = edge.y / edge.length, edge.x / edge.length
        self.rot = M.Matrix(((cos, -sin), (sin, cos)))
        self.width = sticker_width * 0.9
        if index and uvedge.uvface.island is not other.uvface.island:
            self.text = "{}:{}".format(other.uvface.island.abbreviation, index)
        else:
            self.text = index
        self.center = (uvedge.va.co + uvedge.vb.co) / 2 + self.rot @ M.Vector((0, self.width * 0.2))
        self.bounds = [v3, v4, self.center] if v3 != v4 else [v3, self.center]


class NumberAlone:
    """Mark in the document: numbering inside the island denoting edges to be sticked"""
    __slots__ = ('bounds', 'center', 'rot', 'text', 'size')

    def __init__(self, uvedge, index, default_size=0.005):
        """Sticker is directly attached to the given UVEdge"""
        edge = (uvedge.va.co - uvedge.vb.co) if not uvedge.uvface.flipped else (uvedge.vb.co - uvedge.va.co)

        self.size = default_size
        sin, cos = edge.y / edge.length, edge.x / edge.length
        self.rot = M.Matrix(((cos, -sin), (sin, cos)))
        self.text = index
        self.center = (uvedge.va.co + uvedge.vb.co) / 2 - self.rot @ M.Vector((0, self.size * 1.2))
        self.bounds = [self.center]


def init_exporter(self, properties):
    self.page_size = M.Vector((properties.output_size_x, properties.output_size_y))
    self.style = properties.style
    margin = properties.output_margin
    self.margin = M.Vector((margin, margin))
    self.pure_net = (properties.output_type == 'NONE')
    self.do_create_stickers = properties.do_create_stickers
    self.text_size = properties.sticker_width
    self.angle_epsilon = properties.angle_epsilon


class Svg:
    """Simple SVG exporter"""

    def __init__(self, properties):
        init_exporter(self, properties)

    @classmethod
    def encode_image(cls, bpy_image):
        import tempfile
        import base64
        with tempfile.TemporaryDirectory() as directory:
            filename = directory + "/i.png"
            bpy_image.filepath_raw = filename
            bpy_image.save()
            return base64.encodebytes(open(filename, "rb").read()).decode('ascii')

    def format_vertex(self, vector):
        """Return a string with both coordinates of the given vertex."""
        return "{:.6f} {:.6f}".format((vector.x + self.margin.x) * 1000, (self.page_size.y - vector.y - self.margin.y) * 1000)

    def write(self, mesh, filename):
        """Write data to a file given by its name."""
        line_through = " L ".join  # used for formatting of SVG path data
        rows = "\n".join

        dl = ["{:.2f}".format(length * self.style.line_width * 1000) for length in (2, 5, 10)]
        format_style = {
            'SOLID': "none", 'DOT': "{0},{1}".format(*dl), 'DASH': "{1},{2}".format(*dl),
            'LONGDASH': "{2},{1}".format(*dl), 'DASHDOT': "{2},{1},{0},{1}".format(*dl)}

        def format_color(vec):
            return "#{:02x}{:02x}{:02x}".format(round(vec[0] * 255), round(vec[1] * 255), round(vec[2] * 255))

        def format_matrix(matrix):
            return " ".join("{:.6f}".format(cell) for column in matrix for cell in column)

        def path_convert(string, relto=os_path.dirname(filename)):
            assert(os_path)  # check the module was imported
            string = os_path.relpath(string, relto)
            if os_path.sep != '/':
                string = string.replace(os_path.sep, '/')
            return string

        styleargs = {
            name: format_color(getattr(self.style, name)) for name in (
                "outer_color", "outbg_color", "convex_color", "concave_color", "freestyle_color",
                "inbg_color", "sticker_color", "text_color")}
        styleargs.update({
            name: format_style[getattr(self.style, name)] for name in
            ("outer_style", "convex_style", "concave_style", "freestyle_style")})
        styleargs.update({
            name: getattr(self.style, attr)[3] for name, attr in (
                ("outer_alpha", "outer_color"), ("outbg_alpha", "outbg_color"),
                ("convex_alpha", "convex_color"), ("concave_alpha", "concave_color"),
                ("freestyle_alpha", "freestyle_color"),
                ("inbg_alpha", "inbg_color"), ("sticker_alpha", "sticker_color"),
                ("text_alpha", "text_color"))})
        styleargs.update({
            name: getattr(self.style, name) * self.style.line_width * 1000 for name in
            ("outer_width", "convex_width", "concave_width", "freestyle_width", "outbg_width", "inbg_width")})
        for num, page in enumerate(mesh.pages):
            page_filename = "{}_{}.svg".format(filename[:filename.rfind(".svg")], page.name) if len(mesh.pages) > 1 else filename
            with open(page_filename, 'w') as f:
                print(self.svg_base.format(width=self.page_size.x*1000, height=self.page_size.y*1000), file=f)
                print(self.css_base.format(**styleargs), file=f)
                if page.image_path:
                    print(
                        self.image_linked_tag.format(
                            pos="{0:.6f} {0:.6f}".format(self.margin.x*1000),
                            width=(self.page_size.x - 2 * self.margin.x)*1000,
                            height=(self.page_size.y - 2 * self.margin.y)*1000,
                            path=path_convert(page.image_path)),
                        file=f)
                if len(page.islands) > 1:
                    print("<g>", file=f)

                for island in page.islands:
                    print("<g>", file=f)
                    if island.image_path:
                        print(
                            self.image_linked_tag.format(
                                pos=self.format_vertex(island.pos + M.Vector((0, island.bounding_box.y))),
                                width=island.bounding_box.x*1000,
                                height=island.bounding_box.y*1000,
                                path=path_convert(island.image_path)),
                            file=f)
                    elif island.embedded_image:
                        print(
                            self.image_embedded_tag.format(
                                pos=self.format_vertex(island.pos + M.Vector((0, island.bounding_box.y))),
                                width=island.bounding_box.x*1000,
                                height=island.bounding_box.y*1000,
                                path=island.image_path),
                            island.embedded_image, "'/>",
                            file=f, sep="")
                    if island.title:
                        print(
                            self.text_tag.format(
                                size=1000 * self.text_size,
                                x=1000 * (island.bounding_box.x*0.5 + island.pos.x + self.margin.x),
                                y=1000 * (self.page_size.y - island.pos.y - self.margin.y - 0.2 * self.text_size),
                                label=island.title),
                            file=f)

                    data_markers, data_stickerfill = list(), list()
                    for marker in island.markers:
                        if isinstance(marker, Sticker):
                            data_stickerfill.append("M {} Z".format(
                                line_through(self.format_vertex(co + island.pos) for co in marker.points)))
                            if marker.text:
                                data_markers.append(self.text_transformed_tag.format(
                                    label=marker.text,
                                    pos=self.format_vertex(marker.center + island.pos),
                                    mat=format_matrix(marker.rot),
                                    size=marker.width * 1000))
                        elif isinstance(marker, Arrow):
                            size = marker.size * 1000
                            position = marker.center + marker.size * marker.rot @ M.Vector((0, -0.9))
                            data_markers.append(self.arrow_marker_tag.format(
                                index=marker.text,
                                arrow_pos=self.format_vertex(marker.center + island.pos),
                                scale=size,
                                pos=self.format_vertex(position + island.pos - marker.size*M.Vector((0, 0.4))),
                                mat=format_matrix(size * marker.rot)))
                        elif isinstance(marker, NumberAlone):
                            data_markers.append(self.text_transformed_tag.format(
                                label=marker.text,
                                pos=self.format_vertex(marker.center + island.pos),
                                mat=format_matrix(marker.rot),
                                size=marker.size * 1000))
                    if data_stickerfill and self.style.sticker_color[3] > 0:
                        print("<path class='sticker' d='", rows(data_stickerfill), "'/>", file=f)

                    data_outer, data_convex, data_concave, data_freestyle = (list() for i in range(4))
                    outer_edges = set(island.boundary)
                    while outer_edges:
                        data_loop = list()
                        uvedge = outer_edges.pop()
                        while 1:
                            if uvedge.sticker:
                                data_loop.extend(self.format_vertex(co + island.pos) for co in uvedge.sticker.points[1:])
                            else:
                                vertex = uvedge.vb if uvedge.uvface.flipped else uvedge.va
                                data_loop.append(self.format_vertex(vertex.co + island.pos))
                            uvedge = uvedge.neighbor_right
                            try:
                                outer_edges.remove(uvedge)
                            except KeyError:
                                break
                        data_outer.append("M {} Z".format(line_through(data_loop)))

                    visited_edges = set()
                    for loop, uvedge in island.edges.items():
                        edge = mesh.edges[loop.edge]
                        if edge.is_cut(uvedge.uvface.face) and not uvedge.sticker:
                            continue
                        data_uvedge = "M {}".format(
                            line_through(self.format_vertex(v.co + island.pos) for v in (uvedge.va, uvedge.vb)))
                        if edge.freestyle:
                            data_freestyle.append(data_uvedge)
                        # each uvedge is in two opposite-oriented variants; we want to add each only once
                        vertex_pair = frozenset((uvedge.va, uvedge.vb))
                        if vertex_pair not in visited_edges:
                            visited_edges.add(vertex_pair)
                            if edge.angle > self.angle_epsilon:
                                data_convex.append(data_uvedge)
                            elif edge.angle < -self.angle_epsilon:
                                data_concave.append(data_uvedge)
                    if island.is_inside_out:
                        data_convex, data_concave = data_concave, data_convex

                    if data_freestyle:
                        print("<path class='freestyle' d='", rows(data_freestyle), "'/>", file=f)
                    if (data_convex or data_concave) and not self.pure_net and self.style.use_inbg:
                        print("<path class='inner_background' d='", rows(data_convex + data_concave), "'/>", file=f)
                    if data_convex:
                        print("<path class='convex' d='", rows(data_convex), "'/>", file=f)
                    if data_concave:
                        print("<path class='concave' d='", rows(data_concave), "'/>", file=f)
                    if data_outer:
                        if not self.pure_net and self.style.use_outbg:
                            print("<path class='outer_background' d='", rows(data_outer), "'/>", file=f)
                        print("<path class='outer' d='", rows(data_outer), "'/>", file=f)
                    if data_markers:
                        print(rows(data_markers), file=f)
                    print("</g>", file=f)

                if len(page.islands) > 1:
                    print("</g>", file=f)
                print("</svg>", file=f)

    image_linked_tag = "<image transform='translate({pos})' width='{width:.6f}' height='{height:.6f}' xlink:href='{path}'/>"
    image_embedded_tag = "<image transform='translate({pos})' width='{width:.6f}' height='{height:.6f}' xlink:href='data:image/png;base64,"
    text_tag = "<text transform='translate({x} {y})' style='font-size:{size:.2f}'><tspan>{label}</tspan></text>"
    text_transformed_tag = "<text transform='matrix({mat} {pos})' style='font-size:{size:.2f}'><tspan>{label}</tspan></text>"
    arrow_marker_tag = "<g><path transform='matrix({mat} {arrow_pos})' class='arrow' d='M 0 0 L 1 1 L 0 0.25 L -1 1 Z'/>" \
        "<text transform='translate({pos})' style='font-size:{scale:.2f}'><tspan>{index}</tspan></text></g>"

    svg_base = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
    <svg xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink' version='1.1'
    width='{width:.2f}mm' height='{height:.2f}mm' viewBox='0 0 {width:.2f} {height:.2f}'>"""

    css_base = """<style type="text/css">
    path {{
        fill: none;
        stroke-linecap: butt;
        stroke-linejoin: bevel;
        stroke-dasharray: none;
    }}
    path.outer {{
        stroke: {outer_color};
        stroke-dasharray: {outer_style};
        stroke-dashoffset: 0;
        stroke-width: {outer_width:.2};
        stroke-opacity: {outer_alpha:.2};
    }}
    path.convex {{
        stroke: {convex_color};
        stroke-dasharray: {convex_style};
        stroke-dashoffset:0;
        stroke-width:{convex_width:.2};
        stroke-opacity: {convex_alpha:.2}
    }}
    path.concave {{
        stroke: {concave_color};
        stroke-dasharray: {concave_style};
        stroke-dashoffset: 0;
        stroke-width: {concave_width:.2};
        stroke-opacity: {concave_alpha:.2}
    }}
    path.freestyle {{
        stroke: {freestyle_color};
        stroke-dasharray: {freestyle_style};
        stroke-dashoffset: 0;
        stroke-width: {freestyle_width:.2};
        stroke-opacity: {freestyle_alpha:.2}
    }}
    path.outer_background {{
        stroke: {outbg_color};
        stroke-opacity: {outbg_alpha};
        stroke-width: {outbg_width:.2}
    }}
    path.inner_background {{
        stroke: {inbg_color};
        stroke-opacity: {inbg_alpha};
        stroke-width: {inbg_width:.2}
    }}
    path.sticker {{
        fill: {sticker_color};
        stroke: none;
        fill-opacity: {sticker_alpha:.2};
    }}
    path.arrow {{
        fill: {text_color};
    }}
    text {{
        font-style: normal;
        fill: {text_color};
        fill-opacity: {text_alpha:.2};
        stroke: none;
    }}
    text, tspan {{
        text-anchor:middle;
    }}
    </style>"""


class Pdf:
    """Simple PDF exporter"""

    mm_to_pt = 72 / 25.4
    character_width_packed = {
        191: "'", 222: 'ijl\x82\x91\x92', 278: '|¦\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f !,./:;I[\\]ft\xa0·ÌÍÎÏìíîï',
        333: '()-`r\x84\x88\x8b\x93\x94\x98\x9b¡¨\xad¯²³´¸¹{}', 350: '\x7f\x81\x8d\x8f\x90\x95\x9d', 365: '"ºª*°', 469: '^', 500: 'Jcksvxyz\x9a\x9eçýÿ', 584: '¶+<=>~¬±×÷', 611: 'FTZ\x8e¿ßø',
        667: '&ABEKPSVXY\x8a\x9fÀÁÂÃÄÅÈÉÊËÝÞ', 722: 'CDHNRUwÇÐÑÙÚÛÜ', 737: '©®', 778: 'GOQÒÓÔÕÖØ', 833: 'Mm¼½¾', 889: '%æ', 944: 'W\x9c', 1000: '\x85\x89\x8c\x97\x99Æ', 1015: '@', }
    character_width = {c: value for (value, chars) in character_width_packed.items() for c in chars}

    def __init__(self, properties):
        init_exporter(self, properties)
        self.styles = dict()

    def text_width(self, text, scale=None):
        return (scale or self.text_size) * sum(self.character_width.get(c, 556) for c in text) / 1000

    def styling(self, name, do_stroke=True):
        s, m, l = (length * self.style.line_width * 1000 for length in (1, 4, 9))
        format_style = {'SOLID': [], 'DOT': [s, m], 'DASH': [m, l], 'LONGDASH': [l, m], 'DASHDOT': [l, m, s, m]}
        style, color, width = (getattr(self.style, f"{name}_{arg}", None) for arg in ("style", "color", "width"))
        style = style or 'SOLID'
        result = ["q"]
        if do_stroke:
            result += [
                "[ " + " ".join("{:.3f}".format(num) for num in format_style[style]) + " ] 0 d",
                "{0:.3f} {1:.3f} {2:.3f} RG".format(*color),
                "{:.3f} w".format(self.style.line_width * 1000 * width),
                ]
        else:
            result.append("{0:.3f} {1:.3f} {2:.3f} rg".format(*color))
        if color[3] < 1:
            style_name = "R{:03}".format(round(1000 * color[3]))
            result.append("/{} gs".format(style_name))
            if style_name not in self.styles:
                self.styles[style_name] = {"CA": color[3], "ca": color[3]}
        return result

    @classmethod
    def encode_image(cls, bpy_image):
        data = bytes(int(255 * px) for (i, px) in enumerate(bpy_image.pixels) if i % 4 != 3)
        image = {
            "Type": "XObject", "Subtype": "Image", "Width": bpy_image.size[0], "Height": bpy_image.size[1],
            "ColorSpace": "DeviceRGB", "BitsPerComponent": 8, "Interpolate": True,
            "Filter": ["ASCII85Decode", "FlateDecode"], "stream": data}
        return image

    def write(self, mesh, filename):
        def format_dict(obj, refs=tuple()):
            content = "".join("/{} {}\n".format(key, format_value(value, refs)) for (key, value) in obj.items())
            return f"<< {content} >>"

        def line_through(seq):
            fmt = "{0.x:.6f} {0.y:.6f} {1} ".format
            return "".join(fmt(1000*co, cmd) for (co, cmd) in zip(seq, chain("m", repeat("l"))))

        def format_value(value, refs=tuple()):
            if value in refs:
                return "{} 0 R".format(refs.index(value) + 1)
            elif type(value) is dict:
                return format_dict(value, refs)
            elif type(value) in (list, tuple):
                return "[ " + " ".join(format_value(item, refs) for item in value) + " ]"
            elif type(value) is int:
                return str(value)
            elif type(value) is float:
                return "{:.6f}".format(value)
            elif type(value) is bool:
                return "true" if value else "false"
            else:
                return "/{}".format(value)  # this script can output only PDF names, no strings

        def write_object(index, obj, refs, f, stream=None):
            byte_count = f.write("{} 0 obj\n".format(index).encode())
            if type(obj) is not dict:
                stream, obj = obj, dict()
            elif "stream" in obj:
                stream = obj.pop("stream")
            if stream:
                obj["Filter"] = "FlateDecode"
                stream = encode(stream)
                obj["Length"] = len(stream)
            byte_count += f.write(format_dict(obj, refs).encode())
            if stream:
                byte_count += f.write(b"\nstream\n")
                byte_count += f.write(stream)
                byte_count += f.write(b"\nendstream")
            return byte_count + f.write(b"\nendobj\n")

        def encode(data):
            from zlib import compress
            if hasattr(data, "encode"):
                data = data.encode()
            return compress(data)

        page_size_pt = 1000 * self.mm_to_pt * self.page_size
        reset_style = ["Q"]  # graphic command for later use
        root = {"Type": "Pages", "MediaBox": [0, 0, page_size_pt.x, page_size_pt.y], "Kids": list()}
        catalog = {"Type": "Catalog", "Pages": root}
        font = {
            "Type": "Font", "Subtype": "Type1", "Name": "F1",
            "BaseFont": "Helvetica", "Encoding": "MacRomanEncoding"}
        objects = [root, catalog, font]

        for page in mesh.pages:
            commands = ["{0:.6f} 0 0 {0:.6f} 0 0 cm".format(self.mm_to_pt)]
            resources = {"Font": {"F1": font}, "ExtGState": self.styles, "ProcSet": ["PDF"]}
            if any(island.embedded_image for island in page.islands):
                resources["XObject"] = dict()
                resources["ProcSet"].append("ImageC")
            for island in page.islands:
                commands.append("q 1 0 0 1 {0.x:.6f} {0.y:.6f} cm".format(1000*(self.margin + island.pos)))
                if island.embedded_image:
                    identifier = "I{}".format(len(resources["XObject"]) + 1)
                    commands.append(self.command_image.format(1000 * island.bounding_box, identifier))
                    objects.append(island.embedded_image)
                    resources["XObject"][identifier] = island.embedded_image

                if island.title:
                    commands += self.styling("text", do_stroke=False)
                    commands.append(self.command_label.format(
                        size=1000*self.text_size,
                        x=500 * (island.bounding_box.x - self.text_width(island.title)),
                        y=1000 * 0.2 * self.text_size,
                        label=island.title))
                    commands += reset_style

                data_markers, data_stickerfill = list(), list()
                for marker in island.markers:
                    if isinstance(marker, Sticker):
                        data_stickerfill.append(line_through(marker.points) + "f")
                        if marker.text:
                            data_markers.append(self.command_sticker.format(
                                label=marker.text,
                                pos=1000*marker.center,
                                mat=marker.rot,
                                align=-500 * self.text_width(marker.text, marker.width),
                                size=1000*marker.width))
                    elif isinstance(marker, Arrow):
                        size = 1000 * marker.size
                        position = 1000 * (marker.center + marker.size * marker.rot @ M.Vector((0, -0.9)))
                        data_markers.append(self.command_arrow.format(
                            index=marker.text,
                            arrow_pos=1000 * marker.center,
                            pos=position - 1000 * M.Vector((0.5 * self.text_width(marker.text), 0.4 * self.text_size)),
                            mat=size * marker.rot,
                            size=size))
                    elif isinstance(marker, NumberAlone):
                        data_markers.append(self.command_number.format(
                            label=marker.text,
                            pos=1000*marker.center,
                            mat=marker.rot,
                            size=1000*marker.size))

                data_outer, data_convex, data_concave, data_freestyle = (list() for i in range(4))
                outer_edges = set(island.boundary)
                while outer_edges:
                    data_loop = list()
                    uvedge = outer_edges.pop()
                    while 1:
                        if uvedge.sticker:
                            data_loop.extend(uvedge.sticker.points[1:])
                        else:
                            vertex = uvedge.vb if uvedge.uvface.flipped else uvedge.va
                            data_loop.append(vertex.co)
                        uvedge = uvedge.neighbor_right
                        try:
                            outer_edges.remove(uvedge)
                        except KeyError:
                            break
                    data_outer.append(line_through(data_loop) + "s")

                for loop, uvedge in island.edges.items():
                    edge = mesh.edges[loop.edge]
                    if edge.is_cut(uvedge.uvface.face) and not uvedge.sticker:
                        continue
                    data_uvedge = line_through((uvedge.va.co, uvedge.vb.co)) + "S"
                    if edge.freestyle:
                        data_freestyle.append(data_uvedge)
                    # each uvedge exists in two opposite-oriented variants; we want to add each only once
                    if uvedge.sticker or uvedge.uvface.flipped != (id(uvedge.va) > id(uvedge.vb)):
                        if edge.angle > self.angle_epsilon:
                            data_convex.append(data_uvedge)
                        elif edge.angle < -self.angle_epsilon:
                            data_concave.append(data_uvedge)
                if island.is_inside_out:
                    data_convex, data_concave = data_concave, data_convex

                if data_stickerfill and self.style.sticker_color[3] > 0:
                    commands += chain(self.styling("sticker", do_stroke=False), data_stickerfill, reset_style)
                if data_freestyle:
                    commands += chain(self.styling("freestyle"), data_freestyle, reset_style)
                if (data_convex or data_concave) and not self.pure_net and self.style.use_inbg:
                    commands += chain(self.styling("inbg"), data_convex, data_concave, reset_style)
                if data_convex:
                    commands += chain(self.styling("convex"), data_convex, reset_style)
                if data_concave:
                    commands += chain(self.styling("concave"), data_concave, reset_style)
                if data_outer:
                    if not self.pure_net and self.style.use_outbg:
                        commands += chain(self.styling("outbg"), data_outer, reset_style)
                    commands += chain(self.styling("outer"), data_outer, reset_style)
                if data_markers:
                    commands += chain(self.styling("text", do_stroke=False), data_markers, reset_style)
                commands += reset_style  # return from island to page coordinates
            content = "\n".join(commands)
            page = {"Type": "Page", "Parent": root, "Contents": content, "Resources": resources}
            root["Kids"].append(page)
            objects += page, content
            objects.extend(self.styles.values())

        root["Count"] = len(root["Kids"])
        with open(filename, "wb+") as f:
            xref_table = list()
            position = 0
            position += f.write(b"%PDF-1.4\n")
            position += f.write(b"%\xde\xad\xbe\xef\n")
            for index, obj in enumerate(objects, 1):
                xref_table.append(position)
                position += write_object(index, obj, objects, f)
            xref_pos = position
            f.write("xref\n0 {}\n".format(len(xref_table) + 1).encode())
            f.write("{:010} {:05} f\r\n".format(0, 65535).encode())
            for position in xref_table:
                f.write("{:010} {:05} n\r\n".format(position, 0).encode())
            f.write(b"trailer\n")
            f.write(format_dict({"Size": len(xref_table) + 1, "Root": catalog}, objects).encode())
            f.write("\nstartxref\n{}\n%%EOF\n".format(xref_pos).encode())

    command_label = "q /F1 {size:.6f} Tf BT {x:.6f} {y:.6f} Td ({label}) Tj ET Q"
    command_image = "q {0.x:.6f} 0 0 {0.y:.6f} 0 0 cm 1 0 0 -1 0 1 cm /{1} Do Q"
    command_sticker = "q /F1 {size:.6f} Tf {mat[0][0]:.6f} {mat[1][0]:.6f} {mat[0][1]:.6f} {mat[1][1]:.6f} {pos.x:.6f} {pos.y:.6f} cm BT {align:.6f} 0 Td ({label}) Tj ET Q"
    command_arrow = "q /F1 {size:.6f} Tf BT {pos.x:.6f} {pos.y:.6f} Td ({index}) Tj ET {mat[0][0]:.6f} {mat[1][0]:.6f} {mat[0][1]:.6f} {mat[1][1]:.6f} {arrow_pos.x:.6f} {arrow_pos.y:.6f} cm 0 0 m 1 -1 l 0 -0.25 l -1 -1 l f Q"
    command_number = "q /F1 {size:.6f} Tf {mat[0][0]:.6f} {mat[1][0]:.6f} {mat[0][1]:.6f} {mat[1][1]:.6f} {pos.x:.6f} {pos.y:.6f} cm BT ({label}) Tj ET Q"


class Unfold(bpy.types.Operator):
    """Blender Operator: unfold the selected object."""

    bl_idname = "mesh.unfold"
    bl_label = "Unfold"
    bl_description = "Mark seams so that the mesh can be exported as a paper model"
    bl_options = {'REGISTER', 'UNDO'}
    edit: bpy.props.BoolProperty(default=False, options={'HIDDEN'})
    priority_effect_convex: bpy.props.FloatProperty(
        name="Priority Convex", description="Priority effect for edges in convex angles",
        default=default_priority_effect['CONVEX'], soft_min=-1, soft_max=10, subtype='FACTOR')
    priority_effect_concave: bpy.props.FloatProperty(
        name="Priority Concave", description="Priority effect for edges in concave angles",
        default=default_priority_effect['CONCAVE'], soft_min=-1, soft_max=10, subtype='FACTOR')
    priority_effect_length: bpy.props.FloatProperty(
        name="Priority Length", description="Priority effect of edge length",
        default=default_priority_effect['LENGTH'], soft_min=-10, soft_max=1, subtype='FACTOR')
    do_create_uvmap: bpy.props.BoolProperty(
        name="Create UVMap", description="Create a new UV Map showing the islands and page layout", default=False)
    object = None

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == "MESH"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.active = not self.object or len(self.object.data.uv_layers) < 8
        col.prop(self.properties, "do_create_uvmap")
        layout.label(text="Edge Cutting Factors:")
        col = layout.column(align=True)
        col.label(text="Face Angle:")
        col.prop(self.properties, "priority_effect_convex", text="Convex")
        col.prop(self.properties, "priority_effect_concave", text="Concave")
        layout.prop(self.properties, "priority_effect_length", text="Edge Length")

    def execute(self, context):
        sce = bpy.context.scene
        settings = sce.paper_model
        recall_mode = context.object.mode
        bpy.ops.object.mode_set(mode='EDIT')

        self.object = context.object

        cage_size = M.Vector((settings.output_size_x, settings.output_size_y))
        priority_effect = {
            'CONVEX': self.priority_effect_convex,
            'CONCAVE': self.priority_effect_concave,
            'LENGTH': self.priority_effect_length}
        try:
            unfolder = Unfolder(self.object)
            unfolder.do_create_uvmap = self.do_create_uvmap
            scale = sce.unit_settings.scale_length / settings.scale
            unfolder.prepare(cage_size, priority_effect, scale, settings.limit_by_page)
            unfolder.mesh.mark_cuts()
        except UnfoldError as error:
            self.report(type={'ERROR_INVALID_INPUT'}, message=error.args[0])
            error.mesh_select()
            bpy.ops.object.mode_set(mode=recall_mode)
            return {'CANCELLED'}
        mesh = self.object.data
        mesh.update()
        if mesh.paper_island_list:
            unfolder.copy_island_names(mesh.paper_island_list)
        island_list = mesh.paper_island_list
        attributes = {item.label: (item.abbreviation, item.auto_label, item.auto_abbrev) for item in island_list}
        island_list.clear()  # remove previously defined islands
        for island in unfolder.mesh.islands:
            # add islands to UI list and set default descriptions
            list_item = island_list.add()
            # add faces' IDs to the island
            for face in island.faces:
                lface = list_item.faces.add()
                lface.id = face.index
            list_item["label"] = island.label
            list_item["abbreviation"], list_item["auto_label"], list_item["auto_abbrev"] = attributes.get(
                island.label,
                (island.abbreviation, True, True))
            island_item_changed(list_item, context)
            mesh.paper_island_index = -1

        del unfolder
        bpy.ops.object.mode_set(mode=recall_mode)
        return {'FINISHED'}


class ClearAllSeams(bpy.types.Operator):
    """Blender Operator: clear all seams of the active Mesh and all its unfold data"""

    bl_idname = "mesh.clear_all_seams"
    bl_label = "Clear All Seams"
    bl_description = "Clear all the seams and unfolded islands of the active object"

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        ob = context.active_object
        mesh = ob.data

        for edge in mesh.edges:
            edge.use_seam = False
        mesh.paper_island_list.clear()

        return {'FINISHED'}


def page_size_preset_changed(self, context):
    """Update the actual document size to correct values"""
    if hasattr(self, "limit_by_page") and not self.limit_by_page:
        return
    if self.page_size_preset == 'A4':
        self.output_size_x = 0.210
        self.output_size_y = 0.297
    elif self.page_size_preset == 'A3':
        self.output_size_x = 0.297
        self.output_size_y = 0.420
    elif self.page_size_preset == 'US_LETTER':
        self.output_size_x = 0.216
        self.output_size_y = 0.279
    elif self.page_size_preset == 'US_LEGAL':
        self.output_size_x = 0.216
        self.output_size_y = 0.356


class PaperModelStyle(bpy.types.PropertyGroup):
    line_styles = [
        ('SOLID', "Solid (----)", "Solid line"),
        ('DOT', "Dots (. . .)", "Dotted line"),
        ('DASH', "Short Dashes (- - -)", "Solid line"),
        ('LONGDASH', "Long Dashes (-- --)", "Solid line"),
        ('DASHDOT', "Dash-dotted (-- .)", "Solid line")
    ]
    outer_color: bpy.props.FloatVectorProperty(
        name="Outer Lines", description="Color of net outline",
        default=(0.0, 0.0, 0.0, 1.0), min=0, max=1, subtype='COLOR', size=4)
    outer_style: bpy.props.EnumProperty(
        name="Outer Lines Drawing Style", description="Drawing style of net outline",
        default='SOLID', items=line_styles)
    line_width: bpy.props.FloatProperty(
        name="Base Lines Thickness", description="Base thickness of net lines, each actual value is a multiple of this length",
        default=1e-4, min=0, soft_max=5e-3, precision=5, step=1e-2, subtype="UNSIGNED", unit="LENGTH")
    outer_width: bpy.props.FloatProperty(
        name="Outer Lines Thickness", description="Relative thickness of net outline",
        default=3, min=0, soft_max=10, precision=1, step=10, subtype='FACTOR')
    use_outbg: bpy.props.BoolProperty(
        name="Highlight Outer Lines", description="Add another line below every line to improve contrast",
        default=True)
    outbg_color: bpy.props.FloatVectorProperty(
        name="Outer Highlight", description="Color of the highlight for outer lines",
        default=(1.0, 1.0, 1.0, 1.0), min=0, max=1, subtype='COLOR', size=4)
    outbg_width: bpy.props.FloatProperty(
        name="Outer Highlight Thickness", description="Relative thickness of the highlighting lines",
        default=5, min=0, soft_max=10, precision=1, step=10, subtype='FACTOR')

    convex_color: bpy.props.FloatVectorProperty(
        name="Inner Convex Lines", description="Color of lines to be folded to a convex angle",
        default=(0.0, 0.0, 0.0, 1.0), min=0, max=1, subtype='COLOR', size=4)
    convex_style: bpy.props.EnumProperty(
        name="Convex Lines Drawing Style", description="Drawing style of lines to be folded to a convex angle",
        default='DASH', items=line_styles)
    convex_width: bpy.props.FloatProperty(
        name="Convex Lines Thickness", description="Relative thickness of concave lines",
        default=2, min=0, soft_max=10, precision=1, step=10, subtype='FACTOR')
    concave_color: bpy.props.FloatVectorProperty(
        name="Inner Concave Lines", description="Color of lines to be folded to a concave angle",
        default=(0.0, 0.0, 0.0, 1.0), min=0, max=1, subtype='COLOR', size=4)
    concave_style: bpy.props.EnumProperty(
        name="Concave Lines Drawing Style", description="Drawing style of lines to be folded to a concave angle",
        default='DASHDOT', items=line_styles)
    concave_width: bpy.props.FloatProperty(
        name="Concave Lines Thickness", description="Relative thickness of concave lines",
        default=2, min=0, soft_max=10, precision=1, step=10, subtype='FACTOR')
    freestyle_color: bpy.props.FloatVectorProperty(
        name="Freestyle Edges", description="Color of lines marked as Freestyle Edge",
        default=(0.0, 0.0, 0.0, 1.0), min=0, max=1, subtype='COLOR', size=4)
    freestyle_style: bpy.props.EnumProperty(
        name="Freestyle Edges Drawing Style", description="Drawing style of Freestyle Edges",
        default='SOLID', items=line_styles)
    freestyle_width: bpy.props.FloatProperty(
        name="Freestyle Edges Thickness", description="Relative thickness of Freestyle edges",
        default=2, min=0, soft_max=10, precision=1, step=10, subtype='FACTOR')
    use_inbg: bpy.props.BoolProperty(
        name="Highlight Inner Lines", description="Add another line below every line to improve contrast",
        default=True)
    inbg_color: bpy.props.FloatVectorProperty(
        name="Inner Highlight", description="Color of the highlight for inner lines",
        default=(1.0, 1.0, 1.0, 1.0), min=0, max=1, subtype='COLOR', size=4)
    inbg_width: bpy.props.FloatProperty(
        name="Inner Highlight Thickness", description="Relative thickness of the highlighting lines",
        default=2, min=0, soft_max=10, precision=1, step=10, subtype='FACTOR')

    sticker_color: bpy.props.FloatVectorProperty(
        name="Tabs Fill", description="Fill color of sticking tabs",
        default=(0.9, 0.9, 0.9, 1.0), min=0, max=1, subtype='COLOR', size=4)
    text_color: bpy.props.FloatVectorProperty(
        name="Text Color", description="Color of all text used in the document",
        default=(0.0, 0.0, 0.0, 1.0), min=0, max=1, subtype='COLOR', size=4)
bpy.utils.register_class(PaperModelStyle)


class ExportPaperModel(bpy.types.Operator):
    """Blender Operator: save the selected object's net and optionally bake its texture"""

    bl_idname = "export_mesh.paper_model"
    bl_label = "Export Paper Model"
    bl_description = "Export the selected object's net and optionally bake its texture"
    bl_options = {'PRESET'}

    filepath: bpy.props.StringProperty(
        name="File Path", description="Target file to save the SVG", options={'SKIP_SAVE'})
    filename: bpy.props.StringProperty(
        name="File Name", description="Name of the file", options={'SKIP_SAVE'})
    directory: bpy.props.StringProperty(
        name="Directory", description="Directory of the file", options={'SKIP_SAVE'})
    page_size_preset: bpy.props.EnumProperty(
        name="Page Size", description="Size of the exported document",
        default='A4', update=page_size_preset_changed, items=global_paper_sizes)
    output_size_x: bpy.props.FloatProperty(
        name="Page Width", description="Width of the exported document",
        default=0.210, soft_min=0.105, soft_max=0.841, subtype="UNSIGNED", unit="LENGTH")
    output_size_y: bpy.props.FloatProperty(
        name="Page Height", description="Height of the exported document",
        default=0.297, soft_min=0.148, soft_max=1.189, subtype="UNSIGNED", unit="LENGTH")
    output_margin: bpy.props.FloatProperty(
        name="Page Margin", description="Distance from page borders to the printable area",
        default=0.005, min=0, soft_max=0.1, step=0.1, subtype="UNSIGNED", unit="LENGTH")
    output_type: bpy.props.EnumProperty(
        name="Textures", description="Source of a texture for the model",
        default='NONE', items=[
            ('NONE', "No Texture", "Export the net only"),
            ('TEXTURE', "From Materials", "Render the diffuse color and all painted textures"),
            ('AMBIENT_OCCLUSION', "Ambient Occlusion", "Render the Ambient Occlusion pass"),
            ('RENDER', "Full Render", "Render the material in actual scene illumination"),
            ('SELECTED_TO_ACTIVE', "Selected to Active", "Render all selected surrounding objects as a texture")
        ])
    do_create_stickers: bpy.props.BoolProperty(
        name="Create Tabs", description="Create gluing tabs around the net (useful for paper)",
        default=True)
    do_create_numbers: bpy.props.BoolProperty(
        name="Create Numbers", description="Enumerate edges to make it clear which edges should be sticked together",
        default=True)
    sticker_width: bpy.props.FloatProperty(
        name="Tabs and Text Size", description="Width of gluing tabs and their numbers",
        default=0.005, soft_min=0, soft_max=0.05, step=0.1, subtype="UNSIGNED", unit="LENGTH")
    angle_epsilon: bpy.props.FloatProperty(
        name="Hidden Edge Angle", description="Folds with angle below this limit will not be drawn",
        default=pi/360, min=0, soft_max=pi/4, step=0.01, subtype="ANGLE", unit="ROTATION")
    output_dpi: bpy.props.FloatProperty(
        name="Resolution (DPI)", description="Resolution of images in pixels per inch",
        default=90, min=1, soft_min=30, soft_max=600, subtype="UNSIGNED")
    bake_samples: bpy.props.IntProperty(
        name="Samples", description="Number of samples to render for each pixel",
        default=64, min=1, subtype="UNSIGNED")
    file_format: bpy.props.EnumProperty(
        name="Document Format", description="File format of the exported net",
        default='PDF', items=[
            ('PDF', "PDF", "Adobe Portable Document Format 1.4"),
            ('SVG', "SVG", "W3C Scalable Vector Graphics"),
        ])
    image_packing: bpy.props.EnumProperty(
        name="Image Packing Method", description="Method of attaching baked image(s) to the SVG",
        default='ISLAND_EMBED', items=[
            ('PAGE_LINK', "Single Linked", "Bake one image per page of output and save it separately"),
            ('ISLAND_LINK', "Linked", "Bake images separately for each island and save them in a directory"),
            ('ISLAND_EMBED', "Embedded", "Bake images separately for each island and embed them into the SVG")
        ])
    scale: bpy.props.FloatProperty(
        name="Scale", description="Divisor of all dimensions when exporting",
        default=1, soft_min=1.0, soft_max=100.0, subtype='FACTOR', precision=1)
    do_create_uvmap: bpy.props.BoolProperty(
        name="Create UVMap",
        description="Create a new UV Map showing the islands and page layout",
        default=False, options={'SKIP_SAVE'})
    ui_expanded_document: bpy.props.BoolProperty(
        name="Show Document Settings Expanded",
        description="Shows the box 'Document Settings' expanded in user interface",
        default=True, options={'SKIP_SAVE'})
    ui_expanded_style: bpy.props.BoolProperty(
        name="Show Style Settings Expanded",
        description="Shows the box 'Colors and Style' expanded in user interface",
        default=False, options={'SKIP_SAVE'})
    style: bpy.props.PointerProperty(type=PaperModelStyle)

    unfolder = None

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def prepare(self, context):
        sce = context.scene
        self.recall_mode = context.object.mode
        bpy.ops.object.mode_set(mode='EDIT')

        self.object = context.active_object
        self.unfolder = Unfolder(self.object)
        cage_size = M.Vector((sce.paper_model.output_size_x, sce.paper_model.output_size_y))
        unfolder_scale = sce.unit_settings.scale_length/self.scale
        self.unfolder.prepare(cage_size, scale=unfolder_scale, limit_by_page=sce.paper_model.limit_by_page)
        if sce.paper_model.use_auto_scale:
            self.scale = ceil(self.get_scale_ratio(sce))

    def recall(self):
        if self.unfolder:
            del self.unfolder
        bpy.ops.object.mode_set(mode=self.recall_mode)

    def invoke(self, context, event):
        self.scale = context.scene.paper_model.scale
        try:
            self.prepare(context)
        except UnfoldError as error:
            self.report(type={'ERROR_INVALID_INPUT'}, message=error.args[0])
            error.mesh_select()
            self.recall()
            return {'CANCELLED'}
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if not self.unfolder:
            self.prepare(context)
        self.unfolder.do_create_uvmap = self.do_create_uvmap
        try:
            if self.object.data.paper_island_list:
                self.unfolder.copy_island_names(self.object.data.paper_island_list)
            self.unfolder.save(self.properties)
            self.report({'INFO'}, "Saved a {}-page document".format(len(self.unfolder.mesh.pages)))
            return {'FINISHED'}
        except UnfoldError as error:
            self.report(type={'ERROR_INVALID_INPUT'}, message=error.args[0])
            return {'CANCELLED'}
        finally:
            self.recall()

    def get_scale_ratio(self, sce):
        margin = self.output_margin + self.sticker_width
        if min(self.output_size_x, self.output_size_y) <= 2 * margin:
            return False
        output_inner_size = M.Vector((self.output_size_x - 2*margin, self.output_size_y - 2*margin))
        ratio = self.unfolder.mesh.largest_island_ratio(output_inner_size)
        return ratio * sce.unit_settings.scale_length / self.scale

    def draw(self, context):
        layout = self.layout
        layout.prop(self.properties, "do_create_uvmap")
        layout.prop(self.properties, "scale", text="Scale: 1/")
        scale_ratio = self.get_scale_ratio(context.scene)
        if scale_ratio > 1:
            layout.label(
                text="An island is roughly {:.1f}x bigger than page".format(scale_ratio),
                icon="ERROR")
        elif scale_ratio > 0:
            layout.label(text="Largest island is roughly 1/{:.1f} of page".format(1 / scale_ratio))

        if context.scene.unit_settings.scale_length != 1:
            layout.label(
                text="Unit scale {:.1f} makes page size etc. not display correctly".format(
                    context.scene.unit_settings.scale_length), icon="ERROR")
        box = layout.box()
        row = box.row(align=True)
        row.prop(
            self.properties, "ui_expanded_document", text="",
            icon=('TRIA_DOWN' if self.ui_expanded_document else 'TRIA_RIGHT'), emboss=False)
        row.label(text="Document Settings")

        if self.ui_expanded_document:
            box.prop(self.properties, "file_format", text="Format")
            box.prop(self.properties, "page_size_preset")
            col = box.column(align=True)
            col.active = self.page_size_preset == 'USER'
            col.prop(self.properties, "output_size_x")
            col.prop(self.properties, "output_size_y")
            box.prop(self.properties, "output_margin")
            col = box.column()
            col.prop(self.properties, "do_create_stickers")
            col.prop(self.properties, "do_create_numbers")
            col = box.column()
            col.active = self.do_create_stickers or self.do_create_numbers
            col.prop(self.properties, "sticker_width")
            box.prop(self.properties, "angle_epsilon")

            box.prop(self.properties, "output_type")
            col = box.column()
            col.active = (self.output_type != 'NONE')
            if len(self.object.data.uv_layers) >= 8:
                col.label(text="No UV slots left, No Texture is the only option.", icon='ERROR')
            elif context.scene.render.engine != 'CYCLES' and self.output_type != 'NONE':
                col.label(text="Cycles will be used for texture baking.", icon='ERROR')
            row = col.row()
            row.active = self.output_type in ('AMBIENT_OCCLUSION', 'RENDER', 'SELECTED_TO_ACTIVE')
            row.prop(self.properties, "bake_samples")
            col.prop(self.properties, "output_dpi")
            row = col.row()
            row.active = self.file_format == 'SVG'
            row.prop(self.properties, "image_packing", text="Images")

        box = layout.box()
        row = box.row(align=True)
        row.prop(
            self.properties, "ui_expanded_style", text="",
            icon=('TRIA_DOWN' if self.ui_expanded_style else 'TRIA_RIGHT'), emboss=False)
        row.label(text="Colors and Style")

        if self.ui_expanded_style:
            box.prop(self.style, "line_width", text="Default line width")
            col = box.column()
            col.prop(self.style, "outer_color")
            col.prop(self.style, "outer_width", text="Relative width")
            col.prop(self.style, "outer_style", text="Style")
            col = box.column()
            col.active = self.output_type != 'NONE'
            col.prop(self.style, "use_outbg", text="Outer Lines Highlight:")
            sub = col.column()
            sub.active = self.output_type != 'NONE' and self.style.use_outbg
            sub.prop(self.style, "outbg_color", text="")
            sub.prop(self.style, "outbg_width", text="Relative width")
            col = box.column()
            col.prop(self.style, "convex_color")
            col.prop(self.style, "convex_width", text="Relative width")
            col.prop(self.style, "convex_style", text="Style")
            col = box.column()
            col.prop(self.style, "concave_color")
            col.prop(self.style, "concave_width", text="Relative width")
            col.prop(self.style, "concave_style", text="Style")
            col = box.column()
            col.prop(self.style, "freestyle_color")
            col.prop(self.style, "freestyle_width", text="Relative width")
            col.prop(self.style, "freestyle_style", text="Style")
            col = box.column()
            col.active = self.output_type != 'NONE'
            col.prop(self.style, "use_inbg", text="Inner Lines Highlight:")
            sub = col.column()
            sub.active = self.output_type != 'NONE' and self.style.use_inbg
            sub.prop(self.style, "inbg_color", text="")
            sub.prop(self.style, "inbg_width", text="Relative width")
            col = box.column()
            col.active = self.do_create_stickers
            col.prop(self.style, "sticker_color")
            box.prop(self.style, "text_color")


def menu_func_export(self, context):
    self.layout.operator("export_mesh.paper_model", text="Paper Model (.pdf/.svg)")


def menu_func_unfold(self, context):
    self.layout.operator("mesh.unfold", text="Unfold")


class SelectIsland(bpy.types.Operator):
    """Blender Operator: select all faces of the active island"""

    bl_idname = "mesh.select_paper_island"
    bl_label = "Select Island"
    bl_description = "Select an island of the paper model net"

    operation: bpy.props.EnumProperty(
        name="Operation", description="Operation with the current selection",
        default='ADD', items=[
            ('ADD', "Add", "Add to current selection"),
            ('REMOVE', "Remove", "Remove from selection"),
            ('REPLACE', "Replace", "Select only the ")
        ])

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        ob = context.active_object
        me = ob.data
        bm = bmesh.from_edit_mesh(me)
        island = me.paper_island_list[me.paper_island_index]
        faces = {face.id for face in island.faces}
        edges = set()
        verts = set()
        if self.operation == 'REPLACE':
            for face in bm.faces:
                selected = face.index in faces
                face.select = selected
                if selected:
                    edges.update(face.edges)
                    verts.update(face.verts)
            for edge in bm.edges:
                edge.select = edge in edges
            for vert in bm.verts:
                vert.select = vert in verts
        else:
            selected = (self.operation == 'ADD')
            for index in faces:
                face = bm.faces[index]
                face.select = selected
                edges.update(face.edges)
                verts.update(face.verts)
            for edge in edges:
                edge.select = any(face.select for face in edge.link_faces)
            for vert in verts:
                vert.select = any(edge.select for edge in vert.link_edges)
        bmesh.update_edit_mesh(me, loop_triangles=False, destructive=False)
        return {'FINISHED'}


class VIEW3D_PT_paper_model_tools(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Paper'
    bl_label = "Unfold"

    def draw(self, context):
        layout = self.layout
        sce = context.scene
        obj = context.active_object
        mesh = obj.data if obj and obj.type == 'MESH' else None

        layout.operator("mesh.unfold")

        if context.mode == 'EDIT_MESH':
            row = layout.row(align=True)
            row.operator("mesh.mark_seam", text="Mark Seam").clear = False
            row.operator("mesh.mark_seam", text="Clear Seam").clear = True
        else:
            layout.operator("mesh.clear_all_seams")


class VIEW3D_PT_paper_model_settings(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Paper'
    bl_label = "Export"

    def draw(self, context):
        layout = self.layout
        sce = context.scene
        obj = context.active_object
        mesh = obj.data if obj and obj.type == 'MESH' else None

        layout.operator("export_mesh.paper_model")
        props = sce.paper_model
        layout.prop(props, "use_auto_scale")
        sub = layout.row()
        sub.active = not props.use_auto_scale
        sub.prop(props, "scale", text="Model Scale:  1/")

        layout.prop(props, "limit_by_page")
        col = layout.column()
        col.active = props.limit_by_page
        col.prop(props, "page_size_preset")
        sub = col.column(align=True)
        sub.active = props.page_size_preset == 'USER'
        sub.prop(props, "output_size_x")
        sub.prop(props, "output_size_y")


class DATA_PT_paper_model_islands(bpy.types.Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_label = "Paper Model Islands"
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}

    def draw(self, context):
        layout = self.layout
        sce = context.scene
        obj = context.active_object
        mesh = obj.data if obj and obj.type == 'MESH' else None

        layout.operator("mesh.unfold", icon='FILE_REFRESH')
        if mesh and mesh.paper_island_list:
            layout.label(
                text="1 island:" if len(mesh.paper_island_list) == 1 else
                "{} islands:".format(len(mesh.paper_island_list)))
            layout.template_list(
                'UI_UL_list', 'paper_model_island_list', mesh,
                'paper_island_list', mesh, 'paper_island_index', rows=1, maxrows=5)
            sub = layout.split(align=True)
            sub.operator("mesh.select_paper_island", text="Select").operation = 'ADD'
            sub.operator("mesh.select_paper_island", text="Deselect").operation = 'REMOVE'
            sub.prop(sce.paper_model, "sync_island", icon='UV_SYNC_SELECT', toggle=True)
            if mesh.paper_island_index >= 0:
                list_item = mesh.paper_island_list[mesh.paper_island_index]
                sub = layout.column(align=True)
                sub.prop(list_item, "auto_label")
                sub.prop(list_item, "label")
                sub.prop(list_item, "auto_abbrev")
                row = sub.row()
                row.active = not list_item.auto_abbrev
                row.prop(list_item, "abbreviation")
        else:
            layout.box().label(text="Not unfolded")


def label_changed(self, context):
    """The label of an island was changed"""
    # accessing properties via [..] to avoid a recursive call after the update
    self["auto_label"] = not self.label or self.label.isspace()
    island_item_changed(self, context)


def island_item_changed(self, context):
    """The labelling of an island was changed"""
    def increment(abbrev, collisions):
        letters = "ABCDEFGHIJKLMNPQRSTUVWXYZ123456789"
        while abbrev in collisions:
            abbrev = abbrev.rstrip(letters[-1])
            abbrev = abbrev[:2] + letters[letters.find(abbrev[-1]) + 1 if len(abbrev) == 3 else 0]
        return abbrev

    # accessing properties via [..] to avoid a recursive call after the update
    island_list = context.active_object.data.paper_island_list
    if self.auto_label:
        self["label"] = ""  # avoid self-conflict
        number = 1
        while any(item.label == "Island {}".format(number) for item in island_list):
            number += 1
        self["label"] = "Island {}".format(number)
    if self.auto_abbrev:
        self["abbreviation"] = ""  # avoid self-conflict
        abbrev = "".join(first_letters(self.label))[:3].upper()
        self["abbreviation"] = increment(abbrev, {item.abbreviation for item in island_list})
    elif len(self.abbreviation) > 3:
        self["abbreviation"] = self.abbreviation[:3]
    self.name = "[{}] {} ({} {})".format(
        self.abbreviation, self.label, len(self.faces), "faces" if len(self.faces) > 1 else "face")


def island_index_changed(self, context):
    """The active island was changed"""
    if context.scene.paper_model.sync_island and SelectIsland.poll(context):
        bpy.ops.mesh.select_paper_island(operation='REPLACE')


class FaceList(bpy.types.PropertyGroup):
    id: bpy.props.IntProperty(name="Face ID")


class IslandList(bpy.types.PropertyGroup):
    faces: bpy.props.CollectionProperty(
        name="Faces", description="Faces belonging to this island", type=FaceList)
    label: bpy.props.StringProperty(
        name="Label", description="Label on this island",
        default="", update=label_changed)
    abbreviation: bpy.props.StringProperty(
        name="Abbreviation", description="Three-letter label to use when there is not enough space",
        default="", update=island_item_changed)
    auto_label: bpy.props.BoolProperty(
        name="Auto Label", description="Generate the label automatically",
        default=True, update=island_item_changed)
    auto_abbrev: bpy.props.BoolProperty(
        name="Auto Abbreviation", description="Generate the abbreviation automatically",
        default=True, update=island_item_changed)


class PaperModelSettings(bpy.types.PropertyGroup):
    sync_island: bpy.props.BoolProperty(
        name="Sync", description="Keep faces of the active island selected",
        default=False, update=island_index_changed)
    limit_by_page: bpy.props.BoolProperty(
        name="Limit Island Size", description="Do not create islands larger than given dimensions",
        default=False, update=page_size_preset_changed)
    page_size_preset: bpy.props.EnumProperty(
        name="Page Size", description="Maximal size of an island",
        default='A4', update=page_size_preset_changed, items=global_paper_sizes)
    output_size_x: bpy.props.FloatProperty(
        name="Width", description="Maximal width of an island",
        default=0.2, soft_min=0.105, soft_max=0.841, subtype="UNSIGNED", unit="LENGTH")
    output_size_y: bpy.props.FloatProperty(
        name="Height", description="Maximal height of an island",
        default=0.29, soft_min=0.148, soft_max=1.189, subtype="UNSIGNED", unit="LENGTH")
    use_auto_scale: bpy.props.BoolProperty(
        name="Automatic Scale", description="Scale the net automatically to fit on paper",
        default=True)
    scale: bpy.props.FloatProperty(
        name="Scale", description="Divisor of all dimensions when exporting",
        default=1, soft_min=1.0, soft_max=100.0, subtype='FACTOR', precision=1,
        update=lambda settings, _: settings.__setattr__('use_auto_scale', False))


def factory_update_addon_category(cls, prop):
    def func(self, context):
        if hasattr(bpy.types, cls.__name__):
            bpy.utils.unregister_class(cls)
        cls.bl_category = self[prop]
        bpy.utils.register_class(cls)
    return func


class PaperAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    unfold_category: bpy.props.StringProperty(
        name="Unfold Panel Category", description="Category in 3D View Toolbox where the Unfold panel is displayed",
        default="Paper", update=factory_update_addon_category(VIEW3D_PT_paper_model_tools, 'unfold_category'))
    export_category: bpy.props.StringProperty(
        name="Export Panel Category", description="Category in 3D View Toolbox where the Export panel is displayed",
        default="Paper", update=factory_update_addon_category(VIEW3D_PT_paper_model_settings, 'export_category'))

    def draw(self, context):
        sub = self.layout.column(align=True)
        sub.use_property_split = True
        sub.label(text="3D View Panel Category:")
        sub.prop(self, "unfold_category", text="Unfold Panel:")
        sub.prop(self, "export_category", text="Export Panel:")


module_classes = (
    Unfold,
    ExportPaperModel,
    ClearAllSeams,
    SelectIsland,
    FaceList,
    IslandList,
    PaperModelSettings,
    DATA_PT_paper_model_islands,
    VIEW3D_PT_paper_model_tools,
    VIEW3D_PT_paper_model_settings,
    PaperAddonPreferences,
)


def register():
    for cls in module_classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.paper_model = bpy.props.PointerProperty(
        name="Paper Model", description="Settings of the Export Paper Model script",
        type=PaperModelSettings, options={'SKIP_SAVE'})
    bpy.types.Mesh.paper_island_list = bpy.props.CollectionProperty(
        name="Island List", type=IslandList)
    bpy.types.Mesh.paper_island_index = bpy.props.IntProperty(
        name="Island List Index",
        default=-1, min=-1, max=100, options={'SKIP_SAVE'}, update=island_index_changed)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.VIEW3D_MT_edit_mesh.prepend(menu_func_unfold)
    # Force an update on the panel category properties
    prefs = bpy.context.preferences.addons[__name__].preferences
    prefs.unfold_category = prefs.unfold_category
    prefs.export_category = prefs.export_category


def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.VIEW3D_MT_edit_mesh.remove(menu_func_unfold)
    for cls in reversed(module_classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
