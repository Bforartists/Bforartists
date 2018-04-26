bl_info = {
    "name": "Add primitive modals",
    "author": "CC",
    "version": (1, 0),
    "blender": (2, 79, 0),
    "location": "View3D",
    "description": "Adds new options for creating primitive objects in a faster way.",
    "warning": "",
    "wiki_url": "",
    "category": "Add Mesh",
    }

# To support reload properly, try to access a package var, 
# if it's there, reload everything
if "bpy" in locals():
    import imp
    imp.reload(gen_func)
    imp.reload(View_3d_HUD)
    imp.reload(primitive_Box)
    imp.reload(primitive_Plane)
    imp.reload(primitive_Cylinder)
    imp.reload(primitive_Circle)
    imp.reload(primitive_Sphere)
    imp.reload(BoxCreationModal)
    imp.reload(CylinderCreationModal)
    imp.reload(SphereCreationModal)
    
else:
    from . import gen_func, View_3d_HUD, primitive_Box, BoxCreationModal, primitive_Plane, CylinderCreationModal, primitive_Cylinder, primitive_Circle, primitive_Sphere, SphereCreationModal
    

import bpy
from bpy.types import Operator, AddonPreferences
from bpy.props import FloatProperty, IntProperty, BoolProperty

#@addon.Preferences.Include
class addPrimitiveModals(AddonPreferences):
    bl_idname = __name__
    
    Zsensitivity = FloatProperty(name="Z Sensitivity", default=1.0)
    Max_Click_Dist = FloatProperty(name="Max Click Distance", default=2500)
    HUD_Center = BoolProperty(name="UI Centered", default=True)

    def draw(self, context):
        layout = self.layout        
        layout.prop(self, "Zsensitivity")
        layout.prop(self, "Max_Click_Dist")
        layout.prop(self, "HUD_Center")
        #layout.prop(self, "number")

#Add option in the Add object menu.
def add_object_button(self, context):
    
    self.layout.operator_context = 'INVOKE_DEFAULT'
    
    self.layout.operator(
        operator="object.box_creation_modal_operator",
        text="Box Modal",
        icon='MESH_CUBE')
    self.layout.operator(
        operator="object.cylinder_creation_modal_operator",
        text="Cylinder Modal",
        icon='MESH_CYLINDER')
    self.layout.operator(
        operator="object.sphere_creation_modal_operator",
        text="Sphere Modal",
        icon='MESH_UVSPHERE')
    self.layout.separator()


#Add Buttons to the Tool panel
class VIEW3D_PT_ModalAddPanel(bpy.types.Panel):
    """Creates a Panel in the Toolbar"""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'Create'
    bl_label = "Add Modals"


    def draw(self, context):
        lay_out = self.layout.column(align=True)
        lay_out.operator(operator="object.box_creation_modal_operator", text="Box Modal", icon='MESH_CUBE')
        lay_out.operator(operator="object.cylinder_creation_modal_operator", text="Cylinder Modal", icon='MESH_CYLINDER')
        lay_out.operator(operator="object.sphere_creation_modal_operator", text="Sphere Modal", icon='MESH_UVSPHERE')
            
        
def register():

    bpy.utils.register_class(addPrimitiveModals)
    bpy.utils.register_class(VIEW3D_PT_ModalAddPanel)
    bpy.types.INFO_MT_mesh_add.prepend(add_object_button)
    bpy.utils.register_module(__name__)

def unregister():

    bpy.utils.unregister_class(addPrimitiveModals)
    bpy.utils.unregister_class(VIEW3D_PT_ModalAddPanel)
    bpy.types.INFO_MT_mesh_add.remove(add_object_button)
    bpy.utils.unregister_module(__name__)
    
if __name__ == "__main__":
    register()
