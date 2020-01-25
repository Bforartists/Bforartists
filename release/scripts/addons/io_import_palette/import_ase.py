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

# This ASE converion use code from Marcos A Ojeda http://generic.cx/
#
# With notes from
# http://iamacamera.org/default.aspx?id=109 by Carl Camera and
# http://www.colourlovers.com/ase.phps by Chris Williams

# <pep8 compliant>


"""
This script imports a ASE Palette to Blender.

Usage:
Run this script from "File->Import" menu and then load the desired ASE file.
"""

import bpy
import os
import struct


def parse_chunk(fd):
    chunk_type = fd.read(2)
    while chunk_type:
        if chunk_type == b'\x00\x01':
            # a single color
            o = dict_for_chunk(fd)
            yield o

        elif chunk_type == b'\xC0\x01':
            # folder/palette
            o = dict_for_chunk(fd)
            o['swatches'] = [x for x in colors(fd)]
            yield o

        elif chunk_type == b'\xC0\x02':
            # this signals the end of a folder
            assert fd.read(4) == b'\x00\x00\x00\x00'
            pass

        else:
            # the file is malformed?
            assert chunk_type in [
                b'\xC0\x01', b'\x00\x01', b'\xC0\x02', b'\x00\x02']
            pass

        chunk_type = fd.read(2)


def colors(fd):
    chunk_type = fd.read(2)
    while chunk_type in [b'\x00\x01', b'\x00\x02']:
        d = dict_for_chunk(fd)
        yield d
        chunk_type = fd.read(2)
    fd.seek(-2, os.SEEK_CUR)


def dict_for_chunk(fd):
    chunk_length = struct.unpack(">I", fd.read(4))[0]
    data = fd.read(chunk_length)

    title_length = (struct.unpack(">H", data[:2])[0]) * 2
    title = data[2:2 + title_length].decode("utf-16be").strip('\0')
    color_data = data[2 + title_length:]

    output = {
        'name': str(title),
        'type': 'Color Group'  # default to color group
    }

    if color_data:
        fmt = {b'RGB': '!fff', b'Gray': '!f', b'CMYK': '!ffff', b'LAB': '!fff'}
        color_mode = struct.unpack("!4s", color_data[:4])[0].strip()
        color_values = list(struct.unpack(fmt[color_mode], color_data[4:-2]))

        color_types = ['Global', 'Spot', 'Process']
        swatch_type_index = struct.unpack(">h", color_data[-2:])[0]
        swatch_type = color_types[swatch_type_index]

        output.update({
            'data': {
                'mode': color_mode.decode('utf-8'),
                'values': color_values
            },
            'type': str(swatch_type)
        })

    return output


def parse(filename):
    with open(filename, "rb") as data:
        header, v_major, v_minor, chunk_count = struct.unpack("!4sHHI", data.read(12))

        assert header == b"ASEF"
        assert (v_major, v_minor) == (1, 0)

        return [c for c in parse_chunk(data)]


def load(context, filepath):
    output = parse(filepath)

    (path, filename) = os.path.split(filepath)

    pal = None

    for elm in output:
        valid = False
        data = elm['data']
        color = [0, 0, 0]
        val = data['values']

        if data['mode'] == 'RGB':
            valid = True
            color[0] = val[0]
            color[1] = val[1]
            color[2] = val[2]
        elif data['mode'] == 'Gray':
            valid = True
            color[0] = val[0]
            color[1] = val[0]
            color[2] = val[0]
        elif data['mode'] == 'CMYK':
            valid = True
            color[0] = (1.0 - val[0]) * (1.0 - val[3])
            color[1] = (1.0 - val[1]) * (1.0 - val[3])
            color[2] = (1.0 - val[2]) * (1.0 - val[3])

        # Create palette color
        if valid:
            # Create Palette
            if pal is None:
                pal = bpy.data.palettes.new(name=filename)

            # Create Color
            col = pal.colors.new()
            col.color[0] = color[0]
            col.color[1] = color[1]
            col.color[2] = color[2]

    return {'FINISHED'}
