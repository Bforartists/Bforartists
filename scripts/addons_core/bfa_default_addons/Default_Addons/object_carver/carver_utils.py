# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import gpu
from gpu_extras.batch import batch_for_shader
import math
import sys
import random
import bmesh
from mathutils import (
    Euler,
    Matrix,
    Vector,
    Quaternion,
)
from mathutils.geometry import (
    intersect_line_plane,
)

from math import (
    sin,
    cos,
    pi,
    )

import bpy_extras

from bpy_extras import view3d_utils
from bpy_extras.view3d_utils import (
    region_2d_to_vector_3d,
    region_2d_to_location_3d,
    location_3d_to_region_2d,
)

# Cut Square
def CreateCutSquare(self, context):
    """ Create a rectangle mesh """
    far_limit = 10000.0
    faces=[]

    # Get the mouse coordinates
    coord = self.mouse_path[0][0], self.mouse_path[0][1]

    # New mesh
    me = bpy.data.meshes.new('CMT_Square')
    bm = bmesh.new()
    bm.from_mesh(me)

    # New object and link it to the scene
    ob = bpy.data.objects.new('CMT_Square', me)
    self.CurrentObj = ob
    context.collection.objects.link(ob)

    # Scene information
    region = context.region
    rv3d = context.region_data
    depth_location = region_2d_to_vector_3d(region, rv3d, coord)
    self.ViewVector = depth_location

    # Get a point on a infinite plane and its direction
    plane_normal = depth_location
    plane_direction = plane_normal.normalized()

    if self.snapCursor:
        plane_point = context.scene.cursor.location
    else:
        plane_point = self.OpsObj.location if self.OpsObj is not None else Vector((0.0, 0.0, 0.0))

    # Find the intersection of a line going thru each vertex and the infinite plane
    for v_co in self.rectangle_coord:
        vec = region_2d_to_vector_3d(region, rv3d, v_co)
        p0 = region_2d_to_location_3d(region, rv3d,v_co, vec)
        p1 = region_2d_to_location_3d(region, rv3d,v_co, vec) + plane_direction * far_limit
        faces.append(bm.verts.new(intersect_line_plane(p0, p1, plane_point, plane_direction)))

    # Update vertices index
    bm.verts.index_update()
    # New faces
    t_face = bm.faces.new(faces)
    # Set mesh
    bm.to_mesh(me)


# Cut Line
def CreateCutLine(self, context):
    """ Create a polygon mesh """
    far_limit = 10000.0
    vertices = []
    faces = []
    loc = []

    # Get the mouse coordinates
    coord = self.mouse_path[0][0], self.mouse_path[0][1]

    # New mesh
    me = bpy.data.meshes.new('CMT_Line')
    bm = bmesh.new()
    bm.from_mesh(me)

    # New object and link it to the scene
    ob = bpy.data.objects.new('CMT_Line', me)
    self.CurrentObj = ob
    context.collection.objects.link(ob)

    # Scene information
    region = context.region
    rv3d = context.region_data
    depth_location = region_2d_to_vector_3d(region, rv3d, coord)
    self.ViewVector = depth_location

    # Get a point on a infinite plane and its direction
    plane_normal = depth_location
    plane_direction = plane_normal.normalized()

    if self.snapCursor:
        plane_point = context.scene.cursor.location
    else:
        plane_point = self.OpsObj.location if self.OpsObj is not None else Vector((0.0, 0.0, 0.0))

    # Use dict to remove doubles
    # Find the intersection of a line going thru each vertex and the infinite plane
    for idx, v_co in enumerate(list(dict.fromkeys(self.mouse_path))):
        vec = region_2d_to_vector_3d(region, rv3d, v_co)
        p0 = region_2d_to_location_3d(region, rv3d,v_co, vec)
        p1 = region_2d_to_location_3d(region, rv3d,v_co, vec) + plane_direction * far_limit
        loc.append(intersect_line_plane(p0, p1, plane_point, plane_direction))
        vertices.append(bm.verts.new(loc[idx]))

        if idx > 0:
            bm.edges.new([vertices[idx-1],vertices[idx]])

        faces.append(vertices[idx])

    # Update vertices index
    bm.verts.index_update()

    # Nothing is selected, create close geometry
    if self.CreateMode:
        if self.Closed and len(vertices) > 1:
            bm.edges.new([vertices[-1], vertices[0]])
            bm.faces.new(faces)
    else:
        # Create faces if more than 2 vertices
        if len(vertices) > 1 :
            bm.edges.new([vertices[-1], vertices[0]])
            bm.faces.new(faces)

    bm.to_mesh(me)

