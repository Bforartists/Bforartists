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

# Script copyright (C) Bob Holcomb
# Contributors: Campbell Barton, Bob Holcomb, Richard Lärkäng, Damien McGinnes, Mark Stijnman, Sebastian Sille

"""
Exporting is based on 3ds loader from www.gametutorials.com(Thanks DigiBen) and using information
from the lib3ds project (http://lib3ds.sourceforge.net/) sourcecode.
"""

import bpy
import math
import struct
import mathutils
import bpy_extras
from bpy_extras import node_shader_utils

######################################################
# Data Structures
######################################################

# Some of the chunks that we will export
# ----- Primary Chunk, at the beginning of each file
PRIMARY = 0x4D4D

# ------ Main Chunks
VERSION = 0x0002  # This gives the version of the .3ds file
KFDATA = 0xB000  # This is the header for all of the key frame info

# ------ sub defines of OBJECTINFO
OBJECTINFO = 0x3D3D  # Main mesh object chunk before the material and object information
MESHVERSION = 0x3D3E  # This gives the version of the mesh
AMBIENTLIGHT = 0x2100  # The color of the ambient light
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
MATSELFILPCT = 0xA084  # Self illumination strength (percent)
MATSHADING = 0xA100  # Material shading method

MAT_DIFFUSEMAP = 0xA200  # This is a header for a new diffuse texture
MAT_SPECMAP = 0xA204  # head for specularity map
MAT_OPACMAP = 0xA210  # head for opacity map
MAT_REFLMAP = 0xA220  # head for reflect map
MAT_BUMPMAP = 0xA230  # head for normal map
MAT_BUMP_PERCENT = 0xA252  # Normalmap strength (percent)
MAT_TEX2MAP = 0xA33A  # head for secondary texture
MAT_SHINMAP = 0xA33C  # head for roughness map
MAT_SELFIMAP = 0xA33D  # head for emission map

# >------ sub defines of MAT_MAP
MATMAPFILE = 0xA300  # This holds the file name of a texture
MAT_MAP_TILING = 0xa351   # 2nd bit (from LSB) is mirror UV flag
MAT_MAP_TEXBLUR = 0xA353  # Texture blurring factor
MAT_MAP_USCALE = 0xA354   # U axis scaling
MAT_MAP_VSCALE = 0xA356   # V axis scaling
MAT_MAP_UOFFSET = 0xA358  # U axis offset
MAT_MAP_VOFFSET = 0xA35A  # V axis offset
MAT_MAP_ANG = 0xA35C      # UV rotation around the z-axis in rad
MAP_COL1 = 0xA360  # Tint Color1
MAP_COL2 = 0xA362  # Tint Color2
MAP_RCOL = 0xA364  # Red tint
MAP_GCOL = 0xA366  # Green tint
MAP_BCOL = 0xA368  # Blue tint

RGB = 0x0010  # RGB float
RGB1 = 0x0011  # RGB Color1
RGB2 = 0x0012  # RGB Color2
PCT = 0x0030  # Percent chunk
MASTERSCALE = 0x0100  # Master scale factor

# >------ sub defines of OBJECT
OBJECT_MESH = 0x4100  # This lets us know that we are reading a new object
OBJECT_LIGHT = 0x4600  # This lets us know we are reading a light object
OBJECT_CAMERA = 0x4700  # This lets us know we are reading a camera object

# >------ Sub defines of LIGHT
LIGHT_MULTIPLIER = 0x465B  # The light energy factor
LIGHT_SPOTLIGHT = 0x4610  # The target of a spotlight
LIGHT_SPOTROLL = 0x4656  # The roll angle of the spot

# >------ sub defines of CAMERA
OBJECT_CAM_RANGES = 0x4720  # The camera range values

# >------ sub defines of OBJECT_MESH
OBJECT_VERTICES = 0x4110  # The objects vertices
OBJECT_FACES = 0x4120  # The objects faces
OBJECT_MATERIAL = 0x4130  # This is found if the object has a material, either texture map or color
OBJECT_UV = 0x4140  # The UV texture coordinates
OBJECT_SMOOTH = 0x4150  # The objects smooth groups
OBJECT_TRANS_MATRIX = 0x4160  # The Object Matrix

# >------ sub defines of KFDATA
KFDATA_KFHDR = 0xB00A
KFDATA_KFSEG = 0xB008
KFDATA_KFCURTIME = 0xB009
KFDATA_OBJECT_NODE_TAG = 0xB002

# >------ sub defines of OBJECT_NODE_TAG
OBJECT_NODE_ID = 0xB030
OBJECT_NODE_HDR = 0xB010
OBJECT_PIVOT = 0xB013
OBJECT_INSTANCE_NAME = 0xB011
POS_TRACK_TAG = 0xB020
ROT_TRACK_TAG = 0xB021
SCL_TRACK_TAG = 0xB022


# So 3ds max can open files, limit names to 12 in length
# this is very annoying for filenames!
name_unique = []  # stores str, ascii only
name_mapping = {}  # stores {orig: byte} mapping


