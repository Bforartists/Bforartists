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

import logging
logger = logging.getLogger(__name__)


def set_geometry_nodes_input_value(modifier, input_key, value):
    """Set a geometry nodes modifier input value by key or fallback by input name."""
    # print(f"[GN DEBUG] set_geometry_nodes_input_value: modifier={getattr(modifier, 'name', repr(modifier))}, input_key={input_key}, value={value}")
    if not hasattr(modifier, 'properties'):
        # print("[GN DEBUG] modifier has no properties")
        return False

    if hasattr(modifier.properties, 'inputs'):
        inputs = modifier.properties.inputs
    else:
        # print("[GN DEBUG] modifier.properties has no inputs")
        return False

    # Try direct attribute access first (this is how Blender's own code works)
    try:
        input_obj = getattr(inputs, input_key)
        input_obj.value = value
        # print(f"[GN DEBUG] direct input assignment succeeded for {input_key}")
        return True
    except Exception as exc:
        # print(f"[GN DEBUG] direct input assignment failed for {input_key}: {exc}")
        pass

    # Fallback: try to find the input by iterating over available inputs
    try:
        # Get all available input identifiers/names
        input_names = []
        if hasattr(inputs, '__dict__'):
            input_names = [name for name in dir(inputs) if not name.startswith('_')]
        elif hasattr(inputs, 'keys'):
            input_names = list(inputs.keys())
        else:
            # print("[GN DEBUG] cannot determine available inputs")
            return False

        # print(f"[GN DEBUG] available inputs: {input_names}")

        for name in input_names:
            try:
                inp = getattr(inputs, name)
                if getattr(inp, 'identifier', None) == input_key or getattr(inp, 'name', None) == input_key:
                    inp.value = value
                    # print(f"[GN DEBUG] assignment succeeded by identifier/name match for {input_key} -> {name}")
                    return True
            except Exception as exc:
                # print(f"[GN DEBUG] assignment fallback failed for {input_key} on input {name}: {exc}")
                continue
    except Exception as exc:
        # print(f"[GN DEBUG] failed to iterate over inputs: {exc}")
        pass

    # Additional fallback: case-insensitive name match
    try:
        if hasattr(inputs, '__dict__'):
            for name in dir(inputs):
                if name.startswith('_'):
                    continue
                try:
                    inp = getattr(inputs, name)
                    if getattr(inp, 'name', '').lower() == str(input_key).lower():
                        inp.value = value
                        # print(f"[GN DEBUG] assignment succeeded by case-insensitive name match for {input_key} -> {name}")
                        return True
                except Exception as exc:
                    # print(f"[GN DEBUG] assignment name-match failed for {input_key} on input {name}: {exc}")
                    continue
    except Exception as exc:
        # print(f"[GN DEBUG] failed case-insensitive iteration: {exc}")
        pass

    # print(f"[GN DEBUG] no matching input found for {input_key}")
    return False


def set_geometry_nodes_input_value_version_aware(modifier, input_key, value):
    """
    Set a geometry nodes modifier input value with version-aware access patterns.
    
    This function adapts to different Blender versions:
    - Blender 5.0: Direct property access
    - Blender 5.1+: Interface-based access with panels support
    
    Args:
        modifier: The geometry nodes modifier
        input_key: The input identifier or name to set
        value: The value to set
    
    Returns:
        bool: True if successful, False otherwise
    """
    import bpy
    
    # Get version information
    try:
        version_info = bpy.app.version
        version_tuple = (version_info[0], version_info[1], version_info[2] if len(version_info) > 2 else 0)
    except:
        version_tuple = (5, 0, 0)  # Fallback
    
    # For Blender 5.1+ with interface panels support
    if version_tuple >= (5, 1, 0) and hasattr(modifier, 'node_group') and modifier.node_group:
        try:
            # Use interface inspection for modern Blender versions
            interface_items = modifier.node_group.interface.items_tree
            
            for item in interface_items:
                if item.item_type == 'SOCKET':
                    # Check if this socket matches our input_key
                    socket_identifier = getattr(item, 'identifier', None) or getattr(item, 'name', None)
                    
                    if socket_identifier == input_key or getattr(item, 'name', None) == input_key:
                        # Try to set via modifier properties
                        if hasattr(modifier, 'properties') and hasattr(modifier.properties, 'inputs'):
                            try:
                                # Direct access by identifier
                                input_obj = getattr(modifier.properties.inputs, socket_identifier, None)
                                if input_obj:
                                    input_obj.value = value
                                    # print(f"[GN DEBUG] Interface-based assignment succeeded for {input_key}")
                                    return True
                            except Exception as exc:
                                # print(f"[GN DEBUG] Interface-based assignment failed: {exc}")
                                pass
                        
                        # Fallback: try setting via item.default_value
                        try:
                            item.default_value = value
                            # print(f"[GN DEBUG] Item default_value assignment succeeded for {input_key}")
                            return True
                        except Exception as exc:
                            # print(f"[GN DEBUG] Item default_value assignment failed: {exc}")
                            pass
        except Exception as exc:
            # print(f"[GN DEBUG] Interface inspection failed: {exc}")
            pass
    
    # Fallback to the original method for all versions
    return set_geometry_nodes_input_value(modifier, input_key, value)


