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
## [MS-CFB]: Compound File Binary File Format
## http://msdn.microsoft.com/en-us/library/dd942138.aspx


from struct import (
        unpack,
        )
from io import (
        SEEK_SET,
        SEEK_CUR,
        SEEK_END,
        )
from time import (
        strftime,
        gmtime,
        )
from operator import (
        attrgetter,
        )


class DEBUG_CFB_SPEC:
    errors = []
    warnings = []
    enabled = True
    fire_exception = False

    @staticmethod
    def unknown_value(value):
        if DEBUG.enabled:
            s = "#DEBUG {} ???".format(value)
            if DEBUG.fire_exception:
                raise ValueError(s)
            return s
        pass

    @staticmethod
    def add_error(value):
        DEBUG_CFB_SPEC.errors.append(value)

    @staticmethod
    def add_warning(value):
        DEBUG_CFB_SPEC.warnings.append(value)


###############################################################################
#234567890123456789012345678901234567890123456789012345678901234567890123456789
#--------1---------2---------3---------4---------5---------6---------7---------
class Cfb_RawIO_Reader:
    SEPARATOR = '\\'

    __slots__ = (
            '__raw_io',
            '__compound_file_header'
            )

    def __init__(self, raw_io):
        self.__raw_io = raw_io
        self.__compound_file_header = Cfb_File_Header(self)
        self.__compound_file_header.read()

    def tell(self):
        self.__raw_io.tell()

    def seek(self, offset, whence=SEEK_SET):
        return self.__raw_io.seek(offset, whence)

    def read(self, n=-1):
        """ read raw byte(s) buffer """
        return self.__raw_io.read(n)

    def get_stream_directory_names(self):
        return self.__compound_file_header.get_stream_directory_names()

    def get_stream_directory_entry(self, path_name):
        return self.__compound_file_header.get_stream_directory_entry()

    def get_stream(self, path_name):
        directory_entry = self.__compound_file_header.get_stream_directory_entry(path_name)
        if directory_entry and not directory_entry.is_directory():
            stream_sector_list = self.__compound_file_header.get_stream_sector_list(directory_entry)
            if self.__compound_file_header.is_large_stream(directory_entry.Stream_Size):
                sector_shift = self.__compound_file_header.Sector_Shift
            else:
                sector_shift = self.__compound_file_header.Mini_Sector_Shift
            return Cfb_Stream_Reader(
                    self,
                    stream_sector_list,
                    sector_shift,
                    path_name,
                    directory_entry
                    )
        return None

    def read_byte(self):
        """ read a single byte value """
        return unpack('<B', self.__raw_io.read(Cfb_Size_Type.BYTE))[0]

    def read_word(self):
        """ read a single word value """
        return unpack('<H', self.__raw_io.read(Cfb_Size_Type.WORD))[0]

    def read_dword(self):
        """ read a single double word value """
        return unpack('<I', self.__raw_io.read(Cfb_Size_Type.DWORD))[0]

    def read_qword(self):
        """ read a single quad word value """
        return unpack('<Q', self.__raw_io.read(Cfb_Size_Type.QWORD))[0]

    CLSID_NULL = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    #CLSID_NULL = (0x00000000, 0x0000, 0x0000, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, )
    def read_clsid(self):
        """
        b'\xf0\xf1\xf2\xf3\xe0\xe1\xd0\xd1\x07\x06\x05\x04\x03\x02\x01\x00'
        '<L2H8B'
        (0xF3F2F1F0, 0xE1E0, 0xD1D0, 0x07, 0x06, 0x05, 0x04, 0x03, 0x02, 0x01, 0x00, )
        """
        #return unpack('<L2H8B', self.__raw_io.read(Cfb_Size_Type.CLSID))
        return self.__raw_io.read(Cfb_Size_Type.CLSID)


