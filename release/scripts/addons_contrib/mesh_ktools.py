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
        'name': "Kjartans Scripts",
        'author': "Kjartan Tysdal",
        'location': '"Shift+Q" and also in EditMode "W-Specials/ KTools"',
        'description': "Adds my personal collection of small handy scripts (mostly modeling tools)",
        'category': "Mesh",
        'blender': (2, 7, 6),
        'version': (0, 2, 8),
        'wiki_url': 'http://www.kjartantysdal.com/scripts',
}


import bpy, bmesh
from bpy.props import (
        StringProperty,
        IntProperty,
        FloatProperty,
        EnumProperty,
        BoolProperty,
        BoolVectorProperty,
        FloatVectorProperty,
        )


def testPrint():

    print('Hello')


def checkScale(): # check if scale is 0 on any of the axis, if it is then set it to 0.01

    y = -1
    for x in bpy.context.object.scale:
        y += 1
        if x == 0.0:
            bpy.context.object.scale[y] = 0.01


#Adds "Lattice to Selection" to the Addon
class lattice_to_selection(bpy.types.Operator):
        """Add a lattice deformer to the selection"""
        bl_idname = "object.lattice_to_selection"
        bl_label = "Lattice to Selection"
        bl_options = {'REGISTER', 'UNDO'}

        apply_rot = BoolProperty(
                        name = "Local",
                        description = "Orient the lattice to the active object",
                        default = True
                        )
        parent_to = BoolProperty(
                        name = "Parent to Lattice",
                        description = "Parents all the objects to the Lattice",
                        default = False
                        )
        move_first = BoolProperty(name = "First in Modifier Stack", description = "Moves the lattice modifier to be first in the stack", default = False)
        interpolation = bpy.props.EnumProperty(
                                   items= (('KEY_LINEAR', 'Linear', 'Linear Interpolation'),
                                   ('KEY_CARDINAL', 'Cardinal', 'Cardinal Interpolation'),
                                   ('KEY_CATMULL_ROM', 'Catmull Rom', 'Catmull Rom Interpolation'),
                                   ('KEY_BSPLINE', 'BSpline', 'BSpline Interpolation')),
                                   name = "Interpolation", default = 'KEY_BSPLINE')
        seg_u = IntProperty( name = "Lattice U", default = 2, soft_min = 2)
        seg_v = IntProperty( name = "Lattice V", default = 2, soft_min = 2 )
        seg_w = IntProperty( name = "Lattice W", default = 2, soft_min = 2 )

        def execute(self, context):

                apply_rot = not self.apply_rot # Global vs Local
                parent_to = self.parent_to # Parents all the objects to the Lattice
                move_first = self.move_first # moves the lattice modifier to be first in the stack
                interpolation = self.interpolation

                # check if there exists an active object
                if bpy.context.scene.objects.active:
                    active_obj = bpy.context.scene.objects.active.name
                else:
                    for x in bpy.context.selected_objects:
                        if bpy.data.objects[x.name].type == 'MESH':
                            bpy.context.scene.objects.active = bpy.data.objects[x.name]
                            active_obj = bpy.context.scene.objects.active.name
                            break



                if bpy.data.objects[active_obj].type != 'MESH':
                    self.report({'ERROR'}, "Make sure the active object is a Mesh")
                    return {'CANCELLED'}

                mode = bpy.context.active_object.mode


                if mode == 'OBJECT':


                    # check if object type is not MESH and then deselect it
                    for x in bpy.context.selected_objects:
                        if bpy.data.objects[x.name].type != 'MESH':
                            bpy.data.objects[x.name].select = False


                    org_objs = bpy.context.selected_objects


                    bpy.ops.object.duplicate()

                    # remove any modifiers
                    if bpy.context.object.modifiers:
                        for x in bpy.context.object.modifiers:
                            bpy.ops.object.modifier_remove(modifier=x.name)

                    if len(bpy.context.selected_objects) > 1:
                        bpy.ops.object.join()

                    # create tmp:object and store its location, rotation and dimensions
                    bpy.ops.object.transform_apply(location=False, rotation=apply_rot, scale=True)
                    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

                    lattice_loc = bpy.context.object.location
                    lattice_rot = bpy.context.object.rotation_euler
                    bbox_size = bpy.context.object.dimensions
                    tmp_obj = bpy.context.object.name

                    # create the lattice object with the lattice_loc and rot
                    bpy.ops.object.add(radius=1, type='LATTICE', view_align=False, enter_editmode=False, location=lattice_loc, rotation=lattice_rot)

                    lattice_obj = bpy.context.object

                    # set dimensions / bounding box size
                    bpy.context.object.scale = bbox_size

                    bpy.ops.object.select_all(action='DESELECT')

                    # select and delete the tmp_object
                    bpy.data.objects[tmp_obj].select = True
                    bpy.ops.object.delete(use_global=False)

                    # select all the original objects and assign the lattice deformer
                    for i in org_objs:
                       if bpy.data.objects[i.name].type == 'MESH' :
                           bpy.context.scene.objects.active = bpy.data.objects[i.name]
                           bpy.data.objects[i.name].select = True

                           bpy.ops.object.modifier_add(type='LATTICE')
                           lattice_name = bpy.context.object.modifiers[len(bpy.context.object.modifiers)-1].name
                           bpy.context.object.modifiers[lattice_name].object = lattice_obj
                           if move_first == True:
                               for x in bpy.context.object.modifiers:
                                   bpy.ops.object.modifier_move_up(modifier=lattice_name)
                       else:
                           bpy.data.objects[i.name].select = True


                    if parent_to:

                        bpy.data.objects[lattice_obj.name].select = True
                        bpy.context.scene.objects.active = bpy.data.objects[lattice_obj.name]

                        bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
                    else:

                        bpy.ops.object.select_all(action='DESELECT')
                        bpy.data.objects[lattice_obj.name].select = True
                        bpy.context.scene.objects.active = bpy.data.objects[lattice_obj.name]


                    bpy.context.object.data.interpolation_type_u = interpolation
                    bpy.context.object.data.interpolation_type_v = interpolation
                    bpy.context.object.data.interpolation_type_w = interpolation

                    bpy.context.object.data.points_u = self.seg_u
                    bpy.context.object.data.points_v = self.seg_v
                    bpy.context.object.data.points_w = self.seg_w

                    checkScale()


                elif mode == 'EDIT':



                    org_objs = bpy.context.selected_objects

                    # Add vertex group and store its name in a variable
                    bpy.ops.object.vertex_group_assign_new()
                    v_id = len(bpy.context.object.vertex_groups)-1
                    bpy.context.object.vertex_groups[v_id].name = 'tmp_lattice_to_selection'
                    v_group = bpy.context.object.vertex_groups[v_id].name


                    bpy.ops.mesh.duplicate()
                    bpy.ops.mesh.separate(type='SELECTED')

                    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

                    for x in bpy.context.selected_objects:
                        if x not in org_objs:
                            tmp_obj = x.name
                            print(tmp_obj)

                    bpy.ops.object.select_all(action='DESELECT')

                    bpy.context.scene.objects.active = bpy.data.objects[tmp_obj]
                    bpy.data.objects[tmp_obj].select = True


                    if bpy.context.object.modifiers:
                        for x in bpy.context.object.modifiers:
                            bpy.ops.object.modifier_remove(modifier=x.name)


                    bpy.ops.object.transform_apply(location=False, rotation=apply_rot, scale=True)
                    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

                    lattice_loc = bpy.context.object.location
                    lattice_rot = bpy.context.object.rotation_euler
                    bbox_size = bpy.context.object.dimensions
                    tmp_obj = bpy.context.object.name


                    bpy.ops.object.add(radius=1, type='LATTICE', view_align=False, enter_editmode=False, location=lattice_loc, rotation=lattice_rot)

                    lattice_obj = bpy.context.object

                    bpy.context.object.scale = bbox_size

                    bpy.ops.object.select_all(action='DESELECT')


                    bpy.data.objects[tmp_obj].select = True

                    bpy.ops.object.delete(use_global=False)

                    bpy.context.scene.objects.active = bpy.data.objects[active_obj]
                    bpy.data.objects[active_obj].select = True

                    bpy.ops.object.modifier_add(type='LATTICE')
                    lattice_name = bpy.context.object.modifiers[len(bpy.context.object.modifiers)-1].name
                    bpy.context.object.modifiers[lattice_name].object = lattice_obj
                    bpy.context.object.modifiers[lattice_name].vertex_group = v_group

                    if move_first == True:
                        for x in bpy.context.object.modifiers:
                            bpy.ops.object.modifier_move_up(modifier=lattice_name)


                    bpy.ops.object.select_all(action='DESELECT')

                    bpy.data.objects[lattice_obj.name].select = True
                    bpy.context.scene.objects.active = bpy.data.objects[lattice_obj.name]

                    bpy.context.object.data.interpolation_type_u = interpolation
                    bpy.context.object.data.interpolation_type_v = interpolation
                    bpy.context.object.data.interpolation_type_w = interpolation

                    bpy.context.object.data.points_u = self.seg_u
                    bpy.context.object.data.points_v = self.seg_v
                    bpy.context.object.data.points_w = self.seg_w

                    checkScale()




                return {'FINISHED'}

        def invoke( self, context, event ):
            wm = context.window_manager
            return wm.invoke_props_dialog( self )



