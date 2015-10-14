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
    "name": "Discombobulator",
    "description": "Its job is to easily add scifi details to a surface to create nice-looking space-ships or futuristic cities.",
    "author": "Evan J. Rosky (syrux), Chichiri, Jace Priester",
    "version": (0,2),
    "blender": (2, 71, 0),
    "location": "View3D > Toolshelf > Tools Tab",
    "warning": 'Beta',
    'wiki_url': 'http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts',
    'tracker_url': 'https://developer.blender.org/maniphest/task/create/?project=3&type=Bug',
    "category": "Mesh"}
 
import bpy
import random
import mathutils
import math
from mathutils import *

doprots = True
 
# Datas in which we will build the new discombobulated mesh
nPolygons = []
nVerts = []
Verts = []
Polygons = []
dVerts = []
dPolygons = []
i_prots = [] # index of the top polygons on whow we will generate the doodads
i_dood_type = [] # type of doodad (given by index of the doodad obj)
 
bpy.types.Scene.DISC_doodads = []
 
def randnum(a, b):
    return random.random()*(b-a)+a
 
def randVertex(a, b, c, d, Verts):
    """Return a vector of a random vertex on a quad-polygon"""
    i = random.randint(1,2)
    A, B, C, D = 0, 0, 0, 0
    if(a==1):
        A, B, C, D = a, b, c, d
    else:
        A, B, C, D = a, d, c, b
   
    i = randnum(0.1, 0.9)
   

    vecAB=Verts[B]-Verts[A]
    E=Verts[A]+vecAB*i
   
    vecDC=Verts[C]-Verts[D]
    F=Verts[D]+vecDC*i
   
    i = randnum(0.1, 0.9)
    vecEF=F-E
    
    O=E+vecEF*i
    return O
 
################################ Protusions ###################################
 
def fill_older_datas(verts, polygon):
    """ Specifically coded to be called by the function addProtusionToPolygon, its sets up a tuple which contains the vertices from the base and the top of the protusions. """
    temp_vertices = []  
    temp_vertices.append(verts[polygon[0]].copy())
    temp_vertices.append(verts[polygon[1]].copy())
    temp_vertices.append(verts[polygon[2]].copy())
    temp_vertices.append(verts[polygon[3]].copy())
    temp_vertices.append(verts[polygon[0]].copy())
    temp_vertices.append(verts[polygon[1]].copy())
    temp_vertices.append(verts[polygon[2]].copy())
    temp_vertices.append(verts[polygon[3]].copy())
    return temp_vertices
   
def extrude_top(temp_vertices, normal, height):
    """ This function extrude the polygon composed of the four first members of the tuple temp_vertices along the normal multiplied by the height of the extrusion."""
    j = 0
    while j < 3:  
        temp_vertices[0][j]+=normal[j]*height
        temp_vertices[1][j]+=normal[j]*height
        temp_vertices[2][j]+=normal[j]*height
        temp_vertices[3][j]+=normal[j]*height
        j+=1
 
def scale_top(temp_vertices, center, normal, height, scale_ratio):
    """ This function scale the polygon composed of the four first members of the tuple temp_vertices. """
    vec1 = [0, 0, 0]
    vec2 = [0, 0, 0]
    vec3 = [0, 0, 0]
    vec4 = [0, 0, 0]
   
    j = 0
    while j < 3:
        center[j]+=normal[j]*height
        vec1[j] = temp_vertices[0][j] - center[j]
        vec2[j] = temp_vertices[1][j] - center[j]
        vec3[j] = temp_vertices[2][j] - center[j]
        vec4[j] = temp_vertices[3][j] - center[j]
        temp_vertices[0][j] = center[j] + vec1[j]*(1-scale_ratio)
        temp_vertices[1][j] = center[j] + vec2[j]*(1-scale_ratio)
        temp_vertices[2][j] = center[j] + vec3[j]*(1-scale_ratio)
        temp_vertices[3][j] = center[j] + vec4[j]*(1-scale_ratio)
        j+=1
 
