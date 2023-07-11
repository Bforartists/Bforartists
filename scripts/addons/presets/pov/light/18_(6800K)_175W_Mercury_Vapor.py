#Starting from 1901

import bpy
bpy.context.object.data.type = 'SPOT'
lampdata = bpy.context.object.data

lampdata.show_cone = True
lampdata.spot_size = 1.25
lampdata.spot_blend = 0.9
lampdata.color = (0.8470588326454163, 0.9686274528503418, 1.0)
lampdata.energy = 17.25263#7400lm/21.446(=lux)*0.004*6.25(distance) *2 for distance is the point of half strength
