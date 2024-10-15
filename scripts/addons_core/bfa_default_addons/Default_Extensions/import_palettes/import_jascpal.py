# SPDX-FileCopyrightText: 2024 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later


"""
This script imports a JASC-PAL/GraphicsGale Palette to Blender.

Usage:
Run this script from "File->Import" menu and then load the desired PAL file.
"""

import bpy
import os
import struct


def load(context, filepath):
    (path, filename) = os.path.split(filepath)

    finput = open(filepath)

    line = finput.readline()
    assert line.strip() == "JASC-PAL"
    line = finput.readline()
    assert line.strip() == "0100"
    line = finput.readline()
    num_colors = int(line.strip())
    assert num_colors >= 1

    pal = bpy.data.palettes.new(name=filename)


    for _ in range(num_colors):
        line = finput.readline()
        values = line.split()
        palcol = pal.colors.new()
        palcol.color[0] = int(values[0]) / 255.0
        palcol.color[1] = int(values[1]) / 255.0
        palcol.color[2] = int(values[2]) / 255.0

    finput.close()

    return {'FINISHED'}