#Adds Calculate Normals and Smooth to the Addon
class calc_normals(bpy.types.Operator):
        """Calculates and smooths normals."""
        bl_idname = "mesh.calc_normals"
        bl_label = "Calculate Normals"
        bl_options = {'REGISTER', 'UNDO'}

        invert = BoolProperty(name = "Invert Normals", description = "Inverts the normals.", default = False)

        def execute(self, context):

                invert = self.invert
                mode = bpy.context.active_object.mode

                if mode == 'OBJECT':

                        sel = bpy.context.selected_objects
                        active = bpy.context.scene.objects.active.name

                        bpy.ops.object.shade_smooth()


                        for ob in sel:
                                ob = ob.name
                                bpy.context.scene.objects.active = bpy.data.objects[ob]
                                bpy.ops.object.editmode_toggle()
                                bpy.ops.mesh.select_all(action='SELECT')
                                bpy.ops.mesh.normals_make_consistent(inside=invert)
                                bpy.ops.object.editmode_toggle()

                        bpy.context.scene.objects.active = bpy.data.objects[active]

                elif mode == 'EDIT':
                        bpy.ops.mesh.normals_make_consistent(inside=invert)



                return {'FINISHED'}



#Adds SnapToAxis to the Addon
class snaptoaxis(bpy.types.Operator):
        """Snaps selected vertices to zero on the selected axis."""
        bl_idname = "mesh.snaptoaxis"
        bl_label = "Snap to Axis"
        bl_options = {'REGISTER', 'UNDO'}

        #worldspace = bpy.props.EnumProperty(items= (('OBJECT', 'Object Space', 'Snap to the object axis'),
        #                                                                                         ('WORLD', 'World Space', 'Snap to the global axis')),
        #                                                                                         name = "Object/World", default = 'OBJECT')

        snap_x = BoolProperty(name = "Snap to X", description = "Snaps to zero in X. Also sets the axis for the mirror modifier if that button is turned on", default = True)
        snap_y = BoolProperty(name = "Snap to Y", description = "Snaps to zero in Y. Also sets the axis for the mirror modifier if that button is turned on", default = False)
        snap_z = BoolProperty(name = "Snap to Z", description = "Snaps to zero in Z. Also sets the axis for the mirror modifier if that button is turned on", default = False)

        mirror_add = BoolProperty(name = "Add Mirror Modifier", description = "Adds a mirror modifer", default = False)

        mirror_x = BoolProperty(name = "Mirror on X", description = "Sets the modifier to mirror on X", default = True)
        mirror_y = BoolProperty(name = "Mirror on Y", description = "Sets the modifier to mirror on Y", default = False)
        mirror_z = BoolProperty(name = "Mirror on Z", description = "Sets the modifier to mirror on Z", default = False)
        clipping = BoolProperty(name = "Enable Clipping", description = "Prevents vertices from going through the mirror during transform", default = True)




        def draw(self, context):
            layout = self.layout
            col = layout.column()

            col_move = col.column(align=True)
            row = col_move.row(align=True)
            if self.snap_x:
                row.prop(self, "snap_x", text = "X", icon='CHECKBOX_HLT')
            else:
                row.prop(self, "snap_x", text = "X", icon='CHECKBOX_DEHLT')
            if self.snap_y:
                row.prop(self, "snap_y", text = "Y", icon='CHECKBOX_HLT')
            else:
                row.prop(self, "snap_y", text = "Y", icon='CHECKBOX_DEHLT')
            if self.snap_z:
                row.prop(self, "snap_z", text = "Z", icon='CHECKBOX_HLT')
            else:
                row.prop(self, "snap_z", text = "Z", icon='CHECKBOX_DEHLT')

            col.separator()

            col_move = col.column(align=True)
            col_move.prop(self, "mirror_add", icon = 'MODIFIER')
            row = col_move.row(align=True)

            row = col_move.row(align=True)
            row.active = self.mirror_add
            if self.mirror_x:
                row.prop(self, "mirror_x", text = "X", icon='CHECKBOX_HLT')
            else:
                row.prop(self, "mirror_x", text = "X", icon='CHECKBOX_DEHLT')
            if self.mirror_y:
                row.prop(self, "mirror_y", text = "Y", icon='CHECKBOX_HLT')
            else:
                row.prop(self, "mirror_y", text = "Y", icon='CHECKBOX_DEHLT')
            if self.mirror_z:
                row.prop(self, "mirror_z", text = "Z", icon='CHECKBOX_HLT')
            else:
                row.prop(self, "mirror_z", text = "Z", icon='CHECKBOX_DEHLT')

            col = col.column()
            col.active = self.mirror_add
            col.prop(self, "clipping")


        def execute(self, context):

                mode = bpy.context.active_object.mode
                mirror_find = bpy.context.object.modifiers.find('Mirror')
                run = True


                if mode == 'EDIT':
                    loc = bpy.context.object.location


                    me = bpy.context.object.data
                    bm = bmesh.from_edit_mesh(me)

                    for v in bm.verts:
                            if v.select:
                                if self.snap_x == True:
                                    v.co.x = 0
                                if self.snap_y == True:
                                    v.co.y = 0
                                if self.snap_z == True:
                                    v.co.z = 0

                    bmesh.update_edit_mesh(me, True, False)

                if self.mirror_add == True:

                    if mirror_find <= -1:
                        bpy.ops.object.modifier_add(type='MIRROR')

                        bpy.context.object.modifiers['Mirror'].show_viewport = True

                        run = False

                    bpy.context.object.modifiers["Mirror"].use_clip = self.clipping
                    bpy.context.object.modifiers["Mirror"].use_x = self.mirror_x
                    bpy.context.object.modifiers["Mirror"].use_y = self.mirror_y
                    bpy.context.object.modifiers["Mirror"].use_z = self.mirror_z




                return {'FINISHED'}



#Adds QuickBool to the Addon
class quickbool(bpy.types.Operator):
        """Quickly carves out the selected polygons. Works best with manifold meshes."""
        bl_idname = "mesh.quickbool"
        bl_label = "Quick Bool"
        bl_options = {'REGISTER', 'UNDO'}

        del_bool = BoolProperty(name="Delete BoolMesh", description="Deletes the objects used for the boolean operation.", default= True)
        move_to = BoolProperty(name="Move to layer 10", description="Moves the objects used for the boolean operation to layer 10", default= False)
        operation = EnumProperty(items= (('UNION', 'Union', 'Combines'),
                                                                                                 ('INTERSECT', 'Intersect', 'Keep the part that overlaps'),
                                                                                                 ('DIFFERENCE', 'Difference', 'Cuts out')),
                                                                                                 name = "Operation", default = 'DIFFERENCE')

        def draw(self, context):
            layout = self.layout
            col = layout.column()
            col.prop(self, "del_bool")

            col = col.column()
            col.active = self.del_bool == False
            col.prop(self, "move_to")

            col = layout.column()
            col.prop(self, "operation")




        def execute(self, context):

                del_bool = self.del_bool
                move_to = self.move_to
                mode = bpy.context.active_object.mode



                if mode == 'EDIT':

                    #Boolean From Edit mode
                    bpy.ops.mesh.select_linked()
                    bpy.ops.mesh.separate(type='SELECTED')
                    bpy.ops.object.editmode_toggle()

                    #get name of Original+Bool object
                    original = bpy.context.selected_objects[1].name
                    bool = bpy.context.selected_objects[0].name

                    #perform boolean
                    bpy.ops.object.modifier_add(type='BOOLEAN')
                    bpy.context.object.modifiers["Boolean"].object = bpy.data.objects[bool]
                    bpy.context.object.modifiers["Boolean"].operation = self.operation
                    bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")

                    #delete Bool object
                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.ops.object.select_pattern(pattern=bool)

                    bpy.context.scene.objects.active = bpy.data.objects[bool]

                    #Delete all geo inside Shrink_Object
                    bpy.ops.object.mode_set(mode = 'EDIT', toggle = False)
                    bpy.ops.mesh.select_all(action='SELECT')
                    bpy.ops.mesh.delete(type='VERT')
                    bpy.ops.object.mode_set(mode = 'OBJECT', toggle = False)

                    bpy.ops.object.delete()

                    #re-enter edit mode on Original object
                    bpy.context.scene.objects.active = bpy.data.objects[original]
                    bpy.ops.object.select_pattern(pattern=original)
                    bpy.ops.object.editmode_toggle()


                else:

                        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

                        original = bpy.context.active_object.name
                        bool = bpy.context.selected_objects


                        list = []

                        for x in bool:
                                x = x.name
                                if x != original:
                                        list.append(x)

                        for name in list:
                                #Perform Boolean
                                bpy.ops.object.modifier_add(type='BOOLEAN')
                                bpy.context.object.modifiers["Boolean"].object = bpy.data.objects[name]
                                bpy.context.object.modifiers["Boolean"].operation = self.operation
                                bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")


                                if del_bool == True:

                                        bpy.ops.object.select_all(action='DESELECT')
                                        bpy.ops.object.select_pattern(pattern=name)
                                        bpy.context.scene.objects.active = bpy.data.objects[name]

                            #Delete all geo inside Shrink_Object
                                        bpy.ops.object.mode_set(mode = 'EDIT', toggle = False)
                                        bpy.ops.mesh.select_all(action='SELECT')
                                        bpy.ops.mesh.delete(type='VERT')
                                        bpy.ops.object.mode_set(mode = 'OBJECT', toggle = False)

                                        bpy.ops.object.delete(use_global=False)
                                        bpy.context.scene.objects.active = bpy.data.objects[original]
                                else:
                                        bpy.ops.object.select_all(action='DESELECT')
                                        bpy.ops.object.select_pattern(pattern=name)
                                        bpy.context.scene.objects.active = bpy.data.objects[name]

                                        bpy.context.object.display_type = 'WIRE'

                                        # Move to garbage layer
                                        if move_to == True:
                                                bpy.ops.object.move_to_layer(layers=(False, False, False, False, False, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False))

                                        bpy.context.scene.objects.active = bpy.data.objects[original]


                        bpy.ops.object.mode_set(mode=mode, toggle=False)


                return {'FINISHED'}



