# SPDX-FileCopyrightText: 2018-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"

from collections import defaultdict
from pprint import pprint
from math import fabs, sqrt
import os

import bpy
from mathutils import Vector
import bmesh

from .utils import compatibility as compat
from .utils.graph import Graph, Node


__DEBUG_MODE = False


def is_console_mode():
    if "MUV_CONSOLE_MODE" not in os.environ:
        return False
    return os.environ["MUV_CONSOLE_MODE"] == "true"


def is_valid_space(context, allowed_spaces):
    for area in context.screen.areas:
        for space in area.spaces:
            if space.type in allowed_spaces:
                return True
    return False


def is_debug_mode():
    return __DEBUG_MODE


def enable_debugg_mode():
    # pylint: disable=W0603
    global __DEBUG_MODE
    __DEBUG_MODE = True


def disable_debug_mode():
    # pylint: disable=W0603
    global __DEBUG_MODE
    __DEBUG_MODE = False


def debug_print(*s):
    """
    Print message to console in debugging mode
    """

    if is_debug_mode():
        pprint(s)


def check_version(major, minor, _):
    """
    Check blender version
    """

    if bpy.app.version[0] == major and bpy.app.version[1] == minor:
        return 0
    if bpy.app.version[0] > major:
        return 1
    if bpy.app.version[1] > minor:
        return 1
    return -1


def redraw_all_areas():
    """
    Redraw all areas
    """

    for area in bpy.context.screen.areas:
        area.tag_redraw()


def get_space(area_type, region_type, space_type):
    """
    Get current area/region/space
    """

    area = None
    region = None
    space = None

    for area in bpy.context.screen.areas:
        if area.type == area_type:
            break
    else:
        return (None, None, None)
    for region in area.regions:
        if region.type == region_type:
            if compat.check_version(2, 80, 0) >= 0:
                if region.width <= 1 or region.height <= 1:
                    continue
            break
    else:
        return (area, None, None)
    for space in area.spaces:
        if space.type == space_type:
            break
    else:
        return (area, region, None)

    return (area, region, space)


def mouse_on_region(event, area_type, region_type):
    pos = Vector((event.mouse_x, event.mouse_y))

    _, region, _ = get_space(area_type, region_type, "")
    if region is None:
        return False

    if (pos.x > region.x) and (pos.x < region.x + region.width) and \
       (pos.y > region.y) and (pos.y < region.y + region.height):
        return True

    return False


def mouse_on_area(event, area_type):
    pos = Vector((event.mouse_x, event.mouse_y))

    area, _, _ = get_space(area_type, "", "")
    if area is None:
        return False

    if (pos.x > area.x) and (pos.x < area.x + area.width) and \
       (pos.y > area.y) and (pos.y < area.y + area.height):
        return True

    return False


def mouse_on_regions(event, area_type, regions):
    if not mouse_on_area(event, area_type):
        return False

    for region in regions:
        result = mouse_on_region(event, area_type, region)
        if result:
            return True

    return False


def create_bmesh(obj):
    bm = bmesh.from_edit_mesh(obj.data)
    if check_version(2, 73, 0) >= 0:
        bm.faces.ensure_lookup_table()

    return bm


def create_new_uv_map(obj, name=None):
    uv_maps_old = {l.name for l in obj.data.uv_layers}
    bpy.ops.mesh.uv_texture_add()
    uv_maps_new = {l.name for l in obj.data.uv_layers}
    diff = uv_maps_new - uv_maps_old

    if not list(diff):
        return None     # no more UV maps can not be created

    # rename UV map
    new = obj.data.uv_layers[list(diff)[0]]
    if name:
        new.name = name

    return new


def __get_island_info(uv_layer, islands):
    """
    get information about each island
    """

    island_info = []
    for isl in islands:
        info = {}
        max_uv = Vector((-10000000.0, -10000000.0))
        min_uv = Vector((10000000.0, 10000000.0))
        ave_uv = Vector((0.0, 0.0))
        num_uv = 0
        for face in isl:
            n = 0
            a = Vector((0.0, 0.0))
            ma = Vector((-10000000.0, -10000000.0))
            mi = Vector((10000000.0, 10000000.0))
            for l in face['face'].loops:
                uv = l[uv_layer].uv
                ma.x = max(uv.x, ma.x)
                ma.y = max(uv.y, ma.y)
                mi.x = min(uv.x, mi.x)
                mi.y = min(uv.y, mi.y)
                a = a + uv
                n = n + 1
            ave_uv = ave_uv + a
            num_uv = num_uv + n
            a = a / n
            max_uv.x = max(ma.x, max_uv.x)
            max_uv.y = max(ma.y, max_uv.y)
            min_uv.x = min(mi.x, min_uv.x)
            min_uv.y = min(mi.y, min_uv.y)
            face['max_uv'] = ma
            face['min_uv'] = mi
            face['ave_uv'] = a
        ave_uv = ave_uv / num_uv

        info['center'] = ave_uv
        info['size'] = max_uv - min_uv
        info['num_uv'] = num_uv
        info['group'] = -1
        info['faces'] = isl
        info['max'] = max_uv
        info['min'] = min_uv

        island_info.append(info)

    return island_info


