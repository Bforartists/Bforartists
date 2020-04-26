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
from mathutils import (
        Matrix,
        Vector,
        geometry,
        )
from math import (
        sin, cos,
        tan, radians,atan,degrees
        )
from random import triangular
from bpy_extras.object_utils import AddObjectHelper, object_data_add

NARROW_UI = 180
MAX_INPUT_NUMBER = 50

GLOBAL_SCALE = 1       # 1 blender unit = X mm


# next two utility functions are stolen from import_obj.py

def unpack_list(list_of_tuples):
    l = []
    for t in list_of_tuples:
        l.extend(t)
    return l


def unpack_face_list(list_of_tuples):
    l = []
    for t in list_of_tuples:
        face = [i for i in t]

        if len(face) != 3 and len(face) != 4:
            raise RuntimeError("{0} vertices in face".format(len(face)))

        # rotate indices if the 4th is 0
        if len(face) == 4 and face[3] == 0:
            face = [face[3], face[0], face[1], face[2]]

        if len(face) == 3:
            face.append(0)

        l.extend(face)

    return l


"""
Remove Doubles takes a list on Verts and a list of Faces and
removes the doubles, much like Blender does in edit mode.
It doesn't have the range function  but it will round the corrdinates
and remove verts that are very close together.  The function
is useful because you can perform a "Remove Doubles" with out
having to enter Edit Mode. Having to enter edit mode has the
disadvantage of not being able to interactively change the properties.
"""


def RemoveDoubles(verts, faces, Decimal_Places=4):

    new_verts = []
    new_faces = []
    dict_verts = {}
    Rounded_Verts = []

    for v in verts:
        Rounded_Verts.append([round(v[0], Decimal_Places),
                              round(v[1], Decimal_Places),
                              round(v[2], Decimal_Places)])

    for face in faces:
        new_face = []
        for vert_index in face:
            Real_co = tuple(verts[vert_index])
            Rounded_co = tuple(Rounded_Verts[vert_index])

            if Rounded_co not in dict_verts:
                dict_verts[Rounded_co] = len(dict_verts)
                new_verts.append(Real_co)
            if dict_verts[Rounded_co] not in new_face:
                new_face.append(dict_verts[Rounded_co])
        if len(new_face) == 3 or len(new_face) == 4:
            new_faces.append(new_face)

    return new_verts, new_faces


def Scale_Mesh_Verts(verts, scale_factor):
    Ret_verts = []
    for v in verts:
        Ret_verts.append([v[0] * scale_factor, v[1] * scale_factor, v[2] * scale_factor])
    return Ret_verts


# Create a matrix representing a rotation.
#
# Parameters:
#
#        * angle (float) - The angle of rotation desired.
#        * matSize (int) - The size of the rotation matrix to construct. Can be 2d, 3d, or 4d.
#        * axisFlag (string (optional)) - Possible values:
#              o "x - x-axis rotation"
#              o "y - y-axis rotation"
#              o "z - z-axis rotation"
#              o "r - arbitrary rotation around vector"
#        * axis (Vector object. (optional)) - The arbitrary axis of rotation used with "R"
#
# Returns: Matrix object.
#    A new rotation matrix.

def Simple_RotationMatrix(angle, matSize, axisFlag):
    if matSize != 4:
        print("Simple_RotationMatrix can only do 4x4")

    q = radians(angle)  # make the rotation go clockwise

    if axisFlag == 'x':
        matrix = Matrix.Rotation(q, 4, 'X')
    elif axisFlag == 'y':
        matrix = Matrix.Rotation(q, 4, 'Y')
    elif axisFlag == 'z':
        matrix = Matrix.Rotation(q, 4, 'Z')
    else:
        print("Simple_RotationMatrix can only do x y z axis")
    return matrix


# ####################################################################
#              Converter Functions For Bolt Factory
# ####################################################################

def Flat_To_Radius(FLAT):
    h = (float(FLAT) / 2) / cos(radians(30))
    return h


def Get_Phillips_Bit_Height(Bit_Dia):
    Flat_Width_half = (Bit_Dia * (0.5 / 1.82)) / 2.0
    Bit_Rad = Bit_Dia / 2.0
    x = Bit_Rad - Flat_Width_half
    y = tan(radians(60)) * x
    return float(y)


# ####################################################################
#                    Miscellaneous Utilities
# ####################################################################

# Returns a list of verts rotated by the given matrix. Used by SpinDup
def Rot_Mesh(verts, matrix):
    from mathutils import Vector
    return [(matrix @ Vector(v))[:] for v in verts]


# Returns a list of faces that has there index incremented by offset
def Copy_Faces(faces, offset):
    return [[(i + offset) for i in f] for f in faces]


# Much like Blenders built in SpinDup
def SpinDup(VERTS, FACES, DEGREE, DIVISIONS, AXIS):
    verts = []
    faces = []

    if DIVISIONS == 0:
        DIVISIONS = 1

    step = DEGREE / DIVISIONS  # set step so pieces * step = degrees in arc

    for i in range(int(DIVISIONS)):
        rotmat = Simple_RotationMatrix(step * i, 4, AXIS)  # 4x4 rotation matrix, 30d about the x axis.
        Rot = Rot_Mesh(VERTS, rotmat)
        faces.extend(Copy_Faces(FACES, len(verts)))
        verts.extend(Rot)
    return verts, faces


# Returns a list of verts that have been moved up the z axis by DISTANCE
def Move_Verts_Up_Z(VERTS, DISTANCE):
    ret = []
    for v in VERTS:
        ret.append([v[0], v[1], v[2] + DISTANCE])
    return ret


# Returns a list of verts and faces that has been mirrored in the AXIS
def Mirror_Verts_Faces(VERTS, FACES, AXIS, FLIP_POINT=0):
    ret_vert = []
    ret_face = []
    offset = len(VERTS)
    if AXIS == 'y':
        for v in VERTS:
            Delta = v[0] - FLIP_POINT
            ret_vert.append([FLIP_POINT - Delta, v[1], v[2]])
    if AXIS == 'x':
        for v in VERTS:
            Delta = v[1] - FLIP_POINT
            ret_vert.append([v[0], FLIP_POINT - Delta, v[2]])
    if AXIS == 'z':
        for v in VERTS:
            Delta = v[2] - FLIP_POINT
            ret_vert.append([v[0], v[1], FLIP_POINT - Delta])

    for f in FACES:
        fsub = []
        for i in range(len(f)):
            fsub.append(f[i] + offset)
        fsub.reverse()  # flip the order to make norm point out
        ret_face.append(fsub)

    return ret_vert, ret_face


# Returns a list of faces that
# make up an array of 4 point polygon.
def Build_Face_List_Quads(OFFSET, COLUMN, ROW, FLIP=0):
    Ret = []
    RowStart = 0
    for j in range(ROW):
        for i in range(COLUMN):
            Res1 = RowStart + i
            Res2 = RowStart + i + (COLUMN + 1)
            Res3 = RowStart + i + (COLUMN + 1) + 1
            Res4 = RowStart + i + 1
            if FLIP:
                Ret.append([OFFSET + Res1, OFFSET + Res2, OFFSET + Res3, OFFSET + Res4])
            else:
                Ret.append([OFFSET + Res4, OFFSET + Res3, OFFSET + Res2, OFFSET + Res1])
        RowStart += COLUMN + 1
    return Ret


# Returns a list of faces that makes up a fill pattern for a
# circle
def Fill_Ring_Face(OFFSET, NUM, FACE_DOWN=0):
    Ret = []
    Face = [1, 2, 0]
    TempFace = [0, 0, 0]
    # A = 0  # UNUSED
    B = 1
    C = 2
    if NUM < 3:
        return None
    for i in range(NUM - 2):
        if (i % 2):
            TempFace[0] = Face[C]
            TempFace[1] = Face[C] + 1
            TempFace[2] = Face[B]
            if FACE_DOWN:
                Ret.append([OFFSET + Face[2], OFFSET + Face[1], OFFSET + Face[0]])
            else:
                Ret.append([OFFSET + Face[0], OFFSET + Face[1], OFFSET + Face[2]])
        else:
            TempFace[0] = Face[C]
            if Face[C] == 0:
                TempFace[1] = NUM - 1
            else:
                TempFace[1] = Face[C] - 1
            TempFace[2] = Face[B]
            if FACE_DOWN:
                Ret.append([OFFSET + Face[0], OFFSET + Face[1], OFFSET + Face[2]])
            else:
                Ret.append([OFFSET + Face[2], OFFSET + Face[1], OFFSET + Face[0]])

        Face[0] = TempFace[0]
        Face[1] = TempFace[1]
        Face[2] = TempFace[2]
    return Ret

# Returns a list of faces that makes up a fill pattern around the last vert
def Fill_Fan_Face(OFFSET, NUM, FACE_DOWN=0):
    Ret = []
    Face = [NUM-1,0,1]
    TempFace = [0, 0, 0]
    A = 0  
    #B = 1 unsed
    C = 2
    if NUM < 3:
        return None
    for _i in range(NUM - 2):
        TempFace[0] = Face[A]
        TempFace[1] = Face[C] 
        TempFace[2] = Face[C]+1
        if FACE_DOWN:
            Ret.append([OFFSET + Face[2], OFFSET + Face[1], OFFSET + Face[0]])
        else:
            Ret.append([OFFSET + Face[2], OFFSET + Face[1], OFFSET + Face[0]])

        Face[0] = TempFace[0]
        Face[1] = TempFace[1]
        Face[2] = TempFace[2]
    return Ret

# ####################################################################
#                    Create Allen Bit
# ####################################################################

