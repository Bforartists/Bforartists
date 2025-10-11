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
# Wizard Operators
# Contains all wizard operator classes for different asset types
# These are used to popup user input wizards and run scripts after
# an asset has been added
# -----------------------------------------------------------------------------

import bpy
from bpy.types import Operator
import logging

# Set up logging
logger = logging.getLogger(__name__)


# Asset names for wizard recognition
BLEND_NORMALS_BY_PROXIMITY = "Blend Normals by Proximity"


# -----------------------------------------------------------------------------#
# Wizards                                                                      #
# - These are drawn by using functions "def" that get called into an operator
# The operator then opens a panel that a user can confirm and customize
# This helps the user quickly get started, and dependencies scripts can run
# -----------------------------------------------------------------------------#


# -----------------------------------------------------------------------------#
# Mesh Blend by Proximity                                                      #
# -----------------------------------------------------------------------------#

# Nodegroup injection functions
def inject_nodegroup_to_collection(collection_name, nodegroup_name="S_Intersections"):
    """Inject a node group into all materials of objects in the target collection"""
    target_collection = bpy.data.collections.get(collection_name)
    if not target_collection:
        logger.error(f"Collection '{collection_name}' not found!")
        return False
    
    logger.info(f"Processing collection: {collection_name}")

    # Check if node group exists
    node_group = bpy.data.node_groups.get(nodegroup_name)
    if not node_group:
        logger.error(f"Node group '{nodegroup_name}' not found!")
        return False

    processed_objects = 0
    objects_with_materials = 0

    # Process each object in the collection
    for obj in target_collection.objects:
        if obj.type not in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}:
            continue
        
        processed_objects += 1

        # Check if object has materials or material slots
        if not obj.material_slots:
            logger.info(f"  No materials found for {obj.name}, adding default material")
            
            # Create a new material
            default_mat = bpy.data.materials.new(name=f"{obj.name}_DefaultMaterial")
            default_mat.use_nodes = True
            
            # Add material slot to object
            obj.data.materials.append(default_mat)
            
            # Process the new material
            inject_nodegroup_to_material(default_mat, node_group)
            objects_with_materials += 1

        else:
            objects_with_materials += 1
            # Process all materials of the object
            for material_slot in obj.material_slots:
                if material_slot.material:
                    inject_nodegroup_to_material(material_slot.material, node_group)
                else:
                    # Empty material slot found, create and assign default material
                    logger.info(f"  Empty material slot found for {obj.name}, adding default material")
                    default_mat = bpy.data.materials.new(name=f"{obj.name}_DefaultMaterial")
                    default_mat.use_nodes = True
                    material_slot.material = default_mat
                    # Process the new material
                    inject_nodegroup_to_material(default_mat, node_group)

    logger.info(f"Processed {processed_objects} objects, {objects_with_materials} had materials")
    return True

def inject_nodegroup_to_material(material, node_group):
    """Inject node group into a material's node tree"""

    nodes = material.node_tree.nodes
    links = material.node_tree.links

    # Find the output node
    output_node = None
    for node in nodes:
        if node.type == 'OUTPUT_MATERIAL' and node.is_active_output:
            output_node = node
            break

    if not output_node:
        logger.warning(f"  No active material output node found in {material.name}")
        return False

    # Find the surface input socket
    surface_input = output_node.inputs.get("Surface")
    if not surface_input:
        logger.warning(f"  No Surface input found in output node of {material.name}")
        return False

    # Check if surface input is connected
    if not surface_input.is_linked:
        # Add a basic principled BSDF shader
        bsdf_node = nodes.new(type='ShaderNodeBsdfPrincipled')
        bsdf_node.location = (output_node.location.x - 300, output_node.location.y)

        # Connect to output
        links.new(bsdf_node.outputs["BSDF"], surface_input)

        # Now inject the node group
        return inject_nodegroup_before_output(material, node_group, bsdf_node.outputs["BSDF"])

    # Get the connected shader
    connected_shader = surface_input.links[0].from_socket

    # Inject node group between shader and output
    return inject_nodegroup_before_output(material, node_group, connected_shader)

