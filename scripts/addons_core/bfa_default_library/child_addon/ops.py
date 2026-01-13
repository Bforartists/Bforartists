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
# Main Operations Module
# This module serves as the central hub for all operations and panels
# -----------------------------------------------------------------------------

import bpy
from bpy.types import Operator

# Import operations from submodules
from .operators.geometry_nodes import (
    GN_ASSET_NAMES,
    is_gn_asset_object,
    get_all_gn_asset_objects
)

class OBJECT_OT_ApplySelected(Operator):
    """Apply selected objects and optionally join/remesh/boolean in one click"""
    bl_idname = "object.apply_selected_objects"
    bl_label = "Apply Selected Objects"
    bl_description = "Converts objects to regular mesh objects with optional joining, remeshing and boolean operations"
    bl_options = {'REGISTER', 'UNDO'}

    join_on_apply: bpy.props.BoolProperty(
        name="Join on Apply",
        description="Joins all applied objects into a single mesh object without changing geometry",
        default=True
    )

    boolean_on_apply: bpy.props.BoolProperty(
        name="Boolean on Apply",
        description="Uses Float boolean union operations to combine applied objects into a single mesh object",
        default=False
    )

    remesh_on_apply: bpy.props.BoolProperty(
        name="Remesh on Apply",
        description="Creates Voxel-based remeshed mesh with custom resolution to combine applied obejcts into a single remeshed object",
        default=False
    )
    
    voxel_size: bpy.props.FloatProperty(
        name="Voxel Size",
        description="Voxel size for the remeshing operation",
        default=0.1,
        min=0.005,
        max=1.0,
        step=0.01,
        precision=3
    )

    @classmethod
    def poll(cls, context):
        """Available if there are objects selected and only compatible types"""
        selected_objects = context.selected_objects
        if not selected_objects:
            return False
        
        # Check if all selected objects are compatible types
        compatible_types = {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META'}
        for obj in selected_objects:
            if obj.type not in compatible_types:
                return False
        
        return True

    def execute(self, context):
        selected_objects = context.selected_objects
        
        if not selected_objects:
            self.report({'WARNING'}, "No objects found to process")
            return {'CANCELLED'}

        objects_to_delete = []
        new_objects = []
        
        try:
            # Convert all selected objects to mesh
            bpy.ops.object.select_all(action='DESELECT')
            for obj in selected_objects:
                obj.select_set(True)
                objects_to_delete.append(obj)
            
            context.view_layer.objects.active = selected_objects[0]
            bpy.ops.object.visual_geometry_to_objects()
            
            # Get newly created mesh objects
            current_selected = set(context.selected_objects)
            original_selected = set(objects_to_delete)
            new_objects = [obj for obj in current_selected if obj not in original_selected]
            
            final_object = None
            
            if new_objects:
                if self.boolean_on_apply:
                    # Boolean union operation
                    base_object = new_objects[0]
                    base_object.select_set(True)
                    context.view_layer.objects.active = base_object

                    objects_to_bool = new_objects[1:]
                    objects_to_delete.extend(objects_to_bool)

                    if len(new_objects) > 1:
                        for obj in objects_to_bool:
                            if obj and obj.name in context.scene.objects:
                                bool_mod = base_object.modifiers.new(name="Boolean", type='BOOLEAN')
                                bool_mod.operation = 'UNION'
                                bool_mod.solver = 'FLOAT'
                                bool_mod.object = obj
                                
                                try:
                                    bpy.ops.object.modifier_apply(modifier=bool_mod.name)
                                except RuntimeError as e:
                                    print(f"Boolean operation failed: {str(e)}")
                                    continue
                                
                                context.view_layer.update()
                                
                                bpy.ops.object.select_all(action='DESELECT')
                                base_object.select_set(True)
                                context.view_layer.objects.active = base_object
                    
                    final_object = base_object
                
                elif self.join_on_apply and len(new_objects) > 1:
                    # Simple join operation
                    context.view_layer.objects.active = new_objects[0]
                    for obj in new_objects:
                        obj.select_set(True)
                    bpy.ops.object.join()
                    final_object = context.view_layer.objects.active

                elif self.remesh_on_apply:
                    # First join the new objects
                    if len(new_objects) > 1:
                        context.view_layer.objects.active = new_objects[0]
                        for obj in new_objects:
                            obj.select_set(True)
                        bpy.ops.object.join()
                    
                    final_object = context.view_layer.objects.active

                    # Ensure the final object is properly processed before remeshing
                    bpy.ops.object.select_all(action='DESELECT')
                    final_object.select_set(True)
                    context.view_layer.objects.active = final_object
                    
                    # Convert to mesh if it's not already a mesh (safety check)
                    if final_object.type != 'MESH':
                        try:
                            bpy.ops.object.convert(target='MESH')
                        except RuntimeError:
                            # Could not convert object type to mesh for remeshing
                            pass

                    # Make sure the object has valid mesh data
                    if not final_object.data or not hasattr(final_object.data, 'polygons'):
                        try:
                            bpy.ops.object.convert(target='MESH')
                        except RuntimeError:
                            # Invalid mesh data for remeshing
                            final_object = None
                    
                    if final_object:
                        # Add a remesh modifier with the specified voxel size
                        remesh_mod = final_object.modifiers.new(name="TempRemesh", type='REMESH')
                        remesh_mod.mode = 'VOXEL'
                        remesh_mod.voxel_size = self.voxel_size
                        
                        # Set smooth shading for better results
                        remesh_mod.use_smooth_shade = True
                        
                        # Ensure proper selection and context for modifier application
                        bpy.ops.object.select_all(action='DESELECT')
                        final_object.select_set(True)
                        context.view_layer.objects.active = final_object
                        context.view_layer.update()
                        
                        # Apply the modifier with robust error handling
                        try:
                            # Make sure modifier is valid and object is selected
                            if remesh_mod.name in final_object.modifiers:
                                # Apply the modifier via bpy.ops
                                bpy.ops.object.modifier_apply(modifier=remesh_mod.name, report=True)
                                #print(f"✓ Successfully applied remesh with voxel size: {self.voxel_size}")
                            else:
                                #print("⚠ Remesh modifier was not properly created")
                                pass
                        except RuntimeError as e:
                            #print(f"⚠ Remesh operation failed: {str(e)}")
                            
                            # Clean up the modifier if it couldn't be applied
                            if remesh_mod.name in final_object.modifiers:
                                final_object.modifiers.remove(remesh_mod)
                            
                            # Fallback: Try creating the modifier again with different approach
                            try:
                                remesh_mod2 = final_object.modifiers.new(name="RemeshFallback", type='REMESH')
                                remesh_mod2.mode = 'VOXEL'
                                remesh_mod2.voxel_size = self.voxel_size
                                remesh_mod2.use_smooth_shade = True

                                bpy.ops.object.modifier_apply(modifier=remesh_mod2.name)
                            except RuntimeError:
                                # Fallback remesh also failed - silently continue
                                pass
                        
                        # Final cleanup and selection
                        context.view_layer.update()
                        bpy.ops.object.select_all(action='DESELECT')
                        final_object.select_set(True)
                        context.view_layer.objects.active = final_object

                    # DEBUG:
                    #self.report({'INFO'}, f"Applied remesh with voxel size: {self.voxel_size}")
                    
                else:
                    final_object = new_objects[0]

            # Clean up original objects
            bpy.ops.object.select_all(action='DESELECT')
            for obj in objects_to_delete:
                if obj and obj.name in context.scene.objects:
                    obj.select_set(True)
                bpy.ops.object.delete()
            
            # Select final object
            if final_object and final_object.name in context.scene.objects:
                bpy.ops.object.select_all(action='DESELECT')
                final_object.select_set(True)
                context.view_layer.objects.active = final_object
            
            # DEBUG:
            #self.report({'INFO'}, f"Applied {len(selected_objects)} objects")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error during operation: {str(e)}")
            return {'CANCELLED'}



# -----------------------------------------------------------------------------
# Registration
# -----------------------------------------------------------------------------

classes = (
    OBJECT_OT_ApplySelected,
)

# Track if scene properties are registered (prevent duplicates from multiple parent addons)
_scene_props_registered = False


def register():
    """Register all operator classes and scene properties."""
    global _scene_props_registered

    # Register scene properties only once (prevent duplicates from multiple parent addons)
    if not _scene_props_registered:
        bpy.types.Scene.join_apply = bpy.props.BoolProperty(
            name="Join on Apply",
            description="Join converted objects into a single mesh",
            default=True
        )

        bpy.types.Scene.boolean_apply = bpy.props.BoolProperty(
            name="Boolean on Apply",
            description="Apply a boolean union operation to combine objects into a single mesh",
            default=False
        )

        bpy.types.Scene.remesh_apply = bpy.props.BoolProperty(
            name="Remesh on Apply",
            description="Apply a remesh union operation to combine objects into a single mesh",
            default=False
        )

        bpy.types.Scene.voxel_size_apply = bpy.props.FloatProperty(
            name="Voxel Size",
            description="Voxel size for remeshing operation",
            default=0.1,
            min=0.005,
            max=1.0,
            step=0.01,
            precision=3
        )
        _scene_props_registered = True

    from bpy.utils import register_class
    for cls in classes:
        try:
            register_class(cls)
        except ValueError as e:
            if "already registered" not in str(e):
                print(f"⚠ Error registering {cls.__name__}: {e}")


def unregister():
    """Unregister all operator classes and scene properties."""
    global _scene_props_registered

    # Remove scene properties if registered
    if _scene_props_registered:
        try:
            del bpy.types.Scene.join_apply
            del bpy.types.Scene.boolean_apply
            del bpy.types.Scene.remesh_apply
            del bpy.types.Scene.voxel_size_apply
        except AttributeError:
            pass
        _scene_props_registered = False

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        try:
            unregister_class(cls)
        except RuntimeError as e:
            if "not registered" not in str(e):
                print(f"⚠ Error unregistering {cls.__name__}: {e}")
        except Exception as e:
            print(f"⚠ Error unregistering {cls.__name__}: {e}")


if __name__ == "__main__":
    register()