# Constants for assets with operators names
GN_ASSET_NAMES = [
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
    "Smart Tube Rounded Revolved",
    "Blend Normals by Proximity",
]

# -----------------------------------------------------------------------------
# Sidebar Panel Function
# -----------------------------------------------------------------------------

def _socket_exists_in_modifier(modifier, identifier, version):
    """Version-aware check if a socket identifier exists in a modifier.
    
    Blender 5.0-5.1: Direct ID property membership check via 'in' operator.
    Blender 5.2+: ID property 'in' operator raises TypeError, use properties.inputs instead.
    """
    if identifier is None:
        return False

    if version >= (5, 2, 0):
        # Blender 5.2+: modifier.__contains__ and modifier[key] dict access are both gone.
        # Use modifier.properties.inputs as the only reliable path.
        try:
            if hasattr(modifier, 'properties') and hasattr(modifier.properties, 'inputs'):
                _ = getattr(modifier.properties.inputs, identifier)
                return True
        except (AttributeError, TypeError):
            pass
        return False
    else:
        # Blender 5.0-5.1: direct dict membership check works
        try:
            return identifier in modifier
        except TypeError:
            return False


def get_geometry_nodes_inputs(modifier):
    """Returns socket names and types for Geometry Nodes modifier inputs, excluding 'Geometry'.
    Only works with Geometry Nodes modifiers - returns empty list for other modifier types."""
    # First check if this is actually a Geometry Nodes modifier
    if not hasattr(modifier, 'node_group') or modifier.type != 'NODES':
        return []

    # Then check if it has a node group
    if not modifier.node_group:
        return []
    
    version = bpy.app.version
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

            # Some modifier types do not support IDProperty membership checks.
            # Safely test membership and skip unsupported sockets.
            if item.identifier is None:
                continue

            # Version-aware socket existence check
            if not _socket_exists_in_modifier(modifier, item.identifier, version):
                continue

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

def is_gn_asset_object(obj):
    """Check if object has any smart primitive geometry nodes modifiers"""
    if not obj or not obj.modifiers:
        return False

    for mod in obj.modifiers:
        if (mod.type == 'NODES' and
            mod.node_group and
            any(mod.node_group.name.startswith(name) for name in GN_ASSET_NAMES)):
            return True
    return False

def get_all_gn_asset_objects(context):
    """Get all objects that are smart primitives in the current context"""
    return [obj for obj in context.selected_objects if is_gn_asset_object(obj)]


# -----------------------------------------------------------------------------
# Mesh Blend by Proximity Operators
# -----------------------------------------------------------------------------

def get_all_objects_from_collection(collection, include_children=True):
    """Get all objects from a collection, including nested collections if include_children is True"""
    objects = []
    
    # Add objects from current collection
    objects.extend(collection.objects)
    
    # If including nested collections, recursively add objects from child collections
    if include_children:
        for child_collection in collection.children:
            objects.extend(get_all_objects_from_collection(child_collection, include_children=True))
    
    return objects

