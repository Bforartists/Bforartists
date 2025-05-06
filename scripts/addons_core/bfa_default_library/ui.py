import bpy
import os
from bpy.types import Menu, Operator, Panel

# Define the path to the asset library and asset names
ASSET_LIB_PATH = os.path.join(os.path.dirname(__file__), "Geometry Nodes Library")
ASSET_NAMES = [
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
    "Smart Cylinder Revolved",
    "Smart Cylinder Rounded Revolved",
    "Smart Grid",
    "Smart Icosphere",
    "Smart Sphere",
    "Smart Sphere Revolved",
    "Smart Spiral",
    "Smart Torus",
    "Smart Tube Rounded Revolved"
]

def append_asset_as_object(filepath, object_name):
    """Append an object from the library as a local copy"""
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

class ASSET_MT_mesh_add(Menu):
    bl_label = "Default Library Assets"
    bl_idname = "ASSET_MT_mesh_add"

    def draw(self, context):
        layout = self.layout
        for asset_name in ASSET_NAMES:
            op = layout.operator("wm.insert_mesh_asset", text=f"{asset_name} Asset")
            op.asset_name = asset_name

class VIEW3D_PT_asset_panel(Panel):
    bl_label = "Default Library"
    bl_idname = "VIEW3D_PT_asset_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Assets"

    def draw(self, context):
        layout = self.layout
        layout.menu("ASSET_MT_mesh_add")

def menu_func(self, context):
    self.layout.menu("ASSET_MT_mesh_add")

classes = (
    OT_InsertMeshAsset,
    ASSET_MT_mesh_add,
    VIEW3D_PT_asset_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)
