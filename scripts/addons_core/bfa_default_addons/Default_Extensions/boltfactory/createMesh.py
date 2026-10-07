# SPDX-FileCopyrightText: 2010-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later
"""File contains all the Mesh creation required for the Boltfactory"""

from math import (
    sin, cos, tan,
    asin, atan, radians
)
from mathutils import (
    Matrix,
    Vector,
    geometry,
)
import numpy as np
import bpy


# ####################################################################
#                    Miscellaneous Utilities
# ####################################################################

def scale_mesh_verts(verts, scale_factor):
    """
    Applies the scale factor to the verts of an object.
    :param verts: list of verts packed as either a list or tuple.
    :param scale_factor: Float to scale the verts by.
    :return: Scale corrected list of verts.
    """
    ret_verts = []
    for vert in verts:
        ret_verts.append([vert[0] * scale_factor, vert[1] * scale_factor, vert[2] * scale_factor])
    return ret_verts


def simple_rotation_matrix(angle, axis_flag='z'):
    """
    Creates a matrix representing a rotation of size 4.
    :param angle: (float) - The angle of rotation desired in degrees.
    :param axis_flag: (string) - Possible values:
    #              'x' - "x-axis rotation".
    #              'y' - "y-axis rotation".
    #              'z' - "z-axis rotation".
    :return: Matrix object. A new rotation matrix.
    """
    if axis_flag not in ('x', 'y', 'z'):
        print("simple_rotation_matrix can only do x, y or z axis")

    return Matrix.Rotation(radians(angle), 4, axis_flag.upper())


def rot_mesh(verts, matrix):
    """
    Returns a list of verts rotated by the given matrix. Used by spin_dup & create_external_thread.
    :param verts: (list) - mesh verts
    :param matrix: from simple_rotation_matrix()
    :return: verts (list) - rotated vertices
    """
    return [(matrix @ Vector(v))[:] for v in verts]


def copy_faces(faces, offset):
    """
    Returns a list of faces that have their index incremented by offset
    :param faces: (list) - mesh faces
    :param offset: (int) -
    :return: faces (list) -
    """
    return [[(i + offset) for i in f] for f in faces]


def spin_dup(verts, faces, spin_angle, spin_steps, axis):
    """
    Much like Blenders built in spin_dup.
    spin_dup takes verts and faces to perform a rotation divided into a number of steps
    :param verts: (list) - part mesh verts
    :param faces: (list) - part mesh faces
    :param spin_angle: (float) - Total amount of spin in degrees
    :param spin_steps: (integer) - number of divisions, or steps, the rotation is made from
    :param axis: (string, lower case) - 'x', 'y' or 'z'
    :return: s_verts: (list)
             s_faces: (list)
    """
    s_verts = []
    s_faces = []

    if spin_steps == 0:
        spin_steps = 1

    step = spin_angle / spin_steps  # set step so pieces * step = degrees in arc

    for i in range(int(spin_steps)):
        rot_mat = simple_rotation_matrix(step * i, axis)  # 4x4 rotation matrix
        rot = rot_mesh(verts, rot_mat)
        s_faces.extend(copy_faces(faces, len(s_verts)))
        s_verts.extend(rot)
    return s_verts, s_faces


def move_verts_up_z(verts, distance):
    """
    Returns a list of verts that have been moved in the z axis by DISTANCE
    :param verts: (list) - mesh verts
    :param distance: (float) - Distance to move in the Z-axis
    :return: verts (list) - List of moved Verts
    """
    ret = []
    for vert in verts:
        ret.append([vert[0], vert[1], vert[2] + distance])
    return ret


def mirror_verts_faces(verts, faces, axis, flip_point=0.0):
    """
    Returns a list of verts and faces that have been mirrored in the declared AXIS
    :param verts: (list) - mesh verts
    :param faces: (list) - mesh faces
    :param axis: (string) - 'x', 'y' or 'z'
    :param flip_point: (float) - position of the mirror on the selected axis
    :return: Mirrored lists of Verts and Faces of the mesh
    """
    ret_vert = []
    ret_face = []
    offset = len(verts)
    if axis == 'y':
        for vert in verts:
            delta = vert[0] - flip_point
            ret_vert.append([flip_point - delta, vert[1], vert[2]])
    if axis == 'x':
        for vert in verts:
            delta = vert[1] - flip_point
            ret_vert.append([vert[0], flip_point - delta, vert[2]])
    if axis == 'z':
        for vert in verts:
            delta = vert[2] - flip_point
            ret_vert.append([vert[0], vert[1], flip_point - delta])

    for fff in faces:
        fsub = []
        for inc in range(len(fff)):
            fsub.append(fff[inc] + offset)
        fsub.reverse()  # flip the order to make norm point out
        ret_face.append(fsub)

    return ret_vert, ret_face


def build_face_list_quads(offset, column, row, flip=0):
    """
    Returns a list of faces that make up an array of 4 point polygon.
    :param offset: (int) - first vertex starting point.
    :param column: (int)
    :param row: (int)
    :param flip: (bool) - used to manage the surface normal direction.
    :return: List of Faces, where each face is a 4 element list of Vert indexes.
    """
    ret = []
    row_start = 0
    for _j in range(row):
        for inc in range(column):
            res1 = row_start + inc
            res2 = row_start + inc + (column + 1)
            res3 = row_start + inc + (column + 1) + 1
            res4 = row_start + inc + 1
            if flip:
                ret.append([offset + res1, offset + res2, offset + res3, offset + res4])
            else:
                ret.append([offset + res4, offset + res3, offset + res2, offset + res1])
        row_start += column + 1
    return ret


def fill_ring_face(offset, num, face_down=0):
    """
    Returns a list of faces that makes up a fill pattern for a circle.
    :param offset: (int) - starting vertex.
    :param num: (int) - number of vertices to use making the fill.
    :param face_down: (bool) - used to manage the surface normal direction.
    :return: (list) - face list, (maybe empty).
    """
    ret = []
    face = [1, 2, 0]
    temp_face = [0, 0, 0]
    bbb = 1
    ccc = 2
    if num < 3:
        return []                   # insufficient verts to make a face
    for i in range(num - 2):
        if i % 2:
            temp_face[0] = face[ccc]
            temp_face[1] = face[ccc] + 1
            temp_face[2] = face[bbb]
            if face_down:
                ret.append([offset + face[2], offset + face[1], offset + face[0]])
            else:
                ret.append([offset + face[0], offset + face[1], offset + face[2]])
        else:
            temp_face[0] = face[ccc]
            if face[ccc] == 0:
                temp_face[1] = num - 1
            else:
                temp_face[1] = face[ccc] - 1
            temp_face[2] = face[bbb]
            if face_down:
                ret.append([offset + face[0], offset + face[1], offset + face[2]])
            else:
                ret.append([offset + face[2], offset + face[1], offset + face[0]])

        face[0] = temp_face[0]
        face[1] = temp_face[1]
        face[2] = temp_face[2]
    return ret


def fill_fan_face(offset, num, face_down=0):
    """
    Returns a list of faces that makes up a triangular fill pattern around the last vert.
    :param offset: (int) - First Vert index to start with.
    :param num: (int) - Number of verts to use.
    :param face_down: (bool) - used to manage the surface normal direction.
    :return: (list) - list of faces, (maybe empty if fewer than 3 verts given).
    """
    ret = []
    face = [num - 1, 0, 1]
    temp_face = [0, 0, 0]
    aaa = 0
    ccc = 2
    if num < 3:
        return []               # insufficient verts to make a face
    for _i in range(num - 2):
        temp_face[0] = face[aaa]
        temp_face[1] = face[ccc]
        temp_face[2] = face[ccc] + 1
        if face_down:
            ret.append([offset + face[0], offset + face[1], offset + face[2]])
        else:
            ret.append([offset + face[2], offset + face[1], offset + face[0]])

        face[0] = temp_face[0]
        face[1] = temp_face[1]
        face[2] = temp_face[2]
    return ret


# ####################################################################
#                    Create Allen Bit
# ####################################################################

def allen_fill(offset, flip=0):
    """
    This builds the triangles that make up the space between the top
    of the hexagon and the circle inscribed by top dit diameter.
    Implicit is DIV_COUNT=36 as this builds half the circle using 18 points.
    :param offset: (int) - starting index for the first vert of the face list.
    :param flip: (bool) - used to manage the surface normal direction.
    :return: list of faces.
    """
    faces = []
    lookup = [[19, 1, 0],
              [19, 2, 1],
              [19, 3, 2],
              [19, 20, 3],
              [20, 4, 3],
              [20, 5, 4],
              [20, 6, 5],
              [20, 7, 6],
              [20, 8, 7],
              [20, 9, 8],

              [20, 21, 9],

              [21, 10, 9],
              [21, 11, 10],
              [21, 12, 11],
              [21, 13, 12],
              [21, 14, 13],
              [21, 15, 14],

              [21, 22, 15],
              [22, 16, 15],
              [22, 17, 16],
              [22, 18, 17]
              ]
    for i in lookup:
        if flip:
            faces.append([offset + i[2], offset + i[1], offset + i[0]])
        else:
            faces.append([offset + i[0], offset + i[1], offset + i[2]])

    return faces


def allen_bit_dia(flat_distance):
    """
    Used to determine if a given hex size fits in a diameter.
    :param flat_distance: (float) - Distance across hex flats.
    :return: (float) - Flat diameter required with 5% added margin.
    """
    flat_radius = (float(flat_distance) / 2.0) / cos(radians(30))
    return (flat_radius * 1.05) * 2.0


def allen_bit_dia_to_flat(dia):
    """
    Inverse of allen_bit_dia, takes a diameter with 5% margin and determines
    what the hex size across flats is.
    :param dia: (float) - diameter of the hex points including extra 5%.
    :return: (float) - Hex flats distance.
    """
    flat_radius = (dia / 2.0) / 1.05
    return (flat_radius * cos(radians(30))) * 2.0


def create_allen_bit(props_in, flat_distance):
    """
    Creates the hexagonal indent in the top of the head.
    Explicit is div_count=36 as the returned boundary is a ring of 36 verts.
    :param props_in: (parameter) used for - bf_Allen_Bit_Depth
    :param flat_distance: (float) - size of the hex across flats.
    :return: Verts (list).
             Faces (list).
             Diameter (float) - Diameter of the hex Allen consumed in the head.
    """
    verts = []
    faces = []
    div_count = 36

    flat_radius = (flat_distance / 2.0) / cos(radians(30))
    outer_radius = flat_radius * 1.05
    outer_radius_height = flat_radius * (0.1 / 5.77)
    face_start_outside = len(verts)
    deg_step = 360.0 / float(div_count)

    for i in range(int(div_count / 2) + 1):  # only do half and mirror later
        x = sin(radians(i * deg_step)) * outer_radius
        y = cos(radians(i * deg_step)) * outer_radius
        verts.append([x, y, 0])

    face_start_inside = len(verts)

    deg_step = 360.0 / 6.0
    for i in range(int(6 / 2) + 1):
        x = sin(radians(i * deg_step)) * flat_radius
        y = cos(radians(i * deg_step)) * flat_radius
        verts.append([x, y, 0 - outer_radius_height])

    faces.extend(allen_fill(face_start_outside, 0))

    face_start_bottom = len(verts)

    deg_step = 360.0 / 6.0
    for i in range(int(6 / 2) + 1):
        x = sin(radians(i * deg_step)) * flat_radius
        y = cos(radians(i * deg_step)) * flat_radius
        verts.append([x, y, 0 - props_in.bf_Allen_Bit_Depth])

    faces.extend(build_face_list_quads(face_start_inside, 3, 1, True))
    faces.extend(fill_ring_face(face_start_bottom, 4))

    m_verts, m_faces = mirror_verts_faces(verts, faces, 'y')
    verts.extend(m_verts)
    faces.extend(m_faces)

    return verts, faces, outer_radius * 2.0


# ####################################################################
#                    Create Robertson Bit (square)
# Robertson head is a square, 4-sided profile, which may or may not have a slight taper.
# Also known as the Type III Square Recessed in the ASME B18.6.7M 1999.
# Robertson driver bits come with predefined sizes.
# ####################################################################

def robertson_bit_size_to_flat_distance(bit_size):
    """
    Robertson driver bits come with predefined sizes, hence a lookup is required. Takes the R__ number
    and returns the flats as a distance between opposite faces. Also known as the Type III Square Recessed.
    The values used here is the Ref Recess Across Flats from the ASME B18.6.7M 1999.
    :param bit_size: (string) - the R number.
    :return: Distance: (float) - distance between flats.
    """

    # Create a dictionary to look up the name vs size of Robertson bits
    robertson_bits = {'bf_Robertson_R00': 1.3,    # M2
                      'bf_Robertson_R0': 1.78,    # M2.5 / M3
                      'bf_Robertson_R1': 2.31,    # M3.5
                      'bf_Robertson_R2': 2.84,    # M4 / M5
                      'bf_Robertson_R3': 3.36,    # M6
                      'bf_Robertson_R4': 4.85,    # M8 / M10
                      }
    return robertson_bits.get(bit_size, 1.78)     # default to R0 in the M3 preset


