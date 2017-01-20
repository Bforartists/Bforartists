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


import bpy
import time
import copy

from mathutils import *
from math import pi,sin,degrees,radians,atan2,copysign,cos,acos
from random import random,uniform,seed,choice,getstate,setstate
from bpy.props import *
from collections import deque

# Initialise the split error and axis vectors
splitError = 0.0
zAxis = Vector((0,0,1))
yAxis = Vector((0,1,0))
xAxis = Vector((1,0,0))

# This class will contain a part of the tree which needs to be extended and the required tree parameters
class stemSpline:
    def __init__(self,spline,curvature,curvatureV,segments,maxSegs,segLength,childStems,stemRadStart,stemRadEnd,splineNum):
        self.spline = spline
        self.p = spline.bezier_points[-1]
        self.curv = curvature
        self.curvV = curvatureV
        self.seg = segments
        self.segMax = maxSegs
        self.segL = segLength
        self.children = childStems
        self.radS = stemRadStart
        self.radE = stemRadEnd
        self.splN = splineNum
    # This method determines the quaternion of the end of the spline
    def quat(self):
        if len(self.spline.bezier_points) == 1:
            return ((self.spline.bezier_points[-1].handle_right - self.spline.bezier_points[-1].co).normalized()).to_track_quat('Z','Y')
        else:
            return ((self.spline.bezier_points[-1].co - self.spline.bezier_points[-2].co).normalized()).to_track_quat('Z','Y')
    # Determine the declination
    def dec(self):
        tempVec = zAxis.copy()
        tempVec.rotate(self.quat())
        return zAxis.angle(tempVec)
    # Update the end of the spline and increment the segment count
    def updateEnd(self):
        self.p = self.spline.bezier_points[-1]
        self.seg += 1
    # Determine the spread angle for a split
    def spreadAng(self):
        return radians(choice([-1,1])*(20 + 0.75*(30 + abs(degrees(self.dec()) - 90))*random()**2))
    # Determine the splitting angle for a split
    def splitAngle(self,splitAng,splitAngV):
        return max(0,splitAng+uniform(-splitAngV,splitAngV)-self.dec())
    # This is used to change the the curvature per segment of the spline
    def curvAdd(self,curvD):
        self.curv += curvD

# This class contains the data for a point where a new branch will sprout
class childPoint:
    def __init__(self,coords,quat,radiusPar,offset,lengthPar,parBone):
        self.co = coords
        self.quat = quat
        self.radiusPar = radiusPar
        self.offset = offset
        self.lengthPar = lengthPar
        self.parBone = parBone


# This function calculates the shape ratio as defined in the paper
def shapeRatio(shape,ratio,pruneWidthPeak=0.0,prunePowerHigh=0.0,prunePowerLow=0.0):
    if shape == 0:
        return 0.2 + 0.8*ratio
    elif shape == 1:
        return 0.2 + 0.8*sin(pi*ratio)
    elif shape == 2:
        return 0.2 + 0.8*sin(0.5*pi*ratio)
    elif shape == 3:
        return 1.0
    elif shape == 4:
        return 0.5 + 0.5*ratio
    elif shape == 5:
        if ratio <= 0.7:
            return ratio/0.7
        else:
            return (1.0 - ratio)/0.3
    elif shape == 6:
        return 1.0 - 0.8*ratio
    elif shape == 7:
        if ratio <= 0.7:
            return 0.5 + 0.5*ratio/0.7
        else:
            return 0.5 + 0.5*(1.0 - ratio)/0.3
    elif shape == 8:
        if (ratio < (1 - pruneWidthPeak)) and (ratio > 0.0):
            return ((ratio/(1 - pruneWidthPeak))**prunePowerHigh)
        elif (ratio >= (1 - pruneWidthPeak)) and (ratio < 1.0):
            return (((1 - ratio)/pruneWidthPeak)**prunePowerLow)
        else:
            return 0.0

# This function determines the actual number of splits at a given point using the global error
def splits(n):
    global splitError
    nEff = round(n + splitError,0)
    splitError -= (nEff - n)
    return int(nEff)

# Determine the declination from a given quaternion
def declination(quat):
    tempVec = zAxis.copy()
    tempVec.rotate(quat)
    tempVec.normalize()
    return degrees(acos(tempVec.z))

# Determine the length of a child stem
def lengthChild(lMax,offset,lPar,shape=False,lBase=None):
    if shape:
        return lPar*lMax*shapeRatio(shape,(lPar - offset) / max((lPar - lBase), 1e-6))
    else:
        return lMax*(lPar - 0.6*offset)

# Find the actual downAngle taking into account the special case
def downAngle(downAng,downAngV,lPar=None,offset=None,lBase=None):
    if downAngV < 0:
        return downAng + (uniform(-downAngV,downAngV)*(1 - 2*shapeRatio(0,(lPar - offset) / max((lPar - lBase), 1e-6))))
    else:
        return downAng + uniform(-downAngV,downAngV)

# Returns the rotation matrix equivalent to i rotations by 2*pi/(n+1)
def splitRotMat(n,i):
    return Matrix.Rotation(2*i*pi/(n+1),3,'Z')

# Returns the split angle
def angleSplit(splitAng,splitAngV,quat):
    return max(0,splitAng+uniform(-splitAngV,splitAngV)-declination(quat))

# Returns number of stems a stem will sprout
def stems(stemsMax,lPar,offset,lChild=False,lChildMax=None):
    if lChild:
        return stemsMax*(0.2 + 0.8*(lChild/lPar)/lChildMax)
    else:
        return stemsMax*(1.0 - 0.5*offset/lPar)

# Returns the spreading angle
def spreadAng(dec):
    return radians(choice([-1,1])*(20 + 0.75*(30 + abs(dec - 90))*random()**2))

