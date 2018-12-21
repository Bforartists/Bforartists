
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

import bpy
import copy
import bgl
import blf
import mathutils
from mathutils import *
from math import *
#from math import sin, cos, tan, atan, degrees, radians, asin, acos
from bpy_extras import view3d_utils
from bpy.app.handlers import persistent

from .utils_function import *


def scene_cast(region, rv3d, co2d):

    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, co2d)
    #np_print('ray_origin', ray_origin)
    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, co2d)
    #np_print('view_vector', view_vector)
    ray_target = ray_origin + view_vector * 1000
    #np_print('ray_target', ray_target)
    if bpy.app.version[0] > 1 and  bpy.app.version[1] > 76:
        scenecast = bpy.context.scene.ray_cast(ray_origin, view_vector)
        #np_print('scenecast', scenecast)
        result = scenecast[0]
        hitloc = scenecast[1]
        normal = scenecast[2]
        face_index = scenecast[3]
        hitob = scenecast[4]
        matrix = scenecast[5]
    else:
        scenecast = bpy.context.scene.ray_cast(ray_origin, ray_target)
        #np_print('scenecast', scenecast)
        result = scenecast[0]
        hitloc = scenecast[3]
        normal = scenecast[4]
        hitob = scenecast[1]
        matrix = scenecast[2]
        if hitob is not None:
            matrix = hitob.matrix_world.copy()
            matrix_inv = matrix.inverted()
            ray_origin_obj = matrix_inv * ray_origin
            ray_target_obj = matrix_inv * ray_target
            obcast = hitob.ray_cast(ray_origin_obj, ray_target_obj)
            #np_print('obcast', obcast)
            face_index = obcast[2]
        else:
            face_index = -1

    return (result, hitloc, normal, face_index, hitob, matrix, ray_origin, view_vector, ray_target)


def construct_roto_widget(alpha_0, alpha_1, fac, r1, r2, angstep):
    if alpha_1 >= alpha_0: alpha = alpha_1 - alpha_0
    else: alpha = alpha_1 + (360 - alpha_0)
    ring_sides = abs(int(alpha / angstep)) + 1
    np_print('ring_sides', ring_sides)
    ring_angstep = alpha / ring_sides
    np_print('ring_sides, ring_angstep', ring_sides, ring_angstep)
    ring = []
    ang = alpha_0
    co1 = Vector((0.0, 0.0, 0.0))
    co1[0] = round(cos(radians(ang)), 8)
    co1[1] = round(sin(radians(ang)), 8)
    co1 = co1 * r1 * fac
    ring.append(co1)
    co2 = Vector((0.0, 0.0, 0.0))
    co2[0] = round(cos(radians(ang)), 8)
    co2[1] = round(sin(radians(ang)), 8)
    co2 = co2 * r2 * fac
    ring.append(co2)
    for i in range(2, (2 + ring_sides)):
        co = Vector((0.0, 0.0, 0.0))
        ang = ang + ring_angstep
        co[0] = round(cos(radians(ang)), 8)
        co[1] = round(sin(radians(ang)), 8)
        co = co * r2 * fac
        #np_print('co', co)
        #np_print('ring', ring)
        ring.append(co)
    np_print('one done')
    for i in range((2 + ring_sides) + 1, (2 + (2 * ring_sides)+2)):
        co = Vector((0.0, 0.0, 0.0))
        co[0] = round(cos(radians(ang)), 8)
        co[1] = round(sin(radians(ang)), 8)
        ang = ang - ring_angstep
        #np_print('co', co)
        #np_print('ring', ring)
        co = co * r1 * fac
        ring.append(co)
    np_print('two done')
    return ring


def construct_circle_2d(r, angstep):

    sides = int(360 / angstep) + 1
    angstep = 360 / sides
    circle = []
    ang = 0
    for i in range(0, sides):
        co = [0.0, 0.0]
        co[0] = round(cos(radians(ang)), 8)*r
        co[1] = round(sin(radians(ang)), 8)*r
        ang = ang + angstep
        circle.append(co)
    #np_print('circle', circle)
    return circle