def add_prot_polygons(temp_vertices):
    """ Specifically coded to be called by addProtusionToPolygon, this function put the data from the generated protusion at the end the tuples Verts and Polygons, which will later used to generate the final mesh. """
    global Verts
    global Polygons
    global i_prots
   
    findex = len(Verts)
    Verts+=temp_vertices
   
    polygontop = [findex+0, findex+1, findex+2, findex+3]
    polygon1 = [findex+0, findex+1, findex+5, findex+4]
    polygon2 = [findex+1, findex+2, findex+6, findex+5]
    polygon3 = [findex+2, findex+3, findex+7, findex+6]
    polygon4 = [findex+3, findex+0, findex+4, findex+7]
   
    Polygons.append(polygontop)
    i_prots.append(len(Polygons)-1)
    Polygons.append(polygon1)
    Polygons.append(polygon2)
    Polygons.append(polygon3)
    Polygons.append(polygon4)
       
def addProtusionToPolygon(obpolygon, verts, minHeight, maxHeight, minTaper, maxTaper):
    """Create a protusion from the polygon "obpolygon" of the original object and use several values sent by the user. It calls in this order the following functions:
       - fill_older_data;
       - extrude_top;
       - scale_top;
       - add_prot_polygons;
   """
    # some useful variables
    polygon = obpolygon.vertices
    polygontop = polygon
    polygon1 = []
    polygon2 = []
    polygon3 = []
    polygon4 = []
    vertices = []
    tVerts = list(fill_older_datas(verts, polygon)) # list of temp vertices
    height = randnum(minHeight, maxHeight) # height of generated protusion
    scale_ratio = randnum(minTaper, maxTaper)
   
    # extrude the top polygon
    extrude_top(tVerts, obpolygon.normal, height)
    # Now, we scale, the top polygon along its normal
    scale_top(tVerts, GetPolyCentroid(obpolygon,verts), obpolygon.normal, height, scale_ratio)
    # Finally, we add the protusions to the list of polygons
    add_prot_polygons(tVerts)
 
################################## Divide a polygon ##################################
 
def divide_one(list_polygons, list_vertices, verts, polygon, findex):
    """ called by divide_polygon, to generate a polygon from one polygon, maybe I could simplify this process """
    temp_vertices = []
    temp_vertices.append(verts[polygon[0]].copy())
    temp_vertices.append(verts[polygon[1]].copy())
    temp_vertices.append(verts[polygon[2]].copy())
    temp_vertices.append(verts[polygon[3]].copy())
   
    list_vertices+=temp_vertices
       
    list_polygons.append([findex+0, findex+1, findex+2, findex+3])
 
def divide_two(list_polygons, list_vertices, verts, polygon, findex):
    """ called by divide_polygon, to generate two polygons from one polygon and add them to the list of polygons and vertices which form the discombobulated mesh"""
    temp_vertices = []
    temp_vertices.append(verts[polygon[0]].copy())
    temp_vertices.append(verts[polygon[1]].copy())
    temp_vertices.append(verts[polygon[2]].copy())
    temp_vertices.append(verts[polygon[3]].copy())
    temp_vertices.append((verts[polygon[0]]+verts[polygon[1]])/2)
    temp_vertices.append((verts[polygon[2]]+verts[polygon[3]])/2)
       
    list_vertices+=temp_vertices
       
    list_polygons.append([findex+0, findex+4, findex+5, findex+3])
    list_polygons.append([findex+1, findex+2, findex+5, findex+4])

def divide_three(list_polygons, list_vertices, verts, polygon, findex, center):
    """ called by divide_polygon, to generate three polygons from one polygon and add them to the list of polygons and vertices which form the discombobulated mesh"""
    temp_vertices = []
    temp_vertices.append(verts[polygon[0]].copy())
    temp_vertices.append(verts[polygon[1]].copy())
    temp_vertices.append(verts[polygon[2]].copy())
    temp_vertices.append(verts[polygon[3]].copy())
    temp_vertices.append((verts[polygon[0]]+verts[polygon[1]])/2)
    temp_vertices.append((verts[polygon[2]]+verts[polygon[3]])/2)
    temp_vertices.append((verts[polygon[1]]+verts[polygon[2]])/2)
    temp_vertices.append(center.copy())
       
    list_vertices+=temp_vertices
       
    list_polygons.append([findex+0, findex+4, findex+5, findex+3])
    list_polygons.append([findex+1, findex+6, findex+7, findex+4])
    list_polygons.append([findex+6, findex+2, findex+5, findex+7])
  
