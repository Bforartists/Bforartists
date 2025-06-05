#since 1908

import bpy
bpy.context.object.data.type = 'POINT'
lampdata = bpy.context.object.data

lampdata.color = (1.0, 0.8196078431372549, 0.6980392156862745)
lampdata.energy = 2.98424#400/21.446 #lumen values/21.446 or lux when available used as a basis