def get_ro_x_from_iso(region, rv3d, co2d, centerloc):

    scenecast = scene_cast(region, rv3d, co2d)
    ray_origin = scenecast[6]
    view_vector = scenecast[7]
    ray_target = scenecast[8]
    n = scenecast[2]
    if n == Vector((0.0, 0.0, 0.0)):
        if ray_origin[2] > 0:
            if ray_target[2] < ray_origin[2]: n = Vector((0.0, 0.0, 1.0))
            else:
                if view_vector[1] > 0 and abs(view_vector[0]) <= view_vector[1]: n = Vector((0.0, -1.0, 0.0))
                elif view_vector[1] < 0 and abs(view_vector[0]) <= abs(view_vector[1]): n = Vector((0.0, 1.0, 0.0))
                elif view_vector[0] < 0 and abs(view_vector[1]) <= abs(view_vector[0]): n = Vector((1.0, 0.0, 0.0))
                elif view_vector[0] > 0 and abs(view_vector[1]) <= view_vector[0]: n = Vector((-1.0, 0.0, 0.0))
        if ray_origin[2] < 0:
            if ray_target[2] > ray_origin[2]: n = Vector((0.0, 0.0, 1.0))
            else:
                if view_vector[1] > 0 and abs(view_vector[0]) <= view_vector[1]: n = Vector((0.0, -1.0, 0.0))
                elif view_vector[1] < 0 and abs(view_vector[0]) <= abs(view_vector[1]): n = Vector((0.0, 1.0, 0.0))
                elif view_vector[0] < 0 and abs(view_vector[1]) <= abs(view_vector[0]): n = Vector((1.0, 0.0, 0.0))
                elif view_vector[0] > 0 and abs(view_vector[1]) <= view_vector[0]: n = Vector((-1.0, 0.0, 0.0))
        if ray_origin[2] == 0:
            if view_vector[1] > 0 and abs(view_vector[0]) <= view_vector[1]: n = Vector((0.0, -1.0, 0.0))
            elif view_vector[1] < 0 and abs(view_vector[0]) <= abs(view_vector[1]): n = Vector((0.0, 1.0, 0.0))
            elif view_vector[0] < 0 and abs(view_vector[1]) <= abs(view_vector[0]): n = Vector((1.0, 0.0, 0.0))
            elif view_vector[0] > 0 and abs(view_vector[1]) <= view_vector[0]: n = Vector((-1.0, 0.0, 0.0))
    isohipse = mathutils.geometry.intersect_plane_plane(centerloc, n, centerloc, Vector((0.0, 0.0, 1.0)))
    #np_print('n = ', n)
    #np_print('isohipse = ', isohipse)
    if isohipse == (None, None): viso = Vector((0.0, 0.0, 0.0)) + Vector((1.0, 0.0, 0.0))
    else: viso = Vector((0.0, 0.0, 0.0)) - isohipse[1]
    if isohipse == (None, None): isohipse = (centerloc, (centerloc + Vector((1.0, 0.0, 0.0))))
    else: isohipse = (isohipse[0], isohipse[0] - isohipse[1])
    viso = viso.normalized()

    v = Vector((1.0, 0.0, 0.0))
    ro_hor = v.rotation_difference(viso)
    if viso[0] == -1.0000:
        ro_hor = Quaternion ((0.0000, 0.0000, -0.0000, 1.000))
    #ro_hor_deg = degrees(ro_hor)
    #np_print('viso = ', viso)
    #np_print( viso[0], viso[1], viso[2])
    #np_print('ro_hor = ', ro_hor)
    #np_print('ro_hor_deg = ', ro_hor_deg)
    return (ro_hor, isohipse)

