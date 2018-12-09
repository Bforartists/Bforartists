#Since the dawn of time

import bpy
bpy.context.object.data.type = 'AREA'
lampdata = bpy.context.object.data

lampdata.size = 1.2
lampdata.size_y = 2.10
lampdata.shadow_ray_samples_x = 2
lampdata.shadow_ray_samples_y = 3
lampdata.color = (1.0, 1.0, 1.0)
lampdata.energy = 1.094316#91193 #lux
lampdata.distance = 1.0
