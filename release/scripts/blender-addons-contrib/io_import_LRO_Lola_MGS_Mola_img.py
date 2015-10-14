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

bl_info = {
    "name": "LRO Lola & MGS Mola img Importer",
    "author": "Valter Battioli (ValterVB)",
    "version": (1, 1, 8),
    "blender": (2, 58, 0),
    "location": "3D window > Tool Shelf",
    "description": "Import DTM from LRO Lola and MGS Mola",
    "warning": "May consume a lot of memory",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
        "Scripts/Import-Export/NASA_IMG_Importer",
    "tracker_url": "https://developer.blender.org/T25462",
    "category": "Import-Export"}


#***********************************************************************
#ver. 0.0.1: -First version
#ver. 0.0.2: -Add check on path and file
#            -Check on selected coordinates more complete
#ver. 1.1.0: -Optimized for less memory
#ver. 1.1.1: -Correct bug for real value of the High (bad error).
#             now it's less artistic, bat more real Always possible use
#             the old formula. check Magnify (x4)
#            -Correct the bug for directory with dot in the name
#            -Add some warning and more information
#            -Add slider for the scale and info on it
#ver. 1.1.2: -Word correction
#            -Correct the problem for Unix (Upper lower case)
#              If the Ext of the file selected from user is upper
#              than the second file is Upper and Viceversa.
#              (I can't verify because i have Win)
#ver. 1.1.3: -Little fix for previous fix on upper/lower case
#ver. 1.1.4: -Fix for recent API changes. Thanks to Filiciss.
#            -Some code cleaning (PEP8)
#ver. 1.1.5: -Fix for recent API changes. Thanks to Filiciss.
#ver. 1.1.6: -Fix for API changes, and restore Scale factor
#ver. 1.1.7: -Fix for API changes. Move some code out of draw
#ver. 1.1.8: -Add a reset button
#************************************************************************

import bpy
import os.path
import math
import array
import mathutils
from mathutils import *

TO_RAD = math.pi / 180  # From degrees to radians

# turning off relative path - it causes an error if it was true
if bpy.context.user_preferences.filepaths.use_relative_paths == True:
    bpy.context.user_preferences.filepaths.use_relative_paths = False


# A very simple "bridge" tool.
# Connects two equally long vertex rows with faces.
# Returns a list of the new faces (list of  lists)
#
# vertIdx1 ... First vertex list (list of vertex indices).
# vertIdx2 ... Second vertex list (list of vertex indices).
# closed ... Creates a loop (first & last are closed).
# flipped ... Invert the normal of the face(s).
#
# Note: You can set vertIdx1 to a single vertex index to create a fan/star
#       of faces.
# Note: If both vertex idx list are the same length they have to have at
#       least 2 vertices.
def createFaces(vertIdx1, vertIdx2, closed=False, flipped=False):
    faces = []

    if not vertIdx1 or not vertIdx2:
        return None

    if len(vertIdx1) < 2 and len(vertIdx2) < 2:
        return None

    fan = False
    if (len(vertIdx1) != len(vertIdx2)):
        if (len(vertIdx1) == 1 and len(vertIdx2) > 1):
            fan = True
        else:
            return None

    total = len(vertIdx2)

    if closed:
        # Bridge the start with the end.
        if flipped:
            face = [
                vertIdx1[0],
                vertIdx2[0],
                vertIdx2[total - 1]]
            if not fan:
                face.append(vertIdx1[total - 1])
            faces.append(face)

        else:
            face = [vertIdx2[0], vertIdx1[0]]
            if not fan:
                face.append(vertIdx1[total - 1])
            face.append(vertIdx2[total - 1])
            faces.append(face)

    # Bridge the rest of the faces.
    for num in range(total - 1):
        if flipped:
            if fan:
                face = [vertIdx2[num], vertIdx1[0], vertIdx2[num + 1]]
            else:
                face = [vertIdx2[num], vertIdx1[num],
                    vertIdx1[num + 1], vertIdx2[num + 1]]
            faces.append(face)
        else:
            if fan:
                face = [vertIdx1[0], vertIdx2[num], vertIdx2[num + 1]]
            else:
                face = [vertIdx1[num], vertIdx2[num],
                    vertIdx2[num + 1], vertIdx1[num + 1]]
            faces.append(face)
    return faces


