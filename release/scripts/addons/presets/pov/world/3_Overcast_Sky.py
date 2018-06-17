import bpy
scene = bpy.context.scene

scene.world.use_sky_blend = True
scene.world.horizon_color = (0.477, 0.536, 0.604)
#below divided by ten for a better proportion Clear vs Overcast sky 
#since Clear sky is 20000 lux vs 2000 up to 10000 for overcast
scene.world.zenith_color = (0.034, 0.043, 0.047)
scene.world.ambient_color = (0.0, 0.0, 0.0)
scene.world.mist_settings.use_mist = False
scene.world.mist_settings.intensity = 0.0
scene.world.mist_settings.depth = 25.0
scene.world.mist_settings.start = 5.0
scene.pov.media_enable = False
scene.pov.media_scattering_type = '1'
scene.pov.media_samples = 35
scene.pov.media_diffusion_scale = (1.0)
scene.pov.media_diffusion_color = (0.58, 0.66, 0.75)
scene.pov.media_absorption_color = (0.0, 0.0, 0.0)
scene.pov.media_eccentricity = 0.0
