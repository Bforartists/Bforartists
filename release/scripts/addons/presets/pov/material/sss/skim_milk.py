import bpy
material = bpy.context.material #(bpy.context.material.active_node_material if bpy.context.material.active_node_material else bpy.context.material)

material.pov_subsurface_scattering.radius = 18.424, 10.443, 3.502
material.pov_subsurface_scattering.color = 0.889, 0.888, 0.796