###############################################################################
#234567890123456789012345678901234567890123456789012345678901234567890123456789
#--------1---------2---------3---------4---------5---------6---------7---------
class Cfb_Stream_Reader:
    """
    for internal use only
    do not create an instance directly
    """
    __slots__ = (
        '__compound_raw_io',
        '__directory_entry',
        '__path_name',
        '__stream_sector_list',
        '__stream_sector_shift',
        '__stream_sector_size',
        '__stream_sector_mask',
        '__stream_sector_index',
        '__stream_sector_position',
        '__stream_position',
        )

    def __init__(self, compound_raw_io, sector_list, sector_shift, path_name, directory_entry):
        if not isinstance(compound_raw_io, Cfb_RawIO_Reader):
            raise TypeError("Cfb_Stream_Reader(compound_raw_io)")
        if not isinstance(directory_entry, Cfb_File_Directory_Entry):
            raise TypeError("Cfb_Stream_Reader(directory_entry)")

        self.__compound_raw_io = compound_raw_io
        self.__stream_sector_list = sector_list
        self.__stream_sector_shift = sector_shift
        self.__path_name = path_name
        self.__directory_entry = directory_entry

        self.__stream_sector_index = 0
        self.__stream_sector_position = 0
        self.__stream_position = 0
        self.__stream_sector_size = 1 << self.__stream_sector_shift
        self.__stream_sector_mask = self.__stream_sector_size - 1

    def size(self):
        return self.__directory_entry.Stream_Size

    def tell(self):
        return self.__stream_position

    def seek(self, offset, whence=SEEK_SET):
        if whence == SEEK_SET:
            stream_position = offset
        elif whence == SEEK_CUR:
            stream_position = self.__stream_position + offset
        elif whence == SEEK_END:
            stream_position = self.__directory_entry.Stream_Size + offset - 1
        else:
            raise ValueError("Cfb_Stream_Reader.seek(whence)")

        if stream_position < 0 or stream_position > self.__directory_entry.Stream_Size:
            raise IndexError("Cfb_Stream_Reader.seek(offset)")

        ## mit -1
        stream_sector_index = stream_position >> self.__stream_sector_shift
        stream_sector_position = stream_position & self.__stream_sector_mask

        ## set __stream_position without -1
##        stream_sector_index = stream_position >> self.__stream_sector_shift
##        stream_sector_position = stream_position & self.__stream_sector_mask

        stream_sector_offset = self.__stream_sector_list[stream_sector_index] + stream_sector_position


        self.__stream_sector_index = stream_sector_index
        self.__stream_sector_position = stream_sector_position

        ## set __stream_position without -1
        self.__stream_position = stream_position

        self.__compound_raw_io.seek(stream_sector_offset)
        return stream_position

    def read(self, n=-1):
        blocks = []

        if n >= 0:
            max_stream_position = self.__stream_position + n
        else:
            max_stream_position = self.__directory_entry.Stream_Size

        if max_stream_position > self.__directory_entry.Stream_Size:
            max_stream_position = self.__directory_entry.Stream_Size

        while self.__stream_position < max_stream_position:
            self.seek(self.__stream_position)
            max_remaining_size = max_stream_position - self.__stream_position
            size = self.__stream_sector_size - self.__stream_sector_position
            if size > max_remaining_size:
                size = max_remaining_size
            if n >= 0 and size > n:
                size = n
            buffer = self.__compound_raw_io.read(size)
            blocks.append(buffer)
            if size > len(buffer):
                break
                raise IndexError("Cfb_Stream_Reader.read(n)")
            self.__stream_position += size

        ## mit -1
##        self.seek(self.__stream_position - 1)

        ## set __stream_position without -1
##        self.seek(self.__stream_position)

        return b''.join(blocks)

    def read_byte(self):
        """ read a single byte value """
        return unpack('<B', self.read(Cfb_Size_Type.BYTE))[0]

    def read_word(self):
        """ read a single word value """
        return unpack('<H', self.read(Cfb_Size_Type.WORD))[0]

    def read_dword(self):
        """ read a single double word value """
        return unpack('<I', self.read(Cfb_Size_Type.DWORD))[0]

    def read_qword(self):
        """ read a single quad word value """
        return unpack('<Q', self.read(Cfb_Size_Type.QWORD))[0]

    def path_name(self):
        return self.__path_name

    def directory_entry(self):
        return self.__directory_entry

    def sector_list(self):
        return self.__stream_sector_list

    def sector_size(self):
        return self.__stream_sector_size


