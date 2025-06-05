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
"author": "Reiner 'Tiles' Prokein, Draise (Trinumedia)",
"version": (0,2.2),
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
            ## Vertices select
            if select_mode[0]:
                mymode = 0

                # bpy.ops.mesh.dissolve_verts() # This throws a full error report in the face of the user.
                # So we need the below method-
                # Dissolve with catching the error report so that the user does not have the impression that the script is broken.
                if bpy.ops.mesh.dissolve_verts.poll():

                    try:
                        bpy.ops.mesh.dissolve_verts()

                        #self.report({'INFO'}, "Selected vertices were dissolved.")

                        # Check if there is only one vertex left and delete it if true
                        bpy.ops.object.mode_set(mode='OBJECT')
                        remaining_verts = [v for v in me.vertices if v.select]
                        if len(remaining_verts) == 1:
                            me.vertices[remaining_verts[0].index].select = True
                            bpy.ops.object.mode_set(mode='EDIT')
                            bpy.ops.mesh.delete(type='VERT')
                            #self.report({'INFO'}, "Single floating vertices was removed.")
                        else:
                            bpy.ops.object.mode_set(mode='EDIT')

                        # Check if all vertices are selected and delete them if true
                        bpy.ops.object.mode_set(mode='OBJECT')
                        all_verts = [v for v in me.vertices]
                        if len(remaining_verts) == len(all_verts):
                            bpy.ops.object.mode_set(mode='EDIT')
                            bpy.ops.mesh.delete(type='VERT')
                            #self.report({'INFO'}, "All selected vertices were removed.")
                        else:
                            bpy.ops.object.mode_set(mode='EDIT')

                        # Check if there are exactly two selected vertices with no connected edges and delete them
                        selected_verts = [v for v in me.vertices if v.select]
                        if len(selected_verts) == 2:
                            connected_edges = [e for e in me.edges if any(v.index in e.vertices for v in remaining_verts)]
                            if not connected_edges:
                                bpy.ops.object.mode_set(mode='EDIT')
                                bpy.ops.mesh.delete(type='VERT')
                                #self.report({'INFO'}, "Two disconnected vertices as an edge were removed.")
                            else:
                                bpy.ops.object.mode_set(mode='EDIT')

                        # Check if there are exactly two vertices selected and delete them
                        if len(remaining_verts) == 2:
                            bpy.ops.object.mode_set(mode='EDIT')
                            bpy.ops.mesh.delete(type='VERT')
                            #self.report({'INFO'}, "Two last selected vertices as an edge were removed.")
                        else:
                            bpy.ops.object.mode_set(mode='EDIT')


                    except RuntimeError as exception:
                        error = " ".join(exception.args)
                        print("Invalid boundary region to join faces\nYou cannot delete this geometry that way.\nTry another delete method or another selection")
                        self.report({'ERROR'}, error)


            ## Edge select
            elif select_mode[1] and not select_mode[2]:
                mymode = 1

                # bpy.ops.mesh.dissolve_edges(use_verts=self.use_verts) # This throws a full error report in the face of the user.
                # So we need the below method-
                # Dissolve with catching the error report so that the user does not have the impression that the script is broken.
                if bpy.ops.mesh.dissolve_edges.poll():

                    try:
                        # Check if all selected edges are all the edges that exist
                        bpy.ops.object.mode_set(mode='OBJECT')
                        selected_edges = [e for e in me.edges if e.select]
                        all_edges = [e for e in me.edges]

                        # Check if all selected edges are an island
                        island_edges = set()
                        edges_to_check = set(selected_edges)

                        while edges_to_check:
                            edge = edges_to_check.pop()
                            if edge not in island_edges:
                                island_edges.add(edge)
                                connected_edges = [e for e in me.edges if any(v in edge.vertices for v in e.vertices) and e not in island_edges]
                                edges_to_check.update(connected_edges)

                        #### For troubleshooting: ####
                        #if len(selected_edges) == len(island_edges):
                            #self.report({'INFO'}, "Selected edges are all of the edges of that island.")
                        #else:
                            #self.report({'INFO'}, "Selected edges are not all of the edges of that island.")

                        if len(selected_edges) == len(all_edges):
                            bpy.ops.object.mode_set(mode='EDIT')
                            bpy.ops.mesh.delete(type='EDGE')
                            #self.report({'INFO'}, "All selected edges were removed.")
                        elif len(selected_edges) == len(island_edges):
                            bpy.ops.object.mode_set(mode='EDIT')
                            bpy.ops.mesh.delete(type='EDGE')
                            #self.report({'INFO'}, "All connected island edges were removed.")
                        else:
                            # Check if the selected edge has no connecting edges
                            no_connecting_edges = all(find_connected_verts(me, v) == 1 for e in selected_edges for v in e.vertices)
                            if no_connecting_edges:
                                bpy.ops.object.mode_set(mode='EDIT')
                                bpy.ops.mesh.delete(type='EDGE')
                                #self.report({'INFO'}, "Selected edge with no connecting edges was removed.")
                            else:
                                # Check if there are 3 or 4 edges left and remove the selected edge only, breaking face
                                bpy.ops.object.mode_set(mode='OBJECT')
                                if len(all_edges) in [3, 4, 5] or len(island_edges) in [3, 4, 5]:
                                    bpy.ops.object.mode_set(mode='EDIT')
                                    bpy.ops.mesh.delete(type='EDGE_FACE')
                                    #self.report({'INFO'}, "3 or 4 selected edges, only edge was removed.")
                                else:
                                    # Proceed with dissolve
                                    bpy.ops.object.mode_set(mode='EDIT')
                                    bpy.ops.mesh.dissolve_edges(use_verts=self.use_verts)

                                    bpy.ops.mesh.select_mode(type='VERT')
                                    bpy.ops.object.mode_set(mode='OBJECT')
                                    bpy.ops.object.mode_set(mode='EDIT')
                                    vs = [v.index for v in me.vertices if v.select]
                                    bpy.ops.mesh.select_all(action='DESELECT')
                                    bpy.ops.object.mode_set(mode='OBJECT')

                                    for v in vs:
                                        vv = find_connected_verts(me, v)
                                        if vv == 2:
                                            me.vertices[v].select = True
                                    bpy.ops.object.mode_set(mode='EDIT')
                                    bpy.ops.mesh.dissolve_verts()
                                    bpy.ops.mesh.select_all(action='DESELECT')

                                    for v in vs:
                                        me.vertices[v].select = True
                                    #self.report({'INFO'}, "Selected edges were removed.")

                    except RuntimeError as exception:
                        error = " ".join(exception.args)
                        print("Invalid boundary region to join faces\nYou cannot delete this geometry that way. \nTry another delete method or another selection")
                        self.report({'ERROR'}, error)


            ## Face Select
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