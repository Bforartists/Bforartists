### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####

#python tip: from-imports don't save memory.
#They execute and cache the entire module just like a regular import.

import bpy
import bmesh
from .snap_context_l import SnapContext
from mathutils import Vector
from mathutils.geometry import (
        intersect_point_line,
        intersect_line_line,
        intersect_line_plane,
        intersect_ray_tri,
        )


def get_units_info(scale, unit_system, separate_units):
    if unit_system == 'METRIC':
        scale_steps = ((1000, 'km'), (1, 'm'), (1 / 100, 'cm'),
            (1 / 1000, 'mm'), (1 / 1000000, '\u00b5m'))
    elif unit_system == 'IMPERIAL':
        scale_steps = ((5280, 'mi'), (1, '\''),
            (1 / 12, '"'), (1 / 12000, 'thou'))
        scale /= 0.3048  # BU to feet
    else:
        scale_steps = ((1, ' BU'),)
        separate_units = False

    return (scale, scale_steps, separate_units)


def convert_distance(val, units_info, precision=5):
    scale, scale_steps, separate_units = units_info
    sval = val * scale
    idx = 0
    while idx < len(scale_steps) - 1:
        if sval >= scale_steps[idx][0]:
            break
        idx += 1
    factor, suffix = scale_steps[idx]
    sval /= factor
    if not separate_units or idx == len(scale_steps) - 1:
        dval = str(round(sval, precision)) + suffix
    else:
        ival = int(sval)
        dval = str(round(ival, precision)) + suffix
        fval = sval - ival
        idx += 1
        while idx < len(scale_steps):
            fval *= scale_steps[idx - 1][0] / scale_steps[idx][0]
            if fval >= 1:
                dval += ' ' \
                    + ("%.1f" % fval) \
                    + scale_steps[idx][1]
                break
            idx += 1

    return dval


def location_3d_to_region_2d(region, rv3d, coord):
    prj = rv3d.perspective_matrix @ Vector((coord[0], coord[1], coord[2], 1.0))
    width_half = region.width / 2.0
    height_half = region.height / 2.0
    return Vector((width_half + width_half * (prj.x / prj.w),
                   height_half + height_half * (prj.y / prj.w),
                   prj.z / prj.w
                   ))


def out_Location(rv3d, orig, vector):
    view_matrix = rv3d.view_matrix
    v1 = (int(view_matrix[0][0]*1.5), int(view_matrix[0][1]*1.5), int(view_matrix[0][2]*1.5))
    v2 = (int(view_matrix[1][0]*1.5), int(view_matrix[1][1]*1.5), int(view_matrix[1][2]*1.5))

    hit = intersect_ray_tri((1,0,0), (0,1,0), (0,0,0), (vector), (orig), False)
    if hit is None:
        hit = intersect_ray_tri(v1, v2, (0,0,0), (vector), (orig), False)
    if hit is None:
        hit = intersect_ray_tri(v1, v2, (0,0,0), (-vector), (orig), False)
    if hit is None:
        hit = Vector()
    return hit


def get_snap_bm_geom(sctx, main_snap_obj, mcursor):

    r_snp_obj, r_loc, r_elem, r_elem_co = sctx.snap_get(mcursor, main_snap_obj)
    r_view_vector, r_orig = sctx.last_ray
    r_bm = None
    r_bm_geom = None

    if r_snp_obj is not None:
        obj = r_snp_obj.data[0]

        if obj.type == 'MESH' and obj.data.is_editmode:
            r_bm = bmesh.from_edit_mesh(obj.data)
            if len(r_elem) == 1:
                r_bm_geom = r_bm.verts[r_elem[0]]

            elif len(r_elem) == 2:
                try:
                    v1 = r_bm.verts[r_elem[0]]
                    v2 = r_bm.verts[r_elem[1]]
                    r_bm_geom = r_bm.edges.get([v1, v2])
                except IndexError:
                    r_bm.verts.ensure_lookup_table()

            elif len(r_elem) == 3:
                tri = [
                    r_bm.verts[r_elem[0]],
                    r_bm.verts[r_elem[1]],
                    r_bm.verts[r_elem[2]],
                ]

                faces = set(tri[0].link_faces).intersection(tri[1].link_faces, tri[2].link_faces)
                if len(faces) == 1:
                    r_bm_geom = faces.pop()
                else:
                    i = -2
                    edge = None
                    while not edge and i != 1:
                        edge = r_bm.edges.get([tri[i], tri[i + 1]])
                        i += 1
                    if edge:
                        for l in edge.link_loops:
                            if l.link_loop_next.vert == tri[i] or l.link_loop_prev.vert == tri[i - 2]:
                                r_bm_geom = l.face
                                break

    return r_snp_obj, r_loc, r_elem, r_elem_co, r_view_vector, r_orig, r_bm, r_bm_geom