def sane_name(name):
    name_fixed = name_mapping.get(name)
    if name_fixed is not None:
        return name_fixed

    # strip non ascii chars
    new_name_clean = new_name = name.encode("ASCII", "replace").decode("ASCII")[:12]
    i = 0

    while new_name in name_unique:
        new_name = new_name_clean + ".%.3d" % i
        i += 1

    # note, appending the 'str' version.
    name_unique.append(new_name)
    name_mapping[name] = new_name = new_name.encode("ASCII", "replace")
    return new_name


def uv_key(uv):
    return round(uv[0], 6), round(uv[1], 6)


# size defines:
SZ_SHORT = 2
SZ_INT = 4
SZ_FLOAT = 4


class _3ds_ushort(object):
    """Class representing a short (2-byte integer) for a 3ds file.
    *** This looks like an unsigned short H is unsigned from the struct docs - Cam***"""
    __slots__ = ("value", )

    def __init__(self, val=0):
        self.value = val

    def get_size(self):
        return SZ_SHORT

    def write(self, file):
        file.write(struct.pack("<H", self.value))

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
        file.write(struct.pack("<I", self.value))

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
        file.write(struct.pack("<f", self.value))

    def __str__(self):
        return str(self.value)


class _3ds_string(object):
    """Class representing a zero-terminated string for a 3ds file."""
    __slots__ = ("value", )

    def __init__(self, val):
        assert(type(val) == bytes)
        self.value = val

    def get_size(self):
        return (len(self.value) + 1)

    def write(self, file):
        binary_format = "<%ds" % (len(self.value) + 1)
        file.write(struct.pack(binary_format, self.value))

    def __str__(self):
        return str(self.value)


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
'''
class _3ds_point_4d(object):
    """Class representing a four-dimensional point for a 3ds file, for instance a quaternion."""
    __slots__ = "x","y","z","w"
    def __init__(self, point=(0.0,0.0,0.0,0.0)):
        self.x, self.y, self.z, self.w = point

    def get_size(self):
        return 4*SZ_FLOAT

    def write(self,file):
        data=struct.pack('<4f', self.x, self.y, self.z, self.w)
        file.write(data)

    def __str__(self):
        return '(%f, %f, %f, %f)' % (self.x, self.y, self.z, self.w)
'''


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
        file.write(struct.pack('3f', self.r, self.g, self.b))

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
    __slots__ = ("vindex", )

    def __init__(self, vindex):
        self.vindex = vindex

    def get_size(self):
        return 4 * SZ_SHORT

    # no need to validate every face vert. the oversized array will
    # catch this problem

    def write(self, file):
        # The last zero is only used by 3d studio
        file.write(struct.pack("<4H", self.vindex[0], self.vindex[1], self.vindex[2], 0))

    def __str__(self):
        return "[%d %d %d]" % (self.vindex[0], self.vindex[1], self.vindex[2])


class _3ds_array(object):
    """Class representing an array of variables for a 3ds file.

    Consists of a _3ds_ushort to indicate the number of items, followed by the items themselves.
    """
    __slots__ = "values", "size"

    def __init__(self):
        self.values = []
        self.size = SZ_SHORT

    # add an item:
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
    # outputs the number of items, not all of the actual items.
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


# the chunk class
class _3ds_chunk(object):
    """Class representing a chunk in a 3ds file.

    Chunks contain zero or more variables, followed by zero or more subchunks.
    """
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

        The sizes of the variables and subchunks are used to determine this chunk\'s size."""
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
        # write header
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
              "ID=%r" % hex(self.ID.value),
              "size=%r" % self.get_size())
        for variable in self.variables:
            variable.dump(indent + 1)
        for subchunk in self.subchunks:
            subchunk.dump(indent + 1)


######################################################
# EXPORT
######################################################

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
        ma_wrap = node_shader_utils.PrincipledBSDFWrapper(ma)
        ma_tex = ma_wrap.base_color_texture
        if ma_tex and ma_tex.image is not None:
            return ma_tex.image
    else:
        return get_material_image(ma)


def make_material_subchunk(chunk_id, color):
    """Make a material subchunk.

    Used for color subchunks, such as diffuse color or ambient color subchunks."""
    mat_sub = _3ds_chunk(chunk_id)
    col1 = _3ds_chunk(RGB1)
    col1.add_variable("color1", _3ds_rgb_color(color))
    mat_sub.add_subchunk(col1)
    # optional:
    #col2 = _3ds_chunk(RGB1)
    #col2.add_variable("color2", _3ds_rgb_color(color))
    # mat_sub.add_subchunk(col2)
    return mat_sub


def make_percent_subchunk(chunk_id, percent):
    """Make a percentage based subchunk."""
    pct_sub = _3ds_chunk(chunk_id)
    pcti = _3ds_chunk(PCT)
    pcti.add_variable("percent", _3ds_ushort(int(round(percent * 100, 0))))
    pct_sub.add_subchunk(pcti)
    return pct_sub


