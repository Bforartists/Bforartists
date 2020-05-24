#
# Copyright (C) 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# This file is part of Power Sequencer.
#
# Power Sequencer is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Power Sequencer is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with Power Sequencer. If
# not, see <https://www.gnu.org/licenses/>.
#
if __name__ == "__main__":
    import bpy

    render = bpy.context.scene.render
    render.resolution_x = 1920
    render.resolution_y = 1080
    render.resolution_percentage = 100
    render.pixel_aspect_x = 1
    render.pixel_aspect_y = 1

    render.image_settings.file_format = "FFMPEG"
    render.ffmpeg.format = "MPEG4"
    render.ffmpeg.codec = "H264"

    render.ffmpeg.constant_rate_factor = "PERC_LOSSLESS"
    render.ffmpeg.ffmpeg_preset = "BEST"

    scene = bpy.context.scene
    fps = scene.render.fps / scene.render.fps_base
    render.ffmpeg.gopsize = round(fps / 2.0)
    render.ffmpeg.use_max_b_frames = True
    render.ffmpeg.max_b_frames = 2

    render.ffmpeg.video_bitrate = 9000
    render.ffmpeg.maxrate = 9000
    render.ffmpeg.minrate = 0
    render.ffmpeg.buffersize = 224 * 8
    render.ffmpeg.packetsize = 2048
    render.ffmpeg.muxrate = 10080000

    render.ffmpeg.audio_codec = "AAC"
    render.ffmpeg.audio_bitrate = 384
