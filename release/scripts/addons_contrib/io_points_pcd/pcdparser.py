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


import struct
import io

try:
    import lzf
    GOT_LZF_MODULE=True
except:
    GOT_LZF_MODULE=False



def dumpHexData(data):
    for byte in data:
        print(hex(byte) + " ", end="")
    print()


def encodeASCIILine(line):
    return line.decode(encoding='ASCII')



class Point:

    def __init__(self):
        pass


    def setField(self, fieldname, values):
        pass




class PointXYZ(Point):

    def __init__(self):
        super().__init__()
        self.x = 0
        self.y = 0
        self.z = 0


    def setField(self, fieldname, values):
        value = values[0]
        if fieldname == 'x':
            self.x = value
        elif fieldname == 'y':
            self.y = value
        elif fieldname == 'z':
            self.z = value




class PCDParser:

    filepath = ''
    file = None

    points = []
    PointClass = None

    headerEnd = False


    @staticmethod
    def factory(filepath, PointClass):
        version = 'NO_VERSION_NUMBER'
        with open(filepath, 'rb') as f:
            for b in f:
                line = encodeASCIILine(b)
                line_split = line.split()
                if line_split[0] == 'VERSION' and len(line_split) > 1:
                    version = line_split[1]
                    break

        if version == ".7" or version == "0.7":
            return PCDParser_v0_7(filepath, PointClass)
        else:
            return None


    def __init__(self, filepath, PointClass):
        self.filepath = filepath
        self.PointClass = PointClass

        self.file = None
        self.headerEnd = False
        self.points = []


    def parserWarning(self, msg):
        print("[WARNING] ", msg)


    def rmComment(self, line):
        return line[:line.find('#')]


    def parseFile(self):
        with open(self.filepath, 'rb') as self.file:
            self.parseHeader()
            self.parsePoints()

    def onlyParseHeader(self):
        with open(self.filepath, 'rb') as self.file:
            self.parseHeader()


    def parseHeader(self):
        for b in self.file:
            line = encodeASCIILine(b)
            line = self.rmComment(line)

            split = line.split()
            if len(split) > 0:
                self.parseHeaderLine(split)

            if self.headerEnd:
                self.finalizeHeader()
                break


    def parseHeaderLine(self, split):
        keyword = split[0]
        self.parserWarning("Uknown header Keyword '" + keyword + "' gets ignored")


    def finalizeHeader(self):
        pass


    def parsePoints(self):
        pass


    def getPoints(self):
        return self.points


    def version(self):
        return 'NO_VERSION_NUMBER'