def robertson_bit_size_to_depth_distance(bit_size):
    """
    Robertson driver bits come with predefined sizes, hence a lookup is required. Takes the R__ number
    and returns the depth of the bit. Also known as the Type III Square Recessed.
    The values used here is the Max Recess Penetration Gaging Depth from the ASME B18.6.7M 1999.
    :param bit_size: (string) - the R number.
    :return: Distance: (float) - depth.
    """

    # Create a dictionary to look up the name vs size of Robertson bits
    robertson_bits = {'bf_Robertson_R00': 0.7,    # M2
                      'bf_Robertson_R0': 0.97,    # M2.5 / M3
                      'bf_Robertson_R1': 1.66,    # M3.5
                      'bf_Robertson_R2': 1.91,    # M4 / M5
                      'bf_Robertson_R3': 2.42,    # M6
                      'bf_Robertson_R4': 2.54,    # M8 / M10
                      }
    return robertson_bits.get(bit_size, 0.97)     # default to R0 in the M3 preset


def robertson_mesh(props_in):
    """
    Robertson head is a square, 4-sided profile, which may or may not have a slight taper.
    The model here assumes no taper and builds a lookup using the ASME data.
    :param props_in: (parameter) used for - passthrough
    :return: Verts: (list) - mesh Verts.
             Faces: (list) - mesh Faces.
             Diameter: (float) - Diameter of the Bit consumed in the head.
    """

    r_s_verts, r_s_faces, hole_dia = n_bit_mesh(props_in, 4)
    return r_s_verts, r_s_faces, hole_dia


# ####################################################################
#                    Create N-Sided Bit
# Used for Robertson head. Can make a Hex Allen with alternative mesh topology.
# Plus these other 5 Bits; Star, Double Square, Double Hex, Triple Square XZN, 12-Spline.
# ####################################################################

