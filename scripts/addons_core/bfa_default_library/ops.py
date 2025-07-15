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
# ! IMPORTANT! READ THIS WHEN SETTING UP THE LIBRARY
# This is a work in progress, and many assets, categories, thumbnails and more are subject to change.
# Use at own risk. 
# -----------------------------------------------------------------------------

import bpy


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



class OBJECT_OT_ApplySmartPrimitives(bpy.types.Operator):
    """Applies selected smart primitives, converts to mesh, joins them, and optionally remeshes"""
    bl_idname = "object.apply_smart_primitives"
    bl_label = "Apply Smart Primitives"
    bl_options = {'REGISTER', 'UNDO'}

    remesh: bpy.props.BoolProperty(
        name="Remesh",
        description="Apply quad remesh to the final mesh",
        default=False
    )

    boolean: bpy.props.BoolProperty(
        name="Boolean",
        description="Apply boolean operation to combine the primitives",
        default=False
    )

    @classmethod
    def poll(cls, context):
        """Only enable if there are selected objects with smart primitive modifiers"""
        if not context.selected_objects:
            return False
            
        for obj in context.selected_objects:
            if obj.modifiers:
                for mod in obj.modifiers:
                    if (mod.type == 'NODES' and 
                        mod.node_group and 
                        any(mod.node_group.name.startswith(name) for name in OBJECT_PT_GeometryNodesPanel.smart_primitive_names)):
                        return True
        return False
    
    def execute(self, context):
        # Store original active object and selection
        original_active = context.view_layer.objects.active
        original_selected = set(context.selected_objects)
        
        # List to track objects we need to delete after conversion
        objects_to_delete = []
        new_objects = []
        
        try:
            # First pass: Collect all objects with smart primitives and mesh objects
            smart_objects = []
            for obj in context.selected_objects:
                # Add mesh objects
                if obj.type == 'MESH':
                    smart_objects.append(obj)
                    continue
                
                # Add objects with smart primitive modifiers
                if obj.modifiers:
                    for mod in obj.modifiers:
                        if (mod.type == 'NODES' and 
                            mod.node_group and 
                            mod.node_group.name in OBJECT_PT_GeometryNodesPanel.smart_primitive_names):
                            smart_objects.append(obj)
                            break
            
            if not smart_objects:
                self.report({'WARNING'}, "No valid objects found to process")
                return {'CANCELLED'}
            
            # Convert all smart objects to mesh in one operation
            bpy.ops.object.select_all(action='DESELECT')
            for obj in smart_objects:
                obj.select_set(True)
                objects_to_delete.append(obj)
            
            context.view_layer.objects.active = smart_objects[0]
            bpy.ops.object.visual_geometry_to_objects()
            
            # Get newly created objects
            current_selected = set(context.selected_objects)
            new_objects = [obj for obj in current_selected if obj not in original_selected]
            
            # Join all new objects
            if new_objects:                               
                # Apply boolean operation if enabled
                if self.boolean and new_objects:
                    # Start with the first object as our base
                    base_object = new_objects[0]
                    base_object.select_set(True)
                    context.view_layer.objects.active = base_object

                    # Store the other objects to delete them later
                    objects_to_bool = new_objects[1:]
                    objects_to_delete.extend(objects_to_bool)  # Add these to our cleanup list

                    # Iterate through remaining objects
                    for obj in objects_to_bool:
                        # Verify object still exists before processing
                        if obj and obj.name in context.scene.objects:
                            # Add boolean modifier to base object
                            bool_mod = base_object.modifiers.new(name="Boolean", type='BOOLEAN')
                            bool_mod.operation = 'UNION'
                            bool_mod.solver = 'FLOAT'  # Using FLOAT solver for better performance
                            bool_mod.object = obj
                            
                            # Apply the modifier
                            try:
                                bpy.ops.object.modifier_apply(modifier=bool_mod.name)
                            except RuntimeError as e:
                                print(f"Boolean operation failed on {obj.name}: {str(e)}")
                                continue
                            
                            # Update the scene to ensure proper selection
                            context.view_layer.update()
                            
                            # Select only the base object
                            bpy.ops.object.select_all(action='DESELECT')
                            base_object.select_set(True)
                            context.view_layer.objects.active = base_object
                            
                            bpy.ops.object.shade_auto_smooth()
                    
                    # Update final_object reference
                    final_object = base_object
            
                else:
                    # Simple join operation if boolean is disabled
                    if context.scene.join_apply:
                        context.view_layer.objects.active = new_objects[0]
                        for obj in new_objects:
                            obj.select_set(True)
                        bpy.ops.object.join()
                        
                        # Get the final joined object
                        final_object = context.view_layer.objects.active
                    else:
                        # If join is disabled, just use the first object
                        final_object = new_objects[0]
                    
                   
            # Clean up original objects
            bpy.ops.object.select_all(action='DESELECT')
            for obj in objects_to_delete:
                if obj and obj.name in context.scene.objects:
                    obj.select_set(True)
            bpy.ops.object.delete()
                                   
            # Select the final object and make it active
            if final_object and final_object.name in context.scene.objects:
                bpy.ops.object.select_all(action='DESELECT')
                final_object.select_set(True)
                context.view_layer.objects.active = final_object
    
                # Enter edit mode, select all, clear sharp edges, and return to object mode
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.mark_sharp(clear=True)
                bpy.ops.object.mode_set(mode='OBJECT')
            
            self.report({'INFO'}, f"Successfully applied {len(smart_objects)} primitives")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error during operation: {str(e)}")
            # Try to restore original state
            if original_active and original_active.name in context.scene.objects:
                context.view_layer.objects.active = original_active
            return {'CANCELLED'}


