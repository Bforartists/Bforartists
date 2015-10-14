# ***** GPL LICENSE BLOCK *****
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# All rights reserved.
# ***** GPL LICENSE BLOCK *****

# Marmalade SDK is not responsible in any case of the following code.
# This Blender add-on is freely shared for the Blender and Marmalade user communities.


bl_info = {
    "name": "Marmalade Cross-platform Apps (.group)",
    "author": "Benoit Muller",
    "version": (0, 6, 2),
    "blender": (2, 63, 0),
    "location": "File > Export > Marmalade cross-platform Apps (.group)",
    "description": "Export Marmalade Format files (.group)",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
        "Scripts/Import-Export/Marmalade_Exporter",
    "tracker_url": "https://developer.blender.org",
    "category": "Import-Export"}

import os
import shutil
from math import radians

import bpy
from mathutils import Matrix

import mathutils
import math

import datetime

import subprocess


#Container for the exporter settings
class MarmaladeExporterSettings:

    def __init__(self,
                 context,
                 FilePath,
                 CoordinateSystem=1,
                 FlipNormals=False,
                 ApplyModifiers=False,
                 Scale=100,
                 AnimFPS=30,
                 ExportVertexColors=True,
                 ExportMaterialColors=True,
                 ExportTextures=True,
                 CopyTextureFiles=True,
                 ExportArmatures=False,
                 ExportAnimationFrames=0,
                 ExportAnimationActions=0,
                 ExportMode=1,
                 MergeModes=0,
                 Verbose=False):
        self.context = context
        self.FilePath = FilePath
        self.CoordinateSystem = int(CoordinateSystem)
        self.FlipNormals = FlipNormals
        self.ApplyModifiers = ApplyModifiers
        self.Scale = Scale
        self.AnimFPS = AnimFPS
        self.ExportVertexColors = ExportVertexColors
        self.ExportMaterialColors = ExportMaterialColors
        self.ExportTextures = ExportTextures
        self.CopyTextureFiles = CopyTextureFiles
        self.ExportArmatures = ExportArmatures
        self.ExportAnimationFrames = int(ExportAnimationFrames)
        self.ExportAnimationActions = int(ExportAnimationActions)
        self.ExportMode = int(ExportMode)
        self.MergeModes = int(MergeModes)
        self.Verbose = Verbose
        self.WarningList = []


def ExportMadeWithMarmaladeGroup(Config):
    print("----------\nExporting to {}".format(Config.FilePath))
    if Config.Verbose:
        print("Opening File...")
    Config.File = open(Config.FilePath, "w")

    if Config.Verbose:
        print("Done")

    if Config.Verbose:
        print("writing group header")

    Config.File.write('// Marmalade group file exported from : %s\n' % bpy.data.filepath)
    Config.File.write('// Exported %s\n' % str(datetime.datetime.now()))
    Config.File.write("CIwResGroup\n{\n\tname \"%s\"\n" % bpy.path.display_name_from_filepath(Config.FilePath))

    if Config.Verbose:
        print("Generating Object list for export... (Root parents only)")
    if Config.ExportMode == 1:
        Config.ExportList = [Object for Object in Config.context.scene.objects
                             if Object.type in {'ARMATURE', 'EMPTY', 'MESH'}
                             and Object.parent is None]
    else:
        ExportList = [Object for Object in Config.context.selected_objects
                      if Object.type in {'ARMATURE', 'EMPTY', 'MESH'}]
        Config.ExportList = [Object for Object in ExportList
                             if Object.parent not in ExportList]
    if Config.Verbose:
        print("  List: {}\nDone".format(Config.ExportList))

    if Config.Verbose:
        print("Setting up...")

    if Config.ExportAnimationFrames:
        if Config.Verbose:
            print(bpy.context.scene)
            print(bpy.context.scene.frame_current)
        CurrentFrame = bpy.context.scene.frame_current
    if Config.Verbose:
        print("Done")

    Config.ObjectList = []
    if Config.Verbose:
        print("Writing Objects...")
    WriteObjects(Config, Config.ExportList)
    if Config.Verbose:
        print("Done")

    if Config.Verbose:
        print("Objects Exported: {}".format(Config.ExportList))

    if Config.ExportAnimationFrames:
        if Config.Verbose:
            print("Writing Animation...")
        WriteKeyedAnimationSet(Config, bpy.context.scene)
        bpy.context.scene.frame_current = CurrentFrame
        if Config.Verbose:
            print("Done")
    Config.File.write("}\n")
    CloseFile(Config)
    print("Finished")


def GetObjectChildren(Parent):
    return [Object for Object in Parent.children
            if Object.type in {'ARMATURE', 'EMPTY', 'MESH'}]


#Returns the file path of first image texture from Material.
def GetMaterialTextureFullPath(Config, Material):
    if Material:
        #Create a list of Textures that have type "IMAGE"
        ImageTextures = [Material.texture_slots[TextureSlot].texture for TextureSlot in Material.texture_slots.keys() if Material.texture_slots[TextureSlot].texture.type == "IMAGE"]
        #Refine a new list with only image textures that have a file source
        TexImages = [Texture.image for Texture in ImageTextures if getattr(Texture.image, "source", "") == "FILE"]
        ImageFiles = [Texture.image.filepath for Texture in ImageTextures if getattr(Texture.image, "source", "") == "FILE"]
        if TexImages:
            filepath = TexImages[0].filepath
            if TexImages[0].packed_file:
                TexImages[0].unpack()
            if not os.path.exists(filepath):
                #try relative path to the blend file
                filepath = os.path.dirname(bpy.data.filepath) + filepath
            #Marmalade doesn't like jpeg/tif so try to convert in png on the fly
            if (TexImages[0].file_format == 'JPEG' or TexImages[0].file_format == 'TIFF') and os.path.exists(filepath):
                marmaladeConvert = os.path.expandvars("%S3E_DIR%\\..\\tools\\ImageMagick\\win32\\convert.exe")
                if (os.path.exists(marmaladeConvert)):
                    srcImagefilepath = filepath
                    filepath = os.path.splitext(filepath)[0] + '.png'
                    if Config.Verbose:
                        print("  /!\\ Converting Texture %s in PNG: %s{}..." % (TexImages[0].file_format, filepath))
                        print('"%s" "%s" "%s"' % (marmaladeConvert, srcImagefilepath, filepath))
                    subprocess.call([marmaladeConvert, srcImagefilepath, filepath])
            return filepath
    return None