#Utility Function ********************************************************
#
#Input: Latitude Output: Number of the line (1 to n)
def LatToLine(Latitude):
    tmpLines = round((MAXIMUM_LATITUDE - Latitude) * MAP_RESOLUTION + 1.0)
    if tmpLines > LINES:
        tmpLines = LINES
    return tmpLines


#Input: Number of the line (1 to n) Output: Latitude
def LineToLat(Line):
    if MAP_RESOLUTION == 0:
        return 0
    else:
        return float(MAXIMUM_LATITUDE - (Line - 1) / MAP_RESOLUTION)


#Input: Longitude Output: Number of the point (1 to n)
def LongToPoint(Longitude):
    tmpPoints = round((Longitude - WESTERNMOST_LONGITUDE) *
                       MAP_RESOLUTION + 1.0)
    if tmpPoints > LINE_SAMPLES:
        tmpPoints = LINE_SAMPLES
    return tmpPoints


#Input: Number of the Point (1 to n) Output: Longitude
def PointToLong(Point):
    if MAP_RESOLUTION == 0:
        return 0
    else:
        return float(WESTERNMOST_LONGITUDE + (Point - 1) / MAP_RESOLUTION)


#Input: Latitude Output: Neareast real Latitude on grid
def RealLat(Latitude):
    return float(LineToLat(LatToLine(Latitude)))


#Input: Longitude Output: Neareast real Longitude on grid
def RealLong(Longitude):
    return float(PointToLong(LongToPoint(Longitude)))
#**************************************************************************


def MakeMaterialMars(obj):
    #Copied from io_convert_image_to_mesh_img
    mat = bpy.data.materials.new("Mars")
    mat.diffuse_shader = 'MINNAERT'
    mat.diffuse_color = (0.426, 0.213, 0.136)
    mat.darkness = 0.8

    mat.specular_shader = 'WARDISO'
    mat.specular_color = (1.000, 0.242, 0.010)
    mat.specular_intensity = 0.010
    mat.specular_slope = 0.100
    obj.data.materials.append(mat)


def MakeMaterialMoon(obj):
    #Same as Mars Material, but i have canged the color
    mat = bpy.data.materials.new("Moon")
    mat.diffuse_shader = 'MINNAERT'
    mat.diffuse_color = (0.426, 0.426, 0.426)
    mat.darkness = 0.8

    mat.specular_shader = 'WARDISO'
    mat.specular_color = (0.6, 0.6, 0.6)
    mat.specular_intensity = 0.010
    mat.specular_slope = 0.100
    obj.data.materials.append(mat)