class OBJECT_PT_GeometryNodesPanel(bpy.types.Panel):
    """Panel in the sidebar for editing Geometry Nodes properties."""
    bl_idname = "OBJECT_PT_geometry_nodes_panel"
    bl_label = "Primitive Properties"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Item"

    show_panel = True  # Controls whether the panel should be shown

    smart_primitive_names = [
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
    ]
    
    
    @classmethod
    def poll(cls, context):
        """Only show panel for objects with Geometry Nodes modifiers from our smart primitives list."""
        if not cls.show_panel or not context.object or not context.object.modifiers:
            return False
            
        # Check if any modifier is a Geometry Nodes modifier with a node group whose name starts with our smart primitive names
        for mod in context.object.modifiers:
            if (mod.type == 'NODES' and 
                mod.node_group and 
                any(mod.node_group.name.startswith(name) for name in cls.smart_primitive_names)):
                return True
        return False

    def draw(self, context):
        layout = self.layout
        obj = context.object
        
        # Find the first Geometry Nodes modifier that matches our primitive names
        mod = next((m for m in obj.modifiers 
                   if m.type == 'NODES' and 
                   m.node_group and 
                   m.node_group.name in self.smart_primitive_names), None)

        if mod and mod.node_group:
            # Main panel header
            layout.label(text=f"{mod.node_group.name}", icon='NODETREE')
            
            # Get and display all inputs
            inputs = get_geometry_nodes_inputs(mod)
            
            # Track current panel to group sockets together
            current_panel = None
            panel_box = None
            
            for socket_name, socket_id, socket_type, parent_panel in inputs:
                # If we've moved to a new panel, create a new box
                if parent_panel != current_panel:
                    if panel_box:  # Close previous panel if it exists
                        panel_box.separator()
                    current_panel = parent_panel
                    if current_panel:
                        panel_box = layout.box()
                        panel_box.label(text=current_panel, icon='NODE')
                
                # If we're in a panel, use the panel_box layout
                target_layout = panel_box if current_panel else layout
                
                # Create a row for each input to ensure proper layout
                row = target_layout.row()
                
                # Handle different socket types
                if socket_type == 'BOOLEAN':
                    row.prop(mod, f'["{socket_id}"]', text=socket_name, toggle=True)
                elif socket_type == 'VALUE':
                    # Split row into label and slider
                    row.label(text=socket_name)
                    row.prop(mod, f'["{socket_id}"]', text="", slider=False)
                else:
                    row.prop(mod, f'["{socket_id}"]', text=socket_name)

            # Add the apply button with proper spacing
            layout.separator()
            row = layout.row()
            row.scale_y =  1.5 # Make the button larger
            op = row.operator("object.apply_smart_primitives", text="Apply Selected Primitives", icon='CHECKMARK')
            op.remesh = context.scene.join_apply
            op.boolean = context.scene.boolean_apply

            # Add a toggle button for the remesh property
            row = layout.row()
            row.prop(context.scene, "join_apply", text="Join on Apply")

            # Add a toggle button for the boolean property
            row = layout.row()
            row.prop(context.scene, "boolean_apply", text="Boolean on Apply")


