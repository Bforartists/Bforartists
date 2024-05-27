import bpy
material = bpy.context.material #(bpy.context.material.active_node_material if bpy.context.material.active_node_material else bpy.context.material)

material.pov_subsurface_scattering.radius = 9.436, 3.348, 1.790
material.pov_subsurface_scattering.color = 0.439, 0.216, 0.141
