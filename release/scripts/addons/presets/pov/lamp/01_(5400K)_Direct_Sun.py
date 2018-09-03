#Since the dawn of time

import bpy
bpy.context.object.data.type = 'SUN'
lampdata = bpy.context.object.data

lampdata.color = (1.0, 1.0, 0.9843137264251709)
lampdata.energy = 1.2 #100 000lux
#lampdata.distance = 0.001
#lampdata.falloff_type = 'INVERSE_SQUARE'