# Cut Circle
def CreateCutCircle(self, context):
    """ Create a circle mesh """
    far_limit = 10000.0
    FacesList = []

    # Get the mouse coordinates
    mouse_pos_x = self.mouse_path[0][0]
    mouse_pos_y = self.mouse_path[0][1]
    coord = self.mouse_path[0][0], self.mouse_path[0][1]

    # Scene information
    region = context.region
    rv3d = context.region_data
    depth_location = region_2d_to_vector_3d(region, rv3d, coord)
    self.ViewVector = depth_location

    # Get a point on a infinite plane and its direction
    plane_point = context.scene.cursor.location if self.snapCursor else Vector((0.0, 0.0, 0.0))
    plane_normal = depth_location
    plane_direction = plane_normal.normalized()

    # New mesh
    me = bpy.data.meshes.new('CMT_Circle')
    bm = bmesh.new()
    bm.from_mesh(me)

    # New object and link it to the scene
    ob = bpy.data.objects.new('CMT_Circle', me)
    self.CurrentObj = ob
    context.collection.objects.link(ob)

    # Create a circle using a tri fan
    tris_fan, indices = draw_circle(self, mouse_pos_x, mouse_pos_y)

    # Remove the vertex in the center to get the outer line of the circle
    verts = tris_fan[1:]

    # Find the intersection of a line going thru each vertex and the infinite plane
    for vert in verts:
        vec = region_2d_to_vector_3d(region, rv3d, vert)
        p0 = region_2d_to_location_3d(region, rv3d, vert, vec)
        p1 = p0 + plane_direction * far_limit
        loc0 = intersect_line_plane(p0, p1, plane_point, plane_direction)
        t_v0 = bm.verts.new(loc0)
        FacesList.append(t_v0)

    bm.verts.index_update()
    bm.faces.new(FacesList)
    bm.to_mesh(me)


def create_2d_circle(self, step, radius, rotation = 0):
    """ Create the vertices of a 2d circle at (0,0) """
    verts = []
    for angle in range(0, 360, step):
        verts.append(math.cos(math.radians(angle + rotation)) * radius)
        verts.append(math.sin(math.radians(angle + rotation)) * radius)
        verts.append(0.0)
    verts.append(math.cos(math.radians(0.0 + rotation)) * radius)
    verts.append(math.sin(math.radians(0.0 + rotation)) * radius)
    verts.append(0.0)
    return(verts)


def draw_circle(self, mouse_pos_x, mouse_pos_y):
    """ Return the coordinates + indices of a circle using a triangle fan """
    tris_verts = []
    indices = []
    segments = int(360 / self.stepAngle[self.step])
    radius = self.mouse_path[1][0] - self.mouse_path[0][0]
    rotation = (self.mouse_path[1][1] - self.mouse_path[0][1]) / 2

    # Get the vertices of a 2d circle
    verts = create_2d_circle(self, self.stepAngle[self.step], radius, rotation)

    # Create the first vertex at mouse position for the center of the circle
    tris_verts.append(Vector((mouse_pos_x + self.xpos , mouse_pos_y + self.ypos)))

    # For each vertex of the circle, add the mouse position and the translation
    for idx in range(int(len(verts) / 3) - 1):
        tris_verts.append(Vector((verts[idx * 3] + mouse_pos_x + self.xpos, \
                                  verts[idx * 3 + 1] + mouse_pos_y + self.ypos)))
        i1 = idx+1
        i2 = idx+2 if idx+2 <= segments else 1
        indices.append((0,i1,i2))

    return(tris_verts, indices)

