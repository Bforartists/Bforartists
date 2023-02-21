import bpy
cycles = bpy.context.scene.cycles

cycles.max_bounces = 8
cycles.caustics_reflective = False
cycles.caustics_refractive = False
cycles.diffuse_bounces = 1
cycles.glossy_bounces = 4
cycles.transmission_bounces = 8
cycles.volume_bounces = 0
cycles.transparent_max_bounces = 8
cycles.use_fast_gi = False
cycles.ao_bounces = 1
cycles.ao_bounces_render = 1
