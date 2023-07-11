#1908 - today

import bpy
bpy.context.object.data.type = 'POINT'
lampdata = bpy.context.object.data

lampdata.color = (1.0, 0.8392156958580017, 0.6666666865348816)
lampdata.energy = 7.46060#3.7303#1000/21.446/(lampdistance/candledistance)  #lumen values/21.446 or lux when available used as a basis