# Object dimensions (SCULPT Tools tips)
def objDiagonal(obj):
    return ((obj.dimensions[0]**2) + (obj.dimensions[1]**2) + (obj.dimensions[2]**2))**0.5


# Bevel Update
def update_bevel(context):
    selection = context.selected_objects.copy()
    active = context.active_object

    if len(selection) > 0:
        for obj in selection:
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj

            # Test object name
            # Subdive mode : Only bevel weight
            if obj.data.name.startswith("S_") or obj.data.name.startswith("S "):
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.region_to_loop()
                bpy.ops.transform.edge_bevelweight(value=1)
                bpy.ops.object.mode_set(mode='OBJECT')

            else:
                # No subdiv mode : bevel weight + Crease + Sharp
                CreateBevel(context, obj)

    bpy.ops.object.select_all(action='DESELECT')

    for obj in selection:
        obj.select_set(True)
    context.view_layer.objects.active = active

# Create bevel
def CreateBevel(context, CurrentObject):
    # Save active object
    SavActive = context.active_object

    # Test if initial object has bevel
    bevel_modifier = False
    for modifier in SavActive.modifiers:
        if modifier.name == 'Bevel':
            bevel_modifier = True

    if bevel_modifier:
        # Active "CurrentObject"
        context.view_layer.objects.active = CurrentObject

        bpy.ops.object.mode_set(mode='EDIT')

        # Edge mode
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        # Clear all
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.mark_sharp(clear=True)
        bpy.ops.transform.edge_crease(value=-1)
        bpy.ops.transform.edge_bevelweight(value=-1)

        bpy.ops.mesh.select_all(action='DESELECT')

        # Select (in radians) all 30° sharp edges
        bpy.ops.mesh.edges_select_sharp(sharpness=0.523599)
        # Apply bevel weight + Crease + Sharp to the selected edges
        bpy.ops.mesh.mark_sharp()
        bpy.ops.transform.edge_crease(value=1)
        bpy.ops.transform.edge_bevelweight(value=1)

        bpy.ops.mesh.select_all(action='DESELECT')

        bpy.ops.object.mode_set(mode='OBJECT')

        bevel_weights = CurrentObject.data.attributes["bevel_weight_edge"]
        if not bevel_weights:
            bevel_weights = CurrentObject.data.attributes.new("bevel_weight_edge", 'FLOAT', 'EDGE')
        if bevel_weights.data_type != 'FLOAT' or bevel_weights.domain != 'EDGE':
            bevel_weights = None

        for i in range(len(CurrentObject.data.edges)):
            if CurrentObject.data.edges[i].select is True:
                if bevel_weights:
                    bevel_weights.data[i] = 1.0
                CurrentObject.data.edges[i].use_edge_sharp = True

        bevel_modifier = False
        for m in CurrentObject.modifiers:
            if m.name == 'Bevel':
                bevel_modifier = True

        if bevel_modifier is False:
            mod = context.object.modifiers.new("", 'BEVEL')
            mod.limit_method = 'WEIGHT'
            mod.width = 0.01
            mod.profile = 0.699099
            mod.use_clamp_overlap = False
            mod.segments = 3
            mod.loop_slide = False

        bpy.ops.object.shade_smooth()

        context.object.data.set_sharp_from_angle(angle=1.0471975)

        # Restore the active object
        context.view_layer.objects.active = SavActive


def MoveCursor(qRot, location, self):
    """ In brush mode : Draw a circle around the brush """
    if qRot is not None:
        verts = create_2d_circle(self, 10, 1)
        self.CLR_C.clear()
        vc = Vector()
        for idx in range(int(len(verts) / 3)):
            vc.x = verts[idx * 3]
            vc.y = verts[idx * 3 + 1]
            vc.z = verts[idx * 3 + 2]
            vc = qRot @ vc
            self.CLR_C.append(vc.x)
            self.CLR_C.append(vc.y)
            self.CLR_C.append(vc.z)


