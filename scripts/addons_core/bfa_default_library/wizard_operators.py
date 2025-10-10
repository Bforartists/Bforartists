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

# Asset names for wizard recognition
BLEND_NORMALS_BY_PROXIMITY = "Blend Normals by Proximity"


# -----------------------------------------------------------------------------#
# Wizards                                                                      #
# -----------------------------------------------------------------------------#

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
                    # Look for relative position socket
                    for socket_name in geom_nodes.keys():
                        if "relative" in socket_name.lower() or "position" in socket_name.lower():
                            geom_nodes[socket_name] = True

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