def WriteObjects(Config, ObjectList, geoFile=None, mtlFile=None, GeoModel=None,  bChildObjects=False):
    Config.ObjectList += ObjectList

    if bChildObjects == False and Config.MergeModes > 0:
        if geoFile == None:
            #we merge objects, so use name of group file for the name of Geo
            geoFile, mtlFile = CreateGeoMtlFiles(Config, bpy.path.display_name_from_filepath(Config.FilePath))
            GeoModel = CGeoModel(bpy.path.display_name_from_filepath(Config.FilePath))

    for Object in ObjectList:
        if Config.Verbose:
            print("  Writing Object: {}...".format(Object.name))

        if Config.ExportArmatures and Object.type == "ARMATURE":
            Armature = Object.data
            ParentList = [Bone for Bone in Armature.bones if Bone.parent is None]
            if Config.Verbose:
                print("    Writing Armature Bones...")
            #Create the skel file
            skelfullname = os.path.dirname(Config.FilePath) + os.sep + "models" + os.sep + "%s.skel" % (StripName(Object.name))
            ensure_dir(skelfullname)
            if Config.Verbose:
                print("      Creating skel file %s" % (skelfullname))

            skelFile = open(skelfullname, "w")
            skelFile.write('// skel file exported from : %r\n' % os.path.basename(bpy.data.filepath))
            skelFile.write("CIwAnimSkel\n")
            skelFile.write("{\n")
            skelFile.write("\tnumBones %d\n" % (len(Armature.bones)))
            Config.File.write("\t\".\models\%s.skel\"\n" % (StripName(Object.name)))

            WriteArmatureParentRootBones(Config, Object, ParentList, skelFile)

            skelFile.write("}\n")
            skelFile.close()
            if Config.Verbose:
                print("    Done")

        ChildList = GetObjectChildren(Object)
        if Config.ExportMode == 2:  # Selected Objects Only
            ChildList = [Child for Child in ChildList
                         if Child in Config.context.selected_objects]
        if Config.Verbose:
            print("    Writing Children...")
        WriteObjects(Config, ChildList, geoFile, mtlFile, GeoModel, True)
        if Config.Verbose:
            print("    Done Writing Children")

        if Object.type == "MESH":
            if Config.Verbose:
                print("    Generating Mesh...")
            if Config.ApplyModifiers:
                if Config.ExportArmatures:
                    #Create a copy of the object and remove all armature modifiers so an unshaped
                    #mesh can be created from it.
                    Object2 = Object.copy()
                    for Modifier in [Modifier for Modifier in Object2.modifiers if Modifier.type == "ARMATURE"]:
                        Object2.modifiers.remove(Modifier)
                    Mesh = Object2.to_mesh(bpy.context.scene, True, "PREVIEW")
                else:
                    Mesh = Object.to_mesh(bpy.context.scene, True, "PREVIEW")
            else:
                Mesh = Object.to_mesh(bpy.context.scene, False, "PREVIEW")
            if Config.Verbose:
                print("    Done")
                print("    Writing Mesh...")

            # Flip ZY axis (Blender Z up: Marmalade: Y up) ans Scale appropriately
            X_ROT = mathutils.Matrix.Rotation(-math.pi / 2, 4, 'X')

            if Config.MergeModes == 0:
                # No merge, so all objects are exported in MODEL SPACE and not in world space
                # Calculate Scale of the Export
                meshScale = Object.matrix_world.to_scale()  # Export is working, even if user doesn't have use apply scale in Edit mode.

                scalematrix = Matrix()
                scalematrix[0][0] = meshScale.x * Config.Scale
                scalematrix[1][1] = meshScale.y * Config.Scale
                scalematrix[2][2] = meshScale.z * Config.Scale

                meshRot = Object.matrix_world.to_quaternion()  # Export is working, even if user doesn't have use apply Rotation in Edit mode.
                Mesh.transform(X_ROT * meshRot.to_matrix().to_4x4() * scalematrix)
            else:
                # In Merge mode, we need to keep relative postion of each objects, so we export in WORLD SPACE
                SCALE_MAT = mathutils.Matrix.Scale(Config.Scale, 4)
                Mesh.transform(SCALE_MAT * X_ROT * Object.matrix_world)

             # manage merge options

            if Config.MergeModes == 0:
                #one geo per Object, so use name of Object for the Geo file
                geoFile, mtlFile = CreateGeoMtlFiles(Config, StripName(Object.name))
                GeoModel = CGeoModel(StripName(Object.name))

            # Write the Mesh in the Geo file
            WriteMesh(Config, Object, Mesh, geoFile, mtlFile, GeoModel)

            if Config.MergeModes == 0:
                # no merge so finalize the file, and discard the file and geo class
                FinalizeGeoMtlFiles(Config, geoFile, mtlFile)
                geoFile = None
                mtlFile = None
                GeoModel = None
            elif Config.MergeModes == 1:
                # merge in one Mesh, so keep the Geo class and prepare to change object
                GeoModel.NewObject()
            elif Config.MergeModes == 2:
                # merge several Meshes in one file: so clear the mesh data that we just written in the file,
                # but keep Materials info that need to be merged across objects
                GeoModel.ClearAllExceptMaterials()

            if Config.Verbose:
                print("    Done")

            if Config.ApplyModifiers and Config.ExportArmatures:
                bpy.data.objects.remove(Object2)
            bpy.data.meshes.remove(Mesh)

        if Config.Verbose:
            print("  Done Writing Object: {}".format(Object.name))

    if bChildObjects == False:
        # we have finish to do all objects
        if GeoModel:
            if Config.MergeModes == 1:
                # we have Merges all objects in one Mesh, so time to write this big mesh in the file
                GeoModel.PrintGeoMesh(geoFile)
                # time to write skinfile if any
                if len(GeoModel.useBonesDict) > 0:
                    # some mesh was not modified by the armature. so we must skinned the merged mesh.
                    # So unskinned vertices from unarmatured meshes, are assigned to the root bone of the armature
                    for i in range(0, len(GeoModel.vList)):
                        if not i in GeoModel.skinnedVertices:
                            GeoModel.skinnedVertices.append(i)
                            useBonesKey = pow(2, GeoModel.armatureRootBoneIndex)
                            vertexGroupIndices = list((GeoModel.armatureRootBoneIndex,))
                            if useBonesKey not in GeoModel.useBonesDict:
                                GeoModel.mapVertexGroupNames[GeoModel.armatureRootBoneIndex] = StripBoneName(GeoModel.armatureRootBone.name)
                                VertexList = []
                                VertexList.append("\t\tvertWeights { %d, 1.0}" % i)
                                GeoModel.useBonesDict[useBonesKey] = (vertexGroupIndices, VertexList)
                            else:
                                pair_ListGroupIndices_ListAssignedVertices = GeoModel.useBonesDict[useBonesKey]
                                pair_ListGroupIndices_ListAssignedVertices[1].append("\t\tvertWeights { %d, 1.0}" % i)
                                GeoModel.useBonesDict[useBonesKey] = pair_ListGroupIndices_ListAssignedVertices
                    # now generates the skin file
                    PrintSkinWeights(Config, GeoModel.armatureObjectName, GeoModel.useBonesDict, GeoModel.mapVertexGroupNames, GeoModel.name)
            if Config.MergeModes > 0:
                WriteMeshMaterialsForGeoModel(Config, mtlFile, GeoModel)
                FinalizeGeoMtlFiles(Config, geoFile, mtlFile)
        geoFile = None
        mtlFile = None
        GeoModel = None


def CreateGeoMtlFiles(Config, Name):
    #Create the geo file
    geofullname = os.path.dirname(Config.FilePath) + os.sep + "models" + os.sep + "%s.geo" % Name
    ensure_dir(geofullname)
    if Config.Verbose:
        print("      Creating geo file %s" % (geofullname))
    geoFile = open(geofullname, "w")
    geoFile.write('// geo file exported from : %r\n' % os.path.basename(bpy.data.filepath))
    geoFile.write("CIwModel\n")
    geoFile.write("{\n")
    geoFile.write("\tname \"%s\"\n" % Name)
    # add it to the group
    Config.File.write("\t\".\models\%s.geo\"\n" % Name)

    # Create the mtl file
    mtlfullname = os.path.dirname(Config.FilePath) + os.sep + "models" + os.sep + "%s.mtl" % Name
    ensure_dir(mtlfullname)
    if Config.Verbose:
        print("      Creating mtl file %s" % (mtlfullname))
    mtlFile = open(mtlfullname, "w")
    mtlFile.write('// mtl file exported from : %r\n' % os.path.basename(bpy.data.filepath))
    return geoFile, mtlFile


def FinalizeGeoMtlFiles(Config, geoFile, mtlFile):
    if Config.Verbose:
        print("      Closing geo file")
    geoFile.write("}\n")
    geoFile.close()
    if Config.Verbose:
        print("      Closing mtl file")
    mtlFile.close()