# Intersection Nodegroup injection functions
def inject_nodegroup_to_collection(collection_name, nodegroup_name="S_Intersections"):
    """Inject a node group into all materials of objects in the target collection, including nested collections"""
    # print(f"[INJECT DEBUG] Starting injection for collection '{collection_name}', nodegroup '{nodegroup_name}'")
    target_collection = bpy.data.collections.get(collection_name)
    if not target_collection:
        # print(f"[INJECT DEBUG] Collection '{collection_name}' not found!")
        logger.error(f"Collection '{collection_name}' not found!")
        return False

    logger.info(f"Processing collection: {collection_name}")

    # Check if node group exists
    node_group = bpy.data.node_groups.get(nodegroup_name)
    if not node_group:
        # print(f"[INJECT DEBUG] Node group '{nodegroup_name}' not found!")
        logger.error(f"Node group '{nodegroup_name}' not found!")
        return False

    # print(f"[INJECT DEBUG] Found node group '{nodegroup_name}', processing {len(get_all_objects_from_collection(target_collection, include_children=True))} objects")

    processed_objects = 0
    objects_with_materials = 0
    materials_processed = 0
    materials_skipped = 0

    # Get all objects from the collection, including nested collections
    all_objects = get_all_objects_from_collection(target_collection, include_children=True)

    # Process each object in the collection and its nested collections
    for obj in all_objects:
        if obj.type not in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}:
            continue

        processed_objects += 1

        # Check if object has materials or material slots
        if not obj.material_slots:
            logger.info(f"  No materials found for {obj.name}, adding default material")

            # Create a new material
            default_mat = bpy.data.materials.new(name=f"{obj.name}_DefaultMaterial")

            # Add material slot to object
            obj.data.materials.append(default_mat)

            # Process the new material (new materials won't have the node group yet)
            if inject_nodegroup_to_material(default_mat, node_group):
                materials_processed += 1
            objects_with_materials += 1

        else:
            objects_with_materials += 1
            # Process all materials of the object
            for material_slot in obj.material_slots:
                if material_slot.material:
                    # Check if material already has the node group
                    if has_nodegroup_in_material(material_slot.material, nodegroup_name):
                        logger.info(f"  Material {material_slot.material.name} already has {nodegroup_name}, skipping")
                        materials_skipped += 1
                        continue
                    
                    # Inject node group if it doesn't exist
                    if inject_nodegroup_to_material(material_slot.material, node_group):
                        materials_processed += 1
                else:
                    # Empty material slot found, create and assign default material
                    logger.info(f"  Empty material slot found for {obj.name}, adding default material")
                    default_mat = bpy.data.materials.new(name=f"{obj.name}_DefaultMaterial")
                    material_slot.material = default_mat
                    # Process the new material
                    if inject_nodegroup_to_material(default_mat, node_group):
                        materials_processed += 1

    logger.info(f"Processed {processed_objects} objects, {objects_with_materials} had materials")
    logger.info(f"Injected node group into {materials_processed} materials, skipped {materials_skipped} duplicates")
    return materials_processed > 0 or materials_skipped > 0

def inject_nodegroup_to_material(material, node_group):
    """Inject node group into a material's node tree to blend"""
    
    # First check if this material already has the node group
    if has_nodegroup_in_material(material, node_group.name):
        logger.info(f"  Material {material.name} already has {node_group.name}, skipping injection")
        return False

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

def has_nodegroup_in_material(material, nodegroup_name):
    """Check if material already has the specified node group"""
    for node in material.node_tree.nodes:
        if (node.type == 'GROUP' and
            node.node_tree and
            node.node_tree.name == nodegroup_name):
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

        # Inject node group to collection (with duplicate checking built into the function)
        success = inject_nodegroup_to_collection(target_collection.name, self.nodegroup_name)

        if success:
            self.report({'INFO'}, f"Injected {self.nodegroup_name} node group to materials in '{target_collection.name}'")
        else:
            self.report({'ERROR'}, f"Failed to inject {self.nodegroup_name} node group")

        return {'FINISHED'}



class OBJECT_OT_RemoveNodegroupFromCollection(Operator):
    """Remove node group from all materials in target collection, including nested collections"""
    bl_idname = "object.remove_nodegroup_from_collection"
    bl_label = "Remove Node Group from Materials"
    bl_description = "Remove S_Intersections node group from materials of objects in target collection"
    bl_options = {'REGISTER', 'UNDO'}

    nodegroup_name: bpy.props.StringProperty(
        name="Node Group",
        description="Name of the node group to remove",
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

        # Remove node group from collection
        success = remove_nodegroup_from_collection(target_collection.name, self.nodegroup_name)

        if success:
            self.report({'INFO'}, f"Removed {self.nodegroup_name} node group from materials in '{target_collection.name}'")
        else:
            self.report({'ERROR'}, f"Failed to remove {self.nodegroup_name} node group")

        return {'FINISHED'}


def remove_nodegroup_from_collection(collection_name, nodegroup_name="S_Intersections"):
    """Remove a node group from all materials of objects in the target collection, including nested collections"""
    target_collection = bpy.data.collections.get(collection_name)
    if not target_collection:
        logger.error(f"Collection '{collection_name}' not found!")
        return False

    logger.info(f"Processing collection: {collection_name}")

    processed_objects = 0
    materials_processed = 0

    # Get all objects from the collection, including nested collections
    all_objects = get_all_objects_from_collection(target_collection, include_children=True)

    # Process each object in the collection and its nested collections
    for obj in all_objects:
        if obj.type not in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}:
            continue

        processed_objects += 1

        # Process all materials of the object
        for material_slot in obj.material_slots:
            if material_slot.material:
                if remove_nodegroup_from_material(material_slot.material, nodegroup_name):
                    materials_processed += 1

    logger.info(f"Processed {processed_objects} objects, removed node group from {materials_processed} materials")
    return materials_processed > 0


