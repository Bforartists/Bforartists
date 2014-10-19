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

import bpy

from export_svg import svg_export_header, svg_export_animation

def register():
    bpy.app.handlers.render_init.append(svg_export_header)
    bpy.app.handlers.render_complete.append(svg_export_animation)

def unregister():
    bpy.app.handlers.render_init.remove(svg_export_header)
    bpy.app.handlers.render_complete.remove(svg_export_animation)

if __name__ == '__main__':
    register()
