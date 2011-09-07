import bpy
is_ntsc = (bpy.context.scene.render.fps != 25)

bpy.context.scene.render.ffmpeg_format = "MPEG2"
bpy.context.scene.render.resolution_x = 480

if is_ntsc:
    bpy.context.scene.render.resolution_y = 480
    bpy.context.scene.render.ffmpeg_gopsize = 18
else:
    bpy.context.scene.render.resolution_y = 576
    bpy.context.scene.render.ffmpeg_gopsize = 15

bpy.context.scene.render.ffmpeg_video_bitrate = 2040
bpy.context.scene.render.ffmpeg_maxrate = 2516
bpy.context.scene.render.ffmpeg_minrate = 0
bpy.context.scene.render.ffmpeg_buffersize = 224 * 8
bpy.context.scene.render.ffmpeg_packetsize = 2324
bpy.context.scene.render.ffmpeg_muxrate = 0

bpy.context.scene.render.ffmpeg_audio_bitrate = 224
bpy.context.scene.render.ffmpeg_audio_mixrate = 44100
bpy.context.scene.render.ffmpeg_audio_codec = "MP2"
bpy.context.scene.render.ffmpeg_audio_channels = 2
