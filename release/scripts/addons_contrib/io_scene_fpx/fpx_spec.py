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

# <pep8 compliant>

###############################################################################
#234567890123456789012345678901234567890123456789012345678901234567890123456789
#--------1---------2---------3---------4---------5---------6---------7---------


# ##### BEGIN COPYRIGHT BLOCK #####
#
# initial script copyright (c)2013 Alexander Nussbaumer
#
# ##### END COPYRIGHT BLOCK #####

## this is a basic, partial and stripped implementation to read
## [FPT:FPL:FPM] Future Pinball File Format
## http://futurepinball.com
## this python implementation based on the implementation from:
## https://github.com/PinSimDB/fp-addons-sdk.git


if repr(globals()).find("bpy") != -1:
    from io_scene_fpx.cfb_spec import (
            Cfb_RawIO_Reader,
            Cfb_Stream_Reader,
            Cfb_Size_Type,
            Cfb_Extras,
            )
    from io_scene_fpx.lzo_spec import (
            Lzo_Codec,
            )
    from io_scene_fpx.fpx_utils import (
            FpxUtilities,
            )
else:
    from cfb_spec import (
            Cfb_RawIO_Reader,
            Cfb_Stream_Reader,
            Cfb_Size_Type,
            Cfb_Extras,
            )
    from lzo_spec import (
            Lzo_Codec,
            )
    from fpx_utils import (
            FpxUtilities,
            )


from time import (
        struct_time,
        gmtime,
        strftime,
        time,
        )
from struct import (
        pack,
        unpack,
        )
from sys import (
        exc_info,
        )
from os import (
        fstat,
        path,
        makedirs,
        )
from collections import (
        OrderedDict,
        )
from io import (
        SEEK_CUR,
        FileIO,
        )
from codecs import (
        register_error,
        )


class FpxSpec:
    ## TEST_STR = 'START@€@µ@²@³@©@®@¶@ÿ@A@END.bmp'
    ## TEST_RAW = b'START@\x80@\xb5@\xb2@\xb3@\xa9@\xae@\xb6@\xff@A@END.bmp\x00'
    ##
    STRING_FPX_REPLACE = 'use_fpx_replace'
    STRING_ERROR = STRING_FPX_REPLACE
    ##STRING_ERROR = 'replace'
    ##STRING_ERROR = 'ignore'
    ##STRING_ERROR = 'surrogateescape'
    STRING_REPLACE = u'_'

    STRING_ENCODING = 'ascii' # ASCII
    ##STRING_ENCODING = 'cp437' # US
    ##STRING_ENCODING = 'cp858' # Europe + €
    ##STRING_ENCODING = 'cp1252' # WIN EU
    #STRING_ENCODING = 'utf-8'

    WSTRING_ENCODING = 'utf-16-le'

    @staticmethod
    def fpx_replace(exc):
        """ http://www.python.org/dev/peps/pep-0293/ """
        if isinstance(exc, UnicodeEncodeError):
            return ((exc.end-exc.start)*FpxSpec.STRING_REPLACE, exc.end)
        elif isinstance(exc, UnicodeDecodeError):
            return (FpxSpec.STRING_REPLACE, exc.end)
        elif isinstance(exc, UnicodeTranslateError):
            return ((exc.end-exc.start)*FpxSpec.STRING_REPLACE, exc.end)
        else:
            raise TypeError("can't handle {}",format(exc.__name__))

    @staticmethod
    def read_string(raw_io, length):
        """ read a string of a specific length from raw_io """
        buffer = raw_io.read(length)
        if not buffer:
            raise EOFError()
        eol = buffer.find(FpxSpec.STRING_TERMINATION)
        register_error(FpxSpec.STRING_FPX_REPLACE, FpxSpec.fpx_replace)
        s = buffer[:eol].decode(encoding=FpxSpec.STRING_ENCODING, errors=FpxSpec.STRING_ERROR)
        return s

    @staticmethod
    def read_wstring(raw_io, length):
        """ read a string of a specific length from raw_io """
        buffer = raw_io.read(length)
        if not buffer:
            raise EOFError()
        eol = buffer.find(FpxSpec.STRING_TERMINATION)
        register_error(FpxSpec.STRING_FPX_REPLACE, FpxSpec.fpx_replace)
        s = buffer[:eol].decode(encoding=FpxSpec.WSTRING_ENCODING, errors=FpxSpec.STRING_ERROR)
        return s



###############################################################################
class Fp_Stream_Reader(Cfb_Stream_Reader):
    pass


class Fp_Size_Type(Cfb_Size_Type):
    FLOAT = 4
    pass


"""
class Fpm_File_Reader(Cfb_RawIO_Reader):
    pass


class Fpl_File_Reader(Cfb_RawIO_Reader):
    pass
"""

class FpmCollisionData:
    SIZE =  (4 * Fp_Size_Type.DWORD + 7 * Fp_Size_Type.FLOAT)

    def __init__(self):
        self.type = 0 #DWORD
        self.generateHit = 0 #DWORD
        self.effectBall = 0 #DWORD
        self.eventID = 0 #DWORD
        self.x = 0.0 #FLOAT
        self.y = 0.0 #FLOAT
        self.z = 0.0 #FLOAT
        self.value1 = 0.0 #FLOAT
        self.value2 = 0.0 #FLOAT
        self.value3 = 0.0 #FLOAT
        self.value4 = 0.0 #FLOAT

    def __repr__(self):
        return "<{} type=\"{}\", generateHit=\"{}\", effectBall=\"{}\", x=\"{}\", y=\"{}\", z=\"{}\", value1=\"{}\", value2=\"{}\", value3=\"{}\", value4=\"{}\" />".fomat(
                __class__.__name__,
                self.type,
                self.generateHit,
                self.effectBall,
                self.eventID,
                self.x,
                self.y,
                self.z,
                self.value1,
                self.value2,
                self.value3,
                self.value4,
                )


###############################################################################
class Fpm_Model_Type:
    OBJECT_OBJECT = 0 ## e.g.: BULB, COIN_DOOR, FLIPPER_BUTTON, PLUNGER_CASE, RAMP_PROFILE, SHOOTER_LANE, SLING_HAMMER, WIRE_RING, ...
    OBJECT_PEG = 1 # # e.g.: GAME_ROOM, CABINE_LEG, LOCK_DOWN_BAR, RAIL,
    CONTROL_FLIPPER = 2 #
    CONTROL_BUMPER_BASE = 3 #
    CONTROL_BUMPER_CAP = 4 #
    TARGET_TARGET = 5 #
    TARGET_DROP = 6 #
    CONTROL_PLUNGER = 7 #
    OBJECT_ORNAMENT = 8 # # e.g.: BALL
    CONTROL_KICKER = 9 #
    GUIDE_LANE = 10 #
    RUBBER_MODEL = 11 #
    TRIGGER_TRIGGER = 12 #
    LIGHT_FLASHER = 13 #
    LIGHT_BULB = 14 #
    TRIGGER_GATE = 15 #
    TRIGGER_SPINNER = 16 #
    TOY_CUSTOM = 17
    CONTROL_DIVERTER = 18 #
    CONTROL_AUTOPLUNGER = 19 #
    CONTROL_POPUP = 20 #
    RAMP_MODEL = 21 # e.g.: Scoop-Bracket-T1.fpm
    RAMP_WIRE_CAP = 22 #
    TOY_SPINNINGDISK = 23 #
    CONTROL_EMKICKER = 24 #
    TRIGGER_OPTO = 25 #
    TARGET_VARI = 26 ## e.g.: Target-Vari-T1.fpm

    SET_ALIGN_BOTTOM = {
            OBJECT_ORNAMENT,
            RAMP_MODEL,
            TARGET_DROP,
            TARGET_TARGET,
            }

    SET_ALIGN_TOP = {
            TOY_SPINNINGDISK,
            }

    SET_ALIGN_NONE = {
            OBJECT_OBJECT,
            CONTROL_PLUNGER,
            TARGET_DROP,
            TRIGGER_GATE,
            TRIGGER_SPINNER,
            TRIGGER_OPTO,
            TARGET_VARI,
            RAMP_WIRE_CAP
            }

    VALUE_INT_TO_NAME = {
            OBJECT_OBJECT: 'OBJECT_OBJECT',
            OBJECT_PEG: 'OBJECT_PEG',
            CONTROL_FLIPPER: 'CONTROL_FLIPPER',
            CONTROL_BUMPER_BASE: 'CONTROL_BUMPER_BASE',
            CONTROL_BUMPER_CAP: 'CONTROL_BUMPER_CAP',
            TARGET_TARGET: 'TARGET_TARGET',
            TARGET_DROP: 'TARGET_DROP',
            CONTROL_PLUNGER: 'CONTROL_PLUNGER',
            OBJECT_ORNAMENT: 'OBJECT_ORNAMENT',
            CONTROL_KICKER: 'CONTROL_KICKER',
            GUIDE_LANE: 'GUIDE_LANE',
            RUBBER_MODEL: 'RUBBER_MODEL',
            TRIGGER_TRIGGER: 'TRIGGER_TRIGGER',
            LIGHT_FLASHER: 'LIGHT_FLASHER',
            LIGHT_BULB: 'LIGHT_BULB',
            TRIGGER_GATE: 'TRIGGER_GATE',
            TRIGGER_SPINNER: 'TRIGGER_SPINNER',
            TOY_CUSTOM: 'TOY_CUSTOM',
            CONTROL_DIVERTER: 'CONTROL_DIVERTER',
            CONTROL_AUTOPLUNGER: 'CONTROL_AUTOPLUNGER',
            CONTROL_POPUP: 'CONTROL_POPUP',
            RAMP_MODEL: 'RAMP_MODEL',
            RAMP_WIRE_CAP: 'RAMP_WIRE_CAP',
            TOY_SPINNINGDISK: 'TOY_SPINNINGDISK',
            CONTROL_EMKICKER: 'CONTROL_EMKICKER',
            TRIGGER_OPTO: 'TRIGGER_OPTO',
            TARGET_VARI: 'TARGET_VARI',
            }


class Fpl_Library_Type:
    UNKNOWN = 0
    GRAPHIC = 1
    SOUND = 2
    MUSIC = 3
    MODEL = 4
    DMDFONT = 5
    SCRIPT = 6

    TYPE_UNKNOWN = 'UNKNOWN'
    TYPE_GRAPHIC = 'GRAPHIC'
    TYPE_SOUND = 'SOUND'
    TYPE_MUSIC = 'MUSIC'
    TYPE_MODEL = 'MODEL'
    TYPE_DMDFONT = 'DMDFONT'
    TYPE_SCRIPT = 'SCRIPT'

    FILTER_ALL = {TYPE_GRAPHIC, TYPE_SOUND, TYPE_MUSIC, TYPE_MODEL, TYPE_DMDFONT, TYPE_SCRIPT, TYPE_UNKNOWN, }

class Fpt_PackedLibrary_Type:
    UNKNOWN = Fpl_Library_Type.UNKNOWN
    IMAGE = Fpl_Library_Type.GRAPHIC
    SOUND = Fpl_Library_Type.SOUND
    MUSIC = Fpl_Library_Type.MUSIC
    MODEL = Fpl_Library_Type.MODEL
    DMDFONT = Fpl_Library_Type.DMDFONT
    SCRIPT = Fpl_Library_Type.SCRIPT
    IMAGE_LIST = 7
    LIGHT_LIST = 8

    TYPE_UNKNOWN = Fpl_Library_Type.TYPE_UNKNOWN
    TYPE_IMAGE = Fpl_Library_Type.TYPE_GRAPHIC
    TYPE_SOUND = Fpl_Library_Type.TYPE_SOUND
    TYPE_MUSIC = Fpl_Library_Type.TYPE_MUSIC
    TYPE_MODEL = Fpl_Library_Type.TYPE_MODEL
    TYPE_DMDFONT = Fpl_Library_Type.TYPE_DMDFONT
    TYPE_SCRIPT = Fpl_Library_Type.TYPE_SCRIPT
    TYPE_IMAGE_LIST = 'IMAGE_LIST'
    TYPE_LIGHT_LIST = 'LIGHT_LIST'

    FILTER_ALL = {TYPE_IMAGE, TYPE_SOUND, TYPE_MUSIC, TYPE_MODEL, TYPE_DMDFONT, TYPE_SCRIPT, TYPE_IMAGE_LIST, TYPE_LIGHT_LIST, TYPE_UNKNOWN, }

class Fpt_Resource_Type:
    BMP = 1
    JPG = 2
    TGA = 4
    WAV = 6
    MP3 = 7
    OGG = 9
    DMD = 15

    TYPE_BMP = 'BMP'
    TYPE_JPG = 'JPG'
    TYPE_TGA = 'TGA'
    TYPE_WAV = 'WAV'
    TYPE_OGG = 'OGG'
    TYPE_MP3 = 'MP3'
    TYPE_DMD = 'DMD'

    VALUE_INT_TO_NAME = {
            BMP: TYPE_BMP,
            JPG: TYPE_JPG,
            TGA: TYPE_TGA,
            WAV: TYPE_WAV,
            OGG: TYPE_OGG,
            MP3: TYPE_MP3,
            DMD: TYPE_DMD,
            }

    FILTER_ALL_IMAGES = {TYPE_BMP, TYPE_JPG, TYPE_TGA, }
    FILTER_ALL_SOUNDS = {TYPE_OGG, TYPE_WAV, }
    FILTER_ALL_MUSICS = {TYPE_OGG, TYPE_MP3, }
    FILTER_ALL_DMDFONTS = {TYPE_DMD, }


class Fpt_Chunk_Type:
    END = -1
    RAWDATA = 0
    INT = 1
    FLOAT = 2
    COLOR = 3
    VECTOR2D = 4
    STRING = 5
    WSTRING = 6
    STRINGLIST = 7
    VALUELIST = 8
    COLLISIONDATA = 9
    CHUNKLIST = 10
    GENERIC = 11


class FptElementType:
    SURFACE = 2
    LIGHT_ROUND = 3
    LIGHT_SHAPEABLE = 4
    OBJECT_PEG = 6
    CONTROL_FLIPPER = 7
    CONTROL_BUMPER = 8
    TARGET_LEAF = 10
    TARGET_DROP = 11
    CONTROL_PLUNGER = 12
    RUBBER_ROUND = 13
    RUBBER_SHAPEABLE = 14
    OBJECT_ORNAMENT = 15
    GUIDE_WALL = 16
    SPECIAL_TIMER = 17
    SPECIAL_DECAL = 18
    CONTROL_KICKER = 19
    GUIDE_LANE = 20
    RUBBER_MODEL = 21
    TRIGGER_TRIGGER = 22
    LIGHT_FLASHER = 23
    GUIDE_WIRE = 24
    DISPLAY_DISPREEL = 25
    DISPLAY_HUDREEL = 26
    SPECIAL_OVERLAY = 27
    LIGHT_BULB = 29
    TRIGGER_GATE = 30
    TRIGGER_SPINNER = 31
    TOY_CUSTOM = 33
    LIGHT_SEQUENCER = 34
    DISPLAY_SEGMENT = 37
    DISPLAY_HUDSEGMENT = 38
    DISPLAY_DMD = 39
    DISPLAY_HUDDMD = 40
    CONTROL_DIVERTER = 43
    SPECIAL_STA = 44
    CONTROL_AUTOPLUNGER = 46
    TARGET_ROTO = 49
    CONTROL_POPUP = 50
    RAMP_MODEL = 51
    RAMP_WIRE = 53
    TARGET_SWING = 54
    RAMP_RAMP = 55
    TOY_SPINNINGDISK = 56
    LIGHT_LIGHTIMAGE = 57
    KICKER_EMKICKER = 58
    LIGHT_HUDLIGHTIMAGE = 60
    TRIGGER_OPTO = 61
    TARGET_VARI = 62
    TOY_HOLOGRAM = 64

    SET_MESH_OBJECTS = {
            OBJECT_PEG,
            CONTROL_FLIPPER,
            CONTROL_BUMPER,
            TARGET_LEAF,
            TARGET_DROP,
            CONTROL_PLUNGER,
            OBJECT_ORNAMENT,
            CONTROL_KICKER,
            RUBBER_MODEL,
            TRIGGER_TRIGGER,
            LIGHT_FLASHER,
            SPECIAL_OVERLAY,
            LIGHT_BULB,
            TRIGGER_GATE,
            TRIGGER_SPINNER,
            TOY_CUSTOM,
            CONTROL_DIVERTER,
            CONTROL_AUTOPLUNGER,
            TARGET_ROTO,
            CONTROL_POPUP,
            TOY_SPINNINGDISK,
            KICKER_EMKICKER,
            TRIGGER_OPTO,
            TARGET_VARI,
            TOY_HOLOGRAM,
            }

    SET_LIGHT_OBJECTS = {
            LIGHT_ROUND,
            LIGHT_SHAPEABLE,
            CONTROL_BUMPER,
            LIGHT_FLASHER,
            DISPLAY_DISPREEL,
            DISPLAY_HUDREEL,
            LIGHT_BULB,
            LIGHT_SEQUENCER,
            DISPLAY_SEGMENT,
            DISPLAY_HUDSEGMENT,
            DISPLAY_DMD,
            DISPLAY_HUDDMD,
            LIGHT_LIGHTIMAGE,
            LIGHT_HUDLIGHTIMAGE,
            TOY_HOLOGRAM,
            }

    SET_RUBBER_OBJECTS = {
            RUBBER_ROUND,
            RUBBER_SHAPEABLE,
            }

    SET_SPHERE_MAPPING_OBJECTS = {
            SURFACE,
            OBJECT_PEG,
            OBJECT_ORNAMENT,
            GUIDE_WALL,
            TRIGGER_TRIGGER,
            TRIGGER_GATE,
            TOY_CUSTOM,
            CONTROL_DIVERTER,
            CONTROL_POPUP,
            RAMP_MODEL,
            RAMP_RAMP,
            TARGET_VARI,
            }

    SET_WIRE_OBJECTS = {
            GUIDE_WIRE,
            RAMP_WIRE,
            }

    SET_CURVE_OBJECTS = {
            SURFACE,
            LIGHT_ROUND,
            LIGHT_SHAPEABLE,
            RUBBER_ROUND,
            RUBBER_SHAPEABLE,
            GUIDE_WALL,
            GUIDE_WIRE,
            RAMP_WIRE,
            RAMP_RAMP,
            }

    VALUE_NAME_TO_INT = {
            'SURFACE': SURFACE,
            'LIGHT_ROUND': LIGHT_ROUND,
            'LIGHT_SHAPEABLE': LIGHT_SHAPEABLE,
            'OBJECT_PEG': OBJECT_PEG,
            'CONTROL_FLIPPER': CONTROL_FLIPPER,
            'CONTROL_BUMPER': CONTROL_BUMPER,
            'TARGET_LEAF': TARGET_LEAF,
            'TARGET_DROP': TARGET_DROP,
            'CONTROL_PLUNGER': CONTROL_PLUNGER,
            'RUBBER_ROUND': RUBBER_ROUND,
            'RUBBER_SHAPEABLE': RUBBER_SHAPEABLE,
            'OBJECT_ORNAMENT': OBJECT_ORNAMENT,
            'GUIDE_WALL': GUIDE_WALL,
            'SPECIAL_TIMER': SPECIAL_TIMER,
            'SPECIAL_DECAL': SPECIAL_DECAL,
            'CONTROL_KICKER': CONTROL_KICKER,
            'GUIDE_LANE': GUIDE_LANE,
            'RUBBER_MODEL': RUBBER_MODEL,
            'TRIGGER_TRIGGER': TRIGGER_TRIGGER,
            'LIGHT_FLASHER': LIGHT_FLASHER,
            'GUIDE_WIRE': GUIDE_WIRE,
            'DISPLAY_DISPREEL': DISPLAY_DISPREEL,
            'DISPLAY_HUDREEL': DISPLAY_HUDREEL,
            'SPECIAL_OVERLAY': SPECIAL_OVERLAY,
            'LIGHT_BULB': LIGHT_BULB,
            'TRIGGER_GATE': TRIGGER_GATE,
            'TRIGGER_SPINNER': TRIGGER_SPINNER,
            'TOY_CUSTOM': TOY_CUSTOM,
            'LIGHT_SEQUENCER': LIGHT_SEQUENCER,
            'DISPLAY_SEGMENT': DISPLAY_SEGMENT,
            'DISPLAY_HUDSEGMENT': DISPLAY_HUDSEGMENT,
            'DISPLAY_DMD': DISPLAY_DMD,
            'DISPLAY_HUDDMD': DISPLAY_HUDDMD,
            'CONTROL_DIVERTER': CONTROL_DIVERTER,
            'SPECIAL_STA': SPECIAL_STA,
            'CONTROL_AUTOPLUNGER': CONTROL_AUTOPLUNGER,
            'TARGET_ROTO': TARGET_ROTO,
            'CONTROL_POPUP': CONTROL_POPUP,
            'RAMP_MODEL': RAMP_MODEL,
            'RAMP_WIRE': RAMP_WIRE,
            'TARGET_SWING': TARGET_SWING,
            'RAMP_RAMP': RAMP_RAMP,
            'TOY_SPINNINGDISK': TOY_SPINNINGDISK,
            'LIGHT_LIGHTIMAGE': LIGHT_LIGHTIMAGE,
            'KICKER_EMKICKER': KICKER_EMKICKER,
            'LIGHT_HUDLIGHTIMAGE': LIGHT_HUDLIGHTIMAGE,
            'TRIGGER_OPTO': TRIGGER_OPTO,
            'TARGET_VARI': TARGET_VARI,
            'TOY_HOLOGRAM': TOY_HOLOGRAM,
            }

    VALUE_INT_TO_NAME = {
            SURFACE: 'SURFACE',
            LIGHT_ROUND: 'LIGHT_ROUND',
            LIGHT_SHAPEABLE: 'LIGHT_SHAPEABLE',
            OBJECT_PEG: 'OBJECT_PEG',
            CONTROL_FLIPPER: 'CONTROL_FLIPPER',
            CONTROL_BUMPER: 'CONTROL_BUMPER',
            TARGET_LEAF: 'TARGET_LEAF',
            TARGET_DROP: 'TARGET_DROP',
            CONTROL_PLUNGER: 'CONTROL_PLUNGER',
            RUBBER_ROUND: 'RUBBER_ROUND',
            RUBBER_SHAPEABLE: 'RUBBER_SHAPEABLE',
            OBJECT_ORNAMENT: 'OBJECT_ORNAMENT',
            GUIDE_WALL: 'GUIDE_WALL',
            SPECIAL_TIMER: 'SPECIAL_TIMER',
            SPECIAL_DECAL: 'SPECIAL_DECAL',
            CONTROL_KICKER: 'CONTROL_KICKER',
            GUIDE_LANE: 'GUIDE_LANE',
            RUBBER_MODEL: 'RUBBER_MODEL',
            TRIGGER_TRIGGER: 'TRIGGER_TRIGGER',
            LIGHT_FLASHER: 'LIGHT_FLASHER',
            GUIDE_WIRE: 'GUIDE_WIRE',
            DISPLAY_DISPREEL: 'DISPLAY_DISPREEL',
            DISPLAY_HUDREEL: 'DISPLAY_HUDREEL',
            SPECIAL_OVERLAY: 'SPECIAL_OVERLAY',
            LIGHT_BULB: 'LIGHT_BULB',
            TRIGGER_GATE: 'TRIGGER_GATE',
            TRIGGER_SPINNER: 'TRIGGER_SPINNER',
            TOY_CUSTOM: 'TOY_CUSTOM',
            LIGHT_SEQUENCER: 'LIGHT_SEQUENCER',
            DISPLAY_SEGMENT: 'DISPLAY_SEGMENT',
            DISPLAY_HUDSEGMENT: 'DISPLAY_HUDSEGMENT',
            DISPLAY_DMD: 'DISPLAY_DMD',
            DISPLAY_HUDDMD: 'DISPLAY_HUDDMD',
            CONTROL_DIVERTER: 'CONTROL_DIVERTER',
            SPECIAL_STA: 'SPECIAL_STA',
            CONTROL_AUTOPLUNGER: 'CONTROL_AUTOPLUNGER',
            TARGET_ROTO: 'TARGET_ROTO',
            CONTROL_POPUP: 'CONTROL_POPUP',
            RAMP_MODEL: 'RAMP_MODEL',
            RAMP_WIRE: 'RAMP_WIRE',
            TARGET_SWING: 'TARGET_SWING',
            RAMP_RAMP: 'RAMP_RAMP',
            TOY_SPINNINGDISK: 'TOY_SPINNINGDISK',
            LIGHT_LIGHTIMAGE: 'LIGHT_LIGHTIMAGE',
            KICKER_EMKICKER: 'KICKER_EMKICKER',
            LIGHT_HUDLIGHTIMAGE: 'LIGHT_HUDLIGHTIMAGE',
            TRIGGER_OPTO: 'TRIGGER_OPTO',
            TARGET_VARI: 'TARGET_VARI',
            TOY_HOLOGRAM: 'TOY_HOLOGRAM',
            }


