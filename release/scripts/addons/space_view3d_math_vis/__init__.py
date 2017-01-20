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

bl_info = {
    "name": "Math Vis (Console)",
    "author": "Campbell Barton",
    "version": (0, 1),
    "blender": (2, 57, 0),
    "location": "View3D > Tool Shelf or Console",
    "description": "Display console defined mathutils variables in the 3D view",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/3D_interaction/Math_Viz",
    "support": "OFFICIAL",
    "category": "3D View",
}


if "bpy" in locals():
    import importlib
    importlib.reload(utils)
    importlib.reload(draw)
else:
    from . import utils, draw

import bpy


def console_hook():
    draw.tag_redraw_all_view3d()

def register():
    draw.callback_enable()

    import console_python
    console_python.execute.hooks.append((console_hook, ()))


def unregister():
    draw.callback_disable()

    import console_python
    console_python.execute.hooks.remove((console_hook, ()))