def n_bit_mesh(props_in, n_bit_sides):
    """
    A bit hole of n sides. Accepts variable DivCount, rounded to mod(n_sides).
    Includes an option for a security pin.
    If Robertson uses dimension lookup for driver bits as they come with predefined sizes.
    :param props_in: (parameter) used for - bf_Allen_Bit_Flat_Distance, bf_Allen_Bit_Depth, bf_Bit_Type,
                                            bf_Robertson_Size_Type, bf_Div_Count, bf_Security_Bit
    :param n_bit_sides: (Int) - the number of sides for the bit, sourced from "bf_N_Sided_Bit".
    :return: Verts: (list) - mesh Verts.
             Faces: (list) - mesh Faces.
             Diameter: (float) - Diameter of the Bit consumed in the head.
    """

    n_size = props_in.bf_Allen_Bit_Flat_Distance / 2.0        # Needs to be a radius
    deepness = props_in.bf_Allen_Bit_Depth
    if props_in.bf_Bit_Type == 'bf_Bit_Robertson':     # Figure out depth and diameter if Robertson
        n_size = robertson_bit_size_to_flat_distance(props_in.bf_Robertson_Size_Type) / 2.0
        deepness = robertson_bit_size_to_depth_distance(props_in.bf_Robertson_Size_Type)

    # Convert to half diameter
    hole_dia = 2 * n_size * (1/cos(radians(180/n_bit_sides))) * 1.05      # Add 5% for the fill.
    hole_radius = hole_dia * 0.5

    n_verts = []
    n_faces = []

    r_deg_step = np.linspace(-180/n_bit_sides, 180/n_bit_sides, (props_in.bf_Div_Count+n_bit_sides)//n_bit_sides)
    r_angle_rad = [radians(i) for i in r_deg_step]

    # Circle hole boundary
    for theta in r_angle_rad:
        n_verts.append([sin(theta) * hole_radius, cos(theta) * hole_radius, 0.0])

    # phi is the angle represented by the turning number of a polygram
    phi = bit_mesh_point_turning_angle(props_in)

    # Top sides
    for theta in r_angle_rad:
        # n_verts.append([tan(theta) * n_size, n_size, 0.0])        # Basic form when phi==0.
        p_cross = geometry.intersect_line_line_2d([tan(theta) * n_size, n_size],
                                                  [0, 0],
                                                  [n_size * tan(r_angle_rad[0]) * (2 * np.signbit(theta) - 1), n_size],
                                                  [0, n_size * (1 - abs(tan(r_angle_rad[0]) * tan(phi)))])
        n_verts.append([p_cross.x, p_cross.y, 0.0])

    # Down to bottom depth. Simple model rather than a broach of a drilled hole.
    for theta in r_angle_rad:
        # n_verts.append([tan(theta) * n_size, n_size, -deepness])       # Basic form when phi==0.
        p_cross = geometry.intersect_line_line_2d([tan(theta) * n_size, n_size],
                                                  [0, 0],
                                                  [n_size * tan(r_angle_rad[0]) * (2 * np.signbit(theta) - 1), n_size],
                                                  [0, n_size * (1 - abs(tan(r_angle_rad[0]) * tan(phi)))])
        n_verts.append([p_cross.x, p_cross.y, -deepness])

    if props_in.bf_Security_Bit:
        # Centre fill, for adding security nipple
        for theta in r_angle_rad:
            n_verts.append([sin(theta) * n_size/2.5, cos(theta) * n_size/2.5, -deepness])

        deepness *= 0.1     # Make the nipple 10% below the top edge
        for theta in r_angle_rad:
            n_verts.append([sin(theta) * n_size/2.5, cos(theta) * n_size/2.5, -deepness])

    # Now all the verts exist, make the faces for that sector
    n_faces.extend(build_face_list_quads(0, len(r_angle_rad) - 1, len(n_verts)//len(r_angle_rad) - 1, 1))

    n_verts.append([0, 0, 0 - deepness])        # add centre point for fill Fan
    n_faces.extend(fill_fan_face(len(n_verts) - len(r_angle_rad) - 1, len(r_angle_rad) + 1, 0))

    # Need to align a point onto the axis
    n_verts = rot_mesh(n_verts, simple_rotation_matrix(180/n_bit_sides, 'z'))

    s_n_verts, s_n_faces = spin_dup(n_verts, n_faces, 360, n_bit_sides, 'z')

    return s_n_verts, s_n_faces, hole_dia


def bit_mesh_point_turning_angle(props_in):
    """
    This helper function returns the inset angle of the face between points for the n_bit_mesh function.
    A value of zero angle points directly to the next point around the driver bit.
    Another way to view this is controlling the internal angle, or the turning number of a regular polygon.
    The full calculation needs to consider the number of points of the bit mesh and then the
    number of points skipped for a line of straight engagement.
        phi = lobe_step * half the external point angle
    To keep things manageable this will be done by way of a look up against the bit type selected.
    :param props_in: (parameter) used for - bf_Bit_Type
    :return: Angle radians: (float) - Inset angle between bit points
    """
    # phi = 0     Default Plane face i.e. regular square/hexagonal drive.
    # Star = 30 ; a 2{3} regular compound hexagram.
    # Double Square = 22.5 ; a 2{4} regular compound octagram.
    # Double Hex = 15 ; a 2{6} regular compound dodecagram.
    # Triple Square XZN = 30 ; a 3{4} regular compound dodecagram.
    # 12-Spline = 45; a 4{3} regular compound dodecagram.

    phi = {'bf_Bit_Star': 30,
           'bf_Bit_Double_Square': 22.5,
           'bf_Double_Hex': 15,
           'bf_Triple_Square_XZN': 30,
           'bf_12_Spline': 45}

    return radians(phi.get(props_in.bf_Bit_Type, 0))


# ####################################################################
#                    Create Torx Bit
# The hexalobular ISO 10664 (Torx) is defined by radii, the Torx plus® by ellipses.
# Useful reference: www.engineersedge.com/hardware/torx_head_fastener_basic_dimensions_15261.htm#google_vignette
# ####################################################################

def torx_bit_size_to_point_distance(bit_size):
    """
    Torx driver bits come with predefined sizes, hence a lookup is required. Takes the T__ number
    and returns the diameter as a distance between opposite lobes. See ISO 10664:1999(E).
    :param bit_size: (string) - the T number.
    :return: Distance: (float) - maximal diameter of lobes.
    """

    # Create a dictionary to look up the name vs size of Torx bits
    torx_bits = {'bf_Torx_T6':  1.75,    # M2
                 'bf_Torx_T8':  2.39,    # M2.5
                 'bf_Torx_T10': 2.83,    # M3
                 'bf_Torx_T15': 3.35,    # M3.5
                 'bf_Torx_T20': 3.94,    # M4
                 'bf_Torx_T25': 4.52,    # M5
                 'bf_Torx_T30': 5.61,    # M6
                 'bf_Torx_T40': 6.75,    # M8
                 'bf_Torx_T45': 7.92,    # M8 also sometimes
                 'bf_Torx_T50': 8.94,    # M10
                 'bf_Torx_T55': 11.35,   # M12
                 'bf_Torx_T60': 13.45,   # M14
                 'bf_Torx_T70': 15.7,    # M16
                 'bf_Torx_T80': 17.75,   # M18
                 'bf_Torx_T90': 20.2,    # M20
                 'bf_Torx_T100': 22.4    # M22
                 }
    return torx_bits.get(bit_size, 2.83)     # default to T10 in the m3 preset


def torx_fill(offset, flip=0):
    """
    This builds the triangles that make up the space between the top
    of the lobes and the circle inscribed by top dit diameter.
    Implicit is DIV_COUNT=36 as this builds quarter the circle using 9 points.
    :param offset: (int) - starting index for the first vert of the face list.
    :param flip: (bool) - used to manage the surface normal direction.
    :return: list of faces.
    """
    faces = []
    # The first lookup column is used for the outside circle vert index.
    lookup = [[0, 10, 11],
              [0, 11, 12],
              [0, 12, 1],

              [1, 12, 13],
              [1, 13, 14],
              [1, 14, 15],
              [1, 15, 2],

              [2, 15, 16],
              [2, 16, 17],
              [2, 17, 18],
              [2, 18, 19],
              [2, 19, 3],

              [3, 19, 20],
              [3, 20, 21],
              [3, 21, 22],
              [3, 22, 23],
              [3, 23, 24],
              [3, 24, 25],
              [3, 25, 4],

              [4, 25, 26],
              [4, 26, 27],
              [4, 27, 28],
              [4, 28, 29],
              [4, 29, 30],
              [4, 30, 31],
              [4, 31, 5],

              [5, 31, 32],
              [5, 32, 33],
              [5, 33, 34],
              [5, 34, 35],
              [5, 35, 36],
              [5, 36, 6],

              [6, 36, 37],
              [6, 37, 38],
              [6, 38, 39],
              [6, 39, 7],

              [7, 39, 40],
              [7, 40, 41],
              [7, 41, 42],
              [7, 42, 43],
              [7, 43, 8],

              [8, 43, 44],
              [8, 44, 45],
              [8, 45, 46],
              [8, 46, 47],
              [8, 47, 48],
              [8, 48, 49],
              [8, 49, 50],
              [8, 50, 51],
              [8, 51, 52],
              [8, 52, 9],
              ]
    for i in lookup:
        if flip:
            faces.append([offset + i[2], offset + i[1], offset + i[0]])
        else:
            faces.append([offset + i[0], offset + i[1], offset + i[2]])

    return faces


def create_torx_bit(point_distance, height):
    """
    Creates the 6 lobe indent in the top of the head.
    Note: This is an approximation to the Torx standard, scaled from T40.
    :param point_distance: (float) - Maximal lobe diameter.
    :param height: (float) - depth of the recess.
    :return: Verts and Faces: (lists) - making the recess and the diameter required in the bolt head.
             Diameter: (float) - Diameter of the Torx Bit consumed in the head.
    """
    verts = []
    faces = []

    point_radius = point_distance * 0.5
    outer_radius = point_radius * 1.05    # Add 5% to give space for mesh fill

    def do_curve(curve_height):
        """
        Builds the curve radius of the lobes
        :param curve_height: (float) - Z-axis of the returned verts
               Uses numerous variables from outside!
        :return: verts list is directly appended
        """
        point_1_y = point_radius * 0.816592592592593
        point_2_x = point_radius * 0.511111111111111
        point_2_y = point_radius * 0.885274074074074
        point_3_x = point_radius * 0.7072
        point_3_y = point_radius * 0.408296296296296
        point_4_x = point_radius * 1.02222222222222
        small_radius = point_radius * 0.183407407407407
        big_radius = point_radius * 0.333333333333333

        for i in range(0, 90, 10):
            x = sin(radians(i)) * small_radius
            y = cos(radians(i)) * small_radius
            verts.append([x, point_1_y + y, curve_height])

        for i in range(260, 150, -10):
            x = sin(radians(i)) * big_radius
            y = cos(radians(i)) * big_radius
            verts.append([point_2_x + x, point_2_y + y, curve_height])

        for i in range(340, 150 + 360, 10):
            x = sin(radians(i % 360)) * small_radius
            y = cos(radians(i % 360)) * small_radius
            verts.append([point_3_x + x, point_3_y + y, curve_height])

        for i in range(320, 260, -10):
            x = sin(radians(i)) * big_radius
            y = cos(radians(i)) * big_radius
            verts.append([point_4_x + x, y, curve_height])

    face_start_outside = len(verts)

    for deg in range(0, 100, 10):
        xxx = sin(radians(deg)) * outer_radius
        yyy = cos(radians(deg)) * outer_radius
        verts.append([xxx, yyy, 0])

    face_start_top_curve = len(verts)
    do_curve(0)
    faces.extend(torx_fill(face_start_outside, 0))

    face_start_bottom_curve = len(verts)
    do_curve(0 - height)
    faces.extend(build_face_list_quads(face_start_top_curve, 42, 1, True))

    verts.append([0, 0, 0 - height])        # add centre point for fill Fan
    faces.extend(fill_fan_face(face_start_bottom_curve, 44))

    m_verts, m_faces = mirror_verts_faces(verts, faces, 'x')
    verts.extend(m_verts)
    faces.extend(m_faces)

    m_verts, m_faces = mirror_verts_faces(verts, faces, 'y')
    verts.extend(m_verts)
    faces.extend(m_faces)

    return verts, faces, outer_radius * 2.0


# ####################################################################
#                    Create Phillips Bit
# ####################################################################

def phillips_fill(offset, flip=0):
    """
    This builds the triangles that make up the space between the top
    of the bit and the circle inscribed by top dit diameter.
    Also builds the faces making the drive tip.
    Implicit is DIV_COUNT=36 as this builds half the circle using 18 points.
    :param offset: (int) - starting index for the first vert of the face list.
    :param flip: (bool) - used to manage the surface normal direction.
    :return: list of faces.
    """
    faces = []
    lookup = [[0, 1, 10],
              [1, 11, 10],
              [1, 2, 11],
              [2, 12, 11],

              [2, 3, 12],
              [3, 4, 12],
              [4, 5, 12],
              [5, 6, 12],
              [6, 7, 12],

              [7, 13, 12],
              [7, 8, 13],
              [8, 14, 13],
              [8, 9, 14],

              [10, 11, 16, 15],
              [11, 12, 16],         # tip side
              [12, 13, 16],         # tip side
              [13, 14, 17, 16],
              [15, 16, 17, 18]      # tip point
              ]
    for i in lookup:
        if flip:
            if len(i) == 3:
                faces.append([offset + i[2], offset + i[1], offset + i[0]])
            else:
                faces.append([offset + i[3], offset + i[2], offset + i[1], offset + i[0]])
        else:
            if len(i) == 3:
                faces.append([offset + i[0], offset + i[1], offset + i[2]])
            else:
                faces.append([offset + i[0], offset + i[1], offset + i[2], offset + i[3]])
    return faces


def create_phillips_bit(props_in):
    """
    Creates the cross shaped indent in the top of the head.
    Explicit is div_count=36 as the returned boundary is a ring of 36 verts.
    :param props_in: (parameter) used for - bf_Philips_Bit_Dia, bf_Phillips_Bit_Depth
    :return: Verts (list) - mesh Verts.
             Faces (list) - mesh Faces.
             Diameter (float) - Diameter of the Phillips Bit consumed in the head.
    """
    verts = []
    faces = []

    div_count = 36
    flat_radius = props_in.bf_Philips_Bit_Dia * 0.5
    outer_radius = flat_radius * 1.05
    depth = props_in.bf_Phillips_Bit_Depth
    # Some magic numbers here to scale with width of the blade recess.
    flat_half = props_in.bf_Philips_Bit_Dia * (0.5 / 1.82) / 2.0

    face_start_outside = len(verts)
    deg_step = 360.0 / float(div_count)
    for iii in range(int(div_count / 4) + 1):   # only do a quarter and rotate later
        xxx = sin(radians(iii * deg_step)) * outer_radius
        yyy = cos(radians(iii * deg_step)) * outer_radius
        verts.append([xxx, yyy, 0])

    verts.append([0, flat_radius, 0])             # 10
    verts.append([flat_half, flat_radius, 0])     # 11
    verts.append([flat_half, flat_half, 0])       # 12
    verts.append([flat_radius, flat_half, 0])     # 13
    verts.append([flat_radius, 0, 0])             # 14

    verts.append([0, flat_half, 0 - depth])          # 15
    verts.append([flat_half, flat_half, 0 - depth])  # 16
    verts.append([flat_half, 0, 0 - depth])          # 17

    verts.append([0, 0, 0 - depth])            # 18

    faces.extend(phillips_fill(face_start_outside, True))

    s_verts, s_faces = spin_dup(verts, faces, 360, 4, 'z')

    return s_verts, s_faces, outer_radius * 2


# ####################################################################
#                    Create Head Types
# ## Pan Head
# ## Dome Head
# ## Counter Sink Head
# ## Cap Head
# ## Hex Head (now includes variable number of sides)
# ## 12 point (spline)
# ####################################################################

def max_pan_bit_dia(head_dia):
    """
    Used to limit the ring filled by hex bit in the top of the pan head.
    :param head_dia: (float) - Head diameter.
    :return: Diameter: (float) - Diameter available in the head for a bit.
    """
    head_radius = head_dia * 0.5
    x_rad = head_radius * 1.976              # Magic constant from create_pan_head()
    return (sin(radians(24)) * x_rad) * 2.0  # Set to be less than the top ellipse profile.


def create_pan_head(props_in, hole_dia):
    """
    Creates the mesh for a Pan Head. Construction uses two ellipse, the first with a large radius defines
    the top surface of the head. The second ellipse (actually a circle), defines the sides of the head.
    :param props_in: (parameter) used for - bf_Pan_Head_Dia, bf_Shank_Dia, bf_Div_Count
    :param hole_dia: (float) - the hole inscribed by the bit.
    :return: Head_Verts: (list) - Head mesh Verts.
             Head_Faces: (list) - Head mesh Faces.
             Head_Height: (float) - Height of the Head.
             washer_face_z: (float) - Underside surface of the head, accounts for bevel or radius.
    """

    hole_radius = hole_dia * 0.5
    head_radius = props_in.bf_Pan_Head_Dia * 0.5
    shank_radius = props_in.bf_Shank_Dia * 0.5
    shank_rad = props_in.bf_Pan_Head_Dia / 45.0

    verts = []
    row = 0

    x_rad = head_radius * 1.976
    z_rad = head_radius * 1.768 * 1.05   # additional 5% brings this coincident with end_rad for same x.
    end_rad = head_radius * 0.284
    end_z_offset = head_radius * 0.432
    height = head_radius * 0.59

    z = cos(asin(hole_radius / x_rad)) * z_rad            # calculate the z from the actual bit Hole size
    verts.append([hole_radius, 0.0, (0.0 - z_rad) + z])
    row += 1
    start_height = 0 - ((0.0 - z_rad) + z)

    for i in range(5, 25, 2):                           # Top ellipse
        x = sin(radians(i)) * x_rad
        z = cos(radians(i)) * z_rad
        if x > hole_radius:                             # Only add verts once larger than the bit hole
            verts.append([x, 0.0, (0.0 - z_rad) + z])
            row += 1

    for i in range(20, 140, 10):                        # Side ellipse (circle)
        x = sin(radians(i)) * end_rad
        z = cos(radians(i)) * end_rad
        if ((0.0 - end_z_offset) + z) < (0.0 - height):   # clamp to head height
            verts.append([(head_radius - end_rad) + x, 0.0, 0.0 - height])
        else:
            verts.append([(head_radius - end_rad) + x, 0.0, (0.0 - end_z_offset) + z])
        row += 1

    washer_face_z = start_height - height

    # for the bottom radius under the Head to the Shank. About 1/40 - 1/50 of the head diameter.
    for i in range(0, 100, 15):
        x = sin(radians(i)) * shank_rad
        z = cos(radians(i)) * shank_rad
        verts.append([(shank_radius + shank_rad) - x, 0.0, (0.0 - height - shank_rad) + z])
        row += 1

    s_verts, s_faces = spin_dup(verts, [], 360, props_in.bf_Div_Count, 'z')
    s_verts.extend(verts)  # add the start verts to the Spin verts to complete the loop

    s_faces.extend(build_face_list_quads(0, row - 1, props_in.bf_Div_Count))

    # Correct the returned height as being reduced by the hole using start_height and add the underside radius.
    head_height = height - start_height + shank_rad
    return move_verts_up_z(s_verts, start_height), s_faces, head_height, washer_face_z


def create_dome_head(props_in, hole_dia):
    """
    Creates the mesh for a Dome Head.
    :param props_in: (parameter) used for - bf_Dome_Head_Dia, bf_Shank_Dia, bf_Shank_Dia, bf_Div_Count
    :param hole_dia: (float) - the hole inscribed by the bit.
    :return: Head_Verts: (list) - Head mesh Verts.
             Head_Faces: (list) - Head mesh Faces.
             Head_Height: (float) - Height of the Head.
    """

    hole_radius = hole_dia * 0.5
    head_radius = props_in.bf_Dome_Head_Dia * 0.5
    shank_radius = props_in.bf_Shank_Dia * 0.5

    verts = []
    row = 0

    dome_rad = head_radius * 1.12
    rad_offset = head_radius * 0.98
    dome_height = head_radius * 0.64
    other_rad = head_radius * 0.16
    other_rad_x_offset = head_radius * 0.84
    other_rad_z_offset = head_radius * 0.504

    verts.append([hole_radius, 0.0, 0.0])
    row += 1

    for i in range(0, 60, 10):
        x = sin(radians(i)) * dome_rad
        z = cos(radians(i)) * dome_rad
        if ((0.0 - rad_offset) + z) <= 0:
            verts.append([x, 0.0, (0.0 - rad_offset) + z])
            row += 1

    for i in range(60, 160, 10):
        x = sin(radians(i)) * other_rad
        z = cos(radians(i)) * other_rad
        z = (0.0 - other_rad_z_offset) + z
        if z < 0.0 - dome_height:
            z = 0.0 - dome_height
        verts.append([other_rad_x_offset + x, 0.0, z])
        row += 1

    verts.append([shank_radius, 0.0, (0.0 - dome_height)])
    row += 1

    s_verts, s_faces = spin_dup(verts, [], 360, props_in.bf_Div_Count, 'z')
    s_verts.extend(verts)   # add the start verts to the Spin verts to complete the loop

    s_faces.extend(build_face_list_quads(0, row - 1, props_in.bf_Div_Count))

    return s_verts, s_faces, dome_height


def create_counter_sink_head(props_in, hole_dia):
    """
    Creates the mesh for a Counter Sink Head.
    :param props_in: (parameter) used for - bf_CounterSink_Head_Dia, bf_Shank_Dia, bf_CounterSink_Head_Angle,
                                            bf_Div_Count
    :param hole_dia: (float) - the hole inscribed by the bit.
    :return: Head_Verts: (list) - Head mesh Verts.
             Head_Faces: (list) - Head mesh Faces.
             Head_Height: (float) - Height of the Head.
    """

    hole_radius = hole_dia * 0.5                            # the hole inscribed by the bit.
    head_radius = props_in.bf_CounterSink_Head_Dia * 0.5
    shank_radius = props_in.bf_Shank_Dia * 0.5
    rad1 = props_in.bf_CounterSink_Head_Dia * (0.09 / 6.31)    # Top rounding to the head.

    verts = []
    row = 0

    # As per ISO 10642 the angle of the head is not constant with nominal diameter.
    # Between 20 and 22mm shank the head angle changes 90 to 60.
    height = tan((1.5708 - props_in.bf_CounterSink_Head_Angle / 2.0)) * (head_radius - shank_radius) + rad1

    verts.append([hole_radius, 0.0, 0.0])
    row += 1

    # Top radius of the head.
    for i in range(0, 100, 10):
        x = sin(radians(i)) * rad1
        z = cos(radians(i)) * rad1
        verts.append([(head_radius - rad1) + x, 0.0, (0.0 - rad1) + z])
        row += 1

    verts.append([shank_radius, 0.0, 0.0 - height])
    row += 1

    s_verts, s_faces = spin_dup(verts, [], 360, props_in.bf_Div_Count, 'z')
    s_verts.extend(verts)    # add the start verts to the Spin verts to complete the loop

    s_faces.extend(build_face_list_quads(0, row - 1, props_in.bf_Div_Count))

    return s_verts, s_faces, height


def create_cap_head(props_in, hole_dia):
    """
    Creates the mesh for a Cap Head.
    :param props_in: (parameter) used for - bf_Cap_Head_Dia, bf_Shank_Dia, bf_Cap_Head_Height, bf_Div_Count
    :param hole_dia: (float) - the hole inscribed by the bit.
    :return: Head_Verts: (list) - Head mesh Verts.
             Head_Faces: (list) - Head mesh Faces.
             Head_Height: (float) - Height of the Head.
             washer_face_z: (float) - Underside surface of the head, accounts for bevel or radius.
    """
    hole_radius = hole_dia * 0.5
    head_radius = props_in.bf_Cap_Head_Dia * 0.5
    shank_radius = props_in.bf_Shank_Dia * 0.5
    rad1 = props_in.bf_Cap_Head_Dia * (1.0 / 19.0)         # Top radius of the head.
    rad2 = props_in.bf_Cap_Head_Dia * (1.0 / 19.0)         # Bottom radius under the head to the shank.
    height = props_in.bf_Cap_Head_Height

    verts = []
    row = 0
    bevel = height * 0.01

    verts.append([hole_radius, 0.0, 0.0])
    row += 1

    # Top radius of the head.
    for i in range(0, 100, 10):
        x = sin(radians(i)) * rad1
        z = cos(radians(i)) * rad1
        verts.append([(head_radius - rad1) + x, 0.0, (0.0 - rad1) + z])
        row += 1

    verts.append([head_radius, 0.0, 0.0 - height + bevel])
    row += 1

    verts.append([head_radius - bevel, 0.0, 0.0 - height])
    row += 1

    washer_face_z = -height

    # Bottom radius under the head to the shank.
    for i in range(0, 100, 10):
        x = sin(radians(i)) * rad2
        z = cos(radians(i)) * rad2
        verts.append([(shank_radius + rad2) - x, 0.0, (0.0 - height - rad2) + z])
        row += 1

    s_verts, s_faces = spin_dup(verts, [], 360, props_in.bf_Div_Count, 'z')
    s_verts.extend(verts)    # add the start verts to the Spin verts to complete the loop

    s_faces.extend(build_face_list_quads(0, row - 1, props_in.bf_Div_Count))

    return s_verts, s_faces, height + rad2, washer_face_z


def create_hex_head(props_in, hole_dia):
    """
    Creates the mesh for a Hex Head if bf_N_Sided is set to 6.
    :param props_in: (parameter) used for - bf_Hex_Head_Flat_Distance, bf_Shank_Dia, bf_Hex_Head_Height
    :param hole_dia: (float) - the hole inscribed by the bit.
    :return: Head_Verts: (list) - Head mesh Verts.
             Head_Faces: (list) - Head mesh Faces.
             Head_Height: (float) - Updated Height of the Head.
             washer_face_z: (float) - Underside surface of the head, accounts for bevel or radius.
    """

    hole_radius = hole_dia * 0.5
    half_flat = props_in.bf_Hex_Head_Flat_Distance / 2
    top_bevel_radius = half_flat - (half_flat * (0.05 / 8))
    undercut_height = half_flat * (0.05 / 8)
    shank_bevel = half_flat * (0.05 / 8)
    shank_radius = props_in.bf_Shank_Dia / 2
    height = props_in.bf_Hex_Head_Height
    flat_height = height - undercut_height
    washer_face_z = -height + undercut_height - shank_bevel
    n_sides = props_in.bf_N_Sided

    verts = []
    faces = []

    # For a hex this will build 1/6th of the head, i.e. 60 degrees, at the end rotate using spin_dup.
    # Functional construction is to build a sector of 1/6th of the hex head working down the z in slices.
    # Heads of N sides are created by building one Nth (a side) of the nut before rotation.

    # This is in preparation for div_count being variable in the future.
    deg_step = np.linspace(-180/n_sides, 180/n_sides, (props_in.bf_Div_Count+n_sides)//n_sides)
    # deg_step = range(-30, 31, 10)              # For the original hex implementation
    angle_rad = [radians(i) for i in deg_step]   # degrees are not needed in the function convert to radians once

    # inner hole
    for theta in angle_rad:
        verts.append([sin(theta) * hole_radius, cos(theta) * hole_radius, 0.0])

    # bevel
    vect = []        # Empty vector holder
    for theta in angle_rad:
        verts.append([sin(theta) * top_bevel_radius, cos(theta) * top_bevel_radius, 0.0])
        vect.append(Vector([sin(theta) * top_bevel_radius, cos(theta) * top_bevel_radius, 0.0]))

    # Flats
    z_bevel_min = 0     # Lint does not believe that the for loop will always run, if referenced before assignment.
    for theta, vec in zip(angle_rad, vect):
        x = tan(theta) * half_flat
        d_vec = vec - Vector([x, half_flat, 0.0])
        z_bevel_min = d_vec.length * tan(radians(min(45, 5 * n_sides)))
        # Angle was 45. ISO specs for hex is about 30 degrees. Coach bolt, 4 sides, is 20 degrees.
        verts.append([x, half_flat, -z_bevel_min])

    # Clean up situations where the bevel is deeper than the requested available height.
    if z_bevel_min >= flat_height:
        # Re-determine the new height and correct the returned offset of the washer face.
        height = z_bevel_min + undercut_height
        washer_face_z = -height + undercut_height - shank_bevel
        flat_height = max(flat_height, z_bevel_min)

    # down Bits
    for theta in angle_rad:
        verts.append([tan(theta) * half_flat, half_flat, -flat_height])

    # Undercut, re-using the top_bevel_radius
    for theta in angle_rad:
        verts.append([sin(theta) * top_bevel_radius, cos(theta) * top_bevel_radius, -flat_height])

    # washer face
    for theta in angle_rad:
        verts.append([sin(theta) * top_bevel_radius, cos(theta) * top_bevel_radius, -flat_height - undercut_height])

    # washer face to Shank BEVEL
    for theta in angle_rad:
        verts.append([sin(theta) * (shank_radius + shank_bevel),
                      cos(theta) * (shank_radius + shank_bevel),
                      -flat_height - undercut_height])

    # Shank BEVEL
    for theta in angle_rad:
        verts.append([sin(theta) * shank_radius,
                      cos(theta) * shank_radius,
                      -flat_height - undercut_height - shank_bevel])

    # faces.extend(build_face_list_quads(face_start, len(angle_rad) - 1, row - 1))
    faces.extend(build_face_list_quads(0, len(angle_rad) - 1, len(verts)//len(angle_rad) - 1))

    rot_mat = simple_rotation_matrix(180/n_sides - 90, 'z')      # rotation to align point onto x-axis
    verts_r = rot_mesh(verts, rot_mat)

    s_verts, s_faces = spin_dup(verts_r, faces, 360, n_sides, 'z')

    return s_verts, s_faces, (height + shank_bevel), washer_face_z


def create_12_point(flat, hole_dia, shank_dia, height, flange_dia):
    """
    Creates the mesh of the 12 Point - used for both the Nut and Bolt Head.
    This is a bi-hex implementation rather than a tri-square.
    :param flat: (float) - Distance across flats (measured if hexagonal).
    :param hole_dia: (float) - Top side for either internal thread or driver bit.
    :param shank_dia: (float) - Bottom side either for the internal thread or shank of external thread.
    :param height: (float) - Height of the nut/bolt.
    :param flange_dia: (float) - Diameter of the flange.
    :return: Verts: (list) - mesh Verts.
             Faces: (list) - mesh Faces.
             Height: (float) - Z-axis height of the nut/bolt.
    """

    flange_height = (1.89 / 8.0) * height
    flat_height = (4.18 / 8.0) * height

    flange_radius = flange_dia * 0.5
    flange_tapper_height = height - flange_height - flat_height

    verts = []
    faces = []
    hole_radius = hole_dia / 2
    half_flat = flat / 2
    top_bevel_radius = half_flat - (half_flat * (0.05 / 8))

    shank_radius = shank_dia / 2
    row = 0

    face_start = len(verts)

    # inner hole
    x = sin(radians(0)) * hole_radius
    y = cos(radians(0)) * hole_radius
    verts.append([x, y, 0.0])
    # Vert duplication required to map DIV_COUNT = 36 as sides use 72 points.
    verts.append([x, y, 0.0])

    x = sin(radians(10)) * hole_radius
    y = cos(radians(10)) * hole_radius
    verts.append([x, y, 0.0])
    # Vert duplication required to map DIV_COUNT = 36 as sides use 72 points.
    verts.append([x, y, 0.0])

    x = sin(radians(20)) * hole_radius
    y = cos(radians(20)) * hole_radius
    verts.append([x, y, 0.0])
    # Vert duplication required to map DIV_COUNT = 36 as sides use 72 points.
    verts.append([x, y, 0.0])

    x = sin(radians(30)) * hole_radius
    y = cos(radians(30)) * hole_radius
    verts.append([x, y, 0.0])

    row += 1

    # bevel
    x = sin(radians(0)) * top_bevel_radius
    y = cos(radians(0)) * top_bevel_radius
    vec1 = Vector([x, y, 0.0])
    verts.append([x, y, 0.0])

    x = sin(radians(5)) * top_bevel_radius
    y = cos(radians(5)) * top_bevel_radius
    vec2 = Vector([x, y, 0.0])
    verts.append([x, y, 0.0])

    x = sin(radians(10)) * top_bevel_radius
    y = cos(radians(10)) * top_bevel_radius
    vec3 = Vector([x, y, 0.0])
    verts.append([x, y, 0.0])

    x = sin(radians(15)) * top_bevel_radius
    y = cos(radians(15)) * top_bevel_radius
    vec4 = Vector([x, y, 0.0])
    verts.append([x, y, 0.0])

    x = sin(radians(20)) * top_bevel_radius
    y = cos(radians(20)) * top_bevel_radius
    vec5 = Vector([x, y, 0.0])
    verts.append([x, y, 0.0])

    x = sin(radians(25)) * top_bevel_radius
    y = cos(radians(25)) * top_bevel_radius
    vec6 = Vector([x, y, 0.0])
    verts.append([x, y, 0.0])

    x = sin(radians(30)) * top_bevel_radius
    y = cos(radians(30)) * top_bevel_radius
    vec7 = Vector([x, y, 0.0])
    verts.append([x, y, 0.0])

    row += 1

    # 45Deg bevel on the top

    # First we work out how far up the Y axis the vert is
    v_origin = Vector([0.0, 0.0, 0.0])  # center of the model
    v_15_deg_point = Vector([tan(radians(15)) * half_flat, half_flat, 0.0])  # Is a know point to work back from

    x = tan(radians(0)) * half_flat
    point_distance = (tan(radians(30)) * v_15_deg_point.x) + half_flat
    dvec = vec1 - Vector([x, point_distance, 0.0])
    verts.append([x, point_distance, -dvec.length])
    v_0_deg_top_point = Vector([x, point_distance, -dvec.length])

    v_0_deg_point = Vector([x, point_distance, 0.0])

    v_5_deg_line = Vector([tan(radians(5)) * half_flat, half_flat, 0.0])
    v_5_deg_line.length *= 2  # extend out the line on a 5 deg angle

    # We cross 2 lines. One from the origin to the 0 Deg point
    # and the second is from the origin extended out past the first line
    # This gives the cross point of the
    v_cross = geometry.intersect_line_line_2d(v_0_deg_point, v_15_deg_point, v_origin, v_5_deg_line)
    dvec = vec2 - Vector([v_cross.x, v_cross.y, 0.0])
    verts.append([v_cross.x, v_cross.y, -dvec.length])
    v_5_deg_top_point = Vector([v_cross.x, v_cross.y, -dvec.length])

    v_10_deg_line = Vector([tan(radians(10)) * half_flat, half_flat, 0.0])
    v_10_deg_line.length *= 2  # extend out the line

    v_cross = geometry.intersect_line_line_2d(v_0_deg_point, v_15_deg_point, v_origin, v_10_deg_line)
    dvec = vec3 - Vector([v_cross.x, v_cross.y, 0.0])
    verts.append([v_cross.x, v_cross.y, -dvec.length])
    v_10_deg_top_point = Vector([v_cross.x, v_cross.y, -dvec.length])

    # The remaining points are straight forward because y is all the same y height (half_flat)
    x = tan(radians(15)) * half_flat
    dvec = vec4 - Vector([x, half_flat, 0.0])
    verts.append([x, half_flat, -dvec.length])
    v_15_deg_top_point = Vector([x, half_flat, -dvec.length])

    x = tan(radians(20)) * half_flat
    dvec = vec5 - Vector([x, half_flat, 0.0])
    verts.append([x, half_flat, -dvec.length])
    v_20_deg_top_point = Vector([x, half_flat, -dvec.length])

    x = tan(radians(25)) * half_flat
    dvec = vec6 - Vector([x, half_flat, 0.0])
    verts.append([x, half_flat, -dvec.length])
    v_25_deg_top_point = Vector([x, half_flat, -dvec.length])

    x = tan(radians(30)) * half_flat
    dvec = vec7 - Vector([x, half_flat, 0.0])
    verts.append([x, half_flat, -dvec.length])
    v_30_deg_top_point = Vector([x, half_flat, -dvec.length])
    row += 1

    # Down Bits
    flange_adjacent = flange_radius - point_distance
    if flange_adjacent == 0.0:
        flange_adjacent = 0.000001
    flange_opposite = flange_tapper_height

    flange_angle_rad = atan(flange_opposite / flange_adjacent)
    v_extended_flange_edge = Vector([0.0, 0.0, -height + flange_height + (tan(flange_angle_rad) * flange_radius)])

    # 0deg
    v_flange_edge = Vector([sin(radians(0)) * flange_radius, cos(radians(0)) * flange_radius, -height + flange_height])
    v_cross = geometry.intersect_line_line(v_0_deg_top_point, Vector(
        [v_0_deg_top_point.x, v_0_deg_top_point.y, -height]), v_flange_edge, v_extended_flange_edge)
    verts.append(v_cross[0])

    # 5deg
    v_flange_edge = Vector([sin(radians(5)) * flange_radius, cos(radians(5)) * flange_radius, -height + flange_height])
    v_cross = geometry.intersect_line_line(v_5_deg_top_point, Vector(
        [v_5_deg_top_point.x, v_5_deg_top_point.y, -height]), v_flange_edge, v_extended_flange_edge)
    verts.append(v_cross[0])

    # 10deg
    v_flange_edge = Vector([sin(radians(10)) * flange_radius, cos(radians(10))
                            * flange_radius, -height + flange_height])
    v_cross = geometry.intersect_line_line(v_10_deg_top_point, Vector(
        [v_10_deg_top_point.x, v_10_deg_top_point.y, -height]), v_flange_edge, v_extended_flange_edge)
    verts.append(v_cross[0])

    # 15deg
    v_flange_edge = Vector([sin(radians(15)) * flange_radius, cos(radians(15))
                            * flange_radius, -height + flange_height])
    v_cross = geometry.intersect_line_line(v_15_deg_top_point, Vector(
        [v_15_deg_top_point.x, v_15_deg_top_point.y, -height]), v_flange_edge, v_extended_flange_edge)
    verts.append(v_cross[0])

    # 20deg
    v_flange_edge = Vector([sin(radians(20)) * flange_radius, cos(radians(20))
                            * flange_radius, -height + flange_height])
    v_cross = geometry.intersect_line_line(v_20_deg_top_point, Vector(
        [v_20_deg_top_point.x, v_20_deg_top_point.y, -height]), v_flange_edge, v_extended_flange_edge)
    verts.append(v_cross[0])

    # 25deg
    v_flange_edge = Vector([sin(radians(25)) * flange_radius, cos(radians(25))
                            * flange_radius, -height + flange_height])
    v_cross = geometry.intersect_line_line(v_25_deg_top_point, Vector(
        [v_25_deg_top_point.x, v_25_deg_top_point.y, -height]), v_flange_edge, v_extended_flange_edge)
    verts.append(v_cross[0])

    # 30deg
    v_flange_edge = Vector([sin(radians(30)) * flange_radius, cos(radians(30))
                            * flange_radius, -height + flange_height])
    v_cross = geometry.intersect_line_line(v_30_deg_top_point, Vector(
        [v_30_deg_top_point.x, v_30_deg_top_point.y, -height]), v_flange_edge, v_extended_flange_edge)
    verts.append(v_cross[0])

    row += 1

    verts.append([sin(radians(0)) * flange_radius, cos(radians(0)) * flange_radius, -height + flange_height])
    verts.append([sin(radians(5)) * flange_radius, cos(radians(5)) * flange_radius, -height + flange_height])
    verts.append([sin(radians(10)) * flange_radius, cos(radians(10)) * flange_radius, -height + flange_height])
    verts.append([sin(radians(15)) * flange_radius, cos(radians(15)) * flange_radius, -height + flange_height])
    verts.append([sin(radians(20)) * flange_radius, cos(radians(20)) * flange_radius, -height + flange_height])
    verts.append([sin(radians(25)) * flange_radius, cos(radians(25)) * flange_radius, -height + flange_height])
    verts.append([sin(radians(30)) * flange_radius, cos(radians(30)) * flange_radius, -height + flange_height])

    row += 1

    verts.append([sin(radians(0)) * flange_radius, cos(radians(0)) * flange_radius, -height])
    verts.append([sin(radians(5)) * flange_radius, cos(radians(5)) * flange_radius, -height])
    verts.append([sin(radians(10)) * flange_radius, cos(radians(10)) * flange_radius, -height])
    verts.append([sin(radians(15)) * flange_radius, cos(radians(15)) * flange_radius, -height])
    verts.append([sin(radians(20)) * flange_radius, cos(radians(20)) * flange_radius, -height])
    verts.append([sin(radians(25)) * flange_radius, cos(radians(25)) * flange_radius, -height])
    verts.append([sin(radians(30)) * flange_radius, cos(radians(30)) * flange_radius, -height])

    row += 1

    # Duplication of verts forces a divide by 2 of the 72 points to mate with the DIV COUNT=36
    verts.append([sin(radians(0)) * shank_radius, cos(radians(0)) * shank_radius, -height])
    verts.append([sin(radians(0)) * shank_radius, cos(radians(0)) * shank_radius, -height])
    verts.append([sin(radians(10)) * shank_radius, cos(radians(10)) * shank_radius, -height])
    verts.append([sin(radians(10)) * shank_radius, cos(radians(10)) * shank_radius, -height])
    verts.append([sin(radians(20)) * shank_radius, cos(radians(20)) * shank_radius, -height])
    verts.append([sin(radians(20)) * shank_radius, cos(radians(20)) * shank_radius, -height])
    verts.append([sin(radians(30)) * shank_radius, cos(radians(30)) * shank_radius, -height])

    row += 1

    faces.extend(build_face_list_quads(face_start, 6, row - 1))

    s_verts, s_faces = spin_dup(verts, faces, 360, 12, 'z')

    return s_verts, s_faces, 0 - (-height)


def create_12_point_head(flat, hole_dia, shank_dia, height, flange_dia):
    """
    Creates the mesh of the 12 Point Head. Calls create_12_point().
    :param flat: (float) - Distance across flats (measured if hexagonal).
    :param hole_dia: (float) - Top side for either internal thread or driver bit.
    :param shank_dia: (float) - Bottom side either for the internal thread or shank of external thread.
    :param height: (float) - Height of the nut/bolt.
    :param flange_dia: (float) - Diameter of the flange.
    :return: Verts: (list) - mesh Verts.
             Faces: (list) - mesh Faces.
             Height: (float) - Z-axis height of the nut/bolt.
    """
    # under head radius ?
    return create_12_point(flat, hole_dia, shank_dia, height, flange_dia)


# ####################################################################
#                    Create External Thread
# ## create_shank_verts()
# ## create_thread_start_verts()
# ## create_thread_verts()
# ## create_thread_end_verts()
# ## create_external_thread() - Entry point: Uses the 4 functions above
# ####################################################################

def create_shank_verts(props_in, length, height_offset):
    """
    Creates the non-thread portion of the bolt between the Thread Start and the Head.
    :param props_in: (parameter) used for - bf_Shank_Dia, bf_Major_Dia, bf_Div_Count
    :param length: (float) - The required length of the Shank.
    :param height_offset: (float) - Z-axis start point.
    :return: Verts: (list) - Mesh Verts.
             Ret_Row: (int) - Number of points/rows added in the verts list.
             height_offset: (float) - Actual length of the Shank.
    """
    verts = []
    div_count = props_in.bf_Div_Count

    start_radius = props_in.bf_Shank_Dia / 2
    outer_radius = props_in.bf_Major_Dia / 2

    opp = abs(start_radius - outer_radius)
    taper_length = opp / tan(radians(31))

    if taper_length > length:
        taper_length = 0

    straight_length = length - taper_length

    deg_step = 360.0 / div_count

    row = 0
    lowest_z_vert = 0

    # Ring
    for i in range(div_count + 1):
        x = sin(radians(i * deg_step)) * start_radius
        y = cos(radians(i * deg_step)) * start_radius
        z = height_offset
        verts.append([x, y, z])
        lowest_z_vert = min(lowest_z_vert, z)
    height_offset -= straight_length
    row += 1

    for i in range(div_count + 1):
        x = sin(radians(i * deg_step)) * start_radius
        y = cos(radians(i * deg_step)) * start_radius
        z = height_offset
        verts.append([x, y, z])
        lowest_z_vert = min(lowest_z_vert, z)
    height_offset -= taper_length
    row += 1

    return verts, row, height_offset


def create_thread_start_verts(props_in, height_offset):
    """
    Creates the lead in portion of the bolt between the Thread and the Shank.
    :param props_in: (parameter) used for - bf_Minor_Dia, bf_Major_Dia, bf_Pitch, bf_Crest_Percent,
                                            bf_Root_Percent, bf_Div_Count, bf_Thread_Root_Type, bf_Rounded_Root_Dia
    :param height_offset: (float) - Z-axis start point.
    :return: Verts: (list) - Mesh Verts.
             Ret_Row: (int) - Number of points/rows added in the verts list.
             height_offset: (float) - Actual length of the Thread Starting.
    """
    verts = []

    inner_radius = props_in.bf_Minor_Dia / 2
    outer_radius = props_in.bf_Major_Dia / 2
    pitch = props_in.bf_Pitch                               # Thread distance progressed with each revolution.
    div_count = props_in.bf_Div_Count                       # Number of steps used to model each revolution.
    thread_root_type = props_in.bf_Thread_Root_Type         # The shape of the root, 'FLAT' or 'TRIANGLE'.
    root_inner_dia = props_in.bf_Rounded_Root_Dia           # Diameter of the thread root at the bottom ISO724:2003.

    deg_step = 360.0 / div_count
    height_step = pitch / div_count

    row = 0
    lowest_z_vert = 0
    height_start = height_offset

    crest_height = pitch * props_in.bf_Crest_Percent / 100.0
    root_height = pitch * props_in.bf_Root_Percent / 100.0
    root_to_crest_height = crest_to_root_height = (pitch - (crest_height + root_height)) / 2.0

    rank = (outer_radius - inner_radius) / div_count
    cut_off = height_offset
    height_offset = height_offset + pitch

    for _j in range(1):
        # Crest
        for i in range(div_count + 1):
            x = sin(radians(i * deg_step)) * outer_radius
            y = cos(radians(i * deg_step)) * outer_radius
            z = height_offset - (height_step * i)
            if z > cut_off:
                z = cut_off
            verts.append([x, y, z])
            lowest_z_vert = min(lowest_z_vert, z)
        height_offset -= crest_height
        row += 1

        # Flank down
        for i in range(div_count + 1):
            x = sin(radians(i * deg_step)) * outer_radius
            y = cos(radians(i * deg_step)) * outer_radius
            z = height_offset - (height_step * i)
            if z > cut_off:
                z = cut_off
            verts.append([x, y, z])
            lowest_z_vert = min(lowest_z_vert, z)
        height_offset -= crest_to_root_height
        row += 1

        if thread_root_type == 'TRIANGLE':
            root_min = root_inner_dia / 2               # Lint claims this is not used????
            # Top of V-Root
            for i in range(div_count + 1):
                x = sin(radians(i * deg_step)) * outer_radius
                y = cos(radians(i * deg_step)) * outer_radius
                z = height_offset - (height_step * i)
                if z > cut_off:
                    z = cut_off
                verts.append([x, y, z])
                lowest_z_vert = min(lowest_z_vert, z)
            height_offset -= root_height / 2
            row += 1
            # Bottom of V-Root
            for i in range(div_count + 1):
                x = sin(radians(i * deg_step)) * outer_radius
                y = cos(radians(i * deg_step)) * outer_radius
                z = height_offset - (height_step * i)
                if z > cut_off:
                    z = cut_off
                verts.append([x, y, z])
                lowest_z_vert = min(lowest_z_vert, z)
            height_offset -= root_height / 2
            row += 1
        else:  # FLAT root logic
            for i in range(div_count + 1):
                x = sin(radians(i * deg_step)) * outer_radius
                y = cos(radians(i * deg_step)) * outer_radius
                z = height_offset - (height_step * i)
                if z > cut_off:
                    z = cut_off
                verts.append([x, y, z])
                lowest_z_vert = min(lowest_z_vert, z)
            height_offset -= root_height
            row += 1

        # Flank up
        for i in range(div_count + 1):
            x = sin(radians(i * deg_step)) * outer_radius
            y = cos(radians(i * deg_step)) * outer_radius
            z = height_offset - (height_step * i)
            if z > cut_off:
                z = cut_off
            verts.append([x, y, z])
            lowest_z_vert = min(lowest_z_vert, z)
        height_offset -= root_to_crest_height
        row += 1

    # This loop is for the tapered start of the thread
    for j in range(2):
        # Crest
        for i in range(div_count + 1):
            z = height_offset - (height_step * i)
            if z > height_start:
                z = height_start
            x = sin(radians(i * deg_step)) * outer_radius
            y = cos(radians(i * deg_step)) * outer_radius
            verts.append([x, y, z])
            lowest_z_vert = min(lowest_z_vert, z)
        height_offset -= crest_height
        row += 1

        # Flank down
        for i in range(div_count + 1):
            z = height_offset - (height_step * i)
            if z > height_start:
                z = height_start
            x = sin(radians(i * deg_step)) * outer_radius
            y = cos(radians(i * deg_step)) * outer_radius
            verts.append([x, y, z])
            lowest_z_vert = min(lowest_z_vert, z)
        height_offset -= crest_to_root_height
        row += 1

        # Conditional Root Generation
        if thread_root_type == 'TRIANGLE':
            root_min = root_inner_dia / 2
            root_rank = (outer_radius - root_min) / div_count
            # Top of V-Root (tapered)
            for i in range(div_count + 1):
                z = height_offset - (height_step * i)
                if z > height_start:
                    z = height_start
                x = sin(radians(i * deg_step)) * inner_radius
                y = cos(radians(i * deg_step)) * inner_radius
                if j == 0:
                    x = sin(radians(i * deg_step)) * (outer_radius - (i * rank))
                    y = cos(radians(i * deg_step)) * (outer_radius - (i * rank))
                verts.append([x, y, z])
                lowest_z_vert = min(lowest_z_vert, z)
            height_offset -= root_height / 2
            row += 1
            # Bottom of V-Root (tapered)
            for i in range(div_count + 1):
                z = height_offset - (height_step * i)
                if z > height_start:
                    z = height_start
                x = sin(radians(i * deg_step)) * root_min
                y = cos(radians(i * deg_step)) * root_min
                if j == 0:
                    x = sin(radians(i * deg_step)) * (outer_radius - (i * root_rank))
                    y = cos(radians(i * deg_step)) * (outer_radius - (i * root_rank))
                verts.append([x, y, z])
                lowest_z_vert = min(lowest_z_vert, z)
            height_offset -= root_height / 2
            row += 1
        else:  # FLAT root logic (tapered)
            for i in range(div_count + 1):
                z = height_offset - (height_step * i)
                if z > height_start:
                    z = height_start
                x = sin(radians(i * deg_step)) * inner_radius
                y = cos(radians(i * deg_step)) * inner_radius
                if j == 0:
                    x = sin(radians(i * deg_step)) * (outer_radius - (i * rank))
                    y = cos(radians(i * deg_step)) * (outer_radius - (i * rank))
                verts.append([x, y, z])
                lowest_z_vert = min(lowest_z_vert, z)
            height_offset -= root_height
            row += 1

        # Flank up
        for i in range(div_count + 1):
            z = height_offset - (height_step * i)
            if z > height_start:
                z = height_start
            x = sin(radians(i * deg_step)) * inner_radius
            y = cos(radians(i * deg_step)) * inner_radius
            if j == 0:
                x = sin(radians(i * deg_step)) * (outer_radius - (i * rank))
                y = cos(radians(i * deg_step)) * (outer_radius - (i * rank))
            verts.append([x, y, z])
            lowest_z_vert = min(lowest_z_vert, z)
        height_offset -= root_to_crest_height
        row += 1

    return verts, row, height_offset


def create_thread_verts(props_in, height, height_offset):
    """
    Creates the Thread portion of the bolt between the Thread End and the Thread Start.
    :param props_in: (parameter) used for - bf_Minor_Dia, bf_Major_Dia, bf_Pitch, bf_Crest_Percent,
                                            bf_Root_Percent, bf_Div_Count, bf_Thread_Root_Type, bf_Rounded_Root_Dia
    :param height: (float) - Requested length of the Thread Rounded DOWN by nearest complete revolution.
    :param height_offset: (float) - Z-axis start point.
    :return: Verts: (list) - mesh Verts.
             Ret_Row: (int) - number of points/rows added in the verts list.
             height_offset: (float) - actual length of the Thread.
    """
    verts = []

    inner_radius = props_in.bf_Minor_Dia / 2
    outer_radius = props_in.bf_Major_Dia / 2
    pitch = props_in.bf_Pitch                               # Thread distance progressed with each revolution.
    div_count = props_in.bf_Div_Count                       # Number of steps used to model each revolution.
    thread_root_type = props_in.bf_Thread_Root_Type         # The shape of the root, 'FLAT' or 'TRIANGLE'.
    root_inner_dia = props_in.bf_Rounded_Root_Dia           # Diameter of the thread root at the bottom ISO724:2003.

    deg_step = 360.0 / div_count
    height_step = pitch / div_count

    num_of_start_threads = 2.0
    num_of_end_threads = 3.0
    # The int() cast is necessary here to ensure 'num' is an integer for the range() function.
    num = int((height - ((num_of_start_threads * pitch) + (num_of_end_threads * pitch))) / pitch)
    row = 0

    crest_height = pitch * props_in.bf_Crest_Percent / 100.0
    root_height = pitch * props_in.bf_Root_Percent / 100.0
    root_to_crest_height = crest_to_root_height = (pitch - (crest_height + root_height)) / 2.0

    lowest_z_vert = 0

    for _j in range(num):
        # Crest
        for i in range(div_count + 1):
            x = sin(radians(i * deg_step)) * outer_radius
            y = cos(radians(i * deg_step)) * outer_radius
            z = height_offset - (height_step * i)
            verts.append([x, y, z])
            lowest_z_vert = min(lowest_z_vert, z)
        height_offset -= crest_height
        row += 1

        # Flank down
        for i in range(div_count + 1):
            x = sin(radians(i * deg_step)) * outer_radius
            y = cos(radians(i * deg_step)) * outer_radius
            z = height_offset - (height_step * i)
            verts.append([x, y, z])
            lowest_z_vert = min(lowest_z_vert, z)
        height_offset -= crest_to_root_height
        row += 1

        # Conditional Root Generation
        if thread_root_type == 'TRIANGLE':
            root_min = root_inner_dia / 2
            # Top of V-Root
            for i in range(div_count + 1):
                x = sin(radians(i * deg_step)) * inner_radius
                y = cos(radians(i * deg_step)) * inner_radius
                z = height_offset - (height_step * i)
                verts.append([x, y, z])
                lowest_z_vert = min(lowest_z_vert, z)
            height_offset -= root_height / 2
            row += 1
            # Bottom of V-Root
            for i in range(div_count + 1):
                x = sin(radians(i * deg_step)) * root_min
                y = cos(radians(i * deg_step)) * root_min
                z = height_offset - (height_step * i)
                verts.append([x, y, z])
                lowest_z_vert = min(lowest_z_vert, z)
            height_offset -= root_height / 2
            row += 1
        else:  # FLAT root logic
            for i in range(div_count + 1):
                x = sin(radians(i * deg_step)) * inner_radius
                y = cos(radians(i * deg_step)) * inner_radius
                z = height_offset - (height_step * i)
                verts.append([x, y, z])
                lowest_z_vert = min(lowest_z_vert, z)
            height_offset -= root_height
            row += 1

        # Flank up
        for i in range(div_count + 1):
            x = sin(radians(i * deg_step)) * inner_radius
            y = cos(radians(i * deg_step)) * inner_radius
            z = height_offset - (height_step * i)
            verts.append([x, y, z])
            lowest_z_vert = min(lowest_z_vert, z)
        height_offset -= root_to_crest_height
        row += 1

    return verts, row, height_offset


def create_thread_end_verts(props_in, height_offset):
    """
    Creates the Thread End (tip) portion of the bolt joining to the main Thread.
    :param props_in: (parameter) used for - bf_Minor_Dia, bf_Major_Dia, bf_Pitch, bf_Crest_Percent,
                                            bf_Root_Percent, bf_Div_Count, bf_Thread_Root_Type, bf_Rounded_Root_Dia
    :param height_offset: (float) - Z-axis start point.
    :return: Verts: (list) - mesh Verts.
             Ret_Row: (int) - number of points/rows added in the verts list.
             height_offset: (float) - actual length of the Thread Ending.
             lowest_z_vert: (float) - Minimum Z-axis vertex created.
    """
    verts = []

    inner_radius = props_in.bf_Minor_Dia / 2
    outer_radius = props_in.bf_Major_Dia / 2
    pitch = props_in.bf_Pitch                               # Thread distance progressed with each revolution.
    div_count = props_in.bf_Div_Count                       # Number of steps used to model each revolution.
    thread_root_type = props_in.bf_Thread_Root_Type         # The shape of the root, 'FLAT' or 'TRIANGLE'.
    root_inner_dia = props_in.bf_Rounded_Root_Dia           # Diameter of the thread root at the bottom ISO724:2003.

    deg_step = 360.0 / div_count
    height_step = pitch / div_count

    crest_height = pitch * props_in.bf_Crest_Percent / 100.0
    root_height = pitch * props_in.bf_Root_Percent / 100.0
    root_to_crest_height = crest_to_root_height = (pitch - (crest_height + root_height)) / 2.0

    row = 0

    tapper_height_start = height_offset - pitch - pitch
    max_height = tapper_height_start - pitch
    lowest_z_vert = 0

    for _j in range(4):
        # Crest
        for i in range(div_count + 1):
            z = height_offset - (height_step * i)
            z = max(z, max_height)
            tapper_radius = outer_radius
            if z < tapper_height_start:
                tapper_radius = max(outer_radius - (tapper_height_start - z), 0)
            if z <= max_height + crest_height:
                tapper_radius = min(inner_radius, tapper_radius)
            x = sin(radians(i * deg_step)) * tapper_radius
            y = cos(radians(i * deg_step)) * tapper_radius
            verts.append([x, y, z])
            lowest_z_vert = min(lowest_z_vert, z)
        height_offset -= crest_height
        row += 1

        # Flank down
        for i in range(div_count + 1):
            z = height_offset - (height_step * i)
            z = max(z, max_height)
            tapper_radius = outer_radius
            if z < tapper_height_start:
                tapper_radius = max(outer_radius - (tapper_height_start - z), 0)
            if z <= max_height:
                tapper_radius = min(inner_radius, tapper_radius)
            x = sin(radians(i * deg_step)) * tapper_radius
            y = cos(radians(i * deg_step)) * tapper_radius
            verts.append([x, y, z])
            lowest_z_vert = min(lowest_z_vert, z)
        height_offset -= crest_to_root_height
        row += 1

        # Conditional Root Generation
        if thread_root_type == 'TRIANGLE':
            root_min = root_inner_dia / 2
            # Top of V-Root
            for i in range(div_count + 1):
                z = height_offset - (height_step * i)
                z = max(z, max_height)
                tapper_radius = max(outer_radius - (tapper_height_start - z), 0)
                if tapper_radius > inner_radius:
                    tapper_radius = inner_radius
                if z <= max_height:
                    tapper_radius = min(inner_radius, tapper_radius)
                x = sin(radians(i * deg_step)) * tapper_radius
                y = cos(radians(i * deg_step)) * tapper_radius
                verts.append([x, y, z])
                lowest_z_vert = min(lowest_z_vert, z)
            height_offset -= root_height / 2
            row += 1
            # Bottom of V-Root
            for i in range(div_count + 1):
                z = height_offset - (height_step * i)
                z = max(z, max_height)
                tapper_radius = max(outer_radius - (tapper_height_start - z), 0)
                if tapper_radius > inner_radius:
                    tapper_radius = root_min
                if z <= max_height:
                    tapper_radius = min(inner_radius, tapper_radius)
                x = sin(radians(i * deg_step)) * tapper_radius
                y = cos(radians(i * deg_step)) * tapper_radius
                verts.append([x, y, z])
                lowest_z_vert = min(lowest_z_vert, z)
            height_offset -= root_height / 2
            row += 1
        else:  # FLAT root logic
            for i in range(div_count + 1):
                z = height_offset - (height_step * i)
                z = max(z, max_height)
                tapper_radius = max(outer_radius - (tapper_height_start - z), 0)
                if tapper_radius > inner_radius:
                    tapper_radius = inner_radius
                if z <= max_height:
                    tapper_radius = min(inner_radius, tapper_radius)
                x = sin(radians(i * deg_step)) * tapper_radius
                y = cos(radians(i * deg_step)) * tapper_radius
                verts.append([x, y, z])
                lowest_z_vert = min(lowest_z_vert, z)
            height_offset -= root_height
            row += 1

        # Flank up
        for i in range(div_count + 1):
            z = height_offset - (height_step * i)
            z = max(z, max_height)
            tapper_radius = max(outer_radius - (tapper_height_start - z), 0)
            if tapper_radius > inner_radius:
                tapper_radius = inner_radius
            if z <= max_height:
                tapper_radius = min(inner_radius, tapper_radius)
            x = sin(radians(i * deg_step)) * tapper_radius
            y = cos(radians(i * deg_step)) * tapper_radius
            verts.append([x, y, z])
            lowest_z_vert = min(lowest_z_vert, z)
        height_offset -= root_to_crest_height
        row += 1

    return verts, row, height_offset, lowest_z_vert


def create_external_thread(props_in, shank_length, thread_length):
    """
    Main function to generate an external thread. It uses 4 helper functions to build the components of
    the Shank, a Ranked start, main thread and a tapered finish.
    :param props_in: (parameter) used for - bf_Div_Count
    :param shank_length: (float) - The required length of the Shank.
    :param thread_length: (float) - The required length of the Thread.
    :return: Verts: (list) - mesh Verts.
             Faces: (list) - mesh Faces.
             lowest_z_vert: (float) - Minimum Z-axis vertex created.
    """
    verts = []
    faces = []
    div_count = props_in.bf_Div_Count

    total_row = 0

    face_start = len(verts)
    offset = 0.0

    shank_verts, shank_row, offset = create_shank_verts(props_in, shank_length, offset)
    total_row += shank_row

    thread_start_verts, thread_start_row, offset = create_thread_start_verts(props_in, offset)
    total_row += thread_start_row

    thread_verts, thread_row, offset = create_thread_verts(props_in, thread_length, offset)
    total_row += thread_row

    thread_end_verts, thread_end_row, offset, lowest_z_vert = create_thread_end_verts(props_in, offset)
    total_row += thread_end_row

    mini_adder = lowest_z_vert + shank_length + thread_length
    if mini_adder < thread_length * 0.01:
        mini_adder = 0

    verts.extend(shank_verts)
    verts.extend(move_verts_up_z(thread_start_verts, -mini_adder))
    verts.extend(move_verts_up_z(thread_verts, -mini_adder))
    verts.extend(move_verts_up_z(thread_end_verts, -mini_adder))

    faces.extend(build_face_list_quads(face_start, div_count, total_row - 1, 0))
    # Note: len(verts) is calculated AFTER verts are extended
    faces.extend(fill_ring_face(len(verts) - (div_count + 1), div_count, 1))

    rot_mat = simple_rotation_matrix(-90, 'z')     # Aligns thread with head reference being on the x-axis

    return rot_mesh(verts, rot_mat), faces, 0.0 - lowest_z_vert + mini_adder


# ####################################################################
#                   Create Nut
# ## Hex Nut - now makes variable number of sides
# ## Nylon Lock Nut
# ## 12 point (spline / bi-hex) Nut
# ####################################################################

def add_hex_nut(props_in, height):
    """
    Creates a six sided standard nut.
    :param props_in: (parameter) used for - bf_Major_Dia, bf_Hex_Nut_Flat_Distance, bf_Nut_Type
    :param height: (float) - Thickness of the Nut.
    :return: Verts: (list) - mesh Verts.
             Faces: (list) - mesh Faces.
             top_bevel_radius: (float) - Radius of the nut face.
             new_nut_height: (float) - Height of the nut (modified from HEIGHT if clamped)
    """
    # props_in.report({'INFO'}, "Hello:: Starting to go Nuts!")

    hole_radius = props_in.bf_Major_Dia * 0.5
    half_flat = props_in.bf_Hex_Nut_Flat_Distance / 2
    half_height = height / 2
    top_bevel_radius = half_flat - 0.05
    n_sides = props_in.bf_N_Sided

    deg_step = np.linspace(-180/n_sides, 180/n_sides, (props_in.bf_Div_Count+n_sides)//n_sides)
    # deg_step = range(-30, 31, 10)         # For the original hex implementation
    angle_rad = [radians(i) for i in deg_step]   # degrees are not needed in the function convert to radians once

    verts = []
    faces = []

    # inner hole
    for theta in angle_rad:
        verts.append([sin(theta) * hole_radius, cos(theta) * hole_radius, 0.0])

    # bevel
    vect = []        # Empty vector holder
    for theta in angle_rad:
        verts.append([sin(theta) * top_bevel_radius, cos(theta) * top_bevel_radius, 0.0])
        vect.append(Vector([sin(theta) * top_bevel_radius, cos(theta) * top_bevel_radius, 0.0]))

    # Flats
    z_bevel_min = 0     # Lint does not believe that the for loop will always run, if referenced before assignment.
    for theta, vec in zip(angle_rad, vect):
        x = tan(theta) * half_flat
        d_vec = vec - Vector([x, half_flat, 0.0])
        z_bevel_min = d_vec.length * tan(radians(min(45, 5 * n_sides)))
        # Angle was 45. ISO 4032 specs for hex is 15-30 degrees. Coach bolt, 4 sides, is 20 degrees.
        verts.append([x, half_flat, -z_bevel_min])

    # Clean up situations where the bevel is deeper than the requested available height.
    z_min = -max(z_bevel_min, half_height)

    # Midline
    for theta in angle_rad:
        verts.append([tan(theta) * half_flat, half_flat, z_min])

    faces.extend(build_face_list_quads(0, len(angle_rad) - 1, len(verts)//len(angle_rad) - 1))

    # Mirror the top half of the nut to make it complete.
    t_vert, t_face = mirror_verts_faces(verts, faces, 'z', z_min)
    verts.extend(t_vert)

    # if we are making a Nylock Nut then removing the bottom faces are easiest done here.
    if props_in.bf_Nut_Type == 'bf_Nut_Lock':
        faces.extend(t_face[(len(angle_rad) - 1):])
    else:
        faces.extend(t_face)

    rot_mat = simple_rotation_matrix(180/n_sides - 90, 'z')      # rotation to align point onto x-axis
    verts_r = rot_mesh(verts, rot_mat)

    s_verts, s_faces = spin_dup(verts_r, faces, 360, n_sides, 'z')

    new_nut_height = -2 * z_min
    return s_verts, s_faces, top_bevel_radius, new_nut_height


def add_nylon_head(outside_radius, height_offset, div_count):
    """
    Creates the metal part joining the nut and stops at the interface to the Nylon insert.
    :param outside_radius: (float) - Radius of the nut to join on to, TopBevelRadius from add_hex_nut().
    :param height_offset: (float) - Z position of the nut to join on to.
    :param div_count: (int) - Rotational division, currently must be 36 to be manifold.
    :return: Verts: (list) - mesh Verts.
             Faces: (list) - mesh Faces.
             Lowest_Z_vert: (float) - Minimum Z-axis vertex created.
    """
    verts = []
    faces = []
    row = 0

    inner_hole = outside_radius - (outside_radius * (1.25 / 4.75))
    edge_thickness = outside_radius * (0.4 / 4.75)
    rad1 = outside_radius * (0.5 / 4.75)
    over_all_height = outside_radius * (2.0 / 4.75)

    face_start = len(verts)

    lowest_z_vert = 0

    x = inner_hole
    z = (height_offset - over_all_height) + edge_thickness
    verts.append([x, 0.0, z])
    lowest_z_vert = min(lowest_z_vert, z)
    row += 1

    x = inner_hole
    z = height_offset - over_all_height
    verts.append([x, 0.0, z])
    lowest_z_vert = min(lowest_z_vert, z)
    row += 1

    for i in range(180, 80, -10):
        x = sin(radians(i)) * rad1
        z = cos(radians(i)) * rad1
        verts.append([(outside_radius - rad1) + x, 0.0, ((height_offset - over_all_height) + rad1) + z])
        lowest_z_vert = min(lowest_z_vert, z)
        row += 1

    x = outside_radius - 0          # These coordinates cause an internal face to be generated
    z = height_offset               # As the locking part is abutted to the existing nut face
    verts.append([x, 0.0, z])       #
    lowest_z_vert = min(lowest_z_vert, z)
    row += 1

    s_verts, s_faces = spin_dup(verts, faces, 360, div_count, 'z')
    s_verts.extend(verts)        # add the start verts to the Spin verts to complete the loop

    s_faces.extend(build_face_list_quads(face_start, row - 1, div_count, 1))

    return move_verts_up_z(s_verts, 0), s_faces, lowest_z_vert


def add_nylon_part(outside_radius, height_offset, props_in):
    """
    Creates the Nylon insert joining the nut and stops at the interface to the metal part.
    :param outside_radius: (float) - Radius of the nut to join on to, TopBevelRadius from add_hex_nut().
    :param height_offset: (float) - Z position of the nut to join on to.
    :param props_in: (class) - All the parameters from the GUI, using props.bf_Major_Dia & bf_Div_Count
    :return: Verts: (list) - mesh Verts.
             Faces: (list) - mesh Faces.
             Lowest_Z_vert: (float) - Minimum Z-axis vertex created.
    """
    verts = []
    faces = []
    row = 0

    inner_hole = outside_radius - (outside_radius * (1.25 / 4.75))
    edge_thickness = outside_radius * (0.4 / 4.75)
    over_all_height = outside_radius * (2.0 / 4.75)
    part_thickness = over_all_height - edge_thickness
    part_inner_hole = outside_radius * (2.5 / 4.75)

    face_start = len(verts)

    lowest_z_vert = 0

    x = props_in.bf_Major_Dia / 2           # Use this as the starting radius
    z = height_offset
    verts.append([x, 0.0, z])
    lowest_z_vert = min(lowest_z_vert, z)
    row += 1

    x = part_inner_hole                     # Should interfere with the thread
    z = height_offset - edge_thickness / 2    # Borrow edge_thickness to ensure the Nylon has a scalable bevel
    verts.append([x, 0.0, z])
    lowest_z_vert = min(lowest_z_vert, z)
    row += 1

    x = part_inner_hole
    z = height_offset - part_thickness
    verts.append([x, 0.0, z])
    lowest_z_vert = min(lowest_z_vert, z)
    row += 1

    x = inner_hole                          # Attaches to the last part of the Nylon_Head
    z = height_offset - part_thickness
    verts.append([x, 0.0, z])
    lowest_z_vert = min(lowest_z_vert, z)
    row += 1

    s_verts, s_faces = spin_dup(verts, faces, 360, props_in.bf_Div_Count, 'z')
    s_verts.extend(verts)  # add the start verts to the Spin verts to complete the loop

    s_faces.extend(build_face_list_quads(face_start, row - 1, props_in.bf_Div_Count, 1))

    return s_verts, s_faces, 0 - lowest_z_vert


def add_12_point_nut(flat, hole_dia, height, flange_dia):
    """
    Creates the mesh of the 12 Point Nut. Calls create_12_point().
    :param flat: (float) - Distance across flats (measured if hexagonal).
    :param hole_dia: (float) - Diameter for the internal thread.
    :param height: (float) - Height of the nut.
    :param flange_dia: (float) - Diameter of the flange.
    :return: Verts: (list) - mesh Verts.
             Faces: (list) - mesh Faces.
             Height: (float) - Z-axis height of the nut.
    """
    return create_12_point(flat, hole_dia, hole_dia, height, flange_dia)


# ####################################################################
#                   Create Real Internal Thread
#  Starts and ends with a bevel. This is the same way that a nut would
#  be turned on a lathe.
#    Note that root and crest are inverted in this nomenclature.
# ####################################################################

def create_real_internal_thread(props_in, height):
    """
    Creates the internal thread. The internal chamfer is top and bottom as per ISO 4032:1999. It has been chosen
    to have the maximum of the bevel exactly equal to the thread major diameter, this is the minimum permitted
    by the specification. It also most closely aligns to ASME B18 without requiring a more complex model.
    :param props_in: (parameter) used for - bf_Minor_Dia, bf_Major_Dia, bf_Pitch, bf_Crest_Percent,
                                            bf_Root_Percent, bf_Div_Count
    :param height: (float) - The required length of the Thread.
    :return: verts: (list) - mesh Verts.
             faces: (list) - mesh Faces.
    """
    verts = []
    faces = []

    div_count = props_in.bf_Div_Count       # Number of steps used to model each revolution.
    pitch = props_in.bf_Pitch               # Thread distance progressed with each revolution.

    inner_radius = props_in.bf_Minor_Dia / 2
    outer_radius = props_in.bf_Major_Dia / 2

    # Review note: This function would be cleaner to built two arrays, for the angular steps and height increment.
    # Conversion to radians is only done once rather than 8 times per revolution.
    # The for loops will have to zip this pair.
    deg_step = 360.0 / float(div_count)
    height_step = float(pitch) / float(div_count)
    inner_bevel_angle = radians(30)         # ISO 4032:1999 permits this to be 30 to 45 degrees

    num_turns = int(round(height / pitch)) + 2      # add one pitch for the start and one for the end

    row = 0

    crest_height = pitch * props_in.bf_Crest_Percent / 100.0
    root_height = pitch * props_in.bf_Root_Percent / 100.0
    root_to_crest_height = crest_to_root_height = (float(pitch) - (crest_height + root_height)) / 2.0

    height_offset = pitch           # Start one full turn above.
    face_start = len(verts)

    for _ in range(num_turns):      # This is each revolution

        for inc in range(div_count + 1):
            zzz = max(min(0, height_offset - (height_step * inc)), -height)
            xxx = sin(radians(inc * deg_step)) * outer_radius
            yyy = cos(radians(inc * deg_step)) * outer_radius
            verts.append([xxx, yyy, zzz])
        height_offset -= crest_height
        row += 1

        for inc in range(div_count + 1):
            zzz = max(min(0, height_offset - (height_step * inc)), -height)
            xxx = sin(radians(inc * deg_step)) * outer_radius
            yyy = cos(radians(inc * deg_step)) * outer_radius
            verts.append([xxx, yyy, zzz])
        height_offset -= crest_to_root_height
        row += 1

        for inc in range(div_count + 1):
            zzz = max(min(0, height_offset - (height_step * inc)), -height)
            top_bevel = outer_radius + (zzz / tan(inner_bevel_angle))             # Top inner Bevel
            bot_bevel = outer_radius - (height + zzz) / tan(inner_bevel_angle)     # Bottom inner Bevel
            r_bevel = max(top_bevel, bot_bevel)
            xxx = sin(radians(inc * deg_step)) * max(inner_radius, r_bevel)
            yyy = cos(radians(inc * deg_step)) * max(inner_radius, r_bevel)
            verts.append([xxx, yyy, zzz])
        height_offset -= root_height
        row += 1

        for inc in range(div_count + 1):
            zzz = max(min(0, height_offset - (height_step * inc)), -height)
            top_bevel = outer_radius + zzz / tan(inner_bevel_angle)                # Top inner Bevel
            bot_bevel = outer_radius - (height + zzz) / tan(inner_bevel_angle)     # Bottom inner Bevel
            r_bevel = max(top_bevel, bot_bevel)
            xxx = sin(radians(inc * deg_step)) * max(inner_radius, r_bevel)
            yyy = cos(radians(inc * deg_step)) * max(inner_radius, r_bevel)
            verts.append([xxx, yyy, zzz])
        height_offset -= root_to_crest_height
        row += 1

    faces.extend(build_face_list_quads(face_start, div_count, row - 1, flip=1))

    rot_mat = simple_rotation_matrix(-90, 'z')  # Aligns thread with nut reference being on the x-axis

    return rot_mesh(verts, rot_mat), faces


# ####################################################################
#                    Create Nut
#   A nut is made from an outer surface and an inner thread, if
#   it is a lock nut the nylon and shell is then added.
# ####################################################################

def nut_mesh(props, context):
    """
    Creates a Nut mesh. First the outside is then built, this may clamp in the hex nut.
    The new nut height is then passed to the real internal thread creation as this handles any length.
    If required the locking part of the nut added.
    :param props: (class) - All the parameters from the GUI,
    :param context: Blender magic, not used.
    :return: verts: (list) - mesh Verts.
             faces: (list) - mesh Faces.
    """

    verts = []
    faces = []

    face_start = len(verts)

    if props.bf_Nut_Type == 'bf_Nut_12Pnt':
        nut_height = props.bf_12_Point_Nut_Height
    else:
        nut_height = props.bf_Hex_Nut_Height

    new_nut_height = nut_height

    if props.bf_Nut_Type == 'bf_Nut_12Pnt':
        nut_verts, nut_faces, lock_nut_rad = add_12_point_nut(
            props.bf_12_Point_Nut_Flat_Distance,
            props.bf_Major_Dia, nut_height,
            # Limit the size of the Flange to avoid calculation error
            max(props.bf_12_Point_Nut_Flange_Dia, props.bf_12_Point_Nut_Flat_Distance)
        )
    else:
        nut_verts, nut_faces, lock_nut_rad, new_nut_height = add_hex_nut(props, nut_height)

    verts.extend(nut_verts)
    faces.extend(copy_faces(nut_faces, face_start))

    face_start = len(verts)
    thread_verts, thread_faces = create_real_internal_thread(props, new_nut_height)

    verts.extend(thread_verts)
    faces.extend(copy_faces(thread_faces, face_start))

    low_z = 0 - new_nut_height

    if props.bf_Nut_Type == 'bf_Nut_Lock':
        face_start = len(verts)
        nylon_head_verts, nylon_head_faces, low_z = add_nylon_head(
            lock_nut_rad, 0 - new_nut_height,
            props.bf_Div_Count
        )
        verts.extend(nylon_head_verts)
        faces.extend(copy_faces(nylon_head_faces, face_start))

        face_start = len(verts)
        nylon_verts, nylon_faces, temp_low_z = add_nylon_part(
            lock_nut_rad, 0 - new_nut_height, props
            # uses props for : bf_Major_Dia & bf_Div_Count
        )
        verts.extend(nylon_verts)
        faces.extend(copy_faces(nylon_faces, face_start))

    return move_verts_up_z(verts, 0 - low_z), faces


# ####################################################################
#                    Create Bolt
# ####################################################################

def bolt_mesh(props, context):
    """
    Creates a Bolt Mesh. Starts by building any bits, then the main head, before putting
    the shank and thread on. Due to threads being created from an integer number of revolutions
    the shank length is extended to account for any discrepancy.
    :param props: (class) - All the parameters from the GUI,
    :param context: Blender magic, not used.
    :return: verts: (list) - mesh Verts.
             faces: (list) - mesh Faces.
    """

    verts = []
    faces = []

    re_sized_allen_bit_flat_distance = props.bf_Allen_Bit_Flat_Distance  # set default

    head_height = props.bf_Hex_Head_Height  # will be changed by the Head Functions

    if props.bf_Bit_Type == 'bf_Bit_Allen' and props.bf_Head_Type == 'bf_Head_Pan':
        # need to re-size Allen bit if it is too big. Could be more general!
        if allen_bit_dia(props.bf_Allen_Bit_Flat_Distance) > max_pan_bit_dia(props.bf_Pan_Head_Dia):
            re_sized_allen_bit_flat_distance = allen_bit_dia_to_flat(max_pan_bit_dia(props.bf_Pan_Head_Dia))
            # print ("Resized Allen Bit Flat Distance to " ,re_sized_allen_bit_flat_distance)

    # Bit Mesh
    if props.bf_Bit_Type == 'bf_Bit_Allen':
        bit_verts, bit_faces, bit_dia = create_allen_bit(props, re_sized_allen_bit_flat_distance)
    elif props.bf_Bit_Type == 'bf_Bit_Torx':
        bit_verts, bit_faces, bit_dia = create_torx_bit(
            torx_bit_size_to_point_distance(props.bf_Torx_Size_Type),
            props.bf_Torx_Bit_Depth
        )
    elif props.bf_Bit_Type == 'bf_Bit_Robertson':
        bit_verts, bit_faces, bit_dia = robertson_mesh(props)
    elif props.bf_Bit_Type == 'bf_N_Bit_Allen':
        bit_verts, bit_faces, bit_dia = n_bit_mesh(props, props.bf_N_Sided_Bit)
    elif props.bf_Bit_Type == 'bf_Bit_Star':
        bit_verts, bit_faces, bit_dia = n_bit_mesh(props, 6)
    elif props.bf_Bit_Type == 'bf_Bit_Double_Square':
        bit_verts, bit_faces, bit_dia = n_bit_mesh(props, 8)
    elif props.bf_Bit_Type in ['bf_Double_Hex', 'bf_Triple_Square_XZN', 'bf_12_Spline']:
        bit_verts, bit_faces, bit_dia = n_bit_mesh(props, 12)
    elif props.bf_Bit_Type == 'bf_Bit_Philips':
        bit_verts, bit_faces, bit_dia = create_phillips_bit(props)
    else:       # props.bf_Bit_Type == 'bf_Bit_None', use else to guarantee assignment.
        bit_verts = []
        bit_faces = []
        bit_dia = 0.00001  # 0.001, was too close to rounding value causing a hole in the head, WHY NOT ZERO????
    rot_mat = simple_rotation_matrix(-90, 'z')  # Aligns points/lobes with head reference being on the x-axis
    bit_verts = rot_mesh(bit_verts, rot_mat)

    # Head Mesh
    # Define the washer face of the bolt, i.e. the underside. Some bolts have a bevel or radius to the shank included
    # Their head height causes an incorrect shank/thread length determination.
    washer_face_z = 0         # z-axis height, some Heads return a variable that overwrites this
    if props.bf_Head_Type == 'bf_Head_Hex':
        head_verts, head_faces, head_height, washer_face_z = create_hex_head(props, bit_dia)
    elif props.bf_Head_Type == 'bf_Head_12Pnt':
        head_verts, head_faces, head_height = create_12_point_head(
            props.bf_12_Point_Head_Flat_Distance, bit_dia,
            props.bf_Shank_Dia, props.bf_12_Point_Head_Height,
            # Limit the size of the Flange to avoid calculation error
            max(props.bf_12_Point_Head_Flange_Dia, props.bf_12_Point_Head_Flat_Distance)
        )
    elif props.bf_Head_Type == 'bf_Head_Cap':
        head_verts, head_faces, head_height, washer_face_z = create_cap_head(props, bit_dia)
    elif props.bf_Head_Type == 'bf_Head_Dome':
        head_verts, head_faces, head_height = create_dome_head(props, bit_dia)
    elif props.bf_Head_Type == 'bf_Head_Pan':
        head_verts, head_faces, head_height, washer_face_z = create_pan_head(props, bit_dia)
    elif props.bf_Head_Type == 'bf_Head_CounterSink':
        head_verts, head_faces, head_height = create_counter_sink_head(props, bit_dia)
    else:   # props.bf_Head_Type == 'bf_Head_None', use 'else' to guarantee assignment.
        head_verts = []
        head_faces = []

    face_start = len(verts)
    verts.extend(move_verts_up_z(bit_verts, head_height))
    faces.extend(copy_faces(bit_faces, face_start))

    face_start = len(verts)
    verts.extend(move_verts_up_z(head_verts, head_height))
    faces.extend(copy_faces(head_faces, face_start))

    make_shank_length = props.bf_Shank_Length
    make_thread_length = props.bf_Thread_Length
    if washer_face_z != 0:
        # At this point the mesh is back at z=zero. The washer face may be randomly above this depending on
        # the head choice. Optional returned variable is used to shorten up the shank/thread.
        # If the Head function modified the washer_face-z we are here to make a length correction.
        washer_face = washer_face_z + head_height
        make_shank_length = props.bf_Shank_Length - washer_face
        if make_shank_length < 0:
            # If all the shank length is used up then take it off the thread length
            make_thread_length = props.bf_Thread_Length + make_shank_length
            make_shank_length = 0

    face_start = len(verts)
    thread_verts, thread_faces, thread_height = create_external_thread(props, make_shank_length, make_thread_length)

    verts.extend(move_verts_up_z(thread_verts, 0))          # Moving up a distance of Zero????
    faces.extend(copy_faces(thread_faces, face_start))

    return move_verts_up_z(verts, thread_height), faces


def create_new_mesh(props, context, adjusted_scale):
    """
    This is the entry point from the 'menu_func_bolt' or 'bolt_contex_menu'.
    :param props: (class) - All the parameters from the GUI,
    :param context: Blender magic, not used.
    :param adjusted_scale: (float) - to scale the verts by 'context.scene.unit_settings.scale_length'.
    :return: mesh (blender object).
    """

    verts = []
    faces = []
    edges = []
    sObjName = ''

    if props.bf_Model_Type == 'bf_Model_Bolt':
        # print('Create Bolt')
        verts, faces = bolt_mesh(props, context)
        sObjName = 'Bolt'

    if props.bf_Model_Type == 'bf_Model_Nut':
        # print('Create Nut')
        verts, faces = nut_mesh(props, context)
        sObjName = 'Nut'

    verts = scale_mesh_verts(verts, adjusted_scale)

    mesh = bpy.data.meshes.new(name=sObjName)
    mesh.from_pydata(verts, edges, faces)

    # validate checks for thin faces among other things
    is_not_mesh_valid = mesh.validate()

    if is_not_mesh_valid:
        props.report({'INFO'}, "Mesh is not Valid, correcting")

    return mesh