def get_ro_normal_from_vertical(region, rv3d, co2d):

    scenecast = scene_cast(region, rv3d, co2d)
    ray_origin = scenecast[6]
    view_vector = scenecast[7]
    ray_target = scenecast[8]
    hitloc = scenecast[1]
    n = scenecast[2]
    if n == Vector((0.0, 0.0, 0.0)):
        if ray_origin[2] > 0:
            if ray_target[2] < ray_origin[2]:
                n = Vector((0.0, 0.0, 1.0))
                if ray_origin[2] > 10: draw_plane_point = Vector((0.0, 0.0, (ray_origin[2] - 10)))
                else: draw_plane_point = Vector((0.0, 0.0, 0.0))
            else:
                if view_vector[1] > 0 and abs(view_vector[0]) <= view_vector[1]:
                    n = Vector((0.0, -1.0, 0.0))
                    if ray_origin[1] > 0 or ray_origin[1] < -10: draw_plane_point = Vector((0.0, (ray_origin[1] + 10), 0.0))
                    else: draw_plane_point = Vector((0.0, 0.0, 0.0))
                elif view_vector[1] < 0 and abs(view_vector[0]) <= abs(view_vector[1]):
                    n = Vector((0.0, 1.0, 0.0))
                    if ray_origin[1] < 0 or ray_origin[1] > 10: draw_plane_point = Vector((0.0, (ray_origin[1] - 10), 0.0))
                    else: draw_plane_point = Vector((0.0, 0.0, 0.0))
                elif view_vector[0] < 0 and abs(view_vector[1]) <= abs(view_vector[0]):
                    n = Vector((1.0, 0.0, 0.0))
                    if ray_origin[0] > 10 or ray_origin[0] < 0: draw_plane_point = Vector(((ray_origin[0] - 10), 0.0, 0.0))
                    else: draw_plane_point = Vector((0.0, 0.0, 0.0))
                elif view_vector[0] > 0 and abs(view_vector[1]) <= view_vector[0]:
                    n = Vector((-1.0, 0.0, 0.0))
                    if ray_origin[0] < -10 or ray_origin[0] > 0: draw_plane_point = Vector(((ray_origin[0] + 10), 0.0, 0.0))
                    else: draw_plane_point = Vector((0.0, 0.0, 0.0))
        if ray_origin[2] < 0:
            if ray_target[2] > ray_origin[2]:
                n = Vector((0.0, 0.0, -1.0))
                if ray_origin[2] < -10: draw_plane_point = Vector((0.0, 0.0, (ray_origin[2] + 10)))
                else: draw_plane_point = Vector((0.0, 0.0, 0.0))
            else:
                if view_vector[1] > 0 and abs(view_vector[0]) <= view_vector[1]:
                    n = Vector((0.0, -1.0, 0.0))
                    if ray_origin[1] > 0 or ray_origin[1] < -10: draw_plane_point = Vector((0.0, (ray_origin[1] + 10), 0.0))
                    else: draw_plane_point = Vector((0.0, 0.0, 0.0))
                elif view_vector[1] < 0 and abs(view_vector[0]) <= abs(view_vector[1]):
                    n = Vector((0.0, 1.0, 0.0))
                    if ray_origin[1] < 0 or ray_origin[1] > 10: draw_plane_point = Vector((0.0, (ray_origin[1] - 10), 0.0))
                    else: draw_plane_point = Vector((0.0, 0.0, 0.0))
                elif view_vector[0] < 0 and abs(view_vector[1]) <= abs(view_vector[0]):
                    n = Vector((1.0, 0.0, 0.0))
                    if ray_origin[0] > 10 or ray_origin[0] < 0: draw_plane_point = Vector(((ray_origin[0] - 10), 0.0, 0.0))
                    else: draw_plane_point = Vector((0.0, 0.0, 0.0))
                elif view_vector[0] > 0 and abs(view_vector[1]) <= view_vector[0]:
                    n = Vector((-1.0, 0.0, 0.0))
                    if ray_origin[0] < -10 or ray_origin[0] > 0: draw_plane_point = Vector(((ray_origin[0] + 10), 0.0, 0.0))
                    else: draw_plane_point = Vector((0.0, 0.0, 0.0))
        if ray_origin[2] == 0:
            if view_vector[1] > 0 and abs(view_vector[0]) <= view_vector[1]:
                n = Vector((0.0, -1.0, 0.0))
                if ray_origin[1] > 0 or ray_origin[1] < -10: draw_plane_point = Vector((0.0, (ray_origin[1] + 10), 0.0))
                else: draw_plane_point = Vector((0.0, 0.0, 0.0))
            elif view_vector[1] < 0 and abs(view_vector[0]) <= abs(view_vector[1]):
                n = Vector((0.0, 1.0, 0.0))
                if ray_origin[1] < 0 or ray_origin[1] > 10: draw_plane_point = Vector((0.0, (ray_origin[1] - 10), 0.0))
                else: draw_plane_point = Vector((0.0, 0.0, 0.0))
            elif view_vector[0] < 0 and abs(view_vector[1]) <= abs(view_vector[0]):
                n = Vector((1.0, 0.0, 0.0))
                if ray_origin[0] > 10 or ray_origin[0] < 0: draw_plane_point = Vector(((ray_origin[0] - 10), 0.0, 0.0))
                else: draw_plane_point = Vector((0.0, 0.0, 0.0))
            elif view_vector[0] > 0 and abs(view_vector[1]) <= view_vector[0]:
                n = Vector((-1.0, 0.0, 0.0))
                if ray_origin[0] < -10 or ray_origin[0] > 0: draw_plane_point = Vector(((ray_origin[0] + 10), 0.0, 0.0))
                else: draw_plane_point = Vector((0.0, 0.0, 0.0))
        hitloc = mathutils.geometry.intersect_line_plane(ray_origin, (ray_origin + view_vector), draw_plane_point, n)

    v = Vector((0.0, 0.0, 1.0))
    np_print('n', n)
    q = v.rotation_difference(n)
    v = Vector((0.0, 0.0, 1.0))
    ro = v.rotation_difference(n)
    #np_print('ro = ', ro)

    return (n, ro, hitloc)