#Read the LBL file
def ReadLabel(FileName):
    global FileAndPath
    global LINES, LINE_SAMPLES, SAMPLE_TYPE, SAMPLE_BITS, UNIT, MAP_RESOLUTION
    global MAXIMUM_LATITUDE, MINIMUM_LATITUDE, WESTERNMOST_LONGITUDE
    global EASTERNMOST_LONGITUDE, SCALING_FACTOR, OFFSET, RadiusUM, TARGET_NAME
    global Message

    if FileName == '':
        return
    LINES = LINE_SAMPLES = SAMPLE_BITS = MAP_RESOLUTION = 0
    MAXIMUM_LATITUDE = MINIMUM_LATITUDE = 0.0
    WESTERNMOST_LONGITUDE = EASTERNMOST_LONGITUDE = 0.0
    OFFSET = SCALING_FACTOR = 0.0
    SAMPLE_TYPE = UNIT = TARGET_NAME = RadiusUM = Message = ""

    FileAndPath = FileName
    FileAndExt = os.path.splitext(FileAndPath)
    try:
        #Check for UNIX that is case sensitive
        #If the Ext of the file selected from user is Upper, than the second
        #file is Upper and Viceversa
        if FileAndExt[1].isupper():
            f = open(FileAndExt[0] + ".LBL", 'r')  # Open the label file
        else:
            f = open(FileAndExt[0] + ".lbl", 'r')  # Open the label file
        Message = ""
    except:
        Message = "FILE LBL NOT AVAILABLE OR YOU HAVEN'T SELECTED A FILE"
        return

    block = ""
    OFFSET = 0
    for line in f:
        tmp = line.split("=")
        if tmp[0].strip() == "OBJECT" and tmp[1].strip() == "IMAGE":
            block = "IMAGE"
        elif tmp[0].strip() == "OBJECT" and tmp[1].strip() == "IMAGE_MAP_PROJECTION":
            block = "IMAGE_MAP_PROJECTION"
        elif tmp[0].strip() == "END_OBJECT" and tmp[1].strip() == "IMAGE":
            block = ""
        elif tmp[0].strip() == "END_OBJECT" and tmp[1].strip() == "IMAGE_MAP_PROJECTION":
            block = ""
        elif tmp[0].strip() == "TARGET_NAME":
            block = ""
            TARGET_NAME = tmp[1].strip()
        if block == "IMAGE":
            if line.find("LINES") != -1 and not(line.startswith("/*")):
                tmp = line.split("=")
                LINES = int(tmp[1].strip())
            elif line.find("LINE_SAMPLES") != -1 and not(line.startswith("/*")):
                tmp = line.split("=")
                LINE_SAMPLES = int(tmp[1].strip())
            elif line.find("UNIT") != -1 and not(line.startswith("/*")):
                tmp = line.split("=")
                UNIT = tmp[1].strip()
            elif line.find("SAMPLE_TYPE") != -1 and not(line.startswith("/*")):
                tmp = line.split("=")
                SAMPLE_TYPE = tmp[1].strip()
            elif line.find("SAMPLE_BITS") != -1 and not(line.startswith("/*")):
                tmp = line.split("=")
                SAMPLE_BITS = int(tmp[1].strip())
            elif line.find("SCALING_FACTOR") != -1 and not(line.startswith("/*")):
                tmp = line.split("=")
                tmp = tmp[1].split("<")
                SCALING_FACTOR = float(tmp[0].replace(" ", ""))
            elif line.find("OFFSET") != -1 and not(line.startswith("/*")):
                tmp = line.split("=")
                if tmp[0].find("OFFSET") != -1 and len(tmp) > 1:
                    tmp = tmp[1].split("<")
                    tmp[0] = tmp[0].replace(".", "")
                    OFFSET = float(tmp[0].replace(" ", ""))
        elif block == "IMAGE_MAP_PROJECTION":
            if line.find("A_AXIS_RADIUS") != -1 and not(line.startswith("/*")):
                tmp = line.split("=")
                tmp = tmp[1].split("<")
                A_AXIS_RADIUS = float(tmp[0].replace(" ", ""))
                RadiusUM = tmp[1].rstrip().replace(">", "")
            elif line.find("B_AXIS_RADIUS") != -1 and not(line.startswith("/*")):
                tmp = line.split("=")
                tmp = tmp[1].split("<")
                B_AXIS_RADIUS = float(tmp[0].replace(" ", ""))
            elif line.find("C_AXIS_RADIUS") != -1 and not(line.startswith("/*")):
                tmp = line.split("=")
                tmp = tmp[1].split("<")
                C_AXIS_RADIUS = float(tmp[0].replace(" ", ""))
            elif line.find("MAXIMUM_LATITUDE") != -1 and not(line.startswith("/*")):
                tmp = line.split("=")
                tmp = tmp[1].split("<")
                MAXIMUM_LATITUDE = float(tmp[0].replace(" ", ""))
            elif line.find("MINIMUM_LATITUDE") != -1 and not(line.startswith("/*")):
                tmp = line.split("=")
                tmp = tmp[1].split("<")
                MINIMUM_LATITUDE = float(tmp[0].replace(" ", ""))
            elif line.find("WESTERNMOST_LONGITUDE") != -1 and not(line.startswith("/*")):
                tmp = line.split("=")
                tmp = tmp[1].split("<")
                WESTERNMOST_LONGITUDE = float(tmp[0].replace(" ", ""))
            elif line.find("EASTERNMOST_LONGITUDE") != -1 and not(line.startswith("/*")):
                tmp = line.split("=")
                tmp = tmp[1].split("<")
                EASTERNMOST_LONGITUDE = float(tmp[0].replace(" ", ""))
            elif line.find("MAP_RESOLUTION") != -1 and not(line.startswith("/*")):
                tmp = line.split("=")
                tmp = tmp[1].split("<")
                MAP_RESOLUTION = float(tmp[0].replace(" ", ""))
    f.close
    MAXIMUM_LATITUDE = MAXIMUM_LATITUDE - 1 / MAP_RESOLUTION / 2
    MINIMUM_LATITUDE = MINIMUM_LATITUDE + 1 / MAP_RESOLUTION / 2
    WESTERNMOST_LONGITUDE = WESTERNMOST_LONGITUDE + 1 / MAP_RESOLUTION / 2
    EASTERNMOST_LONGITUDE = EASTERNMOST_LONGITUDE - 1 / MAP_RESOLUTION / 2
    if OFFSET == 0:  # When OFFSET isn't available I use the medium of the radius
        OFFSET = (A_AXIS_RADIUS + B_AXIS_RADIUS + C_AXIS_RADIUS) / 3
    else:
        OFFSET = OFFSET / 1000  # Convert m to Km
    if SCALING_FACTOR == 0:
        SCALING_FACTOR = 1.0  # When isn'tavailable I set it to 1


