import bpy
import mathutils
from bpy_extras import view3d_utils
from mathutils import Vector



def RayCastForScene(context, event):
    scene = bpy.context.scene
    region = context.region
    rv3d = context.region_data
    coord = event.mouse_region_x, event.mouse_region_y
    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
    start = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
    
    
    #Raycast
    hit, location, normal, index, object, matrix= scene.ray_cast(start,view_vector)

    
    #If hit something in the scene return, if not then Check the Grid (if not grid then a depth locaiton?)
    if hit:
        #Returns, the location of the hit, The normal of the hit, and the world rotation for the hit.
        return location, normal, normal.to_track_quat('Z', 'Y').to_euler(), 'OBJECT' 
    else:
        #Check the grid.
        planehit = CastToPlaneFromCamera(context, event,(0, 0, 0), (0, 0, 1))
        
        
        
        planedirection = planehit - start
        a1 = planedirection.angle(view_vector) 
        a1d = a1 * 180 / 3.14
        
        if not bpy.context.space_data.region_3d.is_perspective:
            max_creation_dist = 100000000
        else:
            user_preferences = context.user_preferences
            addon_prefs = user_preferences.addons[__package__].preferences   
            max_creation_dist = addon_prefs.Max_Click_Dist
        
        #If the point is not close enough or behind the camera just do a location 500 units from the camera.
        if a1d > 90 or planedirection.length > max_creation_dist:          
            vv = view_vector.normalized()
            vv.x = vv.x * 1000
            vv.y = vv.y * 1000
            vv.z = vv.z * 1000
            distloc = start + vv     
            
            pAxis, axisName, axisDifference = GetBestViewAxis(context)
            #If they are in one of the Views and in ortho then make the object on center grid for that view

            #if not bpy.context.space_data.region_3d.is_perspective:
            
            if axisDifference > 87:# or  not bpy.context.space_data.region_3d.is_perspective:
                if axisName == 'X':
                    distloc.x = 0
                if axisName == 'Y':
                    distloc.y = 0
                if axisName == 'Z':
                    distloc.z = 0
            
            #Return a point in the vector of the camera, an up normal, and a set rotation same as theplane hit.
            return distloc,  pAxis, pAxis.to_track_quat('Z', 'Y').to_euler(), 'SPACE' 
                
        #Return the location the mouse intersects with Grid plane, The normal of the Grid, and the Rotation of the grid.
        return planehit, (0,0,1), Vector((0,0,0)).to_track_quat('Z', 'Y').to_euler(), 'GRID'
    
def getUnitScale():
    #Set unit scales
    if bpy.context.scene.unit_settings.system == 'NONE':
        scene_scale = 1
    else:
        scene_scale = bpy.context.scene.unit_settings.scale_length
    unitSize = bpy.context.space_data.grid_scale / scene_scale
    if bpy.context.scene.unit_settings.system == 'IMPERIAL':
        unitSize = (bpy.context.space_data.grid_scale / scene_scale) / 3.28
    return unitSize


def PointOnGrid(point):
    unitSize = getUnitScale()
    newLoc = Vector((round(point.x / unitSize) * unitSize, round(point.y / unitSize) * unitSize, round(point.z / unitSize) * unitSize))
    return newLoc

def GetBestViewAxis(context):
    #Gets the axis closest to cameras view vector.
    region = context.region
    rv3d = context.region_data
    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, (region.width/2.0, region.height/2.0))    
    xAxis = Vector((1, 0, 0))
    yAxis = Vector((0, 1, 0))
    zAxis = Vector((0, 0, 1))
    a1 = xAxis.angle(view_vector)
    a1d = abs((a1 * 180 / 3.14) - 90)
    a2 = yAxis.angle(view_vector)
    a2d = abs((a2 * 180 / 3.14) - 90)
    a3 = zAxis.angle(view_vector)
    a3d = abs((a3 * 180 / 3.14) - 90)
    
    A = max(a1d, a2d,a3d)
    
    if A == a1d:
        dir = -1
        if a1 * 180 / 3.14 > 90:
            dir = 1
        return Vector((dir, 0, 0)), 'X', abs((a1 * 180 / 3.14) - 90)
    if A == a2d:
        dir = -1
        if a2 * 180 / 3.14 > 90:
            dir = 1
        return Vector((0, dir, 0)), 'Y', abs((a2 * 180 / 3.14) - 90)
    if A == a3d:
        dir = -1
        if a3 * 180 / 3.14 > 90:
            dir = 1
        return Vector((0, 0, dir)), 'Z', abs((a3 * 180 / 3.14) - 90)


def CastToPlaneFromCamera(context, event, origin, normal):
    region = context.region
    rv3d = context.region_data
    coord = event.mouse_region_x, event.mouse_region_y
    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
    start = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
    
    
    #Plane intersect
    lineend = view_vector
    lineend.x = lineend.x * 1000000000
    lineend.y = lineend.y * 1000000000
    lineend.z = lineend.z * 1000000000

    planehit = mathutils.geometry.intersect_line_plane(start, lineend, origin, normal)
    return planehit

def bridgeVertLoops(loop1, loop2, close):

    faces = []

    if len(loop1) != len(loop2):
        return None

    for i in range(len(loop1) -1):
        face = (loop1[i], loop1[i+1], loop2[i+1], loop2[i])
        faces.append(face)

    if close:
        faces.append((loop1[-1], loop1[0], loop2[0], loop2[-1]))
    
    return faces