def __parse_island(bm, face_idx, faces_left, island,
                   face_to_verts, vert_to_faces):
    """
    Parse island
    """

    faces_to_parse = [face_idx]
    while faces_to_parse:
        fidx = faces_to_parse.pop(0)
        if fidx in faces_left:
            faces_left.remove(fidx)
            island.append({'face': bm.faces[fidx]})
            for v in face_to_verts[fidx]:
                connected_faces = vert_to_faces[v]
                for cf in connected_faces:
                    faces_to_parse.append(cf)


def __get_island(bm, face_to_verts, vert_to_faces):
    """
    Get island list
    """

    uv_island_lists = []
    faces_left = set(face_to_verts.keys())
    while faces_left:
        current_island = []
        face_idx = list(faces_left)[0]
        __parse_island(bm, face_idx, faces_left, current_island,
                       face_to_verts, vert_to_faces)
        uv_island_lists.append(current_island)

    return uv_island_lists


def __create_vert_face_db(faces, uv_layer):
    # create mesh database for all faces
    face_to_verts = defaultdict(set)
    vert_to_faces = defaultdict(set)
    for f in faces:
        for l in f.loops:
            id_ = l[uv_layer].uv.to_tuple(5), l.vert.index
            face_to_verts[f.index].add(id_)
            vert_to_faces[id_].add(f.index)

    return (face_to_verts, vert_to_faces)


def get_island_info(obj, only_selected=True):
    bm = bmesh.from_edit_mesh(obj.data)
    if check_version(2, 73, 0) >= 0:
        bm.faces.ensure_lookup_table()

    return get_island_info_from_bmesh(bm, only_selected)


# Return island info.
#
# Format:
#
# [
#   {
#     faces: [
#       {
#         face: BMFace
#         max_uv: Vector (2D)
#         min_uv: Vector (2D)
#         ave_uv: Vector (2D)
#       },
#       ...
#     ]
#     center: Vector (2D)
#     size: Vector (2D)
#     num_uv: int
#     group: int
#     max: Vector (2D)
#     min: Vector (2D)
#   },
#   ...
# ]
def get_island_info_from_bmesh(bm, only_selected=True):
    if not bm.loops.layers.uv:
        return None
    uv_layer = bm.loops.layers.uv.verify()

    # create database
    if only_selected:
        selected_faces = [f for f in bm.faces if f.select]
    else:
        selected_faces = [f for f in bm.faces]

    return get_island_info_from_faces(bm, selected_faces, uv_layer)


def get_island_info_from_faces(bm, faces, uv_layer):
    ftv, vtf = __create_vert_face_db(faces, uv_layer)

    # Get island information
    uv_island_lists = __get_island(bm, ftv, vtf)
    island_info = __get_island_info(uv_layer, uv_island_lists)

    return island_info


def get_uvimg_editor_board_size(area):
    if area.spaces.active.image:
        return area.spaces.active.image.size

    return (255.0, 255.0)


def calc_tris_2d_area(points):
    area = 0.0
    for i, p1 in enumerate(points):
        p2 = points[(i + 1) % len(points)]
        v1 = p1 - points[0]
        v2 = p2 - points[0]
        a = v1.x * v2.y - v1.y * v2.x
        area = area + a

    return fabs(0.5 * area)


def calc_tris_3d_area(points):
    area = 0.0
    for i, p1 in enumerate(points):
        p2 = points[(i + 1) % len(points)]
        v1 = p1 - points[0]
        v2 = p2 - points[0]
        cx = v1.y * v2.z - v1.z * v2.y
        cy = v1.z * v2.x - v1.x * v2.z
        cz = v1.x * v2.y - v1.y * v2.x
        a = sqrt(cx * cx + cy * cy + cz * cz)
        area = area + a

    return 0.5 * area


def get_faces_list(bm, method, only_selected):
    faces_list = []
    if method == 'MESH':
        if only_selected:
            faces_list.append([f for f in bm.faces if f.select])
        else:
            faces_list.append([f for f in bm.faces])
    elif method == 'UV ISLAND':
        if not bm.loops.layers.uv:
            return None
        uv_layer = bm.loops.layers.uv.verify()
        if only_selected:
            faces = [f for f in bm.faces if f.select]
            islands = get_island_info_from_faces(bm, faces, uv_layer)
            for isl in islands:
                faces_list.append([f["face"] for f in isl["faces"]])
        else:
            faces = [f for f in bm.faces]
            islands = get_island_info_from_faces(bm, faces, uv_layer)
            for isl in islands:
                faces_list.append([f["face"] for f in isl["faces"]])
    elif method == 'FACE':
        if only_selected:
            for f in bm.faces:
                if f.select:
                    faces_list.append([f])
        else:
            for f in bm.faces:
                faces_list.append([f])
    else:
        raise ValueError("Invalid method: {}".format(method))

    return faces_list


