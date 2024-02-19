# SPDX-FileCopyrightText: 2017-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

from mathutils import Vector
from mathutils.geometry import intersect_point_line


def depth_get(co, ray_start, ray_dir):
    dvec = co - ray_start
    return dvec.dot(ray_dir)


def region_2d_to_orig_and_view_vector(region, rv3d, coord):
    viewinv = rv3d.view_matrix.inverted_safe()
    persinv = rv3d.perspective_matrix.inverted_safe()

    dx = (2.0 * coord[0] / region.width) - 1.0
    dy = (2.0 * coord[1] / region.height) - 1.0

    if rv3d.is_perspective:
        origin_start = viewinv.translation.copy()

        out = Vector((dx, dy, -0.5))

        w = out.dot(persinv[3].xyz) + persinv[3][3]

        view_vector = ((persinv @ out) / w) - origin_start
    else:
        view_vector = -viewinv.col[2].xyz

        origin_start = ((persinv.col[0].xyz * dx) +
                        (persinv.col[1].xyz * dy) +
                        viewinv.translation)

    view_vector.normalize()
    return view_vector, origin_start


def project_co_v3(sctx, co):
    proj_co = sctx.proj_mat @ co.to_4d()
    try:
        proj_co.xy /= proj_co.w
    except Exception as e:
        print(e)

    win_half = sctx.winsize * 0.5
    proj_co[0] = (proj_co[0] + 1.0) * win_half[0]
    proj_co[1] = (proj_co[1] + 1.0) * win_half[1]

    return proj_co.xy


def intersect_boundbox_threshold(sctx, MVP, ray_origin_local, ray_direction_local, bbmin, bbmax):
    local_bvmin = Vector()
    local_bvmax = Vector()
    tmin = Vector()
    tmax = Vector()

    if (ray_direction_local[0] < 0.0):
        local_bvmin[0] = bbmax[0]
        local_bvmax[0] = bbmin[0]
    else:
        local_bvmin[0] = bbmin[0]
        local_bvmax[0] = bbmax[0]

    if (ray_direction_local[1] < 0.0):
        local_bvmin[1] = bbmax[1]
        local_bvmax[1] = bbmin[1]
    else:
        local_bvmin[1] = bbmin[1]
        local_bvmax[1] = bbmax[1]

    if (ray_direction_local[2] < 0.0):
        local_bvmin[2] = bbmax[2]
        local_bvmax[2] = bbmin[2]
    else:
        local_bvmin[2] = bbmin[2]
        local_bvmax[2] = bbmax[2]

    if (ray_direction_local[0]):
        tmin[0] = (local_bvmin[0] - ray_origin_local[0]) / ray_direction_local[0]
        tmax[0] = (local_bvmax[0] - ray_origin_local[0]) / ray_direction_local[0]
    else:
        tmin[0] = sctx.depth_range[0]
        tmax[0] = sctx.depth_range[1]

    if (ray_direction_local[1]):
        tmin[1] = (local_bvmin[1] - ray_origin_local[1]) / ray_direction_local[1]
        tmax[1] = (local_bvmax[1] - ray_origin_local[1]) / ray_direction_local[1]
    else:
        tmin[1] = sctx.depth_range[0]
        tmax[1] = sctx.depth_range[1]

    if (ray_direction_local[2]):
        tmin[2] = (local_bvmin[2] - ray_origin_local[2]) / ray_direction_local[2]
        tmax[2] = (local_bvmax[2] - ray_origin_local[2]) / ray_direction_local[2]
    else:
        tmin[2] = sctx.depth_range[0]
        tmax[2] = sctx.depth_range[1]

    # `va` and `vb` are the coordinates of the AABB edge closest to the ray #
    va = Vector()
    vb = Vector()
    # `rtmin` and `rtmax` are the minimum and maximum distances of the ray hits on the AABB #

    if ((tmax[0] <= tmax[1]) and (tmax[0] <= tmax[2])):
        rtmax = tmax[0]
        va[0] = vb[0] = local_bvmax[0]
        main_axis = 3
    elif ((tmax[1] <= tmax[0]) and (tmax[1] <= tmax[2])):
        rtmax = tmax[1]
        va[1] = vb[1] = local_bvmax[1]
        main_axis = 2
    else:
        rtmax = tmax[2]
        va[2] = vb[2] = local_bvmax[2]
        main_axis = 1

    if ((tmin[0] >= tmin[1]) and (tmin[0] >= tmin[2])):
        rtmin = tmin[0]
        va[0] = vb[0] = local_bvmin[0]
        main_axis -= 3
    elif ((tmin[1] >= tmin[0]) and (tmin[1] >= tmin[2])):
        rtmin = tmin[1]
        va[1] = vb[1] = local_bvmin[1]
        main_axis -= 1
    else:
        rtmin = tmin[2]
        va[2] = vb[2] = local_bvmin[2]
        main_axis -= 2

    if (main_axis < 0):
        main_axis += 3

# ifdef IGNORE_BEHIND_RAY
    depth_max = depth_get(local_bvmax, ray_origin_local, ray_direction_local)
    if (depth_max < sctx.depth_range[0]):
        return False
# endif

    if (rtmin <= rtmax):
        # if rtmin < rtmax, ray intersect `AABB` #
        return True

    if (ray_direction_local[main_axis] < 0.0):
        va[main_axis] = local_bvmax[main_axis]
        vb[main_axis] = local_bvmin[main_axis]

    else:
        va[main_axis] = local_bvmin[main_axis]
        vb[main_axis] = local_bvmax[main_axis]

    win_half = sctx.winsize * 0.5

    scale = abs(local_bvmax[main_axis] - local_bvmin[main_axis])

    va2d = Vector((
        (MVP[0].xyz.dot(va) + MVP[0][3]),
        (MVP[1].xyz.dot(va) + MVP[1][3]),
    ))

    vb2d = Vector((
        (va2d[0] + MVP[0][main_axis] * scale),
        (va2d[1] + MVP[1][main_axis] * scale),
    ))

    depth_a = MVP[3].xyz.dot(va) + MVP[3][3]
    depth_b = depth_a + MVP[3][main_axis] * scale

    va2d /= depth_a
    vb2d /= depth_b

    va2d[0] = (va2d[0] + 1.0) * win_half[0]
    va2d[1] = (va2d[1] + 1.0) * win_half[1]
    vb2d[0] = (vb2d[0] + 1.0) * win_half[0]
    vb2d[1] = (vb2d[1] + 1.0) * win_half[1]

    p, fac = intersect_point_line(sctx.mval, va2d, vb2d)
    if fac < 0.0:
        return (sctx.mval - va2d).length_squared < sctx._dist_px_sq
    elif fac > 1.0:
        return (sctx.mval - vb2d).length_squared < sctx._dist_px_sq
    else:
        return (sctx.mval - p).length_squared < sctx._dist_px_sq


def intersect_ray_ray_fac(orig_a, dir_a, orig_b, dir_b):
    t = orig_a - orig_b
    n = dir_a.cross(dir_b)
    nlen = n.length_squared

    # if (nlen == 0.0f) the lines are parallel, has no nearest point, only distance squared.*/
    if nlen == 0.0:
        # Calculate the distance to the nearest point to origin then #
        return intersect_point_line(orig_a, orig_b, orig_b + dir_b)
    else:
        c = n - t
        cray = c.cross(dir_b)
        return cray.dot(n) / nlen


def intersect_ray_segment_fac(v0, v1, ray_direction, ray_origin):
    dir_a = v1 - v0
    return intersect_ray_ray_fac(v0, dir_a, ray_origin, ray_direction)
