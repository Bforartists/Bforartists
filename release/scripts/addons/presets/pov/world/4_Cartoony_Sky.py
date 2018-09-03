import bpy
scene = bpy.context.scene

scene.world.use_sky_blend = True
#below multiplied by two for a better proportion Clear vs Overcast sky 
#since Clear sky is 20000 lux vs 2000 for overcast
scene.world.horizon_color = (0.350*2, 0.611*2, 1.0*2)
scene.world.zenith_color = (0.05000000074505806*2, 0.125*2, 0.5*2)
scene.world.ambient_color = (0.0, 0.0, 0.0)
scene.world.mist_settings.use_mist = False
scene.world.mist_settings.intensity = 0.0
scene.world.mist_settings.depth = 25.0
scene.world.mist_settings.start = 5.0
scene.pov.media_enable = False
scene.pov.media_scattering_type = '4'
scene.pov.media_samples = 35
scene.pov.media_diffusion_color = (0.20000000298023224, 0.4000000059604645, 1.0)
scene.pov.media_absorption_color = (0.0, 0.0, 0.0)
scene.pov.media_eccentricity = 0.0