def measure_all_faces_mesh_area(bm):
    if compat.check_version(2, 80, 0) >= 0:
        triangle_loops = bm.calc_loop_triangles()
    else:
        triangle_loops = bm.calc_tessface()

    areas = {face: 0.0 for face in bm.faces}

    for loops in triangle_loops:
        face = loops[0].face
        area = areas[face]
        area += calc_tris_3d_area([l.vert.co for l in loops])
        areas[face] = area

    return areas


def measure_mesh_area(obj, calc_method, only_selected):
    bm = bmesh.from_edit_mesh(obj.data)
    if check_version(2, 73, 0) >= 0:
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

    faces_list = get_faces_list(bm, calc_method, only_selected)

    areas = []
    for faces in faces_list:
        areas.append(measure_mesh_area_from_faces(bm, faces))

    return areas


def measure_mesh_area_from_faces(bm, faces):
    face_areas = measure_all_faces_mesh_area(bm)

    mesh_area = 0.0
    for f in faces:
        if f in face_areas:
            mesh_area += face_areas[f]

    return mesh_area


def find_texture_layer(bm):
    if check_version(2, 80, 0) >= 0:
        return None
    if bm.faces.layers.tex is None:
        return None

    return bm.faces.layers.tex.verify()


def find_texture_nodes_from_material(mtrl):
    nodes = []
    if not mtrl.node_tree:
        return nodes
    for node in mtrl.node_tree.nodes:
        tex_node_types = [
            'TEX_ENVIRONMENT',
            'TEX_IMAGE',
        ]
        if node.type not in tex_node_types:
            continue
        if not node.image:
            continue
        nodes.append(node)

    return nodes


def find_texture_nodes(obj):
    nodes = []
    for slot in obj.material_slots:
        if not slot.material:
            continue
        nodes.extend(find_texture_nodes_from_material(slot.material))

    return nodes


def find_image(obj, face=None, tex_layer=None):
    images = find_images(obj, face, tex_layer)

    if len(images) >= 2:
        raise RuntimeError("Find more than 2 images")
    if not images:
        return None

    return images[0]


def find_images(obj, face=None, tex_layer=None):
    images = []

    # try to find from texture_layer
    if tex_layer and face:
        if face[tex_layer].image is not None:
            images.append(face[tex_layer].image)

    # not found, then try to search from node
    if not images:
        nodes = find_texture_nodes(obj)
        for n in nodes:
            images.append(n.image)

    return images


def measure_all_faces_uv_area(bm, uv_layer):
    if compat.check_version(2, 80, 0) >= 0:
        triangle_loops = bm.calc_loop_triangles()
    else:
        triangle_loops = bm.calc_tessface()

    areas = {face: 0.0 for face in bm.faces}

    for loops in triangle_loops:
        face = loops[0].face
        area = areas[face]
        area += calc_tris_2d_area([l[uv_layer].uv for l in loops])
        areas[face] = area

    return areas


def measure_uv_area_from_faces(obj, bm, faces, uv_layer, tex_layer,
                               tex_selection_method, tex_size):

    face_areas = measure_all_faces_uv_area(bm, uv_layer)

    uv_area = 0.0
    for f in faces:
        if f not in face_areas:
            continue

        f_uv_area = face_areas[f]

        # user specified
        if tex_selection_method == 'USER_SPECIFIED' and tex_size is not None:
            img_size = tex_size
        # first texture if there are more than 2 textures assigned
        # to the object
        elif tex_selection_method == 'FIRST':
            img = find_image(obj, f, tex_layer)
            # can not find from node, so we can not get texture size
            if not img:
                return None
            img_size = img.size
        # average texture size
        elif tex_selection_method == 'AVERAGE':
            imgs = find_images(obj, f, tex_layer)
            if not imgs:
                return None

            img_size_total = [0.0, 0.0]
            for img in imgs:
                img_size_total = [img_size_total[0] + img.size[0],
                                  img_size_total[1] + img.size[1]]
            img_size = [img_size_total[0] / len(imgs),
                        img_size_total[1] / len(imgs)]
        # max texture size
        elif tex_selection_method == 'MAX':
            imgs = find_images(obj, f, tex_layer)
            if not imgs:
                return None

            img_size_max = [-99999999.0, -99999999.0]
            for img in imgs:
                img_size_max = [max(img_size_max[0], img.size[0]),
                                max(img_size_max[1], img.size[1])]
            img_size = img_size_max
        # min texture size
        elif tex_selection_method == 'MIN':
            imgs = find_images(obj, f, tex_layer)
            if not imgs:
                return None

            img_size_min = [99999999.0, 99999999.0]
            for img in imgs:
                img_size_min = [min(img_size_min[0], img.size[0]),
                                min(img_size_min[1], img.size[1])]
            img_size = img_size_min
        else:
            raise RuntimeError("Unexpected method: {}"
                               .format(tex_selection_method))

        uv_area += f_uv_area * img_size[0] * img_size[1]

    return uv_area