def WriteMesh(Config, Object, Mesh,  geoFile=None, mtlFile=None, GeoModel=None):
    if geoFile == None or mtlFile == None:
        print (" ERROR not geo file arguments in WriteMesh method")
        return

    if GeoModel == None:
        print (" ERROR not GeoModel arguments in WriteMesh method")
        return

    BuildOptimizedGeo(Config, Object, Mesh, GeoModel)
    if Config.MergeModes == 0 or Config.MergeModes == 2:
        #if we don't merge, or if we write several meshes into one file ... write the mesh everytime we do an object
        GeoModel.PrintGeoMesh(geoFile)

    if Config.Verbose:
        print("      Done\n      Writing Mesh Materials...")

    if Config.MergeModes == 0:
        #No merge, so we can diretly write the Mtl file associated to this object
        WriteMeshMaterialsForGeoModel(Config, mtlFile, GeoModel)

    if Config.Verbose:
        print("      Done")

    if Config.ExportArmatures:
        if Config.Verbose:
            print("      Writing Mesh Weights...")
        WriteMeshSkinWeightsForGeoModel(Config, Object, Mesh, GeoModel)
        if Config.Verbose:
            print("      Done")


###### optimized version fo Export, can be used also to merge several object in one single geo File ######

# CGeoModel
#  -> List Vertices
#  -> List Normales
#  -> List uv 0
#  -> List uv 1
#  -> List Vertex Colors
#  -> List Materials
#       -> Material name
#       -> Blender Material Object
#       -> List Tris -> Stream Indices v,vn,uv0,uv1,vc
#       -> List Quads -> Stream Indices v,vn,uv0,uv1,vc


#############
#Store one Point of a Quad or Tri in marmalade geo format: //index-list is: { <int> <int> <int> <int> <int> }   //v,vn,uv0,uv1,vc
#############
class CGeoIndexList:
    __slots__ = "v", "vn", "uv0", "uv1", "vc"

    def __init__(self, v, vn, uv0, uv1, vc):
        self.v = v
        self.vn = vn
        self.uv0 = uv0
        self.uv1 = uv1
        self.vc = vc


#############
#Store a Quad or a Tri in marmalade geo format : 3 or 4 CIndexList depending it is a Tri or a Quad
#############
class CGeoPoly:
    __slots__ = "pointsList",

    def __init__(self):
        self.pointsList = []

    def AddPoint(self, v, vn, uv0, uv1, vc):
        self.pointsList.append( CGeoIndexList(v, vn, uv0, uv1, vc))

    def PointsCount(self):
        return len(self.pointsList)

    def PrintPoly(self, geoFile):
        if len(self.pointsList) == 3:
            geoFile.write("\t\t\t\tt ")
        if len(self.pointsList) == 4:
            geoFile.write("\t\t\t\tq ")
        for point in self.pointsList:
            geoFile.write(" {%d, %d, %d, %d, %d}" % (point.v, point.vn, point.uv0, point.uv1, point.vc))
        geoFile.write("\n")


#############
#Store all the poly (tri or quad) assigned to a Material in marmalade geo format
#############
class CGeoMaterialPolys:
    __slots__ = "name", "material", "quadList", "triList", "currentPoly"

    def __init__(self, name, material=None):
        self.name = name
        self.material = material
        self.quadList = []
        self.triList = []
        self.currentPoly = None

    def BeginPoly(self):
        self.currentPoly = CGeoPoly()

    def AddPoint(self, v, vn, uv0, uv1, vc):
        self.currentPoly.AddPoint(v, vn, uv0, uv1, vc)

    def EndPoly(self):
        if (self.currentPoly.PointsCount() == 3):
            self.triList.append(self.currentPoly)
        if (self.currentPoly.PointsCount() == 4):
            self.quadList.append(self.currentPoly)
        self.currentPoly = None

    def ClearPolys(self):
        self.quadList = []
        self.triList = []
        self.currentPoly = None

    def PrintMaterialPolys(self, geoFile):
        geoFile.write("\t\tCSurface\n")
        geoFile.write("\t\t{\n")
        geoFile.write("\t\t\tmaterial \"%s\"\n" % self.name)
        if self.triList:
            geoFile.write("\t\t\tCTris\n")
            geoFile.write("\t\t\t{\n")
            geoFile.write("\t\t\t\tnumTris %d\n" % (len(self.triList)))
            for poly in self.triList:
                poly.PrintPoly(geoFile)
            geoFile.write("\t\t\t}\n")

        if self.quadList:
            geoFile.write("\t\t\tCQuads\n")
            geoFile.write("\t\t\t{\n")
            geoFile.write("\t\t\t\tnumQuads %d\n" % (len(self.quadList)))
            for poly in self.quadList:
                poly.PrintPoly(geoFile)
            geoFile.write("\t\t\t}\n")
        geoFile.write("\t\t}\n")


