# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; version 2
#  of the License.
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
    "name": "UV Align/Distribute",
    "author": "Rebellion (Luca Carella)",
    "version": (1, 3),
    "blender": (2, 7, 3),
    "location": "UV/Image editor > Tool Panel, UV/Image editor UVs > menu",
    "description": "Set of tools to help UV alignment\distribution",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/UV/UV_Align_Distribution",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "UV"}

import math
from collections import defaultdict

import bmesh
import bpy
import mathutils
from bpy.props import EnumProperty, BoolProperty, FloatProperty


# Globals:
bpy.types.Scene.relativeItems = EnumProperty(
    items=[
        ('UV_SPACE', 'Uv Space', 'Align to UV space'),
        ('ACTIVE', 'Active Face', 'Align to active face\island'),
        ('CURSOR', 'Cursor', 'Align to cursor')],
    name="Relative to")

bpy.types.Scene.selectionAsGroup = BoolProperty(
    name="Selection as group",
    description="Treat selection as group",
    default=False)

bm = None
uvlayer = None


def InitBMesh():
    global bm
    global uvlayer
    bm = bmesh.from_edit_mesh(bpy.context.edit_object.data)
    bm.faces.ensure_lookup_table()
    uvlayer = bm.loops.layers.uv.active


def update():
    bmesh.update_edit_mesh(bpy.context.edit_object.data, False, False)
    # bm.to_mesh(bpy.context.object.data)
    # bm.free()


def GBBox(islands):
    minX = minY = 1000
    maxX = maxY = -1000
    for island in islands:
        for face_id in island:
            face = bm.faces[face_id]
            for loop in face.loops:
                u, v = loop[uvlayer].uv
                minX = min(u, minX)
                minY = min(v, minY)
                maxX = max(u, maxX)
                maxY = max(v, maxY)

    return mathutils.Vector((minX, minY)), mathutils.Vector((maxX, maxY))


def GBBoxCenter(islands):
    minX = minY = 1000
    maxX = maxY = -1000
    for island in islands:
        for face_id in island:
            face = bm.faces[face_id]
            for loop in face.loops:
                u, v = loop[uvlayer].uv
                minX = min(u, minX)
                minY = min(v, minY)
                maxX = max(u, maxX)
                maxY = max(v, maxY)

    return (mathutils.Vector((minX, minY)) +
            mathutils.Vector((maxX, maxY))) / 2


def BBox(island):
    minX = minY = 1000
    maxX = maxY = -1000
    # for island in islands:
    # print(island)
    for face_id in island:
        face = bm.faces[face_id]
        for loop in face.loops:
            u, v = loop[uvlayer].uv
            minX = min(u, minX)
            minY = min(v, minY)
            maxX = max(u, maxX)
            maxY = max(v, maxY)

    return mathutils.Vector((minX, minY)), mathutils.Vector((maxX, maxY))


def BBoxCenter(island):
    minX = minY = 1000
    maxX = maxY = -1000
    # for island in islands:
    for face_id in island:
        face = bm.faces[face_id]
        for loop in face.loops:
            u, v = loop[uvlayer].uv
            minX = min(u, minX)
            minY = min(v, minY)
            maxX = max(u, maxX)
            maxY = max(v, maxY)

    return (mathutils.Vector((minX, minY)) +
            mathutils.Vector((maxX, maxY))) / 2


def islandAngle(island):
    uvList = []
    for face_id in island:
        face = bm.faces[face_id]
        for loop in face.loops:
            uv = loop[bm.loops.layers.uv.active].uv
            uvList.append(uv)

    angle = math.degrees(mathutils.geometry.box_fit_2d(uvList))
    return angle


def moveIslands(vector, island):
    for face_id in island:
        face = bm.faces[face_id]
        for loop in face.loops:
            loop[bm.loops.layers.uv.active].uv += vector