def rot_axis_quat(vector1, vector2):
    """ Find the rotation (quaternion) from vector 1 to vector 2"""
    vector1 = vector1.normalized()
    vector2 = vector2.normalized()
    cosTheta = vector1.dot(vector2)
    rotationAxis = Vector((0.0, 0.0, 0.0))
    if (cosTheta < -1 + 0.001):
        v = Vector((0.0, 1.0, 0.0))
        #Get the vector at the right angles to both
        rotationAxis = vector1.cross(v)
        rotationAxis = rotationAxis.normalized()
        q = Quaternion()
        q.w = 0.0
        q.x = rotationAxis.x
        q.y = rotationAxis.y
        q.z = rotationAxis.z
    else:
        rotationAxis = vector1.cross(vector2)
        s = math.sqrt((1.0 + cosTheta) * 2.0)
        invs = 1 / s
        q = Quaternion()
        q.w = s * 0.5
        q.x = rotationAxis.x * invs
        q.y = rotationAxis.y * invs
        q.z = rotationAxis.z * invs
    return q


# Picking (template)
def Picking(context, event):
    """ Put the 3d cursor on the closest object"""

    # get the context arguments
    scene = context.scene
    region = context.region
    rv3d = context.region_data
    coord = event.mouse_region_x, event.mouse_region_y

    # get the ray from the viewport and mouse
    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
    ray_target = ray_origin + view_vector

    def visible_objects_and_duplis():
        depsgraph = context.evaluated_depsgraph_get()
        for dup in depsgraph.object_instances:
            if dup.is_instance:  # Real dupli instance
                obj = dup.instance_object.original
                yield (obj, dup.matrix.copy())
            else:  # Usual object
                obj = dup.object.original
                yield (obj, obj.matrix_world.copy())

    def obj_ray_cast(obj, matrix):
        # get the ray relative to the object
        matrix_inv = matrix.inverted()
        ray_origin_obj = matrix_inv @ ray_origin
        ray_target_obj = matrix_inv @ ray_target
        ray_direction_obj = ray_target_obj - ray_origin_obj
        # cast the ray
        success, location, normal, face_index = obj.ray_cast(ray_origin_obj, ray_direction_obj)
        if success:
            return location, normal, face_index
        return None, None, None

    # cast rays and find the closest object
    best_length_squared = -1.0
    best_obj = None

    # cast rays and find the closest object
    for obj, matrix in visible_objects_and_duplis():
        if obj.type == 'MESH':
            hit, normal, face_index = obj_ray_cast(obj, matrix)
            if hit is not None:
                hit_world = matrix @ hit
                length_squared = (hit_world - ray_origin).length_squared
                if best_obj is None or length_squared < best_length_squared:
                    scene.cursor.location = hit_world
                    best_length_squared = length_squared
                    best_obj = obj
            else:
                if best_obj is None:
                    depth_location = region_2d_to_vector_3d(region, rv3d, coord)
                    loc = region_2d_to_location_3d(region, rv3d, coord, depth_location)
                    scene.cursor.location = loc


def Pick(context, event, self, ray_max=10000.0):
    region = context.region
    rv3d = context.region_data
    coord = event.mouse_region_x, event.mouse_region_y
    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
    ray_target = ray_origin + (view_vector * ray_max)

    def obj_ray_cast(obj, matrix):
        matrix_inv = matrix.inverted()
        ray_origin_obj = matrix_inv @ ray_origin
        ray_target_obj = matrix_inv @ ray_target
        success, hit, normal, face_index = obj.ray_cast(ray_origin_obj, ray_target_obj)
        if success:
            return hit, normal, face_index
        return None, None, None

    best_length_squared = ray_max * ray_max
    best_obj = None
    for obj in self.CList:
        matrix = obj.matrix_world
        hit, normal, face_index = obj_ray_cast(obj, matrix)
        rotation = obj.rotation_euler.to_quaternion()
        if hit is not None:
            hit_world = matrix @ hit
            length_squared = (hit_world - ray_origin).length_squared
            if length_squared < best_length_squared:
                best_length_squared = length_squared
                best_obj = obj
                hits = hit_world
                ns = normal
                fs = face_index

    if best_obj is not None:
        return hits, ns, rotation

    return None, None, None