###############################################################################
class Fpx_zLZO_RawData_Stream:
    def __init__(self, stream, n=-1):
        buffer = stream.read(4)
        if buffer == b'zLZO':
            self.signature = buffer
            self.uncompressed_size = stream.read_dword()
            if n != -1:
                n -= (4 + Fp_Size_Type.DWORD)
        else:
            self.signature = None
            stream.seek(-4, SEEK_CUR)
        self.src_buffer = stream.read(n)

    def grab_to_file(self, filename):
        with FileIO(filename, "wb") as raw_io:
            if not self.signature:
                raw_io.write(self.src_buffer)
            else:
                dst_buffer = bytearray(self.uncompressed_size)
                src_size = len(self.src_buffer)
                Lzo_Codec.Lzo1x_Decompress(self.src_buffer, 0, src_size, dst_buffer, 0)
                raw_io.write(dst_buffer)

            raw_io.flush()
            raw_io.close()


###############################################################################
class Fpt_ChunkDescription:
    def __init__(self, id=0, type=Fpt_Chunk_Type.RAWDATA, name='', offset=0):
        self.id = id
        self.type = type
        self.name = "val__" + name
        self.offset = offset

    def __repr__(self):
        return "<{} id=\"{}\"/, type=\"{}\", name=\"{}\", offset=\"{}\" />".fomat(
                __class__.__name__,
                self.id,
                self.type,
                self.name,
                self.offset,
                )


class Fpt_Data_Reader:
    NEW_OLD_CORRECTION = 0x15BDECDB

    def __repr__(self):
        str_list = []
        str_list.append("<")

        class_name = getattr(self, "obj__class", None)
        if class_name is None:
            class_name = __class__
        str_list.append("{} ".format(class_name))

        obj_name = getattr(self, "obj__name", None)
        if obj_name is not None:
            str_list.append("obj__name=\"{}\", ".format(obj_name))

        name = self.get_value("name")
        if name:
            str_list.append("name=\"{}\", ".format(name))

        d = dir(self)
        for attr in d:
            if attr == "val__end":
                continue
            elif attr == "val__name" and name:
                continue
            elif attr.startswith("val__unknown_"):
                continue
            elif attr.startswith("val__"):
                v = getattr(self, attr, None)
                if v is not None:
                    if isinstance(v, bytes) and len(v) > 4:
                        v = v[:4] + b'...'
                    str_list.append("{}=\"{}\", ".format(attr.replace("val__", ""), v))
            else:
                pass
        str_list.append("/>")
        result = "".join(str_list)
        return result

    def get_value(self, name, default=None):
        v = getattr(self, "val__" + name, default)
        return v

    def get_obj_value(self, name, default=None):
        v = getattr(self, "obj__" + name, default)
        return v

    def read(self, stream, owner=None):
        if owner is None:
            owner = self

        stream_size = stream.size()
        while stream.tell() < stream_size:
            chunk_size = stream.read_dword()
            stream_pos = stream.tell()
            chunk_id = stream.read_dword()
            descriptor = self.obj__chunks.get(chunk_id)
            if descriptor is None:
                # try the alternative chunk_id
                descriptor = self.obj__chunks.get(chunk_id - Fpt_Data_Reader.NEW_OLD_CORRECTION)
            if descriptor is None:
                # unknown chunk type
                stream.read(chunk_size - Fp_Size_Type.DWORD)
                print("#DEBUG unknown chunk id:", "0x{:08X}".format(chunk_id), ", size:", chunk_size - Fp_Size_Type.DWORD, " in ", self.get_obj_value("class"), self)
            else:
                self.read_chunk_data(stream, owner, stream_pos, chunk_size, descriptor)

            if self.read_breaker(owner):
                break

    def read_breaker(self, owner):
        pass

    def read_int(self, stream):
        return unpack("<i", stream.read(4))[0]

    def read_float(self, stream):
        return unpack("<f", stream.read(4))[0]

    def read_color(self, stream):
        return unpack("<BBBB", stream.read(4))

    def read_vector2d(self, stream):
        return unpack("<ff", stream.read(8))

    def read_string(self, stream):
        size = stream.read_dword()
        buffer = stream.read(size)
        register_error(FpxSpec.STRING_FPX_REPLACE, FpxSpec.fpx_replace)
        value = buffer.decode(encoding=FpxSpec.STRING_ENCODING, errors=FpxSpec.STRING_ERROR)
        return value

    def read_wstring(self, stream):
        size = stream.read_dword()
        buffer = stream.read(size)
        register_error(FpxSpec.STRING_FPX_REPLACE, FpxSpec.fpx_replace)
        value = buffer.decode(encoding=FpxSpec.WSTRING_ENCODING, errors=FpxSpec.STRING_ERROR)
        return value

    def read_chunk_data(self, stream, owner, stream_pos, chunk_size, descriptor):
        if descriptor.offset:
            stream.seek(descriptor.offset, SEEK_CUR)

        if descriptor.type == Fpt_Chunk_Type.RAWDATA:
            value = Fpx_zLZO_RawData_Stream(stream, chunk_size - Fp_Size_Type.DWORD)
        elif descriptor.type == Fpt_Chunk_Type.INT:
            value = self.read_int(stream)
        elif descriptor.type == Fpt_Chunk_Type.FLOAT:
            value = self.read_float(stream)
        elif descriptor.type == Fpt_Chunk_Type.COLOR:
            value = self.read_color(stream)
        elif descriptor.type == Fpt_Chunk_Type.VECTOR2D:
            value = self.read_vector2d(stream)
        elif descriptor.type == Fpt_Chunk_Type.STRING:
            value = self.read_string(stream)
        elif descriptor.type == Fpt_Chunk_Type.WSTRING:
            value = self.read_wstring(stream)
        elif descriptor.type == Fpt_Chunk_Type.STRINGLIST:
            value = []
            num_items = self.read_int(stream)
            for i in range(num_items):
                value.append(self.read_string(stream))
        elif descriptor.type == Fpt_Chunk_Type.VALUELIST:
            value = None # TODO
        elif descriptor.type == Fpt_Chunk_Type.COLLISIONDATA:
             # TODO
            n = chunk_size / FpmCollisionData.SIZE
            value = None
        elif descriptor.type == Fpt_Chunk_Type.CHUNKLIST:
            if descriptor.name == "val__shape_point":
                sub_reader = Fpt_SubData_Shape_Point_Reader()
                if sub_reader:
                    sub_reader.read(stream)
            elif descriptor.name == "val__ramp_point":
                sub_reader = Fpt_SubData_Ramp_Point_Reader()
                if sub_reader:
                    sub_reader.read(stream)
            else:
                print("#DEBUG", descriptor.name, "not handled!")
                pass
            value = getattr(owner, descriptor.name, None)
            if value is None:
                value = []
                value.append(sub_reader)
            else:
                value.append(sub_reader)
                return

        elif descriptor.type == Fpt_Chunk_Type.GENERIC:
            value = stream.read(chunk_size - Fp_Size_Type.DWORD)
        elif descriptor.type == Fpt_Chunk_Type.END:
            value = 1
        else:
            value = None

        setattr(owner, descriptor.name, value)

        if value is None:
            stream.read(chunk_size - Fp_Size_Type.DWORD)


class Fpt_SubData_Shape_Point_Reader(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0xA1EDC5D2: Fpt_ChunkDescription(0xA1EDC5D2, Fpt_Chunk_Type.INT, "smooth"),
            0xA2F3C6D2: Fpt_ChunkDescription(0xA2F3C6D2, Fpt_Chunk_Type.RAWDATA, "unknown_0xA2F3C6D2"), # slingshot ???
            0xA8FCC6D2: Fpt_ChunkDescription(0xA8FCC6D2, Fpt_Chunk_Type.RAWDATA, "unknown_0xA8FCC6D2"), # single_leaf ???
            0x99E9BEE4: Fpt_ChunkDescription(0x99E9BEE4, Fpt_Chunk_Type.INT, "automatic_texture_coordinate"),
            0x9AFEBAD1: Fpt_ChunkDescription(0x9AFEBAD1, Fpt_Chunk_Type.FLOAT, "texture_coordinate"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
            0x95F3BCE0: Fpt_ChunkDescription(0x95F3BCE0, Fpt_Chunk_Type.RAWDATA, "unknown_0x95F3BCE0"), # missed event_id ???
            }

    def __init__(self):
        self.obj__class = "Shape_Point"
        self.obj__id = "shape_point"
        self.obj__chunks = Fpt_SubData_Shape_Point_Reader.CHUNK_DICTIONARY

    def read_breaker(self, owner):
        return getattr(owner, 'val__end', None)


class Fpt_SubData_Ramp_Point_Reader(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0xA1EDC5D2: Fpt_ChunkDescription(0xA1EDC5D2, Fpt_Chunk_Type.INT, "smooth"),
            0xA2F3C6D2: Fpt_ChunkDescription(0xA2F3C6D2, Fpt_Chunk_Type.RAWDATA, "unknown_0xA2F3C6D2"), # slingshot ???
            0xA8FCC6D2: Fpt_ChunkDescription(0xA8FCC6D2, Fpt_Chunk_Type.RAWDATA, "unknown_0xA8FCC6D2"), # single_leaf ???
            0x99E9BEE4: Fpt_ChunkDescription(0x99E9BEE4, Fpt_Chunk_Type.INT, "automatic_texture_coordinate"),
            0x9AFEBAD1: Fpt_ChunkDescription(0x9AFEBAD1, Fpt_Chunk_Type.FLOAT, "texture_coordinate"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
            #0x9AF1CAE0: Fpt_ChunkDescription(0x9AF1CAE0, Fpt_Chunk_Type.RAWDATA, "unknown_0x9AF1CAE0"), # missed mark_as_ramp_end_point
            #0xA0EFC2D0: Fpt_ChunkDescription(0xA0EFC2D0, Fpt_Chunk_Type.RAWDATA, "unknown_0xA0EFC2D0"), # missed right_upper_guide
            #0xA0EFC9D8: Fpt_ChunkDescription(0xA0EFC9D8, Fpt_Chunk_Type.RAWDATA, "unknown_0xA0EFC9D8"), # missed right_guide
            #0xA2F3C9D3: Fpt_ChunkDescription(0xA2F3C9D3, Fpt_Chunk_Type.RAWDATA, "unknown_0xA2F3C9D3"), # missed ring_type
            #0xA4F5C2D0: Fpt_ChunkDescription(0xA4F5C2D0, Fpt_Chunk_Type.RAWDATA, "unknown_0xA4F5C2D0"), # missed left_upper_guide
            #0xA4F5C9D8: Fpt_ChunkDescription(0xA4F5C9D8, Fpt_Chunk_Type.RAWDATA, "unknown_0xA4F5C9D8"), # missed left_guide
            #0x95ECC3D1: Fpt_ChunkDescription(0x95ECC3D1, Fpt_Chunk_Type.RAWDATA, "unknown_0x95ECC3D1"), # missed top_wire

            0xA4F5C9D8: Fpt_ChunkDescription(0xA4F5C9D8, Fpt_Chunk_Type.INT, "left_guide"),
            0xA4F5C2D0: Fpt_ChunkDescription(0xA4F5C2D0, Fpt_Chunk_Type.INT, "left_upper_guide"),
            0xA0EFC9D8: Fpt_ChunkDescription(0xA0EFC9D8, Fpt_Chunk_Type.INT, "right_guide"),
            0xA0EFC2D0: Fpt_ChunkDescription(0xA0EFC2D0, Fpt_Chunk_Type.INT, "right_upper_guide"),
            0x95ECC3D1: Fpt_ChunkDescription(0x95ECC3D1, Fpt_Chunk_Type.INT, "top_wire"),
            0x9AF1CAE0: Fpt_ChunkDescription(0x9AF1CAE0, Fpt_Chunk_Type.INT, "mark_as_ramp_end_point"),
            0xA2F3C9D3: Fpt_ChunkDescription(0xA2F3C9D3, Fpt_Chunk_Type.INT, "ring_type"),
            }

    def __init__(self):
        self.obj__class = "Ramp_Point"
        self.obj__id = "ramp_point"
        self.obj__chunks = Fpt_SubData_Ramp_Point_Reader.CHUNK_DICTIONARY

    def read_breaker(self, owner):
        return getattr(owner, 'val__end', None)


class Fpt_Table_Data_Reader(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0xA5F8BBD1: Fpt_ChunkDescription(0xA5F8BBD1, Fpt_Chunk_Type.INT, "width"),
            0x9BFCC6D1: Fpt_ChunkDescription(0x9BFCC6D1, Fpt_Chunk_Type.INT, "length"),
            0xA1FACCD1: Fpt_ChunkDescription(0xA1FACCD1, Fpt_Chunk_Type.INT, "glass_height_front"),
            0xA1FAC0D1: Fpt_ChunkDescription(0xA1FAC0D1, Fpt_Chunk_Type.INT, "glass_height_rear"),
            0x9AF5BFD1: Fpt_ChunkDescription(0x9AF5BFD1, Fpt_Chunk_Type.FLOAT, "slope"),
            0x9DF2CFD5: Fpt_ChunkDescription(0x9DF2CFD5, Fpt_Chunk_Type.COLOR, "playfield_color"),
            0xA2F4C9D5: Fpt_ChunkDescription(0xA2F4C9D5, Fpt_Chunk_Type.STRING, "playfield_texture"),
            0x9DF2CFE2: Fpt_ChunkDescription(0x9DF2CFE2, Fpt_Chunk_Type.COLOR, "cabinet_wood_color"),
            0x9DF2CFE3: Fpt_ChunkDescription(0x9DF2CFE3, Fpt_Chunk_Type.COLOR, "button_color"),
            0x9AFECBE3: Fpt_ChunkDescription(0x9AFECBE3, Fpt_Chunk_Type.COLOR, "translite_color"),
            0xA2F4C9E3: Fpt_ChunkDescription(0xA2F4C9E3, Fpt_Chunk_Type.STRING, "translite_image"),
            0x96F2C6DE: Fpt_ChunkDescription(0x96F2C6DE, Fpt_Chunk_Type.INT, "glossiness"),
            0x95F5C9D1: Fpt_ChunkDescription(0x95F5C9D1, Fpt_Chunk_Type.INT, "warnings_before_tilt"),
            0xA5F8C0DE: Fpt_ChunkDescription(0xA5F8C0DE, Fpt_Chunk_Type.INT, "display_grid_in_editor"),
            0x96FDC0DE: Fpt_ChunkDescription(0x96FDC0DE, Fpt_Chunk_Type.INT, "grid_size"),
            0xA0FBC2E1: Fpt_ChunkDescription(0xA0FBC2E1, Fpt_Chunk_Type.INT, "display_playfield_in_editor"),
            0xA0FAD0E1: Fpt_ChunkDescription(0xA0FAD0E1, Fpt_Chunk_Type.INT, "display_tranlite_in_editor"),
            0xA0EACBE3: Fpt_ChunkDescription(0xA0EACBE3, Fpt_Chunk_Type.INT, "translite_width"),
            0xA4F9CBE3: Fpt_ChunkDescription(0xA4F9CBE3, Fpt_Chunk_Type.INT, "translite_height"),
            0x99E8BED8: Fpt_ChunkDescription(0x99E8BED8, Fpt_Chunk_Type.INT, "machine_type"),
            0xA2F4C9E2: Fpt_ChunkDescription(0xA2F4C9E2, Fpt_Chunk_Type.STRING, "cabinet_texture"),
            0x95EEC3D5: Fpt_ChunkDescription(0x95EEC3D5, Fpt_Chunk_Type.STRING, "poster_image"),
            0x9BF5CFD1: Fpt_ChunkDescription(0x9BF5CFD1, Fpt_Chunk_Type.FLOAT, "table_center_line"),
            0x9BF5CCD1: Fpt_ChunkDescription(0x9BF5CCD1, Fpt_Chunk_Type.FLOAT, "table_flipper_line"),
            0xA0FCBFE1: Fpt_ChunkDescription(0xA0FCBFE1, Fpt_Chunk_Type.RAWDATA, "unknown_0xA0FCBFE1"),
            0x9AFECDD2: Fpt_ChunkDescription(0x9AFECDD2, Fpt_Chunk_Type.RAWDATA, "unknown_0x9AFECDD2"),
            0x9BEDC9D1: Fpt_ChunkDescription(0x9BEDC9D1, Fpt_Chunk_Type.STRING, "table_name"),
            0xA4EBC9D1: Fpt_ChunkDescription(0xA4EBC9D1, Fpt_Chunk_Type.STRING, "version"),
            0x9500C9D1: Fpt_ChunkDescription(0x9500C9D1, Fpt_Chunk_Type.STRING, "table_authors"),
            0xA5EFC9D1: Fpt_ChunkDescription(0xA5EFC9D1, Fpt_Chunk_Type.STRING, "release_date"),
            0x9CFCC9D1: Fpt_ChunkDescription(0x9CFCC9D1, Fpt_Chunk_Type.STRING, "mail"),
            0x96EAC9D1: Fpt_ChunkDescription(0x96EAC9D1, Fpt_Chunk_Type.STRING, "web_page"),
            0xA4FDC9D1: Fpt_ChunkDescription(0xA4FDC9D1, Fpt_Chunk_Type.STRING, "description"),
            0x96EFC9D1: Fpt_ChunkDescription(0x96EFC9D1, Fpt_Chunk_Type.INT, "rules_len"),
            0x94EFC9D1: Fpt_ChunkDescription(0x94EFC9D1, Fpt_Chunk_Type.RAWDATA, "rules"),
            0x99F5C9D1: Fpt_ChunkDescription(0x99F5C9D1, Fpt_Chunk_Type.STRING, "loading_picture"),
            0x95FEC9D1: Fpt_ChunkDescription(0x95FEC9D1, Fpt_Chunk_Type.COLOR, "loading_color"),
            0xA2F1D0DC: Fpt_ChunkDescription(0xA2F1D0DC, Fpt_Chunk_Type.INT, "ball_per_game"),
            0xA700C8DC: Fpt_ChunkDescription(0xA700C8DC, Fpt_Chunk_Type.INT, "initial_jackpot"),
            0x9C10CADC: Fpt_ChunkDescription(0x9C10CADC, Fpt_Chunk_Type.STRING, "high_scores_default_initial_1"),
            0x9710CADC: Fpt_ChunkDescription(0x9710CADC, Fpt_Chunk_Type.INT, "high_scores_default_score_1"),
            0x9C0FCADC: Fpt_ChunkDescription(0x9C0FCADC, Fpt_Chunk_Type.STRING, "high_scores_default_initial_2"),
            0x970FCADC: Fpt_ChunkDescription(0x970FCADC, Fpt_Chunk_Type.INT, "high_scores_default_score_2"),
            0x9C0ECADC: Fpt_ChunkDescription(0x9C0ECADC, Fpt_Chunk_Type.STRING, "high_scores_default_initial_3"),
            0x970ECADC: Fpt_ChunkDescription(0x970ECADC, Fpt_Chunk_Type.INT, "high_scores_default_score_3"),
            0x9C0DCADC: Fpt_ChunkDescription(0x9C0DCADC, Fpt_Chunk_Type.STRING, "high_scores_default_initial_4"),
            0x970DCADC: Fpt_ChunkDescription(0x970DCADC, Fpt_Chunk_Type.INT, "high_scores_default_score_4"),
            0x9BFBBFDC: Fpt_ChunkDescription(0x9BFBBFDC, Fpt_Chunk_Type.STRING, "special_score_title"),
            0x93FBBFDC: Fpt_ChunkDescription(0x93FBBFDC, Fpt_Chunk_Type.INT, "special_score_value"),
            0x96ECCFE2: Fpt_ChunkDescription(0x96ECCFE2, Fpt_Chunk_Type.RAWDATA, "unknown_0x96ECCFE2"),
            0xA4FBBFDC: Fpt_ChunkDescription(0xA4FBBFDC, Fpt_Chunk_Type.STRING, "special_score_text"),
            0x95FDCDD2: Fpt_ChunkDescription(0x95FDCDD2, Fpt_Chunk_Type.RAWDATA, "unknown_0x95FDCDD2"),
            0xA2F4C9D2: Fpt_ChunkDescription(0xA2F4C9D2, Fpt_Chunk_Type.RAWDATA, "unknown_0xA2F4C9D2"),
            0xA5F3BFD2: Fpt_ChunkDescription(0xA5F3BFD2, Fpt_Chunk_Type.RAWDATA, "unknown_0xA5F3BFD2"),
            0x96ECC5D2: Fpt_ChunkDescription(0x96ECC5D2, Fpt_Chunk_Type.RAWDATA, "unknown_0x96ECC5D2"),
            0xA5F2C5D2: Fpt_ChunkDescription(0xA5F2C5D2, Fpt_Chunk_Type.RAWDATA, "unknown_0xA5F2C5D2"),
            0x95F5C9D2: Fpt_ChunkDescription(0x95F5C9D2, Fpt_Chunk_Type.RAWDATA, "unknown_0x95F5C9D2"),
            0x95F5C6D2: Fpt_ChunkDescription(0x95F5C6D2, Fpt_Chunk_Type.RAWDATA, "unknown_0x95F5C6D2"),
            0x9BFBCED2: Fpt_ChunkDescription(0x9BFBCED2, Fpt_Chunk_Type.RAWDATA, "unknown_0x9BFBCED2"),
            0xA4FDC3E2: Fpt_ChunkDescription(0xA4FDC3E2, Fpt_Chunk_Type.GENERIC, "unknown_0xA4FDC3E2"),
            0x4F5A4C7A: Fpt_ChunkDescription(0x4F5A4C7A, Fpt_Chunk_Type.RAWDATA, "script", -Fp_Size_Type.DWORD),
            0x91FBCCD6: Fpt_ChunkDescription(0x91FBCCD6, Fpt_Chunk_Type.FLOAT, "translate_x"),
            0x90FBCCD6: Fpt_ChunkDescription(0x90FBCCD6, Fpt_Chunk_Type.FLOAT, "translate_y"),
            0x9200CFD2: Fpt_ChunkDescription(0x9200CFD2, Fpt_Chunk_Type.FLOAT, "scale_x"),
            0x9100CFD2: Fpt_ChunkDescription(0x9100CFD2, Fpt_Chunk_Type.FLOAT, "scale_y"),
            0x91EECCD6: Fpt_ChunkDescription(0x91EECCD6, Fpt_Chunk_Type.FLOAT, "translite_translate_x"),
            0x90EECCD6: Fpt_ChunkDescription(0x90EECCD6, Fpt_Chunk_Type.FLOAT, "translite_translate_y"),
            0x91EECFD2: Fpt_ChunkDescription(0x91EECFD2, Fpt_Chunk_Type.FLOAT, "translite_scale_x"),
            0x90EECFD2: Fpt_ChunkDescription(0x90EECFD2, Fpt_Chunk_Type.FLOAT, "translite_scale_y"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),

            0x00000008: Fpt_ChunkDescription(0x00000008, Fpt_Chunk_Type.RAWDATA, "unknown_0x00000008"), # missed
            0x95FBBFDC: Fpt_ChunkDescription(0x95FBBFDC, Fpt_Chunk_Type.RAWDATA, "unknown_0x95FBBFDC"), # missed
            }

    def __init__(self):
        self.obj__class = "Table_Data"
        self.obj__chunks = Fpt_Table_Data_Reader.CHUNK_DICTIONARY


class Fpt_File_Version_Reader(Fpt_Data_Reader):
    def __init__(self):
        self.obj__class = "File_Version"

    def read(self, stream):
        self.val__version = stream.read_dword()


class Fpt_Image_Reader(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
                0xA4F1B9D1: Fpt_ChunkDescription(0xA4F1B9D1, Fpt_Chunk_Type.INT, "type"),
                0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.STRING, "name"),
                0xA4F4C4DC: Fpt_ChunkDescription(0xA4F4C4DC, Fpt_Chunk_Type.STRING, "id"),
                0xA1EDD1D5: Fpt_ChunkDescription(0xA1EDD1D5, Fpt_Chunk_Type.STRING, "linked_path"),
                0x9EF3C6D9: Fpt_ChunkDescription(0x9EF3C6D9, Fpt_Chunk_Type.INT, "linked"),
                0xA6E9BEE4: Fpt_ChunkDescription(0xA6E9BEE4, Fpt_Chunk_Type.INT, "s3tc_compression"),
                0x95F5CCE1: Fpt_ChunkDescription(0x95F5CCE1, Fpt_Chunk_Type.INT, "disable_filtering"),
                0x96F3C0D1: Fpt_ChunkDescription(0x96F3C0D1, Fpt_Chunk_Type.COLOR, "transparent_color"),
                0xA4E7C9D2: Fpt_ChunkDescription(0xA4E7C9D2, Fpt_Chunk_Type.INT, "data_len"),
                0xA8EDD1E1: Fpt_ChunkDescription(0xA8EDD1E1, Fpt_Chunk_Type.RAWDATA, "data"),
                0x95EFBBD9: Fpt_ChunkDescription(0x95EFBBD9, Fpt_Chunk_Type.RAWDATA, "unknown_0x95EFBBD9"),
                0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
                }

    def __init__(self):
        self.obj__class = "Image"
        self.obj__chunks = Fpt_Image_Reader.CHUNK_DICTIONARY


class Fpt_Sound_Reader(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
                0xA4F1B9D1: Fpt_ChunkDescription(0xA4F1B9D1, Fpt_Chunk_Type.INT, "type"),
                0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.STRING, "name"),
                0xA4F4C4DC: Fpt_ChunkDescription(0xA4F4C4DC, Fpt_Chunk_Type.STRING, "id"),
                0xA1EDD1D5: Fpt_ChunkDescription(0xA1EDD1D5, Fpt_Chunk_Type.STRING, "linked_path"),
                0x9EF3C6D9: Fpt_ChunkDescription(0x9EF3C6D9, Fpt_Chunk_Type.INT, "linked"),
                0xA6E9BEE4: Fpt_ChunkDescription(0xA6E9BEE4, Fpt_Chunk_Type.INT, "use_compression"),
                0x95F5CCE1: Fpt_ChunkDescription(0x95F5CCE1, Fpt_Chunk_Type.INT, "disable_filtering"),
                0x96F3C0D1: Fpt_ChunkDescription(0x96F3C0D1, Fpt_Chunk_Type.COLOR, "transparent_color"),
                0xA4E7C9D2: Fpt_ChunkDescription(0xA4E7C9D2, Fpt_Chunk_Type.INT, "data_len"),
                0xA8EDD1E1: Fpt_ChunkDescription(0xA8EDD1E1, Fpt_Chunk_Type.RAWDATA, "data"),
                0x95EFBBD9: Fpt_ChunkDescription(0x95EFBBD9, Fpt_Chunk_Type.RAWDATA, "unknown_0x95EFBBD9"),
                0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
                }

    def __init__(self):
        self.obj__class = "Sound"
        self.obj__chunks = Fpt_Sound_Reader.CHUNK_DICTIONARY