def rotateIsland(island, angle):
    rad = math.radians(angle)
    center = BBoxCenter(island)

    for face_id in island:
        face = bm.faces[face_id]
        for loop in face.loops:
            uv_act = bm.loops.layers.uv.active
            x, y = loop[uv_act].uv
            xt = x - center.x
            yt = y - center.y
            xr = (xt * math.cos(rad)) - (yt * math.sin(rad))
            yr = (xt * math.sin(rad)) + (yt * math.cos(rad))
            # loop[bm.loops.layers.uv.active].uv = trans
            loop[bm.loops.layers.uv.active].uv.x = xr + center.x
            loop[bm.loops.layers.uv.active].uv.y = yr + center.y
            # print('fired')


def scaleIsland(island, scaleX, scaleY):
    scale = mathutils.Vector((scaleX, scaleY))
    center = BBoxCenter(island)

    for face_id in island:
        face = bm.faces[face_id]
        for loop in face.loops:
            x = loop[bm.loops.layers.uv.active].uv.x
            y = loop[bm.loops.layers.uv.active].uv.y
            xt = x - center.x
            yt = y - center.y
            xs = xt * scaleX
            ys = yt * scaleY
            loop[bm.loops.layers.uv.active].uv.x = xs + center.x
            loop[bm.loops.layers.uv.active].uv.y = ys + center.y


def vectorDistance(vector1, vector2):
    return math.sqrt(
        math.pow((vector2.x - vector1.x), 2) +
        math.pow((vector2.y - vector1.y), 2))


def matchIsland(active, thresold, island):
    for active_face_id in active:
        active_face = bm.faces[active_face_id]

        for active_loop in active_face.loops:
            activeUVvert = active_loop[bm.loops.layers.uv.active].uv

            for face_id in island:
                face = bm.faces[face_id]

                for loop in face.loops:
                    selectedUVvert = loop[bm.loops.layers.uv.active].uv
                    dist = vectorDistance(selectedUVvert, activeUVvert)

                    if dist <= thresold:
                        loop[bm.loops.layers.uv.active].uv = activeUVvert


def getTargetPoint(context, islands):
    if context.scene.relativeItems == 'UV_SPACE':
        return mathutils.Vector((0.0, 0.0)), mathutils.Vector((1.0, 1.0))
    elif context.scene.relativeItems == 'ACTIVE':
        activeIsland = islands.activeIsland()
        if not activeIsland:
            return None
        else:
            return BBox(activeIsland)
    elif context.scene.relativeItems == 'CURSOR':
        return context.space_data.cursor_location,\
            context.space_data.cursor_location


def IslandSpatialSortX(islands):
    spatialSort = []
    for island in islands:
        spatialSort.append((BBoxCenter(island).x, island))
    spatialSort.sort()
    return spatialSort


def IslandSpatialSortY(islands):
    spatialSort = []
    for island in islands:
        spatialSort.append((BBoxCenter(island).y, island))
    spatialSort.sort()
    return spatialSort


def averageIslandDist(islands):
    distX = 0
    distY = 0
    counter = 0

    for i in range(len(islands)):
        elem1 = BBox(islands[i][1])[1]
        try:
            elem2 = BBox(islands[i + 1][1])[0]
            counter += 1
        except:
            break

        distX += elem2.x - elem1.x
        distY += elem2.y - elem1.y

    avgDistX = distX / counter
    avgDistY = distY / counter
    return mathutils.Vector((avgDistX, avgDistY))


def islandSize(island):
    bbox = BBox(island)
    sizeX = bbox[1].x - bbox[0].x
    sizeY = bbox[1].y - bbox[0].y

    return sizeX, sizeY