def measure_uv_area(obj, calc_method, tex_selection_method,
                    tex_size, only_selected):
    bm = bmesh.from_edit_mesh(obj.data)
    if check_version(2, 73, 0) >= 0:
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

    if not bm.loops.layers.uv:
        return None
    uv_layer = bm.loops.layers.uv.verify()
    tex_layer = find_texture_layer(bm)
    faces_list = get_faces_list(bm, calc_method, only_selected)

    # measure
    uv_areas = []
    for faces in faces_list:
        uv_area = measure_uv_area_from_faces(
            obj, bm, faces, uv_layer, tex_layer,
            tex_selection_method, tex_size)
        if uv_area is None:
            return None
        uv_areas.append(uv_area)

    return uv_areas


def diff_point_to_segment(a, b, p):
    ab = b - a
    normal_ab = ab.normalized()

    ap = p - a
    dist_ax = normal_ab.dot(ap)

    # cross point
    x = a + normal_ab * dist_ax

    # difference between cross point and point
    xp = p - x

    return xp, x


# get selected loop pair whose loops are connected each other
def __get_loop_pairs(l, uv_layer):
    pairs = []
    parsed = []
    loops_ready = [l]
    while loops_ready:
        l = loops_ready.pop(0)
        parsed.append(l)
        for ll in l.vert.link_loops:
            # forward direction
            lln = ll.link_loop_next
            # if there is same pair, skip it
            found = False
            for p in pairs:
                if (ll in p) and (lln in p):
                    found = True
                    break
            # two loops must be selected
            if ll[uv_layer].select and lln[uv_layer].select:
                if not found:
                    pairs.append([ll, lln])
                if (lln not in parsed) and (lln not in loops_ready):
                    loops_ready.append(lln)

            # backward direction
            llp = ll.link_loop_prev
            # if there is same pair, skip it
            found = False
            for p in pairs:
                if (ll in p) and (llp in p):
                    found = True
                    break
            # two loops must be selected
            if ll[uv_layer].select and llp[uv_layer].select:
                if not found:
                    pairs.append([ll, llp])
                if (llp not in parsed) and (llp not in loops_ready):
                    loops_ready.append(llp)

    return pairs


# sort pair by vertex
# (v0, v1) - (v1, v2) - (v2, v3) ....
def __sort_loop_pairs(uv_layer, pairs, closed):
    rest = pairs
    sorted_pairs = [rest[0]]
    rest.remove(rest[0])

    # prepend
    while True:
        p1 = sorted_pairs[0]
        for p2 in rest:
            if p1[0].vert == p2[0].vert:
                sorted_pairs.insert(0, [p2[1], p2[0]])
                rest.remove(p2)
                break
            elif p1[0].vert == p2[1].vert:
                sorted_pairs.insert(0, [p2[0], p2[1]])
                rest.remove(p2)
                break
        else:
            break

    # append
    while True:
        p1 = sorted_pairs[-1]
        for p2 in rest:
            if p1[1].vert == p2[0].vert:
                sorted_pairs.append([p2[0], p2[1]])
                rest.remove(p2)
                break
            elif p1[1].vert == p2[1].vert:
                sorted_pairs.append([p2[1], p2[0]])
                rest.remove(p2)
                break
        else:
            break

    begin_vert = sorted_pairs[0][0].vert
    end_vert = sorted_pairs[-1][-1].vert
    if begin_vert != end_vert:
        return sorted_pairs, ""
    if closed and (begin_vert == end_vert):
        # if the sequence of UV is circular, it is ok
        return sorted_pairs, ""

    # if the begin vertex and the end vertex are same, search the UVs which
    # are separated each other
    tmp_pairs = sorted_pairs
    for i, (p1, p2) in enumerate(zip(tmp_pairs[:-1], tmp_pairs[1:])):
        diff = p2[0][uv_layer].uv - p1[-1][uv_layer].uv
        if diff.length > 0.000000001:
            # UVs are separated
            sorted_pairs = tmp_pairs[i + 1:]
            sorted_pairs.extend(tmp_pairs[:i + 1])
            break
    else:
        p1 = tmp_pairs[0]
        p2 = tmp_pairs[-1]
        diff = p2[-1][uv_layer].uv - p1[0][uv_layer].uv
        if diff.length < 0.000000001:
            # all UVs are not separated
            return None, "All UVs are not separated"

    return sorted_pairs, ""


# get index of the island group which includes loop
def __get_island_group_include_loop(loop, island_info):
    for i, isl in enumerate(island_info):
        for f in isl['faces']:
            for l in f['face'].loops:
                if l == loop:
                    return i    # found

    return -1   # not found


# get index of the island group which includes pair.
# if island group is not same between loops, it will be invalid
def __get_island_group_include_pair(pair, island_info):
    l1_grp = __get_island_group_include_loop(pair[0], island_info)
    if l1_grp == -1:
        return -1   # not found

    for p in pair[1:]:
        l2_grp = __get_island_group_include_loop(p, island_info)
        if (l2_grp == -1) or (l1_grp != l2_grp):
            return -1   # not found or invalid

    return l1_grp


