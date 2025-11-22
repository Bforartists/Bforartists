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
import bmesh
bl_info = {
"name": "Smart Delete",
"description": "Auto detect a delete elements",
"author": "Reiner 'Tiles' Prokein, Draise (Trinumedia)",
"version": (0,2.3),
"blender": (4, 0, 0),
"doc_url": "https://github.com/Bforartists/Manual",
"tracker_url": "https://github.com/Bforartists/Bforartists",
"support": "OFFICIAL",
"category": "Bforartists",
}
 

def find_connected_verts(me, found_index):  
    """Optimized version that uses edge connectivity cache"""
    return len(me.vertices[found_index].link_edges)
 
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
            ## Vertices select - Optimized for performance with bmesh
            if select_mode[0]:
                mymode = 0

                try:
                    # Use bmesh directly for maximum performance on dense meshes
                    bm = bmesh.from_edit_mesh(me)
                    
                    # Get selected vertices
                    selected_verts = [v for v in bm.verts if v.select]
                    
                    if not selected_verts:
                        bmesh.update_edit_mesh(me)
                        return {'FINISHED'}
                    
                    # Handle floating/isolated vertices and small islands first
                    delete_verts = []  # Vertices that should be deleted (not dissolved)
                    dissolve_verts = []  # Vertices that can be dissolved
                    
                    # Check for vertices that form small islands that can't be dissolved
                    processed_verts = set()
                    
                    for vert in selected_verts:
                        if vert in processed_verts:
                            continue
                            
                        # Check for completely isolated vertices (no edges, no faces)
                        if len(vert.link_edges) == 0 and len(vert.link_faces) == 0:
                            delete_verts.append(vert)
                            processed_verts.add(vert)
                            continue
                            
                        # Check for small islands (2 vertices connected by 1 edge)
                        if len(vert.link_edges) == 1:
                            connected_vert = next(iter(vert.link_edges)).other_vert(vert)
                            if connected_vert in selected_verts and connected_vert not in processed_verts:
                                # This is a 2-vertex island - delete both vertices
                                delete_verts.extend([vert, connected_vert])
                                processed_verts.update([vert, connected_vert])
                                continue
                                
                        # Check for vertices that are part of larger structures but can't be dissolved
                        # Vertices with only 1 connection (end of chain) should be deleted, not dissolved
                        if len(vert.link_edges) == 1:
                            delete_verts.append(vert)
                            processed_verts.add(vert)
                            continue
                            
                        # For all other vertices, try to dissolve them
                        if vert not in processed_verts:
                            dissolve_verts.append(vert)
                            processed_verts.add(vert)

                    # Delete vertices that can't be dissolved first
                    if delete_verts:
                        bmesh.ops.delete(bm, geom=delete_verts, context='VERTS')
                    
                    # Handle remaining vertices that can be dissolved
                    if dissolve_verts:
                        # Check if all vertices are selected
                        if len(dissolve_verts) == len(bm.verts):
                            # All vertices selected - delete them all
                            bmesh.ops.delete(bm, geom=dissolve_verts, context='VERTS')
                        else:
                            # Try to dissolve the remaining vertices
                            try:
                                bmesh.ops.dissolve_verts(bm, verts=dissolve_verts)
                            except:
                                # If dissolve fails, delete the vertices
                                bmesh.ops.delete(bm, geom=dissolve_verts, context='VERTS')
                    
                    bmesh.update_edit_mesh(me)
                    
                except RuntimeError as exception:
                    # Fallback to standard operation if bmesh fails
                    try:
                        bpy.ops.mesh.dissolve_verts()
                    except RuntimeError as fallback_exception:
                        error = " ".join(fallback_exception.args)
                        print("Invalid boundary region to join faces\nYou cannot delete this geometry that way.\nTry another delete method or another selection")
                        self.report({'ERROR'}, error)


            ## Edge select - Optimized for performance using bmesh
            elif select_mode[1] and not select_mode[2]:
                mymode = 1

                if bpy.ops.mesh.dissolve_edges.poll():
                    try:
                        # Use bmesh for faster processing without mode switching
                        bm = bmesh.from_edit_mesh(me)
                        
                        selected_edges = [e for e in bm.edges if e.select]
                        all_edges = list(bm.edges)
                        
                        if not selected_edges:
                            bmesh.update_edit_mesh(me)
                            return {'FINISHED'}
                        
                        # Handle floating face edges - check if we're dealing with floating faces
                        complete_floating_faces_edges = []  # All edges of a floating face selected
                        partial_floating_faces_edges = []    # Some edges of a floating face selected
                        regular_edges = []
                        
                        # First pass: identify faces that have all edges selected (complete floating faces)
                        processed_faces = set()
                        for edge in selected_edges:
                            if len(edge.link_faces) == 1:  # Floating face edge
                                face = next(iter(edge.link_faces))
                                if face not in processed_faces:
                                    # Check if ALL edges of this face are selected
                                    face_edges_selected = all(e.select for e in face.edges)
                                    if face_edges_selected:
                                        complete_floating_faces_edges.extend(face.edges)
                                        processed_faces.add(face)
                        
                        # Second pass: handle edges that are part of floating faces but not all edges are selected
                        for edge in selected_edges:
                            if len(edge.link_faces) == 1:  # Floating face edge
                                face = next(iter(edge.link_faces))
                                if face not in processed_faces:  # This face has partial selection
                                    # For partial selection, delete the selected edges to collapse the face
                                    partial_floating_faces_edges.append(edge)
                            elif edge not in complete_floating_faces_edges:
                                regular_edges.append(edge)
                        
                        # Handle complete floating faces - delete them entirely (face + edges)
                        if complete_floating_faces_edges:
                            # Get all faces connected to these edges to delete them
                            faces_to_delete = set()
                            for edge in complete_floating_faces_edges:
                                faces_to_delete.update(edge.link_faces)
                            
                            if faces_to_delete:
                                # Delete the faces and their edges
                                bmesh.ops.delete(bm, geom=list(faces_to_delete), context='FACES')
                        
                        # Handle partial selection on floating faces - delete edges to collapse the face
                        if partial_floating_faces_edges:
                            # Delete the selected edges to collapse quad into triangle or remove face
                            bmesh.ops.delete(bm, geom=partial_floating_faces_edges, context='EDGES')
                        
                        # Handle regular edges
                        if regular_edges:
                            # Check for isolated edges (edges with no connected faces - wire edges)
                            isolated_edges = []
                            edges_to_dissolve = []
                            
                            for edge in regular_edges:
                                if len(edge.link_faces) == 0:  # Wire edges
                                    isolated_edges.append(edge)
                                else:
                                    edges_to_dissolve.append(edge)
                            
                            if isolated_edges:
                                # Delete wire edges (they have no faces to merge)
                                bmesh.ops.delete(bm, geom=isolated_edges, context='EDGES')
                            
                            if edges_to_dissolve:
                                # Use dissolve to merge adjacent faces instead of deleting them
                                dissolve_result = bmesh.ops.dissolve_edges(bm, edges=edges_to_dissolve, use_verts=True)
                                
                                # Clean up any resulting vertices with only 2 connections
                                if dissolve_result and 'verts' in dissolve_result:
                                    verts_to_dissolve = [v for v in dissolve_result['verts'] if len(v.link_edges) == 2]
                                    if verts_to_dissolve:
                                        bmesh.ops.dissolve_verts(bm, verts=verts_to_dissolve)
                        
                        # Final cleanup: Check for and remove any remaining isolated vertices
                        # This handles the case where deleting edges leaves floating vertices
                        isolated_verts = [v for v in bm.verts if v.select and len(v.link_edges) == 0 and len(v.link_faces) == 0]
                        if isolated_verts:
                            bmesh.ops.delete(bm, geom=isolated_verts, context='VERTS')
                        
                        bmesh.update_edit_mesh(me)
                        
                    except RuntimeError as exception:
                        error = " ".join(exception.args)
                        print("Invalid boundary region to join faces\nYou cannot delete this geometry that way. \nTry another delete method or another selection")
                        self.report({'ERROR'}, error)


            ## Face Select - Optimized with bmesh
            elif select_mode[2] and not select_mode[1]:
                mymode = 2 
                try:
                    # Use bmesh for faster face deletion on dense meshes
                    bm = bmesh.from_edit_mesh(me)
                    selected_faces = [f for f in bm.faces if f.select]
                    if selected_faces:
                        bmesh.ops.delete(bm, geom=selected_faces, context='FACES')
                        bmesh.update_edit_mesh(me)
                except:
                    # Fallback to standard operation if bmesh fails
                    bpy.ops.mesh.delete(type='FACE')
            #Dissolve Vertices - Fallback
            else:
                try:
                    bm = bmesh.from_edit_mesh(me)
                    selected_verts = [v for v in bm.verts if v.select]
                    if selected_verts:
                        bmesh.ops.dissolve_verts(bm, verts=selected_verts)
                        bmesh.update_edit_mesh(me)
                except:
                    bpy.ops.mesh.dissolve_verts()
                
            # Maintain selection mode - faster than switching back and forth
            # The bmesh operations preserve selection context better
            if mymode == 1 and not select_mode[1]:
                # Only set back to edge mode if it was changed
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