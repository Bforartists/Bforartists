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
            "name": " Easy Lattice",
            "author": "Kursad Karatas / Mechanical Mustache Labs",
            "version": ( 1, 0, 1 ),
            "blender": ( 2, 80,0 ),
            "location": "View3D > EZ Lattice",
            "description": "Create a lattice for shape editing",
            "warning": "",
            "doc_url": "",
            "tracker_url": "",
            "category": "Mesh"}

import bpy
import copy

import bmesh
from bpy.app.handlers import persistent
from bpy.props import (EnumProperty, FloatProperty, FloatVectorProperty,
                       IntProperty, StringProperty, BoolProperty)
from bpy.types import Operator
from bpy_extras.object_utils import AddObjectHelper, object_data_add
from mathutils import Matrix, Vector
import mathutils
import numpy as np


LAT_TYPES= ( ( 'KEY_LINEAR', 'KEY_LINEAR', '' ), ( 'KEY_CARDINAL', 'KEY_CARDINAL', '' ), ( 'KEY_BSPLINE', 'KEY_BSPLINE', '' ) )

OP_TYPES= ( ( 'NEW', 'NEW', '' ), ( 'APPLY', 'APPLY', '' ), ( 'CLEAR', 'CLEAR', '' ) )

def defineSceneProps():
    bpy.types.Scene.ezlattice_object = StringProperty(name="Object2Operate",
                                        description="Object to be operated on",
                                        default="")

    bpy.types.Scene.ezlattice_objects = StringProperty(name="Objects2Operate",
                                        description="Objects to be operated on",
                                        default="")

    bpy.types.Scene.ezlattice_mode = StringProperty(name="CurrentMode",
                                        default="")

    bpy.types.Scene.ezlattice_lattice = StringProperty(name="LatticeObName",
                                        default="")

    bpy.types.Scene.ezlattice_flag = BoolProperty(name="LatticeFlag", default=False)

def defineObjectProps():

    bpy.types.Object.ezlattice_flag = BoolProperty(name="LatticeFlag", default=False)

    bpy.types.Object.ezlattice_controller = StringProperty(name="LatticeController", default="")

    bpy.types.Object.ezlattice_modifier = StringProperty(name="latticeModifier", default="")

def objectMode():

    if isEditMode():
        bpy.ops.object.mode_set(mode="OBJECT")

    else:
        return True

    return

def isEditMode():
    """Check to see we are in edit  mode
    """

    try:
        if bpy.context.object.mode == "EDIT":
            return True

        else:
            return False

    except:
        print("No active mesh object")



def isObjectMode():

    if bpy.context.object.mode == "OBJECT":
        return True

    else:
        return False


def setMode(mode=None):

    if mode:
        bpy.ops.object.mode_set(mode=mode)

def curMode():

    return bpy.context.object.mode

def editMode():

    if not isEditMode():
        bpy.ops.object.mode_set(mode="EDIT")

    else:
        return True

    return


def setSelectActiveObject(context, obj):

    if context.mode == 'OBJECT':

        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = obj
        obj.select_set(True)


def getObject(name=None):
    try:
        ob=[o for o in bpy.data.objects if o.name == name][0]
        return ob

    except:
        return None



def buildTrnScl_WorldMat( obj ):
    # This function builds a real world matrix that encodes translation and scale and it leaves out the rotation matrix
    # The rotation is applied at obejct level if there is any
    loc,rot,scl=obj.matrix_world.decompose()
    mat_trans = mathutils.Matrix.Translation( loc)

    mat_scale = mathutils.Matrix.Scale( scl[0], 4, ( 1, 0, 0 ) )
    mat_scale @= mathutils.Matrix.Scale( scl[1], 4, ( 0, 1, 0 ) )
    mat_scale @= mathutils.Matrix.Scale( scl[2], 4, ( 0, 0, 1 ) )

    mat_final = mat_trans @ mat_scale

    return mat_final

def getSelectedVerts(context):
    """
    https://devtalk.blender.org/t/foreach-get-for-selected-vertex-indices/7712/6

    v_sel = np.empty(len(me.vertices), dtype=bool)
    me.vertices.foreach_get('select', v_sel)

    sel_idx, = np.where(v_sel)
    unsel_idx, = np.where(np.invert(v_sel))

    """

    obj = context.active_object
    m=obj.matrix_world

    count=len(obj.data.vertices)
    shape = (count, 3)


    if obj.type=='MESH':
        me = obj.data
        bm = bmesh.from_edit_mesh(me)

        verts=[m@v.co for v in bm.verts if v.select]

    return np.array(verts, dtype=np.float32)


