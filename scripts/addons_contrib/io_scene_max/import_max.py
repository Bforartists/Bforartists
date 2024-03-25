# SPDX-FileCopyrightText: 2023-2024 Sebastian Schrand
#                         2017-2022 Jens M. Plonka
#                         2005-2018 Philippe Lagadec
#
# SPDX-License-Identifier: GPL-2.0-or-later

# Import is based on using information from `olefile` IO source-code
# and the FreeCAD Autodesk 3DS Max importer ImportMAX.
#
# `olefile` (formerly OleFileIO_PL) is copyright Philippe Lagadec.
# (https://www.decalage.info)
#
# ImportMAX is copyright Jens M. Plonka.
# (https://www.github.com/jmplonka/Importer3D)

import io
import os
import re
import sys
import bpy
import math
import zlib
import array
import struct
import mathutils

from bpy_extras.node_shader_utils import PrincipledBSDFWrapper


###################
# DATA STRUCTURES #
###################

MAGIC = b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1'
WORD_CLSID = "00020900-0000-0000-C000-000000000046"

MIN_FILE_SIZE = 1536
UNKNOWN_SIZE = 0x7FFFFFFF
MAXFILE_SIZE = 0x7FFFFFFFFFFFFFFF
MAXREGSECT = 0xFFFFFFFA  # (-6) maximum SECT
DIFSECT = 0xFFFFFFFC  # (-4) denotes a DIFAT sector in a FAT
FATSECT = 0xFFFFFFFD  # (-3) denotes a FAT sector in a FAT
ENDOFCHAIN = 0xFFFFFFFE  # (-2) end of a virtual stream chain
FREESECT = 0xFFFFFFFF  # (-1) unallocated sector
MAX_STREAM = 2  # element is a stream object
ROOT_STORE = 5  # element is a root storage

TYP_NAME = 0x0962
INVALID_NAME = re.compile('^[0-9].*')
UNPACK_BOX_DATA = struct.Struct('<HIHHBff').unpack_from  # Index, int, 2short, byte, 2float

FLOAT_POINT = 0x71F11549498702E7  # Float Wire
MATRIX_POS = 0xFFEE238A118F7E02  # Position XYZ
MATRIX_ROT = 0x3A90416731381913  # Rotation Wire
MATRIX_SCL = 0xFEEE238B118F7C01  # Scale XYZ
EDIT_MESH = 0x00000000E44F10B3  # Editable Mesh
EDIT_POLY = 0x192F60981BF8338D  # Editable Poly
CORO_MTL = 0x448931dd70be6506  # CoronaMtl
ARCH_MTL = 0x4A16365470B05735  # ArchMtl
VRAY_MTL = 0x7034695C37BF3F2F  # VRayMtl

SKIPPABLE = {
    0x0000000000001002: 'Camera',
    0x0000000000001011: 'Omni',
    0x0000000000001013: 'Free Direct',
    0x0000000000001020: 'Camera Target',
    0x0000000000001040: 'Line',
    0x0000000000001065: 'Rectangle',
    0x0000000000001097: 'Ellipse',
    0x0000000000001999: 'Circle',
    0x0000000000002013: 'Point',
    0x0000000000009125: 'Biped Object',
    0x0000000000876234: 'Dummy',
    0x05622B0D69011E82: 'Compass',
    0x12A822FB76A11646: 'CV Surface',
    0x1EB3430074F93B07: 'Particle View',
    0x2ECCA84028BF6E8D: 'Bone',
    0x3BDB0E0C628140F6: 'VRayPlane',
    0x4E9B599047DB14EF: 'Slider',
    0x522E47057BF61478: 'Sky',
    0x5FD602DF3C5575A1: 'VRayLight',
    0x77566F65081F1DFC: 'Plane',
}

CONFIG = []
CLS_DATA = []
DLL_DIR_LIST = []
CLS_DIR3_LIST = []
VID_PST_QUE = []
SCENE_LIST = []


def get_valid_name(name):
    if (INVALID_NAME.match(name)):
        return "_%s" % (name.encode('utf8'))
    return "%s" % (name.encode('utf8'))


def i8(data):
    return data if data.__class__ is int else data[0]


def i16(data, offset=0):
    return struct.unpack("<H", data[offset:offset + 2])[0]


def i32(data, offset=0):
    return struct.unpack("<I", data[offset:offset + 4])[0]


def get_byte(data, offset=0):
    size = offset + 1
    value = struct.unpack('<B', data[offset:size])[0]
    return value, size


def get_short(data, offset=0):
    size = offset + 2
    value = struct.unpack('<H', data[offset:size])[0]
    return value, size


def get_long(data, offset=0):
    size = offset + 4
    value = struct.unpack('<I', data[offset:size])[0]
    return value, size


def get_float(data, offset=0):
    size = offset + 4
    value = struct.unpack('<f', data[offset:size])[0]
    return value, size


def get_bytes(data, offset=0, count=1):
    size = offset + count
    values = struct.unpack('<' + 'B' * count, data[offset:size])
    return values, size


def get_shorts(data, offset=0, count=1):
    size = offset + count * 2
    values = struct.unpack('<' + 'H' * count, data[offset:size])
    return values, size


def get_longs(data, offset=0, count=1):
    size = offset + count * 4
    values = struct.unpack('<' + 'I' * count, data[offset:size])
    return values, size


def get_floats(data, offset=0, count=1):
    size = offset + count * 4
    values = struct.unpack('<' + 'f' * count, data[offset:size])
    return values, size


def _clsid(clsid):
    """Converts a CLSID to a readable string."""
    assert len(clsid) == 16
    if not clsid.strip(b"\0"):
        return ""
    return (("%08X-%04X-%04X-%02X%02X-" + "%02X" * 6) %
            ((i32(clsid, 0), i16(clsid, 4), i16(clsid, 6)) +
            tuple(map(i8, clsid[8:16]))))