class MakeIslands():

    def __init__(self):
        InitBMesh()
        global bm
        global uvlayer

        self.face_to_verts = defaultdict(set)
        self.vert_to_faces = defaultdict(set)
        self.selectedIsland = set()

        for face in bm.faces:
            for loop in face.loops:
                id = loop[uvlayer].uv.to_tuple(5), loop.vert.index
                self.face_to_verts[face.index].add(id)
                self.vert_to_faces[id].add(face.index)
                if face.select:
                    if loop[uvlayer].select:
                        self.selectedIsland.add(face.index)

    def addToIsland(self, face_id):
        if face_id in self.faces_left:
            # add the face itself
            self.current_island.append(face_id)
            self.faces_left.remove(face_id)
            # and add all faces that share uvs with this face
            verts = self.face_to_verts[face_id]
            for vert in verts:
                # print('looking at vert {}'.format(vert))
                connected_faces = self.vert_to_faces[vert]
                if connected_faces:
                    for face in connected_faces:
                        self.addToIsland(face)

    def getIslands(self):
        self.islands = []
        self.faces_left = set(self.face_to_verts.keys())
        while len(self.faces_left) > 0:
            face_id = list(self.faces_left)[0]
            self.current_island = []
            self.addToIsland(face_id)
            self.islands.append(self.current_island)

        return self.islands

    def activeIsland(self):
        for island in self.islands:
            try:
                if bm.faces.active.index in island:
                    return island
            except:
                return None

    def selectedIslands(self):
        _selectedIslands = []
        for island in self.islands:
            if not self.selectedIsland.isdisjoint(island):
                _selectedIslands.append(island)
        return _selectedIslands


# #####################
# OPERATOR
# #####################

class OperatorTemplate(bpy.types.Operator):

    @classmethod
    def poll(cls, context):
        return not (context.scene.tool_settings.use_uv_select_sync)


#####################
# ALIGN
#####################

class AlignSXMargin(OperatorTemplate):

    """Align left margin"""
    bl_idname = "uv.align_left_margin"
    bl_label = "Align left margin"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        makeIslands = MakeIslands()
        islands = makeIslands.getIslands()
        selectedIslands = makeIslands.selectedIslands()

        targetElement = getTargetPoint(context, makeIslands)
        if not targetElement:
            self.report({"ERROR"}, "No active face")
            return {"CANCELLED"}

        if context.scene.selectionAsGroup:
            groupBox = GBBox(selectedIslands)
            if context.scene.relativeItems == 'ACTIVE':
                selectedIslands.remove(makeIslands.activeIsland())
            for island in selectedIslands:
                vector = mathutils.Vector((targetElement[0].x - groupBox[0].x,
                                           0.0))
                moveIslands(vector, island)

        else:
            for island in selectedIslands:
                vector = mathutils.Vector(
                    (targetElement[0].x - BBox(island)[0].x, 0.0))
                moveIslands(vector, island)

        update()
        return {'FINISHED'}


class AlignRxMargin(OperatorTemplate):

    """Align right margin"""
    bl_idname = "uv.align_right_margin"
    bl_label = "Align right margin"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        makeIslands = MakeIslands()
        islands = makeIslands.getIslands()
        selectedIslands = makeIslands.selectedIslands()

        targetElement = getTargetPoint(context, makeIslands)
        if not targetElement:
            self.report({"ERROR"}, "No active face")
            return {"CANCELLED"}

        if context.scene.selectionAsGroup:
            groupBox = GBBox(selectedIslands)
            if context.scene.relativeItems == 'ACTIVE':
                selectedIslands.remove(makeIslands.activeIsland())
            for island in selectedIslands:
                vector = mathutils.Vector((targetElement[1].x - groupBox[1].x,
                                           0.0))
                moveIslands(vector, island)

        else:
            for island in selectedIslands:
                vector = mathutils.Vector(
                    (targetElement[1].x - BBox(island)[1].x, 0.0))
                moveIslands(vector, island)

        update()
        return {'FINISHED'}


