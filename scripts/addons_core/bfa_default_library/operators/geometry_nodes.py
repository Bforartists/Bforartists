# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
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

# -----------------------------------------------------------------------------
# Geometry Nodes Asset Operations
# Handles operations related to Geometry Nodes assets including smart primitives
# -----------------------------------------------------------------------------

import bpy
from bpy.types import Operator

# -----------------------------------------------------------------------------
# Smart Primitives
# -----------------------------------------------------------------------------

# Constants for assets with operators names
ASSET_NAMES = [
    "Smart Capsule",
    "Smart Capsule Revolved", 
    "Smart Circle",
    "Smart Circle Revolved",
    "Smart Cone",
    "Smart Cone Rounded",
    "Smart Cone Rounded Revolved",
    "Smart Cube",
    "Smart Cube Rounded",
    "Smart Curve Lofted",
    "Smart Cylinder",
    "Smart Cylinder Rounded Revolved",
    "Smart Grid",
    "Smart Icosphere",
    "Smart Sphere",
    "Smart Sphere Revolved",
    "Smart Spiral",
    "Smart Torus",
    "Smart Tube Revolved",
    "Smart Tube Rounded Revolved"
    "Blend Normals by Proximity"
]

def get_geometry_nodes_inputs(modifier):
    """Returns socket names and types for Geometry Nodes modifier inputs, excluding 'Geometry'.
    Only works with Geometry Nodes modifiers - returns empty list for other modifier types."""
    # First check if this is actually a Geometry Nodes modifier
    if not hasattr(modifier, 'node_group') or modifier.type != 'NODES':
        return []

    # Then check if it has a node group
    if not modifier.node_group:
        return []
    
    inputs = []
    # Get all interface items including panels
    interface_items = modifier.node_group.interface.items_tree
    
    # Create a mapping of panel names to their child sockets
    panel_map = {}
    for item in interface_items:
        if item.item_type == 'PANEL':
            # Use name as key since identifier isn't available
            panel_map[item.name] = {
                'name': item.name,
                'children': []
            }
    
    # Process all items and organize by panels
    for item in interface_items:
        if item.item_type == 'SOCKET' and item.name != "Geometry":
            socket_data = {
                'name': item.name,
                'identifier': item.identifier,  # Use actual identifier instead of name
                'socket_type': item.socket_type,
                'panel': None
            }
            
            # If socket is in a panel, add to panel's children
            if item.parent and item.parent.name in panel_map:
                panel_map[item.parent.name]['children'].append(socket_data)
            else:
                # Add to root if no panel
                inputs.append((socket_data['name'], socket_data['identifier'], 
                             socket_data['socket_type'], None))
    
    # Add panel sockets in correct order
    for panel_data in panel_map.values():
        if panel_data['children']:
            for child in panel_data['children']:
                inputs.append((child['name'], child['identifier'], 
                             child['socket_type'], panel_data['name']))
    
    return inputs

def is_smart_primitive_object(obj):
    """Check if object has any smart primitive geometry nodes modifiers"""
    if not obj or not obj.modifiers:
        return False
        
    for mod in obj.modifiers:
        if (mod.type == 'NODES' and 
            mod.node_group and 
            any(mod.node_group.name.startswith(name) for name in ASSET_NAMES)):
            return True
    return False

def get_all_smart_primitive_objects(context):
    """Get all objects that are smart primitives in the current context"""
    return [obj for obj in context.selected_objects if is_smart_primitive_object(obj)]