##### Modifiers Panel Operators ####

class OBJECT_PT_SmartPrimitiveModifierPanel(bpy.types.Panel):
    """Creates a custom panel in the Modifier properties for Smart Primitives"""
    bl_label = "Smart Primitive Operators"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "modifier"
    bl_parent_id = 'DATA_PT_modifiers'

    @classmethod
    def poll(cls, context):
        # Show panel if any Smart Primitive modifier exists in the stack
        if context.object and context.object.modifiers:
            # Check all modifiers in the stack
            for mod in context.object.modifiers:
                if (mod.type == 'NODES' and
                    mod.node_group and
                    mod.node_group.name in OBJECT_PT_GeometryNodesPanel.smart_primitive_names):
                    return True
        return False

    def draw(self, context):
        layout = self.layout
        obj = context.object
        mod = obj.modifiers.active
        
        # Get and display all inputs
        inputs = get_geometry_nodes_inputs(mod)
        
        # Add the apply button with proper spacing
        layout.separator()
        row = layout.row()
        row.scale_y = 1.5 # Make the button larger
        op = row.operator("object.apply_smart_primitives", text="Apply Selected Primitives", icon='CHECKMARK')
        op.remesh = context.scene.join_apply
        op.boolean = context.scene.boolean_apply

        # Add a toggle button for the remesh property
        row = layout.row()
        row.prop(context.scene, "join_apply", text="Join on Apply")

        # Add a toggle button for the boolean property
        row = layout.row()
        row.prop(context.scene, "boolean_apply", text="Boolean on Apply")


def object_added_handler(scene):
    """Activates the panel when an object with Geometry Nodes is added to the scene."""
    for obj in scene.objects:
        if obj not in object_added_handler.known_objects:
            # Only activate panel for our specific primitives
            mod = next((m for m in obj.modifiers 
                       if m.type == 'NODES' and 
                       m.node_group and 
                       m.node_group.name in OBJECT_PT_GeometryNodesPanel.smart_primitive_names), None)
            if mod:
                OBJECT_PT_GeometryNodesPanel.show_panel = True
            object_added_handler.known_objects.add(obj)

object_added_handler.known_objects = set()


##### Register #####

def register():
    # Register the bool property first
    bpy.types.Scene.join_apply = bpy.props.BoolProperty(
        name="Join",
        description="Apply quad remesh to the final mesh",
        default=False
    )
    
    # Register the bool property first
    bpy.types.Scene.boolean_apply = bpy.props.BoolProperty(
        name="Boolean",
        description="Apply boolean to the final mesh",
        default=False
    )
    
    # Then register the classes and handler
    bpy.utils.register_class(OBJECT_PT_GeometryNodesPanel)
    bpy.utils.register_class(OBJECT_OT_ApplySmartPrimitives)
    bpy.utils.register_class(OBJECT_PT_SmartPrimitiveModifierPanel)

    # Add handler only if it's not already there
    if object_added_handler not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(object_added_handler)

def unregister():
    # Unregister in reverse order
    bpy.utils.unregister_class(OBJECT_PT_GeometryNodesPanel)
    bpy.utils.unregister_class(OBJECT_OT_ApplySmartPrimitives)
    bpy.utils.unregister_class(OBJECT_PT_SmartPrimitiveModifierPanel)
    
    # Remove handler if it exists
    if object_added_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(object_added_handler)

    # Finally, remove the property
    del bpy.types.Scene.join_apply
    del bpy.types.Scene.boolean_apply

if __name__ == "__main__":
    register()
