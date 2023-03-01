import bpy
scene = bpy.context.scene

scene.pov.radio_display_advanced = True
scene.pov.radio_adc_bailout = 0.005
scene.pov.radio_always_sample = False
scene.pov.radio_brightness = 1.0
scene.pov.radio_count = 800
scene.pov.radio_error_bound = 0.2
scene.pov.radio_gray_threshold = 0.0
scene.pov.radio_low_error_factor = 0.7
scene.pov.radio_media = False
scene.pov.radio_subsurface = False
scene.pov.radio_minimum_reuse = 0.01
scene.pov.radio_maximum_reuse = 0.2
scene.pov.radio_nearest_count = 9
scene.pov.radio_normal = False
scene.pov.radio_recursion_limit = 1
scene.pov.radio_pretrace_start = 0.08
scene.pov.radio_pretrace_end = 0.01