def update_fpath(self, context):
    global start_up
    start_up=False
    ReadLabel(bpy.context.scene.fpath)
    if Message != "":
        start_up=True
    else:
        typ = bpy.types.Scene
        var = bpy.props
        typ.FromLat = var.FloatProperty(description="From Latitude", min=float(MINIMUM_LATITUDE), max=float(MAXIMUM_LATITUDE), precision=3, default=0.0)
        typ.ToLat = var.FloatProperty(description="To Latitude", min=float(MINIMUM_LATITUDE), max=float(MAXIMUM_LATITUDE), precision=3)
        typ.FromLong = var.FloatProperty(description="From Longitude", min=float(WESTERNMOST_LONGITUDE), max=float(EASTERNMOST_LONGITUDE), precision=3)
        typ.ToLong = var.FloatProperty(description="To Longitude", min=float(WESTERNMOST_LONGITUDE), max=float(EASTERNMOST_LONGITUDE), precision=3)
        typ.Scale = var.IntProperty(description="Scale", min=1, max=100, default=1)
        typ.Magnify = var.BoolProperty(description="Magnify", default=False)


#Import the data and draw the planet
class Import(bpy.types.Operator):
    bl_idname = 'import.lro_and_mgs'
    bl_label = 'Start Import'
    bl_description = 'Import the data'

    def execute(self, context):
        From_Lat = RealLat(bpy.context.scene.FromLat)
        To_Lat = RealLat(bpy.context.scene.ToLat)
        From_Long = RealLong(bpy.context.scene.FromLong)
        To_Long = RealLong(bpy.context.scene.ToLong)
        BlenderScale = bpy.context.scene.Scale
        Exag = bpy.context.scene.Magnify
        Vertex = []  # Vertex array
        Faces = []  # Faces arrays
        FirstRow = []
        SecondRow = []
        print('*** Start create vertex ***')
        FileAndPath = bpy.context.scene.fpath
        FileAndExt = os.path.splitext(FileAndPath)
        #Check for UNIX that is case sensitive
        #If the Ext of the file selected from user is Upper, than the second file is Upper and Viceversa
        if FileAndExt[1].isupper():
            FileName = FileAndExt[0] + ".IMG"
        else:
            FileName = FileAndExt[0] + ".img"
        f = open(FileName, 'rb')
        f.seek(int((int(LatToLine(From_Lat)) - 1) * (LINE_SAMPLES * (SAMPLE_BITS / 8))), 1)  # Skip the first n line of point
        SkipFirstPoint = int((LongToPoint(From_Long) - 1) * (SAMPLE_BITS / 8))  # Nunmber of points to skip
        PointsToRead = (LongToPoint(To_Long) - LongToPoint(From_Long) + 1) * (int(SAMPLE_BITS) / 8)  # Number of points to be read
        SkipLastPoint = (LINE_SAMPLES * (SAMPLE_BITS / 8)) - PointsToRead - SkipFirstPoint  # Nunmber of points to skip
        LatToRead = From_Lat
        while (LatToRead >= To_Lat):
            f.seek(SkipFirstPoint, 1)  # Skip the first n point
            Altitudes = f.read(int(PointsToRead))  # Read all the point
            Altitudes = array.array("h", Altitudes)  # Change to Array of signed short
            if SAMPLE_TYPE == "MSB_INTEGER":
                Altitudes.byteswap()  # Change from MSB (big endian) to LSB (little endian)
            LongToRead = From_Long
            PointToRead = 0
            while (LongToRead <= To_Long):
                if Exag:
                    tmpRadius = (Altitudes[PointToRead] / SCALING_FACTOR / 1000 + OFFSET) / BlenderScale  # Old formula (High*4)
                else:
                    tmpRadius = ((Altitudes[PointToRead] * SCALING_FACTOR) / 1000 + OFFSET) / BlenderScale  # Correct scale
                CurrentRadius = tmpRadius * (math.cos(LatToRead * TO_RAD))
                X = CurrentRadius * (math.sin(LongToRead * TO_RAD))
                Y = tmpRadius * math.sin(LatToRead * TO_RAD)
                Z = CurrentRadius * math.cos(LongToRead * TO_RAD)
                Vertex.append(Vector((float(X), float(Y), float(Z))))
                LongToRead += (1 / MAP_RESOLUTION)
                PointToRead += 1
            f.seek(int(SkipLastPoint), 1)
            LatToRead -= (1 / MAP_RESOLUTION)
        f.close
        del Altitudes
        print('*** End create Vertex   ***')

        print('*** Start create faces ***')
        LinesToRead = int(LatToLine(To_Lat) - LatToLine(From_Lat) + 1)   # Number of the lines to read
        PointsToRead = int(LongToPoint(To_Long) - LongToPoint(From_Long) + 1)  # Number of the points to read
        for Point in range(0, PointsToRead):
            FirstRow.append(Point)
            SecondRow.append(Point + PointsToRead)
        if int(PointsToRead) == LINE_SAMPLES:
            FaceTemp = createFaces(FirstRow, SecondRow, closed=True, flipped=True)
        else:
            FaceTemp = createFaces(FirstRow, SecondRow, closed=False, flipped=True)
        Faces.extend(FaceTemp)

        FaceTemp = []
        for Line in range(1, (LinesToRead - 1)):
            FirstRow = SecondRow
            SecondRow = []
            FacesTemp = []
            for Point in range(0, PointsToRead):
                SecondRow.append(Point + (Line + 1) * PointsToRead)
            if int(PointsToRead) == LINE_SAMPLES:
                FaceTemp = createFaces(FirstRow, SecondRow, closed=True, flipped=True)
            else:
                FaceTemp = createFaces(FirstRow, SecondRow, closed=False, flipped=True)
            Faces.extend(FaceTemp)
        del FaceTemp
        print('*** End create faces   ***')

        print ('*** Start draw ***')
        mesh = bpy.data.meshes.new(TARGET_NAME)
        mesh.from_pydata(Vertex, [], Faces)
        del Faces
        del Vertex
        mesh.update()
        ob_new = bpy.data.objects.new(TARGET_NAME, mesh)
        ob_new.data = mesh
        scene = bpy.context.scene
        scene.objects.link(ob_new)
        scene.objects.active = ob_new
        ob_new.select = True
        print ('*** End draw   ***')
        print('*** Start Smooth ***')
        bpy.ops.object.shade_smooth()
        print('*** End Smooth   ***')
        if TARGET_NAME == "MOON":
            MakeMaterialMoon(ob_new)
        elif TARGET_NAME == "MARS":
            MakeMaterialMars(ob_new)
        print('*** FINISHED ***')
        return {'FINISHED'}


