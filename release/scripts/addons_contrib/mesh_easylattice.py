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
    "name": "Easy Lattice Object",
    "author": "Kursad Karatas",
    "version": (0, 5),
    "blender": (2, 66, 0),
    "location": "View3D > Easy Lattice",
    "description": "Create a lattice for shape editing",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Easy_Lattice_Editing_Addon",
    "tracker_url": "https://bitbucket.org/kursad/blender_addons_easylattice/src",
    "category": "Mesh"}


import bpy
import mathutils
import math

# Cleanup
def modifiersDelete( obj ):

    for mod in obj.modifiers:
        print(mod)
        if mod.name == "latticeeasytemp":
            try:
                if mod.object == bpy.data.objects['LatticeEasytTemp']:
                    print("applying modifier")
                    bpy.ops.object.modifier_apply( apply_as = 'DATA', modifier = mod.name )

            except:
                bpy.ops.object.modifier_remove( modifier = mod.name )

# Cleanup
def modifiersApplyRemove( obj ):

#     print("passed object is", obj)
#     print("current object is", bpy.context.active_object)

    bpy.ops.object.select_all( action = 'DESELECT' )
    bpy.ops.object.select_pattern(pattern=obj.name, extend=False)
    bpy.context.scene.objects.active=obj

    for mod in obj.modifiers:
#         print("modifier is ", mod)
        if mod.name == "latticeeasytemp":
#             try:
            if mod.object == bpy.data.objects['LatticeEasytTemp']:
#                 print("mod object is ", mod.object)
#                 print("applying modifier", mod," - ", mod.name)

                #obj.select= True
#                 print("current object is", bpy.context.active_object)
                bpy.ops.object.modifier_apply( apply_as = 'DATA', modifier = mod.name )
                #obj.modifiers.remove(mod)

#             except:
#                 bpy.ops.object.modifier_remove( modifier = mod.name )


# Cleanup
def latticeDelete(obj):
    bpy.ops.object.select_all( action = 'DESELECT' )
    for ob in bpy.context.scene.objects:
         if "LatticeEasytTemp" in ob.name:
             ob.select = True
    bpy.ops.object.delete( use_global = False )

    #select the original object back
    obj.select=True

def createLattice( obj, size, pos, props ):
    # Create lattice and object
    lat = bpy.data.lattices.new( 'LatticeEasytTemp' )
    ob = bpy.data.objects.new( 'LatticeEasytTemp', lat )

    loc,rot,scl = getTransformations( obj )

    #get the combined rotation matrix and apply to the lattice
    #ob.matrix_world=buildRot_WorldMat(obj)*ob.matrix_world

    #the position comes from the bbox
    ob.location = pos
        #ob.location=(pos.x+loc.x,pos.y+loc.y,pos.z+loc.z)

    #the size  from bbox
    ob.scale = size
        #ob.scale=(size.x*scl.x, size.y*scl.y,size.z*scl.z)

    #the rotation comes from the combined obj world matrix which was converted to euler pairs.
    ob.rotation_euler = buildRot_World(obj)

    ob.show_x_ray = True
    # Link object to scene
    scn = bpy.context.scene
    scn.objects.link( ob )
    scn.objects.active = ob
    scn.update()

    # Set lattice attributes
    lat.interpolation_type_u = props[3]
    lat.interpolation_type_v = props[3]
    lat.interpolation_type_w = props[3]

    lat.use_outside = False

    lat.points_u = props[0]
    lat.points_v = props[1]
    lat.points_w = props[2]

    #Set lattice points
    '''s = 0.0
    points = [
        (-s,-s,-s), (s,-s,-s), (-s,s,-s), (s,s,-s),
        (-s,-s,s), (s,-s,s), (-s,s,s), (s,s,s)
    ]
    for n,pt in enumerate(lat.points):
        for k in range(3):
            #pt.co[k] = points[n][k]
    '''

    return ob


def selectedVerts_Grp( obj ):
#     vertices=bpy.context.active_object.data.vertices
    vertices = obj.data.vertices

    selverts = []

    if obj.mode == "EDIT":
        bpy.ops.object.editmode_toggle()

    for grp in obj.vertex_groups:

        if "templatticegrp" in grp.name:
            bpy.ops.object.vertex_group_set_active( group = grp.name )
            bpy.ops.object.vertex_group_remove()

    tempgroup = obj.vertex_groups.new( "templatticegrp" )

    # selverts=[vert for vert in vertices if vert.select==True]
    for vert in vertices:
        if vert.select == True:
            selverts.append( vert )
            tempgroup.add( [vert.index], 1.0, "REPLACE" )

    # print(selverts)

    return selverts

def getTransformations( obj ):
    rot = obj.rotation_euler
    loc = obj.location
    size = obj.scale

    return [loc, rot, size]