###############################################################################
#234567890123456789012345678901234567890123456789012345678901234567890123456789
#--------1---------2---------3---------4---------5---------6---------7---------
#
# following classes are for internal use only
#
#


###############################################################################
class Cfb_File_Header:
    """ for internal use only """

    """
    # [MS-CFB]: Compound File Binary File Format
    # 2.2 Compound File Header
    # http://msdn.microsoft.com/en-us/library/dd942138.aspx

    (0x00) Header_Signature[8] = (byte) b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1'
    (0x08) Header_CLSID[16] = (byte) b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    (0x18) Minor_Version = (word) 0x003E
    (0x1A) Major_Version = (word) 0x0003
    (0x1C) Byte_Order = (word) 0xFFFE
    (0x1E) Sector_Shift = (word) 0x0009 (Major_Version == 0x0003)
    (0x20) Mini_Sector_Shift = (word) 0x0006
    (0x22) Reserved = (word) b'\x00\x00\x00\x00\x00\x00'
    (0x28) Number_Of_Directory_Sectors = (dword) 0x00000000 (Major_Version == 0x0003)
    (0x2C) Number_Of_FAT_Sectors = (dword)
    (0x30) First_Directory_Sector_Location = (dword)
    (0x34) Transaction_Signature_Number = (dword) 0x00000000
    (0x38) Mini_Stream_Cutoff_Size = (dword) 0x00001000
    (0x3C) First_Mini_FAT_Sector_Location = (dword)
    (0x40) Number_Of_Mini_FAT_Sectors = (dword)
    (0x44) First_DIFAT_Sector_Location = (dword)
    (0x48) Number_Of_DIFAT_Sectors = (dword)
    (0x4C) DIFAT[109] = (dword)
    (0x200) .
    """

    HEADER_SIGNATURE = b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1'
    HEADER_SIGNATURE_SIZE = len(HEADER_SIGNATURE)

    MINOR_VERSION = 0x003E
    MAX_MAJOR_VERSION = 0x0004
    BYTE_ORDER_LE = 0xFFFE

    RESERVED = b'\x00\x00\x00\x00\x00\x00'
    RESERVED_SIZE = len(RESERVED)

    NUMBER_OF_DIFAT_SECTOR_IN_HEADER = 109

    __slots__ = (
            'Header_Signature',
            'Header_CLSID',
            'Minor_Version',
            'Major_Version',
            'Byte_Order',
            'Sector_Shift',
            'Mini_Sector_Shift',
            'Reserved',
            'Number_Of_Directory_Sectors',
            'Number_Of_FAT_Sectors',
            'First_Directory_Sector_Location',
            'Transaction_Signature_Number',
            'Mini_Stream_Cutoff_Size',
            'First_Mini_FAT_Sector_Location',
            'Number_Of_Mini_FAT_Sectors',
            'First_DIFAT_Sector_Location',
            'Number_Of_DIFAT_Sectors',
            'DIFAT',

            '__sector_size',
            '__mini_sector_size',

            '__compound_raw_io',

            '__directory_entry_list',
            '__file_allocation_table',
            '__mini_file_allocation_table',
            '__mini_stream_sector_location_list',
            '__number_sectors_in_mini_stream',
            '__total_number_of_mini_sectors',
            '__directory_entry_dictionary',
            'debug_counter',
            )

    def __init__(self, compound_raw_io):
        self.debug_counter = 0
        if not isinstance(compound_raw_io, Cfb_RawIO_Reader):
            raise TypeError("Cfb_File_Header(compound_raw_io)")
        self.__compound_raw_io = compound_raw_io
        self.__directory_entry_list = []
        self.__file_allocation_table = []
        self.__mini_file_allocation_table = []
        self.__mini_stream_sector_location_list = []
        self.__directory_entry_dictionary = {}

    def __repr__(self):
        return "<Cfb_File_Header\n" \
                "Header_Signature=\"{}\",\n" \
                "Header_CLSID=\"{}\",\n" \
                "Minor_Version=\"{}\",\n" \
                "Major_Version=\"{}\",\n" \
                "Byte_Order=\"{}\",\n" \
                "Sector_Shift=\"{}\",\n" \
                "Mini_Sector_Shift=\"{}\",\n" \
                "Reserved=\"{}\",\n" \
                "Number_Of_Directory_Sectors=\"{}\",\n" \
                "Number_Of_FAT_Sectors=\"{}\",\n" \
                "First_Directory_Sector_Location=\"{}\",\n" \
                "Transaction_Signature_Number=\"{}\",\n" \
                "Mini_Stream_Cutoff_Size=\"{}\",\n" \
                "First_Mini_FAT_Sector_Location=\"{}\",\n" \
                "Number_Of_Mini_FAT_Sectors=\"{}\",\n" \
                "First_DIFAT_Sector_Location=\"{}\",\n" \
                "Number_Of_DIFAT_Sectors=\"{}\",\n" \
                "/>".format(
                self.Header_Signature,
                Cfb_Extras.str_clsid(self.Header_CLSID),
                self.Minor_Version,
                self.Major_Version,
                self.Byte_Order,
                self.Sector_Shift,
                self.Mini_Sector_Shift,
                self.Reserved,
                self.Number_Of_Directory_Sectors,
                self.Number_Of_FAT_Sectors,
                Cfb_Sector_Type.to_string(self.First_Directory_Sector_Location),
                self.Transaction_Signature_Number,
                self.Mini_Stream_Cutoff_Size,
                Cfb_Sector_Type.to_string(self.First_Mini_FAT_Sector_Location),
                self.Number_Of_Mini_FAT_Sectors,
                Cfb_Sector_Type.to_string(self.First_DIFAT_Sector_Location),
                self.Number_Of_DIFAT_Sectors,
                )

    def read(self):
        self.Header_Signature = self.read_header_signature()
        if self.Header_Signature != self.HEADER_SIGNATURE:
            return False
        self.Header_CLSID = self.__compound_raw_io.read_clsid()
        self.Minor_Version = self.__compound_raw_io.read_word()
        if self.Minor_Version > self.MINOR_VERSION:
            return False
        self.Major_Version = self.__compound_raw_io.read_word()
        if self.Major_Version > self.MAX_MAJOR_VERSION:
            return False
        self.Byte_Order = self.__compound_raw_io.read_word()
        if self.Byte_Order != self.BYTE_ORDER_LE:
            return False
        self.Sector_Shift = self.__compound_raw_io.read_word()
        self.Mini_Sector_Shift = self.__compound_raw_io.read_word()
        self.Reserved = self.__compound_raw_io.read(Cfb_File_Header.RESERVED_SIZE)
        self.Number_Of_Directory_Sectors = self.__compound_raw_io.read_dword()
        self.Number_Of_FAT_Sectors = self.__compound_raw_io.read_dword()
        self.First_Directory_Sector_Location = self.__compound_raw_io.read_dword()
        self.Transaction_Signature_Number = self.__compound_raw_io.read_dword()
        self.Mini_Stream_Cutoff_Size = self.__compound_raw_io.read_dword()
        self.First_Mini_FAT_Sector_Location = self.__compound_raw_io.read_dword()
        self.Number_Of_Mini_FAT_Sectors = self.__compound_raw_io.read_dword()
        self.First_DIFAT_Sector_Location = self.__compound_raw_io.read_dword()
        self.Number_Of_DIFAT_Sectors = self.__compound_raw_io.read_dword()
        self.DIFAT = []

        self.__sector_size = 1 << self.Sector_Shift
        self.__mini_sector_size = 1 << self.Mini_Sector_Shift
        self.__total_number_of_mini_sectors = self.Number_Of_Mini_FAT_Sectors << self.Mini_Sector_Shift

        # read DIFAT entries of header
        size = Cfb_File_Header.NUMBER_OF_DIFAT_SECTOR_IN_HEADER
        sector = self.__compound_raw_io.read(size * Cfb_Size_Type.DWORD)
        entries = unpack('<{}L'.format(size), sector)
        self.DIFAT.extend(entries[0:size])

        # read extended DIFAT entries
        size = self.__sector_size
        number_entries = size // Cfb_Size_Type.DWORD
        sector_location = self.First_DIFAT_Sector_Location
        for i in range(0, self.Number_Of_DIFAT_Sectors):
            if sector_location >= Cfb_Sector_Type.MAXREGULAR:
                break
            self.seek_to_sector(sector_location, size)
            sector = self.__compound_raw_io.read(size)
            entries = unpack('<{}L'.format(number_entries), sector)
            self.DIFAT.extend(entries[0:number_entries - 1])
            sector_location = entries[number_entries - 1]

        # build __file_allocation_table
        for i in range(0, self.Number_Of_FAT_Sectors):
            self.read_ids(self.__sector_size, self.DIFAT[i], self.__file_allocation_table)

        # build __mini_file_allocation_table
        sector_location = self.First_Mini_FAT_Sector_Location
        for i in range(0, self.__total_number_of_mini_sectors, self.__mini_sector_size):
            self.read_ids(self.__sector_size, sector_location, self.__mini_file_allocation_table)
            sector_location = self.__file_allocation_table[sector_location]

        # build __directory_entry_list
        sector_location = self.First_Directory_Sector_Location
        while sector_location != Cfb_Sector_Type.ENDOFCHAIN:
            self.seek_to_sector(sector_location, self.__sector_size)
            for i in range(0, self.__sector_size // 0x80):
                directory_entry = Cfb_File_Directory_Entry(self.__compound_raw_io)
                directory_entry.read()
                self.__directory_entry_list.append(directory_entry)
            sector_location = self.__file_allocation_table[sector_location]

        # build __mini_stream_sector_location_list
        root_directory_entry = self.__directory_entry_list[0]
        self.__number_sectors_in_mini_stream = (root_directory_entry.Stream_Size + self.__sector_size - 1) // self.__sector_size
        sector_location = root_directory_entry.Starting_Sector_Location
        while sector_location != Cfb_Sector_Type.ENDOFCHAIN:
            self.__mini_stream_sector_location_list.append(sector_location)
            sector_location = self.__file_allocation_table[sector_location]

        # build __directory_node_list
        self.build_directory_entry_dictionary(Cfb_Stream_Type.NOSTREAM, root_directory_entry.Child_ID)

        return True

    def seek_to_sector(self, sector_location, sector_size):
        self.__compound_raw_io.seek((sector_location + 1) * sector_size)

    def read_ids(self, sector_size, sector_location, dest_list):
        buffer = self.read_sector(sector_size, sector_location)
        number_sector = sector_size // Cfb_Size_Type.DWORD
        dest_list.extend(unpack("<{}I".format(number_sector), buffer))

    def read_sector(self, sector_size, sector_location):
        self.seek_to_sector(sector_location, sector_size)
        return self.__compound_raw_io.read(sector_size)

    def get_stream_sector_list(self, directory_entry):
        stream_sector_list = []
        is_large_stream = self.is_large_stream(directory_entry.Stream_Size)
        if is_large_stream:
            sector_shift = self.Sector_Shift
        else:
            sector_shift = self.Mini_Sector_Shift
        sector_size = 1 << sector_shift
        remaining_size = directory_entry.Stream_Size
        sector_location = directory_entry.Starting_Sector_Location
        while remaining_size > 0:
            if is_large_stream:
                stream_sector_list.append((sector_location + 1) << sector_shift)
                sector_location = self.__file_allocation_table[sector_location]
            else:
                mini_sector_location = self.get_mini_sector(sector_location)
                stream_sector_list.append(mini_sector_location << sector_shift)
                sector_location = self.__mini_file_allocation_table[sector_location]
            remaining_size -= sector_size
        return stream_sector_list

    def read_header_signature(self):
        return self.__compound_raw_io.read(Cfb_File_Header.HEADER_SIGNATURE_SIZE)

    def build_directory_entry_dictionary(self, parent_id, stream_id, path_name=""):
        if stream_id == Cfb_Stream_Type.NOSTREAM:
            return True
        if stream_id >= len(self.__directory_entry_list):
            return False
        directory_entry = self.__directory_entry_list[stream_id]
        if directory_entry.is_empty():
            return False
        directory_entry._Stream_ID = stream_id
        index = len(self.__directory_entry_dictionary)
        entry_path_name = path_name + Cfb_RawIO_Reader.SEPARATOR + directory_entry.Directory_Entry_Name
        self.__directory_entry_dictionary[entry_path_name] = directory_entry
        self.build_directory_entry_dictionary(parent_id, directory_entry.Left_Sibling_ID, path_name)
        self.build_directory_entry_dictionary(parent_id, directory_entry.Right_Sibling_ID, path_name)
        if directory_entry.is_directory():
            self.build_directory_entry_dictionary(index, directory_entry.Child_ID, entry_path_name)
        return True

    def is_large_stream(self, size):
        return size >= self.Mini_Stream_Cutoff_Size

    def get_mini_sector(self, sector_location):
        sub_shift = self.Sector_Shift - self.Mini_Sector_Shift
        stream_id = sector_location >> sub_shift
        if (stream_id >= self.__number_sectors_in_mini_stream):
            return None
        return ((self.__mini_stream_sector_location_list[stream_id] + 1) << sub_shift) \
                + (sector_location & ((1 << sub_shift) - 1))

    def get_stream_directory_names(self):
        return [key for key, value in sorted(self.__directory_entry_dictionary.items(), key=lambda item: item[1]._Stream_ID)]

    def get_stream_directory_entry(self, path_name):
        return self.__directory_entry_dictionary.get(path_name)


###############################################################################
class Cfb_File_Directory_Entry:
    """ for internal use only """

    """
    # [MS-CFB]: Compound File Binary File Format
    # 2.6.1 Compound File Directory Entry
    # http://msdn.microsoft.com/en-us/library/dd942138.aspx

    (0x00) Directory_Entry_Name[32] = (word) (contains 'Root Entry' as root ('utf-16-le'))
    (0x40) Directory_Entry_Name_Length = (word) (contains the number of bytes)
    (0x42) Object_Type = (byte) (OT_...)
    (0x43) Color_Flag = (byte) (CF_...)
    (0x44) Left_Sibling_ID = (dword) (SID_...)
    (0x48) Right_Sibling_ID = (dword) (SID_...)
    (0x4C) Child_ID = (dword) (SID_...)
    (0x50) CLSID[16] = (byte)
    (0x60) State_Bits = (dword)
    (0x64) Creation_Time = (qword) (contains a 64-bit value representing the number of 100-nanosecond intervals since January 1, 1601 (UTC))
    (0x6C) Modified_Time = (qword)
    (0x74) Starting_Sector_Location = (dword)
    (0x78) Stream_Size = (qword)
    (0x80) .
    """

    __slots__ = (
            'Directory_Entry_Name',
            'Directory_Entry_Name_Length',
            'Object_Type',
            'Color_Flag',
            'Left_Sibling_ID',
            'Right_Sibling_ID',
            'Child_ID',
            'CLSID',
            'State_Bits',
            'Creation_Time',
            'Modified_Time',
            'Starting_Sector_Location',
            'Stream_Size',
            '__compound_raw_io',
            '_Stream_ID',
            )

    def __init__(self, compound_raw_io):
        if not isinstance(compound_raw_io, Cfb_RawIO_Reader):
            raise TypeError("Cfb_File_Directory_Entry(compound_raw_io)")
        self.__compound_raw_io = compound_raw_io
        self._Stream_ID = Cfb_Stream_Type.NOSTREAM


    def __repr__(self):
        return "<Cfb_File_Directory_Entry\n" \
                "Directory_Entry_Name=\"{}\",\n" \
                "Directory_Entry_Name_Length=\"{}\",\n" \
                "Object_Type=\"{}\",\n" \
                "Color_Flag=\"{}\",\n" \
                "Left_Sibling_ID=\"{}\",\n" \
                "Right_Sibling_ID=\"{}\",\n" \
                "Child_ID=\"{}\",\n" \
                "CLSID=\"{}\",\n" \
                "State_Bits=\"{}\",\n" \
                "Creation_Time=\"{}\",\n" \
                "Modified_Time=\"{}\",\n" \
                "Starting_Sector_Location=\"{}\",\n" \
                "Stream_Size=\"{}\",\n" \
                "/>".format(
                self.Directory_Entry_Name,
                self.Directory_Entry_Name_Length,
                Cfb_Object_Type.to_string(self.Object_Type),
                Cfb_Color_Flag.to_string(self.Color_Flag),
                Cfb_Stream_Type.to_string(self.Left_Sibling_ID),
                Cfb_Stream_Type.to_string(self.Right_Sibling_ID),
                Cfb_Stream_Type.to_string(self.Child_ID),
                Cfb_Extras.str_clsid(self.CLSID),
                self.State_Bits,
                Cfb_Extras.str_time(self.Creation_Time),
                Cfb_Extras.str_time(self.Modified_Time),
                Cfb_Sector_Type.to_string(self.Starting_Sector_Location),
                self.Stream_Size,
                )

    def read(self):
        utf_16_le_buffer = self.__compound_raw_io.read(32 * Cfb_Size_Type.UTF16)
        self.Directory_Entry_Name_Length = self.__compound_raw_io.read_word()
        if self.Directory_Entry_Name_Length:
            self.Directory_Entry_Name = \
                    (utf_16_le_buffer[0:(self.Directory_Entry_Name_Length - Cfb_Size_Type.WORD)]
                    ).decode('utf-16-le')
        else:
            self.Directory_Entry_Name = ""
        self.Object_Type = self.__compound_raw_io.read_byte()
        self.Color_Flag = self.__compound_raw_io.read_byte()
        self.Left_Sibling_ID = self.__compound_raw_io.read_dword()
        self.Right_Sibling_ID = self.__compound_raw_io.read_dword()
        self.Child_ID = self.__compound_raw_io.read_dword()
        self.CLSID = self.__compound_raw_io.read_clsid()
        self.State_Bits = self.__compound_raw_io.read_dword()
        self.Creation_Time = self.__compound_raw_io.read_qword()
        self.Modified_Time = self.__compound_raw_io.read_qword()
        self.Starting_Sector_Location = self.__compound_raw_io.read_dword()
        self.Stream_Size = self.__compound_raw_io.read_qword()

    def is_empty(self):
        return self.Object_Type == Cfb_Object_Type.UNKNOWN

    def is_directory(self):
        return self.Object_Type == Cfb_Object_Type.STORAGE \
                or self.Object_Type == Cfb_Object_Type.ROOT_STORAGE


###############################################################################
class Cfb_Extras:
    """ for internal use only """

    @staticmethod
    def to_time(value):
        if value == 0:
            return "UNKNOWN"
        MS_TO_PY_EPOCH_FILETIME_DIFF = -11644473600.0
        MS_100NANO_TO_SECONDS = 10000000.0
        ms_time = value / MS_100NANO_TO_SECONDS
        py_time = ms_time + MS_TO_PY_EPOCH_FILETIME_DIFF
        if py_time < 0:
            return None
        return gmtime(py_time)

    @staticmethod
    def str_time(value):
        if value == 0:
            return "UNKNOWN"
        MS_TO_PY_EPOCH_FILETIME_DIFF = -11644473600.0
        MS_100NANO_TO_SECONDS = 10000000.0
        ms_time = value / MS_100NANO_TO_SECONDS
        py_time = ms_time + MS_TO_PY_EPOCH_FILETIME_DIFF
        if py_time < 0:
            return "0x{:016X}".format(value)
        return strftime("%Y-%m-%d %H:%M:%S", gmtime(py_time))

    @staticmethod
    def str_clsid(value):
        #'<L2H8B'
        #(0xF3F2F1F0, 0xE1E0, 0xD1D0, 0x07, 0x06, 0x05, 0x04, 0x03, 0x02, 0x01, 0x00, )
        dw1, w1, w2, b1, b2, b3, b4, b5, b6, b7, b8 = unpack('<L2H8B', value)
        return "{:08X}-{:04X}-{:04X}-{:02X}{:02X}{:02X}{:02X}{:02X}{:02X}{:02X}{:02X}".format(dw1, w1, w2, b1, b2, b3, b4, b5, b6, b7, b8)


###############################################################################
class Cfb_Size_Type:
    """ for internal use only """
    BYTE = 1
    WORD = 2
    DWORD = 4
    QWORD = 8

    UTF16 = 2
    CLSID = 16

    @staticmethod
    def to_string(value):
        if value == Cfb_Size_Type.BYTE:
            return 'BYTE'
        elif value == Cfb_Size_Type.WORD:
            return 'WORD'
        elif value == Cfb_Size_Type.DWORD:
            return 'DWORD'
        elif value == Cfb_Size_Type.QWORD:
            return 'QWORD'
        return DEBUG_CFB_SPEC.unknown_value(value)


class Cfb_Sector_Type:
    """ for internal use only """
    MAXREGULAR = 0xFFFFFFFA
    DIFAT = 0xFFFFFFFC
    FAT = 0xFFFFFFFD
    ENDOFCHAIN = 0xFFFFFFFE
    FREE = 0xFFFFFFFF

    @staticmethod
    def to_string(value):
        if value >= 0 and value < Cfb_Sector_Type.MAXREGULAR:
            return "{}".format(value)
        elif value == Cfb_Sector_Type.MAXREGULAR:
            return 'MAXREGULAR'
        elif value == Cfb_Sector_Type.DIFAT:
            return 'DIFAT'
        elif value == Cfb_Sector_Type.FAT:
            return 'FAT'
        elif value == Cfb_Sector_Type.ENDOFCHAIN:
            return 'ENDOFCHAIN'
        elif value == Cfb_Sector_Type.FREE:
            return 'FREE'
        return DEBUG_CFB_SPEC.unknown_value(value)


class Cfb_Stream_Type:
    """ for internal use only """
    MAXREGULAR = 0xFFFFFFFA
    NOSTREAM = 0xFFFFFFFF

    @staticmethod
    def to_string(value):
        if value >= 0 and value < Cfb_Stream_Type.MAXREGULAR:
            return "{}".format(value)
        elif value == Cfb_Stream_Type.MAXREGULAR:
            return 'MAXREGULAR'
        elif value == Cfb_Stream_Type.NOSTREAM:
            return 'NOSTREAM'
        return DEBUG_CFB_SPEC.unknown_value(value)


###############################################################################
class Cfb_Object_Type:
    """ for internal use only """
    UNKNOWN = 0
    STORAGE = 1
    STREAM = 2
    ROOT_STORAGE = 5

    @staticmethod
    def to_string(value):
        if value == Cfb_Object_Type.UNKNOWN:
            return 'UNKNOWN'
        elif value == Cfb_Object_Type.STORAGE:
            return 'STORAGE'
        elif value == Cfb_Object_Type.STREAM:
            return 'STREAM'
        elif value == Cfb_Object_Type.ROOT_STORAGE:
            return 'ROOT_STORAGE'
        return DEBUG_CFB_SPEC.unknown_value(value)


###############################################################################
class Cfb_Color_Flag:
    """ for internal use only """
    RED = 0
    BLACK = 1

    @staticmethod
    def to_string(value):
        if value == Cfb_Color_Flag.RED:
            return 'RED'
        elif value == Cfb_Color_Flag.BLACK:
            return 'BLACK'
        return DEBUG_CFB_SPEC.unknown_value(value)

###############################################################################


###############################################################################
#234567890123456789012345678901234567890123456789012345678901234567890123456789
#--------1---------2---------3---------4---------5---------6---------7---------
# ##### END OF FILE #####
