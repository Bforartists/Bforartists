#!BPY
""" Registration info for Blender menus:
Name: 'X3D Extensible 3D (.x3d)...'
Blender: 235
Group: 'Export'
Submenu: 'All Objects...' all
Submenu: 'All Objects compressed...' comp
Submenu: 'Selected Objects...' selected
Tooltip: 'Export to Extensible 3D file (.x3d)'
"""

__author__ = ("Bart")
__email__ = ["Bart, bart:neeneenee*de"]
__url__ = ["Author's (Bart) homepage, http://www.neeneenee.de/vrml"]
__version__ = "2006/01/17"
__bpydoc__ = """\
This script exports to X3D format.

Usage:

Run this script from "File->Export" menu.  A pop-up will ask whether you
want to export only selected or all relevant objects.

Known issues:<br>
    Doesn't handle multiple materials (don't use material indices);<br>
    Doesn't handle multiple UV textures on a single mesh (create a mesh
for each texture);<br>
    Can't get the texture array associated with material * not the UV ones;
"""


# $Id$
#
#------------------------------------------------------------------------
# X3D exporter for blender 2.36 or above
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
#

####################################
# Library dependancies
####################################

import Blender
from Blender import Object, NMesh, Lamp, Draw, Image, Text, sys
from Blender.Scene import Render
import math

####################################
# Global Variables
####################################

scene = Blender.Scene.getCurrent()
world = Blender.World.GetCurrent() 
worldmat = Blender.Texture.Get()
filename = Blender.Get('filename')
_safeOverwrite = True
ARG=''
extension = ''

class DrawTypes:
    """Object DrawTypes enum values
    BOUNDS - draw only the bounding box of the object
    WIRE - draw object as a wire frame
    SOLID - draw object with flat shading
    SHADED - draw object with OpenGL shading
"""
    BOUNDBOX  = 1
    WIRE      = 2
    SOLID     = 3
    SHADED    = 4
    TEXTURE   = 5

if not hasattr(Blender.Object,'DrawTypes'):
    Blender.Object.DrawTypes = DrawTypes()

##########################################################
# Functions for writing output file
##########################################################

class VRML2Export:

    def __init__(self, filename):
        #--- public you can change these ---
        self.writingcolor = 0
        self.writingtexture = 0
        self.writingcoords = 0
        self.wire = 0
        self.proto = 1
        self.matonly = 0
        self.share = 0
        self.billnode = 0
        self.halonode = 0
        self.collnode = 0
        self.tilenode = 0
        self.verbose=2     # level of verbosity in console 0-none, 1-some, 2-most
        self.cp=3          # decimals for material color values     0.000 - 1.000
        self.vp=3          # decimals for vertex coordinate values  0.000 - n.000
        self.tp=3          # decimals for texture coordinate values 0.000 - 1.000
        self.it=3
        
        #--- class private don't touch ---
        self.texNames={}   # dictionary of textureNames
        self.matNames={}   # dictionary of materiaNames
        self.meshNames={}   # dictionary of meshNames
        self.indentLevel=0 # keeps track of current indenting
        self.filename=filename
        self.file = open(filename, "w")
        self.bNav=0
        self.nodeID=0
        self.namesReserved=[ "Anchor","Appearance","Arc2D","ArcClose2D","AudioClip","Background","Billboard",
                             "BooleanFilter","BooleanSequencer","BooleanToggle","BooleanTrigger","Box","Circle2D",
                             "Collision","Color","ColorInterpolator","ColorRGBA","component","Cone","connect",
                             "Contour2D","ContourPolyline2D","Coordinate","CoordinateDouble","CoordinateInterpolator",
                             "CoordinateInterpolator2D","Cylinder","CylinderSensor","DirectionalLight","Disk2D",
                             "ElevationGrid","EspduTransform","EXPORT","ExternProtoDeclare","Extrusion","field",
                             "fieldValue","FillProperties","Fog","FontStyle","GeoCoordinate","GeoElevationGrid",
                             "GeoLocationLocation","GeoLOD","GeoMetadata","GeoOrigin","GeoPositionInterpolator",
                             "GeoTouchSensor","GeoViewpoint","Group","HAnimDisplacer","HAnimHumanoid","HAnimJoint",
                             "HAnimSegment","HAnimSite","head","ImageTexture","IMPORT","IndexedFaceSet",
                             "IndexedLineSet","IndexedTriangleFanSet","IndexedTriangleSet","IndexedTriangleStripSet",
                             "Inline","IntegerSequencer","IntegerTrigger","IS","KeySensor","LineProperties","LineSet",
                             "LoadSensor","LOD","Material","meta","MetadataDouble","MetadataFloat","MetadataInteger",
                             "MetadataSet","MetadataString","MovieTexture","MultiTexture","MultiTextureCoordinate",
                             "MultiTextureTransform","NavigationInfo","Normal","NormalInterpolator","NurbsCurve",
                             "NurbsCurve2D","NurbsOrientationInterpolator","NurbsPatchSurface",
                             "NurbsPositionInterpolator","NurbsSet","NurbsSurfaceInterpolator","NurbsSweptSurface",
                             "NurbsSwungSurface","NurbsTextureCoordinate","NurbsTrimmedSurface","OrientationInterpolator",
                             "PixelTexture","PlaneSensor","PointLight","PointSet","Polyline2D","Polypoint2D",
                             "PositionInterpolator","PositionInterpolator2D","ProtoBody","ProtoDeclare","ProtoInstance",
                             "ProtoInterface","ProximitySensor","ReceiverPdu","Rectangle2D","ROUTE","ScalarInterpolator",
                             "Scene","Script","Shape","SignalPdu","Sound","Sphere","SphereSensor","SpotLight","StaticGroup",
                             "StringSensor","Switch","Text","TextureBackground","TextureCoordinate","TextureCoordinateGenerator",
                             "TextureTransform","TimeSensor","TimeTrigger","TouchSensor","Transform","TransmitterPdu",
                             "TriangleFanSet","TriangleSet","TriangleSet2D","TriangleStripSet","Viewpoint","VisibilitySensor",
                             "WorldInfo","X3D","XvlShell","VertexShader","FragmentShader","MultiShaderAppearance","ShaderAppearance" ]
        self.namesStandard=[ "Empty","Empty.000","Empty.001","Empty.002","Empty.003","Empty.004","Empty.005",
                             "Empty.006","Empty.007","Empty.008","Empty.009","Empty.010","Empty.011","Empty.012",
                             "Scene.001","Scene.002","Scene.003","Scene.004","Scene.005","Scene.06","Scene.013",
                             "Scene.006","Scene.007","Scene.008","Scene.009","Scene.010","Scene.011","Scene.012",
                             "World","World.000","World.001","World.002","World.003","World.004","World.005" ]
        self.namesFog=[ "","LINEAR","EXPONENTIAL","" ]