def make_texture_chunk(chunk_id, images):
    """Make Material Map texture chunk."""
    # Add texture percentage value (100 = 1.0)
    ma_sub = make_percent_subchunk(chunk_id, 1)
    has_entry = False

    def add_image(img):
        filename = bpy.path.basename(image.filepath)
        ma_sub_file = _3ds_chunk(MATMAPFILE)
        ma_sub_file.add_variable("image", _3ds_string(sane_name(filename)))
        ma_sub.add_subchunk(ma_sub_file)

    for image in images:
        add_image(image)
        has_entry = True

    return ma_sub if has_entry else None


def make_material_texture_chunk(chunk_id, texslots, pct):
    """Make Material Map texture chunk given a seq. of `MaterialTextureSlot`'s
        Paint slots are optionally used as image source if no nodes are
        used. No additional filtering for mapping modes is done, all
        slots are written "as is"."""
    # Add texture percentage value
    mat_sub = make_percent_subchunk(chunk_id, pct)
    has_entry = False

    def add_texslot(texslot):
        image = texslot.image

        filename = bpy.path.basename(image.filepath)
        mat_sub_file = _3ds_chunk(MATMAPFILE)
        mat_sub_file.add_variable("mapfile", _3ds_string(sane_name(filename)))
        mat_sub.add_subchunk(mat_sub_file)
        for link in texslot.socket_dst.links:
            socket = link.from_socket.identifier

        maptile = 0

        # no perfect mapping for mirror modes - 3DS only has uniform mirror w. repeat=2
        if texslot.extension == 'EXTEND':
            maptile |= 0x1
        # CLIP maps to 3DS' decal flag
        elif texslot.extension == 'CLIP':
            maptile |= 0x10

        mat_sub_tile = _3ds_chunk(MAT_MAP_TILING)
        mat_sub_tile.add_variable("tiling", _3ds_ushort(maptile))
        mat_sub.add_subchunk(mat_sub_tile)

        if socket == 'Alpha':
            mat_sub_alpha = _3ds_chunk(MAP_TILING)
            alphaflag = 0x40  # summed area sampling 0x20
            mat_sub_alpha.add_variable("alpha", _3ds_ushort(alphaflag))
            mat_sub.add_subchunk(mat_sub_alpha)
            if texslot.socket_dst.identifier in {'Base Color', 'Specular'}:
                mat_sub_tint = _3ds_chunk(MAP_TILING)  # RGB tint 0x200
                tint = 0x80 if texslot.image.colorspace_settings.name == 'Non-Color' else 0x200
                mat_sub_tint.add_variable("tint", _3ds_ushort(tint))
                mat_sub.add_subchunk(mat_sub_tint)

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

    # store all textures for this mapto in order. This at least is what
    # the 3DS exporter did so far, afaik most readers will just skip
    # over 2nd textures.
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

    if image:
        name_str += image.name

    name.add_variable("name", _3ds_string(sane_name(name_str)))
    material_chunk.add_subchunk(name)

    if not material:
        shading.add_variable("shading", _3ds_ushort(1))  # Flat shading
        material_chunk.add_subchunk(make_material_subchunk(MATAMBIENT, (0.0, 0.0, 0.0)))
        material_chunk.add_subchunk(make_material_subchunk(MATDIFFUSE, (0.8, 0.8, 0.8)))
        material_chunk.add_subchunk(make_material_subchunk(MATSPECULAR, (1.0, 1.0, 1.0)))
        material_chunk.add_subchunk(make_percent_subchunk(MATSHINESS, .2))
        material_chunk.add_subchunk(make_percent_subchunk(MATSHIN2, 1))
        material_chunk.add_subchunk(shading)

    elif material and material.use_nodes:
        wrap = node_shader_utils.PrincipledBSDFWrapper(material)
        shading.add_variable("shading", _3ds_ushort(3))  # Phong shading
        material_chunk.add_subchunk(make_material_subchunk(MATAMBIENT, wrap.emission_color[:3]))
        material_chunk.add_subchunk(make_material_subchunk(MATDIFFUSE, wrap.base_color[:3]))
        material_chunk.add_subchunk(make_material_subchunk(MATSPECULAR, material.specular_color[:]))
        material_chunk.add_subchunk(make_percent_subchunk(MATSHINESS, wrap.roughness))
        material_chunk.add_subchunk(make_percent_subchunk(MATSHIN2, wrap.specular))
        material_chunk.add_subchunk(make_percent_subchunk(MATSHIN3, wrap.metallic))
        material_chunk.add_subchunk(make_percent_subchunk(MATTRANS, 1 - wrap.alpha))
        material_chunk.add_subchunk(shading)

        if wrap.base_color_texture:
            d_pct = 0.7 + sum(wrap.base_color[:]) * 0.1
            color = [wrap.base_color_texture]
            matmap = make_material_texture_chunk(MAT_DIFFUSEMAP, color, d_pct)
            if matmap:
                material_chunk.add_subchunk(matmap)

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
            bump = wrap.normalmap_strength
            b_pct = min(bump, 1)
            bumpval = min(999, (bump * 100))  # 3ds max bump = 999
            strength = _3ds_chunk(MAT_BUMP_PERCENT)
            strength.add_variable("bump_pct", _3ds_ushort(int(bumpval)))
            matmap = make_material_texture_chunk(MAT_BUMPMAP, normal, b_pct)
            if matmap:
                material_chunk.add_subchunk(matmap)
                material_chunk.add_subchunk(strength)

        if wrap.roughness_texture:
            roughness = [wrap.roughness_texture]
            r_pct = material.roughness
            matmap = make_material_texture_chunk(MAT_SHINMAP, roughness, r_pct)
            if matmap:
                material_chunk.add_subchunk(matmap)

        if wrap.emission_color_texture:
            e_pct = sum(wrap.emission_color[:]) * .25
            emission = [wrap.emission_color_texture]
            matmap = make_material_texture_chunk(MAT_SELFIMAP, emission, e_pct)
            if matmap:
                material_chunk.add_subchunk(matmap)

        # make sure no textures are lost. Everything that doesn't fit
        # into a channel is exported as secondary texture
        diffuse = []

        for link in wrap.material.node_tree.links:
            if link.from_node.type == 'TEX_IMAGE' and link.to_node.type != 'BSDF_PRINCIPLED':
                diffuse = [link.from_node.image] if not wrap.normalmap_texture else None

        if diffuse:
            matmap = make_texture_chunk(MAT_TEX2MAP, diffuse)
            if matmap:
                material_chunk.add_subchunk(matmap)

    else:
        shading.add_variable("shading", _3ds_ushort(2))  # Gouraud shading
        material_chunk.add_subchunk(make_material_subchunk(MATAMBIENT, material.line_color[:3]))
        material_chunk.add_subchunk(make_material_subchunk(MATDIFFUSE, material.diffuse_color[:3]))
        material_chunk.add_subchunk(make_material_subchunk(MATSPECULAR, material.specular_color[:]))
        material_chunk.add_subchunk(make_percent_subchunk(MATSHINESS, material.roughness))
        material_chunk.add_subchunk(make_percent_subchunk(MATSHIN2, material.specular_intensity))
        material_chunk.add_subchunk(make_percent_subchunk(MATSHIN3, material.metallic))
        material_chunk.add_subchunk(make_percent_subchunk(MATTRANS, 1 - material.diffuse_color[3]))
        material_chunk.add_subchunk(shading)

        slots = [get_material_image(material)]  # can be None

        if image:
            material_chunk.add_subchunk(make_texture_chunk(MAT_DIFFUSEMAP, slots))

    return material_chunk