#Adds Autotubes to the Addon
class autotubes(bpy.types.Operator):
        """Creates a spline tube based on selected edges"""
        bl_idname = "mesh.autotubes"
        bl_label = "Auto Tubes"
        bl_options = {'REGISTER', 'UNDO'}

        bevel = FloatProperty(name="Tube Width", description="Change width of the tube.", default=0.1, min = 0)
        res = IntProperty(name="Tube Resolution", description="Change resolution of the tube.", default=2, min = 0, max = 20)


        def execute(self, context):

                mode = bpy.context.active_object.mode
                type = bpy.context.active_object.type
                bevel = self.bevel
                res = self.res


                if mode == 'EDIT' and type == 'MESH':
                        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                        bpy.ops.object.duplicate()

                        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                        bpy.ops.mesh.select_all(action='INVERT')
                        bpy.ops.mesh.delete(type='EDGE')

                        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                        bpy.ops.object.subdivision_set(level=0)
                        bpy.ops.object.convert(target='CURVE')
                        bpy.context.object.data.fill_mode = 'FULL'
                        bpy.context.object.data.bevel_depth = 0.1
                        bpy.context.object.data.splines[0].use_smooth = True
                        bpy.context.object.data.bevel_resolution = 2
                        bpy.ops.object.shade_smooth()

                        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                        bpy.ops.curve.spline_type_set(type='BEZIER')

                        bpy.context.object.data.bevel_depth = bevel
                        bpy.context.object.data.bevel_resolution = res

                        #bpy.ops.transform.transform(('INVOKE_DEFAULT'), mode='CURVE_SHRINKFATTEN')



                elif type == 'CURVE':

                        bpy.context.object.data.bevel_depth = bevel
                        bpy.context.object.data.bevel_resolution = res

                elif mode != 'EDIT' and type == 'MESH':
                        self.report({'ERROR'}, "This one only works in Edit mode")
                        return {'CANCELLED'}


                return {'FINISHED'}



#Adds basicRename to the Addon

class basicRename(bpy.types.Operator):
        """Renames everything to Banana"""
        bl_idname = "object.basic_rename"
        bl_label = "Basic Renamer"
        bl_options = {'REGISTER', 'UNDO'}

        name = StringProperty(name="Rename", description="Rename selected objects", default="banana")
        padding = IntProperty(name = "Number Padding", description = "Adds how many padded numbers", default = 3, min = 1, max = 8)
        prefix =    StringProperty(name="Pre Fix", description="Adds a Prefix to the name", default="")
        post_ob = StringProperty(name="Post Fix Object", description="Adds ending to object name", default="_MDL")
        post_data = StringProperty(name="Post Fix Data", description="Adds ending to data name", default="_DATA")


        def execute(self, context):


                # The original script
                obj = bpy.context.selected_objects
                name = self.name
                padding = self.padding
                prefix = self.prefix
                post_ob = self.post_ob
                post_data = self.post_data
                number = 0
                for item in obj:
                        number += 1
                        item.name = "%s%s_%s%s" %(str(prefix), str(name), str(number).zfill(padding), str(post_ob))
                        item.data.name = "%s%s_%s%s" %(str(prefix), str(name), str(number).zfill(padding), str(post_data))


                return {'FINISHED'}



class cut_tool(bpy.types.Operator):
        """Context sensitive cut tool"""
        bl_idname = "mesh.cut_tool"
        bl_label = "Cut Tool"
        bl_options = {'REGISTER', 'UNDO'}

        cuts = IntProperty(name="Number of Cuts", description="Change the number of cuts.", default=1, min = 1, soft_max = 10)
        loopcut = BoolProperty(name="Insert LoopCut", description="Makes a loop cut based on the selected edges", default= False)
        smoothness = FloatProperty(name="Smoothness", description="Change the smoothness.", default=0, min = 0, soft_max = 1)
        quad_corners = bpy.props.EnumProperty(items= (('INNERVERT', 'Inner Vert', 'How to subdivide quad corners'),
                                                                                                 ('PATH', 'Path', 'How to subdivide quad corners'),
                                                                                                 ('STRAIGHT_CUT', 'Straight Cut', 'How to subdivide quad corners'),
                                                                                                 ('FAN', 'Fan', 'How to subdivide quad corners')),
                                                                                                 name = "Quad Corner Type", default = 'STRAIGHT_CUT')

        def execute(self, context):

                quad_corners = self.quad_corners
                cuts = self.cuts
                loopcut = self.loopcut
                smoothness = self.smoothness
                mode = bpy.context.active_object.mode

                if mode == 'EDIT':

                        sel_mode = bpy.context.tool_settings.mesh_select_mode[:]

                                                        #Checks and stores if any Vert, Edge or Face is selected.
                        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

                        me = bpy.context.object.data
                        bm = bmesh.new()     # create an empty BMesh
                        bm.from_mesh(me)     # fill it in from a Mesh
                        sel = []
                        edge_sel = []
                        vert_sel = []

                        for v in bm.faces:
                                if v.select:
                                        sel.append(v.index)
                        for v in bm.edges:
                                if v.select:
                                        edge_sel.append(v.index)
                        for v in bm.verts:
                                if v.select:
                                        vert_sel.append(v.index)


                        bm.to_mesh(me)
                        bpy.ops.object.mode_set(mode='EDIT', toggle=False)


                        """
                        if len(sel) == 0 and len(edge_sel) == 0 and len(vert_sel) == 0 :
                                bpy.ops.mesh.knife_tool("INVOKE_DEFAULT")
                        """


                        if sel_mode[2] == True and len(sel) > 1:

                                vgrp = bpy.context.object.vertex_groups.active_index


                                #Store the Hidden Polygons
                                bpy.ops.mesh.select_all(action='SELECT')
                                bpy.ops.object.vertex_group_assign_new()
                                tmp_hidden = bpy.context.object.vertex_groups.active_index
                                bpy.ops.mesh.select_all(action='DESELECT')

                                #Select faces to be cut
                                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                                mesh = bpy.context.active_object.data.polygons

                                for f in sel:
                                        mesh[f].select = True

                                bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                                bpy.ops.mesh.hide(unselected=True)
                                bpy.ops.mesh.select_all(action='SELECT')
                                bpy.ops.mesh.region_to_loop()

                                #Store Boundry Edges
                                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

                                me = bpy.context.object.data
                                bm = bmesh.new()
                                bm.from_mesh(me)
                                boundry_edge = []

                                for v in bm.edges:
                                        if v.select:
                                                boundry_edge.append(v.index)

                                bm.to_mesh(me)

                                bpy.ops.object.mode_set(mode='EDIT', toggle=False)

                                #Store Cut Edges
                                bpy.ops.mesh.select_all(action='INVERT')
                                bpy.ops.mesh.loop_multi_select(ring=True)

                                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

                                me = bpy.context.object.data
                                bm = bmesh.new()
                                bm.from_mesh(me)
                                cut_edges = []

                                for v in bm.edges:
                                        if v.select:
                                                cut_edges.append(v.index)

                                bm.to_mesh(me)

                                bpy.ops.object.mode_set(mode='EDIT', toggle=False)

                                #Store Intersection edges
                                bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
                                bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')

                                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

                                me = bpy.context.object.data
                                bm = bmesh.new()
                                bm.from_mesh(me)
                                int_edges = []

                                for v in bm.edges:
                                        if v.select:
                                                int_edges.append(v.index)

                                bm.to_mesh(me)

                                bpy.ops.object.mode_set(mode='EDIT', toggle=False)

                                #Modify Lists
                                for x in int_edges:
                                        if x in boundry_edge:
                                                cut_edges.remove(x)

                                bpy.ops.mesh.select_all(action='DESELECT')

                                #Select the new edges to cut
                                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                                mesh = bpy.context.active_object.data.edges

                                for f in cut_edges:
                                        mesh[f].select = True

                                #Perform cut and select the cut line.
                                bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                                bpy.ops.mesh.subdivide(number_cuts = cuts, smoothness = smoothness, quadcorner = quad_corners)
                                bpy.ops.mesh.select_all(action='SELECT')
                                bpy.ops.mesh.region_to_loop()
                                bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
                                bpy.ops.mesh.select_all(action='INVERT')
                                bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
                                bpy.ops.mesh.loop_multi_select(ring=False)

                                #Store cut line.
                                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

                                me = bpy.context.object.data
                                bm = bmesh.new()
                                bm.from_mesh(me)
                                cut_line = []

                                for v in bm.edges:
                                        if v.select:
                                                cut_line.append(v.index)

                                bm.to_mesh(me)

                                bpy.ops.object.mode_set(mode='EDIT', toggle=False)

                                bpy.ops.mesh.reveal()
                                bpy.ops.mesh.select_all(action='DESELECT')

                                bpy.context.object.vertex_groups.active_index = tmp_hidden
                                bpy.ops.object.vertex_group_select()
                                bpy.ops.mesh.hide(unselected=True)


                                bpy.ops.mesh.select_all(action='DESELECT')


                                #Select Cutline
                                if cuts <= 1:
                                        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                                        mesh = bpy.context.active_object.data.edges

                                        for f in cut_line:
                                                mesh[f].select = True

                                        bpy.ops.object.mode_set(mode='EDIT', toggle=False)

                                bpy.ops.object.vertex_group_remove(all=False)
                                bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='FACE')

                        elif sel_mode[0] == True and len(vert_sel) >= 2:
                                bpy.ops.mesh.vert_connect_path()

                        elif sel_mode[1] == True and loopcut == False and len(edge_sel) != 0:
                                bpy.ops.mesh.subdivide(number_cuts = cuts, smoothness = smoothness, quadcorner = quad_corners)

                        elif sel_mode[1] == True and loopcut == True and len(edge_sel) != 0:
                                bpy.ops.mesh.loop_multi_select(ring=True)
                                bpy.ops.mesh.subdivide(number_cuts = cuts, smoothness = smoothness, quadcorner = quad_corners)
                        else:
                            bpy.ops.mesh.select_all(action='DESELECT')
                            bpy.ops.mesh.knife_tool("INVOKE_DEFAULT")

                else:
                        self.report({'ERROR'}, "This one only works in Edit mode")

                return {'FINISHED'}