class AlignVAxis(OperatorTemplate):

    """Align vertical axis"""
    bl_idname = "uv.align_vertical_axis"
    bl_label = "Align vertical axis"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        makeIslands = MakeIslands()
        islands = makeIslands.getIslands()
        selectedIslands = makeIslands.selectedIslands()

        targetElement = getTargetPoint(context, makeIslands)
        if not targetElement:
            self.report({"ERROR"}, "No active face")
            return {"CANCELLED"}
        targetCenter = (targetElement[0] + targetElement[1]) / 2
        if context.scene.selectionAsGroup:
            groupBoxCenter = GBBoxCenter(selectedIslands)
            if context.scene.relativeItems == 'ACTIVE':
                selectedIslands.remove(makeIslands.activeIsland())
            for island in selectedIslands:
                vector = mathutils.Vector(
                    (targetCenter.x - groupBoxCenter.x, 0.0))
                moveIslands(vector, island)

        else:
            for island in selectedIslands:
                vector = mathutils.Vector(
                    (targetCenter.x - BBoxCenter(island).x, 0.0))
                moveIslands(vector, island)

        update()
        return {'FINISHED'}


##################################################
class AlignTopMargin(OperatorTemplate):

    """Align top margin"""
    bl_idname = "uv.align_top_margin"
    bl_label = "Align top margin"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        makeIslands = MakeIslands()
        islands = makeIslands.getIslands()
        selectedIslands = makeIslands.selectedIslands()

        targetElement = getTargetPoint(context, makeIslands)
        if not targetElement:
            self.report({"ERROR"}, "No active face")
            return {"CANCELLED"}
        if context.scene.selectionAsGroup:
            groupBox = GBBox(selectedIslands)
            if context.scene.relativeItems == 'ACTIVE':
                selectedIslands.remove(makeIslands.activeIsland())
            for island in selectedIslands:
                vector = mathutils.Vector(
                    (0.0, targetElement[1].y - groupBox[1].y))
                moveIslands(vector, island)

        else:
            for island in selectedIslands:
                vector = mathutils.Vector(
                    (0.0, targetElement[1].y - BBox(island)[1].y))
                moveIslands(vector, island)

        update()
        return {'FINISHED'}


class AlignLowMargin(OperatorTemplate):

    """Align low margin"""
    bl_idname = "uv.align_low_margin"
    bl_label = "Align low margin"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        makeIslands = MakeIslands()
        islands = makeIslands.getIslands()
        selectedIslands = makeIslands.selectedIslands()

        targetElement = getTargetPoint(context, makeIslands)
        if not targetElement:
            self.report({"ERROR"}, "No active face")
            return {"CANCELLED"}
        if context.scene.selectionAsGroup:
            groupBox = GBBox(selectedIslands)
            if context.scene.relativeItems == 'ACTIVE':
                selectedIslands.remove(makeIslands.activeIsland())
            for island in selectedIslands:
                vector = mathutils.Vector(
                    (0.0, targetElement[0].y - groupBox[0].y))
                moveIslands(vector, island)

        else:
            for island in selectedIslands:
                vector = mathutils.Vector(
                    (0.0, targetElement[0].y - BBox(island)[0].y))
                moveIslands(vector, island)

        update()
        return {'FINISHED'}


class AlignHAxis(OperatorTemplate):

    """Align horizontal axis"""
    bl_idname = "uv.align_horizontal_axis"
    bl_label = "Align horizontal axis"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        makeIslands = MakeIslands()
        islands = makeIslands.getIslands()
        selectedIslands = makeIslands.selectedIslands()

        targetElement = getTargetPoint(context, makeIslands)
        if not targetElement:
            self.report({"ERROR"}, "No active face")
            return {"CANCELLED"}
        targetCenter = (targetElement[0] + targetElement[1]) / 2

        if context.scene.selectionAsGroup:
            groupBoxCenter = GBBoxCenter(selectedIslands)
            if context.scene.relativeItems == 'ACTIVE':
                selectedIslands.remove(makeIslands.activeIsland())
            for island in selectedIslands:
                vector = mathutils.Vector(
                    (0.0, targetCenter.y - groupBoxCenter.y))
                moveIslands(vector, island)

        else:
            for island in selectedIslands:
                vector = mathutils.Vector(
                    (0.0, targetCenter.y - BBoxCenter(island).y))
                moveIslands(vector, island)

        update()
        return {'FINISHED'}