def remove_nodegroup_from_material(material, nodegroup_name):
    """Remove node group from a material's node tree and restore original connections"""
    if not material:
        logger.warning(f"Material {material.name} doesn't use nodes or has no node tree")
        return False

    nodes = material.node_tree.nodes
    links = material.node_tree.links

    # Find all node group instances to remove
    nodes_to_remove = []
    for node in nodes:
        if (node.type == 'GROUP' and  # Use single string comparison
            getattr(node, 'node_tree', None) and
            node.node_tree.name == nodegroup_name):
            nodes_to_remove.append(node)

    if not nodes_to_remove:
        logger.info(f"No {nodegroup_name} nodes found in {material.name}")
        return False

    removed_count = 0

    for node in nodes_to_remove:
        # Find the input and output connections
        input_socket = None
        output_socket = None
        input_connection = None
        output_connection = None
        
        # Find shader input socket (usually the first shader input)
        for socket in node.inputs:
            if socket.type == 'SHADER' and socket.is_linked:
                input_connection = socket.links[0].from_socket
                input_socket = socket
                break
        
        # Find shader output socket and its connection
        for socket in node.outputs:
            if socket.type == 'SHADER' and socket.is_linked:
                for link in socket.links:
                    output_connection = link.to_socket
                    output_socket = socket
                    break
                if output_connection:
                    break
        
        # Remove all links to and from this node
        for socket in node.inputs:
            for link in socket.links:
                links.remove(link)

        for socket in node.outputs:
            for link in socket.links:
                links.remove(link)

        # Remove the node
        nodes.remove(node)
        removed_count += 1
        
        # Reconnect original input to output if both connections exist
        if input_connection and output_connection:
            try:
                links.new(input_connection, output_connection)
                logger.info(f"  Restored shader connection in {material.name}")
            except Exception as e:
                logger.warning(f"  Could not restore connection in {material.name}: {e}")

        # If we removed the node but have no output connection, check if we need to add a default shader
        elif input_connection and not output_connection:
            # Find the material output node
            output_node = None
            for n in nodes:
                if n.type == 'OUTPUT_MATERIAL' and n.is_active_output:
                    output_node = n
                    break

            if output_node and output_node.inputs.get("Surface"):
                try:
                    links.new(input_connection, output_node.inputs["Surface"])
                    logger.info(f"  Reconnected shader to output in {material.name}")
                except Exception as e:
                    logger.warning(f"  Could not reconnect to output in {material.name}: {e}")

    logger.info(f"  Removed {removed_count} {nodegroup_name} node(s) from {material.name}")
    return removed_count > 0



