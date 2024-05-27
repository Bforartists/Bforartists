#After 1962
#Common uses: outdoor lighting where good color rendering is needed, television/film lighting, sports fields, car headlights, flood lights, heavy flashlights, green house applications

import bpy
bpy.context.object.data.type = 'SPOT'
lampdata = bpy.context.object.data

lampdata.show_cone = True
lampdata.spot_size = 0.6
lampdata.spot_blend = 0.9
lampdata.color = (0.9490196108818054, 0.9882352948188782, 1.0)
lampdata.energy = 20.98293#9000lm/21.446(=lux)*0.004*6.25(distance) *2 for distance is the point of half strength