#########################################
class AlignRotation(OperatorTemplate):

    """Align island rotation """
    bl_idname = "uv.align_rotation"
    bl_label = "Align island rotation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        makeIslands = MakeIslands()
        islands = makeIslands.getIslands()
        selectedIslands = makeIslands.selectedIslands()
        activeIsland = makeIslands.activeIsland()
        if not activeIsland:
            self.report({"ERROR"}, "No active face")
            return {"CANCELLED"}
        activeAngle = islandAngle(activeIsland)

        for island in selectedIslands:
            uvAngle = islandAngle(island)
            deltaAngle = activeAngle - uvAngle
            deltaAngle = round(-deltaAngle, 5)
            rotateIsland(island, deltaAngle)

        update()
        return {'FINISHED'}


class EqualizeScale(OperatorTemplate):

    """Equalize the islands scale to the active one"""
    bl_idname = "uv.equalize_scale"
    bl_label = "Equalize Scale"
    bl_options = {'REGISTER', 'UNDO'}
    
    keepProportions = BoolProperty(
    name="Keep Proportions",
    description="Mantain proportions during scaling",
    default=False)
    
    useYaxis = BoolProperty(
    name="Use Y axis",
    description="Use y axis as scale reference, default is x",
    default=False)
    
    def execute(self, context):
        makeIslands = MakeIslands()
        islands = makeIslands.getIslands()
        selectedIslands = makeIslands.selectedIslands()
        activeIsland = makeIslands.activeIsland()

        if not activeIsland:
            self.report({"ERROR"}, "No active face")
            return {"CANCELLED"}

        activeSize = islandSize(activeIsland)
        selectedIslands.remove(activeIsland)

        for island in selectedIslands:
            size = islandSize(island)
            scaleX = activeSize[0] / size[0]
            scaleY = activeSize[1] / size[1]
            
            if self.keepProportions:
                if self.useYaxis:
                    scaleX = scaleY
                else:
                    scaleY = scaleX
                                 
            scaleIsland(island, scaleX, scaleY)

        update()
        return {"FINISHED"}
    
    def draw(self,context):
        layout = self.layout      
        layout.prop(self, "keepProportions")        
        if self.keepProportions:
            layout.prop(self,"useYaxis")


############################
# DISTRIBUTION
############################
class DistributeLEdgesH(OperatorTemplate):

    """Distribute left edges equidistantly horizontally"""
    bl_idname = "uv.distribute_ledges_horizontally"
    bl_label = "Distribute Left Edges Horizontally"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        makeIslands = MakeIslands()
        islands = makeIslands.getIslands()
        selectedIslands = makeIslands.selectedIslands()

        if len(selectedIslands) < 3:
            return {'CANCELLED'}

        islandSpatialSort = IslandSpatialSortX(selectedIslands)
        uvFirstX = BBox(islandSpatialSort[0][1])[0].x
        uvLastX = BBox(islandSpatialSort[-1][1])[0].x

        distX = uvLastX - uvFirstX

        deltaDist = distX / (len(selectedIslands) - 1)

        islandSpatialSort.pop(0)
        islandSpatialSort.pop(-1)

        pos = uvFirstX + deltaDist

        for island in islandSpatialSort:
            vec = mathutils.Vector((pos - BBox(island[1])[0].x, 0.0))
            pos += deltaDist
            moveIslands(vec, island[1])
        update()
        return {"FINISHED"}


