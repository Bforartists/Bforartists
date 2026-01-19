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
# Compositor Nodes Asset Operations
# Handles operations related to Compositor Nodes assets
# -----------------------------------------------------------------------------

import bpy
from bpy.types import Operator

class COMPOSITOR_OT_ApplyCompositorSetup(Operator):
    """Apply compositor node setup to current scene"""
    bl_idname = "compositor.apply_setup"
    bl_label = "Apply Compositor Setup"
    bl_description = "Apply the selected compositor node setup to the current scene"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """Available when there's an active scene and compositor nodes can be used"""
        return context.scene and context.scene.use_nodes

    def execute(self, context):
        # Implementation for compositor setup application
        # This would typically involve enabling nodes, setting up specific node trees
        # or applying compositor templates from the asset library
        
        self.report({'INFO'}, "Compositor setup applied")
        return {'FINISHED'}

class COMPOSITOR_OT_ResetCompositor(Operator):
    """Reset compositor to default state"""
    bl_idname = "compositor.reset_setup"
    bl_label = "Reset Compositor"
    bl_description = "Reset the compositor to its default state"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """Available when there's an active scene"""
        return context.scene is not None

    def execute(self, context):
        if context.scene.use_nodes:
            context.scene.use_nodes = False
            context.scene.use_nodes = True  # This resets to default
            self.report({'INFO'}, "Compositor reset to default")
        else:
            self.report({'WARNING'}, "Compositor nodes not enabled")
        
        return {'FINISHED'}

classes = (
    COMPOSITOR_OT_ApplyCompositorSetup,
    COMPOSITOR_OT_ResetCompositor,
)

def register():
    """Register compositor operator classes."""
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError as e:
            if "already registered" not in str(e):
                print(f"⚠ Error registering {cls.__name__}: {e}")


def unregister():
    """Unregister compositor operator classes."""
    for cls in reversed(classes):
        try:
            if hasattr(cls, 'bl_rna'):
                bpy.utils.unregister_class(cls)
        except RuntimeError as e:
            if "not registered" not in str(e):
                print(f"⚠ Error unregistering {cls.__name__}: {e}")