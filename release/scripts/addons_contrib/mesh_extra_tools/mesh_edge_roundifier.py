# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

bl_info = {
    "name": "Edge Roundifier",
    "category": "Mesh",
    'author': 'Piotr Komisarczyk (komi3D), PKHG',
    'version': (1, 0, 0),
    'blender': (2, 7, 3),
    'location': 'SPACE > Edge Roundifier or CTRL-E > Edge Roundifier or Tools > Addons > Edge Roundifier',
    'description': 'Mesh editing script allowing edge rounding',
    'wiki_url': '',
    'tracker_url': '',
    'category': 'Mesh'
}

import bmesh
import bpy
import bpy.props
import imp
from math import sqrt, acos, asin, pi, radians, degrees, sin, acos
from mathutils import Vector, Euler, Matrix, Quaternion
import types


# CONSTANTS
two_pi = 2 * pi  # PKHG>??? maybe other constantly used values too???
XY = "XY"
XZ = "XZ"
YZ = "YZ"
SPIN_END_THRESHOLD = 0.001
LINE_TOLERANCE = 0.0001


# variable controlling all print functions
# PKHG>??? to be replaced, see debugPrintNew ;-)
debug = True


def debugPrint(*text):
    if debug:
        for t in text:
            print(text)


############# for debugging PKHG ################
def debugPrintNew(debug, *text):
    if debug:
        tmp = [el for el in text]
        for row in tmp:
            print(row)

d_XABS_YABS = False
d_Edge_Info = False
d_Plane = False
d_Radius_Angle = False
d_Roots = False
d_RefObject = False
d_LineAB = False
d_Selected_edges = False
d_Rotate_Around_Spin_Center = False
###################################################################################


####################### Geometry and math calcualtion methods #####################

class CalculationHelper:

    def __init__(self):
        '''
        Constructor
        '''

    def getLineCoefficientsPerpendicularToVectorInPoint(self, point, vector, plane):
        x, y, z = point
        xVector, yVector, zVector = vector
        destinationPoint = (x + yVector, y - xVector, z)
        if plane == 'YZ':
            destinationPoint = (x, y + zVector, z - yVector)
        if plane == 'XZ':
            destinationPoint = (x + zVector, y, z - xVector)
        return self.getCoefficientsForLineThrough2Points(point, destinationPoint, plane)

    def getQuadraticRoots(self, coef):
        if len(coef) != 3:
            return NaN
        else:
            a, b, c = coef
            delta = b ** 2 - 4 * a * c
            if delta == 0:
                x = -b / (2 * a)
                return (x, x)
            elif delta < 0:
                return None
            else:
                x1 = (-b - sqrt(delta)) / (2 * a)
                x2 = (-b + sqrt(delta)) / (2 * a)
                return (x1, x2)

    def getCoefficientsForLineThrough2Points(self, point1, point2, plane):
        x1, y1, z1 = point1
        x2, y2, z2 = point2

        # mapping x1,x2, y1,y2 to proper values based on plane
        if plane == YZ:
            x1 = y1
            x2 = y2
            y1 = z1
            y2 = z2
        if plane == XZ:
            y1 = z1
            y2 = z2

        # Further calculations the same as for XY plane
        xabs = abs(x2 - x1)
        yabs = abs(y2 - y1)
        debugPrintNew(d_XABS_YABS, "XABS = " + str(xabs) + " YABS = " + str(yabs))

        if xabs <= LINE_TOLERANCE:
            return None  # this means line x = edgeCenterX
        if yabs <= LINE_TOLERANCE:
            A = 0
            B = y1
            return A, B
        A = (y2 - y1) / (x2 - x1)
        B = y1 - (A * x1)
        return (A, B)

    def getLineCircleIntersections(self, lineAB, circleMidPoint, radius):
        # (x - a)**2 + (y - b)**2 = r**2 - circle equation
        # y = A*x + B - line equation
        # f * x**2 + g * x + h = 0 - quadratic equation
        A, B = lineAB
        a, b = circleMidPoint
        f = 1 + (A ** 2)
        g = -2 * a + 2 * A * B - 2 * A * b
        h = (B ** 2) - 2 * b * B - (radius ** 2) + (a ** 2) + (b ** 2)
        coef = [f, g, h]
        roots = self.getQuadraticRoots(coef)
        if roots != None:
            x1 = roots[0]
            x2 = roots[1]
            point1 = [x1, A * x1 + B]
            point2 = [x2, A * x2 + B]
            return [point1, point2]
        else:
            return None

    def getLineCircleIntersectionsWhenXPerpendicular(self, edgeCenter, circleMidPoint, radius, plane):
        # (x - a)**2 + (y - b)**2 = r**2 - circle equation
        # x = xValue - line equation
        # f * x**2 + g * x + h = 0 - quadratic equation
        xValue = edgeCenter[0]
        if plane == YZ:
            xValue = edgeCenter[1]
        if plane == XZ:
            xValue = edgeCenter[0]

        a, b = circleMidPoint
        f = 1
        g = -2 * b
        h = (a ** 2) + (b ** 2) + (xValue ** 2) - 2 * a * xValue - (radius ** 2)
        coef = [f, g, h]
        roots = self.getQuadraticRoots(coef)
        if roots != None:
            y1 = roots[0]
            y2 = roots[1]
            point1 = [xValue, y1]
            point2 = [xValue, y2]
            return [point1, point2]
        else:
            return None

    # point1 is the point near 90 deg angle
    def getAngle(self, point1, point2, point3):
        distance1 = (Vector(point1) - Vector(point2)).length
        distance2 = (Vector(point2) - Vector(point3)).length
        cos = distance1 / distance2

        if abs(cos) > 1:  # prevents Domain Error
            cos = round(cos)

        alpha = acos(cos)
        return (alpha, degrees(alpha))

    # get two of three coordinates used for further calculation of spin center
    # PKHG>nice if rescriction to these 3 types or planes is to be done
    # komi3D> from 0.0.2 there is a restriction. In future I would like Edge Roundifier to work on
    # komi3D> Normal and View coordinate systems. That would be great...
    def getCircleMidPointOnPlane(self, V1, plane):
        X = V1[0]
        Y = V1[1]
        if plane == 'XZ':
            X = V1[0]
            Y = V1[2]
        elif plane == 'YZ':
            X = V1[1]
            Y = V1[2]
        return [X, Y]

    def getEdgeReference(self, edge, edgeCenter, plane):
        vert1 = edge.verts[1].co
        V = vert1 - edgeCenter
        orthoVector = Vector((V[1], -V[0], V[2]))
        if plane == 'XZ':
            orthoVector = Vector((V[2], V[1], -V[0]))
        elif plane == 'YZ':
            orthoVector = Vector((V[0], V[2], -V[1]))
        refPoint = edgeCenter + orthoVector
        return refPoint


