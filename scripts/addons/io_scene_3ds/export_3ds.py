# SPDX-FileCopyrightText: 2005 Bob Holcomb
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Exporting is based on 3ds loader from www.gametutorials.com(Thanks DigiBen) and using information
from the lib3ds project (http://lib3ds.sourceforge.net/) sourcecode.
"""

import bpy
import time
import math
import struct
import mathutils
import bpy_extras
from bpy_extras import node_shader_utils

###################
# Data Structures #
###################

# Some of the chunks that we will export
# >----- Primary Chunk, at the beginning of each file
PRIMARY = 0x4D4D

# >----- Main Chunks
OBJECTINFO = 0x3D3D  # Main mesh object chunk before material and object information
MESHVERSION = 0x3D3E  # This gives the version of the mesh
VERSION = 0x0002  # This gives the version of the .3ds file
KFDATA = 0xB000  # This is the header for all of the keyframe info

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
LAYER_FOG = 0x2302  # The fog layer atmosphere settings
USE_LAYER_FOG = 0x2303  # The fog layer atmosphere flag
MATERIAL = 45055  # 0xAFFF // This stored the texture info
OBJECT = 16384  # 0x4000 // This stores the faces, vertices, etc...

# >------ sub defines of MATERIAL
MATNAME = 0xA000  # This holds the material name
MATAMBIENT = 0xA010  # Ambient color of the object/material
MATDIFFUSE = 0xA020  # This holds the color of the object/material
MATSPECULAR = 0xA030  # Specular color of the object/material
MATSHINESS = 0xA040  # Specular intensity of the object/material (percent)
MATSHIN2 = 0xA041  # Reflection of the object/material (percent)
MATSHIN3 = 0xA042  # metallic/mirror of the object/material (percent)
MATTRANS = 0xA050  # Transparency value (100-OpacityValue) (percent)
MATSELFILLUM = 0xA080  # # Material self illumination flag
MATSELFILPCT = 0xA084  # Self illumination strength (percent)
MATWIRE = 0xA085  # Material wireframe rendered flag
MATFACEMAP = 0xA088  # Face mapped textures flag
MATPHONGSOFT = 0xA08C  # Phong soften material flag
MATWIREABS = 0xA08E  # Wire size in units flag
MATWIRESIZE = 0xA087  # Rendered wire size in pixels
MATSHADING = 0xA100  # Material shading method

# >------ sub defines of MAT_MAP
MAT_DIFFUSEMAP = 0xA200  # This is a header for a new diffuse texture
MAT_SPECMAP = 0xA204  # head for specularity map
MAT_OPACMAP = 0xA210  # head for opacity map
MAT_REFLMAP = 0xA220  # head for reflect map
MAT_BUMPMAP = 0xA230  # head for normal map
MAT_BUMP_PERCENT = 0xA252  # Normalmap strength (percent)
MAT_TEX2MAP = 0xA33A  # head for secondary texture
MAT_SHINMAP = 0xA33C  # head for roughness map
MAT_SELFIMAP = 0xA33D  # head for emission map
MAT_MAP_FILE = 0xA300  # This holds the file name of a texture
MAT_MAP_TILING = 0xa351   # 2nd bit (from LSB) is mirror UV flag
MAT_MAP_TEXBLUR = 0xA353  # Texture blurring factor
MAT_MAP_USCALE = 0xA354   # U axis scaling
MAT_MAP_VSCALE = 0xA356   # V axis scaling
MAT_MAP_UOFFSET = 0xA358  # U axis offset
MAT_MAP_VOFFSET = 0xA35A  # V axis offset
MAT_MAP_ANG = 0xA35C  # UV rotation around the z-axis in rad
MAP_COL1 = 0xA360  # Tint Color1
MAP_COL2 = 0xA362  # Tint Color2
MAP_RCOL = 0xA364  # Red tint
MAP_GCOL = 0xA366  # Green tint
MAP_BCOL = 0xA368  # Blue tint

RGB = 0x0010  # RGB float Color1
RGB1 = 0x0011  # RGB int Color1
RGBI = 0x0012  # RGB int Color2
RGBF = 0x0013  # RGB float Color2
PCT = 0x0030  # Percent chunk
PCTF = 0x0031  # Percent float
MASTERSCALE = 0x0100  # Master scale factor

# >------ sub defines of OBJECT
OBJECT_MESH = 0x4100  # This lets us know that we are reading a new object
OBJECT_LIGHT = 0x4600  # This lets us know we are reading a light object
OBJECT_CAMERA = 0x4700  # This lets us know we are reading a camera object
OBJECT_HIERARCHY = 0x4F00  # Hierarchy id of the object
OBJECT_PARENT = 0x4F10  # Parent id of the object

# >------ Sub defines of LIGHT
LIGHT_MULTIPLIER = 0x465B  # The light energy factor
LIGHT_INNER_RANGE = 0x4659  # Light inner range value
LIGHT_OUTER_RANGE = 0x465A  # Light outer range value
LIGHT_ATTENUATE = 0x4625  # Light attenuation flag
LIGHT_SPOTLIGHT = 0x4610  # The target of a spotlight
LIGHT_SPOT_ROLL = 0x4656  # Light spot roll angle
LIGHT_SPOT_SHADOWED = 0x4630  # Light spot shadow flag
LIGHT_SPOT_LSHADOW = 0x4641  # Light spot shadow parameters
LIGHT_SPOT_SEE_CONE = 0x4650  # Light spot show cone flag
LIGHT_SPOT_RECTANGLE = 0x4651  # Light spot rectangle flag
LIGHT_SPOT_OVERSHOOT = 0x4652  # Light spot overshoot flag
LIGHT_SPOT_PROJECTOR = 0x4653  # Light spot projection bitmap
LIGHT_SPOT_ASPECT = 0x4657  # Light spot aspect ratio

# >------ sub defines of CAMERA
OBJECT_CAM_RANGES = 0x4720  # The camera range values

# >------ sub defines of OBJECT_MESH
OBJECT_VERTICES = 0x4110  # The objects vertices
OBJECT_VERTFLAGS = 0x4111  # The objects vertex flags
OBJECT_FACES = 0x4120  # The objects faces
OBJECT_MATERIAL = 0x4130  # This is found if the object has a material, either texture map or color
OBJECT_UV = 0x4140  # The UV texture coordinates
OBJECT_SMOOTH = 0x4150  # The objects smooth groups
OBJECT_TRANS_MATRIX = 0x4160  # The Object Matrix

# >------ sub defines of KFDATA
AMBIENT_NODE_TAG = 0xB001  # Ambient node tag
OBJECT_NODE_TAG = 0xB002  # Object tree tag
CAMERA_NODE_TAG = 0xB003  # Camera object tag
TARGET_NODE_TAG = 0xB004  # Camera target tag
LIGHT_NODE_TAG = 0xB005  # Light object tag
LTARGET_NODE_TAG = 0xB006  # Light target tag
SPOT_NODE_TAG = 0xB007  # Spotlight tag
KFDATA_KFSEG = 0xB008  # Frame start & end
KFDATA_KFCURTIME = 0xB009  # Frame current
KFDATA_KFHDR = 0xB00A  # Keyframe header

# >------ sub defines of OBJECT_NODE_TAG
OBJECT_NODE_ID = 0xB030  # Object hierachy ID
OBJECT_NODE_HDR = 0xB010  # Hierachy tree header
OBJECT_INSTANCE_NAME = 0xB011  # Object instance name
OBJECT_PARENT_NAME = 0x80F0  # Object parent name
OBJECT_PIVOT = 0xB013  # Object pivot position
OBJECT_BOUNDBOX = 0xB014  # Object boundbox
OBJECT_MORPH_SMOOTH = 0xB015  # Object smooth angle
POS_TRACK_TAG = 0xB020  # Position transform tag
ROT_TRACK_TAG = 0xB021  # Rotation transform tag
SCL_TRACK_TAG = 0xB022  # Scale transform tag
FOV_TRACK_TAG = 0xB023  # Field of view tag
ROLL_TRACK_TAG = 0xB024  # Roll transform tag
COL_TRACK_TAG = 0xB025  # Color transform tag
HOTSPOT_TRACK_TAG = 0xB027  # Hotspot transform tag
FALLOFF_TRACK_TAG = 0xB028  # Falloff transform tag

ROOT_OBJECT = 0xFFFF  # Root object


# So 3ds max can open files, limit names to 12 in length
# this is very annoying for filenames!
name_unique = []  # stores str, ascii only
name_mapping = {}  # stores {orig: byte} mapping

def sane_name(name):
    name_fixed = name_mapping.get(name)
    if name_fixed is not None:
        return name_fixed

    # Strip non ascii chars
    new_name_clean = new_name = name.encode("ASCII", "replace").decode("ASCII")[:12]
    i = 0

    while new_name in name_unique:
        new_name = new_name_clean + '.%.3d' % i
        i += 1

    # Note, appending the 'str' version
    name_unique.append(new_name)
    name_mapping[name] = new_name = new_name.encode("ASCII", "replace")
    return new_name


def uv_key(uv):
    return round(uv[0], 6), round(uv[1], 6)

# Size defines
SZ_SHORT = 2
SZ_INT = 4
SZ_FLOAT = 4

class _3ds_ushort(object):
    """Class representing a short (2-byte integer) for a 3ds file."""
    __slots__ = ("value", )

    def __init__(self, val=0):
        self.value = val

    def get_size(self):
        return SZ_SHORT

    def write(self, file):
        file.write(struct.pack('<H', self.value))

    def __str__(self):
        return str(self.value)


class _3ds_uint(object):
    """Class representing an int (4-byte integer) for a 3ds file."""
    __slots__ = ("value", )

    def __init__(self, val):
        self.value = val

    def get_size(self):
        return SZ_INT

    def write(self, file):
        file.write(struct.pack('<I', self.value))

    def __str__(self):
        return str(self.value)


class _3ds_float(object):
    """Class representing a 4-byte IEEE floating point number for a 3ds file."""
    __slots__ = ("value", )

    def __init__(self, val):
        self.value = val

    def get_size(self):
        return SZ_FLOAT

    def write(self, file):
        file.write(struct.pack('<f', self.value))

    def __str__(self):
        return str(self.value)


class _3ds_string(object):
    """Class representing a zero-terminated string for a 3ds file."""
    __slots__ = ("value", )

    def __init__(self, val):
        assert type(val) == bytes
        self.value = val

    def get_size(self):
        return (len(self.value) + 1)

    def write(self, file):
        binary_format = '<%ds' % (len(self.value) + 1)
        file.write(struct.pack(binary_format, self.value))

    def __str__(self):
        return str((self.value).decode("ASCII"))


class _3ds_point_3d(object):
    """Class representing a three-dimensional point for a 3ds file."""
    __slots__ = "x", "y", "z"

    def __init__(self, point):
        self.x, self.y, self.z = point

    def get_size(self):
        return 3 * SZ_FLOAT

    def write(self, file):
        file.write(struct.pack('<3f', self.x, self.y, self.z))

    def __str__(self):
        return '(%f, %f, %f)' % (self.x, self.y, self.z)


# Used for writing a track
class _3ds_point_4d(object):
    """Class representing a four-dimensional point for a 3ds file, for instance a quaternion."""
    __slots__ = "w", "x", "y", "z"

    def __init__(self, point):
        self.w, self.x, self.y, self.z = point

    def get_size(self):
        return 4 * SZ_FLOAT

    def write(self,file):
        data=struct.pack('<4f', self.w, self.x, self.y, self.z)
        file.write(data)

    def __str__(self):
        return '(%f, %f, %f, %f)' % (self.w, self.x, self.y, self.z)


class _3ds_point_uv(object):
    """Class representing a UV-coordinate for a 3ds file."""
    __slots__ = ("uv", )

    def __init__(self, point):
        self.uv = point

    def get_size(self):
        return 2 * SZ_FLOAT

    def write(self, file):
        data = struct.pack('<2f', self.uv[0], self.uv[1])
        file.write(data)

    def __str__(self):
        return '(%g, %g)' % self.uv


class _3ds_float_color(object):
    """Class representing a rgb float color for a 3ds file."""
    __slots__ = "r", "g", "b"

    def __init__(self, col):
        self.r, self.g, self.b = col

    def get_size(self):
        return 3 * SZ_FLOAT

    def write(self, file):
        file.write(struct.pack('<3f', self.r, self.g, self.b))

    def __str__(self):
        return '{%f, %f, %f}' % (self.r, self.g, self.b)


class _3ds_rgb_color(object):
    """Class representing a (24-bit) rgb color for a 3ds file."""
    __slots__ = "r", "g", "b"

    def __init__(self, col):
        self.r, self.g, self.b = col

    def get_size(self):
        return 3

    def write(self, file):
        file.write(struct.pack('<3B', int(255 * self.r), int(255 * self.g), int(255 * self.b)))

    def __str__(self):
        return '{%f, %f, %f}' % (self.r, self.g, self.b)


class _3ds_face(object):
    """Class representing a face for a 3ds file."""
    __slots__ = ("vindex", "flag", )

    def __init__(self, vindex, flag):
        self.vindex = vindex
        self.flag = flag

    def get_size(self):
        return 4 * SZ_SHORT

    # No need to validate every face vert, the oversized array will catch this problem
    def write(self, file):
        # The last short is used for face flags
        file.write(struct.pack('<4H', self.vindex[0], self.vindex[1], self.vindex[2], self.flag))

    def __str__(self):
        return '[%d %d %d %d]' % (self.vindex[0], self.vindex[1], self.vindex[2], self.flag)


class _3ds_array(object):
    """Class representing an array of variables for a 3ds file.
    Consists of a _3ds_ushort to indicate the number of items, followed by the items themselves."""
    __slots__ = "values", "size"

    def __init__(self):
        self.values = []
        self.size = SZ_SHORT

    # Add an item
    def add(self, item):
        self.values.append(item)
        self.size += item.get_size()

    def get_size(self):
        return self.size

    def validate(self):
        return len(self.values) <= 65535

    def write(self, file):
        _3ds_ushort(len(self.values)).write(file)
        for value in self.values:
            value.write(file)

    # To not overwhelm the output in a dump, a _3ds_array only
    # outputs the number of items, not all of the actual items
    def __str__(self):
        return '(%d items)' % len(self.values)


class _3ds_named_variable(object):
    """Convenience class for named variables."""
    __slots__ = "value", "name"

    def __init__(self, name, val=None):
        self.name = name
        self.value = val

    def get_size(self):
        if self.value is None:
            return 0
        else:
            return self.value.get_size()

    def write(self, file):
        if self.value is not None:
            self.value.write(file)

    def dump(self, indent):
        if self.value is not None:
            print(indent * " ",
                  self.name if self.name else "[unnamed]",
                  " = ",
                  self.value)


# The chunk class
class _3ds_chunk(object):
    """Class representing a chunk in a 3ds file.
    Chunks contain zero or more variables, followed by zero or more subchunks."""
    __slots__ = "ID", "size", "variables", "subchunks"

    def __init__(self, chunk_id=0):
        self.ID = _3ds_ushort(chunk_id)
        self.size = _3ds_uint(0)
        self.variables = []
        self.subchunks = []

    def add_variable(self, name, var):
        """Add a named variable.
        The name is mostly for debugging purposes."""
        self.variables.append(_3ds_named_variable(name, var))

    def add_subchunk(self, chunk):
        """Add a subchunk."""
        self.subchunks.append(chunk)

    def get_size(self):
        """Calculate the size of the chunk and return it.
        The sizes of the variables and subchunks are used to determine this chunk's size."""
        tmpsize = self.ID.get_size() + self.size.get_size()
        for variable in self.variables:
            tmpsize += variable.get_size()
        for subchunk in self.subchunks:
            tmpsize += subchunk.get_size()
        self.size.value = tmpsize
        return self.size.value

    def validate(self):
        for var in self.variables:
            func = getattr(var.value, "validate", None)
            if (func is not None) and not func():
                return False

        for chunk in self.subchunks:
            func = getattr(chunk, "validate", None)
            if (func is not None) and not func():
                return False

        return True

    def write(self, file):
        """Write the chunk to a file.
        Uses the write function of the variables and the subchunks to do the actual work."""

        # Write header
        self.ID.write(file)
        self.size.write(file)
        for variable in self.variables:
            variable.write(file)
        for subchunk in self.subchunks:
            subchunk.write(file)

    def dump(self, indent=0):
        """Write the chunk to a file.
        Dump is used for debugging purposes, to dump the contents of a chunk to the standard output.
        Uses the dump function of the named variables and the subchunks to do the actual work."""
        print(indent * " ",
              'ID=%r' % hex(self.ID.value),
              'size=%r' % self.get_size())
        for variable in self.variables:
            variable.dump(indent + 1)
        for subchunk in self.subchunks:
            subchunk.dump(indent + 1)


#############
# MATERIALS #
#############

def get_material_image(material):
    """ Get images from paint slots."""
    if material:
        pt = material.paint_active_slot
        tex = material.texture_paint_images
        if pt < len(tex):
            slot = tex[pt]
            if slot.type == 'IMAGE':
                return slot


def get_uv_image(ma):
    """ Get image from material wrapper."""
    if ma and ma.use_nodes:
        mat_wrap = node_shader_utils.PrincipledBSDFWrapper(ma)
        mat_tex = mat_wrap.base_color_texture
        if mat_tex and mat_tex.image is not None:
            return mat_tex.image
    else:
        return get_material_image(ma)


def make_material_subchunk(chunk_id, color):
    """Make a material subchunk.
    Used for color subchunks, such as diffuse color or ambient color subchunks."""
    mat_sub = _3ds_chunk(chunk_id)
    col1 = _3ds_chunk(RGB1)
    col1.add_variable("color1", _3ds_rgb_color(color))
    mat_sub.add_subchunk(col1)
    # Optional
    # col2 = _3ds_chunk(RGBI)
    # col2.add_variable("color2", _3ds_rgb_color(color))
    # mat_sub.add_subchunk(col2)
    return mat_sub


def make_percent_subchunk(chunk_id, percent):
    """Make a percentage based subchunk."""
    pct_sub = _3ds_chunk(chunk_id)
    pcti = _3ds_chunk(PCT)
    pcti.add_variable("percent", _3ds_ushort(int(round(percent * 100, 0))))
    pct_sub.add_subchunk(pcti)
    # Optional
    # pctf = _3ds_chunk(PCTF)
    # pctf.add_variable("pctfloat", _3ds_float(round(percent, 6)))
    # pct_sub.add_subchunk(pctf)
    return pct_sub


def make_texture_chunk(chunk_id, teximages, pct):
    """Make Material Map texture chunk."""
    # Add texture percentage value (100 = 1.0)
    mat_sub = make_percent_subchunk(chunk_id, pct)
    has_entry = False

    def add_image(img, extension):
        filename = bpy.path.basename(img.filepath)
        mat_sub_file = _3ds_chunk(MAT_MAP_FILE)
        mat_sub_tiling = _3ds_chunk(MAT_MAP_TILING)
        mat_sub_file.add_variable("image", _3ds_string(sane_name(filename)))
        mat_sub.add_subchunk(mat_sub_file)

        tiling = 0
        if extension == 'EXTEND':  # decal flag
            tiling |= 0x1
        if extension == 'MIRROR':  # mirror flag
            tiling |= 0x2
        if extension == 'CLIP':  # no wrap
            tiling |= 0x10

        mat_sub_tiling.add_variable("tiling", _3ds_ushort(tiling))
        mat_sub.add_subchunk(mat_sub_tiling)

    for tex in teximages:
        extend = tex.extension
        add_image(tex.image, extend)
        has_entry = True

    return mat_sub if has_entry else None


def make_material_texture_chunk(chunk_id, texslots, pct):
    """Make Material Map texture chunk given a seq. of MaterialTextureSlot's
    Paint slots are optionally used as image source if no nodes are used."""

    # Add texture percentage value
    mat_sub = make_percent_subchunk(chunk_id, pct)
    has_entry = False

    def add_texslot(texslot):
        image = texslot.image
        socket = None

        filename = bpy.path.basename(image.filepath)
        mat_sub_file = _3ds_chunk(MAT_MAP_FILE)
        mat_sub_file.add_variable("mapfile", _3ds_string(sane_name(filename)))
        mat_sub.add_subchunk(mat_sub_file)
        for link in texslot.socket_dst.links:
            socket = link.from_socket.identifier

        mat_sub_mapflags = _3ds_chunk(MAT_MAP_TILING)
        """Control bit flags, where 0x1 activates decaling, 0x2 activates mirror,
        0x8 activates inversion, 0x10 deactivates tiling, 0x20 activates summed area sampling,
        0x40 activates alpha source, 0x80 activates tinting, 0x100 ignores alpha, 0x200 activates RGB tint.
        Bits 0x80, 0x100, and 0x200 are only used with TEXMAP, TEX2MAP, and SPECMAP chunks.
        0x40, when used with a TEXMAP, TEX2MAP, or SPECMAP chunk must be accompanied with a tint bit,
        either 0x100 or 0x200, tintcolor will be processed if a tintflag was created."""

        mapflags = 0
        if texslot.extension == 'EXTEND':
            mapflags |= 0x1
        if texslot.extension == 'MIRROR':
            mapflags |= 0x2
        if texslot.extension == 'CLIP':
            mapflags |= 0x10

        if socket == 'Alpha':
            mapflags |= 0x40
            if texslot.socket_dst.identifier in {'Base Color', 'Specular'}:
                mapflags |= 0x80 if image.colorspace_settings.name == 'Non-Color' else 0x200

        mat_sub_mapflags.add_variable("mapflags", _3ds_ushort(mapflags))
        mat_sub.add_subchunk(mat_sub_mapflags)

        mat_sub_texblur = _3ds_chunk(MAT_MAP_TEXBLUR)  # Based on observation this is usually 1.0
        mat_sub_texblur.add_variable("maptexblur", _3ds_float(1.0))
        mat_sub.add_subchunk(mat_sub_texblur)

        mat_sub_uscale = _3ds_chunk(MAT_MAP_USCALE)
        mat_sub_uscale.add_variable("mapuscale", _3ds_float(round(texslot.scale[0], 6)))
        mat_sub.add_subchunk(mat_sub_uscale)

        mat_sub_vscale = _3ds_chunk(MAT_MAP_VSCALE)
        mat_sub_vscale.add_variable("mapvscale", _3ds_float(round(texslot.scale[1], 6)))
        mat_sub.add_subchunk(mat_sub_vscale)

        mat_sub_uoffset = _3ds_chunk(MAT_MAP_UOFFSET)
        mat_sub_uoffset.add_variable("mapuoffset", _3ds_float(round(texslot.translation[0], 6)))
        mat_sub.add_subchunk(mat_sub_uoffset)

        mat_sub_voffset = _3ds_chunk(MAT_MAP_VOFFSET)
        mat_sub_voffset.add_variable("mapvoffset", _3ds_float(round(texslot.translation[1], 6)))
        mat_sub.add_subchunk(mat_sub_voffset)

        mat_sub_angle = _3ds_chunk(MAT_MAP_ANG)
        mat_sub_angle.add_variable("mapangle", _3ds_float(round(texslot.rotation[2], 6)))
        mat_sub.add_subchunk(mat_sub_angle)

        if texslot.socket_dst.identifier in {'Base Color', 'Specular'}:
            rgb = _3ds_chunk(MAP_COL1)  # Add tint color
            base = texslot.owner_shader.material.diffuse_color[:3]
            spec = texslot.owner_shader.material.specular_color[:]
            rgb.add_variable("mapcolor", _3ds_rgb_color(spec if texslot.socket_dst.identifier == 'Specular' else base))
            mat_sub.add_subchunk(rgb)

    # Store all textures for this mapto in order. This at least is what the
    # 3DS exporter did so far, afaik most readers will just skip over 2nd textures
    for slot in texslots:
        if slot.image is not None:
            add_texslot(slot)
            has_entry = True

    return mat_sub if has_entry else None


def make_material_chunk(material, image):
    """Make a material chunk out of a blender material.
    Shading method is required for 3ds max, 0 for wireframe.
    0x1 for flat, 0x2 for gouraud, 0x3 for phong and 0x4 for metal."""

    material_chunk = _3ds_chunk(MATERIAL)
    name = _3ds_chunk(MATNAME)
    shading = _3ds_chunk(MATSHADING)

    name_str = material.name if material else "None"

    # if image:
    #     name_str += image.name

    name.add_variable("name", _3ds_string(sane_name(name_str)))
    material_chunk.add_subchunk(name)

    if not material:
        shading.add_variable("shading", _3ds_ushort(1))  # Flat shading
        material_chunk.add_subchunk(make_material_subchunk(MATAMBIENT, (0.0, 0.0, 0.0)))
        material_chunk.add_subchunk(make_material_subchunk(MATDIFFUSE, (0.8, 0.8, 0.8)))
        material_chunk.add_subchunk(make_material_subchunk(MATSPECULAR, (1.0, 1.0, 1.0)))
        material_chunk.add_subchunk(make_percent_subchunk(MATSHINESS, 0.8))
        material_chunk.add_subchunk(make_percent_subchunk(MATSHIN2, 0.5))
        material_chunk.add_subchunk(shading)

    elif material and material.use_nodes:
        wrap = node_shader_utils.PrincipledBSDFWrapper(material)
        shading.add_variable("shading", _3ds_ushort(3))  # Phong shading
        material_chunk.add_subchunk(make_material_subchunk(MATAMBIENT, wrap.emission_color[:3]))
        material_chunk.add_subchunk(make_material_subchunk(MATDIFFUSE, wrap.base_color[:3]))
        material_chunk.add_subchunk(make_material_subchunk(MATSPECULAR, material.specular_color[:]))
        material_chunk.add_subchunk(make_percent_subchunk(MATSHINESS, 1 - wrap.roughness))
        material_chunk.add_subchunk(make_percent_subchunk(MATSHIN2, wrap.specular))
        material_chunk.add_subchunk(make_percent_subchunk(MATSHIN3, wrap.metallic))
        material_chunk.add_subchunk(make_percent_subchunk(MATTRANS, 1 - wrap.alpha))
        material_chunk.add_subchunk(make_percent_subchunk(MATSELFILPCT, wrap.emission_strength))
        material_chunk.add_subchunk(shading)

        primary_tex = False
        mtype = 'MIX', 'MIX_RGB'
        mtlks = material.node_tree.links
        mxtex = [lk.from_node for lk in mtlks if lk.from_node.type == 'TEX_IMAGE' and lk.to_node.type in mtype]
        mxpct = next((lk.from_node.inputs[0].default_value for lk in mtlks if lk.from_node.type in mtype and lk.to_node.type == 'BSDF_PRINCIPLED'), 0.5)

        if wrap.base_color_texture:
            color = [wrap.base_color_texture]
            c_pct = 0.7 + sum(wrap.base_color[:]) * 0.1
            matmap = make_material_texture_chunk(MAT_DIFFUSEMAP, color, c_pct)
            if matmap:
                material_chunk.add_subchunk(matmap)
                primary_tex = True

        if mxtex and not primary_tex:
            material_chunk.add_subchunk(make_texture_chunk(MAT_DIFFUSEMAP, mxtex, mxpct))
            primary_tex = True

        if wrap.specular_texture:
            spec = [wrap.specular_texture]
            s_pct = material.specular_intensity
            matmap = make_material_texture_chunk(MAT_SPECMAP, spec, s_pct)
            if matmap:
                material_chunk.add_subchunk(matmap)

        if wrap.alpha_texture:
            alpha = [wrap.alpha_texture]
            a_pct = material.diffuse_color[3]
            matmap = make_material_texture_chunk(MAT_OPACMAP, alpha, a_pct)
            if matmap:
                material_chunk.add_subchunk(matmap)

        if wrap.metallic_texture:
            metallic = [wrap.metallic_texture]
            m_pct = material.metallic
            matmap = make_material_texture_chunk(MAT_REFLMAP, metallic, m_pct)
            if matmap:
                material_chunk.add_subchunk(matmap)

        if wrap.normalmap_texture:
            normal = [wrap.normalmap_texture]
            b_pct = wrap.normalmap_strength
            matmap = make_material_texture_chunk(MAT_BUMPMAP, normal, b_pct)
            if matmap:
                material_chunk.add_subchunk(matmap)
                material_chunk.add_subchunk(make_percent_subchunk(MAT_BUMP_PERCENT, b_pct))

        if wrap.roughness_texture:
            roughness = [wrap.roughness_texture]
            r_pct = 1 - material.roughness
            matmap = make_material_texture_chunk(MAT_SHINMAP, roughness, r_pct)
            if matmap:
                material_chunk.add_subchunk(matmap)

        if wrap.emission_color_texture:
            emission = [wrap.emission_color_texture]
            e_pct = wrap.emission_strength
            matmap = make_material_texture_chunk(MAT_SELFIMAP, emission, e_pct)
            if matmap:
                material_chunk.add_subchunk(matmap)

        # Make sure no textures are lost. Everything that doesn't fit
        # into a channel is exported as secondary texture
        for link in mtlks:
            mxsecondary = link.from_node if link.from_node.type == 'TEX_IMAGE' and link.to_socket.identifier in {'Color1', 'A_Color'} else False
            if mxsecondary:
                matmap = make_texture_chunk(MAT_TEX2MAP, [mxsecondary], 1 - mxpct)
        if primary_tex and matmap:
            material_chunk.add_subchunk(matmap)

    else:
        shading.add_variable("shading", _3ds_ushort(2))  # Gouraud shading
        material_chunk.add_subchunk(make_material_subchunk(MATAMBIENT, material.line_color[:3]))
        material_chunk.add_subchunk(make_material_subchunk(MATDIFFUSE, material.diffuse_color[:3]))
        material_chunk.add_subchunk(make_material_subchunk(MATSPECULAR, material.specular_color[:]))
        material_chunk.add_subchunk(make_percent_subchunk(MATSHINESS, 1 - material.roughness))
        material_chunk.add_subchunk(make_percent_subchunk(MATSHIN2, material.specular_intensity))
        material_chunk.add_subchunk(make_percent_subchunk(MATSHIN3, material.metallic))
        material_chunk.add_subchunk(make_percent_subchunk(MATTRANS, 1 - material.diffuse_color[3]))
        material_chunk.add_subchunk(shading)

        slots = [get_material_image(material)]  # Can be None

        if image:
            material_chunk.add_subchunk(make_texture_chunk(MAT_DIFFUSEMAP, slots))

    return material_chunk


#############
# MESH DATA #
#############

class tri_wrapper(object):
    """Class representing a triangle.
    Used when converting faces to triangles"""

    __slots__ = "vertex_index", "ma", "image", "faceuvs", "offset", "flag", "group"

    def __init__(self, vindex=(0, 0, 0), ma=None, image=None, faceuvs=None, flag=0, group=0):
        self.vertex_index = vindex
        self.ma = ma
        self.image = image
        self.faceuvs = faceuvs
        self.offset = [0, 0, 0]  # Offset indices
        self.flag = flag
        self.group = group


def extract_triangles(mesh):
    """Extract triangles from a mesh."""

    mesh.calc_loop_triangles()
    (polygroup, count) = mesh.calc_smooth_groups(use_bitflags=True)

    tri_list = []
    do_uv = bool(mesh.uv_layers)

    img = None
    for i, face in enumerate(mesh.loop_triangles):
        f_v = face.vertices
        v1, v2, v3 = f_v
        uf = mesh.uv_layers.active.data if do_uv else None

        if do_uv:
            f_uv = [uf[lp].uv for lp in face.loops]
            for ma in mesh.materials:
                img = get_uv_image(ma) if uf else None
                if img is not None:
                    img = img.name
            uv1, uv2, uv3 = f_uv

        """Flag 0x1 sets CA edge visible, Flag 0x2 sets BC edge visible, Flag 0x4 sets AB edge visible
        Flag 0x8 indicates a U axis texture wrap seam and Flag 0x10 indicates a V axis texture wrap seam
        In Blender we use the edge CA, BC, and AB flags for sharp edges flags."""
        a_b = mesh.edges[mesh.loops[face.loops[0]].edge_index]
        b_c = mesh.edges[mesh.loops[face.loops[1]].edge_index]
        c_a = mesh.edges[mesh.loops[face.loops[2]].edge_index]

        if v3 == 0:
            v1, v2, v3 = v3, v1, v2
            a_b, b_c, c_a = c_a, a_b, b_c
            if do_uv:
                uv1, uv2, uv3 = uv3, uv1, uv2

        faceflag = 0
        if c_a.use_edge_sharp:
            faceflag |= 0x1
        if b_c.use_edge_sharp:
            faceflag |= 0x2
        if a_b.use_edge_sharp:
            faceflag |= 0x4

        smoothgroup = polygroup[face.polygon_index]

        if len(f_v) == 3:
            new_tri = tri_wrapper((v1, v2, v3), face.material_index, img)
            if (do_uv):
                new_tri.faceuvs = uv_key(uv1), uv_key(uv2), uv_key(uv3)
            new_tri.flag = faceflag
            new_tri.group = smoothgroup if face.use_smooth else 0
            tri_list.append(new_tri)

    return tri_list


def remove_face_uv(verts, tri_list):
    """Remove face UV coordinates from a list of triangles.
    Since 3ds files only support one pair of uv coordinates for each vertex, face uv coordinates
    need to be converted to vertex uv coordinates. That means that vertices need to be duplicated when
    there are multiple uv coordinates per vertex."""

    # Initialize a list of UniqueUVs, one per vertex
    unique_uvs = [{} for i in range(len(verts))]

    # For each face uv coordinate, add it to the UniqueList of the vertex
    for tri in tri_list:
        for i in range(3):
            # Store the index into the UniqueList for future reference
            # offset.append(uv_list[tri.vertex_index[i]].add(_3ds_point_uv(tri.faceuvs[i])))

            context_uv_vert = unique_uvs[tri.vertex_index[i]]
            uvkey = tri.faceuvs[i]
            offset_index__uv_3ds = context_uv_vert.get(uvkey)

            if not offset_index__uv_3ds:
                offset_index__uv_3ds = context_uv_vert[uvkey] = len(context_uv_vert), _3ds_point_uv(uvkey)

            tri.offset[i] = offset_index__uv_3ds[0]

    # At this point each vertex has a UniqueList containing every uv coord associated with it only once
    # Now we need to duplicate every vertex as many times as it has uv coordinates and make sure the
    # faces refer to the new face indices
    vert_index = 0
    vert_array = _3ds_array()
    uv_array = _3ds_array()
    index_list = []
    for i, vert in enumerate(verts):
        index_list.append(vert_index)

        pt = _3ds_point_3d(vert.co)  # reuse, should be ok
        uvmap = [None] * len(unique_uvs[i])
        for ii, uv_3ds in unique_uvs[i].values():
            # Add a vertex duplicate to the vertex_array for every uv associated with this vertex
            vert_array.add(pt)
            # Add the uv coordinate to the uv array, this for loop does not give
            # uv's ordered by ii, so we create a new map and add the uv's later
            uvmap[ii] = uv_3ds

        # Add uv's in the correct order and add coordinates to the uv array
        for uv_3ds in uvmap:
            uv_array.add(uv_3ds)

        vert_index += len(unique_uvs[i])

    # Make sure the triangle vertex indices now refer to the new vertex list
    for tri in tri_list:
        for i in range(3):
            tri.offset[i] += index_list[tri.vertex_index[i]]
        tri.vertex_index = tri.offset

    return vert_array, uv_array, tri_list


def make_faces_chunk(tri_list, mesh, materialDict):
    """Make a chunk for the faces.
    Also adds subchunks assigning materials to all faces."""
    do_smooth = False
    use_smooth = [poly.use_smooth for poly in mesh.polygons]
    if True in use_smooth:
        do_smooth = True

    materials = mesh.materials
    if not materials:
        ma = None

    face_chunk = _3ds_chunk(OBJECT_FACES)
    face_list = _3ds_array()

    if mesh.uv_layers:
        # Gather materials used in this mesh - mat/image pairs
        unique_mats = {}
        for i, tri in enumerate(tri_list):
            face_list.add(_3ds_face(tri.vertex_index, tri.flag))

            if materials:
                ma = materials[tri.ma]
                if ma:
                    ma = ma.name

            img = tri.image

            try:
                context_face_array = unique_mats[ma, img][1]
            except:
                name_str = ma if ma else "None"
                # if img:
                #     name_str += img

                context_face_array = _3ds_array()
                unique_mats[ma, img] = _3ds_string(sane_name(name_str)), context_face_array

            context_face_array.add(_3ds_ushort(i))

        face_chunk.add_variable("faces", face_list)
        for ma_name, ma_faces in unique_mats.values():
            obj_material_chunk = _3ds_chunk(OBJECT_MATERIAL)
            obj_material_chunk.add_variable("name", ma_name)
            obj_material_chunk.add_variable("face_list", ma_faces)
            face_chunk.add_subchunk(obj_material_chunk)

    else:
        obj_material_faces = []
        obj_material_names = []
        for m in materials:
            if m:
                obj_material_names.append(_3ds_string(sane_name(m.name)))
                obj_material_faces.append(_3ds_array())
        n_materials = len(obj_material_names)

        for i, tri in enumerate(tri_list):
            face_list.add(_3ds_face(tri.vertex_index, tri.flag))
            if (tri.ma < n_materials):
                obj_material_faces[tri.ma].add(_3ds_ushort(i))

        face_chunk.add_variable("faces", face_list)
        for i in range(n_materials):
            obj_material_chunk = _3ds_chunk(OBJECT_MATERIAL)
            obj_material_chunk.add_variable("name", obj_material_names[i])
            obj_material_chunk.add_variable("face_list", obj_material_faces[i])
            face_chunk.add_subchunk(obj_material_chunk)

    if do_smooth:
        obj_smooth_chunk = _3ds_chunk(OBJECT_SMOOTH)
        for i, tri in enumerate(tri_list):
            obj_smooth_chunk.add_variable("face_" + str(i), _3ds_uint(tri.group))
        face_chunk.add_subchunk(obj_smooth_chunk)

    return face_chunk


def make_vert_chunk(vert_array):
    """Make a vertex chunk out of an array of vertices."""
    vert_chunk = _3ds_chunk(OBJECT_VERTICES)
    vert_chunk.add_variable("vertices", vert_array)
    return vert_chunk


def make_uv_chunk(uv_array):
    """Make a UV chunk out of an array of UVs."""
    uv_chunk = _3ds_chunk(OBJECT_UV)
    uv_chunk.add_variable("uv coords", uv_array)
    return uv_chunk


def make_mesh_chunk(ob, mesh, matrix, materialDict, translation):
    """Make a chunk out of a Blender mesh."""

    # Extract the triangles from the mesh
    tri_list = extract_triangles(mesh)

    if mesh.uv_layers:
        # Remove the face UVs and convert it to vertex UV
        vert_array, uv_array, tri_list = remove_face_uv(mesh.vertices, tri_list)
    else:
        # Add the vertices to the vertex array
        vert_array = _3ds_array()
        for vert in mesh.vertices:
            vert_array.add(_3ds_point_3d(vert.co))
        # No UV at all
        uv_array = None

    # Create the chunk
    mesh_chunk = _3ds_chunk(OBJECT_MESH)

    # Add vertex and faces chunk
    mesh_chunk.add_subchunk(make_vert_chunk(vert_array))
    mesh_chunk.add_subchunk(make_faces_chunk(tri_list, mesh, materialDict))

    # If available, add uv chunk
    if uv_array:
        mesh_chunk.add_subchunk(make_uv_chunk(uv_array))

    # Create transformation matrix chunk
    matrix_chunk = _3ds_chunk(OBJECT_TRANS_MATRIX)
    obj_matrix = matrix.transposed().to_3x3()

    if ob.parent is None or (ob.parent.name not in translation):
        obj_translate = matrix.to_translation()

    else:  # Calculate child matrix translation relative to parent
        obj_translate = translation[ob.name].cross(-1 * translation[ob.parent.name])

    matrix_chunk.add_variable("xx", _3ds_float(obj_matrix[0].to_tuple(6)[0]))
    matrix_chunk.add_variable("xy", _3ds_float(obj_matrix[0].to_tuple(6)[1]))
    matrix_chunk.add_variable("xz", _3ds_float(obj_matrix[0].to_tuple(6)[2]))
    matrix_chunk.add_variable("yx", _3ds_float(obj_matrix[1].to_tuple(6)[0]))
    matrix_chunk.add_variable("yy", _3ds_float(obj_matrix[1].to_tuple(6)[1]))
    matrix_chunk.add_variable("yz", _3ds_float(obj_matrix[1].to_tuple(6)[2]))
    matrix_chunk.add_variable("zx", _3ds_float(obj_matrix[2].to_tuple(6)[0]))
    matrix_chunk.add_variable("zy", _3ds_float(obj_matrix[2].to_tuple(6)[1]))
    matrix_chunk.add_variable("zz", _3ds_float(obj_matrix[2].to_tuple(6)[2]))
    matrix_chunk.add_variable("tx", _3ds_float(obj_translate.to_tuple(6)[0]))
    matrix_chunk.add_variable("ty", _3ds_float(obj_translate.to_tuple(6)[1]))
    matrix_chunk.add_variable("tz", _3ds_float(obj_translate.to_tuple(6)[2]))

    mesh_chunk.add_subchunk(matrix_chunk)

    return mesh_chunk


def calc_target(posi, tilt=0.0, pan=0.0):
    """Calculate target position for cameras and spotlights."""
    adjacent = math.radians(90)
    turn = 0.0 if abs(pan) < adjacent else -0.0
    lean = 0.0 if abs(tilt) > adjacent else -0.0
    diagonal = math.sqrt(pow(posi.x ,2) + pow(posi.y ,2))
    target_x = math.copysign(posi.x + (posi.y * math.tan(pan)), pan)
    target_y = math.copysign(posi.y + (posi.x * math.tan(adjacent - pan)), turn)
    target_z = math.copysign(posi.z + diagonal * math.tan(adjacent - tilt), lean)

    return target_x, target_y, target_z


#################
# KEYFRAME DATA #
#################

def make_kfdata(revision, start=0, stop=100, curtime=0):
    """Make the basic keyframe data chunk."""
    kfdata = _3ds_chunk(KFDATA)

    kfhdr = _3ds_chunk(KFDATA_KFHDR)
    kfhdr.add_variable("revision", _3ds_ushort(revision))
    kfhdr.add_variable("filename", _3ds_string(b'Blender'))
    kfhdr.add_variable("animlen", _3ds_uint(stop - start))

    kfseg = _3ds_chunk(KFDATA_KFSEG)
    kfseg.add_variable("start", _3ds_uint(start))
    kfseg.add_variable("stop", _3ds_uint(stop))

    kfcurtime = _3ds_chunk(KFDATA_KFCURTIME)
    kfcurtime.add_variable("curtime", _3ds_uint(curtime))

    kfdata.add_subchunk(kfhdr)
    kfdata.add_subchunk(kfseg)
    kfdata.add_subchunk(kfcurtime)
    return kfdata


def make_track_chunk(ID, ob, ob_pos, ob_rot, ob_size):
    """Make a chunk for track data. Depending on the ID, this will construct
    a position, rotation, scale, roll, color, fov, hotspot or falloff track."""
    track_chunk = _3ds_chunk(ID)

    if ID in {POS_TRACK_TAG, ROT_TRACK_TAG, SCL_TRACK_TAG, ROLL_TRACK_TAG} and ob.animation_data and ob.animation_data.action:
        action = ob.animation_data.action
        if action.fcurves:
            fcurves = action.fcurves
            fcurves.update()
            kframes = [kf.co[0] for kf in [fc for fc in fcurves if fc is not None][0].keyframe_points]
            nkeys = len(kframes)
            if not 0 in kframes:
                kframes.append(0)
                nkeys += 1
            kframes = sorted(set(kframes))
            track_chunk.add_variable("track_flags", _3ds_ushort(0x40))
            track_chunk.add_variable("frame_start", _3ds_uint(int(action.frame_start)))
            track_chunk.add_variable("frame_total", _3ds_uint(int(action.frame_end)))
            track_chunk.add_variable("nkeys", _3ds_uint(nkeys))

            if ID == POS_TRACK_TAG:  # Position
                for i, frame in enumerate(kframes):
                    pos_track = [fc for fc in fcurves if fc is not None and fc.data_path == 'location']
                    pos_x = next((tc.evaluate(frame) for tc in pos_track if tc.array_index == 0), ob_pos.x)
                    pos_y = next((tc.evaluate(frame) for tc in pos_track if tc.array_index == 1), ob_pos.y)
                    pos_z = next((tc.evaluate(frame) for tc in pos_track if tc.array_index == 2), ob_pos.z)
                    pos = ob_size @ mathutils.Vector((pos_x, pos_y, pos_z))
                    track_chunk.add_variable("tcb_frame", _3ds_uint(int(frame)))
                    track_chunk.add_variable("tcb_flags", _3ds_ushort())
                    track_chunk.add_variable("position", _3ds_point_3d((pos.x, pos.y, pos.z)))

            elif ID == ROT_TRACK_TAG:  # Rotation
                for i, frame in enumerate(kframes):
                    rot_track = [fc for fc in fcurves if fc is not None and fc.data_path == 'rotation_euler']
                    rot_x = next((tc.evaluate(frame) for tc in rot_track if tc.array_index == 0), ob_rot.x)
                    rot_y = next((tc.evaluate(frame) for tc in rot_track if tc.array_index == 1), ob_rot.y)
                    rot_z = next((tc.evaluate(frame) for tc in rot_track if tc.array_index == 2), ob_rot.z)
                    quat = mathutils.Euler((rot_x, rot_y, rot_z)).to_quaternion().inverted()
                    track_chunk.add_variable("tcb_frame", _3ds_uint(int(frame)))
                    track_chunk.add_variable("tcb_flags", _3ds_ushort())
                    track_chunk.add_variable("rotation", _3ds_point_4d((quat.angle, quat.axis.x, quat.axis.y, quat.axis.z)))

            elif ID == SCL_TRACK_TAG:  # Scale
                for i, frame in enumerate(kframes):
                    scale_track = [fc for fc in fcurves if fc is not None and fc.data_path == 'scale']
                    size_x = next((tc.evaluate(frame) for tc in scale_track if tc.array_index == 0), ob_size.x)
                    size_y = next((tc.evaluate(frame) for tc in scale_track if tc.array_index == 1), ob_size.y)
                    size_z = next((tc.evaluate(frame) for tc in scale_track if tc.array_index == 2), ob_size.z)
                    track_chunk.add_variable("tcb_frame", _3ds_uint(int(frame)))
                    track_chunk.add_variable("tcb_flags", _3ds_ushort())
                    track_chunk.add_variable("scale", _3ds_point_3d((size_x, size_y, size_z)))

            elif ID == ROLL_TRACK_TAG:  # Roll
                for i, frame in enumerate(kframes):
                    roll_track = [fc for fc in fcurves if fc is not None and fc.data_path == 'rotation_euler']
                    roll = next((tc.evaluate(frame) for tc in roll_track if tc.array_index == 1), ob_rot.y)
                    track_chunk.add_variable("tcb_frame", _3ds_uint(int(frame)))
                    track_chunk.add_variable("tcb_flags", _3ds_ushort())
                    track_chunk.add_variable("roll", _3ds_float(round(math.degrees(roll), 4)))

    elif ID in {COL_TRACK_TAG, FOV_TRACK_TAG, HOTSPOT_TRACK_TAG, FALLOFF_TRACK_TAG} and ob.data.animation_data and ob.data.animation_data.action:
        action = ob.data.animation_data.action
        if action.fcurves:
            fcurves = action.fcurves
            fcurves.update()
            kframes = [kf.co[0] for kf in [fc for fc in fcurves if fc is not None][0].keyframe_points]
            nkeys = len(kframes)
            if not 0 in kframes:
                kframes.append(0)
                nkeys += 1
            kframes = sorted(set(kframes))
            track_chunk.add_variable("track_flags", _3ds_ushort(0x40))
            track_chunk.add_variable("frame_start", _3ds_uint(int(action.frame_start)))
            track_chunk.add_variable("frame_total", _3ds_uint(int(action.frame_end)))
            track_chunk.add_variable("nkeys", _3ds_uint(nkeys))

            if ID == COL_TRACK_TAG:  # Color
                for i, frame in enumerate(kframes):
                    color = [fc.evaluate(frame) for fc in fcurves if fc is not None and fc.data_path == 'color']
                    if not color:
                        color = ob.data.color[:3]
                    track_chunk.add_variable("tcb_frame", _3ds_uint(int(frame)))
                    track_chunk.add_variable("tcb_flags", _3ds_ushort())
                    track_chunk.add_variable("color", _3ds_float_color(color))

            elif ID == FOV_TRACK_TAG:  # Field of view
                for i, frame in enumerate(kframes):
                    lens = next((fc.evaluate(frame) for fc in fcurves if fc is not None and fc.data_path == 'lens'), ob.data.lens)
                    fov = 2 * math.atan(ob.data.sensor_width / (2 * lens))
                    track_chunk.add_variable("tcb_frame", _3ds_uint(int(frame)))
                    track_chunk.add_variable("tcb_flags", _3ds_ushort())
                    track_chunk.add_variable("fov", _3ds_float(round(math.degrees(fov), 4)))

            elif ID == HOTSPOT_TRACK_TAG:  # Hotspot
                beam_angle = math.degrees(ob.data.spot_size)
                for i, frame in enumerate(kframes):
                    blend = next((fc.evaluate(frame) for fc in fcurves if fc is not None and fc.data_path == 'spot_blend'), ob.data.spot_blend)
                    hot_spot = beam_angle - (blend * math.floor(beam_angle))
                    track_chunk.add_variable("tcb_frame", _3ds_uint(int(frame)))
                    track_chunk.add_variable("tcb_flags", _3ds_ushort())
                    track_chunk.add_variable("hotspot", _3ds_float(round(hot_spot, 4)))

            elif ID == FALLOFF_TRACK_TAG:  # Falloff
                for i, frame in enumerate(kframes):
                    fall_off = next((fc.evaluate(frame) for fc in fcurves if fc is not None and fc.data_path == 'spot_size'), ob.data.spot_size)
                    track_chunk.add_variable("tcb_frame", _3ds_uint(int(frame)))
                    track_chunk.add_variable("tcb_flags", _3ds_ushort())
                    track_chunk.add_variable("falloff", _3ds_float(round(math.degrees(fall_off), 4)))

    else:
        track_chunk.add_variable("track_flags", _3ds_ushort(0x40))  # Based on observation default flag is 0x40
        track_chunk.add_variable("frame_start", _3ds_uint(0))
        track_chunk.add_variable("frame_total", _3ds_uint(0))
        track_chunk.add_variable("nkeys", _3ds_uint(1))
        # Next section should be repeated for every keyframe, with no animation only one tag is needed
        track_chunk.add_variable("tcb_frame", _3ds_uint(0))
        track_chunk.add_variable("tcb_flags", _3ds_ushort())

        # New method simply inserts the parameters
        if ID == POS_TRACK_TAG:  # Position vector
            track_chunk.add_variable("position", _3ds_point_3d(ob_pos))

        elif ID == ROT_TRACK_TAG:  # Rotation (angle first [radians], followed by axis)
            quat = ob_rot.to_quaternion().inverted()
            track_chunk.add_variable("rotation", _3ds_point_4d((quat.angle, quat.axis.x, quat.axis.y, quat.axis.z)))

        elif ID == SCL_TRACK_TAG:  # Scale vector
            track_chunk.add_variable("scale", _3ds_point_3d(ob_size))

        elif ID == ROLL_TRACK_TAG:  # Roll angle
            track_chunk.add_variable("roll", _3ds_float(round(math.degrees(ob_rot.y), 4)))

        elif ID == COL_TRACK_TAG:  # Color values
            track_chunk.add_variable("color", _3ds_float_color(ob.data.color[:3]))

        elif ID == FOV_TRACK_TAG:  # Field of view
            track_chunk.add_variable("fov", _3ds_float(round(math.degrees(ob.data.angle), 4)))

        elif ID == HOTSPOT_TRACK_TAG:  # Hotspot
            beam_angle = math.degrees(ob.data.spot_size)
            track_chunk.add_variable("hotspot", _3ds_float(round(beam_angle - (ob.data.spot_blend * math.floor(beam_angle)), 4)))

        elif ID == FALLOFF_TRACK_TAG:  # Falloff
            track_chunk.add_variable("falloff", _3ds_float(round(math.degrees(ob.data.spot_size), 4)))

    return track_chunk


def make_object_node(ob, translation, rotation, scale, name_id):
    """Make a node chunk for a Blender object. Takes Blender object as parameter.
       Blender Empty objects are converted to dummy nodes."""

    name = ob.name
    if ob.type == 'CAMERA':
        obj_node = _3ds_chunk(CAMERA_NODE_TAG)
    elif ob.type == 'LIGHT':
        obj_node = _3ds_chunk(LIGHT_NODE_TAG)
        if ob.data.type == 'SPOT':
            obj_node = _3ds_chunk(SPOT_NODE_TAG)
    else:  # Main object node chunk
        obj_node = _3ds_chunk(OBJECT_NODE_TAG)

    # Chunk for the object ID from name_id dictionary:
    obj_id_chunk = _3ds_chunk(OBJECT_NODE_ID)
    obj_id_chunk.add_variable("node_id", _3ds_ushort(name_id[name]))
    obj_node.add_subchunk(obj_id_chunk)

    # Object node header with object name
    obj_node_header_chunk = _3ds_chunk(OBJECT_NODE_HDR)
    parent = ob.parent

    if ob.type == 'EMPTY':  # Forcing to use the real name for empties
        # Empties called $$$DUMMY and use OBJECT_INSTANCE_NAME chunk as name
        obj_node_header_chunk.add_variable("name", _3ds_string(b"$$$DUMMY"))
        obj_node_header_chunk.add_variable("flags1", _3ds_ushort(0x4000))
        obj_node_header_chunk.add_variable("flags2", _3ds_ushort(0))

    else:  # Add flag variables - Based on observation flags1 is usually 0x0040 and 0x4000 for empty objects
        obj_node_header_chunk.add_variable("name", _3ds_string(sane_name(name)))
        obj_node_header_chunk.add_variable("flags1", _3ds_ushort(0x0040))

        """Flags2 defines 0x01 for display path, 0x02 use autosmooth, 0x04 object frozen,
        0x10 for motion blur, 0x20 for material morph and bit 0x40 for mesh morph."""
        if ob.type == 'MESH' and ob.data.use_auto_smooth:
            obj_node_header_chunk.add_variable("flags2", _3ds_ushort(0x02))
        else:
            obj_node_header_chunk.add_variable("flags2", _3ds_ushort(0))
    obj_node_header_chunk.add_variable("parent", _3ds_ushort(ROOT_OBJECT))

    '''
    # COMMENTED OUT FOR 2.42 RELEASE!! CRASHES 3DS MAX
    # Check parent-child relationships:
    if parent is None or parent.name not in name_id:
        # If no parent, or parents name is not in dictionary, ID becomes -1:
        obj_node_header_chunk.add_variable("parent", _3ds_ushort(-1))
    else:  # Get the parent's ID from the name_id dictionary:
        obj_node_header_chunk.add_variable("parent", _3ds_ushort(name_id[parent.name]))
    '''

    # Add subchunk for node header
    obj_node.add_subchunk(obj_node_header_chunk)

    # Alternatively use PARENT_NAME chunk for hierachy
    if parent is not None and (parent.name in name_id):
        obj_parent_name_chunk = _3ds_chunk(OBJECT_PARENT_NAME)
        obj_parent_name_chunk.add_variable("parent", _3ds_string(sane_name(parent.name)))
        obj_node.add_subchunk(obj_parent_name_chunk)

    # Empty objects need to have an extra chunk for the instance name
    if ob.type == 'EMPTY':  # Will use a real object name for empties for now
        obj_instance_name_chunk = _3ds_chunk(OBJECT_INSTANCE_NAME)
        obj_instance_name_chunk.add_variable("name", _3ds_string(sane_name(name)))
        obj_node.add_subchunk(obj_instance_name_chunk)

    if ob.type in {'MESH', 'EMPTY'}:  # Add a pivot point at the object center
        pivot_pos = (translation[name])
        obj_pivot_chunk = _3ds_chunk(OBJECT_PIVOT)
        obj_pivot_chunk.add_variable("pivot", _3ds_point_3d(pivot_pos))
        obj_node.add_subchunk(obj_pivot_chunk)

        # Create a bounding box from quadrant diagonal
        obj_boundbox = _3ds_chunk(OBJECT_BOUNDBOX)
        obj_boundbox.add_variable("min", _3ds_point_3d(ob.bound_box[0]))
        obj_boundbox.add_variable("max", _3ds_point_3d(ob.bound_box[6]))
        obj_node.add_subchunk(obj_boundbox)

        # Add smooth angle if autosmooth is used
        if ob.type == 'MESH' and ob.data.use_auto_smooth:
            obj_morph_smooth = _3ds_chunk(OBJECT_MORPH_SMOOTH)
            obj_morph_smooth.add_variable("angle", _3ds_float(round(ob.data.auto_smooth_angle, 6)))
            obj_node.add_subchunk(obj_morph_smooth)

    # Add track chunks for position, rotation, size
    ob_scale = scale[name]  # and collect masterscale
    if parent is None or (parent.name not in name_id):
        ob_pos = translation[name]
        ob_rot = rotation[name]
        ob_size = ob.scale

    else:  # Calculate child position and rotation of the object center, no scale applied
        ob_pos = translation[name] - translation[parent.name]
        ob_rot = rotation[name].to_quaternion().cross(rotation[parent.name].to_quaternion().copy().inverted()).to_euler()
        ob_size = mathutils.Vector((1.0, 1.0, 1.0))

    obj_node.add_subchunk(make_track_chunk(POS_TRACK_TAG, ob, ob_pos, ob_rot, ob_scale))

    if ob.type in {'MESH', 'EMPTY'}:
        obj_node.add_subchunk(make_track_chunk(ROT_TRACK_TAG, ob, ob_pos, ob_rot, ob_size))
        obj_node.add_subchunk(make_track_chunk(SCL_TRACK_TAG, ob, ob_pos, ob_rot, ob_size))
    if ob.type =='CAMERA':
        obj_node.add_subchunk(make_track_chunk(FOV_TRACK_TAG, ob, ob_pos, ob_rot, ob_size))
        obj_node.add_subchunk(make_track_chunk(ROLL_TRACK_TAG, ob, ob_pos, ob_rot, ob_size))
    if ob.type =='LIGHT':
        obj_node.add_subchunk(make_track_chunk(COL_TRACK_TAG, ob, ob_pos, ob_rot, ob_size))
    if ob.type == 'LIGHT' and ob.data.type == 'SPOT':
        obj_node.add_subchunk(make_track_chunk(HOTSPOT_TRACK_TAG, ob, ob_pos, ob_rot, ob_size))
        obj_node.add_subchunk(make_track_chunk(FALLOFF_TRACK_TAG, ob, ob_pos, ob_rot, ob_size))
        obj_node.add_subchunk(make_track_chunk(ROLL_TRACK_TAG, ob, ob_pos, ob_rot, ob_size))

    return obj_node


def make_target_node(ob, translation, rotation, scale, name_id):
    """Make a target chunk for light and camera objects."""

    name = ob.name
    name_id["ø " + name] = len(name_id)
    if ob.type == 'CAMERA':  # Add camera target
        tar_node = _3ds_chunk(TARGET_NODE_TAG)
    elif ob.type == 'LIGHT':  # Add spot target
        tar_node = _3ds_chunk(LTARGET_NODE_TAG)

    # Chunk for the object ID from name_id dictionary:
    tar_id_chunk = _3ds_chunk(OBJECT_NODE_ID)
    tar_id_chunk.add_variable("node_id", _3ds_ushort(name_id[name]))
    tar_node.add_subchunk(tar_id_chunk)

    # Object node header with object name
    tar_node_header_chunk = _3ds_chunk(OBJECT_NODE_HDR)
    # Targets get the same name as the object, flags1 is usually 0x0010 and parent ROOT_OBJECT
    tar_node_header_chunk.add_variable("name", _3ds_string(sane_name(name)))
    tar_node_header_chunk.add_variable("flags1", _3ds_ushort(0x0010))
    tar_node_header_chunk.add_variable("flags2", _3ds_ushort(0))
    tar_node_header_chunk.add_variable("parent", _3ds_ushort(ROOT_OBJECT))

    # Add subchunk for node header
    tar_node.add_subchunk(tar_node_header_chunk)

    # Calculate target position
    ob_pos = translation[name]
    ob_rot = rotation[name]
    ob_scale = scale[name]
    target_pos = calc_target(ob_pos, ob_rot.x, ob_rot.z)

    # Add track chunks for target position
    track_chunk = _3ds_chunk(POS_TRACK_TAG)

    if ob.animation_data and ob.animation_data.action:
        action = ob.animation_data.action
        if action.fcurves:
            fcurves = action.fcurves
            fcurves.update()
            kframes = [kf.co[0] for kf in [fc for fc in fcurves if fc is not None][0].keyframe_points]
            nkeys = len(kframes)
            if not 0 in kframes:
                kframes.append(0)
                nkeys += 1
            kframes = sorted(set(kframes))
            track_chunk.add_variable("track_flags", _3ds_ushort(0x40))
            track_chunk.add_variable("frame_start", _3ds_uint(int(action.frame_start)))
            track_chunk.add_variable("frame_total", _3ds_uint(int(action.frame_end)))
            track_chunk.add_variable("nkeys", _3ds_uint(nkeys))

            for i, frame in enumerate(kframes):
                loc_target = [fc for fc in fcurves if fc is not None and fc.data_path == 'location']
                loc_x = next((tc.evaluate(frame) for tc in loc_target if tc.array_index == 0), ob_pos.x)
                loc_y = next((tc.evaluate(frame) for tc in loc_target if tc.array_index == 1), ob_pos.y)
                loc_z = next((tc.evaluate(frame) for tc in loc_target if tc.array_index == 2), ob_pos.z)
                rot_target = [fc for fc in fcurves if fc is not None and fc.data_path == 'rotation_euler']
                rot_x = next((tc.evaluate(frame) for tc in rot_target if tc.array_index == 0), ob_rot.x)
                rot_z = next((tc.evaluate(frame) for tc in rot_target if tc.array_index == 2), ob_rot.z)
                target_distance = ob_scale @ mathutils.Vector((loc_x, loc_y, loc_z))
                target_pos = calc_target(target_distance, rot_x, rot_z)
                track_chunk.add_variable("tcb_frame", _3ds_uint(int(frame)))
                track_chunk.add_variable("tcb_flags", _3ds_ushort())
                track_chunk.add_variable("position", _3ds_point_3d(target_pos))

    else:  # Track header
        track_chunk.add_variable("track_flags", _3ds_ushort(0x40))  # Based on observation default flag is 0x40
        track_chunk.add_variable("frame_start", _3ds_uint(0))
        track_chunk.add_variable("frame_total", _3ds_uint(0))
        track_chunk.add_variable("nkeys", _3ds_uint(1))
        # Keyframe header
        track_chunk.add_variable("tcb_frame", _3ds_uint(0))
        track_chunk.add_variable("tcb_flags", _3ds_ushort())
        track_chunk.add_variable("position", _3ds_point_3d(target_pos))

    tar_node.add_subchunk(track_chunk)

    return tar_node


def make_ambient_node(world):
    """Make an ambient node for the world color, if the color is animated."""

    amb_color = world.color[:3]
    amb_node = _3ds_chunk(AMBIENT_NODE_TAG)
    track_chunk = _3ds_chunk(COL_TRACK_TAG)

    # Chunk for the ambient ID is ROOT_OBJECT
    amb_id_chunk = _3ds_chunk(OBJECT_NODE_ID)
    amb_id_chunk.add_variable("node_id", _3ds_ushort(ROOT_OBJECT))
    amb_node.add_subchunk(amb_id_chunk)

    # Object node header, name is "$AMBIENT$" for ambient nodes
    amb_node_header_chunk = _3ds_chunk(OBJECT_NODE_HDR)
    amb_node_header_chunk.add_variable("name", _3ds_string(b"$AMBIENT$"))
    amb_node_header_chunk.add_variable("flags1", _3ds_ushort(0x4000))  # Flags1 0x4000 for empty objects
    amb_node_header_chunk.add_variable("flags2", _3ds_ushort(0))
    amb_node_header_chunk.add_variable("parent", _3ds_ushort(ROOT_OBJECT))
    amb_node.add_subchunk(amb_node_header_chunk)

    if world.use_nodes and world.node_tree.animation_data.action:
        ambioutput = 'EMISSION' ,'MIX_SHADER', 'WORLD_OUTPUT'
        action = world.node_tree.animation_data.action
        links = world.node_tree.links
        ambilinks = [lk for lk in links if lk.from_node.type in {'EMISSION', 'RGB'} and lk.to_node.type in ambioutput]
        if ambilinks and action.fcurves:
            fcurves = action.fcurves
            fcurves.update()
            emission = next((lk.from_socket.node for lk in ambilinks if lk.to_node.type in ambioutput), False)
            ambinode = next((lk.from_socket.node for lk in ambilinks if lk.to_node.type == 'EMISSION'), emission)
            kframes = [kf.co[0] for kf in [fc for fc in fcurves if fc is not None][0].keyframe_points]
            ambipath = ('nodes[\"RGB\"].outputs[0].default_value' if ambinode and ambinode.type == 'RGB' else
                        'nodes[\"Emission\"].inputs[0].default_value')
            nkeys = len(kframes)
            if not 0 in kframes:
                kframes.append(0)
                nkeys = nkeys + 1
            kframes = sorted(set(kframes))
            track_chunk.add_variable("track_flags", _3ds_ushort(0x40))
            track_chunk.add_variable("frame_start", _3ds_uint(int(action.frame_start)))
            track_chunk.add_variable("frame_total", _3ds_uint(int(action.frame_end)))
            track_chunk.add_variable("nkeys", _3ds_uint(nkeys))

            for i, frame in enumerate(kframes):
                ambient = [fc.evaluate(frame) for fc in fcurves if fc is not None and fc.data_path == ambipath]
                if not ambient:
                    ambient = amb_color
                track_chunk.add_variable("tcb_frame", _3ds_uint(int(frame)))
                track_chunk.add_variable("tcb_flags", _3ds_ushort())
                track_chunk.add_variable("color", _3ds_float_color(ambient[:3]))

    elif world.animation_data.action:
        action = world.animation_data.action
        if action.fcurves:
            fcurves = action.fcurves
            fcurves.update()
            kframes = [kf.co[0] for kf in [fc for fc in fcurves if fc is not None][0].keyframe_points]
            nkeys = len(kframes)
            if not 0 in kframes:
                kframes.append(0)
                nkeys += 1
            kframes = sorted(set(kframes))
            track_chunk.add_variable("track_flags", _3ds_ushort(0x40))
            track_chunk.add_variable("frame_start", _3ds_uint(int(action.frame_start)))
            track_chunk.add_variable("frame_total", _3ds_uint(int(action.frame_end)))
            track_chunk.add_variable("nkeys", _3ds_uint(nkeys))

            for i, frame in enumerate(kframes):
                ambient = [fc.evaluate(frame) for fc in fcurves if fc is not None and fc.data_path == 'color']
                if not ambient:
                    ambient = amb_color
                track_chunk.add_variable("tcb_frame", _3ds_uint(int(frame)))
                track_chunk.add_variable("tcb_flags", _3ds_ushort())
                track_chunk.add_variable("color", _3ds_float_color(ambient))

    else:  # Track header
        track_chunk.add_variable("track_flags", _3ds_ushort(0x40))
        track_chunk.add_variable("frame_start", _3ds_uint(0))
        track_chunk.add_variable("frame_total", _3ds_uint(0))
        track_chunk.add_variable("nkeys", _3ds_uint(1))
        # Keyframe header
        track_chunk.add_variable("tcb_frame", _3ds_uint(0))
        track_chunk.add_variable("tcb_flags", _3ds_ushort())
        track_chunk.add_variable("color", _3ds_float_color(amb_color))

    amb_node.add_subchunk(track_chunk)

    return amb_node


##########
# EXPORT #
##########

def save(operator, context, filepath="", scale_factor=1.0, use_scene_unit=False, use_selection=False,
         object_filter=None, use_hierarchy=False, use_keyframes=False, global_matrix=None, use_cursor=False):
    """Save the Blender scene to a 3ds file."""

    # Time the export
    duration = time.time()
    context.window.cursor_set('WAIT')

    scene = context.scene
    layer = context.view_layer
    depsgraph = context.evaluated_depsgraph_get()
    world = scene.world

    unit_measure = 1.0
    if use_scene_unit:
        unit_length = scene.unit_settings.length_unit
        if unit_length == 'MILES':
            unit_measure = 0.000621371
        elif unit_length == 'KILOMETERS':
            unit_measure = 0.001
        elif unit_length == 'FEET':
            unit_measure = 3.280839895
        elif unit_length == 'INCHES':
            unit_measure = 39.37007874
        elif unit_length == 'CENTIMETERS':
            unit_measure = 100
        elif unit_length == 'MILLIMETERS':
            unit_measure = 1000
        elif unit_length == 'THOU':
            unit_measure = 39370.07874
        elif unit_length == 'MICROMETERS':
            unit_measure = 1000000

    mtx_scale = mathutils.Matrix.Scale((scale_factor * unit_measure),4)

    if global_matrix is None:
        global_matrix = mathutils.Matrix()

    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')

    # Initialize the main chunk (primary)
    primary = _3ds_chunk(PRIMARY)

    # Add version chunk
    version_chunk = _3ds_chunk(VERSION)
    version_chunk.add_variable("version", _3ds_uint(3))
    primary.add_subchunk(version_chunk)

    # Init main object info chunk
    object_info = _3ds_chunk(OBJECTINFO)
    mesh_version = _3ds_chunk(MESHVERSION)
    mesh_version.add_variable("mesh", _3ds_uint(3))
    object_info.add_subchunk(mesh_version)

    # Add MASTERSCALE element
    mscale = _3ds_chunk(MASTERSCALE)
    mscale.add_variable("scale", _3ds_float(1.0))
    object_info.add_subchunk(mscale)

    # Add 3D cursor location
    if use_cursor:
        cursor_chunk = _3ds_chunk(O_CONSTS)
        cursor_chunk.add_variable("cursor", _3ds_point_3d(scene.cursor.location))
        object_info.add_subchunk(cursor_chunk)

    # Init main keyframe data chunk
    if use_keyframes:
        revision = 0x0005
        stop = scene.frame_end
        start = scene.frame_start
        curtime = scene.frame_current
        kfdata = make_kfdata(revision, start, stop, curtime)

    # Add AMBIENT color
    if world is not None and 'WORLD' in object_filter:
        ambient_chunk = _3ds_chunk(AMBIENTLIGHT)
        ambient_light = _3ds_chunk(RGB)
        ambient_light.add_variable("ambient", _3ds_float_color(world.color))
        ambient_chunk.add_subchunk(ambient_light)
        object_info.add_subchunk(ambient_chunk)

        # Add BACKGROUND and BITMAP
        if world.use_nodes:
            bgtype = 'BACKGROUND'
            ntree = world.node_tree.links
            background_color_chunk = _3ds_chunk(RGB)
            background_chunk = _3ds_chunk(SOLIDBACKGND)
            background_flag = _3ds_chunk(USE_SOLIDBGND)
            bgmixer = 'BACKGROUND', 'MIX', 'MIX_RGB'
            bgshade = 'ADD_SHADER', 'MIX_SHADER', 'OUTPUT_WORLD'
            bg_tex = 'TEX_IMAGE', 'TEX_ENVIRONMENT'
            bg_color = next((lk.from_node.inputs[0].default_value[:3] for lk in ntree if lk.from_node.type == bgtype and lk.to_node.type in bgshade), world.color)
            bg_mixer = next((lk.from_node.type for lk in ntree if  lk.from_node.type in bgmixer and lk.to_node.type == bgtype), bgtype)
            bg_image = next((lk.from_node.image.name for lk in ntree if lk.from_node.type in bg_tex and lk.to_node.type == bg_mixer), False)
            gradient = next((lk.from_node.color_ramp.elements for lk in ntree if lk.from_node.type == 'VALTORGB' and lk.to_node.type in bgmixer), False)
            background_color_chunk.add_variable("color", _3ds_float_color(bg_color))
            background_chunk.add_subchunk(background_color_chunk)
            if bg_image:
                background_image = _3ds_chunk(BITMAP)
                background_flag = _3ds_chunk(USE_BITMAP)
                background_image.add_variable("image", _3ds_string(sane_name(bg_image)))
                object_info.add_subchunk(background_image)
            object_info.add_subchunk(background_chunk)

            # Add VGRADIENT chunk
            if gradient and len(gradient) >= 3:
                gradient_chunk = _3ds_chunk(VGRADIENT)
                background_flag = _3ds_chunk(USE_VGRADIENT)
                gradient_chunk.add_variable("midpoint", _3ds_float(gradient[1].position))
                gradient_topcolor_chunk = _3ds_chunk(RGB)
                gradient_topcolor_chunk.add_variable("color", _3ds_float_color(gradient[2].color[:3]))
                gradient_chunk.add_subchunk(gradient_topcolor_chunk)
                gradient_midcolor_chunk = _3ds_chunk(RGB)
                gradient_midcolor_chunk.add_variable("color", _3ds_float_color(gradient[1].color[:3]))
                gradient_chunk.add_subchunk(gradient_midcolor_chunk)
                gradient_lowcolor_chunk = _3ds_chunk(RGB)
                gradient_lowcolor_chunk.add_variable("color", _3ds_float_color(gradient[0].color[:3]))
                gradient_chunk.add_subchunk(gradient_lowcolor_chunk)
                object_info.add_subchunk(gradient_chunk)
            object_info.add_subchunk(background_flag)

            # Add FOG
            fognode = next((lk.from_socket.node for lk in ntree if lk.from_socket.node.type == 'VOLUME_ABSORPTION' and lk.to_socket.node.type in bgshade), False)
            if fognode:
                fog_chunk = _3ds_chunk(FOG)
                fog_color_chunk = _3ds_chunk(RGB)
                use_fog_flag = _3ds_chunk(USE_FOG)
                fog_density = fognode.inputs['Density'].default_value * 100
                fog_color_chunk.add_variable("color", _3ds_float_color(fognode.inputs[0].default_value[:3]))
                fog_chunk.add_variable("nearplane", _3ds_float(world.mist_settings.start))
                fog_chunk.add_variable("nearfog", _3ds_float(fog_density * 0.5))
                fog_chunk.add_variable("farplane", _3ds_float(world.mist_settings.depth))
                fog_chunk.add_variable("farfog", _3ds_float(fog_density + fog_density * 0.5))
                fog_chunk.add_subchunk(fog_color_chunk)
                object_info.add_subchunk(fog_chunk)

            # Add LAYER FOG
            foglayer = next((lk.from_socket.node for lk in ntree if lk.from_socket.node.type == 'VOLUME_SCATTER' and lk.to_socket.node.type in bgshade), False)
            if foglayer:
                layerfog_flag = 0
                if world.mist_settings.falloff == 'QUADRATIC':
                    layerfog_flag |= 0x1
                if world.mist_settings.falloff == 'INVERSE_QUADRATIC':
                    layerfog_flag |= 0x2
                layerfog_chunk = _3ds_chunk(LAYER_FOG)
                layerfog_color_chunk = _3ds_chunk(RGB)
                use_fog_flag = _3ds_chunk(USE_LAYER_FOG)
                layerfog_color_chunk.add_variable("color", _3ds_float_color(foglayer.inputs[0].default_value[:3]))
                layerfog_chunk.add_variable("lowZ", _3ds_float(world.mist_settings.start))
                layerfog_chunk.add_variable("highZ", _3ds_float(world.mist_settings.height))
                layerfog_chunk.add_variable("density", _3ds_float(foglayer.inputs[1].default_value))
                layerfog_chunk.add_variable("flags", _3ds_uint(layerfog_flag))
                layerfog_chunk.add_subchunk(layerfog_color_chunk)
                object_info.add_subchunk(layerfog_chunk)
            if fognode or foglayer and layer.use_pass_mist:
                object_info.add_subchunk(use_fog_flag)
        if use_keyframes and world.animation_data:
            kfdata.add_subchunk(make_ambient_node(world))

    # Make a list of all materials used in the selected meshes (use dictionary, each material is added once)
    materialDict = {}
    mesh_objects = []

    if use_selection:
        objects = [ob for ob in scene.objects if ob.type in object_filter and ob.visible_get(view_layer=layer) and ob.select_get(view_layer=layer)]
    else:
        objects = [ob for ob in scene.objects if ob.type in object_filter and ob.visible_get(view_layer=layer)]

    empty_objects = [ob for ob in objects if ob.type == 'EMPTY']
    light_objects = [ob for ob in objects if ob.type == 'LIGHT']
    camera_objects = [ob for ob in objects if ob.type == 'CAMERA']

    for ob in objects:
        # Get derived objects
        derived_dict = bpy_extras.io_utils.create_derived_objects(depsgraph, [ob])
        derived = derived_dict.get(ob)

        if derived is None:
            continue

        for ob_derived, mtx in derived:
            if ob.type not in {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META'}:
                continue

            try:
                data = ob_derived.to_mesh()
            except:
                data = None

            if data:
                matrix = global_matrix @ mtx
                data.transform(matrix)
                data.transform(mtx_scale)
                mesh_objects.append((ob_derived, data, matrix))
                ma_ls = data.materials
                ma_ls_len = len(ma_ls)

                # Get material/image tuples
                if data.uv_layers:
                    if not ma_ls:
                        ma = ma_name = None

                    for f, uf in zip(data.polygons, data.uv_layers.active.data):
                        if ma_ls:
                            ma_index = f.material_index
                            if ma_index >= ma_ls_len:
                                ma_index = f.material_index = 0
                            ma = ma_ls[ma_index]
                            ma_name = None if ma is None else ma.name
                        # Else there already set to none

                        img = get_uv_image(ma)
                        img_name = None if img is None else img.name

                        materialDict.setdefault((ma_name, img_name), (ma, img))

                else:
                    for ma in ma_ls:
                        if ma:  # Material may be None so check its not
                            materialDict.setdefault((ma.name, None), (ma, None))

                    # Why 0 Why!
                    for f in data.polygons:
                        if f.material_index >= ma_ls_len:
                            f.material_index = 0


    # Make material chunks for all materials used in the meshes
    for ma_image in materialDict.values():
        object_info.add_subchunk(make_material_chunk(ma_image[0], ma_image[1]))

    # Collect translation for transformation matrix
    translation = {}
    rotation = {}
    scale = {}

    # Give all objects a unique ID and build a dictionary from object name to object id
    object_id = {}
    name_id = {}

    for ob, data, matrix in mesh_objects:
        translation[ob.name] = mtx_scale @ ob.location
        rotation[ob.name] = ob.rotation_euler
        scale[ob.name] = mtx_scale.copy()
        name_id[ob.name] = len(name_id)
        object_id[ob.name] = len(object_id)

    for ob in empty_objects:
        translation[ob.name] = mtx_scale @ ob.location
        rotation[ob.name] = ob.rotation_euler
        scale[ob.name] = mtx_scale.copy()
        name_id[ob.name] = len(name_id)

    for ob in light_objects:
        translation[ob.name] = mtx_scale @ ob.location
        rotation[ob.name] = ob.rotation_euler
        scale[ob.name] = mtx_scale.copy()
        name_id[ob.name] = len(name_id)
        object_id[ob.name] = len(object_id)

    for ob in camera_objects:
        translation[ob.name] = mtx_scale @ ob.location
        rotation[ob.name] = ob.rotation_euler
        scale[ob.name] = mtx_scale.copy()
        name_id[ob.name] = len(name_id)
        object_id[ob.name] = len(object_id)

    # Create object chunks for all meshes
    i = 0
    for ob, mesh, matrix in mesh_objects:
        object_chunk = _3ds_chunk(OBJECT)

        # Set the object name
        object_chunk.add_variable("name", _3ds_string(sane_name(ob.name)))

        # Make a mesh chunk out of the mesh
        object_chunk.add_subchunk(make_mesh_chunk(ob, mesh, matrix, materialDict, translation))

        # Add hierachy chunk with ID from object_id dictionary
        if use_hierarchy:
            obj_hierarchy_chunk = _3ds_chunk(OBJECT_HIERARCHY)
            obj_hierarchy_chunk.add_variable("hierarchy", _3ds_ushort(object_id[ob.name]))

            # Add parent chunk if object has a parent
            if ob.parent is not None and (ob.parent.name in object_id):
                obj_parent_chunk = _3ds_chunk(OBJECT_PARENT)
                obj_parent_chunk.add_variable("parent", _3ds_ushort(object_id[ob.parent.name]))
                obj_hierarchy_chunk.add_subchunk(obj_parent_chunk)
            object_chunk.add_subchunk(obj_hierarchy_chunk)

        # ensure the mesh has no over sized arrays - skip ones that do!
        # Otherwise we cant write since the array size wont fit into USHORT
        if object_chunk.validate():
            object_info.add_subchunk(object_chunk)
        else:
            operator.report({'WARNING'}, "Object %r can't be written into a 3DS file")

        # Export object node
        if use_keyframes:
            kfdata.add_subchunk(make_object_node(ob, translation, rotation, scale, name_id))

        i += i

    # Create chunks for all empties - only requires a object node
    if use_keyframes:
        for ob in empty_objects:
            kfdata.add_subchunk(make_object_node(ob, translation, rotation, scale, name_id))

    # Create light object chunks
    for ob in light_objects:
        object_chunk = _3ds_chunk(OBJECT)
        obj_light_chunk = _3ds_chunk(OBJECT_LIGHT)
        color_float_chunk = _3ds_chunk(RGB)
        light_distance = translation[ob.name]
        light_attenuate = _3ds_chunk(LIGHT_ATTENUATE)
        light_inner_range = _3ds_chunk(LIGHT_INNER_RANGE)
        light_outer_range = _3ds_chunk(LIGHT_OUTER_RANGE)
        light_energy_factor = _3ds_chunk(LIGHT_MULTIPLIER)
        light_ratio = ob.data.energy if ob.data.type == 'SUN' else ob.data.energy * 0.001
        object_chunk.add_variable("light", _3ds_string(sane_name(ob.name)))
        obj_light_chunk.add_variable("location", _3ds_point_3d(light_distance))
        color_float_chunk.add_variable("color", _3ds_float_color(ob.data.color))
        light_outer_range.add_variable("distance", _3ds_float(ob.data.cutoff_distance))
        light_inner_range.add_variable("radius", _3ds_float(ob.data.shadow_soft_size * 100))
        light_energy_factor.add_variable("energy", _3ds_float(light_ratio))
        obj_light_chunk.add_subchunk(color_float_chunk)
        obj_light_chunk.add_subchunk(light_outer_range)
        obj_light_chunk.add_subchunk(light_inner_range)
        obj_light_chunk.add_subchunk(light_energy_factor)
        if ob.data.use_custom_distance:
            obj_light_chunk.add_subchunk(light_attenuate)

        if ob.data.type == 'SPOT':
            cone_angle = math.degrees(ob.data.spot_size)
            hot_spot = cone_angle - (ob.data.spot_blend * math.floor(cone_angle))
            spot_pos = calc_target(light_distance, rotation[ob.name].x, rotation[ob.name].z)
            spotlight_chunk = _3ds_chunk(LIGHT_SPOTLIGHT)
            spot_roll_chunk = _3ds_chunk(LIGHT_SPOT_ROLL)
            spotlight_chunk.add_variable("target", _3ds_point_3d(spot_pos))
            spotlight_chunk.add_variable("hotspot", _3ds_float(round(hot_spot, 4)))
            spotlight_chunk.add_variable("angle", _3ds_float(round(cone_angle, 4)))
            spot_roll_chunk.add_variable("roll", _3ds_float(round(rotation[ob.name].y, 6)))
            spotlight_chunk.add_subchunk(spot_roll_chunk)
            if ob.data.use_shadow:
                spot_shadow_flag = _3ds_chunk(LIGHT_SPOT_SHADOWED)
                spot_shadow_chunk = _3ds_chunk(LIGHT_SPOT_LSHADOW)
                spot_shadow_chunk.add_variable("bias", _3ds_float(round(ob.data.shadow_buffer_bias,4)))
                spot_shadow_chunk.add_variable("filter", _3ds_float(round((ob.data.shadow_buffer_clip_start * 10),4)))
                spot_shadow_chunk.add_variable("buffer", _3ds_ushort(0x200))
                spotlight_chunk.add_subchunk(spot_shadow_flag)
                spotlight_chunk.add_subchunk(spot_shadow_chunk)
            if ob.data.show_cone:
                spot_cone_chunk = _3ds_chunk(LIGHT_SPOT_SEE_CONE)
                spotlight_chunk.add_subchunk(spot_cone_chunk)
            if ob.data.use_square:
                spot_square_chunk = _3ds_chunk(LIGHT_SPOT_RECTANGLE)
                spotlight_chunk.add_subchunk(spot_square_chunk)
            if ob.scale.x and ob.scale.y != 0.0:
                spot_aspect_chunk = _3ds_chunk(LIGHT_SPOT_ASPECT)
                spot_aspect_chunk.add_variable("aspect", _3ds_float(round((ob.scale.x / ob.scale.y),4)))
                spotlight_chunk.add_subchunk(spot_aspect_chunk)
            if ob.data.use_nodes:
                links = ob.data.node_tree.links
                bptype = 'EMISSION'
                bpmix = 'MIX', 'MIX_RGB', 'EMISSION'
                bptex = 'TEX_IMAGE', 'TEX_ENVIRONMENT'
                bpout = 'ADD_SHADER', 'MIX_SHADER', 'OUTPUT_LIGHT'
                bshade = next((lk.from_node.type for lk in links if lk.from_node.type == bptype and lk.to_node.type in bpout), None)
                bpnode = next((lk.from_node.type for lk in links if lk.from_node.type in bpmix and lk.to_node.type == bshade), bshade)
                bitmap = next((lk.from_node.image for lk in links if lk.from_node.type in bptex and lk.to_node.type == bpnode), False)
                if bitmap and bitmap is not None:
                    spot_projector_chunk = _3ds_chunk(LIGHT_SPOT_PROJECTOR)
                    spot_projector_chunk.add_variable("image", _3ds_string(sane_name(bitmap.name)))
                    spotlight_chunk.add_subchunk(spot_projector_chunk)
            obj_light_chunk.add_subchunk(spotlight_chunk)

        # Add light to object chunk
        object_chunk.add_subchunk(obj_light_chunk)

        # Add hierachy chunks with ID from object_id dictionary
        if use_hierarchy:
            obj_hierarchy_chunk = _3ds_chunk(OBJECT_HIERARCHY)
            obj_parent_chunk = _3ds_chunk(OBJECT_PARENT)
            obj_hierarchy_chunk.add_variable("hierarchy", _3ds_ushort(object_id[ob.name]))
            if ob.parent is None or (ob.parent.name not in object_id):
                obj_parent_chunk.add_variable("parent", _3ds_ushort(ROOT_OBJECT))
            else:  # Get the parent ID from the object_id dict
                obj_parent_chunk.add_variable("parent", _3ds_ushort(object_id[ob.parent.name]))
            obj_hierarchy_chunk.add_subchunk(obj_parent_chunk)
            object_chunk.add_subchunk(obj_hierarchy_chunk)

        # Add light object and hierarchy chunks to object info
        object_info.add_subchunk(object_chunk)

        # Export light and spotlight target node
        if use_keyframes:
            kfdata.add_subchunk(make_object_node(ob, translation, rotation, scale, name_id))
            if ob.data.type == 'SPOT':
                kfdata.add_subchunk(make_target_node(ob, translation, rotation, scale, name_id))

    # Create camera object chunks
    for ob in camera_objects:
        object_chunk = _3ds_chunk(OBJECT)
        camera_chunk = _3ds_chunk(OBJECT_CAMERA)
        crange_chunk = _3ds_chunk(OBJECT_CAM_RANGES)
        camera_distance = translation[ob.name]
        camera_target = calc_target(camera_distance, rotation[ob.name].x, rotation[ob.name].z)
        object_chunk.add_variable("camera", _3ds_string(sane_name(ob.name)))
        camera_chunk.add_variable("location", _3ds_point_3d(camera_distance))
        camera_chunk.add_variable("target", _3ds_point_3d(camera_target))
        camera_chunk.add_variable("roll", _3ds_float(round(rotation[ob.name].y, 6)))
        camera_chunk.add_variable("lens", _3ds_float(ob.data.lens))
        crange_chunk.add_variable("clipstart", _3ds_float(ob.data.clip_start * 0.1))
        crange_chunk.add_variable("clipend", _3ds_float(ob.data.clip_end * 0.1))
        camera_chunk.add_subchunk(crange_chunk)
        object_chunk.add_subchunk(camera_chunk)

        # Add hierachy chunks with ID from object_id dictionary
        if use_hierarchy:
            obj_hierarchy_chunk = _3ds_chunk(OBJECT_HIERARCHY)
            obj_parent_chunk = _3ds_chunk(OBJECT_PARENT)
            obj_hierarchy_chunk.add_variable("hierarchy", _3ds_ushort(object_id[ob.name]))
            if ob.parent is None or (ob.parent.name not in object_id):
                obj_parent_chunk.add_variable("parent", _3ds_ushort(ROOT_OBJECT))
            else:  # Get the parent ID from the object_id dict
                obj_parent_chunk.add_variable("parent", _3ds_ushort(object_id[ob.parent.name]))
            obj_hierarchy_chunk.add_subchunk(obj_parent_chunk)
            object_chunk.add_subchunk(obj_hierarchy_chunk)

        # Add light object and hierarchy chunks to object info
        object_info.add_subchunk(object_chunk)

        # Export camera and target node
        if use_keyframes:
            kfdata.add_subchunk(make_object_node(ob, translation, rotation, scale, name_id))
            kfdata.add_subchunk(make_target_node(ob, translation, rotation, scale, name_id))

    # Add main object info chunk to primary chunk
    primary.add_subchunk(object_info)

    # Add main keyframe data chunk to primary chunk
    if use_keyframes:
        primary.add_subchunk(kfdata)

    # The chunk hierarchy is completely built, now check the size
    primary.get_size()

    # Open the file for writing
    file = open(filepath, 'wb')

    # Recursively write the chunks to file
    primary.write(file)

    # Close the file
    file.close()

    # Clear name mapping vars, could make locals too
    del name_unique[:]
    name_mapping.clear()

    # Debugging only: report the exporting time
    context.window.cursor_set('DEFAULT')
    print("3ds export time: %.2f" % (time.time() - duration))

    # Debugging only: dump the chunk hierarchy
    # primary.dump()

    return {'FINISHED'}