def getSelectedVertsNumPy(context):
    obj = context.active_object

    if obj.type=='MESH':

        obj.update_from_editmode()

        #BMESH
        me = obj.data
        bm = bmesh.from_edit_mesh(me)

        verts_selected=np.array([v.select for v in bm.verts])

        count=len(obj.data.vertices)
        shape = (count, 3)

        co = np.empty(count*3, dtype=np.float32)

        obj.data.vertices.foreach_get("co",co)


        co.shape=shape

        return co[verts_selected]


def findSelectedVertsBBoxNumPy(context):


    verts=getSelectedVerts(context)

    x_min = verts[:,0].min()
    y_min = verts[:,1].min()
    z_min = verts[:,2].min()

    x_max = verts[:,0].max()
    y_max = verts[:,1].max()
    z_max = verts[:,2].max()


    x_avg = verts[:,0].mean()
    y_avg = verts[:,1].mean()
    z_avg = verts[:,2].mean()

    middle=Vector( ( (x_min+x_max)/2,
                    (y_min+y_max)/2,
                    (z_min+z_max)/2 )
                )

    bbox= [ np.array([x_max,y_max,z_max], dtype=np.float32),
            np.array([x_min, y_min, z_min],  dtype=np.float32),
            np.array([x_avg, y_avg, z_avg],  dtype=np.float32),
            np.array(middle)
            ]

    return bbox


def addSelected2VertGrp():

    C=bpy.context

    grp=C.active_object.vertex_groups.new(name=".templatticegrp")
    bpy.ops.object.vertex_group_assign()
    bpy.ops.object.vertex_group_set_active( group = grp.name )

def removetempVertGrp():

    C=bpy.context

    grp=[g for g in C.active_object.vertex_groups if ".templatticegrp" in g.name]

    if grp:
        for g in grp:
            bpy.context.object.vertex_groups.active_index = g.index
            bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)


def cleanupLatticeObjects(context):

    cur_obj=context.active_object

    try:
        lats=[l for l in bpy.data.objects if ".latticetemp" in l.name]

        if lats:
            for l in lats:
                setSelectActiveObject(context, l)
                bpy.data.objects.remove(l)

                bpy.ops.ed.undo_push()

        setSelectActiveObject(context, cur_obj)

    except:
        print("no cleanup")




def cleanupLatticeModifier(context):

    scn=context.scene

    obj_operated_name=scn.ezlattice_object
    obj_operated=getObject(obj_operated_name)

    curmode=curMode()

    temp_mod=None

    obj=None

    if obj_operated:

        if context.active_object.type=='LATTICE':
            setMode('OBJECT')
            setSelectActiveObject(context, obj_operated )


        temp_mod=[m for m in obj_operated.modifiers if ".LatticeModTemp" in m.name]

        obj=obj_operated

    else:
        temp_mod=[m for m in context.object.modifiers if ".LatticeModTemp" in m.name]
        obj=context.object

    if temp_mod:
        for m in temp_mod:
            bpy.ops.object.modifier_remove(modifier=m.name)

        setMode(curmode)

        return True

    return False

def cleanupApplyPre(context):

    scn=context.scene

    obj_operated_name=scn.ezlattice_object

    obj_operated=getObject(obj_operated_name)

    cur_mode=curMode()


    if obj_operated:

        if context.active_object.type=='LATTICE':
            setMode('OBJECT')
            setSelectActiveObject(context, obj_operated )


        temp_mod=[m for m in obj_operated.modifiers if ".LatticeModTemp" in m.name]


        lats=[l for l in bpy.data.objects if ".latticetemp" in l.name]

        cur_obj=context.active_object

        curmode=curMode()


        if isEditMode():
            objectMode()

        if temp_mod:
            for m in temp_mod:
                if m.object:
                    bpy.ops.object.modifier_apply(apply_as='DATA', modifier=m.name)

                else:
                    bpy.ops.object.modifier_remove(modifier=m.name)

        if lats:
            for l in lats:

                bpy.data.objects.remove(l)

                bpy.ops.ed.undo_push()

        setSelectActiveObject(context, cur_obj)

        setMode(curmode)
        bpy.ops.object.mode_set(mode=curmode)



