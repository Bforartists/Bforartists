# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright 2005 Bob Holcomb

import os
import bpy
import time
import math
import struct
import mathutils
from bpy_extras.image_utils import load_image
from bpy_extras.node_shader_utils import PrincipledBSDFWrapper

BOUNDS_3DS = []


###################
# Data Structures #
###################

# Some of the chunks that we will see
# >----- Primary Chunk, at the beginning of each file
PRIMARY = 0x4D4D

# >----- Main Chunks
OBJECTINFO = 0x3D3D  # This gives the version of the mesh and is found right before the material and object information
VERSION = 0x0002  # This gives the version of the .3ds file
AMBIENTLIGHT = 0x2100  # The color of the ambient light
EDITKEYFRAME = 0xB000  # This is the header for all of the key frame info

# >----- Data Chunks, used for various attributes
COLOR_F = 0x0010  # color defined as 3 floats
COLOR_24 = 0x0011  # color defined as 3 bytes
LIN_COLOR_24 = 0x0012  # linear byte color
LIN_COLOR_F = 0x0013  # linear float color
PCT_SHORT = 0x30  # percentage short
PCT_FLOAT = 0x31  # percentage float
MASTERSCALE = 0x0100  # Master scale factor

# >----- sub defines of OBJECTINFO
MATERIAL = 0xAFFF  # This stored the texture info
OBJECT = 0x4000  # This stores the faces, vertices, etc...

# >------ sub defines of MATERIAL
MAT_NAME = 0xA000  # This holds the material name
MAT_AMBIENT = 0xA010  # Ambient color of the object/material
MAT_DIFFUSE = 0xA020  # This holds the color of the object/material
MAT_SPECULAR = 0xA030  # Specular color of the object/material
MAT_SHINESS = 0xA040  # Roughness of the object/material (percent)
MAT_SHIN2 = 0xA041  # Shininess of the object/material (percent)
MAT_SHIN3 = 0xA042  # Reflection of the object/material (percent)
MAT_TRANSPARENCY = 0xA050  # Transparency value of material (percent)
MAT_XPFALL = 0xA052  # Transparency falloff value
MAT_REFBLUR = 0xA053  # Reflection blurring value
MAT_SELF_ILLUM = 0xA080  # # Material self illumination flag
MAT_TWO_SIDE = 0xA081  # Material is two sided flag
MAT_DECAL = 0xA082  # Material mapping is decaled flag
MAT_ADDITIVE = 0xA083  # Material has additive transparency flag
MAT_SELF_ILPCT = 0xA084  # Self illumination strength (percent)
MAT_WIRE = 0xA085  # Material wireframe rendered flag
MAT_FACEMAP = 0xA088  # Face mapped textures flag
MAT_PHONGSOFT = 0xA08C  # Phong soften material flag
MAT_WIREABS = 0xA08E  # Wire size in units flag
MAT_WIRESIZE = 0xA087  # Rendered wire size in pixels
MAT_SHADING = 0xA100  # Material shading method
MAT_USE_XPFALL = 0xA240  # Transparency falloff flag
MAT_USE_REFBLUR = 0xA250  # Reflection blurring flag

# >------ sub defines of MATERIAL_MAP
MAT_TEXTURE_MAP = 0xA200  # This is a header for a new texture map
MAT_SPECULAR_MAP = 0xA204  # This is a header for a new specular map
MAT_OPACITY_MAP = 0xA210  # This is a header for a new opacity map
MAT_REFLECTION_MAP = 0xA220  # This is a header for a new reflection map
MAT_BUMP_MAP = 0xA230  # This is a header for a new bump map
MAT_BUMP_PERCENT = 0xA252  # Normalmap strength (percent)
MAT_TEX2_MAP = 0xA33A  # This is a header for a secondary texture
MAT_SHIN_MAP = 0xA33C  # This is a header for a new roughness map
MAT_SELFI_MAP = 0xA33D  # This is a header for a new emission map
MAT_MAP_FILEPATH = 0xA300  # This holds the file name of the texture
MAT_MAP_TILING = 0xA351  # 2nd bit (from LSB) is mirror UV flag
MAT_MAP_USCALE = 0xA354  # U axis scaling
MAT_MAP_VSCALE = 0xA356  # V axis scaling
MAT_MAP_UOFFSET = 0xA358  # U axis offset
MAT_MAP_VOFFSET = 0xA35A  # V axis offset
MAT_MAP_ANG = 0xA35C  # UV rotation around the z-axis in rad
MAT_MAP_COL1 = 0xA360  # Map Color1
MAT_MAP_COL2 = 0xA362  # Map Color2
MAT_MAP_RCOL = 0xA364  # Red mapping
MAT_MAP_GCOL = 0xA366  # Green mapping
MAT_MAP_BCOL = 0xA368  # Blue mapping

# >------ sub defines of OBJECT
OBJECT_MESH = 0x4100  # This lets us know that we are reading a new object
OBJECT_LIGHT = 0x4600  # This lets us know we are reading a light object
OBJECT_CAMERA = 0x4700  # This lets us know we are reading a camera object

# >------ Sub defines of LIGHT
LIGHT_SPOTLIGHT = 0x4610  # The target of a spotlight
LIGHT_OFF = 0x4620  # The light is off
LIGHT_ATTENUATE = 0x4625  # Light attenuate flag
LIGHT_RAYSHADE = 0x4627  # Light rayshading flag
LIGHT_SPOT_SHADOWED = 0x4630  # Light spot shadow flag
LIGHT_LOCAL_SHADOW = 0x4640  # Light shadow values 1
LIGHT_LOCAL_SHADOW2 = 0x4641  # Light shadow values 2
LIGHT_SPOT_SEE_CONE = 0x4650  # Light spot cone flag
LIGHT_SPOT_RECTANGLE = 0x4651  # Light spot rectangle flag
LIGHT_SPOT_OVERSHOOT = 0x4652  # Light spot overshoot flag
LIGHT_SPOT_PROJECTOR = 0x4653  # Light spot bitmap name
LIGHT_EXCLUDE = 0x4654  # Light excluded objects
LIGHT_RANGE = 0x4655  # Light range
LIGHT_SPOT_ROLL = 0x4656  # The roll angle of the spot
LIGHT_SPOT_ASPECT = 0x4657  # Light spot aspect flag
LIGHT_RAY_BIAS = 0x4658  # Light ray bias value
LIGHT_INNER_RANGE = 0x4659  # The light inner range
LIGHT_OUTER_RANGE = 0x465A  # The light outer range
LIGHT_MULTIPLIER = 0x465B  # The light energy factor
LIGHT_AMBIENT_LIGHT = 0x4680  # Light ambient flag

# >------ sub defines of CAMERA
OBJECT_CAM_RANGES = 0x4720  # The camera range values

# >------ sub defines of OBJECT_MESH
OBJECT_VERTICES = 0x4110  # The objects vertices
OBJECT_VERTFLAGS = 0x4111  # The objects vertex flags
OBJECT_FACES = 0x4120  # The objects faces
OBJECT_MATERIAL = 0x4130  # The objects face material
OBJECT_UV = 0x4140  # The vertex UV texture coordinates
OBJECT_SMOOTH = 0x4150  # The objects face smooth groups
OBJECT_TRANS_MATRIX = 0x4160  # The objects Matrix

# >------ sub defines of EDITKEYFRAME
KFDATA_AMBIENT = 0xB001  # Keyframe ambient node
KFDATA_OBJECT = 0xB002  # Keyframe object node
KFDATA_CAMERA = 0xB003  # Keyframe camera node
KFDATA_TARGET = 0xB004  # Keyframe target node
KFDATA_LIGHT = 0xB005  # Keyframe light node
KFDATA_LTARGET = 0xB006  # Keyframe light target node
KFDATA_SPOTLIGHT = 0xB007  # Keyframe spotlight node
KFDATA_KFSEG = 0xB008  # Keyframe start and stop
KFDATA_CURTIME = 0xB009  # Keyframe current frame
KFDATA_KFHDR = 0xB00A  # Keyframe node header

