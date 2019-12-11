# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>


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