#Adds customAutoSmooth to the Addon

class customAutoSmooth(bpy.types.Operator):
        """Set AutoSmooth angle"""
        bl_idname = "object.custom_autosmooth"
        bl_label = "Autosmooth"
        bl_options = {'REGISTER', 'UNDO'}

        angle = FloatProperty(name="AutoSmooth Angle", description="Set AutoSmooth angle", default= 30.0, min = 0.0, max = 180.0)


        def execute(self, context):

                mode = bpy.context.active_object.mode

                if mode != 'OBJECT':
                        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

                ob = bpy.context.selected_objects
                angle = self.angle
                angle = angle * (3.14159265359/180)

                bpy.ops.object.shade_smooth()

                for x in ob:
                        x = x.name
                        bpy.data.objects[x].data.use_auto_smooth = True
                        bpy.data.objects[x].data.auto_smooth_angle = angle

                bpy.ops.object.mode_set(mode=mode, toggle=False)

                return {'FINISHED'}

#Adds shrinkwrapSmooth to the Addon

class shrinkwrapSmooth(bpy.types.Operator):
        """Smooths the selected vertices while trying to keep the original shape with a shrinkwrap modifier. """
        bl_idname = "mesh.shrinkwrap_smooth"
        bl_label = "Shrinkwrap Smooth"
        bl_options = {'REGISTER', 'UNDO'}

        pin = BoolProperty(name="Pin Selection Border", description="Pins the outer edge of the selection.", default = True)
        subsurf = IntProperty(name="Subsurf Levels", description="More reliable, but slower results", default = 0, min = 0, soft_max = 4)


        def execute(self, context):

                iterate = 6
                pin = self.pin
                data = bpy.context.object.data.name

                # Set up for vertex weight
                bpy.context.scene.tool_settings.vertex_group_weight = 1
                v_grps = len(bpy.context.object.vertex_groups.items())

                bpy.ops.object.mode_set(mode = 'OBJECT', toggle = False)
                org_ob = bpy.context.object.name

                # Create intermediate object
                bpy.ops.object.mode_set(mode = 'OBJECT', toggle = False)
                bpy.ops.mesh.primitive_plane_add(radius=1, view_align=False, enter_editmode=False)
                bpy.context.object.data = bpy.data.meshes[data]
                tmp_ob = bpy.context.object.name


                bpy.ops.object.duplicate(linked=False)
                shrink_ob = bpy.context.object.name

                bpy.ops.object.select_all(action='DESELECT')
                bpy.ops.object.select_pattern(pattern=tmp_ob)
                bpy.context.scene.objects.active = bpy.data.objects[tmp_ob]

                bpy.ops.object.mode_set(mode = 'EDIT', toggle = False)
                bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')

                if v_grps >= 1:
                    for x in range(v_grps):
                        bpy.ops.object.vertex_group_add()


                if pin == True:
                        bpy.ops.object.vertex_group_assign_new()
                        org_id = bpy.context.object.vertex_groups.active_index

                        bpy.ops.object.vertex_group_assign_new()
                        sel = bpy.context.object.vertex_groups.active.name
                        sel_id = bpy.context.object.vertex_groups.active_index

                        bpy.ops.mesh.region_to_loop()
                        bpy.ops.object.vertex_group_remove_from(use_all_groups=False, use_all_verts=False)

                        bpy.ops.mesh.select_all(action='SELECT')
                        bpy.ops.mesh.region_to_loop()
                        bpy.ops.object.vertex_group_remove_from(use_all_groups=False, use_all_verts=False)

                        bpy.ops.mesh.select_all(action='DESELECT')
                        bpy.ops.object.vertex_group_select(sel_id)


                else:
                        bpy.ops.object.vertex_group_assign_new()
                        sel = bpy.context.object.vertex_groups.active.name


                for x in range(iterate):
                        bpy.ops.object.modifier_add(type='SHRINKWRAP')
                        mod_id = (len(bpy.context.object.modifiers)-1)
                        shrink_name = bpy.context.object.modifiers[mod_id].name

                        bpy.context.object.modifiers[shrink_name].target = bpy.data.objects[shrink_ob]
                        bpy.context.object.modifiers[shrink_name].vertex_group = sel

                        bpy.context.object.modifiers[shrink_name].wrap_method = 'PROJECT'
                        bpy.context.object.modifiers[shrink_name].use_negative_direction = True
                        bpy.context.object.modifiers[shrink_name].subsurf_levels = self.subsurf


                        bpy.ops.mesh.vertices_smooth(factor=1, repeat=1)


                        bpy.ops.object.mode_set(mode = 'OBJECT', toggle = False)
                        bpy.ops.object.convert(target='MESH')
                        bpy.ops.object.mode_set(mode = 'EDIT', toggle = False)


                bpy.ops.object.mode_set(mode = 'OBJECT', toggle = False)



                bpy.ops.object.vertex_group_remove(all = False)
                bpy.ops.object.modifier_remove(modifier=shrink_name)

                bpy.ops.object.select_all(action='DESELECT')
                bpy.ops.object.select_pattern(pattern=shrink_ob)
                bpy.context.scene.objects.active = bpy.data.objects[shrink_ob]

                #Delete all geo inside Shrink_Object
                bpy.ops.object.mode_set(mode = 'EDIT', toggle = False)
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.delete(type='VERT')
                bpy.ops.object.mode_set(mode = 'OBJECT', toggle = False)

                bpy.ops.object.delete(use_global=True)

                bpy.ops.object.select_pattern(pattern=tmp_ob)
                bpy.context.scene.objects.active = bpy.data.objects[tmp_ob]


                bpy.ops.object.mode_set(mode = 'EDIT', toggle = False)

                if pin == True:
                        bpy.ops.mesh.select_all(action='DESELECT')
                        bpy.ops.object.vertex_group_select(org_id)

                bpy.ops.object.mode_set(mode = 'OBJECT', toggle = False)

                bpy.ops.object.delete(use_global=False)


                bpy.ops.object.select_pattern(pattern=org_ob)
                bpy.context.scene.objects.active = bpy.data.objects[org_ob]

                bpy.ops.object.mode_set(mode = 'EDIT', toggle = False)

                # Fix for Blender remembering the previous selection
                bpy.ops.object.vertex_group_assign_new()
                bpy.ops.object.vertex_group_remove(all = False)


                return {'FINISHED'}

#Adds buildCorner to the Addon

class buildCorner(bpy.types.Operator):
        """Builds corner topology. Good for converting ngons"""
        bl_idname = "mesh.build_corner"
        bl_label = "Build Corner"
        bl_options = {'REGISTER', 'UNDO'}

        offset = IntProperty()

        def modal(self, context, event):

                if event.type == 'MOUSEMOVE':

                        delta = self.offset - event.mouse_x

                        if delta >= 0:
                                offset = 1
                        else:
                                offset = 0

                        bpy.ops.mesh.edge_face_add()

                        bpy.ops.mesh.poke()
                        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
                        bpy.ops.object.vertex_group_assign_new()
                        sel_id = bpy.context.object.vertex_groups.active_index

                        bpy.ops.mesh.region_to_loop()
                        bpy.ops.object.vertex_group_remove_from()

                        bpy.ops.mesh.select_nth(nth=2, skip=1, offset=offset)

                        bpy.ops.object.vertex_group_select(sel_id)

                        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
                        bpy.ops.mesh.dissolve_mode(use_verts=False)

                        bpy.ops.mesh.select_all(action='DESELECT')
                        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
                        bpy.ops.object.vertex_group_select()
                        bpy.ops.mesh.select_more()

                        bpy.ops.object.vertex_group_remove(all = False)
                        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')


                elif event.type == 'LEFTMOUSE':
                        return {'FINISHED'}

                elif event.type in {'RIGHTMOUSE', 'ESC'}:
                    bpy.ops.ed.undo()
                    return {'CANCELLED'}

                return {'RUNNING_MODAL'}

        def invoke(self, context, event):
                if context.object:

                        # Check selection

                        bpy.ops.mesh.edge_face_add()
                        bpy.ops.mesh.region_to_loop()

                        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

                        me = bpy.context.object.data
                        bm = bmesh.new()     # create an empty BMesh
                        bm.from_mesh(me)     # fill it in from a Mesh

                        face_sel = []
                        edge_sel = []


                        for v in bm.faces:
                                if v.select:
                                        face_sel.append(v.index)
                        for v in bm.edges:
                                if v.select:
                                        edge_sel.append(v.index)



                        bm.to_mesh(me)
                        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                        bpy.ops.mesh.loop_to_region()


                        ###################################

                        edge_sel = len(edge_sel)

                        if edge_sel == 4:
                                return {'FINISHED'}

                        elif edge_sel%2 == 0:
                                self.offset = event.mouse_x
                                context.window_manager.modal_handler_add(self)
                                return {'RUNNING_MODAL'}

                        #elif edge_sel == 5:
                        #    bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
                        #    bpy.ops.mesh.tris_convert_to_quads(face_threshold=3.14159, shape_threshold=3.14159)
                        #    return {'FINISHED'}

                        else:
                                bpy.ops.mesh.poke()
                                bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
                                bpy.ops.mesh.tris_convert_to_quads(face_threshold=3.14159, shape_threshold=3.14159)
                                return {'FINISHED'}

                else:
                        self.report({'WARNING'}, "No active object, could not finish")
                        return {'CANCELLED'}


