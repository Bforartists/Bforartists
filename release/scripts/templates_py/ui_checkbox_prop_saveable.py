# This script is a simple example for a checkbox prop. It creates a bool.
# This bool can then be used to do things.
# In our example it changes a text button into an icon button and back.
# Note that the state of the bool can be stored with saving the startup.blend
# When you reopen the app, then the checkbox starts with the value that you had when you saved the startup.blend
# You have to install it as an addon though.
# Also note that the bool is globally avaliable. And not just for this script or section

import bpy

class MyData(bpy.types.PropertyGroup):
    checkbox_bool : bpy.props.BoolProperty(name="A checkbox", description="Do this or that", default = False) # Our prop

class XX_PT_checkboxpropPanel(bpy.types.Panel):
    bl_label = "Checkbox prop"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout

        scene = context.scene # Our data is in the current scene
        layout.prop(scene.my_addon_data, "checkbox_bool") # Our checkbox

        # Example useage of the flag.
        # Our buttons. When the checkbox is off then we have the text buttons.
        # When the checkbox is on, then we have icon buttons
        if scene.my_addon_data.checkbox_bool:
            layout.label(text="Mesh:")
            row = layout.row(align=False)
            row.alignment = 'LEFT'
            row.operator("mesh.primitive_plane_add", text="", icon='MESH_PLANE')
            row.operator("mesh.primitive_cube_add", text="", icon='MESH_CUBE')
            row.operator("mesh.primitive_circle_add", text="", icon='MESH_CIRCLE')
            row.operator("mesh.primitive_uv_sphere_add", text="", icon='MESH_UVSPHERE')
            row.operator("mesh.primitive_ico_sphere_add", text="", icon='MESH_ICOSPHERE')
            row = layout.row(align=False)
            row.operator("mesh.primitive_cylinder_add", text="", icon='MESH_CYLINDER')
            row.operator("mesh.primitive_cone_add", text="", icon='MESH_CONE')
            row.operator("mesh.primitive_torus_add", text="", icon='MESH_TORUS')

        else:
            col = layout.column(align=True)
            col.label(text="Mesh:")
            col.operator("mesh.primitive_plane_add", text="Plane", icon='MESH_PLANE')
            col.operator("mesh.primitive_cube_add", text="Cube", icon='MESH_CUBE')
            col.operator("mesh.primitive_circle_add", text="Circle", icon='MESH_CIRCLE')
            col.operator("mesh.primitive_uv_sphere_add", text="UV Sphere", icon='MESH_UVSPHERE')
            col.operator("mesh.primitive_ico_sphere_add", text="Ico Sphere", icon='MESH_ICOSPHERE')
            col.operator("mesh.primitive_cylinder_add", text="Cylinder", icon='MESH_CYLINDER')
            col.operator("mesh.primitive_cone_add", text="Cone", icon='MESH_CONE')
            col.operator("mesh.primitive_torus_add", text="Torus", icon='MESH_TORUS')

def register():
    bpy.utils.register_class(XX_PT_checkboxpropPanel)
    #Our data block
    bpy.utils.register_class(MyData) # Our data block
    bpy.types.Scene.my_addon_data = bpy.props.PointerProperty(type=MyData) # Bind reference of type of our data block to type Scene objects

def unregister():
    del bpy.types.Scene.my_addon_data # Unregister our data block when unregister.
    bpy.utils.unregister_class(MyData) # Our data block
    bpy.utils.unregister_class(XX_PT_checkboxpropPanel)

if __name__ == "__main__":
    register()