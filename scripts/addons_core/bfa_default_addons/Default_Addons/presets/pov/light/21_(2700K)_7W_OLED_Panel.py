#since 2025
#inspired by OSRAM Early Future / IKEA Vitsand / OTI Lumionics Aerelight

import bpy
bpy.context.object.data.type = 'AREA'
lampdata = bpy.context.object.data

lampdata.size = 0.033
lampdata.size_y = 0.133
lampdata.pov.shadow_ray_samples_x = 2
lampdata.pov.shadow_ray_samples_y = 2
lampdata.color = (1.0, 0.8292156958580017, 0.6966666865348816)
lampdata.energy = 0.83932#900lm/21.446(=lux)*0.004*2.5(distance) *2 for distance is the point of half strength