class drawPoly(bpy.types.Operator):
    """Draw a polygon"""
    bl_idname = "mesh.draw_poly"
    bl_label = "Draw Poly"

    cursor_co = FloatVectorProperty()
    vert_count = 0
    manip = BoolProperty()
    vgrp = IntProperty()
    sel_mode = BoolVectorProperty()
    cursor_depth = BoolProperty()
    snap = BoolProperty()


    def modal(self, context, event):

        # set header gui
        context.area.tag_redraw()
        context.area.header_text_set("LMB = Create New Point, SHIFT = Flip Normals, RMB / ENTER = Accept NGon, MMB = Accept QuadFill")


        mesh = bpy.context.active_object.data

        if event.type == 'LEFTMOUSE':
            if event.value == 'PRESS':


                bpy.ops.view3d.cursor3d('INVOKE_DEFAULT')

                obj = bpy.context.active_object
                vert_co = bpy.context.scene.cursor_location
                world = obj.matrix_world.inverted_safe()

                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

                me = bpy.context.object.data
                bm = bmesh.new()
                bm.from_mesh(me)

                # Add new vert
                new_vert = bm.verts.new(vert_co)
                new_vert.co = world*new_vert.co
                new_vert_id = new_vert.index
                self.vert_count += 1

                if self.vert_count >= 2:
                    bm.verts.ensure_lookup_table()
                    set_of_verts = set(bm.verts[i] for i in range(-2,0))
                    bm.edges.new(set_of_verts)

                # Get index of first and last vertex
                first_index = len(bm.verts)-self.vert_count
                second_index = first_index+1
                third_index = first_index+2
                second_to_last_index = len(bm.verts)-2


                bm.to_mesh(me)
                bm.free()

                mesh.vertices[new_vert_id].select = True
                bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                bpy.context.scene.cursor_location = self.cursor_co


                if self.vert_count >= 4:
                    bpy.ops.object.vertex_group_assign()

                if self.vert_count == 3:
                    # remove second vertex from group
                    bpy.ops.mesh.select_all(action='DESELECT')
                    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                    mesh.vertices[first_index].select = True
                    mesh.vertices[third_index].select = True
                    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                    bpy.ops.object.vertex_group_assign()
                    bpy.ops.mesh.select_more()

                if self.vert_count == 2:
                    bpy.ops.mesh.select_more()

                if self.vert_count >= 4:
                    # make core poly
                    bpy.ops.mesh.select_all(action='DESELECT')
                    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                    mesh.vertices[first_index].select = True
                    mesh.vertices[second_index].select = True
                    mesh.vertices[third_index].select = True
                    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                    bpy.ops.mesh.edge_face_add()

                if self.vert_count == 4:
                    bpy.ops.mesh.select_all(action='DESELECT')
                    bpy.ops.object.vertex_group_select(self.vgrp)
                    bpy.ops.mesh.edge_face_add()

                    # Remove remaining core edge
                    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                    mesh.vertices[second_index].select = True
                    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                    bpy.ops.mesh.edge_face_add()


                if self.vert_count >= 5:
                    #bpy.ops.object.vertex_group_assign()
                    bpy.ops.mesh.select_all(action='DESELECT')

                    # Remove Last Edge
                    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                    mesh.vertices[first_index].select = True
                    mesh.vertices[second_to_last_index].select = True
                    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                    bpy.ops.mesh.delete(type='EDGE')

                    # Fill in rest of face
                    bpy.ops.object.vertex_group_select(self.vgrp)
                    bpy.ops.mesh.edge_face_add()


                    # Remove remaining core edge
                    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                    mesh.vertices[second_index].select = True
                    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                    bpy.ops.mesh.edge_face_add()
                    bpy.ops.mesh.flip_normals()


            #return {'FINISHED'}
        elif event.type == 'MIDDLEMOUSE':

            # reset header gui
            context.area.tag_redraw()
            context.area.header_text_set(None)

            # Convert to Quads
            bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
            bpy.ops.mesh.tris_convert_to_quads()
            bpy.ops.mesh.tris_convert_to_quads(face_threshold=3.14159, shape_threshold=3.14159)


            # restore selection mode and manipulator
            bpy.context.tool_settings.mesh_select_mode = self.sel_mode
            bpy.context.space_data.show_manipulator = self.manip
            bpy.context.user_preferences.view.use_mouse_depth_cursor = self.cursor_depth
            bpy.context.scene.tool_settings.use_snap = self.snap


            # Remove and make sure vertex group data is gone
            bpy.ops.object.vertex_group_remove_from(use_all_verts=True)
            bpy.ops.object.vertex_group_remove()
            bpy.ops.object.vertex_group_assign_new()
            bpy.context.object.vertex_groups.active.name = "drawPoly_temp"
            bpy.ops.object.vertex_group_remove()


            return {'CANCELLED'}

        elif event.type in {'RIGHTMOUSE', 'ESC', 'SPACE'}:

            # reset header gui
            context.area.tag_redraw()
            context.area.header_text_set(None)


            # restore selection mode and manipulator
            bpy.context.tool_settings.mesh_select_mode = self.sel_mode
            bpy.context.space_data.show_manipulator = self.manip
            bpy.context.user_preferences.view.use_mouse_depth_cursor = self.cursor_depth
            bpy.context.scene.tool_settings.use_snap = self.snap


            # Remove and make sure vertex group data is gone
            bpy.ops.object.vertex_group_remove_from(use_all_verts=True)
            bpy.ops.object.vertex_group_remove()
            bpy.ops.object.vertex_group_assign_new()
            bpy.context.object.vertex_groups.active.name = "drawPoly_temp"
            bpy.ops.object.vertex_group_remove()


            return {'CANCELLED'}

        elif event.type == 'LEFT_SHIFT' or event.type == 'RIGHT_SHIFT':
            bpy.ops.mesh.flip_normals()

            return {'PASS_THROUGH'}

        elif event.type == 'LEFT_CTRL' or event.type == 'RIGHT_CTRL' :
            if bpy.context.user_preferences.view.use_mouse_depth_cursor == True:
                bpy.context.user_preferences.view.use_mouse_depth_cursor = False
                bpy.context.scene.tool_settings.use_snap = False
            else:
                bpy.context.user_preferences.view.use_mouse_depth_cursor = True
                bpy.context.scene.tool_settings.use_snap = True
            return {'PASS_THROUGH'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):


        sel_ob = len(bpy.context.selected_objects)


        if sel_ob >= 1:
            sel_type = bpy.context.object.type

            if sel_type == 'MESH':
                bpy.ops.object.mode_set(mode='EDIT', toggle=False)

            else:
                self.report({'WARNING'}, "Active object is not a mesh.")
                return {'CANCELLED'}


        elif sel_ob == 0:
            bpy.ops.mesh.primitive_plane_add()
            bpy.context.selected_objects[0].name = "polyDraw"
            bpy.context.selected_objects[0].data.name = "polyDraw"
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.delete(type='VERT')




        # Store selection mode, snap and manipulator settings
        self.sel_mode = bpy.context.tool_settings.mesh_select_mode[:]
        bpy.context.tool_settings.mesh_select_mode = True, False, False
        self.manip = bpy.context.space_data.show_manipulator
        bpy.context.space_data.show_manipulator = False
        self.cursor_depth = bpy.context.user_preferences.view.use_mouse_depth_cursor
        bpy.context.user_preferences.view.use_mouse_depth_cursor = False
        self.snap = bpy.context.scene.tool_settings.use_snap
        bpy.context.scene.tool_settings.use_snap = False

        bpy.ops.object.mode_set(mode='EDIT', toggle=False)

        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_assign_new()
        self.vgrp = bpy.context.object.vertex_groups.active_index
        bpy.context.object.vertex_groups.active.name = "drawPoly_temp"

        self.cursor_co = bpy.context.scene.cursor_location


        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

class toggleSilhouette(bpy.types.Operator):
    """Turns everything black so that you can evaluate the overall shape. Useful when designing"""
    bl_idname = "object.toggle_silhouette"
    bl_label = "Toggle Silhouette"


    diff_col = FloatVectorProperty(default = (0.226, 0.179, 0.141))
    disp_mode = StringProperty(default = 'SOLID')
    matcap = BoolProperty(default = False)
    only_render = BoolProperty(default = False)

    def execute(self, context):


        light_check = bpy.context.user_preferences.system.solid_lights[0].use

        if light_check == True:
            # Set Lights to Off
            bpy.context.user_preferences.system.solid_lights[0].use = False
            bpy.context.user_preferences.system.solid_lights[1].use = False

            # Store variables
            self.diff_col = bpy.context.user_preferences.system.solid_lights[2].diffuse_color
            self.disp_mode = bpy.context.space_data.viewport_shade
            self.matcap = bpy.context.space_data.use_matcap
            self.only_render = bpy.context.space_data.show_only_render

            bpy.context.user_preferences.system.solid_lights[2].diffuse_color = 0,0,0
            bpy.context.space_data.viewport_shade = 'SOLID'
            bpy.context.space_data.use_matcap = False
            bpy.context.space_data.show_only_render = True

        else:
            bpy.context.user_preferences.system.solid_lights[0].use = True
            bpy.context.user_preferences.system.solid_lights[1].use = True
            bpy.context.user_preferences.system.solid_lights[2].diffuse_color = self.diff_col
            bpy.context.space_data.viewport_shade = self.disp_mode
            bpy.context.space_data.use_matcap = self.matcap
            bpy.context.space_data.show_only_render = self.only_render

        return {'FINISHED'}



#Adds growLoop to the Addon

