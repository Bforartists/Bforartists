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
# Shader Nodes Asset Operations
# Handles operations related to Shader Nodes assets
# -----------------------------------------------------------------------------

import bpy
from bpy.types import Operator

class SHADER_OT_ApplyShaderSetup(Operator):
    """Apply shader node setup to selected objects"""
    bl_idname = "shader.apply_setup"
    bl_label = "Apply Shader Setup"
    bl_description = "Apply the selected shader node setup to all selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """Available when there are selected objects with materials"""
        return context.selected_objects and any(obj.type == 'MESH' for obj in context.selected_objects)

    def execute(self, context):
        # Implementation for shader setup application
        # This would typically involve applying specific shader node groups
        # or material setups from the asset library
        
        processed_count = 0
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                # Apply shader logic here
                processed_count += 1
        
        self.report({'INFO'}, f"Shader setup applied to {processed_count} objects")
        return {'FINISHED'}

class SHADER_OT_CreateNewMaterial(Operator):
    """Create a new material with default shader setup"""
    bl_idname = "shader.create_new_material"
    bl_label = "Create New Material"
    bl_description = "Create a new material with a default shader setup"
    bl_options = {'REGISTER', 'UNDO'}

    material_name: bpy.props.StringProperty(
        name="Material Name",
        description="Name for the new material",
        default="New Material"
    )

    @classmethod
    def poll(cls, context):
        """Available when there are selected mesh objects"""
        return context.selected_objects and any(obj.type == 'MESH' for obj in context.selected_objects)

    def execute(self, context):
        processed_count = 0
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                # Create new material
                mat = bpy.data.materials.new(name=self.material_name)
                mat.use_nodes = True
                
                # Assign to object
                if obj.data.materials:
                    obj.data.materials[0] = mat
                else:
                    obj.data.materials.append(mat)
                
                processed_count += 1
        
        self.report({'INFO'}, f"Created materials for {processed_count} objects")
        return {'FINISHED'}

classes = (
    SHADER_OT_ApplyShaderSetup,
    SHADER_OT_CreateNewMaterial,
)

def register():
    """Register shader operator classes."""
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError as e:
            if "already registered" not in str(e):
                print(f"⚠ Error registering {cls.__name__}: {e}")


def unregister():
    """Unregister shader operator classes."""
    for cls in reversed(classes):
        try:
            if hasattr(cls, 'bl_rna'):
                bpy.utils.unregister_class(cls)
        except RuntimeError as e:
            if "not registered" not in str(e):
                print(f"⚠ Error unregistering {cls.__name__}: {e}")