def SelectObject(self, copyobj):
    copyobj.select_set(True)

    for child in copyobj.children:
        SelectObject(self, child)

    if copyobj.parent is None:
        bpy.context.view_layer.objects.active = copyobj

# Undo
def printUndo(self):
    for l in self.UList:
        print(l)


def UndoAdd(self, type, obj):
    """ Create a backup mesh before apply the action to the object """
    if obj is None:
        return

    if type != "DUPLICATE":
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        self.UndoOps.append((obj, type, bm))
    else:
        self.UndoOps.append((obj, type, None))


def UndoListUpdate(self):
    self.UList.append((self.UndoOps.copy()))
    self.UList_Index += 1
    self.UndoOps.clear()


def Undo(self):
    if self.UList_Index < 0:
        return
    # get previous mesh
    for o in self.UList[self.UList_Index]:
        if o[1] == "MESH":
            bm = o[2]
            bm.to_mesh(o[0].data)

    SelectObjList = bpy.context.selected_objects.copy()
    Active_Obj = bpy.context.active_object
    bpy.ops.object.select_all(action='TOGGLE')

    for o in self.UList[self.UList_Index]:
        if o[1] == "REBOOL":
            o[0].select_set(True)
            o[0].hide_viewport = False

        if o[1] == "DUPLICATE":
            o[0].select_set(True)
            o[0].hide_viewport = False

    bpy.ops.object.delete(use_global=False)

    for so in SelectObjList:
        bpy.data.objects[so.name].select_set(True)
    bpy.context.view_layer.objects.active = Active_Obj

    self.UList_Index -= 1
    self.UList[self.UList_Index + 1:] = []


def duplicateObject(self):
    if self.Instantiate:
        bpy.ops.object.duplicate_move_linked(
            OBJECT_OT_duplicate={
                "linked": True,
                "mode": 'TRANSLATION',
            },
            TRANSFORM_OT_translate={
                "value": (0, 0, 0),
            },
        )
    else:
        bpy.ops.object.duplicate_move(
            OBJECT_OT_duplicate={
                "linked": False,
                "mode": 'TRANSLATION',
            },
            TRANSFORM_OT_translate={
                "value": (0, 0, 0),
            },
        )

    ob_new = bpy.context.active_object

    ob_new.location = self.CurLoc
    v = Vector()
    v.x = v.y = 0.0
    v.z = self.BrushDepthOffset
    ob_new.location += self.qRot * v

    if self.ObjectMode:
        ob_new.scale = self.ObjectBrush.scale
    if self.ProfileMode:
        ob_new.scale = self.ProfileBrush.scale

    e = Euler()
    e.x = e.y = 0.0
    e.z = self.aRotZ / 25.0

    # If duplicate with a grid, no random rotation (each mesh in the grid is already rotated randomly)
    if (self.alt is True) and ((self.nbcol + self.nbrow) < 3):
        if self.RandomRotation:
            e.z += random.random()

    qe = e.to_quaternion()
    qRot = self.qRot * qe
    ob_new.rotation_mode = 'QUATERNION'
    ob_new.rotation_quaternion = qRot
    ob_new.rotation_mode = 'XYZ'

    if (ob_new.display_type == "WIRE") and (self.BrushSolidify is False):
        ob_new.hide_viewport = True

    if self.BrushSolidify:
        ob_new.display_type = "SOLID"
        ob_new.show_in_front = False

    for o in bpy.context.selected_objects:
        UndoAdd(self, "DUPLICATE", o)

    if len(bpy.context.selected_objects) > 0:
        bpy.ops.object.select_all(action='TOGGLE')
    for o in self.all_sel_obj_list:
        o.select_set(True)

    bpy.context.view_layer.objects.active = self.OpsObj