def divide_four(list_polygons, list_vertices, verts, polygon, findex, center):
    """ called by divide_polygon, to generate four polygons from one polygon and add them to the list of polygons and vertices which form the discombobulated mesh"""
    temp_vertices = []
    temp_vertices.append(verts[polygon[0]].copy())
    temp_vertices.append(verts[polygon[1]].copy())
    temp_vertices.append(verts[polygon[2]].copy())
    temp_vertices.append(verts[polygon[3]].copy())
    temp_vertices.append((verts[polygon[0]]+verts[polygon[1]])/2)
    temp_vertices.append((verts[polygon[2]]+verts[polygon[3]])/2)
    temp_vertices.append((verts[polygon[1]]+verts[polygon[2]])/2)
    temp_vertices.append(center.copy())
    temp_vertices.append((verts[polygon[0]]+verts[polygon[3]])/2)
    temp_vertices.append(center.copy())
   
    list_vertices+=temp_vertices
       
    list_polygons.append([findex+0, findex+4, findex+7, findex+8])
    list_polygons.append([findex+1, findex+6, findex+7, findex+4])
    list_polygons.append([findex+6, findex+2, findex+5, findex+7])
    list_polygons.append([findex+8, findex+7, findex+5, findex+3])
   
def dividepolygon(obpolygon, verts, number):
    """Divide the poly into the wanted number of polygons"""
    global nPolygons
    global nVerts
   
    poly = obpolygon.vertices
    tVerts = []
   
    if(number==1):
        divide_one(nPolygons, nVerts, verts, poly, len(nVerts))
    elif(number==2):
        divide_two(nPolygons, nVerts, verts, poly, len(nVerts))
    elif(number==3):
        divide_three(nPolygons, nVerts, verts, poly, len(nVerts), GetPolyCentroid(obpolygon,verts))
    elif(number==4):
        divide_four(nPolygons, nVerts, verts, poly, len(nVerts), GetPolyCentroid(obpolygon,verts))
   
############################### Discombobulate ################################

def GetPolyCentroid(obpolygon,allvertcoords):
    centroid=mathutils.Vector((0,0,0))
    for vindex in obpolygon.vertices:
        centroid+=mathutils.Vector(allvertcoords[vindex])
    centroid/=len(obpolygon.vertices)
    return centroid
 
def division(obpolygons, verts, sf1, sf2, sf3, sf4):
    """Function to divide each of the selected polygons"""
    divide = []
    if(sf1): divide.append(1)
    if(sf2): divide.append(2)
    if(sf3): divide.append(3)
    if(sf4): divide.append(4)
    for poly in obpolygons:
        if(poly.select == True and len(poly.vertices)==4):
            a = random.randint(0, len(divide)-1)
            dividepolygon(poly, verts, divide[a])
 
def protusion(obverts, obpolygons, minHeight, maxHeight, minTaper, maxTaper):
    """function to generate the protusions"""
    verts = []
    for vertex in obverts:
        verts.append(vertex.co)
           
    for polygon in obpolygons:
        if(polygon.select == True):
            if(len(polygon.vertices) == 4):
                addProtusionToPolygon(polygon, verts, minHeight, maxHeight, minTaper, maxTaper)
 
def test_v2_near_v1(v1, v2):
    if(v1.x - 0.1 <= v2.x <= v1.x + 0.1
        and v1.y - 0.1 <= v2.y <= v1.y + 0.1
        and v1.z - 0.1 <= v2.z <= v1.z + 0.1):
        return True
   
    return False
 
def angle_between_nor(nor_orig, nor_result):
    angle = math.acos(nor_orig.dot(nor_result))
    axis = nor_orig.cross(nor_result).normalized()
   
    q = mathutils.Quaternion()
    q.x = axis.x*math.sin(angle/2)
    q.y = axis.y*math.sin(angle/2)
    q.z = axis.z*math.sin(angle/2)
    q.w = math.cos(angle/2)
   
    return q
 