def createLatticeObject(context, loc=Vector((0,0,0)), scale=Vector((1,1,1)),
                        name=".latticetemp", divisions=[], interp="KEY_BSPLINE"):

    C=bpy.context
    lat_name=name+"_"+C.object.name

    lat = bpy.data.lattices.new( lat_name )
    ob = bpy.data.objects.new( lat_name, lat )
    ob.data.use_outside=True
    ob.data.points_u=divisions[0]
    ob.data.points_v=divisions[1]
    ob.data.points_w=divisions[2]

    ob.data.interpolation_type_u = interp
    ob.data.interpolation_type_v = interp
    ob.data.interpolation_type_w = interp

    scene = context.scene
    scene.collection.objects.link(ob)
    ob.location=loc
    ob.scale = scale

    return ob


def applyLatticeModifier():

    try:
        temp_mod=[m for m in bpy.context.object.modifiers if ".LatticeModTemp" in m.name]

        if temp_mod:
            for m in temp_mod:
                bpy.ops.object.modifier_apply(apply_as='DATA', modifier=m.name)

    except:
        print("no modifiers")


def addLatticeModifier(context, lat,vrtgrp=""):

    bpy.ops.object.modifier_add(type='LATTICE')

    bpy.context.object.modifiers['Lattice'].name=".LatticeModTemp"

    bpy.context.object.modifiers[".LatticeModTemp"].object=lat
    bpy.context.object.modifiers[".LatticeModTemp"].vertex_group=vrtgrp

    bpy.context.object.modifiers[".LatticeModTemp"].show_in_editmode = True
    bpy.context.object.modifiers[".LatticeModTemp"].show_on_cage = True



def newLatticeOp(obj, context,self):

    scn=context.scene


    if scn.ezlattice_flag:

        applyLatticeOp(obj, context)

        scn.ezlattice_flag=False
        scn.ezlattice_mode=""

        return

    cur_obj=obj
    scn.ezlattice_object=cur_obj.name

    scn.ezlattice_mode=curMode()

    cleanupApplyPre(context)

    removetempVertGrp()

    addSelected2VertGrp()

    bbox=findSelectedVertsBBoxNumPy(context)
    scale=bbox[0]-bbox[1]

    loc_crs=Vector((bbox[3][0],bbox[3][1],bbox[3][2]))

    lat=createLatticeObject(context, loc=loc_crs, scale=scale,
                            divisions=[self.lat_u,self.lat_w,self.lat_m],
                            interp=self.lat_type )

    scn.ezlattice_lattice=lat.name


    setSelectActiveObject(context, cur_obj)

    addLatticeModifier(context, lat=lat, vrtgrp=".templatticegrp")

    objectMode()
    setSelectActiveObject(context, lat)

    editMode()

    scn.ezlattice_flag=True




    return

def resetHelperAttrbs(context):

    scn=context.scene

    scn.ezlattice_mode=""
    scn.ezlattice_object=""
    scn.ezlattice_objects=""
    scn.ezlattice_lattice=""


def applyLatticeOp(obj, context):

    scn=context.scene

    if scn.ezlattice_mode=="EDIT":


        obj_operated_name=scn.ezlattice_object

        obj_operated=getObject(obj_operated_name)

        cur_mode=curMode()

        if obj_operated:

            if context.active_object.type=='LATTICE':
                setMode('OBJECT')
                setSelectActiveObject(context, obj_operated )

            temp_mod=[m for m in obj_operated.modifiers if ".LatticeModTemp" in m.name]


            lats=[l for l in bpy.data.objects if ".latticetemp" in l.name]

            cur_obj=context.active_object

            curmode=curMode()


            if isEditMode():
                objectMode()

            if temp_mod:
                for m in temp_mod:
                    if m.object:
                        bpy.ops.object.modifier_apply(apply_as='DATA', modifier=m.name)

                    else:
                        bpy.ops.object.modifier_remove(modifier=m.name)

            if lats:
                for l in lats:

                    bpy.data.objects.remove(l)

                    bpy.ops.ed.undo_push()

            setSelectActiveObject(context, cur_obj)

            setMode(curmode)
            bpy.ops.object.mode_set(mode=curmode)


        removetempVertGrp()


    resetHelperAttrbs(context)

    return

