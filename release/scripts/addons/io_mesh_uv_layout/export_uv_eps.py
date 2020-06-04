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

# <pep8-80 compliant>

import bpy


def export(filepath, face_data, colors, width, height, opacity):
    with open(filepath, 'w', encoding='utf-8') as file:
        for text in get_file_parts(face_data, colors, width, height, opacity):
            file.write(text)

def get_file_parts(face_data, colors, width, height, opacity):
    yield from header(width, height)
    if opacity > 0.0:
        name_by_color = {}
        yield from prepare_colors(colors, name_by_color)
        yield from draw_colored_polygons(face_data, name_by_color, width, height)
    yield from draw_lines(face_data, width, height)
    yield from footer()


def header(width, height):
    yield "%!PS-Adobe-3.0 EPSF-3.0\n"
    yield f"%%Creator: Blender {bpy.app.version_string}\n"
    yield "%%Pages: 1\n"
    yield "%%Orientation: Portrait\n"
    yield f"%%BoundingBox: 0 0 {width} {height}\n"
    yield f"%%HiResBoundingBox: 0.0 0.0 {width:.4f} {height:.4f}\n"
    yield "%%EndComments\n"
    yield "%%Page: 1 1\n"
    yield "0 0 translate\n"
    yield "1.0 1.0 scale\n"
    yield "0 0 0 setrgbcolor\n"
    yield "[] 0 setdash\n"
    yield "1 setlinewidth\n"
    yield "1 setlinejoin\n"
    yield "1 setlinecap\n"

def prepare_colors(colors, out_name_by_color):
    for i, color in enumerate(colors):
        name = f"COLOR_{i}"
        yield "/%s {" % name
        out_name_by_color[color] = name

        yield "gsave\n"
        yield "%.3g %.3g %.3g setrgbcolor\n" % color
        yield "fill\n"
        yield "grestore\n"
        yield "0 setgray\n"
        yield "} def\n"

def draw_colored_polygons(face_data, name_by_color, width, height):
    for uvs, color in face_data:
        yield from draw_polygon_path(uvs, width, height)
        yield "closepath\n"
        yield "%s\n" % name_by_color[color]

def draw_lines(face_data, width, height):
    for uvs, _ in face_data:
        yield from draw_polygon_path(uvs, width, height)
        yield "closepath\n"
        yield "stroke\n"

def draw_polygon_path(uvs, width, height):
    yield "newpath\n"
    for j, uv in enumerate(uvs):
        uv_scale = (uv[0] * width, uv[1] * height)
        if j == 0:
            yield "%.5f %.5f moveto\n" % uv_scale
        else:
            yield "%.5f %.5f lineto\n" % uv_scale

def footer():
    yield "showpage\n"
    yield "%%EOF\n"
