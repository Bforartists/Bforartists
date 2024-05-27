# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later


"""
This script imports a Krita/Gimp Palette to Blender.

Usage:
Run this script from "File->Import" menu and then load the desired KPL file.
"""

import bpy
import os
import struct


def load(context, filepath):
    (path, filename) = os.path.split(filepath)

    pal = None
    valid = False
    finput = open(filepath)
    line = finput.readline()

    while line:
        if valid:
            # Create Palette
            if pal is None:
                pal = bpy.data.palettes.new(name=filename)

            # Create Color
            values = line.split()
            col = [0, 0, 0]
            col[0] = int(values[0]) / 255.0
            col[1] = int(values[1]) / 255.0
            col[2] = int(values[2]) / 255.0

            palcol = pal.colors.new()
            palcol.color[0] = col[0]
            palcol.color[1] = col[1]
            palcol.color[2] = col[2]

        if line[0] == '#':
            valid = True

        line = finput.readline()

    finput.close()

    return {'FINISHED'}
