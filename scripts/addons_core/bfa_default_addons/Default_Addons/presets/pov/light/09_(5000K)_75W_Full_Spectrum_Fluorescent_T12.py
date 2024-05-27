#Available since 1979 (Triphosphor lamps)

import bpy
bpy.context.object.data.type = 'AREA'
lampdata = bpy.context.object.data

lampdata.size = 0.038
lampdata.size_y = 2.40284
lampdata.pov.shadow_ray_samples_x = 1
lampdata.pov.shadow_ray_samples_y = 2
lampdata.color = (1.0, 0.95686274766922, 0.9490200281143188)
lampdata.energy = 4.45304#4775lm/21.446(=lux)*0.004(distance) *2 for distance is the point of half strength 6200lm?
