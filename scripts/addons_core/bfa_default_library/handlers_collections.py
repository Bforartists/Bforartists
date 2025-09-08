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
# Setups up handlers for dragging in collections to run wizards and scripts after appending.
# -----------------------------------------------------------------------------

import bpy
from bpy.app.handlers import persistent

bpy.types.Scene.target_collection = bpy.props.PointerProperty(type=bpy.types.Collection)
bpy.types.Scene.use_wireframe_on_collection = bpy.props.BoolProperty(
    name="Use Wireframe",
    description="Enable Wireframe Display on the Target Collection",
    default=False
)

bpy.types.Scene.use_relative_position = bpy.props.BoolProperty(
    name="Use Relative Position",
    description="Enable Relative Position of the new Blended mesh",
    default=False
)


global added_collection

#### Asset List ####
global col_blend_normals_by_proximity

#### Asset Names ####
col_blend_normals_by_proximity = "Blend Normals by Proximity"


# -----------------------------------------------------------------------------#
# Persistent Handling                                                          #
# -----------------------------------------------------------------------------#
# Object that will store the handle to the msgbus subscription
subscription_owner = object()

def notify_callback(*args):
    """Callback function for msgbus notifications"""
    print("Collection Asset added to scene")

def subscribe_collection_handlers(subscription_owner):
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.Collection, "name"),
        owner=subscription_owner,
        args=("collection_added",),
        notify=notify_callback,  # Add the callback function
        options={"PERSISTENT"}
    )
    
    if load_handler not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(load_handler)

def unsubscribe_collection_handlers(subscription_owner):
    if subscription_owner is not None:
        bpy.msgbus.clear_by_owner(subscription_owner)
    
    if load_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_handler)

@persistent
def load_handler(dummy):
    subscribe_collection_handlers(subscription_owner)


# -----------------------------------------------------------------------------#
# Handlers                                                                     #
# -----------------------------------------------------------------------------#
# Pre-handler to log existing collections before import to detect what was recently added
@persistent
def pre_collection_asset_added_handler(scene):
    """Logs existing collections before import"""
    pre_collection_asset_added_handler.known_collections = set(bpy.data.collections)
    #print(f"Pre-handler: Known collections initialized: {pre_collection_asset_added_handler.known_collections}")  # DEBUG


# Detect if the new collection was added to scene to invoke the menu.
@persistent
def collection_asset_added_handler(scene):
    """Activates a confirmation dialogue for the newest collection"""
    if not hasattr(pre_collection_asset_added_handler, 'known_collections'):
        #print("Handler: No known collections found, skipping")  # DEBUG
        return

    # Define the asset collections base name
    collection_base_name = col_blend_normals_by_proximity

    # Get current collections and find the differences
    all_collections = set(bpy.data.collections)
    new_collections = all_collections - pre_collection_asset_added_handler.known_collections
    #print(f"Handler: New collections detected: {new_collections}")  # DEBUG

    # Find the specific collection we're looking for
    new_collection = None
    for collection in new_collections:
        if collection_base_name in collection.name:  # Changed to check if base name is in collection name
            new_collection = collection
            #print(f"Handler: Found target collection: {new_collection.name}") # DEBUG
            break

    if new_collection:
        # Check if the operator can be called safely
        if bpy.context.scene is not None and bpy.context.window_manager is not None:
            #print("Handler: Invoking confirmation dialogue")
            bpy.ops.object.blend_normals_by_proximity('INVOKE_DEFAULT')

    # Set the global variable to the added collection
    added_collection = new_collection
    #print(f"Handler: Added collection set to: {added_collection.name}")  # DEBUG

    # Set the active object of the collection (first)
    if added_collection and added_collection.objects:
        bpy.context.view_layer.objects.active = added_collection.objects[0]
    #print(f"Active object set to: {added_collection.objects[0].name}") # DEBUG

    # Update known collections for next import
    pre_collection_asset_added_handler.known_collections = all_collections
    #print(f"Handler: Updated known collections: {pre_collection_asset_added_handler.known_collections}") # DEBUG