##########################################################
# Writing nodes routines
##########################################################

    def writeHeader(self):
        bfile = sys.expandpath(Blender.Get('filename'))
        self.file.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
        self.file.write("<!DOCTYPE X3D PUBLIC \"ISO//Web3D//DTD X3D 3.0//EN\" \"http://www.web3d.org/specifications/x3d-3.0.dtd\">\n")
        self.file.write("<X3D version=\"3.0\" profile=\"Immersive\" xmlns:xsd=\"http://www.w3.org/2001/XMLSchema-instance\" xsd:noNamespaceSchemaLocation=\"http://www.web3d.org/specifications/x3d-3.0.xsd\">\n")
        self.file.write("<head>\n")
        self.file.write("\t<meta name=\"filename\" content=\"%s\" />\n" % sys.basename(bfile))
        self.file.write("\t<meta name=\"generator\" content=\"Blender %s\" />\n" % Blender.Get('version'))
        self.file.write("\t<meta name=\"translator\" content=\"X3D exporter v1.55 (2006/01/17)\" />\n")
        self.file.write("</head>\n")
        self.file.write("<Scene>\n")

    def writeInline(self):
        inlines = Blender.Scene.Get()
        allinlines = len(inlines)
        if scene != inlines[0]:
            return
        else:
            for i in xrange(allinlines):
                nameinline=inlines[i].name
                if (nameinline not in self.namesStandard) and (i > 0):
                    self.file.write("<Inline DEF=\"%s\" " % (self.cleanStr(nameinline)))
                    nameinline = nameinline+".x3d"
                    self.file.write("url=\"%s\" />" % nameinline)
                    self.file.write("\n\n")

    def writeScript(self):
        textEditor = Blender.Text.Get() 
        alltext = len(textEditor)
        for i in xrange(alltext):
            nametext = textEditor[i].getName()
            nlines = textEditor[i].getNLines()
            if (self.proto == 1):
                if (nametext == "proto" or nametext == "proto.js" or nametext == "proto.txt") and (nlines != None):
                    nalllines = len(textEditor[i].asLines())
                    alllines = textEditor[i].asLines()
                    for j in xrange(nalllines):
                        self.writeIndented(alllines[j] + "\n")
            elif (self.proto == 0):
                if (nametext == "route" or nametext == "route.js" or nametext == "route.txt") and (nlines != None):
                    nalllines = len(textEditor[i].asLines())
                    alllines = textEditor[i].asLines()
                    for j in xrange(nalllines):
                        self.writeIndented(alllines[j] + "\n")
        self.writeIndented("\n")

    def writeViewpoint(self, thisObj):
        context = scene.getRenderingContext()
        ratio = float(context.imageSizeY())/float(context.imageSizeX())
        lens = (360* (math.atan(ratio *16 / thisObj.data.getLens()) / math.pi))*(math.pi/180)
        lens = min(lens, math.pi) 
        # get the camera location, subtract 90 degress from X to orient like X3D does
        loc = self.rotatePointForVRML(thisObj.loc)
        rot = [thisObj.RotX - 1.57, thisObj.RotY, thisObj.RotZ]
        nRot = self.rotatePointForVRML(rot)
        # convert to Quaternion and to Angle Axis
        Q  = self.eulerToQuaternions(nRot[0], nRot[1], nRot[2])
        Q1 = self.multiplyQuaternions(Q[0], Q[1])
        Qf = self.multiplyQuaternions(Q1, Q[2])
        angleAxis = self.quaternionToAngleAxis(Qf)
        self.file.write("<Viewpoint DEF=\"%s\" " % (self.cleanStr(thisObj.name)))
        self.file.write("description=\"%s\" " % (thisObj.name))
        self.file.write("centerOfRotation=\"0 0 0\" ")
        self.file.write("position=\"%3.2f %3.2f %3.2f\" " % (loc[0], loc[1], loc[2]))
        self.file.write("orientation=\"%3.2f %3.2f %3.2f %3.2f\" " % (angleAxis[0], angleAxis[1], -angleAxis[2], angleAxis[3]))
        self.file.write("fieldOfView=\"%.3f\" />\n\n" % (lens))

    def writeFog(self):
        if world:
            mtype = world.getMistype()
            mparam = world.getMist()
            grd = world.getHor()
            grd0, grd1, grd2 = grd[0], grd[1], grd[2]
        else:
            return
        if (mtype == 1 or mtype == 2):
            self.file.write("<Fog fogType=\"%s\" " % self.namesFog[mtype])						
            self.file.write("color=\"%s %s %s\" " % (round(grd0,self.cp), round(grd1,self.cp), round(grd2,self.cp)))
            self.file.write("visibilityRange=\"%s\" />\n\n" % round(mparam[2],self.cp))
        else:
            return

    def writeNavigationInfo(self, scene):
        allObj = []
        allObj = list(scene.objects)
        headlight = "TRUE"
        vislimit = 0.0
        for thisObj in allObj:
            objType=thisObj.type
            if objType == "Camera":
                vislimit = thisObj.data.clipEnd
            elif objType == "Lamp":
                headlight = "FALSE"
        self.file.write("<NavigationInfo headlight=\"%s\" " % headlight)
        self.file.write("visibilityLimit=\"%s\" " % (round(vislimit,self.cp)))
        self.file.write("type=\"EXAMINE, ANY\" avatarSize=\"0.25, 1.75, 0.75\" />\n\n")

    def writeSpotLight(self, ob, lamp):
        safeName = self.cleanStr(ob.name)
        if world:
            ambi = world.amb
            ambientIntensity = ((float(ambi[0] + ambi[1] + ambi[2]))/3)/2.5
        else:
            ambi = 0
            ambientIntensity = 0

        # compute cutoff and beamwidth
        intensity=min(lamp.energy/1.75,1.0)
        beamWidth=((lamp.spotSize*math.pi)/180.0)*.37;
        cutOffAngle=beamWidth*1.3

        dx,dy,dz=self.computeDirection(ob)
        # note -dx seems to equal om[3][0]
        # note -dz seems to equal om[3][1]
        # note  dy seems to equal om[3][2]

        location=ob.getLocation('worldspace')
        radius = lamp.dist*math.cos(beamWidth)
        self.file.write("<SpotLight DEF=\"%s\" " % safeName)
        self.file.write("radius=\"%s\" " % (round(radius,self.cp)))
        self.file.write("ambientIntensity=\"%s\" " % (round(ambientIntensity,self.cp)))
        self.file.write("intensity=\"%s\" " % (round(intensity,self.cp)))
        self.file.write("color=\"%s %s %s\" " % (round(lamp.col[0],self.cp), round(lamp.col[1],self.cp), round(lamp.col[2],self.cp)))
        self.file.write("beamWidth=\"%s\" " % (round(beamWidth,self.cp)))
        self.file.write("cutOffAngle=\"%s\" " % (round(cutOffAngle,self.cp)))
        self.file.write("direction=\"%s %s %s\" " % (round(dx,3),round(dy,3),round(dz,3)))
        self.file.write("location=\"%s %s %s\" />\n\n" % (round(location[0],3), round(location[1],3), round(location[2],3)))
        
    def writeDirectionalLight(self, ob, lamp):
        safeName = self.cleanStr(ob.name)
        if world:
            ambi = world.amb
            ambientIntensity = ((float(ambi[0] + ambi[1] + ambi[2]))/3)/2.5
        else:
            ambi = 0
            ambientIntensity = 0

        intensity=min(lamp.energy/1.75,1.0) 
        (dx,dy,dz)=self.computeDirection(ob)
        self.file.write("<DirectionalLight DEF=\"%s\" " % safeName)
        self.file.write("ambientIntensity=\"%s\" " % (round(ambientIntensity,self.cp)))
        self.file.write("color=\"%s %s %s\" " % (round(lamp.col[0],self.cp), round(lamp.col[1],self.cp), round(lamp.col[2],self.cp)))
        self.file.write("intensity=\"%s\" " % (round(intensity,self.cp)))
        self.file.write("direction=\"%s %s %s\" />\n\n" % (round(dx,4),round(dy,4),round(dz,4)))

    def writePointLight(self, ob, lamp):
        safeName = self.cleanStr(ob.name)
        if world:
            ambi = world.amb
            ambientIntensity = ((float(ambi[0] + ambi[1] + ambi[2]))/3)/2.5
        else:
            ambi = 0
            ambientIntensity = 0
        
        location=ob.getLocation('worldspace')
        intensity=min(lamp.energy/1.75,1.0) 
        radius = lamp.dist
        self.file.write("<PointLight DEF=\"%s\" " % safeName)
        self.file.write("ambientIntensity=\"%s\" " % (round(ambientIntensity,self.cp)))
        self.file.write("color=\"%s %s %s\" " % (round(lamp.col[0],self.cp), round(lamp.col[1],self.cp), round(lamp.col[2],self.cp)))
        self.file.write("intensity=\"%s\" " % (round(intensity,self.cp)))
        self.file.write("radius=\"%s\" " % radius )
        self.file.write("location=\"%s %s %s\" />\n\n" % (round(location[0],3), round(location[1],3), round(location[2],3)))

    def writeNode(self, thisObj):
        obname=str(thisObj.getName())
        if obname in self.namesStandard:
            return
        else:
            dx,dy,dz = self.computeDirection(thisObj)
            location = thisObj.getLocation('worldspace')
            self.writeIndented("<%s\n" % obname,1)
            self.writeIndented("# direction %s %s %s\n" % (round(dx,3),round(dy,3),round(dz,3)))
            self.writeIndented("# location %s %s %s\n" % (round(location[0],3), round(location[1],3), round(location[2],3)))
            self.writeIndented("/>\n",-1)
            self.writeIndented("\n")

    def secureName(self, name):
        name = name + str(self.nodeID)
        self.nodeID=self.nodeID+1
        if len(name) <= 3:
            newname = "_" + str(self.nodeID)
            return "%s" % (newname)
        else:
            for bad in ['"','#',"'",',','.','[','\\',']','{','}']:
                name=name.replace(bad,'_')
            if name in self.namesReserved:
                newname = name[0:3] + "_" + str(self.nodeID)
                return "%s" % (newname)
            elif name[0].isdigit():
                newname = "_" + name + str(self.nodeID)
                return "%s" % (newname)
            else:
                newname = name
                return "%s" % (newname)

    def writeIndexedFaceSet(self, ob, normals = 0):
        imageMap={}   # set of used images
        sided={}      # 'one':cnt , 'two':cnt
        vColors={}    # 'multi':1
        meshName = self.cleanStr(ob.name)
        mesh=ob.data
        meshME = self.cleanStr(mesh.name)
        if len(mesh.faces) == 0: return
        for face in mesh.faces:
            if face.mode & Blender.NMesh.FaceModes['HALO'] and self.halonode == 0:
                self.writeIndented("<Billboard axisOfRotation=\"0 0 0\">\n",1)
                self.halonode = 1
            elif face.mode & Blender.NMesh.FaceModes['BILLBOARD'] and self.billnode == 0:
                self.writeIndented("<Billboard axisOfRotation=\"0 1 0\">\n",1)
                self.billnode = 1
            elif face.mode & Blender.NMesh.FaceModes['OBCOL'] and self.matonly == 0:
                self.matonly = 1
            elif face.mode & Blender.NMesh.FaceModes['SHAREDCOL'] and self.share == 0:
                self.share = 1
            elif face.mode & Blender.NMesh.FaceModes['TILES'] and self.tilenode == 0:
                self.tilenode = 1
            elif not face.mode & Blender.NMesh.FaceModes['DYNAMIC'] and self.collnode == 0:
                self.writeIndented("<Collision enabled=\"false\">\n",1)
                self.collnode = 1

        nIFSCnt=self.countIFSSetsNeeded(mesh, imageMap, sided, vColors)
        
        if nIFSCnt > 1:
            self.writeIndented("<Group DEF=\"%s%s\">\n" % ("G_", meshName),1)
        
        if sided.has_key('two') and sided['two'] > 0:
            bTwoSided=1
        else:
            bTwoSided=0
        
        location= ob.getLocation('worldspace')
        self.writeIndented("<Transform DEF=\"%s\" translation=\"%s %s %s\">\n" % (meshName, round(location[0],3), round(location[1],3), round(location[2],3)),1)
        self.writeIndented("<Shape>\n",1)
            
        maters=mesh.materials
        hasImageTexture=0
        issmooth=0

        if len(maters) > 0 or mesh.hasFaceUV():
          self.writeIndented("<Appearance>\n", 1)
          # right now this script can only handle a single material per mesh.
          if len(maters) >= 1:
            mat=Blender.Material.Get(maters[0].name)
            matFlags = mat.getMode()
            if not matFlags & Blender.Material.Modes['TEXFACE']:
              self.writeMaterial(mat, self.cleanStr(maters[0].name,''))
              if len(maters) > 1:
                print "Warning: mesh named %s has multiple materials" % meshName
                print "Warning: only one material per object handled"
        
            #-- textures
            if mesh.hasFaceUV():
                for face in mesh.faces:
                    if (hasImageTexture == 0) and (face.image):
                        self.writeImageTexture(face.image)
                        hasImageTexture=1  # keep track of face texture
            if self.tilenode == 1:
                self.writeIndented("<TextureTransform	scale=\"%s %s\" />\n" % (face.image.xrep, face.image.yrep))
                self.tilenode = 0
            self.writeIndented("</Appearance>\n", -1)

        #-- IndexedFaceSet or IndexedLineSet

        # check if object is wireframe only
        if ob.drawType == Blender.Object.DrawTypes.WIRE:
            # user selected WIRE=2 on the Drawtype=Wire on (F9) Edit page
            ifStyle="IndexedLineSet"
            self.wire = 1
        else:
            # user selected BOUNDS=1, SOLID=3, SHARED=4, or TEXTURE=5
            ifStyle="IndexedFaceSet"
        # look up mesh name, use it if available
        if self.meshNames.has_key(meshME):
            self.writeIndented("<%s USE=\"ME_%s\">" % (ifStyle, meshME), 1)
            self.meshNames[meshME]+=1
        else:
            if int(mesh.users) > 1:
                self.writeIndented("<%s DEF=\"ME_%s\" " % (ifStyle, meshME), 1)
                self.meshNames[meshME]=1
            else:
                self.writeIndented("<%s " % ifStyle, 1)
            if ob.drawType != Blender.Object.DrawTypes.WIRE:
                if bTwoSided == 1:
                    self.file.write("solid=\"false\" ")
                else:
                    self.file.write("solid=\"true\" ")

            for face in mesh.faces:
                if face.smooth:
                     issmooth=1
            if issmooth==1 and self.wire == 0:
                creaseAngle=(mesh.getMaxSmoothAngle())*(math.pi/180.0)
                self.file.write("creaseAngle=\"%s\" " % (round(creaseAngle,self.cp)))

            #--- output vertexColors
            if self.share == 1 and self.matonly == 0:
                self.writeVertexColors(mesh)
            if ob.drawType != Blender.Object.DrawTypes.WIRE:
                #--- output textureCoordinates if UV texture used
                if mesh.hasFaceUV():
                    if self.matonly == 1 and self.share == 1:
                        self.writeFaceColors(mesh)
                    elif hasImageTexture == 1:
                        self.writeTextureCoordinates(mesh)
            #--- output coordinates
            self.writeCoordinates(ob, mesh, meshName)

            self.writingcoords = 1
            self.writingtexture = 1
            self.writingcolor = 1
            self.writeCoordinates(ob, mesh, meshName)
       
            if ob.drawType != Blender.Object.DrawTypes.WIRE:
                #--- output textureCoordinates if UV texture used
                if mesh.hasFaceUV():
                    if hasImageTexture == 1:
                        self.writeTextureCoordinates(mesh)
                    elif self.matonly == 1 and self.share == 1:
                        self.writeFaceColors(mesh)
            #--- output vertexColors
            if self.share == 1 and self.matonly == 0:
                self.writeVertexColors(mesh)
        self.matonly = 0
        self.share = 0
        self.wire = 0
        self.writingcoords = 0
        self.writingtexture = 0
        self.writingcolor = 0
        #--- output closing braces
        self.writeIndented("</%s>\n" % ifStyle, -1)
        self.writeIndented("</Shape>\n", -1)
        self.writeIndented("</Transform>\n", -1)

        if self.halonode == 1:
            self.writeIndented("</Billboard>\n", -1)
            self.halonode = 0

        if self.billnode == 1:
            self.writeIndented("</Billboard>\n", -1)
            self.billnode = 0

        if self.collnode == 1:
            self.writeIndented("</Collision>\n", -1)
            self.collnode = 0

        if nIFSCnt > 1:
            self.writeIndented("</Group>\n", -1)

        self.file.write("\n")

    def writeCoordinates(self, ob, mesh, meshName):
        meshVertexList = mesh.verts

        # create vertex list and pre rotate -90 degrees X for VRML
        location= ob.getLocation('worldspace')
        if self.writingcoords == 0:
            self.file.write('coordIndex="')
            for face in mesh.faces:
                for i in xrange(len(face)):
                    indx=face[i].index
                    self.file.write("%s " % indx)
                self.file.write("-1, ")
            self.file.write("\">\n")
        else:
            #-- vertices
            mesh.transform(ob.matrixWorld)
            self.writeIndented("<Coordinate DEF=\"%s%s\" \n" % ("coord_",meshName), 1)
            self.file.write("\t\t\t\tpoint=\"")
            for v in meshVertexList:
                self.file.write("%.6f %.6f %.6f, " % tuple(v.co))
            self.file.write("\" />")
            self.writeIndented("\n", -1)

    def writeTextureCoordinates(self, mesh):
        texCoordList=[] 
        texIndexList=[]
        j=0

        for face in mesh.faces:
            for i in xrange(len(face)):
                texIndexList.append(j)
                texCoordList.append(face.uv[i])
                j=j+1
            texIndexList.append(-1)
        if self.writingtexture == 0:
            self.file.write("\n\t\t\ttexCoordIndex=\"")
            texIndxStr=""
            for i in xrange(len(texIndexList)):
                texIndxStr = texIndxStr + "%d, " % texIndexList[i]
                if texIndexList[i]==-1:
                    self.file.write(texIndxStr)
                    texIndxStr=""
            self.file.write("\"\n\t\t\t")
        else:
            self.writeIndented("<TextureCoordinate point=\"", 1)
            for i in xrange(len(texCoordList)):
                self.file.write("%s %s, " % (round(texCoordList[i][0],self.tp), round(texCoordList[i][1],self.tp)))
            self.file.write("\" />")
            self.writeIndented("\n", -1)

    def writeFaceColors(self, mesh):
        if self.writingcolor == 0:
            self.file.write("colorPerVertex=\"false\" ")
        else:
            self.writeIndented("<Color color=\"", 1)
            for face in mesh.faces:
                if face.col:
                    c=face.col[0]
                    if self.verbose > 2:
                        print "Debug: face.col r=%d g=%d b=%d" % (c.r, c.g, c.b)
                    aColor = self.rgbToFS(c)
                    self.file.write("%s, " % aColor)
            self.file.write("\" />")
            self.writeIndented("\n",-1)

    def writeVertexColors(self, mesh):
        if self.writingcolor == 0:
            self.file.write("colorPerVertex=\"false\" ")
        else:
            self.writeIndented("<Color color=\"", 1)
            for i in xrange(len(mesh.verts)):
                c=self.getVertexColorByIndx(mesh,i)
                if self.verbose > 2:
                    print "Debug: vertex[%d].col r=%d g=%d b=%d" % (i, c.r, c.g, c.b)

                aColor = self.rgbToFS(c)
                self.file.write("%s, " % aColor)
            self.file.write("\" />")
            self.writeIndented("\n",-1)

    def writeMaterial(self, mat, matName):
        # look up material name, use it if available
        if self.matNames.has_key(matName):
            self.writeIndented("<Material USE=\"MA_%s\" />\n" % matName)
            self.matNames[matName]+=1
            return;

        self.matNames[matName]=1

        ambient = mat.amb/3
        diffuseR, diffuseG, diffuseB = mat.rgbCol[0], mat.rgbCol[1],mat.rgbCol[2]
        if world:
            ambi = world.getAmb()
            ambi0, ambi1, ambi2 = (ambi[0]*mat.amb)*2, (ambi[1]*mat.amb)*2, (ambi[2]*mat.amb)*2
        else:
            ambi0, ambi1, ambi2 = 0, 0, 0
        emisR, emisG, emisB = (diffuseR*mat.emit+ambi0)/2, (diffuseG*mat.emit+ambi1)/2, (diffuseB*mat.emit+ambi2)/2

        shininess = mat.hard/512.0
        specR = (mat.specCol[0]+0.001)/(1.25/(mat.getSpec()+0.001))
        specG = (mat.specCol[1]+0.001)/(1.25/(mat.getSpec()+0.001))
        specB = (mat.specCol[2]+0.001)/(1.25/(mat.getSpec()+0.001))
        transp = 1-mat.alpha
        matFlags = mat.getMode()
        if matFlags & Blender.Material.Modes['SHADELESS']:
          ambient = 1
          shine = 1
          specR = emitR = diffuseR
          specG = emitG = diffuseG
          specB = emitB = diffuseB
        self.writeIndented("<Material DEF=\"MA_%s\" " % matName, 1)
        self.file.write("diffuseColor=\"%s %s %s\" " % (round(diffuseR,self.cp), round(diffuseG,self.cp), round(diffuseB,self.cp)))
        self.file.write("specularColor=\"%s %s %s\" " % (round(specR,self.cp), round(specG,self.cp), round(specB,self.cp)))
        self.file.write("emissiveColor=\"%s %s %s\" \n" % (round(emisR,self.cp), round(emisG,self.cp), round(emisB,self.cp)))
        self.writeIndented("ambientIntensity=\"%s\" " % (round(ambient,self.cp)))
        self.file.write("shininess=\"%s\" " % (round(shininess,self.cp)))
        self.file.write("transparency=\"%s\" />" % (round(transp,self.cp)))
        self.writeIndented("\n",-1)

    def writeImageTexture(self, image):
        name = image.name
        filename = image.filename.split('/')[-1].split('\\')[-1]
        if self.texNames.has_key(name):
            self.writeIndented("<ImageTexture USE=\"%s\" />\n" % self.cleanStr(name))
            self.texNames[name] += 1
            return
        else:
            self.writeIndented("<ImageTexture DEF=\"%s\" " % self.cleanStr(name), 1)
            self.file.write("url=\"%s\" />" % name)
            self.writeIndented("\n",-1)
            self.texNames[name] = 1

    def writeBackground(self):
        if world:	worldname = world.name
        else:		return
        blending = world.getSkytype()	
        grd = world.getHor()
        grd0, grd1, grd2 = grd[0], grd[1], grd[2]
        sky = world.getZen()
        sky0, sky1, sky2 = sky[0], sky[1], sky[2]
        mix0, mix1, mix2 = grd[0]+sky[0], grd[1]+sky[1], grd[2]+sky[2]
        mix0, mix1, mix2 = mix0/2, mix1/2, mix2/2
        self.file.write("<Background ")
        if worldname not in self.namesStandard:
            self.file.write("DEF=\"%s\" " % self.secureName(worldname))
        # No Skytype - just Hor color
        if blending == 0:
            self.file.write("groundColor=\"%s %s %s\" " % (round(grd0,self.cp), round(grd1,self.cp), round(grd2,self.cp)))
            self.file.write("skyColor=\"%s %s %s\" " % (round(grd0,self.cp), round(grd1,self.cp), round(grd2,self.cp)))
        # Blend Gradient
        elif blending == 1:
            self.file.write("groundColor=\"%s %s %s, " % (round(grd0,self.cp), round(grd1,self.cp), round(grd2,self.cp)))
            self.file.write("%s %s %s\" groundAngle=\"1.57, 1.57\" " %(round(mix0,self.cp), round(mix1,self.cp), round(mix2,self.cp)))
            self.file.write("skyColor=\"%s %s %s, " % (round(sky0,self.cp), round(sky1,self.cp), round(sky2,self.cp)))
            self.file.write("%s %s %s\" skyAngle=\"1.57, 1.57\" " %(round(mix0,self.cp), round(mix1,self.cp), round(mix2,self.cp)))
        # Blend+Real Gradient Inverse
        elif blending == 3:
            self.file.write("groundColor=\"%s %s %s, " % (round(sky0,self.cp), round(sky1,self.cp), round(sky2,self.cp)))
            self.file.write("%s %s %s\" groundAngle=\"1.57, 1.57\" " %(round(mix0,self.cp), round(mix1,self.cp), round(mix2,self.cp)))
            self.file.write("skyColor=\"%s %s %s, " % (round(grd0,self.cp), round(grd1,self.cp), round(grd2,self.cp)))
            self.file.write("%s %s %s\" skyAngle=\"1.57, 1.57\" " %(round(mix0,self.cp), round(mix1,self.cp), round(mix2,self.cp)))
        # Paper - just Zen Color
        elif blending == 4:
            self.file.write("groundColor=\"%s %s %s\" " % (round(sky0,self.cp), round(sky1,self.cp), round(sky2,self.cp)))
            self.file.write("skyColor=\"%s %s %s\" " % (round(sky0,self.cp), round(sky1,self.cp), round(sky2,self.cp)))
        # Blend+Real+Paper - komplex gradient
        elif blending == 7:
            self.writeIndented("groundColor=\"%s %s %s, " % (round(sky0,self.cp), round(sky1,self.cp), round(sky2,self.cp)))
            self.writeIndented("%s %s %s\" groundAngle=\"1.57, 1.57\" " %(round(grd0,self.cp), round(grd1,self.cp), round(grd2,self.cp)))
            self.writeIndented("skyColor=\"%s %s %s, " % (round(sky0,self.cp), round(sky1,self.cp), round(sky2,self.cp)))
            self.writeIndented("%s %s %s\" skyAngle=\"1.57, 1.57\" " %(round(grd0,self.cp), round(grd1,self.cp), round(grd2,self.cp)))
        # Any Other two colors
        else:
            self.file.write("groundColor=\"%s %s %s\" " % (round(grd0,self.cp), round(grd1,self.cp), round(grd2,self.cp)))
            self.file.write("skyColor=\"%s %s %s\" " % (round(sky0,self.cp), round(sky1,self.cp), round(sky2,self.cp)))
        alltexture = len(worldmat)
        for i in xrange(alltexture):
            namemat = worldmat[i].getName()
            pic = worldmat[i].getImage()	
            if (namemat == "back") and (pic != None):
                self.file.write("\n\tbackUrl=\"%s\" " % str(pic.getName()))
            elif (namemat == "bottom") and (pic != None):
                self.writeIndented("bottomUrl=\"%s\" " % str(pic.getName()))
            elif (namemat == "front") and (pic != None):
                self.writeIndented("frontUrl=\"%s\" " % str(pic.getName()))
            elif (namemat == "left") and (pic != None):
                self.writeIndented("leftUrl=\"%s\" " % str(pic.getName()))
            elif (namemat == "right") and (pic != None):
                self.writeIndented("rightUrl=\"%s\" " % str(pic.getName()))
            elif (namemat == "top") and (pic != None):
                self.writeIndented("topUrl=\"%s\" " % str(pic.getName()))
        self.writeIndented("/>\n\n")