# x ---- x   <- next_loop_pair
# |      |
# o ---- o   <- pair
def __get_next_loop_pair(pair):
    lp = pair[0].link_loop_prev
    if lp.vert == pair[1].vert:
        lp = pair[0].link_loop_next
        if lp.vert == pair[1].vert:
            # no loop is found
            return None

    ln = pair[1].link_loop_next
    if ln.vert == pair[0].vert:
        ln = pair[1].link_loop_prev
        if ln.vert == pair[0].vert:
            # no loop is found
            return None

    # tri-face
    if lp == ln:
        return [lp]

    # quad-face
    return [lp, ln]


# | ---- |
# % ---- %   <- next_poly_loop_pair
# x ---- x   <- next_loop_pair
# |      |
# o ---- o   <- pair
def __get_next_poly_loop_pair(pair):
    v1 = pair[0].vert
    v2 = pair[1].vert
    for l1 in v1.link_loops:
        if l1 == pair[0]:
            continue
        for l2 in v2.link_loops:
            if l2 == pair[1]:
                continue
            if l1.link_loop_next == l2:
                return [l1, l2]
            elif l1.link_loop_prev == l2:
                return [l1, l2]

    # no next poly loop is found
    return None


# get loop sequence in the same island
def __get_loop_sequence_internal(uv_layer, pairs, island_info, closed):
    loop_sequences = []
    for pair in pairs:
        seqs = [pair]
        p = pair
        isl_grp = __get_island_group_include_pair(pair, island_info)
        if isl_grp == -1:
            return None, "Can not find the island or invalid island"

        while True:
            nlp = __get_next_loop_pair(p)
            if not nlp:
                break       # no more loop pair
            nlp_isl_grp = __get_island_group_include_pair(nlp, island_info)
            if nlp_isl_grp != isl_grp:
                break       # another island
            for nlpl in nlp:
                if nlpl[uv_layer].select:
                    return None, "Do not select UV which does not belong to " \
                                 "the end edge"

            seqs.append(nlp)

            # when face is triangle, it indicates CLOSED
            if (len(nlp) == 1) and closed:
                break

            nplp = __get_next_poly_loop_pair(nlp)
            if not nplp:
                break       # no more loop pair
            nplp_isl_grp = __get_island_group_include_pair(nplp, island_info)
            if nplp_isl_grp != isl_grp:
                break       # another island

            # check if the UVs are already parsed.
            # this check is needed for the mesh which has the circular
            # sequence of the vertices
            matched = False
            for p1 in seqs:
                p2 = nplp
                if ((p1[0] == p2[0]) and (p1[1] == p2[1])) or \
                   ((p1[0] == p2[1]) and (p1[1] == p2[0])):
                    matched = True
            if matched:
                debug_print("This is a circular sequence")
                break

            for nlpl in nplp:
                if nlpl[uv_layer].select:
                    return None, "Do not select UV which does not belong to " \
                                 "the end edge"

            seqs.append(nplp)

            p = nplp

        loop_sequences.append(seqs)
    return loop_sequences, ""


def get_loop_sequences(bm, uv_layer, closed=False):
    sel_faces = [f for f in bm.faces if f.select]

    # get candidate loops
    cand_loops = []
    for f in sel_faces:
        for l in f.loops:
            if l[uv_layer].select:
                cand_loops.append(l)

    if len(cand_loops) < 2:
        return None, "More than 2 UVs must be selected"

    first_loop = cand_loops[0]
    isl_info = get_island_info_from_bmesh(bm, False)
    loop_pairs = __get_loop_pairs(first_loop, uv_layer)
    loop_pairs, err = __sort_loop_pairs(uv_layer, loop_pairs, closed)
    if not loop_pairs:
        return None, err
    loop_seqs, err = __get_loop_sequence_internal(uv_layer, loop_pairs,
                                                  isl_info, closed)
    if not loop_seqs:
        return None, err

    return loop_seqs, ""


def __is_segment_intersect(start1, end1, start2, end2):
    seg1 = end1 - start1
    seg2 = end2 - start2

    a1 = -seg1.y
    b1 = seg1.x
    d1 = -(a1 * start1.x + b1 * start1.y)

    a2 = -seg2.y
    b2 = seg2.x
    d2 = -(a2 * start2.x + b2 * start2.y)

    seg1_line2_start = a2 * start1.x + b2 * start1.y + d2
    seg1_line2_end = a2 * end1.x + b2 * end1.y + d2

    seg2_line1_start = a1 * start2.x + b1 * start2.y + d1
    seg2_line1_end = a1 * end2.x + b1 * end2.y + d1

    if (seg1_line2_start * seg1_line2_end >= 0) or \
            (seg2_line1_start * seg2_line1_end >= 0):
        return False, None

    u = seg1_line2_start / (seg1_line2_start - seg1_line2_end)
    out = start1 + u * seg1

    return True, out