class growLoop(bpy.types.Operator):
        """Grows the selected edges in both directions """
        bl_idname = "mesh.grow_loop"
        bl_label = "Grow Loop"
        bl_options = {'REGISTER', 'UNDO'}

        grow = IntProperty(name="Grow Selection", description="How much to grow selection", default= 1, min=1, soft_max=10)

        def execute(self, context):

                grow = self.grow
                sel_mode = bpy.context.tool_settings.mesh_select_mode[:]

                for x in range(grow):
                        if sel_mode[2] == True:

                                edge_sel = []
                                border = []
                                interior = []
                                face_org = []
                                face_loop = []
                                face_grow = []
                                face_sel = []
                                mesh_edges = bpy.context.active_object.data.edges
                                mesh_faces = bpy.context.active_object.data.polygons

                                bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')

                                me = bpy.context.object.data
                                bm = bmesh.from_edit_mesh(me)

                                for e in bm.edges:
                                        if e.select:
                                                edge_sel.append(e.index)

                                for f in bm.faces:
                                        if f.select:
                                                face_org.append(f.index)

                                bpy.ops.mesh.region_to_loop()

                                for e in bm.edges:
                                        if e.select:
                                                border.append(e.index)



                                for e in edge_sel:
                                        if e not in border:
                                                interior.append(e)

                                bmesh.update_edit_mesh(me, True, False)


                                bpy.ops.mesh.select_all(action='DESELECT')

                                #Select the interior edges
                                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)


                                for e in interior:
                                        mesh_edges[e].select = True

                                bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                                bpy.ops.mesh.loop_multi_select(ring=True)
                                bpy.ops.mesh.select_mode(use_extend=False, use_expand=True, type='FACE')

                                me = bpy.context.object.data
                                bm = bmesh.from_edit_mesh(me)

                                for f in bm.faces:
                                        if f.select:
                                                face_loop.append(f.index)

                                bmesh.update_edit_mesh(me, True, False)

                                bpy.ops.mesh.select_all(action='DESELECT')


                                # Select original faces
                                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                                for x in face_org:
                                        mesh_faces[x].select = True
                                bpy.ops.object.mode_set(mode='EDIT', toggle=False)


                                bpy.ops.mesh.select_more(use_face_step=False)

                                me = bpy.context.object.data
                                bm = bmesh.from_edit_mesh(me)

                                for f in bm.faces:
                                        if f.select:
                                                face_grow.append(f.index)

                                for f in face_grow:
                                        if f in face_loop:
                                                face_sel.append(f)

                                for f in face_org:
                                        face_sel.append(f)

                                bmesh.update_edit_mesh(me, True, False)

                                bpy.ops.mesh.select_all(action='DESELECT')

                                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

                                for f in face_sel:
                                        mesh_faces[f].select = True

                                bpy.ops.object.mode_set(mode='EDIT', toggle=False)

                        else:
                                mesh = bpy.context.active_object.data.edges

                                me = bpy.context.object.data
                                bm = bmesh.from_edit_mesh(me)
                                org_sel = []
                                grow_sel = []
                                loop_sel = []
                                sel = []

                                bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')

                                for e in bm.edges:
                                        if e.select:
                                                org_sel.append(e.index)

                                bpy.ops.mesh.select_more(use_face_step=False)

                                for e in bm.edges:
                                        if e.select:
                                                grow_sel.append(e.index)

                                bpy.ops.mesh.select_all(action='DESELECT')

                                bmesh.update_edit_mesh(me, True, False)

                                # Select the original edges
                                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                                for e in org_sel:
                                        mesh[e].select = True
                                bpy.ops.object.mode_set(mode='EDIT', toggle=False)


                                me = bpy.context.object.data
                                bm = bmesh.from_edit_mesh(me)
                                bpy.ops.mesh.loop_multi_select(ring=False)

                                for e in bm.edges:
                                        if e.select:
                                                loop_sel.append(e.index)

                                bmesh.update_edit_mesh(me, True, False)

                                bpy.ops.mesh.select_all(action='DESELECT')

                                for x in loop_sel:
                                        if x in grow_sel:
                                                sel.append(x)

                                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                                for e in sel:
                                        mesh[e].select = True
                                bpy.ops.object.mode_set(mode='EDIT', toggle=False)

                        bpy.context.tool_settings.mesh_select_mode = sel_mode

                return {'FINISHED'}

#Adds extendLoop to the Addon

class extendLoop(bpy.types.Operator):
        """Uses the active face or edge to extends the selection in one direction"""
        bl_idname = "mesh.extend_loop"
        bl_label = "Extend Loop"
        bl_options = {'REGISTER', 'UNDO'}

        extend = IntProperty(name="Extend Selection", description="How much to extend selection", default= 1, min=1, soft_max=10)

        def execute(self, context):

                sel_mode = bpy.context.tool_settings.mesh_select_mode[:]
                extend = self.extend

                for x in range(extend):
                    if sel_mode[2] == True:

                        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                        active_face = bpy.context.object.data.polygons.active # find active face
                        bpy.ops.object.mode_set(mode='EDIT', toggle=False)

                        edge_sel = []
                        interior = []
                        face_org = []
                        face_loop = []
                        face_grow = []
                        face_sel = []
                        active_edges = []

                        # Get face selection
                        me = bpy.context.object.data
                        bm = bmesh.from_edit_mesh(me)

                        for f in bm.faces:
                                if f.select:
                                        face_org.append(f.index)

                        face_org.remove(active_face)


                        bmesh.update_edit_mesh(me, True, False)

                        bpy.ops.mesh.select_all(action='DESELECT')
                        mesh = bpy.context.active_object.data.polygons

                        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                        for x in face_org:
                                mesh[x].select = True
                        bpy.ops.object.mode_set(mode='EDIT', toggle=False)



                        # Get edge selection
                        me = bpy.context.object.data
                        bm = bmesh.from_edit_mesh(me)

                        for e in bm.edges:
                                if e.select:
                                        edge_sel.append(e.index)


                        bmesh.update_edit_mesh(me, True, False)


                        # Select Active Face
                        bpy.ops.mesh.select_all(action='DESELECT')
                        mesh = bpy.context.active_object.data.polygons

                        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                        mesh[active_face].select = True
                        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')

                        me = bpy.context.object.data
                        bm = bmesh.from_edit_mesh(me)


                        # Store the interior edge

                        for e in bm.edges:
                                if e.select:
                                        active_edges.append(e.index)


                        for e in active_edges:
                                if e in edge_sel:
                                        interior.append(e)

                        bmesh.update_edit_mesh(me, True, False)


                        bpy.ops.mesh.select_all(action='DESELECT')

                        #Select the interior edges
                        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

                        mesh = bpy.context.active_object.data.edges

                        for e in interior:
                                mesh[e].select = True

                        bpy.ops.object.mode_set(mode='EDIT', toggle=False)


                        bpy.ops.mesh.loop_multi_select(ring=True)
                        bpy.ops.mesh.select_mode(use_extend=False, use_expand=True, type='FACE')


                        me = bpy.context.object.data
                        bm = bmesh.from_edit_mesh(me)

                        for f in bm.faces:
                                if f.select:
                                        face_loop.append(f.index)


                        bmesh.update_edit_mesh(me, True, False)

                        bpy.ops.mesh.select_all(action='DESELECT')

                        # Select active face
                        mesh = bpy.context.active_object.data.polygons

                        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                        mesh[active_face].select = True
                        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                        bpy.ops.mesh.select_more(use_face_step=False)


                        face_org.append(active_face)

                        me = bpy.context.object.data
                        bm = bmesh.from_edit_mesh(me)

                        for f in bm.faces:
                                if f.select:
                                        face_grow.append(f.index)

                        for f in face_grow:
                                if f in face_loop:
                                        face_sel.append(f)

                        for f in face_sel:
                                if f not in face_org:
                                        active_face = f

                        for f in face_org:
                                face_sel.append(f)

                        bmesh.update_edit_mesh(me, True, False)

                        bpy.ops.mesh.select_all(action='DESELECT')

                        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

                        for f in face_sel:
                                mesh[f].select = True
                        bpy.context.object.data.polygons.active = active_face

                        bpy.ops.object.mode_set(mode='EDIT', toggle=False)

                    elif sel_mode[1] == True:

                        mesh = bpy.context.active_object.data
                        org_sel = []
                        grow_sel = []
                        loop_sel = []
                        sel = []
                        org_verts = []
                        active_verts = []

                        # Get active edge
                        me = bpy.context.object.data
                        bm = bmesh.from_edit_mesh(me)

                        for x in reversed(bm.select_history):
                                if isinstance(x, bmesh.types.BMEdge):
                                        active_edge = x.index
                                        break

                        # Store the originally selected edges
                        for e in bm.edges:
                                if e.select:
                                        org_sel.append(e.index)


                        bmesh.update_edit_mesh(me, True, False)

                        # Select active edge
                        bpy.ops.mesh.select_all(action='DESELECT')
                        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                        mesh.edges[active_edge].select = True
                        bpy.ops.object.mode_set(mode='EDIT', toggle=False)

                        # Get verts of active edge
                        bm = bmesh.from_edit_mesh(me)

                        for v in bm.verts:
                                if v.select:
                                        active_verts.append(v.index)

                        bmesh.update_edit_mesh(me, True, False)

                        # Select original selection minus active edge
                        bpy.ops.mesh.select_all(action='DESELECT')
                        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                        for x in org_sel:
                            mesh.edges[x].select = True
                        mesh.edges[active_edge].select = False
                        bpy.ops.object.mode_set(mode='EDIT', toggle=False)

                        bm = bmesh.from_edit_mesh(me)

                        # Store the original vertices minus active edge
                        for v in bm.verts:
                            if v.select:
                                org_verts.append(v.index)


                        # Compare verts
                        for x in active_verts:
                            if x in org_verts:
                                active_verts.remove(x)

                        bmesh.update_edit_mesh(me, True, False)

                        # Select end vertex
                        bpy.ops.mesh.select_all(action='DESELECT')
                        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
                        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                        mesh.vertices[active_verts[0]].select = True
                        bpy.ops.object.mode_set(mode='EDIT', toggle=False)


                        # Grow the end vertex and store the edges
                        bpy.ops.mesh.select_more(use_face_step=False)
                        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
                        bm = bmesh.from_edit_mesh(me)

                        for e in bm.edges:
                                if e.select:
                                        grow_sel.append(e.index)

                        bmesh.update_edit_mesh(me, True, False)
                        bpy.ops.mesh.select_all(action='DESELECT')

                        # Run loop of the active edges and store it
                        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                        mesh.edges[active_edge].select = True
                        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                        bpy.ops.mesh.loop_multi_select(ring=False)

                        me = bpy.context.object.data
                        bm = bmesh.from_edit_mesh(me)

                        for e in bm.edges:
                                if e.select:
                                        loop_sel.append(e.index)

                        bmesh.update_edit_mesh(me, True, False)
                        bpy.ops.mesh.select_all(action='DESELECT')

                        # Compare loop_sel vs grow_sel
                        for x in loop_sel:
                                if x in grow_sel:
                                        sel.append(x)


                        # Add original selection to new selection

                        for x in org_sel:
                            if x not in sel:
                                sel.append(x)


                        # Compare org_sel with sel to get the active edge
                        for x in sel:
                            if x not in org_sel:
                                active_edge = x

                        # Select the resulting edges
                        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                        for e in sel:
                                mesh.edges[e].select = True
                        bpy.ops.object.mode_set(mode='EDIT', toggle=False)

                        # Set the new active edge
                        bm = bmesh.from_edit_mesh(me)

                        bm.edges.ensure_lookup_table()
                        bm.select_history.add(bm.edges[active_edge])
                        bmesh.update_edit_mesh(me, True, False)


                return {'FINISHED'}