def doodads(object1, mesh1, dmin, dmax):
    """function to generate the doodads"""
    global dVerts
    global dPolygons
    i = 0
    # on parcoure cette boucle pour ajouter des doodads a toutes les polygons
    # english translation: this loops adds doodads to all polygons
    while(i<len(object1.data.polygons)):
        if object1.data.polygons[i].select==False:
            continue
        doods_nbr = random.randint(dmin, dmax)
        j = 0
        while(j<=doods_nbr):
            origin_dood = randVertex(object1.data.polygons[i].vertices[0], object1.data.polygons[i].vertices[1], object1.data.polygons[i].vertices[2], object1.data.polygons[i].vertices[3], Verts)
            type_dood = random.randint(0, len(bpy.context.scene.DISC_doodads)-1)
            polygons_add = []
            verts_add = []
           
            # First we have to apply scaling and rotation to the mesh
            bpy.ops.object.select_pattern(pattern=bpy.context.scene.DISC_doodads[type_dood],extend=False)
            bpy.context.scene.objects.active=bpy.data.objects[bpy.context.scene.DISC_doodads[type_dood]]
            bpy.ops.object.transform_apply(rotation=True, scale=True)
           
            for polygon in bpy.data.objects[bpy.context.scene.DISC_doodads[type_dood]].data.polygons:
                polygons_add.append(polygon.vertices)
            for vertex in bpy.data.objects[bpy.context.scene.DISC_doodads[type_dood]].data.vertices:
                verts_add.append(vertex.co.copy())
            normal_original_polygon = object1.data.polygons[i].normal
           
            nor_def = mathutils.Vector((0.0, 0.0, 1.0))
            qr = nor_def.rotation_difference(normal_original_polygon.normalized())
           
            case_z = False
            if(test_v2_near_v1(nor_def, -normal_original_polygon)):
                case_z = True
                qr = mathutils.Quaternion((0.0, 0.0, 0.0, 0.0))
            #qr = angle_between_nor(nor_def, normal_original_polygon)
            for vertex in verts_add:
                vertex.rotate(qr)
                vertex+=origin_dood
            findex = len(dVerts)
            for polygon in polygons_add:
                dPolygons.append([polygon[0]+findex, polygon[1]+findex, polygon[2]+findex, polygon[3]+findex])
                i_dood_type.append(bpy.data.objects[bpy.context.scene.DISC_doodads[type_dood]].name)
            for vertex in verts_add:
                dVerts.append(vertex)
            j+=1
        i+=5
       
def protusions_repeat(object1, mesh1, r_prot):

        for j in i_prots:
            if j<len(object1.data.polygons):
                object1.data.polygons[j].select=True
            else:
                print("Warning: hit end of polygons in object1")
 
# add material to discombobulated mesh
def setMatProt(discObj, origObj, sideProtMat, topProtMat):
    # First we put the materials in their slots
    bpy.ops.object.select_pattern(pattern = discObj.name,extend=False)
    bpy.context.scene.objects.active=bpy.data.objects[discObj.name]
    try:
        origObj.material_slots[topProtMat]
        origObj.material_slots[sideProtMat]
    except:
        return
        
    bpy.ops.object.material_slot_add()
    bpy.ops.object.material_slot_add()
    discObj.material_slots[0].material = origObj.material_slots[topProtMat].material
    discObj.material_slots[1].material = origObj.material_slots[sideProtMat].material
   
    # Then we assign materials to protusions
    for polygon in discObj.data.polygons:
        if polygon.index in i_prots:
            polygon.material_index = 0
        else:
            polygon.material_index = 1
 
def setMatDood(doodObj):
    # First we add the materials slots
    bpy.ops.object.select_pattern(pattern = doodObj.name,extend=False)
    bpy.context.scene.objects.active=doodObj
    for name in bpy.context.scene.DISC_doodads:
        try:
            bpy.ops.object.material_slot_add()
            doodObj.material_slots[-1].material = bpy.data.objects[name].material_slots[0].material
            for polygon in doodObj.data.polygons:
                if i_dood_type[polygon.index] == name:
                    polygon.material_index = len(doodObj.material_slots)-1
        except:
            print()
           
           