def get_fac_from_view_loc_plane(region, rv3d, rmin, centerloc, q):

    # writing the dots for circle at center of scene:
    radius = 1
    ang = 0.0
    circle = [(0.0 ,0.0 ,0.0)]
    while ang < 360.0:
        circle.append(((cos(radians(ang)) * radius), (sin(radians(ang)) * radius), (0.0)))
        ang += 10
    circle.append(((cos(radians(0.0)) * radius), (sin(radians(0.0)) * radius), (0.0)))

    # rotating and translating the circle to user picked angle and place:
    circle = rotate_graphic(circle, q)
    circle = translate_graphic(circle, centerloc)

    rmax = 1
    for i, co in enumerate(circle):
        co = view3d_utils.location_3d_to_region_2d(region, rv3d, co)
        circle[i] = co
    for i in range(1, 18):
        r = (circle[0] - circle[i]).length
        r1 = (circle[0] - circle[i + 18]).length
        #if (r + r1) > rmax and abs(r - r1) < min(r, r1)/5: rmax = (r+r1)/2
        #if (r + r1) > rmax and abs(r - r1) < min(r, r1)/10: rmax = r + r1
        if (r + r1) > rmax and (r + r1) / 2 < rmin: rmax = (r + r1)
        elif (r + r1) > rmax and (r + r1) / 2 >= rmin: rmax = (r + r1) * rmin / (((r + r1) / 2)- ((r + r1) / 2) - rmin)
        rmax = abs(rmax)
        circle[i] = co
        #np_print('rmin', rmin)
        #np_print('rmax', rmax)
        fac = (rmin * 2) / rmax
    return fac

def rotate_graphic(graphic, q):
    # rotating the graphic to the angle of chosen normal:
    if q != None:
        for i, co in enumerate(graphic):
            if type(co) == tuple:
                vco = Vector(co)
            else: vco = co
            if vco != None:
                vco = q * vco
            graphic[i] = vco
    return graphic

def translate_graphic(graphic, vectorloc):
    # translating graphic to the chosen point in scene:
    m = copy.deepcopy(graphic[0])
    for i, co in enumerate(graphic):
        #np_print('co', co)
        if type(co) == tuple:
            vco = Vector(co)
        else: vco = co
        if vco != None:
            vco = vco + vectorloc
        graphic[i] = vco
    return graphic


def get_angle_from_iso_planar(centerloc, normal, proj):
    np_print('normal', normal)
    np_print('centerloc', centerloc)
    np_print('proj', proj)
    isohipse = mathutils.geometry.intersect_plane_plane(centerloc, normal, centerloc, Vector((0.0, 0.0, 1.0)))
    np_print('isohipse', isohipse)
    if isohipse == (None, None):
        isohipse = (centerloc, (centerloc + Vector((1.0, 0.0, 0.0))))
        hor = True
    else:
        isohipse = (isohipse[0], isohipse[0] - isohipse[1])
        hor = False
    np_print('isohipse', isohipse)
    vco1 = isohipse[1] - isohipse[0]
    vco2 = proj - centerloc
    np_print('vco1', vco1)
    np_print('vco2', vco2)
    if hor:
        if proj[1] < centerloc[1]: isoang = 360 - degrees(vco1.angle(vco2))
        else: isoang = degrees(vco1.angle(vco2))
    else:
        if proj[2] < centerloc[2]: isoang = 360 - degrees(vco1.angle(vco2))
        else: isoang = degrees(vco1.angle(vco2))

    return isoang, isohipse
    '''
    Return the intersection between two planes
    Parameters:

        plane_a_co (mathutils.Vector) – Point on the first plane
        plane_a_no (mathutils.Vector) – Normal of the first plane
        plane_b_co (mathutils.Vector) – Point on the second plane
        plane_b_no (mathutils.Vector) – Normal of the second plane

    Returns:

    The line of the intersection represented as a point and a vector
    Return type:

    tuple pair of mathutils.Vector or None if the intersection can’t be calculated
    '''

