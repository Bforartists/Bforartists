#Starting from 1918 (World War I Wood's glass)

import bpy
bpy.context.object.data.type = 'POINT'
lampdata = bpy.context.object.data

lampdata.color = (0.6549019813537598, 0.0, 1.0)
lampdata.energy = 1.86515#100/21.446 #lumen values/21.446 or lux when available used as a basis