class PCDParser_v0_7(PCDParser):

    fields = []

    def __init__(self, filepath, PointClass):
        super().__init__(filepath, PointClass)
        self.fields = []


    def version(self):
        return '.7'


    def parseHeaderLine(self, split):
        keyword = split[0]
        if keyword == 'VERSION':
            self.parseVERSION(split[1:])
        elif keyword == 'FIELDS':
            self.parseFIELDS(split[1:])
        elif keyword == 'SIZE':
            self.parseSIZE(split[1:])
        elif keyword == 'TYPE':
            self.parseTYPE(split[1:])
        elif keyword == 'COUNT':
            self.parseCOUNT(split[1:])
        elif keyword == 'WIDTH':
            self.parseWIDTH(split[1:])
        elif keyword == 'HEIGHT':
            self.parseHEIGHT(split[1:])
        elif keyword == 'POINTS':
            self.parsePOINTS(split[1:])
        elif keyword == 'DATA':
            self.parseDATA(split[1:])
        else:
            super().parseHeaderLine(split)


    def parseVERSION(self, split):
        pass


    def parseFIELDS(self, split):
        print("SPLIT FIELDS:", split)
        for field in split:
            self.fields.append([field, None, None, None])
        print("FIELDS, after parsing:", self.fields)


    def parseSIZE(self, split):
        for i, size in enumerate(split):
            self.fields[i][1] = int(size)


    def parseTYPE(self, split):
        for i, type in enumerate(split):
            self.fields[i][2] = type


    def parseCOUNT(self, split):
        for i, count in enumerate(split):
            self.fields[i][3] = int(count)


    def parseWIDTH(self, split):
        self.width = int(split[0])


    def parseHEIGHT(self, split):
        self.height = int(split[0])


    def parsePOINTS(self, split):
        pass


    def parseDATA(self, split):
        if split[0] == "ascii":
            self.datatype = 'ASCII'
        elif split[0] == "binary":
            self.datatype = 'BINARY'
        elif split[0] == "binary_compressed":
            self.datatype = 'BINARY_COMPRESSED'
        self.headerEnd = True


    def finalizeHeader(self):
        self.numPoints = self.width * self.height
        print("FIELDS - finalized", self.fields)


    def parsePoints(self):
        if self.datatype == 'ASCII':
            self.parseASCII()
        elif self.datatype == 'BINARY':
            self.parseBINARY()
        elif self.datatype == 'BINARY_COMPRESSED':
            if not GOT_LZF_MODULE:
                print("[ERROR] No support for BINARY COMPRESSED data format.")
                return
            else:
                self.parseBINARY_COMPRESSED()


    def parseASCII(self):
        parsedPoints = 0
        while parsedPoints < self.numPoints:

            try:
                b = self.file.readline()
                line = encodeASCIILine(b)
            except:
                self.parserError("Unexpected end of data")
                return
            line = self.rmComment(line)
            split = line.split()

            if (len(split) == 0):
                continue
            else:
                parsedPoints += 1

            point = self.PointClass()

            for field in self.fields:
                fieldname = field[0]
                fieldtype = field[2]
                fieldcount = field[3]

                values = []
                for i in range(fieldcount):
                    vs = split.pop(0)
                    if fieldtype == 'F':
                        values.append(float(vs))
                    elif fieldtype in ['U', 'I']:
                        values.append(int(vs))

                point.setField(fieldname, values)

            self.points.append(point)


    def parseBINARY_COMPRESSED(self):
        """ BROKEN!!! - There seem to be uncompatiblities
            with pcl LZF and liblzf"""
        max_size = 1024**3 # 1GB
        fs = '<i'
        compressed_len = struct.unpack('<i', self.file.read(4))[0]
        decompressed_len = struct.unpack('<i', self.file.read(4))[0]

        compressed_body = self.file.read(compressed_len)
        decompressed_body = lzf.decompress(compressed_body, max_size)

        fobj = io.BytesIO(decompressed_body)
        self.parseBINARY(fobj)



    def parseBINARY(self, infile=""):

        if infile == "":
            infile = self.file

        for pointi in range(self.numPoints):
            point = self.PointClass()

            for field in self.fields:
                fieldname = field[0]
                fieldsize = field[1]
                fieldtype = field[2]
                fieldcount = field[3]

                values = []
                for i in range(fieldcount):

                    fs = None
                    if fieldtype == 'F':
                        if fieldsize == 4: #float
                            fs = '<f'
                        elif fieldsize == 8: #double
                            fs = '<d'
                    elif fieldtype == 'U':
                        if fieldsize == 1: #unsinged char
                            fs = '<B'
                        elif fieldsize == 2: #unsinged short
                            fs = '<H'
                        elif fieldsize == 4: #unsinged int
                            fs =  '<I'
                    elif fieldtype == 'I':
                        if fieldsize == 1: #char
                            fs = '<c'
                        elif fieldsize == 2: #short
                            fs = '<h'
                        elif fieldsize == 4: #signed int
                            fs =  '<i'

                    raw = infile.read(fieldsize)
                    if (fs):
                        data = struct.unpack(fs, raw)
                        values.append(data[0])

                point.setField(fieldname, values)

            self.points.append(point)




class PCDWriter:

    def __init__(self, points):
        self.points = points


    def _header(self):
        header =  "# .PCD v0.7 - Point Cloud Data file format\n"
        header += "VERSION 0.7\n"
        header += "FIELDS x y z\n"
        header += "SIZE 4 4 4\n"
        header += "TYPE F F F\n"
        header += "COUNT 1 1 1\n"
        header += "WIDTH " + str(len(self.points)) + "\n"
        header += "HEIGHT 1\n"
        header += "VIEWPOINT 0 0 0 1 0 0 0\n"
        header += "POINTS " + str(len(self.points)) + "\n"
        header += "DATA ascii\n"

        return header


    def write(self, filepath):

        with open(filepath, "w") as f:
            f.write(self._header())
            for point in self.points:
                f.write(str(point.x))
                f.write(" ")
                f.write(str(point.y))
                f.write(" ")
                f.write(str(point.z))
                f.write("\n")



def test():
    parser = PCDParser.factory('test.pcd', PointXYZ)
    if parser:
        parser.parseFile()
        points = parser.getPoints()
        for point in points:
            print(point.x, point.y, point.z)
    else:
        print("Can't create parser for this file")