def update_grid(self, context):
    """
    Thanks to batFINGER for his help :
    source : http://blender.stackexchange.com/questions/55864/multiple-meshes-not-welded-with-pydata
    """
    verts = []
    edges = []
    faces = []
    numface = 0

    if self.nbcol < 1:
        self.nbcol = 1
    if self.nbrow < 1:
        self.nbrow = 1
    if self.gapx < 0:
        self.gapx = 0
    if self.gapy < 0:
        self.gapy = 0

    # Get the data from the profils or the object
    if self.ProfileMode:
        brush = bpy.data.objects.new(
                    self.Profils[self.nProfil][0],
                    bpy.data.meshes[self.Profils[self.nProfil][0]]
                    )
        obj = bpy.data.objects["CT_Profil"]
        obfaces = brush.data.polygons
        obverts = brush.data.vertices
        lenverts = len(obverts)
    else:
        brush = bpy.data.objects["CarverBrushCopy"]
        obj = context.selected_objects[0]
        obverts = brush.data.vertices
        obfaces = brush.data.polygons
        lenverts = len(brush.data.vertices)

    # Gap between each row / column
    gapx = self.gapx
    gapy = self.gapy

    # Width of each row / column
    widthx = brush.dimensions.x * self.scale_x
    widthy = brush.dimensions.y * self.scale_y

    # Compute the corners so the new object will be always at the center
    left = -((self.nbcol - 1) * (widthx + gapx)) / 2
    start = -((self.nbrow - 1) * (widthy + gapy)) / 2

    for i in range(self.nbrow * self.nbcol):
        row = i % self.nbrow
        col = i // self.nbrow
        startx = left + ((widthx + gapx) * col)
        starty = start + ((widthy + gapy) * row)

        # Add random rotation
        if (self.RandomRotation) and not (self.GridScaleX or self.GridScaleY):
            rotmat = Matrix.Rotation(math.radians(360 * random.random()), 4, 'Z')
            for v in obverts:
                v.co = v.co @ rotmat

        verts.extend([((v.co.x - startx, v.co.y - starty, v.co.z)) for v in obverts])
        faces.extend([[v + numface * lenverts for v in p.vertices] for p in obfaces])
        numface += 1

    # Update the mesh
    # Create mesh data
    mymesh = bpy.data.meshes.new("CT_Profil")
    # Generate mesh data
    mymesh.from_pydata(verts, edges, faces)
    # Calculate the edges
    mymesh.update(calc_edges=True)
    # Update data
    obj.data = mymesh
    # Make the object active to remove doubles
    context.view_layer.objects.active = obj


def boolean_operation(bool_type="DIFFERENCE"):
    ActiveObj = bpy.context.active_object
    sel_index = 0 if bpy.context.selected_objects[0] != bpy.context.active_object else 1

    # bpy.ops.object.modifier_apply(modifier="CT_SOLIDIFY")
    bool_name = "CT_" + bpy.context.selected_objects[sel_index].name
    BoolMod = ActiveObj.modifiers.new(bool_name, "BOOLEAN")
    BoolMod.object = bpy.context.selected_objects[sel_index]
    BoolMod.operation = bool_type
    bpy.context.selected_objects[sel_index].display_type = 'WIRE'
    while ActiveObj.modifiers.find(bool_name) > 0:
        bpy.ops.object.modifier_move_up(modifier=bool_name)