# Determines the angle of upward rotation of a segment due to attractUp
def curveUp(attractUp,quat,curveRes):
    tempVec = yAxis.copy()
    tempVec.rotate(quat)
    tempVec.normalize()
    return attractUp*radians(declination(quat))*abs(tempVec.z)/curveRes

# Evaluate a bezier curve for the parameter 0<=t<=1 along its length
def evalBez(p1,h1,h2,p2,t):
    return ((1-t)**3)*p1 + (3*t*(1-t)**2)*h1 + (3*(t**2)*(1-t))*h2 + (t**3)*p2

# Evaluate the unit tangent on a bezier curve for t
def evalBezTan(p1,h1,h2,p2,t):
    return ((-3*(1-t)**2)*p1 + (-6*t*(1-t) + 3*(1-t)**2)*h1 + (-3*(t**2) + 6*t*(1-t))*h2 + (3*t**2)*p2).normalized()

# Determine the range of t values along a splines length where child stems are formed
def findChildPoints(stemList,numChild):
    numPoints = sum([len(n.spline.bezier_points) for n in stemList])
    numSplines = len(stemList)
    numSegs = numPoints - numSplines
    numPerSeg = numChild/numSegs
    numMain = round(numPerSeg*stemList[0].segMax,0)
    return [(a+1)/(numMain) for a in range(int(numMain))]

# Find the coordinates, quaternion and radius for each t on the stem
def interpStem(stem,tVals,lPar,parRad):
    tempList = deque()
    addpoint = tempList.append
    checkVal = (stem.segMax - len(stem.spline.bezier_points) + 1)/stem.segMax
    points = stem.spline.bezier_points
    numPoints = len(stem.spline.bezier_points)
    # Loop through all the parametric values to be determined
    for t in tVals:
        if (t >= checkVal) and (t < 1.0):
            scaledT = (t - checkVal) / max(tVals[-1] - checkVal, 1e-6)
            length = (numPoints-1)*t#scaledT
            index = int(length)
            if scaledT == 1.0:
                coord = points[-1].co
                quat = (points[-1].handle_right - points[-1].co).to_track_quat('Z','Y')
                radius = parRad#points[-2].radius
            else:
                tTemp = length - index
                coord = evalBez(points[index].co,points[index].handle_right,points[index+1].handle_left,points[index+1].co,tTemp)
                quat = (evalBezTan(points[index].co,points[index].handle_right,points[index+1].handle_left,points[index+1].co,tTemp)).to_track_quat('Z','Y')
                radius = (1-tTemp)*points[index].radius + tTemp*points[index+1].radius # Not sure if this is the parent radius at the child point or parent start radius
            addpoint(childPoint(coord,quat,(parRad, radius),t*lPar,lPar,'bone'+(str(stem.splN).rjust(3,'0'))+'.'+(str(index).rjust(3,'0'))))
    return tempList

# Convert a list of degrees to radians
def toRad(list):
    return [radians(a) for a in list]

# This is the function which extends (or grows) a given stem.
def growSpline(stem,numSplit,splitAng,splitAngV,splineList,attractUp,hType,splineToBone):
    # First find the current direction of the stem
    dir = stem.quat()
    # If the stem splits, we need to add new splines etc
    if numSplit > 0:
        # Get the curve data
        cuData = stem.spline.id_data.name
        cu = bpy.data.curves[cuData]
        # Now for each split add the new spline and adjust the growth direction
        for i in range(numSplit):
            newSpline = cu.splines.new('BEZIER')
            newPoint = newSpline.bezier_points[-1]
            (newPoint.co,newPoint.handle_left_type,newPoint.handle_right_type) = (stem.p.co,'VECTOR','VECTOR')
            newPoint.radius = stem.radS*(1 - stem.seg/stem.segMax) + stem.radE*(stem.seg/stem.segMax)
            
            # Here we make the new "sprouting" stems diverge from the current direction
            angle = stem.splitAngle(splitAng,splitAngV)
            divRotMat = Matrix.Rotation(angle + stem.curv + uniform(-stem.curvV,stem.curvV),3,'X')#CurveUP should go after curve is applied
            dirVec = zAxis.copy()
            dirVec.rotate(divRotMat)
            dirVec.rotate(splitRotMat(numSplit,i+1))
            dirVec.rotate(dir)
            
            # if attractUp != 0.0: # Shouldn't have a special case as this will mess with random number generation
            divRotMat = Matrix.Rotation(angle + stem.curv + uniform(-stem.curvV,stem.curvV),3,'X')
            dirVec = zAxis.copy()
            dirVec.rotate(divRotMat)
            dirVec.rotate(splitRotMat(numSplit,i+1))
            dirVec.rotate(dir)
            
            #Different version of the commented code above. We could use the inbuilt vector rotations but given this is a special case, it can be quicker to initialise the vector to the correct value.
