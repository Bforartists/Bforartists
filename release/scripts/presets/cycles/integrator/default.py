import bpy
cycles = bpy.context.scene.cycles

cycles.max_bounces = 12
cycles.diffuse_bounces = 4
cycles.glossy_bounces = 4
cycles.transmission_bounces = 12
cycles.volume_bounces = 0
cycles.transparent_max_bounces = 8
cycles.caustics_reflective = False
cycles.caustics_refractive = False
cycles.blur_glossy = 1.0