#############
#Store all the information on a Model/Mesh (vertices, normal, certcies color, uv0, uv1, TRI, QUAD) in marmalade geo format
#############
class CGeoModel:
    __slots__ = ("name", "MaterialsDict", "vList", "vnList", "vcList", "uv0List", "uv1List",
                "currentMaterialPolys", "vbaseIndex","vnbaseIndex", "uv0baseIndex", "uv1baseIndex",
                "armatureObjectName", "useBonesDict", "mapVertexGroupNames", "armatureRootBone", "armatureRootBoneIndex", "skinnedVertices")

    def __init__(self, name):
        self.name = name
        self.MaterialsDict = {}
        self.vList = []
        self.vnList = []
        self.vcList = []
        self.uv0List = []
        self.uv1List = []
        self.currentMaterialPolys = None
        #used xx baseIndex are used when merging several blender objects into one Mesh in the geo file (internal offset)
        self.vbaseIndex = 0
        self.vnbaseIndex = 0
        self.uv0baseIndex = 0
        self.uv1baseIndex = 0

        # Store some information for skin management , when we merge several object in one big mesh (MergeModes 1)
        # can only work if in the object list only one is rigged with an armature... and if it is located in 0,0,0
        self.armatureObjectName = ""
        #useBonesKey : bit field, where each bit is a VertexGroup.Index): Sum(2^VertGroupIndex).
        #useBonesDict[useBonesKey] = tuple(VertexGroups.group, list(Vertex))
        self.useBonesDict = {}
        self.mapVertexGroupNames = {}
        self.armatureRootBone = None
        self.armatureRootBoneIndex = 0
        self.skinnedVertices = []



    def AddVertex(self, vertex):
        self.vList.append(vertex.copy())

    def AddVertexNormal(self, vertexN):
        self.vnList.append(vertexN.copy())

    # add a uv coordiantes and return the current Index in the stream (index is local to the object, when we merge several object into a one Mesh)
    def AddVertexUV0(self, u, v):
        self.uv0List.append((u, v))
        return len(self.uv0List) - 1 - self.uv0baseIndex

    def AddVertexUV1(self, u, v):
        self.uv1List.append((u, v))
        return len(self.uv1List) - 1 - self.uv1baseIndex

    # add a vertexcolor if it doesn't already exist and return the current Index in the stream (index is global to all objects, when we merge several object into a one Mesh)
    def AddVertexColor(self, r, g, b, a):
        for i in range(0, len(self.vcList)):
            col = self.vcList[i]
            if col[0] == r and col[1] == g and col[2] == b and col[3] == a:
                return i

        self.vcList.append((r, g, b, a))
        return len(self.vcList)-1

    def BeginPoly(self, MaterialName, material=None):
        if MaterialName not in self.MaterialsDict:
            self.currentMaterialPolys = CGeoMaterialPolys(MaterialName, material)
        else:
            self.currentMaterialPolys = self.MaterialsDict[MaterialName]
        self.currentMaterialPolys.BeginPoly()

    def AddPoint(self, v, vn, uv0, uv1, vc):
        if v != -1:
            v += self.vbaseIndex
        if vn != -1:
            vn += self.vnbaseIndex
        if uv0 != -1:
            uv0 += self.uv0baseIndex
        if uv1 != -1:
            uv1 += self.uv1baseIndex

        self.currentMaterialPolys.AddPoint(v, vn, uv0, uv1, vc)

    def EndPoly(self):
        self.currentMaterialPolys.EndPoly()
        self.MaterialsDict[self.currentMaterialPolys.name] = self.currentMaterialPolys
        self.currentMaterialPolys = None

    def NewObject(self):
        #used in Merge mode 1: allows to merge several blender objects into one Mesh.
        self.vbaseIndex = len(self.vList)
        self.vnbaseIndex = len(self.vnList)
        self.uv0baseIndex = len(self.uv0List)
        self.uv1baseIndex = len(self.uv1List)

    def ClearAllExceptMaterials(self):
        #used in Merge mode 2: one geo with several mesh
        self.vList = []
        self.vnList = []
        self.vcList = []
        self.uv0List = []
        self.uv1List = []
        self.currentMaterialPolys = None
        self.vbaseIndex = 0
        self.vnbaseIndex = 0
        self.uv0baseIndex = 0
        self.uv1baseIndex = 0
        for GeoMaterialPolys in self.MaterialsDict.values():
            GeoMaterialPolys.ClearPolys()
        self.useBonesDict = {}
        self.mapVertexGroupNames = {}
        self.armatureObjectName = ""
        self.armatureRootBone = None
        self.armatureRootBoneIndex = 0
        self.skinnedVertices = []

    def PrintGeoMesh(self, geoFile):
        geoFile.write("\tCMesh\n")
        geoFile.write("\t{\n")
        geoFile.write("\t\tname \"%s\"\n" % (StripName(self.name)))

        if self.vList:
            geoFile.write("\t\tCVerts\n")
            geoFile.write("\t\t{\n")
            geoFile.write("\t\t\tnumVerts %d\n" % len(self.vList))
            for vertex in self.vList:
                geoFile.write("\t\t\tv { %.9f, %.9f, %.9f }\n" % (vertex[0], vertex[1], vertex[2]))
            geoFile.write("\t\t}\n")

        if self.vnList:
            geoFile.write("\t\tCVertNorms\n")
            geoFile.write("\t\t{\n")
            geoFile.write("\t\t\tnumVertNorms  %d\n" % len(self.vnList))
            for vertexn in self.vnList:
                geoFile.write("\t\t\tvn { %.9f, %.9f, %.9f }\n" % (vertexn[0], vertexn[1], vertexn[2]))
            geoFile.write("\t\t}\n")

        if self.vcList:
            geoFile.write("\t\tCVertCols\n")
            geoFile.write("\t\t{\n")
            geoFile.write("\t\t\tnumVertCols %d\n" % len(self.vcList))
            for color in self.vcList:
                geoFile.write("\t\t\tcol { %.6f, %.6f, %.6f, %.6f }\n" % (color[0], color[1], color[2], color[3])) #alpha is not supported on blender for vertex colors
            geoFile.write("\t\t}\n")

        if self.uv0List:
            geoFile.write("\t\tCUVs\n")
            geoFile.write("\t\t{\n")
            geoFile.write("\t\t\tsetID 0\n")
            geoFile.write("\t\t\tnumUVs %d\n" % len(self.uv0List))
            for uv in self.uv0List:
                 geoFile.write("\t\t\tuv { %.9f, %.9f }\n" % (uv[0], uv[1]))
            geoFile.write("\t\t}\n")

        if self.uv1List:
            geoFile.write("\t\tCUVs\n")
            geoFile.write("\t\t{\n")
            geoFile.write("\t\t\tsetID 1\n")
            geoFile.write("\t\t\tnumUVs %d\n" % len(self.uv1List))
            for uv in self.uv1List:
                 geoFile.write("\t\t\tuv { %.9f, %.9f }\n" % (uv[0], uv[1]))
            geoFile.write("\t\t}\n")

        for GeoMaterialPolys in self.MaterialsDict.values():
            GeoMaterialPolys.PrintMaterialPolys(geoFile)
        geoFile.write("\t}\n")

    def GetMaterialList(self):
        return list(self.MaterialsDict.keys())

    def GetMaterialByName(self, name):
        if name in self.MaterialsDict:
            return self.MaterialsDict[name].material
        else:
            return None



#############
# iterates faces, vertices ... and store the information in the GeoModel container
def BuildOptimizedGeo(Config, Object, Mesh, GeoModel):
    if GeoModel == None:
        GeoModel = CGeoModel(filename, Object.name)

    #Ensure tessfaces data are here
    Mesh.update (calc_tessface=True)

    #Store Vertex stream, and Normal stream (use directly the order from blender collection
    for Vertex in Mesh.vertices:
        GeoModel.AddVertex(Vertex.co)
        Normal = Vertex.normal
        if Config.FlipNormals:
            Normal = -Normal
        GeoModel.AddVertexNormal(Normal)
    #Check if some colors have been defined
    vertexColors = None
    if Config.ExportVertexColors and (len(Mesh.vertex_colors) > 0):
        vertexColors = Mesh.tessface_vertex_colors[0].data

    #Check if some uv coordinates have been defined
    UVCoordinates = None
    if Config.ExportTextures and (len(Mesh.uv_textures) > 0):
        for UV in Mesh.tessface_uv_textures:
            if UV.active_render:
                UVCoordinates = UV.data
                break

    #Iterate on Faces and Store the poly (quad or tri) and the associate colors,UVs
    for Face in Mesh.tessfaces:
        # stream for vertex (we use the same for normal)
        Vertices = list(Face.vertices)
        if Config.CoordinateSystem == 1:
            Vertices = Vertices[::-1]
        # stream for vertex colors
        if vertexColors:
            MeshColor = vertexColors[Face.index]
            if len(Vertices) == 3:
                FaceColors = list((MeshColor.color1, MeshColor.color2, MeshColor.color3))
            else:
                FaceColors = list((MeshColor.color1, MeshColor.color2, MeshColor.color3, MeshColor.color4))
            if Config.CoordinateSystem == 1:
                FaceColors = FaceColors[::-1]
            colorIndex = []
            for color in FaceColors:
                index = GeoModel.AddVertexColor(color[0], color[1], color[2], 1)  #rgba => no alpha on vertex color in Blender so use 1
                colorIndex.append(index)
        else:
            colorIndex = list((-1,-1,-1,-1))

        # stream for UV0 coordinates
        if UVCoordinates:
            uvFace = UVCoordinates[Face.index]
            uvVertices = []
            for uvVertex in uvFace.uv:
                uvVertices.append(tuple(uvVertex))
            if Config.CoordinateSystem == 1:
                uvVertices = uvVertices[::-1]
            uv0Index = []
            for uvVertex in uvVertices:
                index = GeoModel.AddVertexUV0(uvVertex[0], 1 - uvVertex[1])
                uv0Index.append(index)
        else:
            uv0Index = list((-1, -1, -1, -1))

        # stream for UV1 coordinates
        uv1Index = list((-1, -1, -1, -1))

        mat = None
        # find the associated material
        if Face.material_index < len(Mesh.materials):
            mat = Mesh.materials[Face.material_index]
        if mat:
            matName =  mat.name
        else:
            matName = "NoMaterialAssigned"  # There is no material assigned in blender !!!, exporter have generated a default one

        # now on the material, generates the tri/quad in v,vn,uv0,uv1,vc stream index
        GeoModel.BeginPoly(matName, mat)

        for i in range(0, len(Vertices)):
            GeoModel.AddPoint(Vertices[i], Vertices[i], uv0Index[i], uv1Index[i], colorIndex[i])

        GeoModel.EndPoly()