class OBJECT_OT_ApplySmartPrimitives(Operator):
    """Apply selected smart primitives, converts to mesh, joins them, and optionally remeshes"""
    bl_idname = "object.apply_smart_primitives"
    bl_label = "Apply Smart Primitives"
    bl_description = "Convert smart primitives to regular mesh objects with optional joining and boolean operations"
    bl_options = {'REGISTER', 'UNDO'}

    join_on_apply: bpy.props.BoolProperty(
        name="Join on Apply",
        description="Join all converted primitives into a single mesh object",
        default=True
    )

    boolean_on_apply: bpy.props.BoolProperty(
        name="Boolean on Apply",
        description="Apply boolean union operation to combine the primitives",
        default=False
    )

    boolean_on_apply: bpy.props.BoolProperty(
        name="Remesh on Apply",
        description="Apply boolean union operation to combine the primitives",
        default=False
    )

    @classmethod
    def poll(cls, context):
        """Available if there are smart primitive objects selected"""
        return any(is_smart_primitive_object(obj) for obj in context.selected_objects)
    
    def execute(self, context):
        smart_objects = get_all_smart_primitive_objects(context)
        
        if not smart_objects:
            self.report({'WARNING'}, "No smart primitive objects found to process")
            return {'CANCELLED'}

        # Store original state
        original_active = context.view_layer.objects.active
        original_selected = set(context.selected_objects)
        objects_to_delete = []
        new_objects = []
        
        try:
            # Convert all smart objects to mesh
            bpy.ops.object.select_all(action='DESELECT')
            for obj in smart_objects:
                obj.select_set(True)
                objects_to_delete.append(obj)
            
            context.view_layer.objects.active = smart_objects[0]
            bpy.ops.object.visual_geometry_to_objects()
            
            # Get newly created mesh objects
            current_selected = set(context.selected_objects)
            new_objects = [obj for obj in current_selected if obj not in original_selected]
            
            final_object = None
            
            if new_objects:
                if self.boolean_on_apply:
                    # Boolean union operation
                    base_object = new_objects[0]
                    base_object.select_set(True)
                    context.view_layer.objects.active = base_object

                    objects_to_bool = new_objects[1:]
                    objects_to_delete.extend(objects_to_bool)

                    for obj in objects_to_bool:
                        if obj and obj.name in context.scene.objects:
                            bool_mod = base_object.modifiers.new(name="Boolean", type='BOOLEAN')
                            bool_mod.operation = 'UNION'
                            bool_mod.solver = 'FLOAT'
                            bool_mod.object = obj
                            
                            try:
                                bpy.ops.object.modifier_apply(modifier=bool_mod.name)
                            except RuntimeError as e:
                                print(f"Boolean operation failed: {str(e)}")
                                continue
                            
                            context.view_layer.update()
                            
                            bpy.ops.object.select_all(action='DESELECT')
                            base_object.select_set(True)
                            context.view_layer.objects.active = base_object
                    
                    final_object = base_object
                
                elif self.join_on_apply and len(new_objects) > 1:
                    # Simple join operation
                    context.view_layer.objects.active = new_objects[0]
                    for obj in new_objects:
                        obj.select_set(True)
                    bpy.ops.object.join()
                    final_object = context.view_layer.objects.active
                else:
                    final_object = new_objects[0]
            
            # Clean up original objects
            bpy.ops.object.select_all(action='DESELECT')
            for obj in objects_to_delete:
                if obj and obj.name in context.scene.objects:
                    obj.select_set(True)
            bpy.ops.object.delete()
            
            # Select final object
            if final_object and final_object.name in context.scene.objects:
                bpy.ops.object.select_all(action='DESELECT')
                final_object.select_set(True)
                context.view_layer.objects.active = final_object

                # Clear sharp edges
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.mark_sharp(clear=True)
                bpy.ops.object.mode_set(mode='OBJECT')
            
            self.report({'INFO'}, f"Applied {len(smart_objects)} smart primitives")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error during operation: {str(e)}")
            # Restore original state
            if original_active and original_active.name in context.scene.objects:
                context.view_layer.objects.active = original_active
            return {'CANCELLED'}

# -----------------------------------------------------------------------------
# Mesh Blend by Proximity
# -----------------------------------------------------------------------------

# Import the utility function from operators
from ..wizard_operators import inject_nodegroup_to_collection

def has_nodegroup_in_material(material, nodegroup_name):
    """Check if material already has the specified node group"""
    for node in material.node_tree.nodes:
        if (node.type == 'GROUP' and 
            node.node_group and 
            node.node_group.name == nodegroup_name):
            return True
    return False


class OBJECT_OT_InjectNodegroupToCollection(Operator):
    """Inject node group to all materials in target collection, skipping duplicates"""
    bl_idname = "object.inject_nodegroup_to_collection"
    bl_label = "Inject Node Group to Materials"
    bl_description = "Inject S_Intersections node group to materials of objects in target collection"
    bl_options = {'REGISTER', 'UNDO'}

    nodegroup_name: bpy.props.StringProperty(
        name="Node Group",
        description="Name of the node group to inject",
        default="S_Intersections"
    )

    @classmethod
    def poll(cls, context):
        """Available when there's an active object with Blend Normals by Proximity modifier"""
        obj = context.object
        if not obj or not obj.modifiers:
            return False
        
        for mod in obj.modifiers:
            if (mod.type == 'NODES' and 
                mod.node_group and 
                "Blend Normals by Proximity" in mod.node_group.name):
                return True
        return False

    def execute(self, context):
        obj = context.object
        
        # Find the Blend Normals by Proximity modifier
        target_collection = None
        for mod in obj.modifiers:
            if (mod.type == 'NODES' and 
                mod.node_group and 
                "Blend Normals by Proximity" in mod.node_group.name):
                
                # Try to get the collection from the modifier
                for socket_name in mod.keys():
                    if socket_name.startswith("Socket_") and isinstance(mod[socket_name], bpy.types.Collection):
                        target_collection = mod[socket_name]
                        break
                
                if target_collection:
                    break
        
        if not target_collection:
            self.report({'ERROR'}, "No target collection found in Blend Normals by Proximity modifier")
            return {'CANCELLED'}
        
        # Inject node group to collection
        success = inject_nodegroup_to_collection(target_collection.name, self.nodegroup_name)
        
        if success:
            self.report({'INFO'}, f"Injected {self.nodegroup_name} node group to materials in '{target_collection.name}'")
        else:
            self.report({'ERROR'}, f"Failed to inject {self.nodegroup_name} node group")
        
        return {'FINISHED'}




classes = (
    OBJECT_OT_ApplySmartPrimitives,
    OBJECT_OT_InjectNodegroupToCollection,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Add to modifier panel
    bpy.types.DATA_PT_modifiers.append(draw_inject_nodegroup_button)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    # Remove from modifier panel
    bpy.types.DATA_PT_modifiers.remove(draw_inject_nodegroup_button)
