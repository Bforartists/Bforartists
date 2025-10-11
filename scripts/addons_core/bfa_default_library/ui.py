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
# ! IMPORTANT! READ THIS WHEN SETTING UP THE LIBRARY
# This is a work in progress, and many assets, categories, thumbnails and more are subject to change.
# Use at own risk.
# -----------------------------------------------------------------------------

import bpy
import os
from bpy.types import Menu, Operator, Panel
# Define the path to the asset library and asset names with icons
ASSET_LIB_PATH = os.path.join(os.path.dirname(__file__), "Geometry Nodes Library", "G_Primitives.blend")
ASSETS = [
    ("Capsule", "MESH_CAPSULE"),
    ("Capsule Revolved", "MESH_CAPSULE"),
    ("Circle", "MESH_CIRCLE"),
    ("Circle Revolved", "MESH_CIRCLE"),
    ("Cone", "MESH_CONE"),
    ("Cone Rounded", "MESH_CONE"),
    ("Cone Rounded Revolved", "MESH_CONE"),
    ("Cube", "MESH_CUBE"),
    ("Cube Rounded", "MESH_CUBE"),
    ("Curve Lofted", "CURVE_PATH"),
    ("Cylinder", "MESH_CYLINDER"),
    ("Cylinder Revolved", "MESH_CYLINDER"),
    ("Cylinder Rounded", "MESH_CYLINDER"),
    ("Cylinder Rounded Revolved", "MESH_CYLINDER"),
    ("Grid", "MESH_GRID"),
    ("Icosphere", "MESH_ICOSPHERE"),
    ("Sphere", "MESH_UVSPHERE"),
    ("Sphere Revolved", "MESH_UVSPHERE"),
    ("Spiral", "FORCE_VORTEX"),
    ("Torus", "MESH_TORUS"),
    ("Torus Revolved", "MESH_TORUS"),
    ("Tube", "MESH_CYLINDER"),
    ("Tube Revolved", "MESH_CYLINDER"),
    ("Tube Rounded", "MESH_CYLINDER"),
    ("Tube Rounded Revolved", "MESH_CYLINDER"),
]

def append_asset_as_object(filepath, object_name):
    """Append an object from the library as a local copy"""
    if not os.path.exists(filepath):  # Check if file exists
        print(f"Error: {filepath} not found!")
        return None

    with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
        if object_name in data_from.objects:
            data_to.objects = [object_name]

    if data_to.objects:
        obj = data_to.objects[0]
        new_obj = obj.copy()
        new_obj.data = obj.data.copy() if obj.data else None
        new_obj.location = bpy.context.scene.cursor.location
        new_obj.rotation_euler = bpy.context.scene.cursor.rotation_euler
        bpy.context.collection.objects.link(new_obj)
        return new_obj
    return None

class OT_InsertMeshAsset(Operator):
    bl_idname = "wm.insert_mesh_asset"
    bl_label = "Insert Mesh Asset"

    asset_name: bpy.props.StringProperty()

    def execute(self, context):
        obj = append_asset_as_object(ASSET_LIB_PATH, self.asset_name)
        if obj:
            context.view_layer.objects.active = obj
            obj.select_set(True)
            return {'FINISHED'}
        self.report({'ERROR'}, f"Could not import asset: {self.asset_name}")
        return {'CANCELLED'}

# -----------------------------------------------------------------------------

class WIZARD_OT_TriggerAssetWizard(Operator):
    """Trigger the appropriate wizard for the selected asset or object"""
    bl_idname = "wizard.trigger_asset_wizard"
    bl_label = "Trigger Asset Wizard"
    bl_description = "Run the appropriate wizard for the selected object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """Available when there's an active object"""
        return context.object is not None

    def execute(self, context):
        obj = context.object
        
        # Check for Blend Normals by Proximity modifier
        if obj.modifiers:
            for mod in obj.modifiers:
                if mod.type == 'NODES' and mod.node_group:
                    if "Blend Normals by Proximity" in mod.node_group.name:
                        # Trigger the blend normals wizard
                        bpy.ops.wizard.blend_normals_by_proximity('INVOKE_DEFAULT')
                        self.report({'INFO'}, "Blend Normals wizard triggered")
                        return {'FINISHED'}
        
        # Add more wizard detection here as you implement them
        # Example: if "Another Wizard Asset" in some_property: trigger another wizard
        
        self.report({'INFO'}, "No wizard detected for this object")
        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)

# -----------------------------------------------------------------------------#
# Interface Entries
# -----------------------------------------------------------------------------#

class ASSET_MT_mesh_add(Menu):
    bl_label = "Smart Primitives"
    bl_idname = "ASSET_MT_mesh_add"
    bl_icon = 'ORIGIN_TO_GEOMETRY'

    def draw(self, context):
        layout = self.layout
        for asset_name, icon in ASSETS:
            op = layout.operator("wm.insert_mesh_asset", text=asset_name, icon=icon)
            op.asset_name = asset_name

def menu_func(self, context):
    # Add the sub-menu to the Add menu with an icon
    layout = self.layout
    layout.separator()
    layout.menu("ASSET_MT_mesh_add", icon='ORIGIN_TO_GEOMETRY')

def asset_menu_func(self, context):
    """Add wizard trigger to asset menu"""
    layout = self.layout
    if context.object:
        # Check if object has any wizard-compatible features
        has_wizard = False
        if context.object.modifiers:
            for mod in context.object.modifiers:
                if mod.type == 'NODES' and mod.node_group:
                    if "Blend Normals by Proximity" in mod.node_group.name:
                        has_wizard = True
                        break
        
        if has_wizard:
            layout.separator()
            layout.operator("wizard.trigger_asset_wizard", icon='WIZARD')

# -----------------------------------------------------------------------------#
# Classes
# -----------------------------------------------------------------------------#

classes = (
    OT_InsertMeshAsset,
    WIZARD_OT_TriggerAssetWizard,
    ASSET_MT_mesh_add,
)

# -----------------------------------------------------------------------------#
# Register
# -----------------------------------------------------------------------------#

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    # Add the sub-menu to the main Add menu
    bpy.types.VIEW3D_MT_add.append(menu_func)
    # Add wizard trigger to asset menu
    bpy.types.VIEW3D_MT_object_asset.append(asset_menu_func)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    # Remove the sub-menu from the Add menu
    bpy.types.VIEW3D_MT_add.remove(menu_func)
    # Remove wizard trigger from asset menu
    bpy.types.VIEW3D_MT_object_asset.remove(asset_menu_func)
