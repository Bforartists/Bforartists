#since 1960, no longer manufactured since 2016
#8mm projectors
#used in many automobiles headlamps ; outdoor lighting systems ; watercraft ; desktop lamps (smaller power).
#theatrical and studio (film and television) fixtures, including Ellipsoidal reflector spotlights, Source Four, and Fresnels; PAR Cans

import bpy
bpy.context.object.data.type = 'SPOT'
lampdata = bpy.context.object.data

lampdata.show_cone = True
lampdata.spot_size = 1.9
lampdata.spot_blend = 0.9
lampdata.color = (1.0, 0.9450980424880981, 0.8784313797950745)
lampdata.energy = 12.43433#5000/21.446 #lumen values/20 or lux when available used as a basis
lampdata.distance = 0.015#energy calculated for length 0.075 but width gives better result
lampdata.falloff_type = 'INVERSE_SQUARE'