def get_angle_vector_from_vector(centerloc, startloc, endloc):
    np_print('centerloc', centerloc)
    np_print('startloc', startloc)
    np_print('endloc', endloc)

    vco1 = endloc - centerloc
    vco2 = startloc - centerloc
    np_print('vco1', vco1)
    np_print('vco2', vco2)
    alpha = degrees(vco1.angle(vco2))
    return alpha


def get_eul_z_angle_dif_in_rotated_system(eul_0, eul_1, n):

    np_print('eul_0 =', eul_0)
    np_print('eul_1 =', eul_1)
    v = Vector ((0.0, 0.0, 1.0))
    if n[2] < 0:
        n = Vector((-n[0], -n[1], -n[2]))
        n_dif_quat = n.rotation_difference(v)
        np_print('n_dif_quat =', n_dif_quat)
        n_dif_eul = n_dif_quat.to_euler()
        np_print('n_dif_eul =', n_dif_eul)
        a = copy.deepcopy(eul_0)
        np_print('a =', a)
        b = copy.deepcopy(eul_1)
        np_print('b =', b)
        a.rotate(n_dif_eul)
        b.rotate(n_dif_eul)
        np_print('a =', a)
        np_print('b =', b)
        a_z = degrees(a.z)
        b_z = degrees(b.z)
        np_print('a_z =', a_z)
        np_print('b_z =', b_z)
        alpha_real = a_z - b_z
    else:
        n_dif_quat = n.rotation_difference(v)
        np_print('n_dif_quat =', n_dif_quat)
        n_dif_eul = n_dif_quat.to_euler()
        np_print('n_dif_eul =', n_dif_eul)
        a = copy.deepcopy(eul_0)
        np_print('a =', a)
        b = copy.deepcopy(eul_1)
        np_print('b =', b)
        a.rotate(n_dif_eul)
        b.rotate(n_dif_eul)
        np_print('a =', a)
        np_print('b =', b)
        a_z = degrees(a.z)
        b_z = degrees(b.z)
        np_print('a_z =', a_z)
        np_print('b_z =', b_z)
        alpha_real = a_z - b_z
        alpha_real = -alpha_real
    return alpha_real


def get_eul_z_angle_diff_in_rotated_system(eul_0, eul_1, eul_zero, ro_hor):


    np_print('eul_0 =', eul_0)
    np_print('eul_1 =', eul_1)
    np_print('eul_zero =', eul_zero)

    a = copy.deepcopy(eul_0)
    b = copy.deepcopy(eul_1)
    zero = copy.deepcopy(eul_zero)
    np_print('a =', a)
    np_print('b =', b)
    np_print('zero =', zero)
    a.x = -a.x
    a.y = -a.y
    a.z = -a.z
    eul_0.rotate(a)
    #b.rotate(-ro_hor)
    b.rotate(a)
    np_print('a =', a)
    np_print('eul_0 =', eul_0)
    np_print('b =', b)
    b_z = degrees(round((b.z), 4))
    np_print('b_z =', b_z)
    alpha_real = b_z


    return alpha_real



def get_eul_z_angle_difff_in_rotated_system(eul_0, eul_1, n):

    np_print('eul_0 =', eul_0)
    np_print('eul_1 =', eul_1)

    eul_delta = Euler(((eul_1.x - eul_0.x), (eul_1.y - eul_0.y), (eul_1.z - eul_0.z)), 'XYZ')
    np_print('eul_delta =', eul_delta)
    np_print('n =', n)
    v = Vector ((0.0, 0.0, 1.0))

    n_dif_quat = n.rotation_difference(v)
    np_print('n_dif_quat =', n_dif_quat)
    n_dif_eul = n_dif_quat.to_euler()
    np_print('n_dif_eul =', n_dif_eul)
    eul_delta.rotate(n_dif_eul)
    np_print('eul_delta', eul_delta)
    alpha_real = degrees(eul_delta.z)
    np_print('alpha_real', alpha_real)

    return alpha_real



