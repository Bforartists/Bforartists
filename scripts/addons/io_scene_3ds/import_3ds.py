# SPDX-FileCopyrightText: 2005 Bob Holcomb
#
# SPDX-License-Identifier: GPL-2.0-or-later

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
EDITKEYFRAME = 0xB000  # This is the header for all of the key frame info

# >----- Data Chunks, used for various attributes
COLOR_F = 0x0010  # color defined as 3 floats
COLOR_24 = 0x0011  # color defined as 3 bytes
LIN_COLOR_24 = 0x0012  # linear byte color
LIN_COLOR_F = 0x0013  # linear float color
PCT_SHORT = 0x0030  # percentage short
PCT_FLOAT = 0x0031  # percentage float
MASTERSCALE = 0x0100  # Master scale factor

# >----- sub defines of OBJECTINFO
BITMAP = 0x1100  # The background image name
USE_BITMAP = 0x1101  # The background image flag
SOLIDBACKGND = 0x1200  # The background color (RGB)
USE_SOLIDBGND = 0x1201  # The background color flag
VGRADIENT = 0x1300  # The background gradient colors
USE_VGRADIENT = 0x1301  # The background gradient flag
O_CONSTS = 0x1500  # The origin of the 3D cursor
AMBIENTLIGHT = 0x2100  # The color of the ambient light
FOG = 0x2200  # The fog atmosphere settings
USE_FOG = 0x2201  # The fog atmosphere flag
FOG_BGND = 0x2210  # The fog atmosphere background flag
LAYER_FOG = 0x2302  # The fog layer atmosphere settings
USE_LAYER_FOG = 0x2303  # The fog layer atmosphere flag
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
MAT_MAP_TEXBLUR = 0xA353  # Texture blurring factor (float 0-1)
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
OBJECT_HIERARCHY = 0x4F00  # This lets us know the hierachy id of the object
OBJECT_PARENT = 0x4F10  # This lets us know the parent id of the object

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
LIGHT_ATTENUATE = 0x4625  # Light attenuation flag
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
KF_AMBIENT = 0xB001  # Keyframe ambient node
KF_OBJECT = 0xB002  # Keyframe object node
KF_OBJECT_CAMERA = 0xB003  # Keyframe camera node
KF_TARGET_CAMERA = 0xB004  # Keyframe target node
KF_OBJECT_LIGHT = 0xB005  # Keyframe light node
KF_TARGET_LIGHT = 0xB006  # Keyframe light target node
KF_OBJECT_SPOT_LIGHT = 0xB007  # Keyframe spotlight node
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


def skip_to_end(file, skip_chunk):
    buffer_size = skip_chunk.length - skip_chunk.bytes_read
    binary_format = '%ic' % buffer_size
    file.read(struct.calcsize(binary_format))
    skip_chunk.bytes_read += buffer_size


#############
# MATERIALS #
#############

def add_texture_to_material(image, contextWrapper, pct, extend, alpha, scale, offset, angle, tint1, tint2, mapto):
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
            tint1[:3] + [1] if tint1 else shader.inputs['Base Color'].default_value[:])
        contextWrapper._grid_to_location(1, 2, dst_node=mixer, ref_node=shader)
        img_wrap = contextWrapper.base_color_texture
        image.alpha_mode = 'CHANNEL_PACKED'
        links.new(mixer.outputs['Color'], shader.inputs['Base Color'])
        if tint2 is not None:
            img_wrap.colorspace_name = 'Non-Color'
            mixer.inputs[2].default_value = tint2[:3] + [1]
            links.new(img_wrap.node_image.outputs['Color'], mixer.inputs[0])
        else:
            links.new(img_wrap.node_image.outputs['Color'], mixer.inputs[2])
    elif mapto == 'ROUGHNESS':
        img_wrap = contextWrapper.roughness_texture
    elif mapto == 'METALLIC':
        shader.location = (300,300)
        img_wrap = contextWrapper.metallic_texture
    elif mapto == 'SPECULARITY':
        shader.location = (300,0)
        img_wrap = contextWrapper.specular_tint_texture
        if tint1:
            img_wrap.node_dst.inputs['Coat Tint'].default_value = tint1[:3] + [1]
        if tint2:
            img_wrap.node_dst.inputs['Sheen Tint'].default_value = tint2[:3] + [1]
    elif mapto == 'ALPHA':
        shader.location = (-300,0)
        img_wrap = contextWrapper.alpha_texture
        img_wrap.use_alpha = False
        links.new(img_wrap.node_image.outputs['Color'], img_wrap.socket_dst)
    elif mapto == 'EMISSION':
        shader.location = (0,-900)
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
        own_node = img_wrap.node_image
        contextWrapper.material.blend_method = 'HASHED'
        links.new(own_node.outputs['Alpha'], img_wrap.socket_dst)
        for link in links:
            if link.from_node.type == 'TEX_IMAGE' and link.to_node.type == 'MIX_RGB':
                tex = link.from_node.image.name
                own_map = img_wrap.node_mapping
                if tex == image.name:
                    links.new(link.from_node.outputs['Alpha'], img_wrap.socket_dst)
                    try:
                        nodes.remove(own_map)
                        nodes.remove(own_node)
                    except:
                        pass
                    for imgs in bpy.data.images:
                        if imgs.name[-3:].isdigit():
                            if not imgs.users:
                                bpy.data.images.remove(imgs)

    shader.location = (300, 300)
    contextWrapper._grid_to_location(1, 0, dst_node=contextWrapper.node_out, ref_node=shader)


#############
# MESH DATA #
#############

childs_list = []
parent_list = []

