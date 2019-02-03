import bpy
scene = bpy.context.scene

scene.world.use_sky_blend = True
#below multiplied by two for a better proportion Clear vs Overcast sky
#since Clear sky is 19807 lux vs 2000 for overcast (sun is min 32000 max 100000)
#http://www.pssurvival.com/PS/Lighting/Typical_LUX_Intensities_for_Day_and_Night-2017.pdf
#https://en.wikipedia.org/wiki/Daylight
#https://www.engineeringtoolbox.com/light-level-rooms-d_708.html
#https://www.cactus2000.de/fr/unit/masslux.shtml
#https://blendergrid.com/news/cycles-physically-correct-brightness
#researched result blue is
    #Hue: 0.6
    #Saturation: 0.533
    #Lightness: 0.7
#put scattering scale at 0.0002 and scattering color rgb <0.2061, 0.3933, 1.0>
#with very small value like round rgb 0.00002 0.00002 0.00008
#Sky color at zenith, sun 90Â° elevation = hsl <0.6, 0.533, 0.698>
#Ground color = rgb <0.996, 0.965, 0.855>  = hsl <0.128, 0.141, 0.996>
#Ground Brightness = 0.996

scene.world.horizon_color = (0.047, 0.034, 0.025) #24000 or 22000 lux roughly equals (sun+sky)/5
scene.world.zenith_color = (0.006, 0.013, 0.033) #19807 lux roughly equals hign noon Sun / 5
scene.world.ambient_color = (0.0, 0.0, 0.0)
scene.world.mist_settings.use_mist = False
scene.world.mist_settings.intensity = 0.0
scene.world.mist_settings.depth = 25.0
scene.world.mist_settings.start = 5.0
scene.pov.media_enable = True
scene.pov.media_scattering_type = '4'
scene.pov.media_samples = 35
scene.pov.media_diffusion_scale = (0.00002)
scene.pov.media_diffusion_color = (0.000001, 0.000002, 0.000005)
scene.pov.media_absorption_scale = (0.00002)
scene.pov.media_absorption_color = (0.0000006067, 0.0000007939, 0.0)#up to 0.00007
scene.pov.media_eccentricity = 0.0
