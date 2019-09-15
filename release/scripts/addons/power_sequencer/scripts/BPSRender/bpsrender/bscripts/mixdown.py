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
import os.path as osp
import sys

if __name__ == "__main__":
    for strip in bpy.context.scene.sequence_editor.sequences_all:
        if strip.type == "META":
            continue
        if strip.type != "SOUND":
            strip.mute = True

    path = sys.argv[-1]
    ext = osp.splitext(path)[1][1:].upper()
    bpy.ops.sound.mixdown(filepath=path, check_existing=False, container=ext, codec=ext)
