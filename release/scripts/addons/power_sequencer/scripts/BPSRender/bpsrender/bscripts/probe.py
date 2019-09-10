#
# Copyright (C) 2016-2019 by Razvan Radulescu, Nathan Lovato, and contributors
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
import bpy

EXT = {
    "AVI_JPEG": ".avi",
    "AVI_RAW": ".avi",
    "FFMPEG": {"MKV": ".mkv", "OGG": ".ogv", "QUICKTIME": ".mov", "AVI": ".avi", "MPEG4": ".mp4"},
}

scene = bpy.context.scene

ext = EXT.get(scene.render.image_settings.file_format, "UNDEFINED")
if scene.render.image_settings.file_format == "FFMPEG":
    ext = ext[scene.render.ffmpeg.format]
print("\nBPS:{} {} {}\n".format(scene.frame_start, scene.frame_end, ext))