#############
# Get the list of Material in use by the CGeoModel
def WriteMeshMaterialsForGeoModel(Config, mtlFile, GeoModel):
    for matName in GeoModel.GetMaterialList():
        Material = GeoModel.GetMaterialByName(matName)
        WriteMaterial(Config, mtlFile, Material)


def WriteMaterial(Config, mtlFile, Material=None):
    mtlFile.write("CIwMaterial\n")
    mtlFile.write("{\n")
    if Material:
        mtlFile.write("\tname \"%s\"\n" % Material.name)

        if Config.ExportMaterialColors:
            #if bpy.context.scene.world:
            #    MatAmbientColor = Material.ambient * bpy.context.scene.world.ambient_color
            MatAmbientColor = Material.ambient * Material.diffuse_color
            mtlFile.write("\tcolAmbient {%.2f,%.2f,%.2f,%.2f} \n" % (min(255, MatAmbientColor[0] * 255), min(255, MatAmbientColor[1] * 255), min(255, MatAmbientColor[2] * 255), min(255, Material.alpha * 255)))
            MatDiffuseColor = 255 * Material.diffuse_intensity * Material.diffuse_color
            MatDiffuseColor = min((255, 255, 255)[:],MatDiffuseColor[:])
            mtlFile.write("\tcolDiffuse  {%.2f,%.2f,%.2f} \n" % (MatDiffuseColor[:]))
            MatSpecularColor = 255 * Material.specular_intensity * Material.specular_color
            MatSpecularColor = min((255, 255, 255)[:],MatSpecularColor[:])
            mtlFile.write("\tcolSpecular  {%.2f,%.2f,%.2f} \n" % (MatSpecularColor[:]))
            # EmitColor = Material.emit * Material.diffuse_color
            # mtlFile.write("\tcolEmissive {%.2f,%.2f,%.2f} \n" % (EmitColor* 255)[:])
    else:
        mtlFile.write("\tname \"NoMaterialAssigned\" // There is no material assigned in blender !!!, exporter have generated a default one\n")

    #Copy texture
    if Config.ExportTextures:
        Texture = GetMaterialTextureFullPath(Config, Material)
        if Texture:
            mtlFile.write("\ttexture0 .\\textures\\%s\n" % (bpy.path.basename(Texture)))

            if Config.CopyTextureFiles:
                if not os.path.exists(Texture):
                    #try relative path to the blend file
                    Texture = os.path.dirname(bpy.data.filepath) + Texture
                if os.path.exists(Texture):
                    textureDest = os.path.dirname(Config.FilePath) + os.sep + "models" + os.sep + "textures" + os.sep + ("%s" % bpy.path.basename(Texture))
                    ensure_dir(textureDest)
                    if Config.Verbose:
                        print("      Copying the texture file %s ---> %s" % (Texture, textureDest))
                    shutil.copy(Texture, textureDest)
                else:
                    if Config.Verbose:
                        print("      CANNOT Copy texture file (not found) %s" % (Texture))
    mtlFile.write("}\n")

def GetFirstRootBone(ArmatureObject):
    ArmatureBones = ArmatureObject.data.bones
    ParentBoneList = [Bone for Bone in ArmatureBones if Bone.parent is None]
    if ParentBoneList:
        return ParentBoneList[0]
    return None


def GetVertexGroupFromBone(Object, Bone):
    if Bone:
        vertexGroupList = [VertexGroup for VertexGroup in Object.vertex_groups  if VertexGroup.name == Bone.name]
        if vertexGroupList:
            return vertexGroupList[0]
    return None


def GetBoneListNames(Bones):
    boneList = []
    for Bone in Bones:
        boneList.append(Bone.name)
        boneList += GetBoneListNames(Bone.children)
    return boneList


def FindUniqueIndexForRootBone(Object, RootVertexGroup):
    if RootVertexGroup:
        return RootVertexGroup.index
    else:
        #If there is not VertexGroup associated to the root bone name, we don't have a vertex index.
        #so use the next available free index
        return len(Object.vertex_groups)


def WriteMeshSkinWeightsForGeoModel(Config, Object, Mesh, GeoModel):
    ArmatureList = [Modifier for Modifier in Object.modifiers if Modifier.type == "ARMATURE"]
    if ArmatureList:
        ArmatureObject = ArmatureList[0].object
        if ArmatureObject is None:
            return
        RootBone = GetFirstRootBone(ArmatureObject)
        RootVertexGroup = GetVertexGroupFromBone(Object, RootBone)
        BoneNames = GetBoneListNames(ArmatureObject.data.bones)

        GeoModel.armatureObjectName = StripName(ArmatureObject.name)
        if RootBone:
            GeoModel.armatureRootBone = RootBone
            GeoModel.armatureRootBoneIndex = FindUniqueIndexForRootBone(Object, RootVertexGroup)

        # Marmalade need to declare a vertex per list of affected bones
        # so first we have to get all the combinations of affected bones that exist in the mesh
        # to build thoses groups, we build a unique key (like a bit field, where each bit is a VertexGroup.Index): Sum(2^VertGroupIndex)... so we have a unique Number per combinations

        for Vertex in Mesh.vertices:
            VertexIndex = Vertex.index + GeoModel.vbaseIndex
            AddVertexToDicionarySkinWeights(Config, Object, Mesh, Vertex, GeoModel.useBonesDict, GeoModel.mapVertexGroupNames, VertexIndex, RootBone, RootVertexGroup, BoneNames)
            GeoModel.skinnedVertices.append(VertexIndex)

        if Config.MergeModes != 1:
            # write skin file directly
            PrintSkinWeights(Config, GeoModel.armatureObjectName, GeoModel.useBonesDict, GeoModel.mapVertexGroupNames, StripName(Object.name))


def PrintSkinWeights(Config, ArmatureObjectName, useBonesDict, mapVertexGroupNames, GeoName):
        #Create the skin file
        skinfullname = os.path.dirname(Config.FilePath) + os.sep + "models" + os.sep + "%s.skin" % GeoName
        ensure_dir(skinfullname)
        if Config.Verbose:
            print("      Creating skin file %s" % (skinfullname))
        skinFile = open(skinfullname, "w")
        skinFile.write('// skin file exported from : %r\n' % os.path.basename(bpy.data.filepath))
        skinFile.write("CIwAnimSkin\n")
        skinFile.write("{\n")
        skinFile.write("\tskeleton \"%s\"\n" % ArmatureObjectName)
        skinFile.write("\tmodel \"%s\"\n" % GeoName)

        # now we have Bones grouped in the dictionary , along with the associated influenced vertex weighting
        # So simply iterate the dictionary
        Config.File.write("\t\".\models\%s.skin\"\n" % GeoName)
        for pair_ListGroupIndices_ListAssignedVertices in useBonesDict.values():
            skinFile.write("\tCIwAnimSkinSet\n")
            skinFile.write("\t{\n")
            skinFile.write("\t\tuseBones {")
            for vertexGroupIndex in pair_ListGroupIndices_ListAssignedVertices[0]:
                skinFile.write(" %s" % mapVertexGroupNames[vertexGroupIndex])
            skinFile.write(" }\n")
            skinFile.write("\t\tnumVerts %d\n" % len(pair_ListGroupIndices_ListAssignedVertices[1]))
            for VertexWeightString in pair_ListGroupIndices_ListAssignedVertices[1]:
                skinFile.write(VertexWeightString)
            skinFile.write("\t}\n")

        skinFile.write("}\n")
        skinFile.close()


