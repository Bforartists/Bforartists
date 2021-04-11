import bpy
cycles = bpy.context.scene.cycles

cycles.max_bounces = 32
cycles.caustics_reflective = True
cycles.caustics_refractive = True
cycles.diffuse_bounces = 32
cycles.glossy_bounces = 32
cycles.transmission_bounces = 32
cycles.volume_bounces = 32
cycles.transparent_max_bounces = 32
cycles.use_fast_gi = False
cycles.ao_bounces = 1
cycles.ao_bounces_render = 1