def get_eul_z_angle_diffff_in_rotated_system(eul_0, eul_1, n):

    np_print('eul_0 =', eul_0)
    np_print('eul_1 =', eul_1)
    np_print('n =', n)
    v = Vector ((0.0, 0.0, 1.0))
    n_dif_quat = n.rotation_difference(v)
    np_print('n_dif_quat =', n_dif_quat)
    a = copy.deepcopy(eul_0)
    b = copy.deepcopy(eul_1)
    a.rotate(n_dif_quat)
    b.rotate(n_dif_quat)
    np_print('eul_0 =', a)
    np_print('eul_1 =', b)
    alpha_real = degrees(b.z - a.z )

    '''

    if int(b.y) == -3 and b.z > 0:
        alpha_real = alpha_real - (180*int(b.z / 1.55))
    elif int(b.y) == -6 and b.z > 0:
        alpha_real = alpha_real - (180*int(b.z / 1.55))
    elif int(b.y) == -0 and b.z > 3:
        alpha_real = alpha_real - (180*int(b.z / 1.55))
    elif int(b.y) == -3 and b.z < 0:
        alpha_real = alpha_real + (180*int(b.z / 1.55))
    elif int(b.y) == -6 and b.z < 0:
        alpha_real = alpha_real + (180*int(b.z / 1.55))
    elif int(b.y) == -0 and b.z < -3:
        alpha_real = alpha_real + (180*int(b.z / 1.55))

    '''

    np_print('alpha_real', alpha_real)

    return alpha_real



def get_eul_z_angle_difffff_in_rotated_system(eul_0, eul_1, n):


    np_print('n =', n)
    c = copy.deepcopy(eul_0)
    d = copy.deepcopy(eul_1)
    np_print('------- eul_0 =', eul_0)
    np_print('------- eul_0 =', round(degrees(eul_0.x),2), round(degrees(eul_0.y),2), round(degrees(eul_0.z),2))
    np_print('------- eul_1 =', round(degrees(eul_1.x),2), round(degrees(eul_1.y),2), round(degrees(eul_1.z),2))
    v = Vector ((0.0, 0.0, 1.0))
    if n[2] > 0:
        m = copy.deepcopy(n)
        if abs(n[0]) == 0.0000: m[0] = 0.001
        if abs(n[1]) == 0.0000: m[1] = 0.001
    elif n[2] < 0:
        m = copy.deepcopy(-n)
        if abs(n[0]) == 0.0000: m[0] = 0.001
        if abs(n[1]) == 0.0000: m[1] = 0.001
    else:
        if abs(n[0]) == 0.0000: m = Vector ((0.001, n[1], 0.001))
        elif abs(n[1]) == 0.0000: m = Vector ((n[0], 0.001, 0.001))
        else: m = Vector ((n[0], n[1], 0.001))
    np_print('................m =', m)
    if abs(eul_0.x) == 0: c.x = 0.001
    if abs(eul_0.y) == 0: c.y = 0.001
    if abs(eul_0.z) == 0: c.z = 0.001
    if round(eul_0.x, 4) == 1.5708: c.x = 1.5700
    if round(eul_0.y, 4) == 1.5708: c.y = 1.5700
    if round(eul_0.z, 4) == 1.5708: c.z = 1.5700
    if round(eul_0.x, 4) == -1.5708: c.x = -1.5700
    if round(eul_0.y, 4) == -1.5708: c.y = -1.5700
    if round(eul_0.z, 4) == -1.5708: c.z = -1.5700
    np_print('------- eul_0 =', c)
    n_dif_quat = m.rotation_difference(v)
    n_dif_eul = n_dif_quat.to_euler()
    np_print('``````` n_dif_eul =', round(degrees(n_dif_eul.x),2), round(degrees(n_dif_eul.y),2), round(degrees(n_dif_eul.z),2))
    a = copy.deepcopy(c)
    b = copy.deepcopy(d)
    a.rotate(n_dif_eul)
    b.rotate(n_dif_eul)
    np_print('>>>>>>> eul_0 =', round(degrees(a.x),2), round(degrees(a.y),2), round(degrees(a.z),2))
    np_print('>>>>>>> eul_1 =', round(degrees(b.x),2), round(degrees(b.y),2), round(degrees(b.z),2))
    np_print('------- eul_1 =', b)

    '''
    if int(b.y) == -3 and b.z > 0:
        alpha_real = alpha_real - (180*int(b.z / 1.55))
    elif int(b.y) == -6 and b.z > 0:
        alpha_real = alpha_real - (180*int(b.z / 1.55))
    elif int(b.y) == -0 and b.z > 3:
        alpha_real = alpha_real - (180*int(b.z / 1.55))
    elif int(b.y) == -3 and b.z < 0:
        alpha_real = alpha_real + (180*int(b.z / 1.55))
    elif int(b.y) == -6 and b.z < 0:
        alpha_real = alpha_real + (180*int(b.z / 1.55))
    elif int(b.y) == -0 and b.z < -3:
        alpha_real = alpha_real + (180*int(b.z / 1.55))
    '''
    alpha_real = degrees(b.z - a.z )
    if n[2] < 0: alpha_real = - alpha_real
    np_print('alpha_real', alpha_real)

    return alpha_real