def findBBox( obj, selvertsarray ):

#     mat = buildTrnSclMat( obj )
    mat =buildTrnScl_WorldMat(obj)

    mat_world = obj.matrix_world

    minx, miny, minz = selvertsarray[0].co
    maxx, maxy, maxz = selvertsarray[0].co

    c = 1
#     for vert in selvertsarray:
    for c in range( len( selvertsarray ) ):
        # co=obj.matrix_world*vert.co.to_4d()

#         co = vert.co
        co = selvertsarray[c].co

        if co.x < minx: minx = co.x
        if co.y < miny: miny = co.y
        if co.z < minz: minz = co.z

        if co.x > maxx: maxx = co.x
        if co.y > maxy: maxy = co.y
        if co.z > maxz: maxz = co.z

#         print("local cord", selvertsarray[c].co)
#         print("world cord", co)
        c += 1

#     print("total verts", len(selvertsarray))
#     print("counted verts",c)

    # Based on world coords
#     print("-> minx miny minz",minx, miny, minz )
#     print("-> maxx maxy maxz",maxx, maxy, maxz )

    minpoint = mathutils.Vector( ( minx, miny, minz ) )
    maxpoint = mathutils.Vector( ( maxx, maxy, maxz ) )

    # middle point has to be calculated based on the real world matrix
    #middle = mat_world * mathutils.Vector((x_sum, y_sum, z_sum))/float(c)
    middle = ( ( minpoint + maxpoint ) / 2 )

    minpoint = mat * minpoint  # Calculate only based on loc/scale
    maxpoint = mat * maxpoint  # Calculate only based on loc/scale
    middle = mat_world * middle  # the middle has to be calculated based on the real world matrix

    size = maxpoint - minpoint
    size = mathutils.Vector( ( abs( size.x ), abs( size.y ), abs( size.z ) ) )

    # local coords
    #####################################################
    '''minpoint=mathutils.Vector((minx,miny,minz))
    maxpoint=mathutils.Vector((maxx,maxy,maxz))
    middle=mathutils.Vector( (x_sum/float(len(selvertsarray)), y_sum/float(len(selvertsarray)), z_sum/float(len(selvertsarray))) )
    size=maxpoint-minpoint
    size=mathutils.Vector((abs(size.x),abs(size.y),abs(size.z)))
    '''
    #####################################################


    return [minpoint, maxpoint, size, middle  ]


def buildTrnSclMat( obj ):
    # This function builds a local matrix that encodes translation and scale and it leaves out the rotation matrix
    # The rotation is applied at obejct level if there is any
    mat_trans = mathutils.Matrix.Translation( obj.location )
    mat_scale = mathutils.Matrix.Scale( obj.scale[0], 4, ( 1, 0, 0 ) )
    mat_scale *= mathutils.Matrix.Scale( obj.scale[1], 4, ( 0, 1, 0 ) )
    mat_scale *= mathutils.Matrix.Scale( obj.scale[2], 4, ( 0, 0, 1 ) )

    mat_final = mat_trans * mat_scale


    return mat_final

def buildTrnScl_WorldMat( obj ):
    # This function builds a real world matrix that encodes translation and scale and it leaves out the rotation matrix
    # The rotation is applied at obejct level if there is any
    loc,rot,scl=obj.matrix_world.decompose()
    mat_trans = mathutils.Matrix.Translation( loc)

    mat_scale = mathutils.Matrix.Scale( scl[0], 4, ( 1, 0, 0 ) )
    mat_scale *= mathutils.Matrix.Scale( scl[1], 4, ( 0, 1, 0 ) )
    mat_scale *= mathutils.Matrix.Scale( scl[2], 4, ( 0, 0, 1 ) )

    mat_final = mat_trans * mat_scale


    return mat_final

#Feature use
def buildRot_WorldMat( obj ):
    # This function builds a real world matrix that encodes rotation and it leaves out translation and scale matrices
    loc,rot,scl=obj.matrix_world.decompose()
    rot=rot.to_euler()

    mat_rot = mathutils.Matrix.Rotation(rot[0], 4,'X')
    mat_rot *= mathutils.Matrix.Rotation(rot[1],4,'Z')
    mat_rot *= mathutils.Matrix.Rotation(rot[2], 4,'Y')
    return mat_rot

#Feature use
def buildTrn_WorldMat( obj ):
    # This function builds a real world matrix that encodes translation and scale and it leaves out the rotation matrix
    # The rotation is applied at obejct level if there is any
    loc,rot,scl=obj.matrix_world.decompose()
    mat_trans = mathutils.Matrix.Translation( loc)

    return mat_trans