# -----------------------------------------------------------------------------#
# Wizards                                                                      #
# -----------------------------------------------------------------------------#
# Adds a dialogue to confirm the asset setup.
class OBJECT_OT_asset_blend_normals_by_proximity(bpy.types.Operator):
    bl_idname = "object.blend_normals_by_proximity"
    bl_label = col_blend_normals_by_proximity
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout

        # Collection selection panel
        row = layout.row()
        
        # Check if this is Bforartists
        if "OUTLINER_MT_view" in dir(bpy.types):
            icon = "WIZARD"
        else:
            icon = "INFO"

        row.label(text="Select an existing collection of mesh objects to apply", icon=icon)
        row = layout.row()
        row.prop_search(context.scene, "target_collection", bpy.data, "collections", text="Target Collection")
        row = layout.row()
        row.prop(context.scene, "use_relative_position", text="Use Relative Position")
        row = layout.row()
        row.prop(context.scene, "use_wireframe_on_collection", text="Enable Bounds Display")

    def execute(self, context):
        try:
            # Set viewport settings to wireframe for all children objects
            if context.scene.target_collection and context.scene.use_wireframe_on_collection:
                for obj in context.scene.target_collection.objects:
                    if obj.type == 'MESH':
                        obj.display_type = 'BOUNDS'

            # Asset Reference
            asset = col_blend_normals_by_proximity

            # Add Geometry Nodes modifier
            obj = context.active_object
            geom_nodes = obj.modifiers.get(col_blend_normals_by_proximity)

            if geom_nodes and geom_nodes.node_group and geom_nodes.node_group.name.startswith(asset) and obj == context.active_object:
                #print(f"GN nodetree dected, it is: {geom_nodes.node_group.name}")  # DEBUG
                try:
                    # Find the collection socket
                    group_input_node = None
                    collection_socket = None

                    for node in geom_nodes.node_group.nodes:
                        if node.type == 'GROUP_INPUT':
                            group_input_node = node
                            for output in node.outputs:
                                if output.type == 'COLLECTION':
                                    collection_socket = output
                                    break
                            break

                    # Set relative position if enabled
                    if context.scene.use_relative_position:
                        print("Relative Position Property found")
                        # Find the relative position socket
                        if geom_nodes:

                            geom_nodes["Socket_12"] = True
                            print(f"Socket_12 value after update: {True}")
                        else:
                            print("Geometry Nodes modifier not found")
                    else:
                        print("Relative Position not found")


                    if group_input_node and collection_socket:
                        #print(f"Execute: socket found: {collection_socket}")  # DEBUG
                        # Set the collection both in the modifier and node
                        geom_nodes["Socket_3"] = context.scene.target_collection
                        collection_socket.default_value = context.scene.target_collection

                        # Force update
                        obj.update_tag()
                        bpy.context.view_layer.update()

                        self.report({'INFO'}, "Target Collection successfully assigned to the Geomtry Nodes setup")


                    else:
                        self.report({'WARNING'}, "Collection input not found in Geometry Nodes setup")

                except Exception as e:
                    self.report({'ERROR'}, f"Error assigning collection: {str(e)}")
            else:
                self.report({'ERROR'}, f"Looks like it couldn't find the Collection socket in the Geometry Nodes setup...")




            # Update the properties editor to reflect the changes
            bpy.context.view_layer.update()

            # Nudge the object to force a refresh
            obj.location = obj.location

            # Update properties editor to see changes
            for area in bpy.context.screen.areas:
                if area.type == 'PROPERTIES':
                    area.tag_redraw()

            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"An error occurred: {str(e)}")
            return {'CANCELLED'}

# -----------------------------------------------------------------------------#
# Registry                                                                     #
# -----------------------------------------------------------------------------#
def register():
    bpy.utils.register_class(OBJECT_OT_asset_blend_normals_by_proximity)
    bpy.app.handlers.blend_import_pre.append(pre_collection_asset_added_handler)
    bpy.app.handlers.blend_import_post.append(collection_asset_added_handler)
    subscribe_collection_handlers(subscription_owner)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_asset_blend_normals_by_proximity)
    bpy.app.handlers.blend_import_pre.remove(pre_collection_asset_added_handler)
    bpy.app.handlers.blend_import_post.remove(collection_asset_added_handler)
    unsubscribe_collection_handlers(subscription_owner)

    for handler in bpy.app.handlers.blend_import_pre:
        bpy.app.handlers.blend_import_pre.remove(handler)
    for handler in bpy.app.handlers.blend_import_post:
        bpy.app.hendlers.blend_import_post.remove(handler)


if __name__ == "__main__":
    register()