class DistributeCentersH(OperatorTemplate):

    """Distribute centers equidistantly horizontally"""
    bl_idname = "uv.distribute_center_horizontally"
    bl_label = "Distribute Centers Horizontally"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        makeIslands = MakeIslands()
        islands = makeIslands.getIslands()
        selectedIslands = makeIslands.selectedIslands()

        if len(selectedIslands) < 3:
            return {'CANCELLED'}

        islandSpatialSort = IslandSpatialSortX(selectedIslands)
        uvFirstX = min(islandSpatialSort)
        uvLastX = max(islandSpatialSort)

        distX = uvLastX[0] - uvFirstX[0]

        deltaDist = distX / (len(selectedIslands) - 1)

        islandSpatialSort.pop(0)
        islandSpatialSort.pop(-1)

        pos = uvFirstX[0] + deltaDist

        for island in islandSpatialSort:
            vec = mathutils.Vector((pos - BBoxCenter(island[1]).x, 0.0))
            pos += deltaDist
            moveIslands(vec, island[1])
        update()
        return {"FINISHED"}


class DistributeREdgesH(OperatorTemplate):

    """Distribute right edges equidistantly horizontally"""
    bl_idname = "uv.distribute_redges_horizontally"
    bl_label = "Distribute Right Edges Horizontally"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        makeIslands = MakeIslands()
        islands = makeIslands.getIslands()
        selectedIslands = makeIslands.selectedIslands()

        if len(selectedIslands) < 3:
            return {'CANCELLED'}

        islandSpatialSort = IslandSpatialSortX(selectedIslands)
        uvFirstX = BBox(islandSpatialSort[0][1])[1].x
        uvLastX = BBox(islandSpatialSort[-1][1])[1].x

        distX = uvLastX - uvFirstX

        deltaDist = distX / (len(selectedIslands) - 1)

        islandSpatialSort.pop(0)
        islandSpatialSort.pop(-1)

        pos = uvFirstX + deltaDist

        for island in islandSpatialSort:
            vec = mathutils.Vector((pos - BBox(island[1])[1].x, 0.0))
            pos += deltaDist
            moveIslands(vec, island[1])
        update()
        return {"FINISHED"}


class DistributeTEdgesV(OperatorTemplate):

    """Distribute top edges equidistantly vertically"""
    bl_idname = "uv.distribute_tedges_vertically"
    bl_label = "Distribute Top Edges Vertically"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        makeIslands = MakeIslands()
        islands = makeIslands.getIslands()
        selectedIslands = makeIslands.selectedIslands()

        if len(selectedIslands) < 3:
            return {'CANCELLED'}

        islandSpatialSort = IslandSpatialSortY(selectedIslands)
        uvFirstX = BBox(islandSpatialSort[0][1])[1].y
        uvLastX = BBox(islandSpatialSort[-1][1])[1].y

        distX = uvLastX - uvFirstX

        deltaDist = distX / (len(selectedIslands) - 1)

        islandSpatialSort.pop(0)
        islandSpatialSort.pop(-1)

        pos = uvFirstX + deltaDist

        for island in islandSpatialSort:
            vec = mathutils.Vector((0.0, pos - BBox(island[1])[1].y))
            pos += deltaDist
            moveIslands(vec, island[1])
        update()
        return {"FINISHED"}


class DistributeCentersV(OperatorTemplate):

    """Distribute centers equidistantly vertically"""
    bl_idname = "uv.distribute_center_vertically"
    bl_label = "Distribute Centers Vertically"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        makeIslands = MakeIslands()
        islands = makeIslands.getIslands()
        selectedIslands = makeIslands.selectedIslands()

        if len(selectedIslands) < 3:
            return {'CANCELLED'}

        islandSpatialSort = IslandSpatialSortY(selectedIslands)
        uvFirst = BBoxCenter(islandSpatialSort[0][1]).y
        uvLast = BBoxCenter(islandSpatialSort[-1][1]).y

        dist = uvLast - uvFirst

        deltaDist = dist / (len(selectedIslands) - 1)

        islandSpatialSort.pop(0)
        islandSpatialSort.pop(-1)

        pos = uvFirst + deltaDist

        for island in islandSpatialSort:
            vec = mathutils.Vector((0.0, pos - BBoxCenter(island[1]).y))
            pos += deltaDist
            moveIslands(vec, island[1])
        update()
        return {"FINISHED"}