#Feature use
def buildScl_WorldMat( obj ):
    # This function builds a real world matrix that encodes translation and scale and it leaves out the rotation matrix
    # The rotation is applied at obejct level if there is any
    loc,rot,scl=obj.matrix_world.decompose()

    mat_scale = mathutils.Matrix.Scale( scl[0], 4, ( 1, 0, 0 ) )
    mat_scale *= mathutils.Matrix.Scale( scl[1], 4, ( 0, 1, 0 ) )
    mat_scale *= mathutils.Matrix.Scale( scl[2], 4, ( 0, 0, 1 ) )

    return mat_scale

def buildRot_World( obj ):
    # This function builds a real world rotation values
    loc,rot,scl=obj.matrix_world.decompose()
    rot=rot.to_euler()

    return rot

def run( lat_props ):

#     print("<-------------------------------->")
    #obj = bpy.context.active_object
    obj = bpy.context.object

    if obj.type == "MESH":
        # set global property for the currently active latticed object
        bpy.types.Scene.activelatticeobject = bpy.props.StringProperty( name = "currentlatticeobject", default = "" )
        bpy.types.Scene.activelatticeobject = obj.name

        modifiersDelete( obj )
        selvertsarray = selectedVerts_Grp( obj )
        bbox = findBBox( obj, selvertsarray )

        size = bbox[2]
        pos = bbox[3]

#         print("lattce size, pos", size, " ", pos)
        latticeDelete(obj)
        lat = createLattice( obj, size, pos, lat_props )

        modif = obj.modifiers.new( "latticeeasytemp", "LATTICE" )
        modif.object = lat
        modif.vertex_group = "templatticegrp"


        bpy.ops.object.select_all( action = 'DESELECT' )
        bpy.ops.object.select_pattern(pattern=lat.name, extend=False)
        bpy.context.scene.objects.active=lat

        bpy.context.scene.update()
        bpy.ops.object.mode_set( mode = 'EDIT' )

    if obj.type == "LATTICE":


        if bpy.types.Scene.activelatticeobject:
            name = bpy.types.Scene.activelatticeobject
            print("last active latticed object", name)

            #Are we in edit lattice mode? If so move on to object mode
            if obj.mode=="EDIT":
                bpy.ops.object.editmode_toggle()

            for ob in bpy.context.scene.objects:
                if ob.name == name:  # found the object with the lattice mod
                    print("apply mod on", ob)
                    object = ob
                    modifiersApplyRemove(object)
                    #modifiersDelete( object )  # apply the modifier and delete the lattice
                    latticeDelete(obj)

    return


def main( context, latticeprops ):
    run( latticeprops )

class EasyLattice( bpy.types.Operator ):
    """Tooltip"""
    bl_idname = "object.easy_lattice"
    bl_label = "Easy Lattice Creator"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"

    lat_u = bpy.props.IntProperty( name = "Lattice u", default = 3 )
    lat_w = bpy.props.IntProperty( name = "Lattice w", default = 3 )
    lat_m = bpy.props.IntProperty( name = "Lattice m", default = 3 )

    lat_types = ( ( '0', 'KEY_LINEAR', '0' ), ( '1', 'KEY_CARDINAL', '1' ), ( '2', 'KEY_BSPLINE', '2' ) )
    lat_type = bpy.props.EnumProperty( name = "Lattice Type", items = lat_types, default = '0' )


    @classmethod
    def poll( cls, context ):
        return context.active_object is not None

    def execute( self, context ):

        lat_u = self.lat_u
        lat_w = self.lat_w
        lat_m = self.lat_m

        # this is a reference to the "items" used to generate the
        # enum property.
        lat_type = self.lat_types[int( self.lat_type )][1]
        lat_props = [lat_u, lat_w, lat_m, lat_type]

        main( context, lat_props )
        return {'FINISHED'}

    def invoke( self, context, event ):
        wm = context.window_manager
        return wm.invoke_props_dialog( self )

def menu_draw( self, context ):
    self.layout.operator_context = 'INVOKE_REGION_WIN'
    self.layout.operator( EasyLattice.bl_idname, "Easy Lattice" )

def register():
    bpy.utils.register_class( EasyLattice )
    # bpy.utils.register
    # menu_func = (lambda self, context: self.layout.operator('EasyLattice'))
    # bpy.types.VIEW3D_PT_tools_objectmode.append(menu_draw)
    bpy.types.VIEW3D_MT_edit_mesh_specials.append( menu_draw )


def unregister():
    bpy.utils.unregister_class( EasyLattice )
    # bpy.types.VIEW3D_PT_tools_objectmode.remove(menu_draw)
    bpy.types.VIEW3D_MT_edit_mesh_specials.remove( menu_draw )

if __name__ == "__main__":
    register()
    # run()
#     bpy.ops.object.easy_lattice()