class Fpt_Music_Reader(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
                0xA4F1B9D1: Fpt_ChunkDescription(0xA4F1B9D1, Fpt_Chunk_Type.INT, "type"),
                0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.STRING, "name"),
                0xA4F4C4DC: Fpt_ChunkDescription(0xA4F4C4DC, Fpt_Chunk_Type.STRING, "id"),
                0xA1EDD1D5: Fpt_ChunkDescription(0xA1EDD1D5, Fpt_Chunk_Type.STRING, "linked_path"),
                0x9EF3C6D9: Fpt_ChunkDescription(0x9EF3C6D9, Fpt_Chunk_Type.INT, "linked"),
                0xA6E9BEE4: Fpt_ChunkDescription(0xA6E9BEE4, Fpt_Chunk_Type.INT, "use_compression"),
                0x95F5CCE1: Fpt_ChunkDescription(0x95F5CCE1, Fpt_Chunk_Type.INT, "disable_filtering"),
                0x96F3C0D1: Fpt_ChunkDescription(0x96F3C0D1, Fpt_Chunk_Type.COLOR, "transparent_color"),
                0xA4E7C9D2: Fpt_ChunkDescription(0xA4E7C9D2, Fpt_Chunk_Type.INT, "data_len"),
                0xA8EDD1E1: Fpt_ChunkDescription(0xA8EDD1E1, Fpt_Chunk_Type.RAWDATA, "data"),
                0x95EFBBD9: Fpt_ChunkDescription(0x95EFBBD9, Fpt_Chunk_Type.RAWDATA, "unknown_0x95EFBBD9"),
                0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
                }

    def __init__(self):
        self.obj__class = "Music"
        self.obj__chunks = Fpt_Music_Reader.CHUNK_DICTIONARY


class Fpt_PinModel_Reader(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.STRING, "name"),
            0xA4F4C4DC: Fpt_ChunkDescription(0xA4F4C4DC, Fpt_Chunk_Type.STRING, "id"),
            0x9EF3C6D9: Fpt_ChunkDescription(0x9EF3C6D9, Fpt_Chunk_Type.INT, "linked"),
            0xA4F1B9D1: Fpt_ChunkDescription(0xA4F1B9D1, Fpt_Chunk_Type.INT, "type"),
            0x99E8BED8: Fpt_ChunkDescription(0x99E8BED8, Fpt_Chunk_Type.INT, "material_type"),
            0x9D00C4DC: Fpt_ChunkDescription(0x9D00C4DC, Fpt_Chunk_Type.STRING, "preview_path"),
            0x8FF8BFDC: Fpt_ChunkDescription(0x8FF8BFDC, Fpt_Chunk_Type.INT, "preview_data_len"),
            0x9600CEDC: Fpt_ChunkDescription(0x9600CEDC, Fpt_Chunk_Type.RAWDATA, "preview_data"),
            0x9AFEC2D5: Fpt_ChunkDescription(0x9AFEC2D5, Fpt_Chunk_Type.INT, "per_polygon_collision"),
            0xA5F2C6E0: Fpt_ChunkDescription(0xA5F2C6E0, Fpt_Chunk_Type.INT, "secondary_model_enabled"),
            0xA5FDC3D9: Fpt_ChunkDescription(0xA5FDC3D9, Fpt_Chunk_Type.INT, "secondary_model_z_distance"),
            0xA8EFCBD3: Fpt_ChunkDescription(0xA8EFCBD3, Fpt_Chunk_Type.FLOAT, "special_value"),
            0xA5F2C5D5: Fpt_ChunkDescription(0xA5F2C5D5, Fpt_Chunk_Type.INT, "primary_model_enabled"),
            0x9D00C4D5: Fpt_ChunkDescription(0x9D00C4D5, Fpt_Chunk_Type.STRING, "primary_model_path"),
            0x8FF8BFD5: Fpt_ChunkDescription(0x8FF8BFD5, Fpt_Chunk_Type.INT, "primary_model_data_len"),
            0x9600CED5: Fpt_ChunkDescription(0x9600CED5, Fpt_Chunk_Type.RAWDATA, "primary_model_data"),
            0xA5F2C5D2: Fpt_ChunkDescription(0xA5F2C5D2, Fpt_Chunk_Type.INT, "secondary_model_enabled_at_z_distance"),
            0x9D00C4D2: Fpt_ChunkDescription(0x9D00C4D2, Fpt_Chunk_Type.STRING, "secondary_model_path"),
            0x8FF8BFD2: Fpt_ChunkDescription(0x8FF8BFD2, Fpt_Chunk_Type.INT, "secondary_model_data_len"),
            0x9600CED2: Fpt_ChunkDescription(0x9600CED2, Fpt_Chunk_Type.RAWDATA, "secondary_model_data"),
            0xA5F2C5D1: Fpt_ChunkDescription(0xA5F2C5D1, Fpt_Chunk_Type.INT, "mask_model_enabled"),
            0x9D00C4D1: Fpt_ChunkDescription(0x9D00C4D1, Fpt_Chunk_Type.STRING, "mask_model_path"),
            0x8FF8BFD1: Fpt_ChunkDescription(0x8FF8BFD1, Fpt_Chunk_Type.INT, "mask_model_data_len"),
            0x9600CED1: Fpt_ChunkDescription(0x9600CED1, Fpt_Chunk_Type.RAWDATA, "mask_model_data"),
            0x9CF1BDD3: Fpt_ChunkDescription(0x9CF1BDD3, Fpt_Chunk_Type.INT, "reflection_use_primary_model"),
            0xA5F2C5D3: Fpt_ChunkDescription(0xA5F2C5D3, Fpt_Chunk_Type.INT, "reflection_model_enabled"),
            0x9D00C4D3: Fpt_ChunkDescription(0x9D00C4D3, Fpt_Chunk_Type.STRING, "reflection_model_path"),
            0x8FF8BFD3: Fpt_ChunkDescription(0x8FF8BFD3, Fpt_Chunk_Type.INT, "reflection_model_data_len"),
            0x9600CED3: Fpt_ChunkDescription(0x9600CED3, Fpt_Chunk_Type.RAWDATA, "reflection_model_data"),
            0x8FEEC3E2: Fpt_ChunkDescription(0x8FEEC3E2, Fpt_Chunk_Type.INT, "nb_collision_shapes"),
            0x93FBC3E2: Fpt_ChunkDescription(0x93FBC3E2, Fpt_Chunk_Type.INT, "collision_shapes_enabled"),
            0x9DFCC3E2: Fpt_ChunkDescription(0x9DFCC3E2, Fpt_Chunk_Type.COLLISIONDATA, "collision_shapes_data"),
            0xA1EDD1D5: Fpt_ChunkDescription(0xA1EDD1D5, Fpt_Chunk_Type.STRING, "linked_path"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
            }

    def __init__(self):
        self.obj__class = "Pin_Model"
        self.obj__chunks = Fpt_PinModel_Reader.CHUNK_DICTIONARY


class Fpt_ImageList_Reader(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.STRING, "name"),
            0xA8EDD1E1: Fpt_ChunkDescription(0xA8EDD1E1, Fpt_Chunk_Type.STRINGLIST, "images"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
            }

    def __init__(self):
        self.obj__class = "Image_List"
        self.obj__chunks = Fpt_ImageList_Reader.CHUNK_DICTIONARY


class Fpt_LightList_Reader(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.STRING, "name"),
            0xA8EDD1E1: Fpt_ChunkDescription(0xA8EDD1E1, Fpt_Chunk_Type.STRINGLIST, "lights"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
            }

    def __init__(self):
        self.obj__class = "Light_List"
        self.obj__chunks = Fpt_LightList_Reader.CHUNK_DICTIONARY


class Fpt_DmdFont_Reader(Fpt_Data_Reader):
    def __init__(self):
        self.obj__class = "Dmd_Font"

    def read(self, stream):
        self.val__raw = stream.read()


class Fpt_Table_MAC_Reader(Fpt_Data_Reader):
    def __init__(self):
        self.obj__class = "Table_MAC"

    def read(self, stream):
        self.val__mac = stream.read(16)



###############################################################################
class FptTableElementReader(Fpt_Data_Reader):
    def read(self, stream):
        value = stream.read_dword()
        if value == FptElementType.SURFACE:
            reader = FptTableElementReader_SURFACE(self)
        elif value == FptElementType.LIGHT_ROUND:
            reader = FptTableElementReader_LIGHT_ROUND(self)
        elif value == FptElementType.LIGHT_SHAPEABLE:
            reader = FptTableElementReader_LIGHT_SHAPEABLE(self)
        elif value == FptElementType.OBJECT_PEG:
            reader = FptTableElementReader_OBJECT_PEG(self)
        elif value == FptElementType.CONTROL_FLIPPER:
            reader = FptTableElementReader_CONTROL_FLIPPER(self)
        elif value == FptElementType.CONTROL_BUMPER:
            reader = FptTableElementReader_CONTROL_BUMPER(self)
        elif value == FptElementType.TARGET_LEAF:
            reader = FptTableElementReader_TARGET_LEAF(self)
        elif value == FptElementType.TARGET_DROP:
            reader = FptTableElementReader_TARGET_DROP(self)
        elif value == FptElementType.CONTROL_PLUNGER:
            reader = FptTableElementReader_CONTROL_PLUNGER(self)
        elif value == FptElementType.RUBBER_ROUND:
            reader = FptTableElementReader_RUBBER_ROUND(self)
        elif value == FptElementType.RUBBER_SHAPEABLE:
            reader = FptTableElementReader_RUBBER_SHAPEABLE(self)
        elif value == FptElementType.OBJECT_ORNAMENT:
            reader = FptTableElementReader_OBJECT_ORNAMENT(self)
        elif value == FptElementType.GUIDE_WALL:
            reader = FptTableElementReader_GUIDE_WALL(self)
        elif value == FptElementType.SPECIAL_TIMER:
            reader = FptTableElementReader_SPECIAL_TIMER(self)
        elif value == FptElementType.SPECIAL_DECAL:
            reader = FptTableElementReader_SPECIAL_DECAL(self)
        elif value == FptElementType.CONTROL_KICKER:
            reader = FptTableElementReader_CONTROL_KICKER(self)
        elif value == FptElementType.GUIDE_LANE:
            reader = FptTableElementReader_GUIDE_LANE(self)
        elif value == FptElementType.RUBBER_MODEL:
            reader = FptTableElementReader_RUBBER_MODEL(self)
        elif value == FptElementType.TRIGGER_TRIGGER:
            reader = FptTableElementReader_TRIGGER_TRIGGER(self)
        elif value == FptElementType.LIGHT_FLASHER:
            reader = FptTableElementReader_LIGHT_FLASHER(self)
        elif value == FptElementType.GUIDE_WIRE:
            reader = FptTableElementReader_GUIDE_WIRE(self)
        elif value == FptElementType.DISPLAY_DISPREEL:
            reader = FptTableElementReader_DISPLAY_DISPREEL(self)
        elif value == FptElementType.DISPLAY_HUDREEL:
            reader = FptTableElementReader_DISPLAY_HUDREEL(self)
        elif value == FptElementType.SPECIAL_OVERLAY:
            reader = FptTableElementReader_SPECIAL_OVERLAY(self)
        elif value == FptElementType.LIGHT_BULB:
            reader = FptTableElementReader_LIGHT_BULB(self)
        elif value == FptElementType.TRIGGER_GATE:
            reader = FptTableElementReader_TRIGGER_GATE(self)
        elif value == FptElementType.TRIGGER_SPINNER:
            reader = FptTableElementReader_TRIGGER_SPINNER(self)
        elif value == FptElementType.TOY_CUSTOM:
            reader = FptTableElementReader_TOY_CUSTOM(self)
        elif value == FptElementType.LIGHT_SEQUENCER:
            reader = FptTableElementReader_LIGHT_SEQUENCER(self)
        elif value == FptElementType.DISPLAY_SEGMENT:
            reader = FptTableElementReader_DISPLAY_SEGMENT(self)
        elif value == FptElementType.DISPLAY_HUDSEGMENT:
            reader = FptTableElementReader_DISPLAY_HUDSEGMENT(self)
        elif value == FptElementType.DISPLAY_DMD:
            reader = FptTableElementReader_DISPLAY_DMD(self)
        elif value == FptElementType.DISPLAY_HUDDMD:
            reader = FptTableElementReader_DISPLAY_HUDDMD(self)
        elif value == FptElementType.CONTROL_DIVERTER:
            reader = FptTableElementReader_CONTROL_DIVERTER(self)
        elif value == FptElementType.SPECIAL_STA:
            reader = FptTableElementReader_SPECIAL_STA(self)
        elif value == FptElementType.CONTROL_AUTOPLUNGER:
            reader = FptTableElementReader_CONTROL_AUTOPLUNGER(self)
        elif value == FptElementType.TARGET_ROTO:
            reader = FptTableElementReader_TARGET_ROTO(self)
        elif value == FptElementType.CONTROL_POPUP:
            reader = FptTableElementReader_CONTROL_POPUP(self)
        elif value == FptElementType.RAMP_MODEL:
            reader = FptTableElementReader_RAMP_MODEL(self)
        elif value == FptElementType.RAMP_WIRE:
            reader = FptTableElementReader_RAMP_WIRE(self)
        elif value == FptElementType.TARGET_SWING:
            reader = FptTableElementReader_TARGET_SWING(self)
        elif value == FptElementType.RAMP_RAMP:
            reader = FptTableElementReader_RAMP_RAMP(self)
        elif value == FptElementType.TOY_SPINNINGDISK:
            reader = FptTableElementReader_TOY_SPINNINGDISK(self)
        elif value == FptElementType.LIGHT_LIGHTIMAGE:
            reader = FptTableElementReader_LIGHT_LIGHTIMAGE(self)
        elif value == FptElementType.KICKER_EMKICKER:
            reader = FptTableElementReader_KICKER_EMKICKER(self)
        elif value == FptElementType.LIGHT_HUDLIGHTIMAGE:
            reader = FptTableElementReader_LIGHT_HUDLIGHTIMAGE(self)
        elif value == FptElementType.TRIGGER_OPTO:
            reader = FptTableElementReader_TRIGGER_OPTO(self)
        elif value == FptElementType.TARGET_VARI:
            reader = FptTableElementReader_TARGET_VARI(self)
        elif value == FptElementType.TOY_HOLOGRAM:
            reader = FptTableElementReader_TOY_HOLOGRAM(self)
        else:
            print("#DEBUG", "unknown element type", value)
            pass

        if reader:
            reader.read(stream, self)


