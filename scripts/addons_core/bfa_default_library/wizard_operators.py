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
    bl_description = "Configure the Blend Normals by Proximity geometry nodes setup"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """Available when there's an active object with geometry nodes"""
        return (context.object and
                context.object.modifiers and
                any(mod.type == 'NODES' for mod in context.object.modifiers))

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=330)

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
        row.label(text="Select an existing collection of mesh objects to apply", icon=icon1)
        
        row = layout.row()
        row.prop_search(context.scene, "target_collection", bpy.data, "collections", text="Target Collection")

        row = layout.row()
        row.prop(context.scene, "inject_intersection_nodegroup", text="Apply Blend to Materials", icon="MATERIAL")

        row = layout.row()
        row.prop(context.scene, "use_relative_position", text="Use Relative Position", icon=icon2)

        row = layout.row()
        row.prop(context.scene, "use_wireframe_on_collection", text="Enable Bounds Display", icon="SHADING_BBOX")

    def execute(self, context):
        try:
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
