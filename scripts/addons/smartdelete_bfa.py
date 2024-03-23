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

#This script is based at the work of Vladislav Kindushov and its Smart Delete addon


import bpy
bl_info = {
"name": "Smart Delete",
"description": "Auto detect a delete elements",
"author": "Reiner 'Tiles' Prokein",
"version": (0,2.1),
"blender": (2, 80, 0),
"doc_url": "https://github.com/Bforartists/Manual",
"tracker_url": "https://github.com/Bforartists/Bforartists",
"support": "OFFICIAL",
"category": "Bforartists",
}
 

def find_connected_verts(me, found_index):  
    edges = me.edges  
    connecting_edges = [i for i in edges if found_index in i.vertices[:]]  
    #print('connecting_edges',len(connecting_edges)) # Do not want to polute the console.
    return len(connecting_edges)  
 
class SDEL_OT_meshdissolvecontextual(bpy.types.Operator):
    """ Dissolves mesh elements based on context instead
    of forcing the user to select from a menu what
    it should dissolve.
    """
    bl_idname = "mesh.dissolve_contextual_bfa"
    bl_label = "Smart Delete"
    bl_options = {'UNDO'}
   
    use_verts : bpy.props.BoolProperty(name="Use Verts", default=False)
    
    mymode = 0 # The script changes the modes at one point. We want to store the mode before the operation.
 
    @classmethod
    def poll(cls, context):
        return (context.active_object is not None)# and (context.mode == "EDIT_MESH")
   
    def execute(self, context):

        if bpy.context.mode == 'EDIT_MESH':
            select_mode = context.tool_settings.mesh_select_mode
            me = context.object.data
            # Vertices select
            if select_mode[0]:
                mymode = 0

                # bpy.ops.mesh.dissolve_verts() # This throws a full error report in the face of the user.
                # So we need the below method-
                # Dissolve with catching the error report so that the user does not have the impression that the script is broken.
                if bpy.ops.mesh.dissolve_verts.poll():

                    try:
                        bpy.ops.mesh.dissolve_verts()

                    except RuntimeError as exception:
                        error = " ".join(exception.args)
                        print("Invalid boundary region to join faces\nYou cannot delete this geometry that way.\nTry another delete method or another selection")
                        self.report({'ERROR'}, error)


            # Edge select
            elif select_mode[1] and not select_mode[2]:
                mymode = 1

                # bpy.ops.mesh.dissolve_edges(use_verts=self.use_verts) # This throws a full error report in the face of the user.
                # So we need the below method-
                # Dissolve with catching the error report so that the user does not have the impression that the script is broken.
                if bpy.ops.mesh.dissolve_edges.poll():

                    try:
                        bpy.ops.mesh.dissolve_edges(use_verts=self.use_verts)

                        bpy.ops.mesh.select_mode(type='VERT')
                        bpy.ops.object.mode_set(mode='OBJECT')
                        bpy.ops.object.mode_set(mode='EDIT')
                        vs = [v.index for v in me.vertices if v.select]
                        bpy.ops.mesh.select_all(action='DESELECT')
                        bpy.ops.object.mode_set(mode='OBJECT')
               
                        for v in vs:
                            vv = find_connected_verts(me, v)
                            if vv==2:
                                me.vertices[v].select = True
                        bpy.ops.object.mode_set(mode='EDIT')
                        bpy.ops.mesh.dissolve_verts()
                        bpy.ops.mesh.select_all(action='DESELECT')
               
                        for v in vs:
                            me.vertices[v].select = True

                    except RuntimeError as exception:
                        error = " ".join(exception.args)
                        print("Invalid boundary region to join faces\nYou cannot delete this geometry that way. \nTry another delete method or another selection")
                        self.report({'ERROR'}, error)
                
            # Face Select        
            elif select_mode[2] and not select_mode[1]:
                mymode = 2 
                bpy.ops.mesh.delete(type='FACE')
            #Dissolve Vertices
            else:
                bpy.ops.mesh.dissolve_verts()
                
            # back to previous select mode! When you delete in edge select mode 
            # then the selection method can jump to vertex select mode. Unwanted behaviour. 
            # So we put it back to edge select mode manually after done.
                          
            if mymode == 1:
                bpy.ops.mesh.select_mode(type='EDGE')
                        
        return {'FINISHED'}
classes = (SDEL_OT_meshdissolvecontextual, )

def menu_func(self, context):
    self.layout.operator(SDEL_OT_meshdissolvecontextual.bl_idname, icon = "DELETE")

def register():
    from bpy.utils import register_class
    for cls in classes:
       register_class(cls)
    #bpy.utils.register_class(SDEL_OT_meshdissolvecontextual)#the old way
    bpy.types.VIEW3D_MT_edit_mesh.append(menu_func)
    

def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
       unregister_class(cls)
    #bpy.utils.unregister_class(SDEL_OT_meshdissolvecontextual)#the old way
    bpy.types.VIEW3D_MT_edit_mesh.remove(menu_func)


if __name__ == "__main__":
    register()