#            angle = stem.splitAngle(splitAng,splitAngV)
#            curveUpAng = curveUp(attractUp,dir,stem.segMax)
#            angleX = angle + stem.curv + uniform(-stem.curvV,stem.curvV) - curveUpAng
#            angleZ = 2*i*pi/(numSplit+1)
#            dirVec = Vector((sin(angleX)*sin(angleZ), -sin(angleX)*cos(angleZ), cos(angleX)))
#            dirVec.rotate(dir)

            # Spread the stem out in a random fashion
            spreadMat = Matrix.Rotation(spreadAng(degrees(dirVec.z)),3,'Z')
            dirVec.rotate(spreadMat)
            # Introduce upward curvature
            upRotAxis = xAxis.copy()
            upRotAxis.rotate(dirVec.to_track_quat('Z','Y'))
            curveUpAng = curveUp(attractUp,dirVec.to_track_quat('Z','Y'),stem.segMax)
            upRotMat = Matrix.Rotation(-curveUpAng,3,upRotAxis)
            dirVec.rotate(upRotMat)
            # Make the growth vec the length of a stem segment
            dirVec.normalize()
            dirVec *= stem.segL

            # Get the end point position
            end_co = stem.p.co.copy()

            # Add the new point and adjust its coords, handles and radius
            newSpline.bezier_points.add()
            newPoint = newSpline.bezier_points[-1]
            (newPoint.co,newPoint.handle_left_type,newPoint.handle_right_type) = (end_co + dirVec,hType,hType)
            newPoint.radius = stem.radS*(1 - (stem.seg + 1)/stem.segMax) + stem.radE*((stem.seg + 1)/stem.segMax)
            # If this isn't the last point on a stem, then we need to add it to the list of stems to continue growing
            if stem.seg != stem.segMax:
                splineList.append(stemSpline(newSpline,stem.curv-angle/(stem.segMax-stem.seg),stem.curvV,stem.seg+1,stem.segMax,stem.segL,stem.children,stem.radS,stem.radE,len(cu.splines)-1))
                splineToBone.append('bone'+(str(stem.splN)).rjust(3,'0')+'.'+(str(len(stem.spline.bezier_points)-2)).rjust(3,'0'))
        # The original spline also needs to keep growing so adjust its direction too
        angle = stem.splitAngle(splitAng,splitAngV)
        divRotMat = Matrix.Rotation(angle + stem.curv + uniform(-stem.curvV,stem.curvV),3,'X')
        dirVec = zAxis.copy()
        dirVec.rotate(divRotMat)
        dirVec.rotate(dir)
        spreadMat = Matrix.Rotation(spreadAng(degrees(dirVec.z)),3,'Z')
        dirVec.rotate(spreadMat)
    else:
        # If there are no splits then generate the growth direction without accounting for spreading of stems
        dirVec = zAxis.copy()
        #curveUpAng = curveUp(attractUp,dir,stem.segMax)
        divRotMat = Matrix.Rotation(stem.curv + uniform(-stem.curvV,stem.curvV),3,'X')
        dirVec.rotate(divRotMat)
        #dirVec = Vector((0,-sin(stem.curv - curveUpAng),cos(stem.curv - curveUpAng)))
        dirVec.rotate(dir)
    upRotAxis = xAxis.copy()
    upRotAxis.rotate(dirVec.to_track_quat('Z','Y'))
    curveUpAng = curveUp(attractUp,dirVec.to_track_quat('Z','Y'),stem.segMax)
    upRotMat = Matrix.Rotation(-curveUpAng,3,upRotAxis)
    dirVec.rotate(upRotMat)
    dirVec.normalize()
    dirVec *= stem.segL

    # Get the end point position
    end_co = stem.p.co.copy()

    stem.spline.bezier_points.add()
    newPoint = stem.spline.bezier_points[-1]
    (newPoint.co,newPoint.handle_left_type,newPoint.handle_right_type) = (end_co + dirVec,hType,hType)
    newPoint.radius = stem.radS*(1 - (stem.seg + 1)/stem.segMax) + stem.radE*((stem.seg + 1)/stem.segMax)
    # There are some cases where a point cannot have handles as VECTOR straight away, set these now.
    if numSplit != 0:
        tempPoint = stem.spline.bezier_points[-2]
        (tempPoint.handle_left_type,tempPoint.handle_right_type) = ('VECTOR','VECTOR')
    if len(stem.spline.bezier_points) == 2:
        tempPoint = stem.spline.bezier_points[0]
        (tempPoint.handle_left_type,tempPoint.handle_right_type) = ('VECTOR','VECTOR')
    # Update the last point in the spline to be the newly added one
    stem.updateEnd()
    #return splineList

def genLeafMesh(leafScale,leafScaleX,loc,quat,index,downAngle,downAngleV,rotate,rotateV,oldRot,bend,leaves, leafShape):
    if leafShape == 'hex':
        verts = [Vector((0,0,0)),Vector((0.5,0,1/3)),Vector((0.5,0,2/3)),Vector((0,0,1)),Vector((-0.5,0,2/3)),Vector((-0.5,0,1/3))]
        edges = [[0,1],[1,2],[2,3],[3,4],[4,5],[5,0],[0,3]]
        faces = [[0,1,2,3],[0,3,4,5]]
    elif leafShape == 'rect':
        verts = [Vector((1,0,0)),Vector((1,0,1)),Vector((-1,0,1)),Vector((-1,0,0))]
        edges = [[0,1],[1,2],[2,3],[3,0]]
        faces = [[0,1,2,3],]
    #faces = [[0,1,5],[1,2,4,5],[2,3,4]]

    vertsList = []
    facesList = []

    # If the special -ve flag is used we need a different rotation of the leaf geometry
    if leaves < 0:
        rotMat = Matrix.Rotation(oldRot,3,'Y')
        oldRot += rotate/abs(leaves)
    else:
        oldRot += rotate+uniform(-rotateV,rotateV)
        downRotMat = Matrix.Rotation(downAngle+uniform(-downAngleV,downAngleV),3,'X')
        rotMat = Matrix.Rotation(oldRot,3,'Z')

    normal = yAxis.copy()
    #dirVec = zAxis.copy()
    orientationVec = zAxis.copy()

    # If the bending of the leaves is used we need to rotated them differently
    if (bend != 0.0) and (leaves >= 0):
