#since the 1990's, 
#Often circular or rectangular closed loop electrodeless fluorescent lamps

import bpy
bpy.context.object.data.type = 'SPOT'
lampdata = bpy.context.object.data

#lampdata.use_halo = True
lampdata.spot_size = 3.14
lampdata.spot_blend = 0.9
lampdata.color = (1.0, 0.9450980424880981, 0.8784313797950745)
lampdata.energy = 2.61121#2800/21.446 #lumen values/20 or lux when available used as a basis
lampdata.distance = 0.15#energy calculated for length 0.075 but width gives better result
lampdata.falloff_type = 'INVERSE_SQUARE'