class RingBuffer:
    def __init__(self, arr):
        self.__buffer = arr.copy()
        self.__pointer = 0

    def __repr__(self):
        return repr(self.__buffer)

    def __len__(self):
        return len(self.__buffer)

    def insert(self, val, offset=0):
        self.__buffer.insert(self.__pointer + offset, val)

    def head(self):
        return self.__buffer[0]

    def tail(self):
        return self.__buffer[-1]

    def get(self, offset=0):
        size = len(self.__buffer)
        val = self.__buffer[(self.__pointer + offset) % size]
        return val

    def next(self):
        size = len(self.__buffer)
        self.__pointer = (self.__pointer + 1) % size

    def reset(self):
        self.__pointer = 0

    def find(self, obj):
        try:
            idx = self.__buffer.index(obj)
        except ValueError:
            return None
        return self.__buffer[idx]

    def find_and_next(self, obj):
        size = len(self.__buffer)
        idx = self.__buffer.index(obj)
        self.__pointer = (idx + 1) % size

    def find_and_set(self, obj):
        idx = self.__buffer.index(obj)
        self.__pointer = idx

    def as_list(self):
        return self.__buffer.copy()

    def reverse(self):
        self.__buffer.reverse()
        self.reset()


# clip: reference polygon
# subject: tested polygon
def __do_weiler_atherton_cliping(clip_uvs, subject_uvs, mode,
                                 same_polygon_threshold):

    clip_uvs = RingBuffer(clip_uvs)
    if __is_polygon_flipped(clip_uvs):
        clip_uvs.reverse()
    subject_uvs = RingBuffer(subject_uvs)
    if __is_polygon_flipped(subject_uvs):
        subject_uvs.reverse()

    debug_print("===== Clip UV List =====")
    debug_print(clip_uvs)
    debug_print("===== Subject UV List =====")
    debug_print(subject_uvs)

    # check if clip and subject is overlapped completely
    if __is_polygon_same(clip_uvs, subject_uvs, same_polygon_threshold):
        polygons = [subject_uvs.as_list()]
        debug_print("===== Polygons Overlapped Completely =====")
        debug_print(polygons)
        return True, polygons

    # check if subject is in clip
    if __is_points_in_polygon(subject_uvs, clip_uvs):
        polygons = [subject_uvs.as_list()]
        return True, polygons

    # check if clip is in subject
    if __is_points_in_polygon(clip_uvs, subject_uvs):
        polygons = [subject_uvs.as_list()]
        return True, polygons

    # check if clip and subject is overlapped partially
    intersections = []
    while True:
        subject_uvs.reset()
        while True:
            uv_start1 = clip_uvs.get()
            uv_end1 = clip_uvs.get(1)
            uv_start2 = subject_uvs.get()
            uv_end2 = subject_uvs.get(1)
            intersected, point = __is_segment_intersect(uv_start1, uv_end1,
                                                        uv_start2, uv_end2)
            if intersected:
                clip_uvs.insert(point, 1)
                subject_uvs.insert(point, 1)
                intersections.append([point,
                                      [clip_uvs.get(), clip_uvs.get(1)]])
            subject_uvs.next()
            if subject_uvs.get() == subject_uvs.head():
                break
        clip_uvs.next()
        if clip_uvs.get() == clip_uvs.head():
            break

    debug_print("===== Intersection List =====")
    debug_print(intersections)

    # no intersection, so subject and clip is not overlapped
    if not intersections:
        return False, None

    def get_intersection_pair(intersects, key):
        for sect in intersects:
            if sect[0] == key:
                return sect[1]

        return None

    # make enter/exit pair
    subject_uvs.reset()
    subject_entering = []
    subject_exiting = []
    clip_entering = []
    clip_exiting = []
    intersect_uv_list = []
    while True:
        pair = get_intersection_pair(intersections, subject_uvs.get())
        if pair:
            sub = subject_uvs.get(1) - subject_uvs.get(-1)
            inter = pair[1] - pair[0]
            cross = sub.x * inter.y - inter.x * sub.y
            if cross < 0:
                subject_entering.append(subject_uvs.get())
                clip_exiting.append(subject_uvs.get())
            else:
                subject_exiting.append(subject_uvs.get())
                clip_entering.append(subject_uvs.get())
            intersect_uv_list.append(subject_uvs.get())

        subject_uvs.next()
        if subject_uvs.get() == subject_uvs.head():
            break

    debug_print("===== Enter List =====")
    debug_print(clip_entering)
    debug_print(subject_entering)
    debug_print("===== Exit List =====")
    debug_print(clip_exiting)
    debug_print(subject_exiting)

    # for now, can't handle the situation when fulfill all below conditions
    #        * two faces have common edge
    #        * each face is intersected
    #        * Show Mode is "Part"
    #       so for now, ignore this situation
    if len(subject_entering) != len(subject_exiting):
        if mode == 'FACE':
            polygons = [subject_uvs.as_list()]
            return True, polygons
        return False, None

    def traverse(current_list, entering, exiting, p, current, other_list):
        result = current_list.find(current)
        if not result:
            return None
        if result != current:
            print("Internal Error")
            return None
        if not exiting:
            print("Internal Error: No exiting UV")
            return None

        # enter
        if entering.count(current) >= 1:
            entering.remove(current)

        current_list.find_and_next(current)
        current = current_list.get()

        prev = None
        error = False
        while exiting.count(current) == 0:
            p.append(current.copy())
            current_list.find_and_next(current)
            current = current_list.get()
            if prev == current:
                error = True
                break
            prev = current

        if error:
            print("Internal Error: Infinite loop")
            return None

        # exit
        p.append(current.copy())
        exiting.remove(current)

        other_list.find_and_set(current)
        return other_list.get()

    # Traverse
    polygons = []
    current_uv_list = subject_uvs
    other_uv_list = clip_uvs
    current_entering = subject_entering
    current_exiting = subject_exiting

    poly = []
    current_uv = current_entering[0]

    while True:
        current_uv = traverse(current_uv_list, current_entering,
                              current_exiting, poly, current_uv, other_uv_list)

        if current_uv is None:
            break

        if current_uv_list == subject_uvs:
            current_uv_list = clip_uvs
            other_uv_list = subject_uvs
            current_entering = clip_entering
            current_exiting = clip_exiting
            debug_print("-- Next: Clip --")
        else:
            current_uv_list = subject_uvs
            other_uv_list = clip_uvs
            current_entering = subject_entering
            current_exiting = subject_exiting
            debug_print("-- Next: Subject --")

        debug_print(clip_entering)
        debug_print(clip_exiting)
        debug_print(subject_entering)
        debug_print(subject_exiting)

        if not clip_entering and not clip_exiting \
                and not subject_entering and not subject_exiting:
            break

    polygons.append(poly)

    debug_print("===== Polygons Overlapped Partially =====")
    debug_print(polygons)

    return True, polygons