def Rebool(context, self):

    target_obj = context.active_object

    Brush = context.selected_objects[1]
    Brush.display_type = "WIRE"

    #Deselect all
    bpy.ops.object.select_all(action='TOGGLE')

    target_obj.display_type = "SOLID"
    target_obj.select_set(True)
    bpy.ops.object.duplicate()

    rebool_obj = context.active_object

    m = rebool_obj.modifiers.new("CT_INTERSECT", "BOOLEAN")
    m.operation = "INTERSECT"
    m.object = Brush

    m = target_obj.modifiers.new("CT_DIFFERENCE", "BOOLEAN")
    m.operation = "DIFFERENCE"
    m.object = Brush

    for mb in target_obj.modifiers:
        if mb.type == 'BEVEL':
            mb.show_viewport = False

    if self.ObjectBrush or self.ProfileBrush:
        rebool_obj.show_in_front = False
        try:
            bpy.ops.object.modifier_apply(modifier="CT_SOLIDIFY")
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.report({'ERROR'}, str(exc_value))

    if self.dont_apply_boolean is False:
        try:
            bpy.ops.object.modifier_apply(modifier="CT_INTERSECT")
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.report({'ERROR'}, str(exc_value))

    bpy.ops.object.select_all(action='TOGGLE')

    for mb in target_obj.modifiers:
        if mb.type == 'BEVEL':
            mb.show_viewport = True

    context.view_layer.objects.active = target_obj
    target_obj.select_set(True)
    if self.dont_apply_boolean is False:
        try:
            bpy.ops.object.modifier_apply(modifier="CT_DIFFERENCE")
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.report({'ERROR'}, str(exc_value))

    bpy.ops.object.select_all(action='TOGGLE')

    rebool_obj.select_set(True)

def createMeshFromData(self):
    if self.Profils[self.nProfil][0] not in bpy.data.meshes:
        # Create mesh and object
        me = bpy.data.meshes.new(self.Profils[self.nProfil][0])
        # Create mesh from given verts, faces.
        me.from_pydata(self.Profils[self.nProfil][2], [], self.Profils[self.nProfil][3])
        me.validate(verbose=True, clean_customdata=True)
        # Update mesh with new data
        me.update()

    if "CT_Profil" not in bpy.data.objects:
        ob = bpy.data.objects.new("CT_Profil", bpy.data.meshes[self.Profils[self.nProfil][0]])
        ob.location = Vector((0.0, 0.0, 0.0))

        # Link object to scene and make active
        bpy.context.collection.objects.link(ob)
        bpy.context.view_layer.update()
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        ob.location = Vector((10000.0, 0.0, 0.0))
        ob.display_type = "WIRE"

        self.SolidifyPossible = True
    else:
        bpy.data.objects["CT_Profil"].data = bpy.data.meshes[self.Profils[self.nProfil][0]]

def Selection_Save_Restore(self):
    if "CT_Profil" in bpy.data.objects:
        Selection_Save(self)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects["CT_Profil"].select_set(True)
        bpy.context.view_layer.objects.active = bpy.data.objects["CT_Profil"]
        if bpy.data.objects["CT_Profil"] in self.all_sel_obj_list:
            self.all_sel_obj_list.remove(bpy.data.objects["CT_Profil"])
        bpy.ops.object.delete(use_global=False)
        Selection_Restore(self)

def Selection_Save(self):
    obj_name = getattr(bpy.context.active_object, "name", None)
    self.all_sel_obj_list = bpy.context.selected_objects.copy()
    self.save_active_obj = obj_name


def Selection_Restore(self):
    for o in self.all_sel_obj_list:
        o.select_set(True)
    if self.save_active_obj:
        bpy.context.view_layer.objects.active = bpy.data.objects.get(self.save_active_obj, None)

def Snap_Cursor(self, context, event, mouse_pos):
    """ Find the closest position on the overlay grid and snap the mouse on it """
    # Get the context arguments
    region = context.region
    rv3d = context.region_data

    # Get the VIEW3D area
    for i, a in enumerate(context.screen.areas):
        if a.type == 'VIEW_3D':
            space = context.screen.areas[i].spaces.active

    # Get the grid overlay for the VIEW_3D
    grid_scale = space.overlay.grid_scale
    grid_subdivisions = space.overlay.grid_subdivisions

    # Use the grid scale and subdivision to get the increment
    increment = (grid_scale / grid_subdivisions)
    half_increment = increment / 2

    # Convert the 2d location of the mouse in 3d
    for index, loc in enumerate(reversed(mouse_pos)):
        mouse_loc_3d = region_2d_to_location_3d(region, rv3d, loc, (0, 0, 0))

        # Get the remainder from the mouse location and the ratio
        # Test if the remainder > to the half of the increment
        for i in range(3):
            modulo = mouse_loc_3d[i] % increment
            if modulo < half_increment:
                modulo = - modulo
            else:
                modulo = increment - modulo

            # Add the remainder to get the closest location on the grid
            mouse_loc_3d[i] = mouse_loc_3d[i] + modulo

        # Get the snapped 2d location
        snap_loc_2d = location_3d_to_region_2d(region, rv3d, mouse_loc_3d)

        # Replace the last mouse location by the snapped location
        if len(self.mouse_path) > 0:
            self.mouse_path[len(self.mouse_path) - (index + 1) ] = tuple(snap_loc_2d)