# >------ sub defines of KEYFRAME_NODE
OBJECT_NODE_HDR = 0xB010  # Keyframe object node header
OBJECT_INSTANCE_NAME = 0xB011  # Keyframe object name for dummy objects
OBJECT_PRESCALE = 0xB012  # Keyframe object prescale
OBJECT_PIVOT = 0xB013  # Keyframe object pivot position
OBJECT_BOUNDBOX = 0xB014  # Keyframe object boundbox
MORPH_SMOOTH = 0xB015  # Auto smooth angle for keyframe mesh objects
POS_TRACK_TAG = 0xB020  # Keyframe object position track
ROT_TRACK_TAG = 0xB021  # Keyframe object rotation track
SCL_TRACK_TAG = 0xB022  # Keyframe object scale track
FOV_TRACK_TAG = 0xB023  # Keyframe camera field of view track
ROLL_TRACK_TAG = 0xB024  # Keyframe camera roll track
COL_TRACK_TAG = 0xB025  # Keyframe light color track
MORPH_TRACK_TAG = 0xB026  # Keyframe object morph smooth track
HOTSPOT_TRACK_TAG = 0xB027  # Keyframe spotlight hotspot track
FALLOFF_TRACK_TAG = 0xB028  # Keyframe spotlight falloff track
HIDE_TRACK_TAG = 0xB029  # Keyframe object hide track
OBJECT_NODE_ID = 0xB030  # Keyframe object node id
PARENT_NAME = 0x80F0  # Object parent name tree (dot seperated)

ROOT_OBJECT = 0xFFFF

global scn
scn = None

object_dictionary = {}
parent_dictionary = {}
object_matrix = {}


class Chunk:
    __slots__ = (
        "ID",
        "length",
        "bytes_read",
    )
    # we don't read in the bytes_read, we compute that
    binary_format = '<HI'

    def __init__(self):
        self.ID = 0
        self.length = 0
        self.bytes_read = 0

    def dump(self):
        print('ID: ', self.ID)
        print('ID in hex: ', hex(self.ID))
        print('length: ', self.length)
        print('bytes_read: ', self.bytes_read)


def read_chunk(file, chunk):
    temp_data = file.read(struct.calcsize(chunk.binary_format))
    data = struct.unpack(chunk.binary_format, temp_data)
    chunk.ID = data[0]
    chunk.length = data[1]
    # update the bytes read function
    chunk.bytes_read = 6

    # if debugging
    # chunk.dump()


def read_string(file):
    # read in the characters till we get a null character
    s = []
    while True:
        c = file.read(1)
        if c == b'\x00':
            break
        s.append(c)
        # print('string: ', s)

    # Remove the null character from the string
    # print("read string", s)
    return str(b''.join(s), "utf-8", "replace"), len(s) + 1


##########
# IMPORT #
##########

def process_next_object_chunk(file, previous_chunk):
    new_chunk = Chunk()

    while (previous_chunk.bytes_read < previous_chunk.length):
        # read the next chunk
        read_chunk(file, new_chunk)

def skip_to_end(file, skip_chunk):
    buffer_size = skip_chunk.length - skip_chunk.bytes_read
    binary_format = '%ic' % buffer_size
    file.read(struct.calcsize(binary_format))
    skip_chunk.bytes_read += buffer_size


def add_texture_to_material(image, contextWrapper, pct, extend, alpha, scale, offset, angle, tintcolor, mapto):
    shader = contextWrapper.node_principled_bsdf
    nodetree = contextWrapper.material.node_tree
    shader.location = (-300, 0)
    nodes = nodetree.nodes
    links = nodetree.links

    if mapto == 'COLOR':
        mixer = nodes.new(type='ShaderNodeMixRGB')
        mixer.label = "Mixer"
        mixer.inputs[0].default_value = pct / 100
        mixer.inputs[1].default_value = (
            tintcolor[:3] + [1] if tintcolor else
            shader.inputs['Base Color'].default_value[:]
        )
        contextWrapper._grid_to_location(1, 2, dst_node=mixer, ref_node=shader)
        img_wrap = contextWrapper.base_color_texture
        links.new(img_wrap.node_image.outputs['Color'], mixer.inputs[2])
        links.new(mixer.outputs['Color'], shader.inputs['Base Color'])
    elif mapto == 'SPECULARITY':
        img_wrap = contextWrapper.specular_texture
    elif mapto == 'ALPHA':
        shader.location = (0, -300)
        img_wrap = contextWrapper.alpha_texture
    elif mapto == 'METALLIC':
        shader.location = (300, 300)
        img_wrap = contextWrapper.metallic_texture
    elif mapto == 'ROUGHNESS':
        shader.location = (300, 0)
        img_wrap = contextWrapper.roughness_texture
    elif mapto == 'EMISSION':
        shader.location = (-300, -600)
        img_wrap = contextWrapper.emission_color_texture
    elif mapto == 'NORMAL':
        shader.location = (300, 300)
        img_wrap = contextWrapper.normalmap_texture
    elif mapto == 'TEXTURE':
        img_wrap = nodes.new(type='ShaderNodeTexImage')
        img_wrap.label = image.name
        contextWrapper._grid_to_location(0, 2, dst_node=img_wrap, ref_node=shader)
        for node in nodes:
            if node.label == 'Mixer':
                spare = node.inputs[1] if node.inputs[1].is_linked is False else node.inputs[2]
                socket = spare if spare.is_linked is False else node.inputs[0]
                links.new(img_wrap.outputs['Color'], socket)
            if node.type == 'TEX_COORD':
                links.new(node.outputs['UV'], img_wrap.inputs['Vector'])
        if shader.inputs['Base Color'].is_linked is False:
            links.new(img_wrap.outputs['Color'], shader.inputs['Base Color'])

    img_wrap.image = image
    img_wrap.extension = 'REPEAT'

    if mapto != 'TEXTURE':
        img_wrap.scale = scale
        img_wrap.translation = offset
        img_wrap.rotation[2] = angle

    if extend == 'mirror':
        img_wrap.extension = 'MIRROR'
    elif extend == 'decal':
        img_wrap.extension = 'EXTEND'
    elif extend == 'noWrap':
        img_wrap.extension = 'CLIP'

    if alpha == 'alpha':
        for link in links:
            if link.from_node.type == 'TEX_IMAGE' and link.to_node.type == 'MIX_RGB':
                tex = link.from_node.image.name
                own_node = img_wrap.node_image
                own_map = img_wrap.node_mapping
                if tex == image.name:
                    links.new(link.from_node.outputs['Alpha'], img_wrap.socket_dst)
                    nodes.remove(own_map)
                    nodes.remove(own_node)
                    for imgs in bpy.data.images:
                        if imgs.name[-3:].isdigit():
                            if not imgs.users:
                                bpy.data.images.remove(imgs)
                else:
                    links.new(img_wrap.node_image.outputs['Alpha'], img_wrap.socket_dst)
        contextWrapper.material.blend_method = 'HASHED'

    shader.location = (300, 300)
    contextWrapper._grid_to_location(1, 0, dst_node=contextWrapper.node_out, ref_node=shader)


