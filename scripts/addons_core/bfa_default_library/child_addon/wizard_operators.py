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
# Wizard Popups
#
# Contains all wizard operator classes for different asset types
# These are used to popup user input wizards and run scripts after
# an asset has been added.
#
# These are drawn by using functions "def" that get called into an operator
# The operator then opens a panel that a user can confirm and customize
# This helps the user quickly get started, and dependencies scripts can run
# -----------------------------------------------------------------------------

import bpy
from bpy.types import Operator
import logging

# Set up logging
logger = logging.getLogger(__name__)


# Asset name for wizard recognition
BLEND_NORMALS_BY_PROXIMITY = "Blend Normals by Proximity"


# -----------------------------------------------------------------------------#
# Mesh Blend by Proximity                                                      #
# -----------------------------------------------------------------------------#

class WIZARD_OT_BlendNormalsByProximity(Operator):
    """Wizard to configure Blend Normals by Proximity geometry nodes setup"""
    bl_idname = "wizard.blend_normals_by_proximity"
    bl_label = BLEND_NORMALS_BY_PROXIMITY
    bl_description = "Configure the Blend Normals by Proximity Geometry Nodes setup on Target Collection of Mesh Objects. /nFlat normals will not Blend, only Smooth or Autosmooth normals."
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        """Always available - no checks at all"""
        # Return True unconditionally
        # This is the most permissive poll method possible
        return True

    def invoke(self, context, event):
        # Try to open dialog, but handle failures gracefully
        try:
            # Check if we have the necessary UI context
            if (hasattr(context, 'window_manager') and context.window_manager and
                hasattr(context, 'area') and context.area):
                return context.window_manager.invoke_props_dialog(self, width=400)
            else:
                # No UI context available - can't open dialog
                # Just execute without dialog
                return self.execute(context)
        except Exception as e:
            # If dialog fails, execute without it
            print(f"Failed to open wizard dialog: {e}")
            return self.execute(context)

    def draw(self, context):
        layout = self.layout

        # Check if this is Bforartists for the right icon
        if "OUTLINER_MT_view" in dir(bpy.types):
            icon1 = "WIZARD"
            icon2 = "MOUSE_POSITION"
        else:
            icon1 = "INFO"
            icon2 = "TRANSFORM_ORIGINS"

        # Collection selection panel
        row = layout.row()
        row.label(text="Run this wizard again to change settings on the Target Collection", icon=icon1)

        row = layout.row()
        row.prop_search(context.scene, "target_collection", bpy.data, "collections", text="Target Collection")

        # Show current target collection name or warning
        if context.scene.target_collection:
            row = layout.row()
            #row.label(text=f"Selected: {context.scene.target_collection.name}", icon='OUTLINER_COLLECTION')
            if not context.scene.target_collection.objects:
                row = layout.row()
                row.label(text="Collection is empty, add Mesh Objects to blend", icon='WARNING')
        else:
            row = layout.row()
            row.label(text="Please select a Target Collection", icon='ERROR')

        row = layout.row()
        row.prop(context.scene, "inject_intersection_nodegroup", text="Apply Blend to Materials", icon="MATERIAL")

        row = layout.row()
        row.prop(context.scene, "use_relative_position", text="Use Relative Position", icon=icon2)

        row = layout.row()
        row.prop(context.scene, "use_wireframe_on_collection", text="Enable Bounds Display", icon="SHADING_BBOX")

    def execute(self, context):
        try:
            # Validate that a target collection is selected
            if not context.scene.target_collection:
                self.report({'ERROR'}, "Please select a Target Collection first")
                return {'CANCELLED'}

            # Validate that the target collection has objects
            if not context.scene.target_collection.objects:
                self.report({'WARNING'}, "Target collection is empty, add Mesh Objects to blend")
                # Continue anyway - the operator might handle empty collections

            # RUN SCRIPTS: Import the geometry nodes operator and call it
            success = bpy.ops.object.meshblendbyproximity('EXEC_DEFAULT')

            if 'FINISHED' not in success:
                self.report({'ERROR'}, "Failed to execute mesh blend by proximity operation")
                return {'CANCELLED'}

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
    """Register all wizard operator classes."""
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError as e:
            if "already registered" not in str(e):
                logger.error(f"Error registering {cls.__name__}: {e}")

def unregister():
    """Unregister all wizard operator classes."""
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError as e:
            if "not registered" not in str(e):
                logger.error(f"Error unregistering {cls.__name__}: {e}")

if __name__ == "__main__":
    register()