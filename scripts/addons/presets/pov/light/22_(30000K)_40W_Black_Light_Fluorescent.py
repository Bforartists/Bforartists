#Starting from 1939 (World War II Byler's tubes)

import bpy
bpy.context.object.data.type = 'AREA'
lampdata = bpy.context.object.data

lampdata.size = 0.038
lampdata.size_y = 1.2192
lampdata.color = (0.6549019813537598, 0.0, 1.0)
lampdata.energy = 1.86515#100/21.446 #lumen values/21.446 or lux when available used as a basis
