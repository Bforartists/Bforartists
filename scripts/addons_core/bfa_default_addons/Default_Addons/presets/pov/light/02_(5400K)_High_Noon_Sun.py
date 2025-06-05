#Since the dawn of time

import bpy
bpy.context.object.rotation_euler = (0,0,0)#And loc HIGH
bpy.context.object.location = (0,0,700000000)
bpy.context.object.data.type = 'AREA'
lampdata = bpy.context.object.data

lampdata.shape = 'SQUARE'
lampdata.size = 30000000#0.02
#lampdata.size_y = 0.02
lampdata.pov.shadow_ray_samples_x = 2
#lampdata.pov.shadow_ray_samples_y = 3
lampdata.color = (1.0, 1.0, 1.0)
lampdata.energy = 1.094316#91193 #lux