#        normal.rotate(downRotMat)
#        orientationVec.rotate(downRotMat)
#
#        normal.rotate(rotMat)
#        orientationVec.rotate(rotMat)

        normal.rotate(quat)
        orientationVec.rotate(quat)

        thetaPos = atan2(loc.y,loc.x)
        thetaBend = thetaPos - atan2(normal.y,normal.x)
        rotateZ = Matrix.Rotation(bend*thetaBend,3,'Z')
        normal.rotate(rotateZ)
        orientationVec.rotate(rotateZ)

        phiBend = atan2((normal.xy).length,normal.z)
        orientation = atan2(orientationVec.y,orientationVec.x)
        rotateZOrien = Matrix.Rotation(orientation,3,'X')

        rotateX = Matrix.Rotation(bend*phiBend,3,'Z')

        rotateZOrien2 = Matrix.Rotation(-orientation,3,'X')

    # For each of the verts we now rotate and scale them, then append them to the list to be added to the mesh
    for v in verts:
        
        v.z *= leafScale
        v.x *= leafScaleX*leafScale

        if leaves > 0:
            v.rotate(downRotMat)

        v.rotate(rotMat)
        v.rotate(quat)

        if (bend != 0.0) and (leaves > 0):
            # Correct the rotation
            v.rotate(rotateZ)
            v.rotate(rotateZOrien)
            v.rotate(rotateX)
            v.rotate(rotateZOrien2)

        #v.rotate(quat)
    for v in verts:
        v += loc
        vertsList.append([v.x,v.y,v.z])

    for f in faces:
        facesList.append([f[0] + index,f[1] + index,f[2] + index,f[3] + index])
    return vertsList,facesList,oldRot


def create_armature(armAnim, childP, cu, frameRate, leafMesh, leafObj, leafShape, leaves, levelCount, splineToBone,
                    treeOb, windGust, windSpeed):
    arm = bpy.data.armatures.new('tree')
    armOb = bpy.data.objects.new('treeArm', arm)
    bpy.context.scene.objects.link(armOb)
    # Create a new action to store all animation
    newAction = bpy.data.actions.new(name='windAction')
    armOb.animation_data_create()
    armOb.animation_data.action = newAction
    arm.draw_type = 'STICK'
    arm.use_deform_delay = True
    # Add the armature modifier to the curve
    armMod = treeOb.modifiers.new('windSway', 'ARMATURE')
    #armMod.use_apply_on_spline = True
    armMod.object = armOb
    armMod.use_bone_envelopes = True
    armMod.use_vertex_groups = False # curves don't have vertex groups (yet)
    # If there are leaves then they need a modifier
    if leaves:
        armMod = leafObj.modifiers.new('windSway', 'ARMATURE')
        armMod.object = armOb
        armMod.use_bone_envelopes = True
        armMod.use_vertex_groups = True 
    # Make sure all objects are deselected (may not be required?)
    for ob in bpy.data.objects:
        ob.select = False

    # Set the armature as active and go to edit mode to add bones
    bpy.context.scene.objects.active = armOb
    bpy.ops.object.mode_set(mode='EDIT')
    masterBones = []
    offsetVal = 0
    # For all the splines in the curve we need to add bones at each bezier point
    for i, parBone in enumerate(splineToBone):
        s = cu.splines[i]
        b = None
        # Get some data about the spline like length and number of points
        numPoints = len(s.bezier_points) - 1
        splineL = numPoints * ((s.bezier_points[0].co - s.bezier_points[1].co).length)
        # Set the random phase difference of the animation
        bxOffset = uniform(0, 2 * pi)
        byOffset = uniform(0, 2 * pi)
        # Set the phase multiplier for the spline
        bMult = (s.bezier_points[0].radius / max(splineL, 1e-6)) * (1 / 15) * (1 / frameRate)
        # For all the points in the curve (less the last) add a bone and name it by the spline it will affect
        for n in range(numPoints):
            oldBone = b
            boneName = 'bone' + (str(i)).rjust(3, '0') + '.' + (str(n)).rjust(3, '0')
            b = arm.edit_bones.new(boneName)
            b.head = s.bezier_points[n].co
            b.tail = s.bezier_points[n + 1].co

            b.head_radius = s.bezier_points[n].radius
            b.tail_radius = s.bezier_points[n + 1].radius
            b.envelope_distance = 0.001  #0.001

            # If there are leaves then we need a new vertex group so they will attach to the bone
            if (len(levelCount) > 1) and (i >= levelCount[-2]) and leafObj:
                leafObj.vertex_groups.new(boneName)
            elif (len(levelCount) == 1) and leafObj:
                leafObj.vertex_groups.new(boneName)
            # If this is first point of the spline then it must be parented to the level above it
            if n == 0:
                if parBone:
                    b.parent = arm.edit_bones[parBone]
                #                            if len(parBone) > 11:
                #                                b.use_connect = True
            # Otherwise, we need to attach it to the previous bone in the spline
            else:
                b.parent = oldBone
                b.use_connect = True
            # If there isn't a previous bone then it shouldn't be attached
            if not oldBone:
                b.use_connect = False
            #tempList.append(b)

            # Add the animation to the armature if required
            if armAnim:
                # Define all the required parameters of the wind sway by the dimension of the spline
                a0 = 4 * splineL * (1 - n / (numPoints + 1)) / max(s.bezier_points[n].radius, 1e-6)
                a1 = (windSpeed / 50) * a0
                a2 = (windGust / 50) * a0 + a1 / 2

                # Add new fcurves for each sway  as well as the modifiers
                swayX = armOb.animation_data.action.fcurves.new('pose.bones["' + boneName + '"].rotation_euler', 0)
                swayY = armOb.animation_data.action.fcurves.new('pose.bones["' + boneName + '"].rotation_euler', 2)

                swayXMod1 = swayX.modifiers.new(type='FNGENERATOR')
                swayXMod2 = swayX.modifiers.new(type='FNGENERATOR')

                swayYMod1 = swayY.modifiers.new(type='FNGENERATOR')
                swayYMod2 = swayY.modifiers.new(type='FNGENERATOR')

                # Set the parameters for each modifier
                swayXMod1.amplitude = radians(a1) / numPoints
                swayXMod1.phase_offset = bxOffset
                swayXMod1.phase_multiplier = degrees(bMult)

                swayXMod2.amplitude = radians(a2) / numPoints
                swayXMod2.phase_offset = 0.7 * bxOffset
                swayXMod2.phase_multiplier = 0.7 * degrees(
                    bMult)  # This shouldn't have to be in degrees but it looks much better in animation
                swayXMod2.use_additive = True

                swayYMod1.amplitude = radians(a1) / numPoints
                swayYMod1.phase_offset = byOffset
                swayYMod1.phase_multiplier = degrees(
                    bMult)  # This shouldn't have to be in degrees but it looks much better in animation

                swayYMod2.amplitude = radians(a2) / numPoints
                swayYMod2.phase_offset = 0.7 * byOffset
                swayYMod2.phase_multiplier = 0.7 * degrees(
                    bMult)  # This shouldn't have to be in degrees but it looks much better in animation
                swayYMod2.use_additive = True

    # If there are leaves we need to assign vertices to their vertex groups
    if leaves:
        offsetVal = 0
        leafVertSize = 6
        if leafShape == 'rect':
            leafVertSize = 4
        for i, cp in enumerate(childP):
            for v in leafMesh.vertices[leafVertSize * i:(leafVertSize * i + leafVertSize)]:
                leafObj.vertex_groups[cp.parBone].add([v.index], 1.0, 'ADD')

    # Now we need the rotation mode to be 'XYZ' to ensure correct rotation
    bpy.ops.object.mode_set(mode='OBJECT')
    for p in armOb.pose.bones:
        p.rotation_mode = 'XYZ'
    treeOb.parent = armOb