def clean_doodads():
    current_doodads=list(bpy.context.scene.DISC_doodads)
    
    for name in current_doodads:
        if name not in bpy.data.objects:
            bpy.context.scene.DISC_doodads.remove(name)
            

def discombobulate(minHeight, maxHeight, minTaper, maxTaper, sf1, sf2, sf3, sf4, dmin, dmax, r_prot, sideProtMat, topProtMat, isLast):
    global doprots
    global nVerts
    global nPolygons
    global Verts
    global Polygons
    global dVerts
    global dPolygons
    global i_prots
    
   
    bpy.ops.object.mode_set(mode="OBJECT")
    
    
    #start by cleaning up doodads that don't exist anymore
    clean_doodads()
    
    
    # Create the discombobulated mesh
    mesh = bpy.data.meshes.new("tmp")
    object = bpy.data.objects.new("tmp", mesh)
    bpy.context.scene.objects.link(object)
   
    # init final verts and polygons tuple
    nPolygons = []
    nVerts = []
    Polygons = []
    Verts = []
    dPolygons = []
    dVerts = []
   
    origObj = bpy.context.active_object
   
    # There we collect the rotation, translation and scaling datas from the original mesh
    to_translate = bpy.context.active_object.location
    to_scale     = bpy.context.active_object.scale
    to_rotate    = bpy.context.active_object.rotation_euler
   
    # First, we collect all the informations we will need from the previous mesh        
    obverts = bpy.context.active_object.data.vertices
    obpolygons = bpy.context.active_object.data.polygons
    verts = []
    for vertex in obverts:
        verts.append(vertex.co)
   
    division(obpolygons, verts, sf1, sf2, sf3, sf4)
       
    # Fill in the discombobulated mesh with the new polygons
    mesh.from_pydata(nVerts, [], nPolygons)
    mesh.update(calc_edges = True)
   
    # Reload the datas
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.object.select_pattern(pattern = object.name,extend=False)
    bpy.context.scene.objects.active=bpy.data.objects[object.name]
    obverts = bpy.context.active_object.data.vertices
    obpolygons = bpy.context.active_object.data.polygons
   
    protusion(obverts, obpolygons, minHeight, maxHeight, minTaper, maxTaper)
   
    # Fill in the discombobulated mesh with the new polygons
    mesh1 = bpy.data.meshes.new("discombobulated_object")
    object1 = bpy.data.objects.new("discombobulated_mesh", mesh1)
    bpy.context.scene.objects.link(object1)
    mesh1.from_pydata(Verts, [], Polygons)
    mesh1.update(calc_edges = True)
   
   
    # Set the material's of discombobulated object
    setMatProt(object1, origObj, sideProtMat, topProtMat)
   
    bpy.ops.object.select_pattern(pattern = object1.name,extend=False)
    bpy.context.scene.objects.active=bpy.data.objects[object1.name]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
   
    #if(bpy.context.scene.repeatprot):
    protusions_repeat(object1, mesh1, r_prot)
   
    if(len(bpy.context.scene.DISC_doodads) != 0 and bpy.context.scene.dodoodads and isLast):
        doodads(object1, mesh1, dmin, dmax)
        mesh2 = bpy.data.meshes.new("dood_mesh")
        object2 = bpy.data.objects.new("dood_obj", mesh2)
        bpy.context.scene.objects.link(object2)
        mesh2.from_pydata(dVerts, [], dPolygons)
        mesh2.update(calc_edges = True)
        setMatDood(object2)
        object2.location        = to_translate
        object2.rotation_euler  = to_rotate
        object2.scale           = to_scale
 
    bpy.ops.object.select_pattern(pattern = object.name,extend=False)
    bpy.context.scene.objects.active=bpy.data.objects[object.name]
    bpy.ops.object.delete()
    
    bpy.ops.object.select_pattern(pattern=object1.name,extend=False)
    bpy.context.scene.objects.active=bpy.data.objects[object1.name]
    bpy.context.scene.update()
   
    # translate, scale and rotate discombobulated results
    object1.location        = to_translate
    object1.rotation_euler  = to_rotate
    object1.scale           = to_scale
    
    #set all polys to selected. this allows recursive discombobulating.
    for poly in mesh1.polygons:
        poly.select=True
 
