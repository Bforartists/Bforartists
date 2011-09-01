import bpy
cycles = bpy.context.scene.cycles

cycles.max_bounces = 8
cycles.min_bounces = 3
cycles.no_caustics = True
cycles.diffuse_bounces = 1
cycles.glossy_bounces = 4
cycles.transmission_bounces = 8
cycles.transparent_min_bounces = 8
cycles.transparent_max_bounces = 8