def kickstart_trunk(addstem, branches, cu, curve, curveRes, curveV, length, lengthV, ratio, resU, scale0, scaleV0,
                    scaleVal, taper, vertAtt):
    vertAtt = 0.0
    newSpline = cu.splines.new('BEZIER')
    cu.resolution_u = resU
    newPoint = newSpline.bezier_points[-1]
    newPoint.co = Vector((0, 0, 0))
    newPoint.handle_right = Vector((0, 0, 1))
    newPoint.handle_left = Vector((0, 0, -1))
    # (newPoint.handle_right_type,newPoint.handle_left_type) = ('VECTOR','VECTOR')
    branchL = (scaleVal) * (length[0] + uniform(-lengthV[0], lengthV[0]))
    childStems = branches[1]
    startRad = branchL * ratio * (scale0 + uniform(-scaleV0, scaleV0))
    endRad = startRad * (1 - taper[0])
    newPoint.radius = startRad
    addstem(
        stemSpline(newSpline, curve[0] / curveRes[0], curveV[0] / curveRes[0], 0, curveRes[0], branchL / curveRes[0],
                   childStems, startRad, endRad, 0))
    return vertAtt


def fabricate_stems(addsplinetobone, addstem, baseSize, branches, childP, cu, curve, curveBack, curveRes, curveV,
                    downAngle, downAngleV, leafDist, leaves, length, lengthV, levels, n, oldRotate, ratioPower, resU,
                    rotate, rotateV, scaleVal, shape, storeN, taper, vertAtt):
    for p in childP:
        # Add a spline and set the coordinate of the first point.
        newSpline = cu.splines.new('BEZIER')
        cu.resolution_u = resU
        newPoint = newSpline.bezier_points[-1]
        newPoint.co = p.co
        tempPos = zAxis.copy()
        # If the -ve flag for downAngle is used we need a special formula to find it
        if downAngleV[n] < 0.0:
            downV = downAngleV[n] * (
            1 - 2 * shapeRatio(0, (p.lengthPar - p.offset) / (p.lengthPar - baseSize * scaleVal)))
            random()
        # Otherwise just find a random value
        else:
            downV = uniform(-downAngleV[n], downAngleV[n])
        downRotMat = Matrix.Rotation(downAngle[n] + downV, 3, 'X')
        tempPos.rotate(downRotMat)
        # If the -ve flag for rotate is used we need to find which side of the stem the last child point was and then grow in the opposite direction.
        if rotate[n] < 0.0:
            oldRotate = -copysign(rotate[n] + uniform(-rotateV[n], rotateV[n]), oldRotate)
        # Otherwise just generate a random number in the specified range
        else:
            oldRotate += rotate[n] + uniform(-rotateV[n], rotateV[n])
        # Rotate the direction of growth and set the new point coordinates
        rotMat = Matrix.Rotation(oldRotate, 3, 'Z')
        tempPos.rotate(rotMat)
        tempPos.rotate(p.quat)
        newPoint.handle_right = p.co + tempPos
        if (storeN == levels - 1):
            # If this is the last level before leaves then we need to generate the child points differently
            branchL = (length[n] + uniform(-lengthV[n], lengthV[n])) * (p.lengthPar - 0.6 * p.offset)
            if leaves < 0:
                childStems = False
            else:
                childStems = leaves * shapeRatio(leafDist, p.offset / p.lengthPar)
        elif n == 1:
            # If this is the first level of branching then upward attraction has no effect
            # and a special formula is used to find branch length and the number of child stems.
            # This is also here that the shape is used.
            vertAtt = 0.0
            lMax = length[1] + uniform(-lengthV[1], lengthV[1])
            lMax += copysign(1e-6, lMax)  # Move away from zero to avoid div by zero
            branchL = p.lengthPar * lMax * shapeRatio(shape,
                                                      (p.lengthPar - p.offset) / (p.lengthPar - baseSize * scaleVal))
            childStems = branches[2] * (0.2 + 0.8 * (branchL / p.lengthPar) / lMax)
        else:
            branchL = (length[n] + uniform(-lengthV[n], lengthV[n])) * (p.lengthPar - 0.6 * p.offset)
            childStems = branches[min(3, n + 1)] * (1.0 - 0.5 * p.offset / p.lengthPar)

        #print("n=%d, levels=%d, n'=%d, childStems=%s"%(n, levels, storeN, childStems))
        branchL = max(branchL, 0.0)
        # Determine the starting and ending radii of the stem using the tapering of the stem
        startRad = min(p.radiusPar[0] * ((branchL / p.lengthPar) ** ratioPower), p.radiusPar[1])
        endRad = startRad * (1 - taper[n])
        newPoint.radius = startRad
        # If curveBack is used then the curviness of the stem is different for the first half
        if curveBack[n] == 0:
            curveVal = curve[n] / curveRes[n]
        else:
            curveVal = 2 * curve[n] / curveRes[n]
        # Add the new stem to list of stems to grow and define which bone it will be parented to
        addstem(
            stemSpline(newSpline, curveVal, curveV[n] / curveRes[n], 0, curveRes[n], branchL / curveRes[n], childStems,
                       startRad, endRad, len(cu.splines) - 1))
        addsplinetobone(p.parBone)
    return vertAtt