def AddVertexToDicionarySkinWeights(Config, Object, Mesh, Vertex, useBonesDict, mapVertexGroupNames, VertexIndex, RootBone, RootVertexGroup, BoneNames):
    #build useBones
    useBonesKey = 0
    vertexGroupIndices = []
    weightTotal = 0.0
    if (len(Vertex.groups)) > 4:
        print ("ERROR Vertex %d is influenced by more than 4 bones\n" % (VertexIndex))
    for VertexGroup in Vertex.groups:
        if (VertexGroup.weight > 0):
            groupName = Object.vertex_groups[VertexGroup.group].name
            if groupName in BoneNames:
                mapVertexGroupNames[VertexGroup.group] = StripBoneName(groupName)
                if (len(vertexGroupIndices))<4:  #ignore if more 4 bones are influencing the vertex
                    useBonesKey = useBonesKey + pow(2, VertexGroup.group)
                    vertexGroupIndices.append(VertexGroup.group)
                    weightTotal = weightTotal + VertexGroup.weight
    if (weightTotal == 0):
        bWeightTotZero = True  #avoid divide by zero later on
        if (RootBone):
            if Config.Verbose:
                print(" Warning Weight is ZERO for vertex %d => Add it to the root bone" % (VertexIndex))
            RootBoneGroupIndex = FindUniqueIndexForRootBone(Object, RootVertexGroup)
            mapVertexGroupNames[RootBoneGroupIndex] = StripBoneName(RootBone.name)
            useBonesKey = pow(2, RootBoneGroupIndex)
            vertexGroupIndices = list((RootBoneGroupIndex,))

            weightTotal = 1
    else:
        bWeightTotZero = False

    if len(vertexGroupIndices) > 0:
        vertexGroupIndices.sort();

        #build the vertex weight string: vertex indices, followed by influence weight for each bone
        VertexWeightString = "\t\tvertWeights { %d" % (VertexIndex)
        for vertexGroupIndex in vertexGroupIndices:
            #get the weight of this specific VertexGroup (aka bone)
            boneWeight = 1
            for VertexGroup in Vertex.groups:
                if VertexGroup.group == vertexGroupIndex:
                    boneWeight = VertexGroup.weight
            #calculate the influence of this bone compared to the total of weighting applied to this Vertex
            if not bWeightTotZero:
                VertexWeightString += ", %.7f" % (boneWeight / weightTotal)
            else:
                VertexWeightString += ", %.7f" % (1.0 / len(vertexGroupIndices))
        VertexWeightString += "}"
        if bWeightTotZero:
            VertexWeightString += " // total weight was zero in blender , export assign it to the RootBone with weight 1."
        if (len(Vertex.groups)) > 4:
            VertexWeightString += " // vertex is associated to more than 4 bones in blender !! skip some bone association (was associated to %d bones)." % (len(Vertex.groups))
        VertexWeightString += "\n"

        #store in dictionnary information
        if useBonesKey not in useBonesDict:
            VertexList = []
            VertexList.append(VertexWeightString)
            useBonesDict[useBonesKey] = (vertexGroupIndices, VertexList)
        else:
            pair_ListGroupIndices_ListAssignedVertices = useBonesDict[useBonesKey]
            pair_ListGroupIndices_ListAssignedVertices[1].append(VertexWeightString)
            useBonesDict[useBonesKey] = pair_ListGroupIndices_ListAssignedVertices
    else:
        print ("ERROR Vertex %d is not skinned (it doesn't belong to any vertex group\n" % (VertexIndex))



############# ARMATURE: Bone export, and Bone animation export


def WriteArmatureParentRootBones(Config, Object, RootBonesList, skelFile):

    if len(RootBonesList) > 1:
        print(" /!\\  WARNING ,Marmelade need only one ROOT bone per armature, there is %d root bones " % len(RootBonesList))
        print(RootBonesList)

    PoseBones = Object.pose.bones
    for Bone in RootBonesList:
        if Config.Verbose:
            print("      Writing Root Bone: {}...".format(Bone.name))

        PoseBone = PoseBones[Bone.name]
        WriteBonePosition(Config, Object, Bone, PoseBones, PoseBone, skelFile, True)
        if Config.Verbose:
            print("      Done")
        WriteArmatureChildBones(Config, Object, Bone.children, skelFile)


def WriteArmatureChildBones(Config, Object, BonesList, skelFile):
    PoseBones = Object.pose.bones
    for Bone in BonesList:
        if Config.Verbose:
            print("      Writing Child Bone: {}...".format(Bone.name))
        PoseBone = PoseBones[Bone.name]
        WriteBonePosition(Config, Object, Bone, PoseBones, PoseBone, skelFile, True)
        if Config.Verbose:
            print("      Done")

        WriteArmatureChildBones(Config, Object, Bone.children, skelFile)


def WriteBonePosition(Config, Object, Bone, PoseBones, PoseBone, File, isRestPoseNotAnimPose):
    # Compute armature scale :
    # Many others exporter require sthe user to do Apply Scale in Object Mode to have 1,1,1 scale and so that anim data are correctly scaled
    # Here we retreive the Scale of the Armture Object.matrix_world.to_scale() and we use it to scale the bones :-)
    # So new Blender user should not complain about bad animation export if they forgot to apply the Scale to 1,1,1

    armScale = Object.matrix_world.to_scale()
    armRot = Object.matrix_world.to_quaternion()
    if isRestPoseNotAnimPose:
        #skel file, bone header
        File.write("\tCIwAnimBone\n")
        File.write("\t{\n")
        File.write("\t\tname \"%s\"\n" % StripBoneName(Bone.name))
        #get bone local matrix for rest pose
        if Bone.parent:
            File.write("\t\tparent \"%s\"\n" % StripBoneName(Bone.parent.name))
            localmat = Bone.parent.matrix_local.inverted() * Bone.matrix_local
        else:
            localmat = Bone.matrix_local
    else:
        #anim file, bone header
        File.write("\t\t\n")
        File.write("\t\tbone \"%s\" \n" % StripBoneName(Bone.name))
        localmat = PoseBone.matrix
        #get bone local matrix for current anim pose
        if Bone.parent:
            ParentPoseBone = PoseBones[Bone.parent.name]
            localmat = ParentPoseBone.matrix.inverted() * PoseBone.matrix
        else:
            localmat = PoseBone.matrix

    if not Bone.parent:
        #Flip Y Z axes (only on root bone, other bones are local to root bones, so no need to rotate)
        X_ROT = mathutils.Matrix.Rotation(-math.pi / 2, 4, 'X')
        if Config.MergeModes > 0:
            # Merge mode is in world coordinates and not in model coordinates: so apply the world coordinate on the rootbone
            localmat = X_ROT * Object.matrix_world * localmat
            armScale.x =  armScale.y = armScale.z = 1
        else:
            localmat= X_ROT * armRot.to_matrix().to_4x4() * localmat #apply the armature rotation on the root bone


    loc = localmat.to_translation()
    quat = localmat.to_quaternion()

    #Scale the bone
    loc.x *= (armScale.x * Config.Scale)
    loc.y *= (armScale.y * Config.Scale)
    loc.z *= (armScale.z * Config.Scale)

    File.write("\t\tpos { %.9f, %.9f, %.9f }\n" % (loc[0], loc[1], loc[2]))
    File.write("\t\trot { %.9f, %.9f, %.9f, %.9f }\n" % (quat.w, quat.x, quat.y, quat.z))

    if isRestPoseNotAnimPose:
        File.write("\t}\n")