class tri_wrapper(object):
    """Class representing a triangle.

    Used when converting faces to triangles"""

    __slots__ = "vertex_index", "ma", "image", "faceuvs", "offset", "group"

    def __init__(self, vindex=(0, 0, 0), ma=None, image=None, faceuvs=None, group=0):
        self.vertex_index = vindex
        self.ma = ma
        self.image = image
        self.faceuvs = faceuvs
        self.offset = [0, 0, 0]  # offset indices
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

        uf = mesh.uv_layers.active.data if do_uv else None

        if do_uv:
            f_uv = [uf[lp].uv for lp in face.loops]
            for ma in mesh.materials:
                img = get_uv_image(ma) if uf else None
                if img is not None:
                    img = img.name

        smoothgroup = polygroup[face.polygon_index]

        if len(f_v) == 3:
            new_tri = tri_wrapper((f_v[0], f_v[1], f_v[2]), face.material_index, img)
            if (do_uv):
                new_tri.faceuvs = uv_key(f_uv[0]), uv_key(f_uv[1]), uv_key(f_uv[2])
            new_tri.group = smoothgroup if face.use_smooth else 0
            tri_list.append(new_tri)

    return tri_list


def remove_face_uv(verts, tri_list):
    """Remove face UV coordinates from a list of triangles.

    Since 3ds files only support one pair of uv coordinates for each vertex, face uv coordinates
    need to be converted to vertex uv coordinates. That means that vertices need to be duplicated when
    there are multiple uv coordinates per vertex."""

    # initialize a list of UniqueLists, one per vertex:
    #uv_list = [UniqueList() for i in xrange(len(verts))]
    unique_uvs = [{} for i in range(len(verts))]

    # for each face uv coordinate, add it to the UniqueList of the vertex
    for tri in tri_list:
        for i in range(3):
            # store the index into the UniqueList for future reference:
            # offset.append(uv_list[tri.vertex_index[i]].add(_3ds_point_uv(tri.faceuvs[i])))

            context_uv_vert = unique_uvs[tri.vertex_index[i]]
            uvkey = tri.faceuvs[i]

            offset_index__uv_3ds = context_uv_vert.get(uvkey)

            if not offset_index__uv_3ds:
                offset_index__uv_3ds = context_uv_vert[uvkey] = len(context_uv_vert), _3ds_point_uv(uvkey)

            tri.offset[i] = offset_index__uv_3ds[0]

    # At this point, each vertex has a UniqueList containing every uv coordinate that is associated with it
    # only once.

    # Now we need to duplicate every vertex as many times as it has uv coordinates and make sure the
    # faces refer to the new face indices:
    vert_index = 0
    vert_array = _3ds_array()
    uv_array = _3ds_array()
    index_list = []
    for i, vert in enumerate(verts):
        index_list.append(vert_index)

        pt = _3ds_point_3d(vert.co)  # reuse, should be ok
        uvmap = [None] * len(unique_uvs[i])
        for ii, uv_3ds in unique_uvs[i].values():
            # add a vertex duplicate to the vertex_array for every uv associated with this vertex:
            vert_array.add(pt)
            # add the uv coordinate to the uv array:
            # This for loop does not give uv's ordered by ii, so we create a new map
            # and add the uv's later
            # uv_array.add(uv_3ds)
            uvmap[ii] = uv_3ds

        # Add the uv's in the correct order
        for uv_3ds in uvmap:
            # add the uv coordinate to the uv array:
            uv_array.add(uv_3ds)

        vert_index += len(unique_uvs[i])

    # Make sure the triangle vertex indices now refer to the new vertex list:
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

            face_list.add(_3ds_face(tri.vertex_index))

            if materials:
                ma = materials[tri.ma]
                if ma:
                    ma = ma.name

            img = tri.image

            try:
                context_face_array = unique_mats[ma, img][1]
            except:
                name_str = ma if ma else "None"
                if img:
                    name_str += img

                context_face_array = _3ds_array()
                unique_mats[ma, img] = _3ds_string(sane_name(name_str)), context_face_array

            context_face_array.add(_3ds_ushort(i))
            # obj_material_faces[tri.ma].add(_3ds_ushort(i))

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
            face_list.add(_3ds_face(tri.vertex_index))
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