def perform_pruning(baseSize, baseSplits, childP, cu, currentMax, currentMin, currentScale, curve, curveBack, curveRes,
                    deleteSpline, forceSprout, handles, n, oldMax, orginalSplineToBone, originalCo, originalCurv,
                    originalCurvV, originalHandleL, originalHandleR, originalLength, originalSeg, prune, prunePowerHigh,
                    prunePowerLow, pruneRatio, pruneWidth, pruneWidthPeak, randState, ratio, scaleVal, segSplits,
                    splineToBone, splitAngle, splitAngleV, st, startPrune, vertAtt):
    while startPrune and ((currentMax - currentMin) > 0.005):
        setstate(randState)

        # If the search will halt after this iteration, then set the adjustment of stem length to take into account the pruning ratio
        if (currentMax - currentMin) < 0.01:
            currentScale = (currentScale - 1) * pruneRatio + 1
            startPrune = False
            forceSprout = True
        # Change the segment length of the stem by applying some scaling
        st.segL = originalLength * currentScale
        # To prevent millions of splines being created we delete any old ones and replace them with only their first points to begin the spline again
        if deleteSpline:
            for x in splineList:
                cu.splines.remove(x.spline)
            newSpline = cu.splines.new('BEZIER')
            newPoint = newSpline.bezier_points[-1]
            newPoint.co = originalCo
            newPoint.handle_right = originalHandleR
            newPoint.handle_left = originalHandleL
            (newPoint.handle_left_type, newPoint.handle_right_type) = ('VECTOR', 'VECTOR')
            st.spline = newSpline
            st.curv = originalCurv
            st.curvV = originalCurvV
            st.seg = originalSeg
            st.p = newPoint
            newPoint.radius = st.radS
            splineToBone = orginalSplineToBone

        # Initialise the spline list for those contained in the current level of branching
        splineList = [st]
        # For each of the segments of the stem which must be grown we have to add to each spline in splineList
        for k in range(curveRes[n]):
            # Make a copy of the current list to avoid continually adding to the list we're iterating over
            tempList = splineList[:]
            # print('Leng: ',len(tempList))
            # For each of the splines in this list set the number of splits and then grow it
            for spl in tempList:
                if k == 0:
                    numSplit = 0
                elif (k == 1) and (n == 0):
                    numSplit = baseSplits
                else:
                    numSplit = splits(segSplits[n])
                if (k == int(curveRes[n] / 2)) and (curveBack[n] != 0):
                    spl.curvAdd(-2 * curve[n] / curveRes[n] + 2 * curveBack[n] / curveRes[n])
                growSpline(spl, numSplit, splitAngle[n], splitAngleV[n], splineList, vertAtt, handles,
                           splineToBone)  # Add proper refs for radius and attractUp

        # If pruning is enabled then we must to the check to see if the end of the spline is within the evelope
        if prune:
            # Check each endpoint to see if it is inside
            for s in splineList:
                coordMag = (s.spline.bezier_points[-1].co.xy).length
                ratio = (scaleVal - s.spline.bezier_points[-1].co.z) / (scaleVal * max(1 - baseSize, 1e-6))
                # Don't think this if part is needed
                if (n == 0) and (s.spline.bezier_points[-1].co.z < baseSize * scaleVal):
                    insideBool = True  # Init to avoid UnboundLocalError later
                else:
                    insideBool = (
                    (coordMag / scaleVal) < pruneWidth * shapeRatio(8, ratio, pruneWidthPeak, prunePowerHigh,
                                                                    prunePowerLow))
                # If the point is not inside then we adjust the scale and current search bounds
                if not insideBool:
                    oldMax = currentMax
                    currentMax = currentScale
                    currentScale = 0.5 * (currentMax + currentMin)
                    break
            # If the scale is the original size and the point is inside then we need to make sure it won't be pruned or extended to the edge of the envelope
            if insideBool and (currentScale != 1):
                currentMin = currentScale
                currentMax = oldMax
                currentScale = 0.5 * (currentMax + currentMin)
            if insideBool and ((currentMax - currentMin) == 1):
                currentMin = 1
        # If the search will halt on the next iteration then we need to make sure we sprout child points to grow the next splines or leaves
        if (((currentMax - currentMin) < 0.005) or not prune) or forceSprout:
            tVals = findChildPoints(splineList, st.children)
            #print("debug tvals[%d] , splineList[%d], %s" % ( len(tVals), len(splineList), st.children))
            # If leaves is -ve then we need to make sure the only point which sprouts is the end of the spline
            # if not st.children:
            if not st.children:
                tVals = [0.9]
            # If this is the trunk then we need to remove some of the points because of baseSize
            if n == 0:
                trimNum = int(baseSize * (len(tVals) + 1))
                tVals = tVals[trimNum:]

            # For all the splines, we interpolate them and add the new points to the list of child points
            for s in splineList:
                #print(str(n)+'level: ',s.segMax*s.segL)
                childP.extend(interpStem(s, tVals, s.segMax * s.segL, s.radS))

        # Force the splines to be deleted
        deleteSpline = True
        # If pruning isn't enabled then make sure it doesn't loop
        if not prune:
            startPrune = False
    return ratio, splineToBone