class SnapCache:
    snp_obj = None
    elem = None

    v0 = None
    v1 = None
    vmid = None
    vperp = None

    v2d0 = None
    v2d1 = None
    v2dmid = None
    v2dperp = None

    is_increment = False


def snap_utilities(
        sctx, main_snap_obj,
        mcursor,
        constrain = None,
        previous_vert = None,
        increment = 0.0):

    snp_obj, loc, elem, elem_co, view_vector, orig, bm, bm_geom = get_snap_bm_geom(sctx, main_snap_obj, mcursor)

    is_increment = False
    r_loc = None
    r_type = None
    r_len = 0.0

    if not snp_obj:
        is_increment = True
        if constrain:
            end = orig + view_vector
            t_loc = intersect_line_line(constrain[0], constrain[1], orig, end)
            if t_loc is None:
                t_loc = constrain
            r_loc = t_loc[0]
        else:
            r_type = 'OUT'
            r_loc = out_Location(sctx.rv3d, orig, view_vector)

    elif len(elem) == 1:
        r_type = 'VERT'
        if constrain:
            r_loc = intersect_point_line(loc, constrain[0], constrain[1])[0]
        else:
            r_loc = loc

    elif len(elem) == 2:
        if SnapCache.snp_obj is not snp_obj or not (elem == SnapCache.elem).all():
            SnapCache.snp_obj = snp_obj
            SnapCache.elem = elem

            SnapCache.v0 = elem_co[0]
            SnapCache.v1 = elem_co[1]
            SnapCache.vmid = 0.5 * (SnapCache.v0 + SnapCache.v1)
            SnapCache.v2d0 = location_3d_to_region_2d(sctx.region, sctx.rv3d, SnapCache.v0)
            SnapCache.v2d1 = location_3d_to_region_2d(sctx.region, sctx.rv3d, SnapCache.v1)
            SnapCache.v2dmid = location_3d_to_region_2d(sctx.region, sctx.rv3d, SnapCache.vmid)

            if previous_vert and (not bm_geom or previous_vert not in bm_geom.verts):
                pvert_co = main_snap_obj.mat @ previous_vert.co
                perp_point = intersect_point_line(pvert_co, SnapCache.v0, SnapCache.v1)
                SnapCache.vperp = perp_point[0]
                #factor = point_perpendicular[1]
                SnapCache.v2dperp = location_3d_to_region_2d(sctx.region, sctx.rv3d, perp_point[0])
                SnapCache.is_increment = False
            else:
                SnapCache.is_increment = True

            #else: SnapCache.v2dperp = None

        if constrain:
            t_loc = intersect_line_line(constrain[0], constrain[1], SnapCache.v0, SnapCache.v1)

            if t_loc is None:
                is_increment = True
                end = orig + view_vector
                t_loc = intersect_line_line(constrain[0], constrain[1], orig, end)
            r_loc = t_loc[0]

        elif SnapCache.v2dperp and\
            abs(SnapCache.v2dperp[0] - mcursor[0]) < 10 and abs(SnapCache.v2dperp[1] - mcursor[1]) < 10:
                r_type = 'PERPENDICULAR'
                r_loc = SnapCache.vperp

        elif abs(SnapCache.v2dmid[0] - mcursor[0]) < 10 and abs(SnapCache.v2dmid[1] - mcursor[1]) < 10:
            r_type = 'CENTER'
            r_loc = SnapCache.vmid

        else:
            is_increment = SnapCache.is_increment

            r_type = 'EDGE'
            r_loc = loc

    elif len(elem) == 3:
        r_type = 'FACE'

        if constrain:
            is_increment = False
            r_loc = intersect_point_line(loc, constrain[0], constrain[1])[0]
        else:
            is_increment = True
            r_loc = loc

    if previous_vert:
        pv_co = main_snap_obj.mat @ previous_vert.co
        vec = r_loc - pv_co
        if is_increment and increment:
            r_len = round((1 / increment) * vec.length) * increment
            r_loc = r_len * vec.normalized() + pv_co
        else:
            r_len = vec.length

    return snp_obj, loc, r_loc, r_type, bm, bm_geom, r_len

snap_utilities.cache = SnapCache