###############################################################################
class FptTableElementReader_SURFACE(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x91EDBEE1: Fpt_ChunkDescription(0x91EDBEE1, Fpt_Chunk_Type.INT, "display_image_in_editor"),
            0x9DF2CFD1: Fpt_ChunkDescription(0x9DF2CFD1, Fpt_Chunk_Type.COLOR, "top_color"),
            0xA2F4C9D1: Fpt_ChunkDescription(0xA2F4C9D1, Fpt_Chunk_Type.STRING, "top_texture"),
            0x91EDCFE2: Fpt_ChunkDescription(0x91EDCFE2, Fpt_Chunk_Type.INT, "cookie_cut"),
            0x95F4C2D2: Fpt_ChunkDescription(0x95F4C2D2, Fpt_Chunk_Type.INT, "sphere_map_the_top"),
            0x9DF2CFD2: Fpt_ChunkDescription(0x9DF2CFD2, Fpt_Chunk_Type.COLOR, "side_color"),
            0xA2F4C9D2: Fpt_ChunkDescription(0xA2F4C9D2, Fpt_Chunk_Type.STRING, "side_texture"),
            0x9C00C0D1: Fpt_ChunkDescription(0x9C00C0D1, Fpt_Chunk_Type.INT, "transparency"),
            0x99F2BEDD: Fpt_ChunkDescription(0x99F2BEDD, Fpt_Chunk_Type.FLOAT, "top_height"),
            0x95F2D0DD: Fpt_ChunkDescription(0x95F2D0DD, Fpt_Chunk_Type.FLOAT, "bottom_height"),
            0x99E8BED8: Fpt_ChunkDescription(0x99E8BED8, Fpt_Chunk_Type.INT, "material_type"),
            0x96F4C2D2: Fpt_ChunkDescription(0x96F4C2D2, Fpt_Chunk_Type.INT, "sphere_map_the_side"),
            0x97F2C4DF: Fpt_ChunkDescription(0x97F2C4DF, Fpt_Chunk_Type.INT, "flat_shading"),
            0x9100C6D5: Fpt_ChunkDescription(0x9100C6D5, Fpt_Chunk_Type.INT, "surface_is_a_playfield"),
            0x9DFBCDD3: Fpt_ChunkDescription(0x9DFBCDD3, Fpt_Chunk_Type.INT, "reflects_off_playfield"),
            0x9A00C5E0: Fpt_ChunkDescription(0x9A00C5E0, Fpt_Chunk_Type.STRING, "enamel_map"),
            0x95E9BED3: Fpt_ChunkDescription(0x95E9BED3, Fpt_Chunk_Type.INT, "reflect_texture"),
            0x97ECBFD3: Fpt_ChunkDescription(0x97ECBFD3, Fpt_Chunk_Type.STRING, "playfield"),
            0x99F2C0E1: Fpt_ChunkDescription(0x99F2C0E1, Fpt_Chunk_Type.INT, "dropped"),
            0x9DF5C3E2: Fpt_ChunkDescription(0x9DF5C3E2, Fpt_Chunk_Type.INT, "collidable"),
            0x97FDC4D3: Fpt_ChunkDescription(0x97FDC4D3, Fpt_Chunk_Type.INT, "render_object"),
            0x95EBCDDD: Fpt_ChunkDescription(0x95EBCDDD, Fpt_Chunk_Type.INT, "generate_hit_event"),
            0x95F3C2D2: Fpt_ChunkDescription(0x95F3C2D2, Fpt_Chunk_Type.CHUNKLIST, "shape_point"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0xA1EDC5D2: Fpt_ChunkDescription(0xA1EDC5D2, Fpt_Chunk_Type.INT, "smooth"),
            0xA2F3C6D2: Fpt_ChunkDescription(0xA2F3C6D2, Fpt_Chunk_Type.RAWDATA, "unknown_0xA2F3C6D2"), # slingshot ???
            0xA8FCC6D2: Fpt_ChunkDescription(0xA8FCC6D2, Fpt_Chunk_Type.RAWDATA, "unknown_0xA8FCC6D2"), # single_leaf ???
            0x99E9BEE4: Fpt_ChunkDescription(0x99E9BEE4, Fpt_Chunk_Type.INT, "automatic_texture_coordinate"),
            0x9AFEBAD1: Fpt_ChunkDescription(0x9AFEBAD1, Fpt_Chunk_Type.FLOAT, "texture_coordinate"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_2"
        owner.obj__id = FptElementType.SURFACE
        owner.obj__name = "Surface"
        self.obj__chunks = FptTableElementReader_SURFACE.CHUNK_DICTIONARY


class FptTableElementReader_LIGHT_ROUND(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0x9BFCCFDD: Fpt_ChunkDescription(0x9BFCCFDD, Fpt_Chunk_Type.VECTOR2D, "glow_center"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"),
            0x96F3CDD9: Fpt_ChunkDescription(0x96F3CDD9, Fpt_Chunk_Type.STRING, "lens_texture"),
            0x9D00C9E1: Fpt_ChunkDescription(0x9D00C9E1, Fpt_Chunk_Type.INT, "diameter"),
            0x9DF2CFD9: Fpt_ChunkDescription(0x9DF2CFD9, Fpt_Chunk_Type.COLOR, "lit_color"),
            0xA6ECBFE4: Fpt_ChunkDescription(0xA6ECBFE4, Fpt_Chunk_Type.INT, "auto_set_unlit_color"),
            0x9DF2CFD0: Fpt_ChunkDescription(0x9DF2CFD0, Fpt_Chunk_Type.COLOR, "unlit_color"),
            0xA5F8BBE3: Fpt_ChunkDescription(0xA5F8BBE3, Fpt_Chunk_Type.INT, "border_width"),
            0x9DF2CFE3: Fpt_ChunkDescription(0x9DF2CFE3, Fpt_Chunk_Type.COLOR, "border_color"),
            0x91EDCFE2: Fpt_ChunkDescription(0x91EDCFE2, Fpt_Chunk_Type.INT, "cookie_cut"),
            0x96FDD1D3: Fpt_ChunkDescription(0x96FDD1D3, Fpt_Chunk_Type.INT, "glow_radius"),
            0x9600BED2: Fpt_ChunkDescription(0x9600BED2, Fpt_Chunk_Type.INT, "state"),
            0x95F3C9E3: Fpt_ChunkDescription(0x95F3C9E3, Fpt_Chunk_Type.INT, "blink_interval"),
            0x9600C2E3: Fpt_ChunkDescription(0x9600C2E3, Fpt_Chunk_Type.STRING, "blink_pattern"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_3"
        owner.obj__id = FptElementType.LIGHT_ROUND
        owner.obj__name = "Light_Round"
        self.obj__chunks = FptTableElementReader_LIGHT_ROUND.CHUNK_DICTIONARY


class FptTableElementReader_LIGHT_SHAPEABLE(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "texture_position"),
            0x9BFCCFDD: Fpt_ChunkDescription(0x9BFCCFDD, Fpt_Chunk_Type.VECTOR2D, "halo_position"),
            0x96F3CDD9: Fpt_ChunkDescription(0x96F3CDD9, Fpt_Chunk_Type.STRING, "lens_texture"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"), ## corrected
            #0xB9ADAAAD: Fpt_ChunkDescription(0xB9ADAAAD, Fpt_Chunk_Type.STRING, "surface"), ## wrong chunk id
            0x9DF2CFD9: Fpt_ChunkDescription(0x9DF2CFD9, Fpt_Chunk_Type.COLOR, "lit_color"),
            0xA6ECBFE4: Fpt_ChunkDescription(0xA6ECBFE4, Fpt_Chunk_Type.INT, "auto_set_unlit_color"),
            0x9DF2CFD0: Fpt_ChunkDescription(0x9DF2CFD0, Fpt_Chunk_Type.COLOR, "unlit_color"),
            0xA5F8BBE3: Fpt_ChunkDescription(0xA5F8BBE3, Fpt_Chunk_Type.INT, "border_width"),
            0x9DF2CFE3: Fpt_ChunkDescription(0x9DF2CFE3, Fpt_Chunk_Type.COLOR, "border_color"),
            0x91EDCFE2: Fpt_ChunkDescription(0x91EDCFE2, Fpt_Chunk_Type.INT, "cookie_cut"),
            0x96FDD1D3: Fpt_ChunkDescription(0x96FDD1D3, Fpt_Chunk_Type.INT, "glow_radius"),
            0x9600BED2: Fpt_ChunkDescription(0x9600BED2, Fpt_Chunk_Type.INT, "state"),
            0x95F3C9E3: Fpt_ChunkDescription(0x95F3C9E3, Fpt_Chunk_Type.INT, "blink_interval"),
            0x9600C2E3: Fpt_ChunkDescription(0x9600C2E3, Fpt_Chunk_Type.STRING, "blink_pattern"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            0x95F3C2D2: Fpt_ChunkDescription(0x95F3C2D2, Fpt_Chunk_Type.CHUNKLIST, "shape_point"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0xA1EDC5D2: Fpt_ChunkDescription(0xA1EDC5D2, Fpt_Chunk_Type.INT, "smooth"),
            0xA2F3C6D2: Fpt_ChunkDescription(0xA2F3C6D2, Fpt_Chunk_Type.RAWDATA, "unknown_0xA2F3C6D2"), # slingshot ???
            0xA8FCC6D2: Fpt_ChunkDescription(0xA8FCC6D2, Fpt_Chunk_Type.RAWDATA, "unknown_0xA8FCC6D2"), # single_leaf ???
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
            }


    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_4"
        owner.obj__id = FptElementType.LIGHT_SHAPEABLE
        owner.obj__name = "Light_Shapeable"
        self.obj__chunks = FptTableElementReader_LIGHT_SHAPEABLE.CHUNK_DICTIONARY


class FptTableElementReader_OBJECT_PEG(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0x9DFDC3D8: Fpt_ChunkDescription(0x9DFDC3D8, Fpt_Chunk_Type.STRING, "model"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"),
            0xA300C5DC: Fpt_ChunkDescription(0xA300C5DC, Fpt_Chunk_Type.STRING, "texture"),
            0x99F4C2D2: Fpt_ChunkDescription(0x99F4C2D2, Fpt_Chunk_Type.INT, "sphere_mapping"),
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "color"),
            0xA8F3C0D6: Fpt_ChunkDescription(0xA8F3C0D6, Fpt_Chunk_Type.INT, "mask_as_ornamental"),
            0xA8EDC3D3: Fpt_ChunkDescription(0xA8EDC3D3, Fpt_Chunk_Type.INT, "rotation"),
            0x96E8C0E2: Fpt_ChunkDescription(0x96E8C0E2, Fpt_Chunk_Type.INT, "crystal"),
            0x9DFBCDD3: Fpt_ChunkDescription(0x9DFBCDD3, Fpt_Chunk_Type.INT, "reflects_off_playfield"),
            0xA5F3BFDD: Fpt_ChunkDescription(0xA5F3BFDD, Fpt_Chunk_Type.STRING, "sound_when_hit"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_6"
        owner.obj__id = FptElementType.OBJECT_PEG
        owner.obj__name = "Object_Peg"
        self.obj__chunks = FptTableElementReader_OBJECT_PEG.CHUNK_DICTIONARY


class FptTableElementReader_CONTROL_FLIPPER(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0x9DFDC3D8: Fpt_ChunkDescription(0x9DFDC3D8, Fpt_Chunk_Type.STRING, "model"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"),
            0xA300C5DC: Fpt_ChunkDescription(0xA300C5DC, Fpt_Chunk_Type.STRING, "texture"),
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "color"),
            0xA900BED2: Fpt_ChunkDescription(0xA900BED2, Fpt_Chunk_Type.INT, "start_angle"),
            0xA1FABED2: Fpt_ChunkDescription(0xA1FABED2, Fpt_Chunk_Type.INT, "strength"),
            0xA2EABFE4: Fpt_ChunkDescription(0xA2EABFE4, Fpt_Chunk_Type.INT, "swing"),
            0x9700C6E0: Fpt_ChunkDescription(0x9700C6E0, Fpt_Chunk_Type.INT, "elasticity"),
            0x9BEEBDDF: Fpt_ChunkDescription(0x9BEEBDDF, Fpt_Chunk_Type.STRING, "flipper_up_sound"),
            0x9BEECEDF: Fpt_ChunkDescription(0x9BEECEDF, Fpt_Chunk_Type.STRING, "flipper_down_sound"),
            0x9DFBCDD3: Fpt_ChunkDescription(0x9DFBCDD3, Fpt_Chunk_Type.INT, "reflects_off_playfield"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_7"
        owner.obj__id = FptElementType.CONTROL_FLIPPER
        owner.obj__name = "Control_Flipper"
        self.obj__chunks = FptTableElementReader_CONTROL_FLIPPER.CHUNK_DICTIONARY


class FptTableElementReader_CONTROL_BUMPER(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0xA5F2C5E2: Fpt_ChunkDescription(0xA5F2C5E2, Fpt_Chunk_Type.STRING, "model_cap"),
            0xA5F2C5E3: Fpt_ChunkDescription(0xA5F2C5E3, Fpt_Chunk_Type.STRING, "model_base"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"),
            0x96F3CDD9: Fpt_ChunkDescription(0x96F3CDD9, Fpt_Chunk_Type.STRING, "cap_texture"),
            0xA0EED1D5: Fpt_ChunkDescription(0xA0EED1D5, Fpt_Chunk_Type.INT, "passive"),
            0x9EEED1DD: Fpt_ChunkDescription(0x9EEED1DD, Fpt_Chunk_Type.INT, "trigger_skirt"),
            0x9AFEC7D2: Fpt_ChunkDescription(0x9AFEC7D2, Fpt_Chunk_Type.COLOR, "skirt_color"),
            0x9DF2CFD9: Fpt_ChunkDescription(0x9DF2CFD9, Fpt_Chunk_Type.COLOR, "lit_color"),
            0xA6ECBFE4: Fpt_ChunkDescription(0xA6ECBFE4, Fpt_Chunk_Type.INT, "auto_set_unlit_color"),
            0xA1FDC0D6: Fpt_ChunkDescription(0xA1FDC0D6, Fpt_Chunk_Type.INT, "ordered_halo_glow"),
            0x9DF2CFD0: Fpt_ChunkDescription(0x9DF2CFD0, Fpt_Chunk_Type.COLOR, "unlit_color"),
            0x9DF2CFE3: Fpt_ChunkDescription(0x9DF2CFE3, Fpt_Chunk_Type.COLOR, "base_color"),
            0xA8EDC3D3: Fpt_ChunkDescription(0xA8EDC3D3, Fpt_Chunk_Type.RAWDATA, "unknown_0xA8EDC3D3"),
            0x96E8C0E2: Fpt_ChunkDescription(0x96E8C0E2, Fpt_Chunk_Type.INT, "crystal"),
            0x9DFBCDD3: Fpt_ChunkDescription(0x9DFBCDD3, Fpt_Chunk_Type.INT, "reflects_off_playfield"),
            0xA1FABED2: Fpt_ChunkDescription(0xA1FABED2, Fpt_Chunk_Type.INT, "strength"),
            0xA5F3BFE3: Fpt_ChunkDescription(0xA5F3BFE3, Fpt_Chunk_Type.STRING, "solenoid_sound"),
            0x95F9BBDF: Fpt_ChunkDescription(0x95F9BBDF, Fpt_Chunk_Type.INT, "flash_when_hit"),
            0x9600BED2: Fpt_ChunkDescription(0x9600BED2, Fpt_Chunk_Type.INT, "state"),
            0x95F3C9E3: Fpt_ChunkDescription(0x95F3C9E3, Fpt_Chunk_Type.INT, "blink_interval"),
            0x9600C2E3: Fpt_ChunkDescription(0x9600C2E3, Fpt_Chunk_Type.STRING, "blink_pattern"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_8"
        owner.obj__id = FptElementType.CONTROL_BUMPER
        owner.obj__name = "Control_Bumper"
        self.obj__chunks = FptTableElementReader_CONTROL_BUMPER.CHUNK_DICTIONARY


class FptTableElementReader_TARGET_LEAF(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0x9DFDC3D8: Fpt_ChunkDescription(0x9DFDC3D8, Fpt_Chunk_Type.STRING, "model"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"),
            0xA300C5DC: Fpt_ChunkDescription(0xA300C5DC, Fpt_Chunk_Type.STRING, "texture"),
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "color"),
            0xA8EDC3D3: Fpt_ChunkDescription(0xA8EDC3D3, Fpt_Chunk_Type.INT, "rotation"),
            0x9DFBCDD3: Fpt_ChunkDescription(0x9DFBCDD3, Fpt_Chunk_Type.INT, "reflects_off_playfield"),
            0xA5F3BFD1: Fpt_ChunkDescription(0xA5F3BFD1, Fpt_Chunk_Type.STRING, "sound_when_hit"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_10"
        owner.obj__id = FptElementType.TARGET_LEAF
        owner.obj__name = "Target_Leaf"
        self.obj__chunks = FptTableElementReader_TARGET_LEAF.CHUNK_DICTIONARY


class FptTableElementReader_TARGET_DROP(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0x9DFDC3D8: Fpt_ChunkDescription(0x9DFDC3D8, Fpt_Chunk_Type.STRING, "model"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"),
            0xA300C5DC: Fpt_ChunkDescription(0xA300C5DC, Fpt_Chunk_Type.STRING, "texture"),
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "color"),
            0xA8EDC3D3: Fpt_ChunkDescription(0xA8EDC3D3, Fpt_Chunk_Type.INT, "rotation"),
            0x9DFBCDD3: Fpt_ChunkDescription(0x9DFBCDD3, Fpt_Chunk_Type.INT, "reflects_off_playfield"),
            0x9035D306: Fpt_ChunkDescription(0x9035D306, Fpt_Chunk_Type.STRING, "sound_when_hit"),
            0x9035D2F8: Fpt_ChunkDescription(0x9035D2F8, Fpt_Chunk_Type.STRING, "sound_when_reset"),
            0x8035E308: Fpt_ChunkDescription(0x8035E308, Fpt_Chunk_Type.INT, "bank_count"),
            0x9133D308: Fpt_ChunkDescription(0x9133D308, Fpt_Chunk_Type.INT, "bank_spacing"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_11"
        owner.obj__id = FptElementType.TARGET_DROP
        owner.obj__name = "Target_Drop"
        self.obj__chunks = FptTableElementReader_TARGET_DROP.CHUNK_DICTIONARY


class FptTableElementReader_CONTROL_PLUNGER(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"), ## added ???
            0x9DFDC3D8: Fpt_ChunkDescription(0x9DFDC3D8, Fpt_Chunk_Type.STRING, "model"),
            0xA300C5DC: Fpt_ChunkDescription(0xA300C5DC, Fpt_Chunk_Type.STRING, "texture"),
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "plunger_color"),
            0x9DF2CFE2: Fpt_ChunkDescription(0x9DF2CFE2, Fpt_Chunk_Type.COLOR, "face_plate_color"),
            0xA1FABED2: Fpt_ChunkDescription(0xA1FABED2, Fpt_Chunk_Type.INT, "strength"),
            0x9DFBCDD3: Fpt_ChunkDescription(0x9DFBCDD3, Fpt_Chunk_Type.INT, "reflects_off_playfield"),
            0x95ECCFCF: Fpt_ChunkDescription(0x95ECCFCF, Fpt_Chunk_Type.INT, "include_v_cut"),
            0x90E9CFCF: Fpt_ChunkDescription(0x90E9CFCF, Fpt_Chunk_Type.VECTOR2D, "v_cut_position"),
            0x9BFCC6CF: Fpt_ChunkDescription(0x9BFCC6CF, Fpt_Chunk_Type.INT, "v_cut_lenght"),
            0xA2F4C9CF: Fpt_ChunkDescription(0xA2F4C9CF, Fpt_Chunk_Type.STRING, "v_cut_texture"),
            0x9DF2CFCF: Fpt_ChunkDescription(0x9DF2CFCF, Fpt_Chunk_Type.COLOR, "v_cut_color"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_12"
        owner.obj__id = FptElementType.CONTROL_PLUNGER
        owner.obj__name = "Control_Plunger"
        self.obj__chunks = FptTableElementReader_CONTROL_PLUNGER.CHUNK_DICTIONARY


class FptTableElementReader_RUBBER_ROUND(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0xA4F1B9D1: Fpt_ChunkDescription(0xA4F1B9D1, Fpt_Chunk_Type.INT, "subtype"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"),
            0x96FBCCD6: Fpt_ChunkDescription(0x96FBCCD6, Fpt_Chunk_Type.INT, "offset"),
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "color"),
            0x9700C6E0: Fpt_ChunkDescription(0x9700C6E0, Fpt_Chunk_Type.INT, "elasticity"),
            0x9DFBCDD3: Fpt_ChunkDescription(0x9DFBCDD3, Fpt_Chunk_Type.INT, "reflects_off_playfield"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_13"
        owner.obj__id = FptElementType.RUBBER_ROUND
        owner.obj__name = "Rubber_Round"
        self.obj__chunks = FptTableElementReader_RUBBER_ROUND.CHUNK_DICTIONARY


class FptTableElementReader_RUBBER_SHAPEABLE(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"),
            0x9DF2CFD9: Fpt_ChunkDescription(0x9DF2CFD9, Fpt_Chunk_Type.COLOR, "color"),
            0x96FBCCD6: Fpt_ChunkDescription(0x96FBCCD6, Fpt_Chunk_Type.INT, "offset"),
            0x9DFBCDD3: Fpt_ChunkDescription(0x9DFBCDD3, Fpt_Chunk_Type.INT, "reflects_off_playfield"),
            0xA1FABED2: Fpt_ChunkDescription(0xA1FABED2, Fpt_Chunk_Type.INT, "strength"),
            0x9700C6E0: Fpt_ChunkDescription(0x9700C6E0, Fpt_Chunk_Type.INT, "elasticity"),
            0xA5F3BFD2: Fpt_ChunkDescription(0xA5F3BFD2, Fpt_Chunk_Type.STRING, "sound_slingshot"),
            0x95F3C2D2: Fpt_ChunkDescription(0x95F3C2D2, Fpt_Chunk_Type.CHUNKLIST, "shape_point"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0xA1EDC5D2: Fpt_ChunkDescription(0xA1EDC5D2, Fpt_Chunk_Type.INT, "smooth"),
            0xA2F3C6D2: Fpt_ChunkDescription(0xA2F3C6D2, Fpt_Chunk_Type.INT, "slingshot"),
            0xA8FCC6D2: Fpt_ChunkDescription(0xA8FCC6D2, Fpt_Chunk_Type.INT, "single_leaf"),
            0x95F3BCE0: Fpt_ChunkDescription(0x95F3BCE0, Fpt_Chunk_Type.INT, "event_id"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_14"
        owner.obj__id = FptElementType.RUBBER_SHAPEABLE
        owner.obj__name = "Rubber_Shapeable"
        self.obj__chunks = FptTableElementReader_RUBBER_SHAPEABLE.CHUNK_DICTIONARY


class FptTableElementReader_OBJECT_ORNAMENT(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0x9DFDC3D8: Fpt_ChunkDescription(0x9DFDC3D8, Fpt_Chunk_Type.STRING, "model"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"),
            0xA300C5DC: Fpt_ChunkDescription(0xA300C5DC, Fpt_Chunk_Type.STRING, "texture"),
            0x99F4C2D2: Fpt_ChunkDescription(0x99F4C2D2, Fpt_Chunk_Type.INT, "sphere_mapping"),
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "color"),
            0xA8F3C0D6: Fpt_ChunkDescription(0xA8F3C0D6, Fpt_Chunk_Type.INT, "mask_as_ornamental"),
            0xA8EDC3D3: Fpt_ChunkDescription(0xA8EDC3D3, Fpt_Chunk_Type.INT, "rotation"),
            0x96FBCCD6: Fpt_ChunkDescription(0x96FBCCD6, Fpt_Chunk_Type.INT, "offset"),
            0x9DFBCDD3: Fpt_ChunkDescription(0x9DFBCDD3, Fpt_Chunk_Type.INT, "reflects_off_playfield"),
            0x97ECBFD3: Fpt_ChunkDescription(0x97ECBFD3, Fpt_Chunk_Type.STRING, "playfield"),
            0x9A00C5E0: Fpt_ChunkDescription(0x9A00C5E0, Fpt_Chunk_Type.STRING, "enamel_map"), #
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_15"
        owner.obj__id = FptElementType.OBJECT_ORNAMENT
        owner.obj__name = "Object_Ornament"
        self.obj__chunks = FptTableElementReader_OBJECT_ORNAMENT.CHUNK_DICTIONARY


class FptTableElementReader_GUIDE_WALL(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"),
            0x91EDBEE1: Fpt_ChunkDescription(0x91EDBEE1, Fpt_Chunk_Type.INT, "display_image_in_editor"),
            0x9DF2CFD1: Fpt_ChunkDescription(0x9DF2CFD1, Fpt_Chunk_Type.COLOR, "top_color"),
            0xA2F4C9D1: Fpt_ChunkDescription(0xA2F4C9D1, Fpt_Chunk_Type.STRING, "top_texture"),
            0x91EDCFE2: Fpt_ChunkDescription(0x91EDCFE2, Fpt_Chunk_Type.INT, "cookie_cut"),
            0x95F4C2D2: Fpt_ChunkDescription(0x95F4C2D2, Fpt_Chunk_Type.INT, "sphere_map_the_top"),
            0x9DF2CFD2: Fpt_ChunkDescription(0x9DF2CFD2, Fpt_Chunk_Type.COLOR, "side_color"),
            0xA2F4C9D2: Fpt_ChunkDescription(0xA2F4C9D2, Fpt_Chunk_Type.STRING, "side_texture"),
            0x96F4C2D2: Fpt_ChunkDescription(0x96F4C2D2, Fpt_Chunk_Type.INT, "sphere_map_the_side"),
            0x97F2C4DF: Fpt_ChunkDescription(0x97F2C4DF, Fpt_Chunk_Type.INT, "flat_shading"),
            0x9C00C0D1: Fpt_ChunkDescription(0x9C00C0D1, Fpt_Chunk_Type.INT, "transparency"),
            0xA2F8CDDD: Fpt_ChunkDescription(0xA2F8CDDD, Fpt_Chunk_Type.FLOAT, "height"),
            0x95FDC9CE: Fpt_ChunkDescription(0x95FDC9CE, Fpt_Chunk_Type.FLOAT, "width"),
            0x99E8BED8: Fpt_ChunkDescription(0x99E8BED8, Fpt_Chunk_Type.INT, "material_type"),
            0x9DFBCDD3: Fpt_ChunkDescription(0x9DFBCDD3, Fpt_Chunk_Type.INT, "reflects_off_playfield"),
            0x99F2C0E1: Fpt_ChunkDescription(0x99F2C0E1, Fpt_Chunk_Type.INT, "dropped"),
            0x9DF5C3E2: Fpt_ChunkDescription(0x9DF5C3E2, Fpt_Chunk_Type.INT, "collidable"),
            0x97FDC4D3: Fpt_ChunkDescription(0x97FDC4D3, Fpt_Chunk_Type.INT, "render_object"),
            0x95EBCDDD: Fpt_ChunkDescription(0x95EBCDDD, Fpt_Chunk_Type.INT, "generate_hit_event"),
            0x95F3C2D2: Fpt_ChunkDescription(0x95F3C2D2, Fpt_Chunk_Type.CHUNKLIST, "shape_point"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0xA1EDC5D2: Fpt_ChunkDescription(0xA1EDC5D2, Fpt_Chunk_Type.INT, "smooth"),
            0xA2F3C6D2: Fpt_ChunkDescription(0xA2F3C6D2, Fpt_Chunk_Type.RAWDATA, "unknown_0xA2F3C6D2"), # slingshot ???
            0xA8FCC6D2: Fpt_ChunkDescription(0xA8FCC6D2, Fpt_Chunk_Type.RAWDATA, "unknown_0xA8FCC6D2"), # single_leaf ???
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_16"
        owner.obj__id = FptElementType.GUIDE_WALL
        owner.obj__name = "Guide_Wall"
        self.obj__chunks = FptTableElementReader_GUIDE_WALL.CHUNK_DICTIONARY


class FptTableElementReader_SPECIAL_TIMER(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"), ## added ???
            0xA800C4E0: Fpt_ChunkDescription(0xA800C4E0, Fpt_Chunk_Type.INT, "enabled"),
            0x97EDC4DC: Fpt_ChunkDescription(0x97EDC4DC, Fpt_Chunk_Type.INT, "timer_interval"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_17"
        owner.obj__id = FptElementType.SPECIAL_TIMER
        owner.obj__name = "Special_Timer"
        self.obj__chunks = FptTableElementReader_SPECIAL_TIMER.CHUNK_DICTIONARY


class FptTableElementReader_SPECIAL_DECAL(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"),
            0xA300C5DC: Fpt_ChunkDescription(0xA300C5DC, Fpt_Chunk_Type.STRING, "texture"),
            0xA8EDC3D3: Fpt_ChunkDescription(0xA8EDC3D3, Fpt_Chunk_Type.INT, "rotation"),
            0xA2F8CDDD: Fpt_ChunkDescription(0xA2F8CDDD, Fpt_Chunk_Type.INT, "width"),
            0x95FDC9CE: Fpt_ChunkDescription(0x95FDC9CE, Fpt_Chunk_Type.INT, "height"),
            0x9C00C0D1: Fpt_ChunkDescription(0x9C00C0D1, Fpt_Chunk_Type.INT, "transparency"),
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "color"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_18"
        owner.obj__id = FptElementType.SPECIAL_DECAL
        owner.obj__name = "Special_Decal"
        self.obj__chunks = FptTableElementReader_SPECIAL_DECAL.CHUNK_DICTIONARY


class FptTableElementReader_CONTROL_KICKER(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0x9DFDC3D8: Fpt_ChunkDescription(0x9DFDC3D8, Fpt_Chunk_Type.STRING, "model"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"),
            0xA300C5DC: Fpt_ChunkDescription(0xA300C5DC, Fpt_Chunk_Type.STRING, "texture"),
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "color"),
            0xA8EDC3D3: Fpt_ChunkDescription(0xA8EDC3D3, Fpt_Chunk_Type.INT, "rotation"),
            0x99E8BEDA: Fpt_ChunkDescription(0x99E8BEDA, Fpt_Chunk_Type.INT, "type"),
            0xA1FABED2: Fpt_ChunkDescription(0xA1FABED2, Fpt_Chunk_Type.INT, "strength"),
            0xA5F2C5D3: Fpt_ChunkDescription(0xA5F2C5D3, Fpt_Chunk_Type.INT, "render_model"),
            0xA5F3BFDA: Fpt_ChunkDescription(0xA5F3BFDA, Fpt_Chunk_Type.STRING, "sound_when_hit"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_19"
        owner.obj__id = FptElementType.CONTROL_KICKER
        owner.obj__name = "Control_Kicker"
        self.obj__chunks = FptTableElementReader_CONTROL_KICKER.CHUNK_DICTIONARY


class FptTableElementReader_GUIDE_LANE(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0x9DFDC3D8: Fpt_ChunkDescription(0x9DFDC3D8, Fpt_Chunk_Type.STRING, "model"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"),
            0xA300C5DC: Fpt_ChunkDescription(0xA300C5DC, Fpt_Chunk_Type.STRING, "texture"),
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "color"),
            0xA8EDC3D3: Fpt_ChunkDescription(0xA8EDC3D3, Fpt_Chunk_Type.INT, "rotation"),
            0x96FBCCD6: Fpt_ChunkDescription(0x96FBCCD6, Fpt_Chunk_Type.INT, "offset"),
            0x96E8C0E2: Fpt_ChunkDescription(0x96E8C0E2, Fpt_Chunk_Type.INT, "crystal"),
            0x9A00C5E0: Fpt_ChunkDescription(0x9A00C5E0, Fpt_Chunk_Type.STRING, "enamel_map"), #
            0x9DFBCDD3: Fpt_ChunkDescription(0x9DFBCDD3, Fpt_Chunk_Type.INT, "reflects_off_playfield"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_20"
        owner.obj__id = FptElementType.GUIDE_LANE
        owner.obj__name = "Guide_Lane"
        self.obj__chunks = FptTableElementReader_GUIDE_LANE.CHUNK_DICTIONARY


class FptTableElementReader_RUBBER_MODEL(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0x9DFDC3D8: Fpt_ChunkDescription(0x9DFDC3D8, Fpt_Chunk_Type.STRING, "model"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"),
            0xA300C5DC: Fpt_ChunkDescription(0xA300C5DC, Fpt_Chunk_Type.STRING, "texture"),
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "color"),
            0xA8EDC3D3: Fpt_ChunkDescription(0xA8EDC3D3, Fpt_Chunk_Type.INT, "rotation"),
            0x96FBCCD6: Fpt_ChunkDescription(0x96FBCCD6, Fpt_Chunk_Type.INT, "offset"),
            0x9700C6E0: Fpt_ChunkDescription(0x9700C6E0, Fpt_Chunk_Type.INT, "elasticity"),
            0x9DFBCDD3: Fpt_ChunkDescription(0x9DFBCDD3, Fpt_Chunk_Type.INT, "reflects_off_playfield"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_21"
        owner.obj__id = FptElementType.RUBBER_MODEL
        owner.obj__name = "Rubber_Model"
        self.obj__chunks = FptTableElementReader_RUBBER_MODEL.CHUNK_DICTIONARY


class FptTableElementReader_TRIGGER_TRIGGER(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0x9DFDC3D8: Fpt_ChunkDescription(0x9DFDC3D8, Fpt_Chunk_Type.STRING, "model"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"),
            0xA300C5DC: Fpt_ChunkDescription(0xA300C5DC, Fpt_Chunk_Type.STRING, "texture"),
            0x99F4C2D2: Fpt_ChunkDescription(0x99F4C2D2, Fpt_Chunk_Type.INT, "sphere_mapping"),
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "color"),
            0xA8EDC3D3: Fpt_ChunkDescription(0xA8EDC3D3, Fpt_Chunk_Type.INT, "rotation"),
            0xA3F1C3D2: Fpt_ChunkDescription(0xA3F1C3D2, Fpt_Chunk_Type.INT, "sits_on_playfield"),
            0xA5F2C5D3: Fpt_ChunkDescription(0xA5F2C5D3, Fpt_Chunk_Type.INT, "render_model"),
            0x9DFBCDD3: Fpt_ChunkDescription(0x9DFBCDD3, Fpt_Chunk_Type.INT, "reflects_off_playfield"),
            0xA5F3BFD1: Fpt_ChunkDescription(0xA5F3BFD1, Fpt_Chunk_Type.STRING, "sound_when_hit"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_22"
        owner.obj__id = FptElementType.TRIGGER_TRIGGER
        owner.obj__name = "Trigger_Trigger"
        self.obj__chunks = FptTableElementReader_TRIGGER_TRIGGER.CHUNK_DICTIONARY


class FptTableElementReader_LIGHT_FLASHER(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0x9DFDC3D8: Fpt_ChunkDescription(0x9DFDC3D8, Fpt_Chunk_Type.STRING, "model"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"),
            0x9DF2CFD9: Fpt_ChunkDescription(0x9DF2CFD9, Fpt_Chunk_Type.COLOR, "lit_color"),
            0xA6ECBFE4: Fpt_ChunkDescription(0xA6ECBFE4, Fpt_Chunk_Type.INT, "auto_set_unlit_color"),
            0x9DF2CFD0: Fpt_ChunkDescription(0x9DF2CFD0, Fpt_Chunk_Type.COLOR, "unlit_color"),
            0xA8EDC3D3: Fpt_ChunkDescription(0xA8EDC3D3, Fpt_Chunk_Type.INT, "rotation"),
            0xA1FDC0D6: Fpt_ChunkDescription(0xA1FDC0D6, Fpt_Chunk_Type.INT, "ordered_halo_glow"),
            0x9DFBCDD3: Fpt_ChunkDescription(0x9DFBCDD3, Fpt_Chunk_Type.INT, "reflects_off_playfield"),
            0x97ECBFD3: Fpt_ChunkDescription(0x97ECBFD3, Fpt_Chunk_Type.STRING, "playfield"),
            0x9600BED2: Fpt_ChunkDescription(0x9600BED2, Fpt_Chunk_Type.INT, "state"),
            0x95F3C9E3: Fpt_ChunkDescription(0x95F3C9E3, Fpt_Chunk_Type.INT, "blink_interval"),
            0x9600C2E3: Fpt_ChunkDescription(0x9600C2E3, Fpt_Chunk_Type.STRING, "blink_pattern"),
            0x9134D9F8: Fpt_ChunkDescription(0x9134D9F8, Fpt_Chunk_Type.RAWDATA, "unknown_0x9134D9F8"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_23"
        owner.obj__id = FptElementType.LIGHT_FLASHER
        owner.obj__name = "Light_Flasher"
        self.obj__chunks = FptTableElementReader_LIGHT_FLASHER.CHUNK_DICTIONARY


class FptTableElementReader_GUIDE_WIRE(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"),
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "color"),
            0xA4FAC5DC: Fpt_ChunkDescription(0xA4FAC5DC, Fpt_Chunk_Type.STRING, "texture"),
            0x99F4C2D2: Fpt_ChunkDescription(0x99F4C2D2, Fpt_Chunk_Type.INT, "sphere_mapping"),
            0xA2F8CDDD: Fpt_ChunkDescription(0xA2F8CDDD, Fpt_Chunk_Type.INT, "height"),
            0x95FDC9CE: Fpt_ChunkDescription(0x95FDC9CE, Fpt_Chunk_Type.INT, "width"),
            0xA8F3C0D6: Fpt_ChunkDescription(0xA8F3C0D6, Fpt_Chunk_Type.INT, "mark_as_ornamental"),
            0x9DFBCDD3: Fpt_ChunkDescription(0x9DFBCDD3, Fpt_Chunk_Type.INT, "reflects_off_playfield"),
            0x95F3C2D2: Fpt_ChunkDescription(0x95F3C2D2, Fpt_Chunk_Type.CHUNKLIST, "shape_point"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0xA1EDC5D2: Fpt_ChunkDescription(0xA1EDC5D2, Fpt_Chunk_Type.INT, "smooth"),
            0xA2F3C6D2: Fpt_ChunkDescription(0xA2F3C6D2, Fpt_Chunk_Type.RAWDATA, "unknown_0xA2F3C6D2"), # slingshot ???
            0xA8FCC6D2: Fpt_ChunkDescription(0xA8FCC6D2, Fpt_Chunk_Type.RAWDATA, "unknown_0xA8FCC6D2"), # single_leaf ???
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_24"
        owner.obj__id = FptElementType.GUIDE_WIRE
        owner.obj__name = "Guide_Wire"
        self.obj__chunks = FptTableElementReader_GUIDE_WIRE.CHUNK_DICTIONARY


class FptTableElementReader_DISPLAY_DISPREEL(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0xB8EFCDCF: Fpt_ChunkDescription(0xB8EFCDCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"), ## added ???
            0x90EDBFD3: Fpt_ChunkDescription(0x90EDBFD3, Fpt_Chunk_Type.INT, "number_style"),
            0xA700CCD3: Fpt_ChunkDescription(0xA700CCD3, Fpt_Chunk_Type.INT, "render_face_plate"),
            0x9DF2CFDF: Fpt_ChunkDescription(0x9DF2CFDF, Fpt_Chunk_Type.COLOR, "face_color"),
            0x95F3CFD3: Fpt_ChunkDescription(0x95F3CFD3, Fpt_Chunk_Type.INT, "reels"),
            0xA700C2D2: Fpt_ChunkDescription(0xA700C2D2, Fpt_Chunk_Type.INT, "spacing"),
            0xA6F1BFDF: Fpt_ChunkDescription(0xA6F1BFDF, Fpt_Chunk_Type.INT, "face_spacing"),
            0xA2F8CDDD: Fpt_ChunkDescription(0xA2F8CDDD, Fpt_Chunk_Type.INT, "height"),
            0x95FDC9CE: Fpt_ChunkDescription(0x95FDC9CE, Fpt_Chunk_Type.INT, "width"),
            0xA5F1BFD2: Fpt_ChunkDescription(0xA5F1BFD2, Fpt_Chunk_Type.INT, "spin_speed"),
            0x9BECC3D2: Fpt_ChunkDescription(0x9BECC3D2, Fpt_Chunk_Type.STRING, "spin_sound"),
            0x9DF2CFD9: Fpt_ChunkDescription(0x9DF2CFD9, Fpt_Chunk_Type.COLOR, "lit_color"),
            0xA6ECBFE4: Fpt_ChunkDescription(0xA6ECBFE4, Fpt_Chunk_Type.INT, "auto_set_unlit_color"),
            0x9DF2CFD0: Fpt_ChunkDescription(0x9DF2CFD0, Fpt_Chunk_Type.COLOR, "unlit_color"),
            0x9600BED2: Fpt_ChunkDescription(0x9600BED2, Fpt_Chunk_Type.INT, "state"),
            0x95F3C9E3: Fpt_ChunkDescription(0x95F3C9E3, Fpt_Chunk_Type.INT, "blink_interval"),
            0x9600C2E3: Fpt_ChunkDescription(0x9600C2E3, Fpt_Chunk_Type.STRING, "blink_pattern"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_25"
        owner.obj__id = FptElementType.DISPLAY_DISPREEL
        owner.obj__name = "Display_DispReel"
        self.obj__chunks = FptTableElementReader_DISPLAY_DISPREEL.CHUNK_DICTIONARY


class FptTableElementReader_DISPLAY_HUDREEL(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0xB8EFCDCF: Fpt_ChunkDescription(0xB8EFCDCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"), ## added ???
            0x90EDBFD3: Fpt_ChunkDescription(0x90EDBFD3, Fpt_Chunk_Type.INT, "number_style"),
            0xA700CCD3: Fpt_ChunkDescription(0xA700CCD3, Fpt_Chunk_Type.INT, "render_face_plate"),
            0x9DF2CFDF: Fpt_ChunkDescription(0x9DF2CFDF, Fpt_Chunk_Type.COLOR, "face_color"),
            0x95F3CFD3: Fpt_ChunkDescription(0x95F3CFD3, Fpt_Chunk_Type.INT, "reels"),
            0xA700C2D2: Fpt_ChunkDescription(0xA700C2D2, Fpt_Chunk_Type.INT, "spacing"),
            0xA6F1BFDF: Fpt_ChunkDescription(0xA6F1BFDF, Fpt_Chunk_Type.INT, "face_spacing"),
            0xA2F8CDDD: Fpt_ChunkDescription(0xA2F8CDDD, Fpt_Chunk_Type.INT, "height"),
            0x95FDC9CE: Fpt_ChunkDescription(0x95FDC9CE, Fpt_Chunk_Type.INT, "width"),
            0xA5F1BFD2: Fpt_ChunkDescription(0xA5F1BFD2, Fpt_Chunk_Type.INT, "spin_speed"),
            0x9BECC3D2: Fpt_ChunkDescription(0x9BECC3D2, Fpt_Chunk_Type.STRING, "spin_sound"),
            0x9DF2CFD9: Fpt_ChunkDescription(0x9DF2CFD9, Fpt_Chunk_Type.COLOR, "lit_color"),
            0xA6ECBFE4: Fpt_ChunkDescription(0xA6ECBFE4, Fpt_Chunk_Type.INT, "auto_set_unlit_color"),
            0x9DF2CFD0: Fpt_ChunkDescription(0x9DF2CFD0, Fpt_Chunk_Type.COLOR, "unlit_color"),
            0x9600BED2: Fpt_ChunkDescription(0x9600BED2, Fpt_Chunk_Type.INT, "state"),
            0x95F3C9E3: Fpt_ChunkDescription(0x95F3C9E3, Fpt_Chunk_Type.INT, "blink_interval"),
            0x9600C2E3: Fpt_ChunkDescription(0x9600C2E3, Fpt_Chunk_Type.STRING, "blink_pattern"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_26"
        owner.obj__id = FptElementType.DISPLAY_HUDREEL
        owner.obj__name = "Display_HudReel"
        self.obj__chunks = FptTableElementReader_DISPLAY_HUDREEL.CHUNK_DICTIONARY


class FptTableElementReader_SPECIAL_OVERLAY(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BEFBED3: Fpt_ChunkDescription(0x9BEFBED3, Fpt_Chunk_Type.INT, "render_onto_translite"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "color"),
            0xA2F8CDDD: Fpt_ChunkDescription(0xA2F8CDDD, Fpt_Chunk_Type.INT, "unknown_0x95FDC9CE"),
            0x95FDC9CE: Fpt_ChunkDescription(0x95FDC9CE, Fpt_Chunk_Type.INT, "width"),
            0xA8EDC3D3: Fpt_ChunkDescription(0xA8EDC3D3, Fpt_Chunk_Type.INT, "rotation"),
            0x96F5C5DC: Fpt_ChunkDescription(0x96F5C5DC, Fpt_Chunk_Type.STRING, "image_list"),
            0x95F3C9D0: Fpt_ChunkDescription(0x95F3C9D0, Fpt_Chunk_Type.INT, "update_interval"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_27"
        owner.obj__id = FptElementType.SPECIAL_OVERLAY
        owner.obj__name = "Special_Overlay"
        self.obj__chunks = FptTableElementReader_SPECIAL_OVERLAY.CHUNK_DICTIONARY


class FptTableElementReader_LIGHT_BULB(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0x9DFDC3D8: Fpt_ChunkDescription(0x9DFDC3D8, Fpt_Chunk_Type.STRING, "model"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"),
            0xA5F2C5D3: Fpt_ChunkDescription(0xA5F2C5D3, Fpt_Chunk_Type.INT, "render_model"),
            0x96F3CDD9: Fpt_ChunkDescription(0x96F3CDD9, Fpt_Chunk_Type.STRING, "lens_texture"),
            0x96FDD1D3: Fpt_ChunkDescription(0x96FDD1D3, Fpt_Chunk_Type.INT, "glow_radius"),
            0xA1FDC0D6: Fpt_ChunkDescription(0xA1FDC0D6, Fpt_Chunk_Type.INT, "ordered_halo_glow"),
            0x9DF2CFD9: Fpt_ChunkDescription(0x9DF2CFD9, Fpt_Chunk_Type.COLOR, "lit_color"),
            0xA6ECBFE4: Fpt_ChunkDescription(0xA6ECBFE4, Fpt_Chunk_Type.INT, "auto_set_unlit_color"),
            0x9DF2CFD0: Fpt_ChunkDescription(0x9DF2CFD0, Fpt_Chunk_Type.COLOR, "unlit_color"),
            0x96E8C0E2: Fpt_ChunkDescription(0x96E8C0E2, Fpt_Chunk_Type.INT, "crystal"),
            0xA8EDC3D3: Fpt_ChunkDescription(0xA8EDC3D3, Fpt_Chunk_Type.INT, "rotation"),
            0x9DFBCDD3: Fpt_ChunkDescription(0x9DFBCDD3, Fpt_Chunk_Type.INT, "reflects_off_playfield"),
            0x9600BED2: Fpt_ChunkDescription(0x9600BED2, Fpt_Chunk_Type.INT, "state"),
            0x95F3C9E3: Fpt_ChunkDescription(0x95F3C9E3, Fpt_Chunk_Type.INT, "blink_interval"),
            0x9600C2E3: Fpt_ChunkDescription(0x9600C2E3, Fpt_Chunk_Type.STRING, "blink_pattern"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_29"
        owner.obj__id = FptElementType.LIGHT_BULB
        owner.obj__name = "Light_Bulb"
        self.obj__chunks = FptTableElementReader_LIGHT_BULB.CHUNK_DICTIONARY


class FptTableElementReader_TRIGGER_GATE(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0x9DFDC3D8: Fpt_ChunkDescription(0x9DFDC3D8, Fpt_Chunk_Type.STRING, "model"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"),
            0xA300C5DC: Fpt_ChunkDescription(0xA300C5DC, Fpt_Chunk_Type.STRING, "texture"),
            0x99F4C2D2: Fpt_ChunkDescription(0x99F4C2D2, Fpt_Chunk_Type.INT, "sphere_mapping"),
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "color"),
            0xA8EDC3D3: Fpt_ChunkDescription(0xA8EDC3D3, Fpt_Chunk_Type.INT, "rotation"),
            0x9100BBD6: Fpt_ChunkDescription(0x9100BBD6, Fpt_Chunk_Type.INT, "one_way"),
            0x9DFBCDD3: Fpt_ChunkDescription(0x9DFBCDD3, Fpt_Chunk_Type.INT, "reflects_off_playfield"),
            0x97ECBFD3: Fpt_ChunkDescription(0x97ECBFD3, Fpt_Chunk_Type.STRING, "playfield"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_30"
        owner.obj__id = FptElementType.TRIGGER_GATE
        owner.obj__name = "Trigger_Gate"
        self.obj__chunks = FptTableElementReader_TRIGGER_GATE.CHUNK_DICTIONARY


class FptTableElementReader_TRIGGER_SPINNER(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0x9DFDC3D8: Fpt_ChunkDescription(0x9DFDC3D8, Fpt_Chunk_Type.STRING, "model"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"),
            0xA300C5DC: Fpt_ChunkDescription(0xA300C5DC, Fpt_Chunk_Type.STRING, "texture"),
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "color"),
            0xA8EDC3D3: Fpt_ChunkDescription(0xA8EDC3D3, Fpt_Chunk_Type.INT, "rotation"),
            0x9DFBCDD3: Fpt_ChunkDescription(0x9DFBCDD3, Fpt_Chunk_Type.INT, "reflects_off_playfield"),
            0x99F4D1E1: Fpt_ChunkDescription(0x99F4D1E1, Fpt_Chunk_Type.INT, "damping"),
            0x97ECBFD3: Fpt_ChunkDescription(0x97ECBFD3, Fpt_Chunk_Type.STRING, "playfield"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_31"
        owner.obj__id = FptElementType.TRIGGER_SPINNER
        owner.obj__name = "Trigger_Spinner"
        self.obj__chunks = FptTableElementReader_TRIGGER_SPINNER.CHUNK_DICTIONARY


class FptTableElementReader_TOY_CUSTOM(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0x9DFDC3D8: Fpt_ChunkDescription(0x9DFDC3D8, Fpt_Chunk_Type.STRING, "model"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"),
            0xA300C5DC: Fpt_ChunkDescription(0xA300C5DC, Fpt_Chunk_Type.STRING, "texture"),
            0x99F4C2D2: Fpt_ChunkDescription(0x99F4C2D2, Fpt_Chunk_Type.INT, "sphere_mapping"),
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "color"),
            0x9C00C0D1: Fpt_ChunkDescription(0x9C00C0D1, Fpt_Chunk_Type.INT, "transparency"),
            0xA8EDC3D3: Fpt_ChunkDescription(0xA8EDC3D3, Fpt_Chunk_Type.INT, "rotation"),
            0x96FBCCD6: Fpt_ChunkDescription(0x96FBCCD6, Fpt_Chunk_Type.INT, "offset"),
            0x9DFBCDD3: Fpt_ChunkDescription(0x9DFBCDD3, Fpt_Chunk_Type.INT, "reflects_off_playfield"),
            0x95F3C9D0: Fpt_ChunkDescription(0x95F3C9D0, Fpt_Chunk_Type.INT, "update_interval"),
            0x97ECBFD3: Fpt_ChunkDescription(0x97ECBFD3, Fpt_Chunk_Type.STRING, "playfield"),
            0x9035D306: Fpt_ChunkDescription(0x9035D306, Fpt_Chunk_Type.STRING, "sound_when_hit"),
            0x9035D2F8: Fpt_ChunkDescription(0x9035D2F8, Fpt_Chunk_Type.STRING, "sound_when_reset"),
            0x8035E308: Fpt_ChunkDescription(0x8035E308, Fpt_Chunk_Type.INT, "bank_count"),
            0x9133D308: Fpt_ChunkDescription(0x9133D308, Fpt_Chunk_Type.INT, "bank_spacing"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_33"
        owner.obj__id = FptElementType.TOY_CUSTOM
        owner.obj__name = "Toy_Custom"
        self.obj__chunks = FptTableElementReader_TOY_CUSTOM.CHUNK_DICTIONARY


class FptTableElementReader_LIGHT_SEQUENCER(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0xB8EFCDCF: Fpt_ChunkDescription(0xB8EFCDCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"), ## added ???
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "virtual_center"),
            0x95EEC6D9: Fpt_ChunkDescription(0x95EEC6D9, Fpt_Chunk_Type.STRING, "light_list"),
            0x95F3C9D0: Fpt_ChunkDescription(0x95F3C9D0, Fpt_Chunk_Type.INT, "update_interval"),
            0xA1EECCDF: Fpt_ChunkDescription(0xA1EECCDF, Fpt_Chunk_Type.INT, "flasher_blink"),
            0x9BF8BDDF: Fpt_ChunkDescription(0x9BF8BDDF, Fpt_Chunk_Type.INT, "blink_interval"),
            0x96EFBEDC: Fpt_ChunkDescription(0x96EFBEDC, Fpt_Chunk_Type.INT, "include_translite_light"),
            0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.RAWDATA, "unknown_0xA6F2C6D3"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_34"
        owner.obj__id = FptElementType.LIGHT_SEQUENCER
        owner.obj__name = "Light_Sequencer"
        self.obj__chunks = FptTableElementReader_LIGHT_SEQUENCER.CHUNK_DICTIONARY


class FptTableElementReader_DISPLAY_SEGMENT(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0xB8EFCDCF: Fpt_ChunkDescription(0xB8EFCDCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"), ## added ???
            0x99E8BED2: Fpt_ChunkDescription(0x99E8BED2, Fpt_Chunk_Type.INT, "segment_style"),
            0x95F3CFD2: Fpt_ChunkDescription(0x95F3CFD2, Fpt_Chunk_Type.INT, "digits"),
            0x95FDC9CE: Fpt_ChunkDescription(0x95FDC9CE, Fpt_Chunk_Type.INT, "size"),
            0xA700C2D2: Fpt_ChunkDescription(0xA700C2D2, Fpt_Chunk_Type.INT, "spacing"),
            0xA6F1BFDF: Fpt_ChunkDescription(0xA6F1BFDF, Fpt_Chunk_Type.INT, "face_spacing"),
            0x9BF8C2D0: Fpt_ChunkDescription(0x9BF8C2D0, Fpt_Chunk_Type.INT, "update_interval"),
            0xA2F8C6E4: Fpt_ChunkDescription(0xA2F8C6E4, Fpt_Chunk_Type.INT, "alignment"),
            0x99EED0D2: Fpt_ChunkDescription(0x99EED0D2, Fpt_Chunk_Type.INT, "slow_blink_speed"),
            0x99EED0DF: Fpt_ChunkDescription(0x99EED0DF, Fpt_Chunk_Type.INT, "fast_blink_speed"),
            0x90F5CEE3: Fpt_ChunkDescription(0x90F5CEE3, Fpt_Chunk_Type.INT, "boredom_delay"),
            0x9DF2CFD9: Fpt_ChunkDescription(0x9DF2CFD9, Fpt_Chunk_Type.COLOR, "lit_color"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_37"
        owner.obj__id = FptElementType.DISPLAY_SEGMENT
        owner.obj__name = "Display_Segment"
        self.obj__chunks = FptTableElementReader_DISPLAY_SEGMENT.CHUNK_DICTIONARY


class FptTableElementReader_DISPLAY_HUDSEGMENT(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0xB8EFCDCF: Fpt_ChunkDescription(0xB8EFCDCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"), ## added ???
            0x99E8BED2: Fpt_ChunkDescription(0x99E8BED2, Fpt_Chunk_Type.INT, "segment_style"),
            0x95F3CFD2: Fpt_ChunkDescription(0x95F3CFD2, Fpt_Chunk_Type.INT, "digits"),
            0x95FDC9CE: Fpt_ChunkDescription(0x95FDC9CE, Fpt_Chunk_Type.INT, "size"),
            0xA700C2D2: Fpt_ChunkDescription(0xA700C2D2, Fpt_Chunk_Type.INT, "spacing"),
            0xA6F1BFDF: Fpt_ChunkDescription(0xA6F1BFDF, Fpt_Chunk_Type.INT, "face_spacing"),
            0x9BF8C2D0: Fpt_ChunkDescription(0x9BF8C2D0, Fpt_Chunk_Type.INT, "update_interval"),
            0xA2F8C6E4: Fpt_ChunkDescription(0xA2F8C6E4, Fpt_Chunk_Type.INT, "alignment"),
            0x99EED0D2: Fpt_ChunkDescription(0x99EED0D2, Fpt_Chunk_Type.INT, "slow_blink_speed"),
            0x99EED0DF: Fpt_ChunkDescription(0x99EED0DF, Fpt_Chunk_Type.INT, "fast_blink_speed"),
            0x90F5CEE3: Fpt_ChunkDescription(0x90F5CEE3, Fpt_Chunk_Type.INT, "boredom_delay"),
            0x9DF2CFD9: Fpt_ChunkDescription(0x9DF2CFD9, Fpt_Chunk_Type.COLOR, "lit_color"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_38"
        owner.obj__id = FptElementType.DISPLAY_HUDSEGMENT
        owner.obj__name = "Display_HudSegment"
        self.obj__chunks = FptTableElementReader_DISPLAY_HUDSEGMENT.CHUNK_DICTIONARY


class FptTableElementReader_DISPLAY_DMD(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0xB8EFCDCF: Fpt_ChunkDescription(0xB8EFCDCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"), ## added ???
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "matrix_color"),
            0x9E00CFD2: Fpt_ChunkDescription(0x9E00CFD2, Fpt_Chunk_Type.INT, "scale"),
            0x99E8BEE1: Fpt_ChunkDescription(0x99E8BEE1, Fpt_Chunk_Type.INT, "type"),
            0x9BF8C2D0: Fpt_ChunkDescription(0x9BF8C2D0, Fpt_Chunk_Type.INT, "update_interval"),
            0xA2F8C6E4: Fpt_ChunkDescription(0xA2F8C6E4, Fpt_Chunk_Type.INT, "alignment"),
            0x99EED0D2: Fpt_ChunkDescription(0x99EED0D2, Fpt_Chunk_Type.INT, "slow_blink_speed"),
            0x99EED0DF: Fpt_ChunkDescription(0x99EED0DF, Fpt_Chunk_Type.INT, "fast_blink_speed"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_39"
        owner.obj__id = FptElementType.DISPLAY_DMD
        owner.obj__name = "Display_Dmd"
        self.obj__chunks = FptTableElementReader_DISPLAY_DMD.CHUNK_DICTIONARY


class FptTableElementReader_DISPLAY_HUDDMD(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0xB8EFCDCF: Fpt_ChunkDescription(0xB8EFCDCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"), ## added ???
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "matrix_color"),
            0x9E00CFD2: Fpt_ChunkDescription(0x9E00CFD2, Fpt_Chunk_Type.INT, "scale"),
            0x99E8BEE1: Fpt_ChunkDescription(0x99E8BEE1, Fpt_Chunk_Type.INT, "type"),
            0x9BF8C2D0: Fpt_ChunkDescription(0x9BF8C2D0, Fpt_Chunk_Type.INT, "update_interval"),
            0xA2F8C6E4: Fpt_ChunkDescription(0xA2F8C6E4, Fpt_Chunk_Type.INT, "alignment"),
            0x99EED0D2: Fpt_ChunkDescription(0x99EED0D2, Fpt_Chunk_Type.INT, "slow_blink_speed"),
            0x99EED0DF: Fpt_ChunkDescription(0x99EED0DF, Fpt_Chunk_Type.INT, "fast_blink_speed"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
            }


    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_40"
        owner.obj__id = FptElementType.DISPLAY_HUDDMD
        owner.obj__name = "Display_HudDmd"
        self.obj__chunks = FptTableElementReader_DISPLAY_HUDDMD.CHUNK_DICTIONARY


class FptTableElementReader_CONTROL_DIVERTER(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0x9DFDC3D8: Fpt_ChunkDescription(0x9DFDC3D8, Fpt_Chunk_Type.STRING, "model"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"),
            0xA300C5DC: Fpt_ChunkDescription(0xA300C5DC, Fpt_Chunk_Type.STRING, "texture"),
            0x99F4C2D2: Fpt_ChunkDescription(0x99F4C2D2, Fpt_Chunk_Type.INT, "sphere_mapping"),
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "color"),
            0xA900BED2: Fpt_ChunkDescription(0xA900BED2, Fpt_Chunk_Type.INT, "start_angle"),
            0xA8EDC3D3: Fpt_ChunkDescription(0xA8EDC3D3, Fpt_Chunk_Type.INT, "rotation"),
            0xA2EABFE4: Fpt_ChunkDescription(0xA2EABFE4, Fpt_Chunk_Type.INT, "swing"),
            0x9DFBCDD3: Fpt_ChunkDescription(0x9DFBCDD3, Fpt_Chunk_Type.INT, "reflects_off_playfield"),
            0x9035D306: Fpt_ChunkDescription(0x9035D306, Fpt_Chunk_Type.STRING, "solenoid"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_43"
        owner.obj__id = FptElementType.CONTROL_DIVERTER
        owner.obj__name = "Control_Diverter"
        self.obj__chunks = FptTableElementReader_CONTROL_DIVERTER.CHUNK_DICTIONARY


class FptTableElementReader_SPECIAL_STA(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0xB8EFCDCF: Fpt_ChunkDescription(0xB8EFCDCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"), ## added ???
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "color"),
            0xA2F8CDDD: Fpt_ChunkDescription(0xA2F8CDDD, Fpt_Chunk_Type.INT, "height"),
            0x95FDC9CE: Fpt_ChunkDescription(0x95FDC9CE, Fpt_Chunk_Type.INT, "width"),
            0x96F5C5DC: Fpt_ChunkDescription(0x96F5C5DC, Fpt_Chunk_Type.STRING, "image_list"),
            0x95F3C9D0: Fpt_ChunkDescription(0x95F3C9D0, Fpt_Chunk_Type.INT, "update_interval"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_44"
        owner.obj__id = FptElementType.SPECIAL_STA
        owner.obj__name = "Special_STA"
        self.obj__chunks = FptTableElementReader_SPECIAL_STA.CHUNK_DICTIONARY


class FptTableElementReader_CONTROL_AUTOPLUNGER(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"), ## added ???
            0xA300C5DC: Fpt_ChunkDescription(0xA300C5DC, Fpt_Chunk_Type.STRING, "texture"),
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "color"),
            0xA8EDC3D3: Fpt_ChunkDescription(0xA8EDC3D3, Fpt_Chunk_Type.INT, "rotation"),
            0xA1FABED2: Fpt_ChunkDescription(0xA1FABED2, Fpt_Chunk_Type.INT, "strength"),
            0x9DFBCDD3: Fpt_ChunkDescription(0x9DFBCDD3, Fpt_Chunk_Type.INT, "reflects_off_playfield"),
            0x97ECBFD3: Fpt_ChunkDescription(0x97ECBFD3, Fpt_Chunk_Type.STRING, "playfield"),
            0x95ECCFCF: Fpt_ChunkDescription(0x95ECCFCF, Fpt_Chunk_Type.INT, "include_v_cut"),
            0x90E9CFCF: Fpt_ChunkDescription(0x90E9CFCF, Fpt_Chunk_Type.VECTOR2D, "v_cut_position"),
            0x9BFCC6CF: Fpt_ChunkDescription(0x9BFCC6CF, Fpt_Chunk_Type.INT, "v_cut_lenght"),
            0xA2F4C9CF: Fpt_ChunkDescription(0xA2F4C9CF, Fpt_Chunk_Type.STRING, "v_cut_texture"),
            0x9DF2CFCF: Fpt_ChunkDescription(0x9DF2CFCF, Fpt_Chunk_Type.COLOR, "v_cut_color"),
            0xA5F3BFE4: Fpt_ChunkDescription(0xA5F3BFE4, Fpt_Chunk_Type.STRING, "solenoid"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_46"
        owner.obj__id = FptElementType.CONTROL_AUTOPLUNGER
        owner.obj__name = "Control_AutoPlunger"
        self.obj__chunks = FptTableElementReader_CONTROL_AUTOPLUNGER.CHUNK_DICTIONARY


class FptTableElementReader_TARGET_ROTO(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0x9DFDC3D8: Fpt_ChunkDescription(0x9DFDC3D8, Fpt_Chunk_Type.STRING, "model"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"), ## added ???
            0x96F5C5DC: Fpt_ChunkDescription(0x96F5C5DC, Fpt_Chunk_Type.STRING, "image_list"),
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "color"),
            0xA8EDC3D3: Fpt_ChunkDescription(0xA8EDC3D3, Fpt_Chunk_Type.INT, "rotation"),
            0x96FBCCD6: Fpt_ChunkDescription(0x96FBCCD6, Fpt_Chunk_Type.INT, "offset"),
            0x9DFBCDD3: Fpt_ChunkDescription(0x9DFBCDD3, Fpt_Chunk_Type.INT, "reflects_off_playfield"),
            0x9035D306: Fpt_ChunkDescription(0x9035D306, Fpt_Chunk_Type.STRING, "sound_motor_whir"),
            0x9035D2F8: Fpt_ChunkDescription(0x9035D2F8, Fpt_Chunk_Type.STRING, "sound_when_hit"),
            0x95F3CFD3: Fpt_ChunkDescription(0x95F3CFD3, Fpt_Chunk_Type.INT, "target_count"),
            0x90F5CED3: Fpt_ChunkDescription(0x90F5CED3, Fpt_Chunk_Type.INT, "step_delay"),
            0x95FEBEDF: Fpt_ChunkDescription(0x95FEBEDF, Fpt_Chunk_Type.INT, "firt_target_centered"),
            0x9AEFD1E2: Fpt_ChunkDescription(0x9AEFD1E2, Fpt_Chunk_Type.INT, "carrousel_roto_target"),
            0x96FDD1D3: Fpt_ChunkDescription(0x96FDD1D3, Fpt_Chunk_Type.INT, "radius"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_49"
        owner.obj__id = FptElementType.TARGET_ROTO
        owner.obj__name = "Target_Roto"
        self.obj__chunks = FptTableElementReader_TARGET_ROTO.CHUNK_DICTIONARY


class FptTableElementReader_CONTROL_POPUP(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0x9DFDC3D8: Fpt_ChunkDescription(0x9DFDC3D8, Fpt_Chunk_Type.STRING, "model"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"),
            0xA300C5DC: Fpt_ChunkDescription(0xA300C5DC, Fpt_Chunk_Type.STRING, "texture"),
            0x96E8C0E2: Fpt_ChunkDescription(0x96E8C0E2, Fpt_Chunk_Type.INT, "crystal"),
            0x99F4C2D2: Fpt_ChunkDescription(0x99F4C2D2, Fpt_Chunk_Type.INT, "sphere_mapping"),
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "color"),
            0xA8EDC3D3: Fpt_ChunkDescription(0xA8EDC3D3, Fpt_Chunk_Type.INT, "rotation"),
            0x96FBCCD6: Fpt_ChunkDescription(0x96FBCCD6, Fpt_Chunk_Type.INT, "offset"),
            0x9DFBCDD3: Fpt_ChunkDescription(0x9DFBCDD3, Fpt_Chunk_Type.INT, "reflects_off_playfield"),
            0x97ECBFD3: Fpt_ChunkDescription(0x97ECBFD3, Fpt_Chunk_Type.STRING, "playfield"),
            0xA5F3BFD2: Fpt_ChunkDescription(0xA5F3BFD2, Fpt_Chunk_Type.STRING, "solenoid"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_50"
        owner.obj__id = FptElementType.CONTROL_POPUP
        owner.obj__name = "Control_Popup"
        self.obj__chunks = FptTableElementReader_CONTROL_POPUP.CHUNK_DICTIONARY


class FptTableElementReader_RAMP_MODEL(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0x9DFDC3D8: Fpt_ChunkDescription(0x9DFDC3D8, Fpt_Chunk_Type.STRING, "model"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"),
            0xA300C5DC: Fpt_ChunkDescription(0xA300C5DC, Fpt_Chunk_Type.STRING, "texture"),
            0x99F4C2D2: Fpt_ChunkDescription(0x99F4C2D2, Fpt_Chunk_Type.INT, "sphere_mapping"),
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "color"),
            0xA8EDC3D3: Fpt_ChunkDescription(0xA8EDC3D3, Fpt_Chunk_Type.FLOAT, "rotation"),
            0x96FBCCD6: Fpt_ChunkDescription(0x96FBCCD6, Fpt_Chunk_Type.INT, "offset"),
            0x9C00C0D1: Fpt_ChunkDescription(0x9C00C0D1, Fpt_Chunk_Type.INT, "transparency"),
            0x9DECCFE1: Fpt_ChunkDescription(0x9DECCFE1, Fpt_Chunk_Type.INT, "disable_culling"),
            0x9DFBCDD3: Fpt_ChunkDescription(0x9DFBCDD3, Fpt_Chunk_Type.INT, "reflects_off_playfield"),
            0x97ECBFD3: Fpt_ChunkDescription(0x97ECBFD3, Fpt_Chunk_Type.STRING, "playfield"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_51"
        owner.obj__id = FptElementType.RAMP_MODEL
        owner.obj__name = "Ramp_RampModel"
        self.obj__chunks = FptTableElementReader_RAMP_MODEL.CHUNK_DICTIONARY


class FptTableElementReader_RAMP_WIRE(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"),
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "color"),
            0xA4FAC5DC: Fpt_ChunkDescription(0xA4FAC5DC, Fpt_Chunk_Type.STRING, "texture"),
            0xA2F8CAD2: Fpt_ChunkDescription(0xA2F8CAD2, Fpt_Chunk_Type.INT, "start_height"),
            0xA2F8CAE0: Fpt_ChunkDescription(0xA2F8CAE0, Fpt_Chunk_Type.INT, "end_height"),
            0x96FCBBD3: Fpt_ChunkDescription(0x96FCBBD3, Fpt_Chunk_Type.STRING, "model_start"),
            0xA4FCBBD3: Fpt_ChunkDescription(0xA4FCBBD3, Fpt_Chunk_Type.STRING, "model_end"),
            0x9DFBCDD3: Fpt_ChunkDescription(0x9DFBCDD3, Fpt_Chunk_Type.INT, "reflects_off_playfield"),
            0x97ECBFD3: Fpt_ChunkDescription(0x97ECBFD3, Fpt_Chunk_Type.STRING, "playfield"),
            0x95F3C2D2: Fpt_ChunkDescription(0x95F3C2D2, Fpt_Chunk_Type.CHUNKLIST, "ramp_point"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0xA1EDC5D2: Fpt_ChunkDescription(0xA1EDC5D2, Fpt_Chunk_Type.INT, "smooth"),
            0xA4F5C9D8: Fpt_ChunkDescription(0xA4F5C9D8, Fpt_Chunk_Type.INT, "left_guide"),
            0xA4F5C2D0: Fpt_ChunkDescription(0xA4F5C2D0, Fpt_Chunk_Type.INT, "left_upper_guide"),
            0xA0EFC9D8: Fpt_ChunkDescription(0xA0EFC9D8, Fpt_Chunk_Type.INT, "right_guide"),
            0xA0EFC2D0: Fpt_ChunkDescription(0xA0EFC2D0, Fpt_Chunk_Type.INT, "right_upper_guide"),
            0x95ECC3D1: Fpt_ChunkDescription(0x95ECC3D1, Fpt_Chunk_Type.INT, "top_wire"),
            0x9AF1CAE0: Fpt_ChunkDescription(0x9AF1CAE0, Fpt_Chunk_Type.INT, "mark_as_ramp_end_point"),
            0xA2F3C9D3: Fpt_ChunkDescription(0xA2F3C9D3, Fpt_Chunk_Type.INT, "ring_type"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_53"
        owner.obj__id = FptElementType.RAMP_WIRE
        owner.obj__name = "Ramp_WireRamp"
        self.obj__chunks = FptTableElementReader_RAMP_WIRE.CHUNK_DICTIONARY


class FptTableElementReader_TARGET_SWING(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"), ## added ???
            0x9DFDC3D8: Fpt_ChunkDescription(0x9DFDC3D8, Fpt_Chunk_Type.STRING, "model"),
            0xA300C5DC: Fpt_ChunkDescription(0xA300C5DC, Fpt_Chunk_Type.STRING, "texture"),
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "color"),
            0xA8EDC3D3: Fpt_ChunkDescription(0xA8EDC3D3, Fpt_Chunk_Type.INT, "rotation"),
            0x9DFBCDD3: Fpt_ChunkDescription(0x9DFBCDD3, Fpt_Chunk_Type.INT, "reflects_off_playfield"),
            0xA5F3BFD1: Fpt_ChunkDescription(0xA5F3BFD1, Fpt_Chunk_Type.STRING, "sound_when_hit"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_54"
        owner.obj__id = FptElementType.TARGET_SWING
        owner.obj__name = "Target_Swing"
        self.obj__chunks = FptTableElementReader_TARGET_SWING.CHUNK_DICTIONARY


class FptTableElementReader_RAMP_RAMP(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"),
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "color"),
            0xA3F2C0D5: Fpt_ChunkDescription(0xA3F2C0D5, Fpt_Chunk_Type.INT, "ramp_profile"),
            0xA4FAC5DC: Fpt_ChunkDescription(0xA4FAC5DC, Fpt_Chunk_Type.STRING, "texture"),
            0xA2F8CAD2: Fpt_ChunkDescription(0xA2F8CAD2, Fpt_Chunk_Type.INT, "start_height"),
            0xA5F8BBD2: Fpt_ChunkDescription(0xA5F8BBD2, Fpt_Chunk_Type.INT, "start_width"),
            0xA2F8CAE0: Fpt_ChunkDescription(0xA2F8CAE0, Fpt_Chunk_Type.INT, "end_height"),
            0xA5F8BBE0: Fpt_ChunkDescription(0xA5F8BBE0, Fpt_Chunk_Type.INT, "end_width"),
            0xA2F8CAD9: Fpt_ChunkDescription(0xA2F8CAD9, Fpt_Chunk_Type.INT, "left_side_height"),
            0xA2F8CAD3: Fpt_ChunkDescription(0xA2F8CAD3, Fpt_Chunk_Type.INT, "right_side_height"),
            0x9DFBCDD3: Fpt_ChunkDescription(0x9DFBCDD3, Fpt_Chunk_Type.INT, "reflects_off_playfield"),
            0x97ECBFD3: Fpt_ChunkDescription(0x97ECBFD3, Fpt_Chunk_Type.STRING, "playfield"),
            0x9A00C5E0: Fpt_ChunkDescription(0x9A00C5E0, Fpt_Chunk_Type.STRING, "enamel_map"), #
            0x99F4C2D2: Fpt_ChunkDescription(0x99F4C2D2, Fpt_Chunk_Type.INT, "sphere_mapping"),
            0x9C00C0D1: Fpt_ChunkDescription(0x9C00C0D1, Fpt_Chunk_Type.INT, "transparency"),
            0x95F3C2D2: Fpt_ChunkDescription(0x95F3C2D2, Fpt_Chunk_Type.CHUNKLIST, "ramp_point"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0xA1EDC5D2: Fpt_ChunkDescription(0xA1EDC5D2, Fpt_Chunk_Type.INT, "smooth"),

            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),

            #0xA4F5C9D8: Fpt_ChunkDescription(0xA4F5C9D8, Fpt_Chunk_Type.RAWDATA, "unknown_0xA4F5C9D8"), # left_guide
            #0xA4F5C2D0: Fpt_ChunkDescription(0xA4F5C2D0, Fpt_Chunk_Type.RAWDATA, "unknown_0xA4F5C2D0"), # left_upper_guide
            #0xA0EFC9D8: Fpt_ChunkDescription(0xA0EFC9D8, Fpt_Chunk_Type.RAWDATA, "unknown_0xA0EFC9D8"), # right_guide
            #0xA0EFC2D0: Fpt_ChunkDescription(0xA0EFC2D0, Fpt_Chunk_Type.RAWDATA, "unknown_0xA0EFC2D0"), # right_upper_guide
            #0x95ECC3D1: Fpt_ChunkDescription(0x95ECC3D1, Fpt_Chunk_Type.RAWDATA, "unknown_0x95ECC3D1"),
            #0x9AF1CAE0: Fpt_ChunkDescription(0x9AF1CAE0, Fpt_Chunk_Type.INT, "mark_as_ramp_end_point"),
            #0xA2F3C9D3: Fpt_ChunkDescription(0xA2F3C9D3, Fpt_Chunk_Type.RAWDATA, "unknown_0xA2F3C9D3"), # ring_type

            0xA4F5C9D8: Fpt_ChunkDescription(0xA4F5C9D8, Fpt_Chunk_Type.INT, "left_guide"),
            0xA4F5C2D0: Fpt_ChunkDescription(0xA4F5C2D0, Fpt_Chunk_Type.INT, "left_upper_guide"),
            0xA0EFC9D8: Fpt_ChunkDescription(0xA0EFC9D8, Fpt_Chunk_Type.INT, "right_guide"),
            0xA0EFC2D0: Fpt_ChunkDescription(0xA0EFC2D0, Fpt_Chunk_Type.INT, "right_upper_guide"),
            0x95ECC3D1: Fpt_ChunkDescription(0x95ECC3D1, Fpt_Chunk_Type.INT, "top_wire"),
            0x9AF1CAE0: Fpt_ChunkDescription(0x9AF1CAE0, Fpt_Chunk_Type.INT, "mark_as_ramp_end_point"),
            0xA2F3C9D3: Fpt_ChunkDescription(0xA2F3C9D3, Fpt_Chunk_Type.INT, "ring_type"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_55"
        owner.obj__id = FptElementType.RAMP_RAMP
        owner.obj__name = "Ramp_Ramp"
        self.obj__chunks = FptTableElementReader_RAMP_RAMP.CHUNK_DICTIONARY


class FptTableElementReader_TOY_SPINNINGDISK(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"), ## was missing
            0x9DFDC3D8: Fpt_ChunkDescription(0x9DFDC3D8, Fpt_Chunk_Type.STRING, "model"),
            0xA300C5DC: Fpt_ChunkDescription(0xA300C5DC, Fpt_Chunk_Type.STRING, "texture"),
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "color"),
            0xA1FABED2: Fpt_ChunkDescription(0xA1FABED2, Fpt_Chunk_Type.INT, "motor_power"),
            0x99F4D1E1: Fpt_ChunkDescription(0x99F4D1E1, Fpt_Chunk_Type.INT, "damping"),
            0x9DFBCDD3: Fpt_ChunkDescription(0x9DFBCDD3, Fpt_Chunk_Type.INT, "reflects_off_playfield"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_56"
        owner.obj__id = FptElementType.TOY_SPINNINGDISK
        owner.obj__name = "Toy_SpinningDisk"
        self.obj__chunks = FptTableElementReader_TOY_SPINNINGDISK.CHUNK_DICTIONARY


class FptTableElementReader_LIGHT_LIGHTIMAGE(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0x9BFCCFDD: Fpt_ChunkDescription(0x9BFCCFDD, Fpt_Chunk_Type.VECTOR2D, "glow_center"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"),
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "color"),
            0xA2F8CDDD: Fpt_ChunkDescription(0xA2F8CDDD, Fpt_Chunk_Type.FLOAT, "height"),
            0x95FDC9CE: Fpt_ChunkDescription(0x95FDC9CE, Fpt_Chunk_Type.FLOAT, "width"),
            #0xA2F8CDDD: Fpt_ChunkDescription(0xA2F8CDDD, Fpt_Chunk_Type.INT, "height"),
            #0x95FDC9CE: Fpt_ChunkDescription(0x95FDC9CE, Fpt_Chunk_Type.INT, "width"),
            0x96F5C5DC: Fpt_ChunkDescription(0x96F5C5DC, Fpt_Chunk_Type.STRING, "image_list"),
            0xA8EDC3D3: Fpt_ChunkDescription(0xA8EDC3D3, Fpt_Chunk_Type.INT, "rotation"),
            0x95F3C9D0: Fpt_ChunkDescription(0x95F3C9D0, Fpt_Chunk_Type.INT, "animation_update_interval"),
            0x9E00CAD3: Fpt_ChunkDescription(0x9E00CAD3, Fpt_Chunk_Type.INT, "render_halo_glow"),
            0x96FDD1D3: Fpt_ChunkDescription(0x96FDD1D3, Fpt_Chunk_Type.INT, "glow_radius"),
            0x9DF2CFDD: Fpt_ChunkDescription(0x9DF2CFDD, Fpt_Chunk_Type.COLOR, "halo_color"),
            0x9600BED2: Fpt_ChunkDescription(0x9600BED2, Fpt_Chunk_Type.INT, "state"),
            0x95F3C9E3: Fpt_ChunkDescription(0x95F3C9E3, Fpt_Chunk_Type.INT, "blink_interval"),
            0x9600C2E3: Fpt_ChunkDescription(0x9600C2E3, Fpt_Chunk_Type.STRING, "blink_pattern"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_57"
        owner.obj__id = FptElementType.LIGHT_LIGHTIMAGE
        owner.obj__name = "Light_LightImage"
        self.obj__chunks = FptTableElementReader_LIGHT_LIGHTIMAGE.CHUNK_DICTIONARY


class FptTableElementReader_KICKER_EMKICKER(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0x9DFDC3D8: Fpt_ChunkDescription(0x9DFDC3D8, Fpt_Chunk_Type.STRING, "model"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"),
            0xA300C5DC: Fpt_ChunkDescription(0xA300C5DC, Fpt_Chunk_Type.STRING, "texture"),
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "color"),
            0xA8EDC3D3: Fpt_ChunkDescription(0xA8EDC3D3, Fpt_Chunk_Type.INT, "rotation"),
            0xA1FABED2: Fpt_ChunkDescription(0xA1FABED2, Fpt_Chunk_Type.INT, "strength"),
            0xA5F3BFE4: Fpt_ChunkDescription(0xA5F3BFE4, Fpt_Chunk_Type.STRING, "solenoid"),
            0x9DFBCDD3: Fpt_ChunkDescription(0x9DFBCDD3, Fpt_Chunk_Type.INT, "reflects_off_playfield"),
            0x95ECCFCF: Fpt_ChunkDescription(0x95ECCFCF, Fpt_Chunk_Type.INT, "include_v_cut"),
            0x90E9CFCF: Fpt_ChunkDescription(0x90E9CFCF, Fpt_Chunk_Type.VECTOR2D, "v_cut_position"),
            0x9BFCC6CF: Fpt_ChunkDescription(0x9BFCC6CF, Fpt_Chunk_Type.INT, "v_cut_lenght"),
            0xA2F4C9CF: Fpt_ChunkDescription(0xA2F4C9CF, Fpt_Chunk_Type.STRING, "v_cut_texture"),
            0x9DF2CFCF: Fpt_ChunkDescription(0x9DF2CFCF, Fpt_Chunk_Type.COLOR, "v_cut_color"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_58"
        owner.obj__id = FptElementType.KICKER_EMKICKER
        owner.obj__name = "Kicker_EMKicker"
        self.obj__chunks = FptTableElementReader_KICKER_EMKICKER.CHUNK_DICTIONARY


class FptTableElementReader_LIGHT_HUDLIGHTIMAGE(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"), ## added ???
            0x9BFCCFDD: Fpt_ChunkDescription(0x9BFCCFDD, Fpt_Chunk_Type.VECTOR2D, "glow_center"),
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "color"),
            0xA2F8CDDD: Fpt_ChunkDescription(0xA2F8CDDD, Fpt_Chunk_Type.INT, "height"),
            0x95FDC9CE: Fpt_ChunkDescription(0x95FDC9CE, Fpt_Chunk_Type.INT, "width"),
            0x96F5C5DC: Fpt_ChunkDescription(0x96F5C5DC, Fpt_Chunk_Type.STRING, "image_list"),
            0xA8EDC3D3: Fpt_ChunkDescription(0xA8EDC3D3, Fpt_Chunk_Type.INT, "rotation"),
            0x95F3C9D0: Fpt_ChunkDescription(0x95F3C9D0, Fpt_Chunk_Type.INT, "animation_update_interval"),
            0x9E00CAD3: Fpt_ChunkDescription(0x9E00CAD3, Fpt_Chunk_Type.INT, "render_halo_glow"),
            0x96FDD1D3: Fpt_ChunkDescription(0x96FDD1D3, Fpt_Chunk_Type.INT, "glow_radius"),
            0x9DF2CFDD: Fpt_ChunkDescription(0x9DF2CFDD, Fpt_Chunk_Type.COLOR, "halo_color"),
            0x9600BED2: Fpt_ChunkDescription(0x9600BED2, Fpt_Chunk_Type.INT, "state"),
            0x95F3C9E3: Fpt_ChunkDescription(0x95F3C9E3, Fpt_Chunk_Type.INT, "blink_interval"),
            0x9600C2E3: Fpt_ChunkDescription(0x9600C2E3, Fpt_Chunk_Type.STRING, "blink_pattern"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_60"
        owner.obj__id = FptElementType.LIGHT_HUDLIGHTIMAGE
        owner.obj__name = "Light_HudLightImage"
        self.obj__chunks = FptTableElementReader_LIGHT_HUDLIGHTIMAGE.CHUNK_DICTIONARY


class FptTableElementReader_TRIGGER_OPTO(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0x9DFDC3D8: Fpt_ChunkDescription(0x9DFDC3D8, Fpt_Chunk_Type.STRING, "model"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"),
            0xA6FAC5DC: Fpt_ChunkDescription(0xA6FAC5DC, Fpt_Chunk_Type.STRING, "texture_collector"),
            0xA4FAC5DC: Fpt_ChunkDescription(0xA4FAC5DC, Fpt_Chunk_Type.STRING, "texture_emitter"),
            0x9CEBC4DC: Fpt_ChunkDescription(0x9CEBC4DC, Fpt_Chunk_Type.INT, "invert"),
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "color"),
            0xA8EDC3D3: Fpt_ChunkDescription(0xA8EDC3D3, Fpt_Chunk_Type.INT, "rotation"),
            0x95FDC9CE: Fpt_ChunkDescription(0x95FDC9CE, Fpt_Chunk_Type.INT, "beam_width"),
            0x9DFBCDD3: Fpt_ChunkDescription(0x9DFBCDD3, Fpt_Chunk_Type.INT, "reflects_off_playfield"),
            0xA5F3BFD1: Fpt_ChunkDescription(0xA5F3BFD1, Fpt_Chunk_Type.STRING, "sound_when_hit"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_61"
        owner.obj__id = FptElementType.TRIGGER_OPTO
        owner.obj__name = "Trigger_Opto"
        self.obj__chunks = FptTableElementReader_TRIGGER_OPTO.CHUNK_DICTIONARY


class FptTableElementReader_TARGET_VARI(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0x9DFDC3D8: Fpt_ChunkDescription(0x9DFDC3D8, Fpt_Chunk_Type.STRING, "model"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"), ## added ???
            0xA300C5DC: Fpt_ChunkDescription(0xA300C5DC, Fpt_Chunk_Type.STRING, "texture"),
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "color"),
            0x99F4C2D2: Fpt_ChunkDescription(0x99F4C2D2, Fpt_Chunk_Type.INT, "sphere_mapping"),
            0xA8EDC3D3: Fpt_ChunkDescription(0xA8EDC3D3, Fpt_Chunk_Type.INT, "rotation"),
            0x95F3CFD2: Fpt_ChunkDescription(0x95F3CFD2, Fpt_Chunk_Type.INT, "switch_count"),
            0x9BFCBED2: Fpt_ChunkDescription(0x9BFCBED2, Fpt_Chunk_Type.INT, "tension"),
            0x9DFBCDD3: Fpt_ChunkDescription(0x9DFBCDD3, Fpt_Chunk_Type.INT, "reflects_off_playfield"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_62"
        owner.obj__id = FptElementType.TARGET_VARI
        owner.obj__name = "Target_Vari"
        self.obj__chunks = FptTableElementReader_TARGET_VARI.CHUNK_DICTIONARY


class FptTableElementReader_TOY_HOLOGRAM(Fpt_Data_Reader):
    CHUNK_DICTIONARY = {
            0xA4F4D1D7: Fpt_ChunkDescription(0xA4F4D1D7, Fpt_Chunk_Type.WSTRING, "name"),
            0x9BFCCFCF: Fpt_ChunkDescription(0x9BFCCFCF, Fpt_Chunk_Type.VECTOR2D, "position"),
            0x9DFDC3D8: Fpt_ChunkDescription(0x9DFDC3D8, Fpt_Chunk_Type.STRING, "model"),
            0xA3EFBDD2: Fpt_ChunkDescription(0xA3EFBDD2, Fpt_Chunk_Type.STRING, "surface"),
            0x97F5C3E2: Fpt_ChunkDescription(0x97F5C3E2, Fpt_Chunk_Type.COLOR, "color"),
            0xA2F8CDDD: Fpt_ChunkDescription(0xA2F8CDDD, Fpt_Chunk_Type.INT, "height"),
            0x95FDC9CE: Fpt_ChunkDescription(0x95FDC9CE, Fpt_Chunk_Type.INT, "width"),
            0xA8EDC3D3: Fpt_ChunkDescription(0xA8EDC3D3, Fpt_Chunk_Type.INT, "rotation"),
            0x95F5C9D1: Fpt_ChunkDescription(0x95F5C9D1, Fpt_Chunk_Type.INT, "tilt"),
            0x96FBCCD6: Fpt_ChunkDescription(0x96FBCCD6, Fpt_Chunk_Type.INT, "offset"),
            0x96F5C5DC: Fpt_ChunkDescription(0x96F5C5DC, Fpt_Chunk_Type.STRING, "image_list"),
            0x95F3C9D0: Fpt_ChunkDescription(0x95F3C9D0, Fpt_Chunk_Type.INT, "animation_update_interval"),
            0x97F5CFE1: Fpt_ChunkDescription(0x97F5CFE1, Fpt_Chunk_Type.COLOR, "matrix_color"),
            0x9CFDD1D3: Fpt_ChunkDescription(0x9CFDD1D3, Fpt_Chunk_Type.INT, "render_as_dmd_matrix"),
            0x95F3CFCD: Fpt_ChunkDescription(0x95F3CFCD, Fpt_Chunk_Type.INT, "x_dot_count"),
            0x95F3CFCC: Fpt_ChunkDescription(0x95F3CFCC, Fpt_Chunk_Type.INT, "y_dot_count"),
            0xA0F1BDE1: Fpt_ChunkDescription(0xA0F1BDE1, Fpt_Chunk_Type.INT, "update_interval"),
            0xA2F8C6E4: Fpt_ChunkDescription(0xA2F8C6E4, Fpt_Chunk_Type.INT, "alignment"),
            0x99EED0D2: Fpt_ChunkDescription(0x99EED0D2, Fpt_Chunk_Type.INT, "slow_blink_speed"),
            0x99EED0DF: Fpt_ChunkDescription(0x99EED0DF, Fpt_Chunk_Type.INT, "fast_blink_speed"),
        0xA6F2C6D3: Fpt_ChunkDescription(0xA6F2C6D3, Fpt_Chunk_Type.INT, "object_appers_on"),
            0x9EFEC3D9: Fpt_ChunkDescription(0x9EFEC3D9, Fpt_Chunk_Type.INT, "locked"),
            0x9100C6E4: Fpt_ChunkDescription(0x9100C6E4, Fpt_Chunk_Type.INT, "layer"),
            0xA7FDC4E0: Fpt_ChunkDescription(0xA7FDC4E0, Fpt_Chunk_Type.END, "end"),
            }

    def __init__(self, owner=None):
        if owner is None:
            owner = self
        owner.obj__class = "Table_Element_64"
        owner.obj__id = FptElementType.TOY_HOLOGRAM
        owner.obj__name = "Toy_Hologram"
        self.obj__chunks = FptTableElementReader_TOY_HOLOGRAM.CHUNK_DICTIONARY


###############################################################################
class Fpl_Library_Element():
    pass


###############################################################################
class Fpm_File_Reader(Cfb_RawIO_Reader):
    def read_model(self):
        self.PinModel = None

        stream_names = self.get_stream_directory_names()
        for stream_name in stream_names:
            stream = self.get_stream(stream_name)
            if stream and stream.size():
                self.read_component(stream)

    def read_component(self, stream):
        name = stream.directory_entry().Directory_Entry_Name
        if name:
            name = name.lower()
        if name.startswith("modeldata"):
            reader = Fpt_PinModel_Reader()
            self.PinModel = reader
        else:
            print("#DEBUG skip read_component:", name)
            reader = None

        if reader:
            reader.read(stream)

        #print("#DEBUG", reader)

    def grab_content(self, dst_path=None):
        dst_sub_path_names = {}

        if not dst_path:
            dst_path = "fpm_grab"
            dst_path = path.normpath(dst_path)
            #while path.exists(dst_path):
            #    u_time = unpack("<Q", pack("<d", time()))[0]
            #    dst_path = "fpl_grab_{:016X}".format(u_time)
            #    dst_path = path.normpath(dst_path)
        else:
            dst_path = path.normpath(dst_path)

        makedirs(dst_path, mode=0o777, exist_ok=True)
        self.__dst_path = dst_path

        return Fpm_File_Reader.grab_content_ex(dst_path, { "modeldata": self.PinModel, }, dst_sub_path_names)

    @staticmethod
    def grab_content_ex(dst_path, pinmodel_dict, dst_sub_path_names):
        for key, reader in pinmodel_dict.items():
            item_name = reader.get_value("name")
            item_name = FpxUtilities.toGoodName(item_name) ###
            if item_name:
                dst_sub_path = path.join(dst_path, item_name)
                makedirs(dst_sub_path, mode=0o777, exist_ok=True)
                #print("#DEBUG", item_name, dst_path, dst_sub_path)
                dst_sub_path_names["sub_dir"] = dst_sub_path
            else:
                dst_sub_path = dst_path

            dst_sub_path_names[key] = dst_sub_path

            item_type = reader.get_value("type")
            dst_sub_path_names["type"] = item_type

            # grab preview
            win_item_path = reader.get_value("preview_path")
            item_path = FpxUtilities.toGoodFilePath(win_item_path)
            item_data_len = reader.get_value("preview_data_len")
            item_data = reader.get_value("preview_data")
            if item_path and item_data:
                full_path = path.normpath(path.join(dst_sub_path, item_path))
                item_data.grab_to_file(full_path)
                dst_sub_path_names["preview_data"] = full_path

            # grab primary_model
            win_item_path = reader.get_value("primary_model_path")
            item_path = FpxUtilities.toGoodFilePath(win_item_path)
            item_data_len = reader.get_value("primary_model_data_len")
            item_data = reader.get_value("primary_model_data")
            if item_path and item_data:
                full_path = path.normpath(path.join(dst_sub_path, item_path))
                item_data.grab_to_file(full_path)
                dst_sub_path_names["primary_model_data"] = full_path

            # grab secondary_model
            win_item_path = reader.get_value("secondary_model_path")
            item_path = FpxUtilities.toGoodFilePath(win_item_path)
            item_data_len = reader.get_value("secondary_model_data_len")
            item_data = reader.get_value("secondary_model_data")
            if item_path and item_data:
                full_path = path.normpath(path.join(dst_sub_path, item_path))
                item_data.grab_to_file(full_path)
                dst_sub_path_names["secondary_model_data"] = full_path

            # grab mask_model
            win_item_path = reader.get_value("mask_model_path")
            item_path = FpxUtilities.toGoodFilePath(win_item_path)
            item_data_len = reader.get_value("mask_model_data_len")
            item_data = reader.get_value("mask_model_data")
            if item_path and item_data:
                full_path = path.normpath(path.join(dst_sub_path, item_path))
                item_data.grab_to_file(full_path)
                dst_sub_path_names["mask_model_data"] = full_path

            # grab reflection_model
            win_item_path = reader.get_value("reflection_model_path")
            item_path = FpxUtilities.toGoodFilePath(win_item_path)
            item_data_len = reader.get_value("reflection_model_data_len")
            item_data = reader.get_value("reflection_model_data")
            if item_path and item_data:
                full_path = path.normpath(path.join(dst_sub_path, item_path))
                item_data.grab_to_file(full_path)
                dst_sub_path_names["reflection_model_data"] = full_path

        return dst_path, dst_sub_path_names


###############################################################################
class Fpl_File_Reader(Cfb_RawIO_Reader):
    def read_library(self):
        self.__data = {}

        self.Graphic = {}
        self.Sound = {}
        self.Music = {}
        self.PinModel = {}
        self.DmdFont = {}
        self.Script = {}

        stream_names = self.get_stream_directory_names()
        for stream_name in stream_names:
            stream = self.get_stream(stream_name)
            if stream and stream.size():
                name_root, name_item, name_type = stream_name.split(Fpl_File_Reader.SEPARATOR)
                self.read_component(stream, name_item)

    def read_component(self, stream, name):
        name = FpxUtilities.toGoodName(name) ####
        data = self.__data.get(name)
        if not data:
            data = Fpl_Library_Element()
            self.__data[name] = data

        name_type = stream.directory_entry().Directory_Entry_Name
        if name_type == "FTYP":
            data.FTYP = stream.read_dword()
            if data.FTYP == Fpl_Library_Type.GRAPHIC:
                data._FTYP = Fpl_Library_Type.TYPE_GRAPHIC
                self.Graphic[name] = data
            elif data.FTYP == Fpl_Library_Type.SOUND:
                data._FTYP = Fpl_Library_Type.TYPE_SOUND
                self.Sound[name] = data
            elif data.FTYP == Fpl_Library_Type.MUSIC:
                data._FTYP = Fpl_Library_Type.TYPE_MUSIC
                self.Music[name] = data
            elif data.FTYP == Fpl_Library_Type.MODEL:
                data._FTYP = Fpl_Library_Type.TYPE_MODEL
                self.PinModel[name] = data
            elif data.FTYP == Fpl_Library_Type.DMDFONT:
                data._FTYP = Fpl_Library_Type.TYPE_DMDFONT
                self.DmdFont[name] = data
            elif data.FTYP == Fpl_Library_Type.SCRIPT:
                data._FTYP = Fpl_Library_Type.TYPE_SCRIPT
                self.Script[name] = data
            else:
                data._FTYP = Fpl_Library_Type.TYPE_UNKNOWN
        elif name_type == "FLAD":
            data.FLAD = Cfb_Extras.to_time(stream.read_qword())
        elif name_type == "FPAT":
            data.FPAT = bytes.decode(stream.read())
        elif name_type == "FDAT":
            data.FDAT = Fpx_zLZO_RawData_Stream(stream)
        pass

    def grab_content(self, dst_path=None, filter={}, name=None):
        if not dst_path:
            dst_path = "fpl_grab"
            dst_path = path.normpath(dst_path)
            #while path.exists(dst_path):
            #    u_time = unpack("<Q", pack("<d", time()))[0]
            #    dst_path = "fpl_grab_{:016X}".format(u_time)
            #    dst_path = path.normpath(dst_path)
        else:
            #BUG in makedirs. does not create a folder ending with a blank
            #dst_path = path.normpath(dst_path)
            dst_path = path.normpath(dst_path.rstrip('. '))

        makedirs(dst_path, mode=0o777, exist_ok=True)
        self.__dst_path = dst_path

        dst_sub_path_names = {}

        if name:
            items = [[name, self.__data.get(name)], ]
        else:
            items = self.__data.items()

        if not filter:
            filter = Fpl_Library_Type.FILTER_ALL

        for item_name, value in items:
            if value._FTYP not in filter:
                continue

            dst_sub_path = path.join(dst_path, item_name)
            makedirs(dst_sub_path, mode=0o777, exist_ok=True)

            dst_sub_path_names["sub_dir_{}".format(item_name)] = dst_sub_path
            dst_sub_path_names["type_{}".format(item_name)] = value._FTYP

            # grab item
            win_file_path = value.FPAT
            file_path = FpxUtilities.toGoodFilePath(win_file_path)
            item_path=path.split(file_path)[1]
            item_data=value.FDAT
            if item_path and item_data:
                full_path = path.normpath(path.join(dst_sub_path, item_path))
                item_data.grab_to_file(full_path)
                dst_sub_path_names[item_name] = full_path

        return dst_path, dst_sub_path_names


###############################################################################
class Fpt_File_Reader(Cfb_RawIO_Reader):
    def read_table(self):
        self.__data = {}

        self.Image = {}
        self.Sound = {}
        self.Music = {}
        self.PinModel = {}
        self.DmdFont = {}

        self.ImageList = {}
        self.LightList = {}

        self.Table_Data = None
        self.File_Version = None
        self.Table_Element = {}
        self.Table_MAC = None

        self.Surfaces = {}
        self.Walls = {}

        stream_names = self.get_stream_directory_names()
        for stream_name in stream_names:
            stream = self.get_stream(stream_name)
            if stream and stream.size():
                self.read_component(stream)

    def read_component(self, stream):
        name = stream.directory_entry().Directory_Entry_Name
        if name:
            name = name.lower()
        if name.startswith("table data"):
            reader = Fpt_Table_Data_Reader()
            self.Table_Data = reader
        elif name.startswith("file version"):
            reader = Fpt_File_Version_Reader()
            self.File_Version = reader
        elif name.startswith("table element "):
            reader = FptTableElementReader()
            self.Table_Element[name] = reader
        elif name.startswith("image "):
            reader = Fpt_Image_Reader()
            self.Image[name] = reader
            self.__data[name] = reader
        elif name.startswith("sound "):
            reader = Fpt_Sound_Reader()
            self.Sound[name] = reader
            self.__data[name] = reader
        elif name.startswith("music "):
            reader = Fpt_Music_Reader()
            self.Music[name] = reader
            self.__data[name] = reader
        elif name.startswith("pinmodel "):
            reader = Fpt_PinModel_Reader()
            self.PinModel[name] = reader
            self.__data[name] = reader
        elif name.startswith("imagelist "):
            reader = Fpt_ImageList_Reader()
            self.ImageList[name] = reader
            self.__data[name] = reader
        elif name.startswith("lightlist "):
            reader = Fpt_LightList_Reader()
            self.LightList[name] = reader
            self.__data[name] = reader
        elif name.startswith("dmdfont "):
            reader = Fpt_DmdFont_Reader()
            self.DmdFont[name] = reader
            self.__data[name] = reader
        elif name.startswith("table mac"):
            reader = Fpt_Table_MAC_Reader()
            self.Table_MAC = reader
        else:
            reader = None

        if reader:
            reader.read(stream)

            item_name = reader.get_value("name")
            item_name = FpxUtilities.toGoodName(item_name) ###
            if not item_name:
                return

            fpx_id = reader.get_obj_value("id")
            if fpx_id == FptElementType.SURFACE:
                self.Surfaces[item_name] = reader
            elif fpx_id == FptElementType.GUIDE_WALL:
                self.Walls[item_name] = reader

        ##print("#DEBUG", reader)

    def grab_stream(self, dst_path=None):
        if not dst_path:
            u_time = unpack("<Q", pack("<d", time()))[0]
            dst_path = "fpt_grab_{:016X}".format(unpack("<Q", pack("<d", time()))[0])
        dst_path = path.normpath(dst_path)
        if path.exists(dst_path):
            raise OSError
        makedirs(dst_path, mode=0o777, exist_ok=False)
        self.__dst_path = dst_path

    def grab_content(self, dst_path=None, name=None, filter=None):
        if not dst_path:
            dst_path = "fpt_grab"
            dst_path = path.normpath(dst_path)
            #while path.exists(dst_path):
            #    u_time = unpack("<Q", pack("<d", time()))[0]
            #    dst_path = "fpl_grab_{:016X}".format(u_time)
            #    dst_path = path.normpath(dst_path)
        else:
            dst_path = path.normpath(dst_path)

        makedirs(dst_path, mode=0o777, exist_ok=True)
        self.__dst_path = dst_path

        dst_sub_path_names = {}

        if name:
            items = [[name, self.__data.get(name)], ]
        else:
            items = self.__data.items()

        for key, reader in items:
            if not reader or reader.get_value("linked"):
                continue

            item_name = reader.get_value("name")
            item_name = FpxUtilities.toGoodName(item_name) ####
            if not item_name:
                continue

            dst_sub_path = dst_path.rstrip('. ')

            item_data_dict = {}

            if isinstance(reader, Fpt_Image_Reader):
                type = Fpt_PackedLibrary_Type.TYPE_IMAGE
                item_type = reader.get_value("type")
                item_ext = Fpt_Resource_Type.VALUE_INT_TO_NAME[item_type]
                item_data = reader.get_value("data")
                item_data_dict[item_name] = item_data

            elif isinstance(reader, Fpt_Sound_Reader):
                ##TODO
                #type = Fpt_PackedLibrary_Type.TYPE_SOUND
                #item_type = reader.get_value("type")
                #item_ext = Fpt_Resource_Type.VALUE_INT_TO_NAME[item_type]
                #item_data = reader.get_value("data")
                #item_data_dict[item_name] = item_data
                continue

            elif isinstance(reader, Fpt_Music_Reader):
                ##TODO
                #type = Fpt_PackedLibrary_Type.TYPE_MUSIC
                #item_type = reader.get_value("type")
                #item_ext = Fpt_Resource_Type.VALUE_INT_TO_NAME[item_type]
                #item_data = reader.get_value("data")
                #item_data_dict[item_name] = item_data
                continue

            elif isinstance(reader, Fpt_PinModel_Reader):
                type = Fpt_PackedLibrary_Type.TYPE_MODEL

                fpm_sub_path_names = {}
                dst_sub_path_names["data_{}".format(item_name)] = Fpm_File_Reader.grab_content_ex(dst_path, { item_name: reader, }, fpm_sub_path_names)
                dst_sub_path_names["type_{}".format(item_name)] = type

            elif isinstance(reader, Fpt_ImageList_Reader):
                ##TODO
                #type = Fpt_PackedLibrary_Type.TYPE_IMAGE_LIST
                continue

            elif isinstance(reader, Fpt_LightList_Reader):
                ##TODO
                #type = Fpt_PackedLibrary_Type.TYPE_LIGHT_LIST
                continue

            elif isinstance(reader, Fpt_DmdFont_Reader):
                ##TODO
                #type = Fpt_PackedLibrary_Type.TYPE_DMDFONT
                continue

            else:
                #type = Fpt_PackedLibrary_Type.TYPE_UNKNOWN
                continue

            for sub_item_name, sub_item_data in item_data_dict.items():
                if not sub_item_data:
                    continue
                full_path = path.normpath(path.join(dst_sub_path, "{}.{}".format(sub_item_name, item_ext))).lower()
                sub_item_data.grab_to_file(full_path)
                dst_sub_path_names[sub_item_name] = full_path
                dst_sub_path_names["type_{}".format(sub_item_name)] = type

        return dst_path, dst_sub_path_names


    def dump_stream(self, stream):
        # DEBUG
        print(stream.directory_entry())
        size = stream.size()
        if stream.directory_entry().Directory_Entry_Name == "Table MAC" or stream.directory_entry().Directory_Entry_Name == "File Version":
            dump = stream.read()
            FpxUtilities.dump_bin(
                    dump,
                    0,
                    "#DEBUG RAW_DATA",
                    sector_list=stream.sector_list(),
                    sector_size=stream.sector_size()
                    )

        elif stream.directory_entry().Directory_Entry_Name.startswith("Table Element "):
            start_pos = stream.tell()
            current_pos = start_pos
            table_element = stream.read_dword()
            FpxUtilities.str_end_tag(FpxUtilities.TAG_NAME)
            FpxUtilities.dump_bin(
                    pack("<I", table_element),
                    current_pos,
                    "#DEBUG '{}'".format(Fpt_Chunk_Type.get_table_element_name(table_element)),
                    (size - (current_pos - start_pos)),
                    sector_list=stream.sector_list(),
                    sector_size=stream.sector_size(),
                    add_tags=False
                    )

            size -= Fp_Size_Type.DWORD
            start_pos = stream.tell()
            current_pos = start_pos
            while (current_pos - start_pos) < size:
                token = Fpt_Chunk_Data(stream)
                token.read()
                max_size = (size - (current_pos - start_pos))
                if token.IsBroken:
                    max_size = Fp_Size_Type.DWORD
                FpxUtilities.dump_bin(
                        token.get_raw(),
                        current_pos,
                        repr(token),
                        max_size,
                        sector_list=stream.sector_list(),
                        sector_size=stream.sector_size(),
                        add_tags=False
                        )
                current_pos = stream.tell()
            FpxUtilities.str_end_tag(FpxUtilities.TAG_NAME)

        else:
            start_pos = stream.tell()
            current_pos = start_pos
            FpxUtilities.str_begin_tag(FpxUtilities.TAG_NAME)
            while (current_pos - start_pos) < size:
                token = Fpt_Chunk_Data(stream)
                token.read()
                max_size = (size - (current_pos - start_pos))
                if token.IsBroken:
                    max_size = Fp_Size_Type.DWORD
                FpxUtilities.dump_bin(
                        token.get_raw(),
                        current_pos,
                        repr(token),
                        max_size,
                        sector_list=stream.sector_list(),
                        sector_size=stream.sector_size(),
                        add_tags=False
                        )
                current_pos = stream.tell()
            FpxUtilities.str_end_tag(FpxUtilities.TAG_NAME)


###############################################################################


###############################################################################
#234567890123456789012345678901234567890123456789012345678901234567890123456789
#--------1---------2---------3---------4---------5---------6---------7---------
# ##### END OF FILE #####