'''
def make_matrix_4x3_chunk(matrix):
    matrix_chunk = _3ds_chunk(OBJECT_TRANS_MATRIX)
    for vec in matrix.col:
        for f in vec[:3]:
            matrix_chunk.add_variable("matrix_f", _3ds_float(f))
    return matrix_chunk
'''


def make_mesh_chunk(ob, mesh, matrix, materialDict, translation):
    """Make a chunk out of a Blender mesh."""

    # Extract the triangles from the mesh:
    tri_list = extract_triangles(mesh)

    if mesh.uv_layers:
        # Remove the face UVs and convert it to vertex UV:
        vert_array, uv_array, tri_list = remove_face_uv(mesh.vertices, tri_list)
    else:
        # Add the vertices to the vertex array:
        vert_array = _3ds_array()
        for vert in mesh.vertices:
            vert_array.add(_3ds_point_3d(vert.co))
        # no UV at all:
        uv_array = None

    # create the chunk:
    mesh_chunk = _3ds_chunk(OBJECT_MESH)

    # add vertex chunk:
    mesh_chunk.add_subchunk(make_vert_chunk(vert_array))

    # add faces chunk:
    mesh_chunk.add_subchunk(make_faces_chunk(tri_list, mesh, materialDict))

    # if available, add uv chunk:
    if uv_array:
        mesh_chunk.add_subchunk(make_uv_chunk(uv_array))

    # mesh_chunk.add_subchunk(make_matrix_4x3_chunk(matrix))

    # create transformation matrix chunk
    matrix_chunk = _3ds_chunk(OBJECT_TRANS_MATRIX)
    obj_matrix = matrix.transposed().to_3x3()

    if ob.parent is None:
        obj_translate = translation[ob.name]

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


