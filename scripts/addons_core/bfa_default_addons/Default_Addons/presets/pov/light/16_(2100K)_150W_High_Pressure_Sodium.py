#Starting from 1964

import bpy
bpy.context.object.data.type = 'SPOT'
lampdata = bpy.context.object.data

lampdata.show_cone = True
lampdata.color = (1.0, 0.772549033164978, 0.5607843399047852)
lampdata.energy = 4.47636#12000lm/21.446(=lux)*0.004(distance) *2 for distance is the point of half strength
lampdata.spot_size = 1.9
lampdata.spot_blend = 0.9
