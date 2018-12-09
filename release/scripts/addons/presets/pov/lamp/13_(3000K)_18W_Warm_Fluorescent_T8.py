#Available since 1979
#developed to get closer to tungsten atmospher in interiors

import bpy
bpy.context.object.data.type = 'AREA'
lampdata = bpy.context.object.data

lampdata.size = 0.026
lampdata.size_y = 0.59
lampdata.shadow_ray_samples_x = 1
lampdata.shadow_ray_samples_y = 2
lampdata.color = (1.0, 0.95686274766922, 0.8980392217636108)
lampdata.energy = 1.25898#1350lm/21.446(=lux)*0.004*2.5(distance) *2 for distance is the point of half strength
lampdata.distance = 1.0 #dist values multiplied by 10 for area lights for same power as bulb/spot/...