########################################################
################# SELECTION METHODS ####################

class SelectionHelper:

    def selectVertexInMesh(self, mesh, vertex):
        bpy.ops.object.mode_set(mode="OBJECT")
        for v in mesh.vertices:
            if v.co == vertex:
                v.select = True
                break

        bpy.ops.object.mode_set(mode="EDIT")

    def getSelectedVertex(self, mesh):
        bpy.ops.object.mode_set(mode="OBJECT")
        for v in mesh.vertices:
            if v.select == True:
                bpy.ops.object.mode_set(mode="EDIT")
                return v

        bpy.ops.object.mode_set(mode="EDIT")
        return None

    def refreshMesh(self, bm, mesh):
        bpy.ops.object.mode_set(mode='OBJECT')
        bm.to_mesh(mesh)
        bpy.ops.object.mode_set(mode='EDIT')


class roundify_help(bpy.types.Operator):
    bl_idname = 'help.roundify'
    bl_label = ''

    def draw(self, context):
        layout = self.layout
        layout.label('To use:')
        layout.label('Select a face or faces & inset.')
        layout.label('Inset square, circle or outside.')
        layout.label('To Help:')
        layout.label('Circle: use remove doubles to tidy joins.')
        layout.label('Outset: select & use normals flip before extruding.')

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=350)

###################################################################################


