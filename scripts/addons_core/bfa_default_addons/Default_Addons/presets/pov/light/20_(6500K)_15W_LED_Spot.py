#since 2008

import bpy
bpy.context.object.data.type = 'SPOT'
lampdata = bpy.context.object.data

lampdata.show_cone = True
lampdata.spot_size = 1.39626 #80 degrees in radian
lampdata.spot_blend = 0.5
lampdata.color = (1.0, 0.9372549057006836, 0.9686274528503418)
lampdata.energy = 1.39886#1500lm/21.446(=lux)*0.004*2.5(distance) *2 for distance is the point of half strength