#Adds extendLoop to the Addon

class shrinkLoop(bpy.types.Operator):
        """Shrink the selected loop"""
        bl_idname = "mesh.shrink_loop"
        bl_label = "Shrink Loop"
        bl_options = {'REGISTER', 'UNDO'}

        shrink = IntProperty(name="Shrink Selection", description="How much to shrink selection", default= 1, min=1, soft_max=15)

        def execute(self, context):

                sel_mode = bpy.context.tool_settings.mesh_select_mode[:]
                shrink = self.shrink

                for x in range(shrink):
                    if sel_mode[2] == True:
                        me = bpy.context.object.data
                        bm = bmesh.from_edit_mesh(me)
                        mesh = bpy.context.active_object.data

                        sel = []
                        edge_dic = {}
                        vert_list = []
                        end_verts = []
                        org_faces = []
                        cur_faces = []
                        new_faces = []

                        # Store edges and verts
                        for e in bm.edges:
                            if e.select:
                                sel.append(e.index)

                                # Populate vert_list
                                vert_list.append(e.verts[0].index)
                                vert_list.append(e.verts[1].index)

                                # Store dictionary
                                edge_dic[e.index] = [e.verts[0].index, e.verts[1].index]

                        # Store original faces
                        for f in bm.faces:
                            if f.select:
                                org_faces.append(f.index)

                        # Store end verts
                        for v in vert_list:
                            if vert_list.count(v) == 2:
                                end_verts.append(v)

                        # Check verts in dictionary
                        for key, value in edge_dic.items():
                            if value[0] in end_verts:
                                sel.remove(key)
                                continue
                            if value[1] in end_verts:
                                sel.remove(key)


                        bmesh.update_edit_mesh(me, True, False)

                        # Select the resulting edges
                        bpy.ops.mesh.select_all(action='DESELECT')
                        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

                        for e in sel:
                            mesh.edges[e].select = True
                        bpy.ops.object.mode_set(mode='EDIT', toggle=False)

                        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
                        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')

                        bm = bmesh.from_edit_mesh(me)

                        # Store current faces
                        for f in bm.faces:
                            if f.select:
                                cur_faces.append(f.index)

                        # Compare current and original faces
                        for x in org_faces:
                            if x in cur_faces:
                                new_faces.append(x)

                        bmesh.update_edit_mesh(me, True, False)

                        # Select the resulting faces
                        bpy.ops.mesh.select_all(action='DESELECT')
                        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

                        for e in new_faces:
                            mesh.polygons[e].select = True
                        bpy.ops.object.mode_set(mode='EDIT', toggle=False)

                    else:
                        me = bpy.context.object.data
                        bm = bmesh.from_edit_mesh(me)

                        sel = []
                        edge_dic = {}
                        vert_list = []
                        end_verts = []

                        # Store edges and verts in dictionary
                        for e in bm.edges:
                            if e.select:
                                sel.append(e.index)

                                # Populate vert_list
                                vert_list.append(e.verts[0].index)
                                vert_list.append(e.verts[1].index)

                                # Store dictionary
                                edge_dic[e.index] = [e.verts[0].index, e.verts[1].index]

                        # Store end verts
                        for v in vert_list:
                            if vert_list.count(v) == 1:
                                end_verts.append(v)

                        # Check verts in dictionary
                        for key, value in edge_dic.items():
                            if value[0] in end_verts:
                                sel.remove(key)
                                continue
                            if value[1] in end_verts:
                                sel.remove(key)


                        bmesh.update_edit_mesh(me, True, False)

                        # Select the resulting edges
                        bpy.ops.mesh.select_all(action='DESELECT')

                        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                        mesh = bpy.context.active_object.data.edges
                        for e in sel:
                            mesh[e].select = True
                        bpy.ops.object.mode_set(mode='EDIT', toggle=False)


                return {'FINISHED'}

class paintSelect(bpy.types.Operator):
    """Click and drag to select"""
    bl_idname = "view3d.select_paint"
    bl_label = "Paint Select"
    bl_options = {'REGISTER', 'UNDO'}

    deselect = BoolProperty(default = False, description = 'Deselect objects, polys, edges or verts')
    toggle = BoolProperty(default = False, description = 'Toggles the selection. NOTE: this option can be slow on heavy meshes')
    sel_before = IntProperty(description = 'Do Not Touch', options = {'HIDDEN'})
    sel_after = IntProperty(description = 'Do Not Touch', options = {'HIDDEN'})

    def modal(self, context, event):

        #if event.type == 'MOUSEMOVE':
        refresh = event.mouse_x


        if self.deselect == False:
            bpy.ops.view3d.select('INVOKE_DEFAULT', extend = True, deselect = False)
        else:
            bpy.ops.view3d.select('INVOKE_DEFAULT', extend = False, deselect = True, toggle = True)


        if event.value == 'RELEASE':
            return {'FINISHED'}


        return {'RUNNING_MODAL'}

    def invoke(self, context, event):

        if self.toggle:
            sel_ob = len(bpy.context.selected_objects)

            if sel_ob >= 1:
                mode = bpy.context.object.mode

                if mode == 'EDIT':
                    sel_mode = bpy.context.tool_settings.mesh_select_mode[:]

                    # Get Selection before
                    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                    ob = bpy.context.object.data
                    # check verts
                    if sel_mode[0]:
                        for v in ob.vertices:
                            if v.select:
                                self.sel_before += 1
                    # check edges
                    elif sel_mode[1]:
                        for e in ob.edges:
                            if e.select:
                                self.sel_before += 1
                    # check polys
                    else:
                        for p in ob.polygons:
                            if p.select:
                                self.sel_before += 1

                    # Toggle Selection
                    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                    bpy.ops.view3d.select('INVOKE_DEFAULT', extend = False, toggle = True)

                    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                    ob = bpy.context.object.data
                    # check verts after
                    if sel_mode[0]:
                        for v in ob.vertices:
                            if v.select:
                                self.sel_after += 1

                    # check edges after
                    elif sel_mode[1]:
                        for e in ob.edges:
                            if e.select:
                                self.sel_after += 1
                    # check polys after
                    else:
                        for p in ob.polygons:
                            if p.select:
                                self.sel_after += 1


                    if self.sel_after > self.sel_before:
                        self.deselect = False
                    elif self.sel_after == self.sel_before:
                        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                        bpy.ops.mesh.select_all(action='DESELECT')
                        return {'FINISHED'}
                    else:
                        self.deselect = True

                    bpy.ops.object.mode_set(mode='EDIT', toggle=False)

                elif mode == 'OBJECT':
                    bpy.ops.view3d.select('INVOKE_DEFAULT', extend = False, toggle = True)

                    sel_ob_after = len(bpy.context.selected_objects)

                    if sel_ob_after < sel_ob:
                        self.deselect = True


        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class pathSelectRing(bpy.types.Operator):
    """Selects the shortest edge ring path"""
    bl_idname = "mesh.path_select_ring"
    bl_label = "Path Select Ring"
    bl_options = {'REGISTER', 'UNDO'}

    pick = BoolProperty(name = "Pick Mode", description = "Pick Mode", default = False)
    collapse = BoolProperty(name = "Collapse", description = "Collapses everything between your two selected edges", default = False)

    def draw(self, context):
        layout = self.layout


    def execute(self, context):

        me = bpy.context.object.data
        bm = bmesh.from_edit_mesh(me)
        mesh = bpy.context.active_object.data
        sel_mode = bpy.context.tool_settings.mesh_select_mode[:]

        org_sel = []
        start_end = []
        active_edge = []
        border_sel = []
        vert_sel = []
        face_sel = []

        if sel_mode[1]:

            bpy.context.tool_settings.mesh_select_mode = [False, True, False]

            if self.pick:
                bpy.ops.view3d.select('INVOKE_DEFAULT', extend=True, deselect=False, toggle=False)


            # Store the Start and End edges
            iterate = 0
            for e in reversed(bm.select_history):
                if isinstance(e, bmesh.types.BMEdge):
                    iterate += 1
                    start_end.append(e)
                    if iterate >= 2:
                        break

            if len(start_end) <= 1:
                if self.collapse:
                    bpy.ops.mesh.merge(type='COLLAPSE', uvs=True)
                    return{'FINISHED'}
                return{'CANCELLED'}

            # Store active edge
            for e in reversed(bm.select_history):
                if isinstance(e, bmesh.types.BMEdge):
                    active_edge = e.index
                    break

            # Store original edges
            for e in bm.edges:
                if e.select:
                    org_sel.append(e)

            # Store visible faces
            bpy.ops.mesh.select_all(action='SELECT')
            for f in bm.faces:
                if f.select:
                    face_sel.append(f)


            # Store boundry edges
            bpy.ops.mesh.region_to_loop()

            for e in bm.edges:
                if e.select:
                    border_sel.append(e)

            bpy.ops.mesh.select_all(action='DESELECT')

            # Select Start and End edges
            for e in start_end:
                e.select = True

            # Hide trick
            bpy.ops.mesh.loop_multi_select(ring=True)

            bpy.ops.mesh.select_mode(use_extend=False, use_expand=True, type='FACE')
            bpy.ops.mesh.hide(unselected=True)

            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
            bpy.ops.mesh.select_all(action='DESELECT')
            for e in start_end:
                e.select = True
            bpy.ops.mesh.shortest_path_select()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')

            bpy.ops.mesh.select_all(action='INVERT')
            bpy.ops.mesh.reveal()
            bpy.ops.mesh.select_all(action='INVERT')
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=True, type='EDGE')

            # Deselect border edges
            for e in border_sel:
                e.select = False

            # Add to original selection
            for e in bm.edges:
                if e.select:
                    org_sel.append(e)

            # Restore hidden polygons
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
            for f in face_sel:
                f.select = True
            bpy.ops.mesh.hide(unselected=True)


            # Reselect original selection
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
            bpy.ops.mesh.select_all(action='DESELECT')
            for e in org_sel:
                e.select = True

            # Set active edge
            bm.select_history.add(bm.edges[active_edge])


            if self.collapse:
                bpy.ops.mesh.merge(type='COLLAPSE', uvs=True)

            bmesh.update_edit_mesh(me, True, False)

            return {'FINISHED'}

        else:
            self.report({'WARNING'}, "This tool only workins in edge mode.")
            return {'CANCELLED'}




