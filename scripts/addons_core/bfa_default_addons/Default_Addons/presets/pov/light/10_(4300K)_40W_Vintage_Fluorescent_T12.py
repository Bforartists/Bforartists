#since 1939 , T12 no longer manufactured since T8 propagated

import bpy
bpy.context.object.data.type = 'AREA'
lampdata = bpy.context.object.data

lampdata.size = 0.038
lampdata.size_y = 1.2192
lampdata.pov.shadow_ray_samples_x = 1
lampdata.pov.shadow_ray_samples_y = 2
lampdata.color = (0.901, 1.0, 0.979)
lampdata.energy = 2.14492#2300lm/21.446(=lux)*0.004*2.5(distance) *2 for distance is the point of half strength