###############
# DATA IMPORT #
###############

def is_maxfile(filename):
    """Test if file is a MAX OLE2 container."""
    if hasattr(filename, 'read'):
        header = filename.read(len(MAGIC))
        filename.seek(0)
    elif isinstance(filename, bytes) and len(filename) >= MIN_FILE_SIZE:
        header = filename[:len(MAGIC)]
    else:
        with open(filename, 'rb') as fp:
            header = fp.read(len(MAGIC))
    if header == MAGIC:
        return True
    else:
        return False


class MaxStream(io.BytesIO):
    """Returns an instance of the BytesIO class as read-only file object."""

    def __init__(self, fp, sect, size, offset, sectorsize, fat, filesize):
        if size == UNKNOWN_SIZE:
            size = len(fat) * sectorsize
        nb_sectors = (size + (sectorsize - 1)) // sectorsize

        data = []
        for i in range(nb_sectors):
            try:
                fp.seek(offset + sectorsize * sect)
            except:
                break
            sector_data = fp.read(sectorsize)
            data.append(sector_data)
            try:
                sect = fat[sect] & FREESECT
            except IndexError:
                break
        data = b"".join(data)
        if len(data) >= size:
            data = data[:size]
            self.size = size
        else:
            self.size = len(data)
        io.BytesIO.__init__(self, data)


class MaxFileDirEntry:
    """Directory Entry for a stream or storage."""
    STRUCT_DIRENTRY = '<64sHBBIII16sIQQIII'
    DIRENTRY_SIZE = 128
    assert struct.calcsize(STRUCT_DIRENTRY) == DIRENTRY_SIZE

    def __init__(self, entry, sid, maxfile):
        self.sid = sid
        self.maxfile = maxfile
        self.kids = []
        self.kids_dict = {}
        self.used = False
        (
            self.name_raw,
            self.namelength,
            self.entry_type,
            self.color,
            self.sid_left,
            self.sid_right,
            self.sid_child,
            clsid,
            self.dwUserFlags,
            self.createTime,
            self.modifyTime,
            self.isectStart,
            self.sizeLow,
            self.sizeHigh
        ) = struct.unpack(MaxFileDirEntry.STRUCT_DIRENTRY, entry)

        if self.namelength > 64:
            self.namelength = 64
        self.name_utf16 = self.name_raw[:(self.namelength - 2)]
        self.name = maxfile._decode_utf16_str(self.name_utf16)
        # print('DirEntry SID=%d: %s' % (self.sid, repr(self.name)))
        if maxfile.sectorsize == 512:
            self.size = self.sizeLow
        else:
            self.size = self.sizeLow + (int(self.sizeHigh) << 32)
        self.clsid = _clsid(clsid)
        self.is_minifat = False
        if self.entry_type in (ROOT_STORE, MAX_STREAM) and self.size > 0:
            if self.size < maxfile.minisectorcutoff \
                    and self.entry_type == MAX_STREAM:  # only streams can be in MiniFAT
                self.is_minifat = True
            else:
                self.is_minifat = False
            maxfile._check_duplicate_stream(self.isectStart, self.is_minifat)
        self.sect_chain = None

    def build_sect_chain(self, maxfile):
        if self.sect_chain:
            return
        if self.entry_type not in (ROOT_STORE, MAX_STREAM) or self.size == 0:
            return
        self.sect_chain = list()
        if self.is_minifat and not maxfile.minifat:
            maxfile.loadminifat()
        next_sect = self.isectStart
        while next_sect != ENDOFCHAIN:
            self.sect_chain.append(next_sect)
            if self.is_minifat:
                next_sect = maxfile.minifat[next_sect]
            else:
                next_sect = maxfile.fat[next_sect]

    def build_storage_tree(self):
        if self.sid_child != FREESECT:
            self.append_kids(self.sid_child)
            self.kids.sort()

    def append_kids(self, child_sid):
        if child_sid == FREESECT:
            return
        else:
            child = self.maxfile._load_direntry(child_sid)
            if child.used:
                return
            child.used = True
            self.append_kids(child.sid_left)
            name_lower = child.name.lower()
            self.kids.append(child)
            self.kids_dict[name_lower] = child
            self.append_kids(child.sid_right)
            child.build_storage_tree()

    def __eq__(self, other):
        return self.name == other.name

    def __lt__(self, other):
        return self.name < other.name

    def __ne__(self, other):
        return not self.__eq__(other)

    def __le__(self, other):
        return self.__eq__(other) or self.__lt__(other)