#Draws the Custom Menu in Object Mode
class ktools_menu(bpy.types.Menu):
        bl_label = "KTools - Object Mode"
        bl_idname = "OBJECT_MT_ktools_menu"

        def draw(self, context):

                layout = self.layout
                layout.operator_context = 'INVOKE_DEFAULT'
                layout.operator("mesh.draw_poly")
                layout.operator("object.toggle_silhouette")
                layout.operator("mesh.quickbool")
                layout.operator("mesh.calc_normals")
                layout.operator("object.custom_autosmooth")
                layout.operator("object.basic_rename")
                layout.operator("object.lattice_to_selection")


#Draws the Custom Menu in Edit Mode
class VIEW3D_MT_edit_mesh_ktools_menuEdit(bpy.types.Menu):
        bl_label = "KTools - Edit Mode"
        bl_idname = "VIEW3D_MT_edit_mesh_ktools_menuEdit"

        def draw(self, context):



                layout = self.layout

                layout.operator("mesh.cut_tool")
                layout.operator("mesh.snaptoaxis")
                layout.operator("mesh.autotubes")
                layout.operator("mesh.shrinkwrap_smooth")

                layout.operator_context = 'INVOKE_DEFAULT'
                layout.operator("mesh.build_corner")
                layout.operator("object.lattice_to_selection")

                layout.separator()

                layout.operator("mesh.path_select_ring")
                layout.operator("mesh.grow_loop")
                layout.operator("mesh.shrink_loop")
                layout.operator("mesh.extend_loop")

                layout.separator()

                layout.operator("mesh.draw_poly")
                layout.operator("object.toggle_silhouette")
                layout.operator("mesh.quickbool")
                layout.operator("object.custom_autosmooth")
                layout.operator("mesh.calc_normals")
                layout.operator("object.basic_rename")



#Calls the KTools Object Menu
class ktools(bpy.types.Operator): #Namesuggestion: K-Tools or K-Mac
        """Calls the KTools Menu"""
        bl_idname = "object.ktools"
        bl_label = "KTools Object Menu"
        #bl_options = {'REGISTER', 'UNDO'}

        def execute(self, context):


            bpy.ops.wm.call_menu(name=ktools_menu.bl_idname)
            return {'FINISHED'}

            """
            sel_ob = bpy.context.object


            if sel_ob:

                mode = bpy.context.active_object.mode

                if mode == 'EDIT':
                        bpy.ops.wm.call_menu(name=VIEW3D_MT_edit_mesh_ktools_menuEdit.bl_idname)

                else:
                        bpy.ops.wm.call_menu(name=ktools_menu.bl_idname)

                return {'FINISHED'}

            else:
                bpy.ops.wm.call_menu(name=ktools_menu.bl_idname)
                return {'FINISHED'}
                #self.report({'WARNING'}, "Active object is not a mesh.")
                #return {'CANCELLED'}
                """

#Calls the KTools Edit Menu
class ktools_mesh(bpy.types.Operator): #Namesuggestion: K-Tools or K-Mac
        """Calls the KTools Edit Menu"""
        bl_idname = "mesh.ktools_mesh"
        bl_label = "KTools Mesh Menu"
        #bl_options = {'REGISTER', 'UNDO'}

        def execute(self, context):


            bpy.ops.wm.call_menu(name=VIEW3D_MT_edit_mesh_ktools_menuEdit.bl_idname)
            return {'FINISHED'}


# draw function for integration in menus
def menu_func(self, context):
    self.layout.separator()
    self.layout.menu("VIEW3D_MT_edit_mesh_ktools_menuEdit", text = "KTools")
def menu_func_ob(self, context):
    self.layout.separator()
    self.layout.menu("OBJECT_MT_ktools_menu", text = "KTools")

#Register and Unregister all the operators
def register():
        bpy.utils.register_class(lattice_to_selection)
        bpy.utils.register_class(calc_normals)
        bpy.utils.register_class(snaptoaxis)
        bpy.utils.register_class(quickbool)
        bpy.utils.register_class(autotubes)
        bpy.utils.register_class(basicRename)
        bpy.utils.register_class(cut_tool)
        bpy.utils.register_class(customAutoSmooth)
        bpy.utils.register_class(shrinkwrapSmooth)
        bpy.utils.register_class(buildCorner)
        bpy.utils.register_class(drawPoly)
        bpy.utils.register_class(toggleSilhouette)
        bpy.utils.register_class(growLoop)
        bpy.utils.register_class(extendLoop)
        bpy.utils.register_class(shrinkLoop)
        bpy.utils.register_class(paintSelect)
        bpy.utils.register_class(pathSelectRing)
        bpy.utils.register_class(ktools_menu)
        bpy.utils.register_class(VIEW3D_MT_edit_mesh_ktools_menuEdit)
        bpy.utils.register_class(ktools)
        bpy.utils.register_class(ktools_mesh)

        bpy.types.VIEW3D_MT_edit_mesh_specials.prepend(menu_func)
        bpy.types.VIEW3D_MT_object_specials.prepend(menu_func_ob)

        kc = bpy.context.window_manager.keyconfigs.addon
        if kc:
            # Add paint select to CTRL+SHIFT+ALT+LeftMouse
            km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
            kmi = km.keymap_items.new('view3d.select_paint', 'LEFTMOUSE', 'PRESS', shift=True, ctrl=True, alt=True)



def unregister():
        bpy.utils.unregister_class(lattice_to_selection)
        bpy.utils.unregister_class(calc_normals)
        bpy.utils.unregister_class(snaptoaxis)
        bpy.utils.unregister_class(quickbool)
        bpy.utils.unregister_class(autotubes)
        bpy.utils.unregister_class(basicRename)
        bpy.utils.unregister_class(cut_tool)
        bpy.utils.unregister_class(customAutoSmooth)
        bpy.utils.unregister_class(shrinkwrapSmooth)
        bpy.utils.unregister_class(buildCorner)
        bpy.utils.unregister_class(drawPoly)
        bpy.utils.unregister_class(toggleSilhouette)
        bpy.utils.unregister_class(growLoop)
        bpy.utils.unregister_class(extendLoop)
        bpy.utils.unregister_class(shrinkLoop)
        bpy.utils.unregister_class(paintSelect)
        bpy.utils.unregister_class(pathSelectRing)
        bpy.utils.unregister_class(ktools_menu)
        bpy.utils.unregister_class(VIEW3D_MT_edit_mesh_ktools_menuEdit)
        bpy.utils.unregister_class(ktools)
        bpy.utils.unregister_class(ktools_mesh)

        bpy.types.VIEW3D_MT_edit_mesh_specials.remove(menu_func)
        bpy.types.VIEW3D_MT_object_specials.remove(menu_func_ob)

        kc = bpy.context.window_manager.keyconfigs.addon
        if kc:
            km = kc.keymaps["3D View"]
            for kmi in km.keymap_items:
                if kmi.idname == 'view3d.select_paint':
                    km.keymap_items.remove(kmi)
                    break



# This allows you to run the script directly from blenders text editor
# to test the addon without having to install it.
if __name__ == "__main__":
        register()
