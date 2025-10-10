# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either extreme 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  extreme 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# -----------------------------------------------------------------------------
# Wizard Handlers
# Handles automatic detection and triggering of wizards when assets are imported
# -----------------------------------------------------------------------------

import bpy
from bpy.app.handlers import persistent

# Import wizard operators (this assumes both files are in the same module)
from . import wizard_operators as wiz_ops

# Asset names for wizard recognition (import from operators)
from .wizard_operators import BLEND_NORMALS_BY_PROXIMITY

# Global wizard properties (shared with operators)
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

bpy.types.Scene.inject_intersection_nodegroup = bpy.props.BoolProperty(
    name="Inject Intersection Nodegroup",
    description="Inject S_Intersections node group into materials of target collection",
    default=True
)

# Object that will store the handle to the msgbus subscription
subscription_owner = object()

# -----------------------------------------------------------------------------#
# Handler Mapping System                                                       #
# -----------------------------------------------------------------------------#

# Dictionary mapping asset names/patterns to their respective wizard operators
WIZARD_HANDLERS = {
    BLEND_NORMALS_BY_PROXIMITY: "wizard.blend_normals_by_proximity",
    # Add new handler mappings here, referencing the wizard_operators.py:
    # "Your New Asset Name": "wizard.your_new_wizard",
    # "Another Asset Pattern": "wizard.another_wizard",
}

# -----------------------------------------------------------------------------#
# Collection Handler Functions                                                 #
# -----------------------------------------------------------------------------#

def subscribe_collection_handlers(owner):
    """Subscribe to collection changes"""
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.Collection, "name"),
        owner=owner,
        args=("collection_added",),
        notify=lambda *args: print("Collection Asset added to scene"),
        options={"PERSISTENT"}
    )

def unsubscribe_collection_handlers(owner):
    """Unsubscribe from collection changes"""
    if owner is not None:
        bpy.msgbus.clear_by_owner(owner)

@persistent
def load_handler(dummy):
    """Handler called when a blend file is loaded"""
    subscribe_collection_handlers(subscription_owner)

# Pre-handler to log existing collections before import to detect what was recently added
@persistent
def pre_collection_asset_added_handler(scene):
    """Logs existing collections before import"""
    pre_collection_asset_added_handler.known_collections = set(bpy.data.collections)

# Main handler that detects new collections and triggers appropriate wizards
@persistent
def collection_asset_added_handler(arg):
    """Detects new collections and triggers appropriate wizards"""
    scene = bpy.context.scene
    
    if not hasattr(pre_collection_asset_added_handler, 'known_collections'):
        return

    # Get current collections and find the differences
    all_collections = set(bpy.data.collections)
    new_collections = all_collections - pre_collection_asset_added_handler.known_collections

    # Check each new collection against our wizard handlers
    for collection in new_collections:
        for asset_pattern, wizard_operator in WIZARD_HANDLERS.items():
            if asset_pattern in collection.name:
                # Set the collection in the scene properties
                scene.target_collection = collection
                
                # Set the active object if collection has objects
                if collection.objects:
                    bpy.context.view_layer.objects.active = collection.objects[0]
                    
                # Invoke the appropriate wizard
                try:
                    bpy.ops.wizard.blend_normals_by_proximity('INVOKE_DEFAULT')
                except Exception as e:
                    print(f"Failed to invoke wizard {wizard_operator}: {e}")
                
                break  # Only handle one wizard per collection

    # Update known collections for next import
    pre_collection_asset_added_handler.known_collections = all_collections


# TO DO: Add Node Asset Handlers for GN, Shaders and Compositor. Also add for other asset types, like mesh, material, brush, scene and world.


# -----------------------------------------------------------------------------#
# Easy-to-use function to add new wizard handlers                                           #
# -----------------------------------------------------------------------------#


def register_wizard_handler(asset_pattern, wizard_operator):
    """Register a new wizard handler mapping"""
    WIZARD_HANDLERS[asset_pattern] = wizard_operator

def unregister_wizard_handler(asset_pattern):
    """Unregister a wizard handler mapping"""
    if asset_pattern in WIZARD_HANDLERS:
        del WIZARD_HANDLERS[asset_pattern]

# Initialize the known collections
pre_collection_asset_added_handler.known_collections = set()

def register():
    """Register all handlers"""
    # Register handlers
    bpy.app.handlers.blend_import_pre.append(pre_collection_asset_added_handler)
    bpy.app.handlers.blend_import_post.append(collection_asset_added_handler)
    subscribe_collection_handlers(subscription_owner)

def unregister():
    """Unregister all handlers"""
    # Unregister handlers
    bpy.app.handlers.blend_import_pre.remove(pre_collection_asset_added_handler)
    bpy.app.handlers.blend_import_post.remove(collection_asset_added_handler)
    unsubscribe_collection_handlers(subscription_owner)

if __name__ == "__main__":
    register()