class EdgeRoundifier(bpy.types.Operator):
    """Edge Roundifier"""  # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mesh.edge_roundifier"  # unique identifier for buttons and menu items to reference.
    bl_label = "Edge Roundifier"  # display name in the interface.
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}  # enable undo for the operator.PKHG>INFO and PRESET

    threshold = 0.0005

    obj = None

    edgeScaleFactor = bpy.props.FloatProperty(name='', default=1.0, min=0.00001, max=100000.0, step=0.5, precision=5)
    r = bpy.props.FloatProperty(name='', default=1, min=0.00001, max=1000.0, step=0.1, precision=3)
    a = bpy.props.FloatProperty(name='', default=180.0, min=0.1, max=180.0, step=0.5, precision=1)
    n = bpy.props.IntProperty(name='', default=4, min=1, max=100, step=1)
    flip = bpy.props.BoolProperty(name='Flip', default=False)

    invertAngle = bpy.props.BoolProperty(name='Invert', default=False)
    fullCircles = bpy.props.BoolProperty(name='Circles', default=False)
    bothSides = bpy.props.BoolProperty(name='Both sides', default=False)

    drawArcCenters = bpy.props.BoolProperty(name='Centers', default=False)
    removeEdges = bpy.props.BoolProperty(name='Edges', default=False)
    removeScaledEdges = bpy.props.BoolProperty(name='Scaled edges', default=False)

    connectArcWithEdge = bpy.props.BoolProperty(name='Arc - Edge', default=False)
    connectArcs = bpy.props.BoolProperty(name='Arcs', default=False)
    connectScaledAndBase = bpy.props.BoolProperty(name='Scaled - Base Edge', default=False)
    connectArcsFlip = bpy.props.BoolProperty(name='Flip Arcs', default=False)
    connectArcWithEdgeFlip = bpy.props.BoolProperty(name='Flip Arc - Edge', default=False)

    axisAngle = bpy.props.FloatProperty(name='', default=0.0, min=-180.0, max=180.0, step=0.5, precision=1)
    edgeAngle = bpy.props.FloatProperty(name='', default=0.0, min=-180.0, max=180.0, step=0.5, precision=1)
    offset = bpy.props.FloatProperty(name='', default=0.0, min=-1000000.0, max=1000000.0, step=0.1, precision=5)
    offset2 = bpy.props.FloatProperty(name='', default=0.0, min=-1000000.0, max=1000000.0, step=0.1, precision=5)
    ellipticFactor = bpy.props.FloatProperty(name='', default=0.0, min=-1000000.0, max=1000000.0, step=0.1, precision=5)

    workModeItems = [("Normal", "Normal", ""), ("Reset", "Reset", "")]
    workMode = bpy.props.EnumProperty(
        items=workModeItems,
        name='',
        default='Normal',
        description="Edge Roundifier work mode")

    entryModeItems = [("Radius", "Radius", ""), ("Angle", "Angle", "")]
    entryMode = bpy.props.EnumProperty(
        items=entryModeItems,
        name='',
        default='Angle',
        description="Edge Roundifier entry mode")

    rotateCenterItems = [("Spin", "Spin", ""), ("V1", "V1", ""), ("Edge", "Edge", ""), ("V2", "V2", "")]
    rotateCenter = bpy.props.EnumProperty(
        items=rotateCenterItems,
        name='',
        default='Edge',
        description="Rotate center for spin axis rotate")

    arcModeItems = [("FullEdgeArc", "Full", "Full"), ('HalfEdgeArc', "Half", "Half")]
    arcMode = bpy.props.EnumProperty(
        items=arcModeItems,
        name='',
        default='FullEdgeArc',
        description="Edge Roundifier arc mode")

    angleItems = [('Other', "Other", "User defined angle"), ('180', "180", "HemiCircle"), ('120', "120", "TriangleCircle"),
                  ('90', "90", "QuadCircle"), ('72', "72", "PentagonCircle"), ('60', "60", "HexagonCircle"),
                  ('45', "45", "OctagonCircle"), ('30', "30", "12-gonCircle")]

    angleEnum = bpy.props.EnumProperty(
        items=angleItems,
        name='',
        default='180',
        description="Presets prepare standard angles and calculate proper ray")

    refItems = [('ORG', "Origin", "Use Origin Location"), ('CUR', "3D Cursor", "Use 3DCursor Location"), ('EDG', "Edge", "Use Individual Edge Reference")]
    referenceLocation = bpy.props.EnumProperty(
        items=refItems,
        name='',
        default='ORG',
        description="Reference location used by Edge Roundifier to calculate initial centers of drawn arcs")

    planeItems = [(XY, XY, "XY Plane (Z=0)"), (YZ, YZ, "YZ Plane (X=0)"), (XZ, XZ, "XZ Plane (Y=0)")]
    planeEnum = bpy.props.EnumProperty(
        items=planeItems,
        name='',
        default='XY',
        description="Plane used by Edge Roundifier to calculate spin plane of drawn arcs")

    edgeScaleCenterItems = [('V1', "V1", "v1"), ('CENTER', "Center", "cent"), ('V2', "V2", "v2")]
    edgeScaleCenterEnum = bpy.props.EnumProperty(
        items=edgeScaleCenterItems,
        name='edge scale center',
        default='CENTER',
        description="Center used for scaling initial edge")

    calc = CalculationHelper()
    sel = SelectionHelper()

    def prepareMesh(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')

        mesh = context.scene.objects.active.data
        bm = bmesh.new()
        bm.from_mesh(mesh)

        edges = [ele for ele in bm.edges if ele.select]
        return edges, mesh, bm

    def prepareParameters(self):
        parameters = {"a": "a"}
        parameters["arcMode"] = self.arcMode
        parameters["edgeScaleFactor"] = self.edgeScaleFactor
        parameters["edgeScaleCenterEnum"] = self.edgeScaleCenterEnum
        parameters["plane"] = self.planeEnum
        parameters["radius"] = self.r
        parameters["angle"] = self.a
        parameters["segments"] = self.n
        parameters["fullCircles"] = self.fullCircles
        parameters["invertAngle"] = self.invertAngle
        parameters["bothSides"] = self.bothSides
        parameters["angleEnum"] = self.angleEnum
        parameters["entryMode"] = self.entryMode
        parameters["workMode"] = self.workMode
        parameters["refObject"] = self.referenceLocation
        parameters["flip"] = self.flip
        parameters["drawArcCenters"] = self.drawArcCenters
        parameters["removeEdges"] = self.removeEdges
        parameters["removeScaledEdges"] = self.removeScaledEdges
        parameters["connectArcWithEdge"] = self.connectArcWithEdge
        parameters["connectScaledAndBase"] = self.connectScaledAndBase
        parameters["connectArcs"] = self.connectArcs
        parameters["connectArcsFlip"] = self.connectArcsFlip
        parameters["connectArcWithEdgeFlip"] = self.connectArcWithEdgeFlip
        parameters["axisAngle"] = self.axisAngle
        parameters["edgeAngle"] = self.edgeAngle
        parameters["offset"] = self.offset
        parameters["offset2"] = self.offset2
        parameters["ellipticFactor"] = self.ellipticFactor
        parameters["rotateCenter"] = self.rotateCenter
        return parameters

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        uiPercentage = 0.333

        self.addEnumParameterToUI(box, False, uiPercentage, 'Mode:', 'workMode')
        self.addEnumParameterToUI(box, False, uiPercentage, 'Plane:', 'planeEnum')
        self.addEnumParameterToUI(box, False, uiPercentage, 'Reference:', 'referenceLocation')

        box = layout.box()
        self.addEnumParameterToUI(box, False, uiPercentage, 'Scale base:', 'edgeScaleCenterEnum')
        self.addParameterToUI(box, False, uiPercentage, 'Scale factor:', 'edgeScaleFactor')

        box = layout.box()
        self.addEnumParameterToUI(box, False, uiPercentage, 'Entry mode:', 'entryMode')

        row = box.row(align=False)
        row.prop(self, 'angleEnum', expand=True, text="angle presets")

        self.addParameterToUI(box, False, uiPercentage, 'Angle:', 'a')
        self.addParameterToUI(box, False, uiPercentage, 'Radius:', 'r')
        self.addParameterToUI(box, False, uiPercentage, 'Segments:', 'n')

###################################
        box = layout.box()
        self.addTwoCheckboxesToUI(box, False, 'Options:', 'flip', 'invertAngle')
        self.addTwoCheckboxesToUI(box, False, '', 'bothSides', 'fullCircles')
        self.addCheckboxToUI(box, False, '', 'drawArcCenters')

        box = layout.box()
        self.addTwoCheckboxesToUI(box, False, 'Remove:', 'removeEdges', 'removeScaledEdges')

        box = layout.box()
        self.addTwoCheckboxesToUI(box, False, 'Connect:', 'connectArcs', 'connectArcsFlip')
        self.addTwoCheckboxesToUI(box, False, '', 'connectArcWithEdge', 'connectArcWithEdgeFlip')
        self.addCheckboxToUI(box, False, '', 'connectScaledAndBase')
################################

        box = layout.box()
        self.addParameterToUI(box, False, uiPercentage, 'Orhto offset:', 'offset')
        self.addParameterToUI(box, False, uiPercentage, 'Parallel offset:', 'offset2')

        box = layout.box()
        self.addParameterToUI(box, False, uiPercentage, 'Edge rotate :', 'edgeAngle')
        self.addEnumParameterToUI(box, False, uiPercentage, 'Axis rotate center:', 'rotateCenter')
        self.addParameterToUI(box, False, uiPercentage, 'Axis rotate:', 'axisAngle')

        box = layout.box()
        self.addParameterToUI(box, False, uiPercentage, 'Elliptic factor:', 'ellipticFactor')

    def addParameterToUI(self, layout, alignment, percent, label, property):
        row = layout.row(align=alignment)
        split = row.split(percentage=percent)
        col = split.column()
        col.label(label)
        col2 = split.column()
        row = col2.row(align=alignment)
        row.prop(self, property)

    def addTwoCheckboxesToUI(self, layout, alignment, label, property1, property2):
        row = layout.row(align=alignment)
        row.label(label)
        row.prop(self, property1)
        row.prop(self, property2)

    def addCheckboxToUI(self, layout, alignment, label, property1):
        row = layout.row(align=alignment)
        row.label(label)
        row.prop(self, property1)
        row.label('')

    def addEnumParameterToUI(self, layout, alignment, percent, label, property):
        row = layout.row(align=alignment)
        split = row.split(percentage=percent)
        col = split.column()
        col.label(label)
        col2 = split.column()
        row = col2.row(align=alignment)
        row.prop(self, property, expand=True, text="a")

    def execute(self, context):

        edges, mesh, bm = self.prepareMesh(context)
        parameters = self.prepareParameters()

        self.resetValues(parameters["workMode"])

        self.obj = context.scene.objects.active
        scaledEdges = self.scaleDuplicatedEdges(bm, edges, parameters)

        if len(scaledEdges) > 0:
            self.roundifyEdges(scaledEdges, parameters, bm, mesh)

            if parameters["connectScaledAndBase"]:
                self.connectScaledEdgesWithBaseEdge(scaledEdges, edges, bm, mesh)

            self.sel.refreshMesh(bm, mesh)
            self.selectEdgesAfterRoundifier(context, scaledEdges)
        else:
            debugPrint("No edges selected!")

        if parameters["removeEdges"]:
            bmesh.ops.delete(bm, geom=edges, context=2)
        if parameters["removeScaledEdges"] and self.edgeScaleFactor != 1.0:
            bmesh.ops.delete(bm, geom=scaledEdges, context=2)

        bpy.ops.object.mode_set(mode='OBJECT')
        bm.to_mesh(mesh)
        bpy.ops.object.mode_set(mode='EDIT')

        bm.free()
        return {'FINISHED'}

##########################################
    def resetValues(self, workMode):
        if workMode == "Reset":
            self.setAllParamsToDefaults()

    def setAllParamsToDefaults(self):
        self.edgeScaleFactor = 1.0
        self.r = 1
        self.a = 180.0
        self.n = 4
        self.flip = False
        self.invertAngle = False
        self.fullCircles = False
        self.bothSides = False
        self.drawArcCenters = False
        self.removeEdges = False
        self.removeScaledEdges = False

        self.connectArcWithEdge = False
        self.connectArcs = False
        self.connectScaledAndBase = False
        self.connectArcsFlip = False
        self.connectArcWithEdgeFlip = False

        self.axisAngle = 0.0
        self.edgeAngle = 0.0
        self.offset = 0.0
        self.offset2 = 0.0
        self.ellipticFactor = 0.0

        self.workMode = 'Normal'
        self.entryMode = 'Angle'
        self.angleEnum = '180'
        self.referenceLocation = 'ORG'
        self.planeEnum = 'XY'
        self.edgeScaleCenterEnum = 'CENTER'
        self.rotateCenter = 'Edge'
        ######

    def scaleDuplicatedEdges(self, bm, edges, parameters):
        scaleCenter = parameters["edgeScaleCenterEnum"]
        factor = parameters["edgeScaleFactor"]
        # this code is based on Zeffi's answer to my question
        duplicateEdges = []
        if factor == 1:
            duplicateEdges = edges
        else:
            for e in edges:
                v1 = e.verts[0].co
                v2 = e.verts[1].co
                origin = None
                if scaleCenter == 'CENTER':
                    origin = (v1 + v2) * 0.5
                elif scaleCenter == 'V1':
                    origin = v1
                elif scaleCenter == 'V2':
                    origin = v2

                bmv1 = bm.verts.new(((v1 - origin) * factor) + origin)
                bmv2 = bm.verts.new(((v2 - origin) * factor) + origin)
                bme = bm.edges.new([bmv1, bmv2])
                duplicateEdges.append(bme)
        return duplicateEdges

    def roundifyEdges(self, edges, parameters, bm, mesh):
        arcs = []
        for e in edges:
            arcVerts = self.roundify(e, parameters, bm, mesh)
            arcs.append(arcVerts)

        if parameters["connectArcs"]:
            self.connectArcsTogether(arcs, bm, mesh, parameters)

    def getNormalizedEdgeVector(self, edge):
        V1 = edge.verts[0].co
        V2 = edge.verts[1].co
        edgeVector = V2 - V1
        normEdge = edgeVector.normalized()
        return normEdge

    def getEdgePerpendicularVector(self, edge, plane):
        normEdge = self.getNormalizedEdgeVector(edge)

        edgePerpendicularVector = Vector((normEdge[1], -normEdge[0], 0))
        if plane == YZ:
            edgePerpendicularVector = Vector((0, normEdge[2], -normEdge[1]))
        if plane == XZ:
            edgePerpendicularVector = Vector((normEdge[2], 0, -normEdge[0]))
        return edgePerpendicularVector

    def getEdgeInfo(self, edge):
        V1 = edge.verts[0].co
        V2 = edge.verts[1].co
        edgeVector = V2 - V1
        edgeLength = edgeVector.length
        edgeCenter = (V2 + V1) * 0.5
        return V1, V2, edgeVector, edgeLength, edgeCenter

    def roundify(self, edge, parameters, bm, mesh):
        V1, V2, edgeVector, edgeLength, edgeCenter = self.getEdgeInfo(edge)
        if self.skipThisEdge(V1, V2, parameters["plane"]):
            return

        roundifyParams = None
        arcVerts = None
        roundifyParams = self.calculateRoundifyParams(edge, parameters, bm, mesh)
        if roundifyParams == None:
            return

        arcVerts = self.spinAndPostprocess(edge, parameters, bm, mesh, edgeCenter, roundifyParams)
        return arcVerts

    def spinAndPostprocess(self, edge, parameters, bm, mesh, edgeCenter, roundifyParams):
        spinnedVerts, roundifyParamsUpdated = self.drawSpin(edge, edgeCenter, roundifyParams, parameters, bm, mesh)
        postProcessedArcVerts = self.arcPostprocessing(edge, parameters, bm, mesh, roundifyParamsUpdated, spinnedVerts, edgeCenter)
        return postProcessedArcVerts

    def rotateArcAroundEdge(self, bm, mesh, arcVerts, parameters):
        angle = parameters["edgeAngle"]
        if angle != 0:
            self.arc_rotator(arcVerts, angle, parameters)

    # arc_rotator method was created by PKHG, I (komi3D) adjusted it to fit the rest of this addon
    def arc_rotator(self, arcVerts, extra_rotation, parameters):
        bpy.ops.object.mode_set(mode='OBJECT')
        old_location = self.obj.location.copy()
        bpy.ops.transform.translate(value=- old_location, constraint_axis=(False, False, False), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1)
        bpy.ops.object.mode_set(mode='EDIT')
        adjust_matrix = self.obj.matrix_parent_inverse
        bm = bmesh.from_edit_mesh(self.obj.data)
        lastVert = len(arcVerts) - 1
        if parameters["drawArcCenters"]:
            lastVert = lastVert - 1  # center gets added as last vert of arc
        v0_old = adjust_matrix * arcVerts[0].co.copy()
        v1_old = adjust_matrix * arcVerts[lastVert].co.copy()

        # PKHG>INFO move if necessary v0 to origin such that the axis gos through origin and v1
        if v0_old != Vector((0, 0, 0)):
            for i, ele in enumerate(arcVerts):
                arcVerts[i].co += - v0_old

        axis = arcVerts[0].co - arcVerts[lastVert].co

        a_quat = Quaternion(axis, radians(extra_rotation)).normalized()
        a_mat = Quaternion(axis, radians(extra_rotation)).normalized().to_matrix()

        for ele in arcVerts:
            ele.co = a_mat * ele.co

        # PKHG>INFO move back if needed
        if v0_old != Vector((0, 0, 0)):
            for i, ele in enumerate(arcVerts):
                arcVerts[i].co += + v0_old

        bpy.ops.object.mode_set(mode='OBJECT')
        # PKHG>INFO move origin object back print("old location = " , old_location)
        bpy.ops.transform.translate(value=old_location, constraint_axis=(False, False, False), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1)
        bpy.ops.object.mode_set(mode='EDIT')

    def makeElliptic(self, bm, mesh, arcVertices, parameters):
        if parameters["ellipticFactor"] != 0:  # if 0 then nothing has to be done
            lastVert = len(arcVertices) - 1
            if parameters["drawArcCenters"]:
                lastVert = lastVert - 1  # center gets added as last vert of arc
            v0co = arcVertices[0].co
            v1co = arcVertices[lastVert].co

            for vertex in arcVertices:  # range(len(res_list)):
                # PKHg>INFO compute the base on the edge  of the height-vector
                top = vertex.co  # res_list[nr].co
                t = 0
                if v1co - v0co != 0:
                    t = (v1co - v0co).dot(top - v0co) / (v1co - v0co).length ** 2
                h_bottom = v0co + t * (v1co - v0co)
                height = (h_bottom - top)
                vertex.co = top + parameters["ellipticFactor"] * height

        return arcVertices

    def arcPostprocessing(self, edge, parameters, bm, mesh, roundifyParams, spinnedVerts, edgeCenter):
        [chosenSpinCenter, otherSpinCenter, spinAxis, angle, steps, refObjectLocation] = roundifyParams
        rotatedVerts = []
        if parameters["rotateCenter"] == 'Edge':
            rotatedVerts = self.rotateArcAroundSpinAxis(bm, mesh, spinnedVerts, parameters, edgeCenter)
        elif parameters["rotateCenter"] == 'Spin':
            rotatedVerts = self.rotateArcAroundSpinAxis(bm, mesh, spinnedVerts, parameters, chosenSpinCenter)
        elif parameters["rotateCenter"] == 'V1':
            rotatedVerts = self.rotateArcAroundSpinAxis(bm, mesh, spinnedVerts, parameters, edge.verts[0].co)
        elif parameters["rotateCenter"] == 'V2':
            rotatedVerts = self.rotateArcAroundSpinAxis(bm, mesh, spinnedVerts, parameters, edge.verts[1].co)

        offsetVerts = self.offsetArcPerpendicular(bm, mesh, rotatedVerts, edge, parameters)
        offsetVerts2 = self.offsetArcParallel(bm, mesh, offsetVerts, edge, parameters)
        ellipticVerts = self.makeElliptic(bm, mesh, offsetVerts2, parameters)
        self.rotateArcAroundEdge(bm, mesh, ellipticVerts, parameters)

        if parameters["connectArcWithEdge"]:
            self.connectArcTogetherWithEdge(edge, offsetVerts2, bm, mesh, parameters)
        return offsetVerts2

    def connectArcTogetherWithEdge(self, edge, arcVertices, bm, mesh, parameters):
        lastVert = len(arcVertices) - 1
        if parameters["drawArcCenters"]:
            lastVert = lastVert - 1  # center gets added as last vert of arc
        edgeV1 = edge.verts[0].co
        edgeV2 = edge.verts[1].co
        arcV1 = arcVertices[0].co
        arcV2 = arcVertices[lastVert].co

        bmv1 = bm.verts.new(edgeV1)
        bmv2 = bm.verts.new(arcV1)

        bmv3 = bm.verts.new(edgeV2)
        bmv4 = bm.verts.new(arcV2)

        if parameters["connectArcWithEdgeFlip"] == False:
            bme = bm.edges.new([bmv1, bmv2])
            bme2 = bm.edges.new([bmv3, bmv4])
        else:
            bme = bm.edges.new([bmv1, bmv4])
            bme2 = bm.edges.new([bmv3, bmv2])
        self.sel.refreshMesh(bm, mesh)

    def connectScaledEdgesWithBaseEdge(self, scaledEdges, baseEdges, bm, mesh):
        for i in range(0, len(scaledEdges)):
            scaledEdgeV1 = scaledEdges[i].verts[0].co
            baseEdgeV1 = baseEdges[i].verts[0].co
            scaledEdgeV2 = scaledEdges[i].verts[1].co
            baseEdgeV2 = baseEdges[i].verts[1].co

            bmv1 = bm.verts.new(baseEdgeV1)
            bmv2 = bm.verts.new(scaledEdgeV1)
            bme = bm.edges.new([bmv1, bmv2])

            bmv3 = bm.verts.new(scaledEdgeV2)
            bmv4 = bm.verts.new(baseEdgeV2)
            bme = bm.edges.new([bmv3, bmv4])
        self.sel.refreshMesh(bm, mesh)

    def connectArcsTogether(self, arcs, bm, mesh, parameters):
        for i in range(0, len(arcs) - 1):
            if arcs[i] == None or arcs[i + 1] == None:  # in case on XZ or YZ there are no arcs drawn
                return
            lastVert = len(arcs[i]) - 1
            if parameters["drawArcCenters"]:
                lastVert = lastVert - 1  # center gets added as last vert of arc
            # take last vert of arc i and first vert of arc i+1

            V1 = arcs[i][lastVert].co
            V2 = arcs[i + 1][0].co

            if parameters["connectArcsFlip"]:
                V1 = arcs[i][0].co
                V2 = arcs[i + 1][lastVert].co

            bmv1 = bm.verts.new(V1)
            bmv2 = bm.verts.new(V2)
            bme = bm.edges.new([bmv1, bmv2])

        # connect last arc and first one
        lastArcId = len(arcs) - 1
        lastVertIdOfLastArc = len(arcs[lastArcId]) - 1
        if parameters["drawArcCenters"]:
            lastVertIdOfLastArc = lastVertIdOfLastArc - 1  # center gets added as last vert of arc
        V1 = arcs[lastArcId][lastVertIdOfLastArc].co
        V2 = arcs[0][0].co
        if parameters["connectArcsFlip"]:
            V1 = arcs[lastArcId][0].co
            V2 = arcs[0][lastVertIdOfLastArc].co

        bmv1 = bm.verts.new(V1)
        bmv2 = bm.verts.new(V2)
        bme = bm.edges.new([bmv1, bmv2])

        self.sel.refreshMesh(bm, mesh)

    def offsetArcPerpendicular(self, bm, mesh, Verts, edge, parameters):
        perpendicularVector = self.getEdgePerpendicularVector(edge, parameters["plane"])
        offset = parameters["offset"]
        translation = offset * perpendicularVector

        try:
            bmesh.ops.translate(
                bm,
                verts=Verts,
                vec=translation)
        except ValueError:
            print("[Edge Roundifier]: Perpendicular translate value error - multiple vertices in list - try unchecking 'Centers'")

        indexes = [v.index for v in Verts]
        self.sel.refreshMesh(bm, mesh)
        offsetVertices = [bm.verts[i] for i in indexes]
        return offsetVertices

    def offsetArcParallel(self, bm, mesh, Verts, edge, parameters):
        edgeVector = self.getNormalizedEdgeVector(edge)
        offset = parameters["offset2"]
        translation = offset * edgeVector

        try:
            bmesh.ops.translate(
                bm,
                verts=Verts,
                vec=translation)
        except ValueError:
            print("[Edge Roundifier]: Parallel translate value error - multiple vertices in list - try unchecking 'Centers'")

        indexes = [v.index for v in Verts]
        self.sel.refreshMesh(bm, mesh)
        offsetVertices = [bm.verts[i] for i in indexes]
        return offsetVertices

    def skipThisEdge(self, V1, V2, plane):
        # Check If It is possible to spin selected verts on this plane if not exit roundifier
        if(plane == XY):
            if (V1[0] == V2[0] and V1[1] == V2[1]):
                return True
        elif(plane == YZ):
            if (V1[1] == V2[1] and V1[2] == V2[2]):
                return True
        elif(plane == XZ):
            if (V1[0] == V2[0] and V1[2] == V2[2]):
                return True
        return False

    def calculateRoundifyParams(self, edge, parameters, bm, mesh):
        # BECAUSE ALL DATA FROM MESH IS IN LOCAL COORDINATES
        # AND SPIN OPERATOR WORKS ON GLOBAL COORDINATES
        # WE FIRST NEED TO TRANSLATE ALL INPUT DATA BY VECTOR EQUAL TO ORIGIN POSITION AND THEN PERFORM CALCULATIONS
        # At least that is my understanding :) <komi3D>

        # V1 V2 stores Local Coordinates
        V1, V2, edgeVector, edgeLength, edgeCenter = self.getEdgeInfo(edge)

        debugPrintNew(d_Plane, "PLANE: " + parameters["plane"])
        lineAB = self.calc.getLineCoefficientsPerpendicularToVectorInPoint(edgeCenter, edgeVector, parameters["plane"])
        circleMidPoint = V1
        circleMidPointOnPlane = self.calc.getCircleMidPointOnPlane(V1, parameters["plane"])
        radius = parameters["radius"]

        angle = 0
        if (parameters["entryMode"] == 'Angle'):
            if (parameters["angleEnum"] != 'Other'):
                radius, angle = self.CalculateRadiusAndAngleForAnglePresets(parameters["angleEnum"], radius, angle, edgeLength)
            else:
                radius, angle = self.CalculateRadiusAndAngle(edgeLength)
        debugPrintNew(d_Radius_Angle, "RADIUS = " + str(radius) + "  ANGLE = " + str(angle))
        roots = None
        if angle != pi:  # mode other than 180
            if lineAB == None:
                roots = self.calc.getLineCircleIntersectionsWhenXPerpendicular(edgeCenter, circleMidPointOnPlane, radius, parameters["plane"])
            else:
                roots = self.calc.getLineCircleIntersections(lineAB, circleMidPointOnPlane, radius)
            if roots == None:
                debugPrint("[Edge Roundifier]: No centers were found. Change radius to higher value")
                return None
            roots = self.addMissingCoordinate(roots, V1, parameters["plane"])  # adds X, Y or Z coordinate
        else:
            roots = [edgeCenter, edgeCenter]
        debugPrintNew(d_Roots, "roots=" + str(roots))

        refObjectLocation = None
        objectLocation = bpy.context.active_object.location  # Origin Location

        if parameters["refObject"] == "ORG":
            refObjectLocation = [0, 0, 0]
        elif parameters["refObject"] == "CUR":
            refObjectLocation = bpy.context.scene.cursor_location - objectLocation
        else:
            refObjectLocation = self.calc.getEdgeReference(edge, edgeCenter, parameters["plane"])

        debugPrintNew(d_RefObject, parameters["refObject"], refObjectLocation)
        chosenSpinCenter, otherSpinCenter = self.getSpinCenterClosestToRefCenter(refObjectLocation, roots)

        if (parameters["entryMode"] == "Radius"):
            halfAngle = self.calc.getAngle(edgeCenter, chosenSpinCenter, circleMidPoint)
            angle = 2 * halfAngle[0]  # in radians
            self.a = degrees(angle)  # in degrees

        spinAxis = self.getSpinAxis(parameters["plane"])
        steps = parameters["segments"]
        angle = -angle  # rotate clockwise by default

        return [chosenSpinCenter, otherSpinCenter, spinAxis, angle, steps, refObjectLocation]

    def drawSpin(self, edge, edgeCenter, roundifyParams, parameters, bm, mesh):
        [chosenSpinCenter, otherSpinCenter, spinAxis, angle, steps, refObjectLocation] = roundifyParams

        v0org, v1org = (edge.verts[0], edge.verts[1])

        if parameters["flip"]:
            angle = -angle
            spinCenterTemp = chosenSpinCenter
            chosenSpinCenter = otherSpinCenter
            otherSpinCenter = spinCenterTemp

        if(parameters["invertAngle"]):
            if angle < 0:
                angle = two_pi + angle
            elif angle > 0:
                angle = -two_pi + angle
            else:
                angle = two_pi

        if(parameters["fullCircles"]):
            angle = two_pi

        v0 = bm.verts.new(v0org.co)

        result = bmesh.ops.spin(bm, geom=[v0], cent=chosenSpinCenter, axis=spinAxis,
                                angle=angle, steps=steps, use_duplicate=False)

        # it seems there is something wrong with last index of this spin...
        # I need to calculate the last index manually here...
        vertsLength = len(bm.verts)
        bm.verts.ensure_lookup_table()
        lastVertIndex = bm.verts[vertsLength - 1].index
        lastSpinVertIndices = self.getLastSpinVertIndices(steps, lastVertIndex)

        self.sel.refreshMesh(bm, mesh)

        alternativeLastSpinVertIndices = []
        bothSpinVertices = []
        spinVertices = []
        alternate = False

        if ((angle == pi or angle == -pi) and not parameters["bothSides"]):

            midVertexIndex = lastVertIndex - round(steps / 2)
            bm.verts.ensure_lookup_table()
            midVert = bm.verts[midVertexIndex].co

            midVertexDistance = (Vector(refObjectLocation) - Vector(midVert)).length
            midEdgeDistance = (Vector(refObjectLocation) - Vector(edgeCenter)).length

            if ((parameters["invertAngle"]) or (parameters["flip"])):
                if (midVertexDistance > midEdgeDistance):
                    alternativeLastSpinVertIndices = self.alternateSpin(bm, mesh, angle, chosenSpinCenter, spinAxis, steps, v0, v1org, lastSpinVertIndices)

            else:
                if (midVertexDistance < midEdgeDistance):
                    alternativeLastSpinVertIndices = self.alternateSpin(bm, mesh, angle, chosenSpinCenter, spinAxis, steps, v0, v1org, lastSpinVertIndices)

        elif (angle != two_pi):  # to allow full circles :)
            if (result['geom_last'][0].co - v1org.co).length > SPIN_END_THRESHOLD:
                alternativeLastSpinVertIndices = self.alternateSpin(bm, mesh, angle, chosenSpinCenter, spinAxis, steps, v0, v1org, lastSpinVertIndices)
                alternate = True

        self.sel.refreshMesh(bm, mesh)
        if alternativeLastSpinVertIndices != []:
            lastSpinVertIndices = alternativeLastSpinVertIndices

        if lastSpinVertIndices.stop <= len(bm.verts):  # make sure arc was added to bmesh
            spinVertices = [bm.verts[i] for i in lastSpinVertIndices]
            if alternativeLastSpinVertIndices != []:
                spinVertices = spinVertices + [v0]
            else:
                spinVertices = [v0] + spinVertices

        if (parameters["bothSides"]):
                # do some more testing here!!!
            if (angle == pi or angle == -pi):
                alternativeLastSpinVertIndices = self.alternateSpinNoDelete(bm, mesh, -angle, chosenSpinCenter, spinAxis, steps, v0, v1org, [])
            elif alternate:
                alternativeLastSpinVertIndices = self.alternateSpinNoDelete(bm, mesh, angle, otherSpinCenter, spinAxis, steps, v0, v1org, [])
            elif not alternate:
                alternativeLastSpinVertIndices = self.alternateSpinNoDelete(bm, mesh, -angle, otherSpinCenter, spinAxis, steps, v0, v1org, [])
            bothSpinVertices = [bm.verts[i] for i in lastSpinVertIndices]
            alternativeSpinVertices = [bm.verts[i] for i in alternativeLastSpinVertIndices]
            bothSpinVertices = [v0] + bothSpinVertices + alternativeSpinVertices
            spinVertices = bothSpinVertices

        if (parameters["fullCircles"]):
            v1 = bm.verts.new(v1org.co)
            spinVertices = spinVertices + [v1]

        if (parameters['drawArcCenters']):
            centerVert = bm.verts.new(chosenSpinCenter)
            spinVertices.append(centerVert)

        return spinVertices, [chosenSpinCenter, otherSpinCenter, spinAxis, angle, steps, refObjectLocation]

##########################################

    def deleteSpinVertices(self, bm, mesh, lastSpinVertIndices):
        verticesForDeletion = []
        bm.verts.ensure_lookup_table()
        for i in lastSpinVertIndices:
            vi = bm.verts[i]
            vi.select = True
            debugPrint(str(i) + ") " + str(vi))
            verticesForDeletion.append(vi)

        bmesh.ops.delete(bm, geom=verticesForDeletion, context=1)
        bmesh.update_edit_mesh(mesh, True)
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')

    def alternateSpinNoDelete(self, bm, mesh, angle, chosenSpinCenter, spinAxis, steps, v0, v1org, lastSpinVertIndices):
        v0prim = v0

        result2 = bmesh.ops.spin(bm, geom=[v0prim], cent=chosenSpinCenter, axis=spinAxis,
                                 angle=angle, steps=steps, use_duplicate=False)
        vertsLength = len(bm.verts)
        bm.verts.ensure_lookup_table()
        lastVertIndex2 = bm.verts[vertsLength - 1].index

        lastSpinVertIndices2 = self.getLastSpinVertIndices(steps, lastVertIndex2)
        return lastSpinVertIndices2

    def alternateSpin(self, bm, mesh, angle, chosenSpinCenter, spinAxis, steps, v0, v1org, lastSpinVertIndices):
        self.deleteSpinVertices(bm, mesh, lastSpinVertIndices)
        v0prim = v0

        result2 = bmesh.ops.spin(bm, geom=[v0prim], cent=chosenSpinCenter, axis=spinAxis,
                                 angle=-angle, steps=steps, use_duplicate=False)
        # it seems there is something wrong with last index of this spin...
        # I need to calculate the last index manually here...
        vertsLength = len(bm.verts)
        bm.verts.ensure_lookup_table()
        lastVertIndex2 = bm.verts[vertsLength - 1].index

        lastSpinVertIndices2 = self.getLastSpinVertIndices(steps, lastVertIndex2)
        # second spin also does not hit the v1org
        if (result2['geom_last'][0].co - v1org.co).length > SPIN_END_THRESHOLD:

            self.deleteSpinVertices(bm, mesh, lastSpinVertIndices2)
            self.deleteSpinVertices(bm, mesh, range(v0.index, v0.index + 1))
            return []
        else:
            return lastSpinVertIndices2

    def getLastSpinVertIndices(self, steps, lastVertIndex):
        arcfirstVertexIndex = lastVertIndex - steps + 1
        lastSpinVertIndices = range(arcfirstVertexIndex, lastVertIndex + 1)
        return lastSpinVertIndices


##################

    def rotateArcAroundSpinAxis(self, bm, mesh, vertices, parameters, edgeCenter):

        axisAngle = parameters["axisAngle"]
        plane = parameters["plane"]
        # compensate rotation center
        objectLocation = bpy.context.active_object.location
        #center = objectLocation + chosenSpinCenter
        center = objectLocation + edgeCenter

        rot = Euler((0.0, 0.0, radians(axisAngle)), 'XYZ').to_matrix()
        if plane == YZ:
            rot = Euler((radians(axisAngle), 0.0, 0.0), 'XYZ').to_matrix()
        if plane == XZ:
            rot = Euler((0.0, radians(axisAngle), 0.0), 'XYZ').to_matrix()

        indexes = [v.index for v in vertices]

        bmesh.ops.rotate(
            bm,
            cent=center,
            matrix=rot,
            verts=vertices,
            space=bpy.context.edit_object.matrix_world
        )
        self.sel.refreshMesh(bm, mesh)
        bm.verts.ensure_lookup_table()
        rotatedVertices = [bm.verts[i] for i in indexes]

        return rotatedVertices

    def deleteSpinVertices(self, bm, mesh, lastSpinVertIndices):
        verticesForDeletion = []
        bm.verts.ensure_lookup_table()
        for i in lastSpinVertIndices:
            vi = bm.verts[i]
            vi.select = True
            verticesForDeletion.append(vi)

        bmesh.ops.delete(bm, geom=verticesForDeletion, context=1)
        bmesh.update_edit_mesh(mesh, True)
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')

    def getLastSpinVertIndices(self, steps, lastVertIndex):
        arcfirstVertexIndex = lastVertIndex - steps + 1
        lastSpinVertIndices = range(arcfirstVertexIndex, lastVertIndex + 1)
        return lastSpinVertIndices

    def CalculateRadiusAndAngle(self, edgeLength):
        degAngle = self.a
        angle = radians(degAngle)
        self.r = radius = edgeLength / (2 * sin(angle / 2))
        return radius, angle

    def CalculateRadiusAndAngleForAnglePresets(self, angleEnum, initR, initA, edgeLength):
        radius = initR
        angle = initA

        if angleEnum == "180":
            self.a = 180
        elif angleEnum == "120":
            self.a = 120
        elif angleEnum == "90":
            self.a = 90
        elif angleEnum == "72":
            self.a = 72
        elif angleEnum == "60":
            self.a = 60
        elif angleEnum == "45":
            self.a = 45
        elif angleEnum == "30":
            self.a = 30
        return self.CalculateRadiusAndAngle(edgeLength)

    def getSpinCenterClosestToRefCenter(self, objLocation, roots):
        root0Distance = (Vector(objLocation) - Vector(roots[0])).length
        root1Distance = (Vector(objLocation) - Vector(roots[1])).length

        chosenId = 0
        rejectedId = 1
        if (root0Distance > root1Distance):
            chosenId = 1
            rejectedId = 0
        return roots[chosenId], roots[rejectedId]

    def addMissingCoordinate(self, roots, startVertex, plane):
        if roots != None:
            a, b = roots[0]
            c, d = roots[1]
            if plane == XY:
                roots[0] = Vector((a, b, startVertex[2]))
                roots[1] = Vector((c, d, startVertex[2]))
            if plane == YZ:
                roots[0] = Vector((startVertex[0], a, b))
                roots[1] = Vector((startVertex[0], c, d))
            if plane == XZ:
                roots[0] = Vector((a, startVertex[1], b))
                roots[1] = Vector((c, startVertex[1], d))
        return roots

    def selectEdgesAfterRoundifier(self, context, edges):
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        mesh = context.scene.objects.active.data
        bmnew = bmesh.new()
        bmnew.from_mesh(mesh)
        self.deselectEdges(bmnew)
        for selectedEdge in edges:
            for e in bmnew.edges:
                if (e.verts[0].co - selectedEdge.verts[0].co).length <= self.threshold \
                   and (e.verts[1].co - selectedEdge.verts[1].co).length <= self.threshold:
                    e.select_set(True)

        bpy.ops.object.mode_set(mode='OBJECT')
        bmnew.to_mesh(mesh)
        bmnew.free()
        bpy.ops.object.mode_set(mode='EDIT')

    def deselectEdges(self, bm):
        for edge in bm.edges:
            edge.select_set(False)

    def getSpinAxis(self, plane):
        axis = (0, 0, 1)
        if plane == YZ:
            axis = (1, 0, 0)
        if plane == XZ:
            axis = (0, 1, 0)
        return axis

    @classmethod
    def poll(cls, context):
        return (context.scene.objects.active.type == 'MESH') and (context.scene.objects.active.mode == 'EDIT')


def draw_item(self, context):
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.operator('mesh.edge_roundifier')


def register():
    bpy.utils.register_class(EdgeRoundifier)
    bpy.utils.register_class(EdgeWorksPanel)
    bpy.types.VIEW3D_MT_edit_mesh_edges.append(draw_item)


def unregister():
    bpy.utils.unregister_class(EdgeRoundifier)
    bpy.utils.unregister_class(EdgeWorksPanel)
    bpy.types.VIEW3D_MT_edit_mesh_edges.remove(draw_item)

if __name__ == "__main__":
    register()