def __is_polygon_flipped(points):
    area = 0.0
    for i in range(len(points)):
        uv1 = points.get(i)
        uv2 = points.get(i + 1)
        a = uv1.x * uv2.y - uv1.y * uv2.x
        area = area + a
    if area < 0:
        # clock-wise
        return True
    return False


def __is_point_in_polygon(point, subject_points):
    """Return true when point is inside of the polygon by using
    'Crossing number algorithm'.
    """

    count = 0
    for i in range(len(subject_points)):
        uv_start1 = subject_points.get(i)
        uv_end1 = subject_points.get(i + 1)
        uv_start2 = point
        uv_end2 = Vector((1000000.0, point.y))

        # If the point exactly matches to the point of the polygon,
        # this point is not in polygon.
        if uv_start1.x == uv_start2.x and uv_start1.y == uv_start2.y:
            return False

        intersected, _ = __is_segment_intersect(uv_start1, uv_end1,
                                                uv_start2, uv_end2)
        if intersected:
            count = count + 1

    return count % 2


def __is_points_in_polygon(points, subject_points):
    for i in range(len(points)):
        internal = __is_point_in_polygon(points.get(i), subject_points)
        if not internal:
            return False

    return True


def get_uv_editable_objects(context):
    if compat.check_version(2, 80, 0) < 0:
        objs = []
    else:
        objs = [o for o in bpy.data.objects
                if compat.get_object_select(o) and o.type == 'MESH']

    ob = context.active_object
    if ob is not None:
        objs.append(ob)

    objs = list(set(objs))
    return objs


def get_overlapped_uv_info(bm_list, faces_list, uv_layer_list,
                           mode, same_polygon_threshold=0.0000001):
    # at first, check island overlapped
    isl = []
    for bm, uv_layer, faces in zip(bm_list, uv_layer_list, faces_list):
        info = get_island_info_from_faces(bm, faces, uv_layer)
        isl.extend([(i, uv_layer, bm) for i in info])

    overlapped_isl_pairs = []
    overlapped_uv_layer_pairs = []
    overlapped_bm_paris = []
    for i, (i1, uv_layer_1, bm_1) in enumerate(isl):
        for i2, uv_layer_2, bm_2 in isl[i + 1:]:
            if (i1["max"].x < i2["min"].x) or (i2["max"].x < i1["min"].x) or \
               (i1["max"].y < i2["min"].y) or (i2["max"].y < i1["min"].y):
                continue
            overlapped_isl_pairs.append([i1, i2])
            overlapped_uv_layer_pairs.append([uv_layer_1, uv_layer_2])
            overlapped_bm_paris.append([bm_1, bm_2])

    # check polygon overlapped (inter UV islands)
    overlapped_uvs = []
    for oip, uvlp, bmp in zip(overlapped_isl_pairs,
                              overlapped_uv_layer_pairs,
                              overlapped_bm_paris):
        for clip in oip[0]["faces"]:
            f_clip = clip["face"]
            clip_uvs = [l[uvlp[0]].uv.copy() for l in f_clip.loops]
            for subject in oip[1]["faces"]:
                f_subject = subject["face"]

                # fast operation, apply bounding box algorithm
                if (clip["max_uv"].x < subject["min_uv"].x) or \
                   (subject["max_uv"].x < clip["min_uv"].x) or \
                   (clip["max_uv"].y < subject["min_uv"].y) or \
                   (subject["max_uv"].y < clip["min_uv"].y):
                    continue

                subject_uvs = [l[uvlp[1]].uv.copy() for l in f_subject.loops]
                # slow operation, apply Weiler-Atherton cliping algorithm
                result, polygons = \
                    __do_weiler_atherton_cliping(clip_uvs, subject_uvs,
                                                 mode, same_polygon_threshold)
                if result:
                    overlapped_uvs.append({"clip_bmesh": bmp[0],
                                           "subject_bmesh": bmp[1],
                                           "clip_face": f_clip,
                                           "subject_face": f_subject,
                                           "clip_uv_layer": uvlp[0],
                                           "subject_uv_layer": uvlp[1],
                                           "subject_uvs": subject_uvs,
                                           "polygons": polygons})

    # check polygon overlapped (intra UV island)
    for info, uv_layer, bm in isl:
        for i in range(len(info["faces"])):
            clip = info["faces"][i]
            f_clip = clip["face"]
            clip_uvs = [l[uv_layer].uv.copy() for l in f_clip.loops]
            for j in range(len(info["faces"])):
                if j <= i:
                    continue

                subject = info["faces"][j]
                f_subject = subject["face"]

                # fast operation, apply bounding box algorithm
                if (clip["max_uv"].x < subject["min_uv"].x) or \
                   (subject["max_uv"].x < clip["min_uv"].x) or \
                   (clip["max_uv"].y < subject["min_uv"].y) or \
                   (subject["max_uv"].y < clip["min_uv"].y):
                    continue

                subject_uvs = [l[uv_layer].uv.copy() for l in f_subject.loops]
                # slow operation, apply Weiler-Atherton cliping algorithm
                result, polygons = \
                    __do_weiler_atherton_cliping(clip_uvs, subject_uvs,
                                                 mode, same_polygon_threshold)
                if result:
                    overlapped_uvs.append({"clip_bmesh": bm,
                                           "subject_bmesh": bm,
                                           "clip_face": f_clip,
                                           "subject_face": f_subject,
                                           "clip_uv_layer": uv_layer,
                                           "subject_uv_layer": uv_layer,
                                           "subject_uvs": subject_uvs,
                                           "polygons": polygons})

    return overlapped_uvs


