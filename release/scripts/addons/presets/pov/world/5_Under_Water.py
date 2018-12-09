import bpy
scene = bpy.context.scene

scene.world.use_sky_blend = True
#below multiplied by two for a better proportion Clear vs Overcast sky 
#since Clear sky is 20000 lux vs 2000 for overcast
scene.world.horizon_color = (0.0, 0.0, 0.0)
scene.world.zenith_color = (0.250980406999588, 0.6117647290229797, 1.0)
scene.world.ambient_color = (0.0, 0.0, 0.0)
scene.world.mist_settings.use_mist = False
scene.world.mist_settings.intensity = 0.0
scene.world.mist_settings.depth = 25.0
scene.world.mist_settings.start = 5.0
scene.pov.media_enable = True
scene.pov.media_scattering_type = '5'
scene.pov.media_samples = 35
scene.pov.media_diffusion_color = (0.000034, 0.000034, 0.000017)
scene.pov.media_absorption_color = (0.00000455, 0.00000165, 0.00000031)
scene.pov.media_eccentricity = 0.7