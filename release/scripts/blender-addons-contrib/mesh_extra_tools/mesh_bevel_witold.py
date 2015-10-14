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
'''
Bevel add-on
'''
#--- ### Header
bl_info = {
    "name": "Bevel witold",
    "author": "Witold Jaworski",
    "version": (1, 2, 0),
    "blender": (2, 57, 0),
    "location": "View3D >Specials (W-key)",
    "category": "Mesh",
    "description": "Bevels selected edges",
    "warning": "",
    "wiki_url": "http://airplanes3d.net/scripts-252_e.xml",
    "tracker_url": "http://airplanes3d.net/track-252_e.xml"
    }
#--- ### Change log
#2011-08-08 Witold Jaworski: added "Vertex only" feature
#--- ### Imports
import bpy
from bpy.utils import register_module, unregister_module
from bpy.props import FloatProperty, IntProperty, BoolProperty
from math import log10, floor, pow
#--- ### Constants
DEBUG = 0 #Debug flag - just some text printed on the console...
#--- ### Core operation
def bevel(obj, width, use_vertices):
    """Bevels selected edges of the mesh
       Arguments:
            @obj (Object):         an object with a mesh.
                                   It should have some edges selected
            @width (float):        width of the bevel
            @use_vertices (bool):  True, when bevel only vertices. False otherwise
       This function should be called in the Edit Mode, only!
    """
    #
    #edge = bpy.types.MeshEdge
    #obj = bpy.types.Object
    #bevel = bpy.types.BevelModifier

    bpy.ops.object.editmode_toggle() #switch into OBJECT mode
    #adding the Bevel modifier
    bpy.ops.object.modifier_add(type = 'BEVEL')
    bevel = obj.modifiers[-1] #the new modifier is always added at the end
    bevel.limit_method = 'WEIGHT'
    bevel.edge_weight_method = 'LARGEST'
    bevel.width = width
    bevel.use_only_vertices = use_vertices
    #moving it up, to the first position on the modifier stack:
    while obj.modifiers[0] != bevel:
        bpy.ops.object.modifier_move_up(modifier = bevel.name)

    for elm in (obj.data.vertices if use_vertices else obj.data.edges):
        if elm.select:
            elm.bevel_weight = 1.0

    bpy.ops.object.modifier_apply(apply_as = 'DATA', modifier = bevel.name)

    #clean up after applying our modifier: remove bevel weights:
    for elm in (obj.data.vertices if use_vertices else obj.data.edges):
        if elm.select:
            elm.bevel_weight = 0.0

    bpy.ops.object.editmode_toggle() #switch back into EDIT_MESH mode

class bevel_help(bpy.types.Operator):
	bl_idname = 'help.edge_bevel'
	bl_label = ''

	def draw(self, context):
		layout = self.layout
		layout.label('To use:')
		layout.label('Select A edge or edges & bevel.')
		layout.label('or Select 2 or more verices & bevel.')
		layout.label('To Help:')
		layout.label('best used on flat edges & simple edgeflow')
		layout.label('may error if vert joins multiple edges/complex edge selection')

	def execute(self, context):
		return {'FINISHED'}

	def invoke(self, context, event):
		return context.window_manager.invoke_popup(self, width = 350)
#--- ### Operator
class Bevel(bpy.types.Operator):
    ''' Bevels selected edges of the mesh'''
    bl_idname = "mesh.mbevel" #it is not named mesh.bevel, to not confuse with the standard bevel in the future...
    bl_label = "Bevel Selected"
    bl_description = "Bevels selected edges"
    bl_options = {'REGISTER', 'UNDO'} #Set this options, if you want to update
    #                                  parameters of this operator interactively
    #                                  (in the Tools pane)
    #--- parameters
    use_vertices = BoolProperty(name="Only Vertices", description="Bevel vertices (corners), not edges", default = False)

    width = FloatProperty(name="Width", description="Bevel width value (it is multiplied by 10^Exponent)",
                          subtype = 'DISTANCE', default = 0.1, min = 0.0,
                                                    step = 1, precision = 2)
#    exponent = IntProperty(name="Exponent", description="Order of magnitude of the bevel width (the power of 10)", default = 0)

    use_scale = BoolProperty(name="Use object scale", description="Multiply bevel width by the scale of this object", default = False)

    #--- other fields
    LAST_VERT_NAME = "mesh.mbevel.last_vert" #the name of the custom scene property
    LAST_WIDTH_NAME = "mesh.mbevel.last_width" #the name of the custom scene property
    LAST_EXP_NAME = "mesh.mbevel.last_exponent" #the name of the custom scene property
    LAST_SCALE_NAME = "mesh.mbevel.last_scale" #scale Bevel width by the object scale
    #--- Blender interface methods
    @classmethod
    def poll(cls,context):
        return (context.mode == 'EDIT_MESH')

    def invoke(self, context, event):
        #input validation:
        # 1. Require single-user mesh (modifiers cannot be applied to the multi-user ones):
        obj = context.object
        if obj.data.users > 1:
            self.report(type='ERROR', message="Make this mesh single-user, first")
            return {'CANCELLED'}
        # 2. is there anything selected?
        self.use_vertices = context.scene.get(self.LAST_VERT_NAME, self.use_vertices)

        bpy.ops.object.editmode_toggle()

        if self.use_vertices :
            selected = list(filter(lambda e: e.select, context.object.data.vertices))
        else:
            selected = list(filter(lambda e: e.select, context.object.data.edges))

        bpy.ops.object.editmode_toggle()

        if len(selected) > 0:
            self.use_scale = context.object.get(self.LAST_SCALE_NAME, self.use_scale)

            #setup the default width, to avoid user surprises :)
            def_exp = floor(log10(obj.dimensions.length)) #heuristic: default width exponent is derived from the object size...
            self.exponent = context.scene.get(self.LAST_EXP_NAME, def_exp) #Let's read the last used value, stored in the scene...
            larger = def_exp - self.exponent #How larger/smaller is actual object, comparing to the last used value?
            if larger <= 1 and larger >= 0: #OK, this object has similar size to the previous one...
                self.width = context.scene.get(self.LAST_WIDTH_NAME, self.width)
            else: #the previous bevel size would be too small or too large - revert to defaults:
                self.width = 0.1 #10% of the object order of magnitude
                self.exponent = def_exp #the order of magnitude
            #parameters adjusted, run the command!
            return self.execute(context)
        else:
            self.report(type='ERROR', message="Nothing is selected")
            return {'CANCELLED'}

    def execute(self,context):
        #calculate the bevel width, for this object size and scale
        width = self.width*pow(10,self.exponent)
        if not self.use_scale : width /= max(context.object.scale)
        #call the main function:
        bevel(context.object,width, self.use_vertices)
        #save the last used parameters:
        context.scene[self.LAST_VERT_NAME] = self.use_vertices
        context.scene[self.LAST_WIDTH_NAME] = self.width
        context.scene[self.LAST_EXP_NAME] = self.exponent
        context.object[self.LAST_SCALE_NAME] = self.use_scale
        return {'FINISHED'}

def menu_draw(self, context):
    self.layout.operator_context = 'INVOKE_REGION_WIN'
    self.layout.operator(Bevel.bl_idname, "Bevel_Witold")

#--- ### Register
def register():
    register_module(__name__)
    bpy.types.VIEW3D_MT_edit_mesh_specials.prepend(menu_draw)

def unregister():
    bpy.types.VIEW3D_MT_edit_mesh_specials.remove(menu_draw)
    unregister_module(__name__)

#--- ### Main code
if __name__ == '__main__':
    register()

if DEBUG > 0: print("mesh_bevel.py loaded!")