''' # COMMENTED OUT FOR 2.42 RELEASE!! CRASHES 3DS MAX
def make_kfdata(start=0, stop=0, curtime=0):
    """Make the basic keyframe data chunk"""
    kfdata = _3ds_chunk(KFDATA)

    kfhdr = _3ds_chunk(KFDATA_KFHDR)
    kfhdr.add_variable("revision", _3ds_ushort(0))
    # Not really sure what filename is used for, but it seems it is usually used
    # to identify the program that generated the .3ds:
    kfhdr.add_variable("filename", _3ds_string("Blender"))
    kfhdr.add_variable("animlen", _3ds_uint(stop-start))

    kfseg = _3ds_chunk(KFDATA_KFSEG)
    kfseg.add_variable("start", _3ds_uint(start))
    kfseg.add_variable("stop", _3ds_uint(stop))

    kfcurtime = _3ds_chunk(KFDATA_KFCURTIME)
    kfcurtime.add_variable("curtime", _3ds_uint(curtime))

    kfdata.add_subchunk(kfhdr)
    kfdata.add_subchunk(kfseg)
    kfdata.add_subchunk(kfcurtime)
    return kfdata

def make_track_chunk(ID, obj):
    """Make a chunk for track data.

    Depending on the ID, this will construct a position, rotation or scale track."""
    track_chunk = _3ds_chunk(ID)
    track_chunk.add_variable("track_flags", _3ds_ushort())
    track_chunk.add_variable("unknown", _3ds_uint())
    track_chunk.add_variable("unknown", _3ds_uint())
    track_chunk.add_variable("nkeys", _3ds_uint(1))
    # Next section should be repeated for every keyframe, but for now, animation is not actually supported.
    track_chunk.add_variable("tcb_frame", _3ds_uint(0))
    track_chunk.add_variable("tcb_flags", _3ds_ushort())
    if obj.type=='Empty':
        if ID==POS_TRACK_TAG:
            # position vector:
            track_chunk.add_variable("position", _3ds_point_3d(obj.getLocation()))
        elif ID==ROT_TRACK_TAG:
            # rotation (quaternion, angle first, followed by axis):
            q = obj.getEuler().to_quaternion()  # XXX, todo!
            track_chunk.add_variable("rotation", _3ds_point_4d((q.angle, q.axis[0], q.axis[1], q.axis[2])))
        elif ID==SCL_TRACK_TAG:
            # scale vector:
            track_chunk.add_variable("scale", _3ds_point_3d(obj.getSize()))
    else:
        # meshes have their transformations applied before
        # exporting, so write identity transforms here:
        if ID==POS_TRACK_TAG:
            # position vector:
            track_chunk.add_variable("position", _3ds_point_3d((0.0,0.0,0.0)))
        elif ID==ROT_TRACK_TAG:
            # rotation (quaternion, angle first, followed by axis):
            track_chunk.add_variable("rotation", _3ds_point_4d((0.0, 1.0, 0.0, 0.0)))
        elif ID==SCL_TRACK_TAG:
            # scale vector:
            track_chunk.add_variable("scale", _3ds_point_3d((1.0, 1.0, 1.0)))

    return track_chunk

def make_kf_obj_node(obj, name_to_id):
    """Make a node chunk for a Blender object.

    Takes the Blender object as a parameter. Object id's are taken from the dictionary name_to_id.
    Blender Empty objects are converted to dummy nodes."""

    name = obj.name
    # main object node chunk:
    kf_obj_node = _3ds_chunk(KFDATA_OBJECT_NODE_TAG)
    # chunk for the object id:
    obj_id_chunk = _3ds_chunk(OBJECT_NODE_ID)
    # object id is from the name_to_id dictionary:
    obj_id_chunk.add_variable("node_id", _3ds_ushort(name_to_id[name]))

    # object node header:
    obj_node_header_chunk = _3ds_chunk(OBJECT_NODE_HDR)
    # object name:
    if obj.type == 'Empty':
        # Empties are called "$$$DUMMY" and use the OBJECT_INSTANCE_NAME chunk
        # for their name (see below):
        obj_node_header_chunk.add_variable("name", _3ds_string("$$$DUMMY"))
    else:
        # Add the name:
        obj_node_header_chunk.add_variable("name", _3ds_string(sane_name(name)))
    # Add Flag variables (not sure what they do):
    obj_node_header_chunk.add_variable("flags1", _3ds_ushort(0))
    obj_node_header_chunk.add_variable("flags2", _3ds_ushort(0))

    # Check parent-child relationships:
    parent = obj.parent
    if (parent is None) or (parent.name not in name_to_id):
        # If no parent, or the parents name is not in the name_to_id dictionary,
        # parent id becomes -1:
        obj_node_header_chunk.add_variable("parent", _3ds_ushort(-1))
    else:
        # Get the parent's id from the name_to_id dictionary:
        obj_node_header_chunk.add_variable("parent", _3ds_ushort(name_to_id[parent.name]))

    # Add pivot chunk:
    obj_pivot_chunk = _3ds_chunk(OBJECT_PIVOT)
    obj_pivot_chunk.add_variable("pivot", _3ds_point_3d(obj.getLocation()))
    kf_obj_node.add_subchunk(obj_pivot_chunk)

    # add subchunks for object id and node header:
    kf_obj_node.add_subchunk(obj_id_chunk)
    kf_obj_node.add_subchunk(obj_node_header_chunk)

    # Empty objects need to have an extra chunk for the instance name:
    if obj.type == 'Empty':
        obj_instance_name_chunk = _3ds_chunk(OBJECT_INSTANCE_NAME)
        obj_instance_name_chunk.add_variable("name", _3ds_string(sane_name(name)))
        kf_obj_node.add_subchunk(obj_instance_name_chunk)

    # Add track chunks for position, rotation and scale:
    kf_obj_node.add_subchunk(make_track_chunk(POS_TRACK_TAG, obj))
    kf_obj_node.add_subchunk(make_track_chunk(ROT_TRACK_TAG, obj))
    kf_obj_node.add_subchunk(make_track_chunk(SCL_TRACK_TAG, obj))

    return kf_obj_node
'''