class DistributeBEdgesV(OperatorTemplate):

    """Distribute bottom edges equidistantly vertically"""
    bl_idname = "uv.distribute_bedges_vertically"
    bl_label = "Distribute Bottom Edges Vertically"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        makeIslands = MakeIslands()
        islands = makeIslands.getIslands()
        selectedIslands = makeIslands.selectedIslands()

        if len(selectedIslands) < 3:
            return {'CANCELLED'}

        islandSpatialSort = IslandSpatialSortY(selectedIslands)
        uvFirst = BBox(islandSpatialSort[0][1])[0].y
        uvLast = BBox(islandSpatialSort[-1][1])[0].y

        dist = uvLast - uvFirst

        deltaDist = dist / (len(selectedIslands) - 1)

        islandSpatialSort.pop(0)
        islandSpatialSort.pop(-1)

        pos = uvFirst + deltaDist

        for island in islandSpatialSort:
            vec = mathutils.Vector((0.0, pos - BBox(island[1])[0].y))
            pos += deltaDist
            moveIslands(vec, island[1])
        update()
        return {"FINISHED"}


class EqualizeHGap(OperatorTemplate):

    """Equalize horizontal gap between island"""
    bl_idname = "uv.equalize_horizontal_gap"
    bl_label = "Equalize Horizontal Gap"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        makeIslands = MakeIslands()
        islands = makeIslands.getIslands()
        selectedIslands = makeIslands.selectedIslands()

        if len(selectedIslands) < 3:
            return {'CANCELLED'}

        islandSpatialSort = IslandSpatialSortX(selectedIslands)

        averageDist = averageIslandDist(islandSpatialSort)

        for i in range(len(islandSpatialSort)):
            if islandSpatialSort.index(islandSpatialSort[i + 1]) == \
                    islandSpatialSort.index(islandSpatialSort[-1]):
                break
            elem1 = BBox(islandSpatialSort[i][1])[1].x
            elem2 = BBox(islandSpatialSort[i + 1][1])[0].x

            dist = elem2 - elem1
            increment = averageDist.x - dist

            vec = mathutils.Vector((increment, 0.0))
            island = islandSpatialSort[i + 1][1]
            moveIslands(vec, islandSpatialSort[i + 1][1])
        update()
        return {"FINISHED"}


class EqualizeVGap(OperatorTemplate):

    """Equalize vertical gap between island"""
    bl_idname = "uv.equalize_vertical_gap"
    bl_label = "Equalize Vertical Gap"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        makeIslands = MakeIslands()
        islands = makeIslands.getIslands()
        selectedIslands = makeIslands.selectedIslands()

        if len(selectedIslands) < 3:
            return {'CANCELLED'}

        islandSpatialSort = IslandSpatialSortY(selectedIslands)

        averageDist = averageIslandDist(islandSpatialSort)

        for i in range(len(islandSpatialSort)):
            if islandSpatialSort.index(islandSpatialSort[i + 1]) ==\
                    islandSpatialSort.index(islandSpatialSort[-1]):
                break
            elem1 = BBox(islandSpatialSort[i][1])[1].y
            elem2 = BBox(islandSpatialSort[i + 1][1])[0].y

            dist = elem2 - elem1

            increment = averageDist.y - dist

            vec = mathutils.Vector((0.0, increment))
            island = islandSpatialSort[i + 1][1]

            moveIslands(vec, islandSpatialSort[i + 1][1])
        update()
        return {"FINISHED"}

##############
# SPECIALS
##############


