# <pep8-80 compliant>

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "5.1"
__date__ = "24 Feb 2018"

from collections import defaultdict
from pprint import pprint
from math import fabs, sqrt

import bpy
from mathutils import Vector
import bmesh


DEBUG = False


def debug_print(*s):
    """
    Print message to console in debugging mode
    """

    if DEBUG:
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
            break
    for space in area.spaces:
        if space.type == space_type:
            break

    return (area, region, space)


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

    if face_idx in faces_left:
        faces_left.remove(face_idx)
        island.append({'face': bm.faces[face_idx]})
        for v in face_to_verts[face_idx]:
            connected_faces = vert_to_faces[v]
            if connected_faces:
                for cf in connected_faces:
                    __parse_island(bm, cf, faces_left, island, face_to_verts,
                                   vert_to_faces)


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


def calc_polygon_2d_area(points):
    area = 0.0
    for i, p1 in enumerate(points):
        p2 = points[(i + 1) % len(points)]
        v1 = p1 - points[0]
        v2 = p2 - points[0]
        a = v1.x * v2.y - v1.y * v2.x
        area = area + a

    return fabs(0.5 * area)


def calc_polygon_3d_area(points):
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


def measure_mesh_area(obj):
    bm = bmesh.from_edit_mesh(obj.data)
    if check_version(2, 73, 0) >= 0:
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

    sel_faces = [f for f in bm.faces if f.select]

    # measure
    mesh_area = 0.0
    for f in sel_faces:
        verts = [l.vert.co for l in f.loops]
        f_mesh_area = calc_polygon_3d_area(verts)
        mesh_area = mesh_area + f_mesh_area

    return mesh_area


def measure_uv_area(obj):
    bm = bmesh.from_edit_mesh(obj.data)
    if check_version(2, 73, 0) >= 0:
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

    if not bm.loops.layers.uv:
        return None
    uv_layer = bm.loops.layers.uv.verify()

    if not bm.faces.layers.tex:
        return None
    tex_layer = bm.faces.layers.tex.verify()

    sel_faces = [f for f in bm.faces if f.select]

    # measure
    uv_area = 0.0
    for f in sel_faces:
        uvs = [l[uv_layer].uv for l in f.loops]
        f_uv_area = calc_polygon_2d_area(uvs)

        if not tex_layer:
            return None
        img = f[tex_layer].image
        # not found, try to search from node
        if not img:
            for mat in obj.material_slots:
                for node in mat.material.node_tree.nodes:
                    tex_node_types = [
                        'TEX_ENVIRONMENT',
                        'TEX_IMAGE',
                    ]
                    if (node.type in tex_node_types) and node.image:
                        img = node.image
        if not img:
            return None
        uv_area = uv_area + f_uv_area * img.size[0] * img.size[1]

    return uv_area


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

    def __get_loop_pairs_internal(l_, pairs_, uv_layer_, parsed_):
        parsed_.append(l_)
        for ll in l_.vert.link_loops:
            # forward direction
            lln = ll.link_loop_next
            # if there is same pair, skip it
            found = False
            for p in pairs_:
                if (ll in p) and (lln in p):
                    found = True
                    break
            # two loops must be selected
            if ll[uv_layer_].select and lln[uv_layer_].select:
                if not found:
                    pairs_.append([ll, lln])
                if lln not in parsed_:
                    __get_loop_pairs_internal(lln, pairs_, uv_layer_, parsed_)

            # backward direction
            llp = ll.link_loop_prev
            # if there is same pair, skip it
            found = False
            for p in pairs_:
                if (ll in p) and (llp in p):
                    found = True
                    break
            # two loops must be selected
            if ll[uv_layer_].select and llp[uv_layer_].select:
                if not found:
                    pairs_.append([ll, llp])
                if llp not in parsed_:
                    __get_loop_pairs_internal(llp, pairs_, uv_layer_, parsed_)

    pairs = []
    parsed = []
    __get_loop_pairs_internal(l, pairs, uv_layer, parsed)

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
            return None, "All UVs are not separted"

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
            # sequence of the verticies
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