############ Operator to select and deslect an object as a doodad ###############
 
class chooseDoodad(bpy.types.Operator):
    bl_idname = "object.discombobulate_set_doodad"
    bl_label = "Discombobulate set doodad object"
   
    def execute(self, context):
        bpy.context.scene.DISC_doodads.append(bpy.context.active_object.name)
       
    def invoke(self, context, event):
        self.execute(context)
        return {'FINISHED'}
 
class unchooseDoodad(bpy.types.Operator):
    bl_idname = "object.discombobulate_unset_doodad"
    bl_label = "Discombobulate unset doodad object"
   
    def execute(self, context):
        for name in bpy.context.scene.DISC_doodads:
            if name == bpy.context.active_object.name:
                bpy.context.scene.DISC_doodads.remove(name)
               
    def invoke(self, context, event):
        self.execute(context)
        return {'FINISHED'}
 
################################## Interpolygon ####################################
 
class discombobulator(bpy.types.Operator):
    bl_idname = "object.discombobulate"
    bl_label = "Discombobulate"
    bl_options = {'REGISTER', 'UNDO'}  
   
    def execute(self, context):
        scn = context.scene
        i=0
        while i<scn.repeatprot:
            isLast=False
            if i==scn.repeatprot-1:
                isLast=True
            discombobulate(scn.minHeight, scn.maxHeight, scn.minTaper, scn.maxTaper, scn.subpolygon1, scn.subpolygon2, scn.subpolygon3, scn.subpolygon4, scn.mindoodads, scn.maxdoodads, scn.repeatprot, scn.sideProtMat, scn.topProtMat, isLast)
            i+=1
        return {'FINISHED'}

class discombob_help(bpy.types.Operator):
	bl_idname = 'help.discombobulator'
	bl_label = ''

	def draw(self, context):
		layout = self.layout
		layout.label('To use:')
		layout.label('Works with Quads only not Ngons.')
		layout.label('Select a face or faces')
		layout.label('Press Discombobulate to create greebles')


	
	def execute(self, context):
		return {'FINISHED'}

	def invoke(self, context, event):
		return context.window_manager.invoke_popup(self, width = 300)
		