def save(operator,
         context, filepath="",
         use_selection=True,
         global_matrix=None,
         ):

    import time
    from bpy_extras.io_utils import create_derived_objects, free_derived_objects

    """Save the Blender scene to a 3ds file."""

    # Time the export
    duration = time.time()
    # Blender.Window.WaitCursor(1)

    if global_matrix is None:
        global_matrix = mathutils.Matrix()

    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')

    scene = context.scene
    layer = context.view_layer
    #depsgraph = context.evaluated_depsgraph_get()

    # Initialize the main chunk (primary):
    primary = _3ds_chunk(PRIMARY)
    # Add version chunk:
    version_chunk = _3ds_chunk(VERSION)
    version_chunk.add_variable("version", _3ds_uint(3))
    primary.add_subchunk(version_chunk)

    # Init main object info chunk:
    object_info = _3ds_chunk(OBJECTINFO)
    mesh_version = _3ds_chunk(MESHVERSION)
    mesh_version.add_variable("mesh", _3ds_uint(3))
    object_info.add_subchunk(mesh_version)

    # Add MASTERSCALE element
    mscale = _3ds_chunk(MASTERSCALE)
    mscale.add_variable("scale", _3ds_float(1))
    object_info.add_subchunk(mscale)

    # Add AMBIENT color
    if scene.world is not None:
        ambient_chunk = _3ds_chunk(AMBIENTLIGHT)
        ambient_light = _3ds_chunk(RGB)
        ambient_light.add_variable("ambient", _3ds_float_color(scene.world.color))
        ambient_chunk.add_subchunk(ambient_light)
        object_info.add_subchunk(ambient_chunk)

    ''' # COMMENTED OUT FOR 2.42 RELEASE!! CRASHES 3DS MAX
    # init main key frame data chunk:
    kfdata = make_kfdata()
    '''

    # Make a list of all materials used in the selected meshes (use a dictionary,
    # each material is added once):
    materialDict = {}
    mesh_objects = []

    if use_selection:
        objects = [ob for ob in scene.objects if not ob.hide_viewport and ob.select_get(view_layer=layer)]
    else:
        objects = [ob for ob in scene.objects if not ob.hide_viewport]

    light_objects = [ob for ob in objects if ob.type == 'LIGHT']
    camera_objects = [ob for ob in objects if ob.type == 'CAMERA']

    for ob in objects:
        # get derived objects
        free, derived = create_derived_objects(scene, ob)

        if derived is None:
            continue

        for ob_derived, mtx in derived:
            if ob.type not in {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META'}:
                continue

            #ob_derived_eval = ob_derived.evaluated_get(depsgraph)
            try:
                data = ob_derived.to_mesh()
            except:
                data = None

            if data:
                matrix = global_matrix @ mtx
                data.transform(matrix)
                mesh_objects.append((ob_derived, data, matrix))
                ma_ls = data.materials
                ma_ls_len = len(ma_ls)

                # get material/image tuples.
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
                        # else there already set to none

                        img = get_uv_image(ma)
                        img_name = None if img is None else img.name

                        materialDict.setdefault((ma_name, img_name), (ma, img))

                else:
                    for ma in ma_ls:
                        if ma:  # material may be None so check its not.
                            materialDict.setdefault((ma.name, None), (ma, None))

                    # Why 0 Why!
                    for f in data.polygons:
                        if f.material_index >= ma_ls_len:
                            f.material_index = 0

                # ob_derived_eval.to_mesh_clear()

        if free:
            free_derived_objects(ob)

    # Make material chunks for all materials used in the meshes:
    for ma_image in materialDict.values():
        object_info.add_subchunk(make_material_chunk(ma_image[0], ma_image[1]))

    # Give all objects a unique ID and build a dictionary from object name to object id:
    translation = {}  # collect translation for transformation matrix
    #name_to_id = {}
    for ob, data, matrix in mesh_objects:
        translation[ob.name] = ob.location
        #name_to_id[ob.name]= len(name_to_id)
    """
    #for ob in empty_objects:
    #    name_to_id[ob.name]= len(name_to_id)
    """

    # Create object chunks for all meshes:
    i = 0
    for ob, mesh, matrix in mesh_objects:
        # create a new object chunk
        object_chunk = _3ds_chunk(OBJECT)

        # set the object name
        object_chunk.add_variable("name", _3ds_string(sane_name(ob.name)))

        # make a mesh chunk out of the mesh:
        object_chunk.add_subchunk(make_mesh_chunk(ob, mesh, matrix, materialDict, translation))

        # ensure the mesh has no over sized arrays
        # skip ones that do!, otherwise we cant write since the array size wont
        # fit into USHORT.
        if object_chunk.validate():
            object_info.add_subchunk(object_chunk)
        else:
            operator.report({'WARNING'}, "Object %r can't be written into a 3DS file")

        ''' # COMMENTED OUT FOR 2.42 RELEASE!! CRASHES 3DS MAX
        # make a kf object node for the object:
        kfdata.add_subchunk(make_kf_obj_node(ob, name_to_id))
        '''

        # if not blender_mesh.users:
        # bpy.data.meshes.remove(blender_mesh)
        #blender_mesh.vertices = None

        i += i

    # Create chunks for all empties:
    ''' # COMMENTED OUT FOR 2.42 RELEASE!! CRASHES 3DS MAX
    for ob in empty_objects:
        # Empties only require a kf object node:
        kfdata.add_subchunk(make_kf_obj_node(ob, name_to_id))
        pass
    '''

    # Create light object chunks
    for ob in light_objects:
        object_chunk = _3ds_chunk(OBJECT)
        light_chunk = _3ds_chunk(OBJECT_LIGHT)
        color_float_chunk = _3ds_chunk(RGB)
        energy_factor = _3ds_chunk(LIGHT_MULTIPLIER)
        object_chunk.add_variable("light", _3ds_string(sane_name(ob.name)))
        light_chunk.add_variable("location", _3ds_point_3d(ob.location))
        color_float_chunk.add_variable("color", _3ds_float_color(ob.data.color))
        energy_factor.add_variable("energy", _3ds_float(ob.data.energy * .001))
        light_chunk.add_subchunk(color_float_chunk)
        light_chunk.add_subchunk(energy_factor)

        if ob.data.type == 'SPOT':
            cone_angle = math.degrees(ob.data.spot_size)
            hotspot = cone_angle - (ob.data.spot_blend * math.floor(cone_angle))
            hypo = math.copysign(math.sqrt(pow(ob.location[0], 2) + pow(ob.location[1], 2)), ob.location[1])
            pos_x = ob.location[0] + (ob.location[1] * math.tan(ob.rotation_euler[2]))
            pos_y = ob.location[1] + (ob.location[0] * math.tan(math.radians(90) - ob.rotation_euler[2]))
            pos_z = hypo * math.tan(math.radians(90) - ob.rotation_euler[0])
            spotlight_chunk = _3ds_chunk(LIGHT_SPOTLIGHT)
            spot_roll_chunk = _3ds_chunk(LIGHT_SPOTROLL)
            spotlight_chunk.add_variable("target", _3ds_point_3d((pos_x, pos_y, pos_z)))
            spotlight_chunk.add_variable("hotspot", _3ds_float(round(hotspot, 4)))
            spotlight_chunk.add_variable("angle", _3ds_float(round(cone_angle, 4)))
            spot_roll_chunk.add_variable("roll", _3ds_float(round(ob.rotation_euler[1], 6)))
            spotlight_chunk.add_subchunk(spot_roll_chunk)
            light_chunk.add_subchunk(spotlight_chunk)

        # Add light to object info
        object_chunk.add_subchunk(light_chunk)
        object_info.add_subchunk(object_chunk)

    # Create camera object chunks
    for ob in camera_objects:
        object_chunk = _3ds_chunk(OBJECT)
        camera_chunk = _3ds_chunk(OBJECT_CAMERA)
        diagonal = math.copysign(math.sqrt(pow(ob.location[0], 2) + pow(ob.location[1], 2)), ob.location[1])
        focus_x = ob.location[0] + (ob.location[1] * math.tan(ob.rotation_euler[2]))
        focus_y = ob.location[1] + (ob.location[0] * math.tan(math.radians(90) - ob.rotation_euler[2]))
        focus_z = diagonal * math.tan(math.radians(90) - ob.rotation_euler[0])
        object_chunk.add_variable("camera", _3ds_string(sane_name(ob.name)))
        camera_chunk.add_variable("location", _3ds_point_3d(ob.location))
        camera_chunk.add_variable("target", _3ds_point_3d((focus_x, focus_y, focus_z)))
        camera_chunk.add_variable("roll", _3ds_float(round(ob.rotation_euler[1], 6)))
        camera_chunk.add_variable("lens", _3ds_float(ob.data.lens))
        object_chunk.add_subchunk(camera_chunk)
        object_info.add_subchunk(object_chunk)

    # Add main object info chunk to primary chunk:
    primary.add_subchunk(object_info)

    ''' # COMMENTED OUT FOR 2.42 RELEASE!! CRASHES 3DS MAX
    # Add main keyframe data chunk to primary chunk:
    primary.add_subchunk(kfdata)
    '''

    # At this point, the chunk hierarchy is completely built.

    # Check the size:
    primary.get_size()
    # Open the file for writing:
    file = open(filepath, 'wb')

    # Recursively write the chunks to file:
    primary.write(file)

    # Close the file:
    file.close()

    # Clear name mapping vars, could make locals too
    del name_unique[:]
    name_mapping.clear()

    # Debugging only: report the exporting time:
    # Blender.Window.WaitCursor(0)
    print("3ds export time: %.2f" % (time.time() - duration))

    # Debugging only: dump the chunk hierarchy:
    # primary.dump()

    return {'FINISHED'}