def process_next_chunk(context, file, previous_chunk, imported_objects, CONSTRAIN, FILTER,
                       IMAGE_SEARCH, WORLD_MATRIX, KEYFRAME, CONVERSE, MEASURE, CURSOR):

    contextObName = None
    contextWorld = None
    contextLamp = None
    contextCamera = None
    contextMaterial = None
    contextAlpha = None
    contextColor = None
    contextWrapper = None
    contextMatrix = None
    contextReflection = None
    contextTransmission = None
    contextMesh_vertls = None
    contextMesh_facels = None
    contextMesh_flag = None
    contextMeshMaterials = []
    contextMesh_smooth = None
    contextMeshUV = None
    contextTrack_flag = False

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
    trackposition = {}  # keep track to position for target calculation

    def putContextMesh(context, ContextMesh_vertls, ContextMesh_facels, ContextMesh_flag,
                       ContextMeshMaterials, ContextMesh_smooth, WORLD_MATRIX):

        bmesh = bpy.data.meshes.new(contextObName)

        if ContextMesh_facels is None:
            ContextMesh_facels = []

        if ContextMesh_vertls:

            bmesh.vertices.add(len(ContextMesh_vertls) // 3)
            bmesh.vertices.foreach_set("co", ContextMesh_vertls)

            nbr_faces = len(ContextMesh_facels)
            bmesh.polygons.add(nbr_faces)
            bmesh.loops.add(nbr_faces * 3)
            eekadoodle_faces = []
            for v1, v2, v3 in ContextMesh_facels:
                eekadoodle_faces.extend((v3, v1, v2) if v3 == 0 else (v1, v2, v3))
            bmesh.polygons.foreach_set("loop_start", range(0, nbr_faces * 3, 3))
            bmesh.loops.foreach_set("vertex_index", eekadoodle_faces)

            if bmesh.polygons and contextMeshUV:
                bmesh.uv_layers.new()
                uv_faces = bmesh.uv_layers.active.data[:]
            else:
                uv_faces = None

            for mat_idx, (matName, faces) in enumerate(ContextMeshMaterials):
                if matName is None:
                    bmat = None
                else:
                    bmat = MATDICT.get(matName)
                    # in rare cases no materials defined.

                bmesh.materials.append(bmat)  # can be None
                if bmesh.polygons:
                    for fidx in faces:
                        bmesh.polygons[fidx].material_index = mat_idx
                else:
                    print("\tError: Mesh has no faces!")

            if uv_faces:
                uvl = bmesh.uv_layers.active.data[:]
                for fidx, pl in enumerate(bmesh.polygons):
                    face = ContextMesh_facels[fidx]
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

        if ContextMesh_flag:
            """Bit 0 (0x1) sets edge CA visible, Bit 1 (0x2) sets edge BC visible and
               Bit 2 (0x4) sets edge AB visible. In Blender we use sharp edges for those flags."""
            for f, pl in enumerate(bmesh.polygons):
                face = ContextMesh_facels[f]
                faceflag = ContextMesh_flag[f]
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

        if ContextMesh_smooth:
            for f, pl in enumerate(bmesh.polygons):
                smoothface = ContextMesh_smooth[f]
                if smoothface > 0:
                    bmesh.polygons[f].use_smooth = True
                else:
                    bmesh.polygons[f].use_smooth = False
        else:
            for poly in bmesh.polygons:
                poly.use_smooth = False

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
    CreateCameraObject = False
    CreateLightObject = False
    CreateTrackData = False

    CreateWorld = 'WORLD' in FILTER
    CreateMesh = 'MESH' in FILTER
    CreateLight = 'LIGHT' in FILTER
    CreateCamera = 'CAMERA' in FILTER
    CreateEmpty = 'EMPTY' in FILTER

    def read_short(temp_chunk):
        temp_data = file.read(SZ_U_SHORT)
        temp_chunk.bytes_read += SZ_U_SHORT
        return struct.unpack('<H', temp_data)[0]

    def read_long(temp_chunk):
        temp_data = file.read(SZ_U_INT)
        temp_chunk.bytes_read += SZ_U_INT
        return struct.unpack('<I', temp_data)[0]

    def read_float(temp_chunk):
        temp_data = file.read(SZ_FLOAT)
        temp_chunk.bytes_read += SZ_FLOAT
        return struct.unpack('<f', temp_data)[0]

    def read_float_array(temp_chunk):
        temp_data = file.read(SZ_3FLOAT)
        temp_chunk.bytes_read += SZ_3FLOAT
        return [float(val) for val in struct.unpack('<3f', temp_data)]

    def read_byte_color(temp_chunk):
        temp_data = file.read(struct.calcsize('3B'))
        temp_chunk.bytes_read += 3
        return [float(col) / 255 for col in struct.unpack('<3B', temp_data)]

    def read_texture(new_chunk, temp_chunk, name, mapto):
        uscale, vscale, uoffset, voffset, angle = 1.0, 1.0, 0.0, 0.0, 0.0
        contextWrapper.use_nodes = True
        tint1 = tint2 = None
        extend = 'wrap'
        alpha = False
        pct = 70

        contextWrapper.base_color = contextColor[:]
        contextWrapper.metallic = contextMaterial.metallic
        contextWrapper.roughness = contextMaterial.roughness
        contextWrapper.transmission = contextTransmission
        contextWrapper.specular = contextMaterial.specular_intensity
        contextWrapper.specular_tint = contextMaterial.specular_color[:]
        contextWrapper.emission_color = contextMaterial.line_color[:3]
        contextWrapper.emission_strength = contextMaterial.line_priority / 100
        contextWrapper.alpha = contextMaterial.diffuse_color[3] = contextAlpha
        contextWrapper.node_principled_bsdf.inputs['Coat Weight'].default_value = contextReflection

        while (new_chunk.bytes_read < new_chunk.length):
            read_chunk(file, temp_chunk)
            if temp_chunk.ID == PCT_SHORT:
                pct = read_short(temp_chunk)

            elif temp_chunk.ID == MAT_MAP_FILEPATH:
                texture_name, read_str_len = read_string(file)
                img = load_image(texture_name, dirname, place_holder=False, recursive=IMAGE_SEARCH, check_existing=True)
                temp_chunk.bytes_read += read_str_len  # plus one for the null character that gets removed

            elif temp_chunk.ID == MAT_BUMP_PERCENT:
                contextWrapper.normalmap_strength = (float(read_short(temp_chunk) / 100))
            elif mapto in {'COLOR', 'SPECULARITY'} and temp_chunk.ID == MAT_MAP_TEXBLUR:
                contextWrapper.node_principled_bsdf.inputs['Sheen Weight'].default_value = float(read_float(temp_chunk))

            elif temp_chunk.ID == MAT_MAP_TILING:
                """Control bit flags, where 0x1 activates decaling, 0x2 activates mirror,
                0x8 activates inversion, 0x10 deactivates tiling, 0x20 activates summed area sampling,
                0x40 activates alpha source, 0x80 activates tinting, 0x100 ignores alpha, 0x200 activates RGB tint.
                Bits 0x80, 0x100, and 0x200 are only used with TEXMAP, TEX2MAP, and SPECMAP chunks.
                0x40, when used with a TEXMAP, TEX2MAP, or SPECMAP chunk must be accompanied with a tint bit,
                either 0x100 or 0x200, tintcolor will be processed if colorchunks are present."""
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

            elif temp_chunk.ID == MAT_MAP_USCALE:
                uscale = read_float(temp_chunk)
            elif temp_chunk.ID == MAT_MAP_VSCALE:
                vscale = read_float(temp_chunk)
            elif temp_chunk.ID == MAT_MAP_UOFFSET:
                uoffset = read_float(temp_chunk)
            elif temp_chunk.ID == MAT_MAP_VOFFSET:
                voffset = read_float(temp_chunk)
            elif temp_chunk.ID == MAT_MAP_ANG:
                angle = read_float(temp_chunk)
            elif temp_chunk.ID == MAT_MAP_COL1:
                tint1 = read_byte_color(temp_chunk)
            elif temp_chunk.ID == MAT_MAP_COL2:
                tint2 = read_byte_color(temp_chunk)

            skip_to_end(file, temp_chunk)
            new_chunk.bytes_read += temp_chunk.bytes_read

        # add the map to the material in the right channel
        if img:
            add_texture_to_material(img, contextWrapper, pct, extend, alpha, (uscale, vscale, 1),
                                    (uoffset, voffset, 0), angle, tint1, tint2, mapto)

    def apply_constrain(vec):
        convector = mathutils.Vector.Fill(3, (CONSTRAIN * 0.1))
        consize = mathutils.Vector(vec) * convector if CONSTRAIN != 0.0 else mathutils.Vector(vec)
        return consize

    def get_hierarchy(tree_chunk):
        child_id = read_short(tree_chunk)
        childs_list.insert(child_id, contextObName)
        parent_list.insert(child_id, None)
        if child_id in parent_list:
            idp = parent_list.index(child_id)
            parent_list[idp] = contextObName
        return child_id

    def get_parent(tree_chunk, child_id=-1):
        parent_id = read_short(tree_chunk)
        if parent_id > len(childs_list):
            parent_list[child_id] = parent_id
            parent_list.extend([None] * (parent_id - len(parent_list)))
            parent_list.insert(parent_id, contextObName)
        elif parent_id < len(childs_list):
            parent_list[child_id] = childs_list[parent_id]

    def calc_target(loca, target):
        pan = tilt = 0.0
        plane = loca + target
        angle = math.radians(90)  # Target triangulation
        check_sign = abs(loca.y) < abs(target.y)
        check_axes = abs(loca.x - target.x) > abs(loca.y - target.y)
        plane_y = plane.y if check_sign else -1 * plane.y
        sign_xy = plane.x if check_axes else plane.y
        axis_xy = plane_y if check_axes else plane.x
        hyp = math.sqrt(pow(plane.x,2) + pow(plane.y,2))
        dia = math.sqrt(pow(hyp,2) + pow(plane.z,2))
        yaw = math.atan2(math.copysign(hyp, sign_xy), axis_xy)
        bow = math.acos(hyp / dia) if dia != 0 else 0
        turn = angle - yaw if check_sign else angle + yaw
        tilt = angle - bow if loca.z > target.z else angle + bow
        pan = yaw if check_axes else turn
        return tilt, pan

    def read_track_data(track_chunk):
        """Trackflags 0x1, 0x2 and 0x3 are for looping. 0x8, 0x10 and 0x20
        locks the XYZ axes. 0x100, 0x200 and 0x400 unlinks the XYZ axes."""
        tflags = read_short(track_chunk)
        contextTrack_flag = tflags
        temp_data = file.read(SZ_U_INT * 2)
        track_chunk.bytes_read += SZ_U_INT * 2
        nkeys = read_long(track_chunk)
        for i in range(nkeys):
            nframe = read_long(track_chunk)
            nflags = read_short(track_chunk)
            for f in range(bin(nflags).count('1')):
                temp_data = file.read(SZ_FLOAT)  # Check for spline terms
                track_chunk.bytes_read += SZ_FLOAT
            trackdata = read_float_array(track_chunk)
            keyframe_data[nframe] = trackdata
        return keyframe_data

    def read_track_angle(track_chunk):
        temp_data = file.read(SZ_U_SHORT * 5)
        track_chunk.bytes_read += SZ_U_SHORT * 5
        nkeys = read_long(track_chunk)
        for i in range(nkeys):
            nframe = read_long(track_chunk)
            nflags = read_short(track_chunk)
            for f in range(bin(nflags).count('1')):
                temp_data = file.read(SZ_FLOAT)  # Check for spline terms
                track_chunk.bytes_read += SZ_FLOAT
            angle = read_float(track_chunk)
            keyframe_angle[nframe] = math.radians(angle)
        return keyframe_angle

    dirname = os.path.dirname(file.name)

    # loop through all the data for this chunk (previous chunk) and see what it is
    while (previous_chunk.bytes_read < previous_chunk.length):
        read_chunk(file, new_chunk)

        # Check the Version chunk
        if new_chunk.ID == VERSION:
            # read in the version of the file
            temp_data = file.read(SZ_U_INT)
            version = struct.unpack('<I', temp_data)[0]
            new_chunk.bytes_read += 4  # read the 4 bytes for the version number
            # this loader works with version 3 and below, but may not with 4 and above
            if version > 3:
                print("\tNon-Fatal Error:  Version greater than 3, may not load correctly: ", version)

        # The main object info chunk
        elif new_chunk.ID == OBJECTINFO:
            process_next_chunk(context, file, new_chunk, imported_objects, CONSTRAIN, FILTER,
                               IMAGE_SEARCH, WORLD_MATRIX, KEYFRAME, CONVERSE, MEASURE, CURSOR)

            # keep track of how much we read in the main chunk
            new_chunk.bytes_read += temp_chunk.bytes_read

        # If cursor location
        elif CURSOR and new_chunk.ID == O_CONSTS:
            context.scene.cursor.location = read_float_array(new_chunk)

        # If ambient light chunk
        elif CreateWorld and new_chunk.ID == AMBIENTLIGHT:
            path, filename = os.path.split(file.name)
            realname, ext = os.path.splitext(filename)
            contextWorld = bpy.data.worlds.new("Ambient: " + realname)
            context.scene.world = contextWorld
            read_chunk(file, temp_chunk)
            if temp_chunk.ID == COLOR_F:
                contextWorld.color[:] = read_float_array(temp_chunk)
            elif temp_chunk.ID == LIN_COLOR_F:
                contextWorld.color[:] = read_float_array(temp_chunk)
            else:
                skip_to_end(file, temp_chunk)
            new_chunk.bytes_read += temp_chunk.bytes_read

        # If background chunk
        elif CreateWorld and new_chunk.ID == SOLIDBACKGND:
            backgroundcolor = mathutils.Color((0.1, 0.1, 0.1))
            if contextWorld is None:
                path, filename = os.path.split(file.name)
                realname, ext = os.path.splitext(filename)
                contextWorld = bpy.data.worlds.new("Background: " + realname)
                context.scene.world = contextWorld
            contextWorld.use_nodes = True
            worldnodes = contextWorld.node_tree.nodes
            backgroundnode = worldnodes['Background']
            read_chunk(file, temp_chunk)
            if temp_chunk.ID == COLOR_F:
                backgroundcolor = read_float_array(temp_chunk)
            elif temp_chunk.ID == LIN_COLOR_F:
                backgroundcolor = read_float_array(temp_chunk)
            else:
                skip_to_end(file, temp_chunk)
            backgroundmix = next((wn for wn in worldnodes if wn.type in {'MIX', 'MIX_RGB'}), False)
            backgroundnode.inputs[0].default_value[:3] = backgroundcolor
            if backgroundmix:
                backgroundmix.inputs[2].default_value[:3] = backgroundcolor
            new_chunk.bytes_read += temp_chunk.bytes_read

        # If bitmap chunk
        elif CreateWorld and new_chunk.ID == BITMAP:
            bitmap_name, read_str_len = read_string(file)
            if contextWorld is None:
                path, filename = os.path.split(file.name)
                realname, ext = os.path.splitext(filename)
                contextWorld = bpy.data.worlds.new("Bitmap: " + realname)
                context.scene.world = contextWorld
            contextWorld.use_nodes = True
            links = contextWorld.node_tree.links
            nodes = contextWorld.node_tree.nodes
            bitmap_mix = nodes.new(type='ShaderNodeMixRGB')
            bitmapnode = nodes.new(type='ShaderNodeTexEnvironment')
            bitmap_mix.label = "Solid Color"
            bitmapnode.label = "Bitmap: " + bitmap_name
            bitmap_mix.inputs[2].default_value = nodes['Background'].inputs[0].default_value
            bitmapnode.image = load_image(bitmap_name, dirname, place_holder=False, recursive=IMAGE_SEARCH, check_existing=True)
            bitmap_mix.inputs[0].default_value = 0.5 if bitmapnode.image is not None else 1.0
            bitmapnode.location = (-600, 360) if bitmapnode.image is not None else (-600, 300)
            bitmap_mix.location = (-250, 300)
            gradientnode = next((wn for wn in nodes if wn.type == 'VALTORGB'), False)
            links.new(bitmap_mix.outputs['Color'], nodes['Background'].inputs[0])
            links.new(bitmapnode.outputs['Color'], bitmap_mix.inputs[1])
            if gradientnode:
                links.new(bitmapnode.outputs['Color'], gradientnode.inputs[0])
            new_chunk.bytes_read += read_str_len

        # If gradient chunk:
        elif CreateWorld and new_chunk.ID == VGRADIENT:
            if contextWorld is None:
                path, filename = os.path.split(file.name)
                realname, ext = os.path.splitext(filename)
                contextWorld = bpy.data.worlds.new("Gradient: " + realname)
                context.scene.world = contextWorld
            contextWorld.use_nodes = True
            links = contextWorld.node_tree.links
            nodes = contextWorld.node_tree.nodes
            gradientnode = nodes.new(type='ShaderNodeValToRGB')
            gradientnode.location = (-600, 100)
            gradientnode.label = "Gradient"
            backgroundmix = next((wn for wn in worldnodes if wn.type in {'MIX', 'MIX_RGB'}), False)
            bitmapnode = next((wn for wn in nodes if wn.type in {'TEX_IMAGE', 'TEX_ENVIRONMENT'}), False)
            if backgroundmix:
                links.new(gradientnode.outputs['Color'], backgroundmix.inputs[2])
            else:
                links.new(gradientnode.outputs['Color'], nodes['Background'].inputs[0])
            if bitmapnode:
                links.new(bitmapnode.outputs['Color'], gradientnode.inputs[0])
            gradientnode.color_ramp.elements.new(read_float(new_chunk))
            read_chunk(file, temp_chunk)
            if temp_chunk.ID == COLOR_F:
                gradientnode.color_ramp.elements[2].color[:3] = read_float_array(temp_chunk)
            elif temp_chunk.ID == LIN_COLOR_F:
                gradientnode.color_ramp.elements[2].color[:3] = read_float_array(temp_chunk)
            else:
                skip_to_end(file, temp_chunk)
            new_chunk.bytes_read += temp_chunk.bytes_read
            read_chunk(file, temp_chunk)
            if temp_chunk.ID == COLOR_F:
                gradientnode.color_ramp.elements[1].color[:3] = read_float_array(temp_chunk)
            elif temp_chunk.ID == LIN_COLOR_F:
                gradientnode.color_ramp.elements[1].color[:3] = read_float_array(temp_chunk)
            else:
                skip_to_end(file, temp_chunk)
            new_chunk.bytes_read += temp_chunk.bytes_read
            read_chunk(file, temp_chunk)
            if temp_chunk.ID == COLOR_F:
                gradientnode.color_ramp.elements[0].color[:3] = read_float_array(temp_chunk)
            elif temp_chunk.ID == LIN_COLOR_F:
                gradientnode.color_ramp.elements[0].color[:3] = read_float_array(temp_chunk)
            else:
                skip_to_end(file, temp_chunk)
            new_chunk.bytes_read += temp_chunk.bytes_read

        # If fog chunk:
        elif CreateWorld and new_chunk.ID == FOG:
            if contextWorld is None:
                path, filename = os.path.split(file.name)
                realname, ext = os.path.splitext(filename)
                contextWorld = bpy.data.worlds.new("Fog: " + realname)
                context.scene.world = contextWorld
            contextWorld.use_nodes = True
            links = contextWorld.node_tree.links
            nodes = contextWorld.node_tree.nodes
            fognode = nodes.new(type='ShaderNodeVolumeAbsorption')
            fognode.label = "Fog"
            fognode.location = (10, 60)
            volumemix = next((wn for wn in worldnodes if wn.label == 'Volume' and wn.type in {'ADD_SHADER', 'MIX_SHADER'}), False)
            if volumemix:
                links.new(fognode.outputs['Volume'], volumemix.inputs[1])
            else:
                links.new(fognode.outputs[0], nodes['World Output'].inputs[1])
            contextWorld.mist_settings.use_mist = True
            contextWorld.mist_settings.start = read_float(new_chunk)
            nearfog = read_float(new_chunk) * 0.01
            contextWorld.mist_settings.depth = read_float(new_chunk)
            farfog = read_float(new_chunk) * 0.01
            fognode.inputs[1].default_value = (nearfog + farfog) * 0.5
            read_chunk(file, temp_chunk)
            if temp_chunk.ID == COLOR_F:
                fognode.inputs[0].default_value[:3] = read_float_array(temp_chunk)
            elif temp_chunk.ID == LIN_COLOR_F:
                fognode.inputs[0].default_value[:3] = read_float_array(temp_chunk)
            else:
                skip_to_end(file, temp_chunk)
            new_chunk.bytes_read += temp_chunk.bytes_read
        elif CreateWorld and new_chunk.ID == FOG_BGND:
            pass

        # If layer fog chunk:
        elif CreateWorld and new_chunk.ID == LAYER_FOG:
            """Fog options flags are bit 20 (0x100000) for background fogging,
               bit 0 (0x1) for bottom falloff, and bit 1 (0x2) for top falloff."""
            if contextWorld is None:
                path, filename = os.path.split(file.name)
                realname, ext = os.path.splitext(filename)
                contextWorld = bpy.data.worlds.new("LayerFog: " + realname)
                context.scene.world = contextWorld
            contextWorld.use_nodes = True
            links = contextWorld.node_tree.links
            nodes = contextWorld.node_tree.nodes
            mxvolume = nodes.new(type='ShaderNodeMixShader')
            layerfog = nodes.new(type='ShaderNodeVolumeScatter')
            layerfog.label = "Layer Fog"
            mxvolume.label = "Volume"
            layerfog.location = (10, -60)
            mxvolume.location = (300, 50)
            nodes['World Output'].location = (600, 200)
            links.new(layerfog.outputs['Volume'], mxvolume.inputs[2])
            links.new(mxvolume.outputs[0], nodes['World Output'].inputs[1])
            fognode = next((wn for wn in worldnodes if wn.type == 'VOLUME_ABSORPTION'), False)
            if fognode:
                links.new(fognode.outputs['Volume'], mxvolume.inputs[1])
            context.view_layer.use_pass_mist = False
            contextWorld.mist_settings.use_mist = True
            contextWorld.mist_settings.start = read_float(new_chunk)
            contextWorld.mist_settings.height = read_float(new_chunk)
            layerfog.inputs[1].default_value = read_float(new_chunk)
            layerfog_flag = read_long(new_chunk)
            if layerfog_flag == 0:
                contextWorld.mist_settings.falloff = 'LINEAR'
            if layerfog_flag & 0x1:
                contextWorld.mist_settings.falloff = 'QUADRATIC'
            if layerfog_flag & 0x2:
                contextWorld.mist_settings.falloff = 'INVERSE_QUADRATIC'
            read_chunk(file, temp_chunk)
            if temp_chunk.ID == COLOR_F:
                layerfog.inputs[0].default_value[:3] = read_float_array(temp_chunk)
            elif temp_chunk.ID == LIN_COLOR_F:
                layerfog.inputs[0].default_value[:3] = read_float_array(temp_chunk)
            else:
                skip_to_end(file, temp_chunk)
            new_chunk.bytes_read += temp_chunk.bytes_read
        elif CreateWorld and new_chunk.ID in {USE_FOG, USE_LAYER_FOG}:
            context.view_layer.use_pass_mist = True

        # If material chunk
        elif new_chunk.ID == MATERIAL:
            contextAlpha = True
            contextReflection = False
            contextTransmission = False
            contextColor = mathutils.Color((0.8, 0.8, 0.8))
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
                contextMaterial.line_color[:3] = read_float_array(temp_chunk)
            elif temp_chunk.ID == COLOR_24:
                contextMaterial.line_color[:3] = read_byte_color(temp_chunk)
            else:
                skip_to_end(file, temp_chunk)
            new_chunk.bytes_read += temp_chunk.bytes_read

        elif new_chunk.ID == MAT_DIFFUSE:
            read_chunk(file, temp_chunk)
            if temp_chunk.ID == COLOR_F:
                contextColor = mathutils.Color(read_float_array(temp_chunk))
                contextMaterial.diffuse_color[:3] = contextColor
            elif temp_chunk.ID == COLOR_24:
                contextColor = mathutils.Color(read_byte_color(temp_chunk))
                contextMaterial.diffuse_color[:3] = contextColor
            else:
                skip_to_end(file, temp_chunk)
            new_chunk.bytes_read += temp_chunk.bytes_read

        elif new_chunk.ID == MAT_SPECULAR:
            read_chunk(file, temp_chunk)
            if temp_chunk.ID == COLOR_F:
                contextMaterial.specular_color = read_float_array(temp_chunk)
            elif temp_chunk.ID == COLOR_24:
                contextMaterial.specular_color = read_byte_color(temp_chunk)
            else:
                skip_to_end(file, temp_chunk)
            new_chunk.bytes_read += temp_chunk.bytes_read

        elif new_chunk.ID == MAT_SHINESS:
            read_chunk(file, temp_chunk)
            if temp_chunk.ID == PCT_SHORT:
                contextMaterial.roughness = 1 - (float(read_short(temp_chunk) / 100))
            elif temp_chunk.ID == PCT_FLOAT:
                contextMaterial.roughness = 1.0 - float(read_float(temp_chunk))
            else:
                skip_to_end(file, temp_chunk)
            new_chunk.bytes_read += temp_chunk.bytes_read

        elif new_chunk.ID == MAT_SHIN2:
            read_chunk(file, temp_chunk)
            if temp_chunk.ID == PCT_SHORT:
                contextMaterial.specular_intensity = float(read_short(temp_chunk) / 100)
            elif temp_chunk.ID == PCT_FLOAT:
                contextMaterial.specular_intensity = float(read_float(temp_chunk))
            else:
                skip_to_end(file, temp_chunk)
            new_chunk.bytes_read += temp_chunk.bytes_read

        elif new_chunk.ID == MAT_SHIN3:
            read_chunk(file, temp_chunk)
            if temp_chunk.ID == PCT_SHORT:
                contextMaterial.metallic = float(read_short(temp_chunk) / 100)
            elif temp_chunk.ID == PCT_FLOAT:
                contextMaterial.metallic = float(read_float(temp_chunk))
            else:
                skip_to_end(file, temp_chunk)
            new_chunk.bytes_read += temp_chunk.bytes_read

        elif new_chunk.ID == MAT_TRANSPARENCY:
            read_chunk(file, temp_chunk)
            if temp_chunk.ID == PCT_SHORT:
                contextAlpha = 1 - (float(read_short(temp_chunk) / 100))
                contextMaterial.diffuse_color[3] = contextAlpha
            elif temp_chunk.ID == PCT_FLOAT:
                contextAlpha = 1.0 - float(read_float(temp_chunk))
                contextMaterial.diffuse_color[3] = contextAlpha
            else:
                skip_to_end(file, temp_chunk)
            if contextAlpha < 1:
                contextMaterial.blend_method = 'BLEND'
            new_chunk.bytes_read += temp_chunk.bytes_read

        elif new_chunk.ID == MAT_XPFALL:
            read_chunk(file, temp_chunk)
            if temp_chunk.ID == PCT_SHORT:
                contextTransmission = float(abs(read_short(temp_chunk) / 100))
            else:
                skip_to_end(file, temp_chunk)
            new_chunk.bytes_read += temp_chunk.bytes_read

        elif new_chunk.ID == MAT_REFBLUR:
            read_chunk(file, temp_chunk)
            if temp_chunk.ID == PCT_SHORT:
                contextReflection = float(read_short(temp_chunk) / 100)
            elif temp_chunk.ID == PCT_FLOAT:
                contextReflection = float(read_float(temp_chunk))
            else:
                skip_to_end(file, temp_chunk)
            new_chunk.bytes_read += temp_chunk.bytes_read

        elif new_chunk.ID == MAT_SELF_ILPCT:
            read_chunk(file, temp_chunk)
            if temp_chunk.ID == PCT_SHORT:
                contextMaterial.line_priority = int(read_short(temp_chunk))
            elif temp_chunk.ID == PCT_FLOAT:
                contextMaterial.line_priority = (float(read_float(temp_chunk)) * 100)
            else:
                skip_to_end(file, temp_chunk)
            new_chunk.bytes_read += temp_chunk.bytes_read

        elif new_chunk.ID == MAT_SHADING:
            shading = read_short(new_chunk)
            if shading >= 2:
                contextWrapper.use_nodes = True
                contextWrapper.base_color = contextColor[:]
                contextWrapper.metallic = contextMaterial.metallic
                contextWrapper.roughness = contextMaterial.roughness
                contextWrapper.transmission = contextTransmission
                contextWrapper.specular = contextMaterial.specular_intensity
                contextWrapper.specular_tint = contextMaterial.specular_color[:]
                contextWrapper.emission_color = contextMaterial.line_color[:3]
                contextWrapper.emission_strength = contextMaterial.line_priority / 100
                contextWrapper.alpha = contextMaterial.diffuse_color[3] = contextAlpha
                contextWrapper.node_principled_bsdf.inputs['Coat Weight'].default_value = contextReflection
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
                contextWrapper.normalmap_strength = (float(read_short(temp_chunk) / 100))
            elif temp_chunk.ID == PCT_FLOAT:
                contextWrapper.normalmap_strength = float(read_float(temp_chunk))
            else:
                skip_to_end(file, temp_chunk)
            new_chunk.bytes_read += temp_chunk.bytes_read

        elif new_chunk.ID == MAT_SHIN_MAP:
            read_texture(new_chunk, temp_chunk, "Shininess", 'ROUGHNESS')

        elif new_chunk.ID == MAT_SELFI_MAP:
            read_texture(new_chunk, temp_chunk, "Emit", 'EMISSION')

        elif new_chunk.ID == MAT_TEX2_MAP:
            read_texture(new_chunk, temp_chunk, "Tex", 'TEXTURE')

        # If object chunk - can be mesh, light and spot or camera
        elif new_chunk.ID == OBJECT:
            if CreateBlenderObject:
                putContextMesh(context, contextMesh_vertls, contextMesh_facels, contextMesh_flag,
                               contextMeshMaterials, contextMesh_smooth, WORLD_MATRIX)

                contextMesh_vertls = []
                contextMesh_facels = []
                contextMeshMaterials = []
                contextMesh_flag = None
                contextMesh_smooth = None
                contextMeshUV = None
                contextMatrix = None

            CreateBlenderObject = True if CreateMesh else False
            CreateLightObject = CreateCameraObject = False
            contextObName, read_str_len = read_string(file)
            new_chunk.bytes_read += read_str_len

        # If mesh chunk
        elif new_chunk.ID == OBJECT_MESH:
            pass

        elif CreateMesh and new_chunk.ID == OBJECT_VERTICES:
            """Worldspace vertex locations"""
            num_verts = read_short(new_chunk)
            contextMesh_vertls = struct.unpack('<%df' % (num_verts * 3), file.read(SZ_3FLOAT * num_verts))
            new_chunk.bytes_read += SZ_3FLOAT * num_verts

        elif CreateMesh and new_chunk.ID == OBJECT_FACES:
            num_faces = read_short(new_chunk)
            temp_data = file.read(SZ_4U_SHORT * num_faces)
            new_chunk.bytes_read += SZ_4U_SHORT * num_faces  # 4 short ints x 2 bytes each
            contextMesh_facels = struct.unpack('<%dH' % (num_faces * 4), temp_data)
            contextMesh_flag = [contextMesh_facels[i] for i in range(3, (num_faces * 4) + 3, 4)]
            contextMesh_facels = [contextMesh_facels[i - 3:i] for i in range(3, (num_faces * 4) + 3, 4)]

        elif CreateMesh and new_chunk.ID == OBJECT_MATERIAL:
            material_name, read_str_len = read_string(file)
            new_chunk.bytes_read += read_str_len  # remove 1 null character.
            num_faces_using_mat = read_short(new_chunk)
            temp_data = file.read(SZ_U_SHORT * num_faces_using_mat)
            new_chunk.bytes_read += SZ_U_SHORT * num_faces_using_mat
            temp_data = struct.unpack('<%dH' % (num_faces_using_mat), temp_data)
            contextMeshMaterials.append((material_name, temp_data))
            # look up the material in all the materials

        elif CreateMesh and new_chunk.ID == OBJECT_SMOOTH:
            temp_data = file.read(SZ_U_INT * num_faces)
            smoothgroup = struct.unpack('<%dI' % (num_faces), temp_data)
            new_chunk.bytes_read += SZ_U_INT * num_faces
            contextMesh_smooth = smoothgroup

        elif CreateMesh and new_chunk.ID == OBJECT_UV:
            num_uv = read_short(new_chunk)
            temp_data = file.read(SZ_2FLOAT * num_uv)
            new_chunk.bytes_read += SZ_2FLOAT * num_uv
            contextMeshUV = struct.unpack('<%df' % (num_uv * 2), temp_data)

        elif CreateMesh and new_chunk.ID == OBJECT_TRANS_MATRIX:
            # How do we know the matrix size? 54 == 4x4 48 == 4x3
            temp_data = file.read(SZ_4x3MAT)
            mtx = list(struct.unpack('<ffffffffffff', temp_data))
            new_chunk.bytes_read += SZ_4x3MAT
            contextMatrix = mathutils.Matrix(
                (mtx[:3] + [0], mtx[3:6] + [0], mtx[6:9] + [0], mtx[9:] + [1])).transposed()

        # If hierarchy chunk
        elif CreateMesh and new_chunk.ID == OBJECT_HIERARCHY:
            child_id = get_hierarchy(new_chunk)
        elif CreateMesh and new_chunk.ID == OBJECT_PARENT:
            get_parent(new_chunk, child_id)

        # If light chunk
        elif new_chunk.ID == OBJECT_LIGHT:  # Basic lamp support
            CreateBlenderObject = False
            if not CreateLight:
                contextObName = None
                skip_to_end(file, new_chunk)
            else:
                CreateLightObject = True
                light = bpy.data.lights.new("Lamp", 'POINT')
                contextLamp = bpy.data.objects.new(contextObName, light)
                context.view_layer.active_layer_collection.collection.objects.link(contextLamp)
                imported_objects.append(contextLamp)
                object_dictionary[contextObName] = contextLamp
                contextLamp.data.use_shadow = False
                contextLamp.location = read_float_array(new_chunk)  # Position
            contextMatrix = None # Reset matrix
        elif CreateLightObject and new_chunk.ID == COLOR_F:  # Color
            contextLamp.data.color = read_float_array(new_chunk)
        elif CreateLightObject and new_chunk.ID == LIGHT_OUTER_RANGE:  # Distance
            contextLamp.data.cutoff_distance = read_float(new_chunk)
        elif CreateLightObject and new_chunk.ID == LIGHT_INNER_RANGE:  # Radius
            contextLamp.data.shadow_soft_size = (read_float(new_chunk) * 0.01)
        elif CreateLightObject and new_chunk.ID == LIGHT_MULTIPLIER:  # Intensity
            contextLamp.data.energy = (read_float(new_chunk) * 1000)
        elif CreateLightObject and new_chunk.ID == LIGHT_ATTENUATE:  # Attenuation
            contextLamp.data.use_custom_distance = True

        # If spotlight chunk
        elif CreateLightObject and new_chunk.ID == LIGHT_SPOTLIGHT:  # Spotlight
            contextLamp.data.type = 'SPOT'
            spot = mathutils.Vector(read_float_array(new_chunk))  # Spot location
            aim = calc_target(contextLamp.location, spot)  # Target
            contextLamp.rotation_euler.x = aim[0]
            contextLamp.rotation_euler.z = aim[1]
            hotspot = read_float(new_chunk)  # Hotspot
            beam_angle = read_float(new_chunk)  # Beam angle
            contextLamp.data.spot_size = math.radians(beam_angle)
            contextLamp.data.spot_blend = 1.0 - (hotspot / beam_angle)
        elif CreateLightObject and new_chunk.ID == LIGHT_SPOT_ROLL:  # Roll
            contextLamp.rotation_euler.y = read_float(new_chunk)
        elif CreateLightObject and new_chunk.ID == LIGHT_SPOT_SHADOWED:  # Shadow flag
            contextLamp.data.use_shadow = True
        elif CreateLightObject and new_chunk.ID == LIGHT_LOCAL_SHADOW2:  # Shadow parameters
            contextLamp.data.shadow_buffer_bias = read_float(new_chunk)
            contextLamp.data.shadow_buffer_clip_start = (read_float(new_chunk) * 0.1)
            temp_data = file.read(SZ_U_SHORT)
            new_chunk.bytes_read += SZ_U_SHORT
        elif CreateLightObject and new_chunk.ID == LIGHT_SPOT_SEE_CONE:  # Cone flag
            contextLamp.data.show_cone = True
        elif CreateLightObject and new_chunk.ID == LIGHT_SPOT_RECTANGLE:  # Square flag
            contextLamp.data.use_square = True
        elif CreateLightObject and new_chunk.ID == LIGHT_SPOT_ASPECT:  # Aspect
            contextLamp.empty_display_size = read_float(new_chunk)
        elif CreateLightObject and new_chunk.ID == LIGHT_SPOT_PROJECTOR:  # Projection
            contextLamp.data.use_nodes = True
            nodes = contextLamp.data.node_tree.nodes
            links = contextLamp.data.node_tree.links
            gobo_name, read_str_len = read_string(file)
            new_chunk.bytes_read += read_str_len
            projection = nodes.new(type='ShaderNodeTexImage')
            projection.label = gobo_name
            projection.location = (-340, 360)
            projection.image = load_image(gobo_name, dirname, place_holder=False, recursive=IMAGE_SEARCH, check_existing=True)
            emitnode = next((node for node in nodes if node.type == 'EMISSION'), False)
            emission = emitnode if emitnode else nodes.new(type='ShaderNodeEmission')
            emission.label = "Projector"
            emission.location = (0, 300)
            links.new(emission.outputs['Emission'], nodes['Light Output'].inputs[0])
            links.new(projection.outputs['Color'], emission.inputs[0])
        elif CreateLightObject and new_chunk.ID == OBJECT_HIERARCHY:  # Hierarchy
            child_id = get_hierarchy(new_chunk)
        elif CreateLightObject and new_chunk.ID == OBJECT_PARENT:
            get_parent(new_chunk, child_id)

        # If camera chunk
        elif new_chunk.ID == OBJECT_CAMERA:  # Basic camera support
            CreateBlenderObject = False
            if not CreateCamera:
                contextObName = None
                skip_to_end(file, new_chunk)
            else:
                CreateCameraObject = True
                camera = bpy.data.cameras.new("Camera")
                contextCamera = bpy.data.objects.new(contextObName, camera)
                context.view_layer.active_layer_collection.collection.objects.link(contextCamera)
                imported_objects.append(contextCamera)
                object_dictionary[contextObName] = contextCamera
                contextCamera.location = read_float_array(new_chunk)  # Position
                focus = mathutils.Vector(read_float_array(new_chunk))
                direction = calc_target(contextCamera.location, focus)  # Target
                contextCamera.rotation_euler.x = direction[0]
                contextCamera.rotation_euler.y = read_float(new_chunk)  # Roll
                contextCamera.rotation_euler.z = direction[1]
                contextCamera.data.lens = read_float(new_chunk)  # Focal length
            contextMatrix = None  # Reset matrix
        elif CreateCameraObject and new_chunk.ID == OBJECT_CAM_RANGES:  # Range
            camrange = read_float(new_chunk)
            startrange = camrange if camrange >= 0.01 else 0.1
            contextCamera.data.clip_start = startrange * CONSTRAIN
            contextCamera.data.clip_end = read_float(new_chunk) * CONSTRAIN
        elif CreateCameraObject and new_chunk.ID == OBJECT_HIERARCHY:  # Hierarchy
            child_id = get_hierarchy(new_chunk)
        elif CreateCameraObject and new_chunk.ID == OBJECT_PARENT:
            get_parent(new_chunk, child_id)

        # start keyframe section
        elif new_chunk.ID == EDITKEYFRAME:
            pass

        elif KEYFRAME and new_chunk.ID == KFDATA_KFSEG:
            start = read_long(new_chunk)
            context.scene.frame_start = start
            stop = read_long(new_chunk)
            context.scene.frame_end = stop

        elif KEYFRAME and new_chunk.ID == KFDATA_CURTIME:
            current = read_long(new_chunk)
            context.scene.frame_current = current

        # including these here means their OB_NODE_HDR are scanned
        elif new_chunk.ID in {KF_AMBIENT, KF_OBJECT, KF_OBJECT_CAMERA, KF_OBJECT_LIGHT, KF_OBJECT_SPOT_LIGHT}:
            tracktype = str([kf for kf,ck in globals().items() if ck == new_chunk.ID][0]).split("_")[1]
            tracking = str([kf for kf,ck in globals().items() if ck == new_chunk.ID][0]).split("_")[-1]
            spotting = str([kf for kf,ck in globals().items() if ck == new_chunk.ID][0]).split("_")[-2]
            object_id = hierarchy = ROOT_OBJECT
            child = None
            if not CreateWorld and tracking == 'AMBIENT':
                skip_to_end(file, new_chunk)
            if not CreateLight and tracking == 'LIGHT':
                skip_to_end(file, new_chunk)
            if not CreateCamera and tracking == 'CAMERA':
                skip_to_end(file, new_chunk)

        elif CreateTrackData and new_chunk.ID in {KF_TARGET_CAMERA, KF_TARGET_LIGHT}:
            tracktype = str([kf for kf,ck in globals().items() if ck == new_chunk.ID][0]).split("_")[1]
            tracking = str([kf for kf,ck in globals().items() if ck == new_chunk.ID][0]).split("_")[-1]
            child = None
            if not CreateLight and tracking == 'LIGHT':
                skip_to_end(file, new_chunk)
            if not CreateCamera and tracking == 'CAMERA':
                skip_to_end(file, new_chunk)

        elif new_chunk.ID == OBJECT_NODE_ID:
            object_id = read_short(new_chunk)

        elif new_chunk.ID == OBJECT_NODE_HDR:
            object_name, read_str_len = read_string(file)
            new_chunk.bytes_read += read_str_len
            temp_data = file.read(SZ_U_INT)
            new_chunk.bytes_read += SZ_U_INT
            hierarchy = read_short(new_chunk)
            child = object_dictionary.get(object_name)
            if child is None:
                if CreateWorld and tracking == 'AMBIENT':
                    child = context.scene.world
                    child.use_nodes = True
                    nodetree = child.node_tree
                    links = nodetree.links
                    nodes = nodetree.nodes
                    worldout = nodes['World Output']
                    mixshade = nodes.new(type='ShaderNodeMixShader')
                    ambinode = nodes.new(type='ShaderNodeEmission')
                    ambilite = nodes.new(type='ShaderNodeRGB')
                    ambilite.label = "Ambient Color"
                    mixshade.label = "Surface"
                    ambinode.inputs[0].default_value[:3] = child.color
                    ambinode.location = (10, 180)
                    worldout.location = (600, 180)
                    mixshade.location = (300, 280)
                    ambilite.location = (-250, 100)
                    links.new(mixshade.outputs[0], worldout.inputs['Surface'])
                    links.new(nodes['Background'].outputs[0], mixshade.inputs[1])
                    links.new(ambinode.outputs[0], mixshade.inputs[2])
                    links.new(ambilite.outputs[0], ambinode.inputs[0])
                    ambinode.label = object_name if object_name != '$AMBIENT$' else "Ambient"
                elif CreateEmpty and tracking == 'OBJECT' and object_name == '$$$DUMMY':
                    child = bpy.data.objects.new(object_name, None)  # Create an empty object
                    context.view_layer.active_layer_collection.collection.objects.link(child)
                    imported_objects.append(child)
                else:
                    tracking = tracktype = None
            if tracktype != 'TARGET' and tracking != 'AMBIENT':
                object_dict[object_id] = child
                object_list.append(child)
                object_parent.append(hierarchy)
                pivot_list.append(mathutils.Vector((0.0, 0.0, 0.0)))

        elif new_chunk.ID == PARENT_NAME:
            parent_name, read_str_len = read_string(file)
            parent_dictionary.setdefault(parent_name, []).append(child)
            new_chunk.bytes_read += read_str_len

        elif new_chunk.ID == OBJECT_INSTANCE_NAME and tracking == 'OBJECT':
            instance_name, read_str_len = read_string(file)
            if child.name == '$$$DUMMY':
                child.name = instance_name
            else:  # Child is an instance
                child = child.copy()
                child.name = object_name + "." + instance_name
                context.view_layer.active_layer_collection.collection.objects.link(child)
                object_dict[object_id] = child
                object_list[-1] = child
            object_dictionary[child.name] = child
            new_chunk.bytes_read += read_str_len

        elif new_chunk.ID == OBJECT_PIVOT and tracking == 'OBJECT':  # Pivot
            pivot = read_float_array(new_chunk)
            pivot_list[len(pivot_list) - 1] = mathutils.Vector(pivot)

        elif new_chunk.ID == MORPH_SMOOTH and tracking == 'OBJECT':  # Smooth angle
            smooth_angle = read_float(new_chunk)
            if child.data is not None:  # Check if child is a dummy
                child.data.set_sharp_from_angle(angle=smooth_angle)

        elif KEYFRAME and new_chunk.ID == COL_TRACK_TAG and tracking == 'AMBIENT':  # Ambient
            keyframe_data = {}
            keyframe_data[0] = child.color[:]
            child.color = read_track_data(new_chunk)[0]
            ambinode.inputs[0].default_value[:3] = child.color
            ambilite.outputs[0].default_value[:3] = child.color
            for keydata in keyframe_data.items():
                ambinode.inputs[0].default_value[:3] = keydata[1]
                child.color = ambilite.outputs[0].default_value[:3] = keydata[1]
                child.keyframe_insert(data_path="color", frame=keydata[0])
                nodetree.keyframe_insert(data_path="nodes[\"RGB\"].outputs[0].default_value", frame=keydata[0])
                nodetree.keyframe_insert(data_path="nodes[\"Emission\"].inputs[0].default_value", frame=keydata[0])
            contextTrack_flag = False

        elif KEYFRAME and new_chunk.ID == COL_TRACK_TAG and tracking == 'LIGHT':  # Color
            keyframe_data = {}
            keyframe_data[0] = child.data.color[:]
            child.data.color = read_track_data(new_chunk)[0]
            for keydata in keyframe_data.items():
                child.data.color = keydata[1]
                child.data.keyframe_insert(data_path="color", frame=keydata[0])
            contextTrack_flag = False

        elif KEYFRAME and new_chunk.ID == POS_TRACK_TAG and tracktype == 'OBJECT':  # Translation
            keyframe_data = {}
            keyframe_data[0] = child.location[:]
            child.location = read_track_data(new_chunk)[0]
            if child.type in {'LIGHT', 'CAMERA'}:
                trackposition[0] = child.location
                CreateTrackData = True
            if contextTrack_flag & 0x8:  # Flag 0x8 locks X axis
                child.lock_location[0] = True
            if contextTrack_flag & 0x10:  # Flag 0x10 locks Y axis
                child.lock_location[1] = True
            if contextTrack_flag & 0x20:  # Flag 0x20 locks Z axis
                child.lock_location[2] = True
            for keydata in keyframe_data.items():
                trackposition[keydata[0]] = keydata[1]  # Keep track to position for target calculation
                child.location = apply_constrain(keydata[1]) if hierarchy == ROOT_OBJECT else mathutils.Vector(keydata[1])
                if MEASURE != 1.0:
                    child.location = child.location * MEASURE
                if hierarchy == ROOT_OBJECT:
                    child.location.rotate(CONVERSE)
                if not contextTrack_flag & 0x100:  # Flag 0x100 unlinks X axis
                    child.keyframe_insert(data_path="location", index=0, frame=keydata[0])
                if not contextTrack_flag & 0x200:  # Flag 0x200 unlinks Y axis
                    child.keyframe_insert(data_path="location", index=1, frame=keydata[0])
                if not contextTrack_flag & 0x400:  # Flag 0x400 unlinks Z axis
                    child.keyframe_insert(data_path="location", index=2, frame=keydata[0])
            contextTrack_flag = False

        elif KEYFRAME and new_chunk.ID == POS_TRACK_TAG and tracktype == 'TARGET':  # Target position
            keyframe_data = {}
            location = child.location
            keyframe_data[0] = trackposition[0]
            target = mathutils.Vector(read_track_data(new_chunk)[0])
            direction = calc_target(location, target)
            child.rotation_euler.x = direction[0]
            child.rotation_euler.z = direction[1]
            for keydata in keyframe_data.items():
                track = trackposition.get(keydata[0], child.location)
                locate = mathutils.Vector(track)
                target = mathutils.Vector(keydata[1])
                direction = calc_target(locate, target)
                rotate = mathutils.Euler((direction[0], 0.0, direction[1]), 'XYZ').to_matrix()
                scale = mathutils.Vector.Fill(3, (CONSTRAIN * 0.1)) if CONSTRAIN != 0.0 else child.scale
                transformation = mathutils.Matrix.LocRotScale(locate, rotate, scale)
                child.matrix_world = transformation
                if MEASURE != 1.0:
                    child.matrix_world = mathutils.Matrix.Scale(MEASURE,4) @ child.matrix_world
                if hierarchy == ROOT_OBJECT:
                    child.matrix_world = CONVERSE @ child.matrix_world
                child.keyframe_insert(data_path="rotation_euler", index=0, frame=keydata[0])
                child.keyframe_insert(data_path="rotation_euler", index=2, frame=keydata[0])
            contextTrack_flag = False

        elif KEYFRAME and new_chunk.ID == ROT_TRACK_TAG and tracktype == 'OBJECT':  # Rotation
            keyframe_rotation = {}
            keyframe_rotation[0] = child.rotation_axis_angle[:]
            tflags = read_short(new_chunk)
            temp_data = file.read(SZ_U_INT * 2)
            new_chunk.bytes_read += SZ_U_INT * 2
            nkeys = read_long(new_chunk)
            if tflags & 0x8:  # Flag 0x8 locks X axis
                child.lock_rotation[0] = True
            if tflags & 0x10:  # Flag 0x10 locks Y axis
                child.lock_rotation[1] = True
            if tflags & 0x20:  # Flag 0x20 locks Z axis
                child.lock_rotation[2] = True
            for i in range(nkeys):
                nframe = read_long(new_chunk)
                nflags = read_short(new_chunk)
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

        elif KEYFRAME and new_chunk.ID == SCL_TRACK_TAG and tracktype == 'OBJECT':  # Scale
            keyframe_data = {}
            keyframe_data[0] = child.scale[:]
            child.scale = read_track_data(new_chunk)[0]
            if contextTrack_flag & 0x8:  # Flag 0x8 locks X axis
                child.lock_scale[0] = True
            if contextTrack_flag & 0x10:  # Flag 0x10 locks Y axis
                child.lock_scale[1] = True
            if contextTrack_flag & 0x20:  # Flag 0x20 locks Z axis
                child.lock_scale[2] = True
            for keydata in keyframe_data.items():
                child.scale = apply_constrain(keydata[1]) if hierarchy == ROOT_OBJECT else mathutils.Vector(keydata[1])
                if not contextTrack_flag & 0x100:  # Flag 0x100 unlinks X axis
                    child.keyframe_insert(data_path="scale", index=0, frame=keydata[0])
                if not contextTrack_flag & 0x200:  # Flag 0x200 unlinks Y axis
                    child.keyframe_insert(data_path="scale", index=1, frame=keydata[0])
                if not contextTrack_flag & 0x400:  # Flag 0x400 unlinks Z axis
                    child.keyframe_insert(data_path="scale", index=2, frame=keydata[0])
            contextTrack_flag = False

        elif KEYFRAME and new_chunk.ID == ROLL_TRACK_TAG and tracktype == 'OBJECT':  # Roll angle
            keyframe_angle = {}
            keyframe_angle[0] = child.rotation_euler.y
            child.rotation_euler.y = read_track_angle(new_chunk)[0]
            for keydata in keyframe_angle.items():
                child.rotation_euler.y = keydata[1]
                if hierarchy == ROOT_OBJECT:
                    child.rotation_euler.rotate(CONVERSE)
                child.keyframe_insert(data_path="rotation_euler", index=1, frame=keydata[0])

        elif KEYFRAME and new_chunk.ID == FOV_TRACK_TAG and tracking == 'CAMERA':  # Field of view
            keyframe_angle = {}
            keyframe_angle[0] = child.data.angle
            child.data.angle = read_track_angle(new_chunk)[0]
            for keydata in keyframe_angle.items():
                child.data.lens = (child.data.sensor_width / 2) / math.tan(keydata[1] / 2)
                child.data.keyframe_insert(data_path="lens", frame=keydata[0])

        elif KEYFRAME and new_chunk.ID == HOTSPOT_TRACK_TAG and tracking == 'LIGHT' and spotting == 'SPOT':  # Hotspot
            keyframe_angle = {}
            cone_angle = math.degrees(child.data.spot_size)
            keyframe_angle[0] = cone_angle-(child.data.spot_blend * math.floor(cone_angle))
            hot_spot = math.degrees(read_track_angle(new_chunk)[0])
            child.data.spot_blend = 1.0 - (hot_spot / cone_angle)
            for keydata in keyframe_angle.items():
                child.data.spot_blend = 1.0 - (math.degrees(keydata[1]) / cone_angle)
                child.data.keyframe_insert(data_path="spot_blend", frame=keydata[0])

        elif KEYFRAME and new_chunk.ID == FALLOFF_TRACK_TAG and tracking == 'LIGHT' and spotting == 'SPOT':  # Falloff
            keyframe_angle = {}
            keyframe_angle[0] = math.degrees(child.data.spot_size)
            child.data.spot_size = read_track_angle(new_chunk)[0]
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
        putContextMesh(context, contextMesh_vertls, contextMesh_facels, contextMesh_flag,
            contextMeshMaterials, contextMesh_smooth, WORLD_MATRIX)

    # Assign parents to objects
    # check _if_ we need to assign first because doing so recalcs the depsgraph
    for ind, ob in enumerate(object_list):
        parent = object_parent[ind]
        if parent == ROOT_OBJECT:
            if ob is not None:
                ob.parent = None
        elif parent not in object_dict:
            try:
                ob.parent = object_list[parent]
            except:  # seems object is None or not in list
                object_list.pop(ind)
        else:  # get parent from node_id number
            try:
                ob.parent = object_dict.get(parent)
            except:  # object is None or self to parent exception
                object_list.pop(ind)

        #pivot_list[ind] += pivot_list[parent]  # Not sure this is correct, should parent space matrix be applied before combining?

    # if parent name
    parent_dictionary.pop(None, ...)
    for par, objs in parent_dictionary.items():
        parent = object_dictionary.get(par)
        for ob in objs:
            if parent is not None:
                ob.parent = parent
    parent_dictionary.clear()

    # If hierarchy
    hierarchy = dict(zip(childs_list, parent_list))
    hierarchy.pop(None, ...)
    for idt, (child, parent) in enumerate(hierarchy.items()):
        child_obj = object_dictionary.get(child)
        parent_obj = object_dictionary.get(parent)
        if child_obj and parent_obj is not None:
            child_obj.parent = parent_obj

    # fix pivots
    for ind, ob in enumerate(object_list):
        if ob is None:  # remove None
            object_list.remove(ob)
        elif ob.type == 'MESH':
            pivot = pivot_list[ind]
            pivot_matrix = object_matrix.get(ob, mathutils.Matrix())  # unlikely to fail
            pivot_matrix = mathutils.Matrix.Translation(-1 * pivot)
            # pivot_matrix = mathutils.Matrix.Translation(pivot_matrix.to_3x3() @ -pivot)
            ob.data.transform(pivot_matrix)


##########
# IMPORT #
##########

def load_3ds(filepath, context, CONSTRAIN=10.0, UNITS=False, IMAGE_SEARCH=True,
             FILTER=None, WORLD_MATRIX=False, KEYFRAME=True, APPLY_MATRIX=True,
             CONVERSE=None, CURSOR=False, PIVOT=False):

    print("importing 3DS: %r..." % (filepath), end="")

    if bpy.ops.object.select_all.poll():
        bpy.ops.object.select_all(action='DESELECT')

    MEASURE = 1.0
    duration = time.time()
    current_chunk = Chunk()
    file = open(filepath, 'rb')
    context.window.cursor_set('WAIT')

    # here we go!
    read_chunk(file, current_chunk)
    if current_chunk.ID != PRIMARY:
        context.window.cursor_set('DEFAULT')
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

    if UNITS:
        unit_length = scn.unit_settings.length_unit
        if unit_length == 'MILES':
            MEASURE = 1609.344
        elif unit_length == 'KILOMETERS':
            MEASURE = 1000.0
        elif unit_length == 'FEET':
            MEASURE = 0.3048
        elif unit_length == 'INCHES':
            MEASURE = 0.0254
        elif unit_length == 'CENTIMETERS':
            MEASURE = 0.01
        elif unit_length == 'MILLIMETERS':
            MEASURE = 0.001
        elif unit_length == 'THOU':
            MEASURE = 0.0000254
        elif unit_length == 'MICROMETERS':
            MEASURE = 0.000001

    imported_objects = []  # Fill this list with objects
    process_next_chunk(context, file, current_chunk, imported_objects, CONSTRAIN, FILTER,
                       IMAGE_SEARCH, WORLD_MATRIX, KEYFRAME, CONVERSE, MEASURE, CURSOR)

    # fixme, make unglobal
    object_dictionary.clear()
    object_matrix.clear()

    """
    if APPLY_MATRIX:
        for ob in imported_objects:
            if ob.type == 'MESH':
                ob.data.transform(ob.matrix_local.inverted())
    """

    if UNITS:
        unit_mtx = mathutils.Matrix.Scale(MEASURE,4)
        for ob in imported_objects:
            if ob.type == 'MESH':
                ob.data.transform(unit_mtx)

    if CONVERSE and not KEYFRAME:
        for ob in imported_objects:
            ob.location.rotate(CONVERSE)
            ob.rotation_euler.rotate(CONVERSE)

    # Select all new objects
    for ob in imported_objects:
        if ob.type == 'LIGHT' and ob.data.type == 'SPOT':
            square = math.sqrt(pow(1.0,2) + pow(1.0,2))
            aspect = ob.empty_display_size
            ob.scale.x = (aspect * square / (math.sqrt(pow(aspect,2) + 1.0)))
            ob.scale.y = (square / (math.sqrt(pow(aspect,2) + 1.0)))
            ob.scale.z = 1.0
        ob.select_set(True)
        if ob.type == 'MESH':
            if PIVOT:
                bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN')
            if not APPLY_MATRIX:  # Reset transform
                bpy.ops.object.rotation_clear()
                bpy.ops.object.location_clear()
                bpy.ops.object.scale_clear()

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
    global_clamp_size = CONSTRAIN * 10000
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

        mtx_scale = mathutils.Matrix.Scale(scale, 4)
        for obj in imported_objects:
            if obj.parent is None:
                obj.matrix_world = mtx_scale @ obj.matrix_world

        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type == 'VIEW_3D':
                    area.spaces[0].clip_start = scale * 0.1
                    area.spaces[0].clip_end = scale * 10000

    context.window.cursor_set('DEFAULT')
    print(" done in %.4f sec." % (time.time() - duration))
    file.close()


def load(operator, context, files=None, directory="", filepath="", constrain_size=0.0, use_scene_unit=False,
         use_image_search=True, object_filter=None, use_world_matrix=False, use_keyframes=True,
         use_apply_transform=True, global_matrix=None, use_cursor=False, use_center_pivot=False):

    for f in files:
        load_3ds(os.path.join(directory, f.name), context, CONSTRAIN=constrain_size, UNITS=use_scene_unit,
             IMAGE_SEARCH=use_image_search, FILTER=object_filter, WORLD_MATRIX=use_world_matrix, KEYFRAME=use_keyframes,
             APPLY_MATRIX=use_apply_transform, CONVERSE=global_matrix, CURSOR=use_cursor, PIVOT=use_center_pivot,)

    return {'FINISHED'}
