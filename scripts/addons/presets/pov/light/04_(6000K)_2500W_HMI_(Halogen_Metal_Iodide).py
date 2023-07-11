#After 1969
#made specifically for film and entertainment applications

import bpy
bpy.context.object.data.type = 'SPOT'
lampdata = bpy.context.object.data

lampdata.show_cone = True
lampdata.spot_size = 0.872665
lampdata.spot_blend = 0.9
lampdata.color = (0.99, 0.9882352948188782, 0.998)
lampdata.energy = 223.81796 #240000lm/21.446(=lux)*0.004*2.5(distance) *2 for distance is the point of half strength
