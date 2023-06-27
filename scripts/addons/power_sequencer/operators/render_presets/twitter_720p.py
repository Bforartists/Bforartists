# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

if __name__ == "__main__":
    import bpy

    render = bpy.context.scene.render
    render.resolution_x = 1280
    render.resolution_y = 720
    render.resolution_percentage = 100
    render.pixel_aspect_x = 1
    render.pixel_aspect_y = 1

    # FFMPEG
    render.image_settings.file_format = "FFMPEG"
    render.ffmpeg.format = "MPEG4"
    render.ffmpeg.codec = "H264"

    render.ffmpeg.constant_rate_factor = "HIGH"
    render.ffmpeg.ffmpeg_preset = "BEST"

    is_ntsc = render.fps != 25
    if is_ntsc:
        render.ffmpeg.gopsize = 18
    else:
        render.ffmpeg.gopsize = 15
    render.ffmpeg.use_max_b_frames = False

    render.ffmpeg.video_bitrate = 4000
    render.ffmpeg.maxrate = 4000
    render.ffmpeg.minrate = 0
    render.ffmpeg.buffersize = 224 * 8
    render.ffmpeg.packetsize = 2048
    render.ffmpeg.muxrate = 10080000