class ImportMaxFile:
    """Representing an interface for importing .max files."""

    def __init__(self, filename=None):
        self._filesize = None
        self.byte_order = None
        self.directory_fp = None
        self.direntries = None
        self.dll_version = None
        self.fat = None
        self.first_difat_sector = None
        self.first_dir_sector = None
        self.first_mini_fat_sector = None
        self.fp = None
        self.header_clsid = None
        self.header_signature = None
        self.mini_sector_shift = None
        self.mini_sector_size = None
        self.mini_stream_cutoff_size = None
        self.minifat = None
        self.minifatsect = None
        self.minisectorcutoff = None
        self.minisectorsize = None
        self.ministream = None
        self.minor_version = None
        self.nb_sect = None
        self.num_difat_sectors = None
        self.num_dir_sectors = None
        self.num_fat_sectors = None
        self.num_mini_fat_sectors = None
        self.reserved1 = None
        self.reserved2 = None
        self.root = None
        self.sector_shift = None
        self.sector_size = None
        self.transaction_signature_number = None
        if filename:
            self.open(filename)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _decode_utf16_str(self, utf16_str, errors='replace'):
        unicode_str = utf16_str.decode('UTF-16LE', errors)
        return unicode_str

    def open(self, filename):
        if hasattr(filename, 'read'):
            self.fp = filename
        elif isinstance(filename, bytes) and len(filename) >= MIN_FILE_SIZE:
            self.fp = io.BytesIO(filename)
        else:
            self.fp = open(filename, 'rb')
        filesize = 0
        self.fp.seek(0, os.SEEK_END)
        try:
            filesize = self.fp.tell()
        finally:
            self.fp.seek(0)
        self._filesize = filesize
        self._used_streams_fat = []
        self._used_streams_minifat = []
        header = self.fp.read(512)
        fmt_header = '<8s16sHHHHHHLLLLLLLLLL'
        header_size = struct.calcsize(fmt_header)
        header1 = header[:header_size]
        (
            self.header_signature,
            self.header_clsid,
            self.minor_version,
            self.dll_version,
            self.byte_order,
            self.sector_shift,
            self.mini_sector_shift,
            self.reserved1,
            self.reserved2,
            self.num_dir_sectors,
            self.num_fat_sectors,
            self.first_dir_sector,
            self.transaction_signature_number,
            self.mini_stream_cutoff_size,
            self.first_mini_fat_sector,
            self.num_mini_fat_sectors,
            self.first_difat_sector,
            self.num_difat_sectors
        ) = struct.unpack(fmt_header, header1)

        self.sector_size = 2**self.sector_shift
        self.mini_sector_size = 2**self.mini_sector_shift
        if self.mini_stream_cutoff_size != 0x1000:
            self.mini_stream_cutoff_size = 0x1000
        self.nb_sect = ((filesize + self.sector_size - 1) // self.sector_size) - 1

        # file clsid
        self.header_clsid = _clsid(header[8:24])
        self.sectorsize = self.sector_size  # i16(header, 30)
        self.minisectorsize = self.mini_sector_size   # i16(header, 32)
        self.minisectorcutoff = self.mini_stream_cutoff_size  # i32(header, 56)
        self._check_duplicate_stream(self.first_dir_sector)
        if self.num_mini_fat_sectors:
            self._check_duplicate_stream(self.first_mini_fat_sector)
        if self.num_difat_sectors:
            self._check_duplicate_stream(self.first_difat_sector)

        # Load file allocation tables
        self.loadfat(header)
        self.loaddirectory(self.first_dir_sector)
        self.minifatsect = self.first_mini_fat_sector

    def close(self):
        self.fp.close()

    def _check_duplicate_stream(self, first_sect, minifat=False):
        if minifat:
            used_streams = self._used_streams_minifat
        else:
            if first_sect in (DIFSECT, FATSECT, ENDOFCHAIN, FREESECT):
                return
            used_streams = self._used_streams_fat
        if first_sect in used_streams:
            pass
        else:
            used_streams.append(first_sect)

    def sector_array(self, sect):
        ary = array.array('I', sect)
        if sys.byteorder == 'big':
            ary.byteswap()
        return ary

    def loadfat_sect(self, sect):
        if isinstance(sect, array.array):
            fat1 = sect
        else:
            fat1 = self.sector_array(sect)
        isect = None
        for isect in fat1:
            isect = isect & FREESECT
            if isect == ENDOFCHAIN or isect == FREESECT:
                break
            sector = self.getsect(isect)
            nextfat = self.sector_array(sector)
            self.fat = self.fat + nextfat
        return isect

    def loadfat(self, header):
        sect = header[76:512]
        self.fat = array.array('I')
        self.loadfat_sect(sect)
        if self.num_difat_sectors != 0:
            nb_difat_sectors = (self.sectorsize // 4) - 1
            nb_difat = (self.num_fat_sectors - 109 + nb_difat_sectors - 1) // nb_difat_sectors
            isect_difat = self.first_difat_sector
            for i in range(nb_difat):
                sector_difat = self.getsect(isect_difat)
                difat = self.sector_array(sector_difat)
                self.loadfat_sect(difat[:nb_difat_sectors])
                isect_difat = difat[nb_difat_sectors]
        if len(self.fat) > self.nb_sect:
            self.fat = self.fat[:self.nb_sect]

    def loadminifat(self):
        stream_size = self.num_mini_fat_sectors * self.sector_size
        nb_minisectors = (self.root.size + self.mini_sector_size - 1) // self.mini_sector_size
        used_size = nb_minisectors * 4
        sect = self._open(self.minifatsect, stream_size, force_FAT=True).read()
        self.minifat = self.sector_array(sect)
        self.minifat = self.minifat[:nb_minisectors]

    def getsect(self, sect):
        try:
            self.fp.seek(self.sectorsize * (sect + 1))
        except:
            print('IndexError: Sector index out of range')
        sector = self.fp.read(self.sectorsize)
        return sector

    def loaddirectory(self, sect):
        self.directory_fp = self._open(sect, force_FAT=True)
        max_entries = self.directory_fp.size // 128
        self.direntries = [None] * max_entries
        root_entry = self._load_direntry(0)
        self.root = self.direntries[0]
        self.root.build_storage_tree()

    def _load_direntry(self, sid):
        if self.direntries[sid] is not None:
            return self.direntries[sid]
        self.directory_fp.seek(sid * 128)
        entry = self.directory_fp.read(128)
        self.direntries[sid] = MaxFileDirEntry(entry, sid, self)
        return self.direntries[sid]

    def _open(self, start, size=UNKNOWN_SIZE, force_FAT=False):
        if size < self.minisectorcutoff and not force_FAT:
            if not self.ministream:
                self.loadminifat()
                size_ministream = self.root.size
                self.ministream = self._open(self.root.isectStart,
                                             size_ministream, force_FAT=True)
            return MaxStream(fp=self.ministream, sect=start, size=size,
                             offset=0, sectorsize=self.minisectorsize,
                             fat=self.minifat, filesize=self.ministream.size)
        else:
            return MaxStream(fp=self.fp, sect=start, size=size,
                             offset=self.sectorsize, sectorsize=self.sectorsize,
                             fat=self.fat, filesize=self._filesize)

    def _find(self, filename):
        if isinstance(filename, str):
            filename = filename.split('/')
        node = self.root
        for name in filename:
            for kid in node.kids:
                if kid.name.lower() == name.lower():
                    break
            node = kid
        return node.sid

    def openstream(self, filename):
        sid = self._find(filename)
        entry = self.direntries[sid]
        return self._open(entry.isectStart, entry.size)


###################
# DATA PROCESSING #
###################

class MaxChunk():
    """Representing a chunk of a .max file."""

    def __init__(self, types, size, level, number):
        self.number = number
        self.types = types
        self.level = level
        self.parent = None
        self.previous = None
        self.next = None
        self.size = size
        self.data = None

    def __str__(self):
        return "%s[%4x]%04X:%s" % ("" * self.level, self.number, self.types, self.data)


class ByteArrayChunk(MaxChunk):
    """A byte array of a .max chunk."""

    def __init__(self, types, data, level, number):
        MaxChunk.__init__(self, types, data, level, number)

    def set(self, data, fmt, start, end):
        try:
            self.data = struct.unpack(fmt, data[start:end])
        except Exception as exc:
            self.data = data
            # print('StructError:', exc, name)

    def set_string(self, data):
        try:
            self.data = data.decode('UTF-16LE')
        except:
            self.data = data

    def set_data(self, data):
        if (self.types in [0x0340, 0x4001, 0x0456, 0x0962]):
            self.set_string(data)
        elif (self.types in [0x2034, 0x2035]):
            self.set(data, '<' + 'I' * int(len(data) / 4), 0, len(data))
        elif (self.types in [0x2501, 0x2503, 0x2504, 0x2505, 0x2511]):
            self.set(data, '<' + 'f' * int(len(data) / 4), 0, len(data))
        elif (self.types == 0x2510):
            self.set(data, '<' + 'f' * int(len(data) / 4 - 1) + 'I', 0, len(data))
        elif (self.types == 0x0100):
            self.set(data, '<f', 0, len(data))
        else:
            self.data = data


class ClassIDChunk(ByteArrayChunk):
    """The class ID subchunk of a .max chunk."""

    def __init__(self, types, data, level, number):
        MaxChunk.__init__(self, types, data, level, number)
        self.dll = None

    def set_data(self, data):
        if (self.types == 0x2042):
            self.set_string(data)  # ClsName
        elif (self.types == 0x2060):
            self.set(data, '<IQI', 0, 16)  # DllIndex, ID, SuperID
        else:
            self.data = ":".join("%02x" % (c) for c in data)


class DirectoryChunk(ByteArrayChunk):
    """The directory chunk of a .max file."""

    def __init__(self, types, data, level, number):
        MaxChunk.__init__(self, types, data, level, number)

    def set_data(self, data):
        if (self.types == 0x2039):
            self.set_string(data)
        elif (self.types == 0x2037):
            self.set_string(data)


class ContainerChunk(MaxChunk):
    """A container chunk in a .max file wich includes byte arrays."""

    def __init__(self, types, data, level, number, primReader=ByteArrayChunk):
        MaxChunk.__init__(self, types, data, level, number)
        self.primReader = primReader

    def __str__(self):
        return "%s[%4x]%04X" % ("" * self.level, self.number, self.types)

    def get_first(self, types):
        for child in self.children:
            if (child.types == types):
                return child
        return None

    def set_data(self, data):
        previous = None
        next = None
        reader = ChunkReader()
        self.children = reader.get_chunks(data, self.level + 1, ContainerChunk, self.primReader)


class SceneChunk(ContainerChunk):
    """The scene chunk of a .max file wich includes the relevant data for blender."""

    def __init__(self, types, data, level, number, primReader=ByteArrayChunk):
        MaxChunk.__init__(self, types, data, level, number)
        self.primReader = primReader
        self.matrix = None

    def __str__(self):
        return "%s[%4x]%s" % ("" * self.level, self.number, get_cls_name(self))

    def set_data(self, data):
        previous = None
        next = None
        # print('Scene', "%s\n" %(self))
        reader = ChunkReader()
        self.children = reader.get_chunks(data, self.level + 1,
                                          SceneChunk, ByteArrayChunk)


class ChunkReader():
    """The chunk reader class for decoding the byte arrays."""

    def __init__(self, name=None):
        self.name = name

    def get_chunks(self, data, level, conReader, primReader):
        chunks = []
        offset = 0
        if (level == 0):
            short, step = get_short(data, 0)
            long, step = get_long(data, step)
            if (short == 0x8B1F):
                short, step = get_long(data, step)
                if (short in (0xB000000, 0xA040000)):
                    data = zlib.decompress(data, zlib.MAX_WBITS | 32)
            print("  reading '%s'..." % self.name, len(data))
        while offset < len(data):
            old = offset
            offset, chunk = self.get_next_chunk(data, offset, level,
                                                len(chunks), conReader, primReader)
            chunks.append(chunk)
        return chunks

    def get_next_chunk(self, data, offset, level, number, conReader, primReader):
        header = 6
        typ, siz, = struct.unpack("<Hi", data[offset:offset + header])
        chunksize = siz & UNKNOWN_SIZE
        if (siz == 0):
            siz, = struct.unpack("<q", data[offset + header:offset + header + 8])
            header += 8
            chunksize = siz & MAXFILE_SIZE
        if (siz < 0):
            chunk = conReader(typ, chunksize, level, number, primReader)
        else:
            chunk = primReader(typ, chunksize, level, number)
        chunkdata = data[offset + header:offset + chunksize]
        chunk.set_data(chunkdata)
        return offset + chunksize, chunk


class Point3d():
    """Representing a three dimensional vector plus pointflag."""

    def __init__(self):
        self.points = None
        self.flags = 0
        self.fH = 0
        self.f1 = 0
        self.f2 = 0
        self.fA = []

    def __str__(self):
        return "[%s]-%X,%X,%X,[%s]" % ('/'.join("%d" % p for p in self.points),
                                       self.fH, self.f1, self.f2,
                                       ','.join("%X" % f for f in self.fA))


class Material():
    """Representing a material chunk of a scene chunk."""

    def __init__(self):
        self.data = {}

    def set(self, name, value):
        self.data[name] = value

    def get(self, name, default=None):
        value = None
        if (name in self.data):
            value = self.data[name]
        if (value is None):
            return default
        return value


def get_node(index):
    if isinstance(index, tuple):
        index = index[0]
    global SCENE_LIST
    if (index < len(SCENE_LIST[0].children)):
        return SCENE_LIST[0].children[index]
    return None


def get_node_parent(node):
    parent = None
    if (node):
        chunk = node.get_first(0x0960)
        if (chunk is not None):
            idx, offset = get_long(chunk.data, 0)
            parent = get_node(idx)
    return parent


def get_node_name(node):
    if (node):
        name = node.get_first(TYP_NAME)
        if (name):
            return name.data
    return None


def get_class(chunk):
    global CLS_DIR3_LIST
    if (chunk.types < len(CLS_DIR3_LIST)):
        return CLS_DIR3_LIST[chunk.types]
    return None


def get_dll(chunk):
    global DLL_DIR_LIST
    idx = chunk.get_first(0x2060).data[0]
    if (idx < len(DLL_DIR_LIST)):
        return DLL_DIR_LIST[idx]
    return None


def get_guid(chunk):
    clid = get_class(chunk)
    if (clid):
        return clid.get_first(0x2060).data[1]
    return chunk.types


def get_super_id(chunk):
    clid = get_class(chunk)
    if (clid):
        return clid.get_first(0x2060).data[2]
    return None


def get_cls_name(chunk):
    clid = get_class(chunk)
    if (clid):
        cls_name = clid.get_first(0x2042).data
        try:
            return "'%s'" % (cls_name)
        except:
            return "'%r'" % (cls_name)
    return u"%04X" % (chunk.types)


def get_references(chunk):
    refs = chunk.get_first(0x2034)
    if (refs):
        references = [get_node(idx) for idx in refs.data]
    return references


def get_reference(chunk):
    references = {}
    refs = chunk.get_first(0x2035)
    if (refs):
        offset = 1
        while offset < len(refs.data):
            key = refs.data[offset]
            offset += 1
            idx = refs.data[offset]
            offset += 1
            references[key] = get_node(idx)
    return references


def read_chunks(maxfile, name, filename, conReader=ContainerChunk, primReader=ByteArrayChunk):
    with maxfile.openstream(name) as file:
        scene = file.read()
        reader = ChunkReader(name)
        return reader.get_chunks(scene, 0, conReader, primReader)


def read_class_data(maxfile, filename):
    global CLS_DATA
    CLS_DATA = read_chunks(maxfile, 'ClassData', filename + '.ClsDat.bin')


def read_class_directory(maxfile, filename):
    global CLS_DIR3_LIST
    try:
        CLS_DIR3_LIST = read_chunks(maxfile, 'ClassDirectory3',
                                    filename + '.ClsDir3.bin', ContainerChunk, ClassIDChunk)
    except:
        CLS_DIR3_LIST = read_chunks(maxfile, 'ClassDirectory',
                                    filename + '.ClsDir.bin', ContainerChunk, ClassIDChunk)
    for clsdir in CLS_DIR3_LIST:
        clsdir.dll = get_dll(clsdir)


def read_config(maxfile, filename):
    global CONFIG
    CONFIG = read_chunks(maxfile, 'Config', filename + '.Cnf.bin')


def read_directory(maxfile, filename):
    global DLL_DIR_LIST
    DLL_DIR_LIST = read_chunks(maxfile, 'DllDirectory',
                               filename + '.DllDir.bin', ContainerChunk, DirectoryChunk)


def read_video_postqueue(maxfile, filename):
    global VID_PST_QUE
    VID_PST_QUE = read_chunks(maxfile, 'VideoPostQueue', filename + '.VidPstQue.bin')


def get_point(floatval, default=0.0):
    uid = get_guid(floatval)
    if (uid == 0x2007):  # Bezier-Float
        flv = floatval.get_first(0x7127)
        if (flv):
            try:
                return flv.get_first(0x2501).data[0]
            except:
                print("SyntaxError: %s - assuming 0.0!\n" % (floatval))
        return default
    if (uid == FLOAT_POINT):  # Float Wire
        flv = get_references(floatval)[0]
        return get_point(flv)
    else:
        return default


def get_point_3d(chunk, default=0.0):
    floats = []
    if (chunk):
        refs = get_references(chunk)
        for fl in refs:
            flt = get_point(fl, default)
            if (fl is not None):
                floats.append(flt)
    return floats


def get_position(pos):
    position = None
    mtx = mathutils.Matrix.Identity(4)
    if (pos):
        uid = get_guid(pos)
        if (uid == MATRIX_POS):  # Position XYZ
            position = get_point_3d(pos)
        elif (uid == 0x442312):  # TCB Position
            position = pos.get_first(0x2503).data
        elif (uid == 0x2008):  # Bezier Position
            position = pos.get_first(0x2503).data
        if (position):
            mtx = mathutils.Matrix.Translation(position)
    return mtx


def get_rotation(pos):
    rotation = None
    mtx = mathutils.Matrix.Identity(4)
    if (pos):
        uid = get_guid(pos)
        if (uid == 0x2012):  # Euler XYZ
            rot = get_point_3d(pos)
            rotation = mathutils.Euler((rot[2], rot[1], rot[0])).to_quaternion()
        elif (uid == 0x442313):  # TCB Rotation
            rot = pos.get_first(0x2504).data
            rotation = mathutils.Quaternion((rot[0], rot[1], rot[2], rot[3]))
        elif (uid == 0x4B4B1003):  # Rotation List
            refs = get_references(pos)
            if (len(refs) > 3):
                return get_rotation(refs[0])
        elif (uid == MATRIX_ROT):  # Rotation Wire
            return get_rotation(get_references(pos)[0])
        if (rotation):
            mtx = mathutils.Matrix.Rotation(rotation.angle, 4, rotation.axis)
    return mtx


def get_scale(pos):
    mtx = mathutils.Matrix.Identity(4)
    if (pos):
        uid = get_guid(pos)
        if (uid == 0x2010):  # Bezier Scale
            scale = pos.get_first(0x2501)
            if (scale is None):
                scale = pos.get_first(0x2505)
            pos = scale.data
        elif (uid == 0x442315):  # TCB Zoom
            scale = pos.get_first(0x2501)
            if (scale is None):
                scale = pos.get_first(0x2505)
            pos = scale.data
        elif (uid == MATRIX_SCL):  # ScaleXYZ
            pos = get_point_3d(pos, 1.0)
        else:
            return mtx
        mtx = mathutils.Matrix.Diagonal(pos[:3]).to_4x4()
    return mtx


def create_matrix(prc):
    mtx = mathutils.Matrix.Identity(4)
    pos = rot = scl = None
    uid = get_guid(prc)
    if (uid == 0x2005):  # Position/Rotation/Scale
        pos = get_position(get_references(prc)[0])
        rot = get_rotation(get_references(prc)[1])
        scl = get_scale(get_references(prc)[2])
    elif (uid == 0x9154):  # BipSlave Control
        biped_sub_anim = get_references(prc)[2]
        refs = get_references(biped_sub_anim)
        scl = get_scale(get_references(refs[1])[0])
        rot = get_rotation(get_references(refs[2])[0])
        pos = get_position(get_references(refs[3])[0])
    if (pos is not None):
        mtx = pos @ mtx
    if (rot is not None):
        mtx = rot @ mtx
    if (scl is not None):
        mtx = scl @ mtx
    return mtx


def get_matrix_mesh_material(node):
    refs = get_reference(node)
    if (refs):
        prs = refs.get(0, None)
        msh = refs.get(1, None)
        mat = refs.get(3, None)
        lyr = refs.get(6, None)
    else:
        refs = get_references(node)
        prs = refs[0]
        msh = refs[1]
        mat = refs[3]
        lyr = None
        if (len(refs) > 6):
            lyr = refs[6]
    return prs, msh, mat, lyr


def get_property(properties, idx):
    for child in properties.children:
        if (child.types & 0x100E):
            if (get_short(child.data, 0)[0] == idx):
                return child
    return None


def get_color(colors, idx):
    prop = get_property(colors, idx)
    if (prop is not None):
        siz = len(prop.data) - 12
        col, offset = get_floats(prop.data, siz, 3)
        return (col[0], col[1], col[2])
    return None


def get_value(colors, idx):
    prop = get_property(colors, idx)
    if (prop is not None):
        siz = len(prop.data) - 4
        val, offset = get_float(prop.data, siz)
        return val
    return None


def get_parameter(colors, fmt):
    if (fmt == 0x1):
        siz = len(colors.data) - 12
        para, offset = get_floats(colors.data, siz, 3)
    else:
        siz = len(colors.data) - 4
        para, offset = get_float(colors.data, siz)
    return para


def get_standard_material(refs):
    material = None
    try:
        if (len(refs) > 2):
            colors = refs[2]
            parameters = get_references(colors)[0]
            material = Material()
            material.set('ambient', get_color(parameters, 0x00))
            material.set('diffuse', get_color(parameters, 0x01))
            material.set('specular', get_color(parameters, 0x02))
            material.set('emissive', get_color(parameters, 0x08))
            material.set('shinines', get_value(parameters, 0x0B))
            parablock = refs[4]  # ParameterBlock2
            material.set('glossines', get_value(parablock, 0x02))
            material.set('metallic', get_value(parablock, 0x05))
    except:
        pass
    return material


def get_vray_material(vry):
    material = Material()
    try:
        material.set('diffuse', get_color(vry, 0x01))
        material.set('specular', get_color(vry, 0x02))
        material.set('shinines', get_value(vry, 0x03))
        material.set('refraction', get_value(vry, 0x09))
        material.set('emissive', get_color(vry, 0x17))
        material.set('glossines', get_value(vry, 0x18))
        material.set('metallic', get_value(vry, 0x19))
    except:
        pass
    return material


def get_corona_material(mtl):
    material = Material()
    try:
        cor = mtl.children
        material.set('diffuse', get_parameter(cor[3], 0x1))
        material.set('specular', get_parameter(cor[4], 0x1))
        material.set('emissive', get_parameter(cor[8], 0x1))
        material.set('glossines', get_parameter(cor[9], 0x2))
    except:
        pass
    return material


def get_arch_material(ad):
    material = Material()
    try:
        material.set('diffuse', get_color(ad, 0x1A))
        material.set('specular', get_color(ad, 0x05))
        material.set('shinines', get_value(ad, 0x0B))
    except:
        pass
    return material


def adjust_material(obj, mat):
    material = None
    if (mat is not None):
        uid = get_guid(mat)
        if (uid == 0x0002):  # Standard
            refs = get_references(mat)
            material = get_standard_material(refs)
        elif (uid == 0x0200):  # Multi/Sub-Object
            refs = get_references(mat)
            material = adjust_material(obj, refs[-1])
        elif (uid == VRAY_MTL):  # VRayMtl
            refs = get_reference(mat)
            material = get_vray_material(refs[1])
        elif (uid == CORO_MTL):  # CoronaMtl
            refs = get_references(mat)
            material = get_corona_material(refs[0])
        elif (uid == ARCH_MTL):  # Arch
            refs = get_references(mat)
            material = get_arch_material(refs[0])
        if (obj is not None) and (material is not None):
            objMaterial = bpy.data.materials.new(get_cls_name(mat))
            obj.data.materials.append(objMaterial)
            matShader = PrincipledBSDFWrapper(objMaterial, is_readonly=False, use_nodes=True)
            matShader.base_color = objMaterial.diffuse_color[:3] = material.get('diffuse', (0.8, 0.8, 0.8))
            matShader.specular_tint = objMaterial.specular_color[:3] = material.get('specular', (1, 1, 1))
            matShader.specular = objMaterial.specular_intensity = material.get('glossines', 0.5)
            matShader.roughness = objMaterial.roughness = 1.0 - material.get('shinines', 0.6)
            matShader.metallic = objMaterial.metallic = material.get('metallic', 0)
            matShader.emission_color = material.get('emissive', (0, 0, 0))
            matShader.ior = material.get('refraction', 1.45)


def adjust_matrix(obj, node):
    mtx = create_matrix(node).flatten()
    plc = mathutils.Matrix(*mtx)
    obj.matrix_world = plc
    return plc


def create_shape(context, pts, indices, node, key, mtx, mat, umt):
    name = node.get_first(TYP_NAME).data
    shape = bpy.data.meshes.new(name)
    if (key is not None):
        name = "%s_%d" % (name, key)
    data = []
    if (pts):
        loopstart = []
        looplines = loop = 0
        nb_faces = len(indices)
        for fid in range(nb_faces):
            polyface = indices[fid]
            looplines += len(polyface)
        shape.vertices.add(len(pts) // 3)
        shape.loops.add(looplines)
        shape.polygons.add(nb_faces)
        shape.vertices.foreach_set("co", pts)
        for vtx in indices:
            loopstart.append(loop)
            data.extend(vtx)
            loop += len(vtx)
        shape.polygons.foreach_set("loop_start", loopstart)
        shape.loops.foreach_set("vertex_index", data)

    if (len(data) > 0):
        shape.validate()
        shape.update()
        obj = bpy.data.objects.new(name, shape)
        context.view_layer.active_layer_collection.collection.objects.link(obj)
        obj.matrix_world = mtx
        if (umt):
            adjust_material(obj, mat)
        return True
    return True


def calc_point(data):
    points = []
    long, offset = get_long(data, 0)
    while (offset < len(data)):
        val, offset = get_long(data, offset)
        flt, offset = get_floats(data, offset, 3)
        points.extend(flt)
    return points


def calc_point_float(data):
    points = []
    long, offset = get_long(data, 0)
    while (offset < len(data)):
        flt, offset = get_floats(data, offset, 3)
        points.extend(flt)
    return points


def calc_point_3d(chunk):
    data = chunk.data
    count, offset = get_long(data, 0)
    pointlist = []
    try:
        while (offset < len(data)):
            pt = Point3d()
            long, offset = get_long(data, offset)
            pt.points, offset = get_longs(data, offset, long)
            pt.flags, offset = get_short(data, offset)
            if ((pt.flags & 0x01) != 0):
                pt.f1, offset = get_long(data, offset)
            if ((pt.flags & 0x08) != 0):
                pt.fH, offset = get_short(data, offset)
            if ((pt.flags & 0x10) != 0):
                pt.f2, offset = get_long(data, offset)
            if ((pt.flags & 0x20) != 0):
                pt.fA, offset = get_longs(data, offset, 2 * (long - 3))
            if (len(pt.points) > 0):
                pointlist.append(pt)
    except Exception as exc:
        print('ArrayError:\n', "%s: offset = %d\n" % (exc, offset))
    return pointlist


def get_point_array(values):
    verts = []
    if len(values) >= 4:
        count, offset = get_long(values, 0)
        while (count > 0):
            floats, offset = get_floats(values, offset, 3)
            verts.extend(floats)
            count -= 1
    return verts


def get_poly_4p(points):
    vertex = {}
    for point in points:
        ngon = point.points
        key = point.fH
        if (key not in vertex):
            vertex[key] = []
        vertex[key].append(ngon)
    return vertex


def get_poly_5p(data):
    count, offset = get_long(data, 0)
    ngons = []
    while count > 0:
        pt, offset = get_longs(data, offset, 3)
        offset += 8
        ngons.append(pt)
        count -= 1
    return ngons


def get_poly_6p(data):
    count, offset = get_long(data, 0)
    polylist = []
    while (offset < len(data)):
        long, offset = get_longs(data, offset, 6)
        i = 5
        while ((i > 3) and (long[i] < 0)):
            i -= 1
            if (i > 2):
                polylist.append(long[1:i])
    return polylist


def get_poly_data(chunk):
    offset = 0
    polylist = []
    data = chunk.data
    while (offset < len(data)):
        count, offset = get_long(data, offset)
        points, offset = get_longs(data, offset, count)
        polylist.append(points)
    return polylist


def create_editable_poly(context, node, msh, mat, mtx, umt, uvm):
    coords = point4i = point6i = pointNi = None
    poly = msh.get_first(0x08FE)
    created = False
    lidx = []
    lcrd = []
    lply = []
    if (poly):
        for child in poly.children:
            if (child.types == 0x0100):
                coords = calc_point(child.data)
            elif (child.types == 0x0108):
                point6i = child.data
            elif (child.types == 0x011A):
                point4i = calc_point_3d(child)
            elif (child.types == 0x0310):
                pointNi = child.data
            elif (child.types == 0x0124):
                lidx.append(get_long(child.data, 0)[0])
            elif (child.types == 0x0128):
                lcrd.append(calc_point_float(child.data))
            elif (child.types == 0x012B):
                lply.append(get_poly_data(child))
        if (point4i is not None):
            vertex = get_poly_4p(point4i)
            if (len(vertex) > 0):
                for key, ngons in vertex.items():
                    created |= create_shape(context, coords, ngons,
                                            node, key, mtx, mat, umt)
            else:
                created = True
        elif (point6i is not None):
            ngons = get_poly_6p(point6i)
            created = create_shape(context, coords, ngons, node,
                                   None, mtx, mat, umt)
        elif (pointNi is not None):
            ngons = get_poly_5p(pointNi)
            created = create_shape(context, coords, ngons, node,
                                   None, mtx, mat, umt)
        if (uvm and len(lidx) > 0):
            for i in range(len(lidx)):
                created |= create_shape(context, lcrd[i], lply[i],
                                        node, lidx[i], mtx, mat, umt)
    return created


def create_editable_mesh(context, node, msh, mat, mtx, umt):
    poly = msh.get_first(0x08FE)
    created = False
    if (poly):
        vertex_chunk = poly.get_first(0x0914)
        clsid_chunk = poly.get_first(0x0912)
        coords = get_point_array(vertex_chunk.data)
        ngons = get_poly_5p(clsid_chunk.data)
        created = create_shape(context, coords, ngons, node, None, mtx, mat, umt)
    return created


def create_shell(context, node, shell, mat, mtx, umt, uvm):
    refs = get_references(shell)
    msh = refs[-1]
    if (get_cls_name(msh) == "'Editable Poly'"):
        created = create_editable_poly(context, node, msh, mat, mtx, umt, uvm)
    else:
        created = create_editable_mesh(context, node, msh, mat, mtx, umt)
    return created


def create_skipable(context, node, skip):
    name = node.get_first(TYP_NAME).data
    print("    skipping %s '%s'... " % (skip, name))
    return True


def create_mesh(context, node, msh, mtx, mat, umt, uvm):
    created = False
    uid = get_guid(msh)
    msh.geometry = None
    if (uid == EDIT_MESH):
        created = create_editable_mesh(context, node, msh, mat, mtx, umt)
    elif (uid == EDIT_POLY):
        created = create_editable_poly(context, node, msh, mat, mtx, umt, uvm)
    elif (uid in {0x2032, 0x2033}):
        created = create_shell(context, node, msh, mat, mtx, umt, uvm)
    else:
        skip = SKIPPABLE.get(uid)
        if (skip is not None):
            created = create_skipable(context, node, skip)
    return created, uid


def create_object(context, node, mscale, usemat, uvmesh, transform):
    parent = get_node_parent(node)
    node.parent = parent
    prs, msh, mat, lyr = get_matrix_mesh_material(node)
    while ((parent is not None) and (get_guid(parent) != 0x02)):
        parent_mtx = parent.matrix
        if (parent_mtx):
            prs = prs.dot(parent_mtx)
        parent = get_node_parent(parent)
    if (transform):
        mtx = create_matrix(prs) @ mscale
    else:
        mtx = mscale
    created, uid = create_mesh(context, node, msh, mtx, mat, usemat, uvmesh)


def make_scene(context, mscale, usemat, uvmesh, transform, parent):
    for chunk in parent.children:
        if (isinstance(chunk, SceneChunk)):
            if ((get_guid(chunk) == 0x01) and (get_super_id(chunk) == 0x01)):
                try:
                    create_object(context, chunk, mscale, usemat, uvmesh, transform)
                except Exception as exc:
                    print('ImportError:', exc, chunk)


def read_scene(context, maxfile, filename, mscale, usemat, uvmesh, transform):
    global SCENE_LIST
    SCENE_LIST = read_chunks(maxfile, 'Scene', filename + '.Scn.bin', conReader=SceneChunk)
    make_scene(context, mscale, usemat, uvmesh, transform, SCENE_LIST[0])


def read(context, filename, mscale, usemat, uvmesh, transform):
    if (is_maxfile(filename)):
        maxfile = ImportMaxFile(filename)
        read_class_data(maxfile, filename)
        read_config(maxfile, filename)
        read_directory(maxfile, filename)
        read_class_directory(maxfile, filename)
        read_video_postqueue(maxfile, filename)
        read_scene(context, maxfile, filename, mscale, usemat, uvmesh, transform)
    else:
        print("File seems to be no 3D Studio Max file!")


def load(operator, context, files=None, directory="", filepath="", scale_objects=1.0, use_material=True,
         use_uv_mesh=False, use_collection=False, use_apply_matrix=False, global_matrix=None):
    context.window.cursor_set('WAIT')
    mscale = mathutils.Matrix.Scale(scale_objects, 4)
    if global_matrix is not None:
        mscale = global_matrix @ mscale

    default_layer = context.view_layer.active_layer_collection.collection
    for fl in files:
        if use_collection:
            collection = bpy.data.collections.new(fl.name.split(".")[0])
            context.scene.collection.children.link(collection)
            context.view_layer.active_layer_collection = context.view_layer.layer_collection.children[collection.name]
        read(context, os.path.join(directory, fl.name), mscale, usemat=use_material, uvmesh=use_uv_mesh, transform=use_apply_matrix)

    active = context.view_layer.layer_collection.children.get(default_layer.name)
    if active is not None:
        context.view_layer.active_layer_collection = active

    context.window.cursor_set('DEFAULT')

    return {'FINISHED'}