def clearLatticeOps(obj, context):

    scn=context.scene

    if scn.ezlattice_mode=="EDIT":
        cleanupLatticeModifier(context)



    cleanupLatticeObjects(context)

    resetHelperAttrbs(context)
    return


def objectCheck(context):

    if not [bool(o) for  o in context.selected_objects if o.type!="MESH"]:
        return True

    else:
        return False


class OBJECT_MT_EZLatticeOperator(bpy.types.Menu):
    bl_label = "Easy Lattice Menu"
    bl_idname = "LAT_MT_ezlattice"

    def draw(self, context):

        scn=context.scene
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'

        if scn.ezlattice_flag:
            op="Apply"
            layout.operator("object.ezlattice_new", text=op)

        else:
            op="New"
            layout.operator("object.ezlattice_new", text=op)



class OBJECT_OT_EZLatticeCall(Operator):
    """UV Operator description"""
    bl_idname = "object.ezlatticecall"
    bl_label = "Easy Lattice"
    bl_options = {'REGISTER', 'UNDO'}


    @classmethod
    def poll(cls, context):
        return bool(context.active_object)

    def execute(self, context):
        return {'FINISHED'}

class OBJECT_OT_EZLatticeOperatorNew(Operator):

    """Tooltip"""
    bl_idname = "object.ezlattice_new"
    bl_label = "Easy Lattice Creator"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"

    operation: StringProperty(options={'HIDDEN'})
    isnew: BoolProperty(default=False, options={'HIDDEN'})
    isobjectmode: BoolProperty(default=False, options={'HIDDEN'})

    op_type: EnumProperty( name = "Operation Type", items = OP_TYPES)

    lat_u: IntProperty( name = "Lattice u", default = 3 )
    lat_w: IntProperty( name = "Lattice w", default = 3 )
    lat_m: IntProperty( name = "Lattice m", default = 3 )


    lat_type: EnumProperty( name = "Lattice Type", items = LAT_TYPES)

    @classmethod
    def poll(cls, context):
        return (context.mode == 'EDIT_MESH') or (context.mode == 'EDIT_LATTICE') or (context.object.type=='LATTICE')

    def execute(self, context):

        cur_obj=context.active_object
        objs=context.selected_objects
        scn=context.scene

        if self.isnew and isEditMode():

            self.isobjectmode=False
            scn.ezlattice_objects=""
            scn.ezlattice_mode="EDIT"

            newLatticeOp(cur_obj,context,self)
            self.isnew=False

        else:
            newLatticeOp(cur_obj,context,self)

        return {'FINISHED'}

    def invoke( self, context, event ):
        wm = context.window_manager

        cur_obj=context.active_object

        objs=context.selected_objects

        scn=context.scene

        if isEditMode() and cur_obj.type=='MESH':

            self.isnew=True
            if not scn.ezlattice_flag:
                return wm.invoke_props_dialog( self )

        else:
            newLatticeOp(cur_obj,context,self)

        return {'FINISHED'}


def menu_draw(self, context):
    self.layout.separator()
    self.layout.operator_context = 'INVOKE_REGION_WIN'

    self.layout.menu(OBJECT_MT_EZLatticeOperator.bl_idname)


def draw_item(self, context):
    layout = self.layout
    layout.menu(OBJECT_MT_EZLatticeOperator.bl_idname)

classes = (
    OBJECT_OT_EZLatticeOperatorNew,
    OBJECT_MT_EZLatticeOperator,
)


@persistent
def resetProps(dummy):

    context=bpy.context

    resetHelperAttrbs(context)

    return

def register():

    defineSceneProps()

    bpy.app.handlers.load_post.append(resetProps)

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.VIEW3D_MT_edit_mesh_context_menu.prepend(menu_draw)

    bpy.types.VIEW3D_MT_edit_lattice.prepend(menu_draw)
    bpy.types.VIEW3D_MT_edit_lattice_context_menu.prepend(menu_draw)


def unregister():


    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.types.VIEW3D_MT_edit_mesh_context_menu.remove(menu_draw)

    bpy.types.VIEW3D_MT_edit_lattice.remove(menu_draw)
    bpy.types.VIEW3D_MT_edit_lattice_context_menu.remove(menu_draw)

if __name__ == "__main__":
    register()