def Allen_Fill(OFFSET, FLIP=0):
    faces = []
    Lookup = [[19, 1, 0],
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
    for i in Lookup:
        if FLIP:
            faces.append([OFFSET + i[2], OFFSET + i[1], OFFSET + i[0]])
        else:
            faces.append([OFFSET + i[0], OFFSET + i[1], OFFSET + i[2]])

    return faces


def Allen_Bit_Dia(FLAT_DISTANCE):
    Flat_Radius = (float(FLAT_DISTANCE) / 2.0) / cos(radians(30))
    return (Flat_Radius * 1.05) * 2.0


def Allen_Bit_Dia_To_Flat(DIA):
    Flat_Radius = (DIA / 2.0) / 1.05
    return (Flat_Radius * cos(radians(30))) * 2.0


def Create_Allen_Bit(FLAT_DISTANCE, HEIGHT):
    verts = []
    faces = []
    DIV_COUNT = 36

    Flat_Radius = (float(FLAT_DISTANCE) / 2.0) / cos(radians(30))
    OUTTER_RADIUS = Flat_Radius * 1.05
    Outter_Radius_Height = Flat_Radius * (0.1 / 5.77)
    FaceStart_Outside = len(verts)
    Deg_Step = 360.0 / float(DIV_COUNT)

    for i in range(int(DIV_COUNT / 2) + 1):  # only do half and mirror later
        x = sin(radians(i * Deg_Step)) * OUTTER_RADIUS
        y = cos(radians(i * Deg_Step)) * OUTTER_RADIUS
        verts.append([x, y, 0])

    FaceStart_Inside = len(verts)

    Deg_Step = 360.0 / float(6)
    for i in range(int(6 / 2) + 1):
        x = sin(radians(i * Deg_Step)) * Flat_Radius
        y = cos(radians(i * Deg_Step)) * Flat_Radius
        verts.append([x, y, 0 - Outter_Radius_Height])

    faces.extend(Allen_Fill(FaceStart_Outside, 0))

    FaceStart_Bottom = len(verts)

    Deg_Step = 360.0 / float(6)
    for i in range(int(6 / 2) + 1):
        x = sin(radians(i * Deg_Step)) * Flat_Radius
        y = cos(radians(i * Deg_Step)) * Flat_Radius
        verts.append([x, y, 0 - HEIGHT])

    faces.extend(Build_Face_List_Quads(FaceStart_Inside, 3, 1, True))
    faces.extend(Fill_Ring_Face(FaceStart_Bottom, 4))

    M_Verts, M_Faces = Mirror_Verts_Faces(verts, faces, 'y')
    verts.extend(M_Verts)
    faces.extend(M_Faces)

    return verts, faces, OUTTER_RADIUS * 2.0
# ####################################################################
#                    Create Torx Bit
# ####################################################################

def Torx_Bit_Size_To_Point_Distance(Bit_Size):
    if Bit_Size == 'bf_Torx_T10':
        return 2.83
    elif Bit_Size == 'bf_Torx_T20':
        return 3.94
    elif Bit_Size == 'bf_Torx_T25':
        return 4.52
    elif Bit_Size == 'bf_Torx_T30':
        return 5.61
    elif Bit_Size == 'bf_Torx_T40':
        return 6.75
    elif Bit_Size == 'bf_Torx_T50':
        return 8.94
    elif Bit_Size == 'bf_Torx_T55':
        return 8.94
    else:
        return 2.83  #default to M3

def Torx_Fill(OFFSET, FLIP=0):
    faces = []
    Lookup = [[0,10,11],
            [0,11, 12],
            [0,12,1],
            
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
    for i in Lookup:
        if FLIP:
            faces.append([OFFSET + i[2], OFFSET + i[1], OFFSET + i[0]])
        else:
            faces.append([OFFSET + i[0], OFFSET + i[1], OFFSET + i[2]])

    return faces



def Create_Torx_Bit(Point_Distance, HEIGHT):
    verts = []
    faces = []

    POINT_RADIUS = Point_Distance * 0.5
    OUTTER_RADIUS = POINT_RADIUS * 1.05

    POINT_1_Y = POINT_RADIUS * 0.816592592592593
    POINT_2_X = POINT_RADIUS * 0.511111111111111 
    POINT_2_Y = POINT_RADIUS * 0.885274074074074     
    POINT_3_X = POINT_RADIUS * 0.7072 
    POINT_3_Y = POINT_RADIUS * 0.408296296296296 
    POINT_4_X = POINT_RADIUS * 1.02222222222222 
    SMALL_RADIUS = POINT_RADIUS * 0.183407407407407 
    BIG_RADIUS = POINT_RADIUS * 0.333333333333333 
#     Values for T40    #     POINT_1_Y = 2.756
#     POINT_2_X = 1.725
#     POINT_2_Y = 2.9878    
#     POINT_3_X = 2.3868
#     POINT_3_Y = 1.378
#     POINT_4_X = 3.45
#     
#     SMALL_RADIUS = 0.619
#     BIG_RADIUS = 1.125

    def Do_Curve(Curve_Height):
        for i in range(0, 90, 10):  
            x = sin(radians(i)) * SMALL_RADIUS
            y = cos(radians(i)) * SMALL_RADIUS
            verts.append([x, POINT_1_Y + y, Curve_Height])
    
        for i in range(260, 150, -10):  
            x = sin(radians(i)) * BIG_RADIUS
            y = cos(radians(i)) * BIG_RADIUS
            verts.append([POINT_2_X + x, POINT_2_Y + y, Curve_Height])
    
        for i in range(340, 150 + 360, 10):
            x = sin(radians(i%360)) * SMALL_RADIUS
            y = cos(radians(i%360)) * SMALL_RADIUS
            verts.append([POINT_3_X + x, POINT_3_Y + y, Curve_Height])
    
        for i in range(320, 260, -10):  
            x = sin(radians(i)) * BIG_RADIUS
            y = cos(radians(i)) * BIG_RADIUS
            verts.append([POINT_4_X + x, y, Curve_Height])

    FaceStart_Outside = len(verts)

    for i in range(0, 100, 10):
        x = sin(radians(i)) * OUTTER_RADIUS
        y = cos(radians(i)) * OUTTER_RADIUS
        verts.append([x, y, 0])

    FaceStart_Top_Curve= len(verts)
    Do_Curve(0)
    faces.extend(Torx_Fill(FaceStart_Outside, 0))
    
    FaceStart_Bottom_Curve= len(verts)
    Do_Curve(0 - HEIGHT)
    
    faces.extend(Build_Face_List_Quads(FaceStart_Top_Curve,42 ,1 , True))
 
    verts.append([0,0,0 - HEIGHT]) # add center point for fill Fan
    faces.extend(Fill_Fan_Face(FaceStart_Bottom_Curve, 44))
 
    M_Verts, M_Faces = Mirror_Verts_Faces(verts, faces, 'x')
    verts.extend(M_Verts)
    faces.extend(M_Faces)
  
    M_Verts, M_Faces = Mirror_Verts_Faces(verts, faces, 'y')
    verts.extend(M_Verts)
    faces.extend(M_Faces)

    return verts, faces, OUTTER_RADIUS * 2.0

# ####################################################################
#                    Create Phillips Bit
# ####################################################################

def Phillips_Fill(OFFSET, FLIP=0):
    faces = []
    Lookup = [[0, 1, 10],
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
              [11, 12, 16],
              [12, 13, 16],
              [13, 14, 17, 16],
              [15, 16, 17, 18]
              ]
    for i in Lookup:
        if FLIP:
            if len(i) == 3:
                faces.append([OFFSET + i[2], OFFSET + i[1], OFFSET + i[0]])
            else:
                faces.append([OFFSET + i[3], OFFSET + i[2], OFFSET + i[1], OFFSET + i[0]])
        else:
            if len(i) == 3:
                faces.append([OFFSET + i[0], OFFSET + i[1], OFFSET + i[2]])
            else:
                faces.append([OFFSET + i[0], OFFSET + i[1], OFFSET + i[2], OFFSET + i[3]])
    return faces


def Create_Phillips_Bit(FLAT_DIA, FLAT_WIDTH, HEIGHT):
    verts = []
    faces = []

    DIV_COUNT = 36
    FLAT_RADIUS = FLAT_DIA * 0.5
    OUTTER_RADIUS = FLAT_RADIUS * 1.05

    Flat_Half = float(FLAT_WIDTH) / 2.0

    FaceStart_Outside = len(verts)
    Deg_Step = 360.0 / float(DIV_COUNT)
    for i in range(int(DIV_COUNT / 4) + 1):  # only do half and mirror later
        x = sin(radians(i * Deg_Step)) * OUTTER_RADIUS
        y = cos(radians(i * Deg_Step)) * OUTTER_RADIUS
        verts.append([x, y, 0])

    # FaceStart_Inside = len(verts)               # UNUSED
    verts.append([0, FLAT_RADIUS, 0])             # 10
    verts.append([Flat_Half, FLAT_RADIUS, 0])     # 11
    verts.append([Flat_Half, Flat_Half, 0])       # 12
    verts.append([FLAT_RADIUS, Flat_Half, 0])     # 13
    verts.append([FLAT_RADIUS, 0, 0])             # 14

    verts.append([0, Flat_Half, 0 - HEIGHT])          # 15
    verts.append([Flat_Half, Flat_Half, 0 - HEIGHT])  # 16
    verts.append([Flat_Half, 0, 0 - HEIGHT])          # 17

    verts.append([0, 0, 0 - HEIGHT])            # 18

    faces.extend(Phillips_Fill(FaceStart_Outside, True))

    Spin_Verts, Spin_Face = SpinDup(verts, faces, 360, 4, 'z')

    return Spin_Verts, Spin_Face, OUTTER_RADIUS * 2


# ####################################################################
#                    Create Head Types
# ####################################################################

def Max_Pan_Bit_Dia(HEAD_DIA):
    HEAD_RADIUS = HEAD_DIA * 0.5
    XRad = HEAD_RADIUS * 1.976
    return (sin(radians(10)) * XRad) * 2.0


def Create_Pan_Head(HOLE_DIA, HEAD_DIA, SHANK_DIA, HEIGHT, RAD1, RAD2, FACE_OFFSET, DIV_COUNT):

    HOLE_RADIUS = HOLE_DIA * 0.5
    HEAD_RADIUS = HEAD_DIA * 0.5
    SHANK_RADIUS = SHANK_DIA * 0.5

    verts = []
    faces = []
    Row = 0

    XRad = HEAD_RADIUS * 1.976
    ZRad = HEAD_RADIUS * 1.768
    EndRad = HEAD_RADIUS * 0.284
    EndZOffset = HEAD_RADIUS * 0.432
    HEIGHT = HEAD_RADIUS * 0.59

    """
    Dome_Rad =  5.6
    RAD_Offset = 4.9
    OtherRad = 0.8
    OtherRad_X_Offset = 4.2
    OtherRad_Z_Offset = 2.52
    XRad = 9.88
    ZRad = 8.84
    EndRad = 1.42
    EndZOffset = 2.16
    HEIGHT = 2.95
    """
    FaceStart = FACE_OFFSET

    z = cos(radians(10)) * ZRad
    verts.append([HOLE_RADIUS, 0.0, (0.0 - ZRad) + z])
    Start_Height = 0 - ((0.0 - ZRad) + z)
    Row += 1

    # for i in range(0,30,10):  was 0 to 30 more work needed to make this look good.
    for i in range(10, 30, 10):
        x = sin(radians(i)) * XRad
        z = cos(radians(i)) * ZRad
        verts.append([x, 0.0, (0.0 - ZRad) + z])
        Row += 1

    for i in range(20, 140, 10):
        x = sin(radians(i)) * EndRad
        z = cos(radians(i)) * EndRad
        if ((0.0 - EndZOffset) + z) < (0.0 - HEIGHT):
            verts.append([(HEAD_RADIUS - EndRad) + x, 0.0, 0.0 - HEIGHT])
        else:
            verts.append([(HEAD_RADIUS - EndRad) + x, 0.0, (0.0 - EndZOffset) + z])
        Row += 1

    verts.append([SHANK_RADIUS, 0.0, (0.0 - HEIGHT)])
    Row += 1

    verts.append([SHANK_RADIUS, 0.0, (0.0 - HEIGHT) - Start_Height])
    Row += 1

    sVerts, sFaces = SpinDup(verts, faces, 360, DIV_COUNT, 'z')
    sVerts.extend(verts)  # add the start verts to the Spin verts to complete the loop

    faces.extend(Build_Face_List_Quads(FaceStart, Row - 1, DIV_COUNT))

    # Global_Head_Height = HEIGHT  # UNUSED

    return Move_Verts_Up_Z(sVerts, Start_Height), faces, HEIGHT


def Create_Dome_Head(HOLE_DIA, HEAD_DIA, SHANK_DIA, HEIGHT, RAD1, RAD2, FACE_OFFSET, DIV_COUNT):
    HOLE_RADIUS = HOLE_DIA * 0.5
    HEAD_RADIUS = HEAD_DIA * 0.5
    SHANK_RADIUS = SHANK_DIA * 0.5

    verts = []
    faces = []
    Row = 0
    # Dome_Rad =  HEAD_RADIUS * (1.0/1.75)

    Dome_Rad = HEAD_RADIUS * 1.12
    # Head_Height = HEAD_RADIUS * 0.78
    RAD_Offset = HEAD_RADIUS * 0.98
    Dome_Height = HEAD_RADIUS * 0.64
    OtherRad = HEAD_RADIUS * 0.16
    OtherRad_X_Offset = HEAD_RADIUS * 0.84
    OtherRad_Z_Offset = HEAD_RADIUS * 0.504

    """
    Dome_Rad =  5.6
    RAD_Offset = 4.9
    Dome_Height = 3.2
    OtherRad = 0.8
    OtherRad_X_Offset = 4.2
    OtherRad_Z_Offset = 2.52
   """

    FaceStart = FACE_OFFSET

    verts.append([HOLE_RADIUS, 0.0, 0.0])
    Row += 1

    for i in range(0, 60, 10):
        x = sin(radians(i)) * Dome_Rad
        z = cos(radians(i)) * Dome_Rad
        if ((0.0 - RAD_Offset) + z) <= 0:
            verts.append([x, 0.0, (0.0 - RAD_Offset) + z])
            Row += 1

    for i in range(60, 160, 10):
        x = sin(radians(i)) * OtherRad
        z = cos(radians(i)) * OtherRad
        z = (0.0 - OtherRad_Z_Offset) + z
        if z < (0.0 - Dome_Height):
            z = (0.0 - Dome_Height)
        verts.append([OtherRad_X_Offset + x, 0.0, z])
        Row += 1

    verts.append([SHANK_RADIUS, 0.0, (0.0 - Dome_Height)])
    Row += 1

    sVerts, sFaces = SpinDup(verts, faces, 360, DIV_COUNT, 'z')
    sVerts.extend(verts)   # add the start verts to the Spin verts to complete the loop

    faces.extend(Build_Face_List_Quads(FaceStart, Row - 1, DIV_COUNT))

    return sVerts, faces, Dome_Height


def Create_CounterSink_Head(HOLE_DIA, HEAD_DIA, SHANK_DIA, HEIGHT, RAD1, DIV_COUNT):

    HOLE_RADIUS = HOLE_DIA * 0.5
    HEAD_RADIUS = HEAD_DIA * 0.5
    SHANK_RADIUS = SHANK_DIA * 0.5

    verts = []
    faces = []
    Row = 0

    # HEAD_RADIUS = (HEIGHT/tan(radians(60))) + SHANK_RADIUS
    HEIGHT = tan(radians(60)) * (HEAD_RADIUS - SHANK_RADIUS)

    FaceStart = len(verts)

    verts.append([HOLE_RADIUS, 0.0, 0.0])
    Row += 1

    # rad
    for i in range(0, 100, 10):
        x = sin(radians(i)) * RAD1
        z = cos(radians(i)) * RAD1
        verts.append([(HEAD_RADIUS - RAD1) + x, 0.0, (0.0 - RAD1) + z])
        Row += 1

    verts.append([SHANK_RADIUS, 0.0, 0.0 - HEIGHT])
    Row += 1

    sVerts, sFaces = SpinDup(verts, faces, 360, DIV_COUNT, 'z')
    sVerts.extend(verts)    # add the start verts to the Spin verts to complete the loop

    faces.extend(Build_Face_List_Quads(FaceStart, Row - 1, DIV_COUNT))

    return sVerts, faces, HEIGHT


def Create_Cap_Head(HOLE_DIA, HEAD_DIA, SHANK_DIA, HEIGHT, RAD1, RAD2, DIV_COUNT):

    HOLE_RADIUS = HOLE_DIA * 0.5
    HEAD_RADIUS = HEAD_DIA * 0.5
    SHANK_RADIUS = SHANK_DIA * 0.5

    verts = []
    faces = []
    Row = 0
    BEVEL = HEIGHT * 0.01

    FaceStart = len(verts)

    verts.append([HOLE_RADIUS, 0.0, 0.0])
    Row += 1

    # rad
    for i in range(0, 100, 10):
        x = sin(radians(i)) * RAD1
        z = cos(radians(i)) * RAD1
        verts.append([(HEAD_RADIUS - RAD1) + x, 0.0, (0.0 - RAD1) + z])
        Row += 1

    verts.append([HEAD_RADIUS, 0.0, 0.0 - HEIGHT + BEVEL])
    Row += 1

    verts.append([HEAD_RADIUS - BEVEL, 0.0, 0.0 - HEIGHT])
    Row += 1

    # rad2
    for i in range(0, 100, 10):
        x = sin(radians(i)) * RAD2
        z = cos(radians(i)) * RAD2
        verts.append([(SHANK_RADIUS + RAD2) - x, 0.0, (0.0 - HEIGHT - RAD2) + z])
        Row += 1

    sVerts, sFaces = SpinDup(verts, faces, 360, DIV_COUNT, 'z')
    sVerts.extend(verts)    # add the start verts to the Spin verts to complete the loop

    faces.extend(Build_Face_List_Quads(FaceStart, Row - 1, DIV_COUNT))

    return sVerts, faces, HEIGHT + RAD2


def Create_Hex_Head(FLAT, HOLE_DIA, SHANK_DIA, HEIGHT):

    verts = []
    faces = []
    HOLE_RADIUS = HOLE_DIA * 0.5
    Half_Flat = FLAT / 2
    TopBevelRadius = Half_Flat - (Half_Flat * (0.05 / 8))
    Undercut_Height = (Half_Flat * (0.05 / 8))
    Shank_Bevel = (Half_Flat * (0.05 / 8))
    Flat_Height = HEIGHT - Undercut_Height - Shank_Bevel
    # Undercut_Height = 5
    SHANK_RADIUS = SHANK_DIA / 2
    Row = 0

    verts.append([0.0, 0.0, 0.0])

    FaceStart = len(verts)

    # inner hole
    x = sin(radians(0)) * HOLE_RADIUS
    y = cos(radians(0)) * HOLE_RADIUS
    verts.append([x, y, 0.0])

    x = sin(radians(60 / 6)) * HOLE_RADIUS
    y = cos(radians(60 / 6)) * HOLE_RADIUS
    verts.append([x, y, 0.0])

    x = sin(radians(60 / 3)) * HOLE_RADIUS
    y = cos(radians(60 / 3)) * HOLE_RADIUS
    verts.append([x, y, 0.0])

    x = sin(radians(60 / 2)) * HOLE_RADIUS
    y = cos(radians(60 / 2)) * HOLE_RADIUS
    verts.append([x, y, 0.0])
    Row += 1

    # bevel
    x = sin(radians(0)) * TopBevelRadius
    y = cos(radians(0)) * TopBevelRadius
    vec1 = Vector([x, y, 0.0])
    verts.append([x, y, 0.0])

    x = sin(radians(60 / 6)) * TopBevelRadius
    y = cos(radians(60 / 6)) * TopBevelRadius
    vec2 = Vector([x, y, 0.0])
    verts.append([x, y, 0.0])

    x = sin(radians(60 / 3)) * TopBevelRadius
    y = cos(radians(60 / 3)) * TopBevelRadius
    vec3 = Vector([x, y, 0.0])
    verts.append([x, y, 0.0])

    x = sin(radians(60 / 2)) * TopBevelRadius
    y = cos(radians(60 / 2)) * TopBevelRadius
    vec4 = Vector([x, y, 0.0])
    verts.append([x, y, 0.0])
    Row += 1

    # Flats
    x = tan(radians(0)) * Half_Flat
    dvec = vec1 - Vector([x, Half_Flat, 0.0])
    verts.append([x, Half_Flat, -dvec.length])

    x = tan(radians(60 / 6)) * Half_Flat
    dvec = vec2 - Vector([x, Half_Flat, 0.0])
    verts.append([x, Half_Flat, -dvec.length])

    x = tan(radians(60 / 3)) * Half_Flat
    dvec = vec3 - Vector([x, Half_Flat, 0.0])
    Lowest_Point = -dvec.length
    verts.append([x, Half_Flat, -dvec.length])

    x = tan(radians(60 / 2)) * Half_Flat
    dvec = vec4 - Vector([x, Half_Flat, 0.0])
    Lowest_Point = -dvec.length
    verts.append([x, Half_Flat, -dvec.length])
    Row += 1

    # down Bits Tri
    x = tan(radians(0)) * Half_Flat
    verts.append([x, Half_Flat, Lowest_Point])

    x = tan(radians(60 / 6)) * Half_Flat
    verts.append([x, Half_Flat, Lowest_Point])

    x = tan(radians(60 / 3)) * Half_Flat
    verts.append([x, Half_Flat, Lowest_Point])

    x = tan(radians(60 / 2)) * Half_Flat
    verts.append([x, Half_Flat, Lowest_Point])
    Row += 1

    # down Bits

    x = tan(radians(0)) * Half_Flat
    verts.append([x, Half_Flat, -Flat_Height])

    x = tan(radians(60 / 6)) * Half_Flat
    verts.append([x, Half_Flat, -Flat_Height])

    x = tan(radians(60 / 3)) * Half_Flat
    verts.append([x, Half_Flat, -Flat_Height])

    x = tan(radians(60 / 2)) * Half_Flat
    verts.append([x, Half_Flat, -Flat_Height])
    Row += 1

    # Under cut
    x = sin(radians(0)) * Half_Flat
    y = cos(radians(0)) * Half_Flat
    vec1 = Vector([x, y, 0.0])
    verts.append([x, y, -Flat_Height])

    x = sin(radians(60 / 6)) * Half_Flat
    y = cos(radians(60 / 6)) * Half_Flat
    vec2 = Vector([x, y, 0.0])
    verts.append([x, y, -Flat_Height])

    x = sin(radians(60 / 3)) * Half_Flat
    y = cos(radians(60 / 3)) * Half_Flat
    vec3 = Vector([x, y, 0.0])
    verts.append([x, y, -Flat_Height])

    x = sin(radians(60 / 2)) * Half_Flat
    y = cos(radians(60 / 2)) * Half_Flat
    vec3 = Vector([x, y, 0.0])
    verts.append([x, y, -Flat_Height])
    Row += 1

    # Under cut down bit
    x = sin(radians(0)) * Half_Flat
    y = cos(radians(0)) * Half_Flat
    vec1 = Vector([x, y, 0.0])
    verts.append([x, y, -Flat_Height - Undercut_Height])

    x = sin(radians(60 / 6)) * Half_Flat
    y = cos(radians(60 / 6)) * Half_Flat
    vec2 = Vector([x, y, 0.0])
    verts.append([x, y, -Flat_Height - Undercut_Height])

    x = sin(radians(60 / 3)) * Half_Flat
    y = cos(radians(60 / 3)) * Half_Flat
    vec3 = Vector([x, y, 0.0])
    verts.append([x, y, -Flat_Height - Undercut_Height])

    x = sin(radians(60 / 2)) * Half_Flat
    y = cos(radians(60 / 2)) * Half_Flat
    vec3 = Vector([x, y, 0.0])
    verts.append([x, y, -Flat_Height - Undercut_Height])
    Row += 1

    # Under cut to Shank BEVEL
    x = sin(radians(0)) * (SHANK_RADIUS + Shank_Bevel)
    y = cos(radians(0)) * (SHANK_RADIUS + Shank_Bevel)
    vec1 = Vector([x, y, 0.0])
    verts.append([x, y, -Flat_Height - Undercut_Height])

    x = sin(radians(60 / 6)) * (SHANK_RADIUS + Shank_Bevel)
    y = cos(radians(60 / 6)) * (SHANK_RADIUS + Shank_Bevel)
    vec2 = Vector([x, y, 0.0])
    verts.append([x, y, -Flat_Height - Undercut_Height])

    x = sin(radians(60 / 3)) * (SHANK_RADIUS + Shank_Bevel)
    y = cos(radians(60 / 3)) * (SHANK_RADIUS + Shank_Bevel)
    vec3 = Vector([x, y, 0.0])
    verts.append([x, y, -Flat_Height - Undercut_Height])

    x = sin(radians(60 / 2)) * (SHANK_RADIUS + Shank_Bevel)
    y = cos(radians(60 / 2)) * (SHANK_RADIUS + Shank_Bevel)
    vec3 = Vector([x, y, 0.0])
    verts.append([x, y, -Flat_Height - Undercut_Height])
    Row += 1

    # Under cut to Shank BEVEL
    x = sin(radians(0)) * SHANK_RADIUS
    y = cos(radians(0)) * SHANK_RADIUS
    vec1 = Vector([x, y, 0.0])
    verts.append([x, y, -Flat_Height - Undercut_Height - Shank_Bevel])

    x = sin(radians(60 / 6)) * SHANK_RADIUS
    y = cos(radians(60 / 6)) * SHANK_RADIUS
    vec2 = Vector([x, y, 0.0])
    verts.append([x, y, -Flat_Height - Undercut_Height - Shank_Bevel])

    x = sin(radians(60 / 3)) * SHANK_RADIUS
    y = cos(radians(60 / 3)) * SHANK_RADIUS
    vec3 = Vector([x, y, 0.0])
    verts.append([x, y, -Flat_Height - Undercut_Height - Shank_Bevel])

    x = sin(radians(60 / 2)) * SHANK_RADIUS
    y = cos(radians(60 / 2)) * SHANK_RADIUS
    vec3 = Vector([x, y, 0.0])
    verts.append([x, y, -Flat_Height - Undercut_Height - Shank_Bevel])
    Row += 1

    faces.extend(Build_Face_List_Quads(FaceStart, 3, Row - 1))

    Mirror_Verts, Mirror_Faces = Mirror_Verts_Faces(verts, faces, 'y')
    verts.extend(Mirror_Verts)
    faces.extend(Mirror_Faces)

    Spin_Verts, Spin_Faces = SpinDup(verts, faces, 360, 6, 'z')

    return Spin_Verts, Spin_Faces, 0 - (-HEIGHT)



def Create_12_Point(FLAT, HOLE_DIA, SHANK_DIA, HEIGHT,FLANGE_DIA):
    FLANGE_HEIGHT = (1.89/8.0)*HEIGHT
    FLAT_HEIGHT = (4.18/8.0)*HEIGHT
#     FLANGE_DIA = (13.27/8.0)*FLAT
    
    FLANGE_RADIUS = FLANGE_DIA * 0.5
    FLANGE_TAPPER_HEIGHT =  HEIGHT - FLANGE_HEIGHT - FLAT_HEIGHT 
    
#     HOLE_DIA = 0.0
    
    verts = []
    faces = []
    HOLE_RADIUS = HOLE_DIA / 2
    Half_Flat = FLAT / 2
    TopBevelRadius = Half_Flat - (Half_Flat * (0.05 / 8))
#     Undercut_Height = (Half_Flat * (0.05 / 8))
#     Shank_Bevel = (Half_Flat * (0.05 / 8))
#     Flat_Height = HEIGHT - Undercut_Height - Shank_Bevel
    # Undercut_Height = 5
    SHANK_RADIUS = SHANK_DIA / 2
    Row = 0

    verts.append([0.0, 0.0, 0.0])

#     print("HOLE_RADIUS" + str(HOLE_RADIUS))  
#     print("TopBevelRadius" + str(TopBevelRadius))

    FaceStart = len(verts)

    # inner hole
    x = sin(radians(0)) * HOLE_RADIUS
    y = cos(radians(0)) * HOLE_RADIUS
    verts.append([x, y, 0.0])

    x = sin(radians(5)) * HOLE_RADIUS
    y = cos(radians(5)) * HOLE_RADIUS
    verts.append([x, y, 0.0])

    x = sin(radians(10)) * HOLE_RADIUS
    y = cos(radians(10)) * HOLE_RADIUS
    verts.append([x, y, 0.0])

    x = sin(radians(15)) * HOLE_RADIUS
    y = cos(radians(15)) * HOLE_RADIUS
    verts.append([x, y, 0.0])

    x = sin(radians(20)) * HOLE_RADIUS
    y = cos(radians(20)) * HOLE_RADIUS
    verts.append([x, y, 0.0])
    
    x = sin(radians(25)) * HOLE_RADIUS
    y = cos(radians(25)) * HOLE_RADIUS
    verts.append([x, y, 0.0])
    
    x = sin(radians(30)) * HOLE_RADIUS
    y = cos(radians(30)) * HOLE_RADIUS
    verts.append([x, y, 0.0])
       
    Row += 1



    # bevel
    x = sin(radians(0)) * TopBevelRadius
    y = cos(radians(0)) * TopBevelRadius
    vec1 = Vector([x, y, 0.0])
    verts.append([x, y, 0.0])

    x = sin(radians(5)) * TopBevelRadius
    y = cos(radians(5)) * TopBevelRadius
    vec2 = Vector([x, y, 0.0])
    verts.append([x, y, 0.0])

    x = sin(radians(10)) * TopBevelRadius
    y = cos(radians(10)) * TopBevelRadius
    vec3 = Vector([x, y, 0.0])
    verts.append([x, y, 0.0])

    x = sin(radians(15)) * TopBevelRadius
    y = cos(radians(15)) * TopBevelRadius
    vec4 = Vector([x, y, 0.0])
    verts.append([x, y, 0.0])
    
    x = sin(radians(20)) * TopBevelRadius
    y = cos(radians(20)) * TopBevelRadius
    vec5 = Vector([x, y, 0.0])
    verts.append([x, y, 0.0])
    
    x = sin(radians(25)) * TopBevelRadius
    y = cos(radians(25)) * TopBevelRadius
    vec6 = Vector([x, y, 0.0])
    verts.append([x, y, 0.0])
    
    x = sin(radians(30)) * TopBevelRadius
    y = cos(radians(30)) * TopBevelRadius
    vec7 = Vector([x, y, 0.0])
    verts.append([x, y, 0.0])

    Row += 1


    #45Deg bevel on the top
    
    #First we work out how far up the Y axis the vert is
    v_origin = Vector([0.0,0.0,0.0]) # center of the model
    v_15Deg_Point = Vector([tan(radians(15)) * Half_Flat,Half_Flat,0.0])  #Is a know point to work back from 
    
    x = tan(radians(0)) * Half_Flat
    Point_Distance =(tan(radians(30)) * v_15Deg_Point.x)+Half_Flat
    dvec = vec1 - Vector([x, Point_Distance, 0.0])
    verts.append([x, Point_Distance, -dvec.length])
    v_0_Deg_Top_Point = Vector([x, Point_Distance, -dvec.length])

    v_0_Deg_Point = Vector([x, Point_Distance,0.0])
    
    v_5Deg_Line = Vector([tan(radians(5)) * Half_Flat, Half_Flat, 0.0])
    v_5Deg_Line.length *= 2  # extende out the line on a 5 deg angle

    #We cross 2 lines. One from the origin to the 0 Deg point
    #and the second is from the orign extended out past the first line
    # This gives the cross point of the    
    v_Cross = geometry.intersect_line_line_2d(v_0_Deg_Point,v_15Deg_Point,v_origin,v_5Deg_Line)
    dvec = vec2 - Vector([v_Cross.x,v_Cross.y,0.0])
    verts.append([v_Cross.x,v_Cross.y,-dvec.length])
    v_5_Deg_Top_Point = Vector([v_Cross.x,v_Cross.y,-dvec.length])
    
    v_10Deg_Line = Vector([tan(radians(10)) * Half_Flat, Half_Flat, 0.0])
    v_10Deg_Line.length *= 2  # extende out the line

    v_Cross = geometry.intersect_line_line_2d(v_0_Deg_Point,v_15Deg_Point,v_origin,v_10Deg_Line)
    dvec = vec3 - Vector([v_Cross.x,v_Cross.y,0.0])
    verts.append([v_Cross.x,v_Cross.y,-dvec.length])
    v_10_Deg_Top_Point = Vector([v_Cross.x,v_Cross.y,-dvec.length])
        
    #The remain points are stright forward because y is all the same y height (Half_Flat)  
    x = tan(radians(15)) * Half_Flat
    dvec = vec4 - Vector([x, Half_Flat, 0.0])
    Lowest_Point = -dvec.length
    verts.append([x, Half_Flat, -dvec.length])
    v_15_Deg_Top_Point = Vector([x, Half_Flat, -dvec.length])
    
    x = tan(radians(20)) * Half_Flat
    dvec = vec5 - Vector([x, Half_Flat, 0.0])
    Lowest_Point = -dvec.length
    verts.append([x, Half_Flat, -dvec.length])
    v_20_Deg_Top_Point = Vector([x, Half_Flat, -dvec.length])

    x = tan(radians(25)) * Half_Flat
    dvec = vec6 - Vector([x, Half_Flat, 0.0])
    Lowest_Point = -dvec.length
    verts.append([x, Half_Flat, -dvec.length])
    v_25_Deg_Top_Point = Vector([x, Half_Flat, -dvec.length])

    x = tan(radians(30)) * Half_Flat
    dvec = vec7 - Vector([x, Half_Flat, 0.0])
    Lowest_Point = -dvec.length
    verts.append([x, Half_Flat, -dvec.length])
    v_30_Deg_Top_Point = Vector([x, Half_Flat, -dvec.length])
    Row += 1

    
    #Down Bits
#     print ("Point_Distance")
#     print (Point_Distance)
    


    Flange_Adjacent  = FLANGE_RADIUS - Point_Distance
    if (Flange_Adjacent  == 0.0):
        Flange_Adjacent  = 0.000001
    Flange_Opposite = FLANGE_TAPPER_HEIGHT         
        
#     print ("Flange_Opposite")
#     print (Flange_Opposite)
#     print ("Flange_Adjacent")
#     print (Flange_Adjacent)
        
    FLANGE_ANGLE_RAD = atan(Flange_Opposite/Flange_Adjacent )
#     FLANGE_ANGLE_RAD = radians(45)
#     print("FLANGE_ANGLE_RAD")
#     print (degrees (FLANGE_ANGLE_RAD)) 
    
    
    v_Extended_Flange_Edge = Vector([0.0,0.0,-HEIGHT + FLANGE_HEIGHT + (tan(FLANGE_ANGLE_RAD)* FLANGE_RADIUS) ])
#     print("v_Extended_Flange_Edge")
#     print (v_Extended_Flange_Edge) 

    #0deg
    v_Flange_Edge = Vector([sin(radians(0)) * FLANGE_RADIUS,cos(radians(0)) * FLANGE_RADIUS,-HEIGHT + FLANGE_HEIGHT ])
    v_Cross = geometry.intersect_line_line(v_0_Deg_Top_Point,Vector([v_0_Deg_Top_Point.x,v_0_Deg_Top_Point.y,-HEIGHT]),v_Flange_Edge,v_Extended_Flange_Edge)
    verts.append(v_Cross[0])
    
    #5deg
    v_Flange_Edge = Vector([sin(radians(5)) * FLANGE_RADIUS,cos(radians(5)) * FLANGE_RADIUS,-HEIGHT + FLANGE_HEIGHT ])
    v_Cross = geometry.intersect_line_line(v_5_Deg_Top_Point,Vector([v_5_Deg_Top_Point.x,v_5_Deg_Top_Point.y,-HEIGHT]),v_Flange_Edge,v_Extended_Flange_Edge)
    verts.append(v_Cross[0])
    
    #10deg
    v_Flange_Edge = Vector([sin(radians(10)) * FLANGE_RADIUS,cos(radians(10)) * FLANGE_RADIUS,-HEIGHT + FLANGE_HEIGHT ])
    v_Cross = geometry.intersect_line_line(v_10_Deg_Top_Point,Vector([v_10_Deg_Top_Point.x,v_10_Deg_Top_Point.y,-HEIGHT]),v_Flange_Edge,v_Extended_Flange_Edge)
    verts.append(v_Cross[0])

    #15deg
    v_Flange_Edge = Vector([sin(radians(15)) * FLANGE_RADIUS,cos(radians(15)) * FLANGE_RADIUS,-HEIGHT + FLANGE_HEIGHT ])
    v_Cross = geometry.intersect_line_line(v_15_Deg_Top_Point,Vector([v_15_Deg_Top_Point.x,v_15_Deg_Top_Point.y,-HEIGHT]),v_Flange_Edge,v_Extended_Flange_Edge)
    verts.append(v_Cross[0])


    #20deg
    v_Flange_Edge = Vector([sin(radians(20)) * FLANGE_RADIUS,cos(radians(20)) * FLANGE_RADIUS,-HEIGHT + FLANGE_HEIGHT ])
    v_Cross = geometry.intersect_line_line(v_20_Deg_Top_Point,Vector([v_20_Deg_Top_Point.x,v_20_Deg_Top_Point.y,-HEIGHT]),v_Flange_Edge,v_Extended_Flange_Edge)
    verts.append(v_Cross[0])
    
    #25deg
    v_Flange_Edge = Vector([sin(radians(25)) * FLANGE_RADIUS,cos(radians(25)) * FLANGE_RADIUS,-HEIGHT + FLANGE_HEIGHT ])
    v_Cross = geometry.intersect_line_line(v_25_Deg_Top_Point,Vector([v_25_Deg_Top_Point.x,v_25_Deg_Top_Point.y,-HEIGHT]),v_Flange_Edge,v_Extended_Flange_Edge)
    verts.append(v_Cross[0])
    
    
    #30deg
    v_Flange_Edge = Vector([sin(radians(30)) * FLANGE_RADIUS,cos(radians(30)) * FLANGE_RADIUS,-HEIGHT + FLANGE_HEIGHT ])
    v_Cross = geometry.intersect_line_line(v_30_Deg_Top_Point,Vector([v_30_Deg_Top_Point.x,v_30_Deg_Top_Point.y,-HEIGHT]),v_Flange_Edge,v_Extended_Flange_Edge)
    verts.append(v_Cross[0])

    Row += 1



    verts.append([sin(radians(0)) * FLANGE_RADIUS,cos(radians(0)) * FLANGE_RADIUS,-HEIGHT + FLANGE_HEIGHT ])
    verts.append([sin(radians(5)) * FLANGE_RADIUS,cos(radians(5)) * FLANGE_RADIUS,-HEIGHT + FLANGE_HEIGHT])
    verts.append([sin(radians(10)) * FLANGE_RADIUS,cos(radians(10)) * FLANGE_RADIUS,-HEIGHT + FLANGE_HEIGHT])
    verts.append([sin(radians(15)) * FLANGE_RADIUS,cos(radians(15)) * FLANGE_RADIUS,-HEIGHT + FLANGE_HEIGHT])
    verts.append([sin(radians(20)) * FLANGE_RADIUS,cos(radians(20)) * FLANGE_RADIUS,-HEIGHT + FLANGE_HEIGHT])
    verts.append([sin(radians(25)) * FLANGE_RADIUS,cos(radians(25)) * FLANGE_RADIUS,-HEIGHT + FLANGE_HEIGHT])
    verts.append([sin(radians(30)) * FLANGE_RADIUS,cos(radians(30)) * FLANGE_RADIUS,-HEIGHT + FLANGE_HEIGHT])
       
    Row += 1

    verts.append([sin(radians(0)) * FLANGE_RADIUS,cos(radians(0)) * FLANGE_RADIUS,-HEIGHT])
    verts.append([sin(radians(5)) * FLANGE_RADIUS,cos(radians(5)) * FLANGE_RADIUS,-HEIGHT])
    verts.append([sin(radians(10)) * FLANGE_RADIUS,cos(radians(10)) * FLANGE_RADIUS,-HEIGHT])
    verts.append([sin(radians(15)) * FLANGE_RADIUS,cos(radians(15)) * FLANGE_RADIUS,-HEIGHT])
    verts.append([sin(radians(20)) * FLANGE_RADIUS,cos(radians(20)) * FLANGE_RADIUS,-HEIGHT])
    verts.append([sin(radians(25)) * FLANGE_RADIUS,cos(radians(25)) * FLANGE_RADIUS,-HEIGHT])
    verts.append([sin(radians(30)) * FLANGE_RADIUS,cos(radians(30)) * FLANGE_RADIUS,-HEIGHT])
        
    Row += 1

    
    verts.append([sin(radians(0)) * SHANK_RADIUS,cos(radians(0)) * SHANK_RADIUS,-HEIGHT])
    verts.append([sin(radians(0)) * SHANK_RADIUS,cos(radians(0)) * SHANK_RADIUS,-HEIGHT])
    verts.append([sin(radians(10)) * SHANK_RADIUS,cos(radians(10)) * SHANK_RADIUS,-HEIGHT])
    verts.append([sin(radians(10)) * SHANK_RADIUS,cos(radians(10)) * SHANK_RADIUS,-HEIGHT])
    verts.append([sin(radians(20)) * SHANK_RADIUS,cos(radians(20)) * SHANK_RADIUS,-HEIGHT])
    verts.append([sin(radians(20)) * SHANK_RADIUS,cos(radians(20)) * SHANK_RADIUS,-HEIGHT])
    verts.append([sin(radians(30)) * SHANK_RADIUS,cos(radians(30)) * SHANK_RADIUS,-HEIGHT])
        
    Row += 1


    faces.extend(Build_Face_List_Quads(FaceStart, 6, Row - 1))

    Spin_Verts, Spin_Faces = SpinDup(verts, faces, 360,12, 'z')

    return Spin_Verts, Spin_Faces, 0 - (-HEIGHT)


def Create_12_Point_Head(FLAT, HOLE_DIA, SHANK_DIA, HEIGHT,FLANGE_DIA):
    #TODO add under head radius
    return  Create_12_Point(FLAT, HOLE_DIA, SHANK_DIA, HEIGHT,FLANGE_DIA)
    
    

# ####################################################################
#                    Create External Thread
# ####################################################################


def Thread_Start3(verts, INNER_RADIUS, OUTTER_RADIUS, PITCH, DIV_COUNT,
                  CREST_PERCENT, ROOT_PERCENT, Height_Offset):

    Ret_Row = 0

    Height_Start = Height_Offset - PITCH
    Height_Step = float(PITCH) / float(DIV_COUNT)
    Deg_Step = 360.0 / float(DIV_COUNT)

    Crest_Height = float(PITCH) * float(CREST_PERCENT) / float(100)
    Root_Height = float(PITCH) * float(ROOT_PERCENT) / float(100)
    Root_to_Crest_Height = Crest_to_Root_Height = \
                        (float(PITCH) - (Crest_Height + Root_Height)) / 2.0

    # thread start
    Rank = float(OUTTER_RADIUS - INNER_RADIUS) / float(DIV_COUNT)
    for j in range(4):

        for i in range(DIV_COUNT + 1):
            z = Height_Offset - (Height_Step * i)
            if z > Height_Start:
                z = Height_Start
            x = sin(radians(i * Deg_Step)) * OUTTER_RADIUS
            y = cos(radians(i * Deg_Step)) * OUTTER_RADIUS
            verts.append([x, y, z])
        Height_Offset -= Crest_Height
        Ret_Row += 1

        for i in range(DIV_COUNT + 1):
            z = Height_Offset - (Height_Step * i)
            if z > Height_Start:
                z = Height_Start

            x = sin(radians(i * Deg_Step)) * OUTTER_RADIUS
            y = cos(radians(i * Deg_Step)) * OUTTER_RADIUS
            verts.append([x, y, z])
        Height_Offset -= Crest_to_Root_Height
        Ret_Row += 1

        for i in range(DIV_COUNT + 1):
            z = Height_Offset - (Height_Step * i)
            if z > Height_Start:
                z = Height_Start

            x = sin(radians(i * Deg_Step)) * INNER_RADIUS
            y = cos(radians(i * Deg_Step)) * INNER_RADIUS
            if j == 0:
                x = sin(radians(i * Deg_Step)) * (OUTTER_RADIUS - (i * Rank))
                y = cos(radians(i * Deg_Step)) * (OUTTER_RADIUS - (i * Rank))
            verts.append([x, y, z])
        Height_Offset -= Root_Height
        Ret_Row += 1

        for i in range(DIV_COUNT + 1):
            z = Height_Offset - (Height_Step * i)
            if z > Height_Start:
                z = Height_Start

            x = sin(radians(i * Deg_Step)) * INNER_RADIUS
            y = cos(radians(i * Deg_Step)) * INNER_RADIUS

            if j == 0:
                x = sin(radians(i * Deg_Step)) * (OUTTER_RADIUS - (i * Rank))
                y = cos(radians(i * Deg_Step)) * (OUTTER_RADIUS - (i * Rank))
            verts.append([x, y, z])
        Height_Offset -= Root_to_Crest_Height
        Ret_Row += 1

    return Ret_Row, Height_Offset


def Create_Shank_Verts(START_DIA, OUTTER_DIA, LENGTH, Z_LOCATION, DIV_COUNT):

    verts = []

    START_RADIUS = START_DIA / 2
    OUTTER_RADIUS = OUTTER_DIA / 2

    Opp = abs(START_RADIUS - OUTTER_RADIUS)
    Taper_Lentgh = Opp / tan(radians(31))

    if Taper_Lentgh > LENGTH:
        Taper_Lentgh = 0

    Stright_Length = LENGTH - Taper_Lentgh

    Deg_Step = 360.0 / float(DIV_COUNT)

    Row = 0

    Lowest_Z_Vert = 0

    Height_Offset = Z_LOCATION

    # Ring
    for i in range(DIV_COUNT + 1):
        x = sin(radians(i * Deg_Step)) * START_RADIUS
        y = cos(radians(i * Deg_Step)) * START_RADIUS
        z = Height_Offset - 0
        verts.append([x, y, z])
        Lowest_Z_Vert = min(Lowest_Z_Vert, z)
    Height_Offset -= Stright_Length
    Row += 1

    for i in range(DIV_COUNT + 1):
        x = sin(radians(i * Deg_Step)) * START_RADIUS
        y = cos(radians(i * Deg_Step)) * START_RADIUS
        z = Height_Offset - 0
        verts.append([x, y, z])
        Lowest_Z_Vert = min(Lowest_Z_Vert, z)
    Height_Offset -= Taper_Lentgh
    Row += 1

    return verts, Row, Height_Offset


def Create_Thread_Start_Verts(INNER_DIA, OUTTER_DIA, PITCH, CREST_PERCENT,
                              ROOT_PERCENT, Z_LOCATION, DIV_COUNT):

    verts = []

    INNER_RADIUS = INNER_DIA / 2
    OUTTER_RADIUS = OUTTER_DIA / 2

    Deg_Step = 360.0 / float(DIV_COUNT)
    Height_Step = float(PITCH) / float(DIV_COUNT)

    Row = 0

    Lowest_Z_Vert = 0

    Height_Offset = Z_LOCATION

    Height_Start = Height_Offset

    Crest_Height = float(PITCH) * float(CREST_PERCENT) / float(100)
    Root_Height = float(PITCH) * float(ROOT_PERCENT) / float(100)
    Root_to_Crest_Height = Crest_to_Root_Height = \
                        (float(PITCH) - (Crest_Height + Root_Height)) / 2.0

    Rank = float(OUTTER_RADIUS - INNER_RADIUS) / float(DIV_COUNT)

    Height_Offset = Z_LOCATION + PITCH
    Cut_off = Z_LOCATION

    for j in range(1):

        for i in range(DIV_COUNT + 1):
            x = sin(radians(i * Deg_Step)) * OUTTER_RADIUS
            y = cos(radians(i * Deg_Step)) * OUTTER_RADIUS
            z = Height_Offset - (Height_Step * i)
            if z > Cut_off:
                z = Cut_off
            verts.append([x, y, z])
            Lowest_Z_Vert = min(Lowest_Z_Vert, z)
        Height_Offset -= Crest_Height
        Row += 1

        for i in range(DIV_COUNT + 1):
            x = sin(radians(i * Deg_Step)) * OUTTER_RADIUS
            y = cos(radians(i * Deg_Step)) * OUTTER_RADIUS
            z = Height_Offset - (Height_Step * i)
            if z > Cut_off:
                z = Cut_off
            verts.append([x, y, z])
            Lowest_Z_Vert = min(Lowest_Z_Vert, z)
        Height_Offset -= Crest_to_Root_Height
        Row += 1

        for i in range(DIV_COUNT + 1):
            x = sin(radians(i * Deg_Step)) * OUTTER_RADIUS
            y = cos(radians(i * Deg_Step)) * OUTTER_RADIUS
            z = Height_Offset - (Height_Step * i)
            if z > Cut_off:
                z = Cut_off
            verts.append([x, y, z])
            Lowest_Z_Vert = min(Lowest_Z_Vert, z)
        Height_Offset -= Root_Height
        Row += 1

        for i in range(DIV_COUNT + 1):
            x = sin(radians(i * Deg_Step)) * OUTTER_RADIUS
            y = cos(radians(i * Deg_Step)) * OUTTER_RADIUS
            z = Height_Offset - (Height_Step * i)
            if z > Cut_off:
                z = Cut_off
            verts.append([x, y, z])
            Lowest_Z_Vert = min(Lowest_Z_Vert, z)
        Height_Offset -= Root_to_Crest_Height
        Row += 1

    for j in range(2):
        for i in range(DIV_COUNT + 1):
            z = Height_Offset - (Height_Step * i)
            if z > Height_Start:
                z = Height_Start
            x = sin(radians(i * Deg_Step)) * OUTTER_RADIUS
            y = cos(radians(i * Deg_Step)) * OUTTER_RADIUS
            verts.append([x, y, z])
            Lowest_Z_Vert = min(Lowest_Z_Vert, z)
        Height_Offset -= Crest_Height
        Row += 1

        for i in range(DIV_COUNT + 1):
            z = Height_Offset - (Height_Step * i)
            if z > Height_Start:
                z = Height_Start

            x = sin(radians(i * Deg_Step)) * OUTTER_RADIUS
            y = cos(radians(i * Deg_Step)) * OUTTER_RADIUS
            verts.append([x, y, z])
            Lowest_Z_Vert = min(Lowest_Z_Vert, z)
        Height_Offset -= Crest_to_Root_Height
        Row += 1

        for i in range(DIV_COUNT + 1):
            z = Height_Offset - (Height_Step * i)
            if z > Height_Start:
                z = Height_Start

            x = sin(radians(i * Deg_Step)) * INNER_RADIUS
            y = cos(radians(i * Deg_Step)) * INNER_RADIUS
            if j == 0:
                x = sin(radians(i * Deg_Step)) * (OUTTER_RADIUS - (i * Rank))
                y = cos(radians(i * Deg_Step)) * (OUTTER_RADIUS - (i * Rank))
            verts.append([x, y, z])
            Lowest_Z_Vert = min(Lowest_Z_Vert, z)
        Height_Offset -= Root_Height
        Row += 1

        for i in range(DIV_COUNT + 1):
            z = Height_Offset - (Height_Step * i)
            if z > Height_Start:
                z = Height_Start

            x = sin(radians(i * Deg_Step)) * INNER_RADIUS
            y = cos(radians(i * Deg_Step)) * INNER_RADIUS

            if j == 0:
                x = sin(radians(i * Deg_Step)) * (OUTTER_RADIUS - (i * Rank))
                y = cos(radians(i * Deg_Step)) * (OUTTER_RADIUS - (i * Rank))
            verts.append([x, y, z])
            Lowest_Z_Vert = min(Lowest_Z_Vert, z)
        Height_Offset -= Root_to_Crest_Height
        Row += 1

    return verts, Row, Height_Offset


def Create_Thread_Verts(INNER_DIA, OUTTER_DIA, PITCH, HEIGHT,
                        CREST_PERCENT, ROOT_PERCENT, Z_LOCATION, DIV_COUNT):

    verts = []

    INNER_RADIUS = INNER_DIA / 2
    OUTTER_RADIUS = OUTTER_DIA / 2

    Deg_Step = 360.0 / float(DIV_COUNT)
    Height_Step = float(PITCH) / float(DIV_COUNT)

    NUM_OF_START_THREADS = 4.0
    NUM_OF_END_THREADS = 3.0
    Num = int((HEIGHT - ((NUM_OF_START_THREADS * PITCH) + (NUM_OF_END_THREADS * PITCH))) / PITCH)
    Row = 0

    Crest_Height = float(PITCH) * float(CREST_PERCENT) / float(100)
    Root_Height = float(PITCH) * float(ROOT_PERCENT) / float(100)
    Root_to_Crest_Height = Crest_to_Root_Height = \
                        (float(PITCH) - (Crest_Height + Root_Height)) / 2.0

    Height_Offset = Z_LOCATION

    Lowest_Z_Vert = 0

    for j in range(Num):

        for i in range(DIV_COUNT + 1):
            x = sin(radians(i * Deg_Step)) * OUTTER_RADIUS
            y = cos(radians(i * Deg_Step)) * OUTTER_RADIUS
            z = Height_Offset - (Height_Step * i)
            verts.append([x, y, z])
            Lowest_Z_Vert = min(Lowest_Z_Vert, z)
        Height_Offset -= Crest_Height
        Row += 1

        for i in range(DIV_COUNT + 1):
            x = sin(radians(i * Deg_Step)) * OUTTER_RADIUS
            y = cos(radians(i * Deg_Step)) * OUTTER_RADIUS
            z = Height_Offset - (Height_Step * i)
            verts.append([x, y, z])
            Lowest_Z_Vert = min(Lowest_Z_Vert, z)
        Height_Offset -= Crest_to_Root_Height
        Row += 1

        for i in range(DIV_COUNT + 1):
            x = sin(radians(i * Deg_Step)) * INNER_RADIUS
            y = cos(radians(i * Deg_Step)) * INNER_RADIUS
            z = Height_Offset - (Height_Step * i)
            verts.append([x, y, z])
            Lowest_Z_Vert = min(Lowest_Z_Vert, z)
        Height_Offset -= Root_Height
        Row += 1

        for i in range(DIV_COUNT + 1):
            x = sin(radians(i * Deg_Step)) * INNER_RADIUS
            y = cos(radians(i * Deg_Step)) * INNER_RADIUS
            z = Height_Offset - (Height_Step * i)
            verts.append([x, y, z])
            Lowest_Z_Vert = min(Lowest_Z_Vert, z)
        Height_Offset -= Root_to_Crest_Height
        Row += 1

    return verts, Row, Height_Offset


def Create_Thread_End_Verts(INNER_DIA, OUTTER_DIA, PITCH, CREST_PERCENT,
                            ROOT_PERCENT, Z_LOCATION, DIV_COUNT):
    verts = []

    INNER_RADIUS = INNER_DIA / 2
    OUTTER_RADIUS = OUTTER_DIA / 2

    Deg_Step = 360.0 / float(DIV_COUNT)
    Height_Step = float(PITCH) / float(DIV_COUNT)

    Crest_Height = float(PITCH) * float(CREST_PERCENT) / float(100)
    Root_Height = float(PITCH) * float(ROOT_PERCENT) / float(100)
    Root_to_Crest_Height = Crest_to_Root_Height = \
                        (float(PITCH) - (Crest_Height + Root_Height)) / 2.0

    Row = 0

    Height_Offset = Z_LOCATION
    Tapper_Height_Start = Height_Offset - PITCH - PITCH
    Max_Height = Tapper_Height_Start - PITCH
    Lowest_Z_Vert = 0

    for j in range(4):

        for i in range(DIV_COUNT + 1):
            z = Height_Offset - (Height_Step * i)
            z = max(z, Max_Height)
            Tapper_Radius = OUTTER_RADIUS
            if z < Tapper_Height_Start:
                Tapper_Radius = OUTTER_RADIUS - (Tapper_Height_Start - z)

            x = sin(radians(i * Deg_Step)) * (Tapper_Radius)
            y = cos(radians(i * Deg_Step)) * (Tapper_Radius)
            verts.append([x, y, z])
            Lowest_Z_Vert = min(Lowest_Z_Vert, z)
        Height_Offset -= Crest_Height
        Row += 1

        for i in range(DIV_COUNT + 1):
            z = Height_Offset - (Height_Step * i)
            z = max(z, Max_Height)
            Tapper_Radius = OUTTER_RADIUS
            if z < Tapper_Height_Start:
                Tapper_Radius = OUTTER_RADIUS - (Tapper_Height_Start - z)

            x = sin(radians(i * Deg_Step)) * (Tapper_Radius)
            y = cos(radians(i * Deg_Step)) * (Tapper_Radius)
            verts.append([x, y, z])
            Lowest_Z_Vert = min(Lowest_Z_Vert, z)
        Height_Offset -= Crest_to_Root_Height
        Row += 1

        for i in range(DIV_COUNT + 1):
            z = Height_Offset - (Height_Step * i)
            z = max(z, Max_Height)
            Tapper_Radius = OUTTER_RADIUS - (Tapper_Height_Start - z)
            if Tapper_Radius > INNER_RADIUS:
                Tapper_Radius = INNER_RADIUS

            x = sin(radians(i * Deg_Step)) * (Tapper_Radius)
            y = cos(radians(i * Deg_Step)) * (Tapper_Radius)
            verts.append([x, y, z])
            Lowest_Z_Vert = min(Lowest_Z_Vert, z)
        Height_Offset -= Root_Height
        Row += 1

        for i in range(DIV_COUNT + 1):
            z = Height_Offset - (Height_Step * i)
            z = max(z, Max_Height)
            Tapper_Radius = OUTTER_RADIUS - (Tapper_Height_Start - z)
            if Tapper_Radius > INNER_RADIUS:
                Tapper_Radius = INNER_RADIUS

            x = sin(radians(i * Deg_Step)) * (Tapper_Radius)
            y = cos(radians(i * Deg_Step)) * (Tapper_Radius)
            verts.append([x, y, z])
            Lowest_Z_Vert = min(Lowest_Z_Vert, z)
        Height_Offset -= Root_to_Crest_Height
        Row += 1

    return verts, Row, Height_Offset, Lowest_Z_Vert


def Create_External_Thread(SHANK_DIA, SHANK_LENGTH, INNER_DIA, OUTTER_DIA,
                           PITCH, LENGTH, CREST_PERCENT, ROOT_PERCENT, DIV_COUNT):

    verts = []
    faces = []

    Total_Row = 0
    # Thread_Len = 0  # UNUSED

    Face_Start = len(verts)
    Offset = 0.0

    Shank_Verts, Shank_Row, Offset = Create_Shank_Verts(
                                                    SHANK_DIA, OUTTER_DIA, SHANK_LENGTH,
                                                    Offset, DIV_COUNT
                                                    )
    Total_Row += Shank_Row

    Thread_Start_Verts, Thread_Start_Row, Offset = Create_Thread_Start_Verts(
                                                    INNER_DIA, OUTTER_DIA, PITCH, CREST_PERCENT,
                                                    ROOT_PERCENT, Offset, DIV_COUNT
                                                    )
    Total_Row += Thread_Start_Row

    Thread_Verts, Thread_Row, Offset = Create_Thread_Verts(
                                                    INNER_DIA, OUTTER_DIA, PITCH, LENGTH,
                                                    CREST_PERCENT, ROOT_PERCENT, Offset, DIV_COUNT
                                                    )
    Total_Row += Thread_Row

    Thread_End_Verts, Thread_End_Row, Offset, Lowest_Z_Vert = Create_Thread_End_Verts(
                                                    INNER_DIA, OUTTER_DIA, PITCH, CREST_PERCENT,
                                                    ROOT_PERCENT, Offset, DIV_COUNT
                                                    )
    Total_Row += Thread_End_Row

    verts.extend(Shank_Verts)
    verts.extend(Thread_Start_Verts)
    verts.extend(Thread_Verts)
    verts.extend(Thread_End_Verts)

    faces.extend(Build_Face_List_Quads(Face_Start, DIV_COUNT, Total_Row - 1, 0))
    faces.extend(Fill_Ring_Face(len(verts) - DIV_COUNT, DIV_COUNT, 1))

    return verts, faces, 0.0 - Lowest_Z_Vert


# ####################################################################
#                   Create Nut
# ####################################################################

def add_Hex_Nut(FLAT, HOLE_DIA, HEIGHT):
    global Global_Head_Height
    global Global_NutRad

    verts = []
    faces = []
    HOLE_RADIUS = HOLE_DIA * 0.5
    Half_Flat = FLAT / 2
    Half_Height = HEIGHT / 2
    TopBevelRadius = Half_Flat - 0.05

    Global_NutRad = TopBevelRadius

    Row = 0
    Lowest_Z_Vert = 0.0

    verts.append([0.0, 0.0, 0.0])

    FaceStart = len(verts)
    # inner hole

    x = sin(radians(0)) * HOLE_RADIUS
    y = cos(radians(0)) * HOLE_RADIUS
    # print ("rad 0 x;",  x,  "y:" ,y )
    verts.append([x, y, 0.0])

    x = sin(radians(60 / 6)) * HOLE_RADIUS
    y = cos(radians(60 / 6)) * HOLE_RADIUS
    # print ("rad 60/6x;",  x,  "y:" ,y )
    verts.append([x, y, 0.0])

    x = sin(radians(60 / 3)) * HOLE_RADIUS
    y = cos(radians(60 / 3)) * HOLE_RADIUS
    # print ("rad 60/3x;",  x,  "y:" ,y )
    verts.append([x, y, 0.0])

    x = sin(radians(60 / 2)) * HOLE_RADIUS
    y = cos(radians(60 / 2)) * HOLE_RADIUS
    # print ("rad 60/2x;",  x,  "y:" ,y )
    verts.append([x, y, 0.0])
    Row += 1

    # Bevel

    x = sin(radians(0)) * TopBevelRadius
    y = cos(radians(0)) * TopBevelRadius
    vec1 = Vector([x, y, 0.0])
    verts.append([x, y, 0.0])

    x = sin(radians(60 / 6)) * TopBevelRadius
    y = cos(radians(60 / 6)) * TopBevelRadius
    vec2 = Vector([x, y, 0.0])
    verts.append([x, y, 0.0])

    x = sin(radians(60 / 3)) * TopBevelRadius
    y = cos(radians(60 / 3)) * TopBevelRadius
    vec3 = Vector([x, y, 0.0])
    verts.append([x, y, 0.0])

    x = sin(radians(60 / 2)) * TopBevelRadius
    y = cos(radians(60 / 2)) * TopBevelRadius
    vec4 = Vector([x, y, 0.0])
    verts.append([x, y, 0.0])
    Row += 1

    # Flats
    x = tan(radians(0)) * Half_Flat
    dvec = vec1 - Vector([x, Half_Flat, 0.0])
    verts.append([x, Half_Flat, -dvec.length])
    Lowest_Z_Vert = min(Lowest_Z_Vert, -dvec.length)

    x = tan(radians(60 / 6)) * Half_Flat
    dvec = vec2 - Vector([x, Half_Flat, 0.0])
    verts.append([x, Half_Flat, -dvec.length])
    Lowest_Z_Vert = min(Lowest_Z_Vert, -dvec.length)

    x = tan(radians(60 / 3)) * Half_Flat
    dvec = vec3 - Vector([x, Half_Flat, 0.0])
    Lowest_Point = -dvec.length
    verts.append([x, Half_Flat, -dvec.length])
    Lowest_Z_Vert = min(Lowest_Z_Vert, -dvec.length)

    x = tan(radians(60 / 2)) * Half_Flat
    dvec = vec4 - Vector([x, Half_Flat, 0.0])
    Lowest_Point = -dvec.length
    verts.append([x, Half_Flat, -dvec.length])
    Lowest_Z_Vert = min(Lowest_Z_Vert, -dvec.length)
    Row += 1

    # down Bits Tri
    x = tan(radians(0)) * Half_Flat
    verts.append([x, Half_Flat, Lowest_Point])

    x = tan(radians(60 / 6)) * Half_Flat
    verts.append([x, Half_Flat, Lowest_Point])
    x = tan(radians(60 / 3)) * Half_Flat
    verts.append([x, Half_Flat, Lowest_Point])

    x = tan(radians(60 / 2)) * Half_Flat
    verts.append([x, Half_Flat, Lowest_Point])
    Lowest_Z_Vert = min(Lowest_Z_Vert, Lowest_Point)
    Row += 1

    # down Bits

    x = tan(radians(0)) * Half_Flat
    verts.append([x, Half_Flat, -Half_Height])

    x = tan(radians(60 / 6)) * Half_Flat
    verts.append([x, Half_Flat, -Half_Height])

    x = tan(radians(60 / 3)) * Half_Flat
    verts.append([x, Half_Flat, -Half_Height])

    x = tan(radians(60 / 2)) * Half_Flat
    verts.append([x, Half_Flat, -Half_Height])
    Lowest_Z_Vert = min(Lowest_Z_Vert, -Half_Height)
    Row += 1

    faces.extend(Build_Face_List_Quads(FaceStart, 3, Row - 1))

    Global_Head_Height = HEIGHT

    Tvert, tface = Mirror_Verts_Faces(verts, faces, 'z', Lowest_Z_Vert)
    verts.extend(Tvert)
    faces.extend(tface)

    Tvert, tface = Mirror_Verts_Faces(verts, faces, 'y')
    verts.extend(Tvert)
    faces.extend(tface)

    S_verts, S_faces = SpinDup(verts, faces, 360, 6, 'z')

    # return verts, faces, TopBevelRadius
    return S_verts, S_faces, TopBevelRadius


def add_Nylon_Head(OUTSIDE_RADIUS, Z_LOCATION, DIV_COUNT):
    verts = []
    faces = []
    Row = 0

    INNER_HOLE = OUTSIDE_RADIUS - (OUTSIDE_RADIUS * (1.25 / 4.75))
    EDGE_THICKNESS = (OUTSIDE_RADIUS * (0.4 / 4.75))
    RAD1 = (OUTSIDE_RADIUS * (0.5 / 4.75))
    OVER_ALL_HEIGHT = (OUTSIDE_RADIUS * (2.0 / 4.75))

    FaceStart = len(verts)

    # Start_Height = 0 - 3  # UNUSED
    Height_Offset = Z_LOCATION
    Lowest_Z_Vert = 0

    x = INNER_HOLE
    z = (Height_Offset - OVER_ALL_HEIGHT) + EDGE_THICKNESS
    verts.append([x, 0.0, z])
    Lowest_Z_Vert = min(Lowest_Z_Vert, z)
    Row += 1

    x = INNER_HOLE
    z = (Height_Offset - OVER_ALL_HEIGHT)
    verts.append([x, 0.0, z])
    Lowest_Z_Vert = min(Lowest_Z_Vert, z)
    Row += 1

    for i in range(180, 80, -10):
        x = sin(radians(i)) * RAD1
        z = cos(radians(i)) * RAD1
        verts.append([(OUTSIDE_RADIUS - RAD1) + x, 0.0, ((Height_Offset - OVER_ALL_HEIGHT) + RAD1) + z])
        Lowest_Z_Vert = min(Lowest_Z_Vert, z)
        Row += 1

    x = OUTSIDE_RADIUS - 0
    z = Height_Offset
    verts.append([x, 0.0, z])
    Lowest_Z_Vert = min(Lowest_Z_Vert, z)
    Row += 1

    sVerts, sFaces = SpinDup(verts, faces, 360, DIV_COUNT, 'z')
    sVerts.extend(verts)        # add the start verts to the Spin verts to complete the loop

    faces.extend(Build_Face_List_Quads(FaceStart, Row - 1, DIV_COUNT,1))

    return Move_Verts_Up_Z(sVerts, 0), faces, Lowest_Z_Vert


def add_Nylon_Part(OUTSIDE_RADIUS, Z_LOCATION, DIV_COUNT):
    verts = []
    faces = []
    Row = 0

    INNER_HOLE = OUTSIDE_RADIUS - (OUTSIDE_RADIUS * (1.5 / 4.75))
    EDGE_THICKNESS = (OUTSIDE_RADIUS * (0.4 / 4.75))
    OVER_ALL_HEIGHT = (OUTSIDE_RADIUS * (2.0 / 4.75))
    PART_THICKNESS = OVER_ALL_HEIGHT - EDGE_THICKNESS
    PART_INNER_HOLE = (OUTSIDE_RADIUS * (2.5 / 4.75))

    FaceStart = len(verts)

    Height_Offset = Z_LOCATION
    Lowest_Z_Vert = 0

    x = INNER_HOLE + EDGE_THICKNESS
    z = Height_Offset
    verts.append([x, 0.0, z])
    Lowest_Z_Vert = min(Lowest_Z_Vert, z)
    Row += 1

    x = PART_INNER_HOLE
    z = Height_Offset
    verts.append([x, 0.0, z])
    Lowest_Z_Vert = min(Lowest_Z_Vert, z)
    Row += 1

    x = PART_INNER_HOLE
    z = Height_Offset - PART_THICKNESS
    verts.append([x, 0.0, z])
    Lowest_Z_Vert = min(Lowest_Z_Vert, z)
    Row += 1

    x = INNER_HOLE + EDGE_THICKNESS
    z = Height_Offset - PART_THICKNESS
    verts.append([x, 0.0, z])
    Lowest_Z_Vert = min(Lowest_Z_Vert, z)
    Row += 1

    sVerts, sFaces = SpinDup(verts, faces, 360, DIV_COUNT, 'z')
    sVerts.extend(verts)  # add the start verts to the Spin verts to complete the loop

    faces.extend(Build_Face_List_Quads(FaceStart, Row - 1, DIV_COUNT, 1))

    return sVerts, faces, 0 - Lowest_Z_Vert


def add_12_Point_Nut(FLAT, HOLE_DIA, HEIGHT,FLANGE_DIA):
    return Create_12_Point(FLAT, HOLE_DIA,HOLE_DIA, HEIGHT,FLANGE_DIA)



# ####################################################################
#                   Create Internal Thread
# ####################################################################

def Create_Internal_Thread_Start_Verts(verts, INNER_RADIUS, OUTTER_RADIUS, PITCH, DIV,
                                       CREST_PERCENT, ROOT_PERCENT, Height_Offset):

    Ret_Row = 0
    # Move the offset up so that the verts start at
    # at the correct place (Height_Start)
    Height_Offset = Height_Offset + PITCH

    Height_Start = Height_Offset - PITCH
    Height_Step = float(PITCH) / float(DIV)
    Deg_Step = 360.0 / float(DIV)

    Crest_Height = float(PITCH) * float(CREST_PERCENT) / float(100)
    Root_Height = float(PITCH) * float(ROOT_PERCENT) / float(100)
    Root_to_Crest_Height = Crest_to_Root_Height = \
                        (float(PITCH) - (Crest_Height + Root_Height)) / 2.0

    Rank = float(OUTTER_RADIUS - INNER_RADIUS) / float(DIV)

    for i in range(DIV + 1):
        z = Height_Offset - (Height_Step * i)
        if z > Height_Start:
            z = Height_Start
        x = sin(radians(i * Deg_Step)) * OUTTER_RADIUS
        y = cos(radians(i * Deg_Step)) * OUTTER_RADIUS

        verts.append([x, y, z])
    Height_Offset -= Crest_Height
    Ret_Row += 1

    for i in range(DIV + 1):
        z = Height_Offset - (Height_Step * i)
        if z > Height_Start:
            z = Height_Start

        x = sin(radians(i * Deg_Step)) * OUTTER_RADIUS
        y = cos(radians(i * Deg_Step)) * OUTTER_RADIUS

        verts.append([x, y, z])
    Height_Offset -= Crest_to_Root_Height
    Ret_Row += 1

    for i in range(DIV + 1):
        z = Height_Offset - (Height_Step * i)
        if z > Height_Start:
            z = Height_Start

        x = sin(radians(i * Deg_Step)) * INNER_RADIUS
        y = cos(radians(i * Deg_Step)) * INNER_RADIUS

        x = sin(radians(i * Deg_Step)) * (OUTTER_RADIUS - (i * Rank))
        y = cos(radians(i * Deg_Step)) * (OUTTER_RADIUS - (i * Rank))

        verts.append([x, y, z])
    Height_Offset -= Root_Height
    Ret_Row += 1

    for i in range(DIV + 1):
        z = Height_Offset - (Height_Step * i)
        if z > Height_Start:
            z = Height_Start

        x = sin(radians(i * Deg_Step)) * INNER_RADIUS
        y = cos(radians(i * Deg_Step)) * INNER_RADIUS

        x = sin(radians(i * Deg_Step)) * (OUTTER_RADIUS - (i * Rank))
        y = cos(radians(i * Deg_Step)) * (OUTTER_RADIUS - (i * Rank))

        verts.append([x, y, z])
    Height_Offset -= Root_to_Crest_Height
    Ret_Row += 1

    return Ret_Row, Height_Offset


def Create_Internal_Thread_End_Verts(verts, INNER_RADIUS, OUTTER_RADIUS, PITCH,
                                     CREST_PERCENT, ROOT_PERCENT, Height_Offset,
                                     DIV_COUNT):
    Ret_Row = 0
    Height_End = Height_Offset - PITCH
    Height_Step = float(PITCH) / float(DIV_COUNT)
    Deg_Step = 360.0 / float(DIV_COUNT)

    Crest_Height = float(PITCH) * float(CREST_PERCENT) / float(100)
    Root_Height = float(PITCH) * float(ROOT_PERCENT) / float(100)
    Root_to_Crest_Height = Crest_to_Root_Height = \
                        (float(PITCH) - (Crest_Height + Root_Height)) / 2.0

    Rank = float(OUTTER_RADIUS - INNER_RADIUS) / float(DIV_COUNT)

    Num = 0

    for j in range(2):
        for i in range(DIV_COUNT + 1):
            z = Height_Offset - (Height_Step * i)
            if z < Height_End:
                z = Height_End
            x = sin(radians(i * Deg_Step)) * OUTTER_RADIUS
            y = cos(radians(i * Deg_Step)) * OUTTER_RADIUS
            verts.append([x, y, z])

        Height_Offset -= Crest_Height
        Ret_Row += 1

        for i in range(DIV_COUNT + 1):
            z = Height_Offset - (Height_Step * i)
            if z < Height_End:
                z = Height_End

            x = sin(radians(i * Deg_Step)) * OUTTER_RADIUS
            y = cos(radians(i * Deg_Step)) * OUTTER_RADIUS
            verts.append([x, y, z])

        Height_Offset -= Crest_to_Root_Height
        Ret_Row += 1

        for i in range(DIV_COUNT + 1):
            z = Height_Offset - (Height_Step * i)
            if z < Height_End:
                z = Height_End

            x = sin(radians(i * Deg_Step)) * INNER_RADIUS
            y = cos(radians(i * Deg_Step)) * INNER_RADIUS

            if j == Num:
                # Fix T51338 -  seems that the placing a small random offset makes the mesh valid
                rand_offset = triangular(0.0001, 0.009)
                x = sin(radians(i * Deg_Step)) * (INNER_RADIUS + (i * Rank + rand_offset))
                y = cos(radians(i * Deg_Step)) * (INNER_RADIUS + (i * Rank + rand_offset))

            if j > Num:
                x = sin(radians(i * Deg_Step)) * (OUTTER_RADIUS)
                y = cos(radians(i * Deg_Step)) * (OUTTER_RADIUS)

            verts.append([x, y, z])

        Height_Offset -= Root_Height
        Ret_Row += 1

        for i in range(DIV_COUNT + 1):
            z = Height_Offset - (Height_Step * i)
            if z < Height_End:
                z = Height_End

            x = sin(radians(i * Deg_Step)) * INNER_RADIUS
            y = cos(radians(i * Deg_Step)) * INNER_RADIUS

            if j == Num:
                x = sin(radians(i * Deg_Step)) * (INNER_RADIUS + (i * Rank))
                y = cos(radians(i * Deg_Step)) * (INNER_RADIUS + (i * Rank))
            if j > Num:
                x = sin(radians(i * Deg_Step)) * (OUTTER_RADIUS)
                y = cos(radians(i * Deg_Step)) * (OUTTER_RADIUS)

            verts.append([x, y, z])

        Height_Offset -= Root_to_Crest_Height
        Ret_Row += 1

    return Ret_Row, Height_End  # send back Height End as this is the lowest point


def Create_Internal_Thread(INNER_DIA, OUTTER_DIA, PITCH, HEIGHT,
                           CREST_PERCENT, ROOT_PERCENT, INTERNAL, DIV_COUNT):
    verts = []
    faces = []

    INNER_RADIUS = INNER_DIA / 2
    OUTTER_RADIUS = OUTTER_DIA / 2

    Deg_Step = 360.0 / float(DIV_COUNT)
    Height_Step = float(PITCH) / float(DIV_COUNT)

    # less one pitch for the start and end that is 1/2 pitch high
    Num = int(round((HEIGHT - PITCH) / PITCH))

    Row = 0

    Crest_Height = float(PITCH) * float(CREST_PERCENT) / float(100)
    Root_Height = float(PITCH) * float(ROOT_PERCENT) / float(100)
    Root_to_Crest_Height = Crest_to_Root_Height = \
                        (float(PITCH) - (Crest_Height + Root_Height)) / 2.0

    Height_Offset = 0
    FaceStart = len(verts)

    Row_Inc, Height_Offset = Create_Internal_Thread_Start_Verts(
                                    verts, INNER_RADIUS, OUTTER_RADIUS, PITCH,
                                    DIV_COUNT, CREST_PERCENT, ROOT_PERCENT,
                                    Height_Offset
                                    )
    Row += Row_Inc

    for j in range(Num):

        for i in range(DIV_COUNT + 1):
            x = sin(radians(i * Deg_Step)) * OUTTER_RADIUS
            y = cos(radians(i * Deg_Step)) * OUTTER_RADIUS
            verts.append([x, y, Height_Offset - (Height_Step * i)])
        Height_Offset -= Crest_Height
        Row += 1

        for i in range(DIV_COUNT + 1):
            x = sin(radians(i * Deg_Step)) * OUTTER_RADIUS
            y = cos(radians(i * Deg_Step)) * OUTTER_RADIUS
            verts.append([x, y, Height_Offset - (Height_Step * i)])
        Height_Offset -= Crest_to_Root_Height
        Row += 1

        for i in range(DIV_COUNT + 1):
            x = sin(radians(i * Deg_Step)) * INNER_RADIUS
            y = cos(radians(i * Deg_Step)) * INNER_RADIUS
            verts.append([x, y, Height_Offset - (Height_Step * i)])
        Height_Offset -= Root_Height
        Row += 1

        for i in range(DIV_COUNT + 1):
            x = sin(radians(i * Deg_Step)) * INNER_RADIUS
            y = cos(radians(i * Deg_Step)) * INNER_RADIUS
            verts.append([x, y, Height_Offset - (Height_Step * i)])
        Height_Offset -= Root_to_Crest_Height
        Row += 1

    Row_Inc, Height_Offset = Create_Internal_Thread_End_Verts(
                                        verts, INNER_RADIUS, OUTTER_RADIUS,
                                        PITCH, CREST_PERCENT,
                                        ROOT_PERCENT, Height_Offset, DIV_COUNT
                                        )

    Row += Row_Inc
    faces.extend(Build_Face_List_Quads(FaceStart, DIV_COUNT, Row - 1, FLIP=1))

    return verts, faces, 0 - Height_Offset


def Nut_Mesh(props, context):

    verts = []
    faces = []
    Head_Verts = []
    Head_Faces = []


    Face_Start = len(verts)
    
    
    if props.bf_Nut_Type == 'bf_Nut_12Pnt':
        Nut_Height = props.bf_12_Point_Nut_Height
    else:
        Nut_Height = props.bf_Hex_Nut_Height
    
    Thread_Verts, Thread_Faces, New_Nut_Height = Create_Internal_Thread(
                                                    props.bf_Minor_Dia, props.bf_Major_Dia,
                                                    props.bf_Pitch, Nut_Height,
                                                    props.bf_Crest_Percent, props.bf_Root_Percent,
                                                    1, props.bf_Div_Count
                                                    )
    verts.extend(Thread_Verts)
    faces.extend(Copy_Faces(Thread_Faces, Face_Start))

    Face_Start = len(verts)
    
    if props.bf_Nut_Type == 'bf_Nut_12Pnt':
        Head_Verts, Head_Faces, Lock_Nut_Rad = add_12_Point_Nut(
                                                props.bf_12_Point_Nut_Flat_Distance,
                                                props.bf_Major_Dia, New_Nut_Height,
                                                #Limit the size of the Flange to avoid calculation error
                                                max(props.bf_12_Point_Nut_Flange_Dia,props.bf_12_Point_Nut_Flat_Distance)
                                                )
    else:
        Head_Verts, Head_Faces, Lock_Nut_Rad = add_Hex_Nut(
                                                props.bf_Hex_Nut_Flat_Distance,
                                                props.bf_Major_Dia, New_Nut_Height
                                                )
    verts.extend((Head_Verts))
    faces.extend(Copy_Faces(Head_Faces, Face_Start))

    LowZ = 0 - New_Nut_Height

    if props.bf_Nut_Type == 'bf_Nut_Lock':
        Face_Start = len(verts)
        Nylon_Head_Verts, Nylon_Head_faces, LowZ = add_Nylon_Head(
                                                        Lock_Nut_Rad, 0 - New_Nut_Height,
                                                        props.bf_Div_Count
                                                        )
        verts.extend((Nylon_Head_Verts))
        faces.extend(Copy_Faces(Nylon_Head_faces, Face_Start))

        Face_Start = len(verts)
        Nylon_Verts, Nylon_faces, Temp_LowZ = add_Nylon_Part(
                                                        Lock_Nut_Rad, 0 - New_Nut_Height,
                                                        props.bf_Div_Count
                                                        )
        verts.extend((Nylon_Verts))
        faces.extend(Copy_Faces(Nylon_faces, Face_Start))

    return Move_Verts_Up_Z(verts, 0 - LowZ), faces


# ####################################################################
#                    Create Bolt
# ####################################################################

def Bolt_Mesh(props, context):

    verts = []
    faces = []
    Bit_Verts = []
    Bit_Faces = []
    Bit_Dia = 0.001
    Head_Verts = []
    Head_Faces = []
    Head_Height = 0.0

    ReSized_Allen_Bit_Flat_Distance = props.bf_Allen_Bit_Flat_Distance  # set default

    Head_Height = props.bf_Hex_Head_Height  # will be changed by the Head Functions

    if props.bf_Bit_Type == 'bf_Bit_Allen' and props.bf_Head_Type == 'bf_Head_Pan':
        # need to size Allen bit if it is too big.
        if Allen_Bit_Dia(props.bf_Allen_Bit_Flat_Distance) > Max_Pan_Bit_Dia(props.bf_Pan_Head_Dia):
            ReSized_Allen_Bit_Flat_Distance = Allen_Bit_Dia_To_Flat(
                                                Max_Pan_Bit_Dia(props.bf_Pan_Head_Dia)
                                                )
            ReSized_Allen_Bit_Flat_Distance -= ReSized_Allen_Bit_Flat_Distance * 0.05   # It looks better if it is just a bit smaller
            # print ("Resized Allen Bit Flat Distance to ",ReSized_Allen_Bit_Flat_Distance)

    # Bit Mesh
    if props.bf_Bit_Type == 'bf_Bit_Allen':
        Bit_Verts, Bit_Faces, Bit_Dia = Create_Allen_Bit(
                                                ReSized_Allen_Bit_Flat_Distance,
                                                props.bf_Allen_Bit_Depth
                                                )

    if props.bf_Bit_Type == 'bf_Bit_Torx':
        Bit_Verts, Bit_Faces, Bit_Dia = Create_Torx_Bit(
                                                Torx_Bit_Size_To_Point_Distance(props.bf_Torx_Size_Type),
                                                props.bf_Torx_Bit_Depth
                                                )


    if props.bf_Bit_Type == 'bf_Bit_Philips':
        Bit_Verts, Bit_Faces, Bit_Dia = Create_Phillips_Bit(
                                                props.bf_Philips_Bit_Dia,
                                                props.bf_Philips_Bit_Dia * (0.5 / 1.82),
                                                props.bf_Phillips_Bit_Depth
                                                )
    # Head Mesh
    if props.bf_Head_Type == 'bf_Head_Hex':
        Head_Verts, Head_Faces, Head_Height = Create_Hex_Head(
                                                props.bf_Hex_Head_Flat_Distance, Bit_Dia,
                                                props.bf_Shank_Dia, props.bf_Hex_Head_Height
                                                )
        
    elif props.bf_Head_Type == 'bf_Head_12Pnt':
        Head_Verts, Head_Faces, Head_Height = Create_12_Point_Head(
                                                props.bf_12_Point_Head_Flat_Distance, Bit_Dia,
                                                props.bf_Shank_Dia, props.bf_12_Point_Head_Height,
                                                #Limit the size of the Flange to avoid calculation error
                                                max(props.bf_12_Point_Head_Flange_Dia,props.bf_12_Point_Head_Flat_Distance)  
                                                )
    elif props.bf_Head_Type == 'bf_Head_Cap':
        Head_Verts, Head_Faces, Head_Height = Create_Cap_Head(
                                                Bit_Dia, props.bf_Cap_Head_Dia,
                                                props.bf_Shank_Dia, props.bf_Cap_Head_Height,
                                                props.bf_Cap_Head_Dia * (1.0 / 19.0),
                                                props.bf_Cap_Head_Dia * (1.0 / 19.0),
                                                props.bf_Div_Count
                                                )
    elif props.bf_Head_Type == 'bf_Head_Dome':
        Head_Verts, Head_Faces, Head_Height = Create_Dome_Head(
                                                Bit_Dia, props.bf_Dome_Head_Dia,
                                                props.bf_Shank_Dia, props.bf_Hex_Head_Height,
                                                1, 1, 0, props.bf_Div_Count
                                                )

    elif props.bf_Head_Type == 'bf_Head_Pan':
        Head_Verts, Head_Faces, Head_Height = Create_Pan_Head(
                                                Bit_Dia, props.bf_Pan_Head_Dia,
                                                props.bf_Shank_Dia,
                                                props.bf_Hex_Head_Height, 1, 1, 0,
                                                props.bf_Div_Count
                                                )
    elif props.bf_Head_Type == 'bf_Head_CounterSink':
        Head_Verts, Head_Faces, Head_Height = Create_CounterSink_Head(
                                                Bit_Dia, props.bf_CounterSink_Head_Dia,
                                                props.bf_Shank_Dia, props.bf_CounterSink_Head_Dia,
                                                props.bf_CounterSink_Head_Dia * (0.09 / 6.31),
                                                props.bf_Div_Count
                                                )

    Face_Start = len(verts)
    verts.extend(Move_Verts_Up_Z(Bit_Verts, Head_Height))
    faces.extend(Copy_Faces(Bit_Faces, Face_Start))

    Face_Start = len(verts)
    verts.extend(Move_Verts_Up_Z(Head_Verts, Head_Height))
    faces.extend(Copy_Faces(Head_Faces, Face_Start))

    Face_Start = len(verts)
    Thread_Verts, Thread_Faces, Thread_Height = Create_External_Thread(
                                                    props.bf_Shank_Dia, props.bf_Shank_Length,
                                                    props.bf_Minor_Dia, props.bf_Major_Dia,
                                                    props.bf_Pitch, props.bf_Thread_Length,
                                                    props.bf_Crest_Percent,
                                                    props.bf_Root_Percent, props.bf_Div_Count
                                                    )

    verts.extend(Move_Verts_Up_Z(Thread_Verts, 0))
    faces.extend(Copy_Faces(Thread_Faces, Face_Start))

    return Move_Verts_Up_Z(verts, Thread_Height), faces








def Create_New_Mesh(props, context):

    verts = []
    faces = []
    edges = []
    sObjName = ''

    if props.bf_Model_Type == 'bf_Model_Bolt':
        # print('Create Bolt')
        verts, faces = Bolt_Mesh(props, context)
        sObjName = 'Bolt'

    if props.bf_Model_Type == 'bf_Model_Nut':
        # print('Create Nut')
        verts, faces = Nut_Mesh(props, context)
        sObjName = 'Nut'

    verts, faces = RemoveDoubles(verts, faces)

    verts = Scale_Mesh_Verts(verts, GLOBAL_SCALE)

    mesh = bpy.data.meshes.new(name=sObjName)
    mesh.from_pydata(verts, edges, faces)

    # useful for development when the mesh may be invalid.
    # Fix T51338 : Validate the mesh (the internal thread generator for the Nut
    # should be more reliable now, however there could be other possible errors)
    is_not_mesh_valid = mesh.validate()

    if is_not_mesh_valid:
        props.report({'INFO'}, "Mesh is not Valid, correcting")

    return mesh