class VIEW3D_PT_tools_discombobulate(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = "Discombobulator"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = "Create"
	
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row = layout.split(0.80)
        row.operator('object.discombobulate', text = 'Discombobulate', icon = 'PLUGIN')
        row.operator('help.discombobulator', icon = 'INFO')
        box = layout.box()
        box.label("Protusions settings")
        row = box.row()
        row.prop(context.scene, 'doprots')
        row = box.row()
        row.prop(context.scene, 'minHeight')
        row = box.row()
        row.prop(context.scene, 'maxHeight')
        row = box.row()
        row.prop(context.scene, 'minTaper')
        row = box.row()
        row.prop(context.scene, 'maxTaper')
        row = box.row()
        col1 = row.column(align = True)
        col1.prop(context.scene, "subpolygon1")
        col2 = row.column(align = True)
        col2.prop(context.scene, "subpolygon2")
        col3 = row.column(align = True)
        col3.prop(context.scene, "subpolygon3")
        col4 = row.column(align = True)
        col4.prop(context.scene, "subpolygon4")
        row = box.row()
        row.prop(context.scene, "repeatprot")
        box = layout.box()
        box.label("Doodads settings")
        row = box.row()
        row.prop(context.scene, 'dodoodads')
        row = box.row()
        row.prop(context.scene, "mindoodads")
        row = box.row()
        row.prop(context.scene, "maxdoodads")
        row = box.row()
        row.operator("object.discombobulate_set_doodad", text = "Pick doodad")
        row = box.row()
        row.operator("object.discombobulate_unset_doodad", text = "Remove doodad")
        col = box.column(align = True)
        for name in bpy.context.scene.DISC_doodads:
            col.label(text = name)
        box = layout.box()
        box.label("Materials settings")
        row = box.row()
        row.prop(context.scene, 'topProtMat')
        row = box.row()
        row.prop(context.scene, "sideProtMat")
        row = box.row()
           
# registering and menu integration
def register():
    # Protusions Buttons:
    bpy.types.Scene.repeatprot = bpy.props.IntProperty(name="Repeat protusions", description="make several layers of protusion", default = 1, min = 1, max = 10)
    bpy.types.Scene.doprots = bpy.props.BoolProperty(name="Make protusions", description = "Check if we want to add protusions to the mesh", default = True)
    bpy.types.Scene.polygonschangedpercent = bpy.props.FloatProperty(name="Polygon %", description = "Percentage of changed polygons", default = 1.0)
    bpy.types.Scene.minHeight = bpy.props.FloatProperty(name="Min height", description="Minimal height of the protusions", default=0.2)
    bpy.types.Scene.maxHeight = bpy.props.FloatProperty(name="Max height", description="Maximal height of the protusions", default = 0.4)
    bpy.types.Scene.minTaper = bpy.props.FloatProperty(name="Min taper", description="Minimal height of the protusions", default=0.15, min = 0.0, max = 1.0, subtype = 'PERCENTAGE')
    bpy.types.Scene.maxTaper = bpy.props.FloatProperty(name="Max taper", description="Maximal height of the protusions", default = 0.35, min = 0.0, max = 1.0, subtype = 'PERCENTAGE')
    bpy.types.Scene.subpolygon1 = bpy.props.BoolProperty(name="1", default = True)
    bpy.types.Scene.subpolygon2 = bpy.props.BoolProperty(name="2", default = True)
    bpy.types.Scene.subpolygon3 = bpy.props.BoolProperty(name="3", default = True)
    bpy.types.Scene.subpolygon4 = bpy.props.BoolProperty(name="4", default = True)
   
    # Doodads buttons:
    bpy.types.Scene.dodoodads = bpy.props.BoolProperty(name="Make doodads", description = "Check if we want to generate doodads", default = True)
    bpy.types.Scene.mindoodads = bpy.props.IntProperty(name="Minimum doodads number", description = "Ask for the minimum number of doodads to generate per polygon", default = 1, min = 0, max = 50)
    bpy.types.Scene.maxdoodads = bpy.props.IntProperty(name="Maximum doodads number", description = "Ask for the maximum number of doodads to generate per polygon", default = 6, min = 1, max = 50)
    bpy.types.Scene.doodMinScale = bpy.props.FloatProperty(name="Scale min", description="Minimum scaling of doodad", default = 0.5, min = 0.0, max = 1.0, subtype = 'PERCENTAGE')
    bpy.types.Scene.doodMaxScale = bpy.props.FloatProperty(name="Scale max", description="Maximum scaling of doodad", default = 1.0, min = 0.0, max = 1.0, subtype = 'PERCENTAGE')
   
    # Materials buttons:
    bpy.types.Scene.sideProtMat = bpy.props.IntProperty(name="Side's prot mat", description = "Material of protusion's sides", default = 0, min = 0)
    bpy.types.Scene.topProtMat = bpy.props.IntProperty(name = "Prot's top mat", description = "Material of protusion's top", default = 0, min = 0)
   
    bpy.utils.register_class(discombobulator)
    bpy.utils.register_class(chooseDoodad)
    bpy.utils.register_class(unchooseDoodad)
    bpy.utils.register_class(VIEW3D_PT_tools_discombobulate)
    bpy.utils.register_class(discombob_help)
 
# unregistering and removing menus
def unregister():
    bpy.utils.unregister_class(discombobulator)
    bpy.utils.unregister_class(chooseDoodad)
    bpy.utils.unregister_class(unchooseDoodad)
    bpy.utils.unregister_class(VIEW3D_PT_tools_discombobulate)
    bpy.utils.unregister_class(discombob_help)
 
if __name__ == "__main__":
    register()