def WriteKeyedAnimationSet(Config, Scene):
    for Object in [Object for Object in Config.ObjectList if Object.animation_data]:
        if Config.Verbose:
            print("  Writing Animation Data for Object: {}".format(Object.name))
        actions = []
        if Config.ExportAnimationActions == 0 and Object.animation_data.action:
            actions.append(Object.animation_data.action)
        else:
            actions = bpy.data.actions[:]
            DefaultAction = Object.animation_data.action

        for Action in actions:
            if Config.ExportAnimationActions == 0:
                animFileName = StripName(Object.name)
            else:
                Object.animation_data.action = Action
                animFileName = "%s_%s" % (StripName(Object.name),StripName(Action.name))

            #Object animated (aka single bone object)
            #build key frame time list

            keyframeTimes = set()
            if Config.ExportAnimationFrames == 1:
                # Exports only key frames
                for FCurve in Action.fcurves:
                    for Keyframe in FCurve.keyframe_points:
                        if Keyframe.co[0] < Scene.frame_start:
                            keyframeTimes.add(Scene.frame_start)
                        elif Keyframe.co[0] > Scene.frame_end:
                            keyframeTimes.add(Scene.frame_end)
                        else:
                            keyframeTimes.add(int(Keyframe.co[0]))
            else:
                # Exports all frames
                keyframeTimes.update(range(Scene.frame_start, Scene.frame_end + 1, 1))
            keyframeTimes = list(keyframeTimes)
            keyframeTimes.sort()
            if len(keyframeTimes):
                #Create the anim file for offset animation (or single bone animation
                animfullname = os.path.dirname(Config.FilePath) + os.sep + "anims" + os.sep + "%s_offset.anim" % animFileName
                #not yet supported
                """
                ##    ensure_dir(animfullname)
                ##    if Config.Verbose:
                ##        print("      Creating anim file (single bone animation) %s" % (animfullname))
                ##    animFile = open(animfullname, "w")
                ##    animFile.write('// anim file exported from : %r\n' % os.path.basename(bpy.data.filepath))
                ##    animFile.write("CIwAnim\n")
                ##    animFile.write("{\n")
                ##    animFile.write("\tent \"%s\"\n" % (StripName(Object.name)))
                ##    animFile.write("\tskeleton \"SingleBone\"\n")
                ##    animFile.write("\t\t\n")
                ##
                ##    Config.File.write("\t\".\\anims\\%s_offset.anim\"\n" % animFileName))
                ##
                ##    for KeyframeTime in keyframeTimes:
                ##        #Scene.frame_set(KeyframeTime)
                ##        animFile.write("\tCIwAnimKeyFrame\n")
                ##        animFile.write("\t{\n")
                ##        animFile.write("\t\ttime %.2f // frame num %d \n" % (KeyframeTime/Config.AnimFPS, KeyframeTime))
                ##        animFile.write("\t\t\n")
                ##        animFile.write("\t\tbone \"SingleBone\" \n")
                ##        #postion
                ##        posx = 0
                ##        for FCurve in Action.fcurves:
                ##            if FCurve.data_path == "location" and FCurve.array_index == 0: posx = FCurve.evaluate(KeyframeTime)
                ##        posy = 0
                ##        for FCurve in Action.fcurves:
                ##            if FCurve.data_path == "location" and FCurve.array_index == 1: posy = FCurve.evaluate(KeyframeTime)
                ##        posz = 0
                ##        for FCurve in Action.fcurves:
                ##            if FCurve.data_path == "location" and FCurve.array_index == 2: posz = FCurve.evaluate(KeyframeTime)
                ##        animFile.write("\t\tpos {%.9f,%.9f,%.9f}\n" % (posx, posy, posz))
                ##        #rotation
                ##        rot = Euler()
                ##        rot[0] = 0
                ##        for FCurve in Action.fcurves:
                ##            if FCurve.data_path == "rotation_euler" and FCurve.array_index == 1: rot[0] = FCurve.evaluate(KeyframeTime)
                ##        rot[1] = 0
                ##        for FCurve in Action.fcurves:
                ##            if FCurve.data_path == "rotation_euler" and FCurve.array_index == 2: rot[1] = FCurve.evaluate(KeyframeTime)
                ##        rot[2] = 0
                ##        for FCurve in Action.fcurves:
                ##            if FCurve.data_path == "rotation_euler" and FCurve.array_index == 3: rot[2] = FCurve.evaluate(KeyframeTime)
                ##        rot = rot.to_quaternion()
                ##        animFile.write("\t\trot {%.9f,%.9f,%.9f,%.9f}\n" % (rot[0], rot[1], rot[2], rot[3]))
                ##        #scale
                ##        scalex = 0
                ##        for FCurve in Action.fcurves:
                ##            if FCurve.data_path == "scale" and FCurve.array_index == 0: scalex = FCurve.evaluate(KeyframeTime)
                ##        scaley = 0
                ##        for FCurve in Action.fcurves:
                ##            if FCurve.data_path == "scale" and FCurve.array_index == 1: scaley = FCurve.evaluate(KeyframeTime)
                ##        scalez = 0
                ##        for FCurve in Action.fcurves:
                ##            if FCurve.data_path == "scale" and FCurve.array_index == 2: scalez = FCurve.evaluate(KeyframeTime)
                ##        animFile.write("\t\t//scale {%.9f,%.9f,%.9f}\n" % (scalex, scaley, scalez))
                ##        #keyframe done
                ##        animFile.write("\t}\n")
                ##    animFile.write("}\n")
                ##    animFile.close()
                """
            else:
                if Config.Verbose:
                    print("    Object %s has no useable animation data." % (StripName(Object.name)))

            if Config.ExportArmatures and Object.type == "ARMATURE":
                if Config.Verbose:
                    print("    Writing Armature Bone Animation Data...\n")
                PoseBones = Object.pose.bones
                Bones = Object.data.bones
                #riged bones animated
                #build key frame time list
                keyframeTimes = set()
                if Config.ExportAnimationFrames == 1:
                    # Exports only key frames
                    for FCurve in Action.fcurves:
                        for Keyframe in FCurve.keyframe_points:
                            if Keyframe.co[0] < Scene.frame_start:
                                keyframeTimes.add(Scene.frame_start)
                            elif Keyframe.co[0] > Scene.frame_end:
                                keyframeTimes.add(Scene.frame_end)
                            else:
                                keyframeTimes.add(int(Keyframe.co[0]))
                else:
                    # Exports all frame
                    keyframeTimes.update(range(Scene.frame_start, Scene.frame_end + 1, 1))

                keyframeTimes = list(keyframeTimes)
                keyframeTimes.sort()
                if Config.Verbose:
                    print("Exporting frames: ")
                    print(keyframeTimes)
                    if (Scene.frame_preview_end > Scene.frame_end):
                        print(" WARNING: END Frame of animation in UI preview is Higher than the Scene Frame end:\n Scene.frame_end %d versus Scene.frame_preview_end %d.\n"
                              % (Scene.frame_end, Scene.frame_preview_end))
                        print(" => You might need to change the Scene End Frame, to match the current UI preview frame end...\n=> if you don't want to miss end of animation.\n")

                if len(keyframeTimes):
                    #Create the anim file
                    animfullname = os.path.dirname(Config.FilePath) + os.sep + "anims" + os.sep + "%s.anim" % animFileName
                    ensure_dir(animfullname)
                    if Config.Verbose:
                        print("      Creating anim file (bones animation) %s\n" % (animfullname))
                        print("      Frame count %d \n" % (len(keyframeTimes)))
                    animFile = open(animfullname, "w")
                    animFile.write('// anim file exported from : %r\n' % os.path.basename(bpy.data.filepath))
                    animFile.write("CIwAnim\n")
                    animFile.write("{\n")
                    animFile.write("\tskeleton \"%s\"\n" % (StripName(Object.name)))
                    animFile.write("\t\t\n")

                    Config.File.write("\t\".\\anims\\%s.anim\"\n" % animFileName)

                    for KeyframeTime in keyframeTimes:
                        if Config.Verbose:
                            print("     Writing Frame %d:" % KeyframeTime)
                        animFile.write("\tCIwAnimKeyFrame\n")
                        animFile.write("\t{\n")
                        animFile.write("\t\ttime %.2f // frame num %d \n" % (KeyframeTime / Config.AnimFPS, KeyframeTime))
                        #for every frame write bones positions
                        Scene.frame_set(KeyframeTime)
                        for PoseBone in PoseBones:
                            if Config.Verbose:
                                print("      Writing Bone: {}...".format(PoseBone.name))
                            animFile.write("\t\t\n")

                            Bone = Bones[PoseBone.name]
                            WriteBonePosition(Config, Object, Bone, PoseBones, PoseBone, animFile, False)
                        #keyframe done
                        animFile.write("\t}\n")
                    animFile.write("}\n")
                    animFile.close()
            else:
                if Config.Verbose:
                    print("    Object %s has no useable animation data." % (StripName(Object.name)))
        if Config.ExportAnimationActions == 1:
            #set back the original default animation
            Object.animation_data.action = DefaultAction
        if Config.Verbose:
            print("  Done") #Done with Object