def addTree(props):
    global splitError
    #startTime = time.time()
    # Set the seed for repeatable results
    seed(props.seed)#
    
    # Set all other variables
    levels = props.levels#
    length = props.length#
    lengthV = props.lengthV#
    branches = props.branches#
    curveRes = props.curveRes#
    curve = toRad(props.curve)#
    curveV = toRad(props.curveV)#
    curveBack = toRad(props.curveBack)#
    baseSplits = props.baseSplits#
    segSplits = props.segSplits#
    splitAngle = toRad(props.splitAngle)#
    splitAngleV = toRad(props.splitAngleV)#
    scale = props.scale#
    scaleV = props.scaleV#
    attractUp = props.attractUp#
    shape = int(props.shape)#
    baseSize = props.baseSize
    ratio = props.ratio
    taper = props.taper#
    ratioPower = props.ratioPower#
    downAngle = toRad(props.downAngle)#
    downAngleV = toRad(props.downAngleV)#
    rotate = toRad(props.rotate)#
    rotateV = toRad(props.rotateV)#
    scale0 = props.scale0#
    scaleV0 = props.scaleV0#
    prune = props.prune#
    pruneWidth = props.pruneWidth#
    pruneWidthPeak = props.pruneWidthPeak#
    prunePowerLow = props.prunePowerLow#
    prunePowerHigh = props.prunePowerHigh#
    pruneRatio = props.pruneRatio#
    leafScale = props.leafScale#
    leafScaleX = props.leafScaleX#
    leafShape = props.leafShape
    bend = props.bend#
    leafDist = int(props.leafDist)#
    bevelRes = props.bevelRes#
    resU = props.resU#
    useArm = props.useArm
    
    frameRate = props.frameRate
    windSpeed = props.windSpeed
    windGust = props.windGust
    armAnim = props.armAnim
    
    leafObj = None
    
    # Some effects can be turned ON and OFF, the necessary variables are changed here
    if not props.bevel:
        bevelDepth = 0.0
    else:
        bevelDepth = 1.0

    if not props.showLeaves:
        leaves = 0
    else:
        leaves = props.leaves

    if props.handleType == '0':
        handles = 'AUTO'
    else:
        handles = 'VECTOR'

    for ob in bpy.data.objects:
        ob.select = False

    childP = []
    stemList = []

    # Initialise the tree object and curve and adjust the settings
    cu = bpy.data.curves.new('tree','CURVE')
    treeOb = bpy.data.objects.new('tree',cu)
    bpy.context.scene.objects.link(treeOb)
    
    treeOb.location=bpy.context.scene.cursor_location

    cu.dimensions = '3D'
    cu.fill_mode = 'FULL'
    cu.bevel_depth = bevelDepth
    cu.bevel_resolution = bevelRes

    # Fix the scale of the tree now
    scaleVal = scale + uniform(-scaleV,scaleV)
    scaleVal += copysign(1e-6, scaleVal)  # Move away from zero to avoid div by zero

    # If pruning is turned on we need to draw the pruning envelope
    if prune:
        enHandle = 'VECTOR'
        enNum = 128
        enCu = bpy.data.curves.new('envelope','CURVE')
        enOb = bpy.data.objects.new('envelope',enCu)
        enOb.parent = treeOb
        bpy.context.scene.objects.link(enOb)
        newSpline = enCu.splines.new('BEZIER')
        newPoint = newSpline.bezier_points[-1]
        newPoint.co = Vector((0,0,scaleVal))
        (newPoint.handle_right_type,newPoint.handle_left_type) = (enHandle,enHandle)
        # Set the coordinates by varying the z value, envelope will be aligned to the x-axis
        for c in range(enNum):
            newSpline.bezier_points.add()
            newPoint = newSpline.bezier_points[-1]
            ratioVal = (c+1)/(enNum)
            zVal = scaleVal - scaleVal*(1-baseSize)*ratioVal
            newPoint.co = Vector((scaleVal*pruneWidth*shapeRatio(8,ratioVal,pruneWidthPeak,prunePowerHigh,prunePowerLow),0,zVal))
            (newPoint.handle_right_type,newPoint.handle_left_type) = (enHandle,enHandle)
        newSpline = enCu.splines.new('BEZIER')
        newPoint = newSpline.bezier_points[-1]
        newPoint.co = Vector((0,0,scaleVal))
        (newPoint.handle_right_type,newPoint.handle_left_type) = (enHandle,enHandle)
        # Create a second envelope but this time on the y-axis
        for c in range(enNum):
            newSpline.bezier_points.add()
            newPoint = newSpline.bezier_points[-1]
            ratioVal = (c+1)/(enNum)
            zVal = scaleVal - scaleVal*(1-baseSize)*ratioVal
            newPoint.co = Vector((0,scaleVal*pruneWidth*shapeRatio(8,ratioVal,pruneWidthPeak,prunePowerHigh,prunePowerLow),zVal))
            (newPoint.handle_right_type,newPoint.handle_left_type) = (enHandle,enHandle)

    leafVerts = []
    leafFaces = []
    levelCount = []

    splineToBone = deque([''])
    addsplinetobone = splineToBone.append
 
    leafMesh = None # in case we aren't creating leaves, we'll still have the variable

     # Each of the levels needed by the user we grow all the splines
    for n in range(levels):
        storeN = n
        stemList = deque()
        addstem = stemList.append
        # If n is used as an index to access parameters for the tree it must be at most 3 or it will reference outside the array index
        n = min(3,n)
        vertAtt = attractUp
        splitError = 0.0
        # If this is the first level of growth (the trunk) then we need some special work to begin the tree
        if n == 0:
            vertAtt = kickstart_trunk(addstem, branches, cu, curve, curveRes, curveV, length, lengthV, ratio, resU,
                                      scale0, scaleV0, scaleVal, taper, vertAtt)
        # If this isn't the trunk then we may have multiple stem to intialise
        else:
            # Store the old rotation to allow new stems to be rotated away from the previous one.
            oldRotate = 0
            # For each of the points defined in the list of stem starting points we need to grow a stem.
            vertAtt = fabricate_stems(addsplinetobone, addstem, baseSize, branches, childP, cu, curve, curveBack,
                                      curveRes, curveV, downAngle, downAngleV, leafDist, leaves, length, lengthV,
                                      levels, n, oldRotate, ratioPower, resU, rotate, rotateV, scaleVal, shape, storeN,
                                      taper, vertAtt)

        childP = []
        # Now grow each of the stems in the list of those to be extended
        for st in stemList:
            # When using pruning, we need to ensure that the random effects will be the same for each iteration to make sure the problem is linear.
            randState = getstate()
            startPrune = True
            lengthTest = 0.0
            # Store all the original values for the stem to make sure we have access after it has been modified by pruning
            originalLength = st.segL
            originalCurv = st.curv
            originalCurvV = st.curvV
            originalSeg = st.seg
            originalHandleR = st.p.handle_right.copy()
            originalHandleL = st.p.handle_left.copy()
            originalCo = st.p.co.copy()
            currentMax = 1.0
            currentMin = 0.0
            currentScale = 1.0
            oldMax = 1.0
            deleteSpline = False
            orginalSplineToBone = copy.copy(splineToBone)
            forceSprout = False
            # Now do the iterative pruning, this uses a binary search and halts once the difference between upper and lower bounds of the search are less than 0.005
            ratio, splineToBone = perform_pruning(baseSize, baseSplits, childP, cu, currentMax, currentMin,
                                                  currentScale, curve, curveBack, curveRes, deleteSpline, forceSprout,
                                                  handles, n, oldMax, orginalSplineToBone, originalCo, originalCurv,
                                                  originalCurvV, originalHandleL, originalHandleR, originalLength,
                                                  originalSeg, prune, prunePowerHigh, prunePowerLow, pruneRatio,
                                                  pruneWidth, pruneWidthPeak, randState, ratio, scaleVal, segSplits,
                                                  splineToBone, splitAngle, splitAngleV, st, startPrune, vertAtt)

        levelCount.append(len(cu.splines))
        # If we need to add leaves, we do it here
        if (storeN == levels-1) and leaves:
            oldRot = 0.0
            n = min(3,n+1)
            # For each of the child points we add leaves
            for cp in childP:
                # If the special flag is set then we need to add several leaves at the same location
                if leaves < 0:
                    oldRot = -rotate[n]/2
                    for g in range(abs(leaves)):
                        (vertTemp,faceTemp,oldRot) = genLeafMesh(leafScale,leafScaleX,cp.co,cp.quat,len(leafVerts),downAngle[n],downAngleV[n],rotate[n],rotateV[n],oldRot,bend,leaves, leafShape)
                        leafVerts.extend(vertTemp)
                        leafFaces.extend(faceTemp)
                # Otherwise just add the leaves like splines.
                else:
                    (vertTemp,faceTemp,oldRot) = genLeafMesh(leafScale,leafScaleX,cp.co,cp.quat,len(leafVerts),downAngle[n],downAngleV[n],rotate[n],rotateV[n],oldRot,bend,leaves, leafShape)
                    leafVerts.extend(vertTemp)
                    leafFaces.extend(faceTemp)
            # Create the leaf mesh and object, add geometry using from_pydata, edges are currently added by validating the mesh which isn't great
            leafMesh = bpy.data.meshes.new('leaves')
            leafObj = bpy.data.objects.new('leaves',leafMesh)
            bpy.context.scene.objects.link(leafObj)
            leafObj.parent = treeOb
            leafMesh.from_pydata(leafVerts,(),leafFaces)

            if leafShape == 'rect':
                leafMesh.uv_textures.new("leafUV")
                uvlayer = leafMesh.uv_layers.active.data

                for i in range(0, len(leafFaces)):
                    uvlayer[i*4 + 0].uv = Vector((1, 0))
                    uvlayer[i*4 + 1].uv = Vector((1, 1))
                    uvlayer[i*4 + 2].uv = Vector((1 - leafScaleX, 1))
                    uvlayer[i*4 + 3].uv = Vector((1 - leafScaleX, 0))

            leafMesh.validate()