def process_next_chunk(context, file, previous_chunk, imported_objects, CONSTRAIN, IMAGE_SEARCH, WORLD_MATRIX, KEYFRAME, CONVERSE):

    contextObName = None
    contextLamp = None
    contextCamera = None
    contextMaterial = None
    contextWrapper = None
    contextMatrix = None
    contextMesh_vertls = None
    contextMesh_facels = None
    contextMesh_flag = None
    contextMeshMaterials = []
    contextMesh_smooth = None
    contextMeshUV = None

    # TEXTURE_DICT = {}
    MATDICT = {}

    # Localspace variable names, faster.
    SZ_FLOAT = struct.calcsize('f')
    SZ_2FLOAT = struct.calcsize('2f')
    SZ_3FLOAT = struct.calcsize('3f')
    SZ_4FLOAT = struct.calcsize('4f')
    SZ_U_INT = struct.calcsize('I')
    SZ_U_SHORT = struct.calcsize('H')
    SZ_4U_SHORT = struct.calcsize('4H')
    SZ_4x3MAT = struct.calcsize('ffffffffffff')

    object_dict = {}  # object identities
    object_list = []  # for hierarchy
    object_parent = []  # index of parent in hierarchy, 0xFFFF = no parent
    pivot_list = []  # pivots with hierarchy handling
    track_flags = []  # keyframe track flags
    trackposition = {}  # keep track to position for target calculation

    def putContextMesh(
            context,
            myContextMesh_vertls,
            myContextMesh_facels,
            myContextMesh_flag,
            myContextMeshMaterials,
            myContextMesh_smooth,
            WORLD_MATRIX,
    ):
        bmesh = bpy.data.meshes.new(contextObName)

        if myContextMesh_facels is None:
            myContextMesh_facels = []

        if myContextMesh_vertls:

            bmesh.vertices.add(len(myContextMesh_vertls) // 3)
            bmesh.vertices.foreach_set("co", myContextMesh_vertls)

            nbr_faces = len(myContextMesh_facels)
            bmesh.polygons.add(nbr_faces)
            bmesh.loops.add(nbr_faces * 3)
            eekadoodle_faces = []
            for v1, v2, v3 in myContextMesh_facels:
                eekadoodle_faces.extend((v3, v1, v2) if v3 == 0 else (v1, v2, v3))
            bmesh.polygons.foreach_set("loop_start", range(0, nbr_faces * 3, 3))
            bmesh.loops.foreach_set("vertex_index", eekadoodle_faces)

            if bmesh.polygons and contextMeshUV:
                bmesh.uv_layers.new()
                uv_faces = bmesh.uv_layers.active.data[:]
            else:
                uv_faces = None

            for mat_idx, (matName, faces) in enumerate(myContextMeshMaterials):
                if matName is None:
                    bmat = None
                else:
                    bmat = MATDICT.get(matName)
                    # in rare cases no materials defined.

                bmesh.materials.append(bmat)  # can be None
                for fidx in faces:
                    bmesh.polygons[fidx].material_index = mat_idx

            if uv_faces:
                uvl = bmesh.uv_layers.active.data[:]
                for fidx, pl in enumerate(bmesh.polygons):
                    face = myContextMesh_facels[fidx]
                    v1, v2, v3 = face

                    # eekadoodle
                    if v3 == 0:
                        v1, v2, v3 = v3, v1, v2

                    uvl[pl.loop_start].uv = contextMeshUV[v1 * 2: (v1 * 2) + 2]
                    uvl[pl.loop_start + 1].uv = contextMeshUV[v2 * 2: (v2 * 2) + 2]
                    uvl[pl.loop_start + 2].uv = contextMeshUV[v3 * 2: (v3 * 2) + 2]
                    # always a tri

        bmesh.validate()
        bmesh.update()

        ob = bpy.data.objects.new(contextObName, bmesh)
        object_dictionary[contextObName] = ob
        context.view_layer.active_layer_collection.collection.objects.link(ob)
        imported_objects.append(ob)

        if myContextMesh_flag:
            """Bit 0 (0x1) sets edge CA visible, Bit 1 (0x2) sets edge BC visible and Bit 2 (0x4) sets edge AB visible
               In Blender we use sharp edges for those flags"""
            for f, pl in enumerate(bmesh.polygons):
                face = myContextMesh_facels[f]
                faceflag = myContextMesh_flag[f]
                edge_ab = bmesh.edges[bmesh.loops[pl.loop_start].edge_index]
                edge_bc = bmesh.edges[bmesh.loops[pl.loop_start + 1].edge_index]
                edge_ca = bmesh.edges[bmesh.loops[pl.loop_start + 2].edge_index]
                if face[2] == 0:
                    edge_ab, edge_bc, edge_ca = edge_ca, edge_ab, edge_bc
                if faceflag & 0x1:
                    edge_ca.use_edge_sharp = True
                if faceflag & 0x2:
                    edge_bc.use_edge_sharp = True
                if faceflag & 0x4:
                    edge_ab.use_edge_sharp = True

        if myContextMesh_smooth:
            for f, pl in enumerate(bmesh.polygons):
                smoothface = myContextMesh_smooth[f]
                if smoothface > 0:
                    bmesh.polygons[f].use_smooth = True

        if contextMatrix:
            if WORLD_MATRIX:
                ob.matrix_world = contextMatrix
            else:
                ob.matrix_local = contextMatrix
            object_matrix[ob] = contextMatrix.copy()

    # a spare chunk
    new_chunk = Chunk()
    temp_chunk = Chunk()

    CreateBlenderObject = False
    CreateLightObject = False
    CreateTrackData = False

    def read_float_color(temp_chunk):
        temp_data = file.read(SZ_3FLOAT)
        temp_chunk.bytes_read += SZ_3FLOAT
        return [float(col) for col in struct.unpack('<3f', temp_data)]

    def read_float(temp_chunk):
        temp_data = file.read(SZ_FLOAT)
        temp_chunk.bytes_read += SZ_FLOAT
        return struct.unpack('<f', temp_data)[0]

    def read_short(temp_chunk):
        temp_data = file.read(SZ_U_SHORT)
        temp_chunk.bytes_read += SZ_U_SHORT
        return struct.unpack('<H', temp_data)[0]

    def read_byte_color(temp_chunk):
        temp_data = file.read(struct.calcsize('3B'))
        temp_chunk.bytes_read += 3
        return [float(col) / 255 for col in struct.unpack('<3B', temp_data)]

    def read_texture(new_chunk, temp_chunk, name, mapto):
        uscale, vscale, uoffset, voffset, angle = 1.0, 1.0, 0.0, 0.0, 0.0
        contextWrapper.use_nodes = True
        tintcolor = None
        extend = 'wrap'
        alpha = False
        pct = 50

        contextWrapper.emission_color = contextMaterial.line_color[:3]
        contextWrapper.emission_strength = contextMaterial.line_priority / 100
        contextWrapper.base_color = contextMaterial.diffuse_color[:3]
        contextWrapper.specular = contextMaterial.specular_intensity
        contextWrapper.roughness = contextMaterial.roughness
        contextWrapper.metallic = contextMaterial.metallic
        contextWrapper.alpha = contextMaterial.diffuse_color[3]

        while (new_chunk.bytes_read < new_chunk.length):
            read_chunk(file, temp_chunk)
            if temp_chunk.ID == PCT_SHORT:
                pct = read_short(temp_chunk)

            elif temp_chunk.ID == MAT_MAP_FILEPATH:
                texture_name, read_str_len = read_string(file)
                img = load_image(texture_name, dirname, place_holder=False, recursive=IMAGE_SEARCH, check_existing=True)
                temp_chunk.bytes_read += read_str_len  # plus one for the null character that gets removed

            elif temp_chunk.ID == MAT_MAP_USCALE:
                uscale = read_float(temp_chunk)
            elif temp_chunk.ID == MAT_MAP_VSCALE:
                vscale = read_float(temp_chunk)
            elif temp_chunk.ID == MAT_MAP_UOFFSET:
                uoffset = read_float(temp_chunk)
            elif temp_chunk.ID == MAT_MAP_VOFFSET:
                voffset = read_float(temp_chunk)

            elif temp_chunk.ID == MAT_MAP_TILING:
                """Control bit flags, where 0x1 activates decaling, 0x2 activates mirror,
                0x8 activates inversion, 0x10 deactivates tiling, 0x20 activates summed area sampling,
                0x40 activates alpha source, 0x80 activates tinting, 0x100 ignores alpha, 0x200 activates RGB tint.
                Bits 0x80, 0x100, and 0x200 are only used with TEXMAP, TEX2MAP, and SPECMAP chunks.
                0x40, when used with a TEXMAP, TEX2MAP, or SPECMAP chunk must be accompanied with a tint bit,
                either 0x100 or 0x200, tintcolor will be processed if colorchunks are present"""
                tiling = read_short(temp_chunk)
                if tiling & 0x1:
                    extend = 'decal'
                elif tiling & 0x2:
                    extend = 'mirror'
                elif tiling & 0x8:
                    extend = 'invert'
                elif tiling & 0x10:
                    extend = 'noWrap'
                if tiling & 0x20:
                    alpha = 'sat'
                if tiling & 0x40:
                    alpha = 'alpha'
                if tiling & 0x80:
                    tint = 'tint'
                if tiling & 0x100:
                    tint = 'noAlpha'
                if tiling & 0x200:
                    tint = 'RGBtint'

            elif temp_chunk.ID == MAT_MAP_ANG:
                angle = read_float(temp_chunk)

            elif temp_chunk.ID == MAT_MAP_COL1:
                tintcolor = read_byte_color(temp_chunk)

            skip_to_end(file, temp_chunk)
            new_chunk.bytes_read += temp_chunk.bytes_read

        # add the map to the material in the right channel
        if img:
            add_texture_to_material(img, contextWrapper, pct, extend, alpha, (uscale, vscale, 1),
                                    (uoffset, voffset, 0), angle, tintcolor, mapto)

    def apply_constrain(vec):
        consize = mathutils.Vector(vec) * (CONSTRAIN * 0.1) if CONSTRAIN != 0.0 else mathutils.Vector(vec)
        return consize

    def calc_target(location, target):
        pan = 0.0
        tilt = 0.0
        pos = location + target  # Target triangulation
        if abs(location[0] - target[0]) > abs(location[1] - target[1]):
            foc = math.copysign(math.sqrt(pow(pos[0],2) + pow(pos[1],2)),pos[0])
            dia = math.copysign(math.sqrt(pow(foc,2) + pow(target[2],2)),pos[0])
            pitch = math.radians(90) - math.copysign(math.acos(foc / dia), pos[2])
            if location[0] > target[0]:
                tilt = math.copysign(pitch, pos[0])
                pan = math.radians(90) + math.atan(pos[1] / foc)
            else:
                tilt = -1 * (math.copysign(pitch, pos[0]))
                pan = -1 * (math.radians(90) - math.atan(pos[1] / foc))
        elif abs(location[1] - target[1]) > abs(location[0] - target[0]):
            foc = math.copysign(math.sqrt(pow(pos[1],2) + pow(pos[0],2)),pos[1])
            dia = math.copysign(math.sqrt(pow(foc,2) + pow(target[2],2)),pos[1])
            pitch = math.radians(90) - math.copysign(math.acos(foc / dia), pos[2])
            if location[1] > target[1]:
                tilt = math.copysign(pitch, pos[1])
                pan = math.radians(90) + math.acos(pos[0] / foc)
            else:
                tilt = -1 * (math.copysign(pitch, pos[1]))
                pan = -1 * (math.radians(90) - math.acos(pos[0] / foc))
        direction = tilt, pan
        return direction

    def read_track_data(temp_chunk):
        """Trackflags 0x1, 0x2 and 0x3 are for looping. 0x8, 0x10 and 0x20
        locks the XYZ axes. 0x100, 0x200 and 0x400 unlinks the XYZ axes"""
        new_chunk.bytes_read += SZ_U_SHORT
        temp_data = file.read(SZ_U_SHORT)
        tflags = struct.unpack('<H', temp_data)[0]
        new_chunk.bytes_read += SZ_U_SHORT
        track_flags.append(tflags)
        temp_data = file.read(SZ_U_INT * 2)
        new_chunk.bytes_read += SZ_U_INT * 2
        temp_data = file.read(SZ_U_INT)
        nkeys = struct.unpack('<I', temp_data)[0]
        new_chunk.bytes_read += SZ_U_INT
        if nkeys == 0:
            keyframe_data[0] = default_data
        for i in range(nkeys):
            temp_data = file.read(SZ_U_INT)
            nframe = struct.unpack('<I', temp_data)[0]
            new_chunk.bytes_read += SZ_U_INT
            temp_data = file.read(SZ_U_SHORT)
            nflags = struct.unpack('<H', temp_data)[0]
            new_chunk.bytes_read += SZ_U_SHORT
            for f in range(bin(nflags).count('1')):
                temp_data = file.read(SZ_FLOAT)  # Check for spline terms
                new_chunk.bytes_read += SZ_FLOAT
            temp_data = file.read(SZ_3FLOAT)
            data = struct.unpack('<3f', temp_data)
            new_chunk.bytes_read += SZ_3FLOAT
            keyframe_data[nframe] = data
        return keyframe_data

    def read_track_angle(temp_chunk):
        new_chunk.bytes_read += SZ_U_SHORT * 5
        temp_data = file.read(SZ_U_SHORT * 5)
        temp_data = file.read(SZ_U_INT)
        nkeys = struct.unpack('<I', temp_data)[0]
        new_chunk.bytes_read += SZ_U_INT
        if nkeys == 0:
            keyframe_angle[0] = default_value
        for i in range(nkeys):
            temp_data = file.read(SZ_U_INT)
            nframe = struct.unpack('<I', temp_data)[0]
            new_chunk.bytes_read += SZ_U_INT
            temp_data = file.read(SZ_U_SHORT)
            nflags = struct.unpack('<H', temp_data)[0]
            new_chunk.bytes_read += SZ_U_SHORT
            for f in range(bin(nflags).count('1')):
                temp_data = file.read(SZ_FLOAT)  # Check for spline terms
                new_chunk.bytes_read += SZ_FLOAT
            temp_data = file.read(SZ_FLOAT)
            angle = struct.unpack('<f', temp_data)[0]
            new_chunk.bytes_read += SZ_FLOAT
            keyframe_angle[nframe] = math.radians(angle)
        return keyframe_angle

    dirname = os.path.dirname(file.name)

    # loop through all the data for this chunk (previous chunk) and see what it is
    while (previous_chunk.bytes_read < previous_chunk.length):
        read_chunk(file, new_chunk)

        # is it a Version chunk?
        if new_chunk.ID == VERSION:
            # read in the version of the file
            temp_data = file.read(SZ_U_INT)
            version = struct.unpack('<I', temp_data)[0]
            new_chunk.bytes_read += 4  # read the 4 bytes for the version number
            # this loader works with version 3 and below, but may not with 4 and above
            if version > 3:
                print("\tNon-Fatal Error:  Version greater than 3, may not load correctly: ", version)

        # is it an ambient light chunk?
        elif new_chunk.ID == AMBIENTLIGHT:
            path, filename = os.path.split(file.name)
            realname, ext = os.path.splitext(filename)
            world = bpy.data.worlds.new("Ambient: " + realname)
            world.light_settings.use_ambient_occlusion = True
            context.scene.world = world
            read_chunk(file, temp_chunk)
            if temp_chunk.ID == COLOR_F:
                context.scene.world.color[:] = read_float_color(temp_chunk)
            elif temp_chunk.ID == LIN_COLOR_F:
                context.scene.world.color[:] = read_float_color(temp_chunk)
            else:
                skip_to_end(file, temp_chunk)
            new_chunk.bytes_read += temp_chunk.bytes_read

        # is it an object info chunk?
        elif new_chunk.ID == OBJECTINFO:
            process_next_chunk(context, file, new_chunk, imported_objects, CONSTRAIN, IMAGE_SEARCH, WORLD_MATRIX, KEYFRAME, CONVERSE)

            # keep track of how much we read in the main chunk
            new_chunk.bytes_read += temp_chunk.bytes_read

        # is it an object chunk?
        elif new_chunk.ID == OBJECT:

            if CreateBlenderObject:
                putContextMesh(
                    context,
                    contextMesh_vertls,
                    contextMesh_facels,
                    contextMesh_flag,
                    contextMeshMaterials,
                    contextMesh_smooth,
                    WORLD_MATRIX
                )
                contextMesh_vertls = []
                contextMesh_facels = []
                contextMeshMaterials = []
                contextMesh_flag = None
                contextMesh_smooth = None
                contextMeshUV = None
                contextMatrix = None

            CreateBlenderObject = True
            contextObName, read_str_len = read_string(file)
            new_chunk.bytes_read += read_str_len

        # is it a material chunk?
        elif new_chunk.ID == MATERIAL:
            contextMaterial = bpy.data.materials.new('Material')
            contextWrapper = PrincipledBSDFWrapper(contextMaterial, is_readonly=False, use_nodes=False)

        elif new_chunk.ID == MAT_NAME:
            material_name, read_str_len = read_string(file)
            # plus one for the null character that ended the string
            new_chunk.bytes_read += read_str_len
            contextMaterial.name = material_name.rstrip()  # remove trailing whitespace
            MATDICT[material_name] = contextMaterial

        elif new_chunk.ID == MAT_AMBIENT:
            read_chunk(file, temp_chunk)
            # to not loose this data, ambient color is stored in line color
            if temp_chunk.ID == COLOR_F:
                contextMaterial.line_color[:3] = read_float_color(temp_chunk)
            elif temp_chunk.ID == COLOR_24:
                contextMaterial.line_color[:3] = read_byte_color(temp_chunk)
            else:
                skip_to_end(file, temp_chunk)
            new_chunk.bytes_read += temp_chunk.bytes_read

        elif new_chunk.ID == MAT_DIFFUSE:
            read_chunk(file, temp_chunk)
            if temp_chunk.ID == COLOR_F:
                contextMaterial.diffuse_color[:3] = read_float_color(temp_chunk)
            elif temp_chunk.ID == COLOR_24:
                contextMaterial.diffuse_color[:3] = read_byte_color(temp_chunk)
            else:
                skip_to_end(file, temp_chunk)
            new_chunk.bytes_read += temp_chunk.bytes_read

        elif new_chunk.ID == MAT_SPECULAR:
            read_chunk(file, temp_chunk)
            if temp_chunk.ID == COLOR_F:
                contextMaterial.specular_color = read_float_color(temp_chunk)
            elif temp_chunk.ID == COLOR_24:
                contextMaterial.specular_color = read_byte_color(temp_chunk)
            else:
                skip_to_end(file, temp_chunk)
            new_chunk.bytes_read += temp_chunk.bytes_read

        elif new_chunk.ID == MAT_SHINESS:
            read_chunk(file, temp_chunk)
            if temp_chunk.ID == PCT_SHORT:
                temp_data = file.read(SZ_U_SHORT)
                temp_chunk.bytes_read += SZ_U_SHORT
                contextMaterial.roughness = 1 - (float(struct.unpack('<H', temp_data)[0]) / 100)
            elif temp_chunk.ID == PCT_FLOAT:
                temp_data = file.read(SZ_FLOAT)
                temp_chunk.bytes_read += SZ_FLOAT
                contextMaterial.roughness = 1 - float(struct.unpack('<f', temp_data)[0])
            new_chunk.bytes_read += temp_chunk.bytes_read

        elif new_chunk.ID == MAT_SHIN2:
            read_chunk(file, temp_chunk)
            if temp_chunk.ID == PCT_SHORT:
                temp_data = file.read(SZ_U_SHORT)
                temp_chunk.bytes_read += SZ_U_SHORT
                contextMaterial.specular_intensity = (float(struct.unpack('<H', temp_data)[0]) / 100)
            elif temp_chunk.ID == PCT_FLOAT:
                temp_data = file.read(SZ_FLOAT)
                temp_chunk.bytes_read += SZ_FLOAT
                contextMaterial.specular_intensity = float(struct.unpack('<f', temp_data)[0])
            new_chunk.bytes_read += temp_chunk.bytes_read

        elif new_chunk.ID == MAT_SHIN3:
            read_chunk(file, temp_chunk)
            if temp_chunk.ID == PCT_SHORT:
                temp_data = file.read(SZ_U_SHORT)
                temp_chunk.bytes_read += SZ_U_SHORT
                contextMaterial.metallic = (float(struct.unpack('<H', temp_data)[0]) / 100)
            elif temp_chunk.ID == PCT_FLOAT:
                temp_data = file.read(SZ_FLOAT)
                temp_chunk.bytes_read += SZ_FLOAT
                contextMaterial.metallic = float(struct.unpack('<f', temp_data)[0])
            new_chunk.bytes_read += temp_chunk.bytes_read

        elif new_chunk.ID == MAT_TRANSPARENCY:
            read_chunk(file, temp_chunk)
            if temp_chunk.ID == PCT_SHORT:
                temp_data = file.read(SZ_U_SHORT)
                temp_chunk.bytes_read += SZ_U_SHORT
                contextMaterial.diffuse_color[3] = 1 - (float(struct.unpack('<H', temp_data)[0]) / 100)
            elif temp_chunk.ID == PCT_FLOAT:
                temp_data = file.read(SZ_FLOAT)
                temp_chunk.bytes_read += SZ_FLOAT
                contextMaterial.diffuse_color[3] = 1 - float(struct.unpack('<f', temp_data)[0])
            else:
                skip_to_end(file, temp_chunk)
            new_chunk.bytes_read += temp_chunk.bytes_read

        elif new_chunk.ID == MAT_SELF_ILPCT:
            read_chunk(file, temp_chunk)
            if temp_chunk.ID == PCT_SHORT:
                temp_data = file.read(SZ_U_SHORT)
                temp_chunk.bytes_read += SZ_U_SHORT
                contextMaterial.line_priority = int(struct.unpack('<H', temp_data)[0])
            elif temp_chunk.ID == PCT_FLOAT:
                temp_data = file.read(SZ_FLOAT)
                temp_chunk.bytes_read += SZ_FLOAT
                contextMaterial.line_priority = (float(struct.unpack('<f', temp_data)[0]) * 100)
            new_chunk.bytes_read += temp_chunk.bytes_read

        elif new_chunk.ID == MAT_SHADING:
            shading = read_short(new_chunk)
            if shading >= 2:
                contextWrapper.use_nodes = True
                contextWrapper.emission_color = contextMaterial.line_color[:3]
                contextWrapper.emission_strength = contextMaterial.line_priority / 100
                contextWrapper.base_color = contextMaterial.diffuse_color[:3]
                contextWrapper.specular = contextMaterial.specular_intensity
                contextWrapper.roughness = contextMaterial.roughness
                contextWrapper.metallic = contextMaterial.metallic
                contextWrapper.alpha = contextMaterial.diffuse_color[3]
                contextWrapper.use_nodes = False
                if shading >= 3:
                    contextWrapper.use_nodes = True

        elif new_chunk.ID == MAT_TEXTURE_MAP:
            read_texture(new_chunk, temp_chunk, "Diffuse", 'COLOR')

        elif new_chunk.ID == MAT_SPECULAR_MAP:
            read_texture(new_chunk, temp_chunk, "Specular", 'SPECULARITY')

        elif new_chunk.ID == MAT_OPACITY_MAP:
            read_texture(new_chunk, temp_chunk, "Opacity", 'ALPHA')

        elif new_chunk.ID == MAT_REFLECTION_MAP:
            read_texture(new_chunk, temp_chunk, "Reflect", 'METALLIC')

        elif new_chunk.ID == MAT_BUMP_MAP:
            read_texture(new_chunk, temp_chunk, "Bump", 'NORMAL')

        elif new_chunk.ID == MAT_BUMP_PERCENT:
            read_chunk(file, temp_chunk)
            if temp_chunk.ID == PCT_SHORT:
                temp_data = file.read(SZ_U_SHORT)
                temp_chunk.bytes_read += SZ_U_SHORT
                contextWrapper.normalmap_strength = (float(struct.unpack('<H', temp_data)[0]) / 100)
            elif temp_chunk.ID == PCT_FLOAT:
                temp_data = file.read(SZ_FLOAT)
                temp_chunk.bytes_read += SZ_FLOAT
                contextWrapper.normalmap_strength = float(struct.unpack('<f', temp_data)[0])
            else:
                skip_to_end(file, temp_chunk)
            new_chunk.bytes_read += temp_chunk.bytes_read

        elif new_chunk.ID == MAT_SHIN_MAP:
            read_texture(new_chunk, temp_chunk, "Shininess", 'ROUGHNESS')

        elif new_chunk.ID == MAT_SELFI_MAP:
            read_texture(new_chunk, temp_chunk, "Emit", 'EMISSION')

        elif new_chunk.ID == MAT_TEX2_MAP:
            read_texture(new_chunk, temp_chunk, "Tex", 'TEXTURE')

        # If mesh chunk
        elif new_chunk.ID == OBJECT_MESH:
            pass

        elif new_chunk.ID == OBJECT_VERTICES:
            """Worldspace vertex locations"""
            temp_data = file.read(SZ_U_SHORT)
            num_verts = struct.unpack('<H', temp_data)[0]
            new_chunk.bytes_read += 2
            contextMesh_vertls = struct.unpack('<%df' % (num_verts * 3), file.read(SZ_3FLOAT * num_verts))
            new_chunk.bytes_read += SZ_3FLOAT * num_verts

        elif new_chunk.ID == OBJECT_FACES:
            temp_data = file.read(SZ_U_SHORT)
            num_faces = struct.unpack('<H', temp_data)[0]
            new_chunk.bytes_read += 2
            temp_data = file.read(SZ_4U_SHORT * num_faces)
            new_chunk.bytes_read += SZ_4U_SHORT * num_faces  # 4 short ints x 2 bytes each
            contextMesh_facels = struct.unpack('<%dH' % (num_faces * 4), temp_data)
            contextMesh_flag = [contextMesh_facels[i] for i in range(3, (num_faces * 4) + 3, 4)]
            contextMesh_facels = [contextMesh_facels[i - 3:i] for i in range(3, (num_faces * 4) + 3, 4)]

        elif new_chunk.ID == OBJECT_MATERIAL:
            material_name, read_str_len = read_string(file)
            new_chunk.bytes_read += read_str_len  # remove 1 null character.
            temp_data = file.read(SZ_U_SHORT)
            num_faces_using_mat = struct.unpack('<H', temp_data)[0]
            new_chunk.bytes_read += SZ_U_SHORT
            temp_data = file.read(SZ_U_SHORT * num_faces_using_mat)
            new_chunk.bytes_read += SZ_U_SHORT * num_faces_using_mat
            temp_data = struct.unpack('<%dH' % (num_faces_using_mat), temp_data)
            contextMeshMaterials.append((material_name, temp_data))
            # look up the material in all the materials

        elif new_chunk.ID == OBJECT_SMOOTH:
            temp_data = file.read(SZ_U_INT * num_faces)
            smoothgroup = struct.unpack('<%dI' % (num_faces), temp_data)
            new_chunk.bytes_read += SZ_U_INT * num_faces
            contextMesh_smooth = smoothgroup

        elif new_chunk.ID == OBJECT_UV:
            temp_data = file.read(SZ_U_SHORT)
            num_uv = struct.unpack('<H', temp_data)[0]
            new_chunk.bytes_read += 2
            temp_data = file.read(SZ_2FLOAT * num_uv)
            new_chunk.bytes_read += SZ_2FLOAT * num_uv
            contextMeshUV = struct.unpack('<%df' % (num_uv * 2), temp_data)

        elif new_chunk.ID == OBJECT_TRANS_MATRIX:
            # How do we know the matrix size? 54 == 4x4 48 == 4x3
            temp_data = file.read(SZ_4x3MAT)
            data = list(struct.unpack('<ffffffffffff', temp_data))
            new_chunk.bytes_read += SZ_4x3MAT
            contextMatrix = mathutils.Matrix(
                (data[:3] + [0], data[3:6] + [0], data[6:9] + [0], data[9:] + [1])).transposed()

        # If light chunk
        elif contextObName and new_chunk.ID == OBJECT_LIGHT:  # Basic lamp support
            newLamp = bpy.data.lights.new("Lamp", 'POINT')
            contextLamp = bpy.data.objects.new(contextObName, newLamp)
            context.view_layer.active_layer_collection.collection.objects.link(contextLamp)
            imported_objects.append(contextLamp)
            object_dictionary[contextObName] = contextLamp
            temp_data = file.read(SZ_3FLOAT)
            contextLamp.location = struct.unpack('<3f', temp_data)
            new_chunk.bytes_read += SZ_3FLOAT
            contextMatrix = None  # Reset matrix
            CreateBlenderObject = False
            CreateLightObject = True
        elif CreateLightObject and new_chunk.ID == COLOR_F:  # Light color
            temp_data = file.read(SZ_3FLOAT)
            contextLamp.data.color = struct.unpack('<3f', temp_data)
            new_chunk.bytes_read += SZ_3FLOAT
        elif CreateLightObject and new_chunk.ID == LIGHT_MULTIPLIER:  # Intensity
            temp_data = file.read(SZ_FLOAT)
            contextLamp.data.energy = (float(struct.unpack('<f', temp_data)[0]) * 1000)
            new_chunk.bytes_read += SZ_FLOAT

        # If spotlight chunk
        elif CreateLightObject and new_chunk.ID == LIGHT_SPOTLIGHT:  # Spotlight
            temp_data = file.read(SZ_3FLOAT)
            contextLamp.data.type = 'SPOT'
            spot = mathutils.Vector(struct.unpack('<3f', temp_data))
            aim = calc_target(contextLamp.location, spot)  # Target
            contextLamp.rotation_euler[0] = aim[0]
            contextLamp.rotation_euler[2] = aim[1]
            new_chunk.bytes_read += SZ_3FLOAT
            temp_data = file.read(SZ_FLOAT)  # Hotspot
            hotspot = float(struct.unpack('<f', temp_data)[0])
            new_chunk.bytes_read += SZ_FLOAT
            temp_data = file.read(SZ_FLOAT)  # Beam angle
            beam_angle = float(struct.unpack('<f', temp_data)[0])
            contextLamp.data.spot_size = math.radians(beam_angle)
            contextLamp.data.spot_blend = 1.0 - (hotspot / beam_angle)
            new_chunk.bytes_read += SZ_FLOAT
        elif CreateLightObject and new_chunk.ID == LIGHT_SPOT_ROLL:  # Roll
            temp_data = file.read(SZ_FLOAT)
            contextLamp.rotation_euler[1] = float(struct.unpack('<f', temp_data)[0])
            new_chunk.bytes_read += SZ_FLOAT
        elif CreateLightObject and new_chunk.ID == LIGHT_SPOT_SHADOWED:  # Shadow
            contextLamp.data.use_shadow = True
        elif CreateLightObject and new_chunk.ID == LIGHT_SPOT_SEE_CONE:  # Cone
            contextLamp.data.show_cone = True
        elif CreateLightObject and new_chunk.ID == LIGHT_SPOT_RECTANGLE:  # Square
            contextLamp.data.use_square = True

        # If camera chunk
        elif contextObName and new_chunk.ID == OBJECT_CAMERA:  # Basic camera support
            camera = bpy.data.cameras.new("Camera")
            contextCamera = bpy.data.objects.new(contextObName, camera)
            context.view_layer.active_layer_collection.collection.objects.link(contextCamera)
            imported_objects.append(contextCamera)
            object_dictionary[contextObName] = contextCamera
            temp_data = file.read(SZ_3FLOAT)
            contextCamera.location = struct.unpack('<3f', temp_data)
            new_chunk.bytes_read += SZ_3FLOAT
            temp_data = file.read(SZ_3FLOAT)
            focus = mathutils.Vector(struct.unpack('<3f', temp_data))
            direction = calc_target(contextCamera.location, focus)  # Target
            new_chunk.bytes_read += SZ_3FLOAT
            temp_data = file.read(SZ_FLOAT)
            contextCamera.rotation_euler[0] = direction[0]
            contextCamera.rotation_euler[1] = float(struct.unpack('<f', temp_data)[0])  # Roll
            contextCamera.rotation_euler[2] = direction[1]
            new_chunk.bytes_read += SZ_FLOAT
            temp_data = file.read(SZ_FLOAT)
            contextCamera.data.lens = float(struct.unpack('<f', temp_data)[0])  # Focus
            new_chunk.bytes_read += SZ_FLOAT
            contextMatrix = None  # Reset matrix
            CreateBlenderObject = False

        # start keyframe section
        elif new_chunk.ID == EDITKEYFRAME:
            pass

        elif KEYFRAME and new_chunk.ID == KFDATA_KFSEG:
            temp_data = file.read(SZ_U_INT)
            start = struct.unpack('<I', temp_data)[0]
            new_chunk.bytes_read += 4
            context.scene.frame_start = start
            temp_data = file.read(SZ_U_INT)
            stop = struct.unpack('<I', temp_data)[0]
            new_chunk.bytes_read += 4
            context.scene.frame_end = stop

        elif KEYFRAME and new_chunk.ID == KFDATA_CURTIME:
            temp_data = file.read(SZ_U_INT)
            current = struct.unpack('<I', temp_data)[0]
            new_chunk.bytes_read += 4
            context.scene.frame_current = current

        # including these here means their OB_NODE_HDR are scanned
        # another object is being processed
        elif new_chunk.ID in {KFDATA_AMBIENT, KFDATA_OBJECT, KFDATA_CAMERA, KFDATA_LIGHT, KFDATA_SPOTLIGHT}:
            object_id = ROOT_OBJECT
            tracking = 'OBJECT'
            child = None

        elif CreateTrackData and new_chunk.ID in {KFDATA_TARGET, KFDATA_LTARGET}:
            tracking = 'TARGET'
            child = None

        elif new_chunk.ID == OBJECT_NODE_ID:
            temp_data = file.read(SZ_U_SHORT)
            object_id = struct.unpack('<H', temp_data)[0]
            new_chunk.bytes_read += 2

        elif new_chunk.ID == OBJECT_NODE_HDR:
            object_name, read_str_len = read_string(file)
            new_chunk.bytes_read += read_str_len
            temp_data = file.read(SZ_U_SHORT * 2)
            new_chunk.bytes_read += 4
            temp_data = file.read(SZ_U_SHORT)
            hierarchy = struct.unpack('<H', temp_data)[0]
            new_chunk.bytes_read += 2
            child = object_dictionary.get(object_name)
            colortrack = 'LIGHT'
            if child is None:
                if object_name == '$AMBIENT$':
                    child = context.scene.world
                    child.use_nodes = True
                    colortrack = 'AMBIENT'
                else:
                    child = bpy.data.objects.new(object_name, None)  # Create an empty object
                    context.view_layer.active_layer_collection.collection.objects.link(child)
                    imported_objects.append(child)

            if tracking != 'TARGET' and object_name != '$AMBIENT$':
                object_dict[object_id] = child
                object_list.append(child)
                object_parent.append(hierarchy)
                pivot_list.append(mathutils.Vector((0.0, 0.0, 0.0)))

        elif new_chunk.ID == PARENT_NAME:
            parent_name, read_str_len = read_string(file)
            parent_dictionary.setdefault(parent_name, []).append(child)
            new_chunk.bytes_read += read_str_len

        elif new_chunk.ID == OBJECT_INSTANCE_NAME:
            object_name, read_str_len = read_string(file)
            if child.name == '$$$DUMMY':
                child.name = object_name
            else:
                child.name += "." + object_name
            object_dictionary[object_name] = child
            new_chunk.bytes_read += read_str_len

        elif new_chunk.ID == OBJECT_PIVOT:  # Pivot
            temp_data = file.read(SZ_3FLOAT)
            pivot = struct.unpack('<3f', temp_data)
            new_chunk.bytes_read += SZ_3FLOAT
            pivot_list[len(pivot_list) - 1] = mathutils.Vector(pivot)

        elif new_chunk.ID == MORPH_SMOOTH and child.type == 'MESH':  # Smooth angle
            child.data.use_auto_smooth = True
            temp_data = file.read(SZ_FLOAT)
            smooth_angle = struct.unpack('<f', temp_data)[0]
            new_chunk.bytes_read += SZ_FLOAT
            child.data.auto_smooth_angle = smooth_angle

        elif KEYFRAME and new_chunk.ID == COL_TRACK_TAG and colortrack == 'AMBIENT':  # Ambient
            keyframe_data = {}
            default_data = child.color[:]
            child.node_tree.nodes['Background'].inputs[0].default_value[:3] = read_track_data(temp_chunk)[0]
            for keydata in keyframe_data.items():
                child.node_tree.nodes['Background'].inputs[0].default_value[:3] = keydata[1]
                child.node_tree.keyframe_insert(data_path="nodes[\"Background\"].inputs[0].default_value", frame=keydata[0])
            track_flags.clear()

        elif KEYFRAME and new_chunk.ID == COL_TRACK_TAG and colortrack == 'LIGHT':  # Color
            keyframe_data = {}
            default_data = child.data.color[:]
            child.data.color = read_track_data(temp_chunk)[0]
            for keydata in keyframe_data.items():
                child.data.color = keydata[1]
                child.data.keyframe_insert(data_path="color", frame=keydata[0])
            track_flags.clear()

        elif KEYFRAME and new_chunk.ID == POS_TRACK_TAG and tracking == 'OBJECT':  # Translation
            keyframe_data = {}
            default_data = child.location[:]
            child.location = read_track_data(temp_chunk)[0]
            if child.type in {'LIGHT', 'CAMERA'}:
                trackposition[0] = child.location
                CreateTrackData = True
            if track_flags[0] & 0x8:  # Flag 0x8 locks X axis
                child.lock_location[0] = True
            if track_flags[0] & 0x10:  # Flag 0x10 locks Y axis
                child.lock_location[1] = True
            if track_flags[0] & 0x20:  # Flag 0x20 locks Z axis
                child.lock_location[2] = True
            for keydata in keyframe_data.items():
                trackposition[keydata[0]] = keydata[1]  # Keep track to position for target calculation
                child.location = apply_constrain(keydata[1]) if hierarchy == ROOT_OBJECT else mathutils.Vector(keydata[1])
                if hierarchy == ROOT_OBJECT:
                    child.location.rotate(CONVERSE)
                if not track_flags[0] & 0x100:  # Flag 0x100 unlinks X axis
                    child.keyframe_insert(data_path="location", index=0, frame=keydata[0])
                if not track_flags[0] & 0x200:  # Flag 0x200 unlinks Y axis
                    child.keyframe_insert(data_path="location", index=1, frame=keydata[0])
                if not track_flags[0] & 0x400:  # Flag 0x400 unlinks Z axis
                    child.keyframe_insert(data_path="location", index=2, frame=keydata[0])
            track_flags.clear()

        elif KEYFRAME and new_chunk.ID == POS_TRACK_TAG and tracking == 'TARGET':  # Target position
            keyframe_data = {}
            location = child.location
            target = mathutils.Vector(read_track_data(temp_chunk)[0])
            direction = calc_target(location, target)
            child.rotation_euler[0] = direction[0]
            child.rotation_euler[2] = direction[1]
            for keydata in keyframe_data.items():
                track = trackposition.get(keydata[0], child.location)
                locate = mathutils.Vector(track)
                target = mathutils.Vector(keydata[1])
                direction = calc_target(locate, target)
                rotate = mathutils.Euler((direction[0], 0.0, direction[1]), 'XYZ').to_matrix()
                scale = mathutils.Vector.Fill(3, (CONSTRAIN * 0.1)) if CONSTRAIN != 0.0 else child.scale
                transformation = mathutils.Matrix.LocRotScale(locate, rotate, scale)
                child.matrix_world = transformation
                if hierarchy == ROOT_OBJECT:
                    child.matrix_world = CONVERSE @ child.matrix_world
                child.keyframe_insert(data_path="rotation_euler", index=0, frame=keydata[0])
                child.keyframe_insert(data_path="rotation_euler", index=2, frame=keydata[0])
            track_flags.clear()

        elif KEYFRAME and new_chunk.ID == ROT_TRACK_TAG and tracking == 'OBJECT':  # Rotation
            keyframe_rotation = {}
            new_chunk.bytes_read += SZ_U_SHORT
            temp_data = file.read(SZ_U_SHORT)
            tflags = struct.unpack('<H', temp_data)[0]
            new_chunk.bytes_read += SZ_U_SHORT
            temp_data = file.read(SZ_U_INT * 2)
            new_chunk.bytes_read += SZ_U_INT * 2
            temp_data = file.read(SZ_U_INT)
            nkeys = struct.unpack('<I', temp_data)[0]
            new_chunk.bytes_read += SZ_U_INT
            if nkeys == 0:
                keyframe_rotation[0] = child.rotation_axis_angle[:]
            if tflags & 0x8:  # Flag 0x8 locks X axis
                child.lock_rotation[0] = True
            if tflags & 0x10:  # Flag 0x10 locks Y axis
                child.lock_rotation[1] = True
            if tflags & 0x20:  # Flag 0x20 locks Z axis
                child.lock_rotation[2] = True
            for i in range(nkeys):
                temp_data = file.read(SZ_U_INT)
                nframe = struct.unpack('<I', temp_data)[0]
                new_chunk.bytes_read += SZ_U_INT
                temp_data = file.read(SZ_U_SHORT)
                nflags = struct.unpack('<H', temp_data)[0]
                new_chunk.bytes_read += SZ_U_SHORT
                for f in range(bin(nflags).count('1')):
                    temp_data = file.read(SZ_FLOAT)  # Check for spline term values
                    new_chunk.bytes_read += SZ_FLOAT
                temp_data = file.read(SZ_4FLOAT)
                rotation = struct.unpack('<4f', temp_data)
                new_chunk.bytes_read += SZ_4FLOAT
                keyframe_rotation[nframe] = rotation
            rad, axis_x, axis_y, axis_z = keyframe_rotation[0]
            child.rotation_euler = mathutils.Quaternion((axis_x, axis_y, axis_z), -rad).to_euler()  # Why negative?
            for keydata in keyframe_rotation.items():
                rad, axis_x, axis_y, axis_z = keydata[1]
                child.rotation_euler = mathutils.Quaternion((axis_x, axis_y, axis_z), -rad).to_euler()
                if hierarchy == ROOT_OBJECT:
                    child.rotation_euler.rotate(CONVERSE)
                if not tflags & 0x100:  # Flag 0x100 unlinks X axis
                    child.keyframe_insert(data_path="rotation_euler", index=0, frame=keydata[0])
                if not tflags & 0x200:  # Flag 0x200 unlinks Y axis
                    child.keyframe_insert(data_path="rotation_euler", index=1, frame=keydata[0])
                if not tflags & 0x400:  # Flag 0x400 unlinks Z axis
                    child.keyframe_insert(data_path="rotation_euler", index=2, frame=keydata[0])

        elif KEYFRAME and new_chunk.ID == SCL_TRACK_TAG and tracking == 'OBJECT':  # Scale
            keyframe_data = {}
            default_data = child.scale[:]
            child.scale = read_track_data(temp_chunk)[0]
            if track_flags[0] & 0x8:  # Flag 0x8 locks X axis
                child.lock_scale[0] = True
            if track_flags[0] & 0x10:  # Flag 0x10 locks Y axis
                child.lock_scale[1] = True
            if track_flags[0] & 0x20:  # Flag 0x20 locks Z axis
                child.lock_scale[2] = True
            for keydata in keyframe_data.items():
                child.scale = apply_constrain(keydata[1]) if hierarchy == ROOT_OBJECT else mathutils.Vector(keydata[1])
                if not track_flags[0] & 0x100:  # Flag 0x100 unlinks X axis
                    child.keyframe_insert(data_path="scale", index=0, frame=keydata[0])
                if not track_flags[0] & 0x200:  # Flag 0x200 unlinks Y axis
                    child.keyframe_insert(data_path="scale", index=1, frame=keydata[0])
                if not track_flags[0] & 0x400:  # Flag 0x400 unlinks Z axis
                    child.keyframe_insert(data_path="scale", index=2, frame=keydata[0])
            track_flags.clear()

        elif KEYFRAME and new_chunk.ID == ROLL_TRACK_TAG and tracking == 'OBJECT':  # Roll angle
            keyframe_angle = {}
            default_value = child.rotation_euler[1]
            child.rotation_euler[1] = read_track_angle(temp_chunk)[0]
            for keydata in keyframe_angle.items():
                child.rotation_euler[1] = keydata[1]
                if hierarchy == ROOT_OBJECT:
                    child.rotation_euler.rotate(CONVERSE)
                child.keyframe_insert(data_path="rotation_euler", index=1, frame=keydata[0])

        elif KEYFRAME and new_chunk.ID == FOV_TRACK_TAG and child.type == 'CAMERA':  # Field of view
            keyframe_angle = {}
            default_value = child.data.angle
            child.data.angle = read_track_angle(temp_chunk)[0]
            for keydata in keyframe_angle.items():
                child.data.lens = (child.data.sensor_width / 2) / math.tan(keydata[1] / 2)
                child.data.keyframe_insert(data_path="lens", frame=keydata[0])

        elif KEYFRAME and new_chunk.ID == HOTSPOT_TRACK_TAG and child.type == 'LIGHT' and child.data.type == 'SPOT':  # Hotspot
            keyframe_angle = {}
            cone_angle = math.degrees(child.data.spot_size)
            default_value = cone_angle-(child.data.spot_blend * math.floor(cone_angle))   
            hot_spot = math.degrees(read_track_angle(temp_chunk)[0])
            child.data.spot_blend = 1.0 - (hot_spot/cone_angle)
            for keydata in keyframe_angle.items():
                child.data.spot_blend = 1.0 - (math.degrees(keydata[1]) / cone_angle)
                child.data.keyframe_insert(data_path="spot_blend", frame=keydata[0])

        elif KEYFRAME and new_chunk.ID == FALLOFF_TRACK_TAG and child.type == 'LIGHT' and child.data.type == 'SPOT':  # Falloff
            keyframe_angle = {}
            default_value = math.degrees(child.data.spot_size)
            child.data.spot_size = read_track_angle(temp_chunk)[0]
            for keydata in keyframe_angle.items():
                child.data.spot_size = keydata[1]
                child.data.keyframe_insert(data_path="spot_size", frame=keydata[0])

        else:
            buffer_size = new_chunk.length - new_chunk.bytes_read
            binary_format = '%ic' % buffer_size
            temp_data = file.read(struct.calcsize(binary_format))
            new_chunk.bytes_read += buffer_size

        # update the previous chunk bytes read
        previous_chunk.bytes_read += new_chunk.bytes_read

    # FINISHED LOOP
    # There will be a number of objects still not added
    if CreateBlenderObject:
        putContextMesh(
            context,
            contextMesh_vertls,
            contextMesh_facels,
            contextMesh_flag,
            contextMeshMaterials,
            contextMesh_smooth,
            WORLD_MATRIX
        )

    # Assign parents to objects
    # check _if_ we need to assign first because doing so recalcs the depsgraph
    for ind, ob in enumerate(object_list):
        parent = object_parent[ind]
        if parent == ROOT_OBJECT:
            if ob.parent is not None:
                ob.parent = None
        elif parent not in object_dict:
            if ob.parent != object_list[parent]:
                ob.parent = object_list[parent]
        elif ob.parent != object_dict[parent]:
            ob.parent = object_dict.get(parent)
        else:
            print("\tWarning: Cannot assign self to parent ", ob.name)

        #pivot_list[ind] += pivot_list[parent]  # Not sure this is correct, should parent space matrix be applied before combining?

    for par, objs in parent_dictionary.items():
        parent = object_dictionary.get(par)
        for ob in objs:
            if parent is not None:
                ob.parent = parent

    # fix pivots
    for ind, ob in enumerate(object_list):
        if ob.type == 'MESH':
            pivot = pivot_list[ind]
            pivot_matrix = object_matrix.get(ob, mathutils.Matrix())  # unlikely to fail
            pivot_matrix = mathutils.Matrix.Translation(-1 * pivot)
            # pivot_matrix = mathutils.Matrix.Translation(pivot_matrix.to_3x3() @ -pivot)
            ob.data.transform(pivot_matrix)


def load_3ds(filepath,
             context,
             CONSTRAIN=10.0,
             IMAGE_SEARCH=True,
             WORLD_MATRIX=False,
             KEYFRAME=True,
             APPLY_MATRIX=True,
             CONVERSE=None):

    print("importing 3DS: %r..." % (filepath), end="")

    if bpy.ops.object.select_all.poll():
        bpy.ops.object.select_all(action='DESELECT')

    time1 = time.time()
    current_chunk = Chunk()
    file = open(filepath, 'rb')

    # here we go!
    read_chunk(file, current_chunk)
    if current_chunk.ID != PRIMARY:
        print("\tFatal Error:  Not a valid 3ds file: %r" % filepath)
        file.close()
        return

    if CONSTRAIN:
        BOUNDS_3DS[:] = [1 << 30, 1 << 30, 1 << 30, -1 << 30, -1 << 30, -1 << 30]
    else:
        del BOUNDS_3DS[:]

    # fixme, make unglobal, clear in case
    object_dictionary.clear()
    object_matrix.clear()

    scn = context.scene

    imported_objects = []  # Fill this list with objects
    process_next_chunk(context, file, current_chunk, imported_objects, CONSTRAIN, IMAGE_SEARCH, WORLD_MATRIX, KEYFRAME, CONVERSE)

    # fixme, make unglobal
    object_dictionary.clear()
    object_matrix.clear()

    if APPLY_MATRIX:
        for ob in imported_objects:
            if ob.type == 'MESH':
                me = ob.data
                me.transform(ob.matrix_local.inverted())

    # print(imported_objects)
    if CONVERSE and not KEYFRAME:
        for ob in imported_objects:
            ob.location.rotate(CONVERSE)
            ob.rotation_euler.rotate(CONVERSE)

    for ob in imported_objects:
        ob.select_set(True)
        if not APPLY_MATRIX:  # Reset transform
            bpy.ops.object.rotation_clear()
            bpy.ops.object.location_clear()

    """
    if IMPORT_AS_INSTANCE:
        name = filepath.split('\\')[-1].split('/')[-1]
        # Create a group for this import.
        group_scn = Scene.New(name)
        for ob in imported_objects:
            group_scn.link(ob) # dont worry about the layers

        grp = Blender.Group.New(name)
        grp.objects = imported_objects

        grp_ob = Object.New('Empty', name)
        grp_ob.enableDupGroup = True
        grp_ob.DupGroup = grp
        scn.link(grp_ob)
        grp_ob.Layers = Layers
        grp_ob.sel = 1
    else:
        # Select all imported objects.
        for ob in imported_objects:
            scn.link(ob)
            ob.Layers = Layers
            ob.sel = 1
    """

    context.view_layer.update()

    axis_min = [1000000000] * 3
    axis_max = [-1000000000] * 3
    global_clamp_size = CONSTRAIN
    if global_clamp_size != 0.0:
        # Get all object bounds
        for ob in imported_objects:
            for v in ob.bound_box:
                for axis, value in enumerate(v):
                    if axis_min[axis] > value:
                        axis_min[axis] = value
                    if axis_max[axis] < value:
                        axis_max[axis] = value

        # Scale objects
        max_axis = max(axis_max[0] - axis_min[0],
                       axis_max[1] - axis_min[1],
                       axis_max[2] - axis_min[2])
        scale = 1.0

        while global_clamp_size < max_axis * scale:
            scale = scale / 10.0

        scale_mat = mathutils.Matrix.Scale(scale, 4)

        for obj in imported_objects:
            if obj.parent is None:
                obj.matrix_world = scale_mat @ obj.matrix_world

    # Select all new objects.
    print(" done in %.4f sec." % (time.time() - time1))
    file.close()


def load(operator,
         context,
         filepath="",
         constrain_size=0.0,
         use_image_search=True,
         use_world_matrix=False,
         read_keyframe=True,
         use_apply_transform=True,
         global_matrix=None,
         ):

    load_3ds(filepath,
             context,
             CONSTRAIN=constrain_size,
             IMAGE_SEARCH=use_image_search,
             WORLD_MATRIX=use_world_matrix,
             KEYFRAME=read_keyframe,
             APPLY_MATRIX=use_apply_transform,
             CONVERSE=global_matrix,
             )

    return {'FINISHED'}