################## Utilities

def StripBoneName(name):
    return name.replace(" ", "")


def StripName(Name):

    def ReplaceSet(String, OldSet, NewChar):
        for OldChar in OldSet:
            String = String.replace(OldChar, NewChar)
        return String

    import string

    NewName = ReplaceSet(Name, string.punctuation + " ", "_")
    return NewName


def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)


def CloseFile(Config):
    if Config.Verbose:
        print("Closing File...")
    Config.File.close()
    if Config.Verbose:
        print("Done")


CoordinateSystems = (
    ("1", "Left-Handed", ""),
    ("2", "Right-Handed", ""),
    )


AnimationFrameModes = (
    ("0", "None", ""),
    ("1", "Keyframes Only", ""),
    ("2", "Full Animation", ""),
    )

AnimationActions = (
    ("0", "Default Animation", ""),
    ("1", "All Animations", ""),
    )

ExportModes = (
    ("1", "All Objects", ""),
    ("2", "Selected Objects", ""),
    )

MergeModes = (
    ("0", "None", ""),
    ("1", "Merge in one big Mesh", ""),
    ("2", "Merge in unique Geo File containing several meshes", ""),
    )


from bpy.props import StringProperty, EnumProperty, BoolProperty, IntProperty


class MarmaladeExporter(bpy.types.Operator):
    """Export to the Marmalade model format (.group)"""

    bl_idname = "export.marmalade"
    bl_label = "Export Marmalade"

    filepath = StringProperty(subtype='FILE_PATH')
     #Export Mode
    ExportMode = EnumProperty(
        name="Export",
        description="Select which objects to export. Only Mesh, Empty, " \
                    "and Armature objects will be exported",
        items=ExportModes,
        default="1")

    MergeModes = EnumProperty(
        name="Merge",
        description="Select if objects should be merged in one Geo File (it can be usefull if a scene is done by several cube/forms)." \
                    "Do not merge rigged character that have an armature.",
        items=MergeModes,
        default="0")

    #General Options
    Scale = IntProperty(
        name="Scale Percent",
        description="Scale percentage applied for export",
        default=100, min=1, max=1000)

    FlipNormals = BoolProperty(
        name="Flip Normals",
        description="",
        default=False)
    ApplyModifiers = BoolProperty(
        name="Apply Modifiers",
        description="Apply object modifiers before export",
        default=False)
    ExportVertexColors = BoolProperty(
        name="Export Vertices Colors",
        description="Export colors set on vertices, if any",
        default=True)
    ExportMaterialColors = BoolProperty(
        name="Export Material Colors",
        description="Ambient color is exported on the Material",
        default=True)
    ExportTextures = BoolProperty(
        name="Export Textures and UVs",
        description="Exports UVs and Reference external image files to be used by the model",
        default=True)
    CopyTextureFiles = BoolProperty(
        name="Copy Textures Files",
        description="Copy referenced Textures files in the models\\textures directory",
        default=True)
    ExportArmatures = BoolProperty(
        name="Export Armatures",
        description="Export the bones of any armatures to deform meshes",
        default=True)
    ExportAnimationFrames = EnumProperty(
        name="Animations Frames",
        description="Select the type of animations to export. Only object " \
                    "and armature bone animations can be exported. Keyframes exports only the keyed frames" \
                    "Full Animation exports every frames, None disables animationq export. ",
        items=AnimationFrameModes,
        default="1")
    ExportAnimationActions = EnumProperty(
        name="Animations Actions",
        description="By default only the Default Animation Action assoiated to an armature is exported." \
                    "However if you have defined several animations on the same armature,"\
                    "you can select to export all animations. You can see the list of animation actions in the DopeSheet window.",
        items=AnimationActions,
        default="0")
    AnimFPS = IntProperty(
        name="Animation FPS",
        description="Frame rate used to export animation in seconds (can be used to artficially slow down the exported animation, or to speed up it",
        default=30, min=1, max=300)

    #Advance Options
    CoordinateSystem = EnumProperty(
        name="System",
        description="Select a coordinate system to export to",
        items=CoordinateSystems,
        default="1")

    Verbose = BoolProperty(
        name="Verbose",
        description="Run the exporter in debug mode. Check the console for output",
        default=True)

    def execute(self, context):
        #Append .group
        FilePath = bpy.path.ensure_ext(self.filepath, ".group")

        Config = MarmaladeExporterSettings(context,
                                         FilePath,
                                         CoordinateSystem=self.CoordinateSystem,
                                         FlipNormals=self.FlipNormals,
                                         ApplyModifiers=self.ApplyModifiers,
                                         Scale=self.Scale,
                                         AnimFPS=self.AnimFPS,
                                         ExportVertexColors=self.ExportVertexColors,
                                         ExportMaterialColors=self.ExportMaterialColors,
                                         ExportTextures=self.ExportTextures,
                                         CopyTextureFiles=self.CopyTextureFiles,
                                         ExportArmatures=self.ExportArmatures,
                                         ExportAnimationFrames=self.ExportAnimationFrames,
                                         ExportAnimationActions=self.ExportAnimationActions,
                                         ExportMode=self.ExportMode,
                                         MergeModes=self.MergeModes,
                                         Verbose=self.Verbose)

        # Exit edit mode before exporting, so current object states are exported properly.
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')

        ExportMadeWithMarmaladeGroup(Config)
        return {'FINISHED'}

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = bpy.path.ensure_ext(bpy.data.filepath, ".group")
        WindowManager = context.window_manager
        WindowManager.fileselect_add(self)
        return {'RUNNING_MODAL'}


def menu_func(self, context):
    self.layout.operator(MarmaladeExporter.bl_idname, text="Marmalade cross-platform Apps (.group)")


def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_export.append(menu_func)


def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_export.remove(menu_func)


if __name__ == "__main__":
    register()
