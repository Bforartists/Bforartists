import bpy
camera = bpy.context.edit_movieclip.tracking.camera

camera.sensor_width = 5.37
camera.units = 'MILLIMETERS'
camera.pixel_aspect = 1
