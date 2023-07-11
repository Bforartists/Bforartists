#Available since 1995

import bpy
bpy.context.object.data.type = 'AREA'
lampdata = bpy.context.object.data

lampdata.size = 0.016
lampdata.size_y = 1.149
lampdata.pov.shadow_ray_samples_x = 1
lampdata.pov.shadow_ray_samples_y = 2
lampdata.color = (1.0, 0.83, 0.986274528503418)
lampdata.energy = 4.66287 #0.93257#4.66287#5000lm/21.446(=lux)*0.004*2.5(distance) *2 for distance is the point of half strength