# This can be used if we need particle leaves
#            if (storeN == levels-1) and leaves:
#                normalList = []
#                oldRot = 0.0
#                n = min(3,n+1)
#                oldRot = 0.0
#                # For each of the child points we add leaves
#                for cp in childP:
#                    # Here we make the new "sprouting" stems diverge from the current direction
#                    dirVec = zAxis.copy()
#                    oldRot += rotate[n]+uniform(-rotateV[n],rotateV[n])
#                    downRotMat = Matrix.Rotation(downAngle[n]+uniform(-downAngleV[n],downAngleV[n]),3,'X')
#                    rotMat = Matrix.Rotation(oldRot,3,'Z')
#                    dirVec.rotate(downRotMat)
#                    dirVec.rotate(rotMat)
#                    dirVec.rotate(cp.quat)
#                    normalList.extend([dirVec.x,dirVec.y,dirVec.z])
#                    leafVerts.append(cp.co)
#                # Create the leaf mesh and object, add geometry using from_pydata, edges are currently added by validating the mesh which isn't great
#                edgeList = [(a,a+1) for a in range(len(childP)-1)]
#                leafMesh = bpy.data.meshes.new('leaves')
#                leafObj = bpy.data.objects.new('leaves',leafMesh)
#                bpy.context.scene.objects.link(leafObj)
#                leafObj.parent = treeOb
#                leafMesh.from_pydata(leafVerts,edgeList,())
#                leafMesh.vertices.foreach_set('normal',normalList)

    # If we need and armature we add it
    if useArm:
        # Create the armature and objects
        create_armature(armAnim, childP, cu, frameRate, leafMesh, leafObj, leafShape, leaves, levelCount, splineToBone,
                        treeOb, windGust, windSpeed)
    #print(time.time()-startTime)