class OBJECT_OT_MeshBlendbyProximity(Operator):
    """Apply Mesh Blend by Proximity configuration with target collection settings"""
    bl_idname = "object.meshblendbyproximity"
    bl_label = "Mesh Blend by Proximity"
    bl_description = "Configure the Mesh Blend by Proximity geometry nodes setup with target collection"
    bl_options = {'REGISTER', 'UNDO'}

    # Note: Cannot use PointerProperty for collections on operators
    # Using scene properties instead

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
        # Use scene properties directly (operator properties don't support data-block types)
        target_collection = context.scene.target_collection
        use_wireframe_on_collection = context.scene.use_wireframe_on_collection
        use_relative_position = context.scene.use_relative_position
        inject_intersection_nodegroup = context.scene.inject_intersection_nodegroup

        # Validate target collection exists
        if not target_collection:
            self.report({'ERROR'}, "No target collection selected. Please select a target collection first.")
            return {'CANCELLED'}

        # Set viewport settings to bounds for all children objects if enabled
        if use_wireframe_on_collection:
            for collection_obj in target_collection.objects:
                if collection_obj.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}:
                    collection_obj.show_bounds = True
                    collection_obj.display_type = 'BOUNDS'
        else:
            # Disable bounds
            for collection_obj in target_collection.objects:
                if collection_obj.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}:
                    collection_obj.show_bounds = False
                    collection_obj.display_type = 'TEXTURED'

        # Apply geometry nodes configuration
        # Use the object from the beginning of execute(), not a possibly different active object
        # that may change during modal/UI context handling.

        # Find the Blend Normals by Proximity modifier
        geom_nodes = None
        for mod in obj.modifiers:
            if (mod.type == 'NODES' and
                mod.node_group and
                "Blend Normals by Proximity" in mod.node_group.name):
                geom_nodes = mod
                break

        if geom_nodes and geom_nodes.node_group:
            # print(f"[GN DEBUG] applying settings to Geometry Nodes modifier: {geom_nodes.name}")
            # print(f"[GN DEBUG] using scene properties: target_collection={target_collection}, use_relative_position={use_relative_position}, use_wireframe_on_collection={use_wireframe_on_collection}, inject_intersection_nodegroup={inject_intersection_nodegroup}")
            # Find collection socket in the node group interface and set its modifier input value
            collection_socket_found = False

            for item in geom_nodes.node_group.interface.items_tree:
                if item.item_type == 'SOCKET' and item.socket_type == 'NodeSocketCollection':
                    # print(f"[GN DEBUG] found collection socket item name={item.name}, identifier={item.identifier}")
                    if target_collection:
                        input_key = item.identifier or item.name
                        success = set_geometry_nodes_input_value_version_aware(geom_nodes, input_key, target_collection)
                        # print(f"[GN DEBUG] set collection input {input_key} success={success}")
                        try:
                            item.default_value = target_collection
                        except Exception as exc:
                            # print(f"[GN DEBUG] failed to write item.default_value for collection socket: {exc}")
                            pass
                        collection_socket_found = True
                    break

            # Set relative position if enabled
            for item in geom_nodes.node_group.interface.items_tree:
                if item.item_type == 'SOCKET' and item.socket_type == 'NodeSocketBool':
                    if item.name.lower().startswith(('socket_12', 'relative', 'position')):
                        # print(f"[GN DEBUG] found bool socket item name={item.name}, identifier={item.identifier}")
                        input_key = item.identifier or item.name
                        success = set_geometry_nodes_input_value_version_aware(geom_nodes, input_key, use_relative_position)
                        # print(f"[GN DEBUG] set bool input {input_key} success={success}")
                        try:
                            item.default_value = use_relative_position
                        except Exception as exc:
                            # print(f"[GN DEBUG] failed to write item.default_value for bool socket: {exc}")
                            pass
                        break

            # Inject intersection nodegroup if enabled
            if target_collection:
                if inject_intersection_nodegroup:
                    # print(f"[GN DEBUG] injecting intersection nodegroup to collection {target_collection.name}")
                    success = inject_nodegroup_to_collection(target_collection.name)
                    # print(f"[GN DEBUG] injection success: {success}")
                else:
                    # print(f"[GN DEBUG] removing intersection nodegroup from collection {target_collection.name}")
                    success = remove_nodegroup_from_collection(target_collection.name)
                    # print(f"[GN DEBUG] removal success: {success}")
                    # DEBUG
                    #if success:
                    #    self.report({'INFO'}, "Intersection node group injected into materials to blend them")
            else:
                self.report({'WARNING'}, "No target collection selected - skipping material injection")

            # Force update
            obj.update_tag()
            context.view_layer.update()

            # DEBUG
            #if collection_socket_found:
            #    self.report({'INFO'}, "Target Collection successfully assigned to the Geometry Nodes setup")
            #else:
            #    self.report({'WARNING'}, "Collection input not found in Geometry Nodes setup")

        else:
            self.report({'ERROR'}, "Blend Normals by Proximity geometry nodes setup not found")

        return {'FINISHED'}


classes = (
    OBJECT_OT_InjectNodegroupToCollection,
    OBJECT_OT_RemoveNodegroupFromCollection,
    OBJECT_OT_MeshBlendbyProximity,
)

def register():
    """Register geometry nodes operator classes."""
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError as e:
            if "already registered" not in str(e):
                print(f"⚠ Error registering {cls.__name__}: {e}")


def unregister():
    """Unregister geometry nodes operator classes."""
    for cls in reversed(classes):
        try:
            if hasattr(cls, 'bl_rna'):
                bpy.utils.unregister_class(cls)
        except RuntimeError as e:
            if "not registered" not in str(e):
                print(f"⚠ Error unregistering {cls.__name__}: {e}")