def mini_grid(self, context, color):
    """ Draw a snap mini grid around the cursor based on the overlay grid"""
    # Get the context arguments
    region = context.region
    rv3d = context.region_data

    # Get the VIEW3D area
    for i, a in enumerate(context.screen.areas):
        if a.type == 'VIEW_3D':
            space = context.screen.areas[i].spaces.active
            screen_height = context.screen.areas[i].height
            screen_width = context.screen.areas[i].width

    #Draw the snap grid, only in ortho view
    if not space.region_3d.is_perspective :
        grid_scale = space.overlay.grid_scale
        grid_subdivisions = space.overlay.grid_subdivisions
        increment = (grid_scale / grid_subdivisions)

        # Get the 3d location of the mouse forced to a snap value in the operator
        mouse_coord = self.mouse_path[len(self.mouse_path) - 1]

        snap_loc = region_2d_to_location_3d(region, rv3d, mouse_coord, (0, 0, 0))

        # Add the increment to get the closest location on the grid
        snap_loc[0] += increment
        snap_loc[1] += increment

        # Get the 2d location of the snap location
        snap_loc = location_3d_to_region_2d(region, rv3d, snap_loc)
        origin = location_3d_to_region_2d(region, rv3d, (0,0,0))

        # Get the increment value
        snap_value = snap_loc[0] - mouse_coord[0]

        grid_coords = []

        # Draw lines on X and Z axis from the cursor through the screen
        grid_coords = [
        (0, mouse_coord[1]), (screen_width, mouse_coord[1]),
        (mouse_coord[0], 0), (mouse_coord[0], screen_height)
        ]

        # Draw a mlini grid around the cursor to show the snap options
        grid_coords += [
        (mouse_coord[0] + snap_value, mouse_coord[1] + 25 + snap_value),
        (mouse_coord[0] + snap_value, mouse_coord[1] - 25 - snap_value),
        (mouse_coord[0] + 25 + snap_value, mouse_coord[1] + snap_value),
        (mouse_coord[0] - 25 - snap_value, mouse_coord[1] + snap_value),
        (mouse_coord[0] - snap_value, mouse_coord[1] + 25 + snap_value),
        (mouse_coord[0] - snap_value, mouse_coord[1] - 25 - snap_value),
        (mouse_coord[0] + 25 + snap_value, mouse_coord[1] - snap_value),
        (mouse_coord[0] - 25 - snap_value, mouse_coord[1] - snap_value),
        ]
        draw_shader(self, color, 0.3, 'LINES', grid_coords, size=2)


def draw_shader(self, color, alpha, type, coords, size=1, indices=None):
    """ Create a batch for a draw type """
    gpu.state.blend_set('ALPHA')
    if type =='POINTS':
        gpu.state.program_point_size_set(False)
        gpu.state.point_size_set(size)
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    else:
        shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        shader.uniform_float("viewportSize", gpu.state.viewport_get()[2:])
        shader.uniform_float("lineWidth", 1.0)

    try:
        shader.uniform_float("color", (color[0], color[1], color[2], alpha))
        batch = batch_for_shader(shader, type, {"pos": coords}, indices=indices)
        batch.draw(shader)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        self.report({'ERROR'}, str(exc_value))

    gpu.state.point_size_set(1.0)
    gpu.state.blend_set('NONE')