class MatchIsland(OperatorTemplate):

    """Match UV Island by moving their vertex"""
    bl_idname = "uv.match_island"
    bl_label = "Match Island"
    bl_options = {'REGISTER', 'UNDO'}

    threshold = FloatProperty(
        name="Threshold",
        description="Threshold for island matching",
        default=0.1,
        min=0,
        max=1,
        soft_min=0.01,
        soft_max=1,
        step=1,
        precision=2)

    def execute(self, context):
        makeIslands = MakeIslands()
        islands = makeIslands.getIslands()
        selectedIslands = makeIslands.selectedIslands()
        activeIsland = makeIslands.activeIsland()
        
        if not activeIsland:
            self.report({"ERROR"}, "No active face")
            return {"CANCELLED"}
        
        if len(selectedIslands) < 2:
            return {'CANCELLED'}

        selectedIslands.remove(activeIsland)

        for island in selectedIslands:
            matchIsland(activeIsland, self.threshold, island)

        update()
        return{'FINISHED'}


##############
#   UI
##############
class IMAGE_PT_align_distribute(bpy.types.Panel):
    bl_label = "Align\Distribute"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "Tools"

    @classmethod
    def poll(cls, context):
        sima = context.space_data
        return sima.show_uvedit and \
            not (context.tool_settings.use_uv_sculpt
                 or context.scene.tool_settings.use_uv_select_sync)

    def draw(self, context):
        scn = context.scene
        layout = self.layout
        layout.prop(scn, "relativeItems")
        layout.prop(scn, "selectionAsGroup")

        layout.separator()
        layout.label(text="Align:")

        box = layout.box()
        row = box.row(True)
        row.operator("uv.align_left_margin", "Left")
        row.operator("uv.align_vertical_axis", "VAxis")
        row.operator("uv.align_right_margin", "Right")
        row = box.row(True)
        row.operator("uv.align_top_margin", "Top")
        row.operator("uv.align_horizontal_axis", "HAxis")
        row.operator("uv.align_low_margin", "Low")

        row = layout.row()
        row.operator("uv.align_rotation", "Rotation")
        row.operator("uv.equalize_scale", "Eq. Scale")

        layout.separator()
        # Another Panel??
        layout.label(text="Distribute:")

        box = layout.box()

        row = box.row(True)
        row.operator("uv.distribute_ledges_horizontally", "LEdges")

        row.operator("uv.distribute_center_horizontally",
                     "HCenters")

        row.operator("uv.distribute_redges_horizontally",
                     "RCenters")

        row = box.row(True)
        row.operator("uv.distribute_tedges_vertically", "TEdges")
        row.operator("uv.distribute_center_vertically", "VCenters")
        row.operator("uv.distribute_bedges_vertically", "BEdges")

        row = layout.row(True)
        row.operator("uv.equalize_horizontal_gap", "Eq. HGap")
        row.operator("uv.equalize_vertical_gap", "Eq. VGap")

        layout.separator()
        layout.label("Others:")
        row = layout.row()
        layout.operator("uv.match_island")


# Registration
classes = (
    IMAGE_PT_align_distribute,
    AlignSXMargin,
    AlignRxMargin,
    AlignVAxis,
    AlignTopMargin,
    AlignLowMargin,
    AlignHAxis,
    AlignRotation,
    DistributeLEdgesH,
    DistributeCentersH,
    DistributeREdgesH,
    DistributeTEdgesV,
    DistributeCentersV,
    DistributeBEdgesV,
    EqualizeHGap,
    EqualizeVGap,
    EqualizeScale,
    MatchIsland)


def register():
    for item in classes:
        bpy.utils.register_class(item)
    # bpy.utils.register_manual_map(add_object_manual_map)
    # bpy.types.INFO_MT_mesh_add.append(add_object_button)


def unregister():
    for item in classes:
        bpy.utils.unregister_class(item)
    # bpy.utils.unregister_manual_map(add_object_manual_map)
    # bpy.types.INFO_MT_mesh_add.remove(add_object_button)


if __name__ == "__main__":
    register()

