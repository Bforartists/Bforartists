#Starting from 1876 (first type of commercial lamps developed with electricity)
#Carbon arc lamps were being phased out after the 1910s.
#For general lighting the lamp was replaced by the 1920s and 30s in most cities.
#The lamp continued to be used for spot lights, film production lighting and film projector lamps.
#Most of the remaining carbon arc lamps ceased production by the 1980s

import bpy
bpy.context.object.data.type = 'SPOT'
lampdata = bpy.context.object.data

#lampdata.use_halo = True
lampdata.show_cone = True
lampdata.spot_size = 1.5
lampdata.spot_blend = 0.3
lampdata.color = (1.0, 0.9803921580314636, 0.95686274766922)
lampdata.energy = 51.29162#55000lm/21.446(=lux)*0.004*2.5(distance) *2 for distance is the point of half strength