def inject_nodegroup_before_output(material, node_group, input_socket):
    """Inject node group between the input socket and the output node"""
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    # Create the node group instance
    group_node = nodes.new(type='ShaderNodeGroup')
    group_node.node_tree = node_group
    group_node.name = f"{node_group.name}_Instance"
    group_node.label = node_group.name

    # Position the node group
    output_node = None
    for node in nodes:
        if node.type == 'OUTPUT_MATERIAL' and node.is_active_output:
            output_node = node
            break

    if output_node:
        group_node.location = (output_node.location.x - 200, output_node.location.y)

    # Find appropriate input/output sockets in the node group
    group_input = None
    group_output = None

    for socket in group_node.outputs:
        if socket.type == 'SHADER':
            group_output = socket
            break

    for socket in group_node.inputs:
        if socket.type == 'SHADER':
            group_input = socket
            break

    if not group_input or not group_output:
        logger.warning(f"  Node group {node_group.name} doesn't have appropriate shader inputs/outputs")
        nodes.remove(group_node)
        return False

    # Disconnect the original link
    for link in links:
        if link.to_socket == output_node.inputs["Surface"]:
            links.remove(link)
            break

    # Create new connections
    try:
        # Connect input to node group
        links.new(input_socket, group_input)

        # Connect node group to output
        links.new(group_output, output_node.inputs["Surface"])

        logger.info(f"  Successfully injected {node_group.name} into {material.name}")
        return True

    except Exception as e:
        logger.error(f"  Failed to connect node group: {e}")
        nodes.remove(group_node)
        return False

class WIZARD_OT_BlendNormalsByProximity(Operator):
    """Wizard to configure Blend Normals by Proximity geometry nodes setup"""
    bl_idname = "wizard.blend_normals_by_proximity"
    bl_label = BLEND_NORMALS_BY_PROXIMITY
    bl_description = "Configure the Blend Normals by Proximity geometry nodes setup"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """Available when there's an active object with geometry nodes"""
        return (context.object and
                context.object.modifiers and
                any(mod.type == 'NODES' for mod in context.object.modifiers))

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout

        # Collection selection panel
        row = layout.row()
        row.label(text="Select an existing collection of mesh objects to apply", icon='INFO')
        
        row = layout.row()
        row.prop_search(context.scene, "target_collection", bpy.data, "collections", text="Target Collection")

        row = layout.row()
        row.prop(context.scene, "inject_intersection_nodegroup", text="Blend Materials")

        row = layout.row()
        row.prop(context.scene, "use_relative_position", text="Use Relative Position")

        row = layout.row()
        row.prop(context.scene, "use_wireframe_on_collection", text="Enable Bounds Display")

    def execute(self, context):
        try:
            # Set viewport settings to bounds for all children objects if enabled
            if context.scene.target_collection and context.scene.use_wireframe_on_collection:
                for obj in context.scene.target_collection.objects:
                    if obj.type == 'MESH':
                        obj.display_type = 'BOUNDS'

            # Apply geometry nodes configuration
            obj = context.active_object
            geom_nodes = obj.modifiers.get(BLEND_NORMALS_BY_PROXIMITY)

            if geom_nodes and geom_nodes.node_group and geom_nodes.node_group.name.startswith(BLEND_NORMALS_BY_PROXIMITY):
                # Find collection socket in the node group
                collection_socket_found = False

                for node in geom_nodes.node_group.nodes:
                    if node.type == 'GROUP_INPUT':
                        for output in node.outputs:
                            if output.type == 'COLLECTION':
                                # Set the collection in the modifier
                                geom_nodes[output.identifier] = context.scene.target_collection
                                output.default_value = context.scene.target_collection
                                collection_socket_found = True
                                break
                        if collection_socket_found:
                            break

                # Set relative position if enabled
                if context.scene.use_relative_position:
                    # Set socket_12 to True for relative position
                    geom_nodes["Socket_12"] = True

                # Inject intersection nodegroup if enabled
                if (context.scene.inject_intersection_nodegroup and
                    context.scene.target_collection):
                    success = inject_nodegroup_to_collection(context.scene.target_collection.name)
                    if success:
                        self.report({'INFO'}, "Intersection node group injected into materials to blend them")

                # Force update
                obj.update_tag()
                context.view_layer.update()

                if collection_socket_found:
                    self.report({'INFO'}, "Target Collection successfully assigned to the Geometry Nodes setup")
                else:
                    self.report({'WARNING'}, "Collection input not found in Geometry Nodes setup")

            else:
                self.report({'ERROR'}, "Blend Normals by Proximity geometry nodes setup not found")

            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"An error occurred: {str(e)}")
            return {'CANCELLED'}

# -----------------------------------------------------------------------------#



# Add new wizard operators here following the same pattern
# Example:
# class WIZARD_OT_YourNewWizard(Operator):
#     bl_idname = "wizard.your_new_wizard"
#     bl_label = "Your New Wizard"
#     ...


# List of all wizard operator classes
classes = (
    WIZARD_OT_BlendNormalsByProximity,
)

def register():
    """Register all wizard operators"""
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    """Unregister all wizard operators"""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
