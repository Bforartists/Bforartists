#Available since 1979
#more common than the warm white

import bpy
bpy.context.object.data.type = 'AREA'
lampdata = bpy.context.object.data

lampdata.size = 0.026
lampdata.size_y = 0.59
lampdata.pov.shadow_ray_samples_x = 1
lampdata.pov.shadow_ray_samples_y = 2
lampdata.color = (0.8313725590705872, 0.9215686321258545, 1.0)
lampdata.energy = 1.25898#1350lm/21.446(=lux)*0.004*2.5(distance) *2 for distance is the point of half strength