##########################################################
# export routine
##########################################################

    def export(self, scene, world, worldmat):
        print "Info: starting X3D export to " + self.filename + "..."
        self.writeHeader()
        self.writeScript()
        self.writeNavigationInfo(scene)
        self.writeBackground()
        self.writeFog()
        self.proto = 0
        allObj = []
        if ARG == 'selected':
            allObj = list(scene.objects.context)
        else:
            allObj = list(scene.objects)
            self.writeInline()
        for thisObj in allObj:
            try:
                objType=thisObj.type
                objName=thisObj.name
                self.matonly = 0
                if objType == "Camera":
                    self.writeViewpoint(thisObj)
                elif objType == "Mesh":
                    self.writeIndexedFaceSet(thisObj, normals = 0)
                elif objType == "Lamp":
                    lmpName= thisObj.data
                    lmpType=lmpName.getType()
                    if lmpType == Lamp.Types.Lamp:
                        self.writePointLight(thisObj, lmpName)
                    elif lmpType == Lamp.Types.Spot:
                        self.writeSpotLight(thisObj, lmpName)
                    elif lmpType == Lamp.Types.Sun:
                        self.writeDirectionalLight(thisObj, lmpName)
                    else:
                        self.writeDirectionalLight(thisObj, lmpName)
                elif objType == "Empty" and objName != "Empty":
                    self.writeNode(thisObj)
                else:
                    #print "Info: Ignoring [%s], object type [%s] not handle yet" % (object.name,object.getType())
                    print ""
            except AttributeError:
                print "Error: Unable to get type info for %s" % thisObj.getName()
        if ARG != 'selected':
            self.writeScript()
        self.file.write("\n</Scene>\n</X3D>")
        self.cleanup()
        