def get_eul_z_angle_diffffff_in_rotated_system(eul_0, eul_1, n): # v6?


    np_print('n =', n)
    c = eul_0.copy()
    d = eul_1.copy()
    np_print('------- eul_0 =', eul_0)
    np_print('------- eul_0 =', round(degrees(eul_0.x),6), round(degrees(eul_0.y),6), round(degrees(eul_0.z),6))
    np_print('------- eul_1 =', round(degrees(eul_1.x),6), round(degrees(eul_1.y),6), round(degrees(eul_1.z),6))
    v = Vector ((0.0, 0.0, 1.0))
    if n[2] > 0:
        m = n.copy()
        if abs(n[0]) == 0.0: m[0] = 0.000001
        if abs(n[1]) == 0.0: m[1] = 0.000001
    elif n[2] < 0:
        m = -n.copy()
        if abs(n[0]) == 0.0: m[0] = 0.000001
        if abs(n[1]) == 0.0: m[1] = 0.000001
    else:
        if abs(n[0]) == 0.0: m = Vector ((0.000001, n[1], 0.000001))
        elif abs(n[1]) == 0.0: m = Vector ((n[0], 0.000001, 0.000001))
        else: m = Vector ((n[0], n[1], 0.000001))
    np_print('................m =', m)
    if abs(eul_0.x) == 0: c.x = 0.000001
    if abs(eul_0.y) == 0: c.y = 0.000001
    if abs(eul_0.z) == 0: c.z = 0.000001
    # 90 deg == 1.5707963268 rad
    if round(eul_0.x, 6) == 1.570796: c.x = 1.5708
    if round(eul_0.y, 6) == 1.570796: c.y = 1.5708
    if round(eul_0.z, 6) == 1.570796: c.z = 1.5708
    if round(eul_0.x, 6) == -1.570796: c.x = -1.5708
    if round(eul_0.y, 6) == -1.570796: c.y = -1.5708
    if round(eul_0.z, 6) == -1.570796: c.z = -1.5708
    np_print('------- eul_0 =', c)
    n_dif_quat = m.rotation_difference(v)
    n_dif_eul = n_dif_quat.to_euler()
    np_print('``````` n_dif_eul =', round(degrees(n_dif_eul.x),6), round(degrees(n_dif_eul.y),6), round(degrees(n_dif_eul.z),6))
    a = c.copy()
    b = d.copy()
    a.rotate(n_dif_eul)
    b.rotate(n_dif_eul)
    np_print('>>>>>>> eul_0 =', round(degrees(a.x),6), round(degrees(a.y),6), round(degrees(a.z),6))
    np_print('>>>>>>> eul_1 =', round(degrees(b.x),6), round(degrees(b.y),6), round(degrees(b.z),6))
    np_print('------- eul_1 =', b)

    alpha_real = degrees(b.z - a.z )
    if n[2] < 0: alpha_real = - alpha_real
    np_print('alpha_real', alpha_real)

    return alpha_real