# User inteface
class Img_Importer(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOL_PROPS"
    bl_label = "LRO Lola & MGS Mola IMG Importer"

    def __init__(self):
        typ = bpy.types.Scene
        var = bpy.props

    def draw(self, context):
        layout = self.layout
        if start_up:
            layout.prop(context.scene, "fpath")
            col = layout.column()
            split = col.split(align=True)
            if Message != "":
                split.label("Message: " + Message)
        else:
            col = layout.column()
            split = col.split(align=True)
            split.label("Minimum Latitude: " + str(MINIMUM_LATITUDE) + " deg")
            split.label("Maximum Latitude: " + str(MAXIMUM_LATITUDE) + " deg")

            split = col.split(align=True)
            split.label("Westernmost Longitude: " + str(WESTERNMOST_LONGITUDE) + " deg")
            split.label("Easternmost Longitude: " + str(EASTERNMOST_LONGITUDE) + " deg")

            split = col.split(align=True)
            split.label("Lines: " + str(LINES))
            split.label("Line samples: " + str(LINE_SAMPLES))

            split = col.split(align=True)
            split.label("Sample type: " + str(SAMPLE_TYPE))
            split.label("Sample bits: " + str(SAMPLE_BITS))

            split = col.split(align=True)
            split.label("Unit: " + UNIT)
            split.label("Map resolution: " + str(MAP_RESOLUTION) + " pix/deg")

            split = col.split(align=True)
            split.label("Radius: " + str(OFFSET) + " " + RadiusUM)
            split.label("Scale: " + str(SCALING_FACTOR))

            split = col.split(align=True)
            split.label("Target: ")
            split.label(TARGET_NAME)

            col = layout.column()
            split = col.split(align=True)
            split.prop(context.scene, "FromLat", "Northernmost Lat.")
            split.prop(context.scene, "ToLat", "Southernmost Lat.")
            if bpy.context.scene.FromLat < bpy.context.scene.ToLat:
                col = layout.column()
                split = col.split(align=True)
                split.label("Warning: Northernmost must be greater than Southernmost")

            col = layout.column()
            split = col.split(align=True)
            split.prop(context.scene, "FromLong", "Westernmost Long.")
            split.prop(context.scene, "ToLong", "Easternmost Long.")
            if bpy.context.scene.FromLong > bpy.context.scene.ToLong:
                col = layout.column()
                split = col.split(align=True)
                split.label("Warning: Easternmost must be greater than Westernmost")

            col = layout.column()
            split = col.split(align=True)
            split.prop(context.scene, "Scale", "Scale")
            split.prop(context.scene, "Magnify", "Magnify (x4)")
            if bpy.context.scene.fpath != "":
                col = layout.column()
                split = col.split(align=True)
                split.label("1 Blender unit = " + str(bpy.context.scene.Scale) + RadiusUM)

            if Message != "":
                col = layout.column()
                split = col.split(align=True)
                split.label("Message: " + Message)

            if bpy.context.scene.fpath.upper().endswith(("IMG", "LBL")):  # Check if is selected the correct file
                VertNumbers = (((RealLat(bpy.context.scene.FromLat) - RealLat(bpy.context.scene.ToLat)) * MAP_RESOLUTION) + 1) * ((RealLong(bpy.context.scene.ToLong) - RealLong(bpy.context.scene.FromLong)) * MAP_RESOLUTION + 1)
            else:
                VertNumbers = 0
            #If I have 4 or plus vertex and at least 2 row and at least 2 point, I can import
            if VertNumbers > 3 and (RealLat(bpy.context.scene.FromLat) > RealLat(bpy.context.scene.ToLat)) and (RealLong(bpy.context.scene.FromLong) < RealLong(bpy.context.scene.ToLong)):  # If I have 4 or plus vertex I can import
                split = col.split(align=True)
                split.label("Map resolution on the equator: ")
                split.label(str(2 * math.pi * OFFSET / 360 / MAP_RESOLUTION) + " " + RadiusUM + "/pix")
                col = layout.column()
                split = col.split(align=True)
                split.label("Real Northernmost Lat.: " + str(RealLat(bpy.context.scene.FromLat)) + " deg")
                split.label("Real Southernmost Long.: " + str(RealLat(bpy.context.scene.ToLat)) + " deg")
                split = col.split(align=True)
                split.label("Real Westernmost Long.: " + str(RealLong(bpy.context.scene.FromLong)) + " deg")
                split.label("Real Easternmost Long.: " + str(RealLong(bpy.context.scene.ToLong)) + "deg")
                split = col.split(align=True)
                split.label("Numbers of vertex to be imported: " + str(int(VertNumbers)))
                col.separator()
                col.operator('import.lro_and_mgs', text='Import')
                col.separator()
                col.operator('import.reset', text='Reset')


#Reset the UI
class Reset(bpy.types.Operator):
    bl_idname = 'import.reset'
    bl_label = 'Start Import'

    def execute(self, context):
        clear_properties()
        return {'FINISHED'}


def initialize():
    global MAXIMUM_LATITUDE, MINIMUM_LATITUDE
    global WESTERNMOST_LONGITUDE, EASTERNMOST_LONGITUDE
    global LINES, LINE_SAMPLES, SAMPLE_BITS, MAP_RESOLUTION
    global OFFSET, SCALING_FACTOR
    global SAMPLE_TYPE, UNIT, TARGET_NAME, RadiusUM, Message
    global start_up

    LINES = LINE_SAMPLES = SAMPLE_BITS = MAP_RESOLUTION = 0
    MAXIMUM_LATITUDE = MINIMUM_LATITUDE = 0.0
    WESTERNMOST_LONGITUDE = EASTERNMOST_LONGITUDE = 0.0
    OFFSET = SCALING_FACTOR = 0.0
    SAMPLE_TYPE = UNIT = TARGET_NAME = RadiusUM = Message = ""
    start_up=True

    bpy.types.Scene.fpath = bpy.props.StringProperty(
        name="Import File ",
        description="Select your img file",
        subtype="FILE_PATH",
        default="",
        update=update_fpath)

def clear_properties():
    # can happen on reload
    if bpy.context.scene is None:
        return
    global MAXIMUM_LATITUDE, MINIMUM_LATITUDE
    global WESTERNMOST_LONGITUDE, EASTERNMOST_LONGITUDE
    global LINES, LINE_SAMPLES, SAMPLE_BITS, MAP_RESOLUTION
    global OFFSET, SCALING_FACTOR
    global SAMPLE_TYPE, UNIT, TARGET_NAME, RadiusUM, Message
    global start_up

    LINES = LINE_SAMPLES = SAMPLE_BITS = MAP_RESOLUTION = 0
    MAXIMUM_LATITUDE = MINIMUM_LATITUDE = 0.0
    WESTERNMOST_LONGITUDE = EASTERNMOST_LONGITUDE = 0.0
    OFFSET = SCALING_FACTOR = 0.0
    SAMPLE_TYPE = UNIT = TARGET_NAME = RadiusUM = Message = ""
    start_up=True

    props = ["FromLat", "ToLat", "FromLong", "ToLong", "Scale", "Magnify", "fpath"]
    for p in props:
        if p in bpy.types.Scene.bl_rna.properties:
            exec("del bpy.types.Scene." + p)
        if p in bpy.context.scene:
            del bpy.context.scene[p]
    bpy.types.Scene.fpath = bpy.props.StringProperty(
        name="Import File ",
        description="Select your img file",
        subtype="FILE_PATH",
        default="",
        update=update_fpath)


# registering the script
def register():
    initialize()
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)
    clear_properties()


if __name__ == "__main__":
    register()