##########################################################
# Utility methods
##########################################################

    def cleanup(self):
        self.file.close()
        self.texNames={}
        self.matNames={}
        self.indentLevel=0
        print "Info: finished X3D export to %s\n" % self.filename

    def cleanStr(self, name, prefix='rsvd_'):
        """cleanStr(name,prefix) - try to create a valid VRML DEF name from object name"""

        newName=name[:]
        if len(newName) == 0:
            self.nNodeID+=1
            return "%s%d" % (prefix, self.nNodeID)
        
        if newName in self.namesReserved:
            newName='%s%s' % (prefix,newName)
        
        if newName[0].isdigit():
            newName='%s%s' % ('_',newName)

        for bad in [' ','"','#',"'",',','.','[','\\',']','{','}']:
            newName=newName.replace(bad,'_')
        return newName

    def countIFSSetsNeeded(self, mesh, imageMap, sided, vColors):
        """
        countIFFSetsNeeded() - should look at a blender mesh to determine
        how many VRML IndexFaceSets or IndexLineSets are needed.  A
        new mesh created under the following conditions:
        
         o - split by UV Textures / one per mesh
         o - split by face, one sided and two sided
         o - split by smooth and flat faces
         o - split when faces only have 2 vertices * needs to be an IndexLineSet
        """
        
        imageNameMap={}
        faceMap={}
        nFaceIndx=0
        
        for face in mesh.faces:
            sidename='';
            if (face.mode & NMesh.FaceModes.TWOSIDE) == NMesh.FaceModes.TWOSIDE:
                sidename='two'
            else:
                sidename='one'
            
            if sided.has_key(sidename):
                sided[sidename]+=1
            else:
                sided[sidename]=1

            if face.image:
                faceName="%s_%s" % (face.image.name, sidename);

                try:
                    imageMap[faceName].append(face)
                except:
                    imageMap[faceName]=[face.image.name,sidename,face]

        if self.verbose > 2:
            for faceName in imageMap.iterkeys():
                ifs=imageMap[faceName]
                print "Debug: faceName=%s image=%s, solid=%s facecnt=%d" % \
                      (faceName, ifs[0], ifs[1], len(ifs)-2)

        return len(imageMap)
    
    def faceToString(self,face):

        print "Debug: face.flag=0x%x (bitflags)" % face.flag
        if face.flag & NMesh.FaceFlags.SELECT == NMesh.FaceFlags.SELECT:
            print "Debug: face.flag.SELECT=true"

        print "Debug: face.mode=0x%x (bitflags)" % face.mode
        if (face.mode & NMesh.FaceModes.TWOSIDE) == NMesh.FaceModes.TWOSIDE:
            print "Debug: face.mode twosided"

        print "Debug: face.transp=0x%x (enum)" % face.transp
        if face.transp == NMesh.FaceTranspModes.SOLID:
            print "Debug: face.transp.SOLID"

        if face.image:
            print "Debug: face.image=%s" % face.image.name
        print "Debug: face.materialIndex=%d" % face.materialIndex 

    def getVertexColorByIndx(self, mesh, indx):
        c = None
        for face in mesh.faces:
            j=0
            for vertex in face.v:
                if vertex.index == indx:
                    c=face.col[j]
                    break
                j=j+1
            if c: break
        return c

    def meshToString(self,mesh):
        print "Debug: mesh.hasVertexUV=%d" % mesh.hasVertexUV()
        print "Debug: mesh.hasFaceUV=%d" % mesh.hasFaceUV()
        print "Debug: mesh.hasVertexColours=%d" % mesh.hasVertexColours()
        print "Debug: mesh.verts=%d" % len(mesh.verts)
        print "Debug: mesh.faces=%d" % len(mesh.faces)
        print "Debug: mesh.materials=%d" % len(mesh.materials)

    def rgbToFS(self, c):
        s="%s %s %s" % (
            round(c.r/255.0,self.cp),
            round(c.g/255.0,self.cp),
            round(c.b/255.0,self.cp))
        return s

    def computeDirection(self, ob):
        x,y,z=(0,-1.0,0) # point down
        ax,ay,az = (ob.RotX,ob.RotZ,ob.RotY)

        # rot X
        x1=x
        y1=y*math.cos(ax)-z*math.sin(ax)
        z1=y*math.sin(ax)+z*math.cos(ax)

        # rot Y
        x2=x1*math.cos(ay)+z1*math.sin(ay)
        y2=y1
        z2=z1*math.cos(ay)-x1*math.sin(ay)

        # rot Z
        x3=x2*math.cos(az)-y2*math.sin(az)
        y3=x2*math.sin(az)+y2*math.cos(az)
        z3=z2

        return [x3,y3,z3]
        

    # swap Y and Z to handle axis difference between Blender and VRML
    #------------------------------------------------------------------------
    def rotatePointForVRML(self, v):
        x = v[0]
        y = v[2]
        z = -v[1]
        
        vrmlPoint=[x, y, z]
        return vrmlPoint

    # For writing well formed VRML code
    #------------------------------------------------------------------------
    def writeIndented(self, s, inc=0):
        if inc < 1:
            self.indentLevel = self.indentLevel + inc

        spaces=""
        for x in xrange(self.indentLevel):
            spaces = spaces + "\t"
        self.file.write(spaces + s)

        if inc > 0:
            self.indentLevel = self.indentLevel + inc

    # Converts a Euler to three new Quaternions
    # Angles of Euler are passed in as radians
    #------------------------------------------------------------------------
    def eulerToQuaternions(self, x, y, z):
        Qx = [math.cos(x/2), math.sin(x/2), 0, 0]
        Qy = [math.cos(y/2), 0, math.sin(y/2), 0]
        Qz = [math.cos(z/2), 0, 0, math.sin(z/2)]
        
        quaternionVec=[Qx,Qy,Qz]
        return quaternionVec
    
    # Multiply two Quaternions together to get a new Quaternion
    #------------------------------------------------------------------------
    def multiplyQuaternions(self, Q1, Q2):
        result = [((Q1[0] * Q2[0]) - (Q1[1] * Q2[1]) - (Q1[2] * Q2[2]) - (Q1[3] * Q2[3])),
                  ((Q1[0] * Q2[1]) + (Q1[1] * Q2[0]) + (Q1[2] * Q2[3]) - (Q1[3] * Q2[2])),
                  ((Q1[0] * Q2[2]) + (Q1[2] * Q2[0]) + (Q1[3] * Q2[1]) - (Q1[1] * Q2[3])),
                  ((Q1[0] * Q2[3]) + (Q1[3] * Q2[0]) + (Q1[1] * Q2[2]) - (Q1[2] * Q2[1]))]
        
        return result
    
    # Convert a Quaternion to an Angle Axis (ax, ay, az, angle)
    # angle is in radians
    #------------------------------------------------------------------------
    def quaternionToAngleAxis(self, Qf):
        scale = math.pow(Qf[1],2) + math.pow(Qf[2],2) + math.pow(Qf[3],2)
        ax = Qf[1]
        ay = Qf[2]
        az = Qf[3]

        if scale > .0001:
            ax/=scale
            ay/=scale
            az/=scale
        
        angle = 2 * math.acos(Qf[0])
        
        result = [ax, ay, az, angle]
        return result

##########################################################
# Callbacks, needed before Main
##########################################################

def select_file(filename):
  if pytinst == 1:
    if sys.exists(filename) and _safeOverwrite:
      result = Draw.PupMenu("File Already Exists, Overwrite?%t|Yes%x1|No%x0")
      if(result != 1):
        return

  if not filename.endswith(extension):
    filename += extension

  wrlexport=VRML2Export(filename)
  wrlexport.export(scene, world, worldmat)

def createWRLPath():
  filename = Blender.Get('filename')
  print filename
  
  if filename.find('.') != -1:
    filename = filename.split('.')[0]
    filename += extension
    print filename

  return filename

#########################################################
# main routine
#########################################################

try:
    ARG = __script__['arg'] # user selected argument
except:
    print "older version"

if Blender.Get('version') < 235:
  print "Warning: X3D export failed, wrong blender version!"
  print " You aren't running blender version 2.35 or greater"
  print " download a newer version from http://blender3d.org/"
else:
  if ARG == 'comp':
    from gzip import *
    extension=".x3dz"
  else:
    extension=".x3d"
  Blender.Window.FileSelector(select_file,"Export X3D",createWRLPath())