def get_flipped_uv_info(bm_list, faces_list, uv_layer_list):
    flipped_uvs = []
    for bm, faces, uv_layer in zip(bm_list, faces_list, uv_layer_list):
        for f in faces:
            polygon = RingBuffer([l[uv_layer].uv.copy() for l in f.loops])
            if __is_polygon_flipped(polygon):
                uvs = [l[uv_layer].uv.copy() for l in f.loops]
                flipped_uvs.append({"bmesh": bm,
                                    "face": f,
                                    "uv_layer": uv_layer,
                                    "uvs": uvs,
                                    "polygons": [polygon.as_list()]})

    return flipped_uvs


def __is_polygon_same(points1, points2, threshold):
    if len(points1) != len(points2):
        return False

    pts1 = points1.as_list()
    pts2 = points2.as_list()

    for p1 in pts1:
        for p2 in pts2:
            diff = p2 - p1
            if diff.length < threshold:
                pts2.remove(p2)
                break
        else:
            return False

    return True


def _is_uv_loop_connected(l1, l2, uv_layer):
    uv1 = l1[uv_layer].uv
    uv2 = l2[uv_layer].uv
    return uv1.x == uv2.x and uv1.y == uv2.y


def create_uv_graph(loops, uv_layer):
    # For looking up faster.
    loop_index_to_loop = {}     # { loop index: loop }
    for l in loops:
        loop_index_to_loop[l.index] = l

    # Setup relationship between uv_vert and loops.
    # uv_vert is a representative of the loops which shares same
    # UV coordinate.
    uv_vert_to_loops = {}   # { uv_vert: loops belonged to uv_vert }
    loop_to_uv_vert = {}    # { loop: uv_vert belonged to }
    for l in loops:
        found = False
        for k in uv_vert_to_loops.keys():
            if _is_uv_loop_connected(k, l, uv_layer):
                uv_vert_to_loops[k].append(l)
                loop_to_uv_vert[l] = k
                found = True
                break
        if not found:
            uv_vert_to_loops[l] = [l]
            loop_to_uv_vert[l] = l

    # Collect adjacent uv_vert.
    uv_adj_verts = {}       # { uv_vert: adj uv_vert list }
    for v, vs in uv_vert_to_loops.items():
        uv_adj_verts[v] = []
        for ll in vs:
            ln = ll.link_loop_next
            lp = ll.link_loop_prev
            uv_adj_verts[v].append(loop_to_uv_vert[ln])
            uv_adj_verts[v].append(loop_to_uv_vert[lp])
        uv_adj_verts[v] = list(set(uv_adj_verts[v]))

    # Setup uv_vert graph.
    graph = Graph()
    for v in uv_adj_verts.keys():
        graph.add_node(
            Node(v.index, {"uv_vert": v, "loops": uv_vert_to_loops[v]})
        )
    edges = []
    for v, adjs in uv_adj_verts.items():
        n1 = graph.get_node(v.index)
        for a in adjs:
            n2 = graph.get_node(a.index)
            edges.append(tuple(sorted((n1.key, n2.key))))
    edges = list(set(edges))
    for e in edges:
        n1 = graph.get_node(e[0])
        n2 = graph.get_node(e[1])
        graph.add_edge(n1, n2)